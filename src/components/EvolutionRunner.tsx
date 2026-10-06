import React from 'react';
import { RunConfig, AgentNode, ParentSelector, BenchmarkType } from '../types/ecode';
import { Play, Square, Settings, Terminal, ShieldAlert, Cpu, Sparkles, X } from 'lucide-react';

interface EvolutionRunnerProps {
  isOpen: boolean;
  onClose: () => void;
  config: RunConfig;
  onUpdateConfig: (config: Partial<RunConfig>) => void;
  onRunGeneration: (targetParentId?: string) => Promise<void>;
  isRunning: boolean;
  targetParent: AgentNode | null;
  onClearTargetParent: () => void;
  liveLogs: string[];
}

export const EvolutionRunner: React.FC<EvolutionRunnerProps> = ({
  isOpen,
  onClose,
  config,
  onUpdateConfig,
  onRunGeneration,
  isRunning,
  targetParent,
  onClearTargetParent,
  liveLogs,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl flex flex-col shadow-2xl overflow-hidden max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2">
            <Play className="w-5 h-5 text-indigo-400 fill-current" />
            <h2 className="text-base font-bold text-white">ECode Evolutionary Loop Controller</h2>
          </div>
          <button
            onClick={onClose}
            disabled={isRunning}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-40 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Target Parent Alert if any */}
          {targetParent && (
            <div className="bg-indigo-950/40 border border-indigo-800/80 p-3 rounded-xl flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span className="text-indigo-200">
                  Targeted Mutation pinned to parent:{' '}
                  <strong className="font-mono text-white">{targetParent.id}</strong> ({targetParent.title})
                </span>
              </div>
              <button
                onClick={onClearTargetParent}
                className="text-slate-400 hover:text-white underline cursor-pointer"
              >
                Use automated selector
              </button>
            </div>
          )}

          {/* Config Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Parent Selection Strategy
              </label>
              <select
                value={config.parentSelector}
                disabled={isRunning || !!targetParent}
                onChange={(e) => onUpdateConfig({ parentSelector: e.target.value as ParentSelector })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              >
                <option value="dgm-weighted">DGM-Weighted (Novelty & Fitness Score)</option>
                <option value="score-prop">Score-Proportionate (Softmax Sigmoid)</option>
                <option value="best-score">Best-Score (Greedy Elitism)</option>
                <option value="random">Random (Uniform Exploration)</option>
              </select>
              <p className="text-[11px] text-slate-500 mt-1">
                Policy used to sample parents from the archive for proposing code changes.
              </p>
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Evaluation Benchmark Workload
              </label>
              <select
                value={config.benchmark}
                disabled={isRunning}
                onChange={(e) => onUpdateConfig({ benchmark: e.target.value as BenchmarkType })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              >
                <option value="swe-bench">SWE-bench Lite (Python Real-World Issues)</option>
                <option value="polyglot">Polyglot Benchmark (Multi-language)</option>
                <option value="offline-fixture">Deterministic Offline Fixture (Synthetic)</option>
              </select>
              <p className="text-[11px] text-slate-500 mt-1">
                Target test suite against which candidate agent patches are evaluated.
              </p>
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Random Seed (Reproducibility)
              </label>
              <input
                type="number"
                value={config.seed}
                disabled={isRunning}
                onChange={(e) => onUpdateConfig({ seed: parseInt(e.target.value) || 1 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Ensures exact attribution of mutation & selection sequences.
              </p>
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Execution Sandbox Policy
              </label>
              <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300">
                <input
                  type="checkbox"
                  id="failClosed"
                  checked={config.failClosedDocker}
                  disabled={isRunning}
                  onChange={(e) => onUpdateConfig({ failClosedDocker: e.target.checked })}
                  className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="failClosed" className="text-xs text-slate-300 cursor-pointer">
                  Fail-Closed Docker Isolation (fail if sandbox drops)
                </label>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Strict ECode policy: never execute generated untrusted code on host.
              </p>
            </div>
          </div>

          {/* Terminal output */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                Live Execution Logs & Evaluation Telemetry
              </span>
              {isRunning && (
                <span className="text-xs text-indigo-400 font-mono flex items-center gap-1.5 animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                  Processing iteration...
                </span>
              )}
            </div>
            <div className="bg-slate-950 rounded-xl border border-slate-800 p-3 font-mono text-[11px] text-slate-300 h-48 overflow-y-auto space-y-1">
              {liveLogs.length === 0 ? (
                <div className="text-slate-600 italic">No execution in progress. Click "Evolve Next Generation" to start.</div>
              ) : (
                liveLogs.map((log, index) => (
                  <div key={index} className="leading-relaxed">
                    {log.includes('RESOLVED') ? (
                      <span className="text-emerald-400 font-bold">{log}</span>
                    ) : log.includes('MUTATION') ? (
                      <span className="text-cyan-400">{log}</span>
                    ) : log.includes('WARN') || log.includes('UNRESOLVED') ? (
                      <span className="text-amber-400">{log}</span>
                    ) : (
                      log
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <button
            onClick={onClose}
            disabled={isRunning}
            className="px-4 py-2 text-xs text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-40 cursor-pointer"
          >
            Close
          </button>

          <button
            onClick={() => onRunGeneration(targetParent?.id)}
            disabled={isRunning}
            className="flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white px-5 py-2.5 rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50 cursor-pointer"
          >
            {isRunning ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Evolving Agent...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Evolve Next Generation (+1 Step)</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
