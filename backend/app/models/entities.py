from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nickname: Mapped[str] = mapped_column(String(64), default="小朋友")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    records: Mapped[list["PracticeRecord"]] = relationship(back_populates="user")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(String(256))
    ipa: Mapped[str] = mapped_column(String(128), default="")
    audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    target_phonemes: Mapped[list[str]] = mapped_column(JSON, default=list)
    level: Mapped[str] = mapped_column(String(32), default="beginner")
    tip: Mapped[str] = mapped_column(Text, default="")

    records: Mapped[list["PracticeRecord"]] = relationship(back_populates="lesson")


class PracticeRecord(Base):
    __tablename__ = "practice_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0)
    fluency: Mapped[float] = mapped_column(Float, default=0)
    completeness: Mapped[float] = mapped_column(Float, default=0)
    error_phonemes: Mapped[list[str]] = mapped_column(JSON, default=list)
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="records")
    lesson: Mapped[Lesson] = relationship(back_populates="records")
