"""讯飞 ISE 发音评测适配层。未配置密钥时返回占位结果。"""

from pathlib import Path

from app.config import settings
from app.models import Lesson


def evaluate_audio(audio_path: Path, lesson: Lesson) -> dict:
    """调用讯飞 ISE，返回总分与音素序列。

    当前为骨架实现：配置齐全后在此接入真实评测。
    """
    if not (settings.ise_app_id and settings.ise_api_key and settings.ise_api_secret):
        return {
            "provider": "stub",
            "overall_score": 72.0,
            "accuracy": 68.0,
            "fluency": 80.0,
            "completeness": 90.0,
            "phonemes": list(lesson.target_phonemes),
            "raw": {"audio": str(audio_path), "note": "ISE 未配置，返回占位分数"},
        }

    # TODO: 接入讯飞 ISE WebAPI（录音转码、签名、解析音素结果）
    raise NotImplementedError("讯飞 ISE 正式接入待实现")
