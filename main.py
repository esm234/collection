import os
import logging
import sys
import threading
import time
import signal
from flask import Flask, jsonify
from datetime import datetime

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger("main")

# Log startup information
logger.info("Starting bot application")
logger.info(f"Python version: {sys.version}")
logger.info(f"Running in environment: {os.environ.get('REPLIT_HOSTING', 'local')}")
logger.info(f"Replit Slug: {os.environ.get('REPL_SLUG', 'N/A')}")
logger.info(f"Replit Owner: {os.environ.get('REPL_OWNER', 'N/A')}")

# Check for required environment variables
if not os.environ.get('BOT_TOKEN'):
    logger.warning("BOT_TOKEN environment variable is not set! Make sure to set it in environment variables.")

# Create Flask app for Replit hosting
app = Flask(__name__)
app.config['START_TIME'] = time.time()

@app.route('/')
def home():
    uptime = time.time() - app.config['START_TIME']
    return jsonify({
        "status": "Bot is alive and running!",
        "uptime_seconds": uptime,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "environment": "Replit" if os.environ.get('REPLIT_HOSTING') else "Local"
    })

@app.route('/ping')
def ping():
    """Endpoint specifically for UptimeRobot monitoring"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Health check ping at {current_time}")

    # Check bot thread status
    bot_status = "unknown"
    if 'bot_thread' in globals() and bot_thread:
        bot_status = "running" if bot_thread.is_alive() else "stopped"
    else:
        bot_status = "not_started"

    return jsonify({
        "status": "ok",
        "message": "pong",
        "timestamp": current_time,
        "bot_thread_status": bot_status,
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
        "bot_thread_alive": bot_thread.is_alive() if 'bot_thread' in globals() else False,
        "environment": os.environ.get('REPL_SLUG', 'local'),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": sys.version,
        "replit_url": f"https://{os.environ.get('REPL_SLUG', 'unknown')}.{os.environ.get('REPL_OWNER', 'unknown')}.repl.co" if os.environ.get('REPL_SLUG') else None
    })

# Start bot in a separate thread with proper async handling
def run_bot():
    try:
        logger.info("Importing bot module")
        import bot
        import asyncio
        logger.info("Bot module imported successfully")

        # Create new event loop for this thread
        logger.info("Setting up event loop for bot thread")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Directly call the main function from bot.py
        logger.info("Starting bot.main()")
        bot.main()
    except ImportError as e:
        logger.critical(f"Failed to import bot module: {e}")
        # Don't exit, just log the error
        return
    except Exception as e:
        logger.critical(f"Unexpected error during import or execution: {e}")
        logger.exception("Full traceback:")
        # Don't exit, just log the error
        return

# Global variable for bot thread
bot_thread = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if bot_thread and bot_thread.is_alive():
        logger.info("Stopping bot thread...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start the bot when this module is imported
def start_bot():
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("Bot started in background thread")
    else:
        logger.info("Bot thread is already running")

# Start the bot
start_bot()

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