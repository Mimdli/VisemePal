import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = f"sqlite:///{Path(__file__).resolve().parent / 'test.db'}"

from app.main import app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_lessons(client: TestClient) -> None:
    response = client.get("/lessons")
    assert response.status_code == 200
    lessons = response.json()
    assert len(lessons) >= 1
    assert "text" in lessons[0]


def test_viseme_resource(client: TestClient) -> None:
    response = client.get("/visemes/æ")
    assert response.status_code == 200
    body = response.json()
    assert body["phoneme"] == "æ"
    assert body["child_tip"]


def test_evaluate_and_recommend(client: TestClient, tmp_path: Path) -> None:
    audio = tmp_path / "demo.wav"
    audio.write_bytes(b"RIFF0000WAVEfmt ")
    files = {"audio": ("demo.wav", audio.read_bytes(), "audio/wav")}
    response = client.post("/evaluate", data={"lesson_id": 1}, files=files)
    assert response.status_code == 200
    result = response.json()
    assert result["lesson_id"] == 1
    assert result["record_id"]

    records = client.get("/records")
    assert records.status_code == 200
    assert len(records.json()) >= 1

    recommend = client.get("/recommend")
    assert recommend.status_code == 200
    assert recommend.json()["items"]
