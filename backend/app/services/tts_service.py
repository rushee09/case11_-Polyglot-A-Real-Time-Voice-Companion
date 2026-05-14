"""
TTS Service — backend abstraction stub.
Core TTS is handled by browser speechSynthesis on the frontend.
This module is ready for future Piper/Coqui integration.
"""
from typing import Optional, Dict, Any

LANG_TO_VOICE = {
    "en": "en-US",
    "hi": "hi-IN",
    "es": "es-ES",
    "mixed": "hi-IN",
    "unknown": "en-US",
}


def get_tts_lang_code(language: str) -> str:
    """Return BCP-47 language tag for browser speechSynthesis."""
    return LANG_TO_VOICE.get(language, "en-US")


def get_tts_metadata(language: str, text: str) -> Dict[str, Any]:
    """Return TTS metadata for frontend to use with speechSynthesis."""
    return {
        "lang": get_tts_lang_code(language),
        "text": text,
        "backend_tts_available": False,
        "note": "Using browser speechSynthesis. Backend TTS (Piper/Coqui) stub ready.",
    }


# Future: async def synthesize(text: str, language: str) -> bytes:
#     """Synthesize speech with Piper or Coqui."""
#     raise NotImplementedError("Backend TTS not yet implemented.")
