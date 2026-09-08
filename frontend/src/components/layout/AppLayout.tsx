import { Outlet, NavLink } from 'react-router-dom';
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
} from 'lucide-react';
import { useAppStore } from '@/store/appStore';

const navItems = [
  { group: 'WORK', items: [
    { name: 'Assistant', path: '/assistant', icon: MessageSquare },
    { name: 'Knowledge', path: '/knowledge', icon: BookOpen },
    { name: 'Vision', path: '/vision', icon: Eye },
    { name: 'Coding', path: '/coding', icon: Code },
  ]},
  { group: 'RESULTS', items: [
    { name: 'Workflows', path: '/dashboard', icon: LayoutDashboard },
  ]},
  { group: 'SECURITY', items: [
    { name: 'Security Center', path: '/security', icon: Shield },
    { name: 'Audit', path: '/audit', icon: History },
  ]},
];

export function AppLayout() {
  const { navState, toggleSidebar, systemStatus } = useAppStore();
  const { isSidebarCollapsed } = navState;
  const { localOnly, queueDepth } = systemStatus;

  return (
    <div className="flex h-screen w-full bg-slate-900 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside 
        className={`${isSidebarCollapsed ? 'w-16' : 'w-64'} flex-shrink-0 bg-slate-950 border-r border-slate-800 flex flex-col transition-all duration-300 ease-in-out`}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          {!isSidebarCollapsed && (
            <div className="flex items-center">
              <ShieldCheck className="w-6 h-6 text-emerald-400 mr-2" />
              <h1 className="font-bold text-sm tracking-wider">SOVEREIGN AI<br/><span className="text-emerald-400 font-normal">WORKBENCH</span></h1>
            </div>
          )}
          {isSidebarCollapsed && <ShieldCheck className="w-6 h-6 text-emerald-400 mx-auto" />}
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isSidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-6">
          {navItems.map((group, idx) => (
            <div key={idx}>
              {!isSidebarCollapsed && (
                <h2 className="text-xs font-semibold text-slate-500 tracking-wider mb-3 px-2">{group.group}</h2>
              )}
              <div className="space-y-1">
                {group.items.map(item => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.name}
                      to={item.path}
                      className={({ isActive }) =>
                        `group flex items-center ${isSidebarCollapsed ? 'justify-center' : ''} px-2 py-2.5 text-sm rounded-md transition-all duration-200 ${
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
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <Zap className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-mono">{queueDepth} jobs in queue</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 flex-shrink-0 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md flex items-center justify-between px-6">
          <div className="flex items-center">
            <span className="text-sm font-medium text-slate-400">PROJECT: <span className="text-slate-100">Refinery Alpha</span></span>
          </div>

          <div className="flex items-center space-x-4">
            {/* Status Badge with Glassmorphism */}
            <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border backdrop-blur-sm transition-all duration-300 ${
              localOnly 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/15 hover:border-emerald-500/30' 
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}>
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
              <span>{localOnly ? 'LOCAL-ONLY' : 'ONLINE'}</span>
            </div>
            
            <button 
              className="text-slate-400 hover:text-slate-100 p-2 rounded-md hover:bg-slate-800/50 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
            </button>
            <button 
              className="text-slate-400 hover:text-slate-100 p-2 rounded-md hover:bg-slate-800/50 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              aria-label="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center font-semibold text-sm ml-2 shadow-lg shadow-blue-500/20 ring-2 ring-slate-700">
              OP
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-slate-900">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
