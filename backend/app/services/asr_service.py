import os
import tempfile
from typing import Optional, Tuple

_whisper_model = None
_whisper_available = False


def _load_model():
    global _whisper_model, _whisper_available
    if _whisper_model is not None:
        return
    try:
        from faster_whisper import WhisperModel
        from app.config import settings
        model_size = settings.whisper_model
        _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        _whisper_available = True
    except ImportError:
        _whisper_available = False
    except Exception as e:
        print(f"[ASR] Failed to load Whisper model: {e}")
        _whisper_available = False


def is_asr_available() -> bool:
    _load_model()
    return _whisper_available


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> Tuple[str, str, Optional[float]]:
    """
    Transcribe audio bytes.
    Returns (transcript, detected_language, confidence)
    Raises RuntimeError if ASR is unavailable.
    """
    _load_model()
    if not _whisper_available or _whisper_model is None:
        raise RuntimeError(
            "faster-whisper is not installed. "
            "Run: pip install faster-whisper\n"
            "Text-mode is still available."
        )

    suffix = os.path.splitext(filename)[-1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = _whisper_model.transcribe(tmp_path, beam_size=5)
        transcript = " ".join(seg.text for seg in segments).strip()
        language = info.language or "en"
        # Map faster-whisper lang codes
        lang_map = {"en": "en", "hi": "hi", "es": "es"}
        language = lang_map.get(language, language)
        confidence = float(info.language_probability) if hasattr(info, "language_probability") else None
        return transcript, language, confidence
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
