import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { MetricCard } from '../components/MetricCard';
import { ShieldAlert, Globe, Activity, Terminal, AlertTriangle, Bug } from 'lucide-react';

interface Metrics {
  total_sites: number;
  total_blocks_30d: number;
  total_requests_30d: number;
  unique_attackers: number;
  vulnerabilities: {
    Critical: number;
    High: number;
    Medium: number;
    Low: number;
  };
  waf_trend: Array<{ date: string; blocks: number; requests: number }>;
}

export const Dashboard: React.FC = () => {
  const { apiFetch } = useAuth();
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const data = await apiFetch('/dashboard/metrics');
        setMetrics(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard metrics.');
      } finally {
        setLoading(false);
      }
    };
    loadMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-red-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-2xl flex items-center space-x-3">
        <AlertTriangle className="h-6 w-6" />
        <span>{error}</span>
      </div>
    );
  }

  const totalVulns = metrics 
    ? (metrics.vulnerabilities.Critical + metrics.vulnerabilities.High + metrics.vulnerabilities.Medium + metrics.vulnerabilities.Low) 
    : 0;

  // Custom SVG Trend Line Builder
  const renderTrendSvg = () => {
    if (!metrics || metrics.waf_trend.length === 0) return null;
    
    const width = 600;
    const height = 200;
    const padding = 30;
    const maxVal = Math.max(...metrics.waf_trend.map(d => d.blocks), 1);
    
    const points = metrics.waf_trend.map((d, i) => {
      const x = padding + (i * (width - 2 * padding)) / (metrics.waf_trend.length - 1);
      const y = height - padding - (d.blocks * (height - 2 * padding)) / maxVal;
      return { x, y };
    });

    const pathD = points.reduce((acc, p, i) => {
      return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
    }, '');

    return (
      <svg className="w-full h-64 bg-[#070b19] border border-slate-800/60 rounded-2xl p-4" viewBox={`0 0 ${width} ${height}`}>
        {/* Horizontal grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((r, i) => {
          const y = padding + r * (height - 2 * padding);
          return (
            <line key={i} x1={padding} y1={y} x2={width - padding} y2={y} stroke="#1e293b" strokeDasharray="3 3" />
          );
        })}
        {/* Fill Area */}
        {points.length > 0 && (
          <path
            d={`${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`}
            fill="url(#trend-gradient)"
            opacity="0.15"
          />
        )}
        {/* Line */}
        <path d={pathD} fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        
        {/* Gradient Definition */}
        <defs>
          <linearGradient id="trend-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Data Dots & Label Texts */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="5" fill="#ef4444" stroke="#020617" strokeWidth="2" className="cursor-pointer hover:r-6" />
            <text x={p.x} y={p.y - 10} fill="#f1f5f9" fontSize="10" fontWeight="bold" textAnchor="middle">
              {metrics.waf_trend[i].blocks}
            </text>
            <text x={p.x} y={height - 8} fill="#64748b" fontSize="10" textAnchor="middle">
              {metrics.waf_trend[i].date}
            </text>
          </g>
        ))}
      </svg>
    );
  };

  return (
    <div className="space-y-8">
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Protected Sites"
          value={metrics?.total_sites || 0}
          description="Active Web Applications"
          icon={Globe}
          iconColorClass="text-emerald-500 bg-emerald-500/10"
        />
        <MetricCard
          title="WAF Blocks (30d)"
          value={metrics?.total_blocks_30d || 0}
          description="Malicious requests dropped"
          icon={ShieldAlert}
          iconColorClass="text-red-500 bg-red-500/10"
        />
        <MetricCard
          title="Unique Attackers"
          value={metrics?.unique_attackers || 0}
          description="Banned source IP addresses"
          icon={Activity}
          iconColorClass="text-orange-500 bg-orange-500/10"
        />
        <MetricCard
          title="Vulnerabilities Found"
          value={totalVulns}
          description="Confirmed scan results"
          icon={Bug}
          iconColorClass="text-yellow-500 bg-yellow-500/10"
        />
      </div>

      {/* Charts / Details section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* WAF Trend Line Chart */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
              <Terminal className="h-5 w-5 text-red-500" />
              <span>Real-Time WAF Threats (7 Days)</span>
            </h3>
            <span className="text-xs text-slate-500">Live logs active</span>
          </div>
          {renderTrendSvg()}
        </div>

        {/* Scan Vulnerabilities Ring Chart Legend */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white mb-6">Security Vulnerability Grade</h3>
            {metrics && (
              <div className="flex justify-center mb-6">
                <div className="relative flex items-center justify-center">
                  {/* Styled circular layout */}
                  <div className="w-32 h-32 rounded-full border-4 border-slate-800 flex flex-col items-center justify-center">
                    <span className="text-5xl font-black text-yellow-500">{totalVulns > 0 ? (totalVulns > 5 ? 'D' : 'C') : 'A'}</span>
                    <span className="text-[10px] text-slate-500 font-bold uppercase mt-1">Rating</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Severity Lists */}
          <div className="space-y-2 text-sm border-t border-slate-800/80 pt-4">
            <div className="flex justify-between items-center">
              <span className="flex items-center space-x-2">
                <span className="h-3 w-3 rounded-full bg-red-500"></span>
                <span className="text-slate-400">Critical Severity</span>
              </span>
              <strong className="text-white">{metrics?.vulnerabilities.Critical || 0}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="flex items-center space-x-2">
                <span className="h-3 w-3 rounded-full bg-orange-500"></span>
                <span className="text-slate-400">High Severity</span>
              </span>
              <strong className="text-white">{metrics?.vulnerabilities.High || 0}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="flex items-center space-x-2">
                <span className="h-3 w-3 rounded-full bg-yellow-500"></span>
                <span className="text-slate-400">Medium Severity</span>
              </span>
              <strong className="text-white">{metrics?.vulnerabilities.Medium || 0}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="flex items-center space-x-2">
                <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                <span className="text-slate-400">Low Severity</span>
              </span>
              <strong className="text-white">{metrics?.vulnerabilities.Low || 0}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Dashboard;
