from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.schemas import VisemeOut

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_phoneme_bank() -> list[dict]:
    payload = json.loads((DATA_DIR / "phonemes.json").read_text(encoding="utf-8"))
    return payload["phonemes"]


@lru_cache(maxsize=1)
def load_viseme_map() -> dict[str, dict]:
    return json.loads((DATA_DIR / "visemes.json").read_text(encoding="utf-8"))


def get_viseme(phoneme: str) -> VisemeOut | None:
    item = load_viseme_map().get(phoneme)
    if item is None:
        return None
    return VisemeOut(phoneme=phoneme, **item)


def list_visemes() -> list[VisemeOut]:
    return [VisemeOut(phoneme=key, **value) for key, value in load_viseme_map().items()]
