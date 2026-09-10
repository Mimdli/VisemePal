from collections import Counter

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Lesson, PracticeRecord
from app.schemas import RecommendItem, RecommendOut


def build_recommendation(db: Session, user_id: int) -> RecommendOut:
    """根据历史错误分布生成训练计划。未配置大模型时走规则推荐。"""
    records = (
        db.query(PracticeRecord)
        .filter(PracticeRecord.user_id == user_id)
        .order_by(PracticeRecord.created_at.desc())
        .all()
    )
    error_counter: Counter[str] = Counter()
    for record in records:
        error_counter.update(record.error_phonemes or [])

    if settings.llm_api_key:
        # TODO: 将 error_counter 与进度发给大模型，生成句子与复习计划
        pass

    top_errors = [phoneme for phoneme, _ in error_counter.most_common(3)]
    lessons = db.query(Lesson).all()
    items: list[RecommendItem] = []

    for lesson in lessons:
        if top_errors and not set(lesson.target_phonemes) & set(top_errors):
            continue
        focus = [p for p in lesson.target_phonemes if p in top_errors] or lesson.target_phonemes
        items.append(
            RecommendItem(
                lesson_id=lesson.id,
                title=lesson.title,
                text=lesson.text,
                reason=f"重点练习音素 {', '.join(focus)}" if focus else "巩固今日课程",
                focus_phonemes=focus,
            )
        )
        if len(items) >= 3:
            break

    if not items:
        items = [
            RecommendItem(
                lesson_id=lesson.id,
                title=lesson.title,
                text=lesson.text,
                reason="先熟悉基础口型",
                focus_phonemes=lesson.target_phonemes,
            )
            for lesson in lessons[:3]
        ]

    summary = (
        f"最近容易发错：{', '.join(top_errors)}。先把这几个音的口型和舌位练熟。"
        if top_errors
        else "还没有练习记录，先从基础单词开始跟读吧。"
    )
    return RecommendOut(plan_title="今日纠音小计划", summary=summary, items=items)
