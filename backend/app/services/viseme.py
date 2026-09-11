from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote

from app.schemas import PhonemeOut, VisemeOut
from app.services.lipsync import oculus_for_phone, pose_for_phone
from app.services.phones import to_ipa

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_phoneme_bank() -> list[dict]:
    payload = json.loads((DATA_DIR / "phonemes.json").read_text(encoding="utf-8"))
    return payload["phonemes"]


@lru_cache(maxsize=1)
def load_viseme_map() -> dict[str, dict]:
    return json.loads((DATA_DIR / "visemes.json").read_text(encoding="utf-8"))


def get_viseme(phoneme: str) -> VisemeOut | None:
    key = to_ipa(unquote(phoneme))
    item = load_viseme_map().get(key) or load_viseme_map().get(phoneme)
    oculus = oculus_for_phone(key)
    pose = pose_for_phone(key)
    if item is None:
        if oculus == "sil" and key not in {"h", ""}:
            return None
        return VisemeOut(
            phoneme=key or phoneme,
            mouth_shape=oculus,
            tongue_position="",
            animation_key=f"viseme_{oculus}",
            description="",
            child_tip="",
            oculus=oculus,
            pose=pose,
        )
    return VisemeOut(
        phoneme=key,
        mouth_shape=item["mouth_shape"],
        tongue_position=item["tongue_position"],
        animation_key=item.get("animation_key") or f"viseme_{oculus}",
        description=item.get("description") or "",
        child_tip=item.get("child_tip") or "",
        oculus=oculus,
        pose=pose,
    )


def list_visemes() -> list[VisemeOut]:
    return [item for key in load_viseme_map() if (item := get_viseme(key))]


def list_phonemes() -> list[PhonemeOut]:
    items: list[PhonemeOut] = []
    for row in load_phoneme_bank():
        ipa = row["ipa"]
        items.append(
            PhonemeOut(
                ipa=ipa,
                examples=row.get("examples") or [],
                common_error=row.get("common_error"),
                note=row.get("note") or "",
                viseme=get_viseme(ipa),
            )
        )
    return items
