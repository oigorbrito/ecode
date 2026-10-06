from pathlib import Path
import ast
import os
import subprocess
import tempfile

def tool_info():
    return {
        "name": "editor",
        "description": """Custom editing tool for viewing, creating, and editing files\n
* State is persistent across command calls and discussions with the user.\n
* If `path` is a file, `view` displays the entire file with line numbers. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep.\n
* The `create` command cannot be used if the specified `path` already exists as a file.\n
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`.\n
* The `edit` command overwrites the entire file with the provided `file_text`.\n
* No partial/line-range edits or partial viewing are supported.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["view", "create", "edit"],
                    "description": "The command to run: `view`, `create`, or `edit`."
                },
                "path": {
                    "description": "Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.",
                    "type": "string"
                },
                "file_text": {
                    "description": "Content for create or full-file edit. Mutually exclusive with old_text/new_text.",
                    "type": "string"
                },
                "old_text": {
                    "description": "Exact existing text to replace once during a localized edit.",
                    "type": "string"
                },
                "new_text": {
                    "description": "Replacement text for old_text during a localized edit.",
                    "type": "string"
                }
            },
            "required": ["command", "path"]
        }
    }

def maybe_truncate(content: str, max_length: int = 10000) -> str:
    """Truncate long content and add marker."""
    if len(content) > max_length:
        return content[:max_length] + "\n<response clipped>"
    return content

def validate_path(path: str, command: str) -> Path:
    """
    Validate the file path for each command:
      - 'view': path may be a file or directory; must exist.
      - 'create': path must not exist (for new file creation).
      - 'edit': path must exist (for overwriting).
    """
    path_obj = Path(path)

    # Check if it's an absolute path
    if not path_obj.is_absolute():
        raise ValueError(
            f"The path {path} is not an absolute path (must start with '/')."
        )

    if command == "view":
        # Path must exist
        if not path_obj.exists():
            raise ValueError(f"The path {path} does not exist.")
    elif command == "create":
        # Path must not exist
        if path_obj.exists():
            raise ValueError(f"Cannot create new file; {path} already exists.")
    elif command == "edit":
        # Path must exist and must be a file
        if not path_obj.exists():
            raise ValueError(f"The file {path} does not exist.")
        if path_obj.is_dir():
            raise ValueError(f"{path} is a directory and cannot be edited as a file.")
    else:
        raise ValueError(
            f"Unknown or unsupported command: {command}. "
            "Valid commands: view, create, edit."
        )

    return path_obj

def format_output(content: str, path: str, init_line: int = 1) -> str:
    """Format output with line numbers (for file content)."""
    content = maybe_truncate(content)
    content = content.expandtabs()
    numbered_lines = [
        f"{i + init_line:6}\t{line}"
        for i, line in enumerate(content.split("\n"))
    ]
    return f"Here's the result of running `cat -n` on {path}:\n" + "\n".join(numbered_lines) + "\n"

def read_file(path: Path) -> str:
    """Read and return the entire file contents."""
    try:
        return path.read_text()
    except Exception as e:
        raise ValueError(f"Failed to read file: {e}")

def _validate_candidate(path: Path, content: str) -> None:
    """Reject syntactically invalid Python before touching the target."""
    if path.suffix == ".py":
        try:
            ast.parse(content, filename=str(path))
        except SyntaxError as e:
            raise ValueError(
                f"Python syntax validation failed at line {e.lineno}: {e.msg}"
            ) from e


def write_file(path: Path, content: str):
    """Validate and atomically replace a file in its existing directory."""
    _validate_candidate(path, content)
    temp_name = None
    try:
        mode = path.stat().st_mode if path.exists() else None
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temp_name, mode)
        os.replace(temp_name, path)
        temp_name = None
    except Exception as e:
        raise ValueError(f"Failed to write file: {e}") from e
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

def view_path(path_obj: Path) -> str:
    """View the entire file contents or directory listing."""
    if path_obj.is_dir():
        # For directories: list non-hidden files up to 2 levels deep
        try:
            result = subprocess.run(
                ['find', str(path_obj), '-maxdepth', '2', '-not', '-path', '*/\\.*'],
                capture_output=True,
                text=True
            )
            if result.stderr:
                return f"Error listing directory: {result.stderr}"
            return (
                f"Here's the files and directories up to 2 levels deep in {path_obj}, excluding hidden items:\n"
                + result.stdout
            )
        except Exception as e:
            raise ValueError(f"Failed to list directory: {e}")

    # If it's a file, show the entire file with line numbers
    content = read_file(path_obj)
    return format_output(content, str(path_obj))

def tool_function(
    command: str,
    path: str,
    file_text: str = None,
    old_text: str = None,
    new_text: str = None,
) -> str:
    """
    Main tool function that handles:
      - 'view'  : View the entire file or directory listing
      - 'create': Create a new file with the given file_text
      - 'edit'  : Full replacement with file_text, or one exact old_text/new_text replacement
    """
    try:
        path_obj = validate_path(path, command)

        if command == "view":
            return view_path(path_obj)

        elif command == "create":
            if file_text is None:
                raise ValueError("Missing required `file_text` for 'create' command.")
            write_file(path_obj, file_text)
            return f"File created successfully at: {path}"

        elif command == "edit":
            localized = old_text is not None or new_text is not None
            if localized and file_text is not None:
                raise ValueError(
                    "Use either `file_text` or `old_text`/`new_text`, not both."
                )
            if localized:
                if old_text is None or new_text is None:
                    raise ValueError(
                        "Localized edit requires both `old_text` and `new_text`."
                    )
                if old_text == "":
                    raise ValueError("`old_text` must not be empty.")
                current = read_file(path_obj)
                occurrences = current.count(old_text)
                if occurrences != 1:
                    raise ValueError(
                        "Localized edit requires exactly one match for `old_text`; "
                        f"found {occurrences}."
                    )
                candidate = current.replace(old_text, new_text, 1)
                write_file(path_obj, candidate)
                return f"File at {path} updated by one exact localized replacement."
            if file_text is None:
                raise ValueError(
                    "Edit requires `file_text` or both `old_text` and `new_text`."
                )
            write_file(path_obj, file_text)
            return f"File at {path} has been overwritten with new content."

        else:
            raise ValueError(f"Unknown command: {command}")

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Example usage
    result = tool_function("view", "./coding_agent.py", view_range=[1, 10])
    print(result)
