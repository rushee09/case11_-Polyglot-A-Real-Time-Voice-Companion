# Deck Outline — Polyglot Voice Companion

---

## Slide 1 — Problem

**Title**: "AI Voice Agents Break When You Switch Languages"

- 95% of global users speak more than one language daily
- Hinglish, Spanglish, code-switching: the norm, not the exception
- Existing agents: respond in English regardless of input language, forget context on language switch

---

## Slide 2 — Solution Architecture

**Title**: "Local, Multilingual, Memory-Aware"

- Diagram: Mic → ASR → Language Detection → Memory → Tools → LLM → TTS
- 100% local: faster-whisper + LM Studio, no cloud API required
- Languages: EN, HI, ES, Mixed (Hinglish)
- Memory persists across language switches

---

## Slide 3 — Build Highlights

**Title**: "What We Built in 24 Hours"

| Component | Tech |
|---|---|
| Real-time voice pipeline | FastAPI + faster-whisper |
| Language detection | Keyword rules + langdetect |
| Structured memory | In-process entity store |
| Local LLM | LM Studio (qwen2.5-7b) |
| Browser TTS | Web Speech API |
| Storage + Logs | Supabase (optional) |

- 4 end-to-end scenario datasets with expected behaviors
- 32 unit tests across memory, language, and scenario modules

---

## Slide 4 — Scenario Outcomes

**Title**: "Demonstrated Across 4 Scenarios"

| Scenario | Languages | Key Behavior |
|---|---|---|
| Customer Support | EN → HI | Order ID retained, Hindi response |
| Food Ordering | HI → EN | Hinglish switch, cart preserved |
| Hotel Booking | ES | Hotel options extracted, Spanish response |
| Weather Query | EN, HI, ES, Mixed | All 4 in one session |

**Latency**: ~650ms average on CPU for voice turns

---

## Slide 5 — What's Next

- GPU acceleration → <200ms voice turns
- Piper-TTS for higher-quality Hindi/Spanish voice
- Bengali, Tamil, Portuguese language support
- Multi-user sessions with Redis-backed memory
- Production deployment: Fly.io backend + Vercel frontend
