"""
Gold rate fetching and parsing for the Kerala tracker.

Kept separate from the notification logic so the fragile part - reading numbers
out of somebody else's HTML - can be tested against saved fixtures without a
browser or a network call.

Fetching is layered: a plain HTTP request first (fast, no browser), falling back
to Selenium only when that fails or returns something unparseable.
"""

import os
import random
import re
import time

import requests

SOURCE_URL = "https://www.goodreturns.in/gold-rates/kerala.html"

# Plausibility bounds for a per-gram rate in INR. These exist to catch the
# failure mode that actually bit us: picking up the 8g/10g/100g cell from a
# neighbouring column and recording it as the per-gram rate. On 2026-04-30 the
# tracker stored 150660.0 - exactly 10x the real 15066.0 - and fired a "MAJOR
# CHANGE" alert off it.
RATE_SANITY_MIN = 1000.0
RATE_SANITY_MAX = 60000.0

# 22K is 22/24 = 91.67% pure. Retail 22K quotes sit close to that ratio; anything
# far outside this band means we matched the wrong number.
PURITY_RATIO_22K = 22.0 / 24.0
RATIO_MIN = 0.88
RATIO_MAX = 0.95

REQUEST_TIMEOUT = 20
FETCH_ATTEMPTS = 3

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


class RateExtractionError(Exception):
    """Raised when the page loaded but no trustworthy rate could be read from it."""


def is_plausible_rate(value):
    """True if value could be a per-gram INR gold rate."""
    return isinstance(value, (int, float)) and RATE_SANITY_MIN <= value <= RATE_SANITY_MAX


def _to_number(raw):
    try:
        return float(raw.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


# Patterns are ordered most-specific first. Every gap between the karat label and
# the rupee figure is bounded with a limited non-digit run rather than the old
# `.*?` under re.DOTALL - that unbounded wildcard is what let a match wander
# across the page into the wrong table cell.
def _karat_patterns(karat):
    k = str(karat)
    return [
        rf"{k}K\s*Gold\s*/\s*g\b[^\d₹]{{0,40}}₹?\s*([\d,]+(?:\.\d+)?)",
        rf"{k}\s*(?:K|Karat|Carat)\s*Gold[^\d₹]{{0,40}}₹\s*([\d,]+(?:\.\d+)?)",
        rf"{k}\s*(?:K|Karat|Carat)\b[^\d₹]{{0,60}}₹\s*([\d,]+(?:\.\d+)?)",
    ]


def extract_rate_from_html(html, karat):
    """
    Pull the per-gram rate for the given karat out of raw page HTML.

    Returns the first candidate that passes the plausibility check rather than
    the first candidate found, so an 8g or 10g figure is skipped instead of
    being silently recorded.
    """
    if not html:
        return None

    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;?", " ", text)
    text = re.sub(r"&#8377;|&rupee;|Rs\.?", "₹", text)
    text = re.sub(r"\s+", " ", text)

    for pattern in _karat_patterns(karat):
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = _to_number(match.group(1))
            if is_plausible_rate(value):
                return value

    return _extract_rate_from_tables(html, karat)


def _extract_rate_from_tables(html, karat):
    """Structured fallback: walk table rows looking for the karat label."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return None

    label = re.compile(rf"\b{karat}\s*(?:K|Karat|Carat)\b", re.IGNORECASE)
    gram_label = re.compile(r"\b1\s*(?:gram|gm|g)\b", re.IGNORECASE)

    # Prefer a row that names both the karat and a 1-gram quantity, since
    # goodreturns lays out 1g / 8g / 10g / 100g columns side by side.
    for require_gram in (True, False):
        for row in soup.find_all("tr"):
            row_text = row.get_text(" ", strip=True)
            if not label.search(row_text):
                continue
            if require_gram and not gram_label.search(row_text):
                continue
            for cell in row.find_all(["td", "th"]):
                for raw in re.findall(r"([\d,]+(?:\.\d+)?)", cell.get_text(" ", strip=True)):
                    value = _to_number(raw)
                    if is_plausible_rate(value):
                        return value
    return None


def extract_rates(html):
    """
    Read both karats from a page.

    24K is required. 22K is derived from 24K when the page does not yield a
    trustworthy figure, so a layout change on the 22K row degrades the number's
    precision instead of breaking the whole run.
    """
    rate_24k = extract_rate_from_html(html, 24)
    if not is_plausible_rate(rate_24k):
        raise RateExtractionError("no plausible 24K rate found on page")

    rate_22k = extract_rate_from_html(html, 22)
    source_22k = "scraped"

    if not is_plausible_rate(rate_22k):
        rate_22k, source_22k = None, "derived"
    elif rate_22k >= rate_24k:
        raise RateExtractionError(
            f"22K (₹{rate_22k:,.0f}) is not below 24K (₹{rate_24k:,.0f}); "
            "the karat rows were most likely mis-read"
        )
    else:
        ratio = rate_22k / rate_24k
        if not (RATIO_MIN <= ratio <= RATIO_MAX):
            print(f"⚠️  22K/24K ratio {ratio:.4f} outside {RATIO_MIN}-{RATIO_MAX}; deriving instead")
            rate_22k, source_22k = None, "derived"

    if rate_22k is None:
        rate_22k = round(rate_24k * PURITY_RATIO_22K, 2)

    return {"rate_24k": rate_24k, "rate_22k": rate_22k, "rate_22k_source": source_22k}


def fetch_html_requests(url=SOURCE_URL):
    """Plain HTTP fetch. No browser, ~1s instead of ~45s."""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def fetch_html_selenium(url=SOURCE_URL):
    """Browser fetch, used only when the plain request path does not work out."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    for arg in (
        "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
        "--disable-extensions", "--window-size=1920,1080",
        "--disable-blink-features=AutomationControlled",
    ):
        options.add_argument(arg)
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    try:
        driver.set_page_load_timeout(45)
        driver.get(url)
        time.sleep(random.uniform(2.0, 3.0))
        return driver.page_source
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def fetch_rates(url=SOURCE_URL, allow_selenium=True):
    """
    Fetch and parse rates, trying HTTP first then a browser.

    Returns the rate dict plus which transport produced it. Raises
    RateExtractionError with the accumulated reasons if every attempt fails.
    """
    problems = []

    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            html = fetch_html_requests(url)
            rates = extract_rates(html)
            rates["fetch_method"] = "requests"
            print(f"✅ Fetched via HTTP (attempt {attempt})")
            return rates
        except Exception as exc:
            problems.append(f"requests attempt {attempt}: {exc}")
            print(f"⚠️  HTTP attempt {attempt} failed: {exc}")
            if attempt < FETCH_ATTEMPTS:
                time.sleep(2 ** attempt)

    if allow_selenium:
        try:
            html = fetch_html_selenium(url)
            rates = extract_rates(html)
            rates["fetch_method"] = "selenium"
            print("✅ Fetched via Selenium fallback")
            return rates
        except Exception as exc:
            problems.append(f"selenium: {exc}")
            print(f"⚠️  Selenium fallback failed: {exc}")

    raise RateExtractionError("; ".join(problems))


def validate_against_previous(new_rate, previous_rate, hours_since):
    """
    Reject readings that move more than gold plausibly can.

    Returns (ok, reason). Kerala rates move a few percent a day at most, so a
    large jump between two readings means a bad parse far more often than it
    means a real move. The tolerance widens for long gaps so a multi-day outage
    does not leave the tracker permanently stuck.
    """
    if not previous_rate or previous_rate <= 0:
        return True, ""

    limit = 10.0 if hours_since is not None and hours_since < 24 else 25.0
    change_percent = abs(new_rate - previous_rate) / previous_rate * 100

    if change_percent > limit:
        ratio = new_rate / previous_rate
        hint = ""
        if 9.0 <= ratio <= 11.0 or 0.09 <= ratio <= 0.11:
            hint = " (looks like a per-gram vs per-10g unit mismatch)"
        return False, (
            f"rate moved {change_percent:.1f}% (₹{previous_rate:,.0f} → ₹{new_rate:,.0f}) "
            f"which exceeds the {limit:.0f}% limit for a {hours_since or 0:.1f}h gap{hint}"
        )

    return True, ""
