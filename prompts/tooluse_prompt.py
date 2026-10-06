import json

from tools import load_all_tools


def get_tooluse_prompt():
    """Describe actual tools without embedding their implementation source."""
    infos = sorted((tool['info'] for tool in load_all_tools()), key=lambda info: info['name'])
    names = ', '.join(info['name'] for info in infos)
    schemas = json.dumps(infos, indent=2)
    return f"""Available tool names: {names}.
Only tool_use XML envelopes are executed.
Emit exactly ONE tool call per response, then wait for its result.
Use a Python literal dictionary with tool_name and tool_input.
JSON outside this envelope and prose are not executed.
Tool names are exact registry names; operations are fields in tool_input.

For editor, command is view, create, or edit. Use an absolute path.
Prefer view -> localized edit -> verification. Before editing unknown context, view
it. For localized edit, old_text must match exactly once and new_text is literal.
Preserve all unrelated content. Do not send incomplete implementations, omitted
functions, or placeholders. Do not replace code with ... or pass as a placeholder;
legitimate Python pass/Ellipsis, strings, and comments are allowed. Tool content
is written literally: no completion, recovery, or syntax correction occurs.
Legacy file_text overwrites the entire file and should not be used for a local fix.

Complete example: a file contains `def twice(value): return value + 1`.
Inspect it, then replace only its incorrect expression, then verify syntax:
<tool_use>{{'tool_name': 'editor', 'tool_input': {{'command': 'view', 'path': '/repo/math_utils.py'}}}}</tool_use>
<tool_use>{{'tool_name': 'editor', 'tool_input': {{'command': 'edit', 'path': '/repo/math_utils.py', 'old_text': 'return value + 1', 'new_text': 'return value * 2'}}}}</tool_use>
<tool_use>{{'tool_name': 'bash', 'tool_input': {{'command': 'python -m py_compile /repo/math_utils.py'}}}}</tool_use>
Emit these calls in separate responses and wait for each result.

Actual tool descriptions and input schemas:
{schemas}
""".strip()
