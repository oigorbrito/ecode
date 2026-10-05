# ECode bootstrap checkpoint

Status: `BOOTSTRAP_CHECKPOINT`, not `ECODE_B0`.

## Source identity

- Canonical repository: `https://github.com/oigorbrito/ecode`
- Parent commit: `982b0b34c84ace34d638c574c2ba5221b8dd4cdd` (`origin/main` at checkout)
- Working branch: `baseline/ecode-bootstrap`
- DGM source pin considered: `c885363a59681cb8589fcc2ad5bde4eb3915140e`; see `docs/donors/dgm.yaml`.
- ECode changes in this checkpoint are the local workspace snapshot plus the roadmap/governance reconciliation. The DGM mechanisms have not yet been integrated.

## Reproducible local evidence

Environment observed on 2026-10-05:

- OS: Windows (`win32`)
- Python used: 3.12.10
- Project CI target: Python 3.10; no Python 3.10 interpreter is installed in this environment.
- Dependency manifests are not pinned, so the complete benchmark/runtime environment is not frozen.

Executed checks:

| Check | Result | Scope |
|---|---|---|
| `python -m pytest -q tests/test_evolution_core.py tests/test_local_openai_compatible.py` | `8 passed` | Local tests, mocked adapter; one non-fatal pytest cache permission warning. |
| `python -m ruff check .` | `PASS` | Repository lint configuration. |
| `python -m compileall -q analysis coding_agent.py coding_agent_polyglot.py ecode.py ecode_core llm.py llm_withtools.py self_improve_step.py swe_bench polyglot prompts tools utils test_swebench.py` | `PASS` | Syntax compilation only. |
| Offline fixture, seed 7, 3 iterations, random parent, keep-all | `PASS` | No provider calls; deterministic mutation/evaluation fixture only. |

The fixture recorded `provider_calls: false`, `repository_commit_sha: null`, engine source SHA-256 `23d81b732b2b7a96e8d615dc6b0205170689e22a1eb98590612d66aace806744`, and checksum-manifest SHA-256 `6f6a896d4ab01a2f87c3bbc017bd014cda27208c5b2458fe22ff4a1c1ad054f2`. Its generated bundle is ignored under `.provenance/bootstrap-offline/`; rerun with:

```bash
python -m ecode_core.offline_fixture --output-dir .provenance/bootstrap-offline --seed 7 --iterations 3 --parent-selector random --retention keep-all
```

The fixture now records `repository_head_sha`, `repository_worktree_dirty`, and `repository_commit_sha`. It emits the commit SHA into run/evaluation records only when the source worktree is clean; a dirty tree retains HEAD as context and leaves the evaluated commit SHA null. This checkpoint predates that fix; a clean-tree run is pending the follow-up commit.

This checkpoint does not qualify any model/provider endpoint, the legacy ECode evaluator, a coding benchmark, or performance. Full test suite and real local model execution were not run. `ECODE_B0` remains pending DGM mechanism integration, a pinned dependency/runtime environment, and an end-to-end evolution cycle through the ECode evaluator.

The imported legacy source snapshot contains trailing whitespace; `git diff --cached --check` reports it across existing source files. Broad whitespace-only rewriting is deferred so the bootstrap checkpoint does not mix mechanical cleanup with the baseline integration.
