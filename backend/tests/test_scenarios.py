"""
Scenario integration tests (no LLM required — tests memory + tool layer only).
Run: cd backend && pytest tests/test_scenarios.py -v
"""
import pytest
from app.models.memory import SessionMemory, MemoryEntities
from app.services.memory_service import update_memory_after_turn
from app.services.scenario_tools import extract_entities_from_text, build_tool_context, lookup_order, search_hotels, get_weather
from app.services.language_service import detect_language_from_text


# ─── Scenario 1: Customer Support ───────────────────────────────────────────

def _run_scenario_1():
    session = SessionMemory(session_id="sc1", active_scenario="customer_support")
    turns = [
        ("Hi, I need to check the status of my order. The order ID is 4421.", "en"),
        ("Yes, the email on the account is rahul@example.com.", "en"),
        ("Theek hai, lekin delivery kal tak ho jaayegi kya?", "hi"),
        ("Aur agar nahi hua toh refund mil sakta hai?", "hi"),
        ("Actually let's switch back — can you email me the tracking link?", "en"),
    ]
    for text, expected_lang in turns:
        e = extract_entities_from_text(text, session.entities.to_dict())
        session.entities = MemoryEntities.from_dict(e)
        update_memory_after_turn(session, text, expected_lang, "customer_support")
    return session


def test_scenario_1_order_id_preserved():
    session = _run_scenario_1()
    assert session.entities.order_id == "4421"


def test_scenario_1_email_preserved():
    session = _run_scenario_1()
    assert session.entities.email == "rahul@example.com"


def test_scenario_1_language_switches():
    session = _run_scenario_1()
    # Should have been through en -> hi -> en
    assert session.current_language == "en"


def test_scenario_1_tool_context_has_order():
    session = _run_scenario_1()
    ctx = build_tool_context(session.entities.to_dict(), "customer_support")
    assert "order" in ctx
    assert ctx["order"]["status"] == "Out for delivery"


def test_scenario_1_lookup_order_works():
    result = lookup_order("4421", "rahul@example.com")
    assert result["found"] is True
    assert result["status"] == "Out for delivery"
    assert "refund_policy" in result


# ─── Scenario 2: Travel Planning ────────────────────────────────────────────

def _run_scenario_2():
    session = SessionMemory(session_id="sc2", active_scenario="travel_planning")
    turns = [
        ("Hola, quiero reservar un hotel en Bangalore para el próximo fin de semana.", "es"),
        ("Para dos personas, presupuesto de 5000 rupias por noche.", "es"),
        ("Sorry, my Spanish is rusty. Can we continue in English? Tell me again about the second option.", "en"),
        ("Book it. Confirm the dates please.", "en"),
    ]
    for text, lang in turns:
        e = extract_entities_from_text(text, session.entities.to_dict())
        session.entities = MemoryEntities.from_dict(e)
        update_memory_after_turn(session, text, lang, "travel_planning")
    return session


def test_scenario_2_hotel_city_extracted():
    session = _run_scenario_2()
    assert session.entities.hotel_city is not None
    assert "bangalore" in session.entities.hotel_city.lower()


def test_scenario_2_hotel_people_extracted():
    session = _run_scenario_2()
    assert session.entities.hotel_people == 2


def test_scenario_2_hotel_options_available():
    result = search_hotels("Bangalore", 5000, 2)
    assert result["found"] is True
    assert len(result["options"]) >= 2
    assert result["options"][1]["name"] == "MG Road Business Inn"


def test_scenario_2_second_option_recalled():
    session = _run_scenario_2()
    options = search_hotels("Bangalore", 5000, 2)["options"]
    second = options[1]
    assert second["name"] == "MG Road Business Inn"
    assert second["price_per_night"] == 4800


# ─── Scenario 3: Code-Switching ─────────────────────────────────────────────

def test_scenario_3_mixed_language_detected():
    text = "Mujhe ek pizza order karna hai, but make it veg only please."
    lang, label, _ = detect_language_from_text(text)
    assert lang == "mixed", f"Expected mixed, got {lang}"


def test_scenario_3_food_order_extracted():
    session = SessionMemory(session_id="sc3")
    e = extract_entities_from_text(
        "Mujhe ek pizza order karna hai, but make it veg only please.",
        session.entities.to_dict()
    )
    session.entities = MemoryEntities.from_dict(e)
    assert session.entities.food_order.get("item") == "pizza"
    assert session.entities.food_order.get("preference") == "vegetarian"

    e2 = extract_entities_from_text("And add a coke too.", session.entities.to_dict())
    session.entities = MemoryEntities.from_dict(e2)
    assert session.entities.food_order.get("add_on") == "coke"
    assert session.entities.food_order.get("preference") == "vegetarian"  # still veg


# ─── Scenario 4: Rapid Switching ────────────────────────────────────────────

def _run_scenario_4():
    session = SessionMemory(session_id="sc4", active_scenario="rapid_switching")
    turns = [
        ("What's the weather in Mumbai today?", "en"),
        ("Aur Delhi mein?", "hi"),
        ("¿Y en Chennai?", "es"),
        ("Compare all three for me.", "en"),
    ]
    for text, lang in turns:
        e = extract_entities_from_text(text, session.entities.to_dict())
        session.entities = MemoryEntities.from_dict(e)
        update_memory_after_turn(session, text, lang, "rapid_switching")
    return session


def test_scenario_4_mumbai_in_cities():
    session = _run_scenario_4()
    assert "Mumbai" in session.entities.weather_cities


def test_scenario_4_delhi_in_cities():
    session = _run_scenario_4()
    assert "Delhi" in session.entities.weather_cities


def test_scenario_4_chennai_in_cities():
    session = _run_scenario_4()
    assert "Chennai" in session.entities.weather_cities


def test_scenario_4_weather_tool_works():
    for city in ["Mumbai", "Delhi", "Chennai"]:
        result = get_weather(city)
        assert result["found"] is True, f"Weather not found for {city}"
        assert "temperature" in result


def test_scenario_4_comparison_context_available():
    session = _run_scenario_4()
    ctx = build_tool_context(session.entities.to_dict(), "rapid_switching")
    assert "weather" in ctx
    weather = ctx["weather"]
    assert "Mumbai" in weather
    assert "Delhi" in weather
    assert "Chennai" in weather
