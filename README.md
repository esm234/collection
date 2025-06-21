# THE LAST DANCE - Telegram Support Bot

A Telegram bot that serves as a live support assistant for "THE LAST DANCE" course.

## Features

- Forwards user messages to multiple admin users
- Allows admins to reply directly to users
- Welcome message with user's first name
- Inline keyboard buttons for important links
- In-memory storage (no database required)

## Setup Instructions

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
   Replace `your_telegram_bot_token_here` with your actual Telegram bot token obtained from [@BotFather](https://t.me/BotFather)
   Replace `123456789,987654321` with comma-separated list of admin user IDs

4. Update the URLs in `bot.py` for the inline keyboard buttons:
   - "جروب المناقشة" - Discussion group URL
   - "القناة الرئيسية" - Main channel URL
   - "بوت الملفات" - Files bot URL
   - "الموقع الإلكتروني" - Website URL

5. Run the bot:
   ```
   python bot.py
   ```

## Usage

- Users can start the bot with `/start` to see the welcome message and buttons
- Any message sent by users will be forwarded to all admins
- Admins can reply to forwarded messages to respond to the original user

## Customization

You can customize the welcome message and other texts in the `bot.py` file. 