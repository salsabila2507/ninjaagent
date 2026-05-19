"""
Technical Analysis Engine for NinjaAgent
Provides real-time market analysis and trading signals
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """Technical analysis engine for trading signals"""
    
    def __init__(self):
        self.signals = []
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
            
        # Calculate price changes
        deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
        
        # Calculate gains and losses
        gains = [max(0, delta) for delta in deltas]
        losses = [max(0, -delta) for delta in deltas]
        
        # Calculate average gain and loss
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        # Calculate RSI
        if avg_loss == 0:
            return 100.0
        elif avg_gain == 0:
            return 0.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
            
    def calculate_macd(self, prices: List[float], fast_period: int = 12, slow_period: int = 26) -> Dict:
        """Calculate MACD indicators"""
        # Convert to pandas Series for easier calculation
        price_series = pd.Series(prices)
        
        # Calculate EMAs
        ema_fast = price_series.ewm(span=fast_period).mean()
        ema_slow = price_series.ewm(span=slow_period).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line (9-period EMA of MACD line)
        signal_line = macd_line.ewm(span=9).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.iloc[-1],
            'signal': signal_line.iloc[-1],
            'histogram': histogram.iloc[-1]
        }
        
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, num_std: int = 2) -> Dict:
        """Calculate Bollinger Bands"""
        price_series = pd.Series(prices)
        
        # Middle band (20-period SMA)
        middle_band = price_series.rolling(window=period).mean()
        
        # Standard deviation
        std_dev = price_series.rolling(window=period).std()
        
        # Upper and lower bands
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        return {
            'upper_band': upper_band.iloc[-1],
            'middle_band': middle_band.iloc[-1],
            'lower_band': lower_band.iloc[-1]
        }
        
    def generate_signal(self, prices: List[float], rsi: float, macd_data: Dict) -> str:
        """Generate trading signal based on technical indicators"""
        signals = []
        
        # RSI Signal
        if rsi < 30:
            signals.append("BUY")
        elif rsi > 70:
            signals.append("SELL")
        else:
            signals.append("HOLD")
            
        # MACD Signal
        if macd_data['histogram'] > 0:
            signals.append("BULLISH")
        elif macd_data['histogram'] < 0:
            signals.append("BEARISH")
            
        # Bollinger Band Signal
        if len(prices) > 0:
            current_price = prices[-1]
            # This would need actual Bollinger band data
            # if current_price < lower_band:
            #     signals.append("OVERSOLD")
            # elif current_price > upper_band:
            #     signals.append("OVERBOUGHT")
                
        return ", ".join(signals) if signals else "HOLD"
        
    def get_trading_signals(self, market_data: Dict) -> Dict:
        """Get comprehensive trading signals for assets"""
        signals = {}
        
        # This would process real market data
        # For now, return sample data
        signals['INJ'] = {
            'price': 24.50,
            'rsi': 45.2,
            'signal': 'HOLD',
            'analysis': 'Neutral market condition, wait for breakout'
        }
        
        signals['ATOM'] = {
            'price': 25.00,
            'rsi': 50.0,
            'signal': 'HOLD',
            'analysis': 'Stable market, no strong signals'
        }
        
        return signals

# Global analyzer instance
analyzer = TechnicalAnalyzer()

def get_market_analysis(prices: List[float], symbol: str) -> Dict:
    """Get comprehensive market analysis for a symbol"""
    # Calculate technical indicators
    rsi = analyzer.calculate_rsi(prices)
    
    # Get MACD data
    macd_data = analyzer.calculate_macd(prices)
    
    # Get Bollinger bands
    bb_data = analyzer.calculate_bollinger_bands(prices)
    
    # Generate signal
    signal = analyzer.generate_signal(prices, rsi, macd_data)
    
    return {
        'symbol': symbol,
        'price': prices[-1] if prices else 0,
        'rsi': rsi,
        'macd': macd_data,
        'bollinger_bands': bb_data,
        'signal': signal,
        'timestamp': pd.Timestamp.now()
    }