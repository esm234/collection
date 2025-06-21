from flask import Flask, jsonify
from threading import Thread
import logging
import time
import os
import requests
import random
import threading

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger("keep_alive")

app = Flask('')

@app.route('/')
def home():
    logger.info("Health check endpoint accessed")
    return "Bot is alive and running!"

@app.route('/ping')
def ping():
    """Endpoint specifically for UptimeRobot to ping"""
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"UptimeRobot ping at {current_time}")
    return jsonify({
        "status": "ok",
        "message": "Bot is running",
        "timestamp": current_time
    })

@app.route('/status')
def status():
    """Return detailed status information"""
    uptime = time.time() - app.config.get('START_TIME', time.time())
    return jsonify({
        "status": "ok",
        "uptime_seconds": uptime,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        "environment": os.environ.get('REPL_SLUG', 'local'),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

def self_ping():
    """Periodically ping our own server to keep it alive"""
    repl_slug = os.environ.get('REPL_SLUG')
    repl_owner = os.environ.get('REPL_OWNER')
    
    if repl_slug and repl_owner:
        url = f"https://{repl_slug}.{repl_owner}.repl.co/ping"
    else:
        url = "http://localhost:8080/ping"
    
    while True:
        try:
            # Add a random parameter to prevent caching
            random_param = random.randint(1, 1000000)
            ping_url = f"{url}?nocache={random_param}"
            logger.info(f"Self-pinging at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            response = requests.get(ping_url, timeout=10)
            logger.info(f"Self-ping response: {response.status_code}")
        except Exception as e:
            logger.error(f"Self-ping failed: {e}")
        
        # Sleep for a random time between 4 and 5 minutes
        # This prevents predictable patterns that might be detected by Replit
        sleep_time = random.randint(240, 300)
        time.sleep(sleep_time)

def run():
    try:
        # Store the start time for uptime calculations
        app.config['START_TIME'] = time.time()
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Starting Flask server on port {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")
        # Try to restart after a delay
        time.sleep(10)
        run()

def keep_alive():
    logger.info("Initializing keep-alive server")
    
    # Start the Flask server in a separate thread
    server_thread = Thread(target=run, daemon=True)
    server_thread.start()
    logger.info("Keep-alive server started in background thread")
    
    # Start the self-pinging mechanism in another thread
    logger.info("Starting self-ping mechanism")
    ping_thread = Thread(target=self_ping, daemon=True)
    ping_thread.start()
    logger.info("Self-ping mechanism started in background thread")
    
    # Log the URLs that can be used for monitoring
    repl_slug = os.environ.get('REPL_SLUG')
    repl_owner = os.environ.get('REPL_OWNER')
    if repl_slug and repl_owner:
        logger.info(f"UptimeRobot URL: https://{repl_slug}.{repl_owner}.repl.co/ping")
    else:
        logger.info("Running locally. UptimeRobot can ping: http://localhost:8080/ping") 