"""Speech-to-text. Uses faster-whisper when enabled and installed; otherwise unavailable and the
client must send its own transcript (e.g. the browser's speech recognition or typed text)."""

import logging
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

log = logging.getLogger(__name__)


@lru_cache
def _model() -> Any | None:
    if not get_settings().use_faster_whisper:
        return None
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        log.warning("faster-whisper not installed; server-side STT disabled")
        return None
    return WhisperModel("base.en", device="cpu", compute_type="int8")


def available() -> bool:
    return _model() is not None


def transcribe(wav: bytes) -> str | None:
    model = _model()
    if model is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "a.wav"
        path.write_bytes(wav)
        segments, _ = model.transcribe(str(path), vad_filter=True)
        return " ".join(s.text.strip() for s in segments)
