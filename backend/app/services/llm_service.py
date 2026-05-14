"""
llm_service.py — Agent-loop LLM caller
────────────────────────────────────────
Architecture
  1. Build initial messages: system prompt + session context + chat history + user turn.
  2. POST to LM Studio with tool schemas attached.
  3. If the model returns tool_calls:
       a. Execute each tool locally.
       b. Append assistant + tool-result messages to the thread.
       c. Loop (max 5 iterations = up to 4 tool-calling rounds + 1 final).
  4. Return the final natural-language response together with every tool result
     collected this turn (so chat.py can persist them to session.tool_cache).

The LLM is NEVER given pre-fetched data injected by the backend — it decides what
to look up and calls tools itself, exactly like a real agent.
"""

import json
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings

# Maps language codes to display labels used in the system context block
_LANG_LABELS: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "mixed": "Mixed Hindi-English",
}

# ─── System prompt ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are Polyglot — an intelligent, warm multilingual assistant fluent in English, \
Hindi (including Hinglish), and Spanish. You reason carefully before responding, \
just like a thoughtful human expert would.

── LANGUAGE ──────────────────────────────────────────────────────────────────
Respond in the language specified by `respond_in` in SESSION CONTEXT. Never mix
languages in a single reply. When the user switches language mid-conversation,
carry all prior context forward seamlessly — never ask again for something already
provided.

── REASONING & TOOLS ─────────────────────────────────────────────────────────
Think about what the user actually needs before you respond or call a tool.
If completing a task requires information you don't have yet, ask for it
conversationally — one missing piece at a time, never all at once.

You have tools at your disposal (travel planning, hotel search, weather lookup,
order tracking, food orders). Use them when and only when you genuinely need
external data. Once you have tool results, never re-call the same tool — draw from
`prior_tool_results` in SESSION CONTEXT for any follow-up on the same data.
After receiving tool results, speak naturally — never expose field names, JSON, or
tool names to the user.

── MEMORY ────────────────────────────────────────────────────────────────────
Everything the user has said this session is available to you. Use it. Never ask
for something already given. If the user's name is in SESSION CONTEXT, use it
naturally.

── HANDLING INTERRUPTIONS ────────────────────────────────────────────────────
If the user goes off-topic while you are mid-task (e.g. mid travel planning, order
lookup, food order):
  • Handle or respond to the new topic first.
  • If it is outside your scope (writing office emails, coding, medical/legal
    advice, etc.), politely say you can't help with that and briefly mention what
    you can do.
  • Then, in the same reply, smoothly return to where you left off — only asking
    for information you still need.

── STYLE ─────────────────────────────────────────────────────────────────────
Warm, thoughtful, and natural — like talking to a knowledgeable friend, not
reading a script. For quick questions: 2–3 sentences. For detailed answers like
itineraries or comparisons: as long as genuinely useful. No bullet JSON or raw
data in replies. Output the reply text only — no labels, no preamble.\
"""


# ─── Session context block ─────────────────────────────────────────────────
def _build_context_block(
    detected_language: str,
    language_label: str,
    memory_snapshot: Dict[str, Any],
    respond_language: str,
) -> str:
    """
    Appended to the system prompt so the model knows:
    - what language to respond in
    - the user's name (if known)
    - all tool results fetched in prior turns (the agent's cross-turn memory)
    """
    entities = memory_snapshot.get("entities", {})
    tool_cache = memory_snapshot.get("tool_cache", {})
    # Use the caller-computed respond_language; fall back to language_label only
    # if the code is somehow unknown (should never happen in practice).
    respond_label = _LANG_LABELS.get(respond_language, language_label)

    lines = [
        "\n\n════════════════════════════════════════",
        "SESSION CONTEXT",
        "════════════════════════════════════════",
        f"respond_in: {respond_label}",
        f"detected_language: {detected_language}",
        f"turn: {memory_snapshot.get('turn_count', 0)}",
        f"scenario: {memory_snapshot.get('active_scenario') or 'general'}",
    ]
    if entities.get("user_name"):
        lines.append(f"user_name: {entities['user_name']}")
    if tool_cache:
        lines.append(
            f"prior_tool_results: {json.dumps(tool_cache, ensure_ascii=False)}"
        )
    lines.append("════════════════════════════════════════")
    return "\n".join(lines)


# ─── Message builder ───────────────────────────────────────────────────────
def _build_initial_messages(
    user_text: str,
    detected_language: str,
    language_label: str,
    memory_snapshot: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    respond_language: str = "en",
) -> List[Dict[str, Any]]:
    context_block = _build_context_block(detected_language, language_label, memory_snapshot, respond_language)
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT + context_block}
    ]
    # Prior turns — exclude the last entry (it IS the current user message,
    # added from memory before we handle the response).
    for turn in chat_history[:-1]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_text})
    return messages


# ─── Content-embedded tool call parser ────────────────────────────────────
def _parse_content_tool_calls(content: str) -> List[Dict[str, Any]]:
    """
    Mistral-NeMo (and some other local models) embed tool calls as a JSON array
    in the `content` field instead of using the `tool_calls` field, e.g.:

        content: '[{"name": "lookup_order", "arguments": {"order_id": "4421"}}]'
        tool_calls: []
        finish_reason: "stop"

    This function detects that pattern and normalises it to the standard
    OpenAI tool_calls format so the agent loop can handle it uniformly.
    Returns an empty list if content does not look like tool calls.
    """
    if not content:
        return []
    content = content.strip()
    # Quick rejection: must be a JSON array
    if not (content.startswith("[") and content.endswith("]")):
        return []
    try:
        parsed = json.loads(content)
        if not isinstance(parsed, list):
            return []
        normalized: List[Dict[str, Any]] = []
        for idx, item in enumerate(parsed):
            if not (isinstance(item, dict) and "name" in item and "arguments" in item):
                return []  # not a tool call array — treat as regular content
            args = item["arguments"]
            args_str = json.dumps(args) if isinstance(args, dict) else str(args)
            normalized.append(
                {
                    "id": f"call_{item['name']}_{idx}",
                    "type": "function",
                    "function": {"name": item["name"], "arguments": args_str},
                }
            )
        return normalized
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


# ─── Agent loop ────────────────────────────────────────────────────────────
async def call_llm(
    user_text: str,
    detected_language: str,
    language_label: str,
    memory_snapshot: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    respond_language: str = "en",
    tool_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the agent loop.

    Returns a dict with:
      response_text       — the final natural-language reply
      lm_studio_available — bool
      fallback_mode       — bool (True only when LM Studio is unreachable)
      tool_results        — {tool_name: result} for every tool called this turn
                            (caller should deep-merge into session.tool_cache)
    """
    # Local import to avoid circular dependencies at module load time
    from app.services.scenario_tools import TOOL_DEFINITIONS, execute_tool

    messages = _build_initial_messages(
        user_text, detected_language, language_label, memory_snapshot, chat_history, respond_language
    )
    url = f"{settings.lm_studio_base_url}/chat/completions"
    tool_results_this_turn: Dict[str, Any] = {}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            for _iteration in range(5):  # up to 4 tool-call rounds + 1 final reply
                payload = {
                    "model": settings.lm_studio_model,
                    "messages": messages,
                    "temperature": 0.65,
                    "max_tokens": 900,
                    "tools": TOOL_DEFINITIONS,
                    "tool_choice": "auto",
                }

                r = await client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()

                choice = data["choices"][0]
                finish_reason = choice.get("finish_reason", "stop")
                assistant_msg = choice["message"]

                # ── Normalise tool calls ────────────────────────────────────
                # Standard path: model uses the tool_calls field correctly.
                # Fallback path: Mistral-NeMo / some local models embed tool
                # calls as a JSON array string inside the content field while
                # leaving tool_calls empty and finish_reason as "stop".
                tool_calls = assistant_msg.get("tool_calls") or []
                if not tool_calls:
                    content_text = (assistant_msg.get("content") or "").strip()
                    tool_calls = _parse_content_tool_calls(content_text)
                    if tool_calls:
                        # Rewrite the message so the loop handles it uniformly
                        assistant_msg = {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": tool_calls,
                        }

                # ── Tool-calling round ──────────────────────────────────────
                if tool_calls:
                    messages.append(assistant_msg)  # assistant turn with tool_calls

                    for tc in tool_calls:
                        fn_name = tc["function"]["name"]
                        try:
                            fn_args = json.loads(tc["function"]["arguments"])
                        except (json.JSONDecodeError, TypeError):
                            fn_args = {}

                        result = execute_tool(fn_name, fn_args)

                        # Weather results are keyed by city so multiple
                        # city lookups merge rather than overwrite each other.
                        if fn_name == "get_weather" and result.get("found"):
                            weather_bucket = tool_results_this_turn.setdefault(
                                "get_weather", {}
                            )
                            weather_bucket[result["city"]] = result
                        else:
                            tool_results_this_turn[fn_name] = result

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )
                    continue  # give the model its results and loop

                # ── Final text response ─────────────────────────────────────
                text = (assistant_msg.get("content") or "").strip()
                return {
                    "response_text": text,
                    "lm_studio_available": True,
                    "fallback_mode": False,
                    "tool_results": tool_results_this_turn,
                }

        # Exhausted iterations without a final stop
        return {
            "response_text": "I couldn't finish that in time — please try again.",
            "lm_studio_available": True,
            "fallback_mode": False,
            "tool_results": tool_results_this_turn,
        }

    except Exception as exc:
        return {
            "response_text": (
                "I'm having trouble connecting right now. "
                "Please make sure LM Studio is running and try again."
            ),
            "lm_studio_available": False,
            "fallback_mode": True,
            "error": str(exc),
            "tool_results": {},
        }


# ─── Health check ──────────────────────────────────────────────────────────
async def check_lm_studio() -> bool:
    """Ping the LM Studio models endpoint."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.lm_studio_base_url}/models")
            return r.status_code == 200
    except Exception:
        return False

