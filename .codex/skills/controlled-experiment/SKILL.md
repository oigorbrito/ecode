---
name: ecode-controlled-experiment
description: Plan or operate an explicitly authorized ECode experiment with a frozen condition, bounded budget, independent verifier, and preserved provenance.
---

# ECode controlled experiment

Use when setting up, executing, or auditing a model-backed or fixture-based ECode experiment. An explicit user request is required before model inference, benchmark execution, or other costly external execution.

1. Search existing reports and traces first; reuse them only when revision, model/runtime, workload, verifier, budget, and environment answer the same question.
2. Write the question, hypothesis, baseline, candidate condition, exact workload, independent verifier, budget, timeout, repetition limit, and terminal classifications before execution.
3. Record run identity and hashes. Preserve raw model/tool events, filesystem changes, patch, candidate identity, evaluator result, archive before/after, lineage, and selection where applicable.
4. Enforce fail-closed execution. Any unavailable sandbox, changed executor, model, verifier, or workload is explicit and classified; never fallback silently.
5. Keep `BLOCKED`/`INCOMPLETE` in history while excluding them from eligible parent selection. Keep execution, verification, acceptance, and promotion as separate states and authorities.
6. Stop at the authorized attempt budget. Do not repair model output manually and then count it as model-produced mutation.
7. Report only what the verifier and artifacts establish. A fixture pass remains fixture-scoped; tests alone do not establish performance gain.

Output: frozen protocol; run-level classifications; artifact identities; observed failures; scoped gate result; unrun checks. Never commit, merge, accept, or promote without separate explicit authorization.
