# ECode bootstrap checkpoint

Status: `BOOTSTRAP_CHECKPOINT`, not `ECODE_B0`.

## Source identity

- Canonical repository: `https://github.com/oigorbrito/ecode`
- Parent commit: `982b0b34c84ace34d638c574c2ba5221b8dd4cdd` (`origin/main` at checkout)
- Working branch: `baseline/ecode-bootstrap`
- DGM source pin considered: `c885363a59681cb8589fcc2ad5bde4eb3915140e`; see `docs/donors/dgm.yaml`.
- ECode changes are the local workspace snapshot plus the roadmap/governance reconciliation. The DGM-derived selector and Engine are integrated only in the opt-in provider-free fixture; real mutation/evaluation remain on the legacy production loop.

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

The fixture now records `repository_head_sha`, `repository_worktree_dirty`, and `repository_commit_sha`. It emits the commit SHA into run/evaluation records only when the source worktree is clean; a dirty tree retains HEAD as context and leaves the evaluated commit SHA null.

## Follow-up checkpoint verification

- Code revision exercised: `a96564ba78141d69bbe56eceefb0481e31fc6a42`
- Clean-tree fixture bundle: `.provenance/bootstrap-cli-clean/offline-fixture-seed-7-parent-random-retention-keep-all`
- `repository_worktree_dirty`: `false`; `repository_commit_sha`: `a96564ba78141d69bbe56eceefb0481e31fc6a42`
- `engine_source_sha256`: `586a4aa4a4ac9a12759410280c4ffaf06de4bebb454bee549749ecf9bf6ee70b`
- `checksums.sha256` SHA-256: `6f63539fc421a82b250f98a1fc89e8d4db87ef5237a2f80ba344d702627c3c72`
- Targeted core/adapter/CLI/selector tests: `11 passed`; Ruff and `compileall` passed.
- The main CLI exposes the offline fixture path; normal benchmark execution remains on the legacy outer loop pending the mutation/evaluation split.

This checkpoint does not qualify any model/provider generation capability, the legacy ECode evaluator, a coding benchmark, or performance. Full test suite and real local model inference were not run. `ECODE_B0` remains pending real mutation/evaluation integration, a pinned benchmark runtime, and an end-to-end evolution cycle through the ECode evaluator.

## Evaluation boundary extraction (2026-10-05)

- Added `ecode_core.legacy_evaluation.run_benchmark_evaluation` as a dependency-injected boundary from an already-produced mutation patch to the existing benchmark harness.
- `self_improve_step.evaluate_self_improve` now delegates benchmark execution through that boundary; the legacy `self_improve()` entry point remains compatible.
- The extracted boundary records missing/empty patch state, preserves `BLOCKED / SANDBOX_UNAVAILABLE`, and persists blocked metadata. It does not select parents, mutate code, call models, or authorize archive promotion.
- `ECodeEvaluator` now verifies and includes the candidate artifact in the typed result, deduplicates result artifacts, and suppresses scores for `BLOCKED` and `INCOMPLETE` outcomes.
- `Archive` retains every result in history/lineage but excludes `BLOCKED` and `INCOMPLETE` candidates from the parent-selection pool.
- Focused tests: `python -m pytest -q -p no:cacheprovider tests/test_evolution_core.py tests/test_local_openai_compatible.py` -> `17 passed`; Ruff on changed Python files -> `PASS`; `compileall` and `git diff --check` -> `PASS`.
- Scope: structural separation only. At that checkpoint, the production CLI did not run `EvolutionEngine`; no Docker sandbox, provider, real benchmark, or full-suite qualification occurred. `ECODE_B0` remains pending.

## Mutation adapter extraction (2026-10-05)

- Added `mutation_only` to the legacy `self_improve()` operation. After its existing sandboxed coding-agent step produces a nonempty patch, this mode records the patch path and SHA-256 as `MUTATION_READY` and returns without invoking the evaluator.
- Added `ECodeMutationRunner` as an injected adapter that selects a task through a callback and wraps the resulting patch in `AgentVersion`.
- `EvolutionEngine` now supports `initialize_with_result()` for a previously evaluated seed, and supplies the parent's `EvaluationResult` to each `MutationRunner`; `ECodeEvaluator.from_metadata()` maps cached ECode metadata without executing a benchmark.
- Renamed the contract hash from `source_tree_sha256` to `candidate_sha256`: the ECode mutation artifact is a patch, and calling its digest a source-tree digest would be inaccurate.
- The focused adapter tests exercise patch hashing, parent lineage, and the mutation/evaluation callback boundary. Tests do not run the Docker coding-agent path; its new mutation-only branch remains runtime-unqualified in this environment.
- Focused tests: `python -m pytest -q -p no:cacheprovider tests/test_evolution_core.py tests/test_local_openai_compatible.py` -> `20 passed`; Ruff, `compileall`, and `git diff --check` -> `PASS`.
- The ordinary CLI still uses the legacy threaded orchestration, and the adapter is not yet connected to it. No provider, Docker, benchmark, or promotion was run; `ECODE_B0` remains pending.
- The initial evaluation cache at `.provenance/implementation-history/evaluation/` is absent from this active worktree. A separate `D:\projetos\ecode\ecode-main` copy contains `swe-bench` and `polyglot` cache directories (475 / 1,118 files; tree SHA-256 `9327d248289314a95669e523a19073266209b0dd8f171f836a45c997eb8d9f53` / `87bd0aead333d340562e0acf87bbfd89fafccce0eb6458a3ebd3d9e3f3c3164a`). Those fingerprints identify the observed bytes only: neither tree contains a checksum/provenance manifest, metadata records only `run_id` and aggregate performance, and that checkout has no Git `HEAD`. Therefore this is a located but **unverified** cache, not a valid historical seed; it was not copied or mapped into the Engine.

## DGM parent-selection plumbing gate (2026-10-05)

Claim: **integração e reprodutibilidade passaram; performance real ainda não foi validada.** Aqui, “integração” significa somente o fluxo fixture sem provider: seleção, mutação simulada, avaliação fixture, archive e lineage.

- Selectively ported the DGM parent weight formula from `archive/parent_selector.py`: sigmoid score weight times inverse valid-child count. It is exposed as the opt-in `dgm-weighted` selector in the provider-free ECode fixture.
- The implementation uses ECode's injected seeded RNG. Child counts use the valid archive history even when retention removes candidates from current selection membership. DGM regression filters, elite/focus behavior, and multi-parent selection were not imported.
- Two runs through `ecode.py --offline-fixture`, seed 23, 8 iterations, `dgm-weighted`, `keep-last` limit 4: both manifests verified; both had `provider_calls: false`, 9 version records, and 9 evaluations. Normalized candidate hashes, scores, config hash, and lineage matched exactly between runs. Config SHA-256: `369d774a4059e8fadef9f1e10f1b8cb6dc84d3199d223873549f6a77c2c22722`.
- This passes the local selection→mutation simulation→fixture evaluation→archive/lineage plumbing gate reproducibly. It does not reproduce or verify DGM's LiveCodeBench results and does not promote the selector for real model/benchmark runs.

## CLI engine dispatch gate (2026-10-05)

- Added `--engine legacy|dgm`. `legacy` is the default and continues to dispatch production runs to the existing threaded loop. `dgm` dispatches only to the deterministic, provider-free fixture and defaults to the `dgm-weighted` parent selector; production-only options are rejected in that mode. The older `--offline-fixture` entry point remains compatible.
- The `dgm` CLI run writes `execution_mode: dgm-fixture`, `provider_calls: false`, archive history, lineage, telemetry and checksums. This tests the CLI boundary without reading or trusting the historical cache.
- Targeted tests cover legacy-vs-Engine best-score selection on the same candidates, explicit DGM selection, the CLI's default and explicit legacy dispatch, fixture archive/lineage, and rejection of production options in DGM mode.
- Created a fresh fixture-only baseline pair at `.provenance/new-local-baseline-pair-v3/`, explicitly marked `BASELINE_ORIGIN=NEW_LOCAL_BASELINE`. Each `baseline_manifest.json` records baseline ID, source/code/config/dataset hashes, copied source snapshot, copied dependency manifests, Python/platform/machine and installed package inventory, seed, model/provider/benchmark/segment, and hashes for its captured artifacts. The dataset identity describes a synthetic deterministic fixture; it is not a benchmark dataset. This local schema records tracking concepts similar to [MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/) and [MLflow Datasets](https://mlflow.org/docs/latest/dataset/), without requiring MLflow or claiming external authentication.
- Both runs used seed 23, 8 iterations, `dgm-weighted`, `keep-last` limit 4, and config SHA-256 `8b6642c02f65718a8089483cb9052d9ec208aa352452fc59aa958081a9039a12`. Each produced 9 versions and 9 evaluations; 40 artifact hashes and 41 bundle checksums validated per run. Code SHA-256 `7f476886e36624e85e12bb08fcfe74b1831a4ad912bef302dfbb01b1a6d08fac`, dataset SHA-256 `27ea3691d609529a3829c5430b28217f81e752bec33eb15006bc0cdacab05c0a`, environment hashes, normalized candidate hashes, selection membership, scores/statuses, and lineage matched. Pair record SHA-256: `002150028df2455c07b3f189a3ea2d3f341adf31275e2c2f9428d5e13ea43660`.
- Runtime preflight: Ollama is installed and its local OpenAI-compatible `/v1/models` endpoint responded with model IDs. No completion/inference was sent. Docker CLI exists, but access to Docker Desktop's Linux Engine named pipe returned `permission denied`; the real legacy harness cannot run in this environment until that access boundary is resolved.
- State: `DGM_CORE_INTEGRATION=PASS`; `DGM_CORE_REPRODUCIBILITY=PASS`; `HISTORICAL_CACHE_PROVENANCE=UNVERIFIED`; `HISTORICAL_BASELINE=NOT_USABLE_FOR_COMPARISON`; `REAL_MODEL_CAPABILITY=NOT_EXECUTED`; `PERFORMANCE_GAIN=NOT_PROVEN`.
- This does not wire real mutation or benchmark callbacks to the Engine and does not change the production default.

The imported legacy source snapshot contains trailing whitespace; `git diff --cached --check` reports it across existing source files. Broad whitespace-only rewriting is deferred so the bootstrap checkpoint does not mix mechanical cleanup with the baseline integration.
