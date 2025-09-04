# بوت التجميعات - Telegram Question Collection Bot

A comprehensive Telegram bot designed to collect exam questions (Qiyas) from students who have completed their tests. The bot facilitates organized question collection, two-way communication between admins and students, and provides broadcast capabilities.

## Features

### 🎯 Core Features
- **Multi-media Question Reception**: Accepts text, images, PDF files, voice messages, videos, and stickers
- **Blue Button Menu**: Interactive interface with order list and instructions
- **Two-way Reply System**: Seamless communication between admins and students
- **Broadcast System**: Admin can send messages to all users (all media types)
- **Statistics & Export**: Admin commands for data analysis
- **Automated Notifications**: Milestone alerts every 50 questions

### 📱 User Experience
- **Command Menu**: Accessible via the blue button next to the input field
- **Order Tracking**: Users can view all their submitted questions with timestamps
- **Clear Instructions**: Detailed usage guide explaining the reply system

### 👨‍💼 Admin Features
- `/stats` - View question statistics
- `/export` - Download all JSON data files (questions, replies, users, banned users)
- `/broadcast` - Start broadcast mode for announcements
- `/ban <user_id> [reason]` - Ban a user with optional reason
- `/unban <user_id>` - Unban a user
- `/banned` - Show list of banned users
- **Question Management**: Detailed user info with each question
- **Reply System**: Direct communication with students
- **User Management**: Ban/unban system with detailed tracking

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   - `BOT_TOKEN`: Your Telegram bot token from @BotFather
   - `ADMIN_GROUP_ID`: ID of your admin group for question management
4. Run the bot: `python main.py`

## Usage

### For Students
1. Start the bot with `/start`
2. Send questions in any format (text, images, PDF, voice, video)
3. Get confirmation and track your questions via the blue button menu
4. Receive and respond to admin replies

### For Admins
1. Add the bot to your admin group
2. Use `/broadcast` to send announcements to all users
3. Reply to questions in the group to communicate with students
4. Use `/stats` and `/export` for data management

## Architecture

- **Language**: Python 3.11
- **Framework**: python-telegram-bot library
- **Storage**: JSON files (questions_data.json, replies_data.json)
- **Deployment**: Compatible with cloud platforms

## Environment Variables

Create a `.env` file with the following variables:

```
BOT_TOKEN=your_bot_token_here
ADMIN_GROUP_ID=your_admin_group_id_here
```

## Data Storage

The bot stores data in JSON files:
- `questions_data.json`: All submitted questions with metadata
- `replies_data.json`: Reply tracking and conversation threads
- `users_data.json`: User activity and statistics
- `banned_users.json`: Banned users with ban details and reasons

## Deployment

The bot is designed to work on various platforms including:
- Local development
- Replit
- Heroku
- VPS/Cloud servers

## Commands

### User Commands
- `/start` - Start using the bot and see welcome message
- `/help` - Show help information

### Admin Commands (Admin Group Only)
- `/stats` - View question statistics and user counts
- `/export` - Download all data files (questions, replies, users, banned users)
- `/broadcast` - Start broadcast mode to send messages to all users
- `/ban <user_id> [reason]` - Ban a user with optional reason
- `/unban <user_id>` - Unban a user
- `/banned` - Show list of banned users with details

## Support

For support or questions, please contact the development team.