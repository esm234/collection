#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("uptime_checker")

def get_replit_url():
    """Get the Replit URL from environment variables"""
    repl_slug = os.environ.get('REPL_SLUG')
    repl_owner = os.environ.get('REPL_OWNER')
    
    if repl_slug and repl_owner:
        return f"https://{repl_slug}.{repl_owner}.repl.co"
    else:
        return "http://localhost:8080"  # Default for local testing

def check_endpoint(url, endpoint):
    """Check if an endpoint is accessible"""
    full_url = f"{url}/{endpoint}"
    try:
        logger.info(f"Checking {full_url}...")
        start_time = time.time()
        response = requests.get(full_url, timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            logger.info(f"✅ {endpoint} endpoint is accessible! Response time: {elapsed:.2f}s")
            logger.info(f"Response: {response.text[:100]}...")
            return True
        else:
            logger.error(f"❌ {endpoint} endpoint returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"❌ Failed to access {endpoint} endpoint: {e}")
        return False

def main():
    """Main function to check if UptimeRobot can access the bot"""
    logger.info("Starting UptimeRobot accessibility check")
    
    base_url = get_replit_url()
    logger.info(f"Using base URL: {base_url}")
    
    # Check root endpoint
    root_ok = check_endpoint(base_url, "")
    
    # Check ping endpoint (used by UptimeRobot)
    ping_ok = check_endpoint(base_url, "ping")
    
    # Check status endpoint
    status_ok = check_endpoint(base_url, "status")
    
    # Summary
    logger.info("\n--- Summary ---")
    logger.info(f"Root endpoint: {'✅ OK' if root_ok else '❌ Failed'}")
    logger.info(f"Ping endpoint: {'✅ OK' if ping_ok else '❌ Failed'}")
    logger.info(f"Status endpoint: {'✅ OK' if status_ok else '❌ Failed'}")
    
    if ping_ok:
        logger.info("\n✅ UptimeRobot should be able to access your bot!")
        logger.info(f"UptimeRobot URL to use: {base_url}/ping")
    else:
        logger.error("\n❌ UptimeRobot may not be able to access your bot.")
        logger.error("Please check your Replit configuration and make sure the bot is running.")
    
    return 0 if all([root_ok, ping_ok, status_ok]) else 1

if __name__ == "__main__":
    sys.exit(main()) 