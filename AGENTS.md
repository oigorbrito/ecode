# AGENTS.md

## Purpose

This repository is ECode. Read `docs/ROADMAP.md` before material architecture, evaluation, or agent changes.

ECode is evidence-driven. Planned mechanisms remain hypotheses until local evidence promotes them.

## Before changing the repository

1. Read `README.md`, `docs/ROADMAP.md`, `CONTRIBUTING.md`, and `SECURITY.md` when relevant.
2. Inspect the actual checked-out repository state before assuming a path, script, test command, runtime, or branch exists.
3. Search for already-preserved test, benchmark, CI, audit, and provenance evidence before rerunning work.
4. Reuse existing evidence only when its revision, runtime/model condition, workload, verifier, budget, and relevant environment identity match the current decision question.
5. Prefer the smallest reversible change that tests one hypothesis.

## Evidence semantics

```text
DOCUMENTED != EXECUTED
IMPLEMENTED != EXECUTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
IMPLEMENTED != PROMOTED
EXECUTION_AUTHORITY != ACCEPTANCE_AUTHORITY != PROMOTION_AUTHORITY
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
UPSTREAM_EVIDENCE != LOCAL_PASS
EXTERNAL_PASS != ECODE_PASS
TEST_PASS != BENEFIT_PROVEN
CLAIM_SCOPE <= EVIDENCE_SCOPE
```

Do not report `PASS` for missing, stale, inaccessible, skipped, or unexecuted evidence.

Use explicit non-pass states such as `BLOCKED`, `INCONCLUSIVE`, or the vocabulary defined by the active local harness.

## Experiment discipline

Change one mechanism at a time when attribution matters.

Before executing a test or experiment:

- inspect existing repository evidence;
- inspect relevant CI/workflow results;
- inspect preserved experiment/provenance records;
- determine whether the existing evidence already answers the same question.

```text
EXISTING_VALID_EVIDENCE != RETEST_REQUIRED
```

Rerun only when evidence is missing, incompatible, stale for the decision, inconclusive, or replication is explicitly required.

Decision-bearing comparisons should record enough identity to reproduce the condition, including as applicable:

- ECode revision;
- model/runtime identity;
- hardware;
- dataset/workload;
- random seed;
- verifier;
- budget and timeout;
- repetitions;
- artifact hashes.

A single successful run is insufficient evidence of a general gain when stochastic behavior is material.

## Runtime and safety

Fail closed.

```text
SANDBOX_REQUESTED
+
SANDBOX_UNAVAILABLE
=
BLOCKED
```

Do not silently substitute host execution, a different model/runtime, a different verifier, a different workload, or a weaker safety boundary in a decision-bearing experiment.

Malformed tool calls, no-op edits, path-resolution failures, timeouts, and verifier feedback loops must be classified rather than hidden.

## Testing

Use only test and verification commands that actually exist in the checked-out revision.

Before claiming a change is ready:

- run the smallest relevant tests first;
- run broader regression when practical;
- preserve commands and outcomes;
- distinguish infrastructure failure from candidate failure.

If the current revision does not contain an executable harness, do not claim that a canonical harness command was run.

## Roadmap control

The roadmap may retain future phases before they are implemented.

Do not remove a planned mechanism merely because it has not yet been tested. Gate implementation on empirical qualification.

Change phase ordering only when evidence shows that a prerequisite, risk, or measured failure mode invalidates the previous order.

## Scope control

Do not add expensive mechanisms merely because they are common in agent systems.

```text
MORE_FEATURES != BETTER_PRODUCT
```

Complexity must earn the right to remain.

## Reusable development workflows

- Repository-scoped Codex skills live in `.codex/skills/`; see [`docs/DEVELOPMENT-AGENTS.md`](docs/DEVELOPMENT-AGENTS.md) for their scope, specialized development roles, handoff contract, and qualification policy.
- Invoke a skill only when its description matches the task. Skills and role descriptions are guidance; they do not grant execution, acceptance, or promotion authority.

## Local implementation guidance

- ECode is an experimental Python system for evolutionary coding agents. Main areas are `coding_agent.py`, `ecode.py`, `ecode_core/`, `swe_bench/`, `polyglot/`, `tools/`, and `tests/`.
- Python support and CI target Python 3.10. Verify the actual runtime and workflow before attributing a check to CI.
- Follow the existing module structure and keep changes focused on the requested behavior.
- Treat model-generated code, patches, benchmark repositories and model output as untrusted. Preserve Docker isolation; do not execute generated code directly on the host.
- Do not version credentials, local caches, generated benchmark output or `.provenance/` artifacts.
- Use Git from the checkout's owning environment. For the WSL worktree, use Linux Git. Windows Git is appropriate for native Windows checkouts and isolated clones with their own `.git` directory; do not point it at WSL-managed worktree metadata.
- Preserve pending experimental changes. Commit, merge, publication and promotion require explicit user authorization.
- Unit tests do not qualify a model/provider, benchmark or performance claim. Fixture passes retain their fixture scope.

Existing code-validation commands are:

```bash
ruff check .
python -m compileall -q analysis coding_agent.py coding_agent_polyglot.py ecode.py llm.py llm_withtools.py self_improve_step.py swe_bench polyglot prompts tools utils test_swebench.py
python -m pytest -q
```

In the WSL worktree, use its `.venv/bin/python` when appropriate. Report commands and outcomes, including checks not run or blocked by Docker, credentials or data. For documentation-only changes, review references and `git diff --check`; do not rerun model experiments or benchmarks to validate prose.
