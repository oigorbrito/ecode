import json
import os

from tools import load_all_tools


def get_tooluse_prompt_b0():
    """Original source-dump prompt retained as the B0 control."""
    tool_folder = os.path.join(os.path.dirname(__file__), "../tools")
    tool_files = [
        os.path.join(tool_folder, file)
        for file in os.listdir(tool_folder)
        if file.endswith(".py") and file != "__init__.py"
    ]
    tool_file_contents = [open(file).read().strip() for file in tool_files]
    tools_available = [
        f"```python\n{tool_content}\n```"
        for tool_content in tool_file_contents
    ]
    tools_available = "\n\n".join(tools_available)
    return """Here are the available tools:
{tools_available}

Use the available tools in this format:
```
<tool_use>
{{
    'tool_name': ...,
    'tool_input': ...
}}
</tool_use>
```
""".format(tools_available=tools_available).strip()


def get_tooluse_prompt_c1():
    """Expose only model-relevant tool contracts, not implementation source."""
    contracts = []
    for tool in sorted(load_all_tools(), key=lambda item: item["info"]["name"]):
        info = tool["info"]
        contracts.append({
            "name": info["name"],
            "description": info["description"],
            "input_schema": info["input_schema"],
        })

    return (
        "You have these tools:\n"
        + json.dumps(contracts, indent=2, sort_keys=True)
        + "\n\nCall exactly one tool at a time using:\n"
        + "<tool_use>\n"
        + "{'tool_name': '<name>', 'tool_input': {<arguments>}}\n"
        + "</tool_use>\n"
        + "Use only listed tool names and schema fields. "
        + "After a tool result, continue until the task is complete."
    )


def get_tooluse_prompt():
    """Select the frozen Arena-1 prompt profile without editing code between cells."""
    profile = os.getenv("ECODE_TOOL_PROMPT_PROFILE", "C1").upper()
    if profile == "B0":
        return get_tooluse_prompt_b0()
    if profile == "C1":
        return get_tooluse_prompt_c1()
    raise ValueError(
        "ECODE_TOOL_PROMPT_PROFILE must be B0 or C1; "
        f"received {profile!r}"
    )
