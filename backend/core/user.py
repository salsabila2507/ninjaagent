import json
import os
from typing import Dict, List

# Simple JSON database for user wallet storage
DB_FILE = 'user_wallets.json'

def load_database() -> Dict:
    """Load the user wallet database from file"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"users": {}}

def save_database(data: Dict) -> None:
    """Save the user wallet database to file"""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_wallet_address(user_id: str, wallet_address: str) -> bool:
    """Add a wallet address for a user"""
    data = load_database()
    
    # Validate wallet address (basic validation)
    if not wallet_address or len(wallet_address) < 20:
        return False
    
    if user_id not in data["users"]:
        data["users"][user_id] = {"wallets": []}
    
    if wallet_address not in data["users"][user_id]["wallets"]:
        data["users"][user_id]["wallets"].append(wallet_address)
        save_database(data)
        return True
    return False

def get_user_wallets(user_id: str) -> List[str]:
    """Get all wallet addresses for a user"""
    data = load_database()
    if user_id in data["users"]:
        return data["users"][user_id]["wallets"]
    return []

def remove_wallet_address(user_id: str, wallet_address: str) -> bool:
    """Remove a wallet address for a user"""
    data = load_database()
    if user_id in data["users"] and wallet_address in data["users"][user_id]["wallets"]:
        data["users"][user_id]["wallets"].remove(wallet_address)
        save_database(data)
        return True
    return False

def wallet_address_exists(user_id: str, wallet_address: str) -> bool:
    """Check if a wallet address exists for a user"""
    data = load_database()
    if user_id in data["users"]:
        return wallet_address in data["users"][user_id]["wallets"]
    return False