import React from 'react';
import { useState, useEffect } from 'react';

export default function Home() {
  const [command, setCommand] = useState('');
  const [response, setResponse] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Create WebSocket connection
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => {
      setIsConnected(true);
    };
    ws.onclose = () => {
      setIsConnected(false);
    };
    setSocket(ws);

    return () => {
      ws.close();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Send command to backend
    const response = await fetch('/api/trade/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ command }),
    });
    
    const data = await response.json();
    setResponse(JSON.stringify(data, null, 2));
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">NinjaAgent Trading Dashboard</h1>
      
      <div className="mb-4">
        <p className="text-green-500">● Connected: {isConnected ? 'Yes' : 'No'}</p>
      </div>

      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Enter trading command (e.g., 'buy 10 INJ at market')"
            className="flex-1 p-2 border border-gray-300 rounded"
          />
          <button 
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Execute
          </button>
        </div>
      </form>

      <div className="bg-gray-100 p-4 rounded">
        <pre>{response}</pre>
      </div>
    </div>
  );
}