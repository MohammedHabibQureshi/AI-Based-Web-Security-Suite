import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Upload, GitBranch, Cpu, AlertTriangle, Eye, RefreshCw, Folder } from 'lucide-react';
import { API_BASE } from '../context/AuthContext';

interface Scan {
  id: string;
  name: string;
  repo_url: string | null;
  branch: string | null;
  status: string;
  score: string;
  total_findings: number;
  created_at: string;
}

export const ScannerDashboard: React.FC = () => {
  const { apiFetch } = useAuth();
  const navigate = useNavigate();
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'zip' | 'git'>('zip');

  // Zip scan form states
  const [zipName, setZipName] = useState('');
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [zipError, setZipError] = useState('');
  const [zipSubmitting, setZipSubmitting] = useState(false);

  // Git scan form states
  const [gitName, setGitName] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [gitError, setGitError] = useState('');
  const [gitSubmitting, setGitSubmitting] = useState(false);

  const loadScans = async () => {
    try {
      const data = await apiFetch('/scans/');
      setScans(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScans();
    // Poll scans status every 5 seconds to keep dashboard state fresh while scans execute
    const interval = setInterval(loadScans, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleZipScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setZipError('');
    if (!zipFile) {
      setZipError('Please select a .zip code package.');
      return;
    }
    setZipSubmitting(true);

    const formData = new FormData();
    formData.append('name', zipName);
    formData.append('file', zipFile);

    try {
      const res = await fetch(`${API_BASE}/scans/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('sentinel_token')}`
        },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed.');
      
      setScans(prev => [data, ...prev]);
      setZipName('');
      setZipFile(null);
      // Clear file input DOM element
      const fileInput = document.getElementById('zip-file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      setZipError(err.message || 'Scan trigger failed.');
    } finally {
      setZipSubmitting(false);
    }
  };

  const handleGitScan = async (e: React.FormEvent) => {
    e.preventDefault();
    setGitError('');
    setGitSubmitting(true);

    try {
      const newScan = await apiFetch('/scans/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: gitName,
          repo_url: repoUrl,
          branch
        })
      });

      setScans(prev => [newScan, ...prev]);
      setGitName('');
      setRepoUrl('');
      setBranch('main');
    } catch (err: any) {
      setGitError(err.message || 'Clone scan trigger failed.');
    } finally {
      setGitSubmitting(false);
    }
  };

  const getScoreBadgeClass = (score: string) => {
    switch (score) {
      case 'A': return 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20';
      case 'B': return 'bg-blue-500/10 text-blue-500 border border-blue-500/20';
      case 'C': return 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20';
      case 'D': return 'bg-orange-500/10 text-orange-500 border border-orange-500/20';
      default: return 'bg-red-500/10 text-red-500 border border-red-500/20';
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'Completed': return 'text-emerald-500 bg-emerald-500/10 border border-emerald-500/10';
      case 'Running': return 'text-yellow-500 bg-yellow-500/10 border border-yellow-500/10 animate-pulse';
      case 'Failed': return 'text-red-500 bg-red-500/10 border border-red-500/10';
      default: return 'text-slate-400 bg-slate-800 border border-slate-700/50';
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
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">AI Vulnerability Scanner (SAST)</h1>
        <p className="text-sm text-slate-400">Trigger code reviews via package uploads or repository connections</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Trigger scan panels */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel p-6 rounded-2xl">
            <div className="flex border-b border-slate-800 mb-6">
              <button
                onClick={() => setActiveTab('zip')}
                className={`flex-1 pb-3 text-sm font-semibold text-center border-b-2 transition-all ${
                  activeTab === 'zip' ? 'border-red-500 text-white' : 'border-transparent text-slate-400'
                }`}
              >
                ZIP Upload
              </button>
              <button
                onClick={() => setActiveTab('git')}
                className={`flex-1 pb-3 text-sm font-semibold text-center border-b-2 transition-all ${
                  activeTab === 'git' ? 'border-red-500 text-white' : 'border-transparent text-slate-400'
                }`}
              >
                Git Repository
              </button>
            </div>

            {activeTab === 'zip' ? (
              <form onSubmit={handleZipScan} className="space-y-4">
                {zipError && (
                  <div className="bg-red-500/10 text-red-400 border border-red-500/20 p-3 rounded-xl text-xs flex items-center space-x-1">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span>{zipError}</span>
                  </div>
                )}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Project Name</label>
                  <input
                    type="text"
                    required
                    placeholder="Express Backend API"
                    value={zipName}
                    onChange={(e) => setZipName(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Select ZIP Package</label>
                  <div className="border border-dashed border-slate-800 bg-[#090f23]/40 rounded-xl p-6 text-center hover:border-red-500/50 transition-colors relative cursor-pointer">
                    <Upload className="h-8 w-8 text-slate-500 mx-auto mb-2" />
                    <span className="text-xs text-slate-400 block font-semibold">
                      {zipFile ? zipFile.name : 'Upload .zip file'}
                    </span>
                    <span className="text-[10px] text-slate-600 block mt-1">Source directories (Max 50MB)</span>
                    <input
                      id="zip-file-input"
                      type="file"
                      accept=".zip"
                      required
                      onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={zipSubmitting}
                  className="w-full py-2.5 bg-red-500 hover:bg-red-600 disabled:bg-red-500/50 text-white text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all"
                >
                  <Cpu className="h-4 w-4" />
                  <span>{zipSubmitting ? 'Analyzing Source Code...' : 'Analyze ZIP Package'}</span>
                </button>
              </form>
            ) : (
              <form onSubmit={handleGitScan} className="space-y-4">
                {gitError && (
                  <div className="bg-red-500/10 text-red-400 border border-red-500/20 p-3 rounded-xl text-xs flex items-center space-x-1">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span>{gitError}</span>
                  </div>
                )}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Repository Title</label>
                  <input
                    type="text"
                    required
                    placeholder="Acme Auth Microservice"
                    value={gitName}
                    onChange={(e) => setGitName(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Git HTTP / Clone URL</label>
                  <input
                    type="url"
                    required
                    placeholder="https://github.com/company/auth.git"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Branch</label>
                  <div className="relative">
                    <GitBranch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      required
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      className="w-full pl-9 pr-4 py-2.5 bg-[#090f23] border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500 transition-colors text-xs"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={gitSubmitting}
                  className="w-full py-2.5 bg-red-500 hover:bg-red-600 disabled:bg-red-500/50 text-white text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>{gitSubmitting ? 'Cloning & Auditing...' : 'Clone & Analyze Repo'}</span>
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Scan History list */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <Folder className="h-5 w-5 text-red-500" />
            <span>Vulnerability Assessment Logs</span>
          </h3>

          <div className="border border-slate-800/60 rounded-2xl overflow-hidden bg-[#070b19]/60">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/60 text-slate-400 font-semibold text-xs border-b border-slate-800">
                  <th className="p-4">Project / Repo Target</th>
                  <th className="p-4">Ref/Branch</th>
                  <th className="p-4">Security Grade</th>
                  <th className="p-4">Findings</th>
                  <th className="p-4">Job Status</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {scans.map((scan) => (
                  <tr key={scan.id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="p-4 font-semibold text-slate-200">
                      {scan.name}
                      {scan.repo_url && (
                        <span className="block font-mono text-[9px] text-slate-500 mt-0.5 truncate max-w-xs">{scan.repo_url}</span>
                      )}
                    </td>
                    <td className="p-4 font-mono text-slate-400">
                      {scan.branch || 'ZIP Package'}
                    </td>
                    <td className="p-4 font-bold">
                      {scan.status === 'Completed' ? (
                        <span className={`px-2.5 py-0.5 rounded font-black text-xs ${getScoreBadgeClass(scan.score)}`}>
                          Grade {scan.score}
                        </span>
                      ) : <span className="text-slate-600">-</span>}
                    </td>
                    <td className="p-4">
                      {scan.status === 'Completed' ? (
                        <span className="font-semibold text-slate-200">
                          {scan.total_findings} findings
                        </span>
                      ) : <span className="text-slate-600">-</span>}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getStatusBadgeClass(scan.status)}`}>
                        {scan.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      {scan.status === 'Completed' ? (
                        <button
                          onClick={() => navigate(`/scanner/results/${scan.id}`)}
                          className="p-1.5 bg-slate-800 border border-slate-700/80 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition-colors"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      ) : (
                        <span className="text-[10px] text-slate-600 font-semibold italic">Processing</span>
                      )}
                    </td>
                  </tr>
                ))}
                {scans.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center p-8 text-slate-500">
                      No scans performed in this workspace. Upload code files above.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ScannerDashboard;
