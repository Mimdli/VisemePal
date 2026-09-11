from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthOut(BaseModel):
    status: str = "ok"
    name: str
    ise_ready: bool = False
    llm_ready: bool = False


class VisemePose(BaseModel):
    open: float = 0.08
    width: float = 0.35
    round: float = 0.0
    pucker: float = 0.0
    close: float = 0.0
    bite: float = 0.0
    teeth: float = 0.15
    tongue_front: float = 0.35
    tongue_high: float = 0.35
    tongue_tip: float = 0.0
    tongue_curl: float = 0.0


class VisemeFrame(BaseModel):
    phoneme: str
    viseme: str
    start_ms: int
    duration_ms: int
    pose: VisemePose
    focus: bool = False


class VisemeTrack(BaseModel):
    duration_ms: int
    frames: list[VisemeFrame] = Field(default_factory=list)


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    text: str
    ipa: str
    audio_url: str | None = None
    target_phonemes: list[str] = Field(default_factory=list)
    level: str
    tip: str = ""
    phones: list[str] = Field(default_factory=list)
    viseme_track: VisemeTrack | None = None


class PhonemeError(BaseModel):
    phoneme: str
    expected: str
    actual: str | None = None
    severity: str = "medium"
    tip: str = ""


class EvaluateResult(BaseModel):
    lesson_id: int
    overall_score: float
    accuracy: float
    fluency: float
    completeness: float
    error_phonemes: list[PhonemeError] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
    record_id: int | None = None
    provider: str = "stub"


class VisemeOut(BaseModel):
    phoneme: str
    mouth_shape: str
    tongue_position: str
    animation_key: str
    description: str
    child_tip: str
    oculus: str = "sil"
    pose: VisemePose = Field(default_factory=VisemePose)


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    overall_score: float
    error_phonemes: list[str] = Field(default_factory=list)
    created_at: datetime


class RecommendItem(BaseModel):
    lesson_id: int | None = None
    title: str
    text: str
    reason: str
    focus_phonemes: list[str] = Field(default_factory=list)


class RecommendOut(BaseModel):
    plan_title: str
    summary: str
    items: list[RecommendItem] = Field(default_factory=list)
    source: str = "rules"


class PhonemeOut(BaseModel):
    ipa: str
    examples: list[str] = Field(default_factory=list)
    common_error: str | None = None
    note: str = ""
    viseme: VisemeOut | None = None


class ErrorStat(BaseModel):
    phoneme: str
    count: int


class RecordStatsOut(BaseModel):
    practice_count: int
    average_score: float = 0
    top_errors: list[ErrorStat] = Field(default_factory=list)
