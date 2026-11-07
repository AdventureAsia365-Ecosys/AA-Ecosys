#!/usr/bin/env python3
"""Stop hook (AA-1024 G19, S272): do not offer to stop while the session checklist has open, unblocked work.

Lesson family 14, behaviour half (S228, restated S248, S249, S263; memory "finish before closing", "do it, do not
remind"): the orchestrator ended a turn by asking whether to go on, or by proposing to close the session, while
unchecked items it could do itself were still on the live checklist (.tmp-session/S<nnn>-checklist.md).

When the main session is about to stop, this hook reads the last assistant message of the transcript. It blocks the
stop once (exit 2), listing the open items, only when ALL of these hold:
- a sentence of the LAST PARAGRAPH asks to go on or to close the session ("Shall I continue?", "Anh có muốn em làm
  tiếp phần deploy CIS không?", "Nghiệp muốn em làm tiếp (...), hay chốt phiên ở đây?", "Anh muốn em vào phần kết
  phiên luôn không?"), or the message ends with a proposal to close ("I can close the session now.", "Đề xuất dừng
  phiên ở đây.");
- every question of that paragraph is such an offer (any other question is a real choice or clarification);
- the last paragraph and the line above it carry no approval context: a cost figure or paid run, MFA / an AWS session, a DRY RUN or a
  delete, an approval word (duyệt, đồng ý, approve), a new issue, or labelled options ((a)/(b), phương án, chọn);
- the newest checklist (changed in the last 24 h) has `- [ ]` items without a blocked marker.
A plain statement that mentions the close is not touched: the critic of the design showed that a nudge on every stop
trains tag-gaming. `stop_hook_active` (Claude Code sets it when the turn already continues because of a Stop hook)
lets the next stop through, so it never loops. The block text says never to start a paid run, a delete or anything
else that needs a yes because of it.

Blocked markers (the item waits on someone, a date or another step, so it does not count): [blocked ...], chờ / wait /
waiting, hẹn / ≥<date>, MFA, paid-approval, "tech lead" / "Nghiệp duyệt", Jira draft approval, and dependency waits
(sau khi / sau / chỉ khi / khi ... xong / after / once / until). Reversibility stays judgement.

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

# What counts as an offer to stop (review fix pass 2, S272). The reviewer replayed 2,682 turn-final messages: the
# end-anchored last-line pattern missed 13 real continue-or-stop questions ("..., hay chốt phiên ở đây?", "Anh muốn em
# vào phần kết phiên luôn không?", "Anh có muốn em làm tiếp phần deploy CIS không?" followed by one more line). Now
# every SENTENCE of the last paragraph is read: a question that asks to go on or to close, or a proposal to close that
# ends the message. A statement that only mentions the close ("em ghi vào log khi chốt phiên") is not an offer.
_CONT = r"(?:(?:làm|chạy|đi|code|ship) (?:tiếp|thêm)|tiếp tục|go on|keep going|continue|proceed)"
_CLOSE_VI = r"(?:dừng|chốt|đóng|kết thúc|kết) (?:phiên|session)"
OFFER_QUESTION = re.compile(
    r"(?i)(?:"
    r"\b(?:shall|should|can|may) (?:i|we)\b[^?]{0,60}\b(?:continue|go on|keep going|proceed|stop|close|wrap(?: up)?|"
    r"end)\b"
    r"|\b(?:do you want|want me to|would you like)\b[^?]{0,60}\b(?:continue|go on|keep going|proceed|stop|close|"
    r"wrap(?: up)?|end)\b"
    # Vietnamese: "... (em) làm tiếp ... không / chứ / nhé / nha?", "em tiếp tục deploy nhé?", "hay làm tiếp?"
    rf"|{_CONT}[^?]{{0,60}}(?:không|chứ|nhé|nha|ạ|\?)"
    rf"|\bhay\b[^?]{{0,60}}{_CONT}"
    rf"|(?:\b(?:em|mình|tôi) tiếp\b)[^?]{{0,60}}(?:không|chứ|nhé|nha)"
    # Vietnamese: a question about closing the session ("..., hay chốt phiên ở đây?", "vào phần kết phiên luôn không?")
    rf"|{_CLOSE_VI}"
    r")[^?]*\?\s*$")
OFFER_PROPOSAL = re.compile(
    r"(?i)(?:"
    r"\b(?:i|we) (?:can|could|will|'ll|would|suggest|propose)(?: now)? (?:close|closing|end|ending|wrap up|"
    r"wrapping up|stop|stopping) (?:the|this) session\b[^.?!]*[.!]?"
    rf"|(?:đề xuất|đề nghị|xin phép)\s+(?:\w+\s+){{0,2}}{_CLOSE_VI}[^?!]{{0,80}}[.!]?"
    r")\s*$")
# A choice the user must make: a paid run (any cost figure), MFA / an AWS session, a DRY RUN or a delete, an approval,
# a new issue (the Linear rule asks first), or labelled options. Anywhere in the last paragraph (or on the line right
# above it), the message is never blocked (S272 replay: "Thử 3 tour xong: tổng $0.41.\nAnh cho em chạy tiếp không?" was blocked when only the
# last line was read).
APPROVAL_ASK = re.compile(
    r"(?i)\bpaid\b|\bUSD\b|\$\s*\d|\d\s*\$|\bcosts? (?:about|around|roughly|~|\$|\d)|chi phí|\btốn\b|trả (?:phí|tiền)|/tháng|per month|"
    r"\bMFA\b|aws sts|get-caller-identity|nhập mã|ExpiredToken|\bSTS\b|phiên AWS|AWS session|"
    r"DRY.?RUN|\bxoá|\bxóa|\bdelete|\bdestroy|\bdrop\b|\btruncate|\bpurge|"
    r"\bduyệt|approv|đồng ý|cho phép|\bconsent|"
    r"tạo (?:một |1 |các |\d+ )?issue|(?:create|open) (?:a |an |the |\d+ )?(?:new )?issue|"
    r"\((?:[a-d]|[1-4])\)|\bphương án\b|\boption [a-d1-4]\b|\bchọn\b")
SENTENCE_END = re.compile(r"(?<=[.?!])\s+|\n+")


def last_paragraphs(text: str, n: int) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return paras[-n:]


def is_offer_to_stop(text: str) -> bool:
    """True when the last paragraph asks to go on / to close, has no other question, and no approval context."""
    plain = re.sub(r"[*_`]", "", text)
    paras = last_paragraphs(plain, 2)
    if not paras:
        return False
    # the whole last paragraph, plus the line right above it (a result line, then a blank line, then the question)
    context = paras[-1] + ("\n" + paras[0].splitlines()[-1] if len(paras) == 2 else "")
    if APPROVAL_ASK.search(context):
        return False
    sentences = [s.strip() for s in SENTENCE_END.split(paras[-1][-1200:]) if s and s.strip()]
    questions = [s for s in sentences if s.endswith("?")]
    offers = [s for s in questions if OFFER_QUESTION.search(s)]
    if questions and len(offers) != len(questions):
        return False  # another question is a real choice or clarification the user must answer
    return bool(offers) or bool(sentences and OFFER_PROPOSAL.search(sentences[-1]))


BLOCKED = re.compile(
    r"(?i)\[blocked|\bblocked\b|\bchờ\b|\bwait(?:ing)?\b|\bhẹn\b|≥\s*\d|>=\s*\d|\bMFA\b|paid-approval|tech lead|"
    r"Nghiệp (?:duyệt|nhập|chốt|nhắn|bật)|duyệt Jira|Jira draft|"
    # a dependency wait: the item is due only after another step (S272: "Push l5 CIS ... chỉ khi lane CIS đã xong")
    r"sau khi|\bsau\b|chỉ khi|\bkhi\b.*\bxong\b|\bafter\b|\bonce\b|\buntil\b")
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
    if not text.strip() or not is_offer_to_stop(text):
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
            "Do the ones you can do now (memory: finish before closing; do it, do not remind). Never start a paid "
            "run, a delete, a merge the rules hold, or anything else that needs the tech lead's yes because of this "
            "message. For an item that really waits on someone, a date or a decision, mark it in the checklist "
            "([blocked: <who/what>], chờ ..., hẹn ...) and say so in one line. Then end the turn.")


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
