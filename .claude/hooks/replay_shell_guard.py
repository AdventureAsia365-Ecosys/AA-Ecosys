#!/usr/bin/env python3
"""Replay aa_shell_guard.py over past Bash commands (AA-1024 G2): hit counts per rule, for false-positive review.

    python3 .claude/hooks/replay_shell_guard.py                       # this machine's AA-Ecosys transcripts
    python3 .claude/hooks/replay_shell_guard.py --out hits.jsonl a.jsonl b.jsonl

Reads Claude Code transcripts (read-only; default ~/.claude/projects/-home-nghiep-projects-AA-Ecosys/*.jsonl), takes
every Bash tool_use command once (deduplicated by text), runs the hook's rules on it and prints, per rule, how many
commands it would refuse. RAM-1 depends on the live memory, so the replay counts the commands the heavy classifier
picks (they are refused only while memory is low), plus the lane pytest runs it refuses whatever the memory. Scripts a
command ran are read from disk as they are now (a script deleted since is skipped). --out writes every hit (rule, detail, command) as JSON lines for review. Prints no command
text unless --show N is given. Nothing is written except --out.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aa_shell_guard as guard  # noqa: E402

DEFAULT_GLOB = os.path.expanduser("~/.claude/projects/-home-nghiep-projects-AA-Ecosys/*.jsonl")


def commands(paths: list[str]):
    """Yield every Bash tool_use command in the transcripts."""
    for p in paths:
        try:
            fh = open(p, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"name":"Bash"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = ((d.get("message") or {}).get("content")) or []
                if not isinstance(content, list):
                    continue
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") == "Bash":
                        cmd = (item.get("input") or {}).get("command")
                        if isinstance(cmd, str) and cmd.strip():
                            yield cmd


def replay(cmds, proc_low: bool = False) -> tuple[int, Counter, list[dict], int]:
    seen: set[str] = set()
    hits: list[dict] = []
    counts: Counter = Counter()
    heavy = 0
    for cmd in cmds:
        if cmd in seen:
            continue
        seen.add(cmd)
        try:
            r = guard.check(cmd, proc=Path("/nonexistent-proc"))  # memory unreadable -> RAM-1 never fires here
        except Exception as e:  # noqa: BLE001 - report, keep going
            counts["ERROR"] += 1
            hits.append({"rule": "ERROR", "detail": f"{type(e).__name__}: {e}", "command": cmd})
            continue
        if r:
            counts[r.rule] += 1
            hits.append({"rule": r.rule, "detail": r.detail, "command": cmd})
        texts = guard.texts_of(cmd)
        if any(guard.heavy_command(w) for t in texts for w in guard.simple_commands(t.skeleton)):
            heavy += 1
    return len(seen), counts, hits, heavy


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", help="transcript .jsonl files (default: this project's transcripts)")
    ap.add_argument("--out", help="write every hit as JSON lines here")
    ap.add_argument("--show", type=int, default=0, help="print the first N hit commands per rule (truncated)")
    a = ap.parse_args(argv)
    paths = a.paths or sorted(glob.glob(DEFAULT_GLOB))
    total, counts, hits, heavy = replay(commands(paths))
    print(f"transcripts: {len(paths)}  distinct Bash commands: {total}")
    for rule in guard.RULE_IDS:
        if rule == "RAM-1":
            print(f"  RAM-1   heavy commands (refused only while MemAvailable is low): {heavy}; refused whatever the "
                  f"memory (lane pytest -n > 2 / whole test directory): {counts.get(rule, 0)}")
        else:
            print(f"  {rule:7} would refuse: {counts.get(rule, 0)}")
    if counts.get("ERROR"):
        print(f"  ERROR   hook errors: {counts['ERROR']}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            for h in hits:
                fh.write(json.dumps(h, ensure_ascii=False) + "\n")
    if a.show:
        for rule in sorted(counts):
            print(f"--- {rule}")
            for h in [x for x in hits if x["rule"] == rule][:a.show]:
                print("   ", h["detail"][:100], "::", h["command"].replace("\n", "\\n")[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
