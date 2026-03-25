import React, { useRef, useEffect } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';

const GraphView = ({ elements, activeNodes, onNodeClick }) => {
  const cyRef = useRef(null);

  // Styling matching the screenshot UI
  const style = [
    {
      selector: 'node',
      style: {
        'background-color': '#fff',
        'border-color': '#93c5fd', // pale blue
        'border-width': 1,
        'width': 6,
        'height': 6,
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 1,
        'line-color': '#bfdbfe', // light blue from screenshot
        'curve-style': 'bezier',
        'opacity': 0.6,
      }
    },
    // Distinct entity colors (e.g. Sales Orders, Customers) can be subtly different
    { selector: 'node[type="Order"]', style: { 'background-color': '#3b82f6', 'width': 8, 'height': 8 } },
    { selector: 'node[type="Invoice"]', style: { 'background-color': '#f87171', 'border-width': 0 } },
    { selector: 'node[type="Customer"]', style: { 'background-color': '#cbd5e1', 'border-width': 0 } },
    
    // Highlighted nodes / edges from query
    {
      selector: '.highlighted',
      style: {
        'border-width': 2,
        'border-color': '#2563eb', // dark blue highlight
        'width': 12,
        'height': 12,
        'background-color': '#3b82f6',
        'box-shadow': '0 0 10px #60a5fa',
        'z-index': 100
      }
    },
    {
      selector: '.highlighted-edge',
      style: {
        'width': 2,
        'line-color': '#3b82f6',
        'opacity': 1,
        'target-arrow-shape': 'triangle',
        'target-arrow-color': '#3b82f6',
        'z-index': 99
      }
    }
  ];

  const layout = {
    name: 'cose',
    idealEdgeLength: 50,
    nodeOverlap: 20,
    refresh: 20,
    fit: true,
    padding: 50,
    randomize: false,
    componentSpacing: 100,
    nodeRepulsion: 400000,
    edgeElasticity: 100,
    nestingFactor: 5,
    gravity: 80,
    numIter: 1000,
    initialTemp: 200,
    coolingFactor: 0.95,
    minTemp: 1.0
  };

  useEffect(() => {
    if (cyRef.current) {
      const cy = cyRef.current;
      
      // Clear previous highlights
      cy.elements().removeClass('highlighted highlighted-edge');
      
      // Apply new highlights
      if (activeNodes && activeNodes.length > 0) {
        activeNodes.forEach(id => {
          cy.$(`#${id}`).addClass('highlighted');
          // Highlight connected edges as well
          cy.$(`#${id}`).connectedEdges().addClass('highlighted-edge');
        });
        
        const highlightedElements = cy.elements('.highlighted');
        if (highlightedElements.length > 0) {
          cy.animate({
            fit: {
              eles: highlightedElements,
              padding: 50
            },
            duration: 800
          });
        }
      } else {
        cy.animate({
          fit: { padding: 50 },
          duration: 800
        });
      }
    }
  }, [activeNodes]);

  useEffect(() => {
    if (cyRef.current) {
      const cy = cyRef.current;
      cy.on('tap', 'node', (evt) => {
        const node = evt.target;
        onNodeClick(node.id());
      });
      return () => {
        cy.removeListener('tap');
      };
    }
  }, [onNodeClick]);

  return (
    <div className="w-full h-full bg-slate-50 relative overflow-hidden">
      {/* Optional faint grid background pattern here if desired */}
      <CytoscapeComponent 
        elements={CytoscapeComponent.normalizeElements(elements)} 
        style={{ width: '100%', height: '100%' }}
        stylesheet={style}
        layout={layout}
        cy={(cy) => { cyRef.current = cy }}
        wheelSensitivity={0.2}
      />
    </div>
  );
};

export default GraphView;
