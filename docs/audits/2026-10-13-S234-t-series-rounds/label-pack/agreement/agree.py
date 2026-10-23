#!/usr/bin/env python3
"""AA-783 — decode the export, build the label-page data, and compute human-vs-panel / human-vs-gate agreement.

Local, stdlib only (openpyxl only for `page --pack`). No DB, no LLM, no network.

  agree.py decode  RAW.txt            -o export.json      # ECS exec output -> export.json (gzip or plain; sha checked)
  agree.py page    export.json        -o page_data.json   # what the label page shows: pieces only, no key
                   [--pack ../S234-label-40.xlsx]         #   (pieces whose DB text changed since the panel get
                                                          #    the panel-era text/title/meta from the pack)
  agree.py report  export.json labels.json -o report.json [--md report.md]

labels.json (one labeller or several; the same keys as the admin Label API of AA-791, so the labels can be
POSTed to content_piece_label afterwards without mapping):
  {"schema": "aa783-labels/1", "labeller": "nghiep",
   "labels": [{"piece_id": "...", "label": "as_is|light|heavy|reject",
               "defects": {"fact": "none|light|heavy", "voice": "...", "format": "...", "ai_phrasing": "..."},
               "minutes_to_fix": 5, "worst_sentences": "...", "reason": "...",
               "content_sha256": "<sha of the text that was shown>", "labelled_by": "nghiep"}]}
A bare list of label objects is accepted too; "verdict" is read as "label", "minutes" as "minutes_to_fix".
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

VERDICTS = ("as_is", "light", "heavy", "reject")
GOOD = ("as_is", "light")  # "light edit or better" = the commercial bar
DEFECT_CLASSES = ("fact", "voice", "format", "ai_phrasing")
LEVELS = ("none", "light", "heavy")
LENSES = ("editor", "brand_lead", "channel", "client")

# Gate -> the human defect column it is meant to catch (report 12 §1.2 "What it checks"; AA-800/AA-819 gates).
# A gate missing here is reported under "other" (its fires are still counted, never dropped).
GATE_COLUMN = {
    # invented / unsupported fact, out-of-scope place, promise
    "F1_grounding": "fact", "F9_cta_fact": "fact", "F17_trip_fact": "fact", "F18_rarity": "fact",
    "F12_scope": "fact", "promises_an_option": "fact", "F2_platform_truth": "fact", "F19_authenticity": "fact",
    # brand voice (incl. brand-pack/prompt text leaking into copy and the configured CTA)
    "F9_brand_style": "voice", "F9_brand_voice": "voice", "F2_brand_forbidden": "voice", "F11_brand_name": "voice",
    "F13_leak": "voice", "F6_cta_present": "voice",
    # channel / SEO / format
    "F0_complete": "format", "F4_extreme_length": "format", "F4_seo_surface": "format",
    "F14_social_shape": "format", "F14_first_line": "format", "F16_faq": "format", "F7_faq_dedup": "format",
    "F7_faq_autofix": "format", "F13_hygiene": "format", "F13_repeat": "format",
    "F3_structural_variance": "format", "F5_atom_density": "format", "F8_framework": "format",
    "F10_cannibalization_cross_tenant": "format",
    # AI phrasing / stock lines
    "F15_voice": "ai_phrasing", "F15_voice_warn": "ai_phrasing", "F15_stock_cut": "ai_phrasing",
    "F2_banned_patterns": "ai_phrasing", "F2_superlatives": "ai_phrasing", "F2_style_warn": "ai_phrasing",
}
# Label definitions shown on the label page (EN + VI, from ../HUONG-DAN-CHAM.md, the criteria Nghiệp agreed to in S234).
DEFINITIONS = {
    "label": {
        "as_is": {"en": "Publish verbatim: no false fact, on brand voice, meets the channel standard. A weak sentence that is not worth editing is fine.",
                  "vi": "Đăng nguyên văn được: không sai sự thật, đúng giọng brand, đúng chuẩn kênh."},
        "light": {"en": "Edit in 10 minutes or less, 3 sentences or fewer, no fact research.",
                  "vi": "Sửa ≤ 10 phút, ≤ 3 câu, không cần tra cứu thêm."},
        "heavy": {"en": "More than a light edit (rewrite a paragraph, research a fact, restructure), but worth keeping.",
                  "vi": "Sửa nhiều hơn mức light (viết lại đoạn, tra fact, đổi cấu trúc) nhưng bài vẫn đáng giữ."},
        "reject": {"en": "Discard: rewriting from scratch is faster than fixing.",
                   "vi": "Bỏ: viết lại từ đầu nhanh hơn sửa."},
        "tie_rule": {"en": "Unsure between two labels: pick the stricter one.", "vi": "Phân vân giữa 2 nhãn: chọn nhãn khắt hơn."},
    },
    "defects": {
        "fact": {"en": "Says something about the trip that is not in SOURCE (schedule, times, services, 'included' when SOURCE says optional, pace), a number not in SOURCE, a place outside the piece's scope, or an overstatement. Correct, common background knowledge about a place is NOT a defect.",
                 "vi": "Nói điều không có trong SOURCE về chuyến đi, con số không có trong SOURCE, địa danh ngoài phạm vi, hoặc nói quá. Kiến thức nền đúng, phổ biến KHÔNG tính lỗi."},
        "voice": {"en": "Does not sound like this brand (compare BRAND): wrong audience, wrong energy, a forbidden word, a sentence copied from the brand pack/style guide, a CTA that is not the configured line.",
                  "vi": "Không giống cách brand nói: sai đối tượng, sai năng lượng, từ cấm, chép câu từ brand pack, CTA sai câu cấu hình."},
        "format": {"en": "LinkedIn: under 120 or over 250 words, more than 3 hashtags, weak/long first line, misspelt hashtag. Blog: title/meta off scope or cut, FAQ under 3 or off-topic answers, writer-instruction headings, repeated or broken sentences, CTA twice.",
                   "vi": "LinkedIn: < 120 hoặc > 250 từ, > 3 hashtag, dòng đầu dở, hashtag sai. Blog: title/meta sai phạm vi, FAQ < 3 câu hoặc lạc đề, heading kiểu lệnh, câu lặp/cụt, CTA lặp."},
        "ai_phrasing": {"en": "Reads as machine-written: dense 'not X, but Y' frames, stock lines ('worth sitting with'), generic opener, summary closer, many em dashes.",
                        "vi": "Đọc là biết máy viết: cặp 'không phải X mà là Y' dày, câu sáo, mở bài chung chung, kết tóm tắt, nhiều gạch ngang dài."},
        "levels": {"none": {"en": "none", "vi": "không"},
                   "light": {"en": "present but fixed in seconds", "vi": "có nhưng sửa trong vài giây"},
                   "heavy": {"en": "the main reason the piece cannot be published verbatim", "vi": "lý do chính khiến bài không đăng nguyên văn được"}},
    },
    "minutes_to_fix": {"en": "Minutes to bring the piece to publishable (0 if as_is; empty if reject).",
                       "vi": "Số phút để đưa bài tới mức đăng được (0 nếu as_is; để trống nếu reject)."},
    "worst_sentences": {"en": "Paste the 1-3 worst sentences verbatim.", "vi": "Dán nguyên văn 1–3 câu tệ nhất."},
    "how": {"en": "Judge as the owner of the tour company about to publish this under its brand. Judge each piece on its own. Ignore images, HTML formatting, exact blog length and technical SEO.",
            "vi": "Chấm như chủ công ty tour sắp đăng bài dưới thương hiệu của mình. Chấm từng bài độc lập. Bỏ qua ảnh, HTML, độ dài blog chính xác, SEO kỹ thuật."},
}

# Decision thresholds (config, safe defaults): the panel may stand in for a human on the verdict when both the
# quadratic-weighted kappa and the binary (light-or-better) kappa reach this value (Landis-Koch "substantial").
STAND_IN_KAPPA = 0.60
LIGHT_BAR = 0.60  # the current "light >= 60%" commercial bar (S233/S234), re-expressed on the human scale
BOOT = 2000
SEED = 783


# ----------------------------------------------------------------------------------------------- statistics
def cohen_kappa(a: list, b: list, cats, weights: str | None = None) -> float | None:
    """Cohen's kappa; weights=None (unweighted) or "quadratic" (ordinal, cats in order)."""
    n = len(a)
    if n == 0:
        return None
    k = len(cats)
    idx = {c: i for i, c in enumerate(cats)}

    def w(i, j):
        if weights == "quadratic":
            return ((i - j) ** 2) / ((k - 1) ** 2) if k > 1 else 0.0
        return 0.0 if i == j else 1.0

    obs = Counter((idx[x], idx[y]) for x, y in zip(a, b))
    pa, pb = Counter(idx[x] for x in a), Counter(idx[y] for y in b)
    do = sum(w(i, j) * c for (i, j), c in obs.items()) / n
    de = sum(w(i, j) * pa[i] * pb[j] for i in range(k) for j in range(k)) / (n * n)
    if de == 0:
        return 1.0 if do == 0 else None  # no expected disagreement: both raters constant
    return 1 - do / de


def fleiss_kappa(table: list[list[str]], cats) -> float | None:
    """Fleiss' kappa for items each rated by the same number of raters."""
    if not table:
        return None
    m = len(table[0])
    n = len(table)
    counts = [[row.count(c) for c in cats] for row in table]
    p_j = [sum(r[j] for r in counts) / (n * m) for j in range(len(cats))]
    p_i = [(sum(x * x for x in r) - m) / (m * (m - 1)) for r in counts]
    pbar, pe = sum(p_i) / n, sum(p * p for p in p_j)
    return None if pe == 1 else (pbar - pe) / (1 - pe)


def spearman(x: list[float], y: list[float]) -> float | None:
    if len(x) < 3:
        return None

    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for t in range(i, j + 1):
                r[order[t]] = (i + j) / 2 + 1
            i = j + 1
        return r

    rx, ry = ranks(x), ranks(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return None if den == 0 else num / den


def boot_ci(pairs: list, fn, n=BOOT, seed=SEED) -> list | None:
    """95% percentile bootstrap CI of fn(pairs) over resampled pairs."""
    if len(pairs) < 5:
        return None
    rnd = random.Random(seed)
    vals = []
    for _ in range(n):
        s = [pairs[rnd.randrange(len(pairs))] for _ in pairs]
        v = fn(s)
        if v is not None:
            vals.append(v)
    if len(vals) < n * 0.5:
        return None
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 3), round(vals[int(0.975 * len(vals)) - 1], 3)]


def r3(v):
    return None if v is None else round(v, 3)


def band(k):
    if k is None:
        return "n/a"
    return ("poor" if k < 0 else "slight" if k < 0.2 else "fair" if k < 0.4 else "moderate" if k < 0.6
            else "substantial" if k < 0.8 else "almost perfect")


def verdict_block(pairs: list[tuple[str, str]]) -> dict:
    """pairs = (human, other). Exact + weighted + binary agreement with CIs and the confusion matrix."""
    if not pairs:
        return {"n": 0}
    h, o = [p[0] for p in pairs], [p[1] for p in pairs]
    hb, ob = [x in GOOD for x in h], [x in GOOD for x in o]
    ku = cohen_kappa(h, o, VERDICTS)
    kq = cohen_kappa(h, o, VERDICTS, "quadratic")
    kb = cohen_kappa(hb, ob, (True, False))
    return {
        "n": len(pairs),
        "exact_agreement": r3(sum(a == b for a, b in pairs) / len(pairs)),
        "kappa": r3(ku), "kappa_ci95": boot_ci(pairs, lambda s: cohen_kappa([x for x, _ in s], [y for _, y in s], VERDICTS)),
        "kappa_quadratic": r3(kq),
        "kappa_quadratic_ci95": boot_ci(pairs, lambda s: cohen_kappa([x for x, _ in s], [y for _, y in s], VERDICTS, "quadratic")),
        "binary_agreement": r3(sum(a == b for a, b in zip(hb, ob)) / len(pairs)),
        "kappa_binary": r3(kb),
        "kappa_binary_ci95": boot_ci(pairs, lambda s: cohen_kappa([x in GOOD for x, _ in s], [y in GOOD for _, y in s], (True, False))),
        "band_quadratic": band(kq), "band_binary": band(kb),
        "other_stricter": sum(VERDICTS.index(b) > VERDICTS.index(a) for a, b in pairs),
        "other_more_lenient": sum(VERDICTS.index(b) < VERDICTS.index(a) for a, b in pairs),
        "confusion_human_rows": {a: {b: sum(1 for x, y in pairs if x == a and y == b) for b in VERDICTS} for a in VERDICTS},
    }


def prf(tp, fp, fn) -> dict:
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": r3(tp / (tp + fp)) if tp + fp else None, "recall": r3(tp / (tp + fn)) if tp + fn else None}


# ----------------------------------------------------------------------------------------------- io
def decode_raw(text: str) -> dict:
    if "AA783-BEGIN" not in text or "AA783-END" not in text:
        raise SystemExit("markers AA783-BEGIN / AA783-END not found")
    body = text.split("AA783-BEGIN", 1)[1].split("AA783-END", 1)[0].strip()
    if body.startswith("{"):
        doc = json.loads(body)
    else:
        doc = json.loads(gzip.decompress(base64.b64decode("".join(body.split()))).decode("utf-8"))
    if "AA783-SHA256 " in text:
        want = text.split("AA783-SHA256 ", 1)[1].split()[0]
        got = hashlib.sha256(json.dumps(doc, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()
        if want != got:
            raise SystemExit(f"sha256 mismatch: printed {want}, decoded {got} (output truncated or mangled?)")
    return doc


def load_labels(path: Path) -> list[dict]:
    raw = json.loads(path.read_text())
    items = raw.get("labels", []) if isinstance(raw, dict) else raw
    default_by = raw.get("labeller") if isinstance(raw, dict) else None
    out = []
    for x in items:
        lab = x.get("label") or x.get("verdict")
        if lab not in VERDICTS:
            raise SystemExit(f"label {lab!r} for {x.get('piece_id')} is not one of {VERDICTS}")
        d = x.get("defects") or {}
        bad = {k: v for k, v in d.items() if k not in DEFECT_CLASSES or v not in LEVELS}
        if bad:
            raise SystemExit(f"bad defects for {x.get('piece_id')}: {bad}")
        out.append({"piece_id": x["piece_id"], "by": x.get("labelled_by") or default_by or "human", "label": lab,
                    "defects": {c: d.get(c, "none") for c in DEFECT_CLASSES},
                    "minutes": x.get("minutes_to_fix", x.get("minutes")), "content_sha256": x.get("content_sha256")})
    return out


# ----------------------------------------------------------------------------------------------- page
def cmd_page(a) -> int:
    doc = json.loads(Path(a.export).read_text())
    pack = {}
    if a.pack:
        import openpyxl
        wb = openpyxl.load_workbook(a.pack, read_only=True)
        for r in wb["Label"].iter_rows(min_row=2, values_only=True):
            if r[1]:
                pack[r[1]] = {"title": r[4], "meta": r[5], "text": r[6] or ""}
    out = []
    for p in doc["pieces"]:
        q = dict(p)
        q["text_source"] = "db"
        if doc["key"][p["piece_id"]].get("text_changed_since_panel"):
            if p["piece_id"] not in pack:
                raise SystemExit(f"#{p['n']} text changed since the panel; pass --pack to show the panel-era text")
            q.update(pack[p["piece_id"]])
            q["words"] = len(q["text"].split())
            q["content_sha256"] = hashlib.sha256(q["text"].encode("utf-8")).hexdigest()
            q["text_source"] = "pack"
        out.append(q)
    page = {"schema": "aa783-page/1", "set": doc["set"], "generated_at": doc["generated_at"],
            "choices": {"label": list(VERDICTS), "defect_classes": list(DEFECT_CLASSES), "defect_levels": list(LEVELS)},
            "definitions": DEFINITIONS, "pieces": out}
    leak = json.dumps(page)
    for word in ('"votes"', '"majority"', '"held_reason"', '"gate"', '"panel"', '"final_failed"'):
        assert word not in leak, f"key leaked into page data: {word}"
    Path(a.out).write_text(json.dumps(page, ensure_ascii=False, indent=1) + "\n")
    print(f"page data: {len(out)} pieces, {sum(q['text_source'] == 'pack' for q in out)} from the pack -> {a.out}")
    return 0


# ----------------------------------------------------------------------------------------------- report
def cmd_report(a) -> int:
    doc = json.loads(Path(a.export).read_text())
    key, pieces = doc["key"], {p["piece_id"]: p for p in doc["pieces"]}
    labels = load_labels(Path(a.labels))
    unknown = [l["piece_id"] for l in labels if l["piece_id"] not in key]
    if unknown:
        raise SystemExit(f"labels for pieces not in the export: {unknown[:5]}")
    by_labeller = defaultdict(dict)
    for l in labels:
        by_labeller[l["by"]][l["piece_id"]] = l
    primary_name = a.labeller or max(by_labeller, key=lambda k: len(by_labeller[k]))
    human = by_labeller[primary_name]
    ids = [pid for pid in pieces if pid in human]
    rep: dict = {"schema": "aa783-report/1", "set": doc["set"], "labeller": primary_name,
                 "n_labelled": len(ids), "n_export": len(pieces), "thresholds": {
                     "stand_in_kappa": STAND_IN_KAPPA, "light_bar": LIGHT_BAR}}
    stale = [pid for pid in ids if human[pid]["content_sha256"] and human[pid]["content_sha256"]
             not in (pieces[pid]["content_sha256"], (key[pid].get("panel") or {}).get("panel_text_sha256"))]
    rep["labels_on_unknown_text"] = stale

    def cell(pid):
        return f"{pieces[pid]['tenant_slug']}/{pieces[pid]['channel']}"

    # 1. light share, human vs panel vs gate
    def share(sel):
        sel = list(sel)
        if not sel:
            return None
        hs = [human[p]["label"] for p in sel]
        out = {"n": len(sel), "human_as_is": r3(hs.count("as_is") / len(sel)),
               "human_light_or_better": r3(sum(x in GOOD for x in hs) / len(sel)),
               "human_reject": r3(hs.count("reject") / len(sel)),
               "gate_approved": r3(sum(key[p]["gate"]["status"] == "approved" for p in sel) / len(sel))}
        pan = [key[p]["panel"]["majority"] for p in sel if key[p].get("panel")]
        if pan:
            out["panel_light_or_better"] = r3(sum(x in GOOD for x in pan) / len(pan))
            out["panel_as_is"] = r3(pan.count("as_is") / len(pan))
        mins = [human[p]["minutes"] for p in sel if isinstance(human[p]["minutes"], (int, float))]
        if mins:
            out["human_minutes_median"] = st.median(mins)
        return out

    rep["share"] = {"all": share(ids),
                    "by_channel": {c: share(p for p in ids if pieces[p]["channel"] == c) for c in ("blog", "linkedin")},
                    "by_cell": {c: share(p for p in ids if cell(p) == c) for c in sorted({cell(p) for p in ids})},
                    "by_gate_status": {s: share(p for p in ids if key[p]["gate"]["status"] == s) for s in ("approved", "held")}}
    s_all = rep["share"]["all"]
    if s_all and "panel_light_or_better" in s_all:
        bias = s_all["panel_light_or_better"] - s_all["human_light_or_better"]
        rep["light_bar"] = {"panel_minus_human_light_share": r3(bias),
                            "panel_bar_equivalent_to_human_bar": r3(min(1.0, max(0.0, LIGHT_BAR + bias))),
                            "note": "a panel light share of this value corresponds to a human light share of the "
                                    "LIGHT_BAR on this set (linear offset; n=40, read with the CIs)"}

    # 2. verdict agreement: human vs panel majority, vs each lens, panel internal
    with_panel = [p for p in ids if key[p].get("panel")]
    if with_panel:
        rep["verdict_vs_panel_majority"] = verdict_block([(human[p]["label"], key[p]["panel"]["majority"]) for p in with_panel])
        rep["verdict_vs_lens"] = {l: verdict_block([(human[p]["label"], key[p]["panel"]["lenses"][l]["verdict"])
                                                    for p in with_panel]) for l in LENSES}
        rep["panel_internal_fleiss_kappa"] = {
            "verdict": r3(fleiss_kappa([[key[p]["panel"]["lenses"][l]["verdict"] for l in LENSES] for p in with_panel], VERDICTS)),
            "binary": r3(fleiss_kappa([[key[p]["panel"]["lenses"][l]["verdict"] in GOOD for l in LENSES] for p in with_panel], (True, False)))}
        vb = rep["verdict_vs_panel_majority"]
        rep["panel_can_stand_in"] = bool((vb["kappa_quadratic"] or -1) >= STAND_IN_KAPPA and (vb["kappa_binary"] or -1) >= STAND_IN_KAPPA)
        # tie pieces: does the strict tie rule match the human?
        ties = [p for p in with_panel if key[p]["panel"]["tie"]]
        rep["tie_rule"] = {"n_ties": len(ties), "human_light_or_better_on_ties": sum(human[p]["label"] in GOOD for p in ties)}

    # 3. gate approve/hold vs human (should approve = light or better), and the panel on the same footing
    def approve_block(get):
        tp = sum(get(p) and human[p]["label"] in GOOD for p in ids)
        fp = sum(get(p) and human[p]["label"] not in GOOD for p in ids)
        fn = sum((not get(p)) and human[p]["label"] in GOOD for p in ids)
        tn = len(ids) - tp - fp - fn
        b = prf(tp, fp, fn)
        b.update({"tn": tn, "accuracy": r3((tp + tn) / len(ids)) if ids else None,
                  "kappa": r3(cohen_kappa([bool(get(p)) for p in ids], [human[p]["label"] in GOOD for p in ids], (True, False))),
                  "held_precision": r3(tn / (tn + fn)) if tn + fn else None})
        return b

    rep["gate_approval_vs_human"] = approve_block(lambda p: key[p]["gate"]["status"] == "approved")
    if with_panel and len(with_panel) == len(ids):
        rep["panel_approval_vs_human"] = approve_block(lambda p: key[p]["panel"]["majority"] in GOOD)

    # 4. per gate vs the human defect column it targets (final ledger, and any attempt)
    gates = sorted({g for p in ids for g in key[p]["gate"]["gates_ran"]} |
                   {g for p in ids for g in key[p]["gate"]["ever_failed"]})
    per_gate = {}
    for g in gates:
        col = GATE_COLUMN.get(g)
        ran = [p for p in ids if g in key[p]["gate"]["gates_ran"] or g in key[p]["gate"]["ever_failed"]]
        fin = {p for p in ran if any(f["gate"] == g for f in key[p]["gate"]["final_failed"])}
        ever = {p for p in ran if g in key[p]["gate"]["ever_failed"]}
        row = {"column": col or "other", "ran_on": len(ran), "fired_final": len(fin), "fired_ever": len(ever),
               "blocking_seen": any(key[p]["gate"]["ever_failed"].get(g, {}).get("blocking") for p in ever)}
        if col:
            for name, fired in (("final", fin), ("ever", ever)):
                for lvl, pos in (("any", ("light", "heavy")), ("heavy", ("heavy",))):
                    is_pos = {p for p in ran if human[p]["defects"][col] in pos}
                    row[f"{name}_vs_{lvl}"] = prf(len(fired & is_pos), len(fired - is_pos), len(is_pos - fired))
            row["fired_on_human_light_or_better"] = sum(1 for p in ever if human[p]["label"] in GOOD)
        per_gate[g] = row
    rep["per_gate"] = per_gate
    rep["per_column_union"] = {}
    for col in DEFECT_CLASSES:
        gs = {g for g, c in GATE_COLUMN.items() if c == col}
        ever = {p for p in ids if gs & set(key[p]["gate"]["ever_failed"])}
        fin = {p for p in ids if gs & {f["gate"] for f in key[p]["gate"]["final_failed"]}}
        pos_any = {p for p in ids if human[p]["defects"][col] != "none"}
        pos_heavy = {p for p in ids if human[p]["defects"][col] == "heavy"}
        rep["per_column_union"][col] = {
            "human_any": len(pos_any), "human_heavy": len(pos_heavy),
            "ever_vs_any": prf(len(ever & pos_any), len(ever - pos_any), len(pos_any - ever)),
            "final_vs_any": prf(len(fin & pos_any), len(fin - pos_any), len(pos_any - fin)),
            "ever_vs_heavy": prf(len(ever & pos_heavy), len(ever - pos_heavy), len(pos_heavy - ever))}
    held = [p for p in ids if key[p]["gate"]["status"] == "held"]
    rep["held_gate_vs_human_column"] = {
        p: {"n": key[p]["n"], "held_gate": key[p]["gate"]["held_gate"],
            "column": GATE_COLUMN.get(key[p]["gate"]["held_gate"] or "", "other"),
            "human_level": human[p]["defects"].get(GATE_COLUMN.get(key[p]["gate"]["held_gate"] or "", ""), None),
            "human_label": human[p]["label"]} for p in held}

    # 5. panel scores vs human defect levels (higher defect level should mean lower score: expect rho < 0)
    if with_panel:
        lv = {"none": 0, "light": 1, "heavy": 2}
        dims = {}
        for col, metric in (("fact", "fidelity"), ("ai_phrasing", "ai_tells")):
            hx = [lv[human[p]["defects"][col]] for p in with_panel]
            d = {"panel_mean": r3(spearman(hx, [key[p]["panel"]["mean"][metric] for p in with_panel]))}
            for l in LENSES:
                d[l] = r3(spearman(hx, [key[p]["panel"]["lenses"][l][metric] for p in with_panel]))
            if col == "fact":
                d["fidelity_audit"] = r3(spearman(hx, [key[p]["panel"]["fidelity_audit"] for p in with_panel]))
            dims[f"{col}~{metric}"] = d
        hv = [VERDICTS.index(human[p]["label"]) for p in with_panel]
        dims["verdict~overall"] = {"panel_mean": r3(spearman(hv, [key[p]["panel"]["mean"]["overall"] for p in with_panel]))}
        mp = [p for p in with_panel if isinstance(human[p]["minutes"], (int, float))]
        dims["minutes~overall"] = {"n": len(mp), "panel_mean": r3(spearman(
            [human[p]["minutes"] for p in mp], [key[p]["panel"]["mean"]["overall"] for p in mp]))}
        dims["not_comparable"] = ["voice", "format"]  # brand_voice / channel_fit per lens were not kept in S234
        rep["panel_dimensions_spearman"] = dims

    # 6. a second labeller (e.g. chị Thư): human-human agreement on the overlap
    others = {}
    for name, labs in by_labeller.items():
        if name == primary_name:
            continue
        ov = [p for p in ids if p in labs]
        others[name] = verdict_block([(human[p]["label"], labs[p]["label"]) for p in ov])
    if others:
        rep["human_vs_human"] = others

    # 7. per-piece table for the written report
    rep["pieces"] = [{
        "n": key[p]["n"], "piece_id": p, "cell": cell(p), "gate": key[p]["gate"]["status"],
        "held_gate": key[p]["gate"]["held_gate"], "human": human[p]["label"],
        "panel": (key[p].get("panel") or {}).get("majority"), "votes": (key[p].get("panel") or {}).get("votes"),
        "human_defects": "".join(("-", "l", "H")[LEVELS.index(human[p]["defects"][c])] for c in DEFECT_CLASSES),
        "gates_ever": sorted(key[p]["gate"]["ever_failed"]), "minutes": human[p]["minutes"]}
        for p in sorted(ids, key=lambda q: key[q]["n"])]

    Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n")
    if a.md:
        Path(a.md).write_text(to_md(rep))
    vb = rep.get("verdict_vs_panel_majority", {})
    print(f"labelled {rep['n_labelled']}/{rep['n_export']}; human light-or-better "
          f"{(rep['share']['all'] or {}).get('human_light_or_better')}; kappa vs panel: "
          f"unweighted {vb.get('kappa')} quadratic {vb.get('kappa_quadratic')} binary {vb.get('kappa_binary')}")
    return 0


def to_md(rep: dict) -> str:
    L = [f"# AA-783 agreement report ({rep['set']} set, labeller {rep['labeller']})", "",
         f"Labelled {rep['n_labelled']} of {rep['n_export']}. Thresholds: stand-in kappa {STAND_IN_KAPPA}, light bar {LIGHT_BAR}.", ""]
    s = rep["share"]["all"] or {}
    L += ["## Light share", "", "| Slice | n | Human as-is | Human light+ | Panel light+ | Gate approved |", "|---|---|---|---|---|---|"]
    rows = [("all", s)] + list(rep["share"]["by_channel"].items()) + list(rep["share"]["by_cell"].items())
    for name, x in rows:
        if x:
            L.append(f"| {name} | {x['n']} | {x['human_as_is']} | {x['human_light_or_better']} | "
                     f"{x.get('panel_light_or_better', '–')} | {x['gate_approved']} |")
    if "light_bar" in rep:
        L += ["", f"Panel minus human light share: {rep['light_bar']['panel_minus_human_light_share']}; a panel bar of "
                  f"{rep['light_bar']['panel_bar_equivalent_to_human_bar']} matches a human bar of {LIGHT_BAR}."]
    if "verdict_vs_panel_majority" in rep:
        L += ["", "## Verdict agreement (human vs panel)", "",
              "| Against | n | Exact | kappa (CI) | Quadratic kappa (CI) | Binary kappa (CI) | Panel stricter / more lenient |",
              "|---|---|---|---|---|---|---|"]
        for name, b in [("panel majority", rep["verdict_vs_panel_majority"])] + list(rep["verdict_vs_lens"].items()):
            L.append(f"| {name} | {b['n']} | {b['exact_agreement']} | {b['kappa']} {b['kappa_ci95']} | "
                     f"{b['kappa_quadratic']} {b['kappa_quadratic_ci95']} | {b['kappa_binary']} {b['kappa_binary_ci95']} | "
                     f"{b['other_stricter']} / {b['other_more_lenient']} |")
        L += ["", f"Panel internal Fleiss kappa: {rep['panel_internal_fleiss_kappa']}. "
                  f"Panel can stand in for the human verdict: **{rep['panel_can_stand_in']}**. Ties: {rep['tie_rule']}."]
    g = rep["gate_approval_vs_human"]
    L += ["", "## Gate approve/hold vs human (should approve = light or better)", "",
          f"Gate: precision {g['precision']}, recall {g['recall']}, held precision {g['held_precision']}, "
          f"accuracy {g['accuracy']}, kappa {g['kappa']} (tp {g['tp']}, fp {g['fp']}, fn {g['fn']}, tn {g['tn']})."]
    if "panel_approval_vs_human" in rep:
        p = rep["panel_approval_vs_human"]
        L.append(f"Panel on the same footing: precision {p['precision']}, recall {p['recall']}, accuracy {p['accuracy']}, kappa {p['kappa']}.")
    L += ["", "## Per gate vs the human defect column (any attempt, light or heavy)", "",
          "| Gate | Column | Ran on | Fired final | Fired ever | Precision | Recall | Fired on light+ pieces |", "|---|---|---|---|---|---|---|---|"]
    for name, r in sorted(rep["per_gate"].items(), key=lambda kv: (kv[1]["column"], kv[0])):
        e = r.get("ever_vs_any", {})
        L.append(f"| {name} | {r['column']} | {r['ran_on']} | {r['fired_final']} | {r['fired_ever']} | "
                 f"{e.get('precision', '–')} | {e.get('recall', '–')} | {r.get('fired_on_human_light_or_better', '–')} |")
    if "panel_dimensions_spearman" in rep:
        L += ["", "## Panel scores vs human defect levels (Spearman; negative = agrees)", "",
              "```", json.dumps(rep["panel_dimensions_spearman"], indent=1), "```"]
    L += ["", "## Per piece", "", "| # | Cell | Gate | Held gate | Human | Panel (votes E/B/C/K) | Defects F/V/Fm/AI | Gates fired | Min |",
          "|---|---|---|---|---|---|---|---|---|"]
    for p in rep["pieces"]:
        L.append(f"| {p['n']} | {p['cell']} | {p['gate']} | {p['held_gate'] or ''} | {p['human']} | "
                 f"{p['panel'] or '–'} ({p['votes'] or ''}) | {p['human_defects']} | {', '.join(p['gates_ever'])} | {p['minutes'] if p['minutes'] is not None else ''} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decode")
    d.add_argument("raw")
    d.add_argument("-o", "--out", required=True)
    p = sub.add_parser("page")
    p.add_argument("export")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--pack", help="S234-label-40.xlsx: panel-era text for pieces whose DB text changed")
    r = sub.add_parser("report")
    r.add_argument("export")
    r.add_argument("labels")
    r.add_argument("-o", "--out", required=True)
    r.add_argument("--md")
    r.add_argument("--labeller", help="primary labeller (default: the one with most labels)")
    a = ap.parse_args()
    if a.cmd == "decode":
        doc = decode_raw(Path(a.raw).read_text(errors="replace"))
        Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print(f"decoded {len(doc['pieces'])} pieces ({doc['set']}); counts {doc['counts']}; notes {doc['notes']}")
        return 0
    return cmd_page(a) if a.cmd == "page" else cmd_report(a)


if __name__ == "__main__":
    sys.exit(main())
