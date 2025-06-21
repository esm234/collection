# THE LAST DANCE - Telegram Support Bot

A Telegram bot that serves as a live support assistant for "THE LAST DANCE" course.

## Features

- Forwards user messages to an admin group chat
- Allows admins to reply directly to users from the group
- Support for various media types (text, photos, documents, videos, voice messages, audio, stickers)
- Welcome message with user's first name
- Inline keyboard buttons for important links
- Simple and efficient message handling through a central admin group
- Keep-alive functionality to maintain the bot running on Replit

## Replit Deployment Instructions

1. Create a new Replit project and import this repository
2. Set up environment variables in Replit Secrets:
   - Click on "Tools" in the left sidebar
   - Select "Secrets"
   - Add the following secrets:
     - `BOT_TOKEN`: Your Telegram bot token obtained from [@BotFather](https://t.me/BotFather)
     - `ADMIN_GROUP_ID`: The ID of your admin group chat (e.g., `-1001234567890`)
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
   ADMIN_GROUP_ID=-1001234567890
   ADMIN_IDS=123456789,987654321
   ```
4. Run the bot:
   ```
   python main.py
   ```

## Usage

- Users can start the bot with `/start` to see the welcome message and buttons
- Any message sent by users will be forwarded to the admin group chat
- Admins can reply to forwarded messages in the group to respond to the original user
- The bot will handle the conversation flow between users and admins

## How to Setup the Admin Group

1. Create a new group in Telegram
2. Add your bot to the group
3. Make the bot an admin in the group (to read all messages)
4. Get the group ID by:
   - Sending a message to the group
   - Forwarding that message to [@getidsbot](https://t.me/getidsbot)
   - Look for the "Forwarded from chat" ID (will be negative, like `-1001234567890`)
5. Use this ID as your `ADMIN_GROUP_ID` environment variable

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
   - `ADMIN_GROUP_ID`: Your admin group chat ID
   - `ADMIN_IDS`: Comma-separated list of admin user IDs

The bot will automatically start and stay running without needing external ping services.

## Commands

- `/start` - Start the bot and see welcome message

## How It Works

1. Users send messages to the bot (text or media)
2. Messages are forwarded to the admin group chat with user information
3. When an admin replies to a message in the group, the reply is sent to the corresponding user
4. The bot maintains the conversation flow between users and admins
5. Media messages (photos, documents, videos, etc.) are properly forwarded in both directions

## License

MIT 