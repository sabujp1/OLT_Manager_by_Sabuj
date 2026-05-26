'use client';

import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { 
  Server, 
  Cpu, 
  Wifi, 
  WifiOff, 
  Activity, 
  AlertOctagon, 
  Database,
  Radio, 
  Zap, 
  AlertTriangle 
} from 'lucide-react';
import axios from 'axios';
import { useSocket } from '@/context/SocketContext';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend 
} from 'recharts';

interface StatsState {
  olt: { total: number; online: number; offline: number };
  pon: { total: number };
  onu: { total: number; online: number; offline: number };
  alarms: { total_active: number; fiber_cuts: number; dying_gasps: number; los: number };
  telemetry_avg: { cpu: number; ram: number; temp: number };
  recent_alarms: any[];
  traffic_chart: any[];
}

export default function DashboardPage() {
  const { latestEvent } = useSocket();
  const [stats, setStats] = useState<StatsState | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch stats from REST API
  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get('/api/v1/dashboard/stats');
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching dashboard statistics:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    // Auto-refresh every 10 seconds to keep stats synchronized
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  // Reactive WebSocket Updates: Refresh dashboard metrics if alarms/inventories shift
  useEffect(() => {
    if (latestEvent) {
      if (['alarm_raised', 'alarm_cleared', 'onu_discovered'].includes(latestEvent.event)) {
        fetchStats();
      }
    }
  }, [latestEvent, fetchStats]);

  if (isLoading || !stats) {
    return (
      <DashboardLayout>
        <div className="flex h-[80vh] items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 border-4 border-indigo-600/30 border-t-indigo-500 rounded-full animate-spin" />
            <p className="text-sm text-noc-textMuted font-mono">Syncing NOC Operations Core...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        
        {/* Dashboard Title & Overview Banner */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-wide text-white">NOC Overview</h1>
            <p className="text-xs text-noc-textMuted mt-1">Real-time status of ISP network and multi-vendor OLTs.</p>
          </div>
          <div className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-mono rounded flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-ping" />
            <span>NOC Live Telemetry Stream Active</span>
          </div>
        </div>

        {/* 1. Header Widgets grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          
          {/* Card 1: OLTs */}
          <div className="glass-panel glass-panel-hover p-6 rounded-xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-noc-textMuted uppercase tracking-wider">OLT Status</p>
                <h3 className="text-3xl font-bold mt-2 text-white">{stats.olt.total}</h3>
              </div>
              <div className="p-3 bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 rounded-xl">
                <Server size={22} />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 status-glow-green" />
                {stats.olt.online} Online
              </span>
              <span className="flex items-center gap-1 text-rose-400">
                <span className="w-2 h-2 rounded-full bg-rose-400 status-glow-red" />
                {stats.olt.offline} Offline
              </span>
            </div>
          </div>

          {/* Card 2: ONUs */}
          <div className="glass-panel glass-panel-hover p-6 rounded-xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-noc-textMuted uppercase tracking-wider">ONUs / Clients</p>
                <h3 className="text-3xl font-bold mt-2 text-white">{stats.onu.total}</h3>
              </div>
              <div className="p-3 bg-cyan-600/10 text-cyan-400 border border-cyan-500/20 rounded-xl">
                <Database size={22} />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 status-glow-green" />
                {stats.onu.online} Online
              </span>
              <span className="flex items-center gap-1 text-noc-textMuted">
                <span className="w-2 h-2 rounded-full bg-gray-500" />
                {stats.onu.offline} Offline
              </span>
            </div>
          </div>

          {/* Card 3: Active Alarms */}
          <div className="glass-panel glass-panel-hover p-6 rounded-xl relative overflow-hidden border-l-2 border-l-rose-500/40">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-noc-textMuted uppercase tracking-wider">Active Alarms</p>
                <h3 className="text-3xl font-bold mt-2 text-rose-500">{stats.alarms.total_active}</h3>
              </div>
              <div className="p-3 bg-rose-600/10 text-rose-400 border border-rose-500/20 rounded-xl">
                <AlertOctagon size={22} className="text-rose-500" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3 text-xs text-noc-textMuted">
              <span className="text-rose-400">{stats.alarms.fiber_cuts} Cut</span>
              <span>•</span>
              <span className="text-amber-400">{stats.alarms.dying_gasps} Power</span>
              <span>•</span>
              <span className="text-rose-400">{stats.alarms.los} LOS</span>
            </div>
          </div>

          {/* Card 4: Hardware Telemetry */}
          <div className="glass-panel glass-panel-hover p-6 rounded-xl relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-noc-textMuted uppercase tracking-wider">OLT Telemetry</p>
                <h3 className="text-3xl font-bold mt-2 text-white">Normal</h3>
              </div>
              <div className="p-3 bg-emerald-600/10 text-emerald-400 border border-emerald-500/20 rounded-xl">
                <Cpu size={22} />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3 text-xs text-noc-textMuted">
              <span>CPU: <strong className="text-white">{stats.telemetry_avg.cpu}%</strong></span>
              <span>•</span>
              <span>RAM: <strong className="text-white">{stats.telemetry_avg.ram}%</strong></span>
              <span>•</span>
              <span>Temp: <strong className="text-white">{stats.telemetry_avg.temp}°C</strong></span>
            </div>
          </div>

        </div>

        {/* 2. Main Traffic Line Chart */}
        <div className="grid grid-cols-1 gap-6">
          <div className="glass-panel p-6 rounded-xl flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-white">NOC Live Throughput (Aggregate)</h2>
                <p className="text-xs text-noc-textMuted mt-0.5">Aggregate upload and download traffic over the past 6 hours (Gbps).</p>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-indigo-500 rounded" /> Inbound</span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-cyan-500 rounded" /> Outbound</span>
              </div>
            </div>
            
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.traffic_chart} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorInbound" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorOutbound" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#06B6D4" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#202E4E" />
                  <XAxis dataKey="time" stroke="#9CA3AF" fontSize={11} tickLine={false} />
                  <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} unit=" G" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#151D30', borderColor: '#202E4E', borderRadius: '8px' }}
                    labelStyle={{ color: '#F3F4F6', fontFamily: 'monospace' }}
                  />
                  <Area type="monotone" dataKey="inbound" stroke="#6366F1" fillOpacity={1} fill="url(#colorInbound)" strokeWidth={2} name="Download (Inbound)" />
                  <Area type="monotone" dataKey="outbound" stroke="#06B6D4" fillOpacity={1} fill="url(#colorOutbound)" strokeWidth={2} name="Upload (Outbound)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* 3. Recent Active Alarms list */}
        <div className="grid grid-cols-1 gap-6">
          <div className="glass-panel p-6 rounded-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-white">Active Alarm Console</h2>
                <p className="text-xs text-noc-textMuted mt-0.5">Currently active network warnings requiring operator attention.</p>
              </div>
              <span className="px-2 py-0.5 bg-rose-500/20 text-rose-400 font-mono text-xs rounded-full font-bold">
                {stats.recent_alarms.length} Active Alarms
              </span>
            </div>

            {stats.recent_alarms.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center border border-dashed border-noc-border rounded-xl">
                <Wifi className="text-emerald-500 animate-pulse mb-3" size={32} />
                <p className="text-sm font-semibold text-emerald-400">All Systems Nominal</p>
                <p className="text-xs text-noc-textMuted mt-1">No active alarms or fiber cuts registered on network.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-gray-300">
                  <thead className="bg-[#0C1221] text-noc-textMuted uppercase text-[10px] tracking-widest border-b border-noc-border">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Alarm ID</th>
                      <th className="px-6 py-3 font-semibold">OLT / Node</th>
                      <th className="px-6 py-3 font-semibold">Target ONU</th>
                      <th className="px-6 py-3 font-semibold">Alert Type</th>
                      <th className="px-6 py-3 font-semibold">Severity</th>
                      <th className="px-6 py-3 font-semibold">Details Message</th>
                      <th className="px-6 py-3 font-semibold text-right">Raised Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-noc-border">
                    {stats.recent_alarms.map((alarm) => (
                      <tr key={alarm.id} className="hover:bg-noc-cardLight/30 transition-all font-mono text-xs">
                        <td className="px-6 py-3 text-noc-textMuted">#{alarm.id.substring(0, 8)}</td>
                        <td className="px-6 py-3 text-white font-semibold">{alarm.olt_name || 'N/A'}</td>
                        <td className="px-6 py-3 text-indigo-400">{alarm.onu_serial || 'Node-Level'}</td>
                        <td className="px-6 py-3">
                          <span className="font-semibold text-gray-200">{alarm.alarm_type}</span>
                        </td>
                        <td className="px-6 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            alarm.severity === 'CRITICAL' 
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' 
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          }`}>
                            {alarm.severity}
                          </span>
                        </td>
                        <td className="px-6 py-3 max-w-xs truncate text-gray-300">{alarm.message}</td>
                        <td className="px-6 py-3 text-right text-noc-textMuted">
                          {new Date(alarm.raised_at).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}
