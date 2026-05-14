"""
Storage service — Supabase Postgres primary, local JSON fallback.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

_LOCAL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".local_data")

# ─── Local JSON helpers ──────────────────────────────────────────────────────

def _local_path(table: str) -> str:
    os.makedirs(_LOCAL_DIR, exist_ok=True)
    return os.path.join(_LOCAL_DIR, f"{table}.json")


def _local_read(table: str) -> List[Dict[str, Any]]:
    path = _local_path(table)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _local_append(table: str, record: Dict[str, Any]) -> None:
    rows = _local_read(table)
    rows.append(record)
    with open(_local_path(table), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


# ─── Supabase helpers ────────────────────────────────────────────────────────

_supabase_client = None


def _get_supabase():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    try:
        from supabase import create_client
        from app.config import settings
        if settings.supabase_url and settings.supabase_service_role_key:
            _supabase_client = create_client(
                settings.supabase_url, settings.supabase_service_role_key
            )
    except ImportError:
        pass
    return _supabase_client


def _use_supabase() -> bool:
    from app.config import settings
    return bool(settings.supabase_url and settings.supabase_service_role_key)


# ─── Public API ──────────────────────────────────────────────────────────────

def log_session(session_id: str, scenario_name: Optional[str], language: str) -> None:
    record = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "scenario_name": scenario_name,
        "active_language": language,
        "total_turns": 0,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
    }
    if _use_supabase():
        try:
            sb = _get_supabase()
            if sb:
                sb.table("voice_sessions").upsert(record).execute()
                return
        except Exception as e:
            print(f"[storage] Supabase error: {e}")
    _local_append("voice_sessions", record)


def log_message(
    session_id: str,
    turn_number: int,
    role: str,
    transcript: str,
    detected_language: str,
    response_language: str,
    response_text: str,
    latency_ms: float,
    memory_snapshot: Dict[str, Any],
) -> None:
    record = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "turn_number": turn_number,
        "role": role,
        "transcript": transcript,
        "detected_language": detected_language,
        "response_language": response_language,
        "response_text": response_text,
        "latency_ms": latency_ms,
        "memory_snapshot": memory_snapshot,
        "created_at": datetime.utcnow().isoformat(),
    }
    if _use_supabase():
        try:
            sb = _get_supabase()
            if sb:
                sb.table("conversation_messages").insert(record).execute()
                return
        except Exception as e:
            print(f"[storage] Supabase error: {e}")
    _local_append("conversation_messages", record)


def log_language_switch(
    session_id: str, turn_number: int, from_lang: str, to_lang: str, confidence: Optional[float]
) -> None:
    record = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "turn_number": turn_number,
        "from_language": from_lang,
        "to_language": to_lang,
        "confidence": confidence,
        "created_at": datetime.utcnow().isoformat(),
    }
    if _use_supabase():
        try:
            sb = _get_supabase()
            if sb:
                sb.table("language_switch_events").insert(record).execute()
                return
        except Exception as e:
            print(f"[storage] Supabase error: {e}")
    _local_append("language_switch_events", record)


def log_latency(session_id: str, turn_number: int, latency_dict: Dict[str, Any]) -> None:
    record = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "turn_number": turn_number,
        **latency_dict,
        "created_at": datetime.utcnow().isoformat(),
    }
    if _use_supabase():
        try:
            sb = _get_supabase()
            if sb:
                sb.table("latency_logs").insert(record).execute()
                return
        except Exception as e:
            print(f"[storage] Supabase error: {e}")
    _local_append("latency_logs", record)


def get_session_logs(session_id: str) -> Dict[str, Any]:
    if _use_supabase():
        try:
            sb = _get_supabase()
            if sb:
                msgs = sb.table("conversation_messages").select("*").eq("session_id", session_id).execute()
                switches = sb.table("language_switch_events").select("*").eq("session_id", session_id).execute()
                lats = sb.table("latency_logs").select("*").eq("session_id", session_id).execute()
                return {
                    "messages": msgs.data,
                    "language_switch_events": switches.data,
                    "latency_logs": lats.data,
                }
        except Exception as e:
            print(f"[storage] Supabase error: {e}")

    # Local fallback
    msgs = [r for r in _local_read("conversation_messages") if r.get("session_id") == session_id]
    switches = [r for r in _local_read("language_switch_events") if r.get("session_id") == session_id]
    lats = [r for r in _local_read("latency_logs") if r.get("session_id") == session_id]
    return {"messages": msgs, "language_switch_events": switches, "latency_logs": lats}


def get_storage_mode() -> str:
    return "supabase" if _use_supabase() else "local"
