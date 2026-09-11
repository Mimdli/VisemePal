from __future__ import annotations

from collections import Counter

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Lesson, PracticeRecord
from app.schemas import RecommendItem, RecommendOut
from app.services.llm import LlmError, chat_json


SYSTEM_PROMPT = """你是面向中国儿童的英语发音教练。根据错误音素和学习记录，生成短小、鼓励性的纠音计划。
只返回 JSON，不要 Markdown。结构：
{
  "plan_title": "字符串",
  "summary": "给小朋友看的一两句话",
  "items": [
    {
      "lesson_id": 数字或 null,
      "title": "课程标题",
      "text": "要跟读的单词或短句",
      "reason": "为什么练这个",
      "focus_phonemes": ["æ"]
    }
  ]
}
items 最多 3 条。text 要简短，适合儿童跟读。优先使用提供的现有课程。"""


def build_recommendation(db: Session, user_id: int) -> RecommendOut:
    records = (
        db.query(PracticeRecord)
        .filter(PracticeRecord.user_id == user_id)
        .order_by(PracticeRecord.created_at.desc())
        .all()
    )
    lessons = db.query(Lesson).order_by(Lesson.id.asc()).all()
    error_counter: Counter[str] = Counter()
    for record in records:
        error_counter.update(record.error_phonemes or [])

    if settings.llm_api_key:
        try:
            return _from_llm(lessons, records, error_counter)
        except (LlmError, httpx.HTTPError, KeyError, TypeError, ValueError):
            pass
    return _from_rules(lessons, error_counter)


def _from_llm(
    lessons: list[Lesson],
    records: list[PracticeRecord],
    error_counter: Counter[str],
) -> RecommendOut:
    lesson_brief = [
        {
            "id": lesson.id,
            "title": lesson.title,
            "text": lesson.text,
            "ipa": lesson.ipa,
            "target_phonemes": lesson.target_phonemes,
        }
        for lesson in lessons
    ]
    history = [
        {
            "lesson_id": record.lesson_id,
            "score": record.overall_score,
            "error_phonemes": record.error_phonemes,
        }
        for record in records[:8]
    ]
    payload = chat_json(
        SYSTEM_PROMPT,
        (
            f"错误音素统计：{dict(error_counter)}\n"
            f"现有课程：{lesson_brief}\n"
            f"最近练习：{history}"
        ),
    )
    lesson_map = {lesson.id: lesson for lesson in lessons}
    items: list[RecommendItem] = []
    for raw in payload.get("items") or []:
        lesson_id = raw.get("lesson_id")
        lesson = lesson_map.get(lesson_id) if isinstance(lesson_id, int) else None
        items.append(
            RecommendItem(
                lesson_id=lesson.id if lesson else lesson_id,
                title=raw.get("title") or (lesson.title if lesson else "纠音练习"),
                text=raw.get("text") or (lesson.text if lesson else ""),
                reason=raw.get("reason") or "巩固易错音",
                focus_phonemes=list(raw.get("focus_phonemes") or (lesson.target_phonemes if lesson else [])),
            )
        )
        if len(items) >= 3:
            break
    if not items:
        raise LlmError("大模型没有给出练习项")
    return RecommendOut(
        plan_title=payload.get("plan_title") or "今日纠音小计划",
        summary=payload.get("summary") or "先把最容易发错的音练熟。",
        items=items,
        source="deepseek",
    )


def _from_rules(lessons: list[Lesson], error_counter: Counter[str]) -> RecommendOut:
    top_errors = [phoneme for phoneme, _ in error_counter.most_common(3)]
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
    return RecommendOut(plan_title="今日纠音小计划", summary=summary, items=items, source="rules")
