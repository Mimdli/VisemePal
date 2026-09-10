from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_demo_user
from app.config import settings
from app.db import get_db
from app.models import Lesson, PracticeRecord, User
from app.schemas import EvaluateResult
from app.services.diagnose import diagnose
from app.services.ise import evaluate_audio

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

    ise_result = evaluate_audio(dest, lesson)
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
