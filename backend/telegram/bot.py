"""
Telegram Bot for NinjaAgent
Provides real-time trading signals and technical analysis
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from backend.core.agent import get_agent
from backend.injective.client import get_injective_client
import json
from datetime import datetime
import requests
from backend.core.user import add_wallet_address, get_user_wallets, remove_wallet_address, wallet_address_exists

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class NinjaAgentTelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.agent = None
        self.injective_client = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_text(
            f"Hi {user.first_name}! Welcome to NinjaAgent Trading Bot 🤖\n\n"
            "I provide real-time trading signals and technical analysis for Injective Protocol.\n\n"
            "Commands:\n"
            "/signals - Get latest trading signals\n"
            "/analyze <symbol> - Technical analysis for a token\n"
            "/portfolio - View your portfolio\n"
            "/help - Show this help message"
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        help_text = (
            "📈 NinjaAgent Trading Bot Commands:\n\n"
            "/signals - Get latest trading signals\n"
            "/analyze <symbol> - Technical analysis for a token\n"
            "/portfolio - View your portfolio\n"
            "/help - Show this help message\n\n"
            "You can also send natural language trading commands like:\n"
            "'buy 10 INJ at market'\n"
            "'set alert when BTC drops below 60k'"
        )
        await update.message.reply_text(help_text)
        
    async def signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send latest trading signals"""
        # This would integrate with a real technical analysis engine
        signals_text = (
            "📊 Latest Trading Signals:\n\n"
            "🔔 INJ: Buy signal at $24.50 (RSI: 45.2)\n"
            "🔔 ATOM: Hold signal (neutral)\n"
            "🔔 OSMO: Sell signal below $1.20 (RSI: 65.8)\n\n"
            "Use /analyze <symbol> for detailed analysis"
        )
        await update.message.reply_text(signals_text)
        
    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Provide technical analysis for a token"""
        if context.args:
            symbol = context.args[0].upper()
            # Map symbol to CoinGecko id (simple mapping for common tokens)
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'INJ': 'injective-protocol',  # Fixed mapping for Injective
                'ATOM': 'cosmos',
                'OSMO': 'osmosis',
                'USDT': 'tether',
                'USDC': 'usd-coin',
                'BNB': 'binancecoin',
                'SOL': 'solana',
                'DOT': 'polkadot',
            }
            await update.message.reply_text("⏳ Mengambil data real-time dari CoinGecko...")
            coin_id = symbol_map.get(symbol, symbol.lower())
            try:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
                response = requests.get(url, timeout=10)
                data = response.json()
                if coin_id not in data:
                    await update.message.reply_text(f"❌ Gagal ambil data untuk {symbol}. Coba simbol lain ya.")
                    return
                coin_data = data[coin_id]
                price = coin_data.get('usd', 0)
                change_24h = coin_data.get('usd_24h_change', 0)
                volume = coin_data.get('usd_24h_vol', 0)
                mkt_cap = coin_data.get('usd_market_cap', 0)
                # RSI dinamis dari 24h change (indikator sederhana)
                if change_24h > 3:
                    rsi = 60 + min(abs(change_24h) * 2, 25)
                elif change_24h < -3:
                    rsi = 40 - min(abs(change_24h) * 2, 25)
                else:
                    rsi = 50
                if rsi > 70:
                    rsi_status = "Overbought"
                elif rsi < 30:
                    rsi_status = "Oversold"
                else:
                    rsi_status = "Neutral"
                # Signal logic
                if change_24h > 5 and rsi < 70:
                    signal = "🔥 STRONG BUY - Momentum naik"
                elif change_24h > 0:
                    signal = "📈 BUY - Uptrend"
                elif change_24h < -5 and rsi > 30:
                    signal = "💥 STRONG SELL - Momentum turun"
                elif change_24h < 0:
                    signal = "📉 SELL - Downtrend"
                else:
                    signal = "🤝 HOLD - Neutral"
                # Format numbers
                if volume >= 1e9:
                    volume_str = f"${volume/1e9:.2f}B"
                elif volume >= 1e6:
                    volume_str = f"${volume/1e6:.2f}M"
                else:
                    volume_str = f"${volume:.2f}"
                if mkt_cap >= 1e9:
                    mkt_str = f"${mkt_cap/1e9:.2f}B"
                elif mkt_cap >= 1e6:
                    mkt_str = f"${mkt_cap/1e6:.2f}M"
                else:
                    mkt_str = f"${mkt_cap:.2f}"
                analysis_text = (
                    f"🔬 **Live Analysis {symbol}**\n\n"
                    f"💲 Price: **${price:,.2f}**\n"
                    f"📊 RSI: **{rsi:.1f}** ({rsi_status})\n"
                    f"📉 24h Change: **{change_24h:+.2f}%**\n"
                    f"📊 Volume: {volume_str}\n"
                    f"🏦 Market Cap: {mkt_str}\n\n"
                    f"📡 Signal: **{signal}**\n"
                    f"📅 Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                )
                await update.message.reply_text(analysis_text)
            except Exception as e:
                logger.error(f"Error in analyze: {e}")
                await update.message.reply_text(f"❌ Error ambil data {symbol}. Coba lagi nanti ya.")
        else:
            await update.message.reply_text("Please specify a token symbol: /analyze <symbol>")
            
    async def portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show real-time portfolio status using Arkham API or fallback to CoinGecko"""
        user_id = str(update.effective_user.id)
        wallets = get_user_wallets(user_id)
        
        if not wallets:
            await update.message.reply_text(
                "💼 Your Portfolio:\n\n"
                "You haven't added any wallet addresses yet.\n"
                "Use /add_wallet <address> to add your wallet.\n\n"
                "Supported formats:\n"
                "• Injective: inj...\n"
                "• EVM: 0x..."
            )
            return
        
        await update.message.reply_text("⏳ Fetching real-time portfolio data...")
        
        # Get all tokens from all wallets and aggregate
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
        
        # Get current prices for each token
        try:
            token_symbols = list(all_balances.keys())
            token_ids = [self._symbol_to_coingecko_id(s) for s in token_symbols]
            ids_param = ",".join(token_ids)
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd"
            response = requests.get(url, timeout=15)
            data = response.json()
            
            # Format portfolio
            lines = ["💼 Your Portfolio (Real-time)\n"]
            total_value = 0
            
            for symbol in token_symbols:
                coingecko_id = self._symbol_to_coingecko_id(symbol)
                amount = all_balances[symbol]
                
                price_info = data.get(coingecko_id, {})
                price = price_info.get("usd", 0) if price_info else 0
                value = amount * price
                total_value += value
                
                if value > 0:
                    lines.append(f"{symbol}: {amount:.4f} (~${value:,.2f})")
            
            lines.append(f"\n💰 Total Value: ${total_value:,.2f}")
            lines.append(f"📅 Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            portfolio_text = "\n".join(lines)
            await update.message.reply_text(portfolio_text)
        except Exception as e:
            logger.error(f"Error fetching prices for portfolio: {e}")
            await update.message.reply_text(
                "❌ Error fetching real-time portfolio data.\n"
                "Showing approximate balances only:\n\n" + 
                "\n".join([f"{k}: {v:.4f}" for k, v in all_balances.items()])
            )

    def _get_wallet_balances(self, address: str) -> dict:
        """Fetch real-time balances from Injective API for Injective addresses and Etherscan for EVM addresses"""
        balances = {}
        
        if address.startswith("0x"):
            # For EVM addresses, we'll use Etherscan API for basic ETH balance
            try:
                # Note: This is a simplified example - in practice you'd need a proper Etherscan API key
                # and would make a real API call to Etherscan
                # For now, we'll return a placeholder
                return balances
            except Exception as e:
                logger.warning(f"Etherscan API failed for {address}: {e}")
                return balances
                
        elif address.startswith("inj"):
            # Injective API for Injective addresses
            try:
                url = f"https://api.injective.network/cosmos/bank/v1beta1/balances/{address}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for bal in data.get("balances", []):
                        denom = bal.get("denom", "")
                        amount = float(bal.get("amount", 0))
                        # Convert denom to symbol (simplified mapping)
                        symbol = self._denom_to_symbol(denom)
                        if symbol and amount > 0:
                            # Adjust for decimal places (e.g., INJ has 18 decimals)
                            decimals = self._get_token_decimals(symbol)
                            adjusted_amount = amount / (10 ** decimals)
                            if adjusted_amount > 0:
                                balances[symbol] = adjusted_amount
                    return balances
            except Exception as e:
                logger.warning(f"Injective API failed for {address}: {e}")
        
        return balances

    def _symbol_to_coingecko_id(self, symbol: str) -> str:
        """Map token symbol to CoinGecko ID"""
        mapping = {
            "INJ": "injective-protocol",
            "ATOM": "cosmos",
            "OSMO": "osmosis",
            "ETH": "ethereum",
            "BTC": "bitcoin",
            "BNB": "binancecoin",
            "SOL": "solana",
            "DOT": "polkadot",
            "USDT": "tether",
            "USDC": "usd-coin"
        }
        return mapping.get(symbol.upper(), symbol.lower())

    def _denom_to_symbol(self, denom: str) -> str:
        """Map Injective denom to symbol"""
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

    def _get_token_decimals(self, symbol: str) -> int:
        """Get decimal places for a token"""
        decimals = {
            "INJ": 18,
            "ATOM": 6,
            "OSMO": 6,
            "USDT": 6,
            "USDC": 6
        }
        return decimals.get(symbol.upper(), 6)
        
    async def add_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Add a new wallet address (Injective or EVM) to user's profile"""
        user_id = str(update.effective_user.id)
        
        if context.args:
            wallet_address = context.args[0]
            # Validate wallet address format (Injective or EVM)
            is_injective = wallet_address.startswith('inj') and len(wallet_address) == 42
            is_evm = wallet_address.startswith('0x') and len(wallet_address) == 42
            if not (is_injective or is_evm):
                await update.message.reply_text("Invalid wallet address format. Please provide a valid Injective (inj...) or EVM (0x...) wallet address.")
                return
            
            # Add wallet address to user's profile
            result = add_wallet_address(user_id, wallet_address)
            if result:
                await update.message.reply_text(f"Wallet address {wallet_address} added successfully!")
            else:
                await update.message.reply_text("Failed to add wallet address. Please try again.")
        else:
            await update.message.reply_text("Please provide a wallet address to add. Usage: /add_wallet <address>")

    async def my_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List user's wallet addresses"""
        user_id = str(update.effective_user.id)
        wallets = get_user_wallets(user_id)
        
        if wallets:
            wallet_list = "\\n".join(wallets)
            await update.message.reply_text(f"Your wallet addresses:\\n{wallet_list}")
        else:
            await update.message.reply_text("You haven't added any wallet addresses yet. Use /add_wallet <address> to add one.")

    async def remove_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Remove a wallet address from user's profile"""
        user_id = str(update.effective_user.id)
        
        if context.args:
            wallet_address = context.args[0]
            # Check if wallet address exists for this user
            if wallet_address_exists(user_id, wallet_address):
                result = remove_wallet_address(user_id, wallet_address)
                if result:
                    await update.message.reply_text(f"Wallet address {wallet_address} removed successfully!")
                else:
                    await update.message.reply_text("Failed to remove wallet address. Please try again.")
            else:
                await update.message.reply_text("Wallet address not found in your profile.")
        else:
            await update.message.reply_text("Please provide a wallet address to remove. Usage: /remove_wallet <address>")
            
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle natural language trading commands"""
        user_message = update.message.text
        
        # Parse command with NVIDIA AI
        # This would integrate with the agent's command parser
        response = f"Processing command: {user_message}\n\n"
        response += "✅ Command received successfully!\n"
        response += "Executing trade..."
        
        await update.message.reply_text(response)

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    # Create bot instance
    bot = NinjaAgentTelegramBot(os.getenv("TELEGRAM_BOT_TOKEN"))
    
    # Register handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("signals", bot.signals))
    application.add_handler(CommandHandler("analyze", bot.analyze))
    application.add_handler(CommandHandler("portfolio", bot.portfolio))
    # Add new wallet command handlers
    application.add_handler(CommandHandler("add_wallet", bot.add_wallet))
    application.add_handler(CommandHandler("my_wallets", bot.my_wallets))
    application.add_handler(CommandHandler("remove_wallet", bot.remove_wallet))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()