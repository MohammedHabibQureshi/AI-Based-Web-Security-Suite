import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, LayoutDashboard, Radio, Cpu, Settings, LogOut, User as UserIcon } from 'lucide-react';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'WAF Guard', path: '/waf', icon: Radio },
    { name: 'AI Scanner', path: '/scanner', icon: Cpu },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="flex min-h-screen bg-[#020617] text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-[#070b19] flex flex-col justify-between shrink-0">
        <div>
          {/* Logo */}
          <div className="p-6 flex items-center space-x-3 border-b border-slate-800">
            <Shield className="h-8 w-8 text-red-500 fill-red-500/10" />
            <span className="font-outfit text-base font-bold tracking-tight text-white leading-tight">
              Web Security <span className="text-red-500">Suite</span>
            </span>
          </div>

          {/* Nav */}
          <nav className="p-4 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                    isActive
                      ? 'bg-red-500/10 text-red-500 border-l-4 border-red-500 font-semibold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Profile / Logout Footer */}
        <div className="p-4 border-t border-slate-800 space-y-3">
          <div className="flex items-center space-x-3 px-2">
            <div className="h-9 w-9 rounded-full bg-slate-800 flex items-center justify-center text-red-500 border border-slate-700">
              <UserIcon className="h-4 w-4" />
            </div>
            <div className="truncate">
              <div className="text-sm font-semibold text-white truncate">{user?.name}</div>
              <div className="text-xs text-slate-500 truncate capitalize">{user?.role}</div>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-2.5 text-slate-400 hover:text-white hover:bg-red-500/10 hover:text-red-500 rounded-xl transition-all duration-200"
          >
            <LogOut className="h-4 w-4" />
            <span className="text-sm">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Pane */}
      <main className="flex-1 flex flex-col overflow-y-auto max-h-screen">
        <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between shrink-0 bg-[#020617]/50 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-white">
            {navItems.find((item) => item.path === location.pathname)?.name || 'Security Center'}
          </h2>
          <div className="text-xs text-slate-500">
            Workspace: <strong className="text-slate-300">ID {user?.tenant_id.substring(0, 8)}...</strong>
          </div>
        </header>
        <div className="p-8 max-w-7xl w-full mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};
