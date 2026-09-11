from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_demo_user
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
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> list[PracticeRecord]:
    return (
        db.query(PracticeRecord)
        .filter(PracticeRecord.user_id == user.id)
        .order_by(PracticeRecord.created_at.desc())
        .all()
    )
