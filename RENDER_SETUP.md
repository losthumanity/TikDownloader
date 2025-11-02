# 🏆 TikTok HD Downloader Bot - Render Free Tier Setup Guide

## 🚨 **Render Free Tier Limitations**

### **Sleep Behavior:**
- **Sleeps after:** 15 minutes of inactivity
- **Wake up time:** 50+ seconds on first request
- **Monthly usage:** 750 hours free (31 days = 744 hours)
- **Automatic restart:** Yes, when requests come in

## 🛡️ **Solutions Implemented**

### **✅ Built-in Keep-Alive Service**
- **Internal pinger:** Pings `/health` every 10 minutes
- **Prevents sleep:** Keeps service active during low usage
- **Auto-enabled:** Only on Render free tier

### **✅ Fast Wake-Up Endpoints**
- **`/health`** - Full health check (updates activity)
- **`/ping`** - Quick pong response
- **`/wake`** - Dedicated wake-up endpoint

### **✅ External Keep-Alive (Recommended)**

**Option A: UptimeRobot (Free)**
1. Sign up at [UptimeRobot.com](https://uptimerobot.com)
2. Add monitor: `https://your-app.onrender.com/ping`
3. Check interval: **5 minutes**
4. Monitor type: **HTTP(s)**

**Option B: Cronitor (Free)**
1. Sign up at [Cronitor.io](https://cronitor.io)
2. Create heartbeat monitor
3. Set URL: `https://your-app.onrender.com/wake`
4. Interval: **10 minutes**

**Option C: Better Stack (Free)**
1. Sign up at [BetterStack.com](https://betterstack.com)
2. Create uptime monitor
3. URL: `https://your-app.onrender.com/health`
4. Check every **5 minutes**

## 📊 **How It Works on Render**

### **🟢 Normal Operation (24/7 Active)**
```
User sends TikTok link → Bot responds instantly (2-5 seconds)
Keep-alive pings every 10 minutes → Service stays awake
External monitor pings every 5 minutes → Extra insurance
```

### **🟡 If Service Sleeps (Rare)**
```
User sends TikTok link → 50+ second delay (wake up)
Bot processes request → Normal speed afterwards
Keep-alive resumes → Service stays active again
```

### **🔄 Auto-Recovery**
```
If bot crashes → Render auto-restarts
If memory issues → Process restarts automatically
If webhook fails → Bot switches to polling (fallback)
```

## 🎯 **Expected Performance**

### **Response Times:**
- **Active service:** 2-5 seconds
- **Sleeping service:** 50-60 seconds (first request only)
- **After wake-up:** Normal speed

### **Availability:**
- **99%+ uptime** with external monitoring
- **24/7 operation** for active bots
- **Auto-restart** on crashes

### **User Experience:**
- **Most requests:** Instant response
- **Rare wake-up:** One slow response, then normal
- **No manual intervention** required

## 🔧 **Render Configuration**

### **Environment Variables:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
RENDER_EXTERNAL_URL=https://your-app.onrender.com
RENDER=true
```

### **Service Settings:**
```yaml
- Build Command: pip install -r requirements.txt
- Start Command: python main.py
- Health Check Path: /health
- Port: 10000 (auto-detected)
```

## 📈 **Monitoring Your Bot**

### **Built-in Endpoints:**
- **`/`** - Bot information and status
- **`/health`** - Detailed health metrics
- **`/ping`** - Quick availability check

### **What to Monitor:**
- **Uptime percentage** (should be 99%+)
- **Response time** (usually under 5 seconds)
- **Error rate** (should be minimal)

## 💡 **Best Practices**

### **✅ DO:**
- Set up external monitoring (UptimeRobot recommended)
- Monitor your bot's health endpoint
- Check logs if issues occur
- Use webhook mode for better performance

### **❌ DON'T:**
- Rely only on internal keep-alive
- Set ping intervals too frequent (<5 minutes)
- Ignore slow response complaints
- Deploy without monitoring

## 🎉 **Bottom Line**

**Yes, your bot will work 24/7 on Render free tier with this setup!**

- ✅ **Auto-starts** when someone sends a message
- ✅ **Stays active** with keep-alive services
- ✅ **Self-recovers** from crashes
- ✅ **Zero manual intervention** needed
- ✅ **Works locally** and on Render seamlessly

**The only downside:** Occasional 50-second delay if service sleeps (rare with monitoring).