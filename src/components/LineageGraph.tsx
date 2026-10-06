import React from 'react';
import { AgentNode } from '../types/ecode';
import { GitCommit, Sparkles, CheckCircle2, AlertTriangle, ArrowRight, Zap, Target } from 'lucide-react';

interface LineageGraphProps {
  nodes: AgentNode[];
  selectedNodeId: string | null;
  onSelectNode: (node: AgentNode) => void;
  onSpawnChild: (parentNode: AgentNode) => void;
}

export const LineageGraph: React.FC<LineageGraphProps> = ({
  nodes,
  selectedNodeId,
  onSelectNode,
  onSpawnChild,
}) => {
  // Group nodes by generation
  const generations = React.useMemo(() => {
    const map = new Map<number, AgentNode[]>();
    nodes.forEach((node) => {
      const list = map.get(node.generation) || [];
      list.push(node);
      map.set(node.generation, list);
    });
    return Array.from(map.entries()).sort(([a], [b]) => a - b);
  }, [nodes]);

  const getMutationBadge = (type: AgentNode['mutationType']) => {
    switch (type) {
      case 'baseline':
        return { label: 'Baseline', bg: 'bg-slate-700 text-slate-200' };
      case 'localized_edit':
        return { label: 'Localized Edit', bg: 'bg-emerald-900/60 text-emerald-300 border border-emerald-500/40' };
      case 'tool_protocol':
        return { label: 'Tool Protocol', bg: 'bg-blue-900/60 text-blue-300 border border-blue-500/40' };
      case 'prompt_diagnosis':
        return { label: 'Prompt Diagnosis', bg: 'bg-purple-900/60 text-purple-300 border border-purple-500/40' };
      case 'context_guard':
        return { label: 'Context Guard', bg: 'bg-amber-900/60 text-amber-300 border border-amber-500/40' };
      case 'error_recovery':
        return { label: 'Error Recovery', bg: 'bg-rose-900/60 text-rose-300 border border-rose-500/40' };
    }
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 backdrop-blur-xs">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 mb-6 border-b border-slate-800 gap-2">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-indigo-400" />
            Evolutionary Lineage DAG
          </h2>
          <p className="text-xs text-slate-400">
            Archive of agent candidates, lineage ancestry, and benchmark fitness scores over generations.
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <span>Acc &gt; 40%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
            <span>Acc 25-40%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-600"></span>
            <span>Acc &lt; 25%</span>
          </div>
        </div>
      </div>

      {/* Generation Tracks */}
      <div className="space-y-8 relative">
        {generations.map(([genNum, genNodes], genIdx) => (
          <div key={genNum} className="relative">
            {/* Generation header banner */}
            <div className="flex items-center gap-3 mb-3">
              <span className="bg-slate-800/90 text-indigo-300 px-2.5 py-0.5 rounded text-xs font-mono font-semibold border border-indigo-500/20">
                Generation {genNum}
              </span>
              <div className="h-px bg-slate-800 flex-1"></div>
              <span className="text-xs text-slate-500">
                {genNodes.length} candidate{genNodes.length > 1 ? 's' : ''}
              </span>
            </div>

            {/* Candidates grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {genNodes.map((node) => {
                const isSelected = selectedNodeId === node.id;
                const badge = getMutationBadge(node.mutationType);
                const accPercent = Math.round(node.performance.accuracyScore * 100);

                let scoreColor = 'text-slate-400';
                let scoreBg = 'bg-slate-800';
                if (accPercent >= 45) {
                  scoreColor = 'text-emerald-400 font-bold';
                  scoreBg = 'bg-emerald-500/20 border-emerald-500/30';
                } else if (accPercent >= 25) {
                  scoreColor = 'text-indigo-400 font-semibold';
                  scoreBg = 'bg-indigo-500/20 border-indigo-500/30';
                }

                return (
                  <div
                    key={node.id}
                    onClick={() => onSelectNode(node)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer relative overflow-hidden group ${
                      isSelected
                        ? 'border-indigo-500 bg-slate-800/90 shadow-xl shadow-indigo-500/10 ring-1 ring-indigo-500'
                        : 'border-slate-800 bg-slate-900/80 hover:border-slate-700 hover:bg-slate-850'
                    }`}
                  >
                    {/* Top row: ID, Badge, Score */}
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5 font-mono text-xs">
                        <span className="font-semibold text-slate-200">{node.id}</span>
                        {node.parentId && (
                          <span className="text-[11px] text-slate-500 flex items-center">
                            <ArrowRight className="w-3 h-3 mx-0.5" />
                            {node.parentId.slice(0, 8)}
                          </span>
                        )}
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${badge.bg}`}>
                        {badge.label}
                      </span>
                    </div>

                    {/* Title & Description */}
                    <h3 className="font-medium text-sm text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1 mb-1">
                      {node.title}
                    </h3>
                    <p className="text-xs text-slate-400 line-clamp-2 mb-3">
                      {node.description}
                    </p>

                    {/* Accuracy bar */}
                    <div className="space-y-1 mb-3">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-400">Benchmark Accuracy</span>
                        <span className={`font-mono ${scoreColor}`}>{accPercent}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            accPercent >= 45
                              ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                              : accPercent >= 25
                              ? 'bg-gradient-to-r from-indigo-500 to-cyan-400'
                              : 'bg-slate-600'
                          }`}
                          style={{ width: `${Math.max(accPercent, 4)}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Evaluation stats breakdown */}
                    <div className="grid grid-cols-3 gap-1 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                      <div>
                        <span className="block text-[10px] text-slate-500">Resolved</span>
                        <span className="font-semibold text-emerald-400 font-mono">
                          {node.performance.totalResolved}
                        </span>
                      </div>
                      <div>
                        <span className="block text-[10px] text-slate-500">Unresolved</span>
                        <span className="font-semibold text-slate-300 font-mono">
                          {node.performance.totalUnresolved}
                        </span>
                      </div>
                      <div>
                        <span className="block text-[10px] text-slate-500">Empty</span>
                        <span className="font-semibold text-amber-400 font-mono">
                          {node.performance.totalEmptyPatch}
                        </span>
                      </div>
                    </div>

                    {/* Quick action button */}
                    <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between">
                      <span className="text-[10px] font-mono text-slate-500">
                        {node.attributes.model}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSpawnChild(node);
                        }}
                        className="text-[11px] text-indigo-400 hover:text-indigo-200 font-medium flex items-center gap-1 hover:underline cursor-pointer"
                      >
                        <Zap className="w-3 h-3" />
                        Mutate from here
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
