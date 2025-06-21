#!/bin/bash

# Function to log messages with timestamps
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Install dependencies
log "Installing dependencies..."
pip install -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p .data
touch .data/keep_alive

# Set up cron job for periodic pings (if crontab is available)
if command -v crontab &> /dev/null; then
  log "Setting up cron job for periodic pings..."
  (crontab -l 2>/dev/null; echo "*/3 * * * * curl -s https://438ed1b7-c9a8-4764-ad72-982a5753e85f-00-2jpu2pik289up.kirk.replit.dev/ping > /dev/null 2>&1") | crontab -
fi

# Function to restart the bot if it crashes
restart_bot() {
  log "Bot crashed. Restarting in 5 seconds..."
  sleep 5
  log "Restarting bot..."
  python main.py
}

# Start the bot with automatic restart
log "Starting Telegram bot..."
python main.py || restart_bot 