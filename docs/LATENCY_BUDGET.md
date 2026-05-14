# Latency Budget

## Targets

| Tier | Total | Notes |
|---|---|---|
| Stretch goal | < 800ms | Text input only, no ASR |
| Primary target | < 1200ms | Voice input, local hardware |
| Acceptable | < 2000ms | slower CPU / large model |

## Stage Breakdown

| Stage | Expected | Max | Notes |
|---|---|---|---|
| Audio upload | ~50ms | 200ms | Depends on clip length |
| ASR (faster-whisper base) | ~300ms | 1500ms | CPU, 8-word clip |
| Language detection | <1ms | 5ms | Keyword rules |
| Memory update | <1ms | 2ms | In-process dict |
| Tool context | <1ms | 5ms | Pure Python |
| LLM (LM Studio qwen2.5-7b) | ~300ms | 800ms | First token to full response |
| Response serialization | <5ms | 10ms | |
| **Total (voice)** | **~650ms** | **~2500ms** | |
| **Total (text)** | **~310ms** | **~820ms** | No ASR |

## Hardware Reference

Tests run on: Intel Core i7-12th Gen, 16GB RAM, no GPU. LM Studio CPU inference.

GPU inference (CUDA): ASR drops to ~80ms, LLM to ~150ms for 7B model.

## Optimization Notes

- `faster-whisper` `base` model is optimal for CPU demo; swap to `tiny` if targeting <500ms voice
- LM Studio keeps model in RAM — cold start adds ~500ms first inference only
- Keyword rule detection avoids langdetect entirely for known demo inputs
- Connection keep-alive reduces HTTP overhead on `/api/voice-turn`
