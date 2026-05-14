import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.memory_service import get_or_create_session, update_memory_after_turn, record_assistant_turn
from app.services.language_service import detect_language_from_text, get_language_label
from app.services.scenario_tools import build_tool_context
from app.services.llm_service import call_llm
from app.services.latency_service import LatencyTracker, TimedBlock
from app.services.tts_service import get_tts_metadata
from app.services import storage_service

router = APIRouter()


@router.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    await websocket.accept()

    async def send_status(stage: str, data: dict = None):
        payload = {"stage": stage, **(data or {})}
        await websocket.send_text(json.dumps(payload))

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            text = msg.get("text", "").strip()
            scenario_name = msg.get("scenario_name")

            if not text:
                await send_status("error", {"message": "Empty text"})
                continue

            tracker = LatencyTracker()

            await send_status("language_detected")
            with TimedBlock(tracker, "language_detection_ms"):
                lang, label, confidence = detect_language_from_text(text)

            await send_status("updating_memory")
            with TimedBlock(tracker, "memory_update_ms"):
                session = get_or_create_session(session_id, scenario_name)
                switch_info = update_memory_after_turn(session, text, lang, scenario_name)

            await send_status("calling_llm", {"detected_language": lang, "language_label": label})
            with TimedBlock(tracker, "tool_ms"):
                tool_ctx = build_tool_context(session.entities.to_dict(), scenario_name)

            with TimedBlock(tracker, "llm_ms"):
                memory_snap = session.to_dict()
                chat_history = session.get_chat_history(max_turns=8)
                llm_result = await call_llm(text, lang, label, memory_snap, tool_ctx, chat_history)

            response_text = llm_result["response_text"]
            resp_lang = lang

            record_assistant_turn(session, response_text, resp_lang)

            latency_dict = tracker.to_dict()
            storage_service.log_message(
                session_id=session_id,
                turn_number=session.turn_count,
                role="assistant",
                transcript=text,
                detected_language=lang,
                response_language=resp_lang,
                response_text=response_text,
                latency_ms=latency_dict["total_ms"],
                memory_snapshot=session.to_dict(),
            )
            storage_service.log_latency(session_id, session.turn_count, latency_dict)

            tts_meta = get_tts_metadata(resp_lang, response_text)

            await send_status("response_ready", {
                "session_id": session_id,
                "turn_number": session.turn_count,
                "user_text": text,
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
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"stage": "error", "message": str(e)}))
        except Exception:
            pass
