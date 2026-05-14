"""
Tests for memory persistence across language switches.
Run: cd backend && pytest tests/test_memory.py -v
"""
import pytest
from app.models.memory import SessionMemory, MemoryEntities
from app.services.memory_service import get_or_create_session, update_memory_after_turn
from app.services.scenario_tools import extract_entities_from_text


def test_order_id_persists_across_en_hi_en():
    session = SessionMemory(session_id="mem_test_1")
    # Turn 1 — English
    entities = extract_entities_from_text("The order ID is 4421", session.entities.to_dict())
    session.entities = MemoryEntities.from_dict(entities)
    session.add_turn("user", "The order ID is 4421", "en", "English")

    # Turn 2 — Hindi
    update_memory_after_turn(session, "Theek hai, delivery kal tak kya?", "hi", "customer_support")
    assert session.entities.order_id == "4421", "Order ID must persist after switching to Hindi"

    # Turn 3 — Back to English
    update_memory_after_turn(session, "Can you email me the tracking link?", "en", "customer_support")
    assert session.entities.order_id == "4421", "Order ID must persist after switching back to English"


def test_email_persists_after_language_switch():
    session = SessionMemory(session_id="mem_test_2")
    entities = extract_entities_from_text("the email is rahul@example.com", {})
    session.entities = MemoryEntities.from_dict(entities)
    session.add_turn("user", "the email is rahul@example.com", "en", "English")

    update_memory_after_turn(session, "Theek hai, delivery kal tak kya?", "hi", None)
    assert session.entities.email == "rahul@example.com", "Email must persist after Hindi switch"


def test_hotel_second_option_remembered_after_spanish_to_english():
    session = SessionMemory(session_id="mem_test_3")

    # Turn 1 — Spanish
    entities = extract_entities_from_text(
        "quiero reservar un hotel en Bangalore presupuesto 5000 rupias dos personas",
        session.entities.to_dict()
    )
    session.entities = MemoryEntities.from_dict(entities)
    session.add_turn("user", "quiero reservar...", "es", "Spanish")

    # Simulate hotel options being stored
    session.entities.hotel_options = [
        {"index": 1, "name": "Indiranagar Comfort Stay", "price_per_night": 4200},
        {"index": 2, "name": "MG Road Business Inn", "price_per_night": 4800},
        {"index": 3, "name": "Koramangala Studio Hotel", "price_per_night": 4500},
    ]

    # Turn 2 — English asks for second option
    update_memory_after_turn(
        session,
        "Tell me again about the second option",
        "en",
        "travel_planning"
    )
    assert len(session.entities.hotel_options) == 3, "Hotel options must persist across language switch"
    assert session.entities.hotel_options[1]["name"] == "MG Road Business Inn"


def test_weather_cities_contain_all_three():
    session = SessionMemory(session_id="mem_test_4")
    for text in [
        "What's the weather in Mumbai today?",
        "Aur Delhi mein?",
        "¿Y en Chennai?",
        "Compare all three for me.",
    ]:
        city_entities = extract_entities_from_text(text, session.entities.to_dict())
        session.entities = MemoryEntities.from_dict(city_entities)
    cities = session.entities.weather_cities
    assert "Mumbai" in cities, f"Mumbai missing from {cities}"
    assert "Delhi" in cities, f"Delhi missing from {cities}"
    assert "Chennai" in cities, f"Chennai missing from {cities}"


def test_food_order_remembers_veg_pizza_and_coke():
    session = SessionMemory(session_id="mem_test_5")
    e1 = extract_entities_from_text(
        "Mujhe ek pizza order karna hai, but make it veg only please",
        session.entities.to_dict()
    )
    session.entities = MemoryEntities.from_dict(e1)
    assert session.entities.food_order.get("item") == "pizza"
    assert session.entities.food_order.get("preference") == "vegetarian"

    e2 = extract_entities_from_text("And add a coke too", session.entities.to_dict())
    session.entities = MemoryEntities.from_dict(e2)
    assert session.entities.food_order.get("add_on") == "coke"
    # Pizza preference still present
    assert session.entities.food_order.get("preference") == "vegetarian"
