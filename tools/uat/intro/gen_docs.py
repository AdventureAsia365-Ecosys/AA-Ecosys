"""TripPlanner intro (skill aa-uat-video): write the storyboard and the two narration scripts from narration.json and the
recorded timelines.   python3 -I intro/gen_docs.py   -> out/intro/{storyboard.md, narration-EN.md, narration-VI.md}
"""
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
UAT = HERE.parent
OUT = UAT / "out" / "intro"
data = json.loads((HERE / "narration.json").read_text())
TODAY = date.today().strftime("%d/%m/%Y")


def scenes(lang):
    w = UAT / "work" / f"{data['id']}-{lang.upper()}"
    if not (w / "build.json").exists():
        return None
    b = json.loads((w / "build.json").read_text())
    tl = json.loads((w / "timeline.json").read_text())
    off = {int(k): v for k, v in b["seg_offset"].items()}
    return {st["n"]: (off[st["segment"]] + st["start_ms"] / 1000, off[st["segment"]] + st["end_ms"] / 1000)
            for st in tl}, b["total_s"]


def mmss(s):
    s = max(0, s)
    return f"{int(s // 60)}:{s % 60:04.1f}"


en, vi = scenes("en"), scenes("vi")
lines = [
    f"# TripPlanner product intro — storyboard ({TODAY})", "",
    "Audience: the business owner (non-technical). Recorded on the live production site "
    "(https://aa-tripplanner.vercel.app) at 1440 x 900, plus one phone segment at 390 x 844. "
    "Real pages and real catalogue data only. The contact form is filled with obviously fake demo data and "
    "never submitted (the send request is answered locally with the same \"add your details\" reply the live "
    "site gives a guest); the AI day-by-day narration and free-text search are not used (no paid calls).", "",
    f"Length: EN {mmss(en[1]) if en else 'n/a'}" + (f", VI {mmss(vi[1])}" if vi else ", VI not rendered yet") + ".", "",
    "| # | Scene | EN time | VI time | What is shown | Narration (EN) |",
    "|---|---|---|---|---|---|",
]
for n, st in enumerate(data["steps"], 1):
    def span(x):
        if not x or n not in x[0]:
            return "—"
        a, b = x[0][n]
        return f"{mmss(a)}–{mmss(b)} ({b - a:.0f} s)"
    lines.append(f"| {n} | {st['key']} | {span(en)} | {span(vi)} | {st['scene']} | {' '.join(st['en'])} |")
lines += ["", "Times are the scene's span in the final MP4 of each language (the two recordings differ because "
          "the narration lengths differ). Subtitles: one cue per sentence, timed from the real voice clip."]
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "storyboard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

for lang, head, voice in (("en", "English narration script", "Kokoro af_heart (female)"),
                          ("vi", "Kịch bản lời thuyết minh tiếng Việt (giọng miền Nam)",
                           "VieNeu-TTS v3 Turbo, preset \"Thục Đoan\" (nữ, miền Nam)")):
    out = [f"# TripPlanner intro — {head}", "", f"Voice: {voice}. Recorded {TODAY}.", ""]
    for n, st in enumerate(data["steps"], 1):
        out += [f"## {n}. {st['scene']}", "", " ".join(st[lang]), ""]
    (OUT / f"narration-{lang.upper()}.md").write_text("\n".join(out), encoding="utf-8")
print("storyboard + narration scripts ->", OUT)
