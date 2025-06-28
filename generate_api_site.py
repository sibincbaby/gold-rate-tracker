import json
import os
from datetime import datetime

def generate_api_and_site():
    """Generate API endpoints and website"""
    
    # Load data
    try:
        with open('data/latest_rate.json', 'r') as f:
            latest = json.load(f)
    except:
        latest = {
            'rate': 'N/A', 
            'timestamp': datetime.now().isoformat(),
            'location': 'Kerala',
            'currency': 'INR',
            'unit': 'per gram',
            'purity': '24K'
        }
    
    try:
        with open('data/rate_history.json', 'r') as f:
            history = json.load(f)
    except:
        history = []
    
    # Create docs directory
    os.makedirs('docs', exist_ok=True)
    os.makedirs('docs/api', exist_ok=True)
    
    # 1. Create API endpoints
    
    # Latest rate API
    with open('docs/api/latest.json', 'w') as f:
        json.dump(latest, f, indent=2)
    
    # History API
    with open('docs/api/history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    # Stats API
    if history:
        rates = [entry['rate'] for entry in history if isinstance(entry.get('rate'), (int, float))]
        if rates:
            stats = {
                'current': latest.get('rate'),
                'highest': max(rates),
                'lowest': min(rates),
                'average': round(sum(rates) / len(rates), 2),
                'last_24h_change': round(rates[-1] - rates[-12] if len(rates) >= 12 else 0, 2),
                'total_entries': len(rates),
                'last_updated': latest.get('timestamp')
            }
        else:
            stats = {'error': 'No valid rate data'}
    else:
        stats = {'error': 'No historical data'}
    
    with open('docs/api/stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    # 2. Create main website
    current_rate = latest.get('rate', 'N/A')
    last_updated = latest.get('timestamp', '')[:19].replace('T', ' ') if latest.get('timestamp') else 'Unknown'
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kerala 24K Gold Rate API & Tracker</title>
    <meta name="description" content="Live Kerala 24K gold rate with notifications. Current: ₹{current_rate}/gram">
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
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
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
        
        .rate-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .info-item {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
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
        
        .status {{ 
            color: #00ff00; 
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff00;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .history-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .history-table th,
        .history-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .history-table th {{
            background: rgba(255, 255, 255, 0.1);
            font-weight: bold;
        }}
        
        .update-time {{
            font-size: 0.9rem;
            opacity: 0.7;
            margin-top: 20px;
        }}
        
        @media (max-width: 768px) {{
            .current-rate {{ font-size: 2.5rem; }}
            .api-section {{ grid-template-columns: 1fr; }}
            .rate-info {{ grid-template-columns: 1fr; }}
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
        
        .footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🥇 Kerala Gold Rate Tracker</h1>
            <p>Live 24K gold rates with phone notifications</p>
        </div>
        
        <div class="rate-card">
            <div class="current-rate">₹{current_rate}</div>
            <div class="rate-unit">per gram (24K)</div>
            
            <div class="rate-info">
                <div class="info-item">
                    <strong>📍 Location</strong><br>
                    {latest.get('location', 'Kerala')}
                </div>
                <div class="info-item">
                    <strong>🏆 Purity</strong><br>
                    {latest.get('purity', '24K')}
                </div>
                <div class="info-item">
                    <strong>🔄 Updates</strong><br>
                    Every 2 hours
                </div>
                <div class="info-item">
                    <strong>📊 Status</strong><br>
                    <span class="status"></span>Live
                </div>
            </div>
            
            <div class="update-time">
                Last updated: {last_updated}
            </div>
        </div>
        
        <div class="api-section">
            <div class="api-card">
                <h3>📡 API Endpoints</h3>
                <p>Access gold rate data programmatically:</p>
                
                <h4>Latest Rate:</h4>
                <div class="endpoint">
                    GET ./api/latest.json
                    <button class="copy-btn" onclick="copyEndpoint('api/latest.json')">Copy URL</button>
                </div>
                
                <h4>Historical Data:</h4>
                <div class="endpoint">
                    GET ./api/history.json
                    <button class="copy-btn" onclick="copyEndpoint('api/history.json')">Copy URL</button>
                </div>
                
                <h4>Statistics:</h4>
                <div class="endpoint">
                    GET ./api/stats.json
                    <button class="copy-btn" onclick="copyEndpoint('api/stats.json')">Copy URL</button>
                </div>
            </div>
            
            <div class="api-card">
                <h3>📱 Phone Notifications</h3>
                <p>Get instant alerts when gold rates change significantly!</p>
                
                <h4>✅ Notification Channels:</h4>
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li>📱 Telegram Bot</li>
                    <li>🔔 Pushover</li>
                    <li>🆓 ntfy.sh (free)</li>
                </ul>
                
                <h4>⚡ Alert Triggers:</h4>
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li>Price change ≥ ₹50</li>
                    <li>Percentage change ≥ 1%</li>
                    <li>System errors</li>
                </ul>
            </div>
            
            <div class="api-card">
                <h3>📊 Live Statistics</h3>
                <div id="stats-content">Loading...</div>
            </div>
            
            <div class="api-card">
                <h3>📈 Recent History</h3>
                <div id="history-content">
                    <table class="history-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Rate (₹/g)</th>
                            </tr>
                        </thead>
                        <tbody id="history-tbody">
                            <tr><td colspan="2">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="api-section">
            <div class="api-card">
                <h3>🔗 Integration Examples</h3>
                
                <h4>JavaScript/Fetch:</h4>
                <div class="endpoint">
fetch('./api/latest.json')
  .then(r => r.json())
  .then(data => console.log('₹' + data.rate));
                </div>
                
                <h4>Python/Requests:</h4>
                <div class="endpoint">
import requests
r = requests.get('your-site.com/api/latest.json')
rate = r.json()['rate']
                </div>
                
                <h4>curl:</h4>
                <div class="endpoint">
curl https://your-site.com/api/latest.json
                </div>
            </div>
            
            <div class="api-card">
                <h3>⚙️ Features</h3>
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li>✅ <strong>100% Free</strong> - No costs ever</li>
                    <li>🔄 <strong>Auto-updates</strong> every 2 hours</li>
                    <li>📱 <strong>Phone alerts</strong> for significant changes</li>
                    <li>📊 <strong>Historical data</strong> tracking</li>
                    <li>🌐 <strong>Public APIs</strong> with CORS enabled</li>
                    <li>📈 <strong>Statistics</strong> and analytics</li>
                    <li>🚀 <strong>Fast</strong> - served via GitHub CDN</li>
                    <li>🔒 <strong>Reliable</strong> - GitHub infrastructure</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>🔥 Powered by GitHub Actions | Data from GoodReturns.in</p>
            <p>📈 Open source gold rate tracker with notifications</p>
            <p><a href="https://github.com/yourusername/gold-rate-tracker">⭐ View Source Code on GitHub</a></p>
        </div>
    </div>
    
    <script>
        // Load and display stats
        fetch('./api/stats.json')
            .then(r => r.json())
            .then(data => {{
                const statsDiv = document.getElementById('stats-content');
                if (data.error) {{
                    statsDiv.innerHTML = '<p>No data available yet</p>';
                }} else {{
                    statsDiv.innerHTML = `
                        <p><strong>Current:</strong> ₹${{data.current}}</p>
                        <p><strong>Highest:</strong> ₹${{data.highest}}</p>
                        <p><strong>Lowest:</strong> ₹${{data.lowest}}</p>
                        <p><strong>Average:</strong> ₹${{data.average}}</p>
                        <p><strong>Data Points:</strong> ${{data.total_entries}}</p>
                    `;
                }}
            }})
            .catch(() => {{
                document.getElementById('stats-content').innerHTML = '<p>Stats will appear after first run</p>';
            }});
        
        // Load recent history
        fetch('./api/history.json')
            .
