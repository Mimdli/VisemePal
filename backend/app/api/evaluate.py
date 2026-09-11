from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_demo_user
from app.config import settings
from app.db import get_db
from app.models import Lesson, PracticeRecord, User
from app.schemas import EvaluateResult
from app.services.audio import AudioError, prepare_for_ise
from app.services.diagnose import diagnose
from app.services.ise import IseError, evaluate_audio, has_ise_credentials

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
    dest.write_bytes(await audio.read())
    if dest.stat().st_size == 0:
        raise HTTPException(status_code=400, detail="录音是空的，请重新跟读")

    try:
        pcm_path = prepare_for_ise(dest, settings.upload_dir / "pcm")
    except AudioError as exc:
        if has_ise_credentials():
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        pcm_path = dest

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
