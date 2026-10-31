"""UAT video build (skill aa-uat-video): timeline + captions + clips -> MP4 with burned English subtitles,
an English narration track (default), a Vietnamese narration track, and sidecar WebVTT/SRT files.

  python -I build.py <work/ID> <out_dir>
  python -I build.py <work/ID> <out_dir> --no-burn   (no burned-in subtitles: input for longform.py, which keeps
                                                      the subtitles as switchable tracks; the default is unchanged)
  python -I build.py <work/ID> <out_dir> --soft-subs (a stand-alone chunk with nothing burned in: two soft
                                                      subtitle tracks, mov_text English (default) + Vietnamese, beside
                                                      the two voices; goes to <out_dir>/soft/; a sample to listen to)

Output names: <ID>_<yyyymmdd>_v<n>.mp4 (+ .en/.vi .srt/.vtt, .result.json with "burned": true|false, which
longform.py reads to refuse a burned chunk); --no-burn builds go to <out_dir>/no-burn/ and --soft-subs builds to
<out_dir>/soft/, so no two kinds share a version counter. Prints the MP4 path last.
Each caption is shown from its step start to its step end (timeline.json). Each narration clip starts
at its step start plus a short lead; record.cjs already held the step as long as the clip, so no stretch.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

LEAD_S = 0.25
LANG3 = {"en": "eng", "vi": "vie"}
SUB_TITLE = {"en": "English", "vi": "Tiếng Việt"}


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


def video_seconds(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1",
                          str(path)], check=True, capture_output=True, text=True).stdout.strip()
    return float(out)


def mux_args(audio_meta, soft_srts) -> list:
    """ffmpeg -map/-c:s/-metadata arguments after the inputs: picture, the narration tracks (first one default) and,
    for a soft build, one mov_text track per (lang, srt input index), the first one shown by default."""
    args = ["-map", "0:v"]
    for i, lang, title, idx in audio_meta:
        args += ["-map", f"{idx}:a"]
    for j, (lang, idx) in enumerate(soft_srts):
        args += ["-map", f"{idx}:s"]
    for i, lang, title, idx in audio_meta:
        args += [f"-metadata:s:a:{i}", f"language={LANG3[lang]}", f"-metadata:s:a:{i}", f"title={title}"]
    if audio_meta:
        args += ["-disposition:a:0", "default"]
    if soft_srts:
        args += ["-c:s", "mov_text"]
        for j, (lang, idx) in enumerate(soft_srts):
            args += [f"-metadata:s:s:{j}", f"language={LANG3[lang]}", f"-metadata:s:s:{j}", f"title={SUB_TITLE[lang]}",
                     f"-disposition:s:{j}", "default" if j == 0 else "0"]
    return args


def main(work: Path, out_dir: Path, burn: bool = True, soft: bool = False) -> None:
    caps = {c["n"]: c for c in json.loads((work / "captions.json").read_text())["captions"]}
    timeline = json.loads((work / "timeline.json").read_text())
    result = json.loads((work / "result.json").read_text())
    total_s = result["total_ms"] / 1000
    if soft:
        burn = False
        out_dir = out_dir / "soft"
    elif not burn:
        out_dir = out_dir / "no-burn"
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
    vi_srt, _ = write_subs(cues["vi"], "vi", base)

    has_en = narration(work, "en", timeline, total_s, work / "narration.en.wav")
    has_vi = narration(work, "vi", timeline, total_s, work / "narration.vi.wav")

    style = ("FontName=DejaVu Sans,FontSize=11,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BackColour=&H30000000,BorderStyle=4,Outline=1,Shadow=0,MarginV=18,MarginL=60,MarginR=60")
    sub_file = str(en_srt).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(work / "video.webm")]
    idx = 1
    audio_meta = []
    for lang, ok, title in (("en", has_en, "English narration"), ("vi", has_vi, "Vietnamese narration")):
        if ok:
            cmd += ["-i", str(work / f"narration.{lang}.wav")]
            audio_meta.append((len(audio_meta), lang, title, idx))
            idx += 1
    soft_srts = []
    if soft:
        for lang, srt in (("en", en_srt), ("vi", vi_srt)):
            if cues[lang]:
                cmd += ["-i", str(srt)]
                soft_srts.append((lang, idx))
                idx += 1
    if burn:
        cmd += ["-vf", f"subtitles='{sub_file}':force_style='{style}'"]
    # -shortest trims the narration (total + 1 s) to the picture; a subtitle track ends at its last cue, so a soft
    # build cuts at the picture's own length instead (with -shortest it would end at the last cue).
    end = ["-t", f"{video_seconds(work / 'video.webm'):.3f}"] if soft_srts else ["-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p", "-r", "25",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", *end]
    cmd += mux_args(audio_meta, soft_srts)
    cmd += [str(base.with_suffix(".mp4"))]
    subprocess.run(cmd, check=True)
    base.with_suffix(".result.json").write_text(json.dumps({**result, "burned": burn, "soft_subs": soft}, indent=2), encoding="utf-8")
    print(base.with_suffix(".mp4"))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(Path(args[0]).resolve(), Path(args[1]).resolve(), burn="--no-burn" not in sys.argv[1:],
         soft="--soft-subs" in sys.argv[1:])
