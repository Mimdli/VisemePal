"""DeepSeek / OpenAI 兼容的 Chat Completions 客户端。"""

from __future__ import annotations

import json
import re

import httpx

from app.config import settings


class LlmError(RuntimeError):
    pass


def chat_json(system_prompt: str, user_prompt: str) -> dict:
    if not settings.llm_api_key:
        raise LlmError("未配置大模型密钥")

    url = _chat_completions_url(settings.llm_base_url)
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "temperature": 0.4,
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    return _extract_json(content)


def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/chat/completions"


def _extract_json(content: str) -> dict:
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LlmError("大模型没有返回可用 JSON") from exc
    if not isinstance(parsed, dict):
        raise LlmError("大模型返回格式不正确")
    return parsed
