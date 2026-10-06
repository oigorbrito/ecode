export interface PromptTemplate {
  name: string;
  filename: string;
  description: string;
  code: string;
}

export const promptTemplates: PromptTemplate[] = [
  {
    name: 'Tool-Use System Prompt',
    filename: 'prompts/tooluse_prompt.py',
    description: 'Instructs the coding agent how to discover the repository structure, use bash commands, edit files with localized search/replace, and isolate test executions.',
    code: `TOOL_USE_SYSTEM_PROMPT = """You are an expert autonomous software engineer solving benchmark issues.
You have access to two tools:
1. bash(command="..."): Run shell commands inside an isolated Docker sandbox.
2. edit(file_path="...", target_content="...", replacement_content="..."): Apply precise search-and-replace changes.

Guidelines:
- Never edit entire files from scratch. Always inspect first.
- Re-run failing tests after each modification.
- Formulate an exact hypothesis before modifying source files.
- Fail closed if sandbox is unavailable.
"""`,
  },
  {
    name: 'Self-Improvement Prompt',
    filename: 'prompts/self_improvement_prompt.py',
    description: 'Instructs the meta-agent to propose architectural or algorithmic mutations to the coding agent harness based on previous run failures.',
    code: `SELF_IMPROVEMENT_SYSTEM_PROMPT = """You are mutating the ECode coding agent harness.
Given the previous generation's evaluation logs and unresolved instances:
1. Identify systemic failure modes (e.g. context length overflow, syntax regressions in editing, tool calling failures).
2. Propose a targeted code diff to tools/ or coding_agent.py.
3. Keep the change minimal, testable, and attributable.
4. Output your mutation as a unified git diff format.
"""`,
  },
  {
    name: 'Diagnostic Improvement Prompt',
    filename: 'prompts/diagnose_improvement_prompt.py',
    description: 'Guides the agent through root-cause localization by analyzing stack traces and extracting failing pytest assertions.',
    code: `DIAGNOSE_IMPROVEMENT_PROMPT = """Analyze the pytest failure log:
Extract:
- Failing assertion and expected vs received values
- The exact file and line number where the assertion failed
- Proposed surgical fix without changing the public contract or test harness
"""`,
  },
];

export interface ToolDefinition {
  name: string;
  path: string;
  description: string;
  parameters: { name: string; type: string; description: string }[];
}

export const toolDefinitions: ToolDefinition[] = [
  {
    name: 'bash',
    path: 'tools/bash.py',
    description: 'Executes commands inside the Docker sandbox container with timeout and context output capture.',
    parameters: [
      { name: 'command', type: 'string', description: 'Shell command string to execute in repository working directory' },
      { name: 'timeout_seconds', type: 'number', description: 'Execution timeout before SIGKILL (default: 60s)' },
    ],
  },
  {
    name: 'edit',
    path: 'tools/edit.py',
    description: 'Localized text replacement tool. Ensures target_content occurs exactly once in the file to prevent ambiguous edits.',
    parameters: [
      { name: 'file_path', type: 'string', description: 'Relative path to file in repo' },
      { name: 'target_content', type: 'string', description: 'Exact string snippet to match' },
      { name: 'replacement_content', type: 'string', description: 'Exact string to substitute in place' },
    ],
  },
];
