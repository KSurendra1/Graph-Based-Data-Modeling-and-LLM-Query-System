import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Database, User, Bot } from 'lucide-react';

const ChatBox = ({ onResponse }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    { id: 1, role: 'system', content: 'Hi! I can help you analyze the **Order to Cash** process.', isInitial: true }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = { id: Date.now(), role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/query', { query: userMessage.content });
      
      const botMessage = {
        id: Date.now() + 1,
        role: 'system',
        content: res.data.natural_response,
        sql: res.data.sql_query,
        structuredData: res.data.structured_data
      };
      
      setMessages(prev => [...prev, botMessage]);
      onResponse(res.data);
      
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { 
        id: Date.now() + 2, 
        role: 'system', 
        content: 'Failed to execute query. Check backend connection.',
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 relative">
      <div className="p-4 bg-white border-b border-slate-100 flex flex-col shadow-sm z-10">
        <h2 className="text-sm font-bold text-slate-800">Chat with Graph</h2>
        <span className="text-xs text-slate-400">Order to Cash</span>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm no-scrollbar bg-white">
        {messages.map((msg) => (
          <div key={msg.id} className="flex flex-col space-y-2">
            
            {/* Sender Identification */}
            <div className={`flex items-center gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'system' && (
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-black text-white flex items-center justify-center font-bold text-xs">
                    D
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-bold text-slate-800">Dodge AI</span>
                    <span className="text-[10px] text-slate-400 -mt-1">Graph Agent</span>
                  </div>
                </div>
              )}
              {msg.role === 'user' && (
                <div className="flex items-center gap-2 flex-row-reverse">
                  <div className="w-8 h-8 rounded-full bg-slate-300 text-slate-500 flex items-center justify-center">
                    <User className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-bold text-slate-800">You</span>
                </div>
              )}
            </div>

            {/* Message Bubble */}
            <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] p-4 text-[13px] leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-slate-900 text-white rounded-[20px] rounded-tr-sm shadow-md' 
                  : msg.isInitial 
                    ? 'text-slate-700 font-medium px-0'
                    : msg.isError 
                      ? 'bg-red-50 text-red-600 rounded-lg p-3 border border-red-100'
                      : 'text-slate-800 px-0'
              }`}>
                {msg.isInitial ? (
                  <p dangerouslySetInnerHTML={{ __html: msg.content.replace('**Order to Cash**', '<span class="font-bold">Order to Cash</span>') }}></p>
                ) : (
                  <p>{msg.content}</p>
                )}

                {(msg.sql || msg.structuredData) && (
                  <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                    <div className="flex items-center gap-1.5 text-slate-500 font-semibold mb-2 uppercase tracking-wider text-[10px]">
                      <Database className="w-3 h-3" /> Data Evidence
                    </div>
                    {msg.structuredData && msg.structuredData.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse whitespace-nowrap">
                          <thead>
                            <tr>
                              {Object.keys(msg.structuredData[0]).map(key => (
                                <th key={key} className="p-1 px-2 border-b border-slate-200 text-slate-400 font-medium">{key}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="text-slate-600 font-mono text-[11px]">
                            {msg.structuredData.slice(0,3).map((row, i) => (
                              <tr key={i}>
                                {Object.values(row).map((val, j) => (
                                  <td key={j} className="p-1 px-2 border-b border-slate-100">{String(val)}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {msg.structuredData.length > 3 && (
                          <div className="text-center text-[10px] text-slate-400 mt-2 font-medium">
                            +{msg.structuredData.length - 3} more rows
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white">
        <div className="rounded-xl border border-slate-200 shadow-sm overflow-hidden bg-white focus-within:ring-1 focus-within:ring-slate-300 focus-within:border-slate-300 transition-all">
          <div className="px-3 py-2 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${loading ? 'bg-amber-400 animate-pulse' : 'bg-green-500'}`}></div>
            <span className="text-[10px] text-slate-500 font-semibold">
              {loading ? 'Dodge AI is analyzing...' : 'Dodge AI is awaiting instructions'}
            </span>
          </div>
          <form onSubmit={handleSubmit} className="flex flex-col relative h-24">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Analyze anything"
              disabled={loading}
              className="flex-1 w-full bg-transparent resize-none p-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none disabled:opacity-50"
              onKeyDown={(e) => {
                if(e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <button 
              type="submit" 
              disabled={loading || !query.trim()}
              className="absolute bottom-3 right-3 px-4 py-1.5 bg-slate-400 text-white rounded-md hover:bg-slate-500 disabled:opacity-50 transition-colors text-xs font-semibold"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatBox;
