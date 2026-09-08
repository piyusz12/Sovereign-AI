import { Shield, AlertTriangle, CheckCircle, Lock, Eye, Activity, Server, Users } from 'lucide-react';

interface SecurityAlert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  timestamp: string;
  status: 'active' | 'resolved';
}

const mockAlerts: SecurityAlert[] = [
  { id: '1', severity: 'critical', title: 'Unauthorized Access Attempt', description: 'Multiple failed login attempts detected from IP 192.168.1.105', timestamp: '5m ago', status: 'active' },
  { id: '2', severity: 'high', title: 'API Rate Limit Exceeded', description: 'Endpoint /api/v1/models exceeded rate limit threshold', timestamp: '15m ago', status: 'active' },
  { id: '3', severity: 'medium', title: 'Certificate Expiry Warning', description: 'SSL certificate expires in 7 days', timestamp: '1h ago', status: 'active' },
  { id: '4', severity: 'low', title: 'Configuration Change', description: 'Security policy updated by admin', timestamp: '2h ago', status: 'resolved' },
];

export default function Security() {
  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 p-6 border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center">
              <Shield className="w-6 h-6 mr-2 text-emerald-400" />
              Security Center
            </h2>
            <p className="text-slate-400 mt-1 text-sm">Monitor and manage system security posture</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-md transition-colors border border-slate-700">
              <Eye className="w-4 h-4 mr-2" />
              Audit Logs
            </button>
            <button className="flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-md transition-colors shadow-lg shadow-emerald-500/20">
              <CheckCircle className="w-4 h-4 mr-2" />
              Run Security Scan
            </button>
          </div>
        </div>

        {/* Security Score */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SecurityScoreCard score={87} label="Overall Security Score" trend="+3%" />
          <StatCard icon={<Lock className="w-4 h-4" />} label="Active Policies" value="12" color="blue" />
          <StatCard icon={<AlertTriangle className="w-4 h-4" />} label="Active Alerts" value="3" color="amber" />
          <StatCard icon={<Server className="w-4 h-4" />} label="Protected Endpoints" value="24" color="emerald" />
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Security Alerts */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
              <h3 className="font-semibold text-slate-200 flex items-center">
                <AlertTriangle className="w-4 h-4 mr-2 text-amber-400" />
                Security Alerts
              </h3>
              <span className="text-xs text-slate-500">{mockAlerts.filter(a => a.status === 'active').length} active</span>
            </div>
            <div className="divide-y divide-slate-800">
              {mockAlerts.map((alert) => (
                <div key={alert.id} className="p-4 hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        alert.severity === 'critical' ? 'bg-rose-500 animate-pulse' :
                        alert.severity === 'high' ? 'bg-orange-500' :
                        alert.severity === 'medium' ? 'bg-amber-500' : 'bg-blue-500'
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={`text-xs px-2 py-0.5 rounded-full uppercase font-medium ${
                            alert.severity === 'critical' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                            alert.severity === 'high' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                            alert.severity === 'medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                            'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          }`}>
                            {alert.severity}
                          </span>
                          <h4 className="font-medium text-slate-200">{alert.title}</h4>
                        </div>
                        <p className="text-sm text-slate-400 mb-2">{alert.description}</p>
                        <div className="flex items-center space-x-4 text-xs text-slate-500">
                          <span>{alert.timestamp}</span>
                          <span className={`px-2 py-0.5 rounded-full ${
                            alert.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-400'
                          }`}>
                            {alert.status.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button className="text-slate-400 hover:text-slate-200 p-2 rounded-md hover:bg-slate-700 transition-colors">
                      <Activity className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions & Status */}
          <div className="space-y-4">
            {/* Access Control */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <h3 className="font-semibold text-slate-200 mb-4 flex items-center">
                <Users className="w-4 h-4 mr-2 text-purple-400" />
                Access Control
              </h3>
              <div className="space-y-3">
                <AccessControlItem label="Admin Access" users={3} status="secure" />
                <AccessControlItem label="API Keys" users={8} status="review" />
                <AccessControlItem label="Service Accounts" users={5} status="secure" />
              </div>
            </div>

            {/* System Status */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <h3 className="font-semibold text-slate-200 mb-4 flex items-center">
                <Activity className="w-4 h-4 mr-2 text-blue-400" />
                System Health
              </h3>
              <div className="space-y-3">
                <HealthItem label="Firewall" status="active" />
                <HealthItem label="Intrusion Detection" status="active" />
                <HealthItem label="Encryption" status="enabled" />
                <HealthItem label="Backup System" status="healthy" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface SecurityScoreCardProps {
  score: number;
  label: string;
  trend: string;
}

function SecurityScoreCard({ score, label, trend }: SecurityScoreCardProps) {
  const isGood = score >= 80;
  return (
    <div className="p-4 rounded-lg border bg-gradient-to-br from-emerald-500/10 to-blue-500/10 border-emerald-500/20 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
        <span className={`text-xs font-medium ${isGood ? 'text-emerald-400' : 'text-amber-400'}`}>{trend}</span>
      </div>
      <div className="flex items-end space-x-2">
        <span className={`text-3xl font-bold ${isGood ? 'text-emerald-400' : 'text-amber-400'}`}>{score}</span>
        <span className="text-slate-500 mb-1">/100</span>
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: 'blue' | 'emerald' | 'amber';
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    amber: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]} backdrop-blur-sm transition-all duration-200 hover:shadow-lg`}>
      <div className="flex items-center space-x-2 mb-2">
        <span className="opacity-80">{icon}</span>
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-xl font-bold text-slate-100">{value}</div>
    </div>
  );
}

interface AccessControlItemProps {
  label: string;
  users: number;
  status: 'secure' | 'review';
}

function AccessControlItem({ label, users, status }: AccessControlItemProps) {
  return (
    <div className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800">
      <div>
        <p className="font-medium text-slate-200 text-sm">{label}</p>
        <p className="text-xs text-slate-500 mt-0.5">{users} {users === 1 ? 'user' : 'users'}</p>
      </div>
      <span className={`text-xs px-2 py-1 rounded-full ${
        status === 'secure' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
      }`}>
        {status.toUpperCase()}
      </span>
    </div>
  );
}

interface HealthItemProps {
  label: string;
  status: string;
}

function HealthItem({ label, status }: HealthItemProps) {
  return (
    <div className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800">
      <span className="text-sm text-slate-300">{label}</span>
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-xs text-emerald-400 capitalize">{status}</span>
      </div>
    </div>
  );
}
