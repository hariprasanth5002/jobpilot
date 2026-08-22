import React from 'react';
import { 
  LayoutDashboard, 
  User, 
  FileText, 
  MessageSquare, 
  Settings, 
  Compass, 
  CheckCircle2 
} from 'lucide-react';

export default function Sidebar({ activeTab = 'dashboard', onSelectTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, implemented: true },
    { id: 'profile', label: 'My Profile', icon: User, implemented: false },
    { id: 'documents', label: 'Documents', icon: FileText, implemented: false },
    { id: 'history', label: 'Chat History', icon: MessageSquare, implemented: false },
    { id: 'settings', label: 'Settings', icon: Settings, implemented: false },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 text-base tracking-tight leading-none">JOBPILOT</h1>
              <p className="text-[11px] text-slate-500 font-medium mt-1">AI Career Assistant</p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Navigation</div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onSelectTab && onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {!item.implemented && (
                  <span className="text-[10px] text-slate-400 font-normal px-1.5 py-0.5 rounded bg-slate-100">
                    Soon
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-2 text-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <div>
            <p className="font-medium text-slate-800 text-[11px]">System Ready</p>
            <p className="text-[10px] text-slate-500 font-mono">Local AI: gemma3:1b</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
