"""Generic OpenAI-compatible client adapter; it has no provider-specific branches."""

import os

def is_enabled() -> bool:
    return bool(os.getenv("ECODE_OPENAI_BASE_URL"))


def resolve_model(model: str) -> str:
    if not is_enabled():
        return model
    configured_model = os.getenv("ECODE_OPENAI_MODEL")
    if not configured_model:
        raise ValueError("ECODE_OPENAI_MODEL is required with ECODE_OPENAI_BASE_URL")
    return configured_model


def create_client(model: str, *, client_factory=None):
    if not is_enabled():
        raise RuntimeError("OpenAI-compatible adapter is not configured")
    model = resolve_model(model)
    if client_factory is None:
        import openai

        client_factory = openai.OpenAI
    client = client_factory(
        api_key=os.getenv("ECODE_OPENAI_API_KEY") or "local",
        base_url=os.environ["ECODE_OPENAI_BASE_URL"],
    )
    return client, model


def complete_chat(
    client,
    *,
    model: str,
    messages,
    temperature: float,
    max_tokens: int,
):
    """Call the common Chat Completions subset used by ECode's local profile."""
    return client.chat.completions.create(
        model=resolve_model(model),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        n=1,
    )
