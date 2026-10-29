"""Generate the LLM route and model table (docs/generated/llm-routes.md) from a snapshot of the Model Gateway config.

AA-900 (APP-06-routes). The routes (`shared.llm_role_config`) and the model catalog (`shared.llm_model_catalog`) are
runtime data the admin edits in CIS Settings, so the table is regenerated from a snapshot of those two tables, never
edited by hand. Two committed files: the snapshot `docs/generated/llm-routes.snapshot.json` (the generator's input)
and the page `docs/generated/llm-routes.md` (its output). `check` proves the page is what `render` makes from the
snapshot; `test_llm_routes.py` runs it in the docs-lint "Unit tests of the lint tools" step.

Commands (rendering is standard library only; `dump` also needs asyncpg, present in the CIS containers):

  dump                 inside the CIS api / worker container (S3-mediated ECS exec): read both tables as cis_app
                       (DATABASE_URL, SSL, read-only transaction) and print the snapshot between the markers
                       `--- AA900 LLM ROUTES SNAPSHOT ---` / `--- END ---`. No write, no model call.
  import <exec-log>    on a laptop: take the snapshot out of a saved ECS exec output, write the snapshot file and
                       render the page.
  render               render the page from the committed snapshot.
  check                exit 1 when the committed page differs from the render of the committed snapshot, or when
                       the snapshot holds an account ID or an ARN (the repos are public).

Only non-secret columns are read. `bedrock_profile_ids` is reduced to its account keys (acc2 / acc3): the profile
values can carry ARNs. `updated_by` (a person) is not read. Any 12-digit number or ARN left in a text value is
replaced by `[redacted]` at dump time and refused by `check`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO_ROOT / "docs" / "generated" / "llm-routes.snapshot.json"
PAGE = REPO_ROOT / "docs" / "generated" / "llm-routes.md"
SCHEMA = "aa900-llm-routes/1"
GENERATOR = "tools/docs/gen_llm_routes.py"
BEGIN, END = "--- AA900 LLM ROUTES SNAPSHOT ---", "--- END ---"

ROUTES_SQL = """
    SELECT stage, role, provider, model_id, coalesce(fallback_model_ids, '{}') AS fallback_model_ids,
           shadow_model_id, shadow_sample_pct, account_route, is_active, updated_at
      FROM shared.llm_role_config ORDER BY stage
"""
MODELS_SQL = """
    SELECT model_key, label, vendor, provider, api_style,
           ARRAY(SELECT jsonb_object_keys(bedrock_profile_ids) ORDER BY 1) AS bedrock_accounts,
           wire_model, callable_via, supports_temperature, max_output_tokens,
           price_in_per_mtok::text AS price_in_per_mtok, price_out_per_mtok::text AS price_out_per_mtok,
           price_cache_read_per_mtok::text AS price_cache_read_per_mtok,
           price_cache_write_per_mtok::text AS price_cache_write_per_mtok,
           price_source, enabled, blocked_reason
      FROM shared.llm_model_catalog ORDER BY model_key
"""

_ID_RE = re.compile(r"arn:aws[a-z-]*:[^\s\"']*|(?<!\d)\d{12}(?!\d)")
_APPS = (("tp_", "TripPlanner"),)


# ── snapshot ──────────────────────────────────────────────────────────────────────────────────────────────────────

def redact(value):
    """Strings lose any ARN or 12-digit number; lists and dicts are walked; other values are kept."""
    if isinstance(value, str):
        return _ID_RE.sub("[redacted]", value)
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    return value


def find_ids(value) -> list[str]:
    """Every ARN or 12-digit number left in the snapshot (the `check` refusal)."""
    if isinstance(value, str):
        return _ID_RE.findall(value)
    if isinstance(value, list):
        return [x for v in value for x in find_ids(v)]
    if isinstance(value, dict):
        return [x for v in value.values() for x in find_ids(v)]
    return []


def normalise(snapshot: dict) -> dict:
    """Sorted, typed snapshot: routes by stage, models by key, lists as lists. Raises ValueError on a bad shape."""
    if snapshot.get("schema") != SCHEMA:
        raise ValueError(f"snapshot schema must be {SCHEMA!r}")
    routes = sorted((dict(r) for r in snapshot.get("routes") or []), key=lambda r: r["stage"])
    models = sorted((dict(m) for m in snapshot.get("models") or []), key=lambda m: m["model_key"])
    for r in routes:
        r["fallback_model_ids"] = list(r.get("fallback_model_ids") or [])
        if r.get("updated_at"):
            r["updated_at"] = str(r["updated_at"])[:10]
    for m in models:
        m["bedrock_accounts"] = sorted(m.get("bedrock_accounts") or [])
        m["callable_via"] = list(m.get("callable_via") or [])
    return {"schema": SCHEMA, "captured_at": snapshot.get("captured_at"), "source": snapshot.get("source"),
            "routes": redact(routes), "models": redact(models)}


def snapshot_text(snapshot: dict) -> str:
    return json.dumps(normalise(snapshot), indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def extract(log_text: str) -> dict:
    """The snapshot JSON between the markers of a raw ECS exec output (session banners and CR characters ignored)."""
    text = log_text.replace("\r", "")
    start, stop = text.rfind(BEGIN), -1
    if start >= 0:
        stop = text.find(END, start + len(BEGIN))
    if start < 0 or stop < 0:
        raise ValueError("no snapshot markers in the log")
    return normalise(json.loads(text[start + len(BEGIN):stop]))


# ── render ────────────────────────────────────────────────────────────────────────────────────────────────────────

def _app(stage: str) -> str:
    for prefix, app in _APPS:
        if stage.startswith(prefix):
            return app
    return "CIS"


def _cell(value) -> str:
    if value is None or value == "" or value == []:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return ", ".join(f"`{v}`" for v in value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _price(m: dict, a: str, b: str) -> str:
    x, y = m.get(a), m.get(b)
    if x is None and y is None:
        return "-"
    return f"{_num(x)} / {_num(y)}"


def _num(v) -> str:
    if v is None:
        return "-"
    s = str(v)
    return s.rstrip("0").rstrip(".") if "." in s else s


def fingerprint(snapshot: dict) -> str:
    return hashlib.sha256(snapshot_text(snapshot).encode("utf-8")).hexdigest()


def render(snapshot: dict) -> str:
    snap = normalise(snapshot)
    captured = snap.get("captured_at") or "not captured"
    reviewed = (snap.get("captured_at") or "2026-10-29")[:10]
    head = f"""---
id: APP-06-routes
title: "LLM routes and models"
description: "Every Model Gateway stage with its route (primary, fallbacks, shadow) and every catalog model with vendor, provider, prices and the stages using it; generated from a snapshot of shared.llm_role_config and shared.llm_model_catalog."
type: reference
status: active
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, tripplanner-lambda]
last_reviewed: {reviewed}
review_every_days: 30
generated: true
generator: {GENERATOR}
related: [APP-06-prompts, APP-06-eval, CAT-01, AA-900]
---

# LLM routes and models

<!-- GENERATED by {GENERATOR} from shared.llm_role_config + shared.llm_model_catalog@{captured} - do not edit -->
<!-- docs-fingerprint: {fingerprint(snapshot)} -->

> **Generated - do not edit.** Source: a read-only snapshot of `shared.llm_role_config` and
> `shared.llm_model_catalog` on the shared Dev RDS, captured {captured}
> ([`llm-routes.snapshot.json`](llm-routes.snapshot.json)). The admin changes routes and models in CIS Settings
> (LLM models); after such a change, or a migration that touches either table, capture a new snapshot and render
> this page (`{GENERATOR}`, module docstring). The docs lint fails when this page and the snapshot disagree.

A route is the order the gateway tries models for a stage: the primary, then each fallback; the shadow (when set)
gets a sampled copy of the call for comparison and never serves the result. Prompts per stage are in the CIS prompt
register (`docs/llm/prompt-register.md` in AA-CIS-App). A prompt, model or route change records an eval run ID in its
PR (engineering handbook §5.7).
"""
    if not snap["routes"] and not snap["models"]:
        return head + """
## No snapshot yet

The snapshot has no rows: it has not been captured from the database yet. Run `dump` in the CIS container and
`import` the output (see the generator's docstring).
"""
    used: dict[str, list[str]] = {}
    for r in snap["routes"]:
        for key in [r.get("model_id"), *r["fallback_model_ids"], r.get("shadow_model_id")]:
            if key:
                used.setdefault(key, [])
                if r["stage"] not in used[key]:
                    used[key].append(r["stage"])
    lines = [head, "## Routes", "",
             f"{len(snap['routes'])} stages. Account route `acc3` = the LLM account (Bedrock satellite); `-` = the "
             "model's own provider path.", "",
             "| Stage | App | Role | Active | Primary | Fallbacks (in order) | Shadow | Account route | Updated |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in snap["routes"]:
        shadow = (f"`{r['shadow_model_id']}` ({r.get('shadow_sample_pct') or 0} %)" if r.get("shadow_model_id")
                  else "-")
        lines.append(f"| `{r['stage']}` | {_app(r['stage'])} | {_cell(r.get('role'))} | {_cell(r.get('is_active'))} | "
                     f"`{r.get('model_id')}` | {_cell(r['fallback_model_ids'])} | {shadow} | "
                     f"{_cell(r.get('account_route'))} | {_cell(r.get('updated_at'))} |")
    lines += ["", "## Models", "",
              f"{len(snap['models'])} catalog models. Prices in USD per million tokens (input / output; cache read / "
              "write). `Used by` lists the stages whose route names the model (primary, fallback or shadow).", "",
              "| Model key | Label | Vendor | Provider | API style | Bedrock accounts | Enabled | Price in / out | "
              "Cache read / write | Max output | Used by |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in snap["models"]:
        enabled = _cell(m.get("enabled"))
        if not m.get("enabled") and m.get("blocked_reason"):
            enabled = f"no: {_cell(m['blocked_reason'])}"
        lines.append(f"| `{m['model_key']}` | {_cell(m.get('label'))} | {_cell(m.get('vendor'))} | "
                     f"{_cell(m.get('provider'))} | {_cell(m.get('api_style'))} | {_cell(m['bedrock_accounts'])} | "
                     f"{enabled} | {_price(m, 'price_in_per_mtok', 'price_out_per_mtok')} | "
                     f"{_price(m, 'price_cache_read_per_mtok', 'price_cache_write_per_mtok')} | "
                     f"{_cell(m.get('max_output_tokens'))} | {_cell(used.get(m['model_key']))} |")
    unknown = sorted(k for k in used if k not in {m["model_key"] for m in snap["models"]})
    if unknown:
        lines += ["", "Route keys with no catalog row (legacy keys the gateway resolves in code): "
                  + ", ".join(f"`{k}`" for k in unknown) + "."]
    return "\n".join(lines) + "\n"


def check(snapshot_path: Path = SNAPSHOT, page_path: Path = PAGE) -> list[str]:
    """Problems with the committed pair (empty = good)."""
    problems = []
    if not snapshot_path.is_file() or not page_path.is_file():
        return [f"missing {p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p}"
                for p in (snapshot_path, page_path) if not p.is_file()]
    raw = json.loads(snapshot_path.read_text(encoding="utf-8"))
    ids = find_ids(raw)
    if ids:
        problems.append(f"snapshot holds {len(ids)} account ID / ARN value(s): re-dump (dump redacts them)")
    if snapshot_path.read_text(encoding="utf-8") != snapshot_text(raw):
        problems.append("snapshot is not in normalised form: write it with `import` (sorted keys and rows)")
    if page_path.read_text(encoding="utf-8") != render(raw):
        problems.append("page differs from the render of the snapshot: run `render`, never edit the page")
    return problems


# ── dump (inside the CIS container) ───────────────────────────────────────────────────────────────────────────────

async def dump() -> dict:
    import asyncpg

    dsn = (os.environ.get("DATABASE_URL") or "").strip()
    if not dsn:
        raise SystemExit("DATABASE_URL is not set (run inside the CIS api / worker container)")
    conn = await asyncpg.connect(dsn, ssl="require")
    try:
        async with conn.transaction(readonly=True):
            routes = [dict(r) for r in await conn.fetch(ROUTES_SQL)]
            models = [dict(r) for r in await conn.fetch(MODELS_SQL)]
    finally:
        await conn.close()
    for r in routes:
        r["updated_at"] = r["updated_at"].date().isoformat() if r.get("updated_at") else None
    return normalise({"schema": SCHEMA, "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                      "source": "shared.llm_role_config + shared.llm_model_catalog (aa-cis-dev-db, read as cis_app)",
                      "routes": routes, "models": models})


def _write(snapshot: dict, snapshot_path: Path, page_path: Path) -> None:
    snapshot_path.write_text(snapshot_text(snapshot), encoding="utf-8")
    page_path.write_text(render(snapshot), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AA-900 LLM route and model table")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dump")
    imp = sub.add_parser("import")
    imp.add_argument("log")
    sub.add_parser("render")
    sub.add_parser("check")
    a = ap.parse_args(argv)
    if a.cmd == "dump":
        import asyncio
        snap = asyncio.run(dump())
        print(BEGIN)
        print(json.dumps(snap, ensure_ascii=False, sort_keys=True))
        print(END)
        return 0
    if a.cmd == "import":
        snap = extract(Path(a.log).read_text(encoding="utf-8", errors="replace"))
        _write(snap, SNAPSHOT, PAGE)
        print(f"wrote {SNAPSHOT.relative_to(REPO_ROOT)} ({len(snap['routes'])} routes, {len(snap['models'])} models) "
              f"and {PAGE.relative_to(REPO_ROOT)}")
        return 0
    if a.cmd == "render":
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        _write(snap, SNAPSHOT, PAGE)
        print(f"wrote {PAGE.relative_to(REPO_ROOT)}")
        return 0
    problems = check()
    for p in problems:
        print(f"llm-routes: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
