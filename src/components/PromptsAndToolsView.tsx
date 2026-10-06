import React from 'react';
import { promptTemplates, toolDefinitions, PromptTemplate } from '../data/promptsAndTools';
import { FileCode, Wrench, Terminal, Copy, Check, Save } from 'lucide-react';

export const PromptsAndToolsView: React.FC = () => {
  const [prompts, setPrompts] = React.useState<PromptTemplate[]>(promptTemplates);
  const [selectedPrompt, setSelectedPrompt] = React.useState<PromptTemplate>(promptTemplates[0]);
  const [copied, setCopied] = React.useState(false);
  const [saved, setSaved] = React.useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleUpdateCode = (newCode: string) => {
    const updated = prompts.map((p) =>
      p.filename === selectedPrompt.filename ? { ...p, code: newCode } : p
    );
    setPrompts(updated);
    setSelectedPrompt({ ...selectedPrompt, code: newCode });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Prompts Section */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <div>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileCode className="w-4 h-4 text-purple-400" />
              Agent Prompt Architecture
            </h2>
            <p className="text-xs text-slate-400">
              System prompts that guide the coding agent and the meta-evolutionary self-improvement mutator.
            </p>
          </div>
          {saved && (
            <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium animate-fade-in">
              <Check className="w-3.5 h-3.5" /> Prompt updated in memory
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Prompt Selector */}
          <div className="lg:col-span-4 space-y-2">
            {prompts.map((p) => {
              const isSelected = selectedPrompt.filename === p.filename;
              return (
                <div
                  key={p.filename}
                  onClick={() => setSelectedPrompt(p)}
                  className={`p-3 rounded-lg border transition-all cursor-pointer text-xs ${
                    isSelected
                      ? 'border-indigo-500 bg-slate-800/90 shadow-md ring-1 ring-indigo-500/40'
                      : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                  }`}
                >
                  <h3 className="font-semibold text-slate-200 mb-1">{p.name}</h3>
                  <code className="text-[11px] text-indigo-400 font-mono block mb-1">
                    {p.filename}
                  </code>
                  <p className="text-[11px] text-slate-400 line-clamp-2">
                    {p.description}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Prompt Editor */}
          <div className="lg:col-span-8 bg-slate-950 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
            <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs">
              <span className="font-mono text-slate-300 font-medium">
                {selectedPrompt.filename}
              </span>
              <button
                onClick={() => handleCopy(selectedPrompt.code)}
                className="flex items-center gap-1 text-slate-400 hover:text-white cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
            <textarea
              value={selectedPrompt.code}
              onChange={(e) => handleUpdateCode(e.target.value)}
              className="w-full h-80 p-4 bg-transparent font-mono text-xs text-slate-200 resize-none focus:outline-none leading-relaxed"
              spellCheck={false}
            />
          </div>
        </div>
      </div>

      {/* Tools Section */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
        <div className="pb-4 mb-4 border-b border-slate-800">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Wrench className="w-4 h-4 text-cyan-400" />
            Active Agent Tools Contract
          </h2>
          <p className="text-xs text-slate-400">
            Available primitives provided to LLM during autonomous issue resolution.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {toolDefinitions.map((tool) => (
            <div key={tool.name} className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono font-bold text-sm text-cyan-400 flex items-center gap-1.5">
                  <Terminal className="w-4 h-4 text-indigo-400" />
                  {tool.name}()
                </span>
                <span className="font-mono text-[11px] text-slate-500">{tool.path}</span>
              </div>
              <p className="text-slate-300 mb-3">{tool.description}</p>
              <div className="space-y-1.5 border-t border-slate-800/80 pt-2.5">
                <span className="font-semibold text-slate-400 block text-[11px] uppercase tracking-wider">
                  Parameters:
                </span>
                {tool.parameters.map((param) => (
                  <div key={param.name} className="flex items-start gap-2 text-[11px]">
                    <code className="text-indigo-300 font-mono bg-indigo-950/40 px-1 py-0.5 rounded">
                      {param.name}
                    </code>
                    <span className="text-slate-500 font-mono">({param.type})</span>
                    <span className="text-slate-400">— {param.description}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
