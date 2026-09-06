import { useState, useEffect } from 'react';
import { Server, Activity, ShieldCheck, Database, Cpu } from 'lucide-react';

interface ModelInfo {
  id: string;
  name: string;
  role: string;
  status: string;
  vram_estimate_mb: number;
  loaded: boolean;
}

export function ModelStatus() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [vram, setVram] = useState({ used: 0, max: 8192 });

  useEffect(() => {
    // In a real app, this would be a WebSocket or SSE, 
    // but we use polling for this phase demo.
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/models/status');
        const data = await res.json();
        setModels(data.models);
        setVram({ used: data.vram_used_mb, max: data.max_vram_mb });
      } catch (err) {
        console.error("Failed to fetch model status", err);
      }
    };
    fetchStatus();
    const intv = setInterval(fetchStatus, 3000);
    return () => clearInterval(intv);
  }, []);

  const vramPercent = Math.min((vram.used / vram.max) * 100, 100);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden text-sm flex flex-col h-full">
      <div className="bg-slate-950 p-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Server className="w-4 h-4 text-emerald-400" />
          <h3 className="font-semibold text-slate-200">MODEL ROUTER</h3>
        </div>
        <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium tracking-wide">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
          <span>LOCAL</span>
        </div>
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-6">
        {/* VRAM Gauge */}
        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-2 font-medium">
            <span className="flex items-center"><Cpu className="w-3 h-3 mr-1" /> VRAM USAGE</span>
            <span>{(vram.used / 1024).toFixed(1)} / {(vram.max / 1024).toFixed(1)} GB</span>
          </div>
          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full ${vramPercent > 85 ? 'bg-rose-500' : 'bg-emerald-500'}`}
              style={{ width: `${vramPercent}%`, transition: 'width 0.5s ease' }}
            />
          </div>
        </div>

        {/* Loaded Models */}
        <div>
          <h4 className="text-xs font-semibold text-slate-500 tracking-wider mb-3">AVAILABLE MODELS</h4>
          <div className="space-y-2">
            {models.map(m => (
              <div key={m.id} className={`p-3 rounded-md border ${m.loaded ? 'bg-slate-800/50 border-emerald-500/30' : 'bg-slate-950/50 border-slate-800'} transition-colors`}>
                <div className="flex justify-between items-start mb-1">
                  <span className={`font-medium ${m.loaded ? 'text-emerald-400' : 'text-slate-300'}`}>{m.name}</span>
                  {m.loaded && <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />}
                </div>
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="capitalize">{m.role}</span>
                  <span className="flex items-center"><Database className="w-3 h-3 mr-1"/> {(m.vram_estimate_mb / 1024).toFixed(1)} GB</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
