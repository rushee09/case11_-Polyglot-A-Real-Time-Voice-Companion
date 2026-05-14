import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class LatencyTracker:
    _start: float = field(default_factory=time.perf_counter)
    _checkpoints: Dict[str, float] = field(default_factory=dict)
    audio_upload_ms: Optional[float] = None
    asr_ms: Optional[float] = None
    language_detection_ms: Optional[float] = None
    memory_update_ms: Optional[float] = None
    tool_ms: Optional[float] = None
    llm_ms: Optional[float] = None
    tts_start_ms: Optional[float] = None

    def checkpoint(self, name: str) -> None:
        self._checkpoints[name] = (time.perf_counter() - self._start) * 1000

    def mark(self, field_name: str, elapsed_ms: float) -> None:
        setattr(self, field_name, round(elapsed_ms, 1))

    @property
    def total_ms(self) -> float:
        return round((time.perf_counter() - self._start) * 1000, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audio_upload_ms": self.audio_upload_ms,
            "asr_ms": self.asr_ms,
            "language_detection_ms": self.language_detection_ms,
            "memory_update_ms": self.memory_update_ms,
            "tool_ms": self.tool_ms,
            "llm_ms": self.llm_ms,
            "tts_start_ms": self.tts_start_ms,
            "total_ms": self.total_ms,
        }


class TimedBlock:
    """Context manager to time a block and assign to tracker field."""
    def __init__(self, tracker: LatencyTracker, field_name: str):
        self._tracker = tracker
        self._field_name = field_name
        self._start: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        elapsed = (time.perf_counter() - self._start) * 1000
        self._tracker.mark(self._field_name, elapsed)
