import os
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# User data storage
USER_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")

def _load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def _save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_wallet_address(user_id, wallet_address):
    try:
        data = _load_user_data()
        if user_id not in data:
            data[user_id] = {"wallets": []}
        if "wallets" not in data[user_id]:
            data[user_id]["wallets"] = []
        if wallet_address not in data[user_id]["wallets"]:
            data[user_id]["wallets"].append(wallet_address)
            _save_user_data(data)
        return True
    except Exception as e:
        logger.error(f"Error adding wallet: {e}")
        return False

def remove_wallet_address(user_id, wallet_address):
    try:
        data = _load_user_data()
        if user_id in data and "wallets" in data[user_id]:
            if wallet_address in data[user_id]["wallets"]:
                data[user_id]["wallets"].remove(wallet_address)
                _save_user_data(data)
                return True
        return False
    except Exception as e:
        logger.error(f"Error removing wallet: {e}")
        return False

def get_user_wallets(user_id):
    data = _load_user_data()
    if user_id in data and "wallets" in data[user_id]:
        return data[user_id]["wallets"]
    return []

# Symbol mapping for CoinGecko
SYMBOL_MAP = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'INJ': 'injective-protocol',
    'ATOM': 'cosmos',
    'OSMO': 'osmosis',
    'USDT': 'tether',
    'USDC': 'usd-coin',
    'BNB': 'binancecoin',
    'SOL': 'solana',
    'DOT': 'polkadot',
}

# Real-time signal analysis using CoinGecko + momentum calculations
def get_live_signal(symbol):
    """Fetch real-time market data and generate trading signal"""
    try:
        coin_id = SYMBOL_MAP.get(symbol, symbol.lower())
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&sparkline=false"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if 'market_data' not in data:
            return None
        
        market_data = data['market_data']
        current_price = market_data.get('current_price', {}).get('usd', 0)
        change_24h = market_data.get('price_change_percentage_24h', 0)
        change_7d = market_data.get('price_change_percentage_7d', 0)
        high_24h = market_data.get('high_24h', {}).get('usd', 0)
        low_24h = market_data.get('low_24h', {}).get('usd', 0)
        volume = market_data.get('total_volume', {}).get('usd', 0)
        mkt_cap = market_data.get('market_cap', {}).get('usd', 0)
        
        # Calculate RSI approximation
        if change_24h > 3:
            rsi = 60 + min(abs(change_24h) * 2, 25)
        elif change_24h < -3:
            rsi = 40 - min(abs(change_24h) * 2, 25)
        else:
            rsi = 50
        
        # Real signal logic
        if change_24h > 5 and rsi < 70:
            signal_strength = "🔥 STRONG BUY"
            signal_desc = "Strong momentum with positive price action"
        elif change_24h > 2 and rsi < 60:
            signal_strength = "📈 BUY"
            signal_desc = "Positive momentum building"
        elif change_24h < -5 and rsi > 35:
            signal_strength = "💥 STRONG SELL"
            signal_desc = "Negative momentum accelerating"
        elif change_24h < -2 and rsi > 50:
            signal_strength = "📉 SELL"
            signal_desc = "Downtrend confirmed"
        else:
            signal_strength = "🤝 HOLD"
            signal_desc = "Market in consolidation phase"
        
        return {
            'symbol': symbol,
            'price': current_price,
            'change_24h': change_24h,
            'change_7d': change_7d,
            'rsi': rsi,
            'high_24h': high_24h,
            'low_24h': low_24h,
            'volume': volume,
            'market_cap': mkt_cap,
            'signal_strength': signal_strength,
            'signal_desc': signal_desc
        }
    except Exception as e:
        logger.error(f"Error fetching signal for {symbol}: {e}")
        return None

class NinjaAgentTelegramBot:
    def __init__(self, token):
        self.token = token
        
        self.supported_symbols = ['INJ', 'ETH', 'BTC', 'ATOM', 'OSMO', 'SOL']
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Hi {user.first_name}! Welcome to **NinjaAgent** 🤖⚡\n\n"
            "I'm your AI-powered trading assistant for Injective Protocol and crypto markets.\n\n"
            "📊 **What I can do:**\n"
            "  • Real-time technical analysis\n"
            "  • Live trading signals\n"
            "  • Portfolio tracking (Injective + EVM)\n"
            "  • Market data & price alerts\n\n"
            "🚀 **Quick Start:**\n"
            "  /signals - Get live trading signals\n"
            "  /analyze INJ - Analyze any token\n"
            "  /portfolio - View your portfolio\n"
            "  /add_wallet - Add your wallet\n"
            "  /help - Show all commands"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📈 **NinjaAgent Trading Bot Commands**\n\n"
            "🤖 **Trading & Analysis**\n"
            "  /signals - Get live trading signals (real-time from CoinGecko)\n"
            "  /analyze \u003cSYMBOL\u003e - Detailed technical analysis with RSI, signals\n"
            "  /portfolio - View your real-time portfolio value\n\n"
            "👛 **Wallet Management**\n"
            "  /add_wallet \u003caddress\u003e - Add Injective (inj...) or EVM (0x...) wallet\n"
            "  /my_wallets - List all your wallets\n"
            "  /remove_wallet \u003caddress\u003e - Remove a wallet\n\n"
            "❓ **Help**\n"
            "  /start - Welcome message and quick start\n"
            "  /help - Show this help message\n\n"
            "💡 **Examples:**\n"
            "  /analyze INJ\n"
            "  /analyze ETH\n"
            "  /add_wallet inj1xyz...\n"
            "  /add_wallet 0x123...\n\n"
            "Data powered by CoinGecko, Injective API & Etherscan 🚀"
        )
        await update.message.reply_text(help_text)
    
    async def signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Fetching live trading signals from CoinGecko...")
        
        signals_data = []
        for symbol in self.supported_symbols[:3]:  # Top 3 for brevity
            signal = get_live_signal(symbol)
            if signal:
                signals_data.append(signal)
        
        if not signals_data:
            await update.message.reply_text(
                "❌ Unable to fetch live signals at the moment.\n"
                "Please try again later. The APIs might be temporarily unavailable."
            )
            return
        
        lines = ["📊 **Live Trading Signals**", "📅 Real-time data from CoinGecko\n"]
        for s in signals_data:
            lines.append(
                f"{s['signal_strength']} - **{s['symbol']}** @ ${s['price']:,.2f}\n"
                f"   24h: {s['change_24h']:+.2f}% | RSI: {s['rsi']:.1f}\n"
                f"   {s['signal_desc']}"
            )
        
        lines.append("\n💡 Use /analyze \u003cSYMBOL\u003e for detailed analysis")
        lines.append("📅 Updated: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + " UTC")
        
        await update.message.reply_text("\n".join(lines))
    
    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "⚠️ Please specify a token symbol.\n\n"
                "**Usage:** /analyze \u003cSYMBOL\u003e\n\n"
                "**Examples:**\n"
                "  /analyze INJ\n"
                "  /analyze ETH\n"
                "  /analyze BTC\n\n"
                f"Supported: {', '.join(self.supported_symbols)}"
            )
            return
        
        symbol = context.args[0].upper()
        await update.message.reply_text(f"⏳ Fetching real-time data for **{symbol}** from CoinGecko...")
        
        signal = get_live_signal(symbol)
        if not signal:
            await update.message.reply_text(
                f"❌ Failed to fetch data for **{symbol}**.\n\n"
                f"**Supported symbols:** {', '.join(self.supported_symbols)}\n\n"
                "Please check the symbol and try again."
            )
            return
        
        # Format numbers
        volume = signal['volume']
        if volume >= 1e9:
            volume_str = f"${volume/1e9:.2f}B"
        elif volume >= 1e6:
            volume_str = f"${volume/1e6:.2f}M"
        else:
            volume_str = f"${volume:.2f}"
        
        mkt_cap = signal['market_cap']
        if mkt_cap >= 1e9:
            mkt_str = f"${mkt_cap/1e9:.2f}B"
        elif mkt_cap >= 1e6:
            mkt_str = f"${mkt_cap/1e6:.2f}M"
        else:
            mkt_str = f"${mkt_cap:.2f}"
        
        analysis_text = (
            f"🔬 **Live Analysis: {signal['symbol']}**\n\n"
            f"💲 **Price:** ${signal['price']:,.2f}\n"
            f"📊 **RSI:** {signal['rsi']:.1f}\n"
            f"📉 **24h Change:** {signal['change_24h']:+.2f}%\n"
            f"📊 **7d Change:** {signal['change_7d']:+.2f}%\n"
            f"📊 **Volume (24h):** {volume_str}\n"
            f"🏦 **Market Cap:** {mkt_str}\n"
            f"⬆️ **24h High:** ${signal['high_24h']:,.2f}\n"
            f"⬇️ **24h Low:** ${signal['low_24h']:,.2f}\n\n"
            f"📡 **Signal:** {signal['signal_strength']}\n"
            f"📝 **Analysis:** {signal['signal_desc']}\n\n"
            f"📅 Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"💡 Data: CoinGecko API (Real-time)"
        )
        await update.message.reply_text(analysis_text)
    
    async def portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallets = get_user_wallets(user_id)
        
        if not wallets:
            await update.message.reply_text(
                "💼 **Your Portfolio**\n\n"
                "You haven't added any wallet addresses yet.\n\n"
                "**Supported formats:**\n"
                "  • Injective: `inj1...`\n"
                "  • EVM: `0x...`\n\n"
                "**Add a wallet:**\n"
                "  /add_wallet inj1xyz...\n"
                "  /add_wallet 0x123..."
            )
            return
        
        await update.message.reply_text("⏳ Fetching real-time portfolio data...")
        
        all_balances = {}
        wallet_count = 0
        
        for wallet_address in wallets:
            try:
                balances = self._get_wallet_balances(wallet_address)
                if balances:
                    wallet_count += 1
                    for symbol, amount in balances.items():
                        if symbol in all_balances:
                            all_balances[symbol] += amount
                        else:
                            all_balances[symbol] = amount
            except Exception as e:
                logger.error(f"Error fetching portfolio for {wallet_address}: {e}")
                continue
        
        if not all_balances or wallet_count == 0:
            await update.message.reply_text(
                "❌ Could not fetch portfolio data.\n"
                "The blockchain APIs may be temporarily unavailable.\n"
                "Please try again later."
            )
            return
        
        try:
            token_symbols = list(all_balances.keys())
            token_ids = [SYMBOL_MAP.get(s, s.lower()) for s in token_symbols]
            ids_param = ",".join(token_ids)
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd"
            response = requests.get(url, timeout=15)
            data = response.json()
            
            lines = ["💼 **Your Portfolio (Real-time)**\n"]
            total_value = 0
            
            for symbol in token_symbols:
                coingecko_id = SYMBOL_MAP.get(symbol, symbol.lower())
                amount = all_balances[symbol]
                
                price_info = data.get(coingecko_id, {})
                price = price_info.get("usd", 0) if price_info else 0
                value = amount * price
                total_value += value
                
                if value > 0:
                    lines.append(f"**{symbol}:** {amount:.6f} (~${value:,.2f})")
                else:
                    lines.append(f"**{symbol}:** {amount:.6f}")
            
            lines.append(f"\n💰 **Total Value:** ${total_value:,.2f}")
            lines.append(f"📅 Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            lines.append("💡 Prices from CoinGecko (Real-time)")
            
            await update.message.reply_text("\n".join(lines))
        except Exception as e:
            logger.error(f"Error fetching prices for portfolio: {e}")
            await update.message.reply_text(
                "❌ Error fetching real-time portfolio prices.\n"
                "Showing approximate balances only:\n\n" +
                "\n".join([f"{k}: {v:.6f}" for k, v in all_balances.items()])
            )
    
    def _get_wallet_balances(self, address):
        balances = {}
        
        if address.startswith("0x"):
            try:
                api_key = os.getenv("ETHERSCAN_API_KEY", "NGRTMDUS49SVNVDJM2EFUEGMZFTC86TU3U")
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "1":
                        balance_wei = int(data.get("result", 0))
                        if balance_wei > 0:
                            eth_balance = balance_wei / (10 ** 18)
                            balances["ETH"] = eth_balance
                return balances
            except Exception as e:
                logger.warning(f"Etherscan API failed for {address}: {e}")
                return balances
        
        elif address.startswith("inj"):
            try:
                url = f"https://api.injective.network/cosmos/bank/v1beta1/balances/{address}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for bal in data.get("balances", []):
                        denom = bal.get("denom", "")
                        amount = float(bal.get("amount", 0))
                        symbol = self._denom_to_symbol(denom)
                        if symbol and amount > 0:
                            decimals = self._get_token_decimals(symbol)
                            adjusted_amount = amount / (10 ** decimals)
                            if adjusted_amount > 0:
                                balances[symbol] = adjusted_amount
                return balances
            except Exception as e:
                logger.warning(f"Injective API failed for {address}: {e}")
        
        return balances
    
    def _denom_to_symbol(self, denom):
        if denom == "inj":
            return "INJ"
        elif "uatom" in denom:
            return "ATOM"
        elif "uosmo" in denom:
            return "OSMO"
        elif denom == "uusdt":
            return "USDT"
        elif denom == "uusdc":
            return "USDC"
        return denom.upper()
    
    def _get_token_decimals(self, symbol):
        decimals = {"INJ": 18, "ATOM": 6, "OSMO": 6, "USDT": 6, "USDC": 6}
        return decimals.get(symbol.upper(), 6)
    
    async def add_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if context.args:
            wallet_address = context.args[0]
            is_injective = wallet_address.startswith('inj') and len(wallet_address) == 42
            is_evm = wallet_address.startswith('0x') and len(wallet_address) == 42
            if not (is_injective or is_evm):
                await update.message.reply_text(
                    "⚠️ **Invalid wallet address format.**\n\n"
                    "**Supported formats:**\n"
                    "  • Injective: `inj1...` (42 chars)\n"
                    "  • EVM: `0x...` (42 chars)\n\n"
                    "**Example:**\n"
                    "  /add_wallet inj1xyz...\n"
                    "  /add_wallet 0x123..."
                )
                return
            
            result = add_wallet_address(user_id, wallet_address)
            if result:
                await update.message.reply_text(
                    f"✅ **Wallet added successfully!**\n\n"
                    f"`{wallet_address}`\n\n"
                    "Your portfolio will now include this wallet.\n"
                    "Use /portfolio to see your updated holdings."
                )
            else:
                await update.message.reply_text("❌ Failed to add wallet. Please try again.")
        else:
            await update.message.reply_text(
                "⚠️ **Please provide a wallet address.**\n\n"
                "**Usage:** /add_wallet \u003caddress\u003e\n\n"
                "**Examples:**\n"
                "  /add_wallet inj1xyz...\n"
                "  /add_wallet 0x123...\n\n"
                "**Supported:** Injective (inj...) and EVM (0x...) wallets"
            )
    
    async def my_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallets = get_user_wallets(user_id)
        
        if wallets:
            wallet_list = "\n".join([f"  • `{w[:8]}...{w[-6:]}`" for w in wallets])
            await update.message.reply_text(
                f"👛 **Your Wallets** ({len(wallets)} total)\n\n"
                f"{wallet_list}\n\n"
                "Use /portfolio to see your holdings."
            )
        else:
            await update.message.reply_text(
                "👛 **No wallets found.**\n\n"
                "Add a wallet to track your portfolio:\n"
                "  /add_wallet \u003caddress\u003e\n\n"
                "Supports Injective (inj...) and EVM (0x...) wallets."
            )
    
    async def remove_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if context.args:
            wallet_address = context.args[0]
            if wallet_address in get_user_wallets(user_id):
                result = remove_wallet_address(user_id, wallet_address)
                if result:
                    await update.message.reply_text(
                        f"✅ **Wallet removed!**\n\n"
                        f"`{wallet_address}`\n\n"
                        "This wallet is no longer tracked in your portfolio."
                    )
                else:
                    await update.message.reply_text("❌ Failed to remove wallet. Please try again.")
            else:
                await update.message.reply_text("⚠️ Wallet not found in your profile.")
        else:
            await update.message.reply_text(
                "⚠️ **Please provide a wallet address to remove.**\n\n"
                "**Usage:** /remove_wallet \u003caddress\u003e"
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        
        # Simple natural language processing
        msg_lower = user_message.lower()
        
        if any(word in msg_lower for word in ['buy', 'sell', 'long', 'short']):
            await update.message.reply_text(
                "🚧 **Coming Soon!**\n\n"
                "Direct trading via Telegram is under development.\n"
                "For now, please use the Injective exchange for trades.\n\n"
                "Try these commands instead:\n"
                "  /analyze \u003cSYMBOL\u003e - Get analysis\n"
                "  /signals - Get trading signals\n"
                "  /portfolio - Check your portfolio"
            )
        elif any(word in msg_lower for word in ['price', 'berapa', 'harga']):
            await update.message.reply_text(
                "💡 **Want to check a price?**\n\n"
                "Use: /analyze \u003cSYMBOL\u003e\n\n"
                "Example: /analyze INJ"
            )
        else:
            await update.message.reply_text(
                "🤖 **NinjaAgent is here to help!**\n\n"
                "Try these commands:\n"
                "  /analyze \u003cSYMBOL\u003e - Technical analysis\n"
                "  /signals - Trading signals\n"
                "  /portfolio - Your portfolio\n"
                "  /help - All commands\n\n"
                "Or send a trading command like 'buy 10 INJ' (coming soon!)"
            )

def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    bot = NinjaAgentTelegramBot(os.getenv("TELEGRAM_BOT_TOKEN"))
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("signals", bot.signals))
    application.add_handler(CommandHandler("analyze", bot.analyze))
    application.add_handler(CommandHandler("portfolio", bot.portfolio))
    application.add_handler(CommandHandler("add_wallet", bot.add_wallet))
    application.add_handler(CommandHandler("my_wallets", bot.my_wallets))
    application.add_handler(CommandHandler("remove_wallet", bot.remove_wallet))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()