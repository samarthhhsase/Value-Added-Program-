"""Groq-powered local file assistant with workspace-scoped tools."""

import json
import os
from pathlib import Path

from groq import Groq


MODEL_NAME = "llama-3.3-70b-versatile"
ROOT = (Path(__file__).resolve().parent / "workspace").resolve()
ROOT.mkdir(parents=True, exist_ok=True)


def load_local_env() -> None:
    """Read simple KEY=VALUE entries without printing secrets or requiring a package."""
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def safe_path(path: str) -> Path:
    """Resolve a user path and keep it inside the assistant workspace."""
    target = (ROOT / path).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError("Access outside the assistant workspace is prohibited.")
    return target


def create_file(path: str, content: str) -> str:
    target = safe_path(path)
    if target.exists():
        return "Error: a file or folder with that name already exists."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Created file: {path}"


def create_folder(path: str) -> str:
    target = safe_path(path)
    if target.exists():
        return "Error: a file or folder with that name already exists."
    target.mkdir(parents=True, exist_ok=True)
    return f"Created folder: {path}"


def rename_file(old_path: str, new_path: str) -> str:
    source, destination = safe_path(old_path), safe_path(new_path)
    if not source.is_file():
        return "Error: source file does not exist."
    if destination.exists():
        return "Error: destination already exists."
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.rename(destination)
    return f"Renamed {old_path} to {new_path}."


def delete_file(path: str) -> str:
    target = safe_path(path)
    if not target.is_file():
        return "Error: file does not exist."
    answer = input(f"Confirm deletion of {path}? Type 'yes' to delete: ")
    if answer.strip().lower() != "yes":
        return "Deletion cancelled."
    target.unlink()
    return f"Deleted file: {path}"


def list_files(path: str = ".") -> str:
    target = safe_path(path)
    if not target.is_dir():
        return "Error: directory does not exist."
    entries = sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    return "\n".join(
        ("[DIR] " if item.is_dir() else "[FILE] ") + item.name
        for item in entries
    ) or "Directory is empty."


TOOL_FUNCTIONS = {
    "create_file": create_file,
    "create_folder": create_folder,
    "rename_file": rename_file,
    "delete_file": delete_file,
    "list_files": list_files,
}

TOOLS = [
    {"type": "function", "function": {"name": "create_file", "description": "Create a text file in the workspace.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "create_folder", "description": "Create a folder in the workspace.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "rename_file", "description": "Rename or move a file within the workspace.", "parameters": {"type": "object", "properties": {"old_path": {"type": "string"}, "new_path": {"type": "string"}}, "required": ["old_path", "new_path"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "delete_file", "description": "Delete a file after asking for confirmation.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files and folders in a workspace folder.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}, "additionalProperties": False}}},
]

SYSTEM_PROMPT = f"""You are a local file-management assistant. Use tools to manage files only inside the workspace at {ROOT}.
All tool paths are relative to that workspace. Ask for missing details, and never claim an operation succeeded unless its tool confirms it."""


def run_agent() -> None:
    load_local_env()
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Set it in your environment before starting.")
    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"Groq file assistant ({MODEL_NAME})")
    print(f"Workspace: {ROOT}")
    print("Type 'exit' to quit.")

    while True:
        try:
            prompt = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if prompt.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        if not prompt:
            continue

        turn_start = len(messages)
        messages.append({"role": "user", "content": prompt})
        try:
            while True:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                )
                message = response.choices[0].message
                assistant_message = message.model_dump(exclude_none=True)
                messages.append(assistant_message)
                if not message.tool_calls:
                    print(f"\nAssistant: {message.content or ''}")
                    break

                for call in message.tool_calls:
                    name = call.function.name
                    tool = TOOL_FUNCTIONS.get(name)
                    if tool is None:
                        result = f"Error: unknown tool '{name}'."
                    else:
                        try:
                            arguments = json.loads(call.function.arguments or "{}")
                            result = tool(**arguments)
                        except (TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
                            result = f"Error running {name}: {exc}"
                    print(f"\n[{name}] {result}")
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})
        except Exception as exc:
            del messages[turn_start:]
            print(f"\nGroq request failed: {exc}")


if __name__ == "__main__":
    run_agent()
