import { Eye, Image, ScanLine, Zap, Download, Settings, Play } from 'lucide-react';

interface VisionTask {
  id: string;
  name: string;
  status: 'idle' | 'processing' | 'completed' | 'error';
  thumbnail?: string;
  result?: string;
}

const mockTasks: VisionTask[] = [
  { id: '1', name: 'Object Detection - Batch A', status: 'completed', result: '23 objects detected' },
  { id: '2', name: 'OCR - Document Scan', status: 'processing' },
  { id: '3', name: 'Face Recognition', status: 'idle' },
  { id: '4', name: 'Scene Analysis', status: 'error' },
];

export default function Vision() {
  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 p-6 border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center">
              <Eye className="w-6 h-6 mr-2 text-purple-400" />
              Vision Workspace
            </h2>
            <p className="text-slate-400 mt-1 text-sm">Computer vision and image analysis tools</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-md transition-colors border border-slate-700">
              <Settings className="w-4 h-4 mr-2" />
              Configure
            </button>
            <button className="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-md transition-colors shadow-lg shadow-purple-500/20">
              <Play className="w-4 h-4 mr-2" />
              Run Analysis
            </button>
          </div>
        </div>

        {/* Upload Area */}
        <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-purple-500/50 hover:bg-purple-500/5 transition-all duration-200 cursor-pointer group">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-500/10 border border-purple-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
              <Image className="w-8 h-8 text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-200 mb-2">Drop images or videos here</h3>
            <p className="text-slate-400 text-sm mb-4">Support for PNG, JPG, WEBP, MP4, AVI</p>
            <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-md transition-colors border border-slate-700">
              Browse Files
            </button>
          </div>
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Tasks */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
              <h3 className="font-semibold text-slate-200 flex items-center">
                <ScanLine className="w-4 h-4 mr-2 text-purple-400" />
                Active Tasks
              </h3>
              <span className="text-xs text-slate-500">{mockTasks.length} tasks</span>
            </div>
            <div className="divide-y divide-slate-800">
              {mockTasks.map((task) => (
                <div key={task.id} className="p-4 hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${
                        task.status === 'processing' ? 'bg-blue-400 animate-pulse' :
                        task.status === 'completed' ? 'bg-emerald-400' :
                        task.status === 'error' ? 'bg-rose-400' : 'bg-slate-500'
                      }`} />
                      <span className="font-medium text-slate-200">{task.name}</span>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      task.status === 'processing' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                      task.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      task.status === 'error' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                      'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                    }`}>
                      {task.status.toUpperCase()}
                    </span>
                  </div>
                  {task.result && (
                    <p className="text-sm text-slate-400 ml-5">{task.result}</p>
                  )}
                  {task.status === 'processing' && (
                    <div className="ml-5 mt-2">
                      <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '60%' }} />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <h3 className="font-semibold text-slate-200 mb-4 flex items-center">
                <Zap className="w-4 h-4 mr-2 text-amber-400" />
                Quick Actions
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <QuickActionCard icon={<Image className="w-5 h-5" />} label="Object Detection" color="blue" />
                <QuickActionCard icon={<ScanLine className="w-5 h-5" />} label="OCR Text Extract" color="emerald" />
                <QuickActionCard icon={<Eye className="w-5 h-5" />} label="Face Recognition" color="purple" />
                <QuickActionCard icon={<Download className="w-5 h-5" />} label="Export Results" color="amber" />
              </div>
            </div>

            {/* Model Info */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <h3 className="font-semibold text-slate-200 mb-3">Active Model</h3>
              <div className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800">
                <div>
                  <p className="font-medium text-slate-200">Phi-3.5-Vision</p>
                  <p className="text-xs text-slate-500 mt-0.5">Multimodal AI Model</p>
                </div>
                <div className="flex items-center space-x-2 px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span>Ready</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface QuickActionCardProps {
  icon: React.ReactNode;
  label: string;
  color: 'blue' | 'emerald' | 'purple' | 'amber';
}

function QuickActionCard({ icon, label, color }: QuickActionCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400 hover:bg-blue-500/20',
    emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400 hover:bg-purple-500/20',
    amber: 'bg-amber-500/10 border-amber-500/20 text-amber-400 hover:bg-amber-500/20',
  };

  return (
    <button className={`p-3 rounded-lg border ${colorClasses[color]} transition-all duration-200 hover:shadow-lg hover:scale-[1.02]`}>
      <div className="flex flex-col items-center text-center">
        <div className="mb-2">{icon}</div>
        <span className="text-xs font-medium">{label}</span>
      </div>
    </button>
  );
}
