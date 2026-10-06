# Specialized agents for ECode development

## Scope

These roles support repository migration, implementation, and experiment review. They are development workflow roles; they do not add agents to ECode's runtime, alter `ecode_core` parent selection, or prove that multi-agent coding improves task success.

Use roles selectively where work can be bounded. A single agent remains the default for a cohesive small change. This follows the simplicity-first principle in Anthropic's engineering guidance and OpenAI's recommendation to evaluate workflow traces and then use repeatable eval cases ([sources](#sources)).

## Roles

| Role | Access and task | Required result |
|---|---|---|
| Repository investigator | Read-only. Locate exact code paths, current tests, historical evidence, donor source/revision, and applicable roadmap gate. | File/line or artifact references, commands already run, facts versus hypotheses, unknowns. No edits or experiments. |
| Bounded implementer | Writes only the paths and behavior explicitly assigned. Reads investigator findings but checks relevant code itself. | Minimal diff, rationale, tests actually run, known limitations. No acceptance, merge, or promotion. |
| Independent verifier | Read-only after implementation is frozen. Runs only authorized checks; inspects the diff and artifacts directly rather than relying on implementer's conclusion. | Pass/fail per criterion, reproducer/artifact identity, discrepancies, unverified items. Cannot edit the candidate. |
| Experiment operator | Executes only the frozen, explicitly authorized protocol and budget. | Immutable run identity, raw trace/artifact preservation, classifications, no implicit executor changes. Execution does not imply acceptance. |
| Integrator | Coordinates bounded handoffs, checks path conflicts, reconciles evidence, and presents the result. | Consolidated report that retains disagreements and keeps execution, verification, acceptance, and promotion separate. |

A person or agent may hold different roles across separate stages, but the verifier must not be the implementer of the candidate being verified. The integrator cannot turn execution into acceptance or promotion.

## Handoff contract

Every delegated task states:

- exact objective and in-scope files/artifacts;
- read/write/execute permissions and forbidden actions;
- base revision and dirty-worktree caveats;
- evidence/run identity to preserve;
- expected output schema and stopping condition.

The receiver reports files touched and commands run. The integrator checks the shared worktree afterward; parallel write tasks must use disjoint files or isolated worktrees. Do not delegate model/benchmark execution unless specifically authorized.

## Pilot and qualification

Start with three instruction-only repository skills under `.codex/skills/`: evidence reconciliation, controlled experiment, and donor review. They encode procedures, not product behavior. Keep each skill narrow and load it only for a matching task.

Before calling a skill or agent workflow qualified, build a small task set with positive examples, adjacent negative controls, and an explicit rubric. Capture traces/artifacts and check both outcome and process (correct invocation, required evidence fields, no forbidden execution, no authority crossing). Add efficiency only as an observed measure; do not trade away correctness for speed. Compare the workflow against the same tasks without specialization, holding model, checkout, tools, budget, and verifier constant where possible. Report invocation errors, omissions, edits/retries, time, tokens if observed, and verification outcomes separately. Do not claim improvement from role descriptions or skill creation alone.

No agent workflow benchmark is executed or qualified by adding these files. A future pilot requires its own protocol and authorization.

## Sources

- OpenAI, [Skills](https://developers.openai.com/plugins/concepts/skills): skills are reusable workflow instructions and resources; descriptions guide when they load.
- OpenAI, [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills): define measurable success, include positive and negative trigger cases, inspect traces/artifacts, and use small deterministic checks.
- OpenAI, [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals): traces capture model calls, tools, guardrails, and handoffs; repeatable datasets/evals are appropriate after behavior is understood.
- Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): distinguish predefined workflows from agents that dynamically direct tool use; start simple and add complexity where justified. This is design guidance, not independent ECode performance evidence.
