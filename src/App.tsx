import React, { useState } from 'react';
import { AgentNode, RunConfig, TelemetryLog, EngineType } from './types/ecode';
import { initialAgentNodes, initialRunConfig, initialTelemetryLogs, sampleBenchmarkInstances } from './data/initialData';
import { Navbar } from './components/Navbar';
import { LineageGraph } from './components/LineageGraph';
import { AgentDetailModal } from './components/AgentDetailModal';
import { EvolutionRunner } from './components/EvolutionRunner';
import { BenchmarkExplorer } from './components/BenchmarkExplorer';
import { PromptsAndToolsView } from './components/PromptsAndToolsView';
import { ProvenanceModal } from './components/ProvenanceModal';
import { Activity, Terminal, Shield, Sparkles } from 'lucide-react';

export function App() {
  const [nodes, setNodes] = useState<AgentNode[]>(initialAgentNodes);
  const [config, setConfig] = useState<RunConfig>(initialRunConfig);
  const [selectedNode, setSelectedNode] = useState<AgentNode | null>(null);
  const [targetParent, setTargetParent] = useState<AgentNode | null>(null);
  const [isRunnerOpen, setIsRunnerOpen] = useState(false);
  const [isProvenanceOpen, setIsProvenanceOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'lineage' | 'benchmarks' | 'prompts'>('lineage');
  const [isRunning, setIsRunning] = useState(false);
  const [liveLogs, setLiveLogs] = useState<string[]>([
    '[ECode] System online. DGM contract engine active.',
    '[Provenance] Checksum verified: e3b0c442... Ready for evolution runs.',
  ]);

  // Derived metrics
  const activeGeneration = Math.max(...nodes.map((n) => n.generation), 0);
  const bestAccuracy = Math.max(...nodes.map((n) => n.performance.accuracyScore), 0);

  const handleUpdateConfig = (newCfg: Partial<RunConfig>) => {
    setConfig((prev) => ({ ...prev, ...newCfg }));
  };

  const handleReset = () => {
    if (window.confirm('Reset evolutionary archive back to initial baseline?')) {
      setNodes(initialAgentNodes.slice(0, 1));
      setLiveLogs(['[ECode] Archive reset to initial baseline Gen 0.']);
    }
  };

  const handleSpawnChild = (parentNode: AgentNode) => {
    setTargetParent(parentNode);
    setIsRunnerOpen(true);
  };

  const runEvolutionStep = async (pinnedParentId?: string) => {
    setIsRunning(true);

    // Determine parent
    let parent: AgentNode;
    if (pinnedParentId) {
      parent = nodes.find((n) => n.id === pinnedParentId) || nodes[nodes.length - 1];
    } else if (config.parentSelector === 'best-score') {
      parent = [...nodes].sort((a, b) => b.performance.accuracyScore - a.performance.accuracyScore)[0];
    } else if (config.parentSelector === 'random') {
      parent = nodes[Math.floor(Math.random() * nodes.length)];
    } else {
      // DGM weighted / score prop default
      const scores = nodes.map((n) => n.performance.accuracyScore);
      const maxScore = Math.max(...scores);
      parent = nodes.find((n) => n.performance.accuracyScore === maxScore) || nodes[nodes.length - 1];
    }

    const nextGen = parent.generation + 1;
    const randomHex = Math.random().toString(16).substring(2, 6);
    const newId = `commit-${randomHex}`;

    const mutationPool: Array<{
      type: AgentNode['mutationType'];
      title: string;
      desc: string;
      diff: string;
      accDelta: number;
    }> = [
      {
        type: 'tool_protocol',
        title: 'Fuzzy Tool Input Parameter Coercion',
        desc: 'Ensures tool call arguments handle missing or malformed keys gracefully without triggering unhandled exceptions.',
        diff: `--- a/tools/input_normalizer.py\n+++ b/tools/input_normalizer.py\n@@ -15,5 +15,11 @@ def normalize_args(args):\n+    if "path" in args and "file_path" not in args:\n+        args["file_path"] = args.pop("path")\n+    if "target" in args and "target_content" not in args:\n+        args["target_content"] = args.pop("target")\n+    return args`,
        accDelta: 0.08,
      },
      {
        type: 'localized_edit',
        title: 'Indentation-Preserving Block Replacement',
        desc: 'Automatically aligns whitespace and indentation when inserting nested Python functions and try-except blocks.',
        diff: `--- a/tools/edit.py\n+++ b/tools/edit.py\n@@ -88,6 +88,12 @@ def align_indentation(target, replacement):\n+    indent = detect_leading_whitespace(target)\n+    aligned_lines = [indent + line if line.strip() else line for line in replacement.splitlines()]\n+    return "\\n".join(aligned_lines)`,
        accDelta: 0.12,
      },
      {
        type: 'prompt_diagnosis',
        title: 'Multi-Perspective Failure Reflection Prompt',
        desc: 'Prompts the LLM to inspect both unit test assertions and caller traceback frames before formulating diffs.',
        diff: `--- a/prompts/diagnose_improvement_prompt.py\n+++ b/prompts/diagnose_improvement_prompt.py\n@@ -40,4 +40,9 @@ def format_failure_context(log):\n+    frames = extract_traceback_frames(log)\n+    return f"Failing Frames:\\n{frames}\\nIdentify root variable mismatch."`,
        accDelta: 0.10,
      },
      {
        type: 'context_guard',
        title: 'Adaptive Sliding Window Diff Truncation',
        desc: 'Compresses long test execution logs into concise summaries to preserve model context budget.',
        diff: `--- a/coding_agent.py\n+++ b/coding_agent.py\n@@ -210,6 +210,10 @@ def compress_logs(log_text):\n+    if len(log_text) > 4000:\n+        return log_text[:1500] + "\\n...[TRUNCATED BY ECODE CONTEXT GUARD]...\\n" + log_text[-2500:]\n+    return log_text`,
        accDelta: 0.06,
      },
    ];

    const chosenMutation = mutationPool[Math.floor(Math.random() * mutationPool.length)];

    // Simulation log streaming
    const addLog = (msg: string) => {
      setLiveLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
    };

    addLog(`Initiating Generation ${nextGen} evolution cycle...`);
    await new Promise((r) => setTimeout(r, 600));

    addLog(`Parent selected: ${parent.id} (Score: ${(parent.performance.accuracyScore * 100).toFixed(1)}%) via ${config.parentSelector}`);
    await new Promise((r) => setTimeout(r, 500));

    addLog(`Sandbox isolation check: Docker container ready (Fail-closed: ${config.failClosedDocker ? 'ACTIVE' : 'OFF'})`);
    await new Promise((r) => setTimeout(r, 600));

    addLog(`Formulating mutation candidate [${newId}] applying operator "${chosenMutation.title}"`);
    await new Promise((r) => setTimeout(r, 700));

    addLog(`Evaluating ${newId} against ${config.benchmark.toUpperCase()} benchmark suite...`);
    await new Promise((r) => setTimeout(r, 900));

    const newAcc = Math.min(0.96, Math.max(0.1, +(parent.performance.accuracyScore + chosenMutation.accDelta).toFixed(2)));
    const totalSub = 50;
    const resolved = Math.round(newAcc * totalSub);
    const unresolved = totalSub - resolved;
    const emptyPatch = Math.max(0, parent.performance.totalEmptyPatch - 1);

    addLog(`Evaluation completed! Accuracy: ${(newAcc * 100).toFixed(1)}% (${resolved}/${totalSub} resolved).`);
    addLog(`Candidate ${newId} verified & added to archive!`);

    const newNode: AgentNode = {
      id: newId,
      parentId: parent.id,
      generation: nextGen,
      title: chosenMutation.title,
      description: chosenMutation.desc,
      mutationType: chosenMutation.type,
      patchDiff: chosenMutation.diff,
      candidateSha256: Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
      configSha256: Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
      performance: {
        accuracyScore: newAcc,
        totalSubmitted: totalSub,
        totalResolved: resolved,
        totalUnresolved: unresolved,
        totalEmptyPatch: emptyPatch,
        hallucinationScore: Math.min(2.0, +(parent.performance.hallucinationScore + 0.15).toFixed(2)),
        percentToolUtilized: Math.min(1.0, +(parent.performance.percentToolUtilized + 0.05).toFixed(2)),
      },
      timestamp: new Date().toISOString(),
      status: 'active',
      attributes: {
        model: 'gpt-4o',
        temperature: 0.2,
        toolsUsed: ['bash', 'edit'],
        contextTokens: 9200,
        promptTokens: 48000 + nextGen * 2000,
        completionTokens: 11000 + nextGen * 800,
      },
    };

    setNodes((prev) => [...prev, newNode]);
    setSelectedNode(newNode);
    setTargetParent(null);
    setIsRunning(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        engine={config.engine}
        setEngine={(eng: EngineType) => handleUpdateConfig({ engine: eng })}
        activeGeneration={activeGeneration}
        totalAgents={nodes.length}
        bestAccuracy={bestAccuracy}
        onOpenRunner={() => setIsRunnerOpen(true)}
        onOpenProvenance={() => setIsProvenanceOpen(true)}
        onReset={handleReset}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="flex-1 max-w-7xl mx-auto w-full p-4 md:p-6 space-y-6">
        {/* Navigation Content */}
        {activeTab === 'lineage' && (
          <LineageGraph
            nodes={nodes}
            selectedNodeId={selectedNode?.id || null}
            onSelectNode={(node) => setSelectedNode(node)}
            onSpawnChild={handleSpawnChild}
          />
        )}

        {activeTab === 'benchmarks' && (
          <BenchmarkExplorer instances={sampleBenchmarkInstances} />
        )}

        {activeTab === 'prompts' && <PromptsAndToolsView />}
      </main>

      {/* Floating Bottom Live Telemetry Ticker */}
      <footer className="border-t border-slate-800/80 bg-slate-950/90 backdrop-blur-md px-4 py-2.5 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 truncate">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-semibold text-slate-300">Live Telemetry:</span>
            <span className="font-mono text-slate-400 truncate">
              {liveLogs[liveLogs.length - 1] || 'ECode loop idle.'}
            </span>
          </div>
          <div className="flex items-center gap-4 text-[11px] font-mono shrink-0">
            <span className="text-slate-500">Seed: {config.seed}</span>
            <span className="text-slate-500">Benchmark: {config.benchmark}</span>
            <span className="text-indigo-400 font-semibold">{config.engine.toUpperCase()} Engine</span>
          </div>
        </div>
      </footer>

      {/* Modals */}
      <AgentDetailModal
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
        onSpawnChild={handleSpawnChild}
      />

      <EvolutionRunner
        isOpen={isRunnerOpen}
        onClose={() => setIsRunnerOpen(false)}
        config={config}
        onUpdateConfig={handleUpdateConfig}
        onRunGeneration={runEvolutionStep}
        isRunning={isRunning}
        targetParent={targetParent}
        onClearTargetParent={() => setTargetParent(null)}
        liveLogs={liveLogs}
      />

      <ProvenanceModal
        isOpen={isProvenanceOpen}
        onClose={() => setIsProvenanceOpen(false)}
        nodes={nodes}
        config={config}
      />
    </div>
  );
}
export default App;
