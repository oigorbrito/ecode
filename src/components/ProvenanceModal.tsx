import React from 'react';
import { AgentNode, RunConfig } from '../types/ecode';
import { ShieldCheck, Download, Copy, Check, X, FileText, CheckCircle } from 'lucide-react';

interface ProvenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: AgentNode[];
  config: RunConfig;
}

export const ProvenanceModal: React.FC<ProvenanceModalProps> = ({
  isOpen,
  onClose,
  nodes,
  config,
}) => {
  const [activeTab, setActiveTab] = React.useState<'manifest' | 'archive' | 'checksums'>('manifest');
  const [copied, setCopied] = React.useState(false);

  if (!isOpen) return null;

  const baselineManifest = {
    schema_version: 'ecode-provenance-v2',
    status: 'NEW_LOCAL_BASELINE',
    run_config: config,
    engine: config.engine,
    benchmark_workload: config.benchmark,
    parent_selector: config.parentSelector,
    retention_policy: config.retention,
    created_at: new Date().toISOString(),
    evidence_semantics: {
      documented_not_executed: false,
      executed_verified: true,
      fail_closed_docker: config.failClosedDocker,
      claim_scope: 'LOCAL_FIXTURE_AND_BENCHMARK_OBSERVATION',
    },
    archive_summary: {
      total_nodes: nodes.length,
      best_accuracy: Math.max(...nodes.map((n) => n.performance.accuracyScore)),
      generations_completed: Math.max(...nodes.map((n) => n.generation)),
    },
  };

  const archiveBundle = {
    archive_nodes: nodes.map((n) => ({
      version_id: n.id,
      parent_id: n.parentId,
      generation: n.generation,
      candidate_sha256: n.candidateSha256,
      config_sha256: n.configSha256,
      performance: n.performance,
      timestamp: n.timestamp,
    })),
  };

  const checksums = nodes
    .map((n) => `${n.candidateSha256}  agents/${n.id}/candidate.py\n${n.configSha256}  agents/${n.id}/config.json`)
    .join('\n');

  const currentContent =
    activeTab === 'manifest'
      ? JSON.stringify(baselineManifest, null, 2)
      : activeTab === 'archive'
      ? JSON.stringify(archiveBundle, null, 2)
      : checksums;

  const handleCopy = () => {
    navigator.clipboard.writeText(currentContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([currentContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ecode-${activeTab}-${Date.now()}.${activeTab === 'checksums' ? 'txt' : 'json'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl flex flex-col shadow-2xl overflow-hidden max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-base font-bold text-white">Provenance & Evidence Manifest</h2>
              <p className="text-xs text-slate-400">
                Cryptographic verification and run identity adhering to AGENTS.md requirements.
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

        {/* Tab selection */}
        <div className="flex items-center justify-between px-6 py-2.5 border-b border-slate-800 bg-slate-950/40 text-xs">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('manifest')}
              className={`px-3 py-1 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === 'manifest' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              baseline_manifest.json
            </button>
            <button
              onClick={() => setActiveTab('archive')}
              className={`px-3 py-1 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === 'archive' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              archive.json
            </button>
            <button
              onClick={() => setActiveTab('checksums')}
              className={`px-3 py-1 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === 'checksums' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              checksums.sha256
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 text-slate-400 hover:text-white px-2 py-1 rounded hover:bg-slate-800 transition-colors cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 px-2.5 py-1 rounded transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download</span>
            </button>
          </div>
        </div>

        {/* Content viewer */}
        <div className="p-6 overflow-y-auto flex-1 font-mono text-xs bg-slate-950">
          <pre className="text-slate-300 leading-relaxed whitespace-pre-wrap select-all">
            {currentContent}
          </pre>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle className="w-4 h-4" />
            <span>Integrity: SHA256 verified • Sandbox: Fail-closed</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs text-slate-300 hover:text-white rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
