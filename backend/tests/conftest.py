import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = f"sqlite:///{Path(__file__).resolve().parent / 'test.db'}"
os.environ["ISE_APP_ID"] = ""
os.environ["ISE_API_KEY"] = ""
os.environ["ISE_API_SECRET"] = ""
os.environ["LLM_API_KEY"] = ""

from app.config import settings
from app.main import app


@pytest.fixture(autouse=True)
def disable_external_apis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ise_app_id", "")
    monkeypatch.setattr(settings, "ise_api_key", "")
    monkeypatch.setattr(settings, "ise_api_secret", "")
    monkeypatch.setattr(settings, "llm_api_key", "")


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def write_silence_wav(path: Path, duration_ms: int = 200) -> Path:
    import wave

    frames = int(16000 * duration_ms / 1000)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b"\x00\x00" * frames)
    return path
