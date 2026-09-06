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
  Bell
} from 'lucide-react';

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
  return (
    <div className="flex h-screen w-full bg-slate-900 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 bg-slate-950 border-r border-slate-800 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <ShieldCheck className="w-6 h-6 text-emerald-400 mr-2" />
          <h1 className="font-bold text-sm tracking-wider">SOVEREIGN AI<br/><span className="text-emerald-400 font-normal">WORKBENCH</span></h1>
        </div>
        
        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-8">
          {navItems.map((group, idx) => (
            <div key={idx}>
              <h2 className="text-xs font-semibold text-slate-500 tracking-wider mb-3 px-2">{group.group}</h2>
              <div className="space-y-1">
                {group.items.map(item => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.name}
                      to={item.path}
                      className={({ isActive }) => 
                        `flex items-center px-2 py-2 text-sm rounded-md transition-colors ${
                          isActive 
                            ? 'bg-slate-800 text-white font-medium' 
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                        }`
                      }
                    >
                      <Icon className="w-4 h-4 mr-3" />
                      {item.name}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 flex-shrink-0 border-b border-slate-800 bg-slate-900/50 backdrop-blur flex items-center justify-between px-6">
          <div className="flex items-center">
            <span className="text-sm font-medium text-slate-400">PROJECT: <span className="text-slate-100">Refinery Alpha</span></span>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-emerald-500/10 text-emerald-400 px-3 py-1.5 rounded-full text-xs font-medium border border-emerald-500/20">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span>LOCAL-ONLY</span>
            </div>
            <button className="text-slate-400 hover:text-slate-100 p-2">
              <Bell className="w-5 h-5" />
            </button>
            <button className="text-slate-400 hover:text-slate-100 p-2">
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center font-medium text-sm ml-2">
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
