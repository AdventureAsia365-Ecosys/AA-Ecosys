#!/usr/bin/env python3
"""UAT takes that would be lost with their worktree (skill aa-uat-video §6-7; lesson S280/S281). No cost, no network
except `rclone` in upload / verify.

    python3 tools/uat/check_takes_uploaded.py [check] [PATH ...]      # PASS takes not packaged + uploaded; exit 1 if any
    python3 tools/uat/check_takes_uploaded.py upload --remote "aadrive:01 Video/UAT (kiểm thử nghiệm thu)/<round>/<app>" STEM ...
    python3 tools/uat/check_takes_uploaded.py verify --remote "<remote dir>" STEM ...

A take recorded in a worktree lives in <worktree>/tools/uat/out/ (gitignored): removing the worktree before packaging
and uploading loses it (S280 REH-08a PASS lost, recorded again in S281). PATH is a worktree root (its tools/uat/ is
read), a tools/uat directory, or by default this checkout's tools/uat. A take is out/<stem>.mp4 with
out/<stem>.result.json verdict PASS; it is safe only when out/packages/<stem>.zip exists AND out/packages/<stem>.uploaded
records a successful `rclone check` of that very zip (size + sha256). FAIL takes are not listed (they are re-recorded).

upload copies out/packages/<stem>.zip to the remote directory (`rclone copy`), then runs verify. verify runs
`rclone check <packages dir> <remote> --one-way --include <stem>.zip` and writes the marker only on exit 0 (0
differences): a zip uploaded by hand (skill §7) is recorded with verify. The hook rule aa_shell_guard UAT-1 refuses
`git worktree remove` / `rm -r` of a worktree that still has a PASS take without a marker.

Exit: 0 nothing pending / every upload checked | 1 PASS take(s) pending, or an rclone copy / check failed | 2 usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
MARKER_SUFFIX = ".uploaded"

Run = Callable[[list[str]], "tuple[int, str]"]


@dataclass
class Take:
    stem: str
    reason: str

    def line(self) -> str:
        return f"{self.stem}: {self.reason}"


def uat_dir(path: Path) -> Path:
    """tools/uat of a worktree root, or the directory itself when it is a tools/uat directory."""
    path = Path(path)
    sub = path / "tools" / "uat"
    return sub if sub.is_dir() else path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _verdict(result: Path) -> str | None:
    try:
        return str(json.loads(result.read_text(encoding="utf-8")).get("verdict") or "") or None
    except (OSError, ValueError, AttributeError):
        return None


def marker_ok(zp: Path) -> tuple[bool, str]:
    """(True, "") when <zip>.uploaded records an rclone check of this zip (same size and sha256)."""
    mk = zp.with_suffix(MARKER_SUFFIX)
    if not mk.is_file():
        return False, "zip never rclone-checked (no .uploaded marker)"
    try:
        data = json.loads(mk.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, "unreadable .uploaded marker"
    if data.get("size") != zp.stat().st_size or data.get("sha256") != _sha256(zp):
        return False, "zip changed after its rclone check (re-upload and verify)"
    return True, ""


def pending_takes(uat: Path) -> list[Take]:
    """PASS takes under <uat>/out that are not packaged and rclone-checked, in name order."""
    out = Path(uat) / "out"
    pkg = out / "packages"
    found: list[Take] = []
    if not out.is_dir():
        return found
    for mp4 in sorted(out.glob("*.mp4")):
        stem = mp4.stem
        if _verdict(out / f"{stem}.result.json") != "PASS":
            continue
        zp = pkg / f"{stem}.zip"
        if not zp.is_file():
            found.append(Take(stem, "PASS take with no zip in out/packages (python3 -I tools/uat/package.py uat ...)"))
            continue
        ok, why = marker_ok(zp)
        if not ok:
            found.append(Take(stem, why))
    return found


def _run(argv: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=3600)
    except FileNotFoundError:
        return 127, f"{argv[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _last(text: str) -> str:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return lines[-1] if lines else ""


def verify(uat: Path, stem: str, remote: str, run: Run = _run, now: Callable[[], datetime] | None = None) -> str | None:
    """rclone check of out/packages/<stem>.zip against the remote dir; writes the marker on 0 differences.
    Returns None when recorded, else what went wrong."""
    zp = Path(uat) / "out" / "packages" / f"{stem}.zip"
    if not zp.is_file():
        return f"{stem}: no {zp.name} in out/packages (package it first)"
    rc, text = run(["rclone", "check", str(zp.parent), remote, "--one-way", "--include", zp.name])
    if rc != 0:
        return f"{stem}: rclone check exit {rc}: {_last(text) or 'no output'} (no marker written)"
    stamp = (now or (lambda: datetime.now(timezone.utc)))().strftime("%Y-%m-%dT%H:%M:%SZ")
    zp.with_suffix(MARKER_SUFFIX).write_text(json.dumps(
        {"zip": zp.name, "size": zp.stat().st_size, "sha256": _sha256(zp), "remote": remote, "checked_at": stamp},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return None


def upload(uat: Path, stem: str, remote: str, run: Run = _run) -> str | None:
    """rclone copy of the zip into the remote dir, then verify."""
    zp = Path(uat) / "out" / "packages" / f"{stem}.zip"
    if not zp.is_file():
        return f"{stem}: no {zp.name} in out/packages (package it first)"
    rc, text = run(["rclone", "copy", str(zp), remote])
    if rc != 0:
        return f"{stem}: rclone copy exit {rc}: {_last(text) or 'no output'}"
    return verify(uat, stem, remote, run)


def report(paths: list[Path]) -> int:
    bad = 0
    for p in paths:
        u = uat_dir(p)
        takes = pending_takes(u)
        if not takes:
            print(f"ok   {u}: no PASS take waiting for upload")
            continue
        bad += len(takes)
        print(f"WAIT {u}: {len(takes)} PASS take(s) not packaged + uploaded:")
        for t in takes:
            print(f"     {t.line()}")
    if bad:
        print("Package (tools/uat/package.py uat <stem> \"<title>\"), then upload: python3 tools/uat/check_takes_uploaded.py "
              "upload --remote \"<remote dir>\" <stem> (or verify after a hand upload) before removing the worktree.")
    return 1 if bad else 0


def main(argv: list[str] | None = None, run: Run = _run) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("check", "upload", "verify", "-h", "--help"):
        argv.insert(0, "check")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="list PASS takes not packaged + uploaded (exit 1 if any)")
    c.add_argument("paths", nargs="*", type=Path, help="worktree roots or tools/uat dirs (default: this tools/uat)")
    for name in ("upload", "verify"):
        s = sub.add_parser(name)
        s.add_argument("--remote", required=True, help="rclone remote directory, e.g. aadrive:<folder>")
        s.add_argument("--uat", type=Path, default=HERE, help="the tools/uat directory (default: this one)")
        s.add_argument("stems", nargs="+")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        return report(a.paths or [HERE])
    fn = upload if a.cmd == "upload" else verify
    failed = 0
    for stem in a.stems:
        err = fn(uat_dir(a.uat), stem, a.remote, run)
        if err:
            failed += 1
            print(f"FAIL {err}")
        else:
            print(f"ok   {stem}: rclone check 0 differences, marker {stem}{MARKER_SUFFIX} written")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
