"""
Agentic loop over example_mcp_server.py — Gemini (Vertex AI) version.

Same structure as AgenticMCPUsageOllama.py. The ONLY real difference is the
LLM call: instead of Ollama, we hit the Vertex AI Gemini endpoint. Everything
else — tool discovery, FUNCTION_CALL/FINAL_ANSWER protocol, loop — is
identical, to drive home the point that "the router can be any LLM".

Setup:
  1. Place your service-account JSON in this folder (auto-discovered).
  2. pip install google-genai python-dotenv mcp

Run:
  python AgenticMCPUse.py
"""

import asyncio
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# SSL fix: point Python and gRPC at the macOS system CA bundle, which
# includes the root cert injected by the network proxy.
# Without this, requests to Google APIs fail with CERTIFICATE_VERIFY_FAILED.
# ---------------------------------------------------------------------------
_SYS_CERT = "/private/etc/ssl/cert.pem"
os.environ.setdefault("SSL_CERT_FILE", _SYS_CERT)
os.environ.setdefault("REQUESTS_CA_BUNDLE", _SYS_CERT)
os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", _SYS_CERT)

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

# ---------------------------------------------------------------------------
# Vertex AI / Gemini settings
# ---------------------------------------------------------------------------
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION   = os.environ["GCP_LOCATION"]
MODEL_ID   = os.environ["GCP_MODEL_ID"]

ROOT_DIR = Path(__file__).resolve().parent

# Auto-discover the service account JSON in the project folder.
json_files = sorted(ROOT_DIR.glob("*.json"))
if not json_files:
    raise FileNotFoundError("No service account JSON file found in the project folder.")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(json_files[0])

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)

MAX_ITERATIONS   = 6
LLM_SLEEP_SECONDS = 0


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def call_gemini(prompt: str) -> str:
    """Blocking Vertex AI call — returns the model's text."""
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
    )
    return response.text


async def generate(prompt: str) -> str:
    """Run the blocking Gemini call in a thread so the event loop stays free."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, call_gemini, prompt)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def describe_tools(tools) -> str:
    lines = []
    for i, t in enumerate(tools, 1):
        props = (t.inputSchema or {}).get("properties", {})
        params = ", ".join(f"{n}: {p.get('type', '?')}" for n, p in props.items()) or "no params"
        lines.append(f"{i}. {t.name}({params}) — {t.description or ''}")
    return "\n".join(lines)


def coerce(value: str, schema_type: str):
    if schema_type == "integer":
        return int(value)
    if schema_type == "number":
        return float(value)
    if schema_type == "array":
        return eval(value)
    if schema_type == "boolean":
        return value.lower() in ("true", "1", "yes")
    return value


def first_directive(text: str) -> str:
    """Pick the first line that looks like our protocol (FUNCTION_CALL / FINAL_ANSWER).
    Gemini sometimes pads with extra prose; this keeps the parser robust.
    """
    for line in (text or "").splitlines():
        s = line.strip().lstrip("`").lstrip()
        if s.startswith("FUNCTION_CALL:") or s.startswith("FINAL_ANSWER:"):
            return s
    return (text or "").strip()


# ---------------------------------------------------------------------------
# Main agentic loop
# ---------------------------------------------------------------------------

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["example_mcp_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(f"Connected to example_mcp_server — routing via Gemini ({MODEL_ID})")

            tools = (await session.list_tools()).tools
            tools_desc = describe_tools(tools)
            print(f"Loaded {len(tools)} tools\n")

            system_prompt = f"""You are a file-manipulation agent working inside a sandboxed MCP server.
You solve tasks by calling tools ONE AT A TIME and observing their results.

Available tools:
{tools_desc}

Respond with EXACTLY ONE line, in one of these two formats:
  FUNCTION_CALL: tool_name|arg1|arg2|...
  FINAL_ANSWER: <short natural-language summary of what you did>

Rules:
- Output only the single directive line. No prose, no markdown, no code fences.
- Provide args in the exact order of the tool's parameters.
- Do not invent tools that are not listed above.
- After each FUNCTION_CALL you'll receive the result; use it to decide the next step.
- Prefer the simplest 2–3 tool sequence that solves the task.
- When the task is complete, emit FINAL_ANSWER.
"""

            task = (
                "Create a file called greeting.txt in the sandbox with the content "
                "'hello rohan'. Then read it back to confirm. Then edit it so "
                "'hello' becomes 'hi'. Finally give a FINAL_ANSWER."
            )

            history: list[str] = []
            for iteration in range(1, MAX_ITERATIONS + 1):
                print(f"\n--- Iteration {iteration} ---")

                context = "\n".join(history) if history else "(no prior steps)"
                prompt = (
                    f"{system_prompt}\n"
                    f"Task: {task}\n\n"
                    f"Previous steps:\n{context}\n\n"
                    f"What is your next single action?"
                )

                if LLM_SLEEP_SECONDS:
                    await asyncio.sleep(LLM_SLEEP_SECONDS)

                try:
                    raw = await generate(prompt)
                except Exception as e:
                    print(f"Gemini error: {e}")
                    break

                text = first_directive(raw)
                print(f"LLM: {text}")

                if text.startswith("FINAL_ANSWER:"):
                    print("\n=== Agent done ===")
                    print(text)
                    break

                if not text.startswith("FUNCTION_CALL:"):
                    print("Unexpected response format — stopping.")
                    print(f"Raw model output:\n{raw}")
                    break

                _, call = text.split(":", 1)
                parts = [p.strip() for p in call.split("|")]
                func_name, raw_args = parts[0], parts[1:]

                tool = next((t for t in tools if t.name == func_name), None)
                if tool is None:
                    msg = f"Unknown tool {func_name!r}"
                    print(msg)
                    history.append(f"Iteration {iteration}: {msg}")
                    continue

                props = (tool.inputSchema or {}).get("properties", {})
                arguments = {
                    name: coerce(val, info.get("type", "string"))
                    for (name, info), val in zip(props.items(), raw_args)
                }

                print(f"→ {func_name}({arguments})")
                try:
                    result = await session.call_tool(func_name, arguments=arguments)
                    payload = (
                        result.content[0].text
                        if result.content and hasattr(result.content[0], "text")
                        else str(result)
                    )
                except Exception as e:
                    payload = f"ERROR: {e}"

                print(f"← {payload}")
                history.append(
                    f"Iteration {iteration}: called {func_name}({arguments}) → {payload}"
                )
            else:
                print("\nReached MAX_ITERATIONS without FINAL_ANSWER.")


if __name__ == "__main__":
    asyncio.run(main())
