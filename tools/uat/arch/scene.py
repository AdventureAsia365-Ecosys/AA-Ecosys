"""Scene JSON for the architecture videos (AA-1021): validation, per-cut timelines, keyframes, captions, chapters.

Pure logic (stdlib only); make_episode.py drives it. Episode files (scripts, scene JSON) never go into a public repo:
keep them in .tmp-session/ or Drive. Format (an invented, complete example: tests/test_scene.py):

  {"slug": "ep1-example", "title": "...", "series": "...", "episode": 1,
   "voices": {"F": "af_heart", "M": "am_michael"},                 optional, these are the defaults
   "diagrams": {"eco": {"groups": [...], "nodes": [...], "edges": [...]}},   key -> a sketch (sketch.py format)
   "identity": ["..."],                                            optional: phrases a viewer would search for
   "description": "...", "hashtags": ["#aws"],
   "cuts": {"master": {"aspect": "16:9", "chapters": true, "min_s": 150, "max_s": 260},
            "short":  {"aspect": "9:16", "max_s": 60}, ...},
   "scenes": [{"id": "s1", "chapter": "The problem", "voice": "F", "cuts": ["master", "short"],
               "visual": {"type": "title", "kicker": "...", "title": "...", "lead": "..."},
               "sentences": ["One sentence.", {"text": "...", "voice": "M", "visual": {...}, "cuts": ["master"]}]}]}

Voices: each sentence has a voice key (F/M); a scene without "voice" alternates with the previous scene, starting with F
in odd episodes and M in even ones; a sentence may override it. Visual types: title, points, diagram, end (page.py).
A sentence "visual" is merged over the scene visual. A scene without "cuts" is in the master only.

Phone frames: a diagram may have a variant drawn for some aspects, keyed "<diagram>@<name>" with "aspects":
["9:16", "4:5"] and its own grid (and text_scale / node_w); it shows only labels of its base diagram. A diagram
visual may carry "aspects": {"9:16,4:5": {"focus": [...], "reveal": [...], "highlight": [...]}}, merged over it in
those aspects only (the camera of a phone frame shows fewer nodes, larger).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import sketch

ALLOWED_VOICES = {"af_heart", "am_michael"}
DEFAULT_VOICES = {"F": "af_heart", "M": "am_michael"}
ASPECTS = {"16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920)}
# Caption cue length (characters, two lines at most) and the burned style per aspect. 9:16 keeps the captions in the
# middle band (Shorts / Reels cover the bottom ~20% and the right ~15% with their own buttons).
CUE_CHARS = {"16:9": 84, "1:1": 60, "4:5": 60, "9:16": 44}
LAYOUT = {
    #        header band      stage band       caption bottom margin, font px, side margins (left, right) as fractions
    "16:9": {"header": (0.035, 0.135), "stage": (0.15, 0.80), "cap_margin": 0.045, "cap_px": 44, "side": (0.05, 0.05)},
    "1:1": {"header": (0.04, 0.15), "stage": (0.16, 0.74), "cap_margin": 0.05, "cap_px": 46, "side": (0.06, 0.06)},
    "4:5": {"header": (0.04, 0.14), "stage": (0.15, 0.73), "cap_margin": 0.06, "cap_px": 48, "side": (0.06, 0.06)},
    "9:16": {"header": (0.07, 0.17), "stage": (0.18, 0.645), "cap_margin": 0.27, "cap_px": 52, "side": (0.07, 0.15)},
}
VISUAL_TYPES = {"title", "points", "diagram", "end"}
INTRO_S, SENT_GAP_S, SCENE_GAP_S, OUTRO_S, PRE_S = 0.6, 0.35, 0.6, 1.4, 0.25
CUE_HOLD_S = 0.3


class SceneError(ValueError):
    pass


@dataclass
class Sentence:
    id: str
    scene: str
    chapter: str
    text: str
    voice_key: str
    voice: str
    visual: dict
    cuts: set = field(default_factory=set)


def load(data: dict) -> tuple[dict, list[Sentence]]:
    """Validate an episode and flatten it to sentences. Raises SceneError with every problem found."""
    problems = []
    for key in ("slug", "title", "scenes", "cuts"):
        if key not in data:
            problems.append(f"missing '{key}'")
    if problems:
        raise SceneError("; ".join(problems))
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,60}", data["slug"]):
        problems.append("slug must be lower-case letters, digits and '-'")
    voices = {**DEFAULT_VOICES, **data.get("voices", {})}
    for k, v in voices.items():
        if v not in ALLOWED_VOICES:
            problems.append(f"voice {k}={v} is not an approved voice ({sorted(ALLOWED_VOICES)})")
    cuts = data["cuts"]
    for name, cut in cuts.items():
        if cut.get("aspect") not in ASPECTS:
            problems.append(f"cut {name}: aspect must be one of {sorted(ASPECTS)}")
    if "master" not in cuts:
        problems.append("a 'master' cut is required")
    all_diagrams = data.get("diagrams", {})
    diagrams = {k: v for k, v in all_diagrams.items() if "@" not in k}
    for key, spec in all_diagrams.items():
        if isinstance(spec, str):
            problems.append(f"diagram {key}: a committed diagram ({spec!r}) cannot be used; a relabelled copy keeps "
                            "the public figure's layout (a visual fingerprint): author a sketch (sketch.py)")
        else:
            problems += sketch.validate(spec, key)
    taken: set[tuple[str, str]] = set()
    for key, spec in all_diagrams.items():
        if "@" not in key or isinstance(spec, str):
            continue
        base = key.split("@", 1)[0]
        asps = spec.get("aspects") if isinstance(spec, dict) else None
        if base not in diagrams or isinstance(diagrams[base], str):
            problems.append(f"diagram {key}: variant of an unknown diagram {base!r}")
            continue
        if not (isinstance(asps, list) and asps and set(asps) <= set(ASPECTS)):
            problems.append(f"diagram {key}: aspects must be a list of {sorted(ASPECTS)}")
            continue
        for a in asps:
            if (base, a) in taken:
                problems.append(f"diagram {key}: a second variant of {base} for {a}")
            taken.add((base, a))
        extra = set(sketch.labels(spec)) - set(sketch.labels(diagrams[base]))
        if extra:
            problems.append(f"diagram {key}: labels not in {base}: {sorted(extra)}")
    episode = int(data.get("episode", 1))
    prev = "M" if episode % 2 == 1 else "F"      # so the first scene gets F in odd episodes
    out: list[Sentence] = []
    seen = set()
    for si, sc in enumerate(data["scenes"], 1):
        sid = sc.get("id") or f"s{si}"
        if sid in seen:
            problems.append(f"duplicate scene id {sid}")
        seen.add(sid)
        vkey = sc.get("voice") or ("F" if prev == "M" else "M")
        prev = vkey
        visual = sc.get("visual") or {}
        scene_cuts = set(sc.get("cuts") or ["master"])
        for c in scene_cuts - set(cuts):
            problems.append(f"scene {sid}: unknown cut {c}")
        if not sc.get("sentences"):
            problems.append(f"scene {sid}: no sentences")
        for ni, raw in enumerate(sc.get("sentences", []), 1):
            item = {"text": raw} if isinstance(raw, str) else dict(raw)
            text = " ".join(str(item.get("text", "")).split())
            if not text:
                problems.append(f"{sid}.{ni}: empty text")
            sk = item.get("voice", vkey)
            if sk not in voices:
                problems.append(f"{sid}.{ni}: voice key {sk} not in {sorted(voices)}")
                continue
            vis = {**visual, **(item.get("visual") or {})}
            vt = vis.get("type")
            if vt not in VISUAL_TYPES:
                problems.append(f"{sid}.{ni}: visual type {vt!r} not in {sorted(VISUAL_TYPES)}")
            if vt == "diagram" and vis.get("diagram") not in diagrams:
                problems.append(f"{sid}.{ni}: diagram {vis.get('diagram')!r} not declared in 'diagrams'")
            for ak, ov in (vis.get("aspects") or {}).items():
                if not set(a.strip() for a in ak.split(",")) <= set(ASPECTS):
                    problems.append(f"{sid}.{ni}: visual aspects key {ak!r} is not a list of {sorted(ASPECTS)}")
                if not (isinstance(ov, dict) and set(ov) <= {"reveal", "focus", "highlight"}):
                    problems.append(f"{sid}.{ni}: visual aspects {ak!r} may set reveal / focus / highlight only")
            sc_cuts = set(item.get("cuts") or scene_cuts)
            for c in sc_cuts - set(cuts):
                problems.append(f"{sid}.{ni}: unknown cut {c}")
            out.append(Sentence(f"{sid}.{ni}", sid, sc.get("chapter", ""), text, sk, voices[sk], vis, sc_cuts))
    if problems:
        raise SceneError("; ".join(problems))
    meta = {k: v for k, v in data.items() if k != "scenes"}
    meta["voices"] = voices
    return meta, out


def all_texts(data: dict, sentences: list[Sentence]) -> dict[str, str]:
    """Every authored string of an episode, keyed by where it sits (layer 1 input)."""
    texts = {"title": data.get("title", ""), "series": data.get("series", ""),
             "description": data.get("description", ""), "hashtags": " ".join(data.get("hashtags", []))}
    for s in sentences:
        texts[f"{s.id}:text"] = s.text
        for k, v in s.visual.items():
            if k in ("type", "diagram", "reveal", "focus", "highlight", "aspects"):
                continue
            texts[f"{s.id}:visual.{k}"] = " ".join(v) if isinstance(v, list) else str(v)
    for sc in data.get("scenes", []):
        texts[f"{sc.get('id')}:chapter"] = sc.get("chapter", "")
    return {k: v for k, v in texts.items() if v}


def svgs_for_aspect(svgs: dict[str, str], diagrams: dict, aspect: str) -> dict[str, str]:
    """The rendered diagrams one aspect shows: each base key, drawn from its variant for that aspect if any."""
    out = {k: v for k, v in svgs.items() if "@" not in k}
    for k, spec in diagrams.items():
        if "@" in k and k in svgs and aspect in (spec.get("aspects") or []):
            out[k.split("@", 1)[0]] = svgs[k]
    return out


def cut_sentences(sentences: list[Sentence], cut: str) -> list[Sentence]:
    return [s for s in sentences if cut in s.cuts]


def timeline(sents: list[Sentence], durations: dict[str, float]) -> tuple[list[dict], float]:
    """Start and end of every sentence of one cut (seconds) and the cut length."""
    t, prev_scene, out = INTRO_S, None, []
    for s in sents:
        if prev_scene is not None and s.scene != prev_scene:
            t += SCENE_GAP_S
        d = float(durations[s.id])
        out.append({"id": s.id, "scene": s.scene, "chapter": s.chapter, "start": round(t, 3),
                    "end": round(t + d, 3), "text": s.text, "voice": s.voice, "visual": s.visual})
        t += d + SENT_GAP_S
        prev_scene = s.scene
    total = (t - SENT_GAP_S if out else t) + OUTRO_S
    return out, round(total, 3)


def visual_key(v: dict) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def keyframes(tl: list[dict], total: float) -> list[dict]:
    """One keyframe per run of sentences with the same visual: shown from slightly before its first sentence."""
    out = []
    for e in tl:
        key = visual_key(e["visual"])
        if out and out[-1]["key"] == key:
            continue
        at = 0.0 if not out else max(out[-1]["at"] + 0.5, e["start"] - PRE_S)
        out.append({"n": len(out) + 1, "key": key, "visual": e["visual"], "at": round(at, 3)})
    for i, k in enumerate(out):
        k["until"] = out[i + 1]["at"] if i + 1 < len(out) else total
    return out


def split_cue(text: str, max_chars: int) -> list[str]:
    """Split a sentence into caption cues of at most max_chars, at punctuation first, then at the middle word."""
    if len(text) <= max_chars:
        return [text]
    parts = re.split(r"(?<=[,:;—])\s+", text)
    chunks, cur = [], ""
    for p in parts:
        if cur and len(cur) + 1 + len(p) > max_chars:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur} {p}".strip()
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        if len(c) <= max_chars:
            out.append(c)
            continue
        words = c.split()
        best = None
        for i in range(1, len(words)):
            a = " ".join(words[:i])
            if best is None or abs(len(a) - len(c) / 2) < abs(len(best[0]) - len(c) / 2):
                best = (a, " ".join(words[i:]))
        out += split_cue(best[0], max_chars) + split_cue(best[1], max_chars)
    return out


def cues(tl: list[dict], aspect: str, total: float) -> list[list]:
    """Caption cues [start, end, text] for one cut: each sentence split per aspect, timed by character share."""
    out = []
    for e in tl:
        chunks = split_cue(e["text"], CUE_CHARS[aspect])
        span = e["end"] - e["start"]
        weights = [len(c) for c in chunks]
        a = e["start"]
        for c, w in zip(chunks, weights):
            d = span * w / sum(weights)
            out.append([round(a, 3), round(a + d, 3), c])
            a += d
    for i in range(len(out)):
        nxt = out[i + 1][0] if i + 1 < len(out) else total
        out[i][1] = round(min(out[i][1] + CUE_HOLD_S, nxt - 0.04), 3)
    return out


def chapters(tl: list[dict]) -> list[tuple[float, str]]:
    """(start, title) per scene of the cut (consecutive scenes with one title merge); the first starts at 0."""
    out, prev = [], None
    for e in tl:
        if e["scene"] != prev:
            if not out or out[-1][1] != e["chapter"]:
                out.append((0.0 if not out else max(0.0, e["start"] - PRE_S), e["chapter"]))
            prev = e["scene"]
    return out


def check_cut(name: str, cut: dict, total: float, chaps: list[tuple[float, str]] | None) -> list[str]:
    problems = []
    if cut.get("max_s") and total > cut["max_s"]:
        problems.append(f"cut {name}: {total:.1f}s is longer than max_s {cut['max_s']}")
    if cut.get("min_s") and total < cut["min_s"]:
        problems.append(f"cut {name}: {total:.1f}s is shorter than min_s {cut['min_s']}")
    if chaps is not None:
        if len(chaps) < 3:
            problems.append(f"cut {name}: YouTube chapters need 3 or more (has {len(chaps)})")
        ends = [c[0] for c in chaps[1:]] + [total]
        for (start, title), end in zip(chaps, ends):
            if end - start < 10:
                problems.append(f"cut {name}: chapter '{title}' is {end - start:.1f}s (YouTube needs 10s+)")
    return problems


def ts(sec: float, sep: str) -> str:
    ms = max(0, int(round(sec * 1000)))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def chapter_stamp(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}"


def no_break(text: str) -> str:
    return re.sub(r"(?<=\w)-(?=\w)", "‑", text)


def srt(cs: list[list]) -> str:
    lines = []
    for i, (a, b, t) in enumerate(cs, 1):
        lines += [str(i), f"{ts(a, ',')} --> {ts(b, ',')}", t, ""]
    return "\n".join(lines)


def vtt(cs: list[list]) -> str:
    lines = ["WEBVTT", ""]
    for a, b, t in cs:
        lines += [f"{ts(a, '.')} --> {ts(b, '.')}", t, ""]
    return "\n".join(lines)


def ass(cs: list[list], aspect: str, font: str = "IBM Plex Sans") -> str:
    """Burned captions as ASS at the real frame size: white on a soft slate box (colours are &HAABBGGRR), per-aspect
    size and band."""
    w, h = ASPECTS[aspect]
    lay = LAYOUT[aspect]
    ml, mr = int(lay["side"][0] * w), int(lay["side"][1] * w)
    mv = int(lay["cap_margin"] * h)

    def t(sec):
        cs_ = max(0, int(round(sec * 100)))
        hh, cs_ = divmod(cs_, 360000)
        mm, cs_ = divmod(cs_, 6000)
        ss, cs_ = divmod(cs_, 100)
        return f"{hh}:{mm:02d}:{ss:02d}.{cs_:02d}"

    head = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "WrapStyle: 0",
        "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        f"Style: Cap,{font},{lay['cap_px']},&H00FFFFFF,&H00FFFFFF,&H282B2016,&H282B2016,0,0,0,0,100,100,0,0,3,"
        f"{max(8, lay['cap_px'] // 4)},0,2,{ml},{mr},{mv},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    body = [f"Dialogue: 0,{t(a)},{t(b)},Cap,,0,0,0,,{no_break(x).replace(chr(10), ' ')}" for a, b, x in cs]
    return "\n".join(head + body) + "\n"
