"""UAT video build (skill aa-uat-video): timeline + captions + clips -> MP4 with burned English subtitles,
an English narration track (default), a Vietnamese narration track, and sidecar WebVTT/SRT files.

  python -I build.py <work/ID> <out_dir>

Output names: <ID>_<yyyymmdd>_v<n>.mp4 (+ .en/.vi .srt/.vtt, .result.json); prints the MP4 path last.
Each caption is shown from its step start to its step end (timeline.json). Each narration clip starts
at its step start plus a short lead; record.cjs already held the step as long as the clip, so no stretch.
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

LEAD_S = 0.25


def ts(sec: float, sep: str) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def write_subs(cues, lang, out_base: Path):
    srt, vtt = [], ["WEBVTT", ""]
    for i, (a, b, text) in enumerate(cues, 1):
        srt += [str(i), f"{ts(a, ',')} --> {ts(b, ',')}", text, ""]
        vtt += [f"{ts(a, '.')} --> {ts(b, '.')}", text, ""]
    p_srt = out_base.with_suffix(f".{lang}.srt")
    p_vtt = out_base.with_suffix(f".{lang}.vtt")
    p_srt.write_text("\n".join(srt), encoding="utf-8")
    p_vtt.write_text("\n".join(vtt), encoding="utf-8")
    return p_srt, p_vtt


def narration(work: Path, lang: str, timeline, total_s: float, out_wav: Path) -> bool:
    clips = sorted((work / "audio" / lang).glob("*.wav"))
    if not clips:
        return False
    sr = sf.info(clips[0]).samplerate
    track = np.zeros(int((total_s + 1) * sr), dtype=np.float32)
    for step in timeline:
        p = work / "audio" / lang / f"{step['n']:02d}.wav"
        if not p.exists():
            continue
        s, _ = sf.read(p, dtype="float32")
        if s.ndim > 1:
            s = s.mean(axis=1)
        at = int((step["start_ms"] / 1000 + LEAD_S) * sr)
        end = min(len(track), at + len(s))
        track[at:end] += s[: end - at]
    sf.write(out_wav, np.clip(track, -1, 1), sr)
    return True


def main(work: Path, out_dir: Path) -> None:
    caps = {c["n"]: c for c in json.loads((work / "captions.json").read_text())["captions"]}
    timeline = json.loads((work / "timeline.json").read_text())
    result = json.loads((work / "result.json").read_text())
    total_s = result["total_ms"] / 1000
    out_dir.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    v = 1
    while (out_dir / f"{result['id']}_{day}_v{v}.mp4").exists():
        v += 1
    base = out_dir / f"{result['id']}_{day}_v{v}"

    cues = {}
    for lang in ("en", "vi"):
        cues[lang] = []
        for st in timeline:
            text = caps[st["n"]].get(lang)
            if not text:
                continue
            text = re.sub(r"(?<=\w)-(?=\w)", "‑", text)  # no line break at "AI-generated"
            if st["status"] == "FAIL":
                text = ("[FAIL] " if lang == "en" else "[LỖI] ") + text
            cues[lang].append((st["start_ms"] / 1000, st["end_ms"] / 1000, text))
    en_srt, _ = write_subs(cues["en"], "en", base)
    write_subs(cues["vi"], "vi", base)

    has_en = narration(work, "en", timeline, total_s, work / "narration.en.wav")
    has_vi = narration(work, "vi", timeline, total_s, work / "narration.vi.wav")

    style = ("FontName=DejaVu Sans,FontSize=11,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BackColour=&H30000000,BorderStyle=4,Outline=1,Shadow=0,MarginV=18,MarginL=60,MarginR=60")
    sub_file = str(en_srt).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(work / "video.webm")]
    maps = ["-map", "0:v"]
    idx = 1
    meta = []
    for lang, ok, title in (("en", has_en, "English narration"), ("vi", has_vi, "Vietnamese narration")):
        if ok:
            cmd += ["-i", str(work / f"narration.{lang}.wav")]
            maps += ["-map", f"{idx}:a"]
            a = len([m for m in meta if m[0] == "a"])
            meta.append(("a", a, lang, title))
            idx += 1
    cmd += maps
    cmd += ["-vf", f"subtitles='{sub_file}':force_style='{style}'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p", "-r", "25",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", "-shortest"]
    for kind, i, lang, title in meta:
        cmd += [f"-metadata:s:a:{i}", f"language={'eng' if lang == 'en' else 'vie'}",
                f"-metadata:s:a:{i}", f"title={title}"]
    if meta:
        cmd += ["-disposition:a:0", "default"]
    cmd += [str(base.with_suffix(".mp4"))]
    subprocess.run(cmd, check=True)
    shutil.copy(work / "result.json", base.with_suffix(".result.json"))
    print(base.with_suffix(".mp4"))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
