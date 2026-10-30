"""TripPlanner intro video (skill aa-uat-video): narration clips, one per sentence, for ONE language.

  python -I intro/tts_intro.py <en|vi>      -> work/TripPlanner-intro-<LANG>/audio/NN_K.wav
                                                + sentences.json (per step: clip offsets and lengths)
                                                + durations.json (per step: total narration seconds)

English: Kokoro-82M (kokoro-onnx), voice af_heart (approved), run with ./venv.
Vietnamese: the SOUTHERN voice wired into ../tts.py (VieNeu-TTS v3 Turbo, "Thục Đoan", via lib/vi_vieneu.py in
venv-vi; see vi_batch below). The old northern Piper vais1000 voice is never used. Offline, $0, no API call.
record_intro.cjs holds each step as long as durations.json says, so a step never cuts its narration.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
UAT = HERE.parent
GAP_S = 0.35  # silence between two sentences of one step


def en_synth():
    from kokoro_onnx import Kokoro

    k = Kokoro(str(UAT / "models" / "kokoro-v1.0.int8.onnx"), str(UAT / "models" / "voices-v1.0.bin"))

    def synth(text):
        s, sr = k.create(text, voice="af_heart", speed=1.0, lang="en-us")
        return np.asarray(s, dtype=np.float32), sr

    return synth


def vi_batch(texts, tmp: Path):
    """Southern Vietnamese voice: the wrapper the voice-choice task wired into ../tts.py
    (lib/vi_vieneu.py in venv-vi: VieNeu-TTS v3 Turbo, preset "Thục Đoan" unless UAT_VI_VOICE is set).
    One model load for all sentences. Returns [(samples, sr)] in order. The northern Piper voice is never used."""
    py, script = UAT / "venv-vi" / "bin" / "python", UAT / "lib" / "vi_vieneu.py"
    if not (py.exists() and script.exists()):
        sys.exit("STOP: the southern Vietnamese voice (venv-vi + lib/vi_vieneu.py) is not installed.")
    voice = os.environ.get("UAT_VI_VOICE", "Thục Đoan")
    tmp.mkdir(parents=True, exist_ok=True)
    caps = [{"n": i, "vi": t} for i, t in enumerate(texts, 1)]
    (tmp / "captions.json").write_text(json.dumps({"captions": caps}, ensure_ascii=False))
    env = {**os.environ, "HF_HOME": str(UAT / "models" / "hf")}
    subprocess.run([str(py), "-I", str(script), str(tmp), voice], check=True, env=env)
    out = []
    for c in caps:
        s, sr = sf.read(tmp / "audio" / "vi" / f"{c['n']:02d}.wav", dtype="float32")
        out.append((s.reshape(-1) if s.ndim == 1 else s.mean(axis=1), sr))
    return out


def main(lang: str) -> None:
    data = json.loads((HERE / "narration.json").read_text())
    work = UAT / "work" / f"{data['id']}-{lang.upper()}"
    out = work / "audio"
    out.mkdir(parents=True, exist_ok=True)
    flat = [t for step in data["steps"] for t in step[lang]]
    if lang == "en":
        synth = en_synth()
        clips = iter([synth(t) for t in flat])
    else:
        clips = iter(vi_batch(flat, work / "vi_batch"))
    sentences, durations = {}, {}
    for n, step in enumerate(data["steps"], 1):
        t, items = 0.0, []
        for k, text in enumerate(step[lang], 1):
            s, sr = next(clips)
            p = out / f"{n:02d}_{k}.wav"
            sf.write(p, s, sr)
            d = len(s) / sr
            items.append({"k": k, "file": p.name, "offset": round(t, 3), "dur": round(d, 3), "text": text})
            t += d + GAP_S
        total = t - GAP_S
        sentences[n] = items
        durations[n] = round(total, 3)
        print(f"step {n:02d} {step['key']}: {total:.1f}s", flush=True)
    (work / "sentences.json").write_text(json.dumps(sentences, ensure_ascii=False, indent=2))
    (work / "durations.json").write_text(json.dumps(durations, indent=2))
    print(f"total narration {sum(durations.values()):.1f}s -> {work}")


if __name__ == "__main__":
    main(sys.argv[1])
