from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.models.schemas import (
    ChatRequest, ChatResponse, DetectLanguageRequest,
    LanguageDetectResponse, LatencyBreakdown,
)
from app.services.language_service import detect_language_from_text, get_language_label
from app.services.memory_service import get_or_create_session, update_memory_after_turn, record_assistant_turn
from app.services.llm_service import call_llm
from app.services.latency_service import LatencyTracker, TimedBlock
from app.services.tts_service import get_tts_metadata
from app.services import storage_service
from app.services.guardrail_service import check_input, BLOCKED_RESPONSE

router = APIRouter(prefix="/api")


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    tracker = LatencyTracker()

    # 0. Guardrail — reject prompt injection / jailbreak attempts
    guard = check_input(req.text)
    if guard.blocked:
        raise HTTPException(status_code=400, detail=BLOCKED_RESPONSE)

    # 1. Language detection
    with TimedBlock(tracker, "language_detection_ms"):
        lang, label, confidence, respond_lang = detect_language_from_text(req.text)

    # 2. Memory update
    with TimedBlock(tracker, "memory_update_ms"):
        session = get_or_create_session(req.session_id, req.scenario_name)
        switch_info = update_memory_after_turn(session, req.text, lang, req.scenario_name)

    # 3. LLM — agent loop (model calls tools on demand; no pre-fetch)
    with TimedBlock(tracker, "llm_ms"):
        memory_snap = session.to_dict()
        chat_history = session.get_chat_history(max_turns=6)
        llm_result = await call_llm(
            req.text, lang, label, memory_snap, chat_history,
            respond_language=respond_lang,
        )

    # Persist any tool results the agent fetched this turn into the session
    # cache so that follow-up questions (language switches, "second option",
    # "compare all three") work without the model re-calling tools.
    for tool_name, result in llm_result.get("tool_results", {}).items():
        if tool_name == "get_weather":
            # Merge city-keyed weather dict rather than overwrite
            weather_cache = session.tool_cache.setdefault("get_weather", {})
            weather_cache.update(result)
        else:
            session.tool_cache[tool_name] = result

    response_text: str = llm_result["response_text"]
    # Response language = same as detected (agent mirrors user)
    resp_lang = lang
    resp_label = label

    # 5. Record assistant turn — skip fallback responses so they don't
    #    re-enter chat history and trigger another Channel Error on the next turn.
    if not llm_result.get("fallback_mode", False):
        record_assistant_turn(session, response_text, resp_lang)

    # 6. Store logs
    latency_dict = tracker.to_dict()
    storage_service.log_message(
        session_id=req.session_id,
        turn_number=session.turn_count,
        role="assistant",
        transcript=req.text,
        detected_language=lang,
        response_language=resp_lang,
        response_text=response_text,
        latency_ms=latency_dict["total_ms"],
        memory_snapshot=session.to_dict(),
    )
    storage_service.log_latency(req.session_id, session.turn_count, latency_dict)
    if switch_info.get("language_switched") and switch_info.get("event"):
        ev = switch_info["event"]
        storage_service.log_language_switch(
            req.session_id,
            ev["turn_number"],
            ev["from_language"],
            ev["to_language"],
            confidence,
        )

    tts_meta = get_tts_metadata(resp_lang, response_text)

    return ChatResponse(
        session_id=req.session_id,
        turn_number=session.turn_count,
        user_text=req.text,
        detected_language=lang,
        language_label=label,
        assistant_response=response_text,
        response_language=resp_lang,
        response_language_label=resp_label,
        language_switched=switch_info.get("language_switched", False),
        previous_language=session.previous_language,
        memory_snapshot=session.to_dict(),
        tool_context=llm_result.get("tool_results") or None,
        latency=LatencyBreakdown(**latency_dict),
        lm_studio_available=llm_result.get("lm_studio_available", False),
        fallback_mode=llm_result.get("fallback_mode", False),
    )


@router.post("/detect-language", response_model=LanguageDetectResponse)
async def detect_language(req: DetectLanguageRequest):
    lang, label, confidence, _ = detect_language_from_text(req.text)
    return LanguageDetectResponse(
        detected_language=lang, language_label=label, confidence=confidence
    )


@router.get("/export-csv")
async def export_chat_csv():
    """Download the full conversation history as a CSV file."""
    path = storage_service.get_csv_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No chat history CSV found yet.")
    return FileResponse(
        path=path,
        media_type="text/csv",
        filename="polyglot_chat_history.csv",
    )
