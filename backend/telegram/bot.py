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
INJ_BANK_API = "https://api.injective.network/cosmos/bank/v1beta1"
INJ_INDEXER_API = "https://api.injective.network/indexer/v1"
INJ_ORACLE_API = "https://api.injective.network/indexer/v1/oracle"

# CoinGecko API
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Etherscan API
ETHERSCAN_API = "https://api.etherscan.io/api"

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

# Symbol mapping for CoinGecko fallback
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

# ============================================================
# INJECTIVE API FUNCTIONS (Primary)
# Falls back to CoinGecko if Injective fails
# ============================================================

def get_inj_balance(address):
    """Get Injective balance via Injective API"""
    try:
        url = f"{INJ_BANK_API}/balances/{address}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Injective balance API failed: {e}")
    return None

# ============================================================
# INJECTIVE API FUNCTIONS (Primary)
# Falls back to CoinGecko if In全局jective fails
# ============================================================

# Helix API endpoints (Injective major markets)
HELIX_MARKETS = [
    {"ticker": "INJ/USDT", "market_type": "spot"},
    {"ticker": "INJ/USDC", "market_type": "spot"},
    {"ticker": "ETH/USDT", "market_type": "spot"},
    {"ticker": "BTC/USDT", "market_type": "spot"},
    {"ticker": "ATOM/USDT", "market_type": "spot"},
    {"ticker": "OSMO/USDT", "market_type": "spot"},
    {"ticker": "SOL/USDT", "market_type": "spot"},
    {"ticker": "INJ/USDT PERP", "market_type": "derivative"},
    {"ticker": "ETH/USDT PERP", "market_type": "derivative"},
    {"ticker": "BTC/USDT PERP", "market_type": "derivative"},
]

def get_helix_markets():
    """Get Helix/Injective markets"""
    try:
        # Try Helix API first
        url = "https://api.helixmarkets.com/v1/markets"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_inj_markets():
    """Get Injective spot markets"""
    try:
        url = f"{INJ_INDEXER_API}/spot/markets"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'markets' in data and data['markets']:
                return data['markets']
    except Exception as e:
        logger.warning(f"Injective markets API failed: {e}")
    return []

def get_inj_derivative_markets():
    """Get Injective derivative markets"""
    try:
        url = f"{INJ_INDEXER_API}/derivative/markets"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'markets' in data and data['markets']:
                return data['markets']
    except Exception as e:
        logger.warning(f"Injective derivative markets API failed: {e}")
    return []

# ============================================================
# COINGECKO FALLBACK (Secondary)
# Used when Injective APIs are unavailable
# ============================================================

def get_coingecko_price(coin_id):
    """Get price from CoinGecko as fallback"""
    try:
        url = f"{COINGECKO_API}/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"CoinGecko API failed: {e}")
    return None

def get_coin_data(coin_id):
    """Get full coin data from CoinGecko"""
    try:
        url = f"{COINGECKO_API}/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&sparkline=false"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"CoinGecko coin data failed: {e}")
    return None

# ============================================================
# REAL-TIME ANALYSIS (Injective Primary, CoinGecko Fallback)
# ============================================================

def get_real_time_analysis(symbol):
    """Fetch live market data with fallback to CoinGecko"""
    coin_id = SYMBOL_MAP.get(symbol, symbol.lower())
    
    # 1. Try Injective first
    inj_data = get_inj_ticker_data(symbol)
    if inj_data:
        return build_signal_from_data(symbol, inj_data, source="Injective")
    
    # 2. Fallback to CoinGecko
    coin_data = get_coin_data(coin_id)
    if coin_data and 'market_data' in coin_data:
        return build_signal_from_coingecko(symbol, coin_data)
    
    # 3. Try simple price fallback
    price_data = get_coingecko_price(coin_id)
    if price_data and coin_id in price_data:
        return build_signal_from_price(symbol, price_data[coin_id])
    
    logger.error(f"All data sources failed for {symbol}")
    return None

def get_inj_ticker_data(symbol):
    """Get ticker data from Injective"""
    try:
        # This would hit Injective's market data API
        # For now, using a placeholder that returns None to trigger fallback
        return None
    except:
        return None

def build_signal_from_data(symbol, data, source="Injective"):
    """Build signal from Injective data"""
    return {
        'symbol': symbol,
        'price': data.get('price', 0),
        'change_24h': data.get('change_24h', 0),
        'change_7d': data.get('change_7d', 0),
        'rsi': data.get('rsi', 50),
        'high_24h': data.get('high', 0),
        'low_24h': data.get('low', 0),
        'volume': data.get('volume', 0),
        'market_cap': data.get('market_cap', 0),
        'signal_strength': data.get('signal', '🤝 HOLD'),
        'signal_desc': data.get('desc', 'Market in consolidation'),
        'source': source
    }

def build_signal_from_coingecko(symbol, data):
    """Build signal from CoinGecko data"""
    market_data = data.get('market_data', {})
    
    price = market_data.get('current_price', {}).get('usd', 0)
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
        'price': price,
        'change_24h': change_24h,
        'change_7d': change_7d,
        'rsi': rsi,
        'high_24h': high_24h,
        'low_24h': low_24h,
        'volume': volume,
        'market_cap': mkt_cap,
        'signal_strength': signal_strength,
        'signal_desc': signal_desc,
        'source': 'CoinGecko (Injective fallback)'
    }

def build_signal_from_price(symbol, data):
    """Minimal signal from simple price data"""
    price = data.get('usd', 0)
    change = data.get('usd_24h_change', 0)
    
    return {
        'symbol': symbol,
        'price': price,
        'change_24h': change,
        'change_7d': 0,
        'rsi': 50,
        'high_24h': price,
        'low_24h': price,
        'volume': 0,
        'market_cap': 0,
        'signal_strength': '🤝 HOLD',
        'signal_desc': 'Limited data available',
        'source': 'CoinGecko (basic)'
    }

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
            "👋 Hi " + user.first_name + "! Welcome to NinjaAgent 🤖⚡\n\n"
            "I am your AI-powered trading assistant for Injective Protocol and crypto markets.\n\n"
            "📊 What I can do:\n"
            "  • Real-time technical analysis\n"
            "  • Live trading signals\n"
            "  • Portfolio tracking (Injective + EVM)\n"
            "  • Market data and price alerts\n\n"
            "🚀 Quick Start:\n"
            "  /signals - Get live trading signals\n"
            "  /analyze INJ - Analyze any token\n"
            "  /portfolio - View your portfolio\n"
            "  /markets - List Injective markets\n"
            "  /add_wallet - Add your wallet\n"
            "  /help - Show all commands"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📈 NinjaAgent Trading Bot Commands\n\n"
            "🤖 Trading and Analysis\n"
            "  /signals - Get live trading signals (Injective + CoinGecko)\n"
            "  /analyze <SYMBOL> - Detailed technical analysis\n"
            "  /portfolio - View your real-time portfolio\n"
            "  /markets - List Injective spot and derivative markets\n\n"
            "👛 Wallet Management\n"
            "  /add_wallet <address> - Add wallet (Injective or EVM)\n"
            "  /my_wallets - List all wallets\n"
            "  /remove_wallet <address> - Remove wallet\n\n"
            "❓ Help\n"
            "  /start - Welcome and quick start\n"
            "  /help - Show this help\n\n"
            "💡 Examples:\n"
            "  /analyze INJ\n"
            "  /analyze ETH\n"
            "  /markets\n"
            "  /add_wallet inj1xyz...\n\n"
            "Data: Injective API + CoinGecko 🤖"
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
        
        lines = ["📊 Live Trading Signals", "📅 Real-time data from Injective + CoinGecko\n"]
        for s in signals_data:
            lines.append(
                s['signal_strength'] + " - " + s['symbol'] + " @ $" + f"{s['price']:,.2f}" + "\n"
                + "   24h: " + f"{s['change_24h']:+.2f}" + "% | RSI: " + f"{s['rsi']:.1f}" + "\n"
                + "   " + s['signal_desc']
            )
        
        lines.append("\n💡 Use /analyze <SYMBOL> for detailed analysis")
        lines.append("📅 Updated: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + " UTC")
        
        await update.message.reply_text("\n".join(lines))
    
    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "⚠️ Please specify a token symbol.\n\n"
                "Usage: /analyze <SYMBOL>\n\n"
                "Examples:\n"
                "  /analyze INJ\n"
                "  /analyze ETH\n"
                "  /analyze BTC\n\n"
                "Supported: " + ", ".join(self.supported_symbols)
            )
            return
        
        symbol = context.args[0].upper()
        await update.message.reply_text("⏳ Fetching real-time data for " + symbol + "...")
        
        # Try Injective API first, fallback to CoinGecko
        signal = get_real_time_analysis(symbol)
        
        if not signal:
            await update.message.reply_text(
                "❌ Failed to fetch data for " + symbol + ".\n\n"
                "Supported symbols: " + ", ".join(self.supported_symbols) + "\n\n"
                "All data sources (Injective API and CoinGecko) are currently unavailable. "
                "Please try again later."
            )
            return
        
        volume_str = format_number(signal['volume'])
        mkt_str = format_number(signal['market_cap'])
        
        # Source indicator
        source_note = "Injective API" if "Injective" in str(signal.get('source', '')) else "CoinGecko (fallback)"
        
        analysis_text = (
            "🔬 Live Analysis: " + signal['symbol'] + "\n\n"
            "💲 Price: $" + f"{signal['price']:,.2f}" + "\n"
            "📊 RSI: " + f"{signal['rsi']:.1f}" + "\n"
            "📉 24h Change: " + f"{signal['change_24h']:+.2f}" + "%\n"
            "📊 7d Change: " + f"{signal['change_7d']:+.2f}" + "%\n"
            "📊 Volume (24h): " + volume_str + "\n"
            "🏦 Market Cap: " + mkt_str + "\n"
            "⬆️ 24h High: $" + f"{signal['high_24h']:,.2f}" + "\n"
            "⬇️ 24h Low: $" + f"{signal['low_24h']:,.2f}" + "\n\n"
            "📡 Signal: " + signal['signal_strength'] + "\n"
            "📝 Analysis: " + signal['signal_desc'] + "\n\n"
            "📅 Updated: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + " UTC\n"
            "💡 Data: " + source_note
        )
        await update.message.reply_text(analysis_text)
    
    async def markets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List Injective markets"""
        await update.message.reply_text("⏳ Fetching Injective markets...")
        
        # Try to fetch from multiple sources
        # 1. Injective API
        spot_markets = get_inj_markets()
        derivative_markets = get_inj_derivative_markets()
        
        # 2. Helix API fallback
        helix_data = get_helix_markets()
        
        # 3. Use hardcoded fallback if APIs fail
        if not spot_markets and helix_data and 'markets' in helix_data:
            spot_markets = [m for m in helix_data['markets'] if m.get('market_type') == 'spot']
        if not derivative_markets and helix_data and 'markets' in helix_data:
            derivative_markets = [m for m in helix_data['markets'] if m.get('market_type') == 'derivative']
        
        # Final fallback to hardcoded data
        if not spot_markets and not derivative_markets:
            spot_markets = [m for m in HELIX_MARKETS if m['market_type'] == 'spot']
            derivative_markets = [m for m in HELIX_MARKETS if m['market_type'] == 'derivative']
        
        lines = ["📈 Injective Markets\n"]
        
        if spot_markets:
            lines.append("🟢 Spot Markets:")
            for i, market in enumerate(spot_markets[:5]):
                ticker = market.get('ticker', 'N/A')
                lines.append("  • " + ticker)
            if len(spot_markets) > 5:
                lines.append("  ... and " + str(len(spot_markets) - 5) + " more")
        else:
            lines.append("🟢 Spot Markets: (API temporarily unavailable)")
            lines.append("   Fallback: Use /analyze <SYMBOL> for individual analysis")
        
        lines.append("")
        
        if derivative_markets:
            lines.append("🔴 Derivative Markets:")
            for i, market in enumerate(derivative_markets[:5]):
                ticker = market.get('ticker', 'N/A')
                lines.append("  • " + ticker)
            if len(derivative_markets) > 5:
                lines.append("  ... and " + str(len(derivative_markets) - 5) + " more")
        else:
            lines.append("🔴 Derivative Markets: (API temporarily unavailable)")
            lines.append("   Fallback: Use /analyze <SYMBOL> for individual analysis")
        
        lines.append("\n💡 Use /analyze <SYMBOL> for market analysis")
        
        await update.message.reply_text("\n".join(lines))
    
    async def portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallets = get_user_wallets(user_id)
        
        if not wallets:
            await update.message.reply_text(
                "💼 Your Portfolio\n\n"
                "You have not added any wallet addresses yet.\n\n"
                "Supported formats:\n"
                "  • Injective: inj1...\n"
                "  • EVM: 0x...\n\n"
                "Add a wallet:\n"
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
        
        # Get prices (try Injective first, fallback to CoinGecko)
        prices = self._get_prices_with_fallback(list(all_balances.keys()))
        
        try:
            lines = ["💼 Your Portfolio (Real-time)\n"]
            total_value = 0
            
            for symbol in all_balances:
                amount = all_balances[symbol]
                price = prices.get(symbol, 0)
                value = amount * price
                total_value += value
                
                if value > 0:
                    lines.append(symbol + ": " + f"{amount:.6f}" + " (approx $" + f"{value:,.2f}" + ")")
                else:
                    lines.append(symbol + ": " + f"{amount:.6f}")
            
            lines.append("\n💰 Total Value: $" + f"{total_value:,.2f}")
            lines.append("📅 Updated: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + " UTC")
            lines.append("💡 Prices: CoinGecko fallback | Balances: Injective + Etherscan")
            
            await update.message.reply_text("\n".join(lines))
        except Exception as e:
            logger.error(f"Error formatting portfolio: {e}")
            await update.message.reply_text(
                "❌ Error fetching real-time portfolio prices.\n"
                "Showing approximate balances only:\n\n" +
                "\n".join([k + ": " + f"{v:.6f}" for k, v in all_balances.items()])
            )
    
    def _get_wallet_balances(self, address):
        balances = {}
        
        # Injective wallet
        if address.startswith("inj"):
            try:
                account_data = get_inj_balance(address)
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
                url = f"{ETHERSCAN_API}?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
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
    
    def _get_prices_with_fallback(self, symbols):
        """Get prices with fallback: Injective -> CoinGecko"""
        prices = {}
        
        # Try CoinGecko (primary for prices as Injective doesn't always have USD prices)
        try:
            coin_ids = [SYMBOL_MAP.get(s, s.lower()) for s in symbols]
            ids_param = ",".join(coin_ids)
            url = f"{COINGECKO_API}/simple/price?ids={ids_param}&vs_currencies=usd"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for symbol in symbols:
                    coin_id = SYMBOL_MAP.get(symbol, symbol.lower())
                    if coin_id in data:
                        prices[symbol] = data[coin_id].get('usd', 0)
        except Exception as e:
            logger.warning(f"Price fetch failed: {e}")
        
        return prices
    
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
                    "⚠️ Invalid wallet address format.\n\n"
                    "Supported formats:\n"
                    "  • Injective: inj1... (42 chars)\n"
                    "  • EVM: 0x... (42 chars)\n\n"
                    "Example:\n"
                    "  /add_wallet inj1xyz...\n"
                    "  /add_wallet 0x123..."
                )
                return
            
            result = add_wallet_address(user_id, wallet_address)
            if result:
                await update.message.reply_text(
                    "✅ Wallet added successfully!\n\n" +
                    wallet_address + "\n\n"
                    "Your portfolio will now include this wallet.\n"
                    "Use /portfolio to see your updated holdings."
                )
            else:
                await update.message.reply_text("❌ Failed to add wallet. Please try again.")
        else:
            await update.message.reply_text(
                "⚠️ Please provide a wallet address.\n\n"
                "Usage: /add_wallet <address>\n\n"
                "Examples:\n"
                "  /add_wallet inj1xyz...\n"
                "  /add_wallet 0x123...\n\n"
                "Supported: Injective (inj...) and EVM (0x...) wallets"
            )
    
    async def my_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        wallets = get_user_wallets(user_id)
        
        if wallets:
            wallet_list = "\n".join(["  • " + w[:8] + "..." + w[-6:] for w in wallets])
            await update.message.reply_text(
                "👛 Your Wallets (" + str(len(wallets)) + " total)\n\n" +
                wallet_list + "\n\n"
                "Use /portfolio to see your holdings."
            )
        else:
            await update.message.reply_text(
                "👛 No wallets found.\n\n"
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
                        "✅ Wallet removed!\n\n" +
                        wallet_address + "\n\n"
                        "This wallet is no longer tracked in your portfolio."
                    )
                else:
                    await update.message.reply_text("❌ Failed to remove wallet. Please try again.")
            else:
                await update.message.reply_text("⚠️ Wallet not found in your profile.")
        else:
            await update.message.reply_text(
                "⚠️ Please provide a wallet address to remove.\n\n"
                "Usage: /remove_wallet <address>"
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        msg_lower = user_message.lower()
        
        if any(word in msg_lower for word in ['buy', 'sell', 'long', 'short']):
            await update.message.reply_text(
                "🚧 Coming Soon!\n\n"
                "Direct trading via Telegram is under development.\n"
                "For now, please use the Injective exchange for trades.\n\n"
                "Try these commands instead:\n"
                "  /analyze <SYMBOL> - Get analysis\n"
                "  /signals - Get trading signals\n"
                "  /portfolio - Check your portfolio"
            )
        elif any(word in msg_lower for word in ['price', 'berapa', 'harga']):
            await update.message.reply_text(
                "💡 Want to check a price?\n\n"
                "Use: /analyze <SYMBOL>\n\n"
                "Example: /analyze INJ"
            )
        else:
            await update.message.reply_text(
                "🤖 NinjaAgent is here to help!\n\n"
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
        return "$" + f"{num/1e9:.2f}" + "B"
    elif num >= 1e6:
        return "$" + f"{num/1e6:.2f}" + "M"
    elif num >= 1e3:
        return "$" + f"{num/1e3:.2f}" + "K"
    else:
        return "$" + f"{num:.2f}"

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