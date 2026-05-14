from typing import Dict, Any, Optional
from app.models.memory import SessionMemory, MemoryEntities
from app.services.scenario_tools import extract_entities_from_text
from app.services.language_service import get_language_label

# In-process session store (replace with Redis/Supabase for production)
_sessions: Dict[str, SessionMemory] = {}


def get_or_create_session(session_id: str, scenario_name: Optional[str] = None) -> SessionMemory:
    if session_id not in _sessions:
        _sessions[session_id] = SessionMemory(session_id=session_id)
    session = _sessions[session_id]
    if scenario_name and not session.active_scenario:
        session.active_scenario = scenario_name
    return session


def update_memory_after_turn(
    session: SessionMemory,
    user_text: str,
    detected_language: str,
    scenario_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update memory after a user turn:
    1. Detect language switch
    2. Update language tracking
    3. Extract entities
    4. Return language switch event if any
    """
    language_label = get_language_label(detected_language)

    # Track language switch
    language_switched = False
    if session.turn_count > 0 and session.current_language != detected_language:
        language_switched = True
        session.previous_language = session.current_language

    session.current_language = detected_language
    if scenario_name:
        session.active_scenario = scenario_name

    # Extract entities from user text
    current_entities = session.entities.to_dict()
    updated_entities = extract_entities_from_text(user_text, current_entities)
    session.entities = MemoryEntities.from_dict(updated_entities)

    # Add user turn to memory
    session.add_turn("user", user_text, detected_language, language_label)

    event = None
    if language_switched:
        event = {
            "from_language": session.previous_language,
            "to_language": detected_language,
            "turn_number": session.turn_count,
        }
    return {"language_switched": language_switched, "event": event}


def record_assistant_turn(
    session: SessionMemory, response_text: str, response_language: str
) -> None:
    label = get_language_label(response_language)
    session.add_turn("assistant", response_text, response_language, label)


def get_session_memory(session_id: str) -> Optional[SessionMemory]:
    return _sessions.get(session_id)


def list_sessions() -> list[str]:
    return list(_sessions.keys())
