import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.schemas import TranscribeResponse, ChatResponse, LatencyBreakdown
from app.services import asr_service
from app.services.language_service import detect_language_from_text, get_language_label
from app.services.memory_service import get_or_create_session, update_memory_after_turn, record_assistant_turn
from app.services.scenario_tools import build_tool_context
from app.services.llm_service import call_llm
from app.services.latency_service import LatencyTracker, TimedBlock
from app.services.tts_service import get_tts_metadata
from app.services import storage_service
from app.services.guardrail_service import check_input, BLOCKED_RESPONSE

router = APIRouter(prefix="/api")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...)):
    """Transcribe uploaded audio and return text + detected language."""
    t0 = time.perf_counter()
    audio_bytes = await file.read()

    if not asr_service.is_asr_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "faster-whisper is not installed. "
                "Install it with: pip install faster-whisper\n"
                "Use /api/chat for text-mode instead."
            ),
        )

    try:
        transcript, detected_lang, confidence = asr_service.transcribe_audio(
            audio_bytes, file.filename or "audio.wav"
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    elapsed = (time.perf_counter() - t0) * 1000
    label = get_language_label(detected_lang)

    return TranscribeResponse(
        transcript=transcript,
        detected_language=detected_lang,
        language_label=label,
        confidence=confidence,
        latency_ms=round(elapsed, 1),
    )


@router.post("/voice-turn")
async def voice_turn(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    scenario_name: Optional[str] = Form(None),
):
    """
    Full voice pipeline:
    audio → ASR → language detection → memory → tool context → LLM → response
    """
    tracker = LatencyTracker()

    # 1. Audio upload
    audio_bytes = await file.read()
    tracker.mark("audio_upload_ms", (time.perf_counter() - tracker._start) * 1000)

    # 2. ASR
    if not asr_service.is_asr_available():
        raise HTTPException(
            status_code=503,
            detail="faster-whisper not available. Use POST /api/chat for text mode.",
        )

    with TimedBlock(tracker, "asr_ms"):
        try:
            transcript, asr_lang, confidence = asr_service.transcribe_audio(
                audio_bytes, file.filename or "audio.wav"
            )
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))

    # 2b. Guardrail — scan transcript for injection / jailbreak attempts
    guard = check_input(transcript)
    if guard.blocked:
        raise HTTPException(status_code=400, detail=BLOCKED_RESPONSE)

    # 3. Language detection (use ASR lang, refine with text rules)
    with TimedBlock(tracker, "language_detection_ms"):
        text_lang, label, text_conf = detect_language_from_text(transcript)
        # Prefer ASR language detection for clean audio; text rules catch Hinglish better
        lang = text_lang if text_lang in ("mixed",) else (asr_lang or text_lang)
        label = get_language_label(lang)

    # 4. Memory update
    with TimedBlock(tracker, "memory_update_ms"):
        session = get_or_create_session(session_id, scenario_name)
        switch_info = update_memory_after_turn(session, transcript, lang, scenario_name)

    # 5. Tool context
    with TimedBlock(tracker, "tool_ms"):
        tool_ctx = build_tool_context(session.entities.to_dict(), scenario_name)

    # 6. LLM
    with TimedBlock(tracker, "llm_ms"):
        memory_snap = session.to_dict()
        chat_history = session.get_chat_history(max_turns=8)
        llm_result = await call_llm(transcript, lang, label, memory_snap, tool_ctx, chat_history)

    response_text: str = llm_result["response_text"]
    resp_lang = lang

    # 7. Record assistant turn
    record_assistant_turn(session, response_text, resp_lang)

    # 8. Logs
    latency_dict = tracker.to_dict()
    storage_service.log_message(
        session_id=session_id,
        turn_number=session.turn_count,
        role="assistant",
        transcript=transcript,
        detected_language=lang,
        response_language=resp_lang,
        response_text=response_text,
        latency_ms=latency_dict["total_ms"],
        memory_snapshot=session.to_dict(),
    )
    storage_service.log_latency(session_id, session.turn_count, latency_dict)
    if switch_info.get("language_switched") and switch_info.get("event"):
        ev = switch_info["event"]
        storage_service.log_language_switch(
            session_id, ev["turn_number"],
            ev["from_language"], ev["to_language"], confidence,
        )

    tts_meta = get_tts_metadata(resp_lang, response_text)

    return {
        "session_id": session_id,
        "transcript": transcript,
        "detected_language": lang,
        "language_label": label,
        "assistant_response": response_text,
        "response_language": resp_lang,
        "response_language_label": get_language_label(resp_lang),
        "language_switched": switch_info.get("language_switched", False),
        "previous_language": session.previous_language,
        "tts_metadata": tts_meta,
        "memory_snapshot": session.to_dict(),
        "tool_context": tool_ctx or None,
        "latency": latency_dict,
        "lm_studio_available": llm_result.get("lm_studio_available", False),
        "fallback_mode": llm_result.get("fallback_mode", False),
    }
