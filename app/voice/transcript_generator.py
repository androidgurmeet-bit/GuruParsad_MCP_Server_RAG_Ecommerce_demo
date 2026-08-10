import json
from pathlib import Path

TRANSCRIPTS_DIR = Path(__file__).resolve().parents[2] / "transcripts"


def save_transcript(call_id: str, data: dict) -> Path:
    """Write transcripts/<call_id>/transcript.json and return its path."""
    folder = TRANSCRIPTS_DIR / call_id
    folder.mkdir(parents=True, exist_ok=True)

    file = folder / "transcript.json"
    with file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return file
