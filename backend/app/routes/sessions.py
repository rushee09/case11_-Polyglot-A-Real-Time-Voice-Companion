from fastapi import APIRouter, HTTPException
import json
import logging
import os
from app.services.memory_service import get_session_memory, list_sessions
from app.services import storage_service
from app.services.scenario_tools import (
    lookup_order, search_hotels, get_weather, pizza_order_context
)

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

# ─── Scenarios — loaded from config file (single source of truth) ────────────

_SCENARIOS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "config", "scenarios.json"
)


def _load_scenarios() -> list:
    """Read scenarios from scenarios.json. Returns [] on any error so the app
    keeps running even if the file is temporarily unavailable."""
    try:
        with open(_SCENARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("[scenarios] File not found: %s", _SCENARIOS_FILE)
        return []
    except json.JSONDecodeError as exc:
        logger.error("[scenarios] JSON parse error in %s: %s", _SCENARIOS_FILE, exc)
        return []


@router.get("/scenarios")
async def get_scenarios():
    return _load_scenarios()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = get_session_memory(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "memory": session.to_dict(),
        "turns": [t.to_dict() for t in session.turns],
    }


@router.get("/sessions/{session_id}/logs")
async def get_session_logs(session_id: str):
    logs = storage_service.get_session_logs(session_id)
    return {"session_id": session_id, **logs}


@router.get("/sessions")
async def list_all_sessions():
    return {"sessions": list_sessions()}
