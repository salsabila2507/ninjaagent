"""
Natural Language Command Parser using NVIDIA LLM API
Converts user trading commands into structured actions
"""
import json
import os
from typing import Dict
import requests

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "nvapi-your-key")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com"

SYSTEM_PROMPT = """You are a trading assistant command parser for Injective Protocol.
Convert natural language trading commands into structured JSON.

Available actions: buy, sell, set_alert, cancel_order, portfolio, market_data
Assets: INJ, BTC, ETH, USDT, USDC

Rules:
- Always return valid JSON only
- Interpret vague amounts smartly (e.g., "all" = 100%, "half" = 50%)
- Detect asset symbols even if not explicitly mentioned (context-based)
- For alerts: extract condition (above/below) and price level

Response format:
{
  "action": "buy|sell|set_alert|cancel_order|portfolio|market_data",
  "asset": "INJ|BTC|ETH|USDT|USDC",
  "amount": "float or percentage (e.g., '100' or '50%')",
  "price": "float or null for market order",
  "condition": "conditional expression for alerts, e.g., 'price_below_20'"
}
"""


def parse_command(command: str) -> Dict:
    """
    Parse natural language command into structured trading parameters
    
    Examples:
    - "buy 10 INJ at market" -> {"action": "buy", "asset": "INJ", "amount": 10, "price": null}
    - "set alert when bitcoin drops below 60k" -> {"action": "set_alert", "asset": "BTC", "condition": "price_below_60000"}
    - "sell half of my INJ" -> {"action": "sell", "asset": "INJ", "amount": "50%"}
    - "what's my portfolio worth?" -> {"action": "portfolio"}
    """
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen/qwen3-coder-480b-a35b-instruct",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": command}
        ],
        "temperature": 0.2,  # Low temp for consistent, deterministic parsing
        "max_tokens": 300
    }
    
    try:
        response = requests.post(
            f"{NVIDIA_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        parsed_text = result["choices"][0]["message"]["content"]
        
        # Extract JSON from response
        parsed = json.loads(parsed_text.strip())
        return parsed
        
    except json.JSONDecodeError:
        # Fallback: basic keyword matching
        return _fallback_parse(command)
    except requests.exceptions.RequestException as e:
        return {
            "action": "error",
            "message": f"API error: {str(e)}"
        }


def _fallback_parse(command: str) -> Dict:
    """Simple fallback parser when API fails"""
    command_lower = command.lower()
    
    # Detect action
    if "buy" in command_lower:
        action = "buy"
    elif "sell" in command_lower:
        action = "sell"
    elif "alert" in command_lower or "when" in command_lower:
        action = "set_alert"
    elif "portfolio" in command_lower:
        action = "portfolio"
    else:
        action = "unknown"
    
    # Detect asset
    asset = None
    for coin in ["inj", "btc", "eth", "usdt", "usdc"]:
        if coin in command_lower:
            asset = coin.upper()
            break
    
    return {
        "action": action,
        "asset": asset,
        "amount": None,
        "price": None,
        "condition": None,
        "fallback": True
    }


# Async wrapper for integration with FastAPI
async def parse_command_async(command: str) -> Dict:
    """Async wrapper for parse_command"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, parse_command, command)
