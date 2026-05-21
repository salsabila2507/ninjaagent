import os
import json
from typing import Dict, List, Optional

# User data storage
USER_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")

def _load_user_data() -> Dict:
    """Load user data from JSON file"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def _save_user_data(data: Dict):
    """Save user data to JSON file"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_wallet_address(user_id: str, wallet_address: str) -> bool:
    """Add a wallet address to a user's profile"""
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
        print(f"Error adding wallet: {e}")
        return False

def remove_wallet_address(user_id: str, wallet_address: str) -> bool:
    """Remove a wallet address from a user's profile"""
    try:
        data = _load_user_data()
        if user_id in data and "wallets" in data[user_id]:
            if wallet_address in data[user_id]["wallets"]:
                data[user_id]["wallets"].remove(wallet_address)
                _save_user_data(data)
                return True
        return False
    except Exception as e:
        print(f"Error removing wallet: {e}")
        return False

def get_user_wallets(user_id: str) -> List[str]:
    """Get all wallet addresses for a user"""
    data = _load_user_data()
    if user_id in data and "wallets" in data[user_id]:
        return data[user_id]["wallets"]
    return []

def wallet_address_exists(user_id: str, wallet_address: str) -> bool:
    """Check if a wallet address exists for a user"""
    wallets = get_user_wallets(user_id)
    return wallet_address in wallets