# Code adapted from https://github.com/SakanaAI/AI-Scientist/blob/main/ai_scientist/llm.py.
import json
import logging
import os
import re

import anthropic
import backoff
import openai
from ecode_core.adapters import openai_compatible

MAX_OUTPUT_TOKENS = 4096
AVAILABLE_LLMS = [
    # Anthropic models
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022",
    # OpenAI models
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-2024-05-13",
    "gpt-4o-2024-08-06",
    "o1-preview-2024-09-12",
    "o1-mini-2024-09-12",
    "o1-2024-12-17",
    "o3-mini-2025-01-31",
    # OpenRouter models
    "llama3.1-405b",
    # Anthropic Claude models via Amazon Bedrock
    "bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
    "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
    "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
    "bedrock/anthropic.claude-3-haiku-20240307-v1:0",
    "bedrock/anthropic.claude-3-opus-20240229-v1:0",
    "bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    # Anthropic Claude models Vertex AI
    "vertex_ai/claude-3-opus@20240229",
    "vertex_ai/claude-3-5-sonnet@20240620",
    "vertex_ai/claude-3-5-sonnet-v2@20241022",
    "vertex_ai/claude-3-sonnet@20240229",
    "vertex_ai/claude-3-haiku@20240307",
    # DeepSeek models
    "deepseek-chat",
    "deepseek-coder",
    "deepseek-reasoner",
]


def is_openai_compatible_local():
    return openai_compatible.is_enabled()


def resolve_model(model: str) -> str:
    """Use the configured model name when the generic local endpoint is enabled."""
    return openai_compatible.resolve_model(model)


def create_client(model: str):
    """
    Create and return an LLM client based on the specified model.
    Args:
        model (str): The name of the model to use.
    Returns:
        Tuple[Any, str]: A tuple containing the client instance and the client model name.
    """
    if is_openai_compatible_local():
        return openai_compatible.create_client(model)
    elif model.startswith("claude-"):
        print(f"Using Anthropic API with model {model}.")
        return anthropic.Anthropic(), model
    elif model.startswith("bedrock") and "claude" in model:
        client_model = model.split("/")[-1]
        print(f"Using Amazon Bedrock with model {client_model}.")
        client = anthropic.AnthropicBedrock(
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_region=os.getenv("AWS_REGION_NAME"),
        )
        return client, client_model
    elif model.startswith("vertex_ai") and "claude" in model:
        client_model = model.split("/")[-1]
        print(f"Using Vertex AI with model {client_model}.")
        return anthropic.AnthropicVertex(), client_model
    elif 'gpt' in model or model.startswith("o1-") or model.startswith("o3-"):
        print(f"Using OpenAI API with model {model}.")
        return openai.OpenAI(), model
    elif model.startswith("deepseek-"):
        print(f"Using OpenAI API with {model}.")
        client = openai.OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com"
        )
        return client, model
    elif model == "llama3.1-405b":
        print(f"Using OpenAI API with {model}.")
        client = openai.OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1"
        ), model
    else:
        raise ValueError(f"Model {model} not supported.")


def response_usage_event(response, model):
    """Return provider-reported usage without estimating missing token counts."""
    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")

    def usage_value(*names):
        for name in names:
            value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        return None

    event = {
        "event": "llm_usage",
        "model": getattr(response, "model", None) or model,
        "usage_reported": usage is not None,
        "prompt_tokens": usage_value("prompt_tokens", "input_tokens"),
        "completion_tokens": usage_value("completion_tokens", "output_tokens"),
        "total_tokens": usage_value("total_tokens"),
        "context_window_tokens": None,
        "context_window_status": "NOT_REPORTED_BY_COMPLETION_RESPONSE",
    }
    ollama_api_base_url = os.getenv("ECODE_OLLAMA_API_BASE_URL")
    if ollama_api_base_url:
        from ecode_core.adapters.ollama_runtime import running_model_context

        runtime_context = running_model_context(ollama_api_base_url, event["model"])
        event["context_window_tokens"] = runtime_context["context_window_tokens"]
        event["context_window_status"] = runtime_context["status"]
        event["runtime_context"] = runtime_context
    else:
        event["context_window_status"] = "OLLAMA_RUNTIME_URL_NOT_CONFIGURED"
    return event


def emit_response_usage(response, model, on_usage):
    """Observe a received response without turning observer errors into LLM retries."""
    if on_usage is None:
        return
    stage = "BUILD_USAGE_EVENT"
    try:
        event = response_usage_event(response, model)
        stage = "DELIVER_USAGE_EVENT"
        on_usage(event)
    except Exception as exc:
        # Use an independent sink: invoking the failing callback again could
        # hide the error or cause another completion request. Do not log prompt
        # data or exception messages, which may contain provider credentials.
        logging.getLogger(__name__).error(json.dumps({
            "event": "llm_usage_observer_error",
            "stage": stage,
            "error_type": type(exc).__name__,
            "completion_received": True,
        }, sort_keys=True))

# Get N responses from a single message, used for ensembling.
@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError))
def get_batch_responses_from_llm(
        msg,
        client,
        model,
        system_message,
        print_debug=False,
        msg_history=None,
        temperature=0.75,
        n_responses=1,
):
    if msg_history is None:
        msg_history = []

    if is_openai_compatible_local():
        responses = [
            get_response_from_llm(
                msg,
                client,
                model,
                system_message,
                print_debug=False,
                msg_history=None,
                temperature=temperature,
            )
            for _ in range(n_responses)
        ]
        content = [response for response, _ in responses]
        new_msg_history = [history for _, history in responses]
        return content, new_msg_history

    if model in [
        "gpt-4o-2024-05-13",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
    ]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=n_responses,
            stop=None,
            seed=0,
        )
        content = [r.message.content for r in response.choices]
        new_msg_history = [
            new_msg_history + [{"role": "assistant", "content": c}] for c in content
        ]
    elif model == "llama-3-1-405b-instruct":
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-405b-instruct",
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=n_responses,
            stop=None,
        )
        content = [r.message.content for r in response.choices]
        new_msg_history = [
            new_msg_history + [{"role": "assistant", "content": c}] for c in content
        ]
    else:
        content, new_msg_history = [], []
        for _ in range(n_responses):
            c, hist = get_response_from_llm(
                msg,
                client,
                model,
                system_message,
                print_debug=False,
                msg_history=None,
                temperature=temperature,
            )
            content.append(c)
            new_msg_history.append(hist)

    if print_debug:
        print()
        print("*" * 20 + " LLM START " + "*" * 20)
        for j, msg in enumerate(new_msg_history[0]):
            print(f'{j}, {msg["role"]}: {msg["content"]}')
        print(content)
        print("*" * 21 + " LLM END " + "*" * 21)
        print()

    return content, new_msg_history

@backoff.on_exception(
    backoff.expo,
    (openai.RateLimitError, openai.APITimeoutError, anthropic.RateLimitError, anthropic.APIStatusError),
    max_time=120,
)
def get_response_from_llm(
        msg,
        client,
        model,
        system_message,
        print_debug=False,
        msg_history=None,
        temperature=0.7,
        on_usage=None,
):
    if msg_history is None:
        msg_history = []

    if is_openai_compatible_local():
        model = resolve_model(model)
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = openai_compatible.complete_chat(
            client,
            model=model,
            messages=[{"role": "system", "content": system_message}, *new_msg_history],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        emit_response_usage(response, model, on_usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
        if print_debug:
            print(f"User: {msg}\nAssistant: {content}")
        return content, new_msg_history

    if "claude" in model:
        new_msg_history = msg_history + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": msg,
                    }
                ],
            }
        ]
        response = client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=temperature,
            system=system_message,
            messages=new_msg_history,
        )
        emit_response_usage(response, model, on_usage)
        content = response.content[0].text
        new_msg_history = new_msg_history + [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": content,
                    }
                ],
            }
        ]
    elif model.startswith("gpt-4o-"):
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=1,
            stop=None,
            seed=0,
        )
        emit_response_usage(response, model, on_usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model.startswith("o1-") or model.startswith("o3-"):
        new_msg_history = msg_history + [{"role": "user", "content": system_message + msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                # {"role": "user", "content": system_message},
                *new_msg_history,
            ],
            temperature=1,
            # max_completion_tokens=MAX_OUTPUT_TOKENS,
            n=1,
            # stop=None,
            seed=0,
        )
        emit_response_usage(response, model, on_usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model in ["deepseek-chat", "deepseek-coder"]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=1,
            stop=None,
        )
        emit_response_usage(response, model, on_usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model in ["deepseek-reasoner"]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            n=1,
            stop=None,
        )
        emit_response_usage(response, model, on_usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
        reasoning_content = response.choices[0].message.reasoning_content
    elif model.startswith("llama3.1-"):
        llama_size = model.split("-")[-1]
        client_model = f"meta-llama/llama-3.1-{llama_size}-instruct"
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=client_model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=1,
            stop=None,
        )
        emit_response_usage(response, model, on_usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
        resoning_content = response.choices[0].message.reasoning_content
    else:
        raise ValueError(f"Model {model} not supported.")
    if print_debug:
        print()
        print("*" * 20 + " LLM START " + "*" * 20)
        print(f'User: {new_msg_history[-2]["content"]}')
        print(f'Assistant: {new_msg_history[-1]["content"]}')
        print("*" * 21 + " LLM END " + "*" * 21)
        print()
    return content, new_msg_history

def extract_json_between_markers(llm_output):
    inside_json_block = False
    json_lines = []

    # Split the output into lines and iterate
    for line in llm_output.split('\n'):
        striped_line = line.strip()

        # Check for start of JSON code block
        if striped_line.startswith("```json"):
            inside_json_block = True
            continue

        # Check for end of code block
        if inside_json_block and striped_line.startswith("```"):
            # We've reached the closing triple backticks.
            inside_json_block = False
            break

        # If we're inside the JSON block, collect the lines
        if inside_json_block:
            json_lines.append(line)

    # If we never found a JSON code block, fallback to any JSON-like content
    if not json_lines:
        # Fallback: Try a regex that finds any JSON-like object in the text
        fallback_pattern = r"\{.*?\}"
        matches = re.findall(fallback_pattern, llm_output, re.DOTALL)
        for candidate in matches:
            candidate = candidate.strip()
            if candidate:
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # Attempt to clean control characters and re-try
                    candidate_clean = re.sub(r"[\x00-\x1F\x7F]", "", candidate)
                    try:
                        return json.loads(candidate_clean)
                    except json.JSONDecodeError:
                        continue
        return None

    # Join all lines in the JSON block into a single string
    json_string = "\n".join(json_lines).strip()

    # Try to parse the collected JSON lines
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        # Attempt to remove invalid control characters and re-parse
        json_string_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_string)
        try:
            return json.loads(json_string_clean)
        except json.JSONDecodeError:
            return None
