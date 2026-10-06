import json

from prompts.tooluse_prompt import (
    get_tooluse_prompt,
    get_tooluse_prompt_b0,
    get_tooluse_prompt_c1,
)


def _contracts(prompt):
    prefix = "You have these tools:\n"
    payload = prompt[len(prefix):].split("\n\nCall exactly one tool at a time using:\n", 1)[0]
    return json.loads(payload)


def test_c1_is_default_candidate():
    assert get_tooluse_prompt() == get_tooluse_prompt_c1()


def test_c1_removes_tool_implementation_source():
    prompt = get_tooluse_prompt_c1()

    assert "class BashSession" not in prompt
    assert "subprocess.run" not in prompt
    assert "def tool_function" not in prompt


def test_c1_preserves_exact_tool_contracts():
    contracts = {item["name"]: item for item in _contracts(get_tooluse_prompt_c1())}

    assert set(contracts) == {"bash", "editor"}
    assert contracts["bash"]["input_schema"]["required"] == ["command"]
    assert contracts["editor"]["input_schema"]["required"] == ["command", "path"]
    assert contracts["editor"]["input_schema"]["properties"]["command"]["enum"] == [
        "view", "create", "edit"
    ]


def test_c1_materially_reduces_static_tool_prompt():
    b0 = get_tooluse_prompt_b0()
    c1 = get_tooluse_prompt_c1()

    assert len(c1) < len(b0) * 0.60
