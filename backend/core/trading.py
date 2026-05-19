"""
Trading operations for Injective Protocol
"""
from typing import Dict, Any
import asyncio

class TradingEngine:
    """Trading execution engine for Injective Protocol"""
    
    def __init__(self, client):
        self.client = client
        self.active_orders = {}
        
    async def execute_trade(
        self,
        market_id: str,
        action: str,  # buy or sell
        amount: float,
        price: float = None  # None = market order
    ) -> Dict[str, Any]:
        """Execute a trade on Injective Protocol"""
        try:
            # Determine if it's market or limit order
            is_limit_order = price is not None
            
            if is_limit_order:
                # Place limit order
                result = await self.client.place_spot_order(
                    market_id=market_id,
                    order_type=action,
                    price=price,
                    quantity=amount,
                    is_buy=(action == "buy")
                )
            else:
                # Place market order (immediate execution)
                result = await self._execute_market_order(
                    market_id=market_id,
                    action=action,
                    amount=amount
                )
                
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Trade execution failed: {str(e)}"
            }
    
    async def _execute_market_order(
        self,
        market_id: str,
        action: str,
        amount: float
    ) -> Dict[str, Any]:
        """Execute market order (immediate)"""
        try:
            # For market orders, we set a price that will execute immediately
            # (slightly better price to ensure fill)
            mock_price = 1.0  # This would be calculated from market data
            
            result = await self.client.place_spot_order(
                market_id=market_id,
                order_type=action,
                price=mock_price,
                quantity=amount,
                is_buy=(action == "buy")
            )
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Market order failed: {str(e)}"
            }
    
    async def get_market_price(self, market_id: str) -> float:
        """Get current market price for a trading pair"""
        try:
            # Get latest trade price
            trades = await self.client.get_historical_trades(
                market_id=market_id,
                limit=1
            )
            
            if trades and len(trades) > 0:
                return float(trades[0].price)
            return 0.0
            
        except Exception as e:
            print(f"Failed to get market price: {e}")
            return 0.0
    
    async def monitor_positions(self):
        """Monitor open positions and manage risk"""
        while True:
            try:
                # Check active orders
                for order_id, order in self.active_orders.items():
                    # Get order status
                    status = await self.client.get_order_state(order_id=order_id)
                    
                    # If filled, update position
                    if status and status.state == "filled":
                        # Update portfolio
                        pass
                        
            except Exception as e:
                print(f"Position monitoring error: {e}")
                
            # Check every 30 seconds
            await asyncio.sleep(30)

# Singleton instance
trading_engine = None

async def get_trading_engine(client) -> TradingEngine:
    """Get or create trading engine instance"""
    global trading_engine
    if trading_engine is None:
        trading_engine = TradingEngine(client)
    return trading_engine