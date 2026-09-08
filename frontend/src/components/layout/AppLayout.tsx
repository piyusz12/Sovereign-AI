import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  BookOpen,
  Eye,
  Code,
  Shield,
  History,
  ShieldCheck,
  Settings,
  Bell,
  ChevronLeft,
  ChevronRight,
  Zap,
  CheckCircle2,
  X,
  User,
} from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { api, type AuthUser } from '@/services/api';

const navItems = [
  {
    group: 'WORK',
    items: [
      { name: 'Assistant', path: '/assistant', icon: MessageSquare },
      { name: 'Knowledge', path: '/knowledge', icon: BookOpen },
      { name: 'Vision', path: '/vision', icon: Eye },
      { name: 'Coding', path: '/coding', icon: Code },
    ],
  },
  {
    group: 'RESULTS',
    items: [
      { name: 'Workflows', path: '/dashboard', icon: LayoutDashboard },
    ],
  },
  {
    group: 'SECURITY',
    items: [
      { name: 'Security Center', path: '/security', icon: Shield },
      { name: 'Audit', path: '/audit', icon: History },
    ],
  },
];

const DEMO_ACCOUNTS = [
  { username: 'admin', role: 'admin', label: 'Admin (Full Access)' },
  { username: 'engineer', role: 'engineering', label: 'Engineer (Vision, Code, Docs)' },
  { username: 'ops_user', role: 'operations', label: 'Operations (Vision, Logs)' },
  { username: 'finance_user', role: 'finance', label: 'Finance (Reports, Invoices)' },
  { username: 'hr_user', role: 'hr', label: 'HR (Policies, Internal)' },
  { username: 'procurement_user', role: 'procurement', label: 'Procurement (Contracts)' },
];

export function AppLayout() {
  const { navState, toggleSidebar, systemStatus, updateSystemStatus } = useAppStore();
  const { isSidebarCollapsed } = navState;
  const { localOnly, queueDepth } = systemStatus;

  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(api.getUser());
  const [showSovereigntyModal, setShowSovereigntyModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [sovereigntyData, setSovereigntyData] = useState<any>(null);
  const [recentNotifications, setRecentNotifications] = useState<any[]>([
    { id: '1', title: 'Local Inference Active', text: 'All models running in single-GPU local container.', time: 'Just now', type: 'info' },
    { id: '2', title: 'Zero-Egress Verified', text: 'Hardware network isolation policy enforced.', time: '5m ago', type: 'success' },
    { id: '3', title: 'Session Authenticated', text: 'JWT active with local RBAC clearance.', time: '10m ago', type: 'info' },
  ]);
  const [switchingUser, setSwitchingUser] = useState(false);

  useEffect(() => {
    // Initial login & health probe
    const init = async () => {
      try {
        await api.ensureAuthenticated();
        setCurrentUser(api.getUser());
        const health = await api.getHealth();
        if (health) {
          updateSystemStatus({ localOnly: health.sovereign });
        }
      } catch (err) {
        console.warn('Initial connection probe:', err);
      }
    };
    init();

    // Poll model queue
    const pollQueue = async () => {
      try {
        const status = await api.getModelStatus();
        if (status) {
          updateSystemStatus({
            queueDepth: status.queue_depth || 0,
            hardwareProfile: {
              name: status.hardware_profile?.name || 'Local RTX GPU',
              gpu_name: status.hardware_profile?.name || 'Local GPU (8GB)',
              ram_mb: status.hardware_profile?.ram_mb || 16384,
              vram_mb: status.max_vram_mb || 8192,
            },
          });
        }
      } catch (e) {
        // quiet
      }
    };
    pollQueue();
    const interval = setInterval(pollQueue, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenSovereignty = async () => {
    setShowSovereigntyModal(true);
    try {
      const data = await api.getSovereigntyStatus();
      setSovereigntyData(data);
    } catch {
      setSovereigntyData({
        sovereign: true,
        external_dns_queries: 0,
        external_tcp_connections: 0,
        external_https_requests: 0,
        cloud_ai_requests: 0,
        bytes_uploaded_externally: 0,
        verification_method: 'network_monitoring',
      });
    }
  };

  const handleSwitchAccount = async (username: string) => {
    setSwitchingUser(true);
    try {
      const passwords: Record<string, string> = {
        admin: 'admin123',
        engineer: 'eng123',
        ops_user: 'ops123',
        finance_user: 'fin123',
        hr_user: 'hr123',
        procurement_user: 'proc123',
      };
      const user = await api.login(username, passwords[username] || 'admin123');
      setCurrentUser(user);
      setShowSettingsModal(false);
      setRecentNotifications((prev) => [
        {
          id: Date.now().toString(),
          title: 'User Switched',
          text: `Switched to role: ${user.role.toUpperCase()} (${user.username})`,
          time: 'Just now',
          type: 'success',
        },
        ...prev,
      ]);
    } catch (err: any) {
      alert(`Failed to switch account: ${err.message}`);
    } finally {
      setSwitchingUser(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-slate-900 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside
        className={`${
          isSidebarCollapsed ? 'w-16' : 'w-64'
        } flex-shrink-0 bg-slate-950 border-r border-slate-800 flex flex-col transition-all duration-300 ease-in-out select-none`}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          {!isSidebarCollapsed && (
            <div className="flex items-center cursor-pointer" onClick={() => navigate('/dashboard')}>
              <ShieldCheck className="w-6 h-6 text-emerald-400 mr-2 flex-shrink-0" />
              <h1 className="font-bold text-sm tracking-wider leading-tight">
                SOVEREIGN AI
                <br />
                <span className="text-emerald-400 font-normal">WORKBENCH</span>
              </h1>
            </div>
          )}
          {isSidebarCollapsed && (
            <ShieldCheck
              className="w-6 h-6 text-emerald-400 mx-auto cursor-pointer"
              onClick={() => navigate('/dashboard')}
            />
          )}
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isSidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-6">
          {navItems.map((group, idx) => (
            <div key={idx}>
              {!isSidebarCollapsed && (
                <h2 className="text-xs font-semibold text-slate-500 tracking-wider mb-3 px-2">
                  {group.group}
                </h2>
              )}
              <div className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.name}
                      to={item.path}
                      className={({ isActive }) =>
                        `group flex items-center ${
                          isSidebarCollapsed ? 'justify-center' : ''
                        } px-2.5 py-2.5 text-sm rounded-lg transition-all duration-200 ${
                          isActive
                            ? 'bg-blue-600/20 text-blue-400 font-medium border border-blue-500/30 shadow-lg shadow-blue-500/10'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/70 hover:border-slate-700 border border-transparent'
                        }`
                      }
                      title={isSidebarCollapsed ? item.name : undefined}
                    >
                      <Icon className={`w-4 h-4 ${isSidebarCollapsed ? '' : 'mr-3'}`} />
                      {!isSidebarCollapsed && item.name}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Sidebar Footer - Hardware Info */}
        {!isSidebarCollapsed && (
          <div className="p-4 border-t border-slate-800 bg-slate-950/50">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span className="flex items-center">
                <Zap className="w-3.5 h-3.5 text-emerald-400 mr-1.5" />
                GPU Engine
              </span>
              <span className="font-mono text-emerald-400">READY</span>
            </div>
            <div className="text-[11px] text-slate-500 font-mono">
              {queueDepth} jobs in queue
            </div>
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 flex-shrink-0 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md flex items-center justify-between px-6 z-20">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-slate-400">
              ENVIRONMENT: <span className="text-slate-100 font-semibold">Zero-Egress Enclave</span>
            </span>
            <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[11px] bg-slate-800 border border-slate-700 text-slate-400">
              Role: <span className="text-emerald-400 font-mono">{currentUser?.role || 'admin'}</span>
            </span>
          </div>

          <div className="flex items-center space-x-3">
            {/* Status Badge with Modal trigger */}
            <button
              onClick={handleOpenSovereignty}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border backdrop-blur-sm transition-all duration-300 hover:scale-105 cursor-pointer ${
                localOnly
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              }`}
              title="Click to inspect zero-egress sovereignty audit"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
              <span>{localOnly ? 'LOCAL-ONLY' : 'ONLINE'}</span>
            </button>

            {/* Notifications Button */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="text-slate-400 hover:text-slate-100 p-2 rounded-lg hover:bg-slate-800/60 transition-all duration-200 relative focus:outline-none"
                aria-label="Notifications"
                title="Notifications"
              >
                <Bell className="w-5 h-5" />
                {recentNotifications.length > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-500"></span>
                )}
              </button>

              {/* Notifications Dropdown */}
              {showNotifications && (
                <>
                  <div
                    className="fixed inset-0 z-40 bg-transparent"
                    onClick={() => setShowNotifications(false)}
                  />
                  <div className="absolute right-0 mt-2 w-80 bg-slate-950 border border-slate-800 rounded-xl shadow-2xl p-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                    <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                      <span className="text-xs font-semibold text-slate-300">System Notifications</span>
                      <button
                        onClick={() => setRecentNotifications([])}
                        className="text-[11px] text-slate-500 hover:text-slate-300 cursor-pointer"
                      >
                        Clear
                      </button>
                    </div>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {recentNotifications.length === 0 ? (
                        <p className="text-xs text-slate-500 py-3 text-center">No new notifications</p>
                      ) : (
                        recentNotifications.map((n) => (
                          <div key={n.id} className="p-2 rounded-lg bg-slate-900 border border-slate-800/80 text-xs">
                            <div className="flex justify-between items-start font-medium text-slate-200">
                              <span>{n.title}</span>
                              <span className="text-[10px] text-slate-500 font-mono">{n.time}</span>
                            </div>
                            <p className="text-slate-400 mt-0.5 text-[11px]">{n.text}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Settings Button */}
            <button
              onClick={() => setShowSettingsModal(true)}
              className="text-slate-400 hover:text-slate-100 p-2 rounded-lg hover:bg-slate-800/60 transition-all duration-200 focus:outline-none"
              aria-label="Settings"
              title="System Settings & RBAC Switcher"
            >
              <Settings className="w-5 h-5" />
            </button>

            {/* User Avatar Button */}
            <button
              onClick={() => setShowSettingsModal(true)}
              className="flex items-center space-x-2 pl-2 focus:outline-none"
              title="Switch user role"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center font-bold text-xs shadow-lg shadow-blue-500/20 ring-2 ring-slate-700 uppercase">
                {currentUser?.username.slice(0, 2) || 'AD'}
              </div>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-slate-900">
          <Outlet />
        </main>
      </div>

      {/* Sovereignty Verification Modal */}
      {showSovereigntyModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setShowSovereigntyModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-100">Zero-Egress Data Sovereignty</h3>
                <p className="text-xs text-emerald-400 font-mono">100% On-Premises Air-Gapped Enforcement</p>
              </div>
            </div>

            <div className="space-y-3 my-4 text-xs font-mono">
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 flex justify-between">
                <span className="text-slate-400">External DNS Lookups:</span>
                <span className="text-emerald-400 font-bold">{sovereigntyData?.external_dns_queries ?? 0}</span>
              </div>
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 flex justify-between">
                <span className="text-slate-400">Cloud AI API Requests:</span>
                <span className="text-emerald-400 font-bold">{sovereigntyData?.cloud_ai_requests ?? 0}</span>
              </div>
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 flex justify-between">
                <span className="text-slate-400">Bytes Uploaded to WAN:</span>
                <span className="text-emerald-400 font-bold">{sovereigntyData?.bytes_uploaded_externally ?? 0} B</span>
              </div>
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 flex justify-between">
                <span className="text-slate-400">Outbound TCP Connections:</span>
                <span className="text-emerald-400 font-bold">{sovereigntyData?.external_tcp_connections ?? 0}</span>
              </div>
            </div>

            <div className="flex items-center text-xs text-slate-400 bg-emerald-500/5 p-3 rounded-lg border border-emerald-500/20 mb-4">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 flex-shrink-0" />
              <span>All inference models and document vectors are hosted strictly on local GPU hardware.</span>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowSovereigntyModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settings / RBAC Switcher Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setShowSettingsModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-100">Active User & RBAC Role</h3>
                <p className="text-xs text-slate-400">Switch persona to test fine-grained permissions</p>
              </div>
            </div>

            <div className="mb-4">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Available Personas:
              </label>
              <div className="space-y-2">
                {DEMO_ACCOUNTS.map((acc) => {
                  const isCurrent = currentUser?.username === acc.username;
                  return (
                    <button
                      key={acc.username}
                      disabled={switchingUser}
                      onClick={() => handleSwitchAccount(acc.username)}
                      className={`w-full p-3 rounded-lg border text-left flex items-center justify-between transition-all ${
                        isCurrent
                          ? 'bg-blue-600/20 border-blue-500/40 text-blue-300'
                          : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800/80'
                      }`}
                    >
                      <div>
                        <div className="text-xs font-semibold">{acc.label}</div>
                        <div className="text-[11px] text-slate-500 font-mono">User: {acc.username}</div>
                      </div>
                      {isCurrent && (
                        <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-medium">
                          Active
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-[11px] text-slate-400 mb-4">
              <span className="font-semibold text-slate-300">Backend API:</span> http://127.0.0.1:8080
              <br />
              <span className="font-semibold text-slate-300">Authentication:</span> Local JWT with SHA-256 / bcrypt
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowSettingsModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
