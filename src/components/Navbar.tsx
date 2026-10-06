import React from 'react';
import { GitBranch, Cpu, Play, RefreshCw, FileText, Download, ShieldCheck, Activity } from 'lucide-react';
import { EngineType } from '../types/ecode';

interface NavbarProps {
  engine: EngineType;
  setEngine: (engine: EngineType) => void;
  activeGeneration: number;
  totalAgents: number;
  bestAccuracy: number;
  onOpenRunner: () => void;
  onOpenProvenance: () => void;
  onReset: () => void;
  activeTab: 'lineage' | 'benchmarks' | 'prompts';
  setActiveTab: (tab: 'lineage' | 'benchmarks' | 'prompts') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  engine,
  setEngine,
  activeGeneration,
  totalAgents,
  bestAccuracy,
  onOpenRunner,
  onOpenProvenance,
  onReset,
  activeTab,
  setActiveTab,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-40 px-4 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Brand & Tagline */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 flex items-center justify-center">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                ECode
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  v0.1.0-alpha
                </span>
              </h1>
              <div className="flex items-center gap-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60 text-xs">
                <span className="text-slate-400">Engine:</span>
                <button
                  onClick={() => setEngine(engine === 'dgm' ? 'legacy' : 'dgm')}
                  className={`font-mono font-semibold px-1.5 py-0.5 rounded text-[11px] transition-colors cursor-pointer ${
                    engine === 'dgm'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-amber-600 text-white'
                  }`}
                  title="Toggle between DGM contract loop and legacy execution loop"
                >
                  {engine.toUpperCase()}
                </button>
              </div>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Evolutionary self-improving coding agent research platform
            </p>
          </div>
        </div>

        {/* Quick Metrics */}
        <div className="flex items-center gap-2 sm:gap-4 text-xs">
          <div className="bg-slate-950/60 border border-slate-800/80 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">Gen:</span>
            <span className="font-semibold text-white font-mono">{activeGeneration}</span>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">Agents:</span>
            <span className="font-semibold text-white font-mono">{totalAgents}</span>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-400">Best Acc:</span>
            <span className="font-bold text-emerald-400 font-mono">{(bestAccuracy * 100).toFixed(1)}%</span>
          </div>
        </div>

        {/* Navigation Tabs & Actions */}
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-950/80 p-0.5 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab('lineage')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === 'lineage'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Lineage Archive
            </button>
            <button
              onClick={() => setActiveTab('benchmarks')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === 'benchmarks'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Benchmarks
            </button>
            <button
              onClick={() => setActiveTab('prompts')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === 'prompts'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Prompts & Tools
            </button>
          </div>

          <button
            onClick={onOpenRunner}
            className="flex items-center gap-1.5 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white px-3 py-1.5 rounded-lg font-medium text-xs shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Evolve</span>
          </button>

          <button
            onClick={onOpenProvenance}
            className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg text-xs border border-slate-700/80 transition-colors cursor-pointer"
            title="Inspect Provenance & Baseline Manifest"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden lg:inline">Provenance</span>
          </button>

          <button
            onClick={onReset}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            title="Reset to baseline"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
};
