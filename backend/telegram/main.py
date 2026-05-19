"""
Main entry point for NinjaAgent Telegram Bot
"""
import os
import sys
from dotenv import load_dotenv
from backend.telegram.bot import main

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)
        
    # Start the bot
    main()