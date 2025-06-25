# 🚀 Complete Replit Hosting Guide with UptimeRobot

This guide will walk you through hosting your Telegram bot on Replit and setting up UptimeRobot to keep it running 24/7.

## 📋 Prerequisites

1. **Telegram Bot Token**: Get from [@BotFather](https://t.me/BotFather)
2. **Replit Account**: Sign up at [replit.com](https://replit.com)
3. **UptimeRobot Account**: Sign up at [uptimerobot.com](https://uptimerobot.com) (free)

## 🔧 Step 1: Setup on Replit

### 1.1 Import Your Project
1. Go to [replit.com](https://replit.com)
2. Click "Create Repl"
3. Choose "Import from GitHub" and paste your repository URL
4. Or upload your project files directly

### 1.2 Configure Environment Variables
1. In your Repl, click on "Secrets" (🔒) in the left sidebar
2. Add the following environment variables:

```
BOT_TOKEN = your_actual_bot_token_from_botfather
ADMIN_GROUP_ID = -1001234567890
```

**How to get ADMIN_GROUP_ID:**
1. Create a Telegram group
2. Add your bot to the group as an admin
3. Send a message in the group
4. Forward the message to [@userinfobot](https://t.me/userinfobot)
5. It will show the group ID (negative number)

### 1.3 Test Your Bot
1. Click the "Run" button in Replit
2. Your bot should start and show logs
3. The web interface will be available at your Repl URL

## 🌐 Step 2: Get Your Replit URL

After running your bot, you'll see output like:
```
Replit URL: https://your-repl-name.your-username.repl.co
```

**Important URLs:**
- Main: `https://your-repl-name.your-username.repl.co/`
- Health Check: `https://your-repl-name.your-username.repl.co/ping`
- Status: `https://your-repl-name.your-username.repl.co/status`

## 📊 Step 3: Setup UptimeRobot

### 3.1 Create UptimeRobot Account
1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Sign up for a free account
3. Verify your email

### 3.2 Add Your Bot Monitor
1. Click "Add New Monitor"
2. Choose "HTTP(s)" monitor type
3. Fill in the details:
   - **Friendly Name**: `My Telegram Bot`
   - **URL**: `https://your-repl-name.your-username.repl.co/ping`
   - **Monitoring Interval**: `5 minutes` (free plan)
   - **Monitor Timeout**: `30 seconds`

### 3.3 Configure Alerts (Optional)
1. Add your email for notifications
2. Set up alert contacts
3. Choose when to receive alerts (recommended: when down)

## ⚡ Step 4: Advanced Configuration

### 4.1 Always-On (Replit Hacker Plan)
If you have Replit Hacker plan:
1. Go to your Repl settings
2. Enable "Always On"
3. Your bot will run 24/7 without UptimeRobot

### 4.2 Multiple Monitors (Recommended)
Set up multiple UptimeRobot monitors:
1. **Main Health Check**: `/ping` endpoint
2. **Status Check**: `/status` endpoint  
3. **Root Check**: `/` endpoint

## 🔍 Step 5: Monitoring and Troubleshooting

### 5.1 Check Bot Status
Visit these URLs to monitor your bot:
- `https://your-repl-name.your-username.repl.co/status` - Detailed status
- `https://your-repl-name.your-username.repl.co/ping` - Quick health check

### 5.2 View Logs
1. In Replit, check the Console tab for real-time logs
2. Logs are also saved to `bot.log` file

### 5.3 Common Issues

**Bot not responding:**
- Check if BOT_TOKEN is correct in Secrets
- Verify ADMIN_GROUP_ID is set properly
- Check logs for error messages

**Repl going to sleep:**
- Ensure UptimeRobot is pinging every 5 minutes
- Check that the ping URL is correct
- Verify UptimeRobot monitor is active

**UptimeRobot showing down:**
- Check if your Repl is running
- Verify the ping URL is accessible
- Check Replit status page for outages

## 📈 Step 6: Optimization Tips

### 6.1 Reduce Resource Usage
- The bot automatically manages memory
- Logs are rotated to prevent disk space issues
- Self-ping mechanism prevents sleep

### 6.2 Backup Important Data
- User data is stored in `users_data.json`
- This file is automatically backed up in Replit
- Consider periodic exports for safety

### 6.3 Monitor Performance
- Use `/status` endpoint to check uptime
- Monitor response times in UptimeRobot
- Check memory usage in Replit

## 🎉 You're Done!

Your Telegram bot is now:
- ✅ Hosted on Replit
- ✅ Monitored by UptimeRobot  
- ✅ Running 24/7 (as much as possible on free plan)
- ✅ Automatically restarting if it crashes
- ✅ Self-pinging to stay awake

## 📞 Support

If you encounter issues:
1. Check the logs in Replit Console
2. Verify all environment variables are set
3. Test the ping URL manually in your browser
4. Check UptimeRobot dashboard for monitor status

**Happy botting! 🤖**
