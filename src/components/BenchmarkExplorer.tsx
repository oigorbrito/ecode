import React from 'react';
import { BenchmarkInstance } from '../types/ecode';
import { Target, CheckCircle2, XCircle, AlertTriangle, Clock, Search, FileCode, Check } from 'lucide-react';

interface BenchmarkExplorerProps {
  instances: BenchmarkInstance[];
}

export const BenchmarkExplorer: React.FC<BenchmarkExplorerProps> = ({ instances }) => {
  const [filter, setFilter] = React.useState<'all' | 'resolved' | 'unresolved' | 'empty'>('all');
  const [search, setSearch] = React.useState('');
  const [selectedInstance, setSelectedInstance] = React.useState<BenchmarkInstance | null>(instances[0] || null);

  const filteredInstances = React.useMemo(() => {
    return instances.filter((inst) => {
      const matchesSearch =
        inst.instanceId.toLowerCase().includes(search.toLowerCase()) ||
        inst.repo.toLowerCase().includes(search.toLowerCase()) ||
        inst.problemStatement.toLowerCase().includes(search.toLowerCase());

      if (!matchesSearch) return false;
      if (filter === 'resolved') return inst.resolvedByAgent;
      if (filter === 'unresolved') return !inst.resolvedByAgent && !inst.emptyPatch;
      if (filter === 'empty') return inst.emptyPatch;
      return true;
    });
  }, [instances, filter, search]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Instances List (Left column) */}
      <div className="lg:col-span-5 bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex flex-col h-[750px]">
        <div className="pb-3 border-b border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Target className="w-4 h-4 text-cyan-400" />
              Benchmark Evaluation Tasks
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              {filteredInstances.length} / {instances.length} tasks
            </span>
          </div>

          {/* Search bar */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search repo, issue ID, problem..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex gap-1.5 text-[11px]">
            <button
              onClick={() => setFilter('all')}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                filter === 'all' ? 'bg-indigo-600 text-white font-medium' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('resolved')}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                filter === 'resolved' ? 'bg-emerald-600 text-white font-medium' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Resolved
            </button>
            <button
              onClick={() => setFilter('unresolved')}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                filter === 'unresolved' ? 'bg-rose-600 text-white font-medium' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Unresolved
            </button>
            <button
              onClick={() => setFilter('empty')}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                filter === 'empty' ? 'bg-amber-600 text-white font-medium' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Empty Patch
            </button>
          </div>
        </div>

        {/* Scrollable list */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pt-3 pr-1">
          {filteredInstances.map((inst) => {
            const isSelected = selectedInstance?.instanceId === inst.instanceId;
            return (
              <div
                key={inst.instanceId}
                onClick={() => setSelectedInstance(inst)}
                className={`p-3 rounded-lg border transition-all cursor-pointer text-xs ${
                  isSelected
                    ? 'border-indigo-500 bg-slate-800/90 shadow-md ring-1 ring-indigo-500/50'
                    : 'border-slate-800 bg-slate-950/60 hover:border-slate-700 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono font-semibold text-slate-200 truncate max-w-[220px]">
                    {inst.instanceId}
                  </span>
                  {inst.resolvedByAgent ? (
                    <span className="flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-2 py-0.5 rounded-full font-medium">
                      <CheckCircle2 className="w-3 h-3" /> Resolved
                    </span>
                  ) : inst.emptyPatch ? (
                    <span className="flex items-center gap-1 text-[10px] text-amber-400 bg-amber-950/60 border border-amber-800/80 px-2 py-0.5 rounded-full font-medium">
                      <AlertTriangle className="w-3 h-3" /> Empty Patch
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] text-rose-400 bg-rose-950/60 border border-rose-800/80 px-2 py-0.5 rounded-full font-medium">
                      <XCircle className="w-3 h-3" /> Failed
                    </span>
                  )}
                </div>

                <p className="text-slate-400 line-clamp-2 text-[11px] mb-2 leading-relaxed">
                  {inst.problemStatement}
                </p>

                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1.5 border-t border-slate-800/60">
                  <span className="font-mono text-slate-400">{inst.repo}</span>
                  <div className="flex items-center gap-2">
                    <span>{inst.testsPassed}/{inst.testsTotal} tests</span>
                    <span className="flex items-center gap-0.5">
                      <Clock className="w-3 h-3" /> {inst.execTimeSec}s
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Instance Inspector (Right column) */}
      <div className="lg:col-span-7 bg-slate-900/50 border border-slate-800 rounded-xl p-5 flex flex-col h-[750px] overflow-y-auto">
        {selectedInstance ? (
          <div className="space-y-5">
            {/* Header info */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-indigo-400 bg-indigo-950/60 px-2.5 py-1 rounded border border-indigo-800">
                  {selectedInstance.instanceId}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">
                    Repository: <strong className="text-slate-200">{selectedInstance.repo}</strong> (v{selectedInstance.version})
                  </span>
                </div>
              </div>
              <h3 className="text-base font-semibold text-white">
                Task Problem Statement
              </h3>
            </div>

            {/* Problem statement description */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-200 leading-relaxed font-sans">
              {selectedInstance.problemStatement}
            </div>

            {/* Execution status metrics */}
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-lg">
                <span className="text-slate-500 block mb-0.5">Evaluation Status</span>
                <span className={`font-semibold font-mono ${
                  selectedInstance.resolvedByAgent ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {selectedInstance.resolvedByAgent ? 'PASS (RESOLVED)' : selectedInstance.emptyPatch ? 'EMPTY PATCH' : 'FAIL (UNRESOLVED)'}
                </span>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-lg">
                <span className="text-slate-500 block mb-0.5">Tests Passed</span>
                <span className="font-semibold font-mono text-cyan-400">
                  {selectedInstance.testsPassed} / {selectedInstance.testsTotal}
                </span>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-lg">
                <span className="text-slate-500 block mb-0.5">Sandbox Duration</span>
                <span className="font-semibold font-mono text-slate-200">
                  {selectedInstance.execTimeSec}s
                </span>
              </div>
            </div>

            {/* Base Commit */}
            <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-lg text-xs flex items-center justify-between">
              <span className="text-slate-400">Target Git Base Commit:</span>
              <code className="text-indigo-300 font-mono text-[11px] select-all">
                {selectedInstance.baseCommit}
              </code>
            </div>

            {/* Execution Logs */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-indigo-400" />
                Container & Test Harness Execution Trace
              </h4>
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-[11px] text-slate-300 space-y-1 max-h-64 overflow-y-auto">
                {selectedInstance.logs.map((log, i) => (
                  <div key={i} className="py-0.5">
                    {log.includes('RESOLVED') ? (
                      <span className="text-emerald-400 font-bold">{log}</span>
                    ) : log.includes('UNRESOLVED') || log.includes('EMPTY_PATCH') ? (
                      <span className="text-rose-400 font-bold">{log}</span>
                    ) : (
                      log
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500 text-xs">
            Select an instance from the list to view problem statement and logs.
          </div>
        )}
      </div>
    </div>
  );
};
