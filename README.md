# Polyglot Voice Companion

A **local multilingual real-time voice agent** that listens, transcribes, detects language, remembers context across language switches, calls tools on demand via an LLM-driven agent loop, and speaks the response back — entirely without external AI APIs.

Supports **English, Hindi, and Spanish**. Handles mid-conversation language switches, code-switching (Hinglish), and multi-city follow-up questions while preserving full session context.

---

## Architecture

```
Mic → [Browser]
        │
        ├─ POST /api/voice-turn  (audio upload)
        │     └─ ASR (faster-whisper) → transcript
        │
        └─ POST /api/chat  (text/transcript)
              ├─ Language Detection  (keyword rules + langdetect fallback)
              ├─ Memory Update       (session entities, language-switch tracking)
              │
              └─ Agent Loop (LM Studio)
                    LLM ←──────────────────────────────────┐
                     │   finish_reason == "tool_calls"       │
                     ↓                                       │
                  execute tool  →  append result to thread ──┘
                     │   finish_reason == "stop"
                     ↓
                  response_text
              │
              ├─ Persist tool_results → session.tool_cache
              ├─ Record turn in session history
              └─ Storage (local JSON + CSV / Supabase optional)

WebSocket /ws/session/{id}  — streaming updates for each pipeline stage
```

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, glassmorphism UI |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| ASR | `faster-whisper` (local CPU — optional) |
| LLM | LM Studio local OpenAI-compatible API |
| Agent | OpenAI function-calling tool loop (up to 4 rounds per turn) |
| Language Detection | Keyword scoring + `langdetect` fallback |
| Memory | In-process structured session store with cross-turn tool cache |
| TTS | Browser `speechSynthesis` (Piper/Coqui stub ready) |
| Auth | localStorage user registry (multi-user, signup + login) |
| Storage | Local JSON + CSV (Supabase optional) |
| Realtime | WebSocket `/ws/session/{id}` |

---

## File Structure

```
case11_-Polyglot-A-Real-Time-Voice-Companion/
│
├── start.bat                         # One-click launcher (backend + frontend)
├── docker-compose.yml
│
├── backend/
│   ├── .env                          # Runtime config (copy from .env.example)
│   ├── .env.example
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── main.py                   # FastAPI app, CORS, request logger
│   │   ├── config.py                 # Settings (LM Studio URL, model, Supabase)
│   │   ├── websocket.py              # WS /ws/session/{id} — streaming pipeline
│   │   │
│   │   ├── models/
│   │   │   ├── memory.py             # MemoryEntities, ConversationTurn, SessionMemory
│   │   │   │                           #   SessionMemory.tool_cache  — cross-turn tool results
│   │   │   │                           #   SessionMemory.get_chat_history()  — Vulkan-safe history
│   │   │   └── schemas.py            # Pydantic request/response schemas
│   │   │
│   │   ├── routes/
│   │   │   ├── chat.py               # POST /api/chat — main text/agent endpoint
│   │   │   │                           #   POST /api/detect-language
│   │   │   │                           #   GET  /api/export-csv
│   │   │   ├── voice.py              # POST /api/transcribe — audio → transcript
│   │   │   │                           #   POST /api/voice-turn — audio → full response
│   │   │   ├── sessions.py           # GET  /api/sessions
│   │   │   │                           #   GET  /api/sessions/{id}
│   │   │   │                           #   GET  /api/scenarios — 4 sample scripts
│   │   │   │                           #   GET  /api/tool-demo/{tool}
│   │   │   └── health.py             # GET  /health — LM Studio + ASR + storage status
│   │   │
│   │   └── services/
│   │       ├── llm_service.py        # Agent loop: call_llm(), check_lm_studio()
│   │       │                           #   Sends tools= to LM Studio, executes tool_calls,
│   │       │                           #   loops until finish_reason == "stop"
│   │       ├── scenario_tools.py     # Tool functions + agent schema + executor
│   │       │                           #   TOOL_DEFINITIONS  — OpenAI function schemas
│   │       │                           #   execute_tool(name, args)  — dispatcher
│   │       │                           #   lookup_order(order_id, email?)
│   │       │                           #   search_hotels(city, budget?, people?)
│   │       │                           #   get_weather(city)
│   │       │                           #   confirm_food_order(item, preference?, add_on?)
│   │       │                           #   extract_entities_from_text()  — user_name, order_id…
│   │       │                           #   build_tool_context()  — legacy (used by WS route)
│   │       ├── language_service.py   # detect_language_from_text() — keyword scoring
│   │       │                           #   HINDI_KEYWORDS, SPANISH_KEYWORDS,
│   │       │                           #   ENGLISH_STRONG_INDICATORS
│   │       │                           #   _check_explicit_language_instruction() runs first
│   │       ├── memory_service.py     # get_or_create_session(), update_memory_after_turn()
│   │       │                           #   record_assistant_turn(), list_sessions()
│   │       ├── asr_service.py        # transcribe_audio() via faster-whisper
│   │       │                           #   is_asr_available() — graceful no-op if not installed
│   │       ├── tts_service.py        # get_tts_metadata() — lang → voice hint for browser TTS
│   │       ├── latency_service.py    # LatencyTracker, TimedBlock context manager
│   │       └── storage_service.py   # log_message(), log_latency(), log_language_switch()
│   │                                   #   Local JSON + CSV append; optional Supabase write
│   │
│   ├── .local_data/                  # Auto-created at runtime
│   │   ├── conversation_messages.json
│   │   ├── chat_history.csv          # Downloadable via GET /api/export-csv
│   │   ├── latency_logs.json
│   │   └── language_switch_events.json
│   │
│   └── tests/
│       ├── test_language_switch.py
│       ├── test_memory.py
│       └── test_scenarios.py
│
├── frontend/
│   ├── vite.config.ts                # Proxies /api/* and /ws/* to :8000
│   ├── tailwind.config.js
│   │
│   └── src/
│       ├── App.tsx                   # Router, Nav, RequireAuth guard, ambient orbs
│       ├── main.tsx
│       │
│       ├── api/
│       │   └── client.ts             # sendChat(), sendVoiceTurn(), downloadChatCsv()
│       │                               #   WebSocket helper, TypeScript response types
│       │
│       ├── context/
│       │   └── AuthContext.tsx       # localStorage multi-user auth
│       │                               #   signup(), login(), logout()
│       │                               #   Seeds admin / polyglot123 on first load
│       │
│       ├── pages/
│       │   ├── LandingPage.tsx       # Hero + feature cards
│       │   ├── LoginPage.tsx         # Sign-in / Sign-up tabs (combined)
│       │   ├── VoiceAgentPage.tsx    # Mic recorder + text chat + memory sidebar
│       │   ├── ScenarioTestPage.tsx  # Run all 4 scenarios turn-by-turn
│       │   └── LogsPage.tsx          # Session logs + latency breakdown
│       │
│       ├── components/
│       │   ├── ConversationPanel.tsx # Chat bubble renderer, ThinkingBubble integration
│       │   ├── MicRecorder.tsx       # MediaRecorder → /api/voice-turn
│       │   ├── TextChatBox.tsx       # Text input → /api/chat
│       │   ├── ScenarioCard.tsx      # One scenario script card with run controls
│       │   ├── MemoryPanel.tsx       # Live session entity inspector
│       │   ├── LatencyPanel.tsx      # Per-turn latency breakdown chart
│       │   ├── LanguageBadge.tsx     # Pill badge for detected language
│       │   ├── StatusTimeline.tsx    # WS pipeline stage indicator
│       │   └── ThinkingBubble.tsx    # Animated 3-dot indicator while LLM processes
│       │
│       ├── data/
│       │   └── scenarios.ts          # Typed 4-scenario script data
│       │
│       └── styles/
│           └── index.css             # Tailwind + glassmorphism utilities
│                                       #   .glass-card, .glass-nav, @keyframes thinkingBounce
│
├── supabase/
│   └── schema.sql                    # Tables: messages, latency_logs, language_switch_events
│
└── docs/
    ├── ARCHITECTURE.md
    ├── DECISIONS.md
    ├── LATENCY_BUDGET.md
    ├── demo_script.md
    ├── deck_outline.md
    └── SUBMISSION_NOTES.md
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | LM Studio, ASR, storage status |
| `POST` | `/api/chat` | Text turn → agent loop → response |
| `POST` | `/api/detect-language` | Classify language of a string |
| `GET` | `/api/export-csv` | Download full chat history CSV |
| `POST` | `/api/transcribe` | Upload audio → transcript + language |
| `POST` | `/api/voice-turn` | Upload audio → full agent response |
| `GET` | `/api/sessions` | List active session IDs |
| `GET` | `/api/sessions/{id}` | Full session memory dump |
| `GET` | `/api/scenarios` | 4 sample scenario scripts |
| `GET` | `/api/tool-demo/{tool}` | Smoke-test a tool directly |
| `WS` | `/ws/session/{id}` | Streaming pipeline stages |
| `GET` | `/docs` | Auto-generated Swagger UI |

---

## Agent Loop

The LLM drives all tool calls — the backend never pre-fetches data:

```
1. Build messages:
     system prompt (language rules + tool instructions)
     + SESSION CONTEXT block (respond_in, user_name, prior_tool_results)
     + chat history (last 6 turns)
     + current user message

2. POST to LM Studio with tools= TOOL_DEFINITIONS, tool_choice="auto"

3. if finish_reason == "tool_calls":
     for each tc in tool_calls:
         result = execute_tool(tc.name, tc.args)   # lookup_order / search_hotels / …
         append role:"tool" message to thread
     goto 2  (up to 4 tool-call rounds)

4. finish_reason == "stop"  →  return response_text

5. chat.py merges tool_results into session.tool_cache
     weather results keyed by city so multi-city turns accumulate
```

**Cross-turn memory**: `session.tool_cache` is serialised into `prior_tool_results` in every subsequent system context block. The model answers follow-up questions (language switch, "second option", "compare all three") from cached results without re-calling tools.

---

## Available Tools

| Tool | When called | Returns |
|---|---|---|
| `lookup_order(order_id, email?)` | User mentions order ID or asks about delivery/refund/tracking | Status, expected delivery, refund policy, tracking link info |
| `search_hotels(city, budget?, people?)` | User wants to book accommodation | List of options with name, price, location, rating |
| `get_weather(city)` | User asks about weather in a city | Temperature, condition, humidity |
| `confirm_food_order(item, preference?, add_on?)` | User places a food order | Confirmed order summary |

---

## The 4 Sample Scenarios

### Scenario 1 — Customer Support (EN → HI → EN)
```
T1 EN: "Hi, I need to check my order. The order ID is 4421."
       → LLM calls lookup_order("4421") → replies in English

T2 EN: "Yes, the email is rahul@example.com."
       → LLM calls lookup_order("4421", "rahul@example.com") → confirms delivery

T3 HI: "Theek hai, lekin delivery kal tak ho jaayegi kya?"
       → prior_tool_results has order data → LLM replies in Hindi, no new tool call

T4 HI: "Aur agar nahi hua toh refund mil sakta hai?"
       → LLM answers from cached order.refund_policy in Hindi

T5 EN: "Actually let's switch back — can you email me the tracking link?"
       → LLM switches to English, uses cached order data
```

### Scenario 2 — Travel Planning (ES → ES → EN → EN)
```
T1 ES: "Hola, quiero reservar un hotel en Bangalore para el próximo fin de semana."
       → LLM calls search_hotels("Bangalore") → lists options in Spanish

T2 ES: "Para dos personas, presupuesto de 5000 rupias por noche."
       → LLM calls search_hotels("Bangalore", budget=5000, people=2) → filtered list

T3 EN: "Sorry, my Spanish is rusty. Tell me about the second option."
       → prior_tool_results has hotel list → LLM describes option 2 in English

T4 EN: "Book it. Confirm the dates please."
       → LLM confirms the selected hotel in English
```

### Scenario 3 — Code-Switching (Mixed HI+EN)
```
T1 MIXED: "Mujhe ek pizza order karna hai, but make it veg only please."
          → LLM calls confirm_food_order("pizza", "vegetarian") → replies in Hindi

T2 EN:    "And add a coke too."
          → LLM calls confirm_food_order("pizza", "vegetarian", "coke") → updated order
```

### Scenario 4 — Rapid Switching (EN → HI → ES → EN)
```
T1 EN: "What's the weather in Mumbai today?"
       → LLM calls get_weather("Mumbai") → replies in English
       → tool_cache: {get_weather: {Mumbai: {...}}}

T2 HI: "Aur Delhi mein?"
       → LLM calls get_weather("Delhi") → replies in Hindi
       → tool_cache: {get_weather: {Mumbai: {...}, Delhi: {...}}}

T3 ES: "¿Y en Chennai?"
       → LLM calls get_weather("Chennai") → replies in Spanish
       → tool_cache: {get_weather: {Mumbai, Delhi, Chennai}}

T4 EN: "Compare all three for me."
       → All 3 cities in prior_tool_results → LLM compares in English, no new calls
```

---

## Quick Start

### Prerequisites
- Node.js 18+, Python 3.11+
- [LM Studio](https://lmstudio.ai/) running at `http://localhost:1234` with a model loaded

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
pip install faster-whisper     # Optional — enables voice upload endpoints
cp .env.example .env
# Edit .env: set LM_STUDIO_MODEL to your loaded model name
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env           # No changes needed for local dev
npm run dev
```

Open `http://localhost:5173`

### Or use the one-click launcher
```bash
start.bat    # starts both backend (port 8000) and frontend (port 5173)
```

---

## Configuration (`backend/.env`)

```env
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=qwen2.5-7b-instruct    # must match the model name in LM Studio
WHISPER_MODEL=base                      # tiny | base | small | medium
STORAGE_MODE=local                      # local | supabase
CORS_ORIGINS=http://localhost:5173

# Optional Supabase
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

### Recommended Models

| Model | VRAM | Quality | Notes |
|---|---|---|---|
| `qwen2.5-7b-instruct` | ~5 GB | Good | Fast, reliable function calling |
| `mistral-nemo-instruct-2407` | ~6 GB Q3 | Best multilingual | Strongest Hindi/Spanish |
| `llama-3.2-3b-instruct` | ~3 GB | Acceptable | Low RAM fallback |

> All three support OpenAI function calling (tool use). Quantized builds (Q3–Q4) work fine.

---

## Auth

Default credentials seeded on first load:
```
username: admin
password: polyglot123
```

Sign up for additional accounts at `/login` (Sign Up tab). All credentials are stored in `localStorage` — for demo use only.

---

## Storage

All turns are written to `backend/.local_data/`:

| File | Contents |
|---|---|
| `conversation_messages.json` | Full message log with memory snapshots |
| `chat_history.csv` | Flat CSV — downloadable via `GET /api/export-csv` or the `⬇ CSV` button in the nav |
| `latency_logs.json` | Per-turn latency breakdown (language detection, LLM, tool calls) |
| `language_switch_events.json` | Every language transition with turn number and confidence |

Optional: set Supabase credentials in `.env` to mirror all writes to Postgres.

---

## Tests
```bash
cd backend
pytest tests/ -v
```

---

## Supabase Setup (optional)
1. Create a project at [supabase.com](https://supabase.com)
2. Run `supabase/schema.sql` in the SQL editor
3. Add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` to `backend/.env`
4. `pip install supabase`
