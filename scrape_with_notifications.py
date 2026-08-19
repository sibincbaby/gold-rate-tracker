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
# (Note: IST constant defined after imports below)

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

# 📅 DAILY COMPARISON FEATURE
ENABLE_YESTERDAY_COMPARISON = True  # Show change from yesterday's rate in notifications
YESTERDAY_COMPARISON_WINDOW_HOURS = 22  # Look for rate within 22-26 hours ago (allows for missing data)

# 💰 MULTI-GRAM DISPLAY
ENABLE_MULTI_GRAM_DISPLAY = True  # Show prices for 2g, 5g, 8g, 10g in notifications
GRAM_QUANTITIES = [2, 5, 8, 10]  # Gram quantities to display (customize as needed)

# 💸 SELLING RATE CALCULATOR
ENABLE_SELLING_RATE_DISPLAY = True  # Show actual selling prices after fees
SELLING_FEE_PERCENTAGES = [2, 3, 5]  # Jewellery fee percentages (2%, 3%, 5%)
SELLING_GRAM_QUANTITIES = [1, 2, 5, 8, 10]  # Gram quantities for selling calculations

# 🥇 22K GOLD DISPLAY (Kerala jewellery is sold as 22K / 916 hallmark)
ENABLE_22K_DISPLAY = True         # Show 22K rate alongside 24K in notifications
ENABLE_22K_SELLING_RATES = True   # Show 22K selling value after jewellery fees

# 🔍 WEEKEND SETTINGS
WEEKEND_THRESHOLD_RUPEES = 30
WEEKEND_THRESHOLD_PERCENT = 0.3
ENABLE_WEEKEND_REDUCED_SENSITIVITY = True

# ================================================================================================
# 🚀 TRACKER CODE STARTS HERE
# ================================================================================================

import json
import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import time
import re

from gold_source import (
    SOURCE_URL,
    RateExtractionError,
    fetch_rates,
    validate_against_previous,
)

# Define IST timezone after imports
IST = ZoneInfo("Asia/Kolkata")

class ConfigurableKeralaGoldTracker:
    def __init__(self):
        self.url = SOURCE_URL

        # Notification settings from environment
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.pushover_token = os.environ.get('PUSHOVER_TOKEN')
        self.pushover_user = os.environ.get('PUSHOVER_USER')
        self.ntfy_topic = os.environ.get('NTFY_TOPIC')

        # Calculate current time and period
        self.ist_time = datetime.now(IST)
        self.current_period = self.get_current_period()
        self.is_weekend = self.ist_time.weekday() >= 5

        print(f"🔧 Configured Tracker Initialized")
        print(f"⏰ IST Time: {self.ist_time.strftime('%d %b %Y, %I:%M %p')}")
        print(f"📊 Period: {self.current_period}")

    def load_previous_data(self):
        """Read the last stored reading, or None on the very first run."""
        try:
            with open('data/latest_rate.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    def hours_since(self, previous_data):
        """Hours between the previous reading and now, or None if unknown."""
        if not previous_data:
            return None
        stamp = previous_data.get('timestamp')
        if not stamp:
            return None
        try:
            previous_time = datetime.fromisoformat(stamp)
        except ValueError:
            return None
        if previous_time.tzinfo is None:
            previous_time = previous_time.replace(tzinfo=IST)
        return (self.ist_time - previous_time).total_seconds() / 3600

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
        """Fetch both karats, sanity-check them, then notify and store."""
        print(f"🔍 Kerala Gold Tracker - Period: {self.current_period}")
        print(f"⚙️ Using thresholds: {self.get_thresholds_for_period(self.current_period)}")

        try:
            rates = fetch_rates(self.url)
        except RateExtractionError as exc:
            self.send_error_notification(f"Could not read rate ({self.current_period}): {exc}")
            return None
        except Exception as exc:
            self.send_error_notification(f"Error ({self.current_period}): {exc}")
            return None

        rate = rates['rate_24k']
        rate_22k = rates['rate_22k']

        # A reading that moved further than gold plausibly can is a bad parse,
        # not a market event. Drop it rather than storing it and alerting on it.
        previous_data = self.load_previous_data()
        ok, reason = validate_against_previous(
            rate,
            previous_data.get('rate') if previous_data else None,
            self.hours_since(previous_data),
        )
        if not ok:
            print(f"🚫 Rejected implausible reading: {reason}")
            self.send_error_notification(f"Rejected implausible rate: {reason}")
            return None

        current_data = {
            'rate': rate,
            'rate_24k': rate,
            'rate_22k': rate_22k,
            'rate_22k_source': rates.get('rate_22k_source', 'scraped'),
            'currency': 'INR',
            'unit': 'per gram',
            'purity': '24K',
            'location': 'Kerala',
            'timestamp': self.ist_time.isoformat(),
            'ist_time': self.ist_time.isoformat(),
            'source': self.url,
            'fetch_method': rates.get('fetch_method', 'unknown'),
            'success': True,
            'market_period': self.current_period,
            'is_weekend': self.is_weekend
        }

        self.check_and_notify_configured(current_data)
        self.save_data(current_data)

        print(f"✅ 24K: ₹{rate:,.0f}/g | 22K: ₹{rate_22k:,.0f}/g "
              f"({current_data['rate_22k_source']}) - {self.current_period}")
        return current_data

    def check_and_notify_configured(self, current_data):
        """Notification logic using configured thresholds"""
        try:
            previous_data = self.load_previous_data()

            current_rate = current_data['rate']
            current_period = current_data['market_period']

            # Stashed so the message formatters can show 22K alongside 24K
            self.current_22k = current_data.get('rate_22k')
            self.current_22k_source = current_data.get('rate_22k_source', 'scraped')
            self.previous_22k = previous_data.get('rate_22k') if previous_data else None
            
            if previous_data:
                previous_rate = previous_data.get('rate', 0)
                change = current_rate - previous_rate
                change_percent = (change / previous_rate) * 100 if previous_rate > 0 else 0
                
                # Get time since last change
                previous_timestamp = previous_data.get('timestamp', '')
                if previous_timestamp:
                    previous_time = datetime.fromisoformat(previous_timestamp)
                    if previous_time.tzinfo is None:
                        previous_time = previous_time.replace(tzinfo=IST)
                    time_diff = self.ist_time - previous_time
                else:
                    time_diff = timedelta(0)
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
                    # Get yesterday's rate for comparison
                    yesterday_data = self.get_yesterday_rate()
                    
                    self.send_configured_alert(
                        current_rate, previous_rate, change, change_percent, 
                        priority, notification_type, current_period, minutes_since_last,
                        yesterday_data
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
    
    def send_configured_alert(self, current_rate, previous_rate, change, change_percent, priority, notification_type, period, minutes_since, yesterday_data=None):
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
            
            # Add multi-gram prices
            if ENABLE_MULTI_GRAM_DISPLAY:
                multi_gram = self.format_multi_gram_prices(current_rate)
                message += f"\n\n💰 Quick Prices:\n{multi_gram}"
            
            # Add selling rates
            if ENABLE_SELLING_RATE_DISPLAY:
                selling_rates = self.format_selling_rates(current_rate)
                message += f"\n\n💸 24K Selling Value (After Fees):\n{selling_rates}"

            # Add the 22K block (the rate Kerala jewellery actually trades at)
            message += self.format_22k_section()
            
            # Add yesterday comparison even for stability alerts
            if yesterday_data and ENABLE_YESTERDAY_COMPARISON:
                yesterday_rate = yesterday_data['rate']
                yesterday_change = current_rate - yesterday_rate
                yesterday_change_percent = (yesterday_change / yesterday_rate) * 100 if yesterday_rate > 0 else 0
                hours_ago = yesterday_data['hours_ago']
                
                if ENABLE_EMOJI_IN_MESSAGES:
                    daily_direction = "📈" if yesterday_change > 0 else "📉" if yesterday_change < 0 else "➡️"
                else:
                    daily_direction = "UP" if yesterday_change > 0 else "DOWN" if yesterday_change < 0 else "STABLE"
                
                message += f"\n\n📅 Since Yesterday (~{hours_ago:.0f}h ago):\n{daily_direction} ₹{yesterday_change:+.0f} ({yesterday_change_percent:+.2f}%) from ₹{yesterday_rate:.0f}/g"
            
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
            
            # Determine arrow/emoji for change direction
            if ENABLE_EMOJI_IN_MESSAGES:
                change_arrow = "⬆️" if change > 0 else "⬇️" if change < 0 else "➡️"
            else:
                change_arrow = "↑" if change > 0 else "↓" if change < 0 else "→"

            message = f"""{emoji} {NOTIFICATION_TITLE}

{change_arrow} {magnitude} CHANGE: ₹{change:+.0f} ({change_percent:+.2f}%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Current Rate: ₹{current_rate:,.0f}/g

⏱️ Gap: {minutes_since:.0f} min | 🕐 {self.ist_time.strftime('%I:%M %p')}"""

            # Add multi-gram prices and changes
            if ENABLE_MULTI_GRAM_DISPLAY:
                multi_gram = self.format_multi_gram_prices(current_rate)
                message += f"\n\n💰 Current Prices:\n{multi_gram}"

                multi_gram_change = self.format_multi_gram_change(current_rate, previous_rate)
                if multi_gram_change:
                    message += f"\n\n💸 Price Changes:\n{multi_gram_change}"

            # Add selling rates
            if ENABLE_SELLING_RATE_DISPLAY:
                selling_rates = self.format_selling_rates(current_rate)
                message += f"\n\n💸 24K Selling Value (After Fees):\n{selling_rates}"

            # Add the 22K block (the rate Kerala jewellery actually trades at)
            message += self.format_22k_section()
            
            # Add yesterday comparison
            if yesterday_data and ENABLE_YESTERDAY_COMPARISON:
                yesterday_rate = yesterday_data['rate']
                yesterday_change = current_rate - yesterday_rate
                yesterday_change_percent = (yesterday_change / yesterday_rate) * 100 if yesterday_rate > 0 else 0
                hours_ago = yesterday_data['hours_ago']
                
                if ENABLE_EMOJI_IN_MESSAGES:
                    daily_direction = "📈" if yesterday_change > 0 else "📉" if yesterday_change < 0 else "➡️"
                else:
                    daily_direction = "UP" if yesterday_change > 0 else "DOWN" if yesterday_change < 0 else "STABLE"
                
                message += f"\n\n📅 Since Yesterday (~{hours_ago:.0f}h ago):\n{daily_direction} ₹{yesterday_change:+.0f} ({yesterday_change_percent:+.2f}%) from ₹{yesterday_rate:.0f}/g"
            
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
                
                one_hour_ago = self.ist_time - timedelta(hours=1)
                recent_data = []
                
                for entry in reversed(history):
                    entry_timestamp = entry['timestamp']
                    entry_time = datetime.fromisoformat(entry_timestamp)
                    if entry_time.tzinfo is None:
                        entry_time = entry_time.replace(tzinfo=IST)
                    if entry_time >= one_hour_ago:
                        recent_data.append(entry)
                
                return list(reversed(recent_data))
        except:
            pass
        
        return []
    
    def format_multi_gram_prices(self, rate_per_gram):
        """Format prices for multiple gram quantities"""
        if not ENABLE_MULTI_GRAM_DISPLAY:
            return ""

        prices = []
        for grams in GRAM_QUANTITIES:
            total_price = rate_per_gram * grams
            prices.append(f"{grams}g: ₹{total_price:,.0f}")

        return " | ".join(prices)

    def format_multi_gram_change(self, current_rate, previous_rate):
        """Format price changes for multiple gram quantities"""
        if not ENABLE_MULTI_GRAM_DISPLAY or current_rate == previous_rate:
            return ""

        # Determine arrow based on direction
        if ENABLE_EMOJI_IN_MESSAGES:
            arrow = "⬆️" if current_rate > previous_rate else "⬇️"
        else:
            arrow = "↑" if current_rate > previous_rate else "↓"

        changes = []
        for grams in GRAM_QUANTITIES:
            current_price = current_rate * grams
            previous_price = previous_rate * grams
            change = current_price - previous_price
            changes.append(f"{grams}g: {arrow}₹{abs(change):.0f}")

        return " | ".join(changes)
    
    def format_22k_section(self):
        """
        Build the 22K block for a notification.

        Kerala jewellery is sold as 22K (916 hallmark), so this is the number
        that matters when actually buying or selling ornaments.
        """
        if not ENABLE_22K_DISPLAY:
            return ""

        rate_22k = getattr(self, 'current_22k', None)
        if not rate_22k:
            return ""

        suffix = " (est.)" if getattr(self, 'current_22k_source', 'scraped') == 'derived' else ""
        section = f"\n\n🥇 22K (916) Rate: ₹{rate_22k:,.0f}/g{suffix}"

        previous_22k = getattr(self, 'previous_22k', None)
        if previous_22k:
            change = rate_22k - previous_22k
            if change:
                arrow = "⬆️" if change > 0 else "⬇️"
                percent = (change / previous_22k) * 100
                section += f"\n{arrow} ₹{change:+,.0f} ({percent:+.2f}%)"

        if ENABLE_MULTI_GRAM_DISPLAY:
            section += f"\n{self.format_multi_gram_prices(rate_22k)}"

        if ENABLE_22K_SELLING_RATES and ENABLE_SELLING_RATE_DISPLAY:
            section += f"\n\n💸 22K Selling Value (After Fees):\n{self.format_selling_rates(rate_22k)}"

        return section

    def format_selling_rates(self, rate_per_gram):
        """Format selling rates after jewellery fees"""
        if not ENABLE_SELLING_RATE_DISPLAY:
            return ""

        lines = []

        for grams in SELLING_GRAM_QUANTITIES:
            gross_value = rate_per_gram * grams

            # Calculate net amounts for each fee percentage
            net_values = []
            for fee_percent in SELLING_FEE_PERCENTAGES:
                fee_amount = gross_value * (fee_percent / 100)
                net_amount = gross_value - fee_amount
                # Use compact format with space separator instead of pipe
                net_values.append(f"{fee_percent}%:₹{net_amount:.0f}")

            # Format line for this gram quantity - use space separator
            line = f"{grams}g: " + " ".join(net_values)
            lines.append(line)

        return "\n".join(lines)
    
    def get_yesterday_rate(self):
        """Get rate from approximately 24 hours ago (yesterday)"""
        try:
            if not ENABLE_YESTERDAY_COMPARISON:
                return None
            
            if not os.path.exists('data/rate_history.json'):
                return None
            
            with open('data/rate_history.json', 'r') as f:
                history = json.load(f)
            
            if len(history) < 2:
                return None
            
            # Define the time window for "yesterday" (22-26 hours ago to handle gaps)
            target_time_min = self.ist_time - timedelta(hours=26)
            target_time_max = self.ist_time - timedelta(hours=YESTERDAY_COMPARISON_WINDOW_HOURS)
            
            # Find the closest rate to 24 hours ago
            closest_entry = None
            closest_diff = None
            
            for entry in history:
                try:
                    entry_timestamp = entry.get('timestamp', '')
                    if not entry_timestamp:
                        continue
                    
                    entry_time = datetime.fromisoformat(entry_timestamp)
                    if entry_time.tzinfo is None:
                        entry_time = entry_time.replace(tzinfo=IST)
                    
                    # Check if entry is within the yesterday window
                    if target_time_min <= entry_time <= target_time_max:
                        time_diff = abs((entry_time - (self.ist_time - timedelta(hours=24))).total_seconds())
                        
                        if closest_diff is None or time_diff < closest_diff:
                            closest_diff = time_diff
                            closest_entry = entry
                
                except Exception as e:
                    continue
            
            if closest_entry:
                entry_time = datetime.fromisoformat(closest_entry['timestamp'])
                if entry_time.tzinfo is None:
                    entry_time = entry_time.replace(tzinfo=IST)
                
                hours_ago = (self.ist_time - entry_time).total_seconds() / 3600
                
                return {
                    'rate': closest_entry.get('rate'),
                    'timestamp': closest_entry.get('timestamp'),
                    'hours_ago': hours_ago
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Yesterday rate lookup error: {e}")
            return None
    
    def send_initial_notification(self, current_rate, period):
        """Send initial setup notification with current configuration"""
        emoji = "🚀 " if ENABLE_EMOJI_IN_MESSAGES else ""
        
        message = f"""{emoji}{NOTIFICATION_TITLE}

Current Rate: ₹{current_rate:.0f}/g
Period: {period.replace('_', ' ').title()}
Time: {self.ist_time.strftime('%d %b, %I:%M %p IST')}"""
        
        # Add multi-gram prices
        if ENABLE_MULTI_GRAM_DISPLAY:
            multi_gram = self.format_multi_gram_prices(current_rate)
            message += f"\n\n💰 Quick Prices:\n{multi_gram}"
        
        # Add selling rates
        if ENABLE_SELLING_RATE_DISPLAY:
            selling_rates = self.format_selling_rates(current_rate)
            message += f"\n\n💸 24K Selling Value (After Fees):\n{selling_rates}"

        message += self.format_22k_section()
        
        # Add yesterday comparison if available
        if ENABLE_YESTERDAY_COMPARISON:
            yesterday_data = self.get_yesterday_rate()
            if yesterday_data:
                yesterday_rate = yesterday_data['rate']
                yesterday_change = current_rate - yesterday_rate
                yesterday_change_percent = (yesterday_change / yesterday_rate) * 100 if yesterday_rate > 0 else 0
                hours_ago = yesterday_data['hours_ago']
                
                if ENABLE_EMOJI_IN_MESSAGES:
                    daily_direction = "📈" if yesterday_change > 0 else "📉" if yesterday_change < 0 else "➡️"
                else:
                    daily_direction = "UP" if yesterday_change > 0 else "DOWN" if yesterday_change < 0 else "STABLE"
                
                message += f"\n\n📅 Since Yesterday (~{hours_ago:.0f}h ago):\n{daily_direction} ₹{yesterday_change:+.0f} ({yesterday_change_percent:+.2f}%) from ₹{yesterday_rate:.0f}/g"
        
        message += f""""""
        
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

        print(f"DEBUG: Total message length: {len(message)} characters")
        print(f"DEBUG: Full message preview:\n{message}\n{'='*60}")

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
    print(f"• Yesterday Comparison: {'✅ Enabled' if ENABLE_YESTERDAY_COMPARISON else '❌ Disabled'}")
    print(f"• Multi-Gram Display: {'✅ Enabled' if ENABLE_MULTI_GRAM_DISPLAY else '❌ Disabled'} ({', '.join([f'{g}g' for g in GRAM_QUANTITIES])})")
    print(f"• Selling Calculator: {'✅ Enabled' if ENABLE_SELLING_RATE_DISPLAY else '❌ Disabled'} ({', '.join([f'{f}%' for f in SELLING_FEE_PERCENTAGES])} fees)")
    print("=" * 60)
    
    tracker = ConfigurableKeralaGoldTracker()
    result = tracker.scrape_rate()
    
    if result:
        print(f"✅ Success: ₹{result['rate']} - {result['market_period']}")
    else:
        # Exit non-zero so a failed scrape shows up as a red run instead of
        # a green one that quietly published nothing.
        print("❌ Tracking failed")
        sys.exit(1)
    
    print("\n🔧 To customize alerts, edit the configuration variables at the top of this file!")