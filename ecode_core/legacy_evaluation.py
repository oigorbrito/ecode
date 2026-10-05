from __future__ import annotations

import os
from typing import Any, Callable, MutableMapping, Type


def run_benchmark_evaluation(
    *,
    model_patch_file: str,
    metadata: MutableMapping[str, Any],
    harness_runner: Callable[..., None],
    sandbox_unavailable_error: Type[Exception],
    harness_args: tuple[Any, ...],
    log: Callable[[str], None],
    persist: Callable[[MutableMapping[str, Any]], None],
) -> MutableMapping[str, Any]:
    """Evaluate a produced patch through an injected legacy harness.

    This small adapter keeps benchmark execution separate from mutation and
    makes the boundary testable without importing Docker or a model provider.
    The harness still owns the actual execution/isolation policy.
    """
    patch_exists = os.path.exists(model_patch_file)
    patch_notempty = patch_exists and os.path.getsize(model_patch_file) > 0
    metadata["model_patch_exists"] = patch_exists
    metadata["model_patch_notempty"] = patch_notempty

    if patch_notempty:
        try:
            harness_runner(*harness_args)
        except sandbox_unavailable_error as exc:
            metadata["status"] = "BLOCKED"
            metadata["blocked_reason"] = "SANDBOX_UNAVAILABLE"
            log(str(exc))
            persist(metadata)
            return metadata
        except Exception as exc:
            log(f"Error while evaluating the self-improvement: {exc}")

    return metadata
