from types import SimpleNamespace
import json

import pytest

import llm


@pytest.fixture(autouse=True)
def offline_runtime(monkeypatch):
    monkeypatch.delenv("ECODE_OLLAMA_API_BASE_URL", raising=False)


def test_response_usage_event_records_provider_counts_without_prompt_data():
    response = SimpleNamespace(
        model="qwen2.5-coder:3b",
        usage=SimpleNamespace(prompt_tokens=124, completion_tokens=19, total_tokens=143),
    )

    event = llm.response_usage_event(response, "configured-alias")

    assert event == {
        "event": "llm_usage",
        "model": "qwen2.5-coder:3b",
        "usage_reported": True,
        "prompt_tokens": 124,
        "completion_tokens": 19,
        "total_tokens": 143,
        "context_window_tokens": None,
        "context_window_status": "OLLAMA_RUNTIME_URL_NOT_CONFIGURED",
    }
    assert "prompt" not in event


def test_response_usage_event_does_not_infer_missing_counts():
    response = {"model": "local-model", "usage": {"prompt_tokens": 8}}

    event = llm.response_usage_event(response, "configured-model")

    assert event["usage_reported"] is True
    assert event["prompt_tokens"] == 8
    assert event["completion_tokens"] is None
    assert event["total_tokens"] is None


def test_get_response_emits_usage_side_channel_without_changing_return(monkeypatch):
    response = SimpleNamespace(
        model="qwen2.5-coder:3b",
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=2, total_tokens=12),
        choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))],
    )
    monkeypatch.setattr(llm, "is_openai_compatible_local", lambda: True)
    monkeypatch.setattr(llm, "resolve_model", lambda model: "qwen2.5-coder:3b")
    monkeypatch.setattr(llm.openai_compatible, "complete_chat", lambda *args, **kwargs: response)
    events = []

    result = llm.get_response_from_llm(
        msg="question",
        client=object(),
        model="configured-model",
        system_message="system",
        on_usage=events.append,
    )

    assert result[0] == "answer"
    assert result[1][-1] == {"role": "assistant", "content": "answer"}
    assert len(events) == 1
    assert events[0]["prompt_tokens"] == 10
    assert events[0]["total_tokens"] == 12


def test_response_usage_event_queries_only_explicit_ollama_runtime(monkeypatch):
    monkeypatch.setenv("ECODE_OLLAMA_API_BASE_URL", "http://ollama.example:11434")
    monkeypatch.setattr(
        "ecode_core.adapters.ollama_runtime.running_model_context",
        lambda api_base_url, model: {
            "status": "OBSERVED_FROM_OLLAMA_API_PS",
            "requested_model": model,
            "matched_model": model,
            "context_window_tokens": 8192,
        },
    )
    response = SimpleNamespace(
        model="qwen2.5-coder:3b",
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=3, total_tokens=15),
    )

    event = llm.response_usage_event(response, "configured-model")

    assert event["context_window_tokens"] == 8192
    assert event["context_window_status"] == "OBSERVED_FROM_OLLAMA_API_PS"
    assert event["runtime_context"]["matched_model"] == "qwen2.5-coder:3b"


@pytest.mark.parametrize("usage", [None, {}, {"prompt_tokens": True, "total_tokens": "15"}])
def test_absent_or_invalid_token_counts_remain_unknown(usage):
    event = llm.response_usage_event(SimpleNamespace(usage=usage), "fixture-model")
    assert event["prompt_tokens"] is None
    assert event["completion_tokens"] is None
    assert event["total_tokens"] is None
    assert event["context_window_tokens"] is None


def test_usage_observation_preserves_request_and_return(monkeypatch):
    response = SimpleNamespace(
        model="fixture-model", usage=None,
        choices=[SimpleNamespace(message=SimpleNamespace(content="literal answer"))],
    )
    requests = []

    def complete(client, **kwargs):
        requests.append(kwargs)
        return response

    monkeypatch.setattr(llm, "is_openai_compatible_local", lambda: True)
    monkeypatch.setattr(llm, "resolve_model", lambda model: "fixture-model")
    monkeypatch.setattr(llm.openai_compatible, "complete_chat", complete)
    history = [{"role": "assistant", "content": "previous"}]
    arguments = dict(msg="question", client=object(), model="fixture-model",
                     system_message="system", msg_history=history)
    baseline = llm.get_response_from_llm(**arguments)
    events = []
    observed = llm.get_response_from_llm(**arguments, on_usage=events.append)
    assert baseline == observed
    assert requests[0] == requests[1]
    assert history == [{"role": "assistant", "content": "previous"}]
    assert len(events) == 1


def test_provider_error_does_not_emit_success_usage_or_hide_error(monkeypatch):
    failure = RuntimeError("fixture provider failure")

    def complete(*args, **kwargs):
        raise failure

    monkeypatch.setattr(llm, "is_openai_compatible_local", lambda: True)
    monkeypatch.setattr(llm, "resolve_model", lambda model: model)
    monkeypatch.setattr(llm.openai_compatible, "complete_chat", complete)
    events = []
    with pytest.raises(RuntimeError) as caught:
        llm.get_response_from_llm("question", object(), "fixture-model", "system",
                                  on_usage=events.append)
    assert caught.value is failure
    assert events == []


@pytest.mark.parametrize("failure", [
    RuntimeError("fixture observer failure"),
    llm.openai.APITimeoutError(request=SimpleNamespace()),
])
def test_observer_failure_preserves_response_without_retry(monkeypatch, caplog, failure):
    response = SimpleNamespace(usage=None,
        choices=[SimpleNamespace(message=SimpleNamespace(content="literal answer"))])
    requests = []

    def complete(*args, **kwargs):
        requests.append(kwargs)
        return response

    def observe(event):
        raise failure

    monkeypatch.setattr(llm, "is_openai_compatible_local", lambda: True)
    monkeypatch.setattr(llm, "resolve_model", lambda model: model)
    monkeypatch.setattr(llm.openai_compatible, "complete_chat", complete)
    result = llm.get_response_from_llm("question", object(), "fixture-model", "system",
                                      on_usage=observe)
    assert result == ("literal answer", [{"role": "user", "content": "question"},
                                        {"role": "assistant", "content": "literal answer"}])
    assert len(requests) == 1
    assert json.loads(caplog.records[-1].message) == {
        "event": "llm_usage_observer_error", "stage": "DELIVER_USAGE_EVENT",
        "error_type": type(failure).__name__, "completion_received": True,
    }
    assert "fixture observer failure" not in caplog.text


def test_usage_construction_failure_preserves_response(monkeypatch, caplog):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))])

    def broken_event(*args):
        raise ImportError("fixture missing observer dependency")

    monkeypatch.setattr(llm, "is_openai_compatible_local", lambda: True)
    monkeypatch.setattr(llm, "resolve_model", lambda model: model)
    monkeypatch.setattr(llm.openai_compatible, "complete_chat", lambda *a, **k: response)
    monkeypatch.setattr(llm, "response_usage_event", broken_event)
    events = []
    assert llm.get_response_from_llm("question", object(), "fixture-model", "system",
                                     on_usage=events.append)[0] == "answer"
    assert events == []
    assert json.loads(caplog.records[-1].message)["stage"] == "BUILD_USAGE_EVENT"


def test_tools_logging_failure_does_not_repeat_provider_request(caplog):
    import llm_withtools

    response = SimpleNamespace(usage=None)
    requests = []

    def create(**kwargs):
        requests.append(kwargs)
        return response

    def broken_logger(message):
        raise RuntimeError("fixture logging unavailable")

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    result = llm_withtools.get_response_withtools(client, "claude-fixture", [], [],
                                                 {"type": "auto"}, logging=broken_logger)
    assert result is response
    assert len(requests) == 1
    assert json.loads(caplog.records[-1].message)["event"] == "llm_usage_observer_error"


def test_observer_does_not_swallow_process_interrupt():
    def interrupt(event):
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        llm.emit_response_usage(SimpleNamespace(usage=None), "fixture-model", interrupt)
