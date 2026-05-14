from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MemoryEntities:
    order_id: Optional[str] = None
    email: Optional[str] = None
    order_status: Optional[str] = None
    hotel_city: Optional[str] = None
    hotel_budget: Optional[float] = None
    hotel_people: Optional[int] = None
    hotel_options: List[Dict[str, Any]] = field(default_factory=list)
    selected_hotel_option: Optional[int] = None
    weather_cities: List[str] = field(default_factory=list)
    food_order: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "email": self.email,
            "order_status": self.order_status,
            "hotel_city": self.hotel_city,
            "hotel_budget": self.hotel_budget,
            "hotel_people": self.hotel_people,
            "hotel_options": self.hotel_options,
            "selected_hotel_option": self.selected_hotel_option,
            "weather_cities": self.weather_cities,
            "food_order": self.food_order,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryEntities":
        return cls(
            order_id=d.get("order_id"),
            email=d.get("email"),
            order_status=d.get("order_status"),
            hotel_city=d.get("hotel_city"),
            hotel_budget=d.get("hotel_budget"),
            hotel_people=d.get("hotel_people"),
            hotel_options=d.get("hotel_options", []),
            selected_hotel_option=d.get("selected_hotel_option"),
            weather_cities=d.get("weather_cities", []),
            food_order=d.get("food_order", {}),
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
        """Return last N turns formatted for LLM context."""
        recent = self.turns[-(max_turns * 2):]
        return [{"role": t.role, "content": t.text} for t in recent]
