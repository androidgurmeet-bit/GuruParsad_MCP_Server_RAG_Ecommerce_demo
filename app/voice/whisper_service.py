import os

from faster_whisper import WhisperModel

MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")

_model: WhisperModel | None = None


def get_model() -> WhisperModel:
    """Load the Whisper model once, on first use (weights download on first call)."""
    global _model
    if _model is None:
        _model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8",
        )
    return _model


def transcribe(audio_path: str) -> dict:
    segments, info = get_model().transcribe(audio_path)

    text_parts: list[str] = []
    all_segments: list[dict] = []

    # segments is a generator; consuming it is what actually runs the decode.
    for segment in segments:
        text = segment.text.strip()
        text_parts.append(text)
        all_segments.append(
            {
                # faster-whisper has no diarization, so there is no real speaker label.
                "speaker": "unknown",
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text,
            }
        )

    return {
        "language": info.language,
        "duration": round(info.duration, 2),
        "transcript": " ".join(text_parts),
        "segments": all_segments,
    }
