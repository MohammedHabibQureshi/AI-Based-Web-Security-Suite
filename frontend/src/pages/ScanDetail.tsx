import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CodeViewer } from '../components/CodeViewer';
import { ArrowLeft, Download, ShieldAlert, AlertTriangle, Bug, Terminal, ChevronRight, CheckCircle2 } from 'lucide-react';
import { API_BASE } from '../context/AuthContext';

interface Finding {
  id: string;
  file_path: string;
  line_number: number;
  vulnerability_type: string;
  severity: string;
  plain_explanation: string;
  technical_explanation: string;
  suggested_fix_before: string;
  suggested_fix_after: string;
}

interface ScanDetailData {
  id: string;
  name: string;
  repo_url: string | null;
  branch: string | null;
  status: string;
  score: string;
  total_findings: number;
  created_at: string;
  findings: Finding[];
}

export const ScanDetail: React.FC = () => {
  const { scan_id } = useParams<{ scan_id: string }>();
  const { apiFetch } = useAuth();
  const [scan, setScan] = useState<ScanDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const loadScanDetail = async () => {
      try {
        const data = await apiFetch(`/scans/${scan_id}`);
        setScan(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load scan details.');
      } finally {
        setLoading(false);
      }
    };
    loadScanDetail();
  }, [scan_id]);

  const handleDownloadPDF = async () => {
    if (!scan_id) return;
    setDownloading(true);
    try {
      const response = await fetch(`${API_BASE}/reports/download/${scan_id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('sentinel_token')}`
        }
      });
      if (!response.ok) throw new Error('PDF generation failed.');
      
      const blob = await response.blob();
      
      // Parse Content-Disposition to get the correct filename from backend
      const contentDisp = response.headers.get("content-disposition") || "";
      let filename = `Web_Security_Suite_Report_${scan_id}.pdf`;
      const filenameMatch = contentDisp.match(/filename=(.+)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1];
      } else {
        const mimeType = response.headers.get("content-type") || "application/pdf";
        const fileExt = mimeType.includes("text/html") ? "html" : "pdf";
        filename = `Web_Security_Suite_Report_${scan_id}.${fileExt}`;
      }
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err: any) {
      alert(err.message || 'Download failed.');
    } finally {
      setDownloading(false);
    }
  };

  const getSeverityColor = (sev: string) => {
    switch (sev) {
      case 'Critical': return 'text-red-500 bg-red-500/10 border-red-500/20';
      case 'High': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
      case 'Medium': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
      default: return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-red-500"></div>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-2xl flex items-center space-x-3">
        <AlertTriangle className="h-6 w-6" />
        <span>{error || 'Scan record not found.'}</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Back button & Download Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Link
            to="/scanner"
            className="p-2 border border-slate-800 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/40 transition-all"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <span>Scanner</span>
              <ChevronRight className="h-3 w-3" />
              <span className="text-slate-300">{scan.name}</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight mt-1">{scan.name} Audits</h1>
          </div>
        </div>

        <button
          onClick={handleDownloadPDF}
          disabled={downloading}
          className="flex items-center justify-center space-x-2 bg-red-500 hover:bg-red-600 disabled:bg-red-500/50 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all"
        >
          <Download className="h-4 w-4" />
          <span>{downloading ? 'Compiling Report...' : 'Download PDF Security Report'}</span>
        </button>
      </div>

      {/* Meta Stats Panel */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="glass-panel p-5 rounded-2xl">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Security Grade</div>
          <div className="text-3xl font-extrabold text-yellow-500 font-outfit">Grade {scan.score}</div>
        </div>
        <div className="glass-panel p-5 rounded-2xl">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Audit Status</div>
          <div className="text-lg font-bold text-emerald-500 mt-1 capitalize">{scan.status}</div>
        </div>
        <div className="glass-panel p-5 rounded-2xl">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Total Vulnerabilities</div>
          <div className="text-3xl font-extrabold text-white font-outfit">{scan.total_findings}</div>
        </div>
        <div className="glass-panel p-5 rounded-2xl">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Repo Target</div>
          <div className="text-xs text-slate-300 font-semibold truncate mt-2 font-mono">
            {scan.repo_url ? scan.repo_url.replace('https://github.com/', '') : 'ZIP Upload Package'}
          </div>
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-6">
        <h3 className="text-lg font-bold text-white flex items-center space-x-2">
          <Bug className="h-5 w-5 text-red-500" />
          <span>Vulnerability Log ({scan.findings.length})</span>
        </h3>

        {scan.findings.map((finding) => (
          <div key={finding.id} className="glass-panel p-6 rounded-2xl border-l-4 border-l-red-500 space-y-4">
            {/* Header row */}
            <div className="flex justify-between items-start border-b border-slate-800/80 pb-4">
              <div>
                <h4 className="text-base font-bold text-white">{finding.vulnerability_type}</h4>
                <div className="text-xs text-slate-500 mt-1">
                  Location: <span className="font-mono text-slate-300 bg-slate-900 px-1.5 py-0.5 rounded">{finding.file_path}</span>
                </div>
              </div>
              
              <span className={`px-2.5 py-1 rounded text-xs font-bold uppercase border ${getSeverityColor(finding.severity)}`}>
                {finding.severity}
              </span>
            </div>

            {/* Plain English Explain */}
            <div className="space-y-1.5">
              <div className="text-xs font-bold uppercase tracking-wider text-red-400 flex items-center space-x-1.5">
                <ShieldAlert className="h-4 w-4" />
                <span>Exploit Path (Plain-English Explainer)</span>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed font-sans bg-[#090f23]/40 p-4 rounded-xl border border-slate-800/50">
                {finding.plain_explanation}
              </p>
            </div>

            {/* Technical Explain */}
            <div className="space-y-1.5">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                <Terminal className="h-4 w-4" />
                <span>Technical Root Cause</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed font-mono bg-slate-950/20 p-4 rounded-xl border border-slate-800/20 italic">
                {finding.technical_explanation}
              </p>
            </div>

            {/* Code Diff Panel */}
            <div className="pt-2">
              <CodeViewer
                beforeCode={finding.suggested_fix_before}
                afterCode={finding.suggested_fix_after}
                filePath={finding.file_path}
                lineNumber={finding.line_number}
              />
            </div>
          </div>
        ))}

        {scan.findings.length === 0 && (
          <div className="glass-panel p-12 rounded-2xl text-center space-y-4">
            <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto" />
            <h4 className="text-lg font-bold text-white">Excellent! No Vulnerabilities Found.</h4>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Web Security Suite scanner analyzed your target code directories and verified they do not contain typical OWASP vulnerabilities.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
export default ScanDetail;
