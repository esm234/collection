# 🚀 Quick Deployment Checklist

## Before Deployment

### ✅ Environment Variables
- [ ] `BOT_TOKEN` - Your Telegram bot token from @BotFather
- [ ] `ADMIN_GROUP_ID` - Your admin group ID (negative number)
- [ ] `ADMIN_IDS` - Comma-separated admin user IDs (optional)

### ✅ Bot Configuration
- [ ] Bot is added to admin group as administrator
- [ ] Bot has necessary permissions in the group
- [ ] Test bot locally first (optional but recommended)

## Replit Setup

### ✅ Project Setup
- [ ] All files uploaded to Replit
- [ ] Dependencies in `requirements.txt` are correct
- [ ] `.replit` configuration is properly set

### ✅ Environment Variables in Replit
- [ ] Go to Secrets (🔒) tab in Replit
- [ ] Add `BOT_TOKEN` with your actual token
- [ ] Add `ADMIN_GROUP_ID` with your group ID
- [ ] Add `ADMIN_IDS` if you want specific admin users

### ✅ Test Run
- [ ] Click "Run" button in Replit
- [ ] Check console for any errors
- [ ] Verify bot responds in Telegram
- [ ] Test health check URL: `https://your-repl.repl.co/ping`

## UptimeRobot Setup

### ✅ Account Setup
- [ ] Create free account at uptimerobot.com
- [ ] Verify email address

### ✅ Monitor Configuration
- [ ] Create new HTTP(s) monitor
- [ ] Use URL: `https://your-repl-name.your-username.repl.co/ping`
- [ ] Set interval to 5 minutes
- [ ] Set timeout to 30 seconds
- [ ] Enable monitor

### ✅ Alert Setup (Optional)
- [ ] Add email contact
- [ ] Configure alert preferences
- [ ] Test alert system

## Post-Deployment

### ✅ Verification
- [ ] Bot responds to messages in admin group
- [ ] UptimeRobot shows monitor as "Up"
- [ ] Health check URLs are accessible:
  - [ ] `/ping` - Returns "ok" status
  - [ ] `/status` - Returns detailed information
  - [ ] `/` - Returns basic status

### ✅ Monitoring
- [ ] Check UptimeRobot dashboard regularly
- [ ] Monitor Replit console for errors
- [ ] Test bot functionality periodically

## Troubleshooting

### Common Issues:
1. **Bot not responding**: Check BOT_TOKEN in Secrets
2. **UptimeRobot shows down**: Verify ping URL is correct
3. **Repl keeps sleeping**: Ensure UptimeRobot is pinging every 5 minutes
4. **Permission errors**: Check bot admin status in group

### Quick Fixes:
- Restart Repl if bot stops responding
- Check Secrets are properly set
- Verify group ID is negative number
- Test URLs manually in browser

## Success Indicators

✅ **Your bot is successfully deployed when:**
- UptimeRobot monitor shows "Up" status
- Bot responds to messages in admin group
- Health check URLs return proper responses
- No errors in Replit console
- Bot stays online for extended periods

## Need Help?

1. Check `REPLIT_SETUP.md` for detailed instructions
2. Review console logs in Replit
3. Test each component individually
4. Verify all environment variables are set correctly

**Happy hosting! 🎉**
