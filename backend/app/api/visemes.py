from fastapi import APIRouter, HTTPException

from app.schemas import PhonemeOut, VisemeOut
from app.services.viseme import get_viseme, list_phonemes, list_visemes

router = APIRouter(tags=["resources"])


@router.get("/visemes", response_model=list[VisemeOut])
def list_all_visemes() -> list[VisemeOut]:
    return list_visemes()


@router.get("/visemes/{phoneme}", response_model=VisemeOut)
def get_viseme_detail(phoneme: str) -> VisemeOut:
    viseme = get_viseme(phoneme)
    if viseme is None:
        raise HTTPException(status_code=404, detail="暂无该音素的口型舌位资源")
    return viseme


@router.get("/phonemes", response_model=list[PhonemeOut])
def list_all_phonemes() -> list[PhonemeOut]:
    return list_phonemes()
