import React from 'react';
import { AgentNode } from '../types/ecode';
import { DiffViewer } from './DiffViewer';
import { X, GitCommit, ShieldCheck, Cpu, Clock, Terminal, Zap, Hash, Award } from 'lucide-react';

interface AgentDetailModalProps {
  node: AgentNode | null;
  onClose: () => void;
  onSpawnChild: (parentNode: AgentNode) => void;
}

export const AgentDetailModal: React.FC<AgentDetailModalProps> = ({
  node,
  onClose,
  onSpawnChild,
}) => {
  if (!node) return null;

  const accPercent = Math.round(node.performance.accuracyScore * 100);

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <GitCommit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">{node.title}</h2>
                <span className="font-mono text-xs text-indigo-300 bg-indigo-950/60 border border-indigo-800 px-2 py-0.5 rounded">
                  {node.id}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Generation {node.generation} • Parent: {node.parentId || 'None (Root Baseline)'} • {node.timestamp}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Performance Summary Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950/70 border border-slate-800/80 p-3 rounded-xl">
              <span className="text-xs text-slate-400 block mb-1">Accuracy Score</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-emerald-400">
                  {accPercent}%
                </span>
                <span className="text-xs text-slate-500">
                  ({node.performance.totalResolved}/{node.performance.totalSubmitted})
                </span>
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800/80 p-3 rounded-xl">
              <span className="text-xs text-slate-400 block mb-1">Hallucination Score</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-cyan-400">
                  {node.performance.hallucinationScore.toFixed(2)}
                </span>
                <span className="text-xs text-slate-500">/ 2.00 max</span>
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800/80 p-3 rounded-xl">
              <span className="text-xs text-slate-400 block mb-1">Tool Utilization</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-indigo-400">
                  {Math.round(node.performance.percentToolUtilized * 100)}%
                </span>
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800/80 p-3 rounded-xl">
              <span className="text-xs text-slate-400 block mb-1">Empty Patches</span>
              <div className="flex items-baseline gap-2">
                <span className={`text-2xl font-bold font-mono ${node.performance.totalEmptyPatch > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
                  {node.performance.totalEmptyPatch}
                </span>
                <span className="text-xs text-slate-500">failures</span>
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Mutation Rationale
            </h3>
            <p className="text-sm text-slate-200 bg-slate-950/50 p-3 rounded-xl border border-slate-800/60">
              {node.description}
            </p>
          </div>

          {/* Diff Viewer */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Applied Code Mutation Patch
              </h3>
              <span className="text-xs text-slate-500 font-mono">
                unified git diff
              </span>
            </div>
            <DiffViewer diff={node.patchDiff} title={`Candidate diff for ${node.id}`} />
          </div>

          {/* Checksums & Attributes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl space-y-2 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                <span>Cryptographic Identity</span>
              </div>
              <div>
                <span className="text-slate-500 block">Candidate SHA256:</span>
                <code className="text-slate-300 font-mono text-[11px] break-all select-all">
                  {node.candidateSha256}
                </code>
              </div>
              <div>
                <span className="text-slate-500 block">Config SHA256:</span>
                <code className="text-slate-300 font-mono text-[11px] break-all select-all">
                  {node.configSha256}
                </code>
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl space-y-2 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span>Execution Parameters</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-slate-400">
                <div>Model: <span className="text-slate-200 font-mono">{node.attributes.model}</span></div>
                <div>Temp: <span className="text-slate-200 font-mono">{node.attributes.temperature}</span></div>
                <div>Prompt tokens: <span className="text-slate-200 font-mono">{node.attributes.promptTokens.toLocaleString()}</span></div>
                <div>Completion tokens: <span className="text-slate-200 font-mono">{node.attributes.completionTokens.toLocaleString()}</span></div>
                <div className="col-span-2">Active tools: <span className="text-slate-200 font-mono">{node.attributes.toolsUsed.join(', ')}</span></div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
          >
            Close
          </button>
          <button
            onClick={() => {
              onClose();
              onSpawnChild(node);
            }}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-xs font-medium shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Spawn Mutation From This Parent</span>
          </button>
        </div>
      </div>
    </div>
  );
};
