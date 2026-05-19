# NinjaAgent Telegram Bot

This module provides a Telegram bot interface for NinjaAgent that delivers real-time trading signals and technical analysis directly to users.

## Features

- Real-time trading signals
- Technical analysis for tokens
- Portfolio monitoring
- Natural language trading commands
- Direct integration with main trading engine

## Setup

1. Create a Telegram bot via @BotFather
2. Get your bot token
3. Add the token to your .env file:

```
TELEGRAM_BOT_TOKEN=your_telegeam_bot_token_here
```

## Available Commands

- `/signals` - Get latest trading signals
- `/analyze <symbol>` - Get technical analysis for a specific token
- `/portfolio` - View your portfolio
- `/help` - Show help message

The bot will provide real-time alerts and signals to help you make informed trading decisions.