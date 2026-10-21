"""A small Ollama chat agent with a safe, harmless demo tool."""

import ollama
from pathlib import Path

MODEL = "qwen3:8b"

# Keep any future file tools inside this directory.
ROOT = Path(r"C:\LocalAI\workspace").resolve()
ROOT.mkdir(parents=True, exist_ok=True)


def safe_path(path: str) -> Path:
    """Resolve a path and prevent access outside the workspace."""
    target = (ROOT / path).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError("Access outside the workspace is prohibited.")
    return target


def echo(message: str) -> str:
    """Repeat a short message when the user asks for an echo."""
    return message


TOOLS = [echo]
TOOL_BY_NAME = {tool.__name__: tool for tool in TOOLS}

SYSTEM_PROMPT = """You are Baburao Ganpatrao Apte from Hera Pheri. Be witty and warm,
with occasional light comic phrasing, while keeping answers useful and clear.
Use the echo tool only when the user asks you to repeat or echo something.
Never claim a tool ran unless its result confirms it."""


def run_agent() -> None:
    """Run an interactive conversation, including any requested tool calls."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"Baburao is ready ({MODEL}). Type 'exit' to quit.")

    while True:
        try:
            prompt = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBaburao: Achha, see you next time!")
            break

        if prompt.lower() in {"exit", "quit"}:
            print("Baburao: Achha, see you next time!")
            break
        if not prompt:
            continue

        turn_start = len(messages)
        messages.append({"role": "user", "content": prompt})

        try:
            # A model may answer directly or request one or more tools.
            while True:
                response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
                message = response.message
                messages.append(message)

                tool_calls = message.tool_calls or []
                if not tool_calls:
                    print(f"\nBaburao: {message.content}")
                    break

                for call in tool_calls:
                    name = call.function.name
                    tool = TOOL_BY_NAME.get(name)
                    if tool is None:
                        result = f"Error: unknown tool '{name}'."
                    else:
                        try:
                            result = tool(**call.function.arguments)
                        except (TypeError, ValueError) as exc:
                            result = f"Error running {name}: {exc}"
                    messages.append({
                        "role": "tool",
                        "tool_name": name,
                        "content": str(result),
                    })
        except Exception as exc:
            # Don't lose the session if Ollama is stopped or a request fails.
            del messages[turn_start:]  # discard this incomplete turn
            print(f"\nCould not reach Ollama ({MODEL}): {exc}")
            print("Check that Ollama is running and the model is available.")


if __name__ == "__main__":
    run_agent()
