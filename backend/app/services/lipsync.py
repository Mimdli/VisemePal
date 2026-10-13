"""英文音素到 Oculus viseme 的口型时间轴。

口型集合对齐 TalkingHead / Meta Lipsync 使用的 MPEG-4 15 viseme：
sil, PP, FF, TH, DD, kk, CH, SS, nn, RR, aa, E, I, O, U。
"""

from __future__ import annotations

import re

from app.schemas import VisemeFrame, VisemePose, VisemeTrack
from app.seed import DEMO_LESSONS
from app.services.phones import to_ipa

# 每个 viseme 的可动画参数：数字人正面口型 + 矢状面舌位共用同一套 pose。
OCULUS_POSES: dict[str, VisemePose] = {
    "sil": VisemePose(),
    "PP": VisemePose(open=0.02, close=1.0, tongue_high=0.2),
    "FF": VisemePose(open=0.12, bite=1.0, teeth=0.35, tongue_high=0.15),
    "TH": VisemePose(open=0.22, teeth=0.45, tongue_front=0.85, tongue_tip=1.0),
    "DD": VisemePose(open=0.18, teeth=0.5, tongue_front=0.75, tongue_high=0.55),
    "kk": VisemePose(open=0.16, tongue_front=0.1, tongue_high=0.95),
    "CH": VisemePose(open=0.2, round=0.45, width=0.25, tongue_front=0.55, tongue_high=0.8),
    "SS": VisemePose(open=0.1, width=0.7, teeth=0.85, tongue_front=0.7, tongue_high=0.55),
    "nn": VisemePose(open=0.18, tongue_front=0.8, tongue_high=0.65),
    "RR": VisemePose(open=0.2, round=0.4, tongue_curl=1.0, tongue_front=0.35, tongue_high=0.45),
    "aa": VisemePose(open=0.92, width=0.55, tongue_front=0.45, tongue_high=0.1),
    "E": VisemePose(open=0.42, width=0.72, tongue_front=0.55, tongue_high=0.4),
    "I": VisemePose(open=0.18, width=1.0, tongue_front=0.8, tongue_high=0.85),
    "O": VisemePose(open=0.52, round=0.82, width=0.2, tongue_front=0.25, tongue_high=0.35),
    "U": VisemePose(open=0.22, round=1.0, pucker=0.85, width=0.05, tongue_front=0.15, tongue_high=0.55),
}

IPA_TO_OCULUS: dict[str, str] = {
    "p": "PP",
    "b": "PP",
    "m": "PP",
    "f": "FF",
    "v": "FF",
    "θ": "TH",
    "ð": "TH",
    "t": "DD",
    "d": "DD",
    "k": "kk",
    "g": "kk",
    "ŋ": "kk",
    "ʃ": "CH",
    "ʒ": "CH",
    "tʃ": "CH",
    "dʒ": "CH",
    "s": "SS",
    "z": "SS",
    "n": "nn",
    "l": "nn",
    "r": "RR",
    "æ": "aa",
    "ɑ": "aa",
    "ɑː": "aa",
    "ʌ": "aa",
    "ə": "E",
    "e": "E",
    "ɛ": "E",
    "ɪ": "I",
    "i": "I",
    "iː": "I",
    "j": "I",
    "ɔ": "O",
    "ɔː": "O",
    "ɒ": "O",
    "oʊ": "O",
    "ʊ": "U",
    "u": "U",
    "uː": "U",
    "w": "U",
    "h": "sil",
    "ɜː": "RR",
}

DIPHTHONGS: dict[str, list[str]] = {
    "aɪ": ["æ", "ɪ"],
    "eɪ": ["e", "ɪ"],
    "oʊ": ["ɔ", "ʊ"],
    "aʊ": ["ɑː", "ʊ"],
    "ɔɪ": ["ɔː", "ɪ"],
}

LONG_MARK = "ː"
IPA_SKIP = set("/\\|.,;·ˈˌ()[]-–—͡ ")


def phones_from_ipa(ipa: str) -> list[str]:
    """把 /kæt/ 这类标音切成音素，供非预置课文生成口型轨。"""
    text = (ipa or "").strip()
    if not text:
        return []
    tokens = sorted(set(IPA_TO_OCULUS) | set(DIPHTHONGS), key=len, reverse=True)
    phones: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in IPA_SKIP or char.isdigit():
            index += 1
            continue
        matched = next((token for token in tokens if text.startswith(token, index)), None)
        if matched:
            phones.append(matched)
            index += len(matched)
        else:
            index += 1
    return phones


def _word_phones() -> dict[str, list[str]]:
    table = {
        "the": ["ð", "ə"],
        "is": ["ɪ", "z"],
        "fat": ["f", "æ", "t"],
        "a": ["ə"],
    }
    for spec in DEMO_LESSONS:
        word = spec["text"].strip().lower().rstrip(".")
        if " " not in word and spec.get("phones"):
            table[word] = list(spec["phones"])
    return table


def phones_for_text(text: str, ipa: str = "") -> list[str]:
    for spec in DEMO_LESSONS:
        if spec["text"] == text:
            return list(spec.get("phones") or [])
    parsed = phones_from_ipa(ipa)
    if parsed:
        return parsed
    words = re.findall(r"[a-z']+", (text or "").lower())
    table = _word_phones()
    if words and all(word in table for word in words):
        phones: list[str] = []
        for word in words:
            phones.extend(table[word])
        return phones
    return []


def oculus_for_phone(phone: str) -> str:
    key = to_ipa(phone)
    if key in IPA_TO_OCULUS:
        return IPA_TO_OCULUS[key]
    if key.endswith(LONG_MARK) and key[:-1] in IPA_TO_OCULUS:
        return IPA_TO_OCULUS[key[:-1]]
    return "sil"


# 教学用 IPA 覆盖：同一 Oculus viseme 里把舌位再拆开，例如 /æ/ 靠前、/ɑ/ 靠后。
IPA_POSES: dict[str, VisemePose] = {
    "æ": VisemePose(open=0.95, width=0.72, tongue_front=0.72, tongue_high=0.08),
    "ɑ": VisemePose(open=0.88, width=0.48, tongue_front=0.22, tongue_high=0.12),
    "ɑː": VisemePose(open=0.9, width=0.5, tongue_front=0.2, tongue_high=0.1),
    "ʌ": VisemePose(open=0.55, width=0.42, tongue_front=0.4, tongue_high=0.28),
    "ə": VisemePose(open=0.32, width=0.4, tongue_front=0.45, tongue_high=0.38),
    "e": VisemePose(open=0.42, width=0.7, tongue_front=0.58, tongue_high=0.42),
    "ɛ": VisemePose(open=0.48, width=0.68, tongue_front=0.55, tongue_high=0.35),
    "ɪ": VisemePose(open=0.22, width=0.78, tongue_front=0.72, tongue_high=0.72),
    "i": VisemePose(open=0.16, width=0.95, tongue_front=0.82, tongue_high=0.88),
    "iː": VisemePose(open=0.14, width=1.0, tongue_front=0.86, tongue_high=0.92),
    "θ": VisemePose(open=0.24, teeth=0.55, tongue_front=0.92, tongue_tip=1.0),
    "ð": VisemePose(open=0.24, teeth=0.5, tongue_front=0.9, tongue_tip=1.0),
    "l": VisemePose(open=0.22, tongue_front=0.88, tongue_high=0.7, tongue_tip=0.55),
    "n": VisemePose(open=0.18, tongue_front=0.82, tongue_high=0.68, tongue_tip=0.4),
    "ŋ": VisemePose(open=0.16, tongue_front=0.06, tongue_high=0.98),
    "k": VisemePose(open=0.14, tongue_front=0.08, tongue_high=0.96),
    "g": VisemePose(open=0.16, tongue_front=0.1, tongue_high=0.94),
    "ʃ": VisemePose(open=0.2, round=0.5, width=0.28, tongue_front=0.58, tongue_high=0.82),
    "s": VisemePose(open=0.1, width=0.72, teeth=0.88, tongue_front=0.74, tongue_high=0.58),
    "r": VisemePose(open=0.2, round=0.42, tongue_curl=1.0, tongue_front=0.32, tongue_high=0.48),
    "w": VisemePose(open=0.18, round=1.0, pucker=0.9, width=0.04, tongue_front=0.18, tongue_high=0.52),
    "uː": VisemePose(open=0.2, round=1.0, pucker=0.92, width=0.04, tongue_front=0.12, tongue_high=0.58),
    "ɜː": VisemePose(open=0.28, round=0.35, tongue_curl=0.7, tongue_front=0.4, tongue_high=0.5),
    "ʊ": VisemePose(open=0.24, round=0.75, pucker=0.55, width=0.12, tongue_front=0.2, tongue_high=0.5),
}


def pose_for_phone(phone: str) -> VisemePose:
    key = to_ipa(phone)
    if key in IPA_POSES:
        return IPA_POSES[key].model_copy()
    if key.endswith(LONG_MARK) and key[:-1] in IPA_POSES:
        return IPA_POSES[key[:-1]].model_copy()
    return OCULUS_POSES[oculus_for_phone(phone)].model_copy()


def expand_phones(phones: list[str]) -> list[str]:
    expanded: list[str] = []
    for phone in phones:
        expanded.extend(DIPHTHONGS.get(phone, [phone]))
    return expanded


def _duration_ms(phone: str, focus: bool = False) -> int:
    if phone in DIPHTHONGS:
        length = 160
    elif phone.endswith(LONG_MARK) or phone in {"iː", "uː", "ɑː", "ɔː", "ɜː"}:
        length = 280
    elif phone in {"æ", "ɑ", "e", "ɛ", "ɪ", "ɔ", "ʊ", "ʌ", "ə"}:
        length = 200
    elif phone in {"ʃ", "s", "θ", "ð", "f", "v", "w"}:
        length = 150
    elif phone in IPA_TO_OCULUS and IPA_TO_OCULUS[phone] in {"PP", "DD", "kk"}:
        length = 110
    elif oculus_for_phone(phone) in {"aa", "E", "I", "O", "U"}:
        length = 180
    else:
        length = 100
    if focus:
        return max(length, 320)
    return length


def _viseme_at(sequence: list[str], index: int) -> str:
    """/h/ 不单独做嘴型，提前用后面的元音，和 Oculus / Azure 的协同发音一致。"""
    phone = sequence[index]
    if phone != "h":
        return oculus_for_phone(phone)
    for nxt in sequence[index + 1 :]:
        viseme = oculus_for_phone(nxt)
        if viseme in {"aa", "E", "I", "O", "U"}:
            return viseme
    return "sil"


def build_track(
    phones: list[str],
    focus: list[str] | None = None,
    duration_ms: int | None = None,
) -> VisemeTrack:
    sequence = expand_phones(phones)
    focus_set = set(focus or [])
    cursor = 80
    frames = [
        VisemeFrame(
            phoneme="",
            viseme="sil",
            start_ms=0,
            duration_ms=80,
            pose=OCULUS_POSES["sil"].model_copy(),
            focus=False,
        )
    ]
    for index, phone in enumerate(sequence):
        length = _duration_ms(phone, focus=phone in focus_set)
        viseme = _viseme_at(sequence, index)
        frames.append(
            VisemeFrame(
                phoneme=phone,
                viseme=viseme,
                start_ms=cursor,
                duration_ms=length,
                pose=pose_for_phone(phone),
                focus=phone in focus_set,
            )
        )
        cursor += length
    frames.append(
        VisemeFrame(
            phoneme="",
            viseme="sil",
            start_ms=cursor,
            duration_ms=120,
            pose=OCULUS_POSES["sil"].model_copy(),
            focus=False,
        )
    )
    natural = cursor + 120
    if duration_ms and duration_ms > 0 and natural > 0:
        scale = duration_ms / natural
        for frame in frames:
            frame.start_ms = int(frame.start_ms * scale)
            frame.duration_ms = max(40, int(frame.duration_ms * scale))
        natural = duration_ms
    return VisemeTrack(duration_ms=natural, frames=frames)
