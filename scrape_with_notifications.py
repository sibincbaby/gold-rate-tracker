"""
🥇 CONFIGURABLE KERALA GOLD RATE TRACKER
Configure all thresholds and settings at the top of this file
"""

# ================================================================================================
# 🔧 CONFIGURATION SECTION - EDIT THESE VALUES TO CUSTOMIZE YOUR TRACKER
# ================================================================================================

# 📱 NOTIFICATION THRESHOLDS (₹ and %)
AKGSMA_THRESHOLD_RUPEES = 10      # ₹10 change during AKGSMA morning (9-11 AM)
AKGSMA_THRESHOLD_PERCENT = 0.1    # 0.1% change during AKGSMA morning

EVENING_THRESHOLD_RUPEES = 10     # ₹10 change during evening updates (6-7 PM)
EVENING_THRESHOLD_PERCENT = 0.1   # 0.1% change during evening updates

TRADING_THRESHOLD_RUPEES = 15     # ₹15 change during trading hours (11 AM-6 PM)
TRADING_THRESHOLD_PERCENT = 0.15  # 0.15% change during trading hours

OFFHOURS_THRESHOLD_RUPEES = 20    # ₹20 change during off hours (7 PM-9 AM)
OFFHOURS_THRESHOLD_PERCENT = 0.2  # 0.2% change during off hours

# 🔄 MICRO ALERTS (Very small changes during active periods)
MICRO_ALERT_RUPEES = 5           # ₹5 micro alerts during AKGSMA/Evening
ENABLE_MICRO_ALERTS = True       # Set False to disable micro alerts

# ⚡ RAPID MOVEMENT DETECTION
RAPID_MOVEMENT_THRESHOLD = 5     # ₹5 change for rapid movement detection
RAPID_MOVEMENT_WINDOW_MINUTES = 20  # Within 20 minutes = rapid movement
ENABLE_RAPID_ALERTS = True       # Set False to disable rapid movement alerts

# 📈 TREND REVERSAL DETECTION
TREND_REVERSAL_THRESHOLD = 5     # ₹5 minimum for trend reversal alerts
ENABLE_TREND_ALERTS = True       # Set False to disable trend reversal alerts

# ⏸️ STABILITY ALERTS (No change notifications)
STABILITY_ALERT_MINUTES = 45     # Alert if no change for 45+ minutes during active periods
ENABLE_STABILITY_ALERTS = True   # Set False to disable stability alerts

# 📊 HOURLY REPORTS
ENABLE_HOURLY_REPORTS = True     # Set False to disable hourly trend reports
HOURLY_REPORT_PERIODS = ["AKGSMA_MORNING_RUSH", "ACTIVE_TRADING", "EVENING_UPDATE"]

# 🚨 PRIORITY LEVELS (when to send high priority vs normal)
HIGH_PRIORITY_RUPEES = 25        # ₹25+ = High priority notification
HIGH_PRIORITY_PERCENT = 0.5      # 0.5%+ = High priority notification

# ⏰ TIME ZONE SETTINGS
IST_OFFSET_HOURS = 5             # IST = UTC + 5:30
IST_OFFSET_MINUTES = 30

# 🕐 MARKET PERIOD DEFINITIONS (IST hours)
AKGSMA_START_HOUR = 9            # AKGSMA period starts at 9 AM IST
AKGSMA_END_HOUR = 11             # AKGSMA period ends at 11 AM IST

TRADING_START_HOUR = 11          # Trading period starts at 11 AM IST  
TRADING_END_HOUR = 18            # Trading period ends at 6 PM IST

EVENING_START_HOUR = 18          # Evening updates start at 6 PM IST
EVENING_END_HOUR = 19            # Evening updates end at 7 PM IST

# 📊 DATA RETENTION
HISTORY_ENTRIES_TO_KEEP = 500    # Number of historical entries to keep
ANALYSIS_ENTRIES_FOR_TREND = 3   # Number of entries to check for trend reversal

# 🌐 SCRAPING SETTINGS
SCRAPING_DELAY_MIN = 1.5         # Minimum delay between requests (seconds)
SCRAPING_DELAY_MAX = 3.0         # Maximum delay between requests (seconds)
PAGE_LOAD_DELAY_MIN = 2.0        # Minimum page load wait time
PAGE_LOAD_DELAY_MAX = 3.0        # Maximum page load wait time

# 🏷️ NOTIFICATION CUSTOMIZATION
NOTIFICATION_TITLE = "Kerala 24K Gold Tracker"
ENABLE_EMOJI_IN_MESSAGES = True
INCLUDE_PERIOD_CONTEXT = True

# 🔍 WEEKEND SETTINGS
WEEKEND_THRESHOLD_RUPEES = 30
WEEKEND_THRESHOLD_PERCENT = 0.3
ENABLE_WEEKEND_REDUCED_SENSITIVITY = True

# ================================================================================================
# 🚀 TRACKER CODE STARTS HERE
# ================================================================================================

import json
import os
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

class ConfigurableKeralaGoldTracker:
    def __init__(self):
        self.url = "https://www.goodreturns.in/gold-rates/kerala.html"
        self.setup_driver()
        
        # Notification settings from environment
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.pushover_token = os.environ.get('PUSHOVER_TOKEN')
        self.pushover_user = os.environ.get('PUSHOVER_USER')
        self.ntfy_topic = os.environ.get('NTFY_TOPIC')
        
        # Calculate current time and period
        self.ist_time = datetime.now() + timedelta(hours=IST_OFFSET_HOURS, minutes=IST_OFFSET_MINUTES)
        self.current_period = self.get_current_period()
        self.is_weekend = self.ist_time.weekday() >= 5
        
        print(f"🔧 Configured Tracker Initialized")
        print(f"⏰ IST Time: {self.ist_time.strftime('%d %b %Y, %I:%M %p')}")
        print(f"📊 Period: {self.current_period}")
        print(f"📅 Weekend Mode: {self.is_weekend}")
    
    def setup_driver(self):
        """Setup Chrome driver with configured delays"""
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
        
        import random
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def get_current_period(self):
        """Determine current market period using configured hours"""
        hour = self.ist_time.hour
        
        if AKGSMA_START_HOUR <= hour < AKGSMA_END_HOUR:
            return "AKGSMA_MORNING_RUSH"
        elif TRADING_START_HOUR <= hour < TRADING_END_HOUR:
            return "ACTIVE_TRADING"
        elif EVENING_START_HOUR <= hour < EVENING_END_HOUR:
            return "EVENING_UPDATE"
        else:
            return "OFF_HOURS"
    
    def get_thresholds_for_period(self, period):
        """Get notification thresholds based on current period and configuration"""
        
        # Apply weekend adjustments if enabled
        weekend_multiplier = 1.0
        if self.is_weekend and ENABLE_WEEKEND_REDUCED_SENSITIVITY:
            weekend_multiplier = WEEKEND_THRESHOLD_RUPEES / TRADING_THRESHOLD_RUPEES
        
        if period == "AKGSMA_MORNING_RUSH":
            return {
                'rupees': AKGSMA_THRESHOLD_RUPEES * weekend_multiplier,
                'percent': AKGSMA_THRESHOLD_PERCENT * weekend_multiplier,
                'micro_rupees': MICRO_ALERT_RUPEES if ENABLE_MICRO_ALERTS else 999
            }
        elif period == "EVENING_UPDATE":
            return {
                'rupees': EVENING_THRESHOLD_RUPEES * weekend_multiplier,
                'percent': EVENING_THRESHOLD_PERCENT * weekend_multiplier,
                'micro_rupees': MICRO_ALERT_RUPEES if ENABLE_MICRO_ALERTS else 999
            }
        elif period == "ACTIVE_TRADING":
            return {
                'rupees': TRADING_THRESHOLD_RUPEES * weekend_multiplier,
                'percent': TRADING_THRESHOLD_PERCENT * weekend_multiplier,
                'micro_rupees': 999
            }
        else:  # OFF_HOURS
            return {
                'rupees': OFFHOURS_THRESHOLD_RUPEES * weekend_multiplier,
                'percent': OFFHOURS_THRESHOLD_PERCENT * weekend_multiplier,
                'micro_rupees': 999
            }
    
    def scrape_rate(self):
        """Main scraping function with configured delays"""
        try:
            print(f"🔍 Kerala Gold Tracker - Period: {self.current_period}")
            print(f"⚙️ Using thresholds: {self.get_thresholds_for_period(self.current_period)}")
            
            # Use configured delays
            import random
            time.sleep(random.uniform(SCRAPING_DELAY_MIN, SCRAPING_DELAY_MAX))
            
            self.driver.get(self.url)
            time.sleep(random.uniform(PAGE_LOAD_DELAY_MIN, PAGE_LOAD_DELAY_MAX))
            
            rate = self.extract_24k_rate()
            
            if rate:
                current_data = {
                    'rate': rate,
                    'currency': 'INR',
                    'unit': 'per gram',
                    'purity': '24K',
                    'location': 'Kerala',
                    'timestamp': datetime.now().isoformat(),
                    'ist_time': self.ist_time.isoformat(),
                    'source': self.url,
                    'success': True,
                    'market_period': self.current_period,
                    'is_weekend': self.is_weekend
                }
                
                # Apply configured notification logic
                self.check_and_notify_configured(current_data)
                
                self.save_data(current_data)
                
                print(f"✅ Rate: ₹{rate} - {self.current_period}")
                return current_data
            else:
                self.send_error_notification(f"Failed during {self.current_period}")
                return None
                
        except Exception as e:
            print(f"❌ Pushover error: {e}")
    
    def send_ntfy(self, message, priority):
        """Send ntfy.sh notification"""
        try:
            url = f"https://ntfy.sh/{self.ntfy_topic}"
            
            priority_map = {"low": "min", "normal": "default", "high": "high"}
            
            if ENABLE_EMOJI_IN_MESSAGES:
                tags = "gold,kerala,fire,money" if priority == "high" else "gold,kerala,chart_with_upwards_trend"
            else:
                tags = "gold,kerala"
            
            headers = {
                'Title': NOTIFICATION_TITLE,
                'Priority': priority_map.get(priority, "default"),
                'Tags': tags
            }
            
            response = requests.post(url, data=message, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ ntfy sent")
            else:
                print(f"❌ ntfy failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ ntfy error: {e}")
    
    def save_data(self, data):
        """Save data with configured retention settings"""
        os.makedirs('data', exist_ok=True)
        
        # Save latest
        with open('data/latest_rate.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save to history with configured retention
        history_file = 'data/rate_history.json'
        history = []
        
        if os.path.exists(history_file):
            with open('data/rate_history.json', 'r') as f:
                history = json.load(f)
        
        history.append(data)
        history = history[-HISTORY_ENTRIES_TO_KEEP:]
        
        with open('data/rate_history.json', 'w') as f:
            json.dump(history, f, indent=2)
        
        # Save configuration summary for reference
        config_summary = {
            'last_updated': data['timestamp'],
            'thresholds': {
                'akgsma_rupees': AKGSMA_THRESHOLD_RUPEES,
                'akgsma_percent': AKGSMA_THRESHOLD_PERCENT,
                'evening_rupees': EVENING_THRESHOLD_RUPEES,
                'evening_percent': EVENING_THRESHOLD_PERCENT,
                'trading_rupees': TRADING_THRESHOLD_RUPEES,
                'trading_percent': TRADING_THRESHOLD_PERCENT,
                'offhours_rupees': OFFHOURS_THRESHOLD_RUPEES,
                'offhours_percent': OFFHOURS_THRESHOLD_PERCENT,
                'micro_alerts': MICRO_ALERT_RUPEES if ENABLE_MICRO_ALERTS else 'disabled',
                'rapid_alerts': RAPID_MOVEMENT_THRESHOLD if ENABLE_RAPID_ALERTS else 'disabled'
            },
            'features': {
                'micro_alerts': ENABLE_MICRO_ALERTS,
                'rapid_alerts': ENABLE_RAPID_ALERTS,
                'trend_alerts': ENABLE_TREND_ALERTS,
                'stability_alerts': ENABLE_STABILITY_ALERTS,
                'hourly_reports': ENABLE_HOURLY_REPORTS,
                'weekend_reduced_sensitivity': ENABLE_WEEKEND_REDUCED_SENSITIVITY
            },
            'current_period': data['market_period'],
            'is_weekend': data['is_weekend']
        }
        
        with open('data/config_summary.json', 'w') as f:
            json.dump(config_summary, f, indent=2)

if __name__ == "__main__":
    print("🔧 Starting Configurable Kerala Gold Tracker...")
    print("=" * 60)
    print("📊 CURRENT CONFIGURATION:")
    print(f"• AKGSMA Threshold: ≥₹{AKGSMA_THRESHOLD_RUPEES} ({AKGSMA_THRESHOLD_PERCENT}%)")
    print(f"• Evening Threshold: ≥₹{EVENING_THRESHOLD_RUPEES} ({EVENING_THRESHOLD_PERCENT}%)")
    print(f"• Trading Threshold: ≥₹{TRADING_THRESHOLD_RUPEES} ({TRADING_THRESHOLD_PERCENT}%)")
    print(f"• Off Hours Threshold: ≥₹{OFFHOURS_THRESHOLD_RUPEES} ({OFFHOURS_THRESHOLD_PERCENT}%)")
    print(f"• Micro Alerts: {'✅ Enabled' if ENABLE_MICRO_ALERTS else '❌ Disabled'} (≥₹{MICRO_ALERT_RUPEES})")
    print(f"• Rapid Alerts: {'✅ Enabled' if ENABLE_RAPID_ALERTS else '❌ Disabled'} (≥₹{RAPID_MOVEMENT_THRESHOLD} in {RAPID_MOVEMENT_WINDOW_MINUTES}min)")
    print(f"• Trend Alerts: {'✅ Enabled' if ENABLE_TREND_ALERTS else '❌ Disabled'} (≥₹{TREND_REVERSAL_THRESHOLD})")
    print(f"• Stability Alerts: {'✅ Enabled' if ENABLE_STABILITY_ALERTS else '❌ Disabled'} ({STABILITY_ALERT_MINUTES}min)")
    print(f"• Hourly Reports: {'✅ Enabled' if ENABLE_HOURLY_REPORTS else '❌ Disabled'}")
    print("=" * 60)
    
    tracker = ConfigurableKeralaGoldTracker()
    result = tracker.scrape_rate()
    
    if result:
        print(f"✅ Success: ₹{result['rate']} - {result['market_period']}")
        print(f"📊 Weekend Mode: {result['is_weekend']}")
    else:
        print("❌ Tracking failed")
    
    print("\n🔧 To customize alerts, edit the configuration variables at the top of this file!"):
            self.send_error_notification(f"Error ({self.current_period}): {str(e)}")
            return None
        finally:
            self.driver.quit()
    
    def extract_24k_rate(self):
        """Extract 24K rate from page"""
        try:
            page_source = self.driver.page_source
            
            # Try multiple patterns for Kerala 24K gold
            patterns = [
                r'24K\s+Gold\s*/g.*?₹\s*([\d,]+)',
                r'Kerala.*?24K.*?₹\s*([\d,]+)',
                r'24K.*?₹\s*([\d,]+)',
                r'24\s*Karat.*?₹\s*([\d,]+)',
                r'24k.*?₹\s*([\d,]+)'
            ]
            
            for i, pattern in enumerate(patterns, 1):
                match = re.search(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if match:
                    rate = float(match.group(1).replace(',', ''))
                    print(f"✅ Found via pattern {i}: ₹{rate}")
                    return rate
            
            # Element-based extraction as fallback
            elements_24k = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'k', 'K'), '24K')]")
            
            for element in elements_24k:
                text = element.text
                if '₹' in text:
                    match = re.search(r'₹\s*([\d,]+)', text)
                    if match:
                        rate = float(match.group(1).replace(',', ''))
                        print(f"✅ Found in element: ₹{rate}")
                        return rate
                
                try:
                    parent = element.find_element(By.XPATH, "..")
                    parent_text = parent.text
                    if '₹' in parent_text and '24K' in parent_text:
                        match = re.search(r'₹\s*([\d,]+)', parent_text)
                        if match:
                            rate = float(match.group(1).replace(',', ''))
                            print(f"✅ Found in parent: ₹{rate}")
                            return rate
                except:
                    pass
            
        except Exception as e:
            print(f"❌ Extraction error: {e}")
        
        return None
    
    def check_and_notify_configured(self, current_data):
        """Notification logic using configured thresholds"""
        try:
            previous_data = None
            if os.path.exists('data/latest_rate.json'):
                with open('data/latest_rate.json', 'r') as f:
                    previous_data = json.load(f)
            
            current_rate = current_data['rate']
            current_period = current_data['market_period']
            
            if previous_data:
                previous_rate = previous_data.get('rate', 0)
                change = current_rate - previous_rate
                change_percent = (change / previous_rate) * 100 if previous_rate > 0 else 0
                
                # Get time since last change
                previous_time = datetime.fromisoformat(previous_data.get('timestamp', ''))
                time_diff = datetime.now() - previous_time
                minutes_since_last = time_diff.total_seconds() / 60
                
                # Get configured thresholds for current period
                thresholds = self.get_thresholds_for_period(current_period)
                
                should_notify = False
                priority = "normal"
                notification_type = ""
                
                # Main threshold check
                if abs(change) >= thresholds['rupees'] or abs(change_percent) >= thresholds['percent']:
                    should_notify = True
                    priority = "high" if (abs(change) >= HIGH_PRIORITY_RUPEES or abs(change_percent) >= HIGH_PRIORITY_PERCENT) else "normal"
                    notification_type = f"📊 Main Alert ({current_period.replace('_', ' ').title()})"
                    print(f"📊 Main alert: ₹{change:.0f} (threshold: ₹{thresholds['rupees']:.0f})")
                
                # Micro alerts
                elif ENABLE_MICRO_ALERTS and abs(change) >= thresholds['micro_rupees']:
                    should_notify = True
                    priority = "low"
                    notification_type = "📱 Micro Alert"
                    print(f"📱 Micro alert: ₹{change:.0f}")
                
                # Rapid movement detection
                elif ENABLE_RAPID_ALERTS and minutes_since_last <= RAPID_MOVEMENT_WINDOW_MINUTES and abs(change) >= RAPID_MOVEMENT_THRESHOLD:
                    should_notify = True
                    priority = "high"
                    notification_type = "⚡ Rapid Movement"
                    print(f"⚡ Rapid movement: ₹{change:.0f} in {minutes_since_last:.0f} min")
                
                # Trend reversal detection
                elif ENABLE_TREND_ALERTS:
                    direction_change = self.detect_direction_change(current_rate)
                    if direction_change and abs(change) >= TREND_REVERSAL_THRESHOLD:
                        should_notify = True
                        priority = "normal"
                        notification_type = f"🔄 Trend Reversal ({direction_change})"
                        print(f"🔄 Trend reversal: {direction_change}")
                
                # Stability alerts
                elif ENABLE_STABILITY_ALERTS and change == 0 and minutes_since_last >= STABILITY_ALERT_MINUTES:
                    if current_period in ["AKGSMA_MORNING_RUSH", "EVENING_UPDATE"]:
                        should_notify = True
                        priority = "low"
                        notification_type = "⏸️ Rate Stability"
                        print(f"⏸️ Stability: No change for {minutes_since_last:.0f} minutes")
                
                else:
                    print(f"🔕 No alert: ₹{change:.2f} ({change_percent:.3f}%) - Threshold: ₹{thresholds['rupees']:.0f}")
                
                # Send notification if criteria met
                if should_notify:
                    self.send_configured_alert(
                        current_rate, previous_rate, change, change_percent, 
                        priority, notification_type, current_period, minutes_since_last
                    )
                
                # Hourly reports
                if ENABLE_HOURLY_REPORTS and self.should_send_hourly_update():
                    self.send_hourly_trend_update()
                    
            else:
                # First run
                self.send_initial_notification(current_rate, current_period)
                
        except Exception as e:
            print(f"Configured notification error: {e}")
    
    def detect_direction_change(self, current_rate):
        """Detect trend reversals using configured parameters"""
        try:
            if os.path.exists('data/rate_history.json'):
                with open('data/rate_history.json', 'r') as f:
                    history = json.load(f)
                
                if len(history) >= ANALYSIS_ENTRIES_FOR_TREND:
                    recent_rates = [entry['rate'] for entry in history[-ANALYSIS_ENTRIES_FOR_TREND:]]
                    recent_rates.append(current_rate)
                    
                    if len(recent_rates) >= 3:
                        trend_1 = "up" if recent_rates[1] > recent_rates[0] else "down"
                        trend_2 = "up" if recent_rates[2] > recent_rates[1] else "down"
                        trend_3 = "up" if recent_rates[3] > recent_rates[2] else "down"
                        
                        if trend_1 == trend_2 and trend_2 != trend_3:
                            return f"{trend_2} → {trend_3}"
        except:
            pass
        
        return None
    
    def should_send_hourly_update(self):
        """Check if should send hourly update based on configuration"""
        if not ENABLE_HOURLY_REPORTS:
            return False
            
        if self.current_period not in HOURLY_REPORT_PERIODS:
            return False
        
        if self.ist_time.minute <= 5:
            try:
                os.makedirs('data', exist_ok=True)
                hour_key = self.ist_time.strftime('%Y-%m-%d-%H')
                
                with open('data/last_hourly.txt', 'r') as f:
                    last_hourly = f.read().strip()
                    if last_hourly == hour_key:
                        return False
            except:
                pass
            
            with open('data/last_hourly.txt', 'w') as f:
                f.write(hour_key)
            
            return True
        
        return False
    
    def send_configured_alert(self, current_rate, previous_rate, change, change_percent, priority, notification_type, period, minutes_since):
        """Send alert using configured message format"""
        
        if ENABLE_EMOJI_IN_MESSAGES:
            direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            period_emoji = {"AKGSMA_MORNING_RUSH": "🌅", "EVENING_UPDATE": "🌆", "ACTIVE_TRADING": "📊", "OFF_HOURS": "🌙"}
            emoji = period_emoji.get(period, "📈")
        else:
            direction = "UP" if change > 0 else "DOWN" if change < 0 else "STABLE"
            emoji = ""
        
        if abs(change) == 0:
            message = f"""{emoji} {NOTIFICATION_TITLE}
            
{direction} NO CHANGE for {minutes_since:.0f} minutes
Current: ₹{current_rate:.0f}/g
Type: {notification_type}
Time: {self.ist_time.strftime('%I:%M %p IST')}"""
            
            if INCLUDE_PERIOD_CONTEXT:
                message += f"\n\n💡 Stability during {period.lower().replace('_', ' ')} noted."
        else:
            if abs(change) >= 50:
                magnitude = "MAJOR"
            elif abs(change) >= 25:
                magnitude = "SIGNIFICANT"
            elif abs(change) >= 10:
                magnitude = "MODERATE"
            else:
                magnitude = "MINOR"
            
            message = f"""{emoji} {NOTIFICATION_TITLE}

{direction} {magnitude}: ₹{abs(change):.0f} ({abs(change_percent):.2f}%)

Previous: ₹{previous_rate:.0f}/g
Current: ₹{current_rate:.0f}/g
Change: ₹{change:+.0f}

Type: {notification_type}
Gap: {minutes_since:.0f} min
Time: {self.ist_time.strftime('%I:%M %p IST')}"""
            
            if INCLUDE_PERIOD_CONTEXT:
                message += f"\n\n🎯 Period: {period.lower().replace('_', ' ')}"
        
        self.send_notifications(message, priority)
    
    def send_hourly_trend_update(self):
        """Send hourly trend report if enabled"""
        try:
            hourly_data = self.get_last_hour_data()
            
            if hourly_data and len(hourly_data) >= 2:
                rates = [entry['rate'] for entry in hourly_data]
                
                hourly_high = max(rates)
                hourly_low = min(rates)
                hourly_volatility = hourly_high - hourly_low
                
                opening_rate = rates[0]
                current_rate = rates[-1]
                hourly_change = current_rate - opening_rate
                
                if hourly_change > 10:
                    trend = "📈 BULLISH" if ENABLE_EMOJI_IN_MESSAGES else "BULLISH"
                elif hourly_change < -10:
                    trend = "📉 BEARISH" if ENABLE_EMOJI_IN_MESSAGES else "BEARISH"
                else:
                    trend = "➡️ STABLE" if ENABLE_EMOJI_IN_MESSAGES else "STABLE"
                
                emoji = "📊 " if ENABLE_EMOJI_IN_MESSAGES else ""
                
                message = f"""{emoji}Hourly Gold Trend Report

{trend} Hour: {self.ist_time.strftime('%I:00 %p IST')}

Hourly Performance:
• Opening: ₹{opening_rate:.0f}/g
• Current: ₹{current_rate:.0f}/g  
• High: ₹{hourly_high:.0f}/g
• Low: ₹{hourly_low:.0f}/g
• Change: ₹{hourly_change:+.0f} ({(hourly_change/opening_rate)*100:+.2f}%)
• Volatility: ₹{hourly_volatility:.0f}

Activity: {len(hourly_data)} updates this hour
Period: {self.current_period.replace('_', ' ').title()}"""
                
                self.send_notifications(message, priority="low")
        except Exception as e:
            print(f"Hourly update error: {e}")
    
    def get_last_hour_data(self):
        """Get data from last hour"""
        try:
            if os.path.exists('data/rate_history.json'):
                with open('data/rate_history.json', 'r') as f:
                    history = json.load(f)
                
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_data = []
                
                for entry in reversed(history):
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    if entry_time >= one_hour_ago:
                        recent_data.append(entry)
                
                return list(reversed(recent_data))
        except:
            pass
        
        return []
    
    def send_initial_notification(self, current_rate, period):
        """Send initial setup notification with current configuration"""
        emoji = "🚀 " if ENABLE_EMOJI_IN_MESSAGES else ""
        
        message = f"""{emoji}{NOTIFICATION_TITLE} Started!

Current Rate: ₹{current_rate:.0f}/g
Period: {period.replace('_', ' ').title()}
Time: {self.ist_time.strftime('%d %b, %I:%M %p IST')}
Weekend Mode: {self.is_weekend}

🔧 CONFIGURED THRESHOLDS:
• AKGSMA (9-11 AM): ≥₹{AKGSMA_THRESHOLD_RUPEES} ({AKGSMA_THRESHOLD_PERCENT}%)
• Evening (6-7 PM): ≥₹{EVENING_THRESHOLD_RUPEES} ({EVENING_THRESHOLD_PERCENT}%)
• Trading (11 AM-6 PM): ≥₹{TRADING_THRESHOLD_RUPEES} ({TRADING_THRESHOLD_PERCENT}%)
• Off Hours: ≥₹{OFFHOURS_THRESHOLD_RUPEES} ({OFFHOURS_THRESHOLD_PERCENT}%)

⚡ SPECIAL FEATURES:
• Micro Alerts: {'Enabled' if ENABLE_MICRO_ALERTS else 'Disabled'} (≥₹{MICRO_ALERT_RUPEES})
• Rapid Movement: {'Enabled' if ENABLE_RAPID_ALERTS else 'Disabled'} (≥₹{RAPID_MOVEMENT_THRESHOLD} in {RAPID_MOVEMENT_WINDOW_MINUTES}min)
• Trend Reversals: {'Enabled' if ENABLE_TREND_ALERTS else 'Disabled'} (≥₹{TREND_REVERSAL_THRESHOLD})
• Stability Alerts: {'Enabled' if ENABLE_STABILITY_ALERTS else 'Disabled'} ({STABILITY_ALERT_MINUTES}min)
• Hourly Reports: {'Enabled' if ENABLE_HOURLY_REPORTS else 'Disabled'}

🔧 Easy to customize by editing the configuration variables at the top of the script!"""
        
        self.send_notifications(message, priority="normal")
    
    def send_error_notification(self, error_msg):
        """Send error notification"""
        emoji = "❌ " if ENABLE_EMOJI_IN_MESSAGES else ""
        
        message = f"""{emoji}{NOTIFICATION_TITLE} Error

{error_msg}

Period: {self.current_period}
Time: {self.ist_time.strftime('%I:%M %p IST')}
Weekend: {self.is_weekend}

Will retry on next scheduled run."""
        
        self.send_notifications(message, priority="high")
    
    def send_notifications(self, message, priority="normal"):
        """Send notifications via configured channels"""
        
        if self.telegram_token and self.telegram_chat_id:
            self.send_telegram(message)
        
        if self.pushover_token and self.pushover_user:
            self.send_pushover(message, priority)
        
        if self.ntfy_topic:
            self.send_ntfy(message, priority)
        
        print(f"📱 Alert ({priority}): {message[:80]}...")
    
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
                print("✅ Telegram sent")
            else:
                print(f"❌ Telegram failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Telegram error: {e}")
    
    def send_pushover(self, message, priority):
        """Send Pushover notification"""
        try:
            priority_map = {"low": -1, "normal": 0, "high": 1}
            
            url = "https://api.pushover.net/1/messages.json"
            data = {
                'token': self.pushover_token,
                'user': self.pushover_user,
                'message': message,
                'title': NOTIFICATION_TITLE,
                'priority': priority_map.get(priority, 0)
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("✅ Pushover sent")
            else:
                print(f"❌ Pushover failed: {response.status_code}")
                
        except Exception as e