# ECode — Empirical Engineering Roadmap

## Purpose

ECode evolves by controlled, evidence-bearing changes.

The roadmap records hypotheses, experiment order, and promotion gates. A planned mechanism is not considered implemented or accepted until it passes local qualification.

Core rules:

```text
EXTERNAL_RESULT != ECODE_RESULT
IMPLEMENTED != PROMOTED
TEST_PASS != BENEFIT_PROVEN
```

## Universal qualification chain

```text
IDENTIFY MECHANISM
      ↓
REVIEW EXISTING EVIDENCE
      ↓
ELIGIBLE_FOR_LOCAL_TEST
      ↓
REGISTER HYPOTHESIS
      ↓
FREEZE BASELINE
      ↓
IMPLEMENT BEHIND REMOVABLE BOUNDARY
      ↓
CONTROLLED COMPARISON
      ↓
REPEATED RUNS
      ↓
REGRESSION + HELD-OUT
      ↓
ENGINEERING ECONOMY
      ↓
KEEP / REJECT / INCONCLUSIVE
      ↓
PROMOTION
```

Before rerunning any test, benchmark, qualification, or comparison, first search the repository, CI history, audit records, and preserved provenance for already-valid evidence. Reuse matching evidence when it answers the same decision question.

```text
EXISTING_VALID_EVIDENCE != RETEST_REQUIRED
```

Rerun only when evidence is missing, incompatible with the current condition, stale for the decision being made, inconclusive, or when replication is itself the objective.

## Decision criteria

A mechanism survives only when verified benefit justifies total engineering cost.

Record, as applicable:

- verified task quality;
- repeated-run variance;
- held-out/generalization behavior;
- regressions;
- input/output tokens;
- wall-clock;
- runtime cost;
- RAM/VRAM;
- retries/timeouts;
- dependencies;
- LOC and coupling;
- removability;
- recovery behavior;
- maintenance burden.

Use Pareto-style reasoning when dimensions conflict.

## Wave 0 — Operational baseline

Goal:

```text
ECODE-B0 =
reproducible baseline
+ local runtime
+ fail-closed execution
+ reliable tool/edit loop
+ preserved evidence
```

Mandatory gates:

1. **Fail-closed execution**

```text
SANDBOX_REQUESTED
+
SANDBOX_UNAVAILABLE
=
BLOCKED
```

2. **Local runtime qualification**

Qualify the supported local execution path before adding alternative provider layers.

3. **Environment identity**

Decision-bearing runs record model/runtime identity, hardware, workload, random seed, budget, timeout, verifier and artifact digests.

4. **Reliable model/tool/edit loop**

Controlled real-repository repair must be sufficiently repeatable that malformed calls, no-op edits, path errors, timeouts or verifier feedback loops do not dominate later experiments.

5. **Reproducible end-to-end cycle**

The complete candidate → execution → verification → score/result → persisted evidence path must be reproducible.

## Wave 1 — Search simplification

Compare the baseline search/orchestration mechanism with a smaller candidate search mechanism while holding the rest of the system constant.

Promote only if repeated evidence improves the local Pareto frontier in quality, generalization, cost, latency, or complexity.

## Wave 2 — Runtime and harness mechanisms

Test one mechanism at a time.

Candidate classes include:

- context management / compaction;
- tool/control policy;
- checkpoint/recovery;
- trajectory persistence;
- other mechanisms tied to measured failure modes.

The internal order is evidence-driven. The dominant observed failure mode determines the next experiment.

## Wave 3 — Configuration search

Only after several individual mechanisms have independently passed local qualification.

The configuration search procedure is itself an experimental mechanism and must justify its own overhead.

## Wave 4 — Conditional architecture selection

Precondition:

```text
MULTIPLE_QUALIFIED_MECHANISMS = TRUE
```

Compare one global architecture against task-conditioned selection.

Measure solve rate, cost, latency, routing errors, selector overhead, regressions, and held-out generalization.

## Later expensive mechanisms

Memory, multi-agent coordination, reinforcement learning, co-evolution, and complex routing remain hypotheses, not commitments.

```text
NO_MEASURED_MEMORY_PROBLEM
=
NO_MEMORY_SYSTEM
```

Higher-cost mechanisms require proportionally stronger evidence.

## Experiment discipline

Each experiment should preserve:

```yaml
mechanism:
  name:
  rationale:
hypothesis:
  expected_effect:
baseline:
  revision:
  configuration:
candidate:
  revision:
  configuration:
protocol:
  repetitions:
  held_out:
  verifier:
  budget:
results:
  quality:
  variance:
  held_out:
  tokens:
  runtime:
  memory:
  regressions:
  complexity:
decision:
  KEEP | REJECT | INCONCLUSIVE
```

## Promotion rule

```text
PLANNED
→ ELIGIBLE_FOR_TEST
→ EXPERIMENTAL
→ KEEP / REJECT / INCONCLUSIVE
→ PROMOTED
```

Only `KEEP` may be promoted.

## Product objective

```text
THE SMALLEST ARCHITECTURE
THAT DELIVERS THE HIGHEST
VERIFIED ENGINEERING CAPABILITY
AT ACCEPTABLE TOTAL COST
```

Complexity must earn the right to remain.

## Local reconciliation — 2026-10-06

This roadmap incorporates the public plan from `origin/docs/empirical-migration-roadmap`, revision `3c0046724c3535ef7647866da8abc3c6d3c9317e`. That plan is on a separate remote branch; `origin/main` at `1ee97e9773aa183fcaaac9ad7f0e6d73c4727d87` still contains the repository template.

The active local worktree is `/mnt/d/projetos/ecode/ecode-wsl`, branch `baseline/ecode-bootstrap`, base HEAD `704d666e4f97bb08e841641d35582602e33c4611`. Experimental implementation changes remain uncommitted and require review. This documentation update does not promote them.

| Gate or boundary | Preserved evidence | Scope / consequence |
|---|---|---|
| Fail-closed execution | Docker isolation and blocked-execution contracts implemented locally | Generated code must not execute on the host; infrastructure availability is run-specific. |
| Real-model orchestration | `SELF_IMPROVE_ORCHESTRATION_WITH_REAL_MODEL = PASS` | Controlled synthetic fixture only; actual selection, mutation, candidate, evaluator, archive, lineage and post-evaluation selection. |
| Protocol reliability | `LOCAL_MUTATION_PROTOCOL_RELIABILITY_WITH_REAL_MODEL = PASS`; `MUTATION_LOOP_WITH_REAL_MODEL = PASS` | Five controlled synthetic fixture runs, each with two generations; does not establish real-repository repair reliability. |
| Real-repository repair baseline | `CONTROLLED_REAL_REPOSITORY_REPAIR_WITH_REAL_MODEL = FAIL` | 0/5 verified repairs. |
| Localized editing experiment | `LOCALIZED_REAL_REPOSITORY_REPAIR_WITH_REAL_MODEL = FAIL` | 0/5 verified repairs after three attempts per case; actual edits occurred, but no repair passed the independent verifier. |
| Regression | Preserved report: `133 passed, 3 warnings` | Historical validation of the experimental code snapshot; not a new test execution for this documentation update and not evidence of capability gain. |
| CLI integration | `legacy` remains the production default; `dgm` remains provider-free fixture-only | Real adapter qualification in an experimental harness does not establish production CLI migration. |
| Benchmark / performance | `BENCHMARK = NOT_EXECUTED`; `PERFORMANCE_GAIN = NOT_PROVEN` | No SWE capability claim. |
| Promotion | No commit, candidate merge or promotion performed by these gates | Execution, acceptance and promotion are separate authorities. |

### Evidence identity

The evidence below is local and ignored by Git; it is not distributed with this documentation. Missing local artifacts must not be reported as a fresh verified pass.

- `.provenance/self-improve-orchestration-real-model-2026-10-06/final-report.json`
- `.provenance/local-mutation-protocol-reliability-2026-10-06/final-report.json`
- `.provenance/controlled-real-repository-repair-2026-10-06-rerun-04/final-report.json`
- `.provenance/localized-real-repository-repair-2026-10-06-phase-02/completion-report.json`
- Localized experiment snapshot SHA-256: `1ad0864238017b4ef07c93524d07149d465904af01fc4a32e7a30e7e52d3c0a6`.

The localized report records 17 materialized localized edits, 72 editor errors, 7 timeouts and two candidates whose independent evaluations scored zero. Its read-only provider observation recorded `qwen2.5-coder:3b`, Q4_K_M, with 4,096 loaded context tokens versus 32,768 declared model context. Actual token usage and truncation markers were not captured; context truncation remains unproven.

### Current position and next gate

`WAVE_0 = NOT_COMPLETE`. Synthetic end-to-end success does not satisfy the mandatory reliable real-repository repair gate. `ECODE_B0` is not qualified for decision-bearing search comparisons yet.

The next recommended experiment is explicit comparative local model/runtime qualification, with pinned effective context, the same defects and independent verifiers, and declared budgets. Reuse the existing observations first; any different executor must be explicit. This recommendation does not execute or authorize a model download, a new battery, a benchmark or promotion.

#### Executor pending; offline work continues — 2026-10-06

At the user's request, executor qualification is pending. Docker is installed; the preserved alternate-condition run-08 stopped on `docker-credential-desktop.exe` during image-build preparation. This is a run-specific infrastructure failure and does not demonstrate that Docker is absent. Source identity drift in other preparation attempts remains a separate issue.

`LOCALIZED_REPAIR_ALTERNATE_MODEL_CONDITION = PARTIALLY_VERIFIED`: the preserved condition pins `deepseek-coder:1.3b-instruct`, but contains no completed generation response or verified repair. These runs do not qualify that condition or compare its repair capability with the earlier model.

Offline evidence reconciliation continues while executor qualification is pending. Two replays of seven preserved reports and their observer traces produced byte-identical outputs (SHA-256 `dcd0dc2276a154856fb1390a3cbd7f62b87d5153f6ade630b968f2da528be14b`). Run-01 records 15 LLM-function starts, 15 import errors, and zero completions; runs 02–04 record no LLM-function starts. A function start does not prove a provider request was sent, and zero completions does not mean zero attempted calls.

Local evidence: `.provenance/offline-executor-evidence-2026-10-06/`, including the reconciliation script, both outputs, source report/trace hashes, and ordered event references. Original classifications remain preserved. This is offline audit evidence, not a model, executor, benchmark, or performance pass.

The next independent step is passive observability qualification: distinguish function entry, provider request dispatch, response completion, and local failure; preserve missing token/context fields explicitly. Reuse frozen traces for offline checks. Any real-runtime confirmation and model comparison remain pending executor qualification. Agent-behavior mechanisms and decision-bearing search comparisons retain their existing prerequisites.

Offline qualification of the existing passive telemetry is `PARTIALLY_VERIFIED`. Test doubles cover request/return preservation for a successful observer and explicit unknown token/context states. Inspection and a regression case preserve a remaining failure mode: a usage-callback exception can prevent delivery of an already obtained response. Independent provider transport markers are also absent from the frozen traces. Resolve observer-failure isolation as a single subsequent mechanism, with explicit error evidence; retain real-runtime confirmation as pending. See [EXPERIMENT-HARNESS.md](EXPERIMENT-HARNESS.md) for the scoped qualification limits.

The subsequent observer-failure isolation implementation preserves received responses when usage-event construction or delivery raises an ordinary exception. An independent structured error records the failure stage and exception type; the failing callback is not invoked again. Offline checks cover completion delivery, absence of observer-induced retries, tool-response identity and process interrupts. Evidence lives under `.provenance/observer-failure-isolation-offline-2026-10-06/`. This does not qualify real provider transport, runtime capture, repair capability or performance; executor qualification remains pending.

The next offline step adds optional SDK/HTTP boundary observation to the generic local adapter. It distinguishes SDK call entry/return/error from HTTP request preparation and received response headers. Preparation does not prove provider receipt; headers do not establish completion success. The default path remains uninstrumented. Qualification uses the installed SDK with an in-memory mock transport and evidence under `.provenance/sdk-http-boundary-offline-2026-10-06/`; activation in the harness, concurrent-call attribution, and real-runtime confirmation remain unverified. See [EXPERIMENT-HARNESS.md](EXPERIMENT-HARNESS.md) for the event contract.

`SDK_HTTP_BOUNDARY_OFFLINE = PASS` is restricted to `openai 3.24.0` / `httpx2 2.13.1` with mock transport: success, retry, connection failure and observer failure preserve requests and outcomes. Local regression passed with `161 passed, 3 warnings`. The next evidence task is opt-in capture of these events in the controlled harness, qualified offline before any real activation. Executor qualification and real model/runtime comparison remain pending.

Wave 1 search simplification and later donor mechanisms remain planned. Advance after an adequate operational baseline exists. Keep donor pins and source/license records in `docs/donors/`; no donor gains are local results.

For earlier donor-specific plans and dated bootstrap observations, see [ROADMAP-BOOTSTRAP-HISTORY.md](ROADMAP-BOOTSTRAP-HISTORY.md) and [BOOTSTRAP-CHECKPOINT.md](BOOTSTRAP-CHECKPOINT.md). Those documents are historical evidence, not current status.


## Development workflow: skills and specialized roles

Repository development uses narrow, repo-scoped Codex skills for evidence reconciliation, controlled experiments, and donor mechanism review. Read [DEVELOPMENT-AGENTS.md](DEVELOPMENT-AGENTS.md) for role boundaries, handoffs, and the proposed qualification pilot. These assets guide development; they are not ECode runtime features and have not been evaluated for productivity or repair gains.

The order is deliberate: apply the evidence and protocol skills first, and use an independent, read-only review on tasks where acceptance depends on inspecting implementation or experiment evidence. The investigator, implementer, and verifier are workflow responsibilities, not concurrent agents by default. Evaluate delegated or parallel agent work only later, and only for tasks with demonstrably separable scope and a frozen task set, controls, trace fields, and acceptance criteria. This is a development-discipline sequence; it does not presume or claim an ECode capability, productivity, or repair gain.

The controlled-repair experiment harness is a separate development-infrastructure item. Its reusable runner and input/output boundary are documented in [EXPERIMENT-HARNESS.md](EXPERIMENT-HARNESS.md). Keep changes that steer model behavior out of the harness consolidation; qualify each such mechanism in its own controlled comparison.

Keep the authority boundaries explicit throughout:

```text
EXECUTION_AUTHORITY != ACCEPTANCE_AUTHORITY != PROMOTION_AUTHORITY
IMPLEMENTED != EXECUTED != VERIFIED != ACCEPTED
CLAIM_SCOPE <= EVIDENCE_SCOPE
```
