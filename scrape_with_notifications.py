import json
import os
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

class GoldScraperWithNotifications:
    def __init__(self):
        self.url = "https://www.goodreturns.in/gold-rates/kerala.html"
        self.setup_driver()
        
        # Notification settings
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.pushover_token = os.environ.get('PUSHOVER_TOKEN')
        self.pushover_user = os.environ.get('PUSHOVER_USER')
        self.ntfy_topic = os.environ.get('NTFY_TOPIC')
    
    def setup_driver(self):
        """Setup Chrome driver for GitHub Actions"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def scrape_rate(self):
        """Scrape current gold rate"""
        try:
            print("🔍 Scraping Kerala 24K gold rate...")
            self.driver.get(self.url)
            time.sleep(3)
            
            rate = self.extract_24k_rate()
            
            if rate:
                current_data = {
                    'rate': rate,
                    'currency': 'INR',
                    'unit': 'per gram',
                    'purity': '24K',
                    'location': 'Kerala',
                    'timestamp': datetime.now().isoformat(),
                    'source': self.url,
                    'success': True
                }
                
                # Check for significant changes and send notifications
                self.check_and_notify(current_data)
                
                # Save data
                self.save_data(current_data)
                
                print(f"✅ Success: ₹{rate} per gram (24K)")
                return current_data
            else:
                self.send_error_notification("Failed to scrape 24K gold rate")
                return None
                
        except Exception as e:
            self.send_error_notification(f"Scraping error: {str(e)}")
            return None
        finally:
            self.driver.quit()
    
    def extract_24k_rate(self):
        """Extract 24K gold rate specifically"""
        try:
            print("🔍 Looking for 24K gold rate...")
            
            # Method 1: Look for specific 24K patterns in the page source
            page_source = self.driver.page_source
            
            # Pattern 1: "24K Gold /g" followed by price (most specific)
            pattern1 = r'24K\s+Gold\s*/g.*?₹\s*([\d,]+)'
            match1 = re.search(pattern1, page_source, re.IGNORECASE | re.DOTALL)
            if match1:
                rate = float(match1.group(1).replace(',', ''))
                print(f"✅ Found 24K rate via pattern 1: ₹{rate}")
                return rate
            
            # Pattern 2: Look for table/div structure with 24K
            rate = self.extract_from_elements()
            if rate:
                return rate
            
            # Pattern 3: More flexible patterns
            patterns = [
                r'24K.*?₹\s*([\d,]+)',
                r'24\s*Karat.*?₹\s*([\d,]+)', 
                r'24\s*Carat.*?₹\s*([\d,]+)',
                r'24k.*?₹\s*([\d,]+)'
            ]
            
            for i, pattern in enumerate(patterns, 3):
                match = re.search(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if match:
                    rate = float(match.group(1).replace(',', ''))
                    print(f"✅ Found 24K rate via pattern {i}: ₹{rate}")
                    return rate
            
            # If no 24K found, log what we did find
            print("❌ No 24K rate found. Checking what's available...")
            self.debug_available_rates(page_source)
            
        except Exception as e:
            print(f"❌ Extraction error: {e}")
        
        return None
    
    def extract_from_elements(self):
        """Extract rate by finding 24K elements specifically"""
        try:
            # Look for elements containing "24K" text
            elements_24k = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'k', 'K'), '24K')]")
            
            for element in elements_24k:
                text = element.text
                print(f"🔍 Found 24K element: {text}")
                
                # Check if this element or its siblings contain a price
                if '₹' in text:
                    match = re.search(r'₹\s*([\d,]+)', text)
                    if match:
                        rate = float(match.group(1).replace(',', ''))
                        print(f"✅ Found rate in same element: ₹{rate}")
                        return rate
                
                # Check parent element
                try:
                    parent = element.find_element(By.XPATH, "..")
                    parent_text = parent.text
                    if '₹' in parent_text and '24K' in parent_text:
                        match = re.search(r'₹\s*([\d,]+)', parent_text)
                        if match:
                            rate = float(match.group(1).replace(',', ''))
                            print(f"✅ Found rate in parent element: ₹{rate}")
                            return rate
                except:
                    pass
                
                # Check next sibling elements for price
                try:
                    next_elements = element.find_elements(By.XPATH, "./following-sibling::*[position()<=3]")
                    for next_elem in next_elements:
                        if '₹' in next_elem.text:
                            match = re.search(r'₹\s*([\d,]+)', next_elem.text)
                            if match:
                                rate = float(match.group(1).replace(',', ''))
                                print(f"✅ Found rate in sibling element: ₹{rate}")
                                return rate
                except:
                    pass
            
            # Look for table structures specifically
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    row_text = row.text
                    if '24K' in row_text or '24 K' in row_text:
                        print(f"🔍 Found 24K in table row: {row_text}")
                        # Extract price from this row
                        match = re.search(r'₹\s*([\d,]+)', row_text)
                        if match:
                            rate = float(match.group(1).replace(',', ''))
                            print(f"✅ Found rate in table: ₹{rate}")
                            return rate
            
        except Exception as e:
            print(f"❌ Element extraction error: {e}")
        
        return None
    
    def debug_available_rates(self, page_source):
        """Debug function to see what rates are available"""
        try:
            print("\n🔍 DEBUG: Available gold rates on page:")
            
            # Find all rates with karat info
            patterns = [
                r'(\d+K?\s*(?:Gold|Karat|Carat)?.*?₹\s*[\d,]+)',
                r'(₹\s*[\d,]+.*?\d+K?)',
                r'(\d+\s*(?:Karat|Carat).*?₹\s*[\d,]+)'
            ]
            
            found_rates = set()
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    clean_match = re.sub(r'\s+', ' ', match.strip())
                    if len(clean_match) < 100:  # Avoid long text
                        found_rates.add(clean_match)
            
            for rate in sorted(found_rates):
                print(f"  📊 {rate}")
            
            # Specifically look for 24 and 22 patterns
            k24_matches = re.findall(r'24K?.*?₹\s*([\d,]+)', page_source, re.IGNORECASE)
            k22_matches = re.findall(r'22K?.*?₹\s*([\d,]+)', page_source, re.IGNORECASE)
            
            if k24_matches:
                print(f"\n✅ Found 24K rates: {k24_matches}")
            if k22_matches:
                print(f"⚠️  Found 22K rates: {k22_matches}")
            
        except Exception as e:
            print(f"❌ Debug error: {e}")
    
    def check_and_notify(self, current_data):
        """Check for changes and send notifications"""
        try:
            # Load previous data
            previous_data = None
            if os.path.exists('data/latest_rate.json'):
                with open('data/latest_rate.json', 'r') as f:
                    previous_data = json.load(f)
            
            current_rate = current_data['rate']
            
            if previous_data:
                previous_rate = previous_data.get('rate', 0)
                change = current_rate - previous_rate
                change_percent = (change / previous_rate) * 100 if previous_rate > 0 else 0
                
                # Send notification for significant changes (>1% or >₹50)
                if abs(change) >= 50 or abs(change_percent) >= 1.0:
                    self.send_change_notification(current_rate, previous_rate, change, change_percent)
                else:
                    # Send regular update (less frequent)
                    print(f"Minor change: ₹{change:.2f} ({change_percent:.2f}%)")
            else:
                # First run
                self.send_initial_notification(current_rate)
                
        except Exception as e:
            print(f"Notification check error: {e}")
    
    def send_change_notification(self, current_rate, previous_rate, change, change_percent):
        """Send notification for significant rate changes"""
        
        direction = "📈 INCREASED" if change > 0 else "📉 DECREASED"
        emoji = "🚨" if abs(change_percent) >= 2 else "⚠️"
        
        message = f"""{emoji} Kerala 24K Gold Rate Alert!

{direction} by ₹{abs(change):.0f} ({abs(change_percent):.1f}%)

Previous: ₹{previous_rate:.0f}/g
Current: ₹{current_rate:.0f}/g

Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}
"""
        
        self.send_notifications(message, priority="high")
    
    def send_initial_notification(self, current_rate):
        """Send initial notification"""
        message = f"""🎉 Kerala 24K Gold Rate Tracker Started!

Current Rate: ₹{current_rate:.0f}/g
Monitoring started: {datetime.now().strftime('%d %b %Y, %I:%M %p')}

You'll receive alerts for changes ≥₹50 or ≥1%
"""
        
        self.send_notifications(message, priority="normal")
    
    def send_error_notification(self, error_msg):
        """Send error notification"""
        message = f"""❌ Gold Rate Tracker Error

{error_msg}

Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}
Please check the system.
"""
        
        self.send_notifications(message, priority="high")
    
    def send_notifications(self, message, priority="normal"):
        """Send notifications via multiple channels"""
        
        # 1. Telegram
        if self.telegram_token and self.telegram_chat_id:
            self.send_telegram(message)
        
        # 2. Pushover
        if self.pushover_token and self.pushover_user:
            self.send_pushover(message, priority)
        
        # 3. ntfy.sh (completely free)
        if self.ntfy_topic:
            self.send_ntfy(message, priority)
        
        # Always print to console
        print(f"📱 Notification: {message}")
    
    def send_telegram(self, message):
        """Send Telegram notification"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("✅ Telegram notification sent")
            else:
                print(f"❌ Telegram failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Telegram error: {e}")
    
    def send_pushover(self, message, priority):
        """Send Pushover notification"""
        try:
            priority_map = {"normal": 0, "high": 1}
            
            url = "https://api.pushover.net/1/messages.json"
            data = {
                'token': self.pushover_token,
                'user': self.pushover_user,
                'message': message,
                'title': 'Kerala 24K Gold Rate',
                'priority': priority_map.get(priority, 0)
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("✅ Pushover notification sent")
            else:
                print(f"❌ Pushover failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Pushover error: {e}")
    
    def send_ntfy(self, message, priority):
        """Send ntfy.sh notification (completely free!)"""
        try:
            url = f"https://ntfy.sh/{self.ntfy_topic}"
            
            headers = {
                'Title': 'Kerala 24K Gold Rate',
                'Priority': 'high' if priority == 'high' else 'default',
                'Tags': 'gold,money,alert' if priority == 'high' else 'gold,money'
            }
            
            response = requests.post(url, data=message, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ ntfy notification sent")
            else:
                print(f"❌ ntfy failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ ntfy error: {e}")
    
    def save_data(self, data):
        """Save data to files"""
        os.makedirs('data', exist_ok=True)
        
        # Save latest
        with open('data/latest_rate.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save to history
        history_file = 'data/rate_history.json'
        history = []
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        history.append(data)
        history = history[-100:]  # Keep last 100 entries
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

if __name__ == "__main__":
    scraper = GoldScraperWithNotifications()
    result = scraper.scrape_rate()
    
    if result:
        print(f"✅ Final Result: ₹{result['rate']} per gram (24K)")
    else:
        print("❌ Failed to scrape 24K gold rate")