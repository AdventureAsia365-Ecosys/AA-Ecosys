#!/usr/bin/env python3
"""Stop hook (AA-1024 G19, S272): do not offer to stop while the session checklist has open, unblocked work.

Lesson family 14, behaviour half (S228, restated S248, S249, S263; memory "finish before closing", "do it, do not
remind"): the orchestrator ended a turn by asking whether to go on, or by proposing to close the session, while
unchecked items it could do itself were still on the live checklist (.tmp-session/S<nnn>-checklist.md).

When the main session is about to stop, this hook reads the last assistant message of the transcript. Only when that
message OFFERS TO STOP OR ASKS PERMISSION TO GO ON (close / wrap up the session, "shall I continue", "dừng phiên",
"tiếp không", ...) AND the newest checklist (changed in the last 24 h) has `- [ ]` items without a blocked marker, it
blocks the stop once (exit 2), listing those items. A plain question (a real clarification) is not touched: the critic
of the design showed that a nudge on every stop trains tag-gaming. `stop_hook_active` (Claude Code sets it when the
turn already continues because of a Stop hook) lets the next stop through, so it never loops.

Blocked markers (the item waits on someone or a date, so it does not count): [blocked ...], chờ / wait / waiting,
hẹn / ≥<date>, MFA, paid-approval, "tech lead" / "Nghiệp duyệt", Jira draft approval. Reversibility stays judgement.

Failure: anything unreadable passes (exit 0). Test: python3 .claude/hooks/test_stop_open_work.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
MAX_AGE_S = 24 * 3600
MAX_LIST = 8

OFFER_STOP = re.compile(
    r"(?i)\b(?:shall|should|do you want|want me to|would you like|may) (?:i|me to)? ?(?:continue|go on|keep going|"
    r"proceed|stop|close|wrap)|\b(?:close|end|wrap up|stop) (?:the|this) session\b|\bsession close\b|"
    r"dừng (?:session|phiên)|(?:chốt|đóng|kết thúc|dừng) phiên|(?:có )?(?:làm )?tiếp (?:không|chứ|nhé\?)|"
    r"anh (?:có )?muốn (?:em|mình|tôi) (?:làm )?tiếp|(?:em|mình|tôi) (?:có )?(?:nên )?(?:dừng|chốt) (?:ở đây|lại)")
BLOCKED = re.compile(
    r"(?i)\[blocked|\bblocked\b|\bchờ\b|\bwait(?:ing)?\b|\bhẹn\b|≥\s*\d|>=\s*\d|\bMFA\b|paid-approval|tech lead|"
    r"Nghiệp (?:duyệt|nhập|chốt|nhắn|bật)|duyệt Jira|Jira draft")
OPEN_ITEM = re.compile(r"^\s*[-*] \[ \]\s+(.*)$")


def last_assistant_text(transcript: Path) -> str:
    """Text of the last assistant message in a Claude Code transcript (.jsonl)."""
    try:
        lines = transcript.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    for line in reversed(lines[-400:]):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str):
            return content
        texts = [c.get("text", "") for c in content or [] if isinstance(c, dict) and c.get("type") == "text"]
        if texts:
            return "\n".join(texts)
    return ""


def newest_checklist(root: Path, now: float | None = None) -> Path | None:
    now = now or time.time()
    try:
        found = sorted((p for p in (root / ".tmp-session").glob("S*-checklist.md") if p.is_file()),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return None
    if found and now - found[0].stat().st_mtime <= MAX_AGE_S:
        return found[0]
    return None


def open_items(checklist: Path) -> list[str]:
    try:
        text = checklist.read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        m = OPEN_ITEM.match(line)
        if m and not BLOCKED.search(m.group(1)):
            out.append(m.group(1).strip())
    return out


def check(data: dict, root: Path = ROOT, now: float | None = None) -> str | None:
    """The block reason, or None to let the session stop."""
    if data.get("stop_hook_active"):
        return None
    text = data.get("last_assistant_message") or ""
    if not text and data.get("transcript_path"):
        text = last_assistant_text(Path(data["transcript_path"]))
    tail = text.strip()[-600:]
    if not tail or not OFFER_STOP.search(tail):
        return None
    checklist = newest_checklist(root, now)
    if checklist is None:
        return None
    items = open_items(checklist)
    if not items:
        return None
    listed = "\n".join(f"  - {i[:140]}" for i in items[:MAX_LIST])
    more = f"\n  (+{len(items) - MAX_LIST} more)" if len(items) > MAX_LIST else ""
    return (f"Not yet: {checklist.name} still has {len(items)} open item(s) with no blocked marker:\n{listed}{more}\n"
            "Do the ones you can do now (memory: finish before closing; do it, do not remind). For an item that "
            "really waits on someone or a date, mark it in the checklist ([blocked: <who/what>], chờ ..., hẹn ...) "
            "and say so in one line. Then end the turn.")


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return 0
    if not isinstance(data, dict):
        return 0
    try:
        reason = check(data)
    except Exception as e:  # noqa: BLE001 - a hook bug must never trap the session
        print(f"stop_open_work: internal error {type(e).__name__}: {e} (stop allowed)", file=sys.stderr)
        return 0
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
