# Design Decisions

## Framework Choices

**React + Vite (not Next.js)**
We need a local SPA with a persistent WebSocket — no server-side rendering needed. Vite's dev server proxy to `localhost:8000` avoids CORS friction during development.

**FastAPI (not Express/Node)**
All the AI dependencies (faster-whisper, langdetect, supabase-py) are Python-native. FastAPI gives async WebSocket support, automatic OpenAPI docs, and minimal boilerplate.

**LM Studio (not hosted API)**
Privacy, zero inference cost, works offline on contest hardware. The OpenAI-compatible API means swapping to cloud GPT-4o is a single env var change.

## Language Detection

**Why keyword rules first?**
`langdetect` is accurate but slow (15–60ms per call) and fails on short phrases or mixed text. A simple keyword set like `{"hola","gracias","como","esta"}` for Spanish handles 95% of demo inputs in <0.5ms.

Mixed Hindi-English ("Hinglish") gets a `mixed` code when both Hindi and English keyword scores exceed 0.08. The LLM prompt then says "user is mixing Hindi and English — match their style".

## Memory Architecture

**Why structured entities instead of just chat history?**
When language switches, the LLM loses context from previous turns if we only pass recent history. Structured memory (`order_id`, `email`, `hotel_options`) is injected into every system prompt regardless of language, so the agent always knows what was established.

**Why in-process dict?**
For a local demo with a single user, a dict is perfectly sufficient and has zero latency. Redis or Supabase KV would be the migration path for production.

## TTS Strategy

**Why browser speechSynthesis first?**
Piper-TTS and Coqui are heavy installs (~500MB models) that would block demo setup. Browser TTS works out of the box on any OS and supports `en`, `es`, and often `hi-IN` (Windows/macOS). Backend TTS stub is in place for easy swap.

## What Was De-scoped

- **Real-time streaming LLM**: Token streaming via SSE adds complexity; full response delivery is faster to implement correctly
- **STT confidence threshold UI**: Not needed for demo clarity
- **Multi-user sessions**: In-process dict is fine for single-user local demo
- **Piper/Coqui TTS**: Replaced with browser TTS for reliability
- **Authentication**: Out of scope for a local AI agent demo
