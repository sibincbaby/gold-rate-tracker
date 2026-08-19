# 🥇 Kerala Gold Rate Tracker

Live 24K **and 22K** gold rate tracking for Kerala, with phone notifications - completely FREE!

## 🌐 Live Demo
- **Website**: [https://sibincbaby.github.io/gold-rate-tracker](https://sibincbaby.github.io/gold-rate-tracker)
- **API**: [https://sibincbaby.github.io/gold-rate-tracker/api/latest.json](https://sibincbaby.github.io/gold-rate-tracker/api/latest.json)

## ✨ Features

- 🥇 **24K and 22K (916)** rates, with selling value after jewellery fees
- 🔄 **Auto-updates** on a schedule tuned to AKGSMA rate-setting hours
- 📱 **Phone notifications** when rates change significantly (≥₹50 or ≥1%)
- 📊 **Beautiful web interface** with real-time data
- 🔌 **REST APIs** for integration
- 📈 **Historical data** tracking (last 100 entries)
- 🆓 **100% FREE** - no hosting costs
- 🚀 **Fast & reliable** - powered by GitHub infrastructure

## 📱 Notification Channels

- **📱 Telegram** - Free, unlimited messages
- **🔔 Pushover** - Mobile push notifications
- **🆓 ntfy.sh** - Completely free, no registration needed

## 🚀 Quick Setup

### 1. Fork this repository
### 2. Enable GitHub Actions & Pages
### 3. Add notification secrets (choose one):

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `NTFY_TOPIC` | Your ntfy topic (recommended) | ✅ |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | ❌ |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | ❌ |
| `PUSHOVER_TOKEN` | Pushover app token | ❌ |
| `PUSHOVER_USER` | Pushover user key | ❌ |

### 4. Push changes and you're live!

## 📡 API Endpoints

```bash
# Get current gold rate
GET /api/latest.json

# Get historical data
GET /api/history.json

# Get statistics
GET /api/stats.json
```

## 📊 API Response Example

```json
{
  "rate": 15589.0,
  "rate_24k": 15589.0,
  "rate_22k": 14290.0,
  "rate_22k_source": "scraped",
  "rates": { "24K": 15589.0, "22K": 14290.0 },
  "currency": "INR",
  "unit": "per gram",
  "location": "Kerala",
  "source": "https://www.goodreturns.in/gold-rates/kerala.html",
  "success": true
}
```

`rate` stays the 24K figure so existing consumers keep working. `rate_22k_source`
is `scraped` when read from the page and `derived` when computed as 24K × 22/24
because the page did not yield a trustworthy 22K figure.

## 🔧 Customization

### Change Update Frequency
Edit `.github/workflows/gold-scraper-with-notifications.yml`:

```yaml
schedule:
  - cron: '0 */1 * * *'  # Every hour
  - cron: '*/30 * * * *'  # Every 30 minutes
```

### Adjust Alert Thresholds
Edit `scrape_with_notifications.py`:

```python
# Current: Alert for ≥₹50 or ≥1%
if abs(change) >= 50 or abs(change_percent) >= 1.0:

# More sensitive: Alert for ≥₹25 or ≥0.5%
if abs(change) >= 25 or abs(change_percent) >= 0.5:
```

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the extraction tests (offline, no network needed)
python -m unittest discover -s tests -v

# Run scraper
python scrape_with_notifications.py

# Generate website
python generate_api_site.py
```

### Data files

`data/` holds the tracker's persistent state and **must stay committed** - it is
what makes change alerts, trend detection and the yesterday comparison work. If
it is emptied or ignored, every run looks like a first run.

- `data/latest_rate.json` - last reading
- `data/rate_history.json` - rolling window (last 500 readings)
- `docs/api/archive.json` - full recovered series since Oct 2025

## 📱 Phone Notification Setup

### Option 1: ntfy.sh (Recommended - FREE)

1. Install ntfy app: [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) | [iPhone](https://apps.apple.com/us/app/ntfy/id1625396347)
2. Choose unique topic: `kerala-gold-rate-yourname-123`
3. Subscribe in app
4. Add GitHub secret: `NTFY_TOPIC` = `kerala-gold-rate-yourname-123`

### Option 2: Telegram

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create bot: `/newbot`
3. Get bot token and your chat ID
4. Add GitHub secrets: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

### Option 3: Pushover

1. Create account at [pushover.net](https://pushover.net)
2. Install Pushover app
3. Get user key and create application
4. Add GitHub secrets: `PUSHOVER_TOKEN` and `PUSHOVER_USER`

## 🔍 How It Works

1. **GitHub Actions** runs the scraper on a schedule weighted to Kerala market hours
2. **Plain HTTP + BeautifulSoup** extracts the 24K and 22K rates from GoodReturns.in
   (Selenium is only used as a fallback if that fails)
3. **Comparison** with previous rate triggers notifications
4. **Data** is saved to JSON files
5. **Website** is auto-generated and deployed to GitHub Pages
6. **APIs** serve the data via CDN

## 🎯 Sample Notifications

### 📈 Price Increase Alert
```
🚨 Kerala Gold Rate Alert!

📈 INCREASED by ₹75 (0.8%)

Previous: ₹9,742/g
Current: ₹9,817/g

Time: 28 Jun 2024, 02:30 PM
```

### 📉 Price Decrease Alert
```
⚠️ Kerala Gold Rate Alert!

📉 DECREASED by ₹50 (0.5%)

Previous: ₹9,792/g
Current: ₹9,742/g

Time: 28 Jun 2024, 04:30 PM
```

## 🔄 Monitoring & Logs

- **GitHub Actions**: Check the Actions tab for run logs
- **Website**: Visit your site for current status
- **Notifications**: Test with manual workflow trigger

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## 📜 License

MIT License - feel free to use and modify!

## 🆘 Support

- **Issues**: Use GitHub Issues for bugs/questions
- **Discussions**: Use GitHub Discussions for general help
- **Documentation**: All code is well-documented

## 🎉 Acknowledgments

- **Data Source**: [GoodReturns.in](https://www.goodreturns.in)
- **Infrastructure**: GitHub Actions & Pages
- **Notifications**: Telegram, Pushover, ntfy.sh

---

⭐ **Star this repo** if you find it useful!

Made with ❤️ for gold investors and traders