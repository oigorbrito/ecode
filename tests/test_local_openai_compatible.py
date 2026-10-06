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
