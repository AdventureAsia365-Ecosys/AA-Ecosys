"""Long-form review video (skill aa-uat-video): many short chunk videos -> one MP4 with chapters, where the voice AND
the subtitles are switchable (tech lead decision S261): two audio tracks (English default, Vietnamese) and two soft
subtitle tracks (mov_text English, Vietnamese), nothing burned into the picture.

  python -I longform.py --chunks out/crm/no-burn --prefix CRM-REV- --out out/crm-long --name CRM-REVIEW_20261105_v1
        [--highlight R01,R03,R04,R06,R08,R10,R11,R15] [--per-language] [--subs-default en|none] [--title-vi "..."]

Input: the chunk MP4s from `build.py <work/ID> <dir> --no-burn` (<ID>_<yyyymmdd>_v<n>.mp4, with .en.srt / .vi.srt
and .result.json beside it); the newest version of each id is used, in id order. It stops (exit != 0) when a chosen
chunk is a burned build (subtitles would show twice), is not a PASS (a FAIL chunk keeps [FAIL] captions), recorded
across a deploy (meta.git_sha_start != git_sha_end) or on another app version than the others, or lacks one of its
two narration tracks; --allow-not-pass, --allow-sha-drift and --allow-missing-audio override one check each.
Steps: (1) normalise each chunk: 1440x900 (a 390x844 phone chunk is scaled to fit and padded centred, before any
subtitle is drawn: none is), yuv420p, 25 fps, both audio tracks 48 kHz stereo at -16 LUFS (loudnorm), audio padded to
the picture; (2) a 2.5 s chapter card before each chunk; (3) concat -c copy; (4) EN and VI subtitles merged with each
chunk's offset, chapters from an ffmetadata file; the picture is copied, the audio is re-encoded once over the joined
file (no AAC priming drift across ~40 segments). Also writes chapters.txt and .srt / .vtt sidecars; check the long
output with check_sync.py on both tracks (start and end chapters). --per-language adds <name>_EN.mp4 / <name>_VI.mp4
(that language's voice and subtitles first and default, the other still switchable; in _VI.mp4 the chapter cards and
the chapter list are Vietnamese too, from each chunk's title_vi, else its English title) plus <name>.README.txt: the
Drive player shows no embedded subtitle track by itself, so upload the .srt files beside the MP4 as Drive caption
tracks (or point viewers to the sidecars).
--highlight writes <name>_highlight.mp4 from the listed chunks (same segments, no new recording).
Chapter titles longer than a card line wrap onto two lines (smaller type for very long ones).
Local ffmpeg only, $0. Normalised segments and cards are cached under work/longform/, keyed on the filter and encoder
settings (a changed setting never reuses an old segment).
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H, FPS = 1440, 900, 25
CARD_S = 2.5
BG = "0xF8F6F2"
INK = "0x1F2933"
ACCENT = "0x9E6E16"
ENC_V = ["-c:v", "libx264", "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "50",
         "-video_track_timescale", "12800"]
ENC_A = ["-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2"]
# Normalise filters (templates filled per chunk). Part of the cache key: edit them and old segments are not reused.
NORM_V = ("[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={BG},"
          "setsar=1,fps={FPS},format=yuv420p[v]")
NORM_A = ("[0:a:{i}]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,"
          "apad=whole_dur={secs},atrim=end={secs}[a{i}]")
NORM_SILENT = "[1:a]apad=whole_dur={secs},atrim=end={secs}[a{i}]"
# Card title sizes: (font px, characters per line). DejaVu Sans averages ~0.6 em per character, so each fits the
# 1360 px between the 40 px margins; a title that needs a third line at the smallest size is cut with an ellipsis.
CARD_FITS = ((44, 46), (38, 54), (32, 64))
KICKER = {"en": "Chapter {n} of {total}", "vi": "Phần {n}/{total}"}


DRIVE_NOTE = """{name}: subtitles
The MP4 files carry English and Vietnamese subtitles as switchable tracks, but the Google Drive player does not show
an embedded subtitle track by itself. On Drive, add {name}.en.srt and {name}.vi.srt to the video as caption tracks
(video menu > Manage caption tracks), or open the .srt / .vtt files beside the video in a desktop player.
"""


# ---------- pure helpers (unit-tested in tests/test_longform.py) ----------

def fmt_ts(sec: float, sep: str = ",") -> str:
    ms = int(round(max(sec, 0) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def parse_ts(ts: str) -> float:
    h, m, rest = ts.strip().replace(".", ",").split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(text: str) -> list[tuple[float, float, str]]:
    cues = []
    for block in re.split(r"\r?\n\s*\r?\n", text.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        for i, ln in enumerate(lines):
            m = re.match(r"(\d\d:\d\d:\d\d[,.]\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d[,.]\d\d\d)", ln)
            if m:
                cues.append((parse_ts(m.group(1)), parse_ts(m.group(2)), "\n".join(lines[i + 1:])))
                break
    return cues


def merge_cues(segments: list[tuple[float, list | None]]) -> list[tuple[float, float, str]]:
    """segments: (duration_s, cues of that segment or None for a card), in play order -> cues on the long timeline.
    A cue is clipped to its own segment so it can never run into the next chapter."""
    out, at = [], 0.0
    for duration, cues in segments:
        for a, b, text in cues or []:
            a2, b2 = at + max(a, 0), at + min(b, duration)
            if b2 > a2:
                out.append((round(a2, 3), round(b2, 3), text))
        at += duration
    return out


def chapter_starts(segments: list[tuple[str, float, float]]) -> list[tuple[str, float, float]]:
    """segments: (title, card_s, chunk_s) per chapter -> (title, start_s, end_s); a chapter starts at its card."""
    out, at = [], 0.0
    for title, card, chunk in segments:
        out.append((title, round(at, 3), round(at + card + chunk, 3)))
        at += card + chunk
    return out


def ffmetadata(chapters: list[tuple[str, float, float]], title: str = "") -> str:
    esc = lambda s: re.sub(r"([=;#\\\n])", r"\\\1", s)  # noqa: E731 (ffmetadata escaping)
    lines = [";FFMETADATA1"] + ([f"title={esc(title)}"] if title else [])
    for name, a, b in chapters:
        lines += ["", "[CHAPTER]", "TIMEBASE=1/1000", f"START={int(round(a * 1000))}", f"END={int(round(b * 1000))}",
                  f"title={esc(name)}"]
    return "\n".join(lines) + "\n"


def norm_key() -> str:
    """Hash of everything normalise() applies: part of each normalised segment's cache name."""
    spec = json.dumps([W, H, FPS, BG, NORM_V, NORM_A, NORM_SILENT, ENC_V, ENC_A])
    return hashlib.sha256(spec.encode()).hexdigest()[:10]


def norm_name(src: Path) -> str:
    return f"{src.stem}.{norm_key()}.norm.mp4"


def wrap_title(title: str) -> tuple[list[str], int]:
    """A chapter title -> (card lines, font px): one or two lines at the largest size that fits."""
    for size, chars in CARD_FITS:
        lines = textwrap.wrap(title, chars) or [""]
        if len(lines) <= 2:
            return lines, size
    size, chars = CARD_FITS[-1]
    lines = textwrap.wrap(title, chars)
    return [lines[0], textwrap.shorten(" ".join(lines[1:]), chars, placeholder=" …")], size


def kicker(n: int, total: int, lang: str = "en") -> str:
    return KICKER[lang].format(n=n, total=total)


def chapter_title(item: dict, lang: str = "en") -> str:
    """The chunk's chapter title in that language (title_vi from the scenario, else the English title)."""
    return (item.get("title_vi") if lang == "vi" else None) or item["title"]


def chapters_txt(chapters: list[tuple[str, float, float]]) -> str:
    long = chapters and chapters[-1][2] >= 3600

    def stamp(sec: float) -> str:
        s = int(sec)
        return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if long else f"{s // 60:02d}:{s % 60:02d}"

    return "".join(f"{stamp(a)} {name}\n" for name, a, _ in chapters)


def write_subs(cues, base: Path, lang: str) -> tuple[Path, Path]:
    srt, vtt = [], ["WEBVTT", ""]
    for i, (a, b, text) in enumerate(cues, 1):
        srt += [str(i), f"{fmt_ts(a)} --> {fmt_ts(b)}", text, ""]
        vtt += [f"{fmt_ts(a, '.')} --> {fmt_ts(b, '.')}", text, ""]
    p_srt, p_vtt = Path(f"{base}.{lang}.srt"), Path(f"{base}.{lang}.vtt")
    p_srt.write_text("\n".join(srt), encoding="utf-8")
    p_vtt.write_text("\n".join(vtt), encoding="utf-8")
    return p_srt, p_vtt


def pick_chunks(files: list[str], prefix: str) -> dict[str, str]:
    """Newest <prefix><NN>_<yyyymmdd>_v<n>.mp4 per id (by date, then version) -> {id: file name}."""
    best: dict[str, tuple[str, int, str]] = {}
    for f in files:
        m = re.fullmatch(rf"({re.escape(prefix)}\d\d)_(\d{{8}})_v(\d+)\.mp4", Path(f).name)
        if m and (m.group(1) not in best or (m.group(2), int(m.group(3))) > best[m.group(1)][:2]):
            best[m.group(1)] = (m.group(2), int(m.group(3)), f)
    return {k: v[2] for k, v in sorted(best.items())}


def chunk_problems(results: dict[str, dict], allow_not_pass: bool = False, allow_sha_drift: bool = False) -> list[str]:
    """results: {id: .result.json of the chosen build} -> what forbids joining them (empty list = fine).
    A burned build is always refused (the long video adds soft subtitles: they would show twice)."""
    out, shas = [], {}
    for cid, r in sorted(results.items()):
        if r.get("burned", True):
            out.append(f"{cid}: a burned build (rebuild it with build.py --no-burn)")
        if not allow_not_pass and r.get("verdict") != "PASS":
            out.append(f"{cid}: verdict {r.get('verdict')} (step {r.get('failed_step')})")
        meta = r.get("meta") or {}
        a, b = meta.get("git_sha_start"), meta.get("git_sha_end")
        if not allow_sha_drift:
            if not a or not b:
                out.append(f"{cid}: no app git sha recorded at the start and the end")
            elif a != b:
                out.append(f"{cid}: redeployed during the recording ({a[:7]} -> {b[:7]})")
        if a:
            shas.setdefault(a, []).append(cid)
    if len(shas) > 1 and not allow_sha_drift:
        out.append("chunks recorded on different app versions: " + "; ".join(f"{k[:7]}: {', '.join(v)}" for k, v in shas.items()))
    return out


def highlight_ids(spec: str, prefix: str) -> list[str]:
    """'R01,R03' -> ['<prefix>01', '<prefix>03'] (also accepts 1,3 or full ids)."""
    out = []
    for tok in [t.strip() for t in spec.split(",") if t.strip()]:
        m = re.search(r"(\d+)$", tok)
        if not m:
            raise ValueError(f"not a chunk number: {tok}")
        out.append(f"{prefix}{int(m.group(1)):02d}")
    return out


# ---------- ffmpeg ----------

def run(cmd: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *cmd], check=True)


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def video_duration(path: Path) -> float:
    info = probe(path)
    v = next((s for s in info["streams"] if s["codec_type"] == "video" and s.get("duration")), None)
    return float(v["duration"] if v else info["format"]["duration"])


def run_to(dst: Path, cmd: list[str]) -> None:
    """ffmpeg into <dst>.part, then rename: a failed or killed run never leaves a stub the cache would reuse."""
    part = dst.with_name(dst.stem + ".part" + dst.suffix)
    try:
        run([*cmd, str(part)])
        part.replace(dst)
    finally:
        part.unlink(missing_ok=True)


def audio_tracks(src: Path) -> int:
    return sum(1 for s in probe(src)["streams"] if s["codec_type"] == "audio")


def normalise(src: Path, dst: Path) -> None:
    """A chunk with fewer than two narration tracks gets silence for the missing one; main() refuses that unless
    --allow-missing-audio was passed. `dst` should be named by norm_name() (the settings are in the name)."""
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    n_audio = audio_tracks(src)
    secs = video_duration(src)
    inputs = ["-i", str(src)]
    if n_audio < 2:
        inputs += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    parts = [NORM_V.format(W=W, H=H, BG=BG, FPS=FPS)]
    # Pad each narration to the picture length and cut everything at it. Not an endless apad + -shortest: ffmpeg 6.1
    # then ends with "Error while filtering: No space left on device" (exit 228) although the file is complete.
    for i in range(2):
        parts.append((NORM_A if i < n_audio else NORM_SILENT).format(i=i, secs=f"{secs:.3f}"))
    run_to(dst, [*inputs, "-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a0]", "-map", "[a1]",
                 "-t", f"{secs:.3f}", *ENC_V, *ENC_A])


def card_name(kicker: str, title: str, font: str) -> str:
    """Cache name of a chapter card: a hash of what is drawn and how (layout, encoder), so "Chapter 4 of 21" never
    stands in for "4 of 8" and a card cut by an older layout is not reused."""
    spec = json.dumps([kicker, title, font, W, H, CARD_FITS, ENC_V, ENC_A, "card-v2"])
    return "card-" + hashlib.sha256(spec.encode()).hexdigest()[:16] + ".mp4"


def card(dst: Path, kicker: str, title: str, font: str) -> None:
    if dst.exists():
        return
    lines, size = wrap_title(title)
    k = dst.with_suffix(".k.txt")
    k.write_text(kicker, encoding="utf-8")
    ff = font.replace(":", "\\:")
    step = int(size * 1.3)
    top = -10 - (len(lines) - 1) * step // 2  # the title block stays centred under the kicker
    draws = [f"drawtext=fontfile='{ff}':textfile='{k}':fontsize=26:fontcolor={ACCENT}:x=(w-text_w)/2:y=h/2{top - 60:+d}"]
    for i, line in enumerate(lines):
        t = dst.with_suffix(f".t{i}.txt")
        t.write_text(line, encoding="utf-8")
        draws.append(f"drawtext=fontfile='{ff}':textfile='{t}':fontsize={size}:fontcolor={INK}:"
                     f"x=max((w-text_w)/2\\,40):y=h/2{top + i * step:+d}")
    vf = ",".join([*draws, "format=yuv420p"])
    run_to(dst, ["-f", "lavfi", "-i", f"color=c={BG}:s={W}x{H}:r={FPS}:d={CARD_S}", "-f", "lavfi", "-t", str(CARD_S),
                 "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-map", "0:v", "-map", "1:a", "-map", "1:a",
                 "-t", str(CARD_S), *ENC_V, *ENC_A])


def font_file() -> str:
    try:
        f = subprocess.run(["fc-match", "-f", "%{file}", "DejaVu Sans"], check=True, capture_output=True, text=True).stdout
        if f and Path(f).exists():
            return f
    except (OSError, subprocess.CalledProcessError):
        pass
    sys.exit("STOP: no DejaVu Sans font (sudo apt install fonts-dejavu-core)")


def assemble(items: list[dict], out_base: Path, cache: Path, title: str, subs_default: str, per_language: bool,
             title_vi: str = "") -> Path:
    """items: [{id, title, title_vi?, mp4, en, vi}] in play order -> <out_base>.mp4 (+ sidecars, chapters.txt).
    With per_language, _VI.mp4 is joined from Vietnamese chapter cards and carries a Vietnamese chapter list."""
    font = font_file()
    norms = []
    for it in items:
        npath = cache / norm_name(Path(it["mp4"]))
        normalise(Path(it["mp4"]), npath)
        norms.append(npath)
    out_base.parent.mkdir(parents=True, exist_ok=True)

    def join(lang: str) -> dict:
        """Cards in `lang` + the normalised chunks -> joined MP4, ffmetadata, chapters and both subtitle files."""
        segs, chapters_in, sub_segments = [], [], {"en": [], "vi": []}
        for n, (it, npath) in enumerate(zip(items, norms), 1):
            k, t = kicker(n, len(items), lang), chapter_title(it, lang)
            cpath = cache / card_name(k, t, font)
            card(cpath, k, t, font)
            cd, nd = duration(cpath), duration(npath)
            segs += [cpath, npath]
            chapters_in.append((t, cd, nd))
            for sl in ("en", "vi"):
                cues = parse_srt(Path(it[sl]).read_text(encoding="utf-8")) if it.get(sl) and Path(it[sl]).exists() else []
                sub_segments[sl] += [(cd, None), (nd, cues)]
        listing = cache / f"{out_base.name}.{lang}.concat.txt"
        listing.write_text("".join(f"file '{p.resolve()}'\n" for p in segs), encoding="utf-8")
        joined = cache / f"{out_base.name}.{lang}.joined.mp4"
        # Picture copied; both audio tracks re-encoded once over the whole timeline so ~40 AAC primings cannot add up.
        run(["-f", "concat", "-safe", "0", "-i", str(listing), "-map", "0", "-c:v", "copy", *ENC_A, str(joined)])
        chapters = chapter_starts(chapters_in)
        meta = cache / f"{out_base.name}.{lang}.ffmeta.txt"
        meta.write_text(ffmetadata(chapters, (title_vi or title) if lang == "vi" else title), encoding="utf-8")
        # The EN join writes the sidecars beside the output; the VI join keeps its own copies in the cache.
        sub_base = out_base if lang == "en" else cache / f"{out_base.name}.vi-cards"
        srt = {sl: write_subs(merge_cues(sub_segments[sl]), sub_base, sl)[0] for sl in ("en", "vi")}
        return {"joined": joined, "meta": meta, "chapters": chapters, "srt": srt}

    def mux(dst: Path, src: dict, first: str, sub_default: str) -> None:
        second = "vi" if first == "en" else "en"
        a_idx = {"en": 0, "vi": 1}
        cmd = ["-i", str(src["joined"]), "-i", str(src["srt"][first]), "-i", str(src["srt"][second]), "-i", str(src["meta"]),
               "-map", "0:v", "-map", f"0:a:{a_idx[first]}", "-map", f"0:a:{a_idx[second]}", "-map", "1", "-map", "2",
               "-map_metadata", "3", "-map_chapters", "3", "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text"]
        names = {"en": ("eng", "English"), "vi": ("vie", "Tiếng Việt")}
        for i, lang in enumerate((first, second)):
            cmd += [f"-metadata:s:a:{i}", f"language={names[lang][0]}", f"-metadata:s:a:{i}", f"title={names[lang][1]}",
                    f"-metadata:s:s:{i}", f"language={names[lang][0]}", f"-metadata:s:s:{i}", f"title={names[lang][1]}"]
        cmd += ["-disposition:a:0", "default", "-disposition:a:1", "0",
                "-disposition:s:0", "default" if sub_default == first else "0",
                "-disposition:s:1", "default" if sub_default == second else "0",
                "-movflags", "+faststart", str(dst)]
        run(cmd)

    en = join("en")
    Path(f"{out_base}.chapters.txt").write_text(chapters_txt(en["chapters"]), encoding="utf-8")
    master = out_base.with_suffix(".mp4")
    mux(master, en, "en", subs_default)
    joined = [en["joined"]]
    if per_language:  # a Drive copy per language: that voice and its subtitles first and default, both switchable
        mux(Path(f"{out_base}_EN.mp4"), en, "en", "en")
        vi = join("vi")
        joined.append(vi["joined"])
        Path(f"{out_base}.chapters.vi.txt").write_text(chapters_txt(vi["chapters"]), encoding="utf-8")
        mux(Path(f"{out_base}_VI.mp4"), vi, "vi", "vi")
        Path(f"{out_base}.README.txt").write_text(DRIVE_NOTE.format(name=out_base.name), encoding="utf-8")
    for j in joined:
        j.unlink(missing_ok=True)
    return master


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--chunks", required=True, help="folder of build.py --no-burn outputs (<out>/no-burn)")
    ap.add_argument("--prefix", default="CRM-REV-")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True, help="e.g. CRM-REVIEW_20261105_v1")
    ap.add_argument("--title", default="Adventure Asia Partner CRM review")
    ap.add_argument("--title-vi", default="Đánh giá CRM cho đại lý của Adventure Asia",
                    help="the file title in the Vietnamese copy (--per-language)")
    ap.add_argument("--highlight", default="", help="chunk numbers for the highlight cut, e.g. R01,R03,R04")
    ap.add_argument("--per-language", action="store_true")
    ap.add_argument("--subs-default", choices=("en", "vi", "none"), default="en")
    ap.add_argument("--allow-not-pass", action="store_true", help="join chunks whose verdict is not PASS")
    ap.add_argument("--allow-sha-drift", action="store_true", help="join chunks recorded across a deploy / versions")
    ap.add_argument("--allow-missing-audio", action="store_true", help="fill a missing narration track with silence")
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("STOP: ffmpeg missing")
    chunks_dir = Path(a.chunks).resolve()
    picked = pick_chunks([str(p) for p in chunks_dir.glob(f"{a.prefix}*.mp4")], a.prefix)
    if not picked:
        sys.exit(f"STOP: no {a.prefix}NN_<date>_v<n>.mp4 in {chunks_dir}")
    items, results = {}, {}
    for cid, f in picked.items():
        stem = Path(f).with_suffix("")
        res = Path(f"{stem}.result.json")
        if not res.exists():
            sys.exit(f"STOP: {cid}: no {res.name} beside the MP4")
        results[cid] = json.loads(res.read_text())
        items[cid] = {"id": cid, "title": results[cid]["title"], "title_vi": results[cid].get("title_vi"), "mp4": f,
                      "en": f"{stem}.en.srt", "vi": f"{stem}.vi.srt"}
    problems = chunk_problems(results, a.allow_not_pass, a.allow_sha_drift)
    if not a.allow_missing_audio:
        problems += [f"{cid}: {n} narration track(s), expected 2" for cid, it in items.items()
                     if (n := audio_tracks(Path(it["mp4"]))) < 2]
    if problems:
        sys.exit("STOP:\n  " + "\n  ".join(problems))
    shas = sorted({(r.get("meta") or {}).get("git_sha_start", "?") for r in results.values()})
    print(f"app git sha: {', '.join(shas)}")
    cache = HERE / "work" / "longform"
    cache.mkdir(parents=True, exist_ok=True)
    out = Path(a.out).resolve()
    master = assemble(list(items.values()), out / a.name, cache, a.title, a.subs_default, a.per_language, a.title_vi)
    print(master)
    if a.highlight:
        ids = highlight_ids(a.highlight, a.prefix)
        missing = [i for i in ids if i not in items]
        if missing:
            sys.exit(f"STOP: highlight chunks not found: {', '.join(missing)}")
        hl = assemble([items[i] for i in ids], out / f"{a.name}_highlight", cache, f"{a.title} (highlights)",
                      a.subs_default, a.per_language, f"{a.title_vi} (bản rút gọn)")
        print(hl)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
