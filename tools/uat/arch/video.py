"""MP4 assembly for one cut of an architecture video (AA-1021): keyframes + narration -> captioned, metadata-free MP4.

  video.build_cut(...)   (make_episode.py calls it; see its docstring for the inputs)

  - keyframes: the 2x PNG captures are scaled once to the frame size (lanczos), then joined with 0.45 s cross-fades
    (xfade) on the cut timeline; no screen recording, so labels stay sharp; x264 crf 19, 25 fps, yuv420p.
  - narration: the loudness-normalised clips (tts_arch.py) placed at their sentence starts, AAC 160k 48 kHz.
  - captions: burned from an ASS file with the per-aspect size and band (scene.py LAYOUT), plus .srt and .vtt sidecars.
  - chapters (master only): embedded from an ffmetadata file and written into the description file.
  - metadata: no input tags (-map_metadata -1, or the empty global block of the chapters file) plus bitexact flags;
    the only tag set is a neutral title (gate layer 4 checks it).
Local ffmpeg only, $0. One ffmpeg at a time.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from scene import ASPECTS

XF = 0.45
FPS = 25
SR = 24000


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def scale_keyframe(src: Path, dst: Path, aspect: str) -> Path:
    w, h = ASPECTS[aspect]
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vf",
         f"scale={w}:{h}:flags=lanczos", str(dst)])
    return dst


def narration(tl: list[dict], clips: dict[str, dict], total: float, out_wav: Path) -> Path:
    import numpy as np          # venv only: the stdlib gate tests import make_episode without them
    import soundfile as sf

    track = np.zeros(int((total + 1) * SR), dtype=np.float32)
    for e in tl:
        s, sr = sf.read(clips[e["id"]]["wav"], dtype="float32")
        if s.ndim > 1:
            s = s.mean(axis=1)
        if sr != SR:
            s = np.interp(np.linspace(0, len(s), int(len(s) * SR / sr), endpoint=False), np.arange(len(s)), s)
        at = int(e["start"] * SR)
        end = min(len(track), at + len(s))
        track[at:end] += s[: end - at]
    sf.write(str(out_wav), np.clip(track[: int(total * SR)], -1, 1), SR)
    return out_wav


def ffmetadata(chaps: list[tuple[float, str]], total: float, path: Path) -> Path:
    lines = [";FFMETADATA1"]
    ends = [c[0] for c in chaps[1:]] + [total]
    for (start, title), end in zip(chaps, ends):
        safe = title.replace("=", "\\=").replace(";", "\\;").replace("#", "\\#").replace("\n", " ")
        lines += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(start * 1000)}", f"END={int(end * 1000)}",
                  f"title={safe}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def video_cmd(frames: list[tuple[Path, float, float]], wav: Path, ass_path: Path, fonts_dir: Path | None,
              total: float, out_mp4: Path, title: str, chapters_file: Path | None) -> list[str]:
    """The ffmpeg command: frames = [(png at frame size, at, until)] on the cut timeline."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for i, (png, at, until) in enumerate(frames):
        dur = (until - at) + (XF if i + 1 < len(frames) else 0)
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(png)]
    cmd += ["-i", str(wav)]
    audio_idx = len(frames)
    chap_idx = None
    if chapters_file:
        cmd += ["-i", str(chapters_file)]
        chap_idx = audio_idx + 1
    parts = [f"[{i}:v]format=yuv420p,setsar=1[v{i}]" for i in range(len(frames))]
    last = "v0"
    for i in range(1, len(frames)):
        out = f"x{i}"
        parts.append(f"[{last}][v{i}]xfade=transition=fade:duration={XF}:offset={frames[i][1]:.3f}[{out}]")
        last = out
    esc = str(ass_path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    sub = f"ass='{esc}'"
    if fonts_dir:
        sub += f":fontsdir='{str(fonts_dir).replace(':', chr(92) + ':')}'"
    parts.append(f"[{last}]{sub},fade=t=in:st=0:d=0.4,fade=t=out:st={max(0.0, total - 1.0):.3f}:d=1.0[vout]")
    parts.append(f"[{audio_idx}:a]afade=t=out:st={max(0.0, total - 1.0):.3f}:d=1.0,aresample=48000[aout]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", "[aout]"]
    # Global tags come from the ffmetadata file (it holds none) or from nowhere; either way only the title set below
    # survives. -map_metadata -1 with chapters would also blank the chapter titles, hence the two forms.
    if chap_idx is not None:
        cmd += ["-map_metadata", str(chap_idx), "-map_chapters", str(chap_idx)]
    else:
        cmd += ["-map_metadata", "-1", "-map_chapters", "-1"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart",
            "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact",
            "-metadata", f"title={title}", "-metadata:s:a:0", "language=eng",
            "-t", f"{total:.3f}", str(out_mp4)]
    return cmd


def sample_frames(mp4: Path, out_dir: Path, every_s: float = 2.0) -> list[Path]:
    """One frame every `every_s` seconds of a final MP4 (gate layer 3 input)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("f-*.png"):
        old.unlink()
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp4), "-vf", f"fps=1/{every_s}",
         str(out_dir / "f-%04d.png")])
    return sorted(out_dir.glob("f-*.png"))


def probe_duration(mp4: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                         check=True, capture_output=True, text=True).stdout.strip()
    return float(out)
