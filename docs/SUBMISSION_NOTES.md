# Submission Notes

## Known Issues

### `faster-whisper` optional
Voice upload mode requires `faster-whisper`. If not installed, `/api/transcribe` and `/api/voice-turn` return HTTP 503 with an install message. Text mode (all other endpoints) works without it.

### LM Studio must be running
The backend requires LM Studio at `http://localhost:1234` for live LLM responses. If offline, `/health` will show `lm_studio: false` and all chat endpoints use deterministic fallback templates.

### Browser TTS quality
Hindi TTS quality depends on whether the host OS has an `hi-IN` voice pack installed. On macOS, install via System Preferences → Accessibility → Spoken Content. On Windows, install via Time & Language settings.

### `uuid` dependency
`frontend/package.json` includes `uuid ^9.0.1` and `@types/uuid`. Run `npm install` to pull it in.

### In-process memory
Sessions are stored in a Python dict. Restarting the backend clears all sessions. For persistent sessions, configure Supabase (see README).

## Setup Checklist

- [ ] LM Studio downloaded and a model loaded
- [ ] Local server started in LM Studio (port 1234)
- [ ] `LM_STUDIO_MODEL` set in `backend/.env`
- [ ] `cd backend && pip install -r requirements.txt`
- [ ] `cd frontend && npm install`
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173

## Running Without LM Studio

Everything except LLM responses will work. The agent will respond with canned fallback phrases to demonstrate the language detection and memory pipeline. Set `STORAGE_MODE=local` and no Supabase credentials are required.

## File Layout

```
case11_-Polyglot-A-Real-Time-Voice-Companion/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── websocket.py
│   │   ├── models/         # schemas.py, memory.py
│   │   ├── routes/         # health, chat, voice, sessions
│   │   └── services/       # asr, language, memory, llm, tts, tools, storage, latency
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/          # Landing, VoiceAgent, ScenarioTest, Logs
│   │   ├── components/     # 8 UI components
│   │   ├── api/client.ts
│   │   └── data/scenarios.ts
│   └── package.json
├── supabase/schema.sql
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── LATENCY_BUDGET.md
│   ├── demo_script.md
│   ├── deck_outline.md
│   └── SUBMISSION_NOTES.md
├── docker-compose.yml
└── README.md
```
