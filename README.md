# 🎬 TikTok HD Downloader Bot

A powerful Telegram bot that downloads TikTok videos in **ultra-high quality** without watermarks. Features advanced multi-API architecture with TikDownloader.io integration for maximum quality downloads.

<div align="center">

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/github.com/losthumanity/TikDownloader)

</div>

## ✨ Features

- 🏆 **Ultra HD Quality** - Up to **42MB+ files** with TikDownloader.io (13x larger than standard)
- ✅ **No Watermarks** - Clean videos without TikTok branding  
- � **Smart Fallback System** - Primary: TikDownloader.io → Backup: TikWM → Alternative: MusicalDown
- 🎵 **Original Audio** - Maintains original audio quality
- 🛡️ **Robust Error Handling** - Graceful fallbacks and user feedback
- 📱 **User-Friendly Interface** - Interactive buttons and clear instructions
- 📊 **Statistics Tracking** - Built-in analytics and monitoring
- 🌐 **Free Deployment** - Ready for Railway, Render, Heroku, and more
- ⚡ **Optimized Performance** - Extended timeouts for large file downloads

## 🚀 Quick Start

### 1. Create Your Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Use `/newbot` command
3. Follow the instructions to get your bot token
4. Copy the token for later use

### 2. Local Development

```bash
# Clone this repository
git clone https://github.com/losthumanity/TikDownloader.git
cd TikDownloader

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env file with your bot token (KEEP THIS PRIVATE!)
# TELEGRAM_BOT_TOKEN=your_actual_bot_token_from_botfather

# Run the bot
python main.py
```

### 3. Test Your Bot

1. Start a chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Send any TikTok video link
4. Wait for your HD video download!

## 🌐 Free Deployment Options

### Option 1: Railway (Recommended)

Railway offers the best free tier with automatic HTTPS and easy deployment.

1. **Fork this repository** [losthumanity/TikDownloader](https://github.com/losthumanity/TikDownloader) to your GitHub
2. **Sign up at [Railway](https://railway.app)** with GitHub
3. **Create New Project** → Deploy from GitHub repo
4. **Add Environment Variable**: `TELEGRAM_BOT_TOKEN` = your bot token
5. **Deploy** - Railway will automatically build and deploy!

**Railway Benefits:**
- ✅ 500 hours/month free
- ✅ Automatic HTTPS 
- ✅ Zero configuration
- ✅ GitHub integration

### Option 2: Render

1. **Fork this repository** [losthumanity/TikDownloader](https://github.com/losthumanity/TikDownloader)
2. **Sign up at [Render](https://render.com)**
3. **New Web Service** → Connect your repo
4. **Configuration:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
5. **Environment Variables:**
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `WEBHOOK_URL` = your Render app URL
6. **Deploy**

**Render Benefits:**
- ✅ 750 hours/month free
- ✅ Automatic SSL
- ✅ Easy scaling

### Option 3: Heroku

1. **Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)**
2. **Login and create app:**
```bash
heroku login
heroku create your-bot-name
```
3. **Set environment variables:**
```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_token_here
heroku config:set WEBHOOK_URL=https://your-bot-name.herokuapp.com
```
4. **Deploy:**
```bash
git push heroku main
```

**Heroku Benefits:**
- ✅ 550-1000 hours/month free
- ✅ Easy CLI deployment
- ✅ Add-ons ecosystem

## 📁 Project Structure

```
TikDownloader/
├── 📄 main.py              # Main launcher
├── 🤖 bot.py               # Telegram bot logic
├── 📥 tiktok_downloader.py # TikTok download engine
├── 🏥 health_server.py     # Health check server
├── 📦 requirements.txt     # Python dependencies
├── 🐳 Dockerfile          # Docker configuration
├── 🚂 railway.json        # Railway deployment config
├── 🎨 render.yaml         # Render deployment config
├── 📋 Procfile           # Heroku deployment config
├── 🐍 runtime.txt        # Python version specification
├── 🔐 .env.example       # Environment variables template
├── 📝 README.md          # This file
└── 🚫 .gitignore         # Git ignore rules
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set these in your deployment platform:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Optional - for webhook mode (production)
WEBHOOK_URL=https://your-deployment-url.com
PORT=8443

# Optional - for debugging
DEBUG=False

# Optional - admin notifications
ADMIN_CHAT_ID=your_telegram_user_id
```

### Bot Configuration

The bot automatically detects:
- 🔍 **Development vs Production** mode
- 🌐 **Webhook vs Polling** based on `WEBHOOK_URL`
- 🐳 **Docker environment** for optimal settings

## 🛠️ API Endpoints Used

The bot uses a **smart multi-API architecture** prioritized by quality:

1. **🏆 TikDownloader.io** - **Ultra HD Primary** (up to 42MB+ files, 8K quality)
2. **🥈 tikwm.com** - HD Backup (3-4MB files, 1080p quality)  
3. **🥉 musicaldown.com** - Standard Backup
4. **🔄 Fallback scraping** - Direct TikTok page parsing

**Quality Comparison:**
- **TikDownloader.io:** 42.93 MB ⭐ (13x larger files)
- **TikWM:** 3.31 MB (Standard HD)
- **Automatic failover** if primary API is unavailable

## 🎯 Supported URL Formats

- `https://www.tiktok.com/@username/video/1234567890`
- `https://vm.tiktok.com/ABC123DEF/`
- `https://vt.tiktok.com/ABC123/`
- `https://tiktok.com/t/ABC123/`

## 📊 Bot Commands

- `/start` - Welcome message and main menu
- `/help` - Detailed help and instructions  
- `/stats` - Bot usage statistics
- 📱 **Send TikTok URL** - Download video automatically

## 🎛️ Interactive Features

- 📱 **How to get TikTok link** - Step-by-step guide
- ⚙️ **Quality settings** - HD/Standard options
- 📊 **Live statistics** - Real-time bot metrics
- 🔄 **Retry mechanisms** - Automatic error recovery

## 🧪 Testing

Test the bot locally:

```bash
# Run bot in local mode (polling)
python main.py

# Test individual components
python -c "from tiktok_downloader import download_tiktok_video; import asyncio; print(asyncio.run(download_tiktok_video('TIKTOK_URL_HERE')))"
```

## 📈 Monitoring

### Health Check Endpoints

- `GET /health` - Bot health status
- `GET /` - Bot information and uptime
- `POST /webhook` - Telegram webhook endpoint

### Logging

The bot logs all activities:
- ✅ Successful downloads
- ❌ Failed attempts  
- 📊 User statistics
- 🐛 Error details

## 🚨 Troubleshooting

### Common Issues

**"Invalid TikTok URL"**
- ✅ Check URL format
- ✅ Try copying link again from TikTok

**"Download failed"**
- ✅ Video might be private
- ✅ Try again in a few seconds
- ✅ Check if video still exists

**"File too large"**
- ✅ Telegram has 50MB limit
- ✅ Try shorter videos

**Bot not responding**
- ✅ Check deployment logs
- ✅ Verify bot token
- ✅ Check environment variables

### Deployment Issues

**Railway:**
```bash
# Check logs
railway logs

# Restart service  
railway service restart
```

**Render:**
- Check logs in Render dashboard
- Verify environment variables
- Check build logs for errors

**Heroku:**
```bash
# Check logs
heroku logs --tail

# Restart dyno
heroku restart
```

## 🔒 Security & Privacy

- 🛡️ **No data storage** - Videos are processed and sent immediately
- 🔐 **Secure APIs** - All requests use HTTPS
- 🚫 **No user tracking** - Only basic statistics
- ♻️ **Temporary files** - Auto-cleanup after processing
- 🔑 **Token Security** - Never commit your actual bot token to Git!

### ⚠️ Important Security Notes

- **NEVER** commit your `.env` file with real tokens
- **ALWAYS** use `.env.example` as a template only
- **KEEP** your bot token private and secure
- **USE** environment variables in production deployments

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/losthumanity/TikDownloader/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/losthumanity/TikDownloader/discussions)
- 🌟 **Stars**: If this helps you, please star the repo!

## 🌟 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API
- [tikwm.com](https://www.tikwm.com/) - TikTok API service
- [Railway](https://railway.app) - Deployment platform
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video download utilities

---

<div align="center">

**⭐ If this project helps you, please give it a star! ⭐**

Made with ❤️ for the Telegram community

[🚀 Deploy on Railway](https://railway.app) • [🎨 Deploy on Render](https://render.com) • [📱 Deploy on Heroku](https://heroku.com)

</div>