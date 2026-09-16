from __future__ import annotations

from pathlib import Path

from app.config import BACKEND_DIR, settings
from app.models import Lesson
from app.schemas import EvaluateResult, PhonemeError
from app.services.audio import wav_duration_ms
from app.services.lipsync import build_track, phones_for_text
from app.services.phones import to_ipa
from app.services.viseme import get_viseme, load_phoneme_bank


def diagnose(lesson: Lesson, ise_result: dict) -> EvaluateResult:
    """把评测结果对齐到音素资源库，并带上纠错口型 / 时间轴。"""
    bank = {item["ipa"]: item for item in load_phoneme_bank()}
    target = list(lesson.target_phonemes or [])
    flagged = _flagged_ipas(ise_result)

    ordered: list[tuple[str, str]] = []
    seen: set[str] = set()
    for ipa in target:
        if ipa in flagged and ipa not in seen:
            ordered.append((ipa, flagged[ipa]))
            seen.add(ipa)
    for ipa, kind in flagged.items():
        if ipa not in seen:
            ordered.append((ipa, kind))
            seen.add(ipa)

    overall = float(ise_result.get("overall_score") or 0)
    if not ordered and target and overall < settings.error_score_threshold:
        ordered = [(target[0], "target")]

    errors: list[PhonemeError] = []
    for ipa, kind in ordered:
        meta = bank.get(ipa, {})
        viseme = get_viseme(ipa)
        errors.append(
            PhonemeError(
                phoneme=ipa,
                expected=ipa,
                actual=meta.get("common_error") or None,
                severity="high" if ipa in target else "medium",
                tip=viseme.child_tip if viseme else meta.get("note", ""),
                kind=kind,
                viseme=viseme,
            )
        )

    tips = [error.tip for error in errors if error.tip]
    if overall >= 90 and not errors:
        tips = ["很棒，口型和舌头都到位了，再读一遍巩固一下。"]
    elif not tips:
        tips = ["再跟读一次，注意听标准发音的口型变化。"]

    phones = phones_for_text(lesson.text, lesson.ipa)
    focus = [error.phoneme for error in errors]
    duration = _lesson_audio_ms(lesson)
    return EvaluateResult(
        lesson_id=lesson.id,
        overall_score=overall,
        accuracy=float(ise_result.get("accuracy") or 0),
        fluency=float(ise_result.get("fluency") or 0),
        completeness=float(ise_result.get("completeness") or 0),
        error_phonemes=errors,
        tips=tips,
        provider=str(ise_result.get("provider") or "stub"),
        viseme_track=build_track(phones, focus=focus, duration_ms=duration) if phones else None,
    )


def _flagged_ipas(ise_result: dict) -> dict[str, str]:
    flagged: dict[str, str] = {}
    for item in ise_result.get("phone_errors") or []:
        ipa = to_ipa(str(item.get("symbol") or ""))
        if ipa and ipa not in flagged:
            flagged[ipa] = str(item.get("kind") or "error")
    for symbol in ise_result.get("error_symbols") or []:
        ipa = to_ipa(symbol)
        if ipa and ipa not in flagged:
            flagged[ipa] = "error"
    return flagged


def _lesson_audio_ms(lesson: Lesson) -> int | None:
    audio_url = lesson.audio_url or ""
    if not audio_url:
        return None
    name = Path(audio_url.split("?")[0]).name
    return wav_duration_ms(BACKEND_DIR / "static" / "audio" / name)
