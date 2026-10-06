# Controlled experiment harness

The `ecode_core.controlled_repair_harness` module consolidates the experimental runner preserved under `.provenance/`. It composes the existing ECode `EvolutionEngine`, mutation adapter, evaluator contract, archive, selector, Docker isolation, independent fixture verifier, and event capture. It does not change the agent prompt, parser, dispatcher, editor, mutation strategy, selector, CLI, acceptance, or promotion behavior.

## Responsibilities

- The harness reads an immutable source bundle containing `run-plan.json`, `snapshot-identity.json`, `carried-cases.json`, the frozen observer, and per-case fixture/verifier inputs.
- Each new run gets a separate, previously nonexistent output directory under `.provenance/`. The source bundle is read-only; the output begins with fresh attempt records and includes copies of the frozen plan and identity.
- The run plan supplies the exact model, completion endpoint, read-only runtime-context API base URL, cases, and attempt limit. The harness records these values, its own hash, and hashes of the frozen input files. Model and verifier timeouts and RNG seed are fixed by the harness and recorded in the report. It does not substitute another model, endpoint, executor, or verifier.
- The frozen plan pins the model's exact local name, digest, size, metadata, capabilities, and cached helper-image ID. On `--execute`, the harness queries `/api/tags` through that helper image and requires an exact match before any model-facing request. A missing or changed image/model stops the run; the default preflight makes no Docker/provider request.
- Subjects and independent verification run in disposable Docker containers. A container mount is rejected. Mutation, tool/protocol events, filesystem changes, patches, candidate hashes, evaluations, archive snapshots, lineage, and post-evaluation selection are preserved in the run output.
- The isolated agent image and fixture package use the frozen repository identity. Auxiliary runtime support files are copied only to the fixture package and their paths/hashes are recorded; clean subject modules remain absent. Included image source paths are listed in the report.
- Existing classifications are retained (`REAL_REPAIR_PASS`, `CANDIDATE_INVALID`, `VERIFICATION_FAILED`, `MUTATION_FAILED`, `INFRASTRUCTURE_BLOCKED`, and `HARNESS_FAILURE`); timeout remains explicitly recorded as `MUTATION_TIMEOUT` in the secondary classification where the existing experiment used that representation.

## Invocation

Preflight reads and validates the bundle and prints the frozen model, endpoint, case IDs, and budget. It does not create output files, contact Docker/Ollama, or call a model:

```bash
PYTHONPATH="$PWD" .venv/bin/python -m ecode_core.controlled_repair_harness \
  --source-dir .provenance/<frozen-input-bundle> \
  --output-dir .provenance/<new-run-id>
```

Real execution requires the separate explicit `--execute` flag:

```bash
PYTHONPATH="$PWD" .venv/bin/python -m ecode_core.controlled_repair_harness \
  --source-dir .provenance/<frozen-input-bundle> \
  --output-dir .provenance/<new-run-id> \
  --execute
```

The output path must be a new child of `.provenance/`; existing directories and paths outside it are rejected. The harness checks the frozen source hashes and tracked diff before creating output or starting Docker. A failed check stops the run; do not repair or weaken the identity check to make a run proceed. Preserve `.provenance/` locally and never add it to Git.

Preflight is infrastructure validation, not evidence that model execution, verification, acceptance, or promotion passed. Execution alone does not imply acceptance. Agent-behavior changes such as prompt, tool policy, context selection, retries, or stopping rules require their own controlled comparison with the same task set and independent verifiers.

## Pending execution and offline evidence

Executor qualification is pending at the user's request. Existing Docker installation does not establish successful image construction or isolated execution for a particular frozen run. Preserve credential-helper failures and source drift as separate preparation failures.

For the preserved alternate-model runs, `model_calls` contains only `get_response_from_llm_end` events. It is a completed-response list, not a count of attempted calls or independently observed provider requests. Consult the raw `get_response_from_llm_start` and `get_response_from_llm_error` events as well. Missing provider-dispatch evidence must remain unknown; missing response usage must not be replaced with zero tokens.

The local offline reconciliation in `.provenance/offline-executor-evidence-2026-10-06/` records original report/trace hashes, ordered event references, function starts/completions/errors, and preparation failures. Its two outputs are byte-identical. It invokes neither Docker nor a model and does not change the original artifacts or classifications. It validates evidence interpretation only; it does not qualify real execution.

## Passive observability qualification

Offline tests in `tests/test_llm_usage_telemetry.py` and `tests/test_ollama_runtime.py` exercise provider responses and runtime queries with test doubles. They compare request arguments, returned content/history, and input-history preservation with and without the usage callback. Missing or invalid token counts remain `None`; ambiguous loaded models, missing context and query failures retain explicit statuses. Provider exceptions are propagated without a successful usage event.

The earlier offline snapshot had a known limit: an exception raised by the usage callback propagated after a completion response had been obtained. The subsequent observer-failure isolation change routes usage collection through `emit_response_usage`. Ordinary exceptions during event construction or delivery emit a structured `llm_usage_observer_error` through the independent Python logger, including stage, exception type, and `completion_received=true`. They do not cause a new completion request or prevent delivery of the response. Exception messages and prompt data are excluded. Process interrupts remain propagated; provider exceptions retain the existing error/retry policy.

`PASSIVE_OBSERVABILITY_OFFLINE = PARTIALLY_VERIFIED` remains scoped to simulated paths: the frozen observer lacks independent transport-dispatch and provider-receipt markers, and real token/context capture remains unverified while executor qualification is pending. Observer-failure isolation is a separate offline implementation gate; it does not retroactively change historical results. Transport evidence requires its own explicitly scoped observation boundary. Neither gap justifies estimating tokens or relabeling historical events.

`OBSERVER_FAILURE_ISOLATION_OFFLINE = PASS`, scoped to simulated clients and the standard Python logging sink. Local WSL regression on the final snapshot: `156 passed, 3 warnings` with Python 3.14.4. Syntax and `git diff --check` passed. Ruff was unavailable in the venv; hosted CI and real execution were not performed. A custom logging handler that itself fails is outside this gate. The report and test output are preserved under `.provenance/observer-failure-isolation-offline-2026-10-06/`.

## Optional SDK and HTTP boundary observation

The generic local adapter accepts an optional `on_observation` callback in `create_client` and `complete_chat`. Client creation installs request/response hooks through the SDK's public `DefaultHttpxClient` factory, preserving its backend and defaults. Supply the callback to both functions to observe both boundaries. Existing callers remain uninstrumented unless they opt in; the harness has not activated this option in a real run.

| Event | Evidence scope |
|---|---|
| `sdk_chat_completion_started` | Entry to the SDK completion call after model configuration validation. |
| `http_request_prepared` | HTTP request hook ran before transport; no proof of bytes sent or provider receipt. |
| `http_response_headers_received` | HTTP client obtained response headers and status; no claim of a successful completion. |
| `sdk_chat_completion_returned` | SDK returned a response; independent verification and acceptance remain separate. |
| `sdk_chat_completion_error` | SDK raised an exception; original exception and retry policy are preserved. |

Boundary events omit prompts, URLs, credentials and response bodies. Ordinary callback failures emit `llm_boundary_observer_error` through the independent logger without adding a request or replacing the SDK error. HTTP hooks may occur repeatedly during SDK retries. This implementation does not attach cross-call correlation IDs; concurrent-call attribution remains outside the current scope.

The offline qualification script under `.provenance/sdk-http-boundary-offline-2026-10-06/` uses the installed SDK with an in-memory `MockTransport`, comparing observed and unobserved requests/outcomes for success, a retry, connection failure and observer failure. It opens no sockets and performs no inference. Existing historical traces retain their original evidence limits.

`SDK_HTTP_BOUNDARY_OFFLINE = PASS` for the installed `openai 3.24.0` / `httpx2 2.13.1` condition with mock transport. The connection-failure case records three preparation hooks and an `APIConnectionError`, with no response-header event; the retry case records two preparations and two responses before SDK return. Observed and unobserved requests/outcomes match in all four scenarios. Local WSL regression: `161 passed, 3 warnings`. This gate does not qualify sockets, provider receipt, real model inference, concurrent correlation, or activation in the harness.
