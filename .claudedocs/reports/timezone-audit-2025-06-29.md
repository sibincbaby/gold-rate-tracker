# Timezone Audit Report - Kerala Gold Rate Tracker

**Audit Date:** 2025-06-29  
**Focus:** IST timezone consistency across codebase

## Summary

❌ **Critical Issues Found:** Multiple timezone inconsistencies that can cause data corruption and incorrect scheduling.

## Issues Identified

### 1. Inconsistent IST Implementation

| File | Line | Issue | Impact |
|------|------|-------|---------|
| scrape_with_notifications.py | 109 | Manual UTC+5:30 calculation | ❌ High |
| generate_api_site.py | 41, 88 | Hardcoded UTC+5:30 | ❌ High |
| scrape_with_notifications.py | 210 | Using UTC timestamp | ❌ Critical |
| generate_api_site.py | Multiple | All datetime.now() calls use UTC | ❌ Critical |

### 2. GitHub Actions Schedule

✅ **Correctly configured** - Uses UTC cron with IST comments:
```yaml
- cron: '30,45 3 * * *'      # 9:00, 9:15 AM IST
```

### 3. Specific Problems Found

#### Problem 1: Mixed Timestamp Systems
```python
# scrape_with_notifications.py:210-211
'timestamp': datetime.now().isoformat(),  # UTC
'ist_time': self.ist_time.isoformat(),    # IST (manual calculation)
```
**Impact:** Data inconsistency, wrong time comparisons

#### Problem 2: Manual IST Calculation
```python
# scrape_with_notifications.py:109
self.ist_time = datetime.now() + timedelta(hours=IST_OFFSET_HOURS, minutes=IST_OFFSET_MINUTES)
```
**Issue:** Doesn't handle DST, leap seconds, or timezone changes

#### Problem 3: All generate_api_site.py Uses UTC
```python
# generate_api_site.py - Multiple locations
now = datetime.now()  # Always UTC
today = datetime.now().strftime('%Y-%m-%d')  # Wrong date in IST context
```
**Impact:** Wrong daily statistics, incorrect time calculations

## Recommended Fixes

### Phase 1: Import Proper Timezone Support
```python
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+

# Define IST timezone properly
IST = ZoneInfo("Asia/Kolkata")
```

### Phase 2: Fix All Timestamp Generation
```python
# Replace all datetime.now() calls with:
datetime.now(IST)  # For IST timestamps
datetime.now(timezone.utc)  # For UTC timestamps (if needed)
```

### Phase 3: Consistent Timestamp Strategy
Choose ONE approach:
1. **Option A (Recommended):** All timestamps in IST
2. **Option B:** All timestamps in UTC, convert for display

## Required Changes

### scrape_with_notifications.py
```python
# Line 109 - Fix IST calculation
self.ist_time = datetime.now(IST)

# Line 210 - Use consistent timezone
'timestamp': datetime.now(IST).isoformat(),
'ist_time': datetime.now(IST).isoformat(),  # Remove duplicate
```

### generate_api_site.py
```python
# Replace all datetime.now() with datetime.now(IST)
now = datetime.now(IST)
today = datetime.now(IST).strftime('%Y-%m-%d')
cutoff = datetime.now(IST) - timedelta(hours=24)
```

## Risk Assessment

| Risk | Probability | Impact | Severity |
|------|-------------|--------|----------|
| Wrong daily statistics | High | High | Critical |
| Incorrect notifications | High | Medium | High |
| Data corruption | Medium | High | High |
| Schedule drift | Low | Medium | Medium |

## Immediate Action Required

1. ✅ **Stop using manual UTC+5:30 calculations**
2. ✅ **Import proper timezone libraries**
3. ✅ **Use consistent timezone throughout**
4. ✅ **Test with timezone edge cases**

## Verification Steps

1. Check daily rollover at midnight IST
2. Verify DST handling (though IST doesn't observe DST)
3. Test time comparisons across different periods
4. Validate API timestamp consistency

---

**Critical:** This issue affects data integrity and should be fixed immediately before any production deployment.