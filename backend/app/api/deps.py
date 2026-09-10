from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

DEMO_USER_NICKNAME = "小朋友"


def get_demo_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.nickname == DEMO_USER_NICKNAME).first()
    if user is None:
        user = User(nickname=DEMO_USER_NICKNAME)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
