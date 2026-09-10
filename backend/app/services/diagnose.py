from app.models import Lesson
from app.schemas import EvaluateResult, PhonemeError
from app.services.viseme import get_viseme, load_phoneme_bank


def diagnose(lesson: Lesson, ise_result: dict) -> EvaluateResult:
    """把评测结果对齐到音素资源库，生成儿童可读纠错提示。"""
    bank = {item["ipa"]: item for item in load_phoneme_bank()}
    errors: list[PhonemeError] = []

    target = lesson.target_phonemes or []
    if target:
        focus = target[0]
        meta = bank.get(focus, {})
        viseme = get_viseme(focus)
        errors.append(
            PhonemeError(
                phoneme=focus,
                expected=focus,
                actual=meta.get("common_error"),
                severity="high",
                tip=viseme.child_tip if viseme else meta.get("note", ""),
            )
        )

    tips = [error.tip for error in errors if error.tip]
    if not tips:
        tips = ["再跟读一次，注意听标准发音的口型变化。"]

    return EvaluateResult(
        lesson_id=lesson.id,
        overall_score=float(ise_result.get("overall_score", 0)),
        accuracy=float(ise_result.get("accuracy", 0)),
        fluency=float(ise_result.get("fluency", 0)),
        completeness=float(ise_result.get("completeness", 0)),
        error_phonemes=errors,
        tips=tips,
    )
