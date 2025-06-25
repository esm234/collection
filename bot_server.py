#!/usr/bin/env python3
"""
Final Solution: Telegram Bot Server for Replit
Uses manual polling to avoid event loop conflicts
"""

import os
import logging
import sys
import asyncio
import signal
from datetime import datetime
import time
import threading
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger("bot_server")

# Global status
bot_status = {
    'start_time': time.time(),
    'running': False,
    'last_error': None,
    'messages_processed': 0
}

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    uptime = time.time() - bot_status['start_time']
    return jsonify({
        "status": "Telegram Bot Server Running",
        "uptime_seconds": uptime,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        "bot_running": bot_status['running'],
        "messages_processed": bot_status['messages_processed'],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/ping')
def ping():
    """Health check for UptimeRobot"""
    logger.info("Health check ping")
    return jsonify({
        "status": "ok",
        "message": "pong",
        "bot_running": bot_status['running'],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/status')
def status():
    """Detailed status"""
    uptime = time.time() - bot_status['start_time']
    return jsonify({
        "status": "ok",
        "uptime": uptime,
        "bot_running": bot_status['running'],
        "messages_processed": bot_status['messages_processed'],
        "last_error": bot_status['last_error'],
        "replit_url": f"https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co" if os.environ.get('REPL_SLUG') else None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

class TelegramBotHandler:
    def __init__(self):
        self.bot = None
        self.application = None
        self.last_update_id = 0
        
    async def initialize(self):
        """Initialize the bot"""
        try:
            logger.info("Initializing Telegram bot...")
            
            # Import bot module
            import bot
            from telegram import Bot
            from telegram.ext import Application
            
            # Validate environment
            if not bot.BOT_TOKEN:
                raise ValueError("BOT_TOKEN not found")
            if not bot.ADMIN_GROUP_ID:
                raise ValueError("ADMIN_GROUP_ID not found")
            
            # Create bot instance
            self.bot = Bot(token=bot.BOT_TOKEN)
            
            # Test bot connection
            bot_info = await self.bot.get_me()
            logger.info(f"Bot connected: @{bot_info.username}")
            
            # Import handler functions
            self.start_command = bot.start_command
            self.stats_command = bot.stats_command
            self.handle_admin_group_reply = bot.handle_admin_group_reply
            self.handle_user_message = bot.handle_user_message
            self.ADMIN_GROUP_ID = bot.ADMIN_GROUP_ID
            
            bot_status['running'] = True
            logger.info("Bot initialized successfully")
            return True
            
        except Exception as e:
            error_msg = f"Bot initialization failed: {e}"
            logger.error(error_msg)
            bot_status['last_error'] = error_msg
            bot_status['running'] = False
            return False
    
    async def process_update(self, update):
        """Process a single update"""
        try:
            from telegram import Update
            from telegram.ext import CallbackContext
            
            # Create context
            context = CallbackContext(self.application) if self.application else None
            
            if update.message:
                message = update.message
                
                # Handle commands
                if message.text and message.text.startswith('/'):
                    if message.text.startswith('/start'):
                        await self.start_command(update, context)
                    elif message.text.startswith('/stats'):
                        await self.stats_command(update, context)
                
                # Handle admin group replies
                elif (message.reply_to_message and 
                      message.chat.id == self.ADMIN_GROUP_ID):
                    await self.handle_admin_group_reply(update, context)
                
                # Handle user messages
                elif (message.chat.type == 'private'):
                    await self.handle_user_message(update, context)
                
                bot_status['messages_processed'] += 1
                
        except Exception as e:
            logger.error(f"Error processing update: {e}")
    
    async def poll_updates(self):
        """Manual polling for updates"""
        logger.info("Starting manual polling...")
        
        while bot_status['running']:
            try:
                # Get updates
                updates = await self.bot.get_updates(
                    offset=self.last_update_id + 1,
                    timeout=10,
                    allowed_updates=['message']
                )
                
                # Process each update
                for update in updates:
                    await self.process_update(update)
                    self.last_update_id = update.update_id
                
                # Small delay to prevent hammering
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)  # Wait longer on error

async def run_bot():
    """Run the bot with manual polling"""
    handler = TelegramBotHandler()
    
    if await handler.initialize():
        logger.info("Starting bot polling...")
        await handler.poll_updates()
    else:
        logger.error("Failed to initialize bot")

def run_flask():
    """Run Flask server"""
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask server on port {port}")
    
    if os.environ.get('REPL_SLUG'):
        url = f"https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co"
        logger.info(f"Bot URL: {url}")
        logger.info(f"Health check: {url}/ping")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def signal_handler(signum, frame):
    """Handle shutdown"""
    logger.info(f"Received signal {signum}, shutting down...")
    bot_status['running'] = False
    sys.exit(0)

async def main():
    """Main function"""
    logger.info("🚀 Starting Telegram Bot Server for Replit")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Replit: {os.environ.get('REPL_SLUG', 'Not detected')}")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server started in background")
    
    # Wait for Flask to start
    await asyncio.sleep(2)
    
    # Run the bot
    await run_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)
