import json
import math
import os
import re
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# SSL fix: point Python at the macOS system CA bundle (includes AMAT corporate cert).
_SYS_CERT = "/private/etc/ssl/cert.pem"
os.environ.setdefault("SSL_CERT_FILE", _SYS_CERT)
os.environ.setdefault("REQUESTS_CA_BUNDLE", _SYS_CERT)
os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", _SYS_CERT)

from google import genai

PROJECT_ID = "gcp-prj-dev-gis-dia-01"
LOCATION = "us-central1"
MODEL_ID = "gemini-2.5-flash"

ROOT_DIR = Path(__file__).resolve().parent
json_files = sorted(ROOT_DIR.glob("*.json"))
if not json_files:
    raise FileNotFoundError("No service account JSON file found in the project folder.")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(json_files[0])

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

system_prompt = """You are a helpful AI agent. You MUST use tools to answer ALL questions. NEVER answer from your own knowledge.

You have access to ONLY these three tools:

1. calculate(expression: str)
   Evaluates a math expression. Use Python syntax.
   Available: math.sqrt, math.pi, math.e, math.log, math.sin, math.cos, math.tan, abs, round, pow
   Example: {"tool_name": "calculate", "tool_arguments": {"expression": "math.sqrt(144) + 2**10"}}

2. convert_currency(amount: float, from_currency: str, to_currency: str)
   Converts between currencies using fixed reference rates.
   Supported codes: USD, EUR, GBP, INR, JPY, AUD, CAD, CHF, CNY, SGD
   Example: {"tool_name": "convert_currency", "tool_arguments": {"amount": 100, "from_currency": "USD", "to_currency": "INR"}}

3. convert_units(value: float, from_unit: str, to_unit: str)
   Converts between measurement units.
   Length: mm, cm, m, km, in, ft, yd, mi
   Weight: mg, g, kg, lb, oz, ton
   Temperature: C, F, K
   Volume: ml, l, gal, qt, pt
   Speed: m_s, km_h, mph
   Example: {"tool_name": "convert_units", "tool_arguments": {"value": 5.5, "from_unit": "km", "to_unit": "mi"}}

ABSOLUTE RULES:
- You MUST call a tool. Never answer from memory or training data.
- Respond ONLY with valid JSON — no text outside the JSON.
- Tool call format:  {"tool_name": "...", "tool_arguments": {...}}
- Final answer format: {"answer": "your answer here"}
- If the question cannot be answered with these three tools, respond:
  {"answer": "I can only help with math calculations, currency conversion, and unit conversion. Please ask something in those areas."}
"""

# --- Currency tool ---
CURRENCY_RATES_VS_USD = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "INR": 83.5,
    "JPY": 149.5, "AUD": 1.53, "CAD": 1.36, "CHF": 0.90,
    "CNY": 7.24, "SGD": 1.34,
}

def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    fc = from_currency.upper()
    tc = to_currency.upper()
    if fc not in CURRENCY_RATES_VS_USD:
        return json.dumps({"error": f"Unknown currency: {fc}. Supported: {', '.join(CURRENCY_RATES_VS_USD)}"})
    if tc not in CURRENCY_RATES_VS_USD:
        return json.dumps({"error": f"Unknown currency: {tc}. Supported: {', '.join(CURRENCY_RATES_VS_USD)}"})
    usd = float(amount) / CURRENCY_RATES_VS_USD[fc]
    converted = round(usd * CURRENCY_RATES_VS_USD[tc], 4)
    return json.dumps({"result": converted, "from": f"{amount} {fc}", "to": f"{converted} {tc}"})

# --- Units tool ---
# Each entry: (dimension, factor_to_base)
# base units: meter, kg, liter, m/s
UNIT_TABLE = {
    "mm": ("length", 0.001), "cm": ("length", 0.01), "m": ("length", 1.0),
    "km": ("length", 1000.0), "in": ("length", 0.0254), "ft": ("length", 0.3048),
    "yd": ("length", 0.9144), "mi": ("length", 1609.344),
    "mg": ("weight", 1e-6), "g": ("weight", 0.001), "kg": ("weight", 1.0),
    "lb": ("weight", 0.453592), "oz": ("weight", 0.0283495), "ton": ("weight", 1000.0),
    "ml": ("volume", 0.001), "l": ("volume", 1.0), "gal": ("volume", 3.78541),
    "qt": ("volume", 0.946353), "pt": ("volume", 0.473176),
    "m_s": ("speed", 1.0), "km_h": ("speed", 1 / 3.6), "mph": ("speed", 0.44704),
}

def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    fu = from_unit.lower()
    tu = to_unit.lower()

    # Temperature handled separately (non-linear)
    temp_units = {"c", "f", "k"}
    if fu in temp_units or tu in temp_units:
        v = float(value)
        # to Celsius
        if fu == "f":
            c = (v - 32) * 5 / 9
        elif fu == "k":
            c = v - 273.15
        else:
            c = v
        # from Celsius to target
        if tu == "f":
            result = c * 9 / 5 + 32
        elif tu == "k":
            result = c + 273.15
        else:
            result = c
        return json.dumps({"result": round(result, 4), "from": f"{value} {fu.upper()}", "to": f"{round(result, 4)} {tu.upper()}"})

    if fu not in UNIT_TABLE:
        return json.dumps({"error": f"Unknown unit '{fu}'. Supported: {', '.join(UNIT_TABLE)}, C, F, K"})
    if tu not in UNIT_TABLE:
        return json.dumps({"error": f"Unknown unit '{tu}'. Supported: {', '.join(UNIT_TABLE)}, C, F, K"})

    from_dim, from_factor = UNIT_TABLE[fu]
    to_dim, to_factor = UNIT_TABLE[tu]

    if from_dim != to_dim:
        return json.dumps({"error": f"Cannot convert {fu} ({from_dim}) to {tu} ({to_dim}) — different dimensions"})

    base = float(value) * from_factor
    result = round(base / to_factor, 6)
    return json.dumps({"result": result, "from": f"{value} {fu}", "to": f"{result} {tu}"})

# --- Calculate tool ---
def calculate(expression: str) -> str:
    try:
        allowed = {"math": math, "abs": abs, "round": round, "pow": pow}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return json.dumps({"result": str(result)})
    except Exception as e:
        return json.dumps({"error": str(e)})

TOOLS = {
    "calculate": calculate,
    "convert_currency": convert_currency,
    "convert_units": convert_units,
}

# --- LLM response parser (same as first_agent.py) ---
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
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse LLM output: {text}")

# --- Agent loop ---
def run_agent(user_query: str, max_iterations: int = 10):
    steps = []
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    for _ in range(max_iterations):
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

        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        response_text = response.text

        try:
            parsed = parse_llm_response(response_text)
        except (ValueError, json.JSONDecodeError):
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": "Please respond with valid JSON only."})
            continue

        if "answer" in parsed:
            return {"answer": parsed["answer"], "steps": steps}

        if "tool_name" in parsed:
            tool_name = parsed["tool_name"]
            tool_args = parsed.get("tool_arguments", {})

            if tool_name not in TOOLS:
                err = json.dumps({"error": f"Unknown tool: {tool_name}. Available: calculate, convert_currency, convert_units"})
                steps.append({"tool": tool_name, "args": tool_args, "result": err})
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "tool", "content": err})
                continue

            tool_result = TOOLS[tool_name](**tool_args)
            steps.append({"tool": tool_name, "args": tool_args, "result": tool_result})
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "tool", "content": tool_result})

    return {"answer": "Could not complete within iteration limit.", "steps": steps}

# --- API endpoint ---
class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def handle_query(req: QueryRequest):
    return run_agent(req.query)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
