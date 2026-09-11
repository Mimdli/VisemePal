from pathlib import Path

from app.services.audio import prepare_for_ise, wav_duration_ms
from tests.conftest import write_silence_wav


def test_prepare_wav_to_pcm(tmp_path: Path) -> None:
    wav = write_silence_wav(tmp_path / "in.wav")
    pcm = prepare_for_ise(wav, tmp_path / "out")
    assert pcm.exists()
    assert pcm.stat().st_size > 0
    assert pcm.suffix == ".pcm"


def test_wav_duration_ms(tmp_path: Path) -> None:
    wav = write_silence_wav(tmp_path / "beat.wav", duration_ms=500)
    assert wav_duration_ms(wav) == 500
