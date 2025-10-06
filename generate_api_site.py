import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Define IST timezone
IST = ZoneInfo("Asia/Kolkata")

def generate_enhanced_api_and_site():
    """Generate API endpoints with enhanced timing information"""
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    
    # Load data with staleness validation
    try:
        with open('data/latest_rate.json', 'r') as f:
            latest = json.load(f)
        
        # Preserve original scraping timestamp while handling staleness
        if latest.get('timestamp'):
            try:
                data_timestamp = datetime.fromisoformat(latest['timestamp'])
                if data_timestamp.tzinfo is None:
                    data_timestamp = data_timestamp.replace(tzinfo=IST)
                
                current_time = datetime.now(IST)
                age_hours = (current_time - data_timestamp).total_seconds() / 3600
                
                # Store original scraping timestamp separately - NEVER overwrite it
                latest['original_scrape_timestamp'] = latest['timestamp']
                latest['original_scrape_timestamp_ist'] = latest.get('ist_time', latest['timestamp'])
                
                # For very stale data (>24h), mark data validity but preserve original timestamp
                if age_hours > 24:
                    print(f"⚠️  Data is {age_hours:.1f} hours old - marking as stale but preserving original scrape time")
                    latest['data_validity'] = 'stale'
                    latest['stale_reason'] = f'Data is {age_hours:.1f} hours old'
                else:
                    latest['data_validity'] = 'fresh'
                    
            except (ValueError, TypeError) as e:
                # If timestamp parsing fails, preserve original but mark as invalid
                print(f"⚠️  Invalid timestamp format, preserving original: {e}")
                latest['original_scrape_timestamp'] = latest.get('timestamp', 'invalid')
                latest['original_scrape_timestamp_ist'] = latest.get('ist_time', 'invalid')
                latest['data_validity'] = 'invalid_timestamp'
                latest['timestamp'] = datetime.now(IST).isoformat()
                latest['ist_time'] = datetime.now(IST).isoformat()
    except:
        # File doesn't exist or is corrupted - create fresh fallback
        print("📂 No data file found, creating fallback with current timestamp")
        latest = {
            'rate': 'N/A', 
            'timestamp': datetime.now(IST).isoformat(),
            'ist_time': datetime.now(IST).isoformat(),
            'location': 'Kerala',
            'currency': 'INR',
            'unit': 'per gram',
            'purity': '24K',
            'success': False,
            'market_period': 'UNKNOWN',
            'is_weekend': datetime.now(IST).weekday() >= 5
        }
    
    try:
        with open('data/rate_history.json', 'r') as f:
            history = json.load(f)
    except:
        history = []
    
    # Create docs directory
    os.makedirs('docs', exist_ok=True)
    os.makedirs('docs/api', exist_ok=True)
    
    # Calculate timing information
    now = datetime.now(IST)
    if latest.get('timestamp'):
        last_fetched = datetime.fromisoformat(latest['timestamp'])
        # Ensure timezone consistency for calculations
        if last_fetched.tzinfo is None:
            last_fetched = last_fetched.replace(tzinfo=IST)
        fetch_age_seconds = (now - last_fetched).total_seconds()
        fetch_age_minutes = fetch_age_seconds / 60
        fetch_age_hours = fetch_age_minutes / 60
        
        # Determine next expected update (based on current schedule)
        current_hour = now.hour
        
        if 9 <= current_hour < 11:  # AKGSMA period
            next_update_minutes = 15 - (fetch_age_minutes % 15)
        elif 18 <= current_hour < 19:  # Evening period  
            next_update_minutes = 15 - (fetch_age_minutes % 15)
        elif 11 <= current_hour < 18:  # Trading hours
            next_update_minutes = 30 - (fetch_age_minutes % 30)
        else:  # Off hours
            next_update_minutes = 180 - (fetch_age_minutes % 180)  # 3 hours
    else:
        fetch_age_seconds = 0
        fetch_age_minutes = 0
        fetch_age_hours = 0
        next_update_minutes = 15
    
    # Determine data freshness
    if fetch_age_minutes < 5:
        freshness = "very_fresh"
        freshness_text = "Very Fresh"
    elif fetch_age_minutes < 15:
        freshness = "fresh"
        freshness_text = "Fresh"
    elif fetch_age_minutes < 60:
        freshness = "moderate"
        freshness_text = "Moderate"
    else:
        freshness = "stale"
        freshness_text = "Stale"
    
    # Enhanced latest rate API with comprehensive timing info
    enhanced_latest = {
        # Original data
        'rate': latest.get('rate'),
        'currency': latest.get('currency', 'INR'),
        'unit': latest.get('unit', 'per gram'),
        'purity': latest.get('purity', '24K'),
        'location': latest.get('location', 'Kerala'),
        'source': latest.get('source', 'https://www.goodreturns.in/gold-rates/kerala.html'),
        'success': latest.get('success', True),
        'market_period': latest.get('market_period', 'UNKNOWN'),
        
        # Enhanced timing information
        'data_scraped_at': latest.get('original_scrape_timestamp', latest.get('timestamp')),
        'data_scraped_at_ist': latest.get('original_scrape_timestamp_ist', latest.get('ist_time', latest.get('timestamp'))),
        'api_generated_at': now.isoformat(),
        'api_generated_at_ist': now.isoformat(),
        
        # Legacy fields for backward compatibility
        'data_fetched_at': latest.get('original_scrape_timestamp', latest.get('timestamp')),
        'data_fetched_at_ist': latest.get('original_scrape_timestamp_ist', latest.get('ist_time', latest.get('timestamp'))),
        'api_response_at': now.isoformat(),
        'api_response_at_ist': now.isoformat(),
        
        # Data age information
        'data_age': {
            'seconds': int(fetch_age_seconds),
            'minutes': round(fetch_age_minutes, 1),
            'hours': round(fetch_age_hours, 2),
            'human_readable': format_human_readable_age(fetch_age_seconds)
        },
        
        # Freshness indicators
        'freshness': {
            'status': freshness,
            'description': freshness_text,
            'is_fresh': fetch_age_minutes < 30,
            'is_very_fresh': fetch_age_minutes < 5,
            'confidence': calculate_confidence(fetch_age_minutes)
        },
        
        # Update schedule information
        'update_info': {
            'next_update_in_minutes': max(0, round(next_update_minutes, 1)),
            'update_frequency': get_current_update_frequency(now.hour),
            'last_update_was_scheduled': True,
            'total_updates_today': count_todays_updates(history)
        },
        
        # Data validity information
        'data_validity': {
            'status': latest.get('data_validity', 'unknown'),
            'reason': latest.get('stale_reason', ''),
            'original_timestamp_preserved': latest.get('original_scrape_timestamp') is not None
        },
        
        # API metadata
        'api_info': {
            'version': '2.1',
            'type': 'cached',
            'cache_strategy': 'github_actions_scheduled',
            'real_time': False,
            'rate_limited': False,
            'preserves_original_scrape_time': True
        }
    }
    
    # Save enhanced latest API
    with open('docs/api/latest.json', 'w') as f:
        json.dump(enhanced_latest, f, indent=2)
    
    # Enhanced history API with timing metadata
    enhanced_history = {
        'data': history,
        'metadata': {
            'total_entries': len(history),
            'date_range': {
                'oldest': history[0]['timestamp'] if history else None,
                'newest': history[-1]['timestamp'] if history else None
            },
            'api_generated_at': now.isoformat(),
            'data_points_last_24h': count_last_24h_entries(history),
            'average_update_interval_minutes': calculate_avg_interval(history)
        }
    }
    
    with open('docs/api/history.json', 'w') as f:
        json.dump(enhanced_history, f, indent=2)
    
    # Enhanced stats API
    if history:
        rates = [entry['rate'] for entry in history if isinstance(entry.get('rate'), (int, float))]
        if rates:
            stats = {
                'current': latest.get('rate'),
                'statistics': {
                    'highest': max(rates),
                    'lowest': min(rates),
                    'average': round(sum(rates) / len(rates), 2),
                    'median': round(sorted(rates)[len(rates)//2], 2),
                    'volatility': round(max(rates) - min(rates), 2)
                },
                'trends': {
                    'last_24h_change': calculate_24h_change(history),
                    'last_hour_change': calculate_hour_change(history),
                    'daily_high': get_daily_high(history),
                    'daily_low': get_daily_low(history)
                },
                'data_quality': {
                    'total_data_points': len(rates),
                    'data_completeness': round((len(rates) / len(history)) * 100, 1) if history else 0,
                    'last_updated': latest.get('timestamp'),
                    'data_age_minutes': round(fetch_age_minutes, 1)
                },
                'generated_at': now.isoformat()
            }
        else:
            stats = {'error': 'No valid rate data', 'generated_at': now.isoformat()}
    else:
        stats = {'error': 'No historical data', 'generated_at': now.isoformat()}
    
    with open('docs/api/stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Generate enhanced website with timing information
    generate_enhanced_website(enhanced_latest, enhanced_history, stats)
    
    print("✅ Enhanced API endpoints generated with comprehensive timing information!")
    print(f"📊 Data age: {format_human_readable_age(fetch_age_seconds)}")
    print(f"🔄 Next update in: {round(next_update_minutes, 1)} minutes")

def format_human_readable_age(seconds):
    """Convert seconds to human readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"

def calculate_confidence(age_minutes):
    """Calculate confidence level based on data age"""
    if age_minutes < 5:
        return "very_high"
    elif age_minutes < 15:
        return "high"
    elif age_minutes < 30:
        return "medium"
    elif age_minutes < 60:
        return "low"
    else:
        return "very_low"

def get_current_update_frequency(ist_hour):
    """Get current update frequency description"""
    if 9 <= ist_hour < 11:
        return "Every 15 minutes (AKGSMA morning period)"
    elif 18 <= ist_hour < 19:
        return "Every 15 minutes (Evening update period)"
    elif 11 <= ist_hour < 18:
        return "Every 30 minutes (Active trading hours)"
    else:
        return "Every 3 hours (Off hours)"

def count_todays_updates(history):
    """Count how many updates happened today"""
    try:
        today = datetime.now(IST).strftime('%Y-%m-%d')
        return len([entry for entry in history if entry.get('timestamp', '').startswith(today)])
    except:
        return 0

def count_last_24h_entries(history):
    """Count entries from last 24 hours"""
    try:
        cutoff = datetime.now(IST) - timedelta(hours=24)
        count = 0
        for entry in history:
            entry_timestamp = entry['timestamp']
            entry_time = datetime.fromisoformat(entry_timestamp)
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=IST)
            if entry_time >= cutoff:
                count += 1
        return count
    except:
        return 0

def calculate_avg_interval(history):
    """Calculate average time between updates"""
    try:
        if len(history) < 2:
            return None
        
        intervals = []
        for i in range(1, len(history)):
            timestamp1 = history[i-1]['timestamp']
            timestamp2 = history[i]['timestamp']
            time1 = datetime.fromisoformat(timestamp1)
            time2 = datetime.fromisoformat(timestamp2)
            if time1.tzinfo is None:
                time1 = time1.replace(tzinfo=IST)
            if time2.tzinfo is None:
                time2 = time2.replace(tzinfo=IST)
            interval_minutes = (time2 - time1).total_seconds() / 60
            intervals.append(interval_minutes)
        
        return round(sum(intervals) / len(intervals), 1)
    except:
        return None

def calculate_24h_change(history):
    """Calculate 24 hour change"""
    try:
        if len(history) < 2:
            return 0
        
        current_rate = history[-1]['rate']
        cutoff = datetime.now(IST) - timedelta(hours=24)
        
        for entry in reversed(history[:-1]):
            entry_timestamp = entry['timestamp']
            entry_time = datetime.fromisoformat(entry_timestamp)
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=IST)
            if entry_time <= cutoff:
                return round(current_rate - entry['rate'], 2)
        
        return 0
    except:
        return 0

def calculate_hour_change(history):
    """Calculate 1 hour change"""
    try:
        if len(history) < 2:
            return 0
        
        current_rate = history[-1]['rate']
        cutoff = datetime.now(IST) - timedelta(hours=1)
        
        for entry in reversed(history[:-1]):
            entry_timestamp = entry['timestamp']
            entry_time = datetime.fromisoformat(entry_timestamp)
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=IST)
            if entry_time <= cutoff:
                return round(current_rate - entry['rate'], 2)
        
        return 0
    except:
        return 0

def get_daily_high(history):
    """Get today's highest rate"""
    try:
        today = datetime.now(IST).strftime('%Y-%m-%d')
        today_rates = [entry['rate'] for entry in history 
                      if entry.get('timestamp', '').startswith(today) 
                      and isinstance(entry.get('rate'), (int, float))]
        return max(today_rates) if today_rates else None
    except:
        return None

def get_daily_low(history):
    """Get today's lowest rate"""
    try:
        today = datetime.now(IST).strftime('%Y-%m-%d')
        today_rates = [entry['rate'] for entry in history 
                      if entry.get('timestamp', '').startswith(today) 
                      and isinstance(entry.get('rate'), (int, float))]
        return min(today_rates) if today_rates else None
    except:
        return None

def generate_enhanced_website(latest_data, history_data, stats_data):
    """Generate enhanced website with timing information"""
    
    current_rate = latest_data.get('rate', 'N/A')
    data_age = latest_data.get('data_age', {})
    freshness = latest_data.get('freshness', {})
    update_info = latest_data.get('update_info', {})
    
    # Determine freshness color
    freshness_colors = {
        "very_fresh": "#00ff00",
        "fresh": "#90EE90", 
        "moderate": "#FFA500",
        "stale": "#FF6B6B"
    }
    freshness_color = freshness_colors.get(freshness.get('status', 'moderate'), "#FFA500")
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kerala 24K Gold Rate API with Real Fetch Time</title>
    <meta name="description" content="Kerala 24K gold rate API with real data fetch timing. Current: ₹{current_rate}/gram">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🥇</text></svg>">
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .rate-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        
        .current-rate {{
            font-size: 4rem;
            font-weight: bold;
            color: #ffd700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 10px;
        }}
        
        .rate-unit {{
            font-size: 1.5rem;
            opacity: 0.8;
            margin-bottom: 20px;
        }}
        
        .freshness-indicator {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            border-left: 5px solid {freshness_color};
        }}
        
        .freshness-status {{
            font-size: 1.2rem;
            font-weight: bold;
            color: {freshness_color};
        }}
        
        .timing-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .timing-item {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .timing-value {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #ffd700;
        }}
        
        .timing-label {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 5px;
        }}
        
        .api-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }}
        
        .api-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        
        .endpoint {{
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            margin: 10px 0;
            word-break: break-all;
            position: relative;
        }}
        
        .copy-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
        }}
        
        .copy-btn:hover {{
            background: #2980b9;
        }}
        
        @media (max-width: 768px) {{
            .current-rate {{ font-size: 2.5rem; }}
            .timing-grid {{ grid-template-columns: 1fr; }}
            .api-section {{ grid-template-columns: 1fr; }}
            .container {{ padding: 10px; }}
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            opacity: 0.7;
            margin-top: 40px;
        }}
        
        .footer a {{
            color: #ffd700;
            text-decoration: none;
        }}
        
        .auto-refresh {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.7);
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="auto-refresh">
        🔄 Auto-refresh: <span id="refresh-timer">60</span>s
    </div>
    
    <div class="container">
        <div class="header">
            <h1>🥇 Kerala Gold Rate API</h1>
            <p>Real-time tracking with actual fetch time information</p>
        </div>
        
        <div class="rate-card">
            <div class="current-rate">₹{current_rate}</div>
            <div class="rate-unit">per gram (24K)</div>
            
            <div class="freshness-indicator">
                <div class="freshness-status">
                    {freshness.get('description', 'Unknown')} Data
                </div>
                <div>Last fetched: {data_age.get('human_readable', 'Unknown')}</div>
                <div>Confidence: {freshness.get('confidence', 'Unknown').replace('_', ' ').title()}</div>
            </div>
            
            <div class="timing-grid">
                <div class="timing-item">
                    <div class="timing-value">{data_age.get('minutes', 0):.1f}</div>
                    <div class="timing-label">Minutes Since Fetch</div>
                </div>
                <div class="timing-item">
                    <div class="timing-value">{update_info.get('next_update_in_minutes', 0):.1f}</div>
                    <div class="timing-label">Next Update (min)</div>
                </div>
                <div class="timing-item">
                    <div class="timing-value">{update_info.get('total_updates_today', 0)}</div>
                    <div class="timing-label">Updates Today</div>
                </div>
                <div class="timing-item">
                    <div class="timing-value">{freshness.get('confidence', 'Unknown').replace('_', ' ').title()}</div>
                    <div class="timing-label">Data Confidence</div>
                </div>
            </div>
        </div>
        
        <div class="api-section">
            <div class="api-card">
                <h3>📡 Enhanced API Endpoints</h3>
                <p>All endpoints now include comprehensive timing information:</p>
                
                <h4>Latest Rate with Timing:</h4>
                <div class="endpoint">
                    GET ./api/latest.json
                    <button class="copy-btn" onclick="copyEndpoint('api/latest.json')">Copy URL</button>
                </div>
                
                <h4>Historical Data with Metadata:</h4>
                <div class="endpoint">
                    GET ./api/history.json
                    <button class="copy-btn" onclick="copyEndpoint('api/history.json')">Copy URL</button>
                </div>
                
                <h4>Statistics with Trends:</h4>
                <div class="endpoint">
                    GET ./api/stats.json
                    <button class="copy-btn" onclick="copyEndpoint('api/stats.json')">Copy URL</button>
                </div>
            </div>
            
            <div class="api-card">
                <h3>⏰ Timing Information Included</h3>
                <p>Every API response now includes:</p>
                
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li><strong>data_fetched_at</strong> - When data was actually scraped</li>
                    <li><strong>data_age</strong> - How old the data is (seconds/minutes/hours)</li>
                    <li><strong>freshness</strong> - Data quality assessment</li>
                    <li><strong>next_update_in_minutes</strong> - When next update expected</li>
                    <li><strong>update_frequency</strong> - Current update schedule</li>
                    <li><strong>confidence</strong> - Data reliability score</li>
                </ul>
            </div>
            
            <div class="api-card">
                <h3>📊 Current Schedule</h3>
                <div id="schedule-info">
                    <p><strong>Current Period:</strong> {update_info.get('update_frequency', 'Unknown')}</p>
                    <p><strong>Next Update:</strong> ~{update_info.get('next_update_in_minutes', 0):.1f} minutes</p>
                    <p><strong>Updates Today:</strong> {update_info.get('total_updates_today', 0)} times</p>
                </div>
            </div>
            
            <div class="api-card">
                <h3>🔧 Sample Enhanced Response</h3>
                <div class="endpoint">
{{
  "rate": {current_rate},
  "data_fetched_at": "{latest_data.get('data_fetched_at', '')}",
  "data_age": {{
    "minutes": {data_age.get('minutes', 0):.1f},
    "human_readable": "{data_age.get('human_readable', '')}"
  }},
  "freshness": {{
    "status": "{freshness.get('status', '')}",
    "confidence": "{freshness.get('confidence', '')}"
  }},
  "next_update_in_minutes": {update_info.get('next_update_in_minutes', 0):.1f}
}}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🔥 Enhanced with real fetch timing | Data from GoodReturns.in</p>
            <p>📈 Now you know exactly when data was last fetched!</p>
            <p><a href="https://github.com/sibincbaby/gold-rate-tracker">⭐ View Source Code</a></p>
        </div>
    </div>
    
    <script>
        // Auto-refresh countdown
        let refreshTimer = 60;
        const timerElement = document.getElementById('refresh-timer');
        
        setInterval(() => {{
            refreshTimer--;
            timerElement.textContent = refreshTimer;
            
            if (refreshTimer <= 0) {{
                location.reload();
            }}
        }}, 1000);
        
        // Copy endpoint URL to clipboard
        function copyEndpoint(endpoint) {{
            const fullUrl = window.location.origin + window.location.pathname + endpoint;
            navigator.clipboard.writeText(fullUrl).then(() => {{
                event.target.textContent = 'Copied!';
                setTimeout(() => event.target.textContent = 'Copy URL', 2000);
            }}).catch(() => {{
                prompt('Copy this URL:', fullUrl);
            }});
        }}
        
        // Update timing displays every minute
        setInterval(() => {{
            fetch('./api/latest.json')
                .then(r => r.json())
                .then(data => {{
                    const ageMinutes = data.data_age?.minutes || 0;
                    const nextUpdate = data.update_info?.next_update_in_minutes || 0;
                    
                    // Update displays if elements exist
                    const timingItems = document.querySelectorAll('.timing-value');
                    if (timingItems[0]) timingItems[0].textContent = ageMinutes.toFixed(1);
                    if (timingItems[1]) timingItems[1].textContent = nextUpdate.toFixed(1);
                }})
                .catch(() => console.log('Failed to update timing'));
        }}, 60000);
    </script>
</body>
</html>'''
    
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

from datetime import timedelta

if __name__ == "__main__":
    generate_enhanced_api_and_site()