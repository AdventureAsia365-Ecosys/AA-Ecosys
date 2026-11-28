#!/usr/bin/env python3
"""Guard of `ci_bot_key_consolidate.sh cleanup` (AA-1183 part 2): is every job that reads the aa-ecosys-ci-bot key on
the default branch of every repo already running in the environment `ci-bot`?

`cleanup --apply` deletes the old copies of the key (environment `release` / `ci-hygiene`, AA-CIS-Infra repo level). A
workflow that still reads the key outside `ci-bot` would lose it, so this check must FAIL CLOSED: any listing or file
that cannot be read, an empty workflow list, a file that is not valid YAML, a reference to the key outside a job, or a
job that reads the key in another environment (or a reusable-workflow call that passes it) means "not ready" (exit 1).
Only a complete, clean read of every repo exits 0. Job-level, like tools/security/test_ci_bot_environment.py (a file
that names `environment: ci-bot` for one job no longer clears another job of the same file).

Read-only: `gh api` GET calls with the caller's gh login. Usage (from the root of the repo):
    python3 tools/security/ci_bot_workflows_ready.py --owner <org> AA-Ecosys:master AA-CIS-App:main ...
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import subprocess
import sys
import urllib.parse
from typing import Callable, Optional

import yaml

KEY_NAME = "AA_CI_BOT_PRIVATE_KEY"
ENV_NAME = "ci-bot"

Runner = Callable[[list], tuple]


class NotReady(Exception):
    """The check could not prove the repo ready."""


def _gh_runner(argv: list) -> tuple:
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    return proc.returncode, proc.stdout, proc.stderr


def _get(runner: Runner, path: str, what: str):
    try:
        code, out, err = runner(["gh", "api", "-H", "Accept: application/vnd.github+json", path])
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NotReady(f"cannot read {what}: {type(exc).__name__}") from None
    if code != 0:
        last = (err or "").strip().splitlines()[-1:] or ["no error text"]
        raise NotReady(f"cannot read {what}: {last[0][:200]}")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise NotReady(f"cannot read {what}: the answer is not JSON") from None


def _env(job: dict) -> Optional[str]:
    env = job.get("environment")
    return env.get("name") if isinstance(env, dict) else env


def workflow_problems(name: str, text: str, key: str = KEY_NAME, env_name: str = ENV_NAME) -> list:
    """The reasons one workflow file is not ready (empty list = ready)."""
    ref = f"secrets.{key}"
    if not text.strip():
        return [f"{name}: empty file"]
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError:
        return [f"{name}: not valid YAML"]
    if not isinstance(doc, dict):
        return [f"{name}: not a workflow mapping"]
    out = []
    outside = {k: v for k, v in doc.items() if k != "jobs"}
    if ref in yaml.safe_dump(outside):
        out.append(f"{name}: reads {key} outside any job")
    jobs = doc.get("jobs")
    if ref in text and not isinstance(jobs, dict):
        out.append(f"{name}: reads {key} but its jobs cannot be parsed")
        return out
    for job_id, job in (jobs or {}).items():
        if not isinstance(job, dict):
            if ref in yaml.safe_dump(job):
                out.append(f"{name}:{job_id}: reads {key} in a job that is not a mapping")
            continue
        if ref not in yaml.safe_dump(job):
            continue
        if "uses" in job:
            out.append(f"{name}:{job_id}: passes {key} to a reusable workflow (no environment of its own)")
        elif _env(job) != env_name:
            out.append(f"{name}:{job_id}: reads {key} in environment {_env(job)!r}, not {env_name!r}")
    return out


def repo_problems(owner: str, repo: str, branch: str, runner: Runner = _gh_runner, key: str = KEY_NAME,
                  env_name: str = ENV_NAME) -> list:
    ref = urllib.parse.quote(branch, safe="")
    listing = _get(runner, f"repos/{owner}/{repo}/contents/.github/workflows?ref={ref}", f"{repo} workflow list")
    if not isinstance(listing, list):
        raise NotReady(f"cannot read {repo} workflow list: not a directory listing")
    files = sorted(e.get("path", "") for e in listing if isinstance(e, dict) and e.get("type") == "file"
                   and str(e.get("name", "")).endswith((".yml", ".yaml")))
    if not files:
        raise NotReady(f"{repo}: no workflow file listed on {branch} (refusing: the listing may be incomplete)")
    out = []
    for path in files:
        doc = _get(runner, f"repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}?ref={ref}", f"{repo} {path}")
        content = doc.get("content") if isinstance(doc, dict) else None
        if not content or (doc.get("encoding") or "base64") != "base64":
            raise NotReady(f"cannot read {repo} {path}: no inline content")
        try:
            text = base64.b64decode(content).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            raise NotReady(f"cannot read {repo} {path}: content does not decode") from None
        out += [f"{repo}: {p} on {branch}" for p in workflow_problems(path, text, key, env_name)]
    return out


def check(owner: str, targets: list, runner: Runner = _gh_runner, key: str = KEY_NAME, env_name: str = ENV_NAME) \
        -> list:
    """Every problem across the repos; an unreadable repo is a problem too (never skipped)."""
    if not targets:
        return ["no repository to check"]
    problems = []
    for repo, branch in targets:
        try:
            problems += repo_problems(owner, repo, branch, runner, key, env_name)
        except NotReady as exc:
            problems.append(str(exc))
    return problems


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--owner", required=True)
    ap.add_argument("--key", default=KEY_NAME)
    ap.add_argument("--env", default=ENV_NAME)
    ap.add_argument("targets", nargs="+", metavar="REPO:BRANCH")
    args = ap.parse_args(argv)
    targets = []
    for t in args.targets:
        repo, sep, branch = t.partition(":")
        if not sep or not repo or not branch:
            print(f"not ready: bad target {t!r} (want REPO:BRANCH)", file=sys.stderr)
            return 1
        targets.append((repo, branch))
    problems = check(args.owner, targets, key=args.key, env_name=args.env)
    for p in problems:
        print(f"not ready: {p}", file=sys.stderr)
    if problems:
        return 1
    print(f"ready: every job that reads {args.key} runs in environment {args.env} ({len(targets)} repos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
