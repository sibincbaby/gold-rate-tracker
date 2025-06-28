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
            print("🔍 Scraping Kerala gold rate...")
            self.driver.get(self.url)
            time.sleep(3)
            
            rate = self.extract_rate()
            
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
                
                print(f"✅ Success: ₹{rate} per gram")
                return current_data
            else:
                self.send_error_notification("Failed to scrape gold rate")
                return None
                
        except Exception as e:
            self.send_error_notification(f"Scraping error: {str(e)}")
            return None
        finally:
            self.driver.quit()
    
    def extract_rate(self):
        """Extract gold rate from page"""
        try:
            # Method 1: Look for 24K elements
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '24K') or contains(text(), '24k')]")
            for element in elements:
                text = element.text
                if '₹' in text:
                    match = re.search(r'₹\s*([\d,]+)', text)
                    if match:
                        return float(match.group(1).replace(',', ''))
                
                # Check parent
                try:
                    parent_text = element.find_element(By.XPATH, "..").text
                    if '₹' in parent_text:
                        match = re.search(r'₹\s*([\d,]+)', parent_text)
                        if match:
                            return float(match.group(1).replace(',', ''))
                except:
                    pass
            
            # Method 2: Search page source
            page_source = self.driver.page_source
            patterns = [
                r'24K Gold.*?/g.*?₹\s*([\d,]+)',
                r'24\s*karat.*?₹\s*([\d,]+)',
                r'24\s*[kK].*?₹\s*([\d,]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if match:
                    return float(match.group(1).replace(',', ''))
            
        except Exception as e:
            print(f"Extraction error: {e}")
        
        return None
    
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
        
        message = f"""{emoji} Kerala Gold Rate Alert!

{direction} by ₹{abs(change):.0f} ({abs(change_percent):.1f}%)

Previous: ₹{previous_rate:.0f}/g
Current: ₹{current_rate:.0f}/g

Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}
"""
        
        self.send_notifications(message, priority="high")
    
    def send_initial_notification(self, current_rate):
        """Send initial notification"""
        message = f"""🎉 Gold Rate Tracker Started!

Kerala 24K Gold Rate: ₹{current_rate:.0f}/g
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
                'title': 'Kerala Gold Rate',
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
                'Title': 'Kerala Gold Rate',
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
        print(f"✅ Final Result: ₹{result['rate']} per gram")
    else:
        print("❌ Scraping failed")