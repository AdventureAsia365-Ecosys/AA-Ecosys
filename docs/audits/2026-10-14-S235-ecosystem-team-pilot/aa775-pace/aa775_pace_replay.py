"""AA-775 pre-wiring replay ($0, no LLM, no DB) — how the proposed F17 `pace_promise` finding would fire on
the 80 S234 pieces (.tmp-session/s234/pieces.json + pieces_r2..r4.json). NOT wired into the app: this only
measures the regex + false-positive filter before anyone writes trip_facts.pace_claims.

Rule under test (plan 09 §3 #3, AA-775 plan):
  PACE_RE over body sentences (hygiene.sentence_spans kinds prose/bullet/faq_a), excluding
    - the CTA sentence (hygiene._is_cta with the brand's default_cta — the stored pieces do not keep the
      per-request CTA, so a CTA paraphrase can slip through; listed for review),
    - "the rest of …" (rest = remainder),
    - seed-supported sentences: the matched pace word's stem is in the seed's OWN half (hygiene.split_seed),
      or ≥ SUPPORT_SHARE of the content words in a ±WINDOW-word window around the match are in the own half.
  Blocking would be blog-only; LinkedIn hits are counted separately (they would never hold).

Output per tenant × channel: raw hits, CTA-excluded, 'rest of' excluded, seed-supported (suppressed),
remaining (would fire), plus every remaining and every suppressed sentence for a human FP label.
Usage: <venv python> aa775_pace_replay.py [--repo <worktree with services/>] [--rounds 1,2,3,4]

S235 Batch 2 (AA-775 wired): also runs the shipped trip_facts.pace_claims (source = the seed's own half;
the stored pieces keep no Facts block and no per-request CTA, so cta=None and brand_name=tenant — the
CTA paraphrase filter `_cta_paraphrase` then does the CTA exclusion) and reports, per tenant x channel x
round, `pace_sentences` (the r5 Done-when counter: PACE_RE over body sentences, CTA + CTA paraphrase
excluded) and `wired_findings` (what F17 pace_promise would flag; blog only in the app).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

S234 = Path("/home/nghiep/projects/AA-Ecosys/.tmp-session/s234")
PACE_RE = re.compile(r"\b(pace[ds]?|relentless|exhaust\w*|rest(?:ful|ing)?|rush\w*|manageable|balanced?)\b", re.I)
REST_OF_RE = re.compile(r"\bthe rest of\b", re.I)
WINDOW = 6
SUPPORT_SHARE = 0.6
FILES = {1: "pieces.json", 2: "pieces_r2.json", 3: "pieces_r3.json", 4: "pieces_r4.json"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App")
    ap.add_argument("--rounds", default="1,2,3,4")
    args = ap.parse_args()
    sys.path.insert(0, args.repo)
    from services.acp_content_writing.hygiene import _is_cta, content_words, sentence_spans, split_seed
    from services.acp_content_writing.trip_facts import PACE_RE as APP_PACE_RE, _body_spans, _cta_paraphrase, \
        pace_claims

    wired = defaultdict(lambda: defaultdict(int))
    wired_fire = []

    stats = defaultdict(lambda: defaultdict(int))
    remaining, suppressed = [], []
    for rnd in (int(r) for r in args.rounds.split(",")):
        for i, p in enumerate(json.loads((S234 / FILES[rnd]).read_text())):
            key = f"{p.get('tenant')}|{p.get('channel')}"
            own = split_seed(p.get("seed") or "")[0]
            own_words = set(content_words(own))
            cta = (p.get("brand_pack") or {}).get("default_cta")
            tenant = p.get("tenant")
            wkey = f"{tenant}|{p.get('channel')}|r{rnd}"
            body = [sp["clean"] for sp in _body_spans(p.get("text") or "", cta)]
            wired[wkey]["pace_sentences"] += sum(1 for t in body if APP_PACE_RE.search(t)
                                                 and not _cta_paraphrase(t, cta, tenant))
            found = pace_claims(p.get("text") or "", own, cta, tenant)
            wired[wkey]["wired_findings"] += len(found)
            wired_fire += [{"round": rnd, "piece": p["piece_id"][:8], "tenant": tenant, "channel": p.get("channel"),
                            "finding": f} for f in found]
            for sp in sentence_spans(p.get("text") or ""):
                if sp["kind"] not in ("prose", "bullet", "faq_a"):
                    continue
                sent = sp["clean"]
                m = PACE_RE.search(sent)
                if not m:
                    continue
                stats[key]["hits"] += 1
                rec = {"round": rnd, "i": i, "piece": p["piece_id"][:8], "tenant": p.get("tenant"),
                       "channel": p.get("channel"), "word": m.group(1), "sentence": sent}
                if _is_cta(sent, cta):
                    stats[key]["cta_excluded"] += 1
                    continue
                if REST_OF_RE.search(sent) and not PACE_RE.search(REST_OF_RE.sub(" ", sent)):
                    stats[key]["rest_of_excluded"] += 1
                    continue
                stem = content_words(m.group(1))
                words = sent.split()
                at = len(sent[:m.start()].split())
                window = content_words(" ".join(words[max(0, at - WINDOW):at + WINDOW + 1]))
                share = sum(w in own_words for w in window) / max(1, len(window))
                if (stem and stem[0] in own_words) or share >= SUPPORT_SHARE:
                    stats[key]["seed_supported"] += 1
                    suppressed.append({**rec, "share": round(share, 2)})
                    continue
                stats[key]["would_fire"] += 1
                remaining.append({**rec, "share": round(share, 2)})
    print(json.dumps({"rule": {"regex": PACE_RE.pattern, "window": WINDOW, "support_share": SUPPORT_SHARE},
                      "by_tenant_channel": {k: dict(v) for k, v in sorted(stats.items())},
                      "would_fire": remaining, "suppressed_as_seed_supported": suppressed,
                      "wired_by_tenant_channel_round": {k: dict(v) for k, v in sorted(wired.items())},
                      "wired_findings": wired_fire},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
