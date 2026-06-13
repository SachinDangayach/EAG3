import json
import math
import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# SSL fix: point Python and gRPC at the macOS system CA bundle, which
# includes the corporate (AMAT) root cert injected by the network proxy.
# Without this, requests to Google APIs fail with CERTIFICATE_VERIFY_FAILED.
# ---------------------------------------------------------------------------
_SYS_CERT = "/private/etc/ssl/cert.pem"
os.environ.setdefault("SSL_CERT_FILE", _SYS_CERT)
os.environ.setdefault("REQUESTS_CA_BUNDLE", _SYS_CERT)
os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", _SYS_CERT)

# google-genai is the new Vertex AI SDK (pip install google-genai).
# It replaces the older google-generativeai package.
from google import genai

# ---------------------------------------------------------------------------
# GCP project settings — the model runs on Vertex AI, not the public API,
# so we need a project ID and a region instead of an API key.
# ---------------------------------------------------------------------------
PROJECT_ID = "gcp-prj-dev-gis-dia-01"
LOCATION = "us-central1"
MODEL_ID = "gemini-2.5-flash"

ROOT_DIR = Path(__file__).resolve().parent

# Auto-discover the service account JSON in the project folder.
# The file is set as GOOGLE_APPLICATION_CREDENTIALS so the SDK picks it up
# automatically for all outgoing requests.
json_files = sorted(ROOT_DIR.glob("*.json"))
if not json_files:
    raise FileNotFoundError("No service account JSON file found in the project folder.")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(json_files[0])

# Create a Vertex AI client. vertexai=True switches the SDK from the public
# Gemini API to the enterprise Vertex AI endpoint.
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)


# --- System Prompt ---
system_prompt = """You are a helpful AI agent that can use tools to answer questions accurately.

You have access to the following tools:

1. calculate(expression: str) → str
   Evaluate a mathematical expression. Example: calculate("2**10")

2. get_weather(city: str) → str
   Get the current weather for a city. Example: get_weather("Mumbai")

3. search_notes(query: str) → str
   Search through user's notes. Example: search_notes("meeting agenda")

You must respond in ONE of these two JSON formats:

If you need to use a tool:
{"tool_name": "<name>", "tool_arguments": {"<arg_name>": "<value>"}}

If you have the final answer:
{"answer": "<your final answer>"}

IMPORTANT:
- Respond with ONLY the JSON. No other text.
- Use tools when you need real data or calculations.
- After receiving a tool result, either use another tool or provide your final answer.
"""

# --- Tools ---
def calculate(expression: str) -> str:
    try:
        allowed = {"math": math, "abs": abs, "round": round, "pow": pow}
        # breakpoint()  # <-- inspect the expression before evaluation
        result = eval(expression, {"__builtins__": {}}, allowed)
        return json.dumps({"result": str(result)})
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_weather(city: str) -> str:
    weather_data = {
        "Mumbai": "32°C, Humid, Partly Cloudy",
        "Delhi": "28°C, Clear Sky",
        "London": "15°C, Rainy",
        "New York": "22°C, Sunny",
        "Tokyo": "26°C, Windy",
    }
    weather = weather_data.get(city, f"Weather data not available for {city}")
    return json.dumps({"weather": weather})

def search_notes(query: str) -> str:
    notes = [
        {"title": "Meeting Agenda", "content": "Discuss Q3 targets, review agent architecture"},
        {"title": "Shopping List", "content": "Milk, eggs, bread, coffee"},
        {"title": "Project Ideas", "content": "Build a stock monitoring agent, voice assistant"},
    ]
    results = [n for n in notes if query.lower() in n["title"].lower() or query.lower() in n["content"].lower()]
    return json.dumps({"results": results if results else "No notes found"})

tools = {
    "calculate": calculate,
    "get_weather": get_weather,
    "search_notes": search_notes,
}

# --- Response Parser ---
def parse_llm_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(lines).strip()
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError(f"Could not parse: {text}")

# --- The Agent Loop ---
def run_agent(user_query: str, max_iterations: int = 5):
    print(f"\n{'='*60}")
    print(f"User: {user_query}")
    print(f"{'='*60}")

    # Build initial conversation
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")

        # Build the prompt from message history
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += msg["content"] + "\n\n"
            elif msg["role"] == "user":
                prompt += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n\n"
            elif msg["role"] == "tool":
                prompt += f"Tool Result: {msg['content']}\n\n"
        # print(f"\n{'='*100}")
        # print(f"Prompt to LLM:\n{prompt}")
        # print(f"\n{'='*100}")

# Call the LLM
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            # config={"system_instruction": system_prompt},
        )
        # response = model.generate_content(prompt)
        response_text = response.text
        print(f"LLM Response: {response_text}")

        # Parse the response
        try:
            parsed = parse_llm_response(response_text)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Parse error: {e}")
            print("Asking LLM to try again...")
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": "Please respond with valid JSON only."})
            continue

        # Check if it's a final answer
        if "answer" in parsed:
            print(f"\n{'='*60}")
            print(f"Agent Answer: {parsed['answer']}")
            print(f"{'='*60}")
            return parsed["answer"]

        # It's a tool call
        if "tool_name" in parsed:
            tool_name = parsed["tool_name"]
            tool_args = parsed.get("tool_arguments", {})

            print(f"Calling tool: {tool_name}({tool_args})")

            if tool_name not in tools:
                print(f"Unknown tool: {tool_name}")
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "tool", "content": json.dumps({"error": f"Unknown tool: {tool_name}"})})
                continue

            # Execute the tool
            tool_result = tools[tool_name](**tool_args)
            print(f"Tool Result: {tool_result}")

            # Add to conversation history
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "tool", "content": tool_result})

    print("Max iterations reached. Agent could not complete the task.")
    return None

 # --- Run it! ---
if __name__ == "__main__":
    # # Test 1: Simple tool call
    # run_agent("What is the weather in Mumbai?")

    # # Test 2: Calculation
    # run_agent("What is 2 raised to the power of 10, plus the square root of 144?")

    # # Test 3: Multi-step reasoning
    # run_agent("Search my notes for project ideas, then tell me the weather in Tokyo so I can decide if I should work from a cafe there")

    # Test 4: Something that needs multiple tools
    run_agent("Calculate the sum of exponential values of the first 6 Fibonacci numbers")           