import os
import logging
import sys
import threading
import time

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
logger.info(f"Running in environment: {os.environ.get('REPL_SLUG', 'local')}")

# Check for required environment variables
if not os.environ.get('BOT_TOKEN'):
    logger.warning("BOT_TOKEN environment variable is not set! Make sure to set it in Replit Secrets.")

# Start anti-sleep mechanism in a separate thread
def start_anti_sleep():
    try:
        logger.info("Starting anti-sleep mechanism")
        import anti_sleep
        anti_sleep_thread = threading.Thread(target=anti_sleep.main, daemon=True)
        anti_sleep_thread.start()
        logger.info("Anti-sleep mechanism started in background thread")
    except ImportError:
        logger.warning("Anti-sleep module not found, continuing without it")
    except Exception as e:
        logger.error(f"Failed to start anti-sleep mechanism: {e}")

# Start anti-sleep in background
start_anti_sleep()

# Import and run the bot
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