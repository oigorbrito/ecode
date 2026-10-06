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
