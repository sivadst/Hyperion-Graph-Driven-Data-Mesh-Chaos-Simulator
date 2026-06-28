import React, { useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  MarkerType,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { NodeState, EdgeState } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Activity, Database, Server, Component } from 'lucide-react';

interface CustomNodeData {
  label: string;
  type: string;
  state?: NodeState;
}

const getIcon = (type: string) => {
  switch (type) {
    case 'KAFKA_TOPIC':
      return <Activity className="w-4 h-4 text-blue-400" />;
    case 'SPARK_JOB':
      return <Server className="w-4 h-4 text-purple-400" />;
    case 'VECTOR_STORE':
    case 'POSTGRES_DB':
      return <Database className="w-4 h-4 text-green-400" />;
    default:
      return <Component className="w-4 h-4 text-slate-400" />;
  }
};

const CustomNode = ({ data }: { data: CustomNodeData }) => {
  const status = data.state?.status || 'Nominal';
  
  const statusColors = {
    Nominal: 'border-slate-600 bg-slate-900',
    Degraded: 'border-yellow-500 bg-yellow-950/30',
    Critical: 'border-red-500 bg-red-950/30',
    Isolated: 'border-slate-800 bg-slate-950 text-slate-500 opacity-60',
  };

  return (
    <div className={cn(
      "px-4 py-3 shadow-lg rounded-xl border-2 min-w-[150px] transition-all duration-300",
      statusColors[status]
    )}>
      <Handle type="target" position={Position.Top} className="!bg-slate-500" />
      <div className="flex items-center gap-2 mb-2">
        {getIcon(data.type)}
        <div className="font-semibold text-sm">{data.label}</div>
      </div>
      
      {data.state && status !== 'Isolated' && (
        <div className="text-[10px] space-y-1 text-slate-300 mt-2">
          <div className="flex justify-between">
            <span>Lat:</span>
            <span className={data.state.latency > 100 ? 'text-yellow-400' : ''}>
              {data.state.latency.toFixed(0)}ms
            </span>
          </div>
          <div className="flex justify-between">
            <span>Qual:</span>
            <span className={data.state.data_quality_score < 0.8 ? 'text-red-400' : ''}>
              {(data.state.data_quality_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span>Anom:</span>
            <span className={data.state.anomaly_score > 0.6 ? 'text-red-400' : ''}>
              {data.state.anomaly_score.toFixed(2)}
            </span>
          </div>
        </div>
      )}
      
      {status === 'Isolated' && (
        <div className="text-[10px] text-center mt-2 text-slate-500 font-semibold tracking-widest uppercase">
          Circuit Broken
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-slate-500" />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

interface TopologyCanvasProps {
  nodes: Node[];
  edges: Edge[];
}

export function TopologyCanvas({ nodes, edges }: TopologyCanvasProps) {
  return (
    <div className="w-full h-full bg-slate-950/50 rounded-xl border border-slate-800 overflow-hidden relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        className="bg-slate-950"
      >
        <Background color="#334155" gap={24} />
        <Controls className="bg-slate-900 border-slate-800 fill-slate-50" />
      </ReactFlow>
    </div>
  );
}
