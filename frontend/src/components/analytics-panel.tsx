import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity } from 'lucide-react';

interface AnalyticsPanelProps {
  centrality: {
    betweenness: Record<string, number>;
    pagerank: Record<string, number>;
  };
}

export function AnalyticsPanel({ centrality }: AnalyticsPanelProps) {
  
  const data = Object.entries(centrality.betweenness || {}).map(([nodeId, score]) => ({
    name: nodeId.split('-')[0], // simplified name
    betweenness: Number(score.toFixed(3)),
    pagerank: Number((centrality.pagerank?.[nodeId] || 0).toFixed(3))
  }));

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Activity className="w-4 h-4 text-emerald-400" />
          Structural Vulnerability (SPOFs)
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 min-h-[200px]">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#020617', borderColor: '#1e293b', fontSize: '12px' }}
                itemStyle={{ color: '#f8fafc' }}
              />
              <Bar dataKey="betweenness" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Betweenness Centrality" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            Awaiting structural analysis...
          </div>
        )}
      </CardContent>
    </Card>
  );
}
