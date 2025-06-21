#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import logging
import subprocess
import requests
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("monitor")

def check_web_server():
    """Check if the web server is responding"""
    try:
        response = requests.get("http://localhost:8080/ping", timeout=5)
        if response.status_code == 200:
            logger.info("Web server is running")
            return True
        else:
            logger.warning(f"Web server returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Web server check failed: {e}")
        return False

def restart_bot():
    """Restart the bot process"""
    try:
        logger.info("Attempting to restart the bot")
        # Kill any existing python processes running main.py
        try:
            if os.name == 'nt':  # Windows
                os.system('taskkill /f /im python.exe /fi "WINDOWTITLE eq main.py"')
            else:  # Linux/Mac
                os.system("pkill -f 'python main.py'")
        except Exception as e:
            logger.warning(f"Error killing existing processes: {e}")
        
        # Start the bot in a new process
        if os.name == 'nt':  # Windows
            process = subprocess.Popen(["python", "main.py"], 
                                      creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            process = subprocess.Popen(["python", "main.py"],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        
        logger.info(f"Bot restarted with PID {process.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        return False

def main():
    """Main monitoring function"""
    logger.info("Bot monitor started")
    
    while True:
        if not check_web_server():
            logger.warning("Web server not responding, restarting bot")
            restart_bot()
            # Wait for bot to start up
            time.sleep(30)
        else:
            # Log status every hour
            current_time = datetime.now()
            if current_time.minute == 0 and current_time.second < 10:
                logger.info(f"Bot monitor running - {current_time}")
        
        # Check every minute
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception in monitor: {e}")
        sys.exit(1) 