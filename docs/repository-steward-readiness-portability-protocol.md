# Repository Steward readiness portability protocol — ECode

## Purpose

Qualify the existing GitHub-native Repository Steward readiness bundle on ECode without changing classifier semantics or granting write authority.

This protocol is frozen before implementation. The reusable source is the accepted Searchleads target state recorded by NDV PR #71 and Searchleads evidence commit `450243c4de7223db5d2e0b10de737de403520d3d`.

## Scope

Install the seven readiness files from the accepted Searchleads target:

- five shell scripts under `.github/scripts/`;
- `.github/workflows/repository-steward-readiness-classifier-tests.yml`;
- `.github/workflows/repository-steward-readiness-observer.yml`.

The intended installation is byte-for-byte reuse of those seven files. No ECode-specific classifier change is authorized.

Authority remains:

```text
READ
REPORT
```

No automatic merge, review, rerun, issue closure, release, branch deletion, repository-rule mutation, model execution, or benchmark promotion is authorized.

## Target compatibility

ECode's native `CI` workflow runs on `pull_request`. The accepted Searchleads observer listens to completed `pull_request` or `dynamic` workflow runs through GitHub-native current-head association and excludes its own observer workflow. Therefore no workflow-name adaptation is planned.

The installation must not alter ECode application code, experiment state, roadmap ordering, executor selection, model configuration, or benchmark claims.

## Acceptance gate

1. On the literal installation PR head, the Steward classifier workflow must execute shell syntax plus the v1/v2 and association matrices.
2. Existing ECode PR checks must be inspected independently. A skipped, absent, stale, inaccessible, or pending check is not PASS.
3. Only after applicable installation checks succeed may the implementation be merged to activate the observer on the default branch.
4. After activation, open one minimal documentation-only fixture. Do not invoke the observer manually.
5. Record the exact fixture head, native source workflow run, observer run/job, association result, final native fields, and decision.
6. Verify the observer is not part of the fixture head check rollup.
7. Close the fixture without merge and retain its branch.
8. Accept only executed target observations. Uninduced states remain NOT_PROVEN.

## Decision semantics

A positive v2 report requires the existing frozen ensemble:

```text
state=OPEN
isDraft=false
mergeStateStatus=CLEAN
mergeable=MERGEABLE
statusCheckRollup=SUCCESS
reviewDecision=APPROVED or native null normalized to NONE
```

Missing, malformed, stale, uncertain, or mismatched-head data remains fail-closed.

## Evidence boundary

```text
PROTOCOL = FROZEN
IMPLEMENTATION = NOT_IMPLEMENTED at freeze
TARGET_SYNTHETIC_MATRICES = NOT_EXECUTED
TARGET_NATIVE_AUTOMATION = NOT_PROVEN
TARGET_ACCEPTANCE = PENDING_EXECUTION
```

Upstream NDV/RJ/Searchleads results are source evidence only and do not constitute an ECode PASS.
