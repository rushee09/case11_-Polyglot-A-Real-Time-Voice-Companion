from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any


# ─── Request schemas ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    text: str
    session_id: str
    scenario_name: Optional[str] = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty_or_huge(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be empty")
        if len(v) > 2_000:
            raise ValueError("text exceeds maximum allowed length (2000 chars)")
        return v


class DetectLanguageRequest(BaseModel):
    text: str


class TranscribeResponse(BaseModel):
    transcript: str
    detected_language: str
    language_label: str
    confidence: Optional[float] = None
    latency_ms: float


# ─── Response schemas ───────────────────────────────────────────────────────

class LatencyBreakdown(BaseModel):
    audio_upload_ms: Optional[float] = None
    asr_ms: Optional[float] = None
    language_detection_ms: Optional[float] = None
    memory_update_ms: Optional[float] = None
    tool_ms: Optional[float] = None
    llm_ms: Optional[float] = None
    tts_start_ms: Optional[float] = None
    total_ms: float


class ChatResponse(BaseModel):
    session_id: str
    turn_number: int
    user_text: str
    detected_language: str
    language_label: str
    assistant_response: str
    response_language: str
    response_language_label: str
    language_switched: bool
    previous_language: Optional[str] = None
    memory_snapshot: Dict[str, Any]
    tool_context: Optional[Dict[str, Any]] = None
    latency: LatencyBreakdown
    lm_studio_available: bool
    fallback_mode: bool = False


class LanguageDetectResponse(BaseModel):
    detected_language: str
    language_label: str
    confidence: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    lm_studio: str
    asr: str
    storage_mode: str
    whisper_model: str
    lm_model: str


class SessionResponse(BaseModel):
    session_id: str
    memory: Dict[str, Any]
    turns: List[Dict[str, Any]]


class SessionLogsResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    language_switch_events: List[Dict[str, Any]]
    latency_logs: List[Dict[str, Any]]


class ScenarioTurn(BaseModel):
    turn_number: int
    language: str
    user_text: str
    translation: Optional[str] = None
    expected_behavior: str


class Scenario(BaseModel):
    name: str
    title: str
    description: str
    turns: List[ScenarioTurn]
