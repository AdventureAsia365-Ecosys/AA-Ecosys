"""UAT narration (skill aa-uat-video): one local TTS clip per step caption, before recording.

  python -I tts.py <work/ID>            -> <work/ID>/audio/{en,vi}/NN.wav + durations.json

English: Kokoro-82M (Apache-2.0 weights) through kokoro-onnx (MIT), voice af_heart (female, approved).
Vietnamese: VieNeu-TTS v3 Turbo (Apache-2.0 weights + preset voices, commercial use allowed), Southern
female preset "Thục Đoan" by default; override with env UAT_VI_VOICE (e.g. "Adam" = Southern male).
It runs in the sibling venv venv-vi through lib/vi_vieneu.py (one model load for all steps).
Piper vi_VN-vais1000 (Northern accent) was rejected by the tech lead; never use it.
durations.json maps step number -> the longer of the two clips (seconds); record.cjs holds each step that long.
Runs offline, $0, no API call. Kokoro is freed before VieNeu loads, so only one model is in RAM at a time.
"""
import gc
import json
import os
import subprocess
import sys
from pathlib import Path

import soundfile as sf

HERE = Path(__file__).resolve().parent
MODELS = HERE / "models"
EN_VOICE = "af_heart"
VI_PY = HERE / "venv-vi" / "bin" / "python"
VI_SCRIPT = HERE / "lib" / "vi_vieneu.py"
VI_VOICE = os.environ.get("UAT_VI_VOICE", "Thục Đoan")


def main(work: Path) -> None:
    caps = json.loads((work / "captions.json").read_text())["captions"]
    (work / "audio" / "en").mkdir(parents=True, exist_ok=True)
    (work / "audio" / "vi").mkdir(parents=True, exist_ok=True)

    from kokoro_onnx import Kokoro

    kokoro = Kokoro(str(MODELS / "kokoro-v1.0.int8.onnx"), str(MODELS / "voices-v1.0.bin"))
    durations = {}
    for c in caps:
        n = c["n"]
        samples, sr = kokoro.create(c["en"], voice=EN_VOICE, speed=1.0, lang="en-us")
        sf.write(work / "audio" / "en" / f"{n:02d}.wav", samples, sr)
        durations[n] = len(samples) / sr
    del kokoro
    gc.collect()

    if any(c.get("vi") for c in caps) and VI_PY.exists():
        env = {**os.environ, "HF_HOME": str(MODELS / "hf")}
        subprocess.run([str(VI_PY), "-I", str(VI_SCRIPT), str(work), VI_VOICE], check=True, env=env)
        for c in caps:
            p = work / "audio" / "vi" / f"{c['n']:02d}.wav"
            if c.get("vi") and p.exists():
                info = sf.info(p)
                durations[c["n"]] = max(durations[c["n"]], info.frames / info.samplerate)

    durations = {n: round(d, 3) for n, d in durations.items()}
    for n, d in durations.items():
        print(f"step {n}: {d}s")
    (work / "durations.json").write_text(json.dumps(durations, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
