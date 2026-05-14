"""
Tests for language detection and switch event creation.
Run: cd backend && pytest tests/test_language_switch.py -v
"""
import pytest
from app.services.language_service import detect_language_from_text
from app.models.memory import SessionMemory
from app.services.memory_service import update_memory_after_turn


def test_english_detection():
    lang, label, _ = detect_language_from_text(
        "Hi, I need to check the status of my order. The order ID is 4421."
    )
    assert lang == "en", f"Expected 'en', got '{lang}'"
    assert label == "English"


def test_hindi_detection():
    lang, label, _ = detect_language_from_text(
        "Theek hai, lekin delivery kal tak ho jaayegi kya?"
    )
    assert lang == "hi", f"Expected 'hi', got '{lang}'"
    assert label == "Hindi"


def test_hindi_refund_detection():
    lang, label, _ = detect_language_from_text(
        "Aur agar nahi hua toh refund mil sakta hai?"
    )
    assert lang == "hi", f"Expected 'hi', got '{lang}'"


def test_spanish_detection():
    lang, label, _ = detect_language_from_text(
        "Hola, quiero reservar un hotel en Bangalore para el próximo fin de semana."
    )
    assert lang == "es", f"Expected 'es', got '{lang}'"
    assert label == "Spanish"


def test_spanish_detection_2():
    lang, label, _ = detect_language_from_text(
        "¿Y en Chennai?"
    )
    assert lang == "es", f"Expected 'es', got '{lang}'"


def test_mixed_hindi_english_detection():
    lang, label, _ = detect_language_from_text(
        "Mujhe ek pizza order karna hai, but make it veg only please."
    )
    assert lang == "mixed", f"Expected 'mixed', got '{lang}'"
    assert "Mixed" in label


def test_language_switch_event_created():
    session = SessionMemory(session_id="switch_test_1")
    session.add_turn("user", "Hello", "en", "English")
    session.current_language = "en"

    result = update_memory_after_turn(session, "Theek hai, delivery kya?", "hi", None)
    assert result["language_switched"] is True
    assert result["event"]["from_language"] == "en"
    assert result["event"]["to_language"] == "hi"


def test_no_switch_event_same_language():
    session = SessionMemory(session_id="switch_test_2")
    session.add_turn("user", "Hello", "en", "English")
    session.current_language = "en"

    result = update_memory_after_turn(session, "Can you help me?", "en", None)
    assert result["language_switched"] is False


def test_language_switch_en_to_es():
    session = SessionMemory(session_id="switch_test_3")
    session.add_turn("user", "Hello", "en", "English")
    session.current_language = "en"

    result = update_memory_after_turn(
        session,
        "Hola, quiero reservar un hotel en Bangalore.",
        "es", None
    )
    assert result["language_switched"] is True
    assert result["event"]["to_language"] == "es"
