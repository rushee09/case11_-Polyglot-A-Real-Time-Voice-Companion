"""
language_service.py — Dynamic language detection

Detection strategy (in priority order):
  1. Explicit language-switch instruction  ("speak in Hindi", "en español", etc.)
  2. Romanized Hindi grammar markers       (langdetect cannot detect Latin-script Hindi)
  3. Spanish punctuation ¿ ¡              (unambiguous signal for very short texts)
  4. langdetect library                   (handles 55+ languages via native script)
  5. Fallback: English

No hardcoded vocabulary or scenario-specific keywords.
Language support is limited only by what langdetect can identify.
"""

import re
import logging
from typing import Tuple, Optional
from langdetect import detect_langs, DetectorFactory, LangDetectException

DetectorFactory.seed = 42  # reproducible results across requests

logger = logging.getLogger(__name__)


# ─── ISO 639-1 → Display label ───────────────────────────────────────────────
# Full set of ISO codes langdetect may return, plus special internal codes.

_ISO_LABELS: dict[str, str] = {
    "af": "Afrikaans", "ar": "Arabic", "bg": "Bulgarian", "bn": "Bengali",
    "ca": "Catalan", "cs": "Czech", "cy": "Welsh", "da": "Danish",
    "de": "German", "el": "Greek", "en": "English", "es": "Spanish",
    "et": "Estonian", "fa": "Persian", "fi": "Finnish", "fr": "French",
    "gu": "Gujarati", "he": "Hebrew", "hi": "Hindi", "hr": "Croatian",
    "hu": "Hungarian", "id": "Indonesian", "it": "Italian", "ja": "Japanese",
    "kn": "Kannada", "ko": "Korean", "lt": "Lithuanian", "lv": "Latvian",
    "mk": "Macedonian", "ml": "Malayalam", "mr": "Marathi", "ne": "Nepali",
    "nl": "Dutch", "no": "Norwegian", "pa": "Punjabi", "pl": "Polish",
    "pt": "Portuguese", "ro": "Romanian", "ru": "Russian", "sk": "Slovak",
    "sl": "Slovenian", "sq": "Albanian", "sr": "Serbian", "sv": "Swedish",
    "sw": "Swahili", "ta": "Tamil", "te": "Telugu", "th": "Thai",
    "tl": "Filipino", "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu",
    "vi": "Vietnamese", "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "mixed": "Mixed Languages",
    "unknown": "Unknown",
}


def get_language_label(code: str) -> str:
    """Return a human-readable label for an ISO 639-1 / BCP-47 language code."""
    return _ISO_LABELS.get(code, code.upper())


# ─── Explicit language-switch instruction patterns ───────────────────────────
# Universal meta-instructions the user can give in any conversation topic.
# These ALWAYS override the detection result.

_EXPLICIT_LANG_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Hindi / Hindustani
    (re.compile(r"\b(speak|respond|answer|reply|write|continue)\s+in\s+(hindi|hindustani)\b", re.I), "hi"),
    (re.compile(r"\b(hindi|hindustani)\s*(mein|main|me)\b", re.I), "hi"),
    (re.compile(r"\b(jawab|reply|ans|answer|bolo|boliye|batao|bataiye)\s+.{0,20}\b(hindi|hindustani)\b", re.I), "hi"),
    # English
    (re.compile(r"\b(speak|respond|answer|reply|write|continue)\s+in\s+english\b", re.I), "en"),
    (re.compile(r"\bswitch(\s+back)?\s+to\s+english\b", re.I), "en"),
    (re.compile(r"\bin\s+english\b", re.I), "en"),
    # Spanish
    (re.compile(r"\b(habla|responde|contesta|escribe|continúa)\s+en\s+espa[nñ]ol\b", re.I), "es"),
    (re.compile(r"\ben\s+espa[nñ]ol\b", re.I), "es"),
]


def _check_explicit_language_instruction(text: str) -> Optional[str]:
    """Return a forced language code if the user is explicitly requesting a language."""
    for pattern, lang_code in _EXPLICIT_LANG_PATTERNS:
        if pattern.search(text):
            return lang_code
    return None


# ─── Romanized Hindi grammar markers ─────────────────────────────────────────
# langdetect treats Latin-script Hindi (Romanized / Hinglish) as English because
# it contains no Devanagari characters.  This set contains high-frequency,
# unambiguous Hindi GRAMMAR words — not vocabulary tied to any topic or scenario.

_ROMAN_HINDI: frozenset[str] = frozenset({
    # Copulas / auxiliaries
    "hai", "hain", "tha", "thi", "the", "ho", "hoga", "hogi", "hoge",
    "hua", "hui", "hue",
    # Negation
    "nahi", "nahin", "mat", "na",
    # Interrogatives
    "kya", "kaise", "kaisa", "kaisi", "kaun", "kab", "kahan", "kyun", "kyunki",
    # Conjunctions / discourse markers
    "aur", "lekin", "magar", "toh", "bhi", "par", "agar", "tab", "phir",
    # Personal pronouns
    "mujhe", "mera", "meri", "mere",
    "tum", "tumhe", "tumhara",
    "aap", "aapko", "aapka",
    "main", "hum", "unhe", "usse", "unka", "iska", "uska",
    # Common verb roots (domain-neutral)
    "karo", "karna", "karta", "karti", "karte",
    "chahiye", "chahta", "chahti", "chahte",
    "batao", "bolo", "boliye", "suniye",
    "milega", "milegi", "sakta", "sakti", "sakte",
    "jaana", "jaayega", "jaayegi",
    # Adverbs / adjectives
    "theek", "accha", "acha", "bahut", "jaldi", "abhi",
    "kal", "aaj",
    # Discourse particles
    "bas", "sirf", "sab", "kuch", "koi", "sabhi",
})


def _romanized_hindi_score(tokens: list[str], total: int) -> float:
    return sum(1 for t in tokens if t in _ROMAN_HINDI) / total


# ─── Main detection ──────────────────────────────────────────────────────────

def detect_language_from_text(text: str) -> Tuple[str, str, Optional[float], str]:
    """
    Detect the language of user input.

    Returns:
        (language_code, label, confidence, respond_language)

    respond_language is the code the LLM should reply in:
      - Matches language_code for unambiguous input.
      - For "mixed" (Hinglish): the dominant language ("hi" or "en").
    """
    # 1. Explicit language-switch instruction — always wins
    explicit = _check_explicit_language_instruction(text)
    if explicit:
        return explicit, get_language_label(explicit), 1.0, explicit

    # Tokenise (preserve accented chars so langdetect sees them)
    tokens = re.sub(r"[^\w\s¿¡áéíóúüñ]", " ", text.lower()).split()
    total = max(len(tokens), 1)
    hi_score = _romanized_hindi_score(tokens, total)

    # 2. Run langdetect on the original text (handles native-script languages well)
    ld_lang: Optional[str] = None
    ld_prob: float = 0.0
    try:
        results = detect_langs(text)
        if results:
            ld_lang = results[0].lang
            ld_prob = results[0].prob
    except LangDetectException:
        pass

    # 3. Romanized Hindi / Hinglish
    # langdetect sees Latin-script Hindi as English (often with low confidence).
    english_like = ld_lang in ("en", None) or ld_prob < 0.6
    if hi_score >= 0.10 and english_like:
        if hi_score >= 0.25:
            return "hi", get_language_label("hi"), round(hi_score, 2), "hi"
        dominant = "hi" if hi_score >= 0.15 else "en"
        return "mixed", get_language_label("mixed"), round(hi_score, 2), dominant

    # 4. Spanish — ¿¡ punctuation is unambiguous even in short texts
    has_spanish_punct = "¿" in text or "¡" in text
    if has_spanish_punct or (ld_lang == "es" and ld_prob > 0.35):
        conf = ld_prob if ld_lang == "es" else 0.85
        return "es", get_language_label("es"), round(conf, 2), "es"

    # 5. Hindi in Devanagari — langdetect handles native script reliably
    if ld_lang == "hi" and ld_prob > 0.4:
        return "hi", get_language_label("hi"), round(ld_prob, 2), "hi"

    # 6. Any language langdetect is confident about
    if ld_lang and ld_prob > 0.4:
        return ld_lang, get_language_label(ld_lang), round(ld_prob, 2), ld_lang

    # 7. Mild Romanized Hindi signal
    if hi_score >= 0.06:
        return "hi", get_language_label("hi"), round(hi_score, 2), "hi"

    # 8. Default to English
    return "en", get_language_label("en"), 0.3, "en"

