'use client';

import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { 
  Search, 
  RefreshCw, 
  RotateCw, 
  Power, 
  Tag, 
  CheckSquare, 
  Square,
  AlertOctagon,
  ArrowRight,
  Database
} from 'lucide-react';
import axios from 'axios';

interface ONU {
  id: string;
  olt_id: string;
  olt_name: string;
  pon_port_id: string;
  pon_port_number: string;
  onu_index: number;
  serial_number: string;
  mac_address: string | null;
  customer_id: string | null;
  username: string | null;
  vlan: number | null;
  ip_address: string | null;
  status: string;
  rx_power: number;
  tx_power: number;
  distance: number;
  uptime: string | null;
}

export default function OnusPage() {
  const [onus, setOnus] = useState<ONU[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedOnus, setSelectedOnus] = useState<string[]>([]);
  
  // VLAN change modal
  const [showVlanModal, setShowVlanModal] = useState<ONU | null>(null);
  const [vlanVal, setVlanVal] = useState('');

  const fetchOnus = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await axios.get('/api/v1/onus/', {
        params: { q: searchQuery || undefined }
      });
      setOnus(res.data);
    } catch (err) {
      console.error('Error fetching ONUs:', err);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    // Debounced search trigger
    const timeout = setTimeout(fetchOnus, 300);
    return () => clearTimeout(timeout);
  }, [fetchOnus]);

  const handleAction = async (onu: ONU, action: string, extraParams: any = {}) => {
    const confirmation = confirm(`Are you sure you want to execute ${action.toUpperCase()} on ONU: ${onu.serial_number}?`);
    if (!confirmation) return;

    try {
      await axios.post(`/api/v1/onus/${onu.id}/action`, {
        action,
        ...extraParams
      });
      alert(`Success: Initiated ${action} command.`);
      fetchOnus();
    } catch (err: any) {
      alert(`Operation Failed: ${err.response?.data?.detail || 'Unexpected response.'}`);
    }
  };

  const handleVlanChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showVlanModal || !vlanVal) return;

    try {
      await axios.post(`/api/v1/onus/${showVlanModal.id}/action`, {
        action: 'change_vlan',
        vlan: parseInt(vlanVal)
      });
      setShowVlanModal(null);
      setVlanVal('');
      fetchOnus();
    } catch (err: any) {
      alert(`VLAN change failed: ${err.response?.data?.detail}`);
    }
  };

  // Bulk actions handling
  const toggleSelect = (id: string) => {
    setSelectedOnus((prev) => 
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedOnus.length === onus.length) {
      setSelectedOnus([]);
    } else {
      setSelectedOnus(onus.map(o => o.id));
    }
  };

  const handleBulkAction = async (action: string) => {
    if (selectedOnus.length === 0) return;
    const confirmation = confirm(`Execute bulk ${action.toUpperCase()} across ${selectedOnus.length} selected ONUs?`);
    if (!confirmation) return;

    try {
      const res = await axios.post('/api/v1/onus/bulk-action', {
        onu_ids: selectedOnus,
        action
      });
      alert(`Bulk run executed.\nSucceeded: ${res.data.success_count}\nFailed: ${res.data.failed_count}`);
      setSelectedOnus([]);
      fetchOnus();
    } catch (err: any) {
      alert(`Bulk execution error: ${err.message}`);
    }
  };

  // Color signal strength decoder
  const getSignalBadge = (val: number) => {
    if (val === 0 || val <= -40) return <span className="text-gray-500 font-semibold">Offline</span>;
    if (val >= -27.0) return <span className="text-[#10B981] font-semibold">{val} dBm</span>;
    if (val >= -30.0) return <span className="text-[#F59E0B] font-semibold">{val} dBm</span>;
    return <span className="text-[#EF4444] font-semibold">{val} dBm</span>;
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-wide text-white">ONU Console</h1>
            <p className="text-xs text-noc-textMuted mt-1">Search GPON/EPON terminals, monitor optical levels, and run remote diagnostics.</p>
          </div>
        </div>

        {/* 1. Control & Filter panel */}
        <div className="glass-panel p-4 rounded-xl flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="relative w-full md:max-w-md">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-noc-textMuted">
              <Search size={16} />
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search ONUs by Serial, MAC, Customer ID, Username or VLAN..."
              className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 pl-10 pr-4 text-xs focus:outline-none focus:border-indigo-500 text-white"
            />
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
            <button
              onClick={fetchOnus}
              className="p-2 bg-[#0C1221] hover:bg-noc-cardLight text-noc-textMuted hover:text-white rounded border border-noc-border transition-all"
              title="Refresh Inventory"
            >
              <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            </button>

            {/* Bulk actions block */}
            {selectedOnus.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-xs">
                <span className="font-mono text-indigo-400 mr-2">{selectedOnus.length} Selected</span>
                <button
                  onClick={() => handleBulkAction('reboot')}
                  className="py-1 px-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded text-[10px] uppercase transition-all"
                >
                  Bulk Reboot
                </button>
                <button
                  onClick={() => handleBulkAction('disable')}
                  className="py-1 px-2.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 font-semibold rounded text-[10px] uppercase border border-rose-500/20 transition-all"
                >
                  Bulk Shut
                </button>
              </div>
            )}
          </div>
        </div>

        {/* 2. ONU Inventory Grid Table */}
        <div className="glass-panel rounded-xl overflow-hidden">
          {isLoading && onus.length === 0 ? (
            <div className="py-24 text-center font-mono text-xs text-noc-textMuted animate-pulse">
              Running dynamic inventory sync query...
            </div>
          ) : onus.length === 0 ? (
            <div className="py-16 text-center">
              <Database className="text-noc-textMuted mx-auto mb-3" size={32} />
              <p className="text-sm font-semibold text-gray-300">No active ONUs matching filters</p>
              <p className="text-xs text-noc-textMuted mt-1">If OLTs were recently added, wait for background worker polling to sync.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-gray-300">
                <thead className="bg-[#0C1221] text-noc-textMuted uppercase text-[10px] tracking-widest border-b border-noc-border">
                  <tr>
                    <th className="px-6 py-4 w-12 text-center">
                      <button onClick={toggleSelectAll} className="text-noc-textMuted hover:text-white">
                        {selectedOnus.length === onus.length ? <CheckSquare size={14} /> : <Square size={14} />}
                      </button>
                    </th>
                    <th className="px-6 py-4">Serial Number</th>
                    <th className="px-6 py-4">OLT IP / Name</th>
                    <th className="px-6 py-4">PON Port</th>
                    <th className="px-6 py-4">VLAN</th>
                    <th className="px-6 py-4">Customer ID</th>
                    <th className="px-6 py-4">RX Signal</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Distance</th>
                    <th className="px-6 py-4 text-right">Console Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-noc-border">
                  {onus.map((onu) => {
                    const isSel = selectedOnus.includes(onu.id);
                    return (
                      <tr key={onu.id} className={`hover:bg-noc-cardLight/20 transition-all font-mono text-xs ${isSel ? 'bg-indigo-600/5' : ''}`}>
                        <td className="px-6 py-4 text-center">
                          <button onClick={() => toggleSelect(onu.id)} className="text-noc-textMuted hover:text-white">
                            {isSel ? <CheckSquare size={14} className="text-indigo-500" /> : <Square size={14} />}
                          </button>
                        </td>
                        <td className="px-6 py-4 font-semibold text-white">{onu.serial_number}</td>
                        <td className="px-6 py-4 text-gray-400">{onu.olt_name}</td>
                        <td className="px-6 py-4 text-gray-400">{onu.pon_port_number}:{onu.onu_index}</td>
                        <td className="px-6 py-4 text-gray-300">{onu.vlan || 'Untagged'}</td>
                        <td className="px-6 py-4 text-indigo-400 font-semibold">{onu.customer_id || 'Not Provisioned'}</td>
                        <td className="px-6 py-4">{getSignalBadge(onu.rx_power)}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            onu.status === 'ONLINE' 
                              ? 'bg-emerald-500/10 text-emerald-400' 
                              : onu.status === 'LOS' 
                                ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                                : 'bg-gray-500/10 text-gray-400'
                          }`}>
                            {onu.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-400">{onu.distance}m</td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleAction(onu, 'reboot')}
                              className="p-1.5 bg-[#0C1221] hover:bg-noc-cardLight text-noc-textMuted hover:text-white rounded border border-noc-border transition-all"
                              title="Reboot ONU"
                            >
                              <RotateCw size={12} />
                            </button>
                            
                            {onu.status === 'ONLINE' ? (
                              <button
                                onClick={() => handleAction(onu, 'disable')}
                                className="p-1.5 bg-rose-500/5 hover:bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded transition-all"
                                title="Disable ONU port"
                              >
                                <Power size={12} />
                              </button>
                            ) : (
                              <button
                                onClick={() => handleAction(onu, 'enable')}
                                className="p-1.5 bg-emerald-500/5 hover:bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded transition-all"
                                title="Enable ONU port"
                              >
                                <Power size={12} />
                              </button>
                            )}

                            <button
                              onClick={() => { setShowVlanModal(onu); setVlanVal(onu.vlan ? onu.vlan.toString() : ''); }}
                              className="p-1.5 bg-[#0C1221] hover:bg-noc-cardLight text-indigo-400 hover:text-indigo-300 rounded border border-noc-border transition-all"
                              title="Change Bridging VLAN"
                            >
                              <Tag size={12} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 3. VLAN Modify Modal Dialog */}
        {showVlanModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-sm glass-panel rounded-2xl shadow-glass overflow-hidden">
              <div className="px-6 py-4 border-b border-noc-border bg-[#0C1221] flex justify-between items-center">
                <h3 className="text-sm font-bold text-white tracking-wide">Configure Native VLAN</h3>
                <button onClick={() => setShowVlanModal(null)} className="text-noc-textMuted hover:text-white font-mono text-xs">[CLOSE]</button>
              </div>

              <form onSubmit={handleVlanChange} className="p-6 space-y-4">
                <p className="text-xs text-noc-textMuted leading-relaxed">
                  Modifying Native VLAN for ONU: <strong className="text-white">{showVlanModal.serial_number}</strong>. This fires a CLI command directly to the OLT native interface.
                </p>

                <div>
                  <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">Bridging VLAN Tag (1-4094)</label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="4094"
                    value={vlanVal}
                    onChange={(e) => setVlanVal(e.target.value)}
                    placeholder="e.g. 100"
                    className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white font-mono"
                  />
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowVlanModal(null)}
                    className="py-1.5 px-3 bg-noc-card hover:bg-noc-cardLight text-gray-400 rounded text-xs transition-all border border-noc-border"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="py-1.5 px-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs transition-all"
                  >
                    Push Config
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      </div>
    </DashboardLayout>
  );
}
