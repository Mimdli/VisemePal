"""讯飞 ISE 流式评测：签名握手、上传 PCM、解析音素 XML。"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote

import websockets
from websockets.exceptions import WebSocketException

from app.config import settings
from app.models import Lesson
from app.services.phones import to_ipa

ISE_HOST = settings.ise_host
ISE_PATH = settings.ise_path
CHUNK_SIZE = 1280


class IseError(RuntimeError):
    pass


def has_ise_credentials() -> bool:
    return bool(settings.ise_app_id and settings.ise_api_key and settings.ise_api_secret)


async def evaluate_audio(audio_path: Path, lesson: Lesson) -> dict:
    if not has_ise_credentials():
        return _stub_result(lesson, audio_path)

    pcm = audio_path.read_bytes()
    if not pcm:
        raise IseError("录音是空的，请重新跟读")

    category, paper = _paper_for_lesson(lesson)
    try:
        xml_text = await _stream_evaluate(pcm, category, paper)
    except (OSError, WebSocketException, TimeoutError, asyncio.TimeoutError) as exc:
        raise IseError(f"讯飞评测连接失败：{exc}") from exc
    parsed = parse_ise_xml(xml_text)
    parsed["provider"] = "ise"
    parsed["raw_xml"] = xml_text
    return parsed


def _stub_result(lesson: Lesson, audio_path: Path) -> dict:
    return {
        "provider": "stub",
        "overall_score": 72.0,
        "accuracy": 68.0,
        "fluency": 80.0,
        "completeness": 90.0,
        "error_symbols": list(lesson.target_phonemes[:1]),
        "syllable_errors": [],
        "raw": {"audio": str(audio_path), "note": "ISE 未配置，返回占位分数"},
    }


def _paper_for_lesson(lesson: Lesson) -> tuple[str, str]:
    text = (lesson.text or "").strip()
    if any(token in text for token in (" ", ".", "!", "?")):
        return "read_sentence", f"\ufeff[content]\n{text}"
    return "read_word", f"\ufeff[word]\n{text}"


def _auth_url() -> str:
    date = format_datetime(datetime.now(timezone.utc), usegmt=True)
    signature_origin = f"host: {ISE_HOST}\ndate: {date}\nGET {ISE_PATH} HTTP/1.1"
    digest = hmac.new(
        settings.ise_api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature = base64.b64encode(digest).decode("utf-8")
    authorization_origin = (
        f'api_key="{settings.ise_api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
    return (
        f"wss://{ISE_HOST}{ISE_PATH}"
        f"?authorization={quote(authorization, safe='')}"
        f"&date={quote(date, safe='')}"
        f"&host={ISE_HOST}"
    )


async def _stream_evaluate(pcm: bytes, category: str, paper: str) -> str:
    xml_chunks: list[str] = []
    async with websockets.connect(_auth_url(), ping_interval=20, close_timeout=5) as ws:
        await ws.send(
            json.dumps(
                {
                    "common": {"app_id": settings.ise_app_id},
                    "business": {
                        "sub": "ise",
                        "ent": "en_vip",
                        "category": category,
                        "cmd": "ssb",
                        "auf": "audio/L16;rate=16000",
                        "aue": "raw",
                        "tte": "utf-8",
                        "ttp_skip": True,
                        "text": paper,
                        "rst": "entirety",
                        "ise_unite": "1",
                        "plev": "1",
                        "rstcd": "utf8",
                        "extra_ability": "multi_dimension;syll_phone_err_msg",
                    },
                    "data": {"status": 0, "data": ""},
                }
            )
        )

        chunks = [pcm[index : index + CHUNK_SIZE] for index in range(0, len(pcm), CHUNK_SIZE)] or [b""]
        for index, chunk in enumerate(chunks):
            is_last = index == len(chunks) - 1
            await ws.send(
                json.dumps(
                    {
                        "business": {
                            "cmd": "auw",
                            "aus": 4 if is_last else 1 if index == 0 else 2,
                        },
                        "data": {
                            "status": 2 if is_last else 1,
                            "data": base64.b64encode(chunk).decode("utf-8"),
                        },
                    }
                )
            )
            await asyncio.sleep(0.04)

        while True:
            message = json.loads(await asyncio.wait_for(ws.recv(), timeout=20))
            if message.get("code") not in (0, "0", None):
                raise IseError(message.get("message") or f"ISE 错误码 {message.get('code')}")
            payload = (message.get("data") or {}).get("data")
            if payload:
                xml_chunks.append(base64.b64decode(payload).decode("utf-8", errors="ignore"))
            status = (message.get("data") or {}).get("status", message.get("status"))
            if status == 2:
                break

    xml_text = "".join(xml_chunks).strip()
    if not xml_text:
        raise IseError("讯飞没有返回评测结果")
    return xml_text


# 讯飞 ISE dp_message：0 正确，16 漏读，32 增读，64 回读，128 替换。
DP_KIND = {16: "missing", 32: "extra", 64: "repeat", 128: "substitute"}
VOWEL_IPA = {
    "æ", "ɑ", "ɑː", "ʌ", "ə", "e", "ɛ", "ɪ", "i", "iː",
    "ɔ", "ɔː", "ɒ", "oʊ", "ʊ", "u", "uː", "aɪ", "eɪ", "aʊ", "ɔɪ", "ɜː",
}


def parse_ise_xml(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    scores: dict[str, float] = {}
    key_map = {
        "total_score": "overall_score",
        "accuracy_score": "accuracy",
        "fluency_score": "fluency",
        "integrity_score": "completeness",
        "phone_score": "phone_score",
    }
    for element in root.iter():
        for attr, dest in key_map.items():
            if attr in element.attrib and dest not in scores:
                value = _to_float(element.attrib[attr])
                if value is not None:
                    scores[dest] = value

    syllable_errors: list[dict] = []
    phone_errors: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for syll in root.iter("syll"):
        serr = int(syll.attrib.get("serr_msg") or 0)
        phones_el = list(syll.findall("phone"))
        contents = [node.attrib.get("content", "") for node in phones_el]
        flagged = [_phone_error(node) for node in phones_el]
        flagged = [item for item in flagged if item]
        if not flagged and serr:
            flagged = _syllable_fallback(phones_el)
        if serr or flagged:
            syllable_errors.append(
                {"content": syll.attrib.get("content", ""), "serr_msg": serr, "phones": contents}
            )
        for item in flagged:
            key = (item["symbol"], item["kind"])
            if key in seen:
                continue
            seen.add(key)
            phone_errors.append(item)

    error_symbols = [item["symbol"] for item in phone_errors if item.get("symbol")]
    overall = scores.get("overall_score", scores.get("phone_score", 0))
    return {
        "overall_score": overall,
        "accuracy": scores.get("accuracy", overall),
        "fluency": scores.get("fluency", overall),
        "completeness": scores.get("completeness", 100.0 if overall else 0.0),
        "error_symbols": error_symbols,
        "phone_errors": phone_errors,
        "syllable_errors": syllable_errors,
    }


def _to_float(raw: str | None) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _phone_error(node: ET.Element) -> dict | None:
    symbol = (node.attrib.get("content") or "").strip()
    if not symbol:
        return None
    dp_message = int(node.attrib.get("dp_message") or 0)
    score = _to_float(node.attrib.get("score") or node.attrib.get("total_score"))
    kind = DP_KIND.get(dp_message)
    low = score is not None and score < settings.error_score_threshold
    if not kind and not low:
        return None
    if not kind:
        kind = "low_score"
    return {"symbol": symbol, "kind": kind, "score": score, "dp_message": dp_message}


def _syllable_fallback(phones_el: list[ET.Element]) -> list[dict]:
    """音节标了错、但没有音素级标记时，只点元音，避免把整音节辅音都算错。"""
    ranked: list[ET.Element] = []
    others: list[ET.Element] = []
    for node in phones_el:
        symbol = (node.attrib.get("content") or "").strip()
        if not symbol:
            continue
        if to_ipa(symbol) in VOWEL_IPA:
            ranked.append(node)
        else:
            others.append(node)
    chosen = ranked[:1] or others[:1]
    errors: list[dict] = []
    for node in chosen:
        errors.append(
            {
                "symbol": node.attrib.get("content", ""),
                "kind": "syllable",
                "score": _to_float(node.attrib.get("score") or node.attrib.get("total_score")),
                "dp_message": int(node.attrib.get("dp_message") or 0),
            }
        )
    return errors
