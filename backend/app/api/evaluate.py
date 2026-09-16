from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_demo_user
from app.config import settings
from app.db import get_db
from app.models import Lesson, PracticeRecord, User
from app.schemas import EvaluateResult
from app.services.audio import (
    AudioError,
    cleanup_old_uploads,
    prepare_for_ise,
    validate_pcm,
)
from app.services.diagnose import diagnose
from app.services.ise import IseError, evaluate_audio

router = APIRouter(prefix="/evaluate", tags=["evaluate"])


@router.post("", response_model=EvaluateResult)
async def evaluate_pronunciation(
    lesson_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> EvaluateResult:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="课程不存在")

    suffix = Path(audio.filename or "record.wav").suffix or ".wav"
    filename = f"{uuid4().hex}{suffix}"
    dest = settings.upload_dir / filename
    cleanup_old_uploads(settings.upload_dir, settings.upload_retention_days)
    content = await audio.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"录音不能超过 {settings.max_upload_bytes // (1024 * 1024)} MB",
        )
    if not content:
        raise HTTPException(status_code=400, detail="录音是空的，请重新跟读")
    dest.write_bytes(content)

    try:
        pcm_path = prepare_for_ise(dest, settings.upload_dir / "pcm")
        validate_pcm(
            pcm_path,
            min_duration_ms=settings.min_audio_duration_ms,
            min_rms=settings.min_audio_rms,
        )
    except AudioError as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        ise_result = await evaluate_audio(pcm_path, lesson)
    except IseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    result = diagnose(lesson, ise_result)
    record = PracticeRecord(
        user_id=user.id,
        lesson_id=lesson.id,
        overall_score=result.overall_score,
        accuracy=result.accuracy,
        fluency=result.fluency,
        completeness=result.completeness,
        error_phonemes=[item.phoneme for item in result.error_phonemes],
        audio_path=str(dest),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    result.record_id = record.id
    return result
