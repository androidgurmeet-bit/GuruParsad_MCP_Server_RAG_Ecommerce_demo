from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    speaker: str
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    language: str
    duration: float
    transcript: str
    segments: list[TranscriptSegment]
