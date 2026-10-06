# AGENTS.md

## Purpose

This repository is ECode. Read `ROADMAP.md` before material architecture, evaluation, or agent changes.

ECode is evidence-driven. Planned mechanisms remain hypotheses until local evidence promotes them.

## Before changing the repository

1. Read `README.md`, `ROADMAP.md`, `CONTRIBUTING.md`, and `SECURITY.md` when relevant.
2. Inspect the actual checked-out repository state before assuming a path, script, test command, runtime, or branch exists.
3. Search for already-preserved test, benchmark, CI, audit, and provenance evidence before rerunning work.
4. Reuse existing evidence only when its revision, runtime/model condition, workload, verifier, budget, and relevant environment identity match the current decision question.
5. Prefer the smallest reversible change that tests one hypothesis.

## Evidence semantics

```text
DOCUMENTED != EXECUTED
IMPLEMENTED != PROMOTED
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
