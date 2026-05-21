class Agent:
    """Simple agent wrapper for NinjaAgent"""
    def __init__(self):
        pass
    
    def process_message(self, message: str) -> str:
        """Process a message and return a response"""
        return f"Processing: {message}"

def get_agent() -> Agent:
    """Get the singleton agent instance"""
    return Agent()