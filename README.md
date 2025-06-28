# 🥇 Kerala Gold Rate Tracker

Live 24K gold rate tracking with phone notifications - completely FREE!

## 🌐 Live Demo
- **Website**: [https://yourusername.github.io/gold-rate-tracker](https://yourusername.github.io/gold-rate-tracker)
- **API**: [https://yourusername.github.io/gold-rate-tracker/api/latest.json](https://yourusername.github.io/gold-rate-tracker/api/latest.json)

## ✨ Features

- 🔄 **Auto-updates** every 2 hours via GitHub Actions
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
  "rate": 9742.0,
  "currency": "INR",
  "unit": "per gram",
  "purity": "24K",
  "location": "Kerala",
  "timestamp": "2024-06-28T14:30:00.123456",
  "source": "https://www.goodreturns.in/gold-rates/kerala.html",
  "success": true
}
```

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
pip install selenium beautifulsoup4 requests

# Run scraper
python scrape_with_notifications.py

# Generate website
python generate_api_site.py
```

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

1. **GitHub Actions** runs the scraper every 2 hours
2. **Selenium** extracts gold rate from GoodReturns.in
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