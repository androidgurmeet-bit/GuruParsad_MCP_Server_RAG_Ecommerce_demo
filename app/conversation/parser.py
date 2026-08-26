"""Turn a Whisper transcript payload into the fields a Conversation needs."""

UNKNOWN_LANGUAGE = "unknown"


def message_from_transcript(transcript: dict) -> str:
    """The spoken text as one line.

    `transcript["transcript"]` is already the joined segment text, but a partial
    payload can arrive without it — fall back to re-joining the segments before
    giving up.
    """
    message = str(transcript.get("transcript") or "").strip()
    if message:
        return message

    parts = [
        str(segment.get("text") or "").strip()
        for segment in transcript.get("segments") or []
        if isinstance(segment, dict)
    ]
    return " ".join(part for part in parts if part)


def language_from_transcript(transcript: dict) -> str:
    """Whisper's auto-detected language code, or "unknown" if it reported none."""
    return str(transcript.get("language") or "").strip() or UNKNOWN_LANGUAGE
