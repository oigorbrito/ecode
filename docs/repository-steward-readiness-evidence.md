# Repository Steward readiness — ECode target evidence

## Decision

The Repository Steward readiness bundle is accepted on ECode for automatic GitHub-native READ/REPORT in the scope executed below.

```text
PROTOCOL = FROZEN
IMPLEMENTATION = MERGED
TARGET_SYNTHETIC_MATRICES = EXECUTED_PASS
TARGET_NATIVE_AUTOMATION = EXECUTED_PASS
TARGET_READ_REPORT_ACCEPTANCE = ACCEPTED_IN_RECORDED_SCOPE
AUTOMATIC_WRITE_AUTHORITY = NOT_GRANTED
```

This does not qualify any ECode model, executor, benchmark, repair capability, release, or performance claim.

## Source and implementation

- Reuse source evidence: Searchleads commit `450243c4de7223db5d2e0b10de737de403520d3d`, as registered by NDV PR #71.
- Frozen ECode protocol: PR #9, merged as `af78b3ef03a2c744ac3a9a7379b05c7846d45a4f`.
- ECode installation PR: #10.
- Exact installation head: `792b0c26df19863936d3774a9e1b8a16370f7772`.
- Activated default-branch merge: `55155cf17ebbd400a4e223600ff7ba57fe017ee4`.

All seven readiness files were reused from the accepted Searchleads target state. No ECode-specific classifier or observer logic was added.

## Installation execution

Repository Steward classifier run `37546001479`, job `112550049075`, checked out the literal installation head and recorded:

```text
TESTED_HEAD=792b0c26df19863936d3774a9e1b8a16370f7772
CLASSIFIER_MATRIX=PASS
CLASSIFIER_V2_MATRIX=PASS
RUN_ASSOCIATION_MATRIX=PASS
```

The existing ECode application CI run `37546001270`, job `112550048484`, completed successfully on the same installation head. The repository's additional lightweight CI run `37546001245` also completed successfully.

## Automatic native fixture

Fixture PR #11 was opened without a manual readiness comment.

- exact fixture head: `0bf6e5899480e6b0943d0c59031fa3666313bd2c`;
- source CI run: `37546086790`;
- automatic observer run: `37546130410`;
- observer job: `112550471585`.

The observer associated the completed source run to the current open PR:

```text
ASSOCIATION source_run=37546086790 source_head=0bf6e5899480e6b0943d0c59031fa3666313bd2c pr=11
```

Its first native query recorded:

```text
state=OPEN
draft=false
mergeStateStatus=CLEAN
mergeable=MERGEABLE
reviewDecision=NONE
checks=SUCCESS
base=main
head=test/steward-readiness-native-fixture
head_sha=0bf6e5899480e6b0943d0c59031fa3666313bd2c
decision=READY_FOR_MERGE_CANDIDATE
protocol=v2
attempt=0
```

The fixture head check rollup contained exactly three successful jobs:

- `Tests and static checks` — job `112550326387`;
- `classifier` — job `112550325825`;
- `build` — job `112550325706`.

The Repository Steward observer job was absent from the fixture head check rollup because it executed from the activated default-branch workflow.

Fixture PR #11 was closed without merge. Its branch was retained.

## Evidence boundary

This accepts only the executed ECode target conditions above. Draft, conflict, blocked, behind, review veto, malformed response, API error, head change during reread, and exhausted pending-budget cases were not induced natively on ECode and receive no new target-native PASS.

The existing synthetic classifier coverage remains separately attributable. READ/REPORT acceptance grants no automatic merge, review, rerun, issue closure, release, branch deletion, repository-rule mutation, or promotion authority.
