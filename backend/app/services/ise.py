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
                        "plev": "0",
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
                try:
                    scores[dest] = float(element.attrib[attr])
                except ValueError:
                    continue

    syllable_errors: list[dict] = []
    error_symbols: list[str] = []
    for syll in root.iter("syll"):
        serr = int(syll.attrib.get("serr_msg") or 0)
        phones = [phone.attrib.get("content", "") for phone in syll.findall("phone")]
        if serr:
            syllable_errors.append({"content": syll.attrib.get("content", ""), "serr_msg": serr, "phones": phones})
            error_symbols.extend(phones)
        for phone in syll.findall("phone"):
            dp_message = int(phone.attrib.get("dp_message") or 0)
            if dp_message in {16, 32}:
                error_symbols.append(phone.attrib.get("content", ""))

    overall = scores.get("overall_score", scores.get("phone_score", 0))
    return {
        "overall_score": overall,
        "accuracy": scores.get("accuracy", overall),
        "fluency": scores.get("fluency", overall),
        "completeness": scores.get("completeness", 100.0 if overall else 0.0),
        "error_symbols": [symbol for symbol in error_symbols if symbol],
        "syllable_errors": syllable_errors,
    }
