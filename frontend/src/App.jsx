import React, { useEffect, useState } from 'react';
import axios from 'axios';
import GraphView from './components/GraphView';
import ChatBox from './components/ChatBox';
import { LayoutDashboard, Minimize2, Layers } from 'lucide-react';

function App() {
  const [elements, setElements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeNodes, setActiveNodes] = useState([]);
  const [selectedNodeData, setSelectedNodeData] = useState(null);
  const [showGranular, setShowGranular] = useState(true);

  // Fetch initial graph
  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const res = await axios.get('http://localhost:8000/graph');
        const data = res.data;
        
        const formattedElements = [
          ...data.nodes.map(n => ({ data: { ...n } })),
          ...data.edges.map(e => ({ data: { id: e.id, source: e.source, target: e.target, label: e.type } }))
        ];
        
        setElements(formattedElements);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setError("Failed to load graph data. Make sure backend is running on port 8000.");
        setLoading(false);
      }
    };
    fetchGraph();
  }, []);

  const handleQueryResponse = (response) => {
    if (response.affected_nodes && response.affected_nodes.length > 0) {
      setActiveNodes(response.affected_nodes);
    } else {
      setActiveNodes([]);
    }
  };

  const handleNodeClick = async (nodeId) => {
    try {
      const res = await axios.get(`http://localhost:8000/node/${nodeId}`);
      setSelectedNodeData(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden bg-white text-slate-800 font-sans">
      
      {/* Top Header */}
      <div className="h-14 border-b border-slate-200 flex items-center px-4 shrink-0 bg-white">
        <LayoutDashboard className="w-5 h-5 text-slate-500 mr-3" />
        <span className="text-slate-400 font-medium mr-2">Mapping</span>
        <span className="text-slate-300 mx-2">/</span>
        <span className="text-slate-800 font-semibold">Order to Cash</span>
      </div>

      <div className="flex flex-1 h-[calc(100vh-3.5rem)] overflow-hidden">
        {/* Left Panel: Graph View */}
        <div className="flex-1 relative border-r border-slate-200 bg-slate-50">
          
          {/* Top Left Floating Controls */}
          <div className="absolute top-4 left-4 z-10 flex gap-2">
            <button className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-md shadow-sm text-sm font-medium hover:bg-slate-50">
              <Minimize2 className="w-4 h-4" /> Minimize
            </button>
            <button 
              onClick={() => setShowGranular(!showGranular)}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 text-white rounded-md shadow-sm text-sm font-medium hover:bg-slate-800"
            >
              <Layers className="w-4 h-4" /> {showGranular ? "Hide Granular Overlay" : "Show Granular Overlay"}
            </button>
          </div>
          
          {loading ? (
            <div className="flex items-center justify-center h-full w-full">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full w-full flex-col">
              <p className="text-red-500 font-medium">{error}</p>
            </div>
          ) : (
            <GraphView 
              elements={elements} 
              activeNodes={activeNodes}
              onNodeClick={handleNodeClick}
            />
          )}

          {/* Floating Node Details Card */}
          {selectedNodeData && (
            <div className="absolute top-32 left-[25%] bg-white p-5 rounded-xl border border-slate-200 shadow-xl z-20 w-80 max-h-96 overflow-y-auto">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold text-slate-900">
                  {selectedNodeData.label}
                </h3>
                <button 
                  onClick={() => setSelectedNodeData(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-2 text-sm text-slate-600">
                <p><span className="font-semibold text-slate-500">ID:</span> {selectedNodeData.id.split('_')[1]}</p>
                {Object.entries(selectedNodeData.properties || {}).map(([key, value]) => (
                  <p key={key}>
                    <span className="font-semibold text-slate-500 capitalize">{key}:</span> {String(value)}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel: Chat Interface */}
        <div className="w-[400px] flex flex-col bg-white shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)] z-10">
          <ChatBox onResponse={handleQueryResponse} />
        </div>
      </div>
      
    </div>
  );
}

export default App;
