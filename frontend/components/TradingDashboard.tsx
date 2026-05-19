"use client";

import { useState, useEffect, useRef } from "react";

interface TradeHistory {
  id: string;
  action: string;
  asset: string;
  amount: number;
  price: number;
  timestamp: string;
  status: string;
}

interface MarketData {
  asset: string;
  price: number;
  change_24h: number;
  volume_24h: number;
}

export default function TradingDashboard() {
  const [command, setCommand] = useState("");
  const [chatHistory, setChatHistory] = useState<{role: string, content: string}[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [portfolio, setPortfolio] = useState({
    total_value: 0,
    positions: [],
    alerts: 0
  });
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize WebSocket
  useEffect(() => {
    const ws = new WebSocket("wss://your-api-url/ws");
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "command_result") {
        setChatHistory(prev => [...prev, {
          role: "assistant",
          content: JSON.stringify(data.data, null, 2)
        }]);
        setIsProcessing(false);
      }
    };

    return () => ws.close();
  }, []);

  const executeCommand = async () => {
    if (!command.trim()) return;
    
    setIsProcessing(true);
    setChatHistory(prev => [...prev, { role: "user", content: command }]);

    // Send via WebSocket if available
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "command",
        command: command
      }));
    } else {
      // Fallback to HTTP
      try {
        const response = await fetch("/api/trade/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command })
        });
        const result = await response.json();
        
        setChatHistory(prev => [...prev, {
          role: "assistant",
          content: JSON.stringify(result, null, 2)
        }]);
      } catch (error) {
        setChatHistory(prev => [...prev, {
          role: "assistant",
          content: `Error: ${error}`
        }]);
      }
      setIsProcessing(false);
    }
    
    setCommand("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      executeCommand();
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      {/* Header */}
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
          NinjaAgent
        </h1>
        <p className="text-gray-400 mt-2">AI-Powered Trading Assistant for Injective Protocol</p>
      </header>

      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Interface */}
        <div className="lg:col-span-2 bg-gray-800 rounded-xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="text-green-400">●</span> Trading Console
          </h2>
          
          {/* Chat History */}
          <div className="h-96 overflow-y-auto mb-4 bg-gray-900 rounded-lg p-4">
            {chatHistory.map((msg, index) => (
              <div key={index} className={`mb-4 ${msg.role === "user" ? "text-right" : "text-left"}`}>
                <div className={`inline-block max-w-[80%] p-3 rounded-lg ${
                  msg.role === "user" 
                    ? "bg-blue-600 text-white" 
                    : "bg-gray-700 text-gray-200"
                }`}>
                  <pre className="whitespace-pre-wrap text-sm font-mono">{msg.content}</pre>
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="text-center text-gray-400 mt-4">
                <div className="animate-spin inline-block w-6 h-6 border-2 border-white border-t-transparent rounded-full"></div>
              </div>
            )}
          </div>

          {/* Command Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Try: 'buy 10 INJ at market' or 'set alert when INJ drops below $20'"
              className="flex-1 bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={executeCommand}
              disabled={isProcessing}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
            >
              Execute
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Portfolio Summary */}
          <div className="bg-gray-800 rounded-xl p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4">Portfolio</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Total Value</span>
                <span className="text-xl font-bold text-green-400">${portfolio.total_value.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Active Alerts</span>
                <span className="text-blue-400">{portfolio.alerts}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Positions</span>
                <span className="text-purple-400">{portfolio.positions.length}</span>
              </div>
            </div>
          </div>

          {/* Example Commands */}
          <div className="bg-gray-800 rounded-xl p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4">Quick Commands</h3>
            <div className="space-y-2">
              {[
                "buy 10 INJ at market",
                "sell 50% of my INJ",
                "set alert when INJ > $25",
                "show my portfolio",
                "get INJ market data"
              ].map((cmd, i) => (
                <button
                  key={i}
                  onClick={() => setCommand(cmd)}
                  className="w-full text-left p-2 rounded bg-gray-700 hover:bg-gray-600 text-sm transition-colors"
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <footer className="mt-8 text-center text-gray-500 text-sm">
        <p>NinjaAgent v1.0 — Built for Injective Solo AI Builder Sprint</p>
        <p className="mt-1">Powered by NVIDIA AI + Injective Protocol</p>
      </footer>
    </div>
  );
}
