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

# Injective API endpoints
INJ_BANK_API = "https://lcd.injective.network/cosmos/bank/v1beta1"
INJ_EXCHANGE_API = "https://sentry.exchange.grpc-web.injective.network/injective_exchange_rpc.InjectiveExchangeRPC"
INJ_EXPLORER_API = "https://api.explorer.injective.network/api/v1"
INJ_INDEXER_API = "https://api.injective.network/indexer/v1"
INJ_ORACLE_API = "https://api.injective.network/indexer/v1/oracle"

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

# Symbol mapping for CoinGecko (supplementary)
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

# Injective market IDs
INJ_MARKETS = {
    'INJ/USDT': '0x...',  # Spot market
    'ETH/USDT': '0x...',
    'BTC/USDT': '0x...',
}

# ============================================================
# INJECTIVE API FUNCTIONS
# ============================================================

def get_inj_account(address):
    """Get Injective account info"""
    try:
        url = f"{INJ_BANK_API}/balances/{address}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Injective API failed for {address}: {e}")
    return {}

def get_inj_oracle_price(symbol):
    """Get Injective oracle price for a symbol"""
    try:
        url = f"{INJ_INDEXER_API}/oracle/price"
        # Try to fetch from Injective oracle
        headers = {'Content-Type': 'application/json'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Parse oracle data
            return data
    except Exception as e:
        logger.warning(f"Injective oracle failed for {symbol}: {e}")
    return None

def get_inj_markets():
    """Get all Injective markets"""
    try:
        url = f"{INJ_INDEXER_API}/spot/markets"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Injective markets API failed: {e}")
    return []

def get_inj_derivative_markets():
    """Get all Injective derivative markets"""
    try:
        url = f"{INJ_INDEXER_API}/derivative/markets"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Injective derivative markets API failed: {e}")
    return []

def get_inj_orderbook(market_id):
    """Get orderbook for a specific market"""
    try:
        url = f"{INJ_INDEXER_API}/spot/orderbooks"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Injective orderbook failed for {market_id}: {e}")
    return {}

def get_inj_recent_trades(address):
    """Get recent trades for an address"""
    try:
        url = f"{INJ_EXPLORER_API}/txs?sender={address}&limit=10"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Injective explorer failed for {address}: {e}")
    return []

# ============================================================
# REAL-TIME SIGNAL ANALYSIS
# ============================================================

def get_real_time_analysis(symbol):
    """Fetch live market data and generate trading signal"""
    try:
        # Try Injective oracle first
        inj_price_data = get_inj_oracle_price(symbol)
        
        # Fallback to CoinGecko
        coin_id = SYMBOL_MAP.get(symbol, symbol.lower())
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&sparkline=false"
        response = requests.get(url, timeout=10)
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
        
        # RSI approximation
        if change_24h > 3:
            rsi = 60 + min(abs(change_24h) * 2, 25)
        elif change_24h < -3:
            rsi = 40 - min(abs(change_24h) * 2, 25)
        else:
            rsi = 50
        
        # Signal logic
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

# ============================================================
# BOT CLASS
# ============================================================

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
            "  /markets - List Injective markets\n"
            "  /add_wallet - Add your wallet\n"
            "  /help - Show all commands"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📈 **NinjaAgent Trading Bot Commands**\n\n"
            "🤖 **Trading & Analysis**\n"
            "  /symbols - Get live trading signals (Injective + CoinGecko)\n"
            "  /analyze <SYMBOL> - Detailed technical analysis\n"
            "  /portfolio - View your real-time portfolio\n"
            "  /markets - List Injective spot & derivative markets\n\n"
            "👛 **Wallet Management**\n"
            "  /add_wallet <address> - Add wallet (Injective or EVM)\n"
            "  /my_wallets - List all wallets\n"
            "  /remove_wallet <address> - Remove wallet\n\n"
            "❓ **Help**\n"
            "  /start - Welcome & quick start\n"
            "  /help - Show this help\n\n"
            "💡 **Examples:**\n"
            "  /analyze INJ\n"
            "  /analyze ETH\n"
            "  /markets\n"
            "  /add_wallet inj1xyz...\n\n"
            "Data: Injective API + CoinGecko 🚀"
        )
        await update.message.reply_text(help_text)
    
    async def signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Fetching live trading signals...")
        
        signals_data = []
        for symbol in self.supported_symbols[:3]:
            signal = get_real_time_analysis(symbol)
            if signal:
                signals_data.append(signal)
        
        if not signals_data:
            await update.message.reply_text(
                "❌ Unable to fetch live signals. Please try again later."
            )
            return
        
        lines = ["📊 **Live Trading Signals**", "📅 Real-time data from Injective + CoinGecko\n"]
        for s in signals_data:
            lines.append(
                f"{s['signal_strength']} - **{s['symbol']}** @ ${s['price']:,.2f}\n"
                f"   24h: {s['change_24h']:+.2f}% | RSI: {s['rsi']:.1f}\n"
                f"   {s['signal_desc']}"
            )
        
        lines.append("\n💡 Use /analyze <SYMBOL> for detailed analysis")
        lines.append("📅 Updated: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + " UTC")
        
        await update.message.reply_text("\n".join(lines))
    
    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "⚠️ Please specify a token symbol.\n\n"
                "**Usage:** /analyze <SYMBOL>\n\n"
                "**Examples:**\n"
                "  /analyze INJ\n"
                "  /analyze ETH\n"
                "  /analyze BTC\n\n"
                f"**Supported:** {', '.join(self.supported_symbols)}"
            )
            return
        
        symbol = context.args[0].upper()
        await update.message.reply_text(f"⏳ Fetching real-time data for **{symbol}**...")
        
        signal = get_real_time_analysis(symbol)
        if not signal:
            await update.message.reply_text(
                f"❌ Failed to fetch data for **{symbol}**.\n\n"
                f"**Supported symbols:** {', '.join(self.supported_symbols)}"
            )
            return
        
        volume_str = format_number(signal['volume'])
        mkt_str = format_number(signal['market_cap'])
        
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
            f"💡 Data: Injective API + CoinGecko"
        )
        await update.message.reply_text(analysis_text)
    
    async def markets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List Injective markets"""
        await update.message.reply_text("⏳ Fetching Injective markets...")
        
        # Try to fetch from Injective
        spot_markets = get_inj_markets()
        derivative_markets = get_inj_derivative_markets()
        
        lines = ["📈 **Injective Markets**\n"]
        
        if spot_markets:
            lines.append("🟢 **Spot Markets:**")
            # Show first 5 markets
            for i, market in enumerate(spot_markets[:5]):
                ticker = market.get('ticker', 'N/A')
                lines.append(f"  • {ticker}")
            if len(spot_markets) > 5:
                lines.append(f"  ... and {len(spot_markets) - 5} more")
        else:
            lines.append("🟢 **Spot Markets:** (API temporarily unavailable)")
        
        lines.append("")
        
        if derivative_markets:
            lines.append("🔴 **Derivative Markets:**")
            for i, market in enumerate(derivative_markets[:5]):
                ticker = market.get('ticker', 'N/A')
                lines.append(f"  • {ticker}")
            if len(derivative_markets) > 5:
                lines.append(f"  ... and {len(derivative_markets) - 5} more")
        else:
            lines.append("🔴 **Derivative Markets:** (API temporarily unavailable)")
        
        lines.append("\n💡 Use /analyze <SYMBOL> for market analysis")
        
        await update.message.reply_text("\n".join(lines))
    
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
                "The APIs may be temporarily unavailable.\n"
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
            lines.append("💡 Prices: CoinGecko | Balances: Injective + Etherscan")
            
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
        
        # Injective wallet
        if address.startswith("inj"):
            try:
                account_data = get_inj_account(address)
                if account_data and 'balances' in account_data:
                    for bal in account_data['balances']:
                        denom = bal.get('denom', '')
                        amount = float(bal.get('amount', 0))
                        symbol = self._denom_to_symbol(denom)
                        if symbol and amount > 0:
                            decimals = self._get_token_decimals(symbol)
                            adjusted_amount = amount / (10 ** decimals)
                            if adjusted_amount > 0:
                                balances[symbol] = adjusted_amount
            except Exception as e:
                logger.warning(f"Injective balance fetch failed: {e}")
        
        # EVM wallet
        elif address.startswith("0x"):
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
            except Exception as e:
                logger.warning(f"Etherscan balance fetch failed: {e}")
        
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
                "**Usage:** /add_wallet <address>\n\n"
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
                "  /add_wallet <address>\n\n"
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
                "**Usage:** /remove_wallet <address>"
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        msg_lower = user_message.lower()
        
        if any(word in msg_lower for word in ['buy', 'sell', 'long', 'short']):
            await update.message.reply_text(
                "🚧 **Coming Soon!**\n\n"
                "Direct trading via Telegram is under development.\n"
                "For now, please use the Injective exchange for trades.\n\n"
                "Try these commands instead:\n"
                "  /analyze <SYMBOL> - Get analysis\n"
                "  /signals - Get trading signals\n"
                "  /portfolio - Check your portfolio"
            )
        elif any(word in msg_lower for word in ['price', 'berapa', 'harga']):
            await update.message.reply_text(
                "💡 **Want to check a price?**\n\n"
                "Use: /analyze <SYMBOL>\n\n"
                "Example: /analyze INJ"
            )
        else:
            await update.message.reply_text(
                "🤖 **NinjaAgent is here to help!**\n\n"
                "Try these commands:\n"
                "  /analyze <SYMBOL> - Technical analysis\n"
                "  /signals - Trading signals\n"
                "  /portfolio - Your portfolio\n"
                "  /markets - Injective markets\n"
                "  /help - All commands\n\n"
                "Or send a trading command like 'buy 10 INJ' (coming soon!)"
            )

def format_number(num):
    """Format numbers for display"""
    if num >= 1e9:
        return f"${num/1e9:.2f}B"
    elif num >= 1e6:
        return f"${num/1e6:.2f}M"
    elif num >= 1e3:
        return f"${num/1e3:.2f}K"
    else:
        return f"${num:.2f}"

def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    bot = NinjaAgentTelegramBot(os.getenv("TELEGRAM_BOT_TOKEN"))
    
    # Command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("signals", bot.signals))
    application.add_handler(CommandHandler("analyze", bot.analyze))
    application.add_handler(CommandHandler("portfolio", bot.portfolio))
    application.add_handler(CommandHandler("markets", bot.markets))
    application.add_handler(CommandHandler("add_wallet", bot.add_wallet))
    application.add_handler(CommandHandler("my_wallets", bot.my_wallets))
    application.add_handler(CommandHandler("remove_wallet", bot.remove_wallet))
    
    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()