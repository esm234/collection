import os
import logging
import sys
import threading
import time
import signal
from flask import Flask, jsonify
from datetime import datetime
import asyncio

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger("main_simple")

# Log startup information
logger.info("Starting bot application (Simple Version)")
logger.info(f"Python version: {sys.version}")
logger.info(f"Running in environment: {os.environ.get('REPLIT_HOSTING', 'local')}")

# Check for required environment variables
if not os.environ.get('BOT_TOKEN'):
    logger.warning("BOT_TOKEN environment variable is not set!")

# Create Flask app for Replit hosting
app = Flask(__name__)
app.config['START_TIME'] = time.time()

# Global variables
bot_application = None
bot_running = False

@app.route('/')
def home():
    uptime = time.time() - app.config['START_TIME']
    return jsonify({
        "status": "Bot server is running!",
        "uptime_seconds": uptime,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bot_status": "running" if bot_running else "stopped",
        "environment": "Replit" if os.environ.get('REPLIT_HOSTING') else "Local"
    })

@app.route('/ping')
def ping():
    """Endpoint specifically for UptimeRobot monitoring"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Health check ping at {current_time}")
    
    return jsonify({
        "status": "ok",
        "message": "pong",
        "timestamp": current_time,
        "bot_running": bot_running,
        "server_running": True
    })

@app.route('/status')
def status():
    """Detailed status endpoint"""
    uptime = time.time() - app.config['START_TIME']
    return jsonify({
        "status": "ok",
        "uptime_seconds": uptime,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        "bot_running": bot_running,
        "environment": os.environ.get('REPL_SLUG', 'local'),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": sys.version,
        "replit_url": f"https://{os.environ.get('REPL_SLUG', 'unknown')}.{os.environ.get('REPL_OWNER', 'unknown')}.repl.co" if os.environ.get('REPL_SLUG') else None
    })

@app.route('/restart')
def restart_bot():
    """Endpoint to restart the bot"""
    global bot_running
    try:
        logger.info("Restart requested via web endpoint")
        start_bot_async()
        return jsonify({"status": "ok", "message": "Bot restart initiated"})
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        return jsonify({"status": "error", "message": str(e)})

def start_bot_async():
    """Start the bot in the background"""
    global bot_application, bot_running
    
    try:
        logger.info("Starting bot asynchronously...")
        
        # Import bot module
        import bot
        
        # Create the Application
        bot_application = bot.Application.builder().token(bot.BOT_TOKEN).build()

        # Add command handlers
        bot_application.add_handler(bot.CommandHandler("start", bot.start_command))
        bot_application.add_handler(bot.CommandHandler("stats", bot.stats_command))
        
        # Add message handlers for admin group
        bot_application.add_handler(bot.MessageHandler(
            bot.filters.REPLY & ~bot.filters.COMMAND & bot.filters.Chat(chat_id=bot.ADMIN_GROUP_ID),
            bot.handle_admin_group_reply
        ))
        
        # Add message handlers for user messages (all types)
        bot_application.add_handler(bot.MessageHandler(
            ~bot.filters.COMMAND & ~bot.filters.ChatType.CHANNEL & ~bot.filters.ChatType.GROUP,
            bot.handle_user_message
        ))

        # Setup bot on startup
        bot_application.post_init = bot.setup_commands
        
        # Start polling in a separate thread
        def run_polling():
            global bot_running
            try:
                logger.info("Starting bot polling...")
                bot_running = True
                
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run the bot
                bot_application.run_polling(allowed_updates=bot.Update.ALL_TYPES)
            except Exception as e:
                logger.error(f"Bot polling error: {e}")
                bot_running = False
        
        # Start in daemon thread
        bot_thread = threading.Thread(target=run_polling, daemon=True)
        bot_thread.start()
        logger.info("Bot started successfully in background thread")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        logger.exception("Full traceback:")
        bot_running = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global bot_running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    bot_running = False
    if bot_application:
        try:
            bot_application.stop()
        except:
            pass
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start the bot when this module is imported
logger.info("Initializing bot...")
start_bot_async()

# This is used by gunicorn and direct execution
if __name__ == "__main__":
    # If running directly, start the Flask server too
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Bot URL will be: https://{os.environ.get('REPL_SLUG', 'localhost')}.{os.environ.get('REPL_OWNER', 'local')}.repl.co" if os.environ.get('REPL_SLUG') else f"http://localhost:{port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        sys.exit(1)
