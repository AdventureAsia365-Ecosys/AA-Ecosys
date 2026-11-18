#!/usr/bin/env python3
"""AA-1135 — keep the CIS byte copy of the delivery metrics engine in step with this repo.

The CIS API computes a custom date range of Platform › Delivery with a byte copy of tools/delivery/delivery_engine.py
(AA-CIS-App api/services/delivery_engine.py) and its lock file (api/services/delivery_engine.lock.json: source path,
sha256, definitions version). The published summary carries the engine's sha256 (definitions.engine_sha256); CIS
refuses a custom range while its copy differs, so a collector change shows up as "custom ranges paused" until the copy
is refreshed with this tool in a CIS pull request.

    python3 tools/delivery/sync_engine.py --cis apps/AA-CIS-App            # write the copy, the lock and the fixture
    python3 tools/delivery/sync_engine.py --cis apps/AA-CIS-App --check    # exit 1 when the copy differs

It also writes the CIS parity fixture (tests/unit/fixtures/delivery_range/: the summary and the day files the collector
publishes for the invented repo of tools/delivery/fixtures/demo_github.json), so the CIS test can pin custom == preset
with the copied engine.

Stdlib only. Exit 0 = in step (or written), 1 = differs (--check), 2 = bad usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ENGINE = Path(__file__).with_name("delivery_engine.py")
COPY = Path("api/services/delivery_engine.py")
LOCK = Path("api/services/delivery_engine.lock.json")
SOURCE = "AA-Ecosys/tools/delivery/delivery_engine.py"
FIXTURE = Path("tests/unit/fixtures/delivery_range")


def write_fixture(folder: Path) -> int:
    """The published summary (trimmed to what a range needs) and day files of the invented demo repo; files written."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import delivery_metrics as dm
    import test_delivery_metrics as t

    cfg, store, report, _fake = t.collected()
    summary = dm.summarize(cfg, store, t.NOW, {"repo": "AA-Ecosys"}, report)
    trimmed = {k: summary[k] for k in ("format", "generated_at", "environment", "definitions", "config")}
    trimmed["apps"] = [{"id": a["id"], "name": a["name"], "repo": a["repo"], "complete_since": a["complete_since"],
                        "git": {"complete_since": a["git"]["complete_since"]}, "ranges": a["ranges"]}
                       for a in summary["apps"]]
    if folder.exists():
        for old in sorted(folder.rglob("*"), reverse=True):
            old.unlink() if old.is_file() else old.rmdir()
    days = {(e.get("time") or "")[:10] for e in store.events.values()}
    dm.write_outputs(folder, trimmed, store.day_files(days))
    return sum(1 for p in folder.rglob("*") if p.is_file())


def lock_of(data: bytes) -> dict:
    m = re.search(rb'^DEFINITIONS_VERSION = "([^"]+)"', data, re.M)
    return {
        "about": "Byte copy of the root collector's delivery engine (AA-1135). Never edit the copy: change the root "
        "file, then run the root tools/delivery/sync_engine.py --cis <this repo>.",
        "source": SOURCE,
        "sha256": hashlib.sha256(data).hexdigest(),
        "definitions_version": m.group(1).decode() if m else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--cis", type=Path, required=True, help="the AA-CIS-App checkout")
    ap.add_argument("--check", action="store_true", help="only compare; exit 1 when the copy or its lock differs")
    args = ap.parse_args(argv)
    if not (args.cis / "api" / "services").is_dir():
        print(f"{args.cis}: not an AA-CIS-App checkout (api/services missing)", file=sys.stderr)
        return 2
    data = ENGINE.read_bytes()
    lock = lock_of(data)
    copy, lock_path = args.cis / COPY, args.cis / LOCK
    have = copy.read_bytes() if copy.exists() else None
    have_lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else None
    if args.check:
        if have != data or have_lock != lock:
            print(f"{copy}: differs from {SOURCE} (sha256 {lock['sha256'][:12]}); run without --check to refresh")
            return 1
        print(f"{copy}: in step (sha256 {lock['sha256'][:12]})")
        return 0
    copy.write_bytes(data)
    lock_path.write_text(json.dumps(lock, indent=1) + "\n", encoding="utf-8")
    n = write_fixture(args.cis / FIXTURE)
    print(f"wrote {copy}, {lock_path} and {n} fixture files (sha256 {lock['sha256'][:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
