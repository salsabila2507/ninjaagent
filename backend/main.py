"""
Main application entry point for NinjaAgent
"""
import os
import asyncio
from typing import Dict
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.core.agent import get_agent
from backend.injective.client import get_injective_client
from backend.ai.parser import parse_command_async

app = FastAPI(title="NinjaAgent API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
ninja_agent = None
injective_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize clients on startup"""
    global ninja_agent, injective_client
    
    # Initialize NinjaAgent with NVIDIA API key
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_api_key:
        ninja_agent = get_agent(nvidia_api_key=nvidia_api_key)
    
    # Initialize Injective client if mnemonic is provided
    mnemonic = os.getenv("INJECTIVE_MNEMONIC")
    if mnemonic:
        network = os.getenv("INJECTIVE_NETWORK", "testnet")
        injective_client = await get_injective_client(network)
        await injective_client.init_client(mnemonic)

@app.post("/api/trade/execute")
async def execute_trade(command: dict):
    """
    Execute a natural language trading command
    
    Body: {"command": "buy 10 INJ at market"}
    """
    user_command = command.get("command", "")
    
    # Parse with NVIDIA LLM
    parsed = await parse_command_async(user_command)
    
    # Execute with agent
    result = await ninja_agent.process_command(user_command)
    
    return {
        "status": "success",
        "parsed": parsed,
        "result": result
    }

@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio status"""
    if ninja_agent:
        return await ninja_agent._show_portfolio()
    return {"error": "Agent not initialized"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process the data and send response
            await websocket.send_text("Command received")
    except Exception as e:
        await websocket.close(code=1000)

if __name__ == "__main__":
    # Run the server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)