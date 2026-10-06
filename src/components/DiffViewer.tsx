import React from 'react';
import { Copy, Check } from 'lucide-react';

interface DiffViewerProps {
  diff: string;
  title?: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ diff, title }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(diff);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = diff.split('\n');

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 overflow-hidden font-mono text-xs">
      {title && (
        <div className="flex items-center justify-between px-3 py-2 bg-slate-950/70 border-b border-slate-800 text-slate-400">
          <span className="font-semibold text-slate-300">{title}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            title="Copy diff"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      )}
      <div className="overflow-x-auto p-3 max-h-80 overflow-y-auto leading-relaxed">
        {lines.map((line, idx) => {
          let lineClass = 'text-slate-400';
          let bgClass = '';
          if (line.startsWith('+++') || line.startsWith('---')) {
            lineClass = 'text-indigo-400 font-semibold';
            bgClass = 'bg-indigo-950/20';
          } else if (line.startsWith('@@')) {
            lineClass = 'text-cyan-400 font-semibold';
            bgClass = 'bg-cyan-950/20';
          } else if (line.startsWith('+')) {
            lineClass = 'text-emerald-300';
            bgClass = 'bg-emerald-950/40 border-l-2 border-emerald-500 pl-1';
          } else if (line.startsWith('-')) {
            lineClass = 'text-rose-400';
            bgClass = 'bg-rose-950/40 border-l-2 border-rose-500 pl-1';
          }

          return (
            <div key={idx} className={`whitespace-pre ${lineClass} ${bgClass} py-0.5 px-1 rounded-xs`}>
              {line || ' '}
            </div>
          );
        })}
      </div>
    </div>
  );
};
