from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_demo_user
from app.db import get_db
from app.models import PracticeRecord, User
from app.schemas import RecordOut

router = APIRouter(prefix="/records", tags=["records"])


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
