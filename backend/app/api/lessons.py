from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import BACKEND_DIR
from app.db import get_db
from app.models import Lesson
from app.schemas import LessonOut
from app.services.audio import wav_duration_ms
from app.services.lipsync import build_track, phones_for_text

router = APIRouter(prefix="/lessons", tags=["lessons"])


def _audio_duration_ms(audio_url: str | None) -> int | None:
    if not audio_url:
        return None
    name = Path(audio_url.split("?")[0]).name
    return wav_duration_ms(BACKEND_DIR / "static" / "audio" / name)


def to_lesson_out(lesson: Lesson, request: Request) -> LessonOut:
    payload = LessonOut.model_validate(lesson)
    if payload.audio_url and not payload.audio_url.startswith("http"):
        payload.audio_url = str(request.base_url).rstrip("/") + payload.audio_url
    phones = phones_for_text(lesson.text, lesson.ipa)
    payload.phones = phones
    payload.viseme_track = build_track(
        phones,
        focus=lesson.target_phonemes,
        duration_ms=_audio_duration_ms(lesson.audio_url),
    )
    return payload


@router.get("", response_model=list[LessonOut])
def list_lessons(request: Request, db: Session = Depends(get_db)) -> list[LessonOut]:
    lessons = db.query(Lesson).order_by(Lesson.id.asc()).all()
    return [to_lesson_out(lesson, request) for lesson in lessons]


@router.get("/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: int, request: Request, db: Session = Depends(get_db)) -> LessonOut:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return to_lesson_out(lesson, request)
