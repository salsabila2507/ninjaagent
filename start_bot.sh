#!/bin/bash
set -e

export TELEGRAM_BOT_TOKEN=8519702355:AAFdHDt_13r0Psn_uizxbaIXXHH0gCbYIpA
export PYTHONPATH=/root/NinjaAgent:$PYTHONPATH

echo "Starting NinjaAgent Telegram Bot..."
echo "Please wait..."

# Kill existing bot instances
echo "Checking for existing bot instances..."
pkill -f "python3 backend/telegram/main.py" || true
pkill -f "python3 backend/telegram/bot.py" || true

sleep 5

# Check if the old process is still running
if pgrep -f "python3 backend/telegram" > /dev/null; then
    echo "Error: Could not kill existing bot instances."
    exit 1
fi

# Run the bot
echo "Starting bot..."
python3 backend/telegram/bot.py