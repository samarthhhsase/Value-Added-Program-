
import json
import os
from pathlib import Path
from groq import Groq


def load_local_env():
    """Load KEY=value entries from the .env beside this script."""
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


# Load .env before initializing the Groq client. Keep the key out of source code.
load_local_env()
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("Set the GROQ_API_KEY environment variable.")

client = Groq(api_key=api_key)

MODEL_NAME = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """
You are an echo assistant.
Use the echo tool whenever the user asks you to echo text.
For other requests, respond normally.
"""

# Python tool
def echo_fun(content: str):
    return content

# Groq native tool definition
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "echo_fun",
            "description": "Echo the supplied text exactly as provided.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Text to echo"
                    }
                },
                "required": ["content"],
                "additionalProperties": False
            }
        }
    }
]

# Map tool names to Python functions
TOOL_FUNCTIONS = {
    "echo_fun": echo_fun
}


def run_agent():
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    print("Groq Echo Agent")
    print("Type 'exit' to quit.")

    while True:
        prompt = input("\nEnter message: ").strip()

        if prompt.lower() == "exit":
            break

        if not prompt:
            continue

        messages.append({"role": "user", "content": prompt})

        while True:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # Preserve the assistant message and its tool calls
            messages.append(assistant_message.model_dump(exclude_none=True))

            if not assistant_message.tool_calls:
                print("\nAgent:", assistant_message.content or "")
                break

            # Execute each requested tool
            for call in assistant_message.tool_calls:
                name = call.function.name

                try:
                    args = json.loads(call.function.arguments)
                    tool = TOOL_FUNCTIONS.get(name)

                    if tool is None:
                        raise ValueError(f"Unknown tool: {name}")

                    result = tool(**args)

                except Exception as exc:
                    result = f"Error: {exc}"

                print(f"\n[Tool: {name}]")
                print(result)

                # Return the tool result to the model
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result)
                })


if __name__ == "__main__":
    run_agent()
