"""Generic OpenAI-compatible client adapter; it has no provider-specific branches."""

import json
import logging
import os


def _observe(callback, event):
    if callback is None:
        return
    try:
        callback(event)
    except Exception as exc:
        logging.getLogger(__name__).error(json.dumps({
            "event": "llm_boundary_observer_error",
            "observed_event": event["event"],
            "error_type": type(exc).__name__,
        }, sort_keys=True))


def observation_hooks(callback):
    """HTTP hooks observe preparation and headers, never claim remote receipt."""
    def request_prepared(request):
        _observe(callback, {"event": "http_request_prepared", "method": request.method})

    def response_headers(response):
        _observe(callback, {"event": "http_response_headers_received",
                            "status_code": response.status_code})

    return {"request": [request_prepared], "response": [response_headers]}

def is_enabled() -> bool:
    return bool(os.getenv("ECODE_OPENAI_BASE_URL"))


def resolve_model(model: str) -> str:
    if not is_enabled():
        return model
    configured_model = os.getenv("ECODE_OPENAI_MODEL")
    if not configured_model:
        raise ValueError("ECODE_OPENAI_MODEL is required with ECODE_OPENAI_BASE_URL")
    return configured_model


def create_client(model: str, *, client_factory=None, on_observation=None):
    if not is_enabled():
        raise RuntimeError("OpenAI-compatible adapter is not configured")
    model = resolve_model(model)
    if client_factory is None:
        import openai

        client_factory = openai.OpenAI
    options = {}
    if on_observation is not None:
        import openai

        options["http_client"] = openai.DefaultHttpxClient(
            event_hooks=observation_hooks(on_observation)
        )
    client = client_factory(
        api_key=os.getenv("ECODE_OPENAI_API_KEY") or "local",
        base_url=os.environ["ECODE_OPENAI_BASE_URL"],
        **options,
    )
    return client, model


def complete_chat(
    client,
    *,
    model: str,
    messages,
    temperature: float,
    max_tokens: int,
    on_observation=None,
):
    """Call the common Chat Completions subset used by ECode's local profile."""
    resolved_model = resolve_model(model)
    _observe(on_observation, {"event": "sdk_chat_completion_started"})
    try:
        response = client.chat.completions.create(
            model=resolved_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            n=1,
        )
    except Exception as exc:
        _observe(on_observation, {"event": "sdk_chat_completion_error",
                                  "error_type": type(exc).__name__})
        raise
    _observe(on_observation, {"event": "sdk_chat_completion_returned"})
    return response
