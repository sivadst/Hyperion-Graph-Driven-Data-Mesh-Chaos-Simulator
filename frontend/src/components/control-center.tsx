import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Play, Square, Zap, AlertTriangle } from 'lucide-react';
import { NodeState } from '@/lib/types';

interface ControlCenterProps {
  runId: string | null;
  nodes: NodeState[];
  onStart: () => void;
  onStop: () => void;
  onInjectFault: (nodeId: string, type: string, severity: number) => void;
}

export function ControlCenter({ runId, nodes, onStart, onStop, onInjectFault }: ControlCenterProps) {
  const [selectedNode, setSelectedNode] = useState<string>('');

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-500" />
          Mission Control
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-6">
        <div className="flex gap-2">
          <Button 
            className="flex-1" 
            variant={runId ? "outline" : "default"}
            onClick={onStart}
            disabled={!!runId}
          >
            <Play className="w-4 h-4 mr-2" /> Start Run
          </Button>
          <Button 
            className="flex-1" 
            variant={runId ? "destructive" : "outline"}
            onClick={onStop}
            disabled={!runId}
          >
            <Square className="w-4 h-4 mr-2" /> Stop Run
          </Button>
        </div>

        <div className="space-y-4 pt-4 border-t border-slate-800">
          <h4 className="text-sm font-medium text-slate-300">Fault Injection Target</h4>
          <select 
            className="w-full bg-slate-900 border border-slate-800 rounded-md p-2 text-sm text-slate-200"
            value={selectedNode}
            onChange={(e) => setSelectedNode(e.target.value)}
            disabled={!runId}
          >
            <option value="">Select a node...</option>
            {nodes.map(n => (
              <option key={n.id} value={n.id}>{n.id}</option>
            ))}
          </select>

          <div className="grid grid-cols-2 gap-2">
            <Button 
              variant="secondary" 
              className="w-full text-xs"
              disabled={!runId || !selectedNode}
              onClick={() => onInjectFault(selectedNode, 'latency_spike', 500)}
            >
              +500ms Latency
            </Button>
            <Button 
              variant="secondary" 
              className="w-full text-xs"
              disabled={!runId || !selectedNode}
              onClick={() => onInjectFault(selectedNode, 'null_injection', 0.8)}
            >
              80% Null Values
            </Button>
          </div>
        </div>

        {runId && (
          <div className="mt-auto p-3 bg-blue-950/20 border border-blue-900/50 rounded-lg flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
            <div className="text-xs text-blue-200 space-y-1">
              <p className="font-semibold">AI Sentinel Active</p>
              <p className="opacity-80">IsolationForest pipeline is actively monitoring baseline telemetry.</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
