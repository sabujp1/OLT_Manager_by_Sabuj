'use client';

import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { AlertOctagon, CheckCircle2, RefreshCw, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';

interface Alarm {
  id: string;
  olt_id: string | null;
  olt_name: string | null;
  onu_id: string | null;
  onu_serial: string | null;
  alarm_type: string;
  severity: string;
  message: string;
  is_active: boolean;
  raised_at: string;
  cleared_at: string | null;
}

export default function AlarmsPage() {
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showActiveOnly, setShowActiveOnly] = useState(true);

  const fetchAlarms = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await axios.get('/api/v1/alarms/', {
        params: { active_only: showActiveOnly }
      });
      setAlarms(res.data);
    } catch (err) {
      console.error('Error fetching alarms:', err);
    } finally {
      setIsLoading(false);
    }
  }, [showActiveOnly]);

  useEffect(() => {
    fetchAlarms();
  }, [fetchAlarms]);

  const handleClearAlarm = async (id: string) => {
    try {
      await axios.post(`/api/v1/alarms/${id}/clear`);
      alert('Alarm successfully cleared and logged to history.');
      fetchAlarms();
    } catch (err: any) {
      alert(`Clear action failed: ${err.message}`);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-wide text-white">NOC Alarms Panel</h1>
            <p className="text-xs text-noc-textMuted mt-1">Audit active line cuts, power losses, and hardware alerts.</p>
          </div>

          <div className="flex items-center gap-3">
            
            {/* Filter Toggle */}
            <button
              onClick={() => setShowActiveOnly(prev => !prev)}
              className="flex items-center gap-2 py-2 px-4 bg-[#0C1221] hover:bg-noc-cardLight text-indigo-400 text-xs font-semibold rounded-lg border border-noc-border tracking-wide transition-all"
            >
              {showActiveOnly ? <EyeOff size={14} /> : <Eye size={14} />}
              <span>{showActiveOnly ? 'Show Alarm History' : 'Show Active Only'}</span>
            </button>

            <button
              onClick={fetchAlarms}
              className="p-2.5 bg-[#0C1221] hover:bg-noc-cardLight text-noc-textMuted hover:text-white rounded border border-noc-border transition-all"
              title="Refresh Alarms"
            >
              <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* 1. Main Alarm List */}
        <div className="glass-panel rounded-xl overflow-hidden">
          {isLoading && alarms.length === 0 ? (
            <div className="py-24 text-center font-mono text-xs text-noc-textMuted animate-pulse">
              Retrieving active SNMP traps log...
            </div>
          ) : alarms.length === 0 ? (
            <div className="py-16 text-center">
              <CheckCircle2 className="text-emerald-500 mx-auto mb-3" size={32} />
              <p className="text-sm font-semibold text-gray-300">All Systems Normal</p>
              <p className="text-xs text-noc-textMuted mt-1">No alarm logs found matching the active filters.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-gray-300">
                <thead className="bg-[#0C1221] text-noc-textMuted uppercase text-[10px] tracking-widest border-b border-noc-border">
                  <tr>
                    <th className="px-6 py-4">Alarm ID</th>
                    <th className="px-6 py-4">OLT Device</th>
                    <th className="px-6 py-4">Target ONU Serial</th>
                    <th className="px-6 py-4">Classification</th>
                    <th className="px-6 py-4">Severity</th>
                    <th className="px-6 py-4">Details Message</th>
                    <th className="px-6 py-4">Raised Time</th>
                    <th className="px-6 py-4">Status / Clear</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-noc-border">
                  {alarms.map((alarm) => (
                    <tr key={alarm.id} className="hover:bg-noc-cardLight/20 transition-all font-mono text-xs">
                      <td className="px-6 py-4 text-noc-textMuted">#{alarm.id.substring(0, 8)}</td>
                      <td className="px-6 py-4 text-white font-semibold">{alarm.olt_name || 'System-Level'}</td>
                      <td className="px-6 py-4 text-indigo-400 font-semibold">{alarm.onu_serial || 'Core Node'}</td>
                      <td className="px-6 py-4 text-gray-300">{alarm.alarm_type}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          alarm.severity === 'CRITICAL' 
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                            : alarm.severity === 'MAJOR'
                              ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}>
                          {alarm.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 max-w-xs truncate text-gray-300" title={alarm.message}>
                        {alarm.message}
                      </td>
                      <td className="px-6 py-4 text-noc-textMuted">
                        {new Date(alarm.raised_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        {alarm.is_active ? (
                          <button
                            onClick={() => handleClearAlarm(alarm.id)}
                            className="py-1 px-2.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 font-semibold rounded text-[10px] uppercase border border-rose-500/20 transition-all"
                          >
                            Clear
                          </button>
                        ) : (
                          <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                            <CheckCircle2 size={12} />
                            Cleared
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </DashboardLayout>
  );
}
