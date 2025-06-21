import os
import logging
import sys

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