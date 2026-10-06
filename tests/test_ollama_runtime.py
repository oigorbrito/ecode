import io
import json

import pytest

from ecode_core.adapters import ollama_runtime


def test_running_model_context_reads_only_exact_loaded_model(monkeypatch):
    calls = []
    payload = {
        "models": [
            {"name": "other-model", "context_length": 4096},
            {"name": "qwen2.5-coder:3b", "context_length": 8192},
        ]
    }

    def fake_urlopen(url, timeout):
        calls.append((url, timeout))
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr(ollama_runtime, "urlopen", fake_urlopen)

    event = ollama_runtime.running_model_context(
        "http://ollama.example:11434/", "qwen2.5-coder:3b"
    )

    assert event["status"] == "OBSERVED_FROM_OLLAMA_API_PS"
    assert event["context_window_tokens"] == 8192
    assert event["matched_model"] == "qwen2.5-coder:3b"
    assert calls == [("http://ollama.example:11434/api/ps", 2.0)]


def test_running_model_context_does_not_alias_or_infer_model_match(monkeypatch):
    monkeypatch.setattr(
        ollama_runtime,
        "urlopen",
        lambda *args, **kwargs: io.BytesIO(
            b'{"models":[{"name":"qwen2.5-coder:3b-custom","context_length":8192}]}'
        ),
    )

    event = ollama_runtime.running_model_context(
        "http://ollama.example:11434", "qwen2.5-coder:3b"
    )

    assert event["status"] == "REQUESTED_MODEL_NOT_UNIQUELY_LOADED"
    assert event["context_window_tokens"] is None


def test_running_model_context_rejects_ambiguous_endpoint():
    event = ollama_runtime.running_model_context(
        "http://user:password@ollama.example:11434?token=secret", "qwen2.5-coder:3b"
    )

    assert event == {
        "status": "INVALID_EXPLICIT_OLLAMA_API_BASE_URL",
        "context_window_tokens": None,
    }


@pytest.mark.parametrize("payload,status", [
    ({"models": []}, "REQUESTED_MODEL_NOT_UNIQUELY_LOADED"),
    ({"models": [{"name": "fixture-model"}, {"name": "fixture-model"}]},
     "REQUESTED_MODEL_NOT_UNIQUELY_LOADED"),
    ({"models": [{"name": "fixture-model", "context_length": True}]},
     "LOADED_MODEL_CONTEXT_NOT_REPORTED"),
    ({"models": [{"name": "fixture-model", "context_length": 0}]},
     "LOADED_MODEL_CONTEXT_NOT_REPORTED"),
    ({"models": None}, "OLLAMA_RUNTIME_RESPONSE_INVALID"),
])
def test_context_is_not_inferred_from_missing_or_ambiguous_data(monkeypatch, payload, status):
    monkeypatch.setattr(ollama_runtime, "urlopen",
                        lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
    event = ollama_runtime.running_model_context("http://fixture.invalid", "fixture-model")
    assert event["status"] == status
    assert event["context_window_tokens"] is None


def test_context_query_failure_remains_explicit(monkeypatch):
    def unavailable(*args, **kwargs):
        raise TimeoutError("fixture timeout")

    monkeypatch.setattr(ollama_runtime, "urlopen", unavailable)
    event = ollama_runtime.running_model_context("http://fixture.invalid", "fixture-model")
    assert event == {"status": "OLLAMA_RUNTIME_QUERY_FAILED",
                     "context_window_tokens": None, "error_type": "TimeoutError"}
