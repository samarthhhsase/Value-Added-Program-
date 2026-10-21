"""
Minimal Ollama agent with a single tool: echo.
"""

from nbconvert import export
import ollama

MODEL = "qwen3:8b"
MAX_STEPS = 4


def UPPERCASE(text: str) -> str:
    """Return the given text in uppercase.
    Args:
        text: The text to convert to uppercase.
    """
    return text.upper()

def echo(text: str) -> str:
    """Return the given text unchanged.
    Args:
        text: The text to echo back.
    """
    return text


TOOLS = [echo, UPPERCASE]

SYSTEM_PROMPT = """
You are an echo agent.
When the user wants something repeated or echoed, call the echo tool with
exactly that text, then reply with the tool's result.
Never claim to have echoed anything unless the tool returned it.
You also return the text in UPPERCASE if the user asks for it, by calling the UPPERCASE tool.
"""

def run_agent():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("Echo Agent (type 'exit' to quit)")

    while True:
        prompt = input("\nYou: ").strip()
        if prompt.lower() == "exit":
            break
        if not prompt:
            continue

        messages.append({"role": "user", "content": prompt})

        for _ in range(MAX_STEPS):
            response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
            messages.append(response.message)

            if not response.message.tool_calls:
                print("\nAgent:", response.message.content)
                break

            for call in response.message.tool_calls:
                name = call.function.name
                args = call.function.arguments

                if name == "UPPERCASE":
                    try:
                        result = UPPERCASE(**args)
                    except Exception as exc:
                        result = f"Error: {exc}"
                elif name == "echo":
                    try:
                        result = echo(**args)
                    except Exception as exc:
                        result = f"Error: {exc}"
                else:
                    result = "Error: Unknown tool."
                if result is not None:  
                    print(f"\n[Tool: {name}] {result}")
                    messages.append(
                    {"role": "tool", "tool_name": name, "content": str(result)}
                )
        else:
            print("\nAgent: Stopped: step limit reached.")


if __name__ == "__main__":
    run_agent()