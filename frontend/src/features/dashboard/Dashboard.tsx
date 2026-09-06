import { ModelStatus } from '@/features/models/ModelStatus';

export default function Dashboard() {
  return (
    <div className="p-6 h-full flex flex-col space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Active Workflows</h2>
          <p className="text-slate-400 mt-1 text-sm">Monitor intelligent agents and model routing.</p>
        </div>
      </div>
      
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg overflow-hidden flex flex-col">
           <div className="p-4 border-b border-slate-800 bg-slate-950/50">
             <h3 className="font-semibold text-slate-200">Execution Trace</h3>
           </div>
           <div className="p-6 flex-1 flex items-center justify-center text-slate-500">
             Run a workflow to see the execution trace here.
           </div>
        </div>
        
        <div className="lg:col-span-1 min-h-0">
          <ModelStatus />
        </div>
      </div>
    </div>
  );
}
