from pathlib import Path
import subprocess
import os
import tempfile

def tool_info():
    return {
        "name": "editor",
        "description": """Custom editing tool for viewing, creating, and editing files\n
* State is persistent across command calls and discussions with the user.\n
* If `path` is a file, `view` displays the entire file with line numbers. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep.\n
* The `create` command cannot be used if the specified `path` already exists as a file.\n
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`.\n
* Prefer `view`, then `edit` with `old_text` and `new_text`: replace exactly one literal occurrence. Missing, empty, or ambiguous targets fail without writing. No line-range editing.\n
* `file_text` remains available for whole-file overwrite, mutually exclusive with localized parameters. All supplied text is applied literally, without syntax repair or completion. Prefer minimal edits; preserve unrelated code. Verify afterward.""",
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
                "old_text": {
                    "description": "For localized edit: exact nonempty text already present exactly once in the file. View first.",
                    "type": "string"
                },
                "new_text": {
                    "description": "For localized edit: literal replacement text, including any intended indentation. May be empty.",
                    "type": "string"
                },
                "file_text": {
                    "description": "Required for create or legacy whole-file edit only. Mutually exclusive with old_text/new_text; written literally.",
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

def write_file(path: Path, content: str):
    """Write (overwrite) entire file contents."""
    try:
        path.write_text(content)
    except Exception as e:
        raise ValueError(f"Failed to write file: {e}")

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

def localized_edit(path: Path, old_text: str, new_text: str) -> str:
    """Replace one exact target; preserve other bytes and commit atomically."""
    if not isinstance(old_text, str) or not old_text:
        raise ValueError("Localized edit requires nonempty string old_text.")
    if not isinstance(new_text, str):
        raise ValueError("Localized edit requires string new_text.")
    original = path.read_bytes()
    text = original.decode("utf-8")
    start = text.find(old_text)
    if start < 0:
        raise ValueError("Localized edit target not found; no bytes written.")
    if text.find(old_text, start + 1) >= 0:
        raise ValueError("Localized edit target is ambiguous; no bytes written.")
    updated = (text[:start] + new_text + text[start + len(old_text):]).encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, path.stat().st_mode)
        if path.read_bytes() != original:
            raise ValueError("File changed during localized edit; no replacement committed.")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return f"Localized edit applied literally at {path}; replaced {len(old_text.encode('utf-8'))} bytes with {len(new_text.encode('utf-8'))} bytes."


def tool_function(command: str, path: str, file_text: str = None,
                  old_text: str = None, new_text: str = None) -> str:
    """
    Main tool function that handles:
      - 'view'  : View the entire file or directory listing
      - 'create': Create a new file with the given file_text
      - 'edit'  : Replace one exact old_text with new_text, or legacy file_text overwrite
    """
    try:
        path_obj = validate_path(path, command)

        localized = old_text is not None or new_text is not None
        if localized and command != "edit":
            raise ValueError("old_text/new_text are only valid for edit.")
        if localized and file_text is not None:
            raise ValueError("Choose old_text/new_text or file_text, never both.")
        if command == "view":
            return view_path(path_obj)

        elif command == "create":
            if file_text is None:
                raise ValueError("Missing required `file_text` for 'create' command.")
            write_file(path_obj, file_text)
            return f"File created successfully at: {path}"

        elif command == "edit":
            if localized:
                return localized_edit(path_obj, old_text, new_text)
            if file_text is None:
                raise ValueError("Missing required `file_text` for 'edit' command.")
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
