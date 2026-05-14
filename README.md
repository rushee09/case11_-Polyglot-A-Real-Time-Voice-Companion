# Polyglot Voice Companion

**A local multilingual real-time voice agent** that listens, transcribes, detects language, remembers context across language switches, generates a response via LM Studio, and speaks it back — all without any external AI API.

---

## Architecture

```
Mic → [Browser] → POST /api/voice-turn
                  ├─ ASR (faster-whisper)
                  ├─ Language Detection (keyword rules + langdetect)
                  ├─ Memory Update (structured entities)
                  ├─ Tool Context (mock scenario tools)
                  ├─ LLM (LM Studio local OpenAI API)
                  └─ Response → Browser TTS (speechSynthesis)
```

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| ASR | faster-whisper (local CPU) |
| LLM | LM Studio (local OpenAI-compatible API) |
| Language Detection | Keyword rules + langdetect fallback |
| Memory | In-process structured session store |
| TTS | Browser `speechSynthesis` (backend Piper/Coqui stub ready) |
| Storage | Local JSON (Supabase Postgres optional) |
| Realtime | WebSocket `/ws/session/{id}` |

---

## Quick Start

### Prerequisites
- Node.js 18+, Python 3.11+
- [LM Studio](https://lmstudio.ai/) running at `http://localhost:1234`

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
pip install faster-whisper   # Optional — enables voice upload
cp .env.example .env         # Set LM_STUDIO_MODEL
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Tests
```bash
cd backend && pytest tests/ -v
```

---

## LM Studio Setup

1. Download from https://lmstudio.ai/
2. Load a model: `qwen2.5-7b-instruct` (recommended), `llama-3.2-3b-instruct` (low RAM), `mistral-nemo-12b` (best multilingual)
3. Start local server (default port 1234)
4. Set `LM_STUDIO_MODEL=<model-name>` in `backend/.env`

> **Offline mode**: Deterministic fallbacks serve all 4 scenarios if LM Studio is offline.

---

## Supabase Setup (optional)
1. Create project, run `supabase/schema.sql`
2. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`
3. `pip install supabase`

---

## Demo Flow
1. **Voice Agent** → select Scenario 1 → type or record English order inquiry
2. Switch to Hindi mid-conversation → agent mirrors language, memory persists
3. **Scenarios** page → run all 4 scenario sequences
4. **Logs** page → paste session ID → view latency breakdown + language switch events

See `docs/demo_script.md` for the full 6-minute demo walkthrough.