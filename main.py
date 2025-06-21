import os
import logging
import sys
import threading
import time
from flask import Flask

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

# Log startup information
logger.info("Starting bot application")
logger.info(f"Python version: {sys.version}")
logger.info(f"Running in environment: {os.environ.get('RENDER', 'local')}")

# Check for required environment variables
if not os.environ.get('BOT_TOKEN'):
    logger.warning("BOT_TOKEN environment variable is not set! Make sure to set it in environment variables.")

# Create Flask app for Render.com
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

@app.route('/ping')
def ping():
    return "pong"

# Start bot in a separate thread
def run_bot():
    try:
        logger.info("Importing bot module")
        import bot
        logger.info("Bot module imported successfully")
        
        # Directly call the main function from bot.py
        logger.info("Starting bot.main()")
        bot.main()
    except ImportError as e:
        logger.critical(f"Failed to import bot module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during import or execution: {e}")
        sys.exit(1)

# Start the bot when this module is imported
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
logger.info("Bot started in background thread")

# This is used by gunicorn
if __name__ == "__main__":
    # If running directly, start the Flask server too
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 