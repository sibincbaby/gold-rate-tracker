# 📅 Yesterday Rate Comparison Feature

## Overview
Your gold rate tracker now includes a **Daily Comparison Feature** that shows how the current rate compares to yesterday's rate, in addition to the immediate change from the last reading.

## ✅ What's Been Implemented

### 1. **Yesterday Rate Lookup**
- New method `get_yesterday_rate()` that searches historical data for a rate from approximately 24 hours ago
- Smart lookup window: Searches between 22-26 hours ago to handle gaps in data collection
- Finds the closest available rate to exactly 24 hours ago

### 2. **Enhanced Notifications**
All your notifications now include **TWO comparisons**:

#### **Immediate Change** (Already existed):
- Shows change from the last recorded rate
- Could be from minutes or hours ago
- Example: `Previous: ₹7,850/g → Current: ₹7,865/g (Change: ₹+15)`

#### **Daily Change** (NEW):
- Shows change from yesterday's rate (~24 hours ago)
- Displays how many hours ago the comparison rate was from
- Example: `📅 Since Yesterday (~24h ago): 📈 ₹+45 (+0.57%) from ₹7,820/g`

### 3. **Configuration Options**
Added two new configuration variables at the top of the script:

```python
# 📅 DAILY COMPARISON FEATURE
ENABLE_YESTERDAY_COMPARISON = True  # Enable/disable yesterday comparison
YESTERDAY_COMPARISON_WINDOW_HOURS = 22  # Look for rates 22-26 hours ago
```

## 📱 Example Notification

### Before (Old Format):
```
🌅 Kerala 24K Gold Tracker

📈 MODERATE: ₹15 (0.19%)

Previous: ₹7,850/g
Current: ₹7,865/g
Change: ₹+15

Type: 📊 Main Alert
Gap: 45 min
Time: 10:30 AM IST
```

### After (New Format with Yesterday Comparison):
```
🌅 Kerala 24K Gold Tracker

📈 MODERATE: ₹15 (0.19%)

Previous: ₹7,850/g
Current: ₹7,865/g
Change: ₹+15

Type: 📊 Main Alert
Gap: 45 min
Time: 10:30 AM IST

📅 Since Yesterday (~24h ago):
📈 ₹+45 (+0.57%) from ₹7,820/g

🎯 Period: akgsma morning rush
```

## 🎯 Benefits

### 1. **Dual Perspective**
- **Short-term**: See immediate market movements (minutes/hours)
- **Long-term**: See daily trends (24-hour comparison)

### 2. **Better Context**
- Understand if the day is trending up or down overall
- Compare short-term volatility vs daily trend
- Example: Current rate may be down ₹10 from last reading, but up ₹50 from yesterday

### 3. **Smart Data Handling**
- Handles missing data gracefully (searches 22-26 hour window)
- Shows exactly how many hours ago the comparison was made
- Works with your existing `rate_history.json` (keeps up to 500 entries)
- If no yesterday data exists, the feature simply doesn't show (no errors)

## 🔧 How It Works

### Data Flow:
1. **Current Run**: Scrapes new rate (e.g., ₹7,865)
2. **Yesterday Lookup**: Searches `rate_history.json` for rate ~24h ago (finds ₹7,820 from 24.2h ago)
3. **Calculations**:
   - Daily change: ₹7,865 - ₹7,820 = +₹45
   - Daily percent: (+45 / 7,820) × 100 = +0.57%
4. **Display**: Shows both immediate change AND daily change in notification

### Example Scenarios:

#### Scenario 1: Rate Rising Throughout Day
```
Immediate: ₹+15 from last reading
Daily: ₹+50 from yesterday
→ Consistent upward trend
```

#### Scenario 2: Rate Volatile but Flat Overall
```
Immediate: ₹-20 from last reading
Daily: ₹+5 from yesterday
→ Short-term dip in otherwise stable/rising day
```

#### Scenario 3: Major Daily Movement
```
Immediate: ₹+10 from last reading
Daily: ₹-80 from yesterday
→ Small recovery but still down significantly for the day
```

## 📊 Data Requirements

### Minimum Requirements:
- At least 2 entries in `rate_history.json`
- At least one entry from 22-26 hours ago

### Typical Scenario:
- If you run the script every 30 minutes, you'll have ~48 entries per day
- With 500-entry history, you have ~10 days of data
- Yesterday comparison will work as long as you have data from previous day

### Edge Cases Handled:
- **No historical data**: Feature silently disabled (no error)
- **First run**: Only shows current rate, no comparison
- **Data gaps**: Searches 22-26h window to find closest available rate
- **Disabled feature**: Set `ENABLE_YESTERDAY_COMPARISON = False`

## 🎛️ Customization

### To Disable Yesterday Comparison:
```python
ENABLE_YESTERDAY_COMPARISON = False
```

### To Adjust Lookup Window:
```python
# More strict (23-25 hours):
YESTERDAY_COMPARISON_WINDOW_HOURS = 23

# More lenient (20-28 hours):
YESTERDAY_COMPARISON_WINDOW_HOURS = 20
```

### To Customize Display Format:
Edit the `send_configured_alert()` method around lines 490-520 to change:
- Emoji used for daily direction
- Text format
- Number formatting (e.g., show decimals)

## 🚀 Usage

### No Changes Needed!
The feature is **already enabled** by default. Just run your script as normal:

```bash
python scrape_with_notifications.py
```

### First Run After Update:
- May not show yesterday comparison (needs historical data)
- After 24+ hours of running, will automatically start showing daily comparisons

### In Your GitHub Actions:
- No changes needed to workflow
- Feature works automatically with scheduled runs
- Data persists in `data/rate_history.json`

## 📈 Example Use Cases

### 1. Morning Trading Decisions
```
Current: ₹7,865/g
Since Yesterday: +₹45 (+0.57%)
→ Rate is trending up, might continue rising
```

### 2. Evening Review
```
Current: ₹7,820/g
Since Yesterday: -₹30 (-0.38%)
→ Rate dropped today, might be good buying opportunity
```

### 3. Weekend Stability Check
```
Current: ₹7,850/g
Since Yesterday: ₹+2 (+0.03%)
→ Very stable over 24h, minimal volatility
```

## 🐛 Troubleshooting

### Yesterday comparison not showing?
- Check: Do you have data older than 22 hours in `data/rate_history.json`?
- Check: Is `ENABLE_YESTERDAY_COMPARISON = True`?
- Wait: Feature needs historical data from previous day

### Shows wrong hours ago?
- The script searches for the closest rate to 24h ago
- May show 23h, 24h, 25h depending on data availability
- This is expected behavior

### Want more precise 24h comparison?
- Adjust `YESTERDAY_COMPARISON_WINDOW_HOURS = 23` (narrower window)
- Run script more frequently (every 15 min instead of 30 min)

## 💡 Future Enhancements (Possible)

Want more daily analytics? You could add:
- [ ] Week-over-week comparison (7 days ago)
- [ ] Daily high/low tracking
- [ ] Daily opening vs closing rate
- [ ] Multi-day trend indicators
- [ ] Daily volatility metrics

Let me know if you want any of these features implemented!

---

**Feature Status**: ✅ Fully Implemented and Ready to Use!
