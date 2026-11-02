"""Build one architecture episode (AA-1021): every cut, the blog images, the 5-layer gate log. Any gate hit fails.

  tools/uat/venv/bin/python -I tools/uat/arch/make_episode.py <episode.json> --out <dir>
      [--work DIR] [--private DIR] [--cuts master,short] [--diagrams DIR] [--no-ngram]

  in : <episode.json> (scene.py format; kept OUTSIDE git), the label profile + deny-list in --private
       (default: env ARCH_VIDEO_PRIVATE, else tools/uat/arch/private/; both gitignored), the diagrams in
       docs/architecture/diagrams/*.svg (internal, real names; anonymized here through the profile).
  out: <out>/<slug>/<slug>_<cut>.mp4 + .srt + .vtt + .description.txt, blog/<slug>.md + blog/images/*.png,
       and beside it <out>/<slug>-gate/: gate-log.md + gate-log.json (counts only, no script text) and REVIEW.md
       (layer 5 checklist); that folder is for the team, never published, and stays out of the layer 4 scan.
  work: <work>/<slug>/ (stage pages, 2x keyframes, DOM dumps, OCR frames); default <out>/../work.
  exit: 0 = built, gate layers 1-4 PASS (layer 5 is the human review) | 1 = gate FAIL | 2 = scene / duration error.

Order: layer 1 on every authored string (before any TTS) -> anonymize diagrams (+ layer 1 on their labels) -> TTS ->
per-cut timelines and length checks -> per-aspect keyframe capture with the layer 2 DOM check -> MP4s -> layer 2
audit, layer 3 OCR, layer 4 artifacts -> logs. Cost $0: local Kokoro, Chromium, ffmpeg, tesseract; no upload.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gate  # noqa: E402
import labels  # noqa: E402
import page  # noqa: E402
import scene  # noqa: E402
import tts_arch  # noqa: E402
import video  # noqa: E402

REPO = HERE.parents[2]


def opt(argv: list[str], name: str, default=None):
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return default


def cache_dir() -> Path:
    return Path(os.environ.get("ARCH_VIDEO_CACHE") or HERE / ".cache")


def fail(msg: str, code: int) -> int:
    print(f"STOP: {msg}", file=sys.stderr)
    return code


def description(meta: dict, cut: str, chaps: list | None) -> str:
    cfg = meta["cuts"][cut]
    lines = [meta["title"], "", cfg.get("description") or meta.get("description", "")]
    if chaps:
        lines += ["", "Chapters"] + [f"{scene.chapter_stamp(s)} {t}" for s, t in chaps]
    lines += ["", "Narration: synthetic voice."]
    tags = cfg.get("hashtags") or meta.get("hashtags") or []
    if tags:
        lines += ["", " ".join(tags)]
    return "\n".join(lines).strip() + "\n"


REVIEW = """# Review checklist (gate layer 5)

Gate layers 1-4 passed for this build (see gate-log.md). Layer 5 is human and is not automated.

## A. Independent review agent (reads the episode script and the blog post; never the internal docs alone)

- [ ] No company, product, brand, person, reseller, vendor-of-models or niche data-vendor name; no domain, account,
      region, resource or issue identifier; no internal coined term.
- [ ] Nothing planned is shown or said as live: planned items use "designed to" wording or are left out.
- [ ] No cost, price, budget figure, credit, cap value or count that fingerprints the system.
- [ ] No weak point, incident, outage, refusal case, open gap or dated event.
- [ ] No sentence that reads like a line from the public repos (searchability); the n-gram layer is a floor, not proof.
- [ ] The combination of facts in this episode does not single out the company more than the series already does.

## B. Tech lead (watches every cut before upload)

- [ ] Master 16:9: voice natural enough, both voices alternate as intended, captions in sync and readable.
- [ ] Short 9:16: nothing important under the platform buttons (bottom ~20%, right ~15%); length under 60 s.
- [ ] X clip: under 2:20; captions burned.
- [ ] LinkedIn clip: 60-120 s; captions burned; SRT attached on upload.
- [ ] Description files: generic, "Narration: synthetic voice", no links to company domains or repos.
- [ ] Blog post: same rules; images are the public renders only.
- [ ] Posting account matches the "engineering notes" framing (no employer link on the post itself).

Sign-off: review agent ______  tech lead ______  date ______
"""


def main(argv: list[str]) -> int:
    argv = list(argv)
    out_root = Path(opt(argv, "--out") or "").resolve()
    work_root = opt(argv, "--work")
    priv = gate.private_dir(opt(argv, "--private"))
    only = opt(argv, "--cuts")
    diag_dir = Path(opt(argv, "--diagrams") or REPO / "docs" / "architecture" / "diagrams").resolve()
    no_ngram = "--no-ngram" in argv
    argv = [a for a in argv if a != "--no-ngram"]
    if len(argv) != 1 or not str(out_root):
        print(__doc__)
        return 2
    ep_path = Path(argv[0]).resolve()
    data = json.loads(ep_path.read_text(encoding="utf-8"))
    try:
        meta, sents = scene.load(data)
    except scene.SceneError as e:
        return fail(str(e), 2)
    slug = meta["slug"]
    out = out_root / slug
    gate_dir = out_root / f"{slug}-gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    work = (Path(work_root).resolve() if work_root else out_root.parent / "work") / slug
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    cuts = [c for c in meta["cuts"] if not only or c in only.split(",")]
    log: dict = {"slug": slug, "date": dt.date.today().isoformat(), "layers": {}, "cuts": {}}

    patterns = gate.load_patterns(priv)
    profile = labels.load_profile(priv / "labels.public.json")
    workspace = gate.default_workspace()
    allow = gate.load_allow(priv)

    # Layer 1: every authored string, the blog post and the public labels, before anything is rendered.
    texts = scene.all_texts(data, sents)
    for name, cfg in meta["cuts"].items():
        if cfg.get("description"):
            texts[f"cut:{name}:description"] = cfg["description"]
    blog = data.get("blog") or {}
    blog_src = (ep_path.parent / blog["file"]) if blog.get("file") else None
    if blog_src:
        texts["blog"] = blog_src.read_text(encoding="utf-8")
    texts["series_tag"] = meta.get("series_tag", "")
    label_texts = {f"label:{k}": v for k, v in profile["map"].items() if v}
    hits = gate.check_texts(texts, patterns, workspace, allow, ngram=not no_ngram)
    hits += gate.check_texts(label_texts, patterns, None, allow, ngram=False)
    if not no_ngram:
        hits += gate.label_set_scan(list(label_texts.values()), workspace)
    svgs = {}
    for key, stem in meta.get("diagrams", {}).items():
        svg = labels.anonymize_svg((diag_dir / f"{stem}.svg").read_text(encoding="utf-8"), profile)
        svgs[key] = svg
        visible = " | ".join(re.findall(r"<text[^>]*>([^<]*)</text>", svg))
        hits += gate.scan_text(visible, f"diagram:{key}", patterns)
    log["layers"]["L1"] = {"status": "FAIL" if hits else "PASS", "hits": len(hits), "by_category": gate.counts(hits),
                           "strings": len(texts) + len(label_texts), "ngram": "off" if no_ngram else
                           f"{gate.NGRAM_N}-word phrases + internal-looking tokens vs public repos"}
    if hits:
        gate.report(hits, "L1 text")
        write_logs(gate_dir, log)
        return 1
    print(f"L1 text: PASS ({len(texts)} strings, {len(label_texts)} labels, {len(svgs)} diagrams)")

    # Narration.
    used = [s for s in sents if s.cuts & set(cuts)]
    clips = tts_arch.synth([(s.id, s.text, s.voice) for s in used], cache_dir() / "tts")
    durations = {k: v["dur"] for k, v in clips.items()}

    # Timelines and length rules per cut.
    plans, problems = {}, []
    for c in cuts:
        cfg = meta["cuts"][c]
        tl, total = scene.timeline(scene.cut_sentences(sents, c), durations)
        chaps = scene.chapters(tl) if cfg.get("chapters") else None
        problems += scene.check_cut(c, cfg, total, chaps)
        plans[c] = {"cfg": cfg, "tl": tl, "total": total, "chaps": chaps, "kfs": scene.keyframes(tl, total)}
    for c, p in plans.items():
        print(f"cut {c}: {p['total']:.1f}s, {len(p['tl'])} sentences, {len(p['kfs'])} keyframes")
    if problems:
        return fail("; ".join(problems), 2)

    # Keyframes per aspect (layer 2 runs inside capture.cjs before each shot).
    pat_json = work / "patterns.json"
    pat_json.write_text(json.dumps(gate.patterns_json(patterns)), encoding="utf-8")
    font = cache_dir() / "fonts" / "IBMPlexSans-VF.ttf"
    if not font.exists():
        print("WARNING: IBM Plex Sans missing (run setup.sh); falling back to Liberation Sans", file=sys.stderr)
    blog_imgs = blog.get("images") or {}
    aspects = sorted({plans[c]["cfg"]["aspect"] for c in cuts} | ({"16:9"} if blog_imgs else set()))
    shots: dict[tuple[str, str], Path] = {}
    meta_page = {"title": meta.get("series", ""), "series_tag": meta.get("series_tag", "")}
    for asp in aspects:
        adir = work / f"kf-{asp.replace(':', 'x')}"
        if adir.exists():
            shutil.rmtree(adir)
        adir.mkdir(parents=True)
        uniq: list[dict] = []
        for c in cuts:
            if plans[c]["cfg"]["aspect"] != asp:
                continue
            for k in plans[c]["kfs"]:
                if k["key"] not in [u["key"] for u in uniq]:
                    uniq.append({"key": k["key"], "visual": k["visual"]})
        if asp == "16:9":
            for v in blog_imgs.values():
                key = scene.visual_key(v)
                if key not in [u["key"] for u in uniq]:
                    uniq.append({"key": key, "visual": v})
        for i, u in enumerate(uniq, 1):
            u["n"] = i
        html_path = page.write(adir / "stage.html", meta_page, asp, svgs, font)
        kf_json = adir / "keyframes.json"
        kf_json.write_text(json.dumps([{"n": u["n"], "visual": u["visual"]} for u in uniq]), encoding="utf-8")
        rc = subprocess.run(["node", str(HERE / "capture.cjs"), str(html_path), str(kf_json), str(adir), asp,
                             str(pat_json)]).returncode
        if rc != 0:
            log["layers"]["L2"] = {"status": "FAIL", "aspect": asp, "exit": rc}
            write_logs(gate_dir, log)
            return fail(f"capture {asp} exited {rc} (4 = DOM gate hit, 5 = network request)", 1)
        for u in uniq:
            src = adir / f"kf-{u['n']:02d}.png"
            shots[(asp, u["key"])] = video.scale_keyframe(src, adir / f"kf-{u['n']:02d}.final.png", asp)

    # MP4 per cut.
    fonts_dir = font.parent if font.exists() else None
    title = f"{meta.get('series', '')} - {meta['title']}".strip(" -")
    for c in cuts:
        p = plans[c]
        asp = p["cfg"]["aspect"]
        base = out / f"{slug}_{c}"
        cs = scene.cues(p["tl"], asp, p["total"])
        Path(f"{base}.srt").write_text(scene.srt(cs), encoding="utf-8")
        Path(f"{base}.vtt").write_text(scene.vtt(cs), encoding="utf-8")
        cwork = work / f"cut-{c}"
        cwork.mkdir(exist_ok=True)
        ass_path = cwork / "captions.ass"
        ass_path.write_text(scene.ass(cs, asp, "IBM Plex Sans" if fonts_dir else "Liberation Sans"), encoding="utf-8")
        wav = video.narration(p["tl"], clips, p["total"], cwork / "narration.wav")
        chap_file = video.ffmetadata(p["chaps"], p["total"], cwork / "chapters.txt") if p["chaps"] else None
        frames = [(shots[(asp, k["key"])], k["at"], k["until"]) for k in p["kfs"]]
        video.run(video.video_cmd(frames, wav, ass_path, fonts_dir, p["total"], Path(f"{base}.mp4"), title, chap_file))
        Path(f"{base}.description.txt").write_text(description(meta, c, p["chaps"]), encoding="utf-8")
        real = video.probe_duration(Path(f"{base}.mp4"))
        log["cuts"][c] = {"aspect": asp, "seconds": round(real, 1), "keyframes": len(p["kfs"]), "cues": len(cs),
                          "chapters": len(p["chaps"] or [])}
        print(f"built {base.name}.mp4 {real:.1f}s")

    if blog_src:
        bdir = out / "blog"
        (bdir / "images").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(blog_src, bdir / f"{slug}.md")
        for name, v in blog_imgs.items():
            shutil.copyfile(shots[("16:9", scene.visual_key(v))], bdir / "images" / name)

    # Layer 2 audit (the saved DOM dumps), layer 3 OCR, layer 4 artifacts.
    dom_hits, dumps = [], sorted(work.glob("kf-*/dom/*.json"))
    for d in dumps:
        dom_hits += gate.scan_text(gate.dom_dump_texts(json.loads(d.read_text(encoding="utf-8"))),
                                   f"{d.parent.parent.name}/{d.name}", patterns, layer="L2")
    log["layers"]["L2"] = {"status": "FAIL" if dom_hits else "PASS", "hits": len(dom_hits),
                           "by_category": gate.counts(dom_hits), "frames_checked_before_capture": len(dumps)}
    images = sorted(work.glob("kf-*/kf-*.final.png"))
    for c in cuts:
        images += video.sample_frames(out / f"{slug}_{c}.mp4", work / f"cut-{c}" / "ocr-frames")
    ocr_hits, ocr_status = gate.check_ocr(images, patterns, gate.literal_terms(priv))
    log["layers"]["L3"] = {"status": ("SKIPPED" if ocr_status.startswith("SKIPPED") else
                                      ("FAIL" if ocr_hits else "PASS")), "hits": len(ocr_hits),
                           "by_category": gate.counts(ocr_hits), "images": len(images), "note": ocr_status}
    (gate_dir / "REVIEW.md").write_text(REVIEW, encoding="utf-8")
    log["layers"]["L5"] = {"status": "PENDING", "note": "review agent + tech lead, checklist REVIEW.md"}
    art_hits = gate.check_artifacts(out, patterns)
    log["layers"]["L4"] = {"status": "FAIL" if art_hits else "PASS", "hits": len(art_hits),
                           "by_category": gate.counts(art_hits), "files": sum(1 for p in out.rglob("*") if p.is_file())}
    log["tools"] = tool_versions()
    write_logs(gate_dir, log)
    all_hits = dom_hits + ocr_hits + art_hits
    rc = gate.report(all_hits, "L2-L4")
    for name in ("L1", "L2", "L3", "L4", "L5"):
        layer = log["layers"].get(name, {})
        print(f"{name}: {layer.get('status')} {layer.get('note', '')}".rstrip())
    return rc


def tool_versions() -> dict:
    tess = gate.tesseract_cmd()
    vers = {"ffmpeg": gate.tool_version(["ffmpeg", "-version"]),
            "tesseract": gate.tool_version(tess[0] + ["--version"], tess[1]) if tess else "not installed",
            "node": gate.tool_version(["node", "--version"])}
    try:
        from importlib.metadata import version

        vers["kokoro-onnx"] = version("kokoro-onnx")
    except Exception:  # noqa: BLE001 - informational only
        vers["kokoro-onnx"] = "unknown"
    pw = HERE.parent / "node_modules" / "playwright" / "package.json"
    if pw.exists():
        vers["playwright"] = json.loads(pw.read_text())["version"]
    return vers


def write_logs(out: Path, log: dict) -> None:
    (out / "gate-log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    lines = [f"# Gate log: {log['slug']} ({log['date']})", "", "| Layer | Status | Hits | Notes |", "|---|---|---|---|"]
    names = {"L1": "1 text + n-gram", "L2": "2 DOM before capture", "L3": "3 OCR on frames",
             "L4": "4 artifacts + metadata",
             "L5": "5 human review"}
    for k in ("L1", "L2", "L3", "L4", "L5"):
        layer = log["layers"].get(k)
        if not layer:
            lines.append(f"| {names[k]} | not run | - | |")
            continue
        extra = {kk: vv for kk, vv in layer.items() if kk not in ("status", "hits", "by_category")}
        lines.append(f"| {names[k]} | {layer['status']} | {layer.get('hits', '-')} | "
                     f"{'; '.join(f'{a}: {b}' for a, b in extra.items())} |")
    if log.get("cuts"):
        lines += ["", "| Cut | Aspect | Seconds | Keyframes | Cues | Chapters |", "|---|---|---|---|---|---|"]
        for c, v in log["cuts"].items():
            lines.append(f"| {c} | {v['aspect']} | {v['seconds']} | {v['keyframes']} | {v['cues']} | {v['chapters']} |")
    if log.get("tools"):
        lines += ["", "Tools: " + "; ".join(f"{k} {v}" for k, v in log["tools"].items())]
    (out / "gate-log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
