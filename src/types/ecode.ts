export type EngineType = 'dgm' | 'legacy';
export type ParentSelector = 'dgm-weighted' | 'score-prop' | 'best-score' | 'random';
export type RetentionPolicy = 'keep-all' | 'keep-last';
export type BenchmarkType = 'swe-bench' | 'polyglot' | 'offline-fixture';

export interface ArtifactRef {
  path: string;
  sha256: string;
  mediaType: string;
}

export interface EvaluationPerformance {
  accuracyScore: number;
  totalSubmitted: number;
  totalResolved: number;
  totalUnresolved: number;
  totalEmptyPatch: number;
  hallucinationScore: number;
  percentToolUtilized: number;
}

export interface AgentNode {
  id: string; // e.g. "initial", "commit-a7f2", etc.
  parentId: string | null;
  generation: number;
  title: string;
  description: string;
  mutationType: 'baseline' | 'tool_protocol' | 'prompt_diagnosis' | 'localized_edit' | 'context_guard' | 'error_recovery';
  patchDiff: string;
  candidateSha256: string;
  configSha256: string;
  performance: EvaluationPerformance;
  timestamp: string;
  status: 'active' | 'archived' | 'failed';
  attributes: {
    model: string;
    temperature: number;
    toolsUsed: string[];
    contextTokens: number;
    promptTokens: number;
    completionTokens: number;
  };
}

export interface BenchmarkInstance {
  instanceId: string;
  repo: string;
  version: string;
  problemStatement: string;
  baseCommit: string;
  resolvedByAgent: boolean;
  emptyPatch: boolean;
  execTimeSec: number;
  testsPassed: number;
  testsTotal: number;
  logs: string[];
}

export interface RunConfig {
  engine: EngineType;
  benchmark: BenchmarkType;
  parentSelector: ParentSelector;
  retention: RetentionPolicy;
  archiveLimit: number;
  seed: number;
  mutationBatchSize: number;
  maxGenerations: number;
  timeoutSec: number;
  failClosedDocker: boolean;
  localOpenAiUrl: string;
  ollamaBaseUrl: string;
}

export interface TelemetryLog {
  timestamp: string;
  level: 'info' | 'warn' | 'evidence' | 'mutation' | 'eval';
  message: string;
  agentId?: string;
  generation?: number;
}
