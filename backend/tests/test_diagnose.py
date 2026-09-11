from types import SimpleNamespace

from app.services.diagnose import diagnose


def test_diagnose_maps_ise_phones_to_target_ipa() -> None:
    lesson = SimpleNamespace(id=1, target_phonemes=["æ"])
    result = diagnose(
        lesson,
        {
            "provider": "ise",
            "overall_score": 64.5,
            "accuracy": 60,
            "fluency": 70,
            "completeness": 90,
            "error_symbols": ["ae", "k"],
        },
    )
    assert result.provider == "ise"
    assert result.error_phonemes[0].phoneme == "æ"
    assert "张大" in result.tips[0]
