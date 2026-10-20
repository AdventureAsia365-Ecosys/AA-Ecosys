"""AA-865 (S245) — READ-ONLY pooled F9_cta_fact re-flag rate over the AA-777 retry rounds r5–r7, with Wilson 95%
intervals, plus a dump of every retry that added a blocking fail, for classification. $0: no LLM call.

Runs INSIDE the CIS api container (S3-presigned ECS exec on aa-cis-dev-api), no arguments.
- DB: the container's DATABASE_URL (role cis_app; CIS schemas only), ssl="require", one READ ONLY transaction.
  It never reads aa-cis/dev/rds (the CIS task role is denied that secret since X1 S18/S19).
- Output: the full JSON goes to s3://aa-cis-bronze-005097885195/scripts/out/s245_aa865_pool.json (the only write);
  stdout is a short summary, because the SSM session truncates long stdout (lessons, S237). Set STDOUT_FULL = True
  to print the whole document instead (for .tmp-session/s237/exec_s3out.sh, which uploads stdout itself).

Metric (copied, not re-invented): `reconstruct()` and "retry added a blocking fail" are copied from
.tmp-session/s239/aa777_r7_readout.py (port of S234 fr_analyze.py). Per piece, attempt k's blocking-fail SET comes
from repair_log entry k's `feedback` "GATE: msg" prefixes (last attempt without an entry = final gate_ledger, waived
counted; a guard-reverted last attempt = discarded_attempts[0].gate_ledger); effective state after a guard revert =
the state before it; retry k (k >= 2) "added" when fails(k) - effective(k-1) is non-empty. Denominator = every retry.
The pooled numbers must reproduce the committed per-round readouts: EXPECTED below; a mismatch is reported.

Pools: primary_r5_r7 (issue title), extended_with_aa768, current_code_r7, natural_post_r7 (T9 pieces created after
the r7 run that are in no set), reference_S234_r4 (pre-sticky; never pooled).
"""
import sys

_STDOUT = sys.stdout
sys.stdout = sys.stderr  # app imports may log to stdout; keep stdout for the result only

import asyncio  # noqa: E402
import collections as C  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from urllib.parse import unquote, urlparse  # noqa: E402

sys.path.insert(0, "/app")

import asyncpg  # noqa: E402

# ── constants ────────────────────────────────────────────────────────────────────────────────────
STDOUT_FULL = False
REGION = "us-west-1"
S3_BUCKET = "aa-cis-bronze-005097885195"
S3_OUT_KEY = "scripts/out/s245_aa865_pool.json"
TARGET_RATE = 0.08
Z95 = 1.959963984540054
# r7 run started 2026-10-16T07:52Z and its last wave finished about 08:10Z; a T9 piece created after this is on the
# r7 (post-#767) loop code. The content-writing commits after r7 (#776, #792) touch the tenant pool only.
NATURAL_AFTER = datetime(2026, 10, 16, 8, 12, tzinfo=timezone.utc)
F9 = "F9_cta_fact"
NON_SENTENCE_MODES = {"full_rewrite", "seo_fields"}
POST_LOOP_CUT_MODES = {"f9_truth_cut", "f9_cut_refused", "aup_cut"}

# S234_r4 / S235_r5 / S239_aa768_pre761: BASE_SETS of .tmp-session/s239/aa777_r7_readout.py.
# S239_r6* / S239_r7*: `pieces` of docs/audits/2026-10-16-S239-in-progress-audit/aa777-r{6,7}/readout_stdout.json
# (main set vs the 5 AA-768 pilot requests), root origin/master.
SETS = {
    "S234_r4": ["49ed3642-30d5-4696-a228-479c017665a7", "91e4b9d2-157a-4a5f-90b3-332b6d9f5338",
                "1376c2c3-7560-4394-bed8-97063f4d5564", "7c8bc7df-5de4-402b-8ffc-2b3b72afc67a",
                "3fd85285-7010-4338-9172-34d4acbe4b0a", "bb776a54-93cc-4f10-a108-6e26f9f05324",
                "71ad6b1f-9eb5-4509-915c-5c7644a5b71a", "6961b261-6956-4b66-b563-9d34b8f8b5da",
                "e980728e-f77a-47ba-8b59-0b63a28e301c", "d8990697-4227-4ddc-9541-793c8ae59993",
                "68a56edf-32df-477c-b0c1-2413a1360472", "6599b514-4fbb-4c45-ba22-f29b234e4143",
                "bf00c670-4496-409c-b8ef-9938c339685c", "e61ad7bc-6684-49d9-9727-cafec9de28b8",
                "67f08753-4c50-4962-a8bd-10224ac2df78", "9594430b-93c7-425d-ac19-9dde2c33fe88",
                "2fc0a2fb-7708-4a38-a3b5-b1275c1e3089", "9b65bd97-0e42-4ceb-96c3-2e50c3bb8058",
                "4c2bb8c1-dfaf-4369-b349-36bde9e9e5c9", "5939df86-f8d4-491e-affc-348d0618ddcd"],
    "S235_r5": ["d075fa29-983c-4587-ac0f-8a2707cc90e8", "fb086ed1-f6af-4cc6-b360-98918e835292",
                "22f7d8d5-4748-4066-9eae-e6b9fb42e2f3", "83df67f9-7775-4eb5-9485-46453923906f",
                "db4cf81e-d5a2-4ddf-8529-7c180259ba4d", "bfb3456e-1fe8-4466-9bc7-691c3291e380",
                "d46c030b-1be6-4618-858a-840319481de8", "adc2cd04-14ca-4cee-bf54-e88946301e31",
                "a1e1f1f4-2b2b-44ba-ba76-8e91641ce435", "a8f147e9-a9bd-436f-86d1-87ef1fcf8b99",
                "ad01f4b5-937c-42f9-96c2-afc3c319bad3", "ea9786a6-4733-4f98-8d0f-97727c1bc740",
                "7b4b75c1-6cdb-47d9-b4d8-7b6fe23903a8", "83d14812-c209-4690-a7a7-318d10ac152c",
                "73035732-8541-4c22-806c-6d92da331cb7", "bb53cb48-1fee-4f4e-95a9-f3dbc507feb2",
                "3d5631b1-1a6b-41ec-a350-c60b556c4adf", "ccb0843c-bb8d-4050-a6e9-2a163f8adb4b",
                "206433a2-8998-4ecc-8797-165c19bd9510", "f810ddd0-c2d0-4199-8b29-5ae527d78f9a"],
    "S239_aa768_pre761": ["1f02cecb-efd6-4f9c-bf32-1c6efbf3c77b", "a7e18faf-4b68-4453-8020-000e38109674",
                          "dde74641-455f-4d9d-9c8e-696dc3a456c8", "26a20425-95e7-48c1-9c80-01e76948a38e",
                          "7594ffed-d1a9-4f6e-9bba-95d18d403b7c"],
    "S239_r6": ["f1f8cac9-ccbe-468b-b30d-179d542372e6", "e73d995d-9a4c-4fab-b950-27b34433e1c5",
                "7aebf612-8ab1-490f-bc73-0cee4eb0fd1f", "1a8dec5d-3134-4e28-9072-ff04056feb10",
                "f5209e57-e2a2-4e2a-8194-638222a5c86b", "8a6d52c0-455a-4b07-b46e-2ba86c0e5f11",
                "a3d82ff1-d359-46c4-82d9-270d6d9655ad", "efa202fe-7b4c-47a5-81ca-339d66b32771",
                "fedede89-8cb4-4501-8783-09d1df8ceb9e", "e37b3783-1398-4507-88e1-069704eb3dab",
                "0cce2bf9-b82c-4448-987e-2e124e630d23", "582cd11d-d8b3-44ce-9426-dbd9d3f958fa",
                "17125e0c-1598-47ba-8d3b-affc642da26f", "d56a7b92-6e8a-4381-a87a-a8262e19132f",
                "a2133050-dbcf-46e2-978b-f7b8fd656a40", "3532ecdd-57ca-4041-9530-ba46df85b0f4",
                "f15221c8-3285-4b37-b552-5ef620574ee4", "263e5a5a-e4d8-4cdc-ad9e-2545a26c757d",
                "4b7826fd-e3b6-4742-9463-ebf3f0d034bf", "c8e0f755-d620-4e5e-af30-22aac0817685"],
    "S239_r6_aa768": ["89d60686-8b8b-4aef-acb8-fc140a39c80b", "35ee6a3d-061f-4d33-be56-28f792318675",
                      "e547c752-9b37-44a2-b0c1-8c65d58a7cc2", "dfeeccba-1805-4b0b-935a-87f850c96781",
                      "fa48733e-c7bd-4469-b90d-60901f839b2c"],
    "S239_r7": ["31b91e79-cc6a-448d-94ff-1aeeaebb473b", "3aa22704-cc09-4c30-b026-749883bf7daa",
                "aabf6441-b62d-4bec-9882-d1ebfbc53ee5", "a7884f39-57ec-4850-b508-498f55d507ce",
                "3cc6f742-c0e4-4b2f-b196-e1b51e721805", "b05c1dea-3113-47c8-a251-a5fdc51512cf",
                "ff8e1c9f-f6c8-41c7-bd8c-b972a418ec44", "2a5356c8-188b-45d1-8f22-08f2f490f49f",
                "23d46bb8-ae1d-4253-83a0-e9a9915ffa74", "4dd0e729-dd27-400a-89da-74beb9b8c34f",
                "00989f55-a1ee-434f-9153-09ef4e2c1a31", "21697065-39c8-4642-a7db-f214ed2ee9f9",
                "33cd51b2-659f-4737-84b7-acbf7c668ba1", "53dd72bf-d337-46e0-bfc5-2fffcbb44750",
                "039a8b1f-ffd0-4633-88a2-2fbd985f651c", "ad2981e9-74c7-49b8-a001-bf7071286ab4",
                "ba405cd1-9aae-4a32-9178-622c6cf4ac44", "f6fc7e71-42c4-4b39-b270-84cdfd4d5662",
                "3801eaf7-ed92-4e1f-b4de-aee0aba162b5", "b1ddcfab-ab1a-472e-b5e8-977db6a15138"],
    "S239_r7_aa768": ["ebfff6f3-96bd-4464-9713-7bfc0f3c2594", "31706a16-c8c7-436c-b7cc-6f9a4ccd3c74",
                      "9c4ff9be-f642-4249-811a-45cd350f61e5", "7e36dd46-b141-41eb-bcba-84b6086b7b64",
                      "355c7e01-faf7-4b10-8d52-30f68d74154f"],
}
# committed readouts (retry_added_blocking_fail num/den per set) — the reproduction check
EXPECTED = {"S234_r4": (4, 32), "S235_r5": (1, 26), "S239_aa768_pre761": (1, 9), "S239_r6": (4, 26),
            "S239_r6_aa768": (0, 8), "S239_r7": (3, 23), "S239_r7_aa768": (1, 8)}
POOLS = {
    "primary_r5_r7": ["S235_r5", "S239_r6", "S239_r7"],
    "extended_with_aa768": ["S235_r5", "S239_r6", "S239_r7", "S239_aa768_pre761", "S239_r6_aa768", "S239_r7_aa768"],
    "current_code_r7": ["S239_r7", "S239_r7_aa768"],
    "natural_post_r7": ["natural_post_r7"],
    "extended_plus_natural": ["S235_r5", "S239_r6", "S239_r7", "S239_aa768_pre761", "S239_r6_aa768",
                              "S239_r7_aa768", "natural_post_r7"],
    "reference_S234_r4": ["S234_r4"],
}

# ── the app's own text helpers (same code as the deployed loop); fallbacks keep the rates working ─────────────
try:
    from services.acp_content_writing.hygiene import sentence_spans
    from services.acp_content_writing.quality_gates import _cmp_fold, _f9_key, _f9_passed_keys, _REFERENT_OPEN_RE
    from services.acp_content_writing.sentence_repair import locate_sentence
    HELPERS = "services.acp_content_writing (hygiene.sentence_spans, quality_gates._f9_key/_cmp_fold/" \
              "_f9_passed_keys, sentence_repair.locate_sentence)"
except Exception as _e:  # noqa: BLE001
    sentence_spans = _cmp_fold = _f9_key = _f9_passed_keys = locate_sentence = _REFERENT_OPEN_RE = None
    HELPERS = f"unavailable ({_e!r:.160}) — rates only, no sentence location"

_WORD_RE = re.compile(r"[0-9a-z]+(?:'[a-z]+)?")
_STOP = set("""a an the and or but so yet of to in on at by for with from into onto over under about as is are was were
be been being it its it's this that these those there here then than you your yours we our us they their them he she
his her i me my not no nor do does did done have has had will would can could may might must shall should just also
very more most much many some any each every all both such only own same too s t""".split())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _jsonb(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return None
    return v


def wilson(k: int, n: int, z: float = Z95) -> dict:
    """Wilson score interval for k successes in n trials (95% by default)."""
    if not n:
        return {"num": k, "den": n, "rate": None, "ci95": None}
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"num": k, "den": n, "rate": round(p, 4), "ci95": [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)],
            "le_target": p <= TARGET_RATE, "ci_upper_le_target": c + h <= TARGET_RATE}


# ── copied from aa777_r7_readout.py (S234 fr_analyze port) ─────────────────────────────────────────────────────

def failset(ledger, include_waived=True):
    return {g["gate"] for g in ledger or [] if isinstance(g, dict) and not g.get("passed")
            and (g.get("blocking", True) or (include_waived and g.get("waived")))}


def reconstruct(p):
    """fr_analyze.reconstruct, plus: post-loop cut entries (no feedback) are not attempt records.
    Extended for AA-865: also returns the per-attempt repair_log entries and guard entries."""
    rl = [e for e in (p["repair_log"] or []) if isinstance(e, dict)]
    entries = {}
    for e in rl:
        if e.get("gate_targeted") == "gate_regression_guard":
            continue
        if "feedback" not in e and e.get("repair_mode") in POST_LOOP_CUT_MODES:
            continue
        entries.setdefault(e.get("attempt"), e)
    guards = {e.get("attempt"): e for e in rl if e.get("gate_targeted") == "gate_regression_guard"}
    n = max([p["attempt_number"] or 1] + [k for k in entries if k] + [k for k in guards if k])
    disc = (p["discarded_attempts"] or [None])[0]
    atts, snap_disagree = [], 0
    for k in range(1, n + 1):
        if k in entries:
            e = entries[k]
            fb = e.get("feedback") or [f"{e.get('gate_targeted')}: {v}" for v in e.get("violations") or []]
            fails = {f.split(":", 1)[0] for f in fb}
            if e.get("gate_ledger"):  # AA-791 snapshot cross-check
                snap = failset(e["gate_ledger"], include_waived=False)
                snap_disagree += snap != fails
        elif k == n:
            led = disc["gate_ledger"] if (k in guards and isinstance(disc, dict)
                                          and disc.get("attempt_number") == k) else p["gate_ledger"]
            fails = failset(led)
        else:
            fails = None
        if k == 1:
            mode = "write"
        else:
            prev = guards.get(k - 1) or entries.get(k - 1)
            mode = (prev or {}).get("repair_mode") or "full_rewrite"
        atts.append({"k": k, "fails": fails, "mode": mode, "guard": k in guards})
    eff = []
    for i, a in enumerate(atts):
        eff.append(eff[-1] if (a["guard"] and i > 0) else a["fails"])
    return atts, eff, snap_disagree, entries, guards


# ── AA-865 additions: attempt texts, F9 quotes, location ───────────────────────────────────────────────────────

def attempt_texts(p, n: int, guards: dict) -> dict:
    """{attempt: (text, source)} for the attempts whose text is stored. content_piece keeps the final text and at most
    one discarded attempt. Guard revert at the last attempt n: final = attempt n-1, discarded = attempt n. Otherwise
    final = attempt n (attempt_number), discarded = attempt n-1 (service.py AA-570)."""
    out = {}
    disc = (p["discarded_attempts"] or [None])[0]
    disc_k = disc.get("attempt_number") if isinstance(disc, dict) else None
    if isinstance(disc, dict) and disc_k and disc.get("content_text"):
        out[disc_k] = (disc["content_text"], "discarded_attempts[0]")
    final_k = (n - 1) if (n in guards and disc_k == n) else n
    out.setdefault(final_k, (p["content_text"] or "", "content_text (final)"))
    return out


def ledger_of(k: int, n: int, entries: dict, guards: dict, p) -> list:
    """Attempt k's gate ledger: the AA-791 snapshot on repair_log entry k, else (last attempt) the stored ledger."""
    if k in entries and entries[k].get("gate_ledger"):
        return entries[k]["gate_ledger"]
    if k == n:
        disc = (p["discarded_attempts"] or [None])[0]
        if k in guards and isinstance(disc, dict) and disc.get("attempt_number") == k:
            return disc.get("gate_ledger") or []
        return p["gate_ledger"] or []
    return []


def violations_of(k: int, gate: str, n: int, entries: dict, guards: dict, p) -> list[str]:
    """Attempt k's violation strings for `gate`: repair_log entry k's `feedback` (untrimmed) when present, else the
    ledger (snapshot violations are cut to 300 chars)."""
    if k in entries and entries[k].get("feedback"):
        pre = gate + ":"
        return [f[len(pre):].strip() for f in entries[k]["feedback"] if isinstance(f, str) and f.startswith(pre)]
    for g in ledger_of(k, n, entries, guards, p):
        if isinstance(g, dict) and g.get("gate") == gate and not g.get("passed"):
            return [str(v) for v in g.get("violations") or []]
    return []


def gate_passed_at(k: int, gate: str, n: int, entries: dict, guards: dict, p):
    """True / False / None (unknown) — did `gate` pass at attempt k."""
    led = ledger_of(k, n, entries, guards, p)
    for g in led:
        if isinstance(g, dict) and g.get("gate") == gate:
            return bool(g.get("passed"))
    if k in entries and entries[k].get("feedback") is not None:
        return not any(isinstance(f, str) and f.startswith(gate + ":") for f in entries[k]["feedback"])
    return None


_CLAIM_RE = re.compile(r'"(?P<sentence>.+?)" \(claims: (?P<claim>.*?); source: (?P<why>.*?)\)(?=; "|$)', re.S)
_INTEGRITY_RE = re.compile(r"TEXT_INTEGRITY: '(?P<sentence>.+)'$", re.S)
_PHRASE_RE = re.compile(r'exact flagged phrase\(s\): (?P<rest>.+)$', re.S)
_FIELD_RE = re.compile(r'^(?P<field>title|meta) unsupported claim: "(?P<sentence>.+?)" \(claims: (?P<claim>.*?); '
                       r'source: (?P<why>.*?)\)$', re.S)


def parse_f9(violations: list[str]) -> list[dict]:
    """The F9_cta_fact items of one attempt, from the violation strings gate_brand_voice writes:
    'audit <status>: <codes> — unsupported claim(s): "<sentence>" (claims: <c>; source: <why>); "…"',
    "TEXT_INTEGRITY: '<sentence>'", '<title|meta> unsupported claim: …', the reasonless warn, or a phrase list."""
    items = []
    for v in violations:
        m = _FIELD_RE.match(v)
        if m:
            items.append({"kind": f"{m['field']}_claim", "sentence": m["sentence"], "claim": m["claim"],
                          "why_not_in_source": m["why"]})
            continue
        m = _INTEGRITY_RE.match(v)
        if m:
            items.append({"kind": "text_integrity", "sentence": m["sentence"], "claim": None,
                          "why_not_in_source": None})
            continue
        if "unsupported claim(s):" in v:
            body = v.split("unsupported claim(s):", 1)[1].strip()
            found = list(_CLAIM_RE.finditer(body))
            for m in found:
                items.append({"kind": "unsupported_claim", "sentence": m["sentence"], "claim": m["claim"],
                              "why_not_in_source": m["why"]})
            if not found:
                items.append({"kind": "unparsed", "raw": v[:1200]})
            continue
        m = _PHRASE_RE.search(v)
        if m:
            for ph in re.findall(r'"([^"]+)"', m["rest"]):
                items.append({"kind": "flagged_phrase", "sentence": ph, "claim": None, "why_not_in_source": None,
                              "codes": v.split("—", 1)[0].strip()[:200]})
            continue
        items.append({"kind": "other", "raw": v[:1200]})
    return items


_PAIRED_QUOTE_RE = re.compile(r"'([^']*)'|\"([^\"]*)\"|“([^”]*)”")


def _quoted(msg: str, base_text: str | None) -> list[str]:
    """The sentences a non-F9 violation message quotes. With the attempt's text: every sentence of it (>= 4 words)
    whose fold is inside the message's fold (robust to apostrophes). Without it: paired quotes, scanned left to right
    so the gap between two quoted strings is never read as a quote, kept when >= 12 characters."""
    if base_text and _cmp_fold and sentence_spans:
        fm = _cmp_fold(msg)
        hits = [sp["clean"] for sp in _spans(base_text)
                if len(_cmp_fold(sp["clean"]).split()) >= 4 and _cmp_fold(sp["clean"]) in fm]
        if hits:
            return hits
    return [q for m in _PAIRED_QUOTE_RE.finditer(msg) for q in [next((g for g in m.groups() if g is not None), "")]
            if len(q.strip()) >= 12]


def targets_of(k: int, entries: dict, base_text: str | None = None) -> list[dict]:
    """What the attempt k -> k+1 repair was asked to fix: every blocking violation of attempt k, with the quoted
    sentence(s) when the message carries one (feedback lines are 'GATE: message')."""
    e = entries.get(k) or {}
    out = []
    for f in e.get("feedback") or []:
        if not isinstance(f, str) or ":" not in f:
            continue
        gate, msg = f.split(":", 1)
        msg = msg.strip()
        quotes = [it.get("sentence") for it in parse_f9([msg]) if it.get("sentence")] if gate == F9 \
            else _quoted(msg, base_text)
        out.append({"gate": gate, "message": msg[:600], "quotes": quotes[:4]})
    return out


def _words(t: str) -> list[str]:
    return _WORD_RE.findall((_cmp_fold(t) if _cmp_fold else t.lower()))


def _content_words(t: str) -> set[str]:
    return {w for w in _words(t) if w not in _STOP and len(w) > 2}


def _spans(text: str) -> list[dict]:
    return [sp for sp in sentence_spans(text or "")] if sentence_spans else []


def locate(text: str, quote: str) -> dict:
    """Where a judge quote sits in `text`: the sentence(s) it spans (current sentence_repair.locate_sentence, the same
    matcher the sticky pass uses), with each sentence's previous sentence and kind."""
    if not (locate_sentence and text and quote):
        return {"located": False}
    try:
        span = locate_sentence(text, str(quote))
    except Exception as e:  # noqa: BLE001
        return {"located": False, "error": repr(e)[:160]}
    if span is None:
        return {"located": False}
    spans = _spans(text)
    ks = [i for i, sp in enumerate(spans) if sp["start"] < span[1] and span[0] < sp["end"]]
    if not ks:
        return {"located": False}
    return {"located": True, "n_sentences": len(ks),
            "sentences": [spans[i]["clean"] for i in ks],
            "prev_sentence": spans[ks[0] - 1]["clean"] if ks[0] else None,
            "kinds": [spans[i]["kind"] for i in ks],
            "keys": [_f9_key(spans[i - 1]["clean"] if i else None, spans[i]["clean"]) for i in ks]}


def _sentence_index(text: str) -> dict:
    """fold(sentence) -> (sentence, previous sentence) for every sentence of `text`."""
    out, prev = {}, None
    for sp in _spans(text):
        out.setdefault(_cmp_fold(sp["clean"]), (sp["clean"], prev))
        prev = sp["clean"]
    return out


def _best_match(sentence: str, candidates: list[str]) -> tuple[float, str | None]:
    """Jaccard of content words between `sentence` and the closest candidate (0 when none)."""
    a = _content_words(sentence)
    best, best_c = 0.0, None
    for c in candidates:
        b = _content_words(c)
        if not a or not b:
            continue
        j = len(a & b) / len(a | b)
        if j > best:
            best, best_c = j, c
    return round(best, 3), best_c


def analyse_f9_item(item: dict, k: int, base: int, texts: dict, prev_targets: list[dict],
                    prev_f9_items: list[dict], passed_by_earlier: set | None, mode: str) -> dict:
    """Location of one attempt-k F9 item against the base attempt (k-1, or the attempt before a guard-reverted
    k-1), and a heuristic class hint (C1 real new fault / C2 F9 re-judging / C3 two-sentence quote)."""
    out = {**item}
    sent = item.get("sentence")
    if not sent or item.get("kind") in ("title_claim", "meta_claim"):
        out["location"] = "seo_field" if item.get("kind") in ("title_claim", "meta_claim") else "no_quote"
        out["suggested_class"] = "unclassifiable_without_quote" if not sent else "seo_field (non-blocking alone)"
        return out
    text_k = (texts.get(k) or (None,))[0]
    text_p = (texts.get(base) or (None,))[0]
    loc = locate(text_k, sent) if text_k else {"located": False, "reason": "attempt-k text not stored"}
    out["in_attempt_k"] = {x: loc.get(x) for x in ("located", "n_sentences", "sentences", "prev_sentence", "kinds",
                                                   "reason", "error") if loc.get(x) is not None}
    target_quotes = [q for t in prev_targets for q in t["quotes"]]
    target_gates = sorted({t["gate"] for t in prev_targets})
    sentences = loc.get("sentences") or [sent]
    score, closest = _best_match(" ".join(sentences), target_quotes)
    out["closest_base_target"] = {"jaccard": score, "quote": closest,
                                  "gate": next((t["gate"] for t in prev_targets if closest in t["quotes"]), None)}
    out["base_targets_gates"] = target_gates
    out["flagged_by_f9_at_base"] = any(
        _best_match(s, [i.get("sentence") or "" for i in prev_f9_items])[0] >= 0.6 for s in sentences)
    if loc.get("located") and text_p:
        idx = _sentence_index(text_p)
        present = [idx.get(_cmp_fold(s)) for s in sentences]
        unchanged = all(present)
        out["location_method"] = "base attempt text stored: exact sentence comparison"
        if unchanged:
            prev_now = loc.get("prev_sentence")
            prev_then = present[0][1]
            out["unchanged_since_base"] = True
            out["prev_sentence_changed"] = _cmp_fold(prev_now or "") != _cmp_fold(prev_then or "")
            out["opens_on_referent"] = bool(_REFERENT_OPEN_RE and _REFERENT_OPEN_RE.match(
                " ".join((sentences[0] or "").split()).lower()))
        else:
            out["unchanged_since_base"] = False
            j, before = _best_match(" ".join(sentences), [s for s, _ in idx.values()])
            out["closest_base_sentence"] = {"jaccard": j, "sentence": before}
            if before:
                out["content_words_added"] = sorted(_content_words(" ".join(sentences)) - _content_words(before))
                out["content_words_removed"] = sorted(_content_words(before) - _content_words(" ".join(sentences)))
    else:
        out["location_method"] = ("base attempt text not stored: compared with its repair targets "
                                  "(a sentence repair edits only its items)")
        out["unchanged_since_base"] = None if mode in NON_SENTENCE_MODES else score < 0.5
        if closest and score >= 0.5:
            out["content_words_added"] = sorted(_content_words(" ".join(sentences)) - _content_words(closest))
            out["content_words_removed"] = sorted(_content_words(closest) - _content_words(" ".join(sentences)))
    if passed_by_earlier is not None and loc.get("keys"):
        out["would_be_sticky_now"] = all(key in passed_by_earlier for key in loc["keys"])
    # heuristic class hint — the report sets the real class by reading the case
    if (loc.get("n_sentences") or 1) > 1:
        hint = "C3_two_sentence_quote"
    elif mode in NON_SENTENCE_MODES:
        hint = "C1_or_C2_full_rewrite (whole text rewritten; read the case)"
    elif out.get("unchanged_since_base"):
        why = []
        if out.get("prev_sentence_changed") and out.get("opens_on_referent"):
            why.append("referent opener + previous sentence changed -> new sticky key")
        if out.get("flagged_by_f9_at_base"):
            why.append("also flagged at the base attempt (never passed, so not sticky)")
        hint = "C2_rejudge_unchanged_sentence" + (f" ({'; '.join(why)})" if why else " (sticky miss)")
    elif out.get("unchanged_since_base") is False:
        added = out.get("content_words_added") or []
        hint = ("C1_candidate_real_new_fault (repair added content words: " + ", ".join(added[:8]) + ")") if added \
            else "C2_rejudge_repaired_sentence (no content word added: deletion / style edit)"
    else:
        hint = "unknown (sentence not located)"
    out["suggested_class"] = hint
    return out


def piece_rows(set_name: str, p: dict, calls: list[dict]) -> tuple[dict, list[dict]]:
    """(per-piece retry summary, list of retry-added cases)."""
    atts, eff, snap_dis, entries, guards = reconstruct(p)
    n = len(atts)
    texts = attempt_texts(p, n, guards)
    rl = [e for e in (p["repair_log"] or []) if isinstance(e, dict)]
    post_loop_edit = any(e.get("repair_mode") in POST_LOOP_CUT_MODES for e in rl)
    judge = sorted([c for c in calls if c["stage"] == "t10_judge"
                    and (c["quality_signal"] or {}).get("gate") == "F9_brand_voice"
                    and not (c["quality_signal"] or {}).get("shadow")], key=lambda c: c["created_at"])
    retries, cases, anoms = [], [], []
    for i in range(1, n):
        before, after = eff[i - 1], atts[i]["fails"]
        if before is None or after is None:
            anoms.append(f"unknown fails at attempt {i + 1}")
            continue
        new = after - before
        k = atts[i]["k"]
        retries.append({"k": k, "mode": atts[i]["mode"], "added": sorted(new), "guard": atts[i]["guard"]})
        if not new:
            continue
        # the attempt the k-1 -> k repair started from: k-1, or, when k-1 was guard-reverted, the attempt before it
        # (service.py AA-528 restores that attempt's text and ledger, and plan() runs on them)
        base = k - 1
        while base > 1 and atts[base - 1]["guard"]:
            base -= 1
        prev_targets = targets_of(base, entries, (texts.get(base) or (None,))[0])
        prev_f9 = parse_f9(violations_of(base, F9, n, entries, guards, p))
        # approximate sticky replay: union of _f9_passed_keys over the earlier attempts whose text is stored
        passed = None
        if _f9_passed_keys and _cmp_fold:
            passed = set()
            for j in range(1, base + 1):
                if j in texts and gate_passed_at(j, F9, n, entries, guards, p) is not None:
                    flagged = {_cmp_fold(it.get("sentence") or "") for it in
                               parse_f9(violations_of(j, F9, n, entries, guards, p))} - {""}
                    try:
                        passed |= _f9_passed_keys(texts[j][0], flagged)
                    except Exception:  # noqa: BLE001
                        pass
            if not any(j in texts for j in range(1, base + 1)):
                passed = None
        case = {
            "set": set_name, "piece_id": p["piece_id"], "slug": p["slug"], "channel": p["channel"],
            "status": p["status"], "held_reason": (p["held_reason"] or "")[:300] or None,
            "attempts": n, "k": k, "mode": atts[i]["mode"], "guard_reverted_k": atts[i]["guard"],
            "added_gates": sorted(new), "fixed_gates": sorted(before - after),
            "base_attempt": base,
            "f9_passed_at_base": gate_passed_at(base, F9, n, entries, guards, p),
            "base_repair_targets": prev_targets,
            "base_repair_entry": {x: (entries.get(base) or {}).get(x) for x in (
                "repair_mode", "sentences_repaired", "repeat_guard_deletes", "integrity_reverts", "integrity_problems",
                "specifics_reverts", "specifics_problems", "hazard_kept") if (entries.get(base) or {}).get(x)},
            "texts_stored_for_attempts": {str(a): src for a, (_, src) in sorted(texts.items())},
            "final_text_post_loop_edits": post_loop_edit,
            "f9_judge_calls": [{"at": str(c["created_at"]), "status": (c["quality_signal"] or {}).get("status"),
                                "failure_codes": (c["quality_signal"] or {}).get("failure_codes"),
                                "sticky_pass": (c["quality_signal"] or {}).get("sticky_pass"),
                                "reasonless": (c["quality_signal"] or {}).get("reasonless"),
                                "prompt_version": (c["quality_signal"] or {}).get("prompt_version"),
                                "model": c["model"], "stop_reason": c["stop_reason"]} for c in judge],
            "added": {},
        }
        for gate in sorted(new):
            viols = violations_of(k, gate, n, entries, guards, p)
            if gate == F9:
                items = parse_f9(viols)
                case["added"][gate] = [analyse_f9_item(it, k, base, texts, prev_targets, prev_f9, passed,
                                                       atts[i]["mode"])
                                       for it in items] or [{"kind": "no_violation_text", "raw": viols[:3]}]
            else:
                case["added"][gate] = [{"violation": v[:1200]} for v in viols]
        cases.append(case)
    row = {"set": set_name, "piece_id": p["piece_id"], "channel": p["channel"], "status": p["status"],
           "attempts": n, "retries": retries, "snapshot_disagreements": snap_dis, "anomalies": anoms,
           "created_at": str(p["created_at"]), "created_by": p.get("created_by")}
    return row, cases


def pool_metrics(rows: list[dict]) -> dict:
    retries = [x for r in rows for x in r["retries"]]
    sent = [x for x in retries if x["mode"] not in NON_SENTENCE_MODES]
    gates = C.Counter(g for x in retries for g in x["added"])
    by_mode = C.defaultdict(lambda: {"retries": 0, "any_added": 0, "f9_added": 0})
    for x in retries:
        m = by_mode[x["mode"]]
        m["retries"] += 1
        m["any_added"] += bool(x["added"])
        m["f9_added"] += F9 in x["added"]
    return {
        "pieces": len(rows), "retries": len(retries),
        "any_blocking_added": wilson(sum(bool(x["added"]) for x in retries), len(retries)),
        "f9_cta_fact_added": wilson(sum(F9 in x["added"] for x in retries), len(retries)),
        "any_blocking_added_excluding_F17": wilson(
            sum(bool(set(x["added"]) - {"F17_trip_fact"}) for x in retries), len(retries)),
        "sentence_family": {
            "any_blocking_added": wilson(sum(bool(x["added"]) for x in sent), len(sent)),
            "f9_cta_fact_added": wilson(sum(F9 in x["added"] for x in sent), len(sent))},
        "added_by_gate": dict(gates), "by_mode": {k: dict(v) for k, v in by_mode.items()},
        "anomalies": [(r["piece_id"][:8], a) for r in rows for a in r["anomalies"]],
        "snapshot_disagreements": sum(r["snapshot_disagreements"] for r in rows),
    }


# ── IO ─────────────────────────────────────────────────────────────────────────────────────────────────────────

PIECES_SQL = """
SELECT p.piece_id::text, t.slug, p.channel, p.status, p.held_reason, p.attempt_number, p.gate_ledger, p.repair_log,
       p.discarded_attempts, p.content_text, p.created_at, p.job_id::text, j.created_by
  FROM acp_shared.content_piece p JOIN shared.tenants t ON t.tenant_id = p.tenant_id
  LEFT JOIN shared.job j ON j.id = p.job_id
 WHERE p.piece_id = ANY($1::uuid[])
"""
NATURAL_SQL = """
SELECT p.piece_id::text
  FROM acp_shared.content_piece p
 WHERE p.created_at > $1 AND p.status IN ('approved', 'held') AND NOT (p.piece_id = ANY($2::uuid[]))
 ORDER BY p.created_at
"""
CALLS_SQL = """
SELECT job_id::text, content_piece_id::text, stage, model, cost_usd, quality_signal, stop_reason, created_at
  FROM shared.llm_call_log
 WHERE stage = 't10_judge' AND (job_id = ANY($1::uuid[]) OR content_piece_id = ANY($2::uuid[]))
"""


def _connect_kwargs() -> dict:
    """asyncpg kwargs from the container's DATABASE_URL (cis_app). Never printed."""
    dsn = os.environ["DATABASE_URL"].strip()
    u = urlparse(dsn.replace("postgresql+asyncpg://", "postgresql://", 1))
    return {"host": u.hostname, "port": u.port or 5432, "user": unquote(u.username or ""),
            "password": unquote(u.password or ""), "database": u.path.lstrip("/")}


async def main() -> dict:
    conn = await asyncpg.connect(**_connect_kwargs(), ssl="require",
                                 server_settings={"application_name": "adhoc-s245-aa865-pool"})
    try:
        async with conn.transaction(readonly=True):
            role = await conn.fetchval("SELECT current_user")
            known = sorted({i for v in SETS.values() for i in v})
            natural = [r["piece_id"] for r in await conn.fetch(NATURAL_SQL, NATURAL_AFTER, known)]
            ids = known + natural
            pieces = {}
            for r in await conn.fetch(PIECES_SQL, ids):
                d = dict(r)
                for k in ("gate_ledger", "repair_log", "discarded_attempts"):
                    d[k] = _jsonb(d[k]) or []
                pieces[d["piece_id"]] = d
            jobs = sorted({p["job_id"] for p in pieces.values() if p["job_id"]})
            calls = C.defaultdict(list)
            for r in await conn.fetch(CALLS_SQL, jobs, ids):
                d = dict(r)
                d["quality_signal"] = _jsonb(d["quality_signal"]) or {}
                calls[d["job_id"] or d["content_piece_id"]].append(d)
    finally:
        await conn.close()

    sets = {**SETS, "natural_post_r7": natural}
    rows, cases = {}, []
    for name, members in sets.items():
        rows[name] = []
        for pid in members:
            p = pieces.get(pid)
            if p is None or p["status"] == "failed":  # same rule as the r6/r7 readouts
                continue
            row, cs = piece_rows(name, p, calls.get(p["job_id"] or pid, []))
            rows[name].append(row)
            cases.extend(cs)

    per_set = {name: pool_metrics(r) for name, r in rows.items()}
    repro = {}
    for name, (num, den) in EXPECTED.items():
        got = per_set[name]["any_blocking_added"]
        repro[name] = {"expected": f"{num}/{den}", "got": f"{got['num']}/{got['den']}",
                       "match": (got["num"], got["den"]) == (num, den)}
    pools = {name: pool_metrics([r for s in members for r in rows[s]]) for name, members in POOLS.items()}
    f9_items = [it for c in cases for it in c["added"].get(F9, [])]
    out = {
        "script": "s245_f9_pool (AA-865)", "at": _now(), "db_role": role, "helpers": HELPERS,
        "target_rate": TARGET_RATE, "natural_after": NATURAL_AFTER.isoformat(),
        "missing_pieces": sorted(i for i in known if i not in pieces),
        "failed_pieces_excluded": sorted(i for i in ids if i in pieces and pieces[i]["status"] == "failed"),
        "reproduction_check": repro, "reproduction_all_match": all(v["match"] for v in repro.values()),
        "pools": pools, "per_set": per_set,
        "natural_post_r7": {"pieces": len(rows["natural_post_r7"]),
                            "created_by": dict(C.Counter(str(r["created_by"]) for r in rows["natural_post_r7"]))},
        "cases_summary": {
            "retry_added_cases": len(cases),
            "f9_cases": sum(1 for c in cases if F9 in c["added"]),
            "f9_items": len(f9_items),
            "suggested_class": dict(C.Counter(str(it.get("suggested_class", "")).split(" (")[0] for it in f9_items)),
        },
        "cases": cases,
        "pieces": {name: r for name, r in rows.items()},
    }
    try:
        import boto3
        boto3.client("s3", region_name=REGION).put_object(
            Bucket=S3_BUCKET, Key=S3_OUT_KEY, Body=json.dumps(out, default=str, ensure_ascii=False).encode(),
            ContentType="application/json")
        out["s3"] = f"s3://{S3_BUCKET}/{S3_OUT_KEY}"
    except Exception as e:  # noqa: BLE001
        out["s3_error"] = repr(e)[:200]
    return out


def summary(out: dict) -> dict:
    def short(m):
        return {"n": m["retries"], "any": [m["any_blocking_added"]["num"], m["any_blocking_added"]["ci95"]],
                "f9": [m["f9_cta_fact_added"]["num"], m["f9_cta_fact_added"]["ci95"]]}
    return {"script": out.get("script"), "at": out.get("at"), "role": out.get("db_role"),
            "s3": out.get("s3"), "s3_error": out.get("s3_error"), "repro_ok": out.get("reproduction_all_match"),
            "missing": len(out.get("missing_pieces") or []), "helpers_ok": not str(out.get("helpers")).startswith(
                "unavailable"),
            "pools": {k: short(v) for k, v in (out.get("pools") or {}).items()},
            "cases": out.get("cases_summary"), "elapsed_s": out.get("elapsed_s")}


if __name__ == "__main__":
    t0 = time.time()
    try:
        result = asyncio.run(main())
        result["elapsed_s"] = round(time.time() - t0, 1)
        doc = result if STDOUT_FULL else summary(result)
    except Exception as e:  # noqa: BLE001
        doc = {"script": "s245_f9_pool (AA-865)", "fatal": repr(e)[:500]}
    _STDOUT.write(json.dumps(doc, default=str, ensure_ascii=False) + "\n")
    _STDOUT.flush()
