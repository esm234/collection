#!/bin/bash

# Function to log messages with timestamps
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if bot is running
check_bot() {
  if pgrep -f "python.*main.py" > /dev/null; then
    return 0
  else
    return 1
  fi
}

# Function to restart the bot if it crashes
restart_bot() {
  log "Bot crashed or stopped. Restarting in 10 seconds..."
  sleep 10
  log "Restarting bot..."
  python main.py &
  BOT_PID=$!
  log "Bot restarted with PID: $BOT_PID"
}

# Function to monitor bot health
monitor_bot() {
  while true; do
    sleep 30
    if ! check_bot; then
      log "Bot process not found. Attempting restart..."
      restart_bot
    fi
  done
}

# Cleanup function
cleanup() {
  log "Received termination signal. Cleaning up..."
  pkill -f "python.*main.py"
  exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Install dependencies
log "Installing dependencies..."
pip install -r requirements.txt --quiet

# Create data directory if it doesn't exist
mkdir -p .data
touch .data/keep_alive

# Create logs directory
mkdir -p logs

# Set environment variables for Replit
export REPLIT_HOSTING=1
export PYTHONUNBUFFERED=1

# Get Replit URL for monitoring
if [ -n "$REPL_SLUG" ] && [ -n "$REPL_OWNER" ]; then
  REPLIT_URL="https://${REPL_SLUG}.${REPL_OWNER}.repl.co"
  log "Replit URL: $REPLIT_URL"

  # Set up self-ping using curl (if available)
  if command -v curl &> /dev/null; then
    log "Setting up self-ping mechanism..."
    (
      while true; do
        sleep 180  # 3 minutes
        curl -s "$REPLIT_URL/ping" > /dev/null 2>&1 || log "Self-ping failed"
      done
    ) &
    PING_PID=$!
    log "Self-ping started with PID: $PING_PID"
  fi
fi

# Start the bot
log "Starting Telegram bot..."
python main.py &
BOT_PID=$!
log "Bot started with PID: $BOT_PID"

# Start monitoring in background
monitor_bot &
MONITOR_PID=$!
log "Monitor started with PID: $MONITOR_PID"

# Keep the script running
log "All processes started. Bot is now running on Replit."
log "Health check URL: $REPLIT_URL/ping"
log "Status URL: $REPLIT_URL/status"

# Wait for the main bot process
wait $BOT_PID