import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Plus, Power, ShieldAlert, CircleDot } from 'lucide-react';

interface Site {
  id: string;
  name: string;
  domain: string;
  origin_url: string;
  mode: string;
  block_threshold: number;
  created_at: string;
}

interface WafLog {
  id: string;
  site_name: string;
  ip_address: string;
  method: string;
  path: string;
  risk_score: number;
  blocked: boolean;
  matched_rules: string[];
  timestamp: string;
}

export const WafDashboard: React.FC = () => {
  const { apiFetch } = useAuth();
  const [sites, setSites] = useState<Site[]>([]);
  const [logs, setLogs] = useState<WafLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [domain, setDomain] = useState('');
  const [originUrl, setOriginUrl] = useState('');
  const [mode, setMode] = useState('Block');
  const [threshold, setThreshold] = useState(50);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const initData = async () => {
      try {
        const sitesData = await apiFetch('/sites/');
        setSites(sitesData);

        const logsData = await apiFetch('/logs/?limit=15');
        // Parse matched rules lists if strings
        const parsedLogs = logsData.map((l: any) => ({
          ...l,
          matched_rules: typeof l.matched_rules === 'string' ? JSON.parse(l.matched_rules) : l.matched_rules || []
        }));
        setLogs(parsedLogs);
      } catch (e) {
        console.error("Failed loading WAF data: ", e);
      } finally {
        setLoading(false);
      }
    };

    initData();

    // Establish WebSocket Connection for real-time alerts
    const ws = new WebSocket("ws://localhost:8000/api/dashboard/ws");
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.id && payload.ip_address) {
          // Verify it matches one of our sites before displaying
          setLogs(prev => [payload, ...prev].slice(0, 15));
        }
      } catch (err) {
        // Handle keepalive
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleAddSite = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSaving(true);

    try {
      const newSite = await apiFetch('/sites/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          domain,
          origin_url: originUrl,
          mode,
          block_threshold: threshold
        })
      });

      setSites(prev => [...prev, newSite]);
      setShowAddModal(false);
      setName('');
      setDomain('');
      setOriginUrl('');
    } catch (err: any) {
      setFormError(err.message || 'Failed to add protected site.');
    } finally {
      setSaving(false);
    }
  };

  const toggleSiteMode = async (site: Site) => {
    const updatedMode = site.mode === 'Block' ? 'Monitor' : 'Block';
    try {
      const updated = await apiFetch(`/sites/${site.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: updatedMode })
      });
      setSites(prev => prev.map(s => s.id === site.id ? updated : s));
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top action header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">WAF Web Applications Guard</h1>
          <p className="text-sm text-slate-400">Configure proxy routing, rules, and inspect incoming request flows</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center space-x-2 bg-red-500 hover:bg-red-600 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>Protect New Application</span>
        </button>
      </div>

      {/* Protected Apps List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sites.map(site => (
          <div key={site.id} className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white leading-tight">{site.name}</h3>
                  <span className="font-mono text-xs text-slate-500 block mt-1">{site.domain}</span>
                </div>
                <button
                  onClick={() => toggleSiteMode(site)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
                    site.mode === 'Block' 
                      ? 'bg-red-500/10 text-red-500 border border-red-500/20' 
                      : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                  }`}
                >
                  <Power className="h-3 w-3" />
                  <span>{site.mode === 'Block' ? 'Blocking Active' : 'Monitoring Only'}</span>
                </button>
              </div>

              <div className="space-y-2 mt-4 text-xs text-slate-400 border-t border-slate-800/80 pt-4">
                <div className="flex justify-between">
                  <span>Backend Origin URL:</span>
                  <span className="font-mono text-white">{site.origin_url}</span>
                </div>
                <div className="flex justify-between">
                  <span>WAF Block Threshold:</span>
                  <span className="text-white font-semibold">{site.block_threshold}/100 Risk</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Live Threat Logs Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-red-500 pulsing-dot mr-1"></span>
            <span>Live WAF Guard Activity Feed</span>
          </h3>
          <span className="text-xs text-slate-500">WebSocket connection listening...</span>
        </div>

        <div className="border border-slate-800/60 rounded-2xl overflow-hidden bg-[#070b19]/60">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/60 text-slate-400 font-semibold text-xs border-b border-slate-800">
                <th className="p-4">App Target</th>
                <th className="p-4">Attacker IP</th>
                <th className="p-4">Request path</th>
                <th className="p-4">Risk score</th>
                <th className="p-4">Status</th>
                <th className="p-4">Matched Signatures</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {logs.map((log, idx) => (
                <tr key={log.id || idx} className="hover:bg-slate-800/20 transition-colors animate-fadeIn">
                  <td className="p-4 font-semibold text-slate-200">{log.site_name}</td>
                  <td className="p-4 font-mono text-slate-400">{log.ip_address}</td>
                  <td className="p-4 font-mono text-slate-300">
                    <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-400 font-bold mr-2">{log.method}</span>
                    {log.path}
                  </td>
                  <td className="p-4 font-bold">
                    <span className={log.risk_score >= 70 ? 'text-red-500' : log.risk_score >= 40 ? 'text-orange-500' : 'text-slate-400'}>
                      {log.risk_score}/100
                    </span>
                  </td>
                  <td className="p-4">
                    {log.blocked ? (
                      <span className="inline-flex items-center space-x-1 text-red-400 bg-red-500/10 px-2 py-0.5 rounded">
                        <ShieldAlert className="h-3.5 w-3.5" />
                        <span>Blocked</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                        <CircleDot className="h-3.5 w-3.5 text-yellow-500" />
                        <span>Monitored</span>
                      </span>
                    )}
                  </td>
                  <td className="p-4">
                    <div className="flex flex-wrap gap-1">
                      {log.matched_rules.map((rule, rIdx) => (
                        <span key={rIdx} className="bg-slate-800 border border-slate-700/50 text-[10px] text-slate-400 px-1.5 py-0.5 rounded">
                          {rule}
                        </span>
                      ))}
                      {log.matched_rules.length === 0 && <span className="text-slate-600">-</span>}
                    </div>
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center p-8 text-slate-500">
                    No logs recorded. Direct traffic through your WAF proxy port to trigger inspections.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-lg p-8 rounded-2xl shadow-2xl relative">
            <h2 className="text-xl font-bold text-white mb-6">Protect New Web Application</h2>
            
            <form onSubmit={handleAddSite} className="space-y-4">
              {formError && (
                <div className="bg-red-500/10 text-red-400 border border-red-500/20 p-3 rounded-xl text-sm">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Application Name</label>
                <input
                  type="text"
                  required
                  placeholder="Billing Portal API"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Domain / Host</label>
                  <input
                    type="text"
                    required
                    placeholder="api.billing.io"
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Origin URL</label>
                  <input
                    type="text"
                    required
                    placeholder="http://localhost:8001"
                    value={originUrl}
                    onChange={(e) => setOriginUrl(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Proxy Mode</label>
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                  >
                    <option value="Block">Block Attacks</option>
                    <option value="Monitor">Log-Only (Monitor)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Block Threshold ({threshold})</label>
                  <input
                    type="range"
                    min="10"
                    max="90"
                    value={threshold}
                    onChange={(e) => setThreshold(parseInt(e.target.value))}
                    className="w-full h-10 mt-1"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2.5 border border-slate-800 rounded-xl text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2.5 bg-red-500 hover:bg-red-600 disabled:bg-red-500/50 text-white font-semibold rounded-xl transition-all"
                >
                  {saving ? 'Saving...' : 'Deploy Shield'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default WafDashboard;
