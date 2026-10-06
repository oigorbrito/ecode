"""Explicit, read-only observation of Ollama's currently loaded model context."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen


def running_model_context(api_base_url: str, requested_model: str, *, timeout: float = 2.0) -> dict:
    """Query Ollama GET /api/ps; never infer a loaded context from model metadata."""
    parsed = urlsplit(api_base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return {"status": "INVALID_EXPLICIT_OLLAMA_API_BASE_URL", "context_window_tokens": None}

    api_root = urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))
    endpoint = f"{api_root}/api/ps"
    try:
        with urlopen(endpoint, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, URLError, ValueError) as exc:
        return {
            "status": "OLLAMA_RUNTIME_QUERY_FAILED",
            "context_window_tokens": None,
            "error_type": type(exc).__name__,
        }

    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return {"status": "OLLAMA_RUNTIME_RESPONSE_INVALID", "context_window_tokens": None}

    matches = [
        item for item in models
        if isinstance(item, dict) and item.get("name") == requested_model
    ]
    if len(matches) != 1:
        return {
            "status": "REQUESTED_MODEL_NOT_UNIQUELY_LOADED",
            "requested_model": requested_model,
            "context_window_tokens": None,
            "loaded_model_count": len(models),
        }

    context_length = matches[0].get("context_length")
    if not isinstance(context_length, int) or isinstance(context_length, bool) or context_length <= 0:
        return {
            "status": "LOADED_MODEL_CONTEXT_NOT_REPORTED",
            "requested_model": requested_model,
            "matched_model": matches[0]["name"],
            "context_window_tokens": None,
        }
    return {
        "status": "OBSERVED_FROM_OLLAMA_API_PS",
        "requested_model": requested_model,
        "matched_model": matches[0]["name"],
        "context_window_tokens": context_length,
    }
