# Technical Analysis Engine for NinjaAgent

This module provides real-time market analysis and trading signals for the NinjaAgent trading assistant.

## Features

- Real-time technical analysis
- Multiple indicator support (RSI, MACD, Bollinger Bands)
- Customizable signal generation
- Market trend analysis

## Supported Indicators

1. **RSI (Relative Strength Index)** - Momentum indicator
2. **MACD (Moving Average Convergence Divergence)** - Trend following indicator
3. **Bollinger Bands** - Volatility indicator
4. **Moving Averages** - Trend direction indicator

## Usage

The technical analysis engine integrates with the Injective Protocol to provide real-time market insights and trading signals that can be delivered via:
- REST API
- WebSocket streams
- Telegram bot alerts

## Signal Types

- **BUY** - Strong buy signal
- **SELL** - Strong sell signal
- **HOLD** - Market neutral, wait for breakout
- **NEUTRAL** - Market stable, no strong direction

The engine processes real-time market data and generates actionable trading signals that can be used by both the web interface and Telegram bot.