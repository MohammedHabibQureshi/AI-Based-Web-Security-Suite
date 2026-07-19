import React from 'react';

interface CodeViewerProps {
  beforeCode: string;
  afterCode: string;
  filePath: string;
  lineNumber?: number;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  beforeCode,
  afterCode,
  filePath,
  lineNumber
}) => {
  return (
    <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#070c1e]">
      <div className="bg-[#0b132b] px-4 py-2.5 border-b border-slate-800 flex justify-between items-center text-xs">
        <span className="font-mono text-slate-300">{filePath} {lineNumber ? `(Line ${lineNumber})` : ''}</span>
        <span className="bg-red-500/10 text-red-500 font-semibold px-2 py-0.5 rounded uppercase tracking-wider text-[10px]">Remediation Diff</span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-800">
        {/* Vulnerable Code */}
        <div className="p-4">
          <div className="text-[10px] text-red-500 font-bold uppercase tracking-wider mb-2 flex items-center space-x-1.5">
            <span className="h-2 w-2 rounded-full bg-red-500"></span>
            <span>Vulnerable Code Snippet</span>
          </div>
          <pre className="text-xs text-red-400 font-mono bg-red-950/10 border border-red-900/20 p-3 rounded-lg overflow-x-auto max-h-72">
            <code>{beforeCode || '// No snippet recorded.'}</code>
          </pre>
        </div>

        {/* Secure Code Fix */}
        <div className="p-4">
          <div className="text-[10px] text-green-500 font-bold uppercase tracking-wider mb-2 flex items-center space-x-1.5">
            <span className="h-2 w-2 rounded-full bg-green-500"></span>
            <span>Remediated Secure Code</span>
          </div>
          <pre className="text-xs text-green-400 font-mono bg-green-950/10 border border-green-900/20 p-3 rounded-lg overflow-x-auto max-h-72">
            <code>{afterCode || '// Auto-remediation code not available.'}</code>
          </pre>
        </div>
      </div>
    </div>
  );
};
export default CodeViewer;
