from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ecode_core.adapters import openai_compatible


def test_local_endpoint_uses_shared_openai_client(monkeypatch):
    monkeypatch.setenv("ECODE_OPENAI_BASE_URL", "http://localhost:8080/v1")
    monkeypatch.setenv("ECODE_OPENAI_MODEL", "loaded-model")
    monkeypatch.delenv("ECODE_OPENAI_API_KEY", raising=False)
    factory = Mock(return_value="client")

    client, model = openai_compatible.create_client(
        "o1-2024-12-17",
        client_factory=factory,
    )

    assert (client, model) == ("client", "loaded-model")
    factory.assert_called_once_with(
        api_key="local",
        base_url="http://localhost:8080/v1",
    )


def test_local_endpoint_requires_model_name(monkeypatch):
    monkeypatch.setenv("ECODE_OPENAI_BASE_URL", "http://localhost:8080/v1")
    monkeypatch.delenv("ECODE_OPENAI_MODEL", raising=False)

    with pytest.raises(ValueError, match="ECODE_OPENAI_MODEL is required"):
        openai_compatible.create_client("claude-3-5-sonnet-20241022")


def test_local_endpoint_uses_generic_chat_completions(monkeypatch):
    monkeypatch.setenv("ECODE_OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("ECODE_OPENAI_MODEL", "qwen-local")
    create = Mock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))]
        )
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )

    response = openai_compatible.complete_chat(
        client,
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "say hello"}],
        temperature=0.7,
        max_tokens=100,
    )

    assert response.choices[0].message.content == "hello"
    create.assert_called_once_with(
        model="qwen-local",
        messages=[{"role": "user", "content": "say hello"}],
        temperature=0.7,
        max_tokens=100,
        n=1,
    )


def test_sdk_observation_preserves_arguments_and_response(monkeypatch):
    monkeypatch.delenv("ECODE_OPENAI_BASE_URL", raising=False)
    response = object()
    create = Mock(return_value=response)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    arguments = dict(model="fixture", messages=[{"role": "user", "content": "literal"}],
                     temperature=0.7, max_tokens=100)
    baseline = openai_compatible.complete_chat(client, **arguments)
    baseline_args = create.call_args
    events = []
    observed = openai_compatible.complete_chat(client, **arguments, on_observation=events.append)
    assert observed is baseline is response
    assert create.call_args == baseline_args
    assert [e["event"] for e in events] == ["sdk_chat_completion_started",
                                           "sdk_chat_completion_returned"]
    assert all("messages" not in e for e in events)


def test_sdk_error_is_not_misreported_as_transport_receipt(monkeypatch):
    monkeypatch.delenv("ECODE_OPENAI_BASE_URL", raising=False)
    failure = RuntimeError("local failure")
    create = Mock(side_effect=failure)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    events = []
    with pytest.raises(RuntimeError) as caught:
        openai_compatible.complete_chat(client, model="fixture", messages=[], temperature=0.7,
                                       max_tokens=100, on_observation=events.append)
    assert caught.value is failure
    assert events == [{"event": "sdk_chat_completion_started"},
                      {"event": "sdk_chat_completion_error", "error_type": "RuntimeError"}]
    assert create.call_count == 1


def test_boundary_observer_failure_preserves_original_error(monkeypatch, caplog):
    monkeypatch.delenv("ECODE_OPENAI_BASE_URL", raising=False)
    original = ValueError("provider failure")
    create = Mock(side_effect=original)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    def broken(event):
        raise RuntimeError("observer failure")

    with pytest.raises(ValueError) as caught:
        openai_compatible.complete_chat(client, model="fixture", messages=[], temperature=0.7,
                                       max_tokens=100, on_observation=broken)
    assert caught.value is original
    assert create.call_count == 1
    assert len(caplog.records) == 2
    assert "llm_boundary_observer_error" in caplog.text
    assert "observer failure" not in caplog.text


def test_http_hooks_report_only_preparation_and_headers():
    events = []
    hooks = openai_compatible.observation_hooks(events.append)
    hooks["request"][0](SimpleNamespace(method="POST"))
    hooks["response"][0](SimpleNamespace(status_code=503))
    assert events == [{"event": "http_request_prepared", "method": "POST"},
                      {"event": "http_response_headers_received", "status_code": 503}]


def test_opt_in_uses_sdk_default_http_client(monkeypatch):
    import openai

    monkeypatch.setenv("ECODE_OPENAI_BASE_URL", "http://fixture.invalid/v1")
    monkeypatch.setenv("ECODE_OPENAI_MODEL", "fixture")
    http_client = object()
    http_factory = Mock(return_value=http_client)
    monkeypatch.setattr(openai, "DefaultHttpxClient", http_factory)
    factory = Mock(return_value="fixture-client")
    client, model = openai_compatible.create_client("fixture", client_factory=factory,
                                                   on_observation=lambda e: None)
    assert (client, model) == ("fixture-client", "fixture")
    assert factory.call_args.kwargs["http_client"] is http_client
    assert set(http_factory.call_args.kwargs) == {"event_hooks"}
