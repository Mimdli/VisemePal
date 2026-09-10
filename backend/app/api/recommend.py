from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_demo_user
from app.db import get_db
from app.models import User
from app.schemas import RecommendOut
from app.services.recommend import build_recommendation

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("", response_model=RecommendOut)
def get_recommendation(
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> RecommendOut:
    return build_recommendation(db, user.id)
