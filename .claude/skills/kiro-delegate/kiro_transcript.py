"""Render a kiro-cli session (.jsonl from ~/.kiro/sessions/cli/) as a readable transcript.

Compact by design (the reviewer reads all of it, so it must carry evidence, not bulk):
  - shell calls: the command + exit status + FULL stdout/stderr (outputs over LONG lines keep the
    first/last HEAD lines; the untrimmed text stays in session.jsonl);
  - file reads: path + range only — the file is in the repo, re-open it if needed;
  - file writes/edits: path + operation + size only — the change itself is in diff.patch;
  - other tools: input + result, trimmed the same way.
Thinking blocks are skipped (redacted by the model anyway).

usage: python3 kiro_transcript.py <session.jsonl> <out.md> [--full]
"""
import json
import sys

LONG = 200
HEAD = 80
READ_TOOLS = {"read", "fs_read", "glob", "grep"}
WRITE_TOOLS = {"write", "fs_write", "edit", "str_replace"}
SHELL_TOOLS = {"shell", "execute_bash"}


def _block(text: str) -> str:
    text = text if text.endswith("\n") else text + "\n"
    return "```\n" + text.replace("```", "ʼʼʼ") + "```\n"


def _trim(text: str, full: bool) -> str:
    lines = text.splitlines()
    if full or len(lines) <= LONG:
        return text
    return "\n".join(lines[:HEAD] + [f"... [{len(lines) - 2 * HEAD} lines trimmed — full text in session.jsonl] ..."]
                     + lines[-HEAD:])


def _result_text(content: list, full: bool) -> str:
    parts = []
    for c in content or []:
        d = c.get("data")
        if c.get("kind") == "json" and isinstance(d, dict) and ("stdout" in d or "stderr" in d):
            parts.append(f"[{d.get('exit_status', '')}]")
            if d.get("stdout"):
                parts.append("--- stdout ---\n" + _trim(d["stdout"], full))
            if d.get("stderr"):
                parts.append("--- stderr ---\n" + _trim(d["stderr"], full))
        elif c.get("kind") == "text":
            parts.append(_trim(str(d), full))
        else:
            parts.append(_trim(json.dumps(d, ensure_ascii=False, indent=1), full))
    return "\n".join(parts)


def _summary_of(name: str, inp: dict) -> str:
    if name in READ_TOOLS:
        ops = inp.get("operations") or [inp]
        return "; ".join(f"{o.get('mode', '')} {o.get('path', o.get('pattern', ''))}"
                         f"{' L' + str(o.get('start_line')) + '-' + str(o.get('end_line')) if o.get('start_line') else ''}"
                         for o in ops)
    if name in WRITE_TOOLS:
        body = inp.get("content") or inp.get("file_text") or inp.get("new_str") or ""
        return f"{inp.get('command', name)} {inp.get('path', '')} ({len(str(body))} chars — see diff.patch)"
    return ""


def render(lines: list[dict], full: bool = False) -> str:
    out = ["# Kiro session transcript\n"]
    calls: dict[str, tuple[int, str]] = {}
    n = 0
    for entry in lines:
        kind, data = entry.get("kind"), entry.get("data") or {}
        content = data.get("content") or []
        if kind == "Prompt":
            text = "\n".join(str(c.get("data")) for c in content if c.get("kind") == "text")
            out.append("## Prompt\n" + _block(text))
        elif kind == "AssistantMessage":
            for c in content:
                if c.get("kind") == "text" and str(c.get("data", "")).strip():
                    out.append("**Kiro:** " + str(c["data"]).strip() + "\n")
                elif c.get("kind") == "toolUse":
                    n += 1
                    tu = c["data"]
                    name = tu.get("name") or ""
                    calls[tu.get("toolUseId")] = (n, name)
                    inp = dict(tu.get("input") or {})
                    purpose = inp.pop("__tool_use_purpose", "")
                    out.append(f"### Call {n}: `{name}`" + (f" — {purpose}" if purpose else "") + "\n")
                    short = "" if full else _summary_of(name, inp)
                    if short:
                        out.append(f"`{short}`\n")
                    elif name in SHELL_TOOLS:
                        out.append(_block(f"$ {inp.get('command', '')}" + (f"   # in {inp['working_dir']}" if inp.get("working_dir") else "")))
                    else:
                        out.append(_block(_trim(json.dumps(inp, ensure_ascii=False, indent=1), full)))
        elif kind == "ToolResults":
            for c in content:
                if c.get("kind") != "toolResult":
                    continue
                r = c["data"]
                num, name = calls.get(r.get("toolUseId"), ("?", ""))
                head = f"#### Result {num} ({r.get('status')})"
                if not full and (name in READ_TOOLS or name in WRITE_TOOLS) and r.get("status") == "success":
                    out.append(head + " — content omitted (repo / diff.patch)\n")
                    continue
                out.append(head + "\n" + _block(_result_text(r.get("content"), full)))
    out.append(f"\n_{n} tool calls._\n")
    return "\n".join(out)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    with open(dst, "w", encoding="utf-8") as f:
        f.write(render(rows, full="--full" in sys.argv))
