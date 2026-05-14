from fastapi import APIRouter, HTTPException
from app.services.memory_service import get_session_memory, list_sessions
from app.services import storage_service
from app.services.scenario_tools import (
    lookup_order, search_hotels, get_weather, pizza_order_context
)

router = APIRouter(prefix="/api")

# ─── Scenarios data ──────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "name": "customer_support",
        "title": "Scenario 1 — Customer Support: Order Status",
        "description": "English → Hindi → English with order context preserved.",
        "turns": [
            {"turn_number": 1, "language": "en", "user_text": "Hi, I need to check the status of my order. The order ID is 4421.", "translation": None, "expected_behavior": "Agent acknowledges in English and asks for verification."},
            {"turn_number": 2, "language": "en", "user_text": "Yes, the email on the account is rahul@example.com.", "translation": None, "expected_behavior": "Agent confirms order is out for delivery in English."},
            {"turn_number": 3, "language": "hi", "user_text": "Theek hai, lekin delivery kal tak ho jaayegi kya?", "translation": "OK, but will the delivery happen by tomorrow?", "expected_behavior": "Agent switches to Hindi, retains order context, answers in Hindi."},
            {"turn_number": 4, "language": "hi", "user_text": "Aur agar nahi hua toh refund mil sakta hai?", "translation": "And if not, can I get a refund?", "expected_behavior": "Agent continues in Hindi and answers refund question using order context."},
            {"turn_number": 5, "language": "en", "user_text": "Actually let's switch back — can you email me the tracking link?", "translation": None, "expected_behavior": "Agent switches back to English and remembers order/email context."},
        ],
    },
    {
        "name": "travel_planning",
        "title": "Scenario 2 — Travel Planning: Hotel Booking",
        "description": "Spanish → English with hotel options recalled.",
        "turns": [
            {"turn_number": 1, "language": "es", "user_text": "Hola, quiero reservar un hotel en Bangalore para el próximo fin de semana.", "translation": "Hello, I want to book a hotel in Bangalore for next weekend.", "expected_behavior": "Agent responds in Spanish."},
            {"turn_number": 2, "language": "es", "user_text": "Para dos personas, presupuesto de 5000 rupias por noche.", "translation": "For two people, budget of 5000 rupees per night.", "expected_behavior": "Agent suggests options in Spanish."},
            {"turn_number": 3, "language": "en", "user_text": "Sorry, my Spanish is rusty. Can we continue in English? Tell me again about the second option.", "translation": None, "expected_behavior": "Agent switches to English and recalls the second hotel option."},
            {"turn_number": 4, "language": "en", "user_text": "Book it. Confirm the dates please.", "translation": None, "expected_behavior": "Agent confirms booking details in English."},
        ],
    },
    {
        "name": "code_switching",
        "title": "Scenario 3 — Code-Switching Within an Utterance",
        "description": "Mixed Hindi-English handled gracefully.",
        "turns": [
            {"turn_number": 1, "language": "mixed", "user_text": "Mujhe ek pizza order karna hai, but make it veg only please.", "translation": "I want to order a pizza, but make it veg only please.", "expected_behavior": "Agent handles mixed language gracefully and documents choice."},
            {"turn_number": 2, "language": "en", "user_text": "And add a coke too.", "translation": None, "expected_behavior": "Agent remembers veg pizza order and adds coke."},
        ],
    },
    {
        "name": "rapid_switching",
        "title": "Scenario 4 — Rapid Language Switching",
        "description": "English → Hindi → Spanish → English with city memory.",
        "turns": [
            {"turn_number": 1, "language": "en", "user_text": "What's the weather in Mumbai today?", "translation": None, "expected_behavior": "Agent answers about Mumbai in English."},
            {"turn_number": 2, "language": "hi", "user_text": "Aur Delhi mein?", "translation": "And in Delhi?", "expected_behavior": "Agent understands context and answers in Hindi."},
            {"turn_number": 3, "language": "es", "user_text": "¿Y en Chennai?", "translation": "And in Chennai?", "expected_behavior": "Agent understands context and answers in Spanish."},
            {"turn_number": 4, "language": "en", "user_text": "Compare all three for me.", "translation": None, "expected_behavior": "Agent compares Mumbai, Delhi, Chennai in English using memory."},
        ],
    },
]


@router.get("/scenarios")
async def get_scenarios():
    return SCENARIOS


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
