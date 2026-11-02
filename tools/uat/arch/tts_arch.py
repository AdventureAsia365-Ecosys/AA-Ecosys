"""Narration for the architecture videos (AA-1021): one local Kokoro clip per sentence, voice per sentence, loudnorm.

  tts_arch.synth(items, cache_dir) -> {sentence_id: seconds}    items: [(sentence_id, text, voice)]

Kokoro-82M (Apache-2.0 weights) through kokoro-onnx (MIT), voices af_heart (F) and am_michael (M), English only,
speed 1.0. Each clip is normalised with ffmpeg loudnorm in two passes (measure, then linear gain) to -16 LUFS,
true peak -1.5 dB, so the two voices sit at the same loudness. Clips are cached by a hash of voice + text, so a
re-run re-synthesises only the sentences that changed. Runs offline in tools/uat/venv, $0; one model in RAM.
"""
from __future__ import annotations

import gc
import hashlib
import json
import re
import subprocess
from pathlib import Path

UAT = Path(__file__).resolve().parents[1]
MODELS = UAT / "models"
LUFS, TP, LRA = -16.0, -1.5, 11.0


def clip_name(text: str, voice: str) -> str:
    return hashlib.sha256(f"{voice}\n{text}".encode("utf-8")).hexdigest()[:20]


def loudnorm(src: Path, dst: Path) -> None:
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af",
                            f"loudnorm=I={LUFS}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    m = json.loads(re.findall(r"\{[^{}]*\}", probe)[-1])
    af = (f"loudnorm=I={LUFS}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-af", af, "-ar", "24000",
                    "-ac", "1", str(dst)], check=True)


def duration(path: Path) -> float:
    import soundfile as sf

    info = sf.info(str(path))
    return info.frames / info.samplerate


def synth(items: list[tuple[str, str, str]], cache: Path) -> dict[str, dict]:
    """Clips for every (id, text, voice); returns {id: {"wav": path, "dur": seconds}}."""
    import soundfile as sf

    cache.mkdir(parents=True, exist_ok=True)
    todo = [(i, t, v) for i, t, v in items if not (cache / f"{clip_name(t, v)}.wav").exists()]
    if todo:
        from kokoro_onnx import Kokoro

        kokoro = Kokoro(str(MODELS / "kokoro-v1.0.int8.onnx"), str(MODELS / "voices-v1.0.bin"))
        for sid, text, voice in todo:
            samples, sr = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
            raw = cache / f"{clip_name(text, voice)}.raw.wav"
            sf.write(str(raw), samples, sr)
            loudnorm(raw, cache / f"{clip_name(text, voice)}.wav")
            raw.unlink()
            print(f"tts {sid} {voice}: {len(samples) / sr:.1f}s", flush=True)
        del kokoro
        gc.collect()
    out = {}
    for sid, text, voice in items:
        p = cache / f"{clip_name(text, voice)}.wav"
        out[sid] = {"wav": str(p), "dur": round(duration(p), 3)}
    return out
