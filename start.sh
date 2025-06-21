#!/bin/bash

# Start the bot
echo "Starting Telegram bot..."
python main.py &
BOT_PID=$!

# Wait a bit for the bot to initialize
sleep 10

# Start the monitor
echo "Starting monitor..."
python monitor.py &
MONITOR_PID=$!

# Function to handle termination
cleanup() {
    echo "Stopping processes..."
    kill $BOT_PID
    kill $MONITOR_PID
    exit 0
}

# Register the cleanup function for when the script receives SIGINT or SIGTERM
trap cleanup SIGINT SIGTERM

# Keep the script running
echo "Both processes started. Press Ctrl+C to stop."
wait 