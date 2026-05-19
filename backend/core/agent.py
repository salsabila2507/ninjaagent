import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

class TradeCommand(BaseModel):
    action: str  # buy, sell, set_alert, cancel_order
    asset: Optional[str] = None
    amount: Optional[float] = None
    price: Optional[float] = None
    condition: Optional[str] = None

class MarketData(BaseModel):
    asset: str
    price: float
    change_24h: float
    volume_24h: float
    timestamp: datetime

class NinjaAgent:
    """
    Autonomous AI Trading Assistant for Injective Protocol
    - Understands natural language trading commands
    - Monitors market conditions in real-time
    - Executes trades via Injective API
    - Provides intelligent risk management
    """
    
    def __init__(self, nvidia_api_key: str, mnemonic: Optional[str] = None):
        self.nvidia_api_key = nvidia_api_key
        self.mnemonic = mnemonic
        self.wallet_address = None
        self.active_alerts = []
        self.position_size = 0.0
        self.max_position = 1000.0  # Max $1000 per trade
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.take_profit_pct = 0.10  # 10% take profit
        self.trade_history = []
        
    async def process_command(self, command: str) -> Dict:
        """
        Parse natural language command and execute trading action
        Examples:
        - 'buy 10 INJ at market price'
        - 'set alert when INJ drops below $20'
        - 'sell 50% of my INJ position'
        - 'show my portfolio'
        """
        # Parse command using NVIDIA LLM
        parsed = await self._parse_command_with_ai(command)
        
        if parsed['action'] == 'buy':
            return await self._execute_buy(parsed)
        elif parsed['action'] == 'sell':
            return await self._execute_sell(parsed)
        elif parsed['action'] == 'set_alert':
            return await self._set_alert(parsed)
        elif parsed['action'] == 'portfolio':
            return await self._show_portfolio()
        elif parsed['action'] == 'market_data':
            return await self._get_market_data(parsed.get('asset'))
        else:
            return {
                'status': 'error',
                'message': f"Unknown command: {command}"
            }
    
    async def _parse_command_with_ai(self, command: str) -> Dict:
        """Use NVIDIA LLM to parse natural language into structured commands"""
        # Implementation akan diisi di ai/parser.py
        pass
    
    async def _execute_buy(self, order_params: Dict) -> Dict:
        """Execute buy order with risk management checks"""
        # Risk management check
        if order_params.get('amount', 0) > self.max_position:
            return {
                'status': 'rejected',
                'reason': f"Order exceeds max position size of ${self.max_position}"
            }
        
        # Execute via Injective client
        # ... implementation in trading.py
        
        self.position_size += order_params.get('amount', 0)
        return {
            'status': 'executed',
            'action': 'buy',
            'details': order_params
        }
    
    async def _execute_sell(self, order_params: Dict) -> Dict:
        """Execute sell order"""
        # Implementation akan diisi di trading.py
        pass
    
    async def _set_alert(self, alert_params: Dict) -> Dict:
        """Set price alert for an asset"""
        alert = {
            'asset': alert_params['asset'],
            'condition': alert_params['condition'],
            'created_at': datetime.now()
        }
        self.active_alerts.append(alert)
        return {
            'status': 'alert_set',
            'alert': alert
        }
    
    async def _show_portfolio(self) -> Dict:
        """Show current portfolio and P&L"""
        return {
            'status': 'success',
            'portfolio': {
                'positions': self.trade_history,
                'total_value': self.position_size,
                'alerts': len(self.active_alerts)
            }
        }
    
    async def _get_market_data(self, asset: Optional[str]) -> Dict:
        """Get real-time market data for specified asset or all tracked assets"""
        # Implementation akan diisi di market_monitor.py
        pass
    
    async def monitor_market(self):
        """Continuously monitor market and trigger alerts"""
        while True:
            for alert in self.active_alerts:
                # Check if condition met
                # ... price check logic
                pass
            await asyncio.sleep(30)  # Check every 30 seconds

# Singleton instance
agent_instance = None

def get_agent(nvidia_api_key: str) -> NinjaAgent:
    """Get or create NinjaAgent instance"""
    global agent_instance
    if agent_instance is None:
        agent_instance = NinjaAgent(nvidia_api_key=nvidia_api_key)
    return agent_instance
