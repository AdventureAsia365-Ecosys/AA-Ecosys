"""Own-voice cloning (skill aa-uat-video): clone a consenting speaker with VieNeu-TTS v3 Turbo, locally on CPU.

  tools/uat/venv-vi/bin/python -I tools/uat/own-voice/clone.py [<recording>]   (default: newest file in own-voice/input/)

1. ffmpeg -> mono 44.1 kHz WAV, high-pass + loudness-normalised (work/ref_full.wav).
2. Split on pauses; build up to 3 candidate reference windows of 5-8 s (VieNeu uses at most 8 s).
3. Process A enrolls each window (speaker embedding + reference codes -> work/voice_w<k>.npz) and exits;
   process B synthesizes the same 4 sample caption lines (SAMPLE_LINES) per window -> out/clone_w<k>.wav + .mp3.
   Two processes so the encoder/denoiser and the generator are never in RAM together.
Use a chosen window: UAT_VI_VOICE=$PWD/tools/uat/own-voice/work/voice_w<k>.npz bash tools/uat/run.sh <scenario>.
input/, work/ and out/ are gitignored: a voice recording never goes into git.
Model + code Apache-2.0 (https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo). Offline after first
download, $0. Only ever clone a recording of a person who gave consent (the model card's own rule).
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
UAT = HERE.parent
os.environ.setdefault("HF_HOME", str(UAT / "models" / "hf"))
SR = 44100
DENOISE = os.environ.get("UAT_CLONE_DENOISE", "1") == "1"  # 0 = clip already clean


SAMPLE_LINES = [  # the first 4 Vietnamese captions of scenarios/tripplanner/tp-pub-01.cjs
    "Khách du lịch mở trang lập kế hoạch chuyến đi của Adventure Asia. Không cần tài khoản để xem.",
    "Trang chủ hiển thị các tour thật từ danh mục, mỗi tour có quốc gia và số ngày.",
    "Phía dưới, mỗi điểm đến cho biết có bao nhiêu tour và độ dài các tour.",
    "Khách chọn Bhutan và mở trang điểm đến của Bhutan.",
]


def windows(wav: np.ndarray, sr: int, n: int = 3):
    import librosa
    iv = librosa.effects.split(wav, top_db=35, frame_length=2048, hop_length=512)
    out, i = [], 0
    while i < len(iv) and len(out) < n:
        s, e = iv[i]
        j = i
        while j + 1 < len(iv) and (iv[j + 1][1] - s) / sr <= 8.0:
            j += 1
            e = iv[j][1]
        if (e - s) / sr >= 5.0:
            out.append((max(0, s - int(0.1 * sr)), min(len(wav), e + int(0.1 * sr))))
        i = j + 1
    return out


def enroll(n_win: int) -> None:
    from vieneu import Vieneu
    tts = Vieneu(precision="int8")  # the generator is unused here; int8 keeps this process small
    for k in range(1, n_win + 1):
        emb, codes = tts.encode_reference(str(HERE / "work" / f"ref_w{k}.wav"), denoise=DENOISE)
        np.savez(HERE / "work" / f"voice_w{k}.npz", speaker_emb=np.asarray(emb, dtype=np.float32),
                 codes=np.asarray(codes, dtype=np.int64))


def synth(n_win: int) -> None:
    from vieneu import Vieneu
    tts = Vieneu()
    for k in range(1, n_win + 1):
        z = np.load(HERE / "work" / f"voice_w{k}.npz")
        voice = {"speaker_emb": z["speaker_emb"], "codes": z["codes"]}
        t0, parts = time.time(), []
        for ln in SAMPLE_LINES:
            a = np.asarray(tts.infer(ln, voice=voice), dtype=np.float32).reshape(-1)
            parts += [a, np.zeros(int(0.5 * tts.sample_rate), dtype=np.float32)]
        audio = np.concatenate(parts)
        p = HERE / "out" / f"clone_w{k}.wav"
        sf.write(p, audio, tts.sample_rate)
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(p), "-b:a", "128k",
                        str(p.with_suffix(".mp3"))], check=True)
        print(f"w{k}: {len(audio) / tts.sample_rate:.1f}s audio in {time.time() - t0:.1f}s "
              f"-> {p.with_suffix('.mp3')}", flush=True)


def main(src: Path) -> None:
    work = HERE / "work"
    work.mkdir(exist_ok=True)
    (HERE / "out").mkdir(exist_ok=True)
    full = work / "ref_full.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar",
                    str(SR), "-af", "highpass=f=70,loudnorm=I=-20:TP=-2", str(full)], check=True)
    wav, sr = sf.read(full, dtype="float32")
    print(f"input {src.name}: {len(wav) / sr:.1f}s")
    wins = windows(wav, sr)
    if not wins:
        sys.exit("no 5-8 s stretch of speech found - record again with short pauses between sentences")
    for k, (s, e) in enumerate(wins, 1):
        sf.write(work / f"ref_w{k}.wav", wav[s:e], sr)
        print(f"w{k}: reference {s / sr:.1f}-{e / sr:.1f}s -> {work / f'ref_w{k}.wav'}")
    me = [sys.executable, "-I", str(Path(__file__).resolve())]
    subprocess.run(me + ["--enroll", str(len(wins))], check=True)
    subprocess.run(me + ["--synth", str(len(wins))], check=True)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] in ("--enroll", "--synth"):
        (enroll if sys.argv[1] == "--enroll" else synth)(int(sys.argv[2]))
    elif len(sys.argv) > 1:
        main(Path(sys.argv[1]).resolve())
    else:
        (HERE / "input").mkdir(exist_ok=True)
        files = sorted((f for f in (HERE / "input").iterdir() if f.is_file() and not f.name.startswith(".")),
                       key=lambda f: f.stat().st_mtime)
        if not files:
            sys.exit("no recording in input/ yet")
        main(files[-1])
