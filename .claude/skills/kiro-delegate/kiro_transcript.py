"""Render a kiro-cli session (.jsonl from ~/.kiro/sessions/cli/) as a readable transcript.

Every tool call is listed with its full input and its full result (stdout, stderr, exit status,
file contents) — the headless run.log only shows "Running: <cmd>", not what the command printed.
Thinking blocks are skipped (redacted by the model anyway).

usage: python3 kiro_transcript.py <session.jsonl> <out.md>
"""
import json
import sys


def _block(text: str) -> str:
    text = text if text.endswith("\n") else text + "\n"
    return "```\n" + text.replace("```", "ʼʼʼ") + "```\n"


def _result_text(content: list) -> str:
    parts = []
    for c in content or []:
        if c.get("kind") == "json":
            d = c.get("data") or {}
            if isinstance(d, dict) and ("stdout" in d or "stderr" in d):
                parts.append(f"[{d.get('exit_status', '')}]")
                if d.get("stdout"):
                    parts.append("--- stdout ---\n" + d["stdout"])
                if d.get("stderr"):
                    parts.append("--- stderr ---\n" + d["stderr"])
            else:
                parts.append(json.dumps(d, ensure_ascii=False, indent=1))
        elif c.get("kind") == "text":
            parts.append(str(c.get("data", "")))
        else:
            parts.append(json.dumps(c, ensure_ascii=False))
    return "\n".join(parts)


def render(lines: list[dict]) -> str:
    out = ["# Kiro session transcript\n"]
    calls: dict[str, int] = {}
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
                    calls[tu.get("toolUseId")] = n
                    inp = dict(tu.get("input") or {})
                    purpose = inp.pop("__tool_use_purpose", "")
                    out.append(f"### Tool call {n}: `{tu.get('name')}`" + (f" — {purpose}" if purpose else "") + "\n")
                    out.append(_block(json.dumps(inp, ensure_ascii=False, indent=1)))
        elif kind == "ToolResults":
            for c in content:
                if c.get("kind") != "toolResult":
                    continue
                r = c["data"]
                out.append(f"#### Result of call {calls.get(r.get('toolUseId'), '?')} ({r.get('status')})\n")
                out.append(_block(_result_text(r.get("content"))))
    out.append(f"\n_{n} tool calls._\n")
    return "\n".join(out)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    with open(dst, "w", encoding="utf-8") as f:
        f.write(render(rows))
