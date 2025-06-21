#!/bin/bash

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the bot
echo "Starting Telegram bot..."
python main.py 