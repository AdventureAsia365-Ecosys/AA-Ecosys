"""UAT video checks (skill aa-uat-video): speech at every subtitle cue start, plus one frame every 20 s to look at.

  python -I check_sync.py <mp4> <srt> [--track N] [--frames DIR]
    --track N     audio stream to check (0 = English default, 1 = Vietnamese in a UAT MP4)
    --frames DIR  also write DIR/fNN.png, one frame every 20 s (check: cursor, subtitles, no checkpoint page)
Exit 1 when a cue has no speech in its first second (RMS < 0.01). Local ffmpeg only.
"""
import argparse
import re
import subprocess
from pathlib import Path

import numpy as np


def secs(s: str) -> float:
    h, m, r = s.split(":")
    sec, ms = r.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("srt")
    ap.add_argument("--track", type=int, default=0)
    ap.add_argument("--frames")
    a = ap.parse_args()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.mp4, "-map", f"0:a:{a.track}", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], check=True, capture_output=True).stdout
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    cues = re.findall(r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", Path(a.srt).read_text(encoding="utf-8"))
    bad = 0
    for i, (s, e) in enumerate(cues, 1):
        a0, a1 = int(secs(s) * 16000), int(min(secs(e), secs(s) + 1.0) * 16000)
        rms = float(np.sqrt(np.mean(audio[a0:a1] ** 2))) if a1 > a0 else 0.0
        if rms < 0.01:
            bad += 1
            print(f"cue {i} {s}: quiet (rms {rms:.4f})")
    print(f"{len(cues)} cues, {bad} without speech in their first second; audio {len(audio) / 16000:.1f}s")
    if a.frames:
        Path(a.frames).mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.mp4, "-vf", "fps=1/20",
                        str(Path(a.frames) / "f%02d.png")], check=True)
        print(f"frames -> {a.frames}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
