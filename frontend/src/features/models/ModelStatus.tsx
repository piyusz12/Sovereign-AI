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
  const [vram, setVram] = useState({ used: 0, max: 8192, status: 'GREEN' });
  const [hardware, setHardware] = useState({ name: 'Unknown', ram_mb: 0 });
  const [queueDepth, setQueueDepth] = useState(0);

  useEffect(() => {
    // In a real app, this would be a WebSocket or SSE, 
    // but we use polling for this phase demo.
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/models/status');
        const data = await res.json();
        setModels(data.models);
        setVram({ used: data.vram_used_mb, max: data.max_vram_mb, status: data.vram_status || 'GREEN' });
        if (data.hardware_profile) {
            setHardware(data.hardware_profile);
        }
        setQueueDepth(data.queue_depth || 0);
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
            <span className={vram.status === 'RED' ? 'text-rose-400' : vram.status === 'YELLOW' ? 'text-amber-400' : 'text-emerald-400'}>
                {(vram.used / 1024).toFixed(1)} / {(vram.max / 1024).toFixed(1)} GB
            </span>
          </div>
          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden mb-4">
            <div 
              className={`h-full rounded-full ${vram.status === 'RED' ? 'bg-rose-500' : vram.status === 'YELLOW' ? 'bg-amber-500' : 'bg-emerald-500'}`}
              style={{ width: `${vramPercent}%`, transition: 'width 0.5s ease' }}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="bg-slate-950 p-2 rounded border border-slate-800">
                <div className="text-slate-500 mb-1 font-medium tracking-wider">HARDWARE</div>
                <div className="text-slate-300 font-mono text-[10px] uppercase truncate">{hardware.name}</div>
                <div className="text-slate-400 mt-0.5">{(hardware.ram_mb / 1024).toFixed(0)} GB RAM</div>
            </div>
            <div className="bg-slate-950 p-2 rounded border border-slate-800">
                <div className="text-slate-500 mb-1 font-medium tracking-wider">GPU QUEUE</div>
                <div className="flex items-center mt-1">
                    <span className={`text-lg font-semibold ${queueDepth > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>{queueDepth}</span>
                    <span className="text-slate-500 ml-2">jobs</span>
                </div>
            </div>
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
