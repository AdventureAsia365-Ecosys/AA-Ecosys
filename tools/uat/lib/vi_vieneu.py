"""Vietnamese narration with VieNeu-TTS v3 Turbo (skill aa-uat-video): one model load, one WAV per caption.

  venv-vi/bin/python -I lib/vi_vieneu.py <work/ID> [voice]   -> <work/ID>/audio/vi/NN.wav
  voice = a preset name (default "Thục Đoan") or an enrolled clone own-voice/work/voice_w<k>.npz

Runs in its own venv (venv-vi: vieneu SDK, torch-free ONNX Runtime on CPU). Model + preset voices are
Apache-2.0 (https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo, "Usage Rights & Licensing FAQ": presets
licensed for commercial use, speakers consented). Peak RAM ~1.9 GB on this box. Offline after first download.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

DEFAULT_VOICE = "Thục Đoan"  # female, Southern (Nam), storytelling


def main(work: Path, voice: str) -> None:
    from vieneu import Vieneu

    caps = json.loads((work / "captions.json").read_text())["captions"]
    out = work / "audio" / "vi"
    out.mkdir(parents=True, exist_ok=True)
    tts = Vieneu()
    if voice.endswith(".npz"):  # an enrolled own-voice clone from own-voice/clone.py
        z = np.load(voice)
        voice_arg = {"speaker_emb": z["speaker_emb"], "codes": z["codes"]}
    else:
        voice_arg = voice
    sr = getattr(tts, "sample_rate", None) or 48000
    for c in caps:
        if not c.get("vi"):
            continue
        a = np.asarray(tts.infer(c["vi"], voice=voice_arg), dtype=np.float32).reshape(-1)
        p = out / f"{c['n']:02d}.wav"
        sf.write(p, a, sr)
        print(f"vi step {c['n']}: {len(a) / sr:.2f}s ({voice})", flush=True)


if __name__ == "__main__":
    os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parent.parent / "models" / "hf"))
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else DEFAULT_VOICE)
