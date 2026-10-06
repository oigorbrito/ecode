"""Exact localized editor contract, no provider calls."""
import ast
import re
import pytest
from tools import edit
import llm_withtools as dispatcher
from prompts.tooluse_prompt import get_tooluse_prompt


def call(path, **kwargs):
    return edit.tool_function('edit', str(path), **kwargs)


def test_preserves_unrelated_bytes_utf8_and_crlf(tmp_path):
    p=tmp_path/'a.py';original='α = 1\r\ndef twice(x):\r\n    return x + 1\r\n# preserved\r\n'.encode();p.write_bytes(original)
    p.chmod(0o640)
    assert 'Localized edit applied literally' in call(p,old_text='return x + 1',new_text='return x * 2')
    assert p.read_bytes()==original.replace(b'return x + 1',b'return x * 2')
    assert p.stat().st_mode & 0o777 == 0o640


@pytest.mark.parametrize('content,target', [('abc','missing'),('abc abc','abc'),('aaaa','aaa'),('abc','')])
def test_missing_empty_or_ambiguous_target_fails_closed(tmp_path,content,target):
    p=tmp_path/'a';p.write_text(content)
    assert call(p,old_text=target,new_text='replacement').startswith('Error:')
    assert p.read_text()==content
    assert list(tmp_path.iterdir())==[p]


@pytest.mark.parametrize('replacement',['Your modified code goes here.','def broken(:','pass','...','Ellipsis','"..."','# ...'])
def test_literal_content_without_autocorrection_or_placeholder_detector(tmp_path,replacement):
    p=tmp_path/'a.py';p.write_text('prefix\nTARGET\nsuffix\n')
    assert not call(p,old_text='TARGET',new_text=replacement).startswith('Error:')
    assert p.read_text()=='prefix\n'+replacement+'\nsuffix\n'


def test_empty_replacement_and_view_before_edit(tmp_path):
    p=tmp_path/'a';p.write_text('left TARGET right')
    assert 'left TARGET right' in edit.tool_function('view',str(p))
    assert not call(p,old_text='TARGET',new_text='').startswith('Error:')
    assert p.read_text()=='left  right'


def test_atomic_failure_preserves_original_and_removes_temporary(tmp_path,monkeypatch):
    p=tmp_path/'a';p.write_bytes(b'left target right')
    def denied(*args):raise OSError('replace denied')
    monkeypatch.setattr(edit.os,'replace',denied)
    assert 'replace denied' in call(p,old_text='target',new_text='changed')
    assert p.read_bytes()==b'left target right'
    assert list(tmp_path.iterdir())==[p]


@pytest.mark.parametrize('kwargs',[{'old_text':'a'}, {'new_text':'b'}, {'old_text':'a','new_text':'b','file_text':'c'}])
def test_incomplete_or_conflicting_modes_do_not_write(tmp_path,kwargs):
    p=tmp_path/'a';p.write_text('a')
    assert call(p,**kwargs).startswith('Error:')
    assert p.read_text()=='a'


def test_legacy_whole_file_is_literal_and_still_available(tmp_path):
    p=tmp_path/'a';p.write_text('old')
    assert 'overwritten' in call(p,file_text='exact text')
    assert p.read_text()=='exact text'


def test_actual_parser_dispatcher_localized_edit(tmp_path):
    p=tmp_path/'a.py';p.write_text('def twice(value): return value + 1\n')
    registry={'editor':{'function':edit.tool_function}}
    proposal={'tool_name':'editor','tool_input':{'command':'edit','path':str(p),'old_text':'return value + 1','new_text':'return value * 2'}}
    parsed=dispatcher.check_for_tool_use('<tool_use>'+repr(proposal)+'</tool_use>','qwen2.5-coder:3b')
    assert parsed==proposal
    assert 'Localized edit applied literally' in dispatcher.process_tool_call(registry,'editor',parsed['tool_input'])
    assert p.read_text()=='def twice(value): return value * 2\n'
    assert 'not found' in dispatcher.process_tool_call(registry,'edit',proposal['tool_input'])
    assert dispatcher.check_for_tool_use(repr(proposal),'qwen2.5-coder:3b') is None
    assert p.read_text()=='def twice(value): return value * 2\n'


def test_prompt_examples_use_real_schema_and_complete_localized_content(tmp_path):
    prompt=get_tooluse_prompt();schema=edit.tool_info()['input_schema']['properties']
    examples=[]
    for block in re.findall(r'<tool_use>(.*?)</tool_use>',prompt,re.S):
        try:examples.append(ast.literal_eval(block))
        except (ValueError,SyntaxError):continue
    assert len(examples)==3
    assert 'complete file content' not in prompt
    assert 'old_text' in schema and 'new_text' in schema
    assert 'view -> localized edit -> verification' in prompt
    proposal=examples[1];assert proposal['tool_name']=='editor'
    assert set(proposal['tool_input']) <= set(schema)
    assert proposal['tool_input']['old_text']=='return value + 1'
    assert proposal['tool_input']['new_text']=='return value * 2'
    p=tmp_path/'math_utils.py';p.write_text('def twice(value): return value + 1\n')
    payload={**proposal['tool_input'],'path':str(p)}
    assert not edit.tool_function(**payload).startswith('Error:')
    assert p.read_text()=='def twice(value): return value * 2\n'