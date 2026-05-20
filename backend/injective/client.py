"""
Injective client stub for NinjaAgent
"""

def get_injective_client():
    """Return a mock injective client"""
    class MockClient:
        def __init__(self):
            self.initialized = True
            
        def get_market_data(self, symbol):
            return {"price": 24.50, "change_24h": -2.3}
            
        def get_account_info(self):
            return {"balance": {"INJ": 10.5, "ATOM": 2.1, "OSMO": 15.0}}
    
    return MockClient()