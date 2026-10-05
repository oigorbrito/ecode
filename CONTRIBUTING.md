# Contributing

## Contribution process

1. Open or reference an issue when the change is non-trivial.
2. Work on a branch rather than committing directly to the primary branch.
3. Keep changes scoped and reviewable.
4. Add or update tests when behavior changes.
5. Run the checks relevant to the change. The current project checks are:

```bash
ruff check .
python -m compileall -q analysis coding_agent.py coding_agent_polyglot.py ecode.py llm.py llm_withtools.py self_improve_step.py swe_bench polyglot prompts tools utils test_swebench.py
python -m pytest -q
```

6. Open a pull request describing the change and the evidence executed.
7. Do not report a check as passed unless it was executed on the current change.

## Acceptable contributions

Changes should preserve documented interfaces and invariants, avoid introducing generated binaries into source control, and keep dependency changes explicit and reviewable.

## Test policy

Do not report provider-backed or benchmark qualification from unit tests alone. Docker, provider credentials, local model availability, benchmark data, and hosted CI are separate evidence scopes; report each as `NOT_RUN`, `BLOCKED`, or `PASS_WITH_SCOPE` as appropriate.
