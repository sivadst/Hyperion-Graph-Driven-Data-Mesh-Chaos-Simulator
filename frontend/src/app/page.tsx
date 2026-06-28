"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { TopologyCanvas } from '@/components/topology-canvas';
import { ControlCenter } from '@/components/control-center';
import { AnalyticsPanel } from '@/components/analytics-panel';
import { LiveTerminal } from '@/components/live-terminal';
import { Topology, SimulationState, NodeState } from '@/lib/types';
import { Node as FlowNode, Edge as FlowEdge } from 'reactflow';
import { Layers } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace('http', 'ws');

export default function Home() {
  const [topologies, setTopologies] = useState<{id: string, name: string}[]>([]);
  const [activeTopology, setActiveTopology] = useState<Topology | null>(null);
  
  const [runId, setRunId] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [edges, setEdges] = useState<FlowEdge[]>([]);
  const [rawNodesState, setRawNodesState] = useState<NodeState[]>([]);
  
  const [centrality, setCentrality] = useState<{betweenness: Record<string, number>, pagerank: Record<string, number>}>({ betweenness: {}, pagerank: {} });
  const [logs, setLogs] = useState<string[]>([]);

  // Fetch initial topologies
  useEffect(() => {
    fetch(`${API_URL}/api/topology/`)
      .then(res => res.json())
      .then(data => {
        setTopologies(data);
        if (data.length > 0) {
          loadTopology(data[0].id);
        }
      })
      .catch(err => console.error("Failed to load topologies", err));
  }, []);

  const loadTopology = async (id: string) => {
    const res = await fetch(`${API_URL}/api/topology/${id}`);
    const data: Topology = await res.json();
    setActiveTopology(data);
    
    // Setup initial ReactFlow nodes and edges
    const flowNodes = data.nodes.map((n, i) => ({
      id: n.id,
      type: 'custom',
      position: { x: (i % 3) * 250 + 100, y: Math.floor(i / 3) * 150 + 100 }, // basic auto-layout
      data: { label: n.name, type: n.type }
    }));
    
    const flowEdges = data.edges.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      animated: false,
      style: { stroke: '#475569', strokeWidth: 2 }
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  };

  const startSimulation = async () => {
    if (!activeTopology) return;
    
    const res = await fetch(`${API_URL}/api/simulation/start/${activeTopology.id}`, { method: 'POST' });
    const data = await res.json();
    setRunId(data.run_id);
    setLogs(prev => [...prev, `Simulation Run [${data.run_id}] started.`]);

    const socket = new WebSocket(`${WS_URL}/api/simulation/ws/${data.run_id}`);
    
    socket.onmessage = (event) => {
      const state: SimulationState = JSON.parse(event.data);
      
      if (state.status === 'COMPLETED') {
        setRunId(null);
        socket.close();
        setLogs(prev => [...prev, `Simulation Run [${data.run_id}] completed.`]);
        return;
      }

      setRawNodesState(state.nodes);
      setCentrality(state.centrality);

      // Update flow nodes
      setNodes(prevNodes => prevNodes.map(n => {
        const nState = state.nodes.find(sn => sn.id === n.id);
        return {
          ...n,
          data: { ...n.data, state: nState }
        };
      }));

      // Update flow edges
      setEdges(prevEdges => prevEdges.map(e => {
        const eState = state.edges.find(se => se.source === e.source && se.target === e.target);
        
        const isSevered = eState?.status === 'Severed';
        
        return {
          ...e,
          animated: !isSevered && eState?.weight > 0,
          style: { 
            stroke: isSevered ? '#ef4444' : '#3b82f6', 
            strokeWidth: isSevered ? 1 : 2,
            opacity: isSevered ? 0.3 : 1,
            strokeDasharray: isSevered ? '5,5' : 'none'
          }
        };
      }));

      // Log structural changes
      state.nodes.forEach(n => {
        if (n.status === 'Isolated') {
          setLogs(prev => {
            const msg = `AI Core mitigation triggered: Circuit Breaking applied to ${n.id}`;
            return prev[prev.length - 1] !== msg ? [...prev, msg].slice(-50) : prev;
          });
        }
      });
    };

    setWs(socket);
  };

  const stopSimulation = async () => {
    if (!runId) return;
    await fetch(`${API_URL}/api/simulation/stop/${runId}`, { method: 'POST' });
  };

  const injectFault = async (nodeId: string, type: string, severity: number) => {
    if (!runId) return;
    await fetch(`${API_URL}/api/simulation/inject/${runId}/${nodeId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, severity })
    });
    setLogs(prev => [...prev, `Injected ${type} (severity: ${severity}) into ${nodeId}`]);
  };

  return (
    <main className="h-screen w-full flex flex-col p-4 gap-4 overflow-hidden bg-slate-950 text-slate-50">
      
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-800 pb-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Hyperion</h1>
            <p className="text-xs text-slate-400">Enterprise Data Mesh Drift & Chaos Simulator</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <select 
            className="bg-slate-900 border border-slate-800 rounded-md p-2 text-sm"
            onChange={(e) => loadTopology(e.target.value)}
            disabled={!!runId}
          >
            {topologies.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        
        {/* Left Column (Canvas) */}
        <div className="col-span-9 rounded-xl flex flex-col gap-4">
          <div className="flex-1 min-h-0">
            <TopologyCanvas nodes={nodes} edges={edges} />
          </div>
          
          <div className="h-48 shrink-0">
            <LiveTerminal logs={logs} />
          </div>
        </div>

        {/* Right Column (Controls & Analytics) */}
        <div className="col-span-3 flex flex-col gap-4 min-h-0">
          <div className="flex-1 min-h-0">
            <ControlCenter 
              runId={runId} 
              nodes={rawNodesState}
              onStart={startSimulation}
              onStop={stopSimulation}
              onInjectFault={injectFault}
            />
          </div>
          <div className="flex-1 min-h-0">
            <AnalyticsPanel centrality={centrality} />
          </div>
        </div>
        
      </div>
    </main>
  );
}
