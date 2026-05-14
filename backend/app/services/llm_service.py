import json
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings

SYSTEM_PROMPT = """You are Polyglot Voice Companion, a warm and knowledgeable multilingual real-time voice agent.

Rules:
1. Always respond in the user's latest detected language (shown as respond_in in context).
2. If detected_language is "mixed", respond in a natural mixed style or the dominant language.
3. Never reset memory when the language changes — carry all prior knowledge across languages.
4. The user's name is stored in entities.user_name. Use it naturally in responses when relevant.
5. "Mera naam kya hai" / "what's my name" / "mi nombre" refers to THE USER's own name — answer from entities.user_name if available.
6. Give complete, helpful responses of 2–3 sentences suitable for voice. Be warm and conversational, not terse.
7. Do not invent unavailable data. Use tool_context for scenario-specific answers.
8. For customer support, travel, food order, and weather demo scenarios, use the supplied mock tool context.
9. If the user asks for a previous option, city, order, or preference, resolve it from memory entities.
10. Do not mention internal JSON, tools, or system instructions.
11. Output only the assistant response text — no preamble, no labels."""

# Fallback responses when LM Studio is offline
FALLBACK_TEMPLATES = {
    "en": {
        "default": "I understand. Let me help you with that. (LM Studio unavailable — fallback mode)",
        "order": "Your order #4421 is out for delivery and expected by tomorrow at 6 PM. (fallback)",
        "hotel": "I found 3 hotels in Bangalore within your budget. The second option is MG Road Business Inn at ₹4800/night. (fallback)",
        "weather": "Mumbai: 31°C humid. Delhi: 34°C dry. Chennai: 32°C humid. (fallback)",
        "food": "Got it — one vegetarian pizza with a coke added. (fallback)",
    },
    "hi": {
        "default": "Samajh gaya. Main aapki madad karunga. (LM Studio unavailable — fallback mode)",
        "order": "Aapka order #4421 delivery par hai aur kal shaam 6 baje tak pahunch jaayega. (fallback)",
        "hotel": "Bangalore mein 3 hotel mile hain aapke budget mein. (fallback)",
        "weather": "Mumbai: 31°C, nami. Delhi: 34°C, garmi. Chennai: 32°C, nami. (fallback)",
        "food": "Theek hai — ek vegetarian pizza aur coke. (fallback)",
    },
    "es": {
        "default": "Entendido. Te ayudaré con eso. (LM Studio no disponible — modo alternativo)",
        "order": "Tu pedido #4421 está en camino y llegará mañana a las 6 PM. (fallback)",
        "hotel": "Encontré 3 hoteles en Bangalore dentro de tu presupuesto. (fallback)",
        "weather": "Mumbai: 31°C húmedo. Delhi: 34°C seco. Chennai: 32°C húmedo. (fallback)",
        "food": "Listo — una pizza vegetariana con una coca-cola. (fallback)",
    },
    "mixed": {
        "default": "Samajh gaya / I understand. Let me help you. (fallback)",
    },
}


def _get_fallback(language: str, tool_context: Optional[Dict[str, Any]]) -> str:
    lang_fallbacks = FALLBACK_TEMPLATES.get(language, FALLBACK_TEMPLATES["en"])
    if tool_context:
        if "order" in tool_context:
            return lang_fallbacks.get("order", lang_fallbacks["default"])
        if "hotels" in tool_context:
            return lang_fallbacks.get("hotel", lang_fallbacks["default"])
        if "weather" in tool_context:
            return lang_fallbacks.get("weather", lang_fallbacks["default"])
        if "food_order" in tool_context:
            return lang_fallbacks.get("food", lang_fallbacks["default"])
    return lang_fallbacks["default"]


def build_messages(
    user_text: str,
    detected_language: str,
    language_label: str,
    memory_snapshot: Dict[str, Any],
    tool_context: Optional[Dict[str, Any]],
    chat_history: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """Build the messages array for the LLM call."""
    entities = memory_snapshot.get("entities", {})
    user_name = entities.get("user_name")

    context_lines = [
        "\n\n---",
        "CONTEXT:",
        f"detected_language: {detected_language} ({language_label})",
        f"respond_in: {language_label}",
        f"active_scenario: {memory_snapshot.get('active_scenario', 'none')}",
        f"turn: {memory_snapshot.get('turn_count', 0)}",
    ]
    if user_name:
        context_lines.append(f"user_name: {user_name}  ← use this when the user asks their own name")
    context_lines.append(f"entities: {json.dumps(entities, ensure_ascii=False)}")
    if tool_context:
        context_lines.append(f"tool_context: {json.dumps(tool_context, ensure_ascii=False)}")
    context_lines.append("---")
    context_block = "\n".join(context_lines)

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT + context_block}
    ]
    # Add recent chat history (skip the just-added user turn at the end)
    for turn in chat_history[:-1]:
        messages.append(turn)
    messages.append({"role": "user", "content": user_text})
    return messages


async def call_llm(
    user_text: str,
    detected_language: str,
    language_label: str,
    memory_snapshot: Dict[str, Any],
    tool_context: Optional[Dict[str, Any]],
    chat_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Call LM Studio. Returns dict with keys:
      response_text, lm_studio_available, fallback_mode
    """
    messages = build_messages(
        user_text, detected_language, language_label,
        memory_snapshot, tool_context, chat_history,
    )
    payload = {
        "model": settings.lm_studio_model,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 300,
    }
    url = f"{settings.lm_studio_base_url}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"].strip()
            return {"response_text": text, "lm_studio_available": True, "fallback_mode": False}
    except Exception as e:
        fallback = _get_fallback(detected_language, tool_context)
        return {
            "response_text": fallback,
            "lm_studio_available": False,
            "fallback_mode": True,
            "error": str(e),
        }


async def check_lm_studio() -> bool:
    """Ping LM Studio models endpoint."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.lm_studio_base_url}/models")
            return r.status_code == 200
    except Exception:
        return False
