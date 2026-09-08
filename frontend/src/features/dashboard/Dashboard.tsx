import { Activity, Server, Cpu, Database, TrendingUp, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { useAppStore } from '@/store/appStore';

interface WorkflowMetric {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'queued';
  duration: string;
  progress: number;
}

const mockWorkflows: WorkflowMetric[] = [
  { id: 'wf-001', name: 'Document Analysis Pipeline', status: 'running', duration: '2m 34s', progress: 67 },
  { id: 'wf-002', name: 'Image Recognition Batch', status: 'completed', duration: '8m 12s', progress: 100 },
  { id: 'wf-003', name: 'Security Audit Scan', status: 'queued', duration: '--', progress: 0 },
  { id: 'wf-004', name: 'Code Generation Task', status: 'failed', duration: '1m 05s', progress: 45 },
];

export default function Dashboard() {
  const { systemStatus } = useAppStore();
  const { hardwareProfile, queueDepth, activeWorkflows } = systemStatus;

  const getStatusColor = (status: WorkflowMetric['status']) => {
    switch (status) {
      case 'running': return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
      case 'completed': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'failed': return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      case 'queued': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    }
  };

  const getStatusIcon = (status: WorkflowMetric['status']) => {
    switch (status) {
      case 'running': return <Activity className="w-4 h-4 animate-pulse" />;
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'failed': return <AlertCircle className="w-4 h-4" />;
      case 'queued': return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6 overflow-y-auto">
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Active Workflows</h2>
          <p className="text-slate-400 mt-1 text-sm">Monitor intelligent agents and model routing.</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-md transition-colors shadow-lg shadow-blue-500/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50">
            New Workflow
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          icon={<Server className="w-5 h-5" />}
          label="Hardware Profile"
          value={hardwareProfile.gpu_name}
          subvalue={`${(hardwareProfile.ram_mb / 1024).toFixed(0)} GB RAM`}
          color="emerald"
        />
        <StatCard 
          icon={<Cpu className="w-5 h-5" />}
          label="VRAM Available"
          value={`${(hardwareProfile.vram_mb / 1024).toFixed(1)} GB`}
          subvalue={`${Math.round((hardwareProfile.vram_mb / 24576) * 100)}% free`}
          color="blue"
        />
        <StatCard 
          icon={<TrendingUp className="w-5 h-5" />}
          label="Queue Depth"
          value={queueDepth.toString()}
          subvalue={queueDepth > 0 ? 'Processing jobs' : 'Idle'}
          color={queueDepth > 0 ? 'amber' : 'emerald'}
        />
        <StatCard 
          icon={<Database className="w-5 h-5" />}
          label="Active Workflows"
          value={activeWorkflows.toString()}
          subvalue="Currently running"
          color="purple"
        />
      </div>

      {/* Main Content Grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
        {/* Execution Trace Panel */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
            <h3 className="font-semibold text-slate-200 flex items-center">
              <Activity className="w-4 h-4 mr-2 text-blue-400" />
              Execution Trace
            </h3>
            <span className="text-xs text-slate-500">Real-time updates</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {mockWorkflows.length > 0 ? (
              <div className="space-y-3">
                {mockWorkflows.map((workflow) => (
                  <div 
                    key={workflow.id}
                    className={`p-4 rounded-lg border ${getStatusColor(workflow.status)} transition-all duration-200 hover:shadow-lg`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(workflow.status)}
                        <span className="font-medium text-slate-200">{workflow.name}</span>
                      </div>
                      <span className="text-xs font-mono text-slate-400">{workflow.duration}</span>
                    </div>
                    {workflow.progress > 0 && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-slate-400 mb-1">
                          <span>Progress</span>
                          <span>{workflow.progress}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              workflow.status === 'running' ? 'bg-blue-500' :
                              workflow.status === 'completed' ? 'bg-emerald-500' :
                              workflow.status === 'failed' ? 'bg-rose-500' : 'bg-amber-500'
                            }`}
                            style={{ width: `${workflow.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-500">
                <Server className="w-12 h-12 mb-4 opacity-50" />
                <p className="text-sm">No active workflows</p>
                <p className="text-xs mt-1">Start a workflow to see execution traces</p>
              </div>
            )}
          </div>
        </div>

        {/* Model Status Panel */}
        <div className="lg:col-span-1 min-h-0">
          <ModelStatusPanel />
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subvalue: string;
  color: 'emerald' | 'blue' | 'amber' | 'purple';
}

function StatCard({ icon, label, value, subvalue, color }: StatCardProps) {
  const colorClasses = {
    emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    amber: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]} backdrop-blur-sm transition-all duration-200 hover:shadow-lg`}>
      <div className="flex items-center space-x-2 mb-2">
        <span className="opacity-80">{icon}</span>
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-xl font-bold text-slate-100">{value}</div>
      <div className="text-xs text-slate-500 mt-1">{subvalue}</div>
    </div>
  );
}

function ModelStatusPanel() {
  const { systemStatus } = useAppStore();
  const { hardwareProfile, queueDepth } = systemStatus;

  const vramPercent = 35; // Mock value

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
            <span className="text-emerald-400">
              {(vramPercent * hardwareProfile.vram_mb / 100 / 1024).toFixed(1)} / {(hardwareProfile.vram_mb / 1024).toFixed(1)} GB
            </span>
          </div>
          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden mb-4">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all duration-500"
              style={{ width: `${vramPercent}%` }}
            />
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="bg-slate-950 p-2 rounded border border-slate-800">
              <div className="text-slate-500 mb-1 font-medium tracking-wider">HARDWARE</div>
              <div className="text-slate-300 font-mono text-[10px] uppercase truncate">{hardwareProfile.name}</div>
              <div className="text-slate-400 mt-0.5">{(hardwareProfile.ram_mb / 1024).toFixed(0)} GB RAM</div>
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
            {[
              { name: 'Llama-3.2-3B', role: 'assistant', loaded: true, vram: 2.1 },
              { name: 'Qwen2.5-Coder-7B', role: 'coding', loaded: true, vram: 4.8 },
              { name: 'Phi-3.5-Vision', role: 'vision', loaded: false, vram: 3.2 },
            ].map((model) => (
              <div 
                key={model.name} 
                className={`p-3 rounded-md border transition-colors ${
                  model.loaded 
                    ? 'bg-slate-800/50 border-emerald-500/30' 
                    : 'bg-slate-950/50 border-slate-800'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className={`font-medium ${model.loaded ? 'text-emerald-400' : 'text-slate-300'}`}>
                    {model.name}
                  </span>
                  {model.loaded && <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />}
                </div>
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="capitalize">{model.role}</span>
                  <span className="flex items-center">
                    <Database className="w-3 h-3 mr-1" />
                    {model.vram.toFixed(1)} GB
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
