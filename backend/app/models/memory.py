from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MemoryEntities:
    """
    Universal entity store — works across any conversation domain.
    Only truly cross-domain facts are tracked as first-class fields.
    Everything else (order details, trip parameters, food items, etc.)
    is held by the LLM's tool_cache in SessionMemory.
    """
    user_name: Optional[str] = None
    order_id: Optional[str] = None   # any reference / booking / order ID
    email: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)  # free-form domain facts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_name": self.user_name,
            "order_id": self.order_id,
            "email": self.email,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryEntities":
        return cls(
            user_name=d.get("user_name"),
            order_id=d.get("order_id"),
            email=d.get("email"),
            context=d.get("context", {}),
        )


@dataclass
class ConversationTurn:
    turn_number: int
    role: str  # "user" or "assistant"
    text: str
    detected_language: str
    language_label: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_number": self.turn_number,
            "role": self.role,
            "text": self.text,
            "detected_language": self.detected_language,
            "language_label": self.language_label,
            "timestamp": self.timestamp,
        }


@dataclass
class SessionMemory:
    session_id: str
    active_scenario: Optional[str] = None
    current_language: str = "en"
    previous_language: Optional[str] = None
    turn_count: int = 0
    entities: MemoryEntities = field(default_factory=MemoryEntities)
    conversation_summary: str = ""
    turns: List[ConversationTurn] = field(default_factory=list)
    # Accumulates tool call results across turns so the LLM never needs to
    # call the same tool twice for information it already retrieved.
    tool_cache: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "active_scenario": self.active_scenario,
            "current_language": self.current_language,
            "previous_language": self.previous_language,
            "turn_count": self.turn_count,
            "entities": self.entities.to_dict(),
            "conversation_summary": self.conversation_summary,
            "turns": [t.to_dict() for t in self.turns],
            "tool_cache": self.tool_cache,
            "created_at": self.created_at,
        }

    def add_turn(self, role: str, text: str, detected_language: str, language_label: str) -> None:
        self.turn_count += 1
        self.turns.append(
            ConversationTurn(
                turn_number=self.turn_count,
                role=role,
                text=text,
                detected_language=detected_language,
                language_label=language_label,
            )
        )

    def get_chat_history(self, max_turns: int = 10) -> List[Dict[str, str]]:
        """Return last N turns formatted for LLM context.

        Always starts with a user turn so the message array sent to the model
        is well-formed (system → user → assistant → …).  A malformed array
        that starts with an assistant turn causes a Vulkan Channel Error in
        llama.cpp when the GPU compute graph cannot be resolved.
        """
        recent = self.turns[-(max_turns * 2):]
        # Drop leading assistant turns to guarantee first role == "user"
        while recent and recent[0].role != "user":
            recent = recent[1:]
        return [{"role": t.role, "content": t.text} for t in recent]
