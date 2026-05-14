"""
guardrail_service.py — Input guardrail against prompt injection & jailbreak attempts.

Checks (ordered cheapest → costliest):
  1. Hard length cap  (prevents context-window flooding / DoS)
  2. Word-repetition flood  (prevents token-stuffing attacks)
  3. Regex pattern bank  (instruction overrides, persona hijacks, delimiter injection,
                          HTML/JS injection, encoding probes, data-extraction probes)

All checks are in-process — no external API required.
Nothing in the error response reveals which rule fired, preventing adversaries from
reverse-engineering the filter.
"""

import re
import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Tuneable limits ────────────────────────────────────────────────────────

MAX_INPUT_CHARS = 2_000   # hard cap on raw text length
MAX_WORD_REPEATS = 50     # reject if any single token appears > N times

# ─── Pattern bank ──────────────────────────────────────────────────────────
# Each entry: (compiled regex, reason_tag, severity)
# severity: "high" | "medium"

_RULES: list[tuple[re.Pattern, str, str]] = [

    # ── Instruction-override attacks ────────────────────────────────────────
    (
        re.compile(
            r"ignore\s+(all\s+)?(previous|prior|above|your)\s+"
            r"(instructions?|rules?|prompts?|guidelines?|constraints?)",
            re.I,
        ),
        "instruction_override", "high",
    ),
    (
        re.compile(
            r"disregard\s+(all\s+)?(previous|prior|above|your)\s+", re.I
        ),
        "instruction_override", "high",
    ),
    (
        re.compile(
            r"forget\s+(your\s+)?"
            r"(instructions?|system\s+prompt|guidelines?|rules?|constraints?|training)",
            re.I,
        ),
        "instruction_override", "high",
    ),
    (
        re.compile(
            r"override\s+(your\s+)?"
            r"(programming|instructions?|rules?|constraints?|directives?)",
            re.I,
        ),
        "instruction_override", "high",
    ),
    (
        re.compile(
            r"(your\s+(new|real|actual|true)\s+"
            r"(instructions?|rules?|purpose|goal|objective)\s+(are|is|:))",
            re.I,
        ),
        "instruction_override", "high",
    ),
    (
        re.compile(
            r"(from\s+now\s+on|starting\s+now|new\s+directive)"
            r".{0,80}(you\s+(will|must|should|are\s+to))",
            re.I | re.S,
        ),
        "instruction_override", "high",
    ),

    # ── Persona / role-play hijacks ─────────────────────────────────────────
    (
        re.compile(
            r"\b(you\s+are\s+now|act\s+as|pretend\s+(to\s+be|you\s+are)|"
            r"roleplay\s+as|imagine\s+you\s+are|simulate\s+being)\b"
            r".{0,80}(AI|bot|assistant|model|GPT|DAN|evil|unrestricted|no\s+limit)",
            re.I | re.S,
        ),
        "persona_hijack", "high",
    ),
    (
        re.compile(r"\bDAN\b"),   # "Do Anything Now" — case-sensitive intentional
        "jailbreak_keyword", "high",
    ),
    (
        re.compile(r"\bjailbreak\b", re.I),
        "jailbreak_keyword", "high",
    ),

    # ── Restriction-bypass phrasing ──────────────────────────────────────────
    (
        re.compile(
            r"no\s+(ethical\s+)?"
            r"(limits?|restrictions?|rules?|guidelines?|filters?|safeguards?)",
            re.I,
        ),
        "restriction_bypass", "high",
    ),
    (
        re.compile(
            r"(without|bypass|skip|remove)\s+(your\s+)?"
            r"(safety|ethical|content)\s+(filter|guard|check|restriction|policy)",
            re.I,
        ),
        "restriction_bypass", "high",
    ),

    # ── System-prompt delimiter injection ───────────────────────────────────
    (
        re.compile(
            r"(<\|system\|>|\[SYSTEM\]|###\s*system|<system>|"
            r"\[\[SYSTEM\]\]|<\|im_start\|>|\[INST\]|\[\/INST\])",
            re.I,
        ),
        "system_delimiter", "high",
    ),
    (
        re.compile(
            r"---+\s*(end\s+of\s+(prompt|system|instruction)|"
            r"new\s+(instruction|prompt|task))",
            re.I,
        ),
        "delimiter_injection", "high",
    ),

    # ── HTML / JavaScript injection ─────────────────────────────────────────
    (
        re.compile(
            r"<\s*(script|iframe|object|embed|svg|img|link|meta|style)[^>]{0,200}>",
            re.I,
        ),
        "html_injection", "medium",
    ),
    (
        re.compile(r"javascript\s*:", re.I),
        "html_injection", "medium",
    ),

    # ── System-prompt / training-data extraction probes ─────────────────────
    (
        re.compile(
            r"(print|output|repeat|echo|reveal|show|display|tell\s+me)\s+"
            r"(your\s+)?"
            r"(system\s+prompt|instructions?|training\s+data|"
            r"context\s+window|internal\s+prompt|initial\s+prompt)",
            re.I,
        ),
        "data_extraction", "medium",
    ),
    (
        re.compile(
            r"what\s+(are|is)\s+(your\s+)?(system\s+)?instructions?\b", re.I
        ),
        "data_extraction", "medium",
    ),

    # ── Encoding / obfuscation probes ───────────────────────────────────────
    (
        re.compile(r"base64\s*(decode|encode)\s*[:=\(]", re.I),
        "encoding_probe", "medium",
    ),
    (
        re.compile(r"(\\x[0-9a-fA-F]{2}){5,}"),
        "encoding_probe", "medium",
    ),
]


# ─── Result type ────────────────────────────────────────────────────────────

@dataclass
class GuardrailResult:
    blocked: bool
    reason: Optional[str] = None        # internal tag — never sent to client
    severity: str = "none"              # "none" | "medium" | "high"
    detail: str = field(default="")     # internal notes for logging


# ─── Friendly blocked message (intentionally vague) ─────────────────────────
# Does NOT reveal which rule fired — prevents adversaries reverse-engineering the filter.

BLOCKED_RESPONSE = (
    "I'm here to help with travel, orders, weather, and conversation. "
    "I couldn't process that message — please try rephrasing."
)


# ─── Main check ─────────────────────────────────────────────────────────────

def check_input(text: str) -> GuardrailResult:
    """
    Validate raw user input before it reaches the LLM.
    Returns GuardrailResult with blocked=True if the input should be rejected.
    """

    # 1. Hard length cap
    if len(text) > MAX_INPUT_CHARS:
        logger.warning(
            "[guardrail] BLOCKED reason=input_too_long len=%d",
            len(text),
        )
        return GuardrailResult(
            blocked=True,
            reason="input_too_long",
            severity="medium",
            detail=f"length {len(text)} > {MAX_INPUT_CHARS}",
        )

    # 2. Repetition-flood check (token stuffing)
    tokens = text.lower().split()
    if tokens:
        top_word, top_count = Counter(tokens).most_common(1)[0]
        if top_count > MAX_WORD_REPEATS:
            logger.warning(
                "[guardrail] BLOCKED reason=repetition_flood word=%r count=%d",
                top_word,
                top_count,
            )
            return GuardrailResult(
                blocked=True,
                reason="repetition_flood",
                severity="medium",
                detail=f"word '{top_word}' repeated {top_count} times",
            )

    # 3. Pattern scan
    for pattern, reason, severity in _RULES:
        if pattern.search(text):
            snippet = text[:120].replace("\n", " ")
            logger.warning(
                "[guardrail] BLOCKED reason=%s severity=%s snippet=%r",
                reason,
                severity,
                snippet,
            )
            return GuardrailResult(
                blocked=True,
                reason=reason,
                severity=severity,
                detail=f"matched pattern for {reason}",
            )

    return GuardrailResult(blocked=False)
