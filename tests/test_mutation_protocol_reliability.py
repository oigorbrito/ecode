"""Deterministic protocol qualification; no model or shell execution."""
import ast
import hashlib
import json
import os
from pathlib import Path

import pytest

import llm_withtools as tools
from prompts.tooluse_prompt import get_tooluse_prompt


def registry(calls):
    def spy(**kwargs):
        calls.append(kwargs)
        return 'TOOL_OK'
    return {name: {'function': spy} for name in ('bash', 'editor')}


@pytest.mark.parametrize('name', ['edit', 'file', 'file_read', 'file_write'])
def test_unknown_names_remain_rejected_and_diagnosed(name):
    calls = []
    registered = registry(calls)
    payload = {'command': 'edit', 'path': '/repo/candidate.py', 'file_text': 'exact\n'}
    response = '<tool_use>' + repr({'tool_name': name, 'tool_input': payload}) + '</tool_use>'
    parsed = tools.check_for_tool_use(response, 'qwen2.5-coder:3b')
    assert parsed == {'tool_name': name, 'tool_input': payload}
    assert tools.process_tool_call(registered, name, parsed['tool_input']) == (
        f"Error: Tool '{name}' not found. Available tools: bash, editor.")
    assert tools.diagnose_manual_tool_response(response, registered) == [
        {'classification': 'UNKNOWN_TOOL', 'tool_name': name, 'block_index': 0}]
    assert calls == []


def test_literal_json_without_envelope_is_observed_but_not_executed():
    calls = []
    registered = registry(calls)
    response = '```json\n' + json.dumps({'tool_name': 'editor', 'tool_input': {
        'command': 'edit', 'path': '/repo/candidate.py', 'file_text': 'edited'}}) + '\n```'
    assert tools.check_for_tool_use(response, 'qwen2.5-coder:3b') is None
    assert tools.diagnose_manual_tool_response(response, registered) == [
        {'classification': 'INVALID_TOOL_ENVELOPE', 'dispatched': False}]
    assert calls == []


def test_multiple_calls_preserve_unknown_and_not_dispatched_events():
    calls = []
    registered = registry(calls)
    proposals = [{'tool_name': name, 'tool_input': {'command': 'edit'}}
                 for name in ('file_read', 'file_write', 'bash')]
    response = '\n'.join('<tool_use>' + repr(p) + '</tool_use>' for p in proposals)
    assert tools.check_for_tool_use(response, 'qwen2.5-coder:3b') == proposals[0]
    events = tools.diagnose_manual_tool_response(response, registered)
    assert [e['classification'] for e in events] == [
        'UNKNOWN_TOOL', 'TOOL_CALL_NOT_DISPATCHED', 'TOOL_CALL_NOT_DISPATCHED']
    assert [e['block_index'] for e in events] == [0, 1, 2]
    assert calls == []


@pytest.mark.parametrize('response', ['edit candidate.py', '<tool_use>not a dict</tool_use>',
                                     '<tool_use>{}</tool_use>'])
def test_prose_or_invalid_envelopes_cannot_dispatch(response):
    calls = []
    assert tools.check_for_tool_use(response, 'qwen2.5-coder:3b') is None
    events = tools.diagnose_manual_tool_response(response, registry(calls))
    assert all(e['classification'] == 'INVALID_TOOL_ENVELOPE' for e in events)
    assert calls == []


def test_valid_payload_dispatches_exactly_once_without_changes():
    calls = []
    registered = registry(calls)
    proposal = {'tool_name': 'editor', 'tool_input': {
        'command': 'edit', 'path': '/repo/candidate.py', 'file_text': 'exact\n'}}
    response = '<tool_use>' + repr(proposal) + '</tool_use>'
    assert tools.diagnose_manual_tool_response(response, registered) == []
    parsed = tools.check_for_tool_use(response, 'qwen2.5-coder:3b')
    assert tools.process_tool_call(registered, parsed['tool_name'], parsed['tool_input']) == 'TOOL_OK'
    assert calls == [proposal['tool_input']]


def test_manual_loop_keeps_invalid_envelope_terminal_without_retry(monkeypatch):
    calls = []
    model_calls = []
    registered = registry(calls)
    monkeypatch.setattr(tools, 'load_all_tools', lambda **kw: [
        {'info': {'name': name}, **tool} for name, tool in registered.items()])
    monkeypatch.setattr(tools, 'create_client', lambda model: (object(), model))
    def respond(**kwargs):
        model_calls.append(kwargs)
        return ('```json\n' + json.dumps({'tool_name': 'editor', 'tool_input': {}}) + '\n```', [])
    monkeypatch.setattr(tools, 'get_response_from_llm', respond)
    logs = []
    tools.chat_with_agent_manualtools('task', 'qwen2.5-coder:3b', logging=logs.append)
    assert len(model_calls) == 1
    assert calls == []
    assert any('INVALID_TOOL_ENVELOPE' in line for line in logs)


def test_prompt_uses_real_schemas_and_parseable_examples():
    prompt = get_tooluse_prompt()
    assert 'Available tool names: bash, editor.' in prompt
    assert 'ONE tool call per response' in prompt
    assert 'view, create, or edit' in prompt
    assert 'class BashSession' not in prompt
    assert 'def tool_function' not in prompt
    for block in tools.re.findall(r'<tool_use>(.*?)</tool_use>', prompt, tools.re.DOTALL):
        if block == '...':
            continue
        # The introductory notation is not itself a literal proposal.
        try:
            proposal = ast.literal_eval(block)
        except (ValueError, SyntaxError):
            continue
        assert proposal['tool_name'] in ('bash', 'editor')
        assert isinstance(proposal['tool_input'], dict)


def patch_description(path):
    # Extract the production helper only; no benchmark/provider imports.
    source = Path(__file__).resolve().parents[1] / 'self_improve_step.py'
    node = next(n for n in ast.parse(source.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == 'describe_mutation_patch')
    namespace = {'os': os, 'hashlib': hashlib}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['describe_mutation_patch'](str(path))


def test_nonempty_patch_preserves_mutation_ready_hash(tmp_path):
    path = tmp_path / 'model.patch'
    content = b'diff --git a/candidate.py b/candidate.py\n'
    path.write_bytes(content)
    assert patch_description(path) == {'status': 'MUTATION_READY', 'model_patch_file': str(path),
                                      'model_patch_sha256': hashlib.sha256(content).hexdigest()}


@pytest.mark.parametrize('content', [b'', b' \n\t'])
def test_empty_patch_reports_factual_state_without_candidate(tmp_path, content):
    path = tmp_path / 'model.patch'
    path.write_bytes(content)
    result = patch_description(path)
    assert result == {'status': 'PATCH_EMPTY', 'mutation_diagnostic': {
        'classification': 'PATCH_EMPTY', 'patch_state': 'EMPTY'}}
    assert path.read_bytes() == content


def test_missing_patch_is_not_reported_as_ready(tmp_path):
    result = patch_description(tmp_path / 'missing.patch')
    assert result['status'] == 'PATCH_EMPTY'
    assert result['mutation_diagnostic']['patch_state'] == 'UNREADABLE'
    assert 'model_patch_file' not in result


@pytest.mark.parametrize('content', [b'\xff', '\u2003\n'.encode('utf-8')])
def test_invalid_text_or_unicode_whitespace_cannot_be_ready(tmp_path, content):
    path = tmp_path / 'model.patch'
    path.write_bytes(content)
    assert patch_description(path)['status'] == 'PATCH_EMPTY'
    assert path.read_bytes() == content
