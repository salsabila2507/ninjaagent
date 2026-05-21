class InjectiveClient:
    """Simple Injective client wrapper"""
    def __init__(self):
        pass
    
    def get_market_data(self, market_id: str):
        """Get market data for a given market"""
        return {"market_id": market_id, "price": 0.0}

def get_injective_client() -> InjectiveClient:
    """Get the singleton Injective client instance"""
    return InjectiveClient()