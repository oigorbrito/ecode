import json

import pytest

from llm_withtools import check_for_tool_use, process_tool_call
from tools.edit import tool_function


@pytest.fixture(autouse=True)
def select_c1_treatment(monkeypatch):
    monkeypatch.setenv("ECODE_TOOL_PROMPT_PROFILE", "C1")


@pytest.mark.parametrize("value", [
    "candidate.py", "view candidate.py", "edit /tmp/fixture/candidate.py",
    "def add_one(value):\n    return value + 1",
    json.dumps({"command": "edit", "path": "/tmp/fixture/candidate.py",
                "file_text": "def add_one(value):\n    return value + 1"}),
])
def test_editor_strings_are_rejected_without_guessing(value):
    calls = []

    def editor(command, path, file_text=None):
        calls.append((command, path, file_text))

    result = process_tool_call({"editor": {"function": editor}}, "editor", value)

    assert result.startswith("Error executing tool 'editor':")
    assert calls == []


def test_editor_valid_object_is_dispatched_without_rewriting():
    calls = []

    def editor(command, path, file_text=None):
        calls.append((command, path, file_text))
        return "EDITOR_CALLED"

    value = {"command": "edit", "path": "/tmp/fixture/candidate.py",
             "file_text": "exact content\n"}

    assert process_tool_call({"editor": {"function": editor}}, "editor", value) == "EDITOR_CALLED"
    assert calls == [("edit", "/tmp/fixture/candidate.py", "exact content\n")]


@pytest.mark.parametrize("name", ["edit", "nano", "unknown"])
def test_unknown_tool_lists_actual_available_names_without_dispatch(name):
    calls = []

    def spy(**kwargs):
        calls.append(kwargs)

    result = process_tool_call(
        {"editor": {"function": spy}, "bash": {"function": spy}}, name,
        {"command": "edit", "path": "/tmp/fixture/candidate.py"},
    )

    assert result == f"Error: Tool '{name}' not found. Available tools: bash, editor."
    assert calls == []


def test_available_tool_feedback_uses_registry_not_hardcoded_names():
    result = process_tool_call({"custom": {"function": lambda: None}}, "missing", {})
    assert result == "Error: Tool 'missing' not found. Available tools: custom."


@pytest.mark.parametrize("operation", ["nano", "unknown", ""])
def test_invalid_editor_operation_lists_valid_commands_without_writing(tmp_path, operation):
    path = tmp_path / "candidate.py"
    path.write_text("parent")
    result = tool_function(operation, str(path), file_text="candidate")

    assert "Valid commands: view, create, edit." in result
    assert path.read_text() == "parent"


@pytest.mark.parametrize("operation", ["view", "edit"])
def test_missing_editor_path_is_factual_and_is_not_redirected(tmp_path, operation):
    missing = tmp_path / "missing.py"
    other = tmp_path / "candidate.py"
    other.write_text("parent")
    result = tool_function(operation, str(missing), file_text="candidate")

    assert "does not exist" in result
    assert str(missing) in result
    assert not missing.exists()
    assert other.read_text() == "parent"


def test_manual_parser_preserves_observed_editor_string_for_validation():
    response = "<tool_use>{'tool_name': 'editor', 'tool_input': 'edit /tmp/fixture/candidate.py'}</tool_use>"
    assert check_for_tool_use(response, model="qwen2.5-coder:3b") == {
        "tool_name": "editor", "tool_input": "edit /tmp/fixture/candidate.py",
    }


def test_editor_payload_missing_required_path_is_not_dispatched():
    calls = []

    def editor(command, path, file_text=None):
        calls.append((command, path, file_text))

    result = process_tool_call({"editor": {"function": editor}}, "editor", {"command": "edit"})
    assert result.startswith("Error executing tool 'editor':")
    assert calls == []


def test_c1_dispatches_localized_editor_payload_end_to_end(tmp_path):
    path = tmp_path / "candidate.py"
    path.write_text("def value():\n    return 1\n")
    tools = {"editor": {"function": tool_function}}

    result = process_tool_call(
        tools,
        "editor",
        {
            "command": "edit",
            "path": str(path),
            "old_text": "    return 1",
            "new_text": "    return 2",
        },
    )

    assert "localized replacement" in result
    assert path.read_text() == "def value():\n    return 2\n"
