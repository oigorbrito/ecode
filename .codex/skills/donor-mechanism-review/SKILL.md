---
name: ecode-donor-mechanism-review
description: Review one external donor mechanism for possible ECode experimentation, preserving source, license, and evidence boundaries.
---

# ECode donor mechanism review

Use for one donor mechanism at a time, before porting or integrating it.

1. Identify the donor repository and exact revision. Prefer primary material: source at that revision, its license/notice, and the original paper or project report.
2. Separate the donor's reported result from independently confirmed facts and local ECode results. Record workload, verifier, model/runtime, budget, and limitations of reported evidence.
3. Describe the smallest mechanism that could be tested in ECode and its interface/dependency/maintenance costs. Do not propose importing the donor framework wholesale without a specific need.
4. State one falsifiable local hypothesis, baseline, candidate, controls, held-out/regression check, metrics, and removal path.
5. Check roadmap prerequisites and existing ECode evidence. If the baseline or operational prerequisites are not ready, mark the mechanism planned/ineligible for execution rather than executing it.
6. Do not change product code, run a benchmark, infer a license, or claim migration authorization as part of this review.

Output: pinned source; license status; evidence quality/scope; minimal mechanism; experiment proposal; dependencies/costs; risks; decision `ELIGIBLE_FOR_LOCAL_TEST`, `INELIGIBLE`, or `INCONCLUSIVE`.
