# NinjaAgent 🤖⚡

> **AI-Powered Autonomous Trading Assistant for Injective Protocol**
>
> Built for Injective Solo AI Builder Sprint 2026

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is NinjaAgent?

**NinjaAgent** is an intelligent, autonomous trading assistant that lets you trade on Injective Protocol using natural language. No complex interfaces, no manual order forms — just tell it what you want, and it handles the rest.

### Key Features

- 🤖 **Natural Language Trading**: "Buy 10 INJ when it drops below $20"
- 📊 **Real-time Market Monitoring**: Live price tracking and alerts
- ⚡ **Instant Execution**: Direct integration with Injective Protocol
- 🛡️ **Risk Management**: Built-in stop-loss and position size controls
- 🌐 **WebSocket Live Updates**: Real-time portfolio and market data
- 💬 **AI-Powered Parsing**: NVIDIA AI for accurate command interpretation
- 📱 **Telegram Bot Integration**: Real-time trading signals via Telegram

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [Injective Wallet](https://injective.com/wallet)
- NVIDIA API Key ([Get one free](https://build.nvidia.com/))

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ninjaagent
cd ninjaagent

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your actual keys
```

### Environment Variables

Create a `.env` file with your configuration:

```bash
NVIDIA_API_KEY=your_nvidia_api_key_here
INJECTIVE_MNEMONIC=your_injective_wallet_mnemonic_here
INJECTIVE_NETWORK=testnet  # or mainnet
INJECTIVE_MARKET_ID=inj-usdt  # default market
TELEGRAM_BOT_TOKEN=8519702355:AAFdHDt_13r0Psn_uizxbaIXXHH0gCbYIpA
```

### Run the Application

```bash
# Start the API server
python backend/main.py

# Or start Telegram bot
python backend/telegram/main.py

# Or use Docker Compose
docker-compose up
```

The API will be available at `http://localhost:8000`

---

## 💡 Usage Examples

### Natural Language Commands

| Command | Action |
|---------|--------|
| `"buy 10 INJ at market"` | Market buy 10 INJ |
| `"sell 50% of my INJ"` | Partial position sell |
| `"set alert when BTC drops below 60k"` | Price alert setup |
| `"what's my portfolio worth?"` | Portfolio overview |
| `"cancel my open orders"` | Order cancellation |

### API Endpoint

```bash
curl -X POST "http://localhost:8000/api/trade/execute" \
  -H "Content-Type: application/json" \
  -d '{"command":"buy 10 INJ at market"}'
```

### WebSocket Real-time Updates

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Update:", data);
};
```

### Telegram Bot Commands

| Command | Action |
|---------|--------|
| `/start` | Start the bot and show help |
| `/signals` | Get latest trading signals |
| `/analyze <symbol>` | Technical analysis for a token |
| `/portfolio` | View your portfolio |
| `/help` | Show help message |

You can also send natural language trading commands directly to the bot:
- "buy 10 INJ at market"
- "set alert when BTC drops below 60k"
- "what's my portfolio worth?"

---

## 🏗 Architecture

```
┌─────────────────┐
│   Frontend      │  Next.js Dashboard
│  (React/TS)     │
└────────┬────────┘
         │ WebSocket/HTTP
         ▼
┌─────────────────────────────────┐
│         FastAPI Server          │
│  ┌─────────┐  ┌──────────────┐ │
│  │ Parser  │  │   NinjaAgent │ │
│  │ (NVIDIA │  │   Trading    │ │
│  │  LLM)   │  │   Engine     │ │
│  └────┬────┘  └──────┬───────┘ │
│       │              │         │
│       ▼              ▼         │
│  ┌─────────┐  ┌──────────────┐ │
│  │Natural  │  │  Injective   │ │
│  │Language │  │  Protocol    │ │
│  │Commands │  │  Client      │ │
│  └─────────┘  └──────────────┘ │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Telegram Bot   │
│ (Real-time      │
│  Signals)       │
└─────────────────┘
```

---

## 🎥 Demo

[Replace with your demo video link]

**Live Demo**: [Your deployed URL]

---

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Test trading commands
python scripts/test_commands.py
```

---

## 🤝 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI |
| AI/NLP | NVIDIA AI (Qwen Coder) |
| Blockchain | Injective Protocol (injective-py) |
| Frontend | Next.js, React, Tailwind CSS |
| Real-time | WebSocket |
| Deployment | Docker, Vercel |
| Telegram | python-telegram-bot |

---

## 🏆 Hackathon Criteria

| Criteria | How NinjaAgent Delivers |
|----------|------------------------|
| **Usefulness** | Solves real trading friction with natural language and provides real-time signals |
| **Execution Quality** | Working API, WebSocket, and dashboard with Telegram integration |
| **Simplicity** | "Tell, don't click" — intuitive UX with Telegram bot support |
| **Documentation** | Clear README, API docs, setup guide |
| **Future Potential** | Open for plugins, multi-chain expansion with Telegram community support |

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

Built with 🔥 for the Injective community