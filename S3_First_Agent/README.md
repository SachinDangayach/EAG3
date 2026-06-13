# S3 — First Agent

A full-stack AI agent that answers questions about **math calculations**, **currency conversion**, and **unit conversion**. The LLM (Gemini on Vertex AI) is constrained to use only the provided tools — it never answers from its own knowledge.

---

## Architecture

```
┌─────────────────────┐        POST /query        ┌──────────────────────┐
│   React Frontend    │ ────────────────────────▶ │  FastAPI Backend     │
│   (Vite, port 5173) │ ◀──────────────────────── │  (uvicorn, port 8000)│
└─────────────────────┘    { answer, steps[] }    └──────────┬───────────┘
                                                             │
                                                   Agent loop (≤10 iters)
                                                             │
                                                   ┌─────────▼──────────┐
                                                   │  Gemini 2.5 Flash  │
                                                   │  (Vertex AI)       │
                                                   └─────────┬──────────┘
                                                             │ tool calls
                                              ┌──────────────┼─────────────┐
                                         calculate   convert_currency  convert_units
```

---

## Project Structure

```
S3_First_Agent/
├── first_agent.py        # Original CLI agent (reference)
├── agent_server.py       # FastAPI backend — agent loop + tools
└── frontend/
    ├── package.json
    ├── vite.config.js    # Proxies /query → localhost:8000
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx       # Chat UI with collapsible tool-call steps
        └── App.css
```

---

## Tools Available to the LLM

| Tool | Description | Example |
|---|---|---|
| `calculate` | Evaluates a Python math expression (`math.*`, `abs`, `round`, `pow`) | `2**10 + math.sqrt(144)` |
| `convert_currency` | Converts between 10 currencies using fixed reference rates | 500 USD → INR |
| `convert_units` | Converts length, weight, temperature, volume, speed | 10 km → miles, 100°F → °C |

**Supported currencies:** USD, EUR, GBP, INR, JPY, AUD, CAD, CHF, CNY, SGD

**Supported units:**
- Length: `mm`, `cm`, `m`, `km`, `in`, `ft`, `yd`, `mi`
- Weight: `mg`, `g`, `kg`, `lb`, `oz`, `ton`
- Temperature: `C`, `F`, `K`
- Volume: `ml`, `l`, `gal`, `qt`, `pt`
- Speed: `m_s`, `km_h`, `mph`

---

## Setup & Running

### Prerequisites

```bash
# Python deps
pip install fastapi uvicorn google-genai

# Node deps (one-time)
cd frontend && npm install
```

Place your GCP service account JSON file in the `S3_First_Agent/` folder.  
The server auto-discovers the first `*.json` file and sets `GOOGLE_APPLICATION_CREDENTIALS`.

### Start the backend

```bash
# From S3_First_Agent/
python3 agent_server.py
# Listening on http://0.0.0.0:8000
```

### Start the frontend

```bash
# From S3_First_Agent/frontend/
npm run dev
# Open http://localhost:5173
```

---

## How the Agent Loop Works

1. User query is sent to `POST /query`.
2. The system prompt forces the LLM to respond in JSON — either a tool call or a final answer.
3. If it's a tool call, the tool executes and the result is appended to the conversation.
4. Steps repeat (up to 10 iterations) until the LLM emits `{"answer": "..."}`.
5. The response includes both the final answer and every tool step taken, which the UI renders as collapsible badges.
