#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import logging
import requests
import random
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("anti_sleep.log"), logging.StreamHandler()]
)
logger = logging.getLogger("anti_sleep")

def get_replit_url():
    """Get the Replit URL from environment variables"""
    repl_slug = os.environ.get('REPL_SLUG')
    repl_owner = os.environ.get('REPL_OWNER')
    
    if repl_slug and repl_owner:
        return f"https://{repl_slug}.{repl_owner}.repl.co"
    
    # For your specific URL
    return "https://438ed1b7-c9a8-4764-ad72-982a5753e85f-00-2jpu2pik289up.kirk.replit.dev"

def ping_server():
    """Ping our own server to keep it alive"""
    url = get_replit_url()
    endpoints = ["", "/ping", "/status"]
    
    while True:
        for endpoint in endpoints:
            try:
                # Add a random parameter to prevent caching
                random_param = random.randint(1, 1000000)
                ping_url = f"{url}{endpoint}?nocache={random_param}"
                
                logger.info(f"Pinging {ping_url}")
                start_time = time.time()
                response = requests.get(ping_url, timeout=10)
                elapsed = time.time() - start_time
                
                logger.info(f"Response from {endpoint}: {response.status_code} in {elapsed:.2f}s")
            except Exception as e:
                logger.error(f"Failed to ping {endpoint}: {e}")
            
            # Small delay between endpoint pings
            time.sleep(2)
        
        # Log a status message every hour
        current_time = datetime.now()
        if current_time.minute == 0 and current_time.second < 10:
            logger.info(f"Anti-sleep mechanism has been running for {(time.time() - start_time):.0f} seconds")
        
        # Sleep for a random time between 3 and 4 minutes
        # This is shorter than UptimeRobot's 5 minutes to ensure we stay awake
        sleep_time = random.randint(180, 240)
        logger.info(f"Sleeping for {sleep_time} seconds before next ping")
        time.sleep(sleep_time)

def external_ping():
    """Use external services to ping our server"""
    url = get_replit_url() + "/ping"
    external_services = [
        f"https://ping.gg/ping?url={url}",
        f"https://ping-api.vercel.app/api/ping?url={url}"
    ]
    
    while True:
        for service in external_services:
            try:
                logger.info(f"Using external service: {service}")
                response = requests.get(service, timeout=15)
                logger.info(f"External service response: {response.status_code}")
            except Exception as e:
                logger.error(f"External service failed: {e}")
            
            # Sleep between external service calls
            time.sleep(5)
        
        # Sleep for a longer period between external service ping cycles
        sleep_time = random.randint(600, 900)  # 10-15 minutes
        time.sleep(sleep_time)

def main():
    """Main function to start anti-sleep mechanisms"""
    logger.info("Starting anti-sleep mechanisms")
    
    # Start the self-ping thread
    ping_thread = threading.Thread(target=ping_server, daemon=True)
    ping_thread.start()
    logger.info("Self-ping thread started")
    
    # Start the external ping thread
    external_thread = threading.Thread(target=external_ping, daemon=True)
    external_thread.start()
    logger.info("External ping thread started")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Anti-sleep mechanism stopped by user")
    except Exception as e:
        logger.error(f"Error in main thread: {e}")

if __name__ == "__main__":
    main() 