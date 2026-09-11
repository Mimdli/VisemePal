from __future__ import annotations

import shutil
import subprocess

from sqlalchemy.orm import Session

from app.config import BACKEND_DIR
from app.models import Lesson, User

AUDIO_DIR = BACKEND_DIR / "static" / "audio"

DEMO_LESSONS = [
    {
        "title": "小猫 cat",
        "text": "cat",
        "ipa": "/kæt/",
        "target_phonemes": ["æ"],
        "phones": ["k", "æ", "t"],
        "level": "beginner",
        "tip": "嘴巴张大一点，发出扁扁的 /æ/。",
        "slug": "cat",
    },
    {
        "title": "绵羊 sheep",
        "text": "sheep",
        "ipa": "/ʃiːp/",
        "target_phonemes": ["iː", "ʃ"],
        "phones": ["ʃ", "iː", "p"],
        "level": "beginner",
        "tip": "微笑拉长声音，不要发成短短的 ship。",
        "slug": "sheep",
    },
    {
        "title": "小船 ship",
        "text": "ship",
        "ipa": "/ʃɪp/",
        "target_phonemes": ["ɪ"],
        "phones": ["ʃ", "ɪ", "p"],
        "level": "beginner",
        "tip": "声音短而松，和 sheep 对比着练。",
        "slug": "ship",
    },
    {
        "title": "想一想 think",
        "text": "think",
        "ipa": "/θɪŋk/",
        "target_phonemes": ["θ"],
        "phones": ["θ", "ɪ", "ŋ", "k"],
        "level": "beginner",
        "tip": "舌尖轻轻伸到牙齿中间吹气。",
        "slug": "think",
    },
    {
        "title": "这个 this",
        "text": "this",
        "ipa": "/ðɪs/",
        "target_phonemes": ["ð"],
        "phones": ["ð", "ɪ", "s"],
        "level": "beginner",
        "tip": "舌头位置和 think 一样，但要发出声音。",
        "slug": "this",
    },
    {
        "title": "非常 very",
        "text": "very",
        "ipa": "/ˈveri/",
        "target_phonemes": ["v"],
        "phones": ["v", "e", "r", "i"],
        "level": "beginner",
        "tip": "上牙轻轻咬住下嘴唇，不要发成 we。",
        "slug": "very",
    },
    {
        "title": "我们 we",
        "text": "we",
        "ipa": "/wiː/",
        "target_phonemes": ["w"],
        "phones": ["w", "iː"],
        "level": "beginner",
        "tip": "嘴唇收圆，不要碰到牙齿。",
        "slug": "we",
    },
    {
        "title": "灯光 light",
        "text": "light",
        "ipa": "/laɪt/",
        "target_phonemes": ["l"],
        "phones": ["l", "aɪ", "t"],
        "level": "beginner",
        "tip": "舌尖点一下上牙后面，再松开。",
        "slug": "light",
    },
    {
        "title": "红色 red",
        "text": "red",
        "ipa": "/red/",
        "target_phonemes": ["r"],
        "phones": ["r", "e", "d"],
        "level": "beginner",
        "tip": "舌头向后卷一点，不要碰到牙齿。",
        "slug": "red",
    },
    {
        "title": "短句 The cat is fat.",
        "text": "The cat is fat.",
        "ipa": "/ðə kæt ɪz fæt/",
        "target_phonemes": ["æ", "ð"],
        "phones": ["ð", "ə", "k", "æ", "t", "ɪ", "z", "f", "æ", "t"],
        "level": "beginner",
        "tip": "两个 /æ/ 都要把嘴巴张大。",
        "slug": "the-cat-is-fat",
    },
]


def seed_if_empty(db: Session) -> None:
    if db.query(User).count() == 0:
        db.add(User(nickname="小朋友"))

    existing = {lesson.text: lesson for lesson in db.query(Lesson).all()}
    for spec in DEMO_LESSONS:
        audio_url = _ensure_demo_audio(spec["text"], spec["slug"])
        current = existing.get(spec["text"])
        if current is None:
            db.add(
                Lesson(
                    title=spec["title"],
                    text=spec["text"],
                    ipa=spec["ipa"],
                    audio_url=audio_url,
                    target_phonemes=spec["target_phonemes"],
                    level=spec["level"],
                    tip=spec["tip"],
                )
            )
            continue
        current.title = spec["title"]
        current.ipa = spec["ipa"]
        current.target_phonemes = spec["target_phonemes"]
        current.tip = spec["tip"]
        if audio_url:
            current.audio_url = audio_url
    db.commit()


def _ensure_demo_audio(text: str, slug: str) -> str | None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIO_DIR / f"{slug}.wav"
    if path.exists():
        return f"/static/audio/{slug}.wav"
    if not shutil.which("say"):
        return None
    result = subprocess.run(
        ["say", "-o", str(path), "--data-format=LEI16@16000", text],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and path.exists():
        return f"/static/audio/{slug}.wav"
    return None
