import React, { useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Terminal } from 'lucide-react';

interface LiveTerminalProps {
  logs: string[];
}

export function LiveTerminal({ logs }: LiveTerminalProps) {
  const endOfLogsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfLogsRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <Card className="h-full flex flex-col bg-black border-slate-800">
      <CardHeader className="pb-2 border-b border-slate-900 bg-slate-950 rounded-t-xl">
        <CardTitle className="flex items-center gap-2 text-sm text-slate-400">
          <Terminal className="w-4 h-4" />
          Event Stream
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-relaxed space-y-1">
        {logs.length === 0 ? (
          <div className="text-slate-700 italic">No events recorded yet.</div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="text-emerald-500/80 break-words">
              <span className="text-slate-600 mr-2">[{new Date().toISOString().split('T')[1].slice(0, -1)}]</span>
              {log}
            </div>
          ))
        )}
        <div ref={endOfLogsRef} />
      </CardContent>
    </Card>
  );
}
