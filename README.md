# THE LAST DANCE - Telegram Support Bot

A Telegram bot that serves as a live support assistant for "THE LAST DANCE" course.

## Features

- Forwards user messages to multiple admin users
- Allows admins to reply directly to users
- Welcome message with user's first name
- Inline keyboard buttons for important links
- Smart handling system that assigns users to specific admins
- Admin release command to free users when admins are unavailable
- Keep-alive functionality to maintain the bot running on Replit

## Replit Deployment Instructions

1. Create a new Replit project and import this repository
2. Set up environment variables in Replit Secrets:
   - Click on "Tools" in the left sidebar
   - Select "Secrets"
   - Add the following secrets:
     - `BOT_TOKEN`: Your Telegram bot token obtained from [@BotFather](https://t.me/BotFather)
     - `ADMIN_IDS`: Comma-separated list of admin user IDs (e.g., `123456789,987654321`)

3. Update the URLs in `bot.py` for the inline keyboard buttons:
   - "جروب المناقشة" - Discussion group URL
   - "القناة الرئيسية" - Main channel URL
   - "بوت الملفات" - Files bot URL
   - "الموقع الإلكتروني" - Website URL

4. Run the bot on Replit:
   - The bot should automatically start when you click "Run"
   - If not, run `python main.py` in the Replit shell

## UptimeRobot Configuration

To keep your bot running 24/7 on Replit:

1. Create an account on [UptimeRobot](https://uptimerobot.com/) if you don't have one
2. Add a new monitor:
   - Select "HTTP(s)" as the monitor type
   - Enter your Replit URL + "/ping" as the URL (e.g., `https://your-repl-name.your-username.repl.co/ping`)
   - Set the monitoring interval to 5 minutes
   - Save the monitor

3. Your bot should now stay awake as UptimeRobot will ping it every 5 minutes

## Local Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with the following content:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_IDS=123456789,987654321
   ```
4. Run the bot:
   ```
   python main.py
   ```

## Usage

- Users can start the bot with `/start` to see the welcome message and buttons
- Any message sent by users will be forwarded to all admins
- Admins can reply to forwarded messages to respond to the original user
- The first admin to reply to a user becomes that user's handler
- Admins can release a user with `/release user_id` if they're unavailable

## Customization

You can customize the welcome message and other texts in the `bot.py` file.

## Deployment on Render.com

This bot is configured for deployment on Render.com. Follow these steps to deploy:

1. Create a new account on [Render.com](https://render.com/) if you don't have one
2. Connect your GitHub repository to Render
3. Create a new Web Service and select your repository
4. Use the following settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 1 main:app`
5. Add the following environment variables:
   - `BOT_TOKEN`: Your Telegram bot token from BotFather
   - `ADMIN_IDS`: Comma-separated list of admin user IDs

The bot will automatically start and stay running without needing external ping services.

## Commands

- `/start` - Start the bot and see welcome message
- `/release <user_id>` - (Admin only) Release a user from your queue so other admins can handle them

## How It Works

1. Users send messages to the bot
2. Messages are forwarded to all admins
3. When an admin replies, they become the handler for that user
4. All future messages from that user go only to the assigned admin
5. Admins can release users with the `/release` command

## License

MIT 