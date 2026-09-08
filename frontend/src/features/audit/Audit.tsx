import { History, FileText, Search, Filter, Download, Clock, User, Activity, Shield, Lock } from 'lucide-react';

interface AuditLog {
  id: string;
  action: string;
  user: string;
  resource: string;
  timestamp: string;
  status: 'success' | 'warning' | 'error';
  details?: string;
}

const mockAuditLogs: AuditLog[] = [
  { id: '1', action: 'MODEL_DEPLOYMENT', user: 'admin', resource: 'Llama-3.2-3B', timestamp: '2024-01-15 14:32:05', status: 'success', details: 'Model successfully deployed to GPU cluster' },
  { id: '2', action: 'SECURITY_POLICY_UPDATE', user: 'security_admin', resource: 'Firewall Rules', timestamp: '2024-01-15 13:15:22', status: 'success', details: 'Updated ingress rules for API gateway' },
  { id: '3', action: 'API_KEY_GENERATION', user: 'developer_1', resource: 'Production API', timestamp: '2024-01-15 12:45:18', status: 'warning', details: 'New API key generated with elevated permissions' },
  { id: '4', action: 'CONFIG_CHANGE', user: 'system', resource: 'Rate Limiter', timestamp: '2024-01-15 11:20:33', status: 'error', details: 'Failed to apply configuration: validation error' },
  { id: '5', action: 'USER_ACCESS_GRANTED', user: 'admin', resource: 'Dashboard', timestamp: '2024-01-15 10:05:47', status: 'success', details: 'Read access granted to user_42' },
];

export default function Audit() {
  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 p-6 border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center">
              <History className="w-6 h-6 mr-2 text-blue-400" />
              Audit Center
            </h2>
            <p className="text-slate-400 mt-1 text-sm">Comprehensive audit logs and compliance tracking</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-md transition-colors border border-slate-700">
              <Filter className="w-4 h-4 mr-2" />
              Filter
            </button>
            <button className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-md transition-colors border border-slate-700">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          </div>
        </div>

        {/* Search & Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="text"
              placeholder="Search audit logs..."
              className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200"
            />
          </div>
          <StatCard label="Total Events" value="1,247" trend="+12%" />
          <StatCard label="Success Rate" value="98.5%" trend="+0.3%" color="emerald" />
          <StatCard label="Warnings" value="18" trend="-5" color="amber" />
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Audit Logs Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
            <h3 className="font-semibold text-slate-200 flex items-center">
              <FileText className="w-4 h-4 mr-2 text-blue-400" />
              Recent Audit Events
            </h3>
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <Clock className="w-3.5 h-3.5" />
              <span>Last 24 hours</span>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/30">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">User</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Resource</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Timestamp</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {mockAuditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-4 py-3">
                      <div>
                        <span className="font-medium text-slate-200 text-sm">{log.action}</span>
                        {log.details && (
                          <p className="text-xs text-slate-500 mt-0.5 truncate max-w-xs">{log.details}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
                          <User className="w-3.5 h-3.5 text-blue-400" />
                        </div>
                        <span className="text-sm text-slate-300 font-mono">{log.user}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-300">{log.resource}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-400 font-mono">{log.timestamp}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                        log.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                        log.status === 'warning' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                        'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}>
                        {log.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button className="text-slate-400 hover:text-slate-200 p-1 rounded-md hover:bg-slate-700 transition-colors">
                        <Activity className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800 bg-slate-950/30">
            <span className="text-xs text-slate-500">Showing 1-5 of 1,247 events</span>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-1 text-xs text-slate-400 bg-slate-800 border border-slate-700 rounded-md hover:bg-slate-700 transition-colors disabled:opacity-50" disabled>
                Previous
              </button>
              <button className="px-3 py-1 text-xs text-slate-200 bg-blue-600 border border-blue-500 rounded-md hover:bg-blue-500 transition-colors">
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Compliance Summary */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <ComplianceCard title="Data Protection" status="Compliant" score={100} icon={<Shield className="w-5 h-5" />} />
          <ComplianceCard title="Access Control" status="Review Needed" score={85} icon={<Lock className="w-5 h-5" />} warning />
          <ComplianceCard title="Audit Logging" status="Compliant" score={98} icon={<History className="w-5 h-5" />} />
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  trend?: string;
  color?: 'default' | 'emerald' | 'amber';
}

function StatCard({ label, value, trend, color = 'default' }: StatCardProps) {
  const colorClasses = {
    default: 'bg-slate-800/50 border-slate-700',
    emerald: 'bg-emerald-500/10 border-emerald-500/20',
    amber: 'bg-amber-500/10 border-amber-500/20',
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]} backdrop-blur-sm transition-all duration-200 hover:shadow-lg`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
        {trend && (
          <span className={`text-xs font-medium ${
            trend.startsWith('+') && !trend.includes('-') ? 'text-emerald-400' : 'text-slate-500'
          }`}>{trend}</span>
        )}
      </div>
      <div className="text-xl font-bold text-slate-100">{value}</div>
    </div>
  );
}

// Need to import Shield and Lock for ComplianceCard

interface ComplianceCardProps {
  title: string;
  status: string;
  score: number;
  icon: React.ReactNode;
  warning?: boolean;
}

function ComplianceCard({ title, status, score, icon, warning }: ComplianceCardProps) {
  return (
    <div className={`p-4 rounded-lg border transition-all duration-200 hover:shadow-lg ${
      warning 
        ? 'bg-amber-500/5 border-amber-500/20' 
        : 'bg-slate-800/50 border-slate-700'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className={warning ? 'text-amber-400' : 'text-blue-400'}>{icon}</span>
          <span className="font-medium text-slate-200 text-sm">{title}</span>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${
          warning ? 'bg-amber-500/10 text-amber-400' : 'bg-emerald-500/10 text-emerald-400'
        }`}>
          {status}
        </span>
      </div>
      <div className="flex items-center space-x-2">
        <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all duration-500 ${
              warning ? 'bg-amber-500' : 'bg-emerald-500'
            }`}
            style={{ width: `${score}%` }}
          />
        </div>
        <span className={`text-sm font-semibold ${warning ? 'text-amber-400' : 'text-emerald-400'}`}>
          {score}%
        </span>
      </div>
    </div>
  );
}
