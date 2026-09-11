"""把跟读录音转成讯飞 ISE 需要的 16kHz / 16bit / 单声道 PCM。"""

from __future__ import annotations

import array
import shutil
import struct
import subprocess
import wave
from pathlib import Path

TARGET_RATE = 16000
TARGET_WIDTH = 2
TARGET_CHANNELS = 1


class AudioError(RuntimeError):
    pass


def wav_duration_ms(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        with wave.open(str(path), "rb") as wf:
            rate = wf.getframerate()
            if not rate:
                return None
            return int(wf.getnframes() / rate * 1000)
    except wave.Error:
        return None


def prepare_for_ise(src: Path, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    wav_path = work_dir / f"{src.stem}_16k.wav"
    pcm_path = work_dir / f"{src.stem}_16k.pcm"

    if _is_pcm_wav(src):
        _wav_to_target(src, wav_path)
    else:
        _convert_with_system(src, wav_path)
        _wav_to_target(wav_path, wav_path)

    _extract_pcm(wav_path, pcm_path)
    return pcm_path


def _is_pcm_wav(path: Path) -> bool:
    if path.suffix.lower() != ".wav":
        return False
    try:
        with wave.open(str(path), "rb") as wf:
            return wf.getcomptype() == "NONE"
    except wave.Error:
        return False


def _convert_with_system(src: Path, dest: Path) -> None:
    if shutil.which("ffmpeg"):
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            str(TARGET_RATE),
            "-sample_fmt",
            "s16",
            str(dest),
        ]
    elif shutil.which("afconvert"):
        command = [
            "afconvert",
            "-f",
            "WAVE",
            "-d",
            f"LEI16@{TARGET_RATE}",
            "-c",
            "1",
            str(src),
            str(dest),
        ]
    else:
        raise AudioError("无法转码录音：请安装 ffmpeg，或使用 wav 格式上传")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0 or not dest.exists():
        raise AudioError(result.stderr.strip() or "音频转码失败")


def _wav_to_target(src: Path, dest: Path) -> None:
    with wave.open(str(src), "rb") as wf:
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    samples = _frames_to_mono_s16(frames, channels, width)
    if rate != TARGET_RATE:
        samples = _resample(samples, rate, TARGET_RATE)

    with wave.open(str(dest), "wb") as out:
        out.setnchannels(TARGET_CHANNELS)
        out.setsampwidth(TARGET_WIDTH)
        out.setframerate(TARGET_RATE)
        out.writeframes(samples.tobytes())


def _extract_pcm(wav_path: Path, pcm_path: Path) -> None:
    with wave.open(str(wav_path), "rb") as wf:
        pcm_path.write_bytes(wf.readframes(wf.getnframes()))


def _frames_to_mono_s16(frames: bytes, channels: int, width: int) -> array.array:
    if width == 1:
        samples = array.array("h", [(b - 128) * 256 for b in frames])
    elif width == 2:
        samples = array.array("h")
        samples.frombytes(frames)
    elif width == 4:
        count = len(frames) // 4
        unpacked = struct.unpack("<" + "i" * count, frames)
        samples = array.array("h", [max(-32768, min(32767, value // 65536)) for value in unpacked])
    else:
        raise AudioError(f"不支持的采样宽度：{width}")

    if channels <= 1:
        return samples

    mono = array.array("h")
    for index in range(0, len(samples), channels):
        chunk = samples[index : index + channels]
        if not chunk:
            break
        mono.append(int(sum(chunk) / len(chunk)))
    return mono


def _resample(samples: array.array, from_rate: int, to_rate: int) -> array.array:
    if from_rate == to_rate or not samples:
        return samples
    ratio = to_rate / from_rate
    out_length = max(1, int(len(samples) * ratio))
    output = array.array("h")
    for index in range(out_length):
        position = index / ratio
        left = int(position)
        right = min(left + 1, len(samples) - 1)
        frac = position - left
        value = samples[left] * (1 - frac) + samples[right] * frac
        output.append(int(max(-32768, min(32767, value))))
    return output
