"""TripPlanner intro video build (skill aa-uat-video): segments + narration clips -> one MP4 per language with the
narration of that language and burned-in subtitles of that language, plus sidecar .srt / .vtt.

  python -I intro/build_intro.py <en|vi>
    in : work/TripPlanner-intro-<LANG>/{seg-N.webm, timeline.json, result.json, sentences.json, audio/}
    out: out/intro/TripPlanner-intro-<LANG>_<yyyymmdd>.{mp4,srt,vtt}

Each segment is cut at its trim_ms (blank page load), the phone segment (390 x 844) is centred on a navy
1440 x 900 frame, then the segments are joined. One subtitle cue per sentence (long ones split at commas),
timed from the real clip length, so voice and text stay in sync. Short title card at the start, fade out
at the end. Local ffmpeg only, $0.
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
UAT = HERE.parent
LEAD_S = 0.25          # same as record_intro.cjs LEAD_MS
W, H, FPS = 1440, 900, 25
NAVY = "0x1d2633"
MAX_CUE = 84           # characters per cue (two lines of the burned style)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd):
    subprocess.run(cmd, check=True)


def probe_dur(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         check=True, capture_output=True, text=True).stdout.strip()
    return float(out)


def ts(sec: float, sep: str) -> str:
    ms = max(0, int(round(sec * 1000)))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def split_cue(text: str):
    """Split a long sentence at commas / colons into chunks of at most MAX_CUE characters."""
    if len(text) <= MAX_CUE:
        return [text]
    parts = re.split(r"(?<=[,:;])\s+", text)
    chunks, cur = [], ""
    for p in parts:
        if cur and len(cur) + 1 + len(p) > MAX_CUE:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur} {p}".strip()
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:  # a chunk still too long: split at the word nearest the middle
        if len(c) <= MAX_CUE:
            out.append(c)
            continue
        words, best = c.split(), None
        for i in range(1, len(words)):
            a = " ".join(words[:i])
            if best is None or abs(len(a) - len(c) / 2) < abs(len(best[0]) - len(c) / 2):
                best = (a, " ".join(words[i:]))
        out += list(best)
    return out


def main(lang: str) -> None:
    data = json.loads((HERE / "narration.json").read_text())
    work = UAT / "work" / f"{data['id']}-{lang.upper()}"
    out_dir = UAT / "out" / "intro"
    out_dir.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((work / "timeline.json").read_text())
    result = json.loads((work / "result.json").read_text())
    sentences = json.loads((work / "sentences.json").read_text())
    if result["verdict"] != "PASS":
        print(f"WARNING: recording verdict {result['verdict']} at step {result['failed_step']}")

    # 1. Normalise each segment to 1440x900 @25 fps, cut its blank start.
    seg_files, seg_offset, t = [], {}, 0.0
    for seg in result["segments"]:
        src = work / f"seg-{seg['n']}.webm"
        if not src.exists():
            continue
        trim = seg["trim_ms"] / 1000
        dst = work / f"seg-{seg['n']}.norm.mp4"
        if seg["name"] == "mobile":
            # Phone frame top-aligned and kept above the subtitle band, so the bottom bar stays visible.
            ph = 760
            pw = round(seg["viewport"]["width"] * ph / seg["viewport"]["height"] / 2) * 2
            px, py = (W - pw) // 2, 26
            vf = (f"scale={pw}:{ph},pad={W}:{H}:{px}:{py}:color={NAVY},"
                  f"drawbox=x={px - 5}:y={py - 5}:w={pw + 10}:h={ph + 10}:color=0x0f141b@1:t=5,fps={FPS},format=yuv420p")
        else:
            vf = f"scale={W}:{H},fps={FPS},format=yuv420p"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{trim:.3f}", "-i", str(src),
             "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(dst)])
        seg_offset[seg["n"]] = t - trim      # global time = seg_offset + step time (relative to seg t0)
        t += probe_dur(dst)
        seg_files.append(dst)
    total = t
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in seg_files))
    joined = work / "joined.mp4"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c", "copy", str(joined)])

    # 2. Narration track + sentence cues on the global timeline.
    clips = sorted((work / "audio").glob("*.wav"))
    sr = sf.info(clips[0]).samplerate
    track = np.zeros(int((total + 2) * sr), dtype=np.float32)
    cues = []
    for st in timeline:
        base = seg_offset[st["segment"]] + st["start_ms"] / 1000 + LEAD_S
        for it in sentences[str(st["n"])]:
            s, csr = sf.read(work / "audio" / it["file"], dtype="float32")
            if s.ndim > 1:
                s = s.mean(axis=1)
            if csr != sr:
                s = np.interp(np.linspace(0, len(s), int(len(s) * sr / csr), endpoint=False), np.arange(len(s)), s)
            at = int((base + it["offset"]) * sr)
            end = min(len(track), at + len(s))
            track[at:end] += s[: end - at]
            chunks = split_cue(it["text"])
            weights = [len(c) for c in chunks]
            a = base + it["offset"]
            for c, wgt in zip(chunks, weights):
                d = it["dur"] * wgt / sum(weights)
                cues.append([a, a + d, c])
                a += d
    for i in range(len(cues)):  # hold each cue a little, never into the next one
        nxt = cues[i + 1][0] if i + 1 < len(cues) else total
        cues[i][1] = min(cues[i][1] + 0.35, nxt - 0.04)
    peak = float(np.max(np.abs(track))) or 1.0
    track = track * min(1.0, 0.89 / peak)
    wav = work / f"narration.{lang}.wav"
    sf.write(wav, track[: int(total * sr)], sr)

    day = datetime.now().strftime("%Y%m%d")
    base_name = out_dir / f"TripPlanner-intro-{lang.upper()}_{day}"
    srt, vtt = [], ["WEBVTT", ""]
    for i, (a, b, text) in enumerate(cues, 1):
        text = re.sub(r"(?<=\w)-(?=\w)", "‑", text)  # no line break inside "day-by-day"
        srt += [str(i), f"{ts(a, ',')} --> {ts(b, ',')}", text, ""]
        vtt += [f"{ts(a, '.')} --> {ts(b, '.')}", text, ""]
    p_srt = base_name.with_suffix(".srt")
    p_srt.write_text("\n".join(srt), encoding="utf-8")
    base_name.with_suffix(".vtt").write_text("\n".join(vtt), encoding="utf-8")

    # 3. Final encode: burned subtitles, title card (0.4-5.6 s), fade in / out, AAC narration.
    title = data["title"][lang].replace(":", "\\:")
    sub = data["subtitle"][lang].replace(":", "\\:")
    style = ("FontName=DejaVu Sans,FontSize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BackColour=&H60000000,BorderStyle=4,Outline=1,Shadow=0,MarginV=16,MarginL=70,MarginR=70")
    sub_file = str(p_srt).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    en = "enable='between(t,0.4,5.6)'"
    vf = ",".join([
        f"drawbox=x=0:y=ih-250:w=iw:h=120:color=0x1d2633@0.82:t=fill:{en}",
        f"drawtext=fontfile={FONT_B}:text='{title}':fontsize=44:fontcolor=white:x=70:y=h-236:{en}",
        f"drawtext=fontfile={FONT}:text='{sub}':fontsize=26:fontcolor=0xF2B544:x=72:y=h-180:{en}",
        f"subtitles='{sub_file}':force_style='{style}'",
        "fade=t=in:st=0:d=0.6",
        f"fade=t=out:st={total - 1.2:.2f}:d=1.2",
    ])
    mp4 = base_name.with_suffix(".mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(joined), "-i", str(wav),
         "-map", "0:v", "-map", "1:a", "-vf", vf,
         "-af", f"afade=t=out:st={total - 1.2:.2f}:d=1.2",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart",
         "-metadata", f"title={data['title'][lang]} ({lang.upper()})",
         "-metadata:s:a:0", f"language={'eng' if lang == 'en' else 'vie'}",
         "-t", f"{total:.3f}", str(mp4)])
    (work / "build.json").write_text(json.dumps({"total_s": round(total, 3), "cues": len(cues),
                                                  "seg_offset": seg_offset, "mp4": str(mp4)}, indent=2))
    print(f"{mp4}  {total:.1f}s  {len(cues)} cues")


if __name__ == "__main__":
    main(sys.argv[1])
