---
name: ecode-evidence-reconciliation
description: Reconcile existing ECode gate, test, CI, and provenance evidence when reports conflict or a status must be updated.
---

# ECode evidence reconciliation

Use only for read-only evidence reconciliation and scoped status reporting.

1. Identify the worktree, branch, HEAD, dirty state, and evidence/run identity. Do not assume artifacts from different run identities describe one execution.
2. Locate existing reports, raw traces, hashes, and relevant code/tests before proposing another run. Do not rerun tests, models, or benchmarks unless the user asks or evidence is incompatible with the decision.
3. Map every requested claim to a concrete artifact and field. Distinguish upstream evidence, implementation, execution, verification, acceptance, and promotion.
4. Compare contradictory reports as separate records. Preserve each source's original classification; do not average or silently overwrite them.
5. Report missing/incompatible evidence as unknown, blocked, partial, or not run using the gate's vocabulary. Never infer a pass from an absent artifact.
6. Preserve authority boundaries and claim scope. Report no benchmark/performance/SWE capability unless the exact evidence supports it.

Output: run identity; claim-to-evidence mapping; discrepancies; canonical scoped status; current Git state; next decision gate. Make no repository edits.
