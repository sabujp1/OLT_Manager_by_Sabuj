'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/navigation';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useSocket } from '@/context/SocketContext';
import { 
  LayoutDashboard, 
  Layers, 
  Search, 
  Map, 
  AlertTriangle, 
  Activity, 
  LogOut, 
  Clock, 
  ShieldCheck, 
  Wifi, 
  WifiOff 
} from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const { isConnected, activeAlarms } = useSocket();
  const pathname = usePathname();
  const router = useRouter();
  
  // NOC ticking clock state
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTimeStr(d.toLocaleTimeString());
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { label: 'NOC Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { label: 'OLT Inventory', icon: Layers, path: '/olts' },
    { label: 'ONU Manager', icon: Search, path: '/onus' },
    { label: 'Topology GIS', icon: Map, path: '/topology' },
    { label: 'Live Alarms', icon: AlertTriangle, path: '/alarms', badge: activeAlarms.length },
  ];

  return (
    <div className="flex h-screen w-screen bg-[#0B0F19] overflow-hidden text-gray-200">
      
      {/* 1. Left Sidebar */}
      <aside className="w-64 border-r border-noc-border bg-[#0B1220] flex flex-col z-20">
        
        {/* Logo/Branding */}
        <div className="h-16 flex items-center px-6 gap-3 border-b border-noc-border">
          <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-lg status-glow-green">
            <Activity size={20} />
          </div>
          <div>
            <h1 className="font-semibold text-lg tracking-wide text-white">OLT NOC</h1>
            <p className="text-xs text-noc-textMuted tracking-widest font-mono uppercase">Manager v1.0</p>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg text-sm transition-all duration-150 ${
                  isActive 
                    ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20' 
                    : 'text-noc-textMuted hover:text-white hover:bg-noc-cardLight/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={18} />
                  <span>{item.label}</span>
                </div>
                {item.badge && item.badge > 0 ? (
                  <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                    isActive ? 'bg-indigo-600/30 text-indigo-300' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {item.badge}
                  </span>
                ) : null}
              </button>
            );
          })}
        </nav>

        {/* User profile section at the bottom */}
        <div className="p-4 border-t border-noc-border bg-[#090D18]">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-indigo-600/20 flex items-center justify-center border border-indigo-500/30 text-indigo-400 font-bold">
              {user?.full_name?.charAt(0) || 'A'}
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-semibold truncate text-white">{user?.full_name || 'NOC Operator'}</h2>
              <div className="flex items-center gap-1 text-[10px] text-indigo-400 font-mono">
                <ShieldCheck size={10} />
                <span>{user?.role || 'READ_ONLY'}</span>
              </div>
            </div>
          </div>
          
          <button 
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-all border border-rose-500/15"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* 2. Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* NOC Header */}
        <header className="h-16 border-b border-noc-border bg-[#0B1220]/70 backdrop-blur-md flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-6">
            
            {/* Live ticking clock */}
            <div className="flex items-center gap-2 text-noc-textMuted font-mono text-sm border-r border-noc-border pr-6">
              <Clock size={16} className="text-indigo-400" />
              <span>{timeStr}</span>
            </div>

            {/* WebSocket connection status dot */}
            <div className="flex items-center gap-2">
              {isConnected ? (
                <>
                  <Wifi size={16} className="text-[#10B981]" />
                  <span className="text-xs text-noc-textMuted font-mono">WS Stream Online</span>
                  <div className="w-2 h-2 rounded-full bg-[#10B981] status-glow-green" />
                </>
              ) : (
                <>
                  <WifiOff size={16} className="text-rose-500" />
                  <span className="text-xs text-rose-400 font-mono">WS Connecting</span>
                  <div className="w-2 h-2 rounded-full bg-rose-500 status-glow-red" />
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-2 py-1 text-[11px] font-mono rounded bg-noc-card border border-noc-border text-noc-textMuted">
              POP: <span className="text-white">All Sites</span>
            </span>
          </div>
        </header>

        {/* Content scrolling grid */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          
          {/* Top Live Alarm banner ticker (shows when critical alarm occurs) */}
          {activeAlarms.length > 0 && (
            <div className="mb-6 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center justify-between animate-pulse">
              <div className="flex items-center gap-3">
                <AlertTriangle size={18} className="text-rose-500" />
                <span className="text-sm font-medium text-rose-300">
                  <strong className="text-white">CRITICAL ALARM ACTIVE:</strong> {activeAlarms[0].message}
                </span>
              </div>
              <button 
                onClick={() => router.push('/alarms')} 
                className="text-xs text-rose-400 hover:text-white font-mono underline"
              >
                Inspect Alerts
              </button>
            </div>
          )}

          {children}
        </main>
      </div>
    </div>
  );
}
