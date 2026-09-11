from __future__ import annotations

from app.config import settings
from app.models import Lesson
from app.schemas import EvaluateResult, PhonemeError
from app.services.phones import to_ipa
from app.services.viseme import get_viseme, load_phoneme_bank


def diagnose(lesson: Lesson, ise_result: dict) -> EvaluateResult:
    """把评测结果对齐到音素资源库，生成儿童可读纠错提示。"""
    bank = {item["ipa"]: item for item in load_phoneme_bank()}
    target = list(lesson.target_phonemes or [])
    ise_ipas = [to_ipa(symbol) for symbol in ise_result.get("error_symbols") or []]
    ise_ipas = [ipa for ipa in ise_ipas if ipa]

    ordered: list[str] = []
    for ipa in target:
        if ipa in ise_ipas and ipa not in ordered:
            ordered.append(ipa)
    for ipa in ise_ipas:
        if ipa not in ordered:
            ordered.append(ipa)

    overall = float(ise_result.get("overall_score") or 0)
    if not ordered and target and overall < settings.error_score_threshold:
        ordered = target[:1]

    errors: list[PhonemeError] = []
    for ipa in ordered:
        meta = bank.get(ipa, {})
        viseme = get_viseme(ipa)
        errors.append(
            PhonemeError(
                phoneme=ipa,
                expected=ipa,
                actual=meta.get("common_error"),
                severity="high" if ipa in target else "medium",
                tip=viseme.child_tip if viseme else meta.get("note", ""),
            )
        )

    tips = [error.tip for error in errors if error.tip]
    if overall >= 90 and not errors:
        tips = ["很棒，口型和舌头都到位了，再读一遍巩固一下。"]
    elif not tips:
        tips = ["再跟读一次，注意听标准发音的口型变化。"]

    return EvaluateResult(
        lesson_id=lesson.id,
        overall_score=overall,
        accuracy=float(ise_result.get("accuracy") or 0),
        fluency=float(ise_result.get("fluency") or 0),
        completeness=float(ise_result.get("completeness") or 0),
        error_phonemes=errors,
        tips=tips,
        provider=str(ise_result.get("provider") or "stub"),
    )
