'use client';

import React, { useState, useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { Server, Plus, Edit2, Trash2, ShieldCheck, Play, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

interface OLT {
  id: string;
  name: string;
  ip_address: string;
  vendor: string;
  model: string | null;
  connection_method: string;
  status: string;
  cpu_usage: number;
  ram_usage: number;
  temperature: number;
  uptime: string | null;
  location: string | null;
  pop_name: string | null;
}

export default function OltsPage() {
  const [olts, setOlts] = useState<OLT[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editOlt, setEditOlt] = useState<OLT | null>(null);

  // Form fields
  const [name, setName] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [vendor, setVendor] = useState('GENERIC');
  const [connectionMethod, setConnectionMethod] = useState('SNMP');
  const [snmpCommunity, setSnmpCommunity] = useState('');
  const [sshUsername, setSshUsername] = useState('');
  const [sshPassword, setSshPassword] = useState('');
  const [popName, setPopName] = useState('');
  const [location, setLocation] = useState('');
  const [lat, setLat] = useState('');
  const [lon, setLon] = useState('');

  // Diagnostic test state
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  const fetchOlts = async () => {
    try {
      const res = await axios.get('/api/v1/olts/');
      setOlts(res.data);
    } catch (err) {
      console.error('Error fetching OLTs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOlts();
  }, []);

  const handleTestConnection = async () => {
    setTestResult(null);
    setIsTesting(true);
    try {
      const res = await axios.post('/api/v1/olts/test-connection', {
        vendor,
        connection_method: connectionMethod,
        ip_address: ipAddress,
        snmp_community: snmpCommunity || 'public',
        ssh_username: sshUsername || null,
        ssh_password: sshPassword || null
      });
      setTestResult(res.data);
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.response?.data?.detail || 'Failed to trigger diagnostic test.'
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name,
      ip_address: ipAddress,
      vendor,
      connection_method: connectionMethod,
      snmp_community: snmpCommunity || null,
      ssh_username: sshUsername || null,
      ssh_password: sshPassword || null,
      pop_name: popName || null,
      location: location || null,
      latitude: lat ? parseFloat(lat) : null,
      longitude: lon ? parseFloat(lon) : null
    };

    try {
      if (editOlt) {
        await axios.put(`/api/v1/olts/${editOlt.id}`, payload);
      } else {
        await axios.post('/api/v1/olts/', payload);
      }
      setShowModal(false);
      resetForm();
      fetchOlts();
    } catch (err) {
      console.error('Error saving OLT:', err);
      alert('Error saving OLT parameters. Double check input details.');
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this OLT device from inventory? All linked ports and ONUs will be removed.')) {
      try {
        await axios.delete(`/api/v1/olts/${id}`);
        fetchOlts();
      } catch (err) {
        console.error('Error deleting OLT:', err);
      }
    }
  };

  const resetForm = () => {
    setEditOlt(null);
    setName('');
    setIpAddress('');
    setVendor('GENERIC');
    setConnectionMethod('SNMP');
    setSnmpCommunity('');
    setSshUsername('');
    setSshPassword('');
    setPopName('');
    setLocation('');
    setLat('');
    setLon('');
    setTestResult(null);
  };

  const openEdit = (olt: OLT) => {
    setEditOlt(olt);
    setName(olt.name);
    setIpAddress(olt.ip_address);
    setVendor(olt.vendor);
    setConnectionMethod(olt.connection_method);
    setPopName(olt.pop_name || '');
    setLocation(olt.location || '');
    setLat(olt.location ? '' : ''); // Optional coordinates
    setShowModal(true);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-wide text-white">OLT Inventory</h1>
            <p className="text-xs text-noc-textMuted mt-1">Manage infrastructure, IP addresses, SNMP configs, and CLI logins.</p>
          </div>
          <button
            onClick={() => { resetForm(); setShowModal(true); }}
            className="flex items-center gap-2 py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold tracking-wide shadow-lg shadow-indigo-600/10 transition-all"
          >
            <Plus size={16} />
            <span>Add OLT Node</span>
          </button>
        </div>

        {/* 1. Main Grid List */}
        {isLoading ? (
          <div className="py-24 text-center font-mono text-xs text-noc-textMuted animate-pulse">
            Querying network switches inventory...
          </div>
        ) : olts.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-noc-border rounded-xl">
            <Server className="text-noc-textMuted mx-auto mb-3" size={32} />
            <p className="text-sm font-semibold text-gray-300">No OLT devices added</p>
            <p className="text-xs text-noc-textMuted mt-1">Configure your first hardware node to start SNMP live polling.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {olts.map((olt) => (
              <div key={olt.id} className="glass-panel p-6 rounded-xl flex flex-col justify-between relative overflow-hidden">
                
                {/* Vendor label background */}
                <div className="absolute top-0 right-0 px-3 py-1 bg-noc-border text-gray-400 font-mono text-[9px] uppercase tracking-wider rounded-bl border-l border-b border-noc-border">
                  {olt.vendor}
                </div>

                <div className="space-y-4">
                  <div>
                    <h2 className="text-base font-bold text-white tracking-wide">{olt.name}</h2>
                    <p className="text-xs text-indigo-400 font-mono mt-1">{olt.ip_address}</p>
                  </div>

                  {/* Physical location stats */}
                  <div className="grid grid-cols-2 gap-2 py-3 border-y border-noc-border text-xs">
                    <div>
                      <p className="text-[10px] text-noc-textMuted uppercase tracking-wider font-mono">POP Site</p>
                      <p className="font-semibold text-gray-300 mt-1">{olt.pop_name || 'Unassigned'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-noc-textMuted uppercase tracking-wider font-mono">Location</p>
                      <p className="font-semibold text-gray-300 mt-1 truncate">{olt.location || 'Unassigned'}</p>
                    </div>
                  </div>

                  {/* Polled Telemetry stats */}
                  <div className="space-y-2.5 text-xs font-mono">
                    <div className="flex justify-between">
                      <span className="text-noc-textMuted">Poll Status:</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 ${
                        olt.status === 'ONLINE' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${olt.status === 'ONLINE' ? 'bg-emerald-400 status-glow-green' : 'bg-rose-400 status-glow-red'}`} />
                        {olt.status}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-noc-textMuted">CPU / RAM:</span>
                      <span className="text-gray-300">{olt.status === 'ONLINE' ? `${olt.cpu_usage}% / ${olt.ram_usage}%` : '—'}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-noc-textMuted">Temperature:</span>
                      <span className="text-gray-300">{olt.status === 'ONLINE' ? `${olt.temperature}°C` : '—'}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-noc-textMuted">Uptime:</span>
                      <span className="text-gray-300 text-right truncate max-w-[150px]">{olt.status === 'ONLINE' ? olt.uptime : '—'}</span>
                    </div>
                  </div>
                </div>

                {/* Card Actions footer */}
                <div className="mt-6 pt-4 border-t border-noc-border flex items-center justify-between">
                  <div className="inline-flex gap-1 items-center px-2 py-1 rounded bg-[#090D18] text-[10px] text-noc-textMuted font-mono uppercase">
                    <ShieldCheck size={11} />
                    <span>via {olt.connection_method}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openEdit(olt)}
                      className="p-2 bg-[#0C1221] hover:bg-noc-cardLight text-noc-textMuted hover:text-white rounded border border-noc-border transition-all"
                      title="Edit Configuration"
                    >
                      <Edit2 size={13} />
                    </button>
                    <button
                      onClick={() => handleDelete(olt.id)}
                      className="p-2 bg-rose-500/5 hover:bg-rose-500/10 text-rose-500 hover:text-rose-400 rounded border border-rose-500/20 transition-all"
                      title="Remove Node"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

              </div>
            ))}
          </div>
        )}

        {/* 2. Add / Edit OLT Modal Dialog */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
            <div className="w-full max-w-2xl glass-panel rounded-2xl shadow-glass overflow-hidden flex flex-col my-8">
              
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-noc-border bg-[#0C1221] flex justify-between items-center">
                <h3 className="text-base font-bold text-white tracking-wide">
                  {editOlt ? `Modify OLT Node: ${editOlt.name}` : 'Register New OLT Node'}
                </h3>
                <button 
                  onClick={() => setShowModal(false)}
                  className="text-noc-textMuted hover:text-white font-mono text-sm"
                >
                  [CLOSE]
                </button>
              </div>

              {/* Modal Body */}
              <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-6 space-y-6 max-h-[70vh]">
                
                {/* Section A: Hardware Identity */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest font-mono">1. Identity & Network Address</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">OLT Label Name</label>
                      <input
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="e.g. Huawei-MA5800-Core1"
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">IP Management Address</label>
                      <input
                        type="text"
                        required
                        value={ipAddress}
                        onChange={(e) => setIpAddress(e.target.value)}
                        placeholder="e.g. 10.100.5.10"
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white font-mono"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">Hardware Vendor</label>
                      <select
                        value={vendor}
                        onChange={(e) => setVendor(e.target.value)}
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white"
                      >
                        <option value="HUAWEI">Huawei SmartAX</option>
                        <option value="ZTE">ZTE ZXROS</option>
                        <option value="BDCOM">BDCOM EPON/GPON</option>
                        <option value="VSOL">VSOL GPON</option>
                        <option value="CDATA">CData</option>
                        <option value="GENERIC">Generic SNMP Switch</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">Connection Protocol</label>
                      <select
                        value={connectionMethod}
                        onChange={(e) => setConnectionMethod(e.target.value)}
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white"
                      >
                        <option value="SNMP">SNMP GET/Walk (Reads)</option>
                        <option value="SSH">SSH Command Terminal (Reads/CLI Writes)</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Section B: Credentials */}
                <div className="space-y-4 pt-4 border-t border-noc-border">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest font-mono">2. Security & Credentials</h4>
                  
                  {connectionMethod === 'SNMP' ? (
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">SNMP Read Community Key</label>
                      <input
                        type="password"
                        value={snmpCommunity}
                        onChange={(e) => setSnmpCommunity(e.target.value)}
                        placeholder="e.g. public123 (leave empty to retain saved)"
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white"
                      />
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">SSH Username</label>
                        <input
                          type="text"
                          value={sshUsername}
                          onChange={(e) => setSshUsername(e.target.value)}
                          placeholder="e.g. admin"
                          className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">SSH Password</label>
                        <input
                          type="password"
                          value={sshPassword}
                          onChange={(e) => setSshPassword(e.target.value)}
                          placeholder="leave empty to retain saved"
                          className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Section C: POP / Geographical mapping */}
                <div className="space-y-4 pt-4 border-t border-noc-border">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest font-mono">3. Physical Mapping & Coordinates</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">POP Station Name</label>
                      <input
                        type="text"
                        value={popName}
                        onChange={(e) => setPopName(e.target.value)}
                        placeholder="e.g. Central-POP-01"
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">Physical Address / Rack Position</label>
                      <input
                        type="text"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                        placeholder="e.g. Rack A, Shelf 3, Room 102"
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">Latitude</label>
                      <input
                        type="text"
                        value={lat}
                        onChange={(e) => setLat(e.target.value)}
                        placeholder="e.g. 23.8103"
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-noc-textMuted uppercase mb-1">Longitude</label>
                      <input
                        type="text"
                        value={lon}
                        onChange={(e) => setLon(e.target.value)}
                        placeholder="e.g. 90.4125"
                        className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2 px-3 text-xs focus:outline-none focus:border-indigo-500 text-white font-mono"
                      />
                    </div>
                  </div>
                </div>

                {/* Section D: Diagnostic Connection testing */}
                <div className="pt-4 border-t border-noc-border space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-gray-300 uppercase font-mono">4. Reachability Test</h4>
                      <p className="text-[10px] text-noc-textMuted mt-0.5">Diagnose IP access and authentication prior to saving.</p>
                    </div>
                    <button
                      type="button"
                      disabled={isTesting || !ipAddress}
                      onClick={handleTestConnection}
                      className="py-1 px-3 bg-noc-card hover:bg-noc-cardLight disabled:opacity-50 text-indigo-400 text-xs font-semibold rounded border border-noc-border tracking-wide transition-all"
                    >
                      {isTesting ? 'Pinging Node...' : 'Run Diagnostics'}
                    </button>
                  </div>

                  {testResult && (
                    <div className={`p-3 border rounded-lg text-xs flex gap-2 items-start ${
                      testResult.success 
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                        : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                    }`}>
                      {testResult.success ? (
                        <>
                          <CheckCircle size={14} className="mt-0.5 shrink-0" />
                          <div>
                            <strong className="block text-white">Diagnostics Succeeded:</strong>
                            <span className="text-[11px] block mt-0.5">{testResult.message}</span>
                          </div>
                        </>
                      ) : (
                        <>
                          <XCircle size={14} className="mt-0.5 shrink-0" />
                          <div>
                            <strong className="block text-white">Diagnostics Failed:</strong>
                            <span className="text-[11px] block mt-0.5">{testResult.message}</span>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>

                {/* Save actions footer */}
                <div className="pt-6 border-t border-noc-border flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="py-2 px-4 bg-noc-card hover:bg-noc-cardLight text-gray-400 hover:text-white rounded-lg text-xs font-semibold tracking-wide transition-all border border-noc-border"
                  >
                    Discard Changes
                  </button>
                  <button
                    type="submit"
                    className="py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold tracking-wide shadow-lg shadow-indigo-600/10 transition-all"
                  >
                    {editOlt ? 'Save Configuration' : 'Add to Active Inventory'}
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
