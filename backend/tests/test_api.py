from pathlib import Path

from tests.conftest import write_silence_wav


def test_dev_console(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "开发控制台" in response.text
    assert "/static/web/app.js" in response.text
    assert "talkinghead" in response.text


def test_avatar_id_rejected(client) -> None:
    assert client.get("/avatars/not-an-id.glb").status_code == 400
    bad = client.get("/avatars/fetch", params={"src": "https://example.com/x.glb"})
    assert bad.status_code == 400


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_lessons(client) -> None:
    response = client.get("/lessons")
    assert response.status_code == 200
    lessons = response.json()
    assert len(lessons) >= 5
    assert "text" in lessons[0]
    assert lessons[0]["phones"]
    assert lessons[0]["viseme_track"]["frames"]


def test_viseme_resource(client) -> None:
    response = client.get("/visemes/æ")
    assert response.status_code == 200
    body = response.json()
    assert body["phoneme"] == "æ"
    assert body["child_tip"]
    assert body["oculus"] == "aa"
    assert body["pose"]["open"] > 0.7
    assert body["pose"]["tongue_front"] > 0.6


def test_viseme_arpabet_alias(client) -> None:
    response = client.get("/visemes/ae")
    assert response.status_code == 200
    assert response.json()["phoneme"] == "æ"


def test_phoneme_bank(client) -> None:
    response = client.get("/phonemes")
    assert response.status_code == 200
    ipas = {item["ipa"] for item in response.json()}
    assert {"æ", "θ", "ð", "ʃ"} <= ipas


def test_evaluate_and_recommend(client, tmp_path: Path) -> None:
    audio = write_silence_wav(tmp_path / "demo.wav")
    files = {"audio": ("demo.wav", audio.read_bytes(), "audio/wav")}
    response = client.post("/evaluate", data={"lesson_id": 1}, files=files)
    assert response.status_code == 200
    result = response.json()
    assert result["lesson_id"] == 1
    assert result["record_id"]
    assert result["provider"] == "stub"
    assert result["error_phonemes"]

    records = client.get("/records")
    assert records.status_code == 200
    assert len(records.json()) >= 1

    stats = client.get("/records/stats")
    assert stats.status_code == 200
    assert stats.json()["practice_count"] >= 1

    recommend = client.get("/recommend")
    assert recommend.status_code == 200
    body = recommend.json()
    assert body["items"]
    assert body["source"] == "rules"
