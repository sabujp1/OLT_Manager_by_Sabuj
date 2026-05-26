'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Activity, ShieldCheck, Mail, Lock } from 'lucide-react';
import axios from 'axios';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    
    try {
      // In Docker networking, `/api/v1` handles local redirects. Nginx reverse proxies this.
      const res = await axios.post('/api/v1/auth/login/json', { email, password });
      const { access_token, role, user_id, full_name } = res.data;
      login(access_token, role, user_id, full_name);
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail || 
        'Could not connect to OLT NOC API. Check if Docker container backend is running.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-[#070A13] flex items-center justify-center relative p-6 font-sans">
      
      {/* Visual glow backgrounds */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-600/5 rounded-full blur-3xl" />

      {/* Main glass card login box */}
      <div className="w-full max-w-md glass-panel p-8 rounded-2xl shadow-glass relative z-10">
        
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-indigo-600/20 text-indigo-400 rounded-xl mb-3 border border-indigo-500/20 status-glow-green">
            <Activity size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide">OLT NOC Manager</h1>
          <p className="text-xs text-noc-textMuted mt-1">ISP MULTI-VENDOR INFRASTRUCTURE MONITORING</p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-xs text-rose-400">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-noc-textMuted uppercase tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-noc-textMuted">
                <Mail size={16} />
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@oltnoc.local"
                className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-indigo-500 text-white placeholder-gray-600"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-noc-textMuted uppercase tracking-wider mb-2">
              Secret Access Key
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-noc-textMuted">
                <Lock size={16} />
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#0C1221] border border-noc-border rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-indigo-500 text-white placeholder-gray-600"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white py-2.5 rounded-lg text-sm font-semibold tracking-wide shadow-lg shadow-indigo-600/10 transition-all"
          >
            {isSubmitting ? 'Verifying Credentials...' : 'Sign In to Operations Console'}
          </button>
        </form>

        {/* Credentials hints helpful block */}
        <div className="mt-8 pt-6 border-t border-noc-border/40 text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-indigo-500/5 border border-indigo-500/10 text-[11px] text-indigo-400 font-mono">
            <ShieldCheck size={12} />
            <span>Default Superuser credentials active:</span>
          </div>
          <p className="text-[11px] font-mono text-noc-textMuted mt-2">
            User: <span className="text-white">admin@oltnoc.local</span> / Pass: <span className="text-white">admin123</span>
          </p>
        </div>

      </div>
    </div>
  );
}
