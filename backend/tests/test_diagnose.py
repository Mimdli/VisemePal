from types import SimpleNamespace

from app.services.diagnose import diagnose


def test_diagnose_maps_ise_phones_to_target_ipa() -> None:
    lesson = SimpleNamespace(id=1, target_phonemes=["æ"], text="cat", ipa="/kæt/", audio_url=None)
    result = diagnose(
        lesson,
        {
            "provider": "ise",
            "overall_score": 64.5,
            "accuracy": 60,
            "fluency": 70,
            "completeness": 90,
            "error_symbols": ["ae", "k"],
            "phone_errors": [
                {"symbol": "ae", "kind": "substitute"},
                {"symbol": "k", "kind": "low_score"},
            ],
        },
    )
    assert result.provider == "ise"
    assert result.error_phonemes[0].phoneme == "æ"
    assert result.error_phonemes[0].kind == "substitute"
    assert result.error_phonemes[0].viseme
    assert result.error_phonemes[0].viseme.oculus == "aa"
    assert "张大" in result.tips[0]
    assert result.viseme_track
    assert any(frame.focus and frame.phoneme == "æ" for frame in result.viseme_track.frames)
