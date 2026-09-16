from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.api.deps import get_demo_user
from app.config import settings
from app.db import get_db
from app.models import PracticeRecord, User
from app.schemas import ErrorStat, RecordOut, RecordStatsOut

router = APIRouter(prefix="/records", tags=["records"])


@router.get("/stats", response_model=RecordStatsOut)
def record_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> RecordStatsOut:
    records = db.query(PracticeRecord).filter(PracticeRecord.user_id == user.id).all()
    counter: Counter[str] = Counter()
    for record in records:
        counter.update(record.error_phonemes or [])
    average = (
        round(sum(record.overall_score for record in records) / len(records), 1)
        if records
        else 0.0
    )
    return RecordStatsOut(
        practice_count=len(records),
        average_score=average,
        top_errors=[ErrorStat(phoneme=phoneme, count=count) for phoneme, count in counter.most_common(5)],
    )


@router.get("", response_model=list[RecordOut])
def list_records(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> list[RecordOut]:
    records = (
        db.query(PracticeRecord)
        .options(joinedload(PracticeRecord.lesson))
        .filter(PracticeRecord.user_id == user.id)
        .order_by(PracticeRecord.created_at.desc())
        .all()
    )
    base_url = str(request.base_url).rstrip("/")
    return [
        RecordOut(
            id=record.id,
            lesson_id=record.lesson_id,
            lesson_title=record.lesson.title,
            text=record.lesson.text,
            overall_score=record.overall_score,
            accuracy=record.accuracy,
            fluency=record.fluency,
            completeness=record.completeness,
            error_phonemes=record.error_phonemes or [],
            audio_url=f"{base_url}/records/{record.id}/audio"
            if record.audio_path
            else None,
            created_at=record.created_at,
        )
        for record in records
    ]


@router.get("/{record_id}/audio", response_class=FileResponse)
def record_audio(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> FileResponse:
    record = (
        db.query(PracticeRecord)
        .filter(
            PracticeRecord.id == record_id,
            PracticeRecord.user_id == user.id,
        )
        .first()
    )
    if record is None or not record.audio_path:
        raise HTTPException(status_code=404, detail="练习录音不存在")
    path = Path(record.audio_path).resolve()
    upload_root = settings.upload_dir.resolve()
    if upload_root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="练习录音不存在")
    media_type = "audio/wav" if path.suffix.lower() == ".wav" else "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)
