from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_demo_user
from app.db import get_db
from app.models import User
from app.schemas import RecommendOut
from app.services.recommend import build_recommendation

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("", response_model=RecommendOut)
def get_recommendation(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> RecommendOut:
    result = build_recommendation(db, user.id)
    base_url = str(request.base_url).rstrip("/")
    for item in result.items:
        if item.audio_url and not item.audio_url.startswith("http"):
            item.audio_url = base_url + item.audio_url
    return result
