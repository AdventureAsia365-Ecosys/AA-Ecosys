#!/usr/bin/env python3
"""PostToolUse hook (AA-1136 slice 1): after an agent edits a file, lint that one file and point at its docs pages.

Registered for Edit|Write|MultiEdit in .claude/settings.json (through sync-post-edit.sh). For the file the tool wrote:
  1. finds its checkout from tool_input.file_path (a lane worktree under .tmp-session/wt/ works; cwd is not used) and
     records that checkout in the agent's state, so the Stop / SubagentStop dispatcher checks only repos it wrote;
  2. a Python file: ruff on that one file (the repo's own ruff config when one sits between the file and the checkout
     top, else only fatal rules E9,F63,F7,F82). TS/JS files get no lint here: eslint starts node (1-3 s), over budget;
  3. docs impact: the entries of docs/catalogue/doc-map.yaml (AA-1132) whose code globs match the file.

Mode (AA_SYNC_HOOKS, tools/sync/hookio.py): off = nothing; log (default) = one line in the hook log, silent; warn /
block = also add a short reminder to the agent's context (each finding once per session + agent). Never blocks.

Failure: any error is logged and the hook exits 0. Test: python3 .claude/hooks/test_sync_post_edit.py
"""

from __future__ import annotations

import time

_T0 = time.perf_counter()

import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# The code and the doc map come from the checkout that holds this script (the main checkout in a session, the
# worktree in its own tests); the log and state files follow CLAUDE_PROJECT_DIR (tools/sync/hookio.py).
CODE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE_ROOT / "tools" / "sync"))
import change_guard  # noqa: E402
import hookio  # noqa: E402

EVENT = "PostToolUse"
LINT_TIMEOUT_S = 2
FATAL_RULES = "E9,F63,F7,F82"
RUFF_PLACES = (".venv/bin/ruff", "api/.venv/bin/ruff", "backend/.venv/bin/ruff")
DOC_MAP = "docs/catalogue/doc-map.yaml"
LINT_SHOWN = 5
TRACKED = ("code", "schema", "test", "note")


# --- lint ---------------------------------------------------------------------------------------------------------


def find_ruff(repo: hookio.Repo) -> str | None:
    """The repo's own ruff first, then PATH without the Windows folders (/mnt/*: one stat there costs ~4 ms on WSL,
    shutil.which over the full PATH took 220 ms in the S285 measure)."""
    for top in (repo.top, repo.main):
        for rel in RUFF_PLACES:
            if top and (Path(top) / rel).is_file():
                return str(Path(top) / rel)
    path = os.pathsep.join(d for d in os.environ.get("PATH", "").split(os.pathsep) if d and not d.startswith("/mnt/"))
    return shutil.which("ruff", path=path)


def ruff_config_dir(path: Path, top: Path) -> Path | None:
    """The folder of the nearest ruff config between the file and the checkout top, or None."""
    for d in (path.parent, *path.parent.parents):
        for name in ("ruff.toml", ".ruff.toml"):
            if (d / name).is_file():
                return d
        py = d / "pyproject.toml"
        try:
            if py.is_file() and "[tool.ruff" in py.read_text(encoding="utf-8", errors="replace"):
                return d
        except OSError:
            pass
        if d == top:
            break
    return None


def lint_python(repo: hookio.Repo, path: Path) -> tuple[str, list[str]]:
    """(status, finding lines): status ok | findings | unavailable | error."""
    ruff = find_ruff(repo)
    if not ruff:
        return "unavailable", []
    cfg = ruff_config_dir(path, repo.top)
    cmd = [ruff, "check", "--quiet", "--no-cache", "--output-format=concise"]
    if cfg is None:
        cmd += ["--isolated", "--select", FATAL_RULES]
    cmd.append(str(path))
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=LINT_TIMEOUT_S, check=False,
                             cwd=str(cfg or repo.top))
    except (OSError, subprocess.TimeoutExpired) as e:
        return "error", [type(e).__name__]
    if res.returncode == 0:
        return "ok", []
    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip() and not ln.startswith("Found ")]
    if res.returncode == 1 and lines:
        return "findings", [ln.replace(str(path), repo.rel) for ln in lines]
    return "error", [res.stderr.strip()[:200]]


# --- docs impact (doc-map, cached as JSON so a normal edit never imports yaml) ------------------------------------


def _cache_path() -> Path:
    return hookio.state_dir() / "doc-map-cache.json"


def load_doc_map(root: Path = CODE_ROOT) -> list[dict]:
    """[{id, repo, pages, patterns}] of the doc map; [] when it is missing or broken (logged by the caller)."""
    path = root / DOC_MAP
    st = path.stat()
    key = f"{st.st_mtime_ns}:{st.st_size}"
    cache = _cache_path()
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("key") == key and data.get("map") == str(path):
            return data["entries"]
    except (OSError, ValueError, AttributeError, KeyError):
        pass
    sys.path.insert(0, str(root / "tools" / "docs"))
    import doc_impact  # noqa: PLC0415 - imported only on a cache miss (PyYAML, ~50 ms)

    entries = [{"id": e.id, "repo": e.repo, "pages": e.pages, "patterns": [p.pattern for p in e.patterns]}
               for e in doc_impact.load_map(path)]
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps({"key": key, "map": str(path), "entries": entries}), encoding="utf-8")
        os.replace(tmp, cache)
    except OSError:
        pass
    return entries


def docs_hits(entries: list[dict], repo: str, rel: str) -> list[dict]:
    """Map entries of `repo` whose code globs match `rel`, unless `rel` is one of the entry's own pages."""
    hits = []
    for e in entries:
        if e["repo"] != repo:
            continue
        if not any(re.match(p, rel) for p in e["patterns"]):
            continue
        own = {p.split(":", 1)[1] if ":" in p else p for p in e["pages"]
               if (p.split(":", 1)[0] if ":" in p else "AA-Ecosys") == repo}
        if rel in own:
            continue
        hits.append(e)
    return hits


# --- the hook -----------------------------------------------------------------------------------------------------


def run(data: dict, m: str) -> tuple[dict, str]:
    """(log record, reminder text for the agent or '')."""
    rec: dict = {"event": EVENT, "hook": "sync_post_edit", "mode": m, "agent": hookio.agent_key(data),
                 "agent_type": str(data.get("agent_type") or ""), "tool": str(data.get("tool_name") or "")}
    path = hookio.edited_path(data)
    repo = hookio.find_repo(path)
    if not repo or not repo.rel:
        rec["outcome"] = "outside-repo"
        return rec, ""
    kind = change_guard.classify(repo.rel)
    rec.update({"repo": repo.name, "repo_kind": repo.kind, "file_kind": kind})
    if kind == "ignored":
        rec["outcome"] = "ignored"
        return rec, ""

    state = hookio.load_state(data)
    dirty = False
    if kind in TRACKED and str(repo.top) not in state["repos"]:
        state["repos"].append(str(repo.top))
        dirty = True

    said: list[str] = []
    if repo.rel.endswith(".py") and kind in ("code", "test"):
        status, lines = lint_python(repo, Path(path))
        rec["lint"] = status
        rec["lint_findings"] = len(lines) if status == "findings" else 0
        if status == "findings":
            key = "lint:" + repo.rel + ":" + hashlib.sha1("\n".join(lines).encode()).hexdigest()[:12]
            if hookio.speaks(m) and hookio.first_time(state, key):
                dirty = True
                shown = "\n".join(f"  {ln}" for ln in lines[:LINT_SHOWN])
                more = f"\n  (+{len(lines) - LINT_SHOWN} more)" if len(lines) > LINT_SHOWN else ""
                said.append(f"ruff on {repo.rel}:\n{shown}{more}")
    if kind in ("code", "schema", "test", "other"):
        try:
            hits = docs_hits(load_doc_map(), repo.name, repo.rel)
        except Exception as e:  # noqa: BLE001 - a broken map is a note in the log, never a hook failure
            hits, rec["docs_error"] = [], f"{type(e).__name__}: {e}"[:200]
        rec["docs_entries"] = [h["id"] for h in hits]
        new = [h for h in hits if hookio.speaks(m) and hookio.first_time(state, f"docs:{repo.name}:{h['id']}")]
        if new:
            dirty = True
            pages = sorted({p for h in new for p in h["pages"]})
            said.append(f"Docs impact: {repo.rel} is described by {', '.join(pages[:6])}"
                        + (f" (+{len(pages) - 6})" if len(pages) > 6 else "")
                        + ". Update the page in the same PR, or say 'Docs-impact: none: <reason>' in the PR body.")
    if dirty:
        hookio.save_state(data, state)
    rec["would"] = "remind" if (rec.get("lint") == "findings" or rec.get("docs_entries")) else "none"
    rec["said"] = bool(said)
    return rec, "\n".join(said)


def main() -> int:
    data = hookio.read_event()
    m = hookio.mode()
    if m == "off":
        return 0
    text = ""
    try:
        rec, text = run(data, m)
    except Exception as e:  # noqa: BLE001 - a hook bug must never trap the agent
        rec = {"event": EVENT, "hook": "sync_post_edit", "mode": m, "agent": hookio.agent_key(data),
               "error": f"{type(e).__name__}: {e}"[:300]}
    rec["latency_ms"] = round((time.perf_counter() - _T0) * 1000, 1)
    hookio.log_event(rec)
    if text and hookio.speaks(m):
        print(hookio.context_output(EVENT, text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
