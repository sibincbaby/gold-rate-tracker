"""
🥇 CONFIGURABLE KERALA GOLD RATE TRACKER - PRODUCTION READY VERSION
Configure all thresholds and settings at the top of this file
Features proper IST timezone handling and enhanced functionality
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

# 🏖️ INDIAN HOLIDAYS (Gold markets closed)
INDIAN_HOLIDAYS_2025 = [
    "2025-01-26",  # Republic Day
    "2025-03-14",  # Holi
    "2025-04-14",  # Ram Navami
    "2025-04-18",  # Good Friday
    "2025-05-01",  # Labour Day
    "2025-08-15",  # Independence Day
    "2025-08-16",  # Janmashtami
    "2025-09-07",  # Ganesh Chaturthi
    "2025-10-02",  # Gandhi Jayanti
    "2025-10-20",  # Dussehra
    "2025-11-01",  # Diwali
    "2025-11-05",  # Bhai Dooj
    "2025-12-25",  # Christmas
]

# 🔧 SELENIUM SETTINGS
USE_WEBDRIVER_MANAGER = True     # Auto-download Chrome driver
CHROME_HEADLESS = True           # Run Chrome in headless mode
CHROME_NO_SANDBOX = True         # Required for some environments

# ================================================================================================
# 🚀 TRACKER CODE STARTS HERE
# ================================================================================================

# Standard library imports
import json
import os
import re
import time
import random
from datetime import datetime, timedelta

# Third-party imports
import pytz
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Optional: Auto Chrome driver management
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    print("⚠️  webdriver-manager not installed. Using system Chrome driver.")

def validate_configuration():
    """Validate configuration values"""
    errors = []
    
    # Validate thresholds
    if AKGSMA_THRESHOLD_RUPEES <= 0:
        errors.append("AKGSMA_THRESHOLD_RUPEES must be positive")
    if not (0 <= AKGSMA_THRESHOLD_PERCENT <= 100):
        errors.append("AKGSMA_THRESHOLD_PERCENT must be between 0 and 100")
    
    # Validate hours
    if not (0 <= AKGSMA_START_HOUR <= 23):
        errors.append("AKGSMA_START_HOUR must be between 0 and 23")
    if AKGSMA_START_HOUR >= AKGSMA_END_HOUR:
        errors.append("AKGSMA_START_HOUR must be less than AKGSMA_END_HOUR")
    
    # Validate delays
    if SCRAPING_DELAY_MIN >= SCRAPING_DELAY_MAX:
        errors.append("SCRAPING_DELAY_MIN must be less than SCRAPING_DELAY_MAX")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True

class ImprovedTimeHandling:
    """Handles proper IST timezone management with validation"""
    
    def __init__(self):
        try:
            self.ist_tz = pytz.timezone('Asia/Kolkata')
            self.utc_tz = pytz.UTC
            # Test timezone functionality
            test_time = self.get_current_ist()
            if test_time is None:
                raise ValueError("Timezone initialization failed")
        except Exception as e:
            print(f"❌ Timezone initialization error: {e}")
            raise
        
    def get_current_ist(self):
        """Get current time in IST using proper timezone handling"""
        try:
            utc_now = datetime.now(self.utc_tz)
            ist_now = utc_now.astimezone(self.ist_tz)
            return ist_now
        except Exception as e:
            print(f"❌ Error getting IST time: {e}")
            return None
    
    def get_current_period(self):
        """Determine current market period using IST"""
        ist_time = self.get_current_ist()
        if ist_time is None:
            return "UNKNOWN"
            
        hour = ist_time.hour
        
        if AKGSMA_START_HOUR <= hour < AKGSMA_END_HOUR:
            return "AKGSMA_MORNING_RUSH"
        elif TRADING_START_HOUR <= hour < TRADING_END_HOUR:
            return "ACTIVE_TRADING"
        elif EVENING_START_HOUR <= hour < EVENING_END_HOUR:
            return "EVENING_UPDATE"
        else:
            return "OFF_HOURS"
    
    def is_market_day(self):
        """Check if today is a trading day (Monday-Friday, excluding holidays)"""
        ist_time = self.get_current_ist()
        if ist_time is None:
            return False
        
        # Check if it's a weekend (Saturday=5, Sunday=6)
        if ist_time.weekday() >= 5:
            return False
        
        # Check if it's a holiday
        date_str = ist_time.strftime('%Y-%m-%d')
        if date_str in INDIAN_HOLIDAYS_2025:
            return False
        
        return True
    
    def get_next_market_open(self):
        """Get next market opening time in IST"""
        ist_time = self.get_current_ist()
        if ist_time is None:
            return None
        
        # If it's before 9 AM today and it's a market day
        if ist_time.hour < AKGSMA_START_HOUR and self.is_market_day():
            next_open = ist_time.replace(hour=AKGSMA_START_HOUR, minute=0, second=0, microsecond=0)
        else:
            # Find next business day at 9 AM
            days_ahead = 1
            next_day = ist_time + timedelta(days=days_ahead)
            
            while not self._is_market_day_for_date(next_day):
                days_ahead += 1
                next_day = ist_time + timedelta(days=days_ahead)
                # Prevent infinite loop
                if days_ahead > 10:
                    break
            
            next_open = next_day.replace(hour=AKGSMA_START_HOUR, minute=0, second=0, microsecond=0)
        
        return next_open
    
    def _is_market_day_for_date(self, date_obj):
        """Check if a specific date is a market day"""
        if date_obj.weekday() >= 5:
            return False
        
        date_str = date_obj.strftime('%Y-%m-%d')
        if date_str in INDIAN_HOLIDAYS_2025:
            return False
        
        return True
    
    def format_ist_time(self, dt=None):
        """Format IST time for display"""
        if dt is None:
            dt = self.get_current_ist()
        if dt is None:
            return "Unknown Time"
        return dt.strftime('%d %b %Y, %I:%M:%S %p IST')
    
    def get_market_status(self):
        """Get comprehensive market status"""
        ist_time = self.get_current_ist()
        if ist_time is None:
            return {
                'error': 'Unable to get IST time',
                'current_ist': None,
                'formatted_time': 'Unknown',
                'period': 'UNKNOWN',
                'is_trading_day': False,
                'is_market_hours': False,
                'next_market_open': None,
                'is_holiday': False
            }
        
        period = self.get_current_period()
        is_trading_day = self.is_market_day()
        
        status = {
            'current_ist': ist_time,
            'formatted_time': self.format_ist_time(ist_time),
            'period': period,
            'is_trading_day': is_trading_day,
            'is_market_hours': period in ['AKGSMA_MORNING_RUSH', 'ACTIVE_TRADING', 'EVENING_UPDATE'] and is_trading_day,
            'next_market_open': self.get_next_market_open(),
            'is_holiday': ist_time.strftime('%Y-%m-%d') in INDIAN_HOLIDAYS_2025
        }
        
        return status

class ConfigurableKeralaGoldTracker:
    def __init__(self):
        self.url = "https://www.goodreturns.in/gold-rates/kerala.html"
        self.driver = None
        
        # Use improved time handling
        try:
            self.time_handler = ImprovedTimeHandling()
            self.market_status = self.time_handler.get_market_status()
        except Exception as e:
            print(f"❌ Time handler initialization failed: {e}")
            raise
        
        # Notification settings from environment
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.pushover_token = os.environ.get('PUSHOVER_TOKEN')
        self.pushover_user = os.environ.get('PUSHOVER_USER')
        self.ntfy_topic = os.environ.get('NTFY_TOPIC')
        
        print(f"🔧 Configured Tracker Initialized")
        print(f"⏰ IST Time: {self.market_status['formatted_time']}")
        print(f"📊 Period: {self.market_status['period']}")
        print(f"📅 Trading Day: {self.market_status['is_trading_day']}")
        print(f"🏪 Market Hours: {self.market_status['is_market_hours']}")
        print(f"🏖️ Holiday: {self.market_status['is_holiday']}")
    
    def setup_driver(self):
        """Setup Chrome driver with improved error handling"""
        chrome_options = Options()
        
        if CHROME_HEADLESS:
            chrome_options.add_argument("--headless")
        if CHROME_NO_SANDBOX:
            chrome_options.add_argument("--no-sandbox")
            
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        try:
            # Try webdriver-manager first if available
            if USE_WEBDRIVER_MANAGER and WEBDRIVER_MANAGER_AVAILABLE:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✅ Using webdriver-manager for Chrome driver")
            else:
                # Fallback to system Chrome driver
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✅ Using system Chrome driver")
            
            # Anti-detection measures
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except WebDriverException as e:
            print(f"❌ Chrome driver setup failed: {e}")
            print("💡 Make sure Chrome browser is installed and ChromeDriver is in PATH")
            raise
        except Exception as e:
            print(f"❌ Unexpected driver setup error: {e}")
            raise
    
    def create_backup(self):
        """Create backup of important data files"""
        try:
            os.makedirs('data/backups', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            files_to_backup = [
                'data/latest_rate.json',
                'data/rate_history.json',
                'data/config_summary.json'
            ]
            
            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    backup_path = f'data/backups/{timestamp}_{filename}'
                    
                    with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                        dst.write(src.read())
            
            print(f"✅ Backup created: {timestamp}")
            
        except Exception as e:
            print(f"⚠️  Backup creation failed: {e}")
    
    def get_thresholds_for_period(self, period):
        """Get notification thresholds based on current period and configuration"""
        
        # Apply weekend/holiday adjustments if enabled
        adjustment_multiplier = 1.0
        if (not self.market_status['is_trading_day'] or self.market_status['is_holiday']) and ENABLE_WEEKEND_REDUCED_SENSITIVITY:
            adjustment_multiplier = WEEKEND_THRESHOLD_RUPEES / TRADING_THRESHOLD_RUPEES
        
        if period == "AKGSMA_MORNING_RUSH":
            return {
                'rupees': AKGSMA_THRESHOLD_RUPEES * adjustment_multiplier,
                'percent': AKGSMA_THRESHOLD_PERCENT * adjustment_multiplier,
                'micro_rupees': MICRO_ALERT_RUPEES if ENABLE_MICRO_ALERTS else 999
            }
        elif period == "EVENING_UPDATE":
            return {
                'rupees': EVENING_THRESHOLD_RUPEES * adjustment_multiplier,
                'percent': EVENING_THRESHOLD_PERCENT * adjustment_multiplier,
                'micro_rupees': MICRO_ALERT_RUPEES if ENABLE_MICRO_ALERTS else 999
            }
        elif period == "ACTIVE_TRADING":
            return {
                'rupees': TRADING_THRESHOLD_RUPEES * adjustment_multiplier,
                'percent': TRADING_THRESHOLD_PERCENT * adjustment_multiplier,
                'micro_rupees': 999
            }
        else:  # OFF_HOURS
            return {
                'rupees': OFFHOURS_THRESHOLD_RUPEES * adjustment_multiplier,
                'percent': OFFHOURS_THRESHOLD_PERCENT * adjustment_multiplier,
                'micro_rupees': 999
            }
    
    def scrape_rate(self):
        """Main scraping function with improved error handling"""
        try:
            print(f"🔍 Kerala Gold Tracker - Period: {self.market_status['period']}")
            print(f"⚙️ Using thresholds: {self.get_thresholds_for_period(self.market_status['period'])}")
            
            # Setup driver
            self.setup_driver()
            
            # Use configured delays
            time.sleep(random.uniform(SCRAPING_DELAY_MIN, SCRAPING_DELAY_MAX))
            
            # Load page with timeout
            try:
                self.driver.get(self.url)
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                time.sleep(random.uniform(PAGE_LOAD_DELAY_MIN, PAGE_LOAD_DELAY_MAX))
            except TimeoutException:
                print("⚠️  Page load timeout - continuing anyway")
            
            rate = self.extract_24k_rate()
            
            if rate and rate > 0:
                current_data = {
                    'rate': rate,
                    'currency': 'INR',
                    'unit': 'per gram',
                    'purity': '24K',
                    'location': 'Kerala',
                    'timestamp': datetime.now(pytz.UTC).isoformat(),
                    'ist_time': self.market_status['current_ist'].isoformat() if self.market_status['current_ist'] else None,
                    'ist_formatted': self.market_status['formatted_time'],
                    'source': self.url,
                    'success': True,
                    'market_period': self.market_status['period'],
                    'is_trading_day': self.market_status['is_trading_day'],
                    'is_market_hours': self.market_status['is_market_hours'],
                    'is_holiday': self.market_status['is_holiday']
                }
                
                # Create backup before processing
                self.create_backup()
                
                # Apply configured notification logic
                self.check_and_notify_configured(current_data)
                
                self.save_data(current_data)
                
                print(f"✅ Rate: ₹{rate} - {self.market_status['period']}")
                return current_data
            else:
                error_msg = "No valid rate found" if rate is None else f"Invalid rate: {rate}"
                self.send_error_notification(f"Failed during {self.market_status['period']}: {error_msg}")
                return None
                
        except WebDriverException as e:
            self.send_error_notification(f"WebDriver error ({self.market_status['period']}): {str(e)[:100]}")
            return None
        except Exception as e:
            self.send_error_notification(f"Error ({self.market_status['period']}): {str(e)[:100]}")
            return None
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    def extract_24k_rate(self):
        """Extract 24K rate from page with improved pattern matching"""
        try:
            page_source = self.driver.page_source
            
            # Enhanced patterns for Kerala 24K gold
            patterns = [
                r'24K\s+Gold\s*/g.*?₹\s*([\d,]+)',
                r'Kerala.*?24K.*?₹\s*([\d,]+)',
                r'24K.*?₹\s*([\d,]+)',
                r'24\s*Karat.*?₹\s*([\d,]+)',
                r'24k.*?₹\s*([\d,]+)',
                r'₹\s*([\d,]+).*?24K',
                r'₹\s*([\d,]+).*?24\s*Karat'
            ]
            
            for i, pattern in enumerate(patterns, 1):
                match = re.search(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if match:
                    rate_str = match.group(1).replace(',', '')
                    try:
                        rate = float(rate_str)
                        # Validate rate is reasonable (between ₹3000-₹10000)
                        if 3000 <= rate <= 10000:
                            print(f"✅ Found via pattern {i}: ₹{rate}")
                            return rate
                        else:
                            print(f"⚠️  Pattern {i} found unreasonable rate: ₹{rate}")
                    except ValueError:
                        continue
            
            # Element-based extraction as fallback
            try:
                elements_24k = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'k', 'K'), '24K')]")
                
                for element in elements_24k:
                    text = element.text
                    if '₹' in text:
                        match = re.search(r'₹\s*([\d,]+)', text)
                        if match:
                            rate_str = match.group(1).replace(',', '')
                            try:
                                rate = float(rate_str)
                                if 3000 <= rate <= 10000:
                                    print(f"✅ Found in element: ₹{rate}")
                                    return rate
                            except ValueError:
                                continue
                    
                    # Check parent element
                    try:
                        parent = element.find_element(By.XPATH, "..")
                        parent_text = parent.text
                        if '₹' in parent_text and '24K' in parent_text:
                            match = re.search(r'₹\s*([\d,]+)', parent_text)
                            if match:
                                rate_str = match.group(1).replace(',', '')
                                try:
                                    rate = float(rate_str)
                                    if 3000 <= rate <= 10000:
                                        print(f"✅ Found in parent: ₹{rate}")
                                        return rate
                                except ValueError:
                                    continue
                    except:
                        pass
            except Exception as e:
                print(f"⚠️  Element search error: {e}")
            
        except Exception as e:
            print(f"❌ Extraction error: {e}")
        
        print("❌ No valid 24K gold rate found")
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
                try:
                    previous_time = datetime.fromisoformat(previous_data.get('timestamp', ''))
                    time_diff = datetime.now(pytz.UTC) - previous_time
                    minutes_since_last = time_diff.total_seconds() / 60
                except:
                    minutes_since_last = 0
                
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
            print(f"❌ Configured notification error: {e}")
    
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
        except Exception as e:
            print(f"⚠️  Trend detection error: {e}")
        
        return None
    
    def should_send_hourly_update(self):
        """Check if should send hourly update based on configuration"""
        if not ENABLE_HOURLY_REPORTS:
            return False
            
        if self.market_status['period'] not in HOURLY_REPORT_PERIODS:
            return False
        
        ist_time = self.time_handler.get_current_ist()
        if ist_time is None:
            return False
            
        if ist_time.minute <= 5:
            try:
                os.makedirs('data', exist_ok=True)
                hour_key = ist_time.strftime('%Y-%m-%d-%H')
                
                if os.path.exists('data/last_hourly.txt'):
                    with open('data/last_hourly.txt', 'r') as f:
                        last_hourly = f.read().strip()
                        if last_hourly == hour_key:
                            return False
                
                with open('data/last_hourly.txt', 'w') as f:
                    f.write(hour_key)
                
                return True
            except Exception as e:
                print(f"⚠️  Hourly update check error: {e}")
        
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
        
        ist_formatted = self.time_handler.format_ist_time()
        
        if abs(change) == 0:
            message = f"""{emoji} {NOTIFICATION_TITLE}

{direction} NO CHANGE for {minutes_since:.0f} minutes
Current: ₹{current_rate:.0f}/g
Type: {notification_type}
Time: {ist_formatted}"""
            
            if INCLUDE_PERIOD_CONTEXT:
                market_context = ""
                if not self.market_status['is_trading_day']:
                    market_context = " (Non-trading day)"
                elif self.market_status['is_holiday']:
                    market_context = " (Holiday)"
                
                message += f"\n\n💡 Stability during {period.lower().replace('_', ' ')}{market_context} noted."
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
Time: {ist_formatted}"""
            
            if INCLUDE_PERIOD_CONTEXT:
                market_context = ""
                if not self.market_status['is_trading_day']:
                    market_context = " (Non-trading day)"
                elif self.market_status['is_holiday']:
                    market_context = " (Holiday)"
                
                message += f"\n\n🎯 Period: {period.lower().replace('_', ' ')}{market_context}"
        
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
                ist_formatted = self.time_handler.format_ist_time()
                
                message = f"""{emoji}Hourly Gold Trend Report

{trend} Hour: {self.time_handler.get_current_ist().strftime('%I:00 %p IST') if self.time_handler.get_current_ist() else 'Unknown'}

Hourly Performance:
• Opening: ₹{opening_rate:.0f}/g
• Current: ₹{current_rate:.0f}/g  
• High: ₹{hourly_high:.0f}/g
• Low: ₹{hourly_low:.0f}/g
• Change: ₹{hourly_change:+.0f} ({(hourly_change/opening_rate)*100:+.2f}%)
• Volatility: ₹{hourly_volatility:.0f}

Activity: {len(hourly_data)} updates this hour
Period: {self.market_status['period'].replace('_', ' ').title()}
Market Day: {self.market_status['is_trading_day']}"""
                
                self.send_notifications(message, priority="low")
        except Exception as e:
            print(f"❌ Hourly update error: {e}")
    
    def get_last_hour_data(self):
        """Get data from last hour"""
        try:
            if os.path.exists('data/rate_history.json'):
                with open('data/rate_history.json', 'r') as f:
                    history = json.load(f)
                
                one_hour_ago = datetime.now(pytz.UTC) - timedelta(hours=1)
                recent_data = []
                
                for entry in reversed(history):
                    try:
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time >= one_hour_ago:
                            recent_data.append(entry)
                    except:
                        continue
                
                return list(reversed(recent_data))
        except Exception as e:
            print(f"⚠️  Last hour data error: {e}")
        
        return []
    
    def send_initial_notification(self, current_rate, period):
        """Send initial setup notification with current configuration"""
        emoji = "🚀 " if ENABLE_EMOJI_IN_MESSAGES else ""
        ist_formatted = self.time_handler.format_ist_time()
        
        message = f"""{emoji}{NOTIFICATION_TITLE} Started!

Current Rate: ₹{current_rate:.0f}/g
Period: {period.replace('_', ' ').title()}
Time: {ist_formatted}
Trading Day: {self.market_status['is_trading_day']}
Holiday: {self.market_status['is_holiday']}

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

🏖️ HOLIDAY TRACKING:
Monitors {len(INDIAN_HOLIDAYS_2025)} Indian holidays for market closures

🔧 Easy to customize by editing configuration variables at top of script!"""
        
        self.send_notifications(message, priority="normal")
    
    def send_error_notification(self, error_msg):
        """Send error notification"""
        emoji = "❌ " if ENABLE_EMOJI_IN_MESSAGES else ""
        ist_formatted = self.time_handler.format_ist_time()
        
        message = f"""{emoji}{NOTIFICATION_TITLE} Error

{error_msg}

Period: {self.market_status['period']}
Time: {ist_formatted}
Trading Day: {self.market_status['is_trading_day']}
Holiday: {self.market_status['is_holiday']}

Will retry on next scheduled run."""
        
        self.send_notifications(message, priority="high")
    
    def send_notifications(self, message, priority="normal"):
        """Send notifications via configured channels"""
        
        notifications_sent = 0
        
        if self.telegram_token and self.telegram_chat_id:
            if self.send_telegram(message):
                notifications_sent += 1
        
        if self.pushover_token and self.pushover_user:
            if self.send_pushover(message, priority):
                notifications_sent += 1
        
        if self.ntfy_topic:
            if self.send_ntfy(message, priority):
                notifications_sent += 1
        
        if notifications_sent == 0:
            print(f"⚠️  No notifications sent - check environment variables")
        
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
                return True
            else:
                print(f"❌ Telegram failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Telegram network error: {e}")
            return False
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
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
                return True
            else:
                print(f"❌ Pushover failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Pushover network error: {e}")
            return False
        except Exception as e:
            print(f"❌ Pushover error: {e}")
            return False
    
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
                return True
            else:
                print(f"❌ ntfy failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ ntfy network error: {e}")
            return False
        except Exception as e:
            print(f"❌ ntfy error: {e}")
            return False
    
    def save_data(self, data):
        """Save data with configured retention settings and improved error handling"""
        try:
            os.makedirs('data', exist_ok=True)
            
            # Save latest with atomic write
            temp_file = 'data/latest_rate.json.tmp'
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, 'data/latest_rate.json')
            
            # Save to history with configured retention
            history_file = 'data/rate_history.json'
            history = []
            
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r') as f:
                        history = json.load(f)
                except json.JSONDecodeError:
                    print("⚠️  Corrupted history file - starting fresh")
                    history = []
            
            history.append(data)
            history = history[-HISTORY_ENTRIES_TO_KEEP:]
            
            # Atomic write for history
            temp_history = 'data/rate_history.json.tmp'
            with open(temp_history, 'w') as f:
                json.dump(history, f, indent=2)
            os.replace(temp_history, history_file)
            
            # Save configuration summary for reference
            config_summary = {
                'last_updated': data['timestamp'],
                'ist_time': data['ist_formatted'],
                'version': '2.0.0',
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
                'market_info': {
                    'current_period': data['market_period'],
                    'is_trading_day': data['is_trading_day'],
                    'is_market_hours': data['is_market_hours'],
                    'is_holiday': data['is_holiday']
                },
                'timezone_info': {
                    'utc_timestamp': data['timestamp'],
                    'ist_timestamp': data['ist_time'],
                    'ist_formatted': data['ist_formatted']
                }
            }
            
            # Atomic write for config summary
            temp_config = 'data/config_summary.json.tmp'
            with open(temp_config, 'w') as f:
                json.dump(config_summary, f, indent=2)
            os.replace(temp_config, 'data/config_summary.json')
            
            print("✅ Data saved successfully")
            
        except Exception as e:
            print(f"❌ Data save error: {e}")
    
    def get_daily_summary(self):
        """Generate daily summary of gold rate movements"""
        try:
            if os.path.exists('data/rate_history.json'):
                with open('data/rate_history.json', 'r') as f:
                    history = json.load(f)
                
                # Get today's data (IST)
                ist_today = self.time_handler.get_current_ist()
                if ist_today is None:
                    return None
                    
                ist_today_date = ist_today.date()
                today_data = []
                
                for entry in history:
                    try:
                        entry_ist = datetime.fromisoformat(entry['ist_time']).date()
                        if entry_ist == ist_today_date:
                            today_data.append(entry)
                    except:
                        continue
                
                if today_data:
                    rates = [entry['rate'] for entry in today_data]
                    opening = rates[0]
                    closing = rates[-1]
                    high = max(rates)
                    low = min(rates)
                    change = closing - opening
                    change_percent = (change / opening) * 100 if opening > 0 else 0
                    volatility = high - low
                    
                    return {
                        'date': ist_today_date.strftime('%d %b %Y'),
                        'opening': opening,
                        'closing': closing,
                        'high': high,
                        'low': low,
                        'change': change,
                        'change_percent': change_percent,
                        'volatility': volatility,
                        'updates': len(today_data)
                    }
        except Exception as e:
            print(f"⚠️  Daily summary error: {e}")
        
        return None
    
    def send_daily_summary(self):
        """Send end-of-day summary if enabled"""
        summary = self.get_daily_summary()
        if summary:
            emoji = "📊 " if ENABLE_EMOJI_IN_MESSAGES else ""
            direction = "📈" if summary['change'] > 0 else "📉" if summary['change'] < 0 else "➡️"
            
            message = f"""{emoji}Daily Gold Summary - {summary['date']}

{direction} Daily Performance:
• Opening: ₹{summary['opening']:.0f}/g
• Closing: ₹{summary['closing']:.0f}/g
• High: ₹{summary['high']:.0f}/g  
• Low: ₹{summary['low']:.0f}/g
• Change: ₹{summary['change']:+.0f} ({summary['change_percent']:+.2f}%)
• Volatility: ₹{summary['volatility']:.0f}

📈 Trading Activity: {summary['updates']} rate updates
🕒 Generated: {self.time_handler.format_ist_time()}"""
            
            self.send_notifications(message, priority="low")

def setup_environment_variables():
    """Setup guide for environment variables"""
    print("\n🔧 ENVIRONMENT VARIABLES SETUP:")
    print("=" * 50)
    print("Set these environment variables for notifications:")
    print()
    print("For Telegram:")
    print("export TELEGRAM_BOT_TOKEN='your_bot_token'")
    print("export TELEGRAM_CHAT_ID='your_chat_id'")
    print()
    print("For Pushover:")
    print("export PUSHOVER_TOKEN='your_app_token'")
    print("export PUSHOVER_USER='your_user_key'")
    print()
    print("For ntfy.sh:")
    print("export NTFY_TOPIC='your_unique_topic'")
    print("=" * 50)

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import selenium
    except ImportError:
        missing_deps.append("selenium")
    
    try:
        import pytz
    except ImportError:
        missing_deps.append("pytz")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n💡 Install with: pip install " + " ".join(missing_deps))
        return False
    
    return True

def main():
    """Main execution function"""
    print("🔧 Starting Enhanced Kerala Gold Tracker with Proper IST Handling...")
    print("=" * 80)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Validate configuration
    if not validate_configuration():
        return
    
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
    print(f"• Holiday Tracking: {len(INDIAN_HOLIDAYS_2025)} holidays configured")
    print(f"• WebDriver Manager: {'✅ Enabled' if USE_WEBDRIVER_MANAGER and WEBDRIVER_MANAGER_AVAILABLE else '❌ Disabled'}")
    print("=" * 80)
    
    # Check if environment variables are set
    required_vars = ['TELEGRAM_BOT_TOKEN', 'PUSHOVER_TOKEN', 'NTFY_TOPIC']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("⚠️  Missing notification setup!")
        setup_environment_variables()
        print("\n💡 You can still run the tracker - it will just print results without sending notifications.")
        print("=" * 80)
    
    try:
        tracker = ConfigurableKeralaGoldTracker()
        result = tracker.scrape_rate()
        
        if result:
            print(f"✅ Success: ₹{result['rate']} - {result['market_period']}")
            print(f"📊 Trading Day: {result['is_trading_day']}")
            print(f"🏖️ Holiday: {result['is_holiday']}")
            print(f"🕒 IST Time: {result['ist_formatted']}")
            
            # Check if it's end of trading day for summary
            ist_time = tracker.time_handler.get_current_ist()
            if ist_time and ist_time.hour == 19 and ist_time.minute <= 5:  # 7 PM IST
                tracker.send_daily_summary()
                
        else:
            print("❌ Tracking failed")
            
    except KeyboardInterrupt:
        print("\n🛑 Tracker stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🔧 To customize alerts, edit the configuration variables at the top of this file!")
    print("🌍 This version uses proper IST timezone handling with pytz library")
    print("🏖️ Includes Indian holiday tracking and market day detection")
    print("🛡️ Enhanced error handling and data backup mechanisms")

if __name__ == "__main__":
    main()