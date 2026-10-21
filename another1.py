from groq import Groq
import json
import os
import subprocess
import psutil

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Use a free-tier model on Groq with native tool-calling capabilities 
MODEL_NAME = "qwen/qwen3.8-276"
def echo_fun(content: str):
    return content
TOOLS =[echo_fun]
SYSTEMPROMPT = """
You are a local echo-management assistant. Use the available tools to create, rename, delete and list files.
"""
def run_agent():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Local Qwen3 File Agent")
    print("Type 'exit' to quit.")
    while True:
        prompt = input("\nEnter file details: "),strip()
        if prompt.lower() == "exit":
            break
        if not prompt: 
            continue
        messages.append({"role": "user", "content": prompt})
        while True:
            response = client.chat(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOLS,
            )
            messages.append(response.message)
            if not response.message.tool_calls:
                print("Agent:", response.message.content)
                break
            for call in response.message.tool_calls:
                name = call.tool_name
                args = call.function.arguments