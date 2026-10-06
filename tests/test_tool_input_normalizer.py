import pytest

from llm_withtools import (
    InvalidToolInput,
    normalize_bash_tool_input,
    process_tool_call_b0,
    process_tool_call,
    process_tool_call_c1,
)


class BashSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, command):
        self.calls.append(command)
        return "BASH_CALLED"


def test_valid_object_is_unchanged():
    value = {"command": "echo X"}

    normalized = normalize_bash_tool_input(value)

    assert normalized is value
    assert normalized == {"command": "echo X"}


def test_string_is_normalized_to_command_object():
    value = " echo X "

    assert normalize_bash_tool_input(value) == {"command": value}


def test_empty_string_is_rejected():
    with pytest.raises(InvalidToolInput):
        normalize_bash_tool_input("")


def test_whitespace_string_is_rejected():
    with pytest.raises(InvalidToolInput):
        normalize_bash_tool_input("   ")


def test_none_is_rejected():
    with pytest.raises(InvalidToolInput):
        normalize_bash_tool_input(None)


def test_wrong_object_shape_is_rejected():
    with pytest.raises(InvalidToolInput):
        normalize_bash_tool_input({"cmd": "echo X"})


def test_extra_object_fields_are_rejected():
    with pytest.raises(InvalidToolInput):
        normalize_bash_tool_input({"command": "echo X", "unexpected": True})


def test_nested_command_is_rejected():
    with pytest.raises(InvalidToolInput):
        normalize_bash_tool_input({"command": {"nested": "echo X"}})


@pytest.mark.parametrize(
    "value",
    [[], 123, True, {"command": ""}, {"command": "   "}, {"command": None},
     {"command": 123}],
)
def test_other_non_object_types_are_rejected(value):
    with pytest.raises(InvalidToolInput):
        normalize_bash_tool_input(value)


def test_c1_normalizes_string_before_bash_dispatch():
    bash = BashSpy()

    result = process_tool_call_c1({"bash": {"function": bash}}, "bash", "echo X")

    assert result == "BASH_CALLED"
    assert bash.calls == ["echo X"]


def test_c1_does_not_normalize_other_tools():
    calls = []

    def editor(command):
        calls.append(command)
        return "EDITOR_CALLED"

    result = process_tool_call_c1({"editor": {"function": editor}}, "editor", "echo X")

    assert result.startswith("Error executing tool 'editor':")
    assert calls == []


def test_existing_valid_dispatch_still_executes():
    for dispatch in (process_tool_call_b0, process_tool_call_c1):
        bash = BashSpy()
        result = dispatch({"bash": {"function": bash}}, "bash", {"command": "echo X"})
        assert result == "BASH_CALLED"
        assert bash.calls == ["echo X"]


@pytest.mark.parametrize(
    "value",
    ["", "   ", None, {"cmd": "echo X"}, {"command": "echo X", "unexpected": True},
     {"command": {"nested": "echo X"}}, [], 123, True],
)
def test_c1_invalid_payload_never_reaches_bash(value):
    bash = BashSpy()

    result = process_tool_call_c1({"bash": {"function": bash}}, "bash", value)

    assert result.startswith("Error executing tool 'bash':")
    assert bash.calls == []


def test_b0_nested_payload_is_not_silently_rewritten():
    bash = BashSpy()
    value = {"command": {"nested": "echo X"}}

    result = process_tool_call_b0({"bash": {"function": bash}}, "bash", value)

    assert result == "BASH_CALLED"
    assert bash.calls == [{"nested": "echo X"}]


def test_production_dispatcher_is_promoted_to_c1():
    assert process_tool_call is process_tool_call_c1


def test_production_dispatcher_normalizes_bash_string():
    bash = BashSpy()

    result = process_tool_call({"bash": {"function": bash}}, "bash", "echo X")

    assert result == "BASH_CALLED"
    assert bash.calls == ["echo X"]
