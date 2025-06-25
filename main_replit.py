#!/usr/bin/env python3
import os
import logging
import sys
import asyncio
import signal
from flask import Flask, jsonify
from datetime import datetime
import threading
import time

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger("main_replit")

# Log startup information
logger.info("Starting Telegram Bot for Replit")
logger.info(f"Python version: {sys.version}")
logger.info(f"Replit environment detected: {bool(os.environ.get('REPL_SLUG'))}")

# Create Flask app for health checks
app = Flask(__name__)
app.config['START_TIME'] = time.time()

# Global bot status
bot_status = {
    'running': False,
    'last_error': None,
    'start_time': None
}

@app.route('/')
def home():
    uptime = time.time() - app.config['START_TIME']
    return jsonify({
        "status": "Server is running!",
        "uptime_seconds": uptime,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bot_running": bot_status['running'],
        "bot_error": bot_status['last_error'],
        "environment": "Replit"
    })

@app.route('/ping')
def ping():
    """Health check endpoint for UptimeRobot"""
    logger.info(f"Health check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return jsonify({
        "status": "ok",
        "message": "pong",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bot_running": bot_status['running'],
        "server_uptime": time.time() - app.config['START_TIME']
    })

@app.route('/status')
def status():
    """Detailed status endpoint"""
    uptime = time.time() - app.config['START_TIME']
    return jsonify({
        "status": "ok",
        "server_uptime": uptime,
        "bot_running": bot_status['running'],
        "bot_start_time": bot_status['start_time'],
        "last_error": bot_status['last_error'],
        "environment": os.environ.get('REPL_SLUG', 'local'),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "replit_url": f"https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co" if os.environ.get('REPL_SLUG') else None
    })

def run_flask_server():
    """Run Flask server in a separate thread"""
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask server on port {port}")
    
    if os.environ.get('REPL_SLUG'):
        logger.info(f"Bot will be available at: https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co")
        logger.info(f"Health check URL: https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co/ping")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")

async def run_telegram_bot():
    """Run the Telegram bot with proper async handling"""
    global bot_status
    
    try:
        logger.info("Importing bot module...")
        import bot
        
        # Check environment variables
        if not bot.BOT_TOKEN:
            raise ValueError("BOT_TOKEN not found in environment variables")
        if not bot.ADMIN_GROUP_ID:
            raise ValueError("ADMIN_GROUP_ID not found in environment variables")
            
        logger.info("Creating Telegram bot application...")
        
        # Create the Application
        application = bot.Application.builder().token(bot.BOT_TOKEN).build()

        # Add handlers
        application.add_handler(bot.CommandHandler("start", bot.start_command))
        application.add_handler(bot.CommandHandler("stats", bot.stats_command))
        
        # Admin group reply handler
        application.add_handler(bot.MessageHandler(
            bot.filters.REPLY & ~bot.filters.COMMAND & bot.filters.Chat(chat_id=bot.ADMIN_GROUP_ID),
            bot.handle_admin_group_reply
        ))
        
        # User message handler
        application.add_handler(bot.MessageHandler(
            ~bot.filters.COMMAND & ~bot.filters.ChatType.CHANNEL & ~bot.filters.ChatType.GROUP,
            bot.handle_user_message
        ))

        # Setup commands
        application.post_init = bot.setup_commands
        
        # Update bot status
        bot_status['running'] = True
        bot_status['start_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bot_status['last_error'] = None
        
        logger.info("Starting Telegram bot polling...")
        
        # Run the bot
        await application.run_polling(allowed_updates=bot.Update.ALL_TYPES)
        
    except Exception as e:
        error_msg = f"Bot error: {e}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
        bot_status['running'] = False
        bot_status['last_error'] = error_msg

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    bot_status['running'] = False
    sys.exit(0)

async def main():
    """Main function that runs everything"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    logger.info("Flask server started in background thread")
    
    # Small delay to let Flask start
    await asyncio.sleep(2)
    
    # Run the Telegram bot in the main thread
    logger.info("Starting Telegram bot in main thread...")
    await run_telegram_bot()

if __name__ == "__main__":
    try:
        # Run everything
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)
