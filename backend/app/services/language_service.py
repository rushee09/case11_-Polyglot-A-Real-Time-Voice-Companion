import re
from typing import Tuple, Optional

LANGUAGE_LABELS = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "mixed": "Mixed Hindi-English",
    "unknown": "Unknown",
}

# Rule-based keyword sets
SPANISH_KEYWORDS = {
    "hola", "quiero", "reservar", "para", "personas", "presupuesto",
    "rupias", "noche", "hotel", "hablar", "gracias", "por", "favor",
    "también", "opciones", "confirmar", "fechas", "cuánto", "dónde",
    "cómo", "qué", "está", "son", "pueden", "segunda", "segunda",
    "opción", "sí", "no", "mi", "español", "rusty",
    "continúa", "reserva",
}

HINDI_KEYWORDS = {
    "theek", "lekin", "kal", "tak", "jaayegi", "kya", "aur", "agar",
    "nahi", "mil", "sakta", "mujhe", "karna", "hai", "hoga", "mere",
    "mera", "yeh", "woh", "toh", "bhi", "sab", "karo", "chahiye",
    "jaldi", "bahut", "accha", "acha", "paisa", "ho", "se", "ke", "ka",
    "ki", "nahin", "refund", "delivery", "order", "please", "pizza",
    "veg", "aaj", "kal",
    # common connectors / pronouns / verbs missed before
    "mein", "tum", "aap", "main", "hum", "unhe", "usse", "unka",
    "kaise", "kaisa", "kaisi", "jawab", "hindi", "bolo", "boliye",
    "batao", "bataiye", "dijiye", "do", "suniye", "samajh", "samajhiye",
    "bolna", "chahta", "chahti", "likhiye", "likhna", "padhiye",
    "hain", "tha", "thi", "the", "raha", "rahi", "rahe",
    "hay", "hua", "huye", "naam", "kuch", "koi", "sab", "sabhi",
    "pyar", "desh", "bharat", "duniya", "log", "ghar", "kaam",
}

ENGLISH_STRONG_INDICATORS = {
    "the", "is", "are", "was", "were", "have", "has", "will", "would",
    "can", "could", "should", "would", "hello", "hi", "yes", "no",
    "please", "thank", "what", "where", "when", "how", "need", "want",
    "check", "status", "order", "email", "booking", "hotel", "weather",
}


# Explicit language-switch instruction patterns.
# These override keyword scoring so "jawab Hindi mein dijiye" is never
# mis-classified as English.
_EXPLICIT_LANG_PATTERNS = [
    # Hindi instruction patterns
    (re.compile(r"\b(hindi|hindustani)\s*(mein|main|me|m)\b", re.I), "hi"),
    (re.compile(r"\b(jawab|reply|ans|answer|bolo|boliye|batao|bataiye)\s+.{0,20}\b(hindi|hindustani)\b", re.I), "hi"),
    (re.compile(r"\b(speak|respond|answer|reply|write)\s+in\s+hindi\b", re.I), "hi"),
    # English instruction patterns
    (re.compile(r"\b(speak|respond|answer|reply|write)\s+in\s+english\b", re.I), "en"),
    (re.compile(r"\bin\s+english\s+(please|boliye|dijiye|karo)?\b", re.I), "en"),
    # Spanish instruction patterns
    (re.compile(r"\b(habla|responde|contesta|escribe)\s+en\s+espa[nñ]ol\b", re.I), "es"),
    (re.compile(r"\ben\s+espa[nñ]ol\b", re.I), "es"),
]


def _check_explicit_language_instruction(text: str) -> Optional[str]:
    """Return a forced language code if the user is explicitly requesting a language."""
    for pattern, lang_code in _EXPLICIT_LANG_PATTERNS:
        if pattern.search(text):
            return lang_code
    return None


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    # Keep special Spanish chars
    text = re.sub(r"[^\w\s¿¡áéíóúüñ]", " ", text)
    return text.split()


def detect_language_from_text(text: str) -> Tuple[str, str, Optional[float]]:
    """
    Rule-based language detection.
    Returns (language_code, label, confidence).
    """
    # Check for explicit language-switch instruction first — highest priority
    explicit = _check_explicit_language_instruction(text)
    if explicit:
        return explicit, LANGUAGE_LABELS[explicit], 1.0

    tokens = _tokenize(text)
    token_set = set(tokens)

    # Check for Spanish-specific punctuation
    has_spanish_punct = "¿" in text or "¡" in text

    spanish_hits = len(token_set & SPANISH_KEYWORDS) + (3 if has_spanish_punct else 0)
    hindi_hits = len(token_set & HINDI_KEYWORDS)
    english_hits = len(token_set & ENGLISH_STRONG_INDICATORS)

    total_tokens = max(len(tokens), 1)

    # Normalise by sentence length
    spanish_score = spanish_hits / total_tokens
    hindi_score = hindi_hits / total_tokens
    english_score = english_hits / total_tokens

    # Mixed detection: strong presence of both hindi and english
    if hindi_score > 0.08 and english_score > 0.08:
        return "mixed", LANGUAGE_LABELS["mixed"], round(min(hindi_score, english_score), 2)

    # Dominant language
    scores = {"es": spanish_score, "hi": hindi_score, "en": english_score}
    best = max(scores, key=lambda k: scores[k])
    best_score = scores[best]

    if best_score < 0.03:
        # Try langdetect as fallback
        try:
            from langdetect import detect as ld_detect, DetectorFactory
            DetectorFactory.seed = 0
            ld_lang = ld_detect(text)
            if ld_lang in ("es", "hi", "en"):
                return ld_lang, LANGUAGE_LABELS.get(ld_lang, ld_lang), 0.5
        except Exception:
            pass
        return "en", LANGUAGE_LABELS["en"], 0.3  # default to English

    confidence = round(min(best_score * 5, 1.0), 2)
    return best, LANGUAGE_LABELS[best], confidence


def get_language_label(code: str) -> str:
    return LANGUAGE_LABELS.get(code, "Unknown")
