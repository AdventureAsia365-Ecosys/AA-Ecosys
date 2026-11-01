"""Test doubles for the ship tools (used by tools/github/test_ship_*.py only).

FakeRunner answers external commands from scripted rules and keeps a fake clock, so no test reaches GitHub, AWS or
the network. HybridRunner runs real `git` (temporary repositories) and scripts everything else.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Callable

from ship_common import Result, Runner


def check(name: str, conclusion: str | None = "SUCCESS", status: str = "COMPLETED", wf: str = "CI",
          started: str = "2026-11-01T10:00:00Z") -> dict:
    return {"__typename": "CheckRun", "name": name, "workflowName": wf, "status": status, "conclusion": conclusion,
            "startedAt": started, "completedAt": started if status == "COMPLETED" else None}


def status_ctx(context: str, state: str, started: str = "2026-11-01T10:00:00Z") -> dict:
    return {"__typename": "StatusContext", "context": context, "state": state, "startedAt": started}


def pr(n: int = 1, state: str = "OPEN", checks: list | None = None, head: str = "a" * 40, draft: bool = False,
       base: str = "main", mss: str = "CLEAN", merge_oid: str | None = None, branch: str = "feat/x") -> dict:
    return {"number": n, "state": state, "isDraft": draft, "mergeStateStatus": mss, "baseRefName": base,
            "headRefName": branch, "headRefOid": head,
            "mergeCommit": {"oid": merge_oid} if merge_oid else None,
            "statusCheckRollup": checks if checks is not None else [check("Lint"), check("Unit tests")]}


Response = Result | Callable[[list[str]], Result]


class FakeRunner(Runner):
    """Rules are (tokens, responses): a call matches when every token is one of its argv elements (first rule
    wins). Responses are used in order and the last one repeats. An unmatched call fails the test."""

    def __init__(self) -> None:
        self.rules: list[tuple[tuple[str, ...], list[Response]]] = []
        self.calls: list[list[str]] = []
        self.t = 1_793_000_000.0  # 2026-10-26T07:33:20Z, a fixed fake clock
        self.slept = 0.0

    def on(self, tokens: tuple[str, ...] | list[str], *responses: Response) -> "FakeRunner":
        self.rules.append((tuple(tokens), list(responses)))
        return self

    def _answer(self, argv: list[str]) -> Result:
        self.calls.append(list(argv))
        for tokens, responses in self.rules:
            if all(t in argv for t in tokens):
                resp = responses.pop(0) if len(responses) > 1 else responses[0]
                return resp(argv) if callable(resp) else resp
        raise AssertionError(f"unexpected command: {argv}")

    def run(self, argv, timeout=None, input_text=None) -> Result:
        return self._answer(argv)

    def stream(self, argv, prefix, timeout=None) -> Result:
        return self._answer(argv)

    def sleep(self, seconds: float) -> None:
        self.t += seconds
        self.slept += seconds

    def now(self) -> float:
        return self.t

    def called(self, *tokens: str) -> list[list[str]]:
        return [c for c in self.calls if all(t in c for t in tokens)]


class HybridRunner(FakeRunner):
    """Real git (argv[0] == 'git'), scripted everything else."""

    def run(self, argv, timeout=None, input_text=None) -> Result:
        if argv and argv[0] == "git":
            self.calls.append(list(argv))
            return Runner().run(argv, timeout=timeout)
        return self._answer(argv)


GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test Author",
    "GIT_AUTHOR_EMAIL": "author@example.invalid",
    "GIT_COMMITTER_NAME": "Test Author",
    "GIT_COMMITTER_EMAIL": "author@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


class GitSandbox:
    """A bare 'origin' and one clone ('wt') in a temporary directory."""

    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ship-tools-")
        self._old = {k: os.environ.get(k) for k in GIT_ENV}
        os.environ.update(GIT_ENV)
        self.origin = os.path.join(self.tmp.name, "origin.git")
        self.wt = os.path.join(self.tmp.name, "wt")
        self.other = os.path.join(self.tmp.name, "other")
        self.git(self.tmp.name, "init", "-q", "--bare", "-b", "main", self.origin)
        self.git(self.tmp.name, "clone", "-q", self.origin, self.wt)
        self.commit(self.wt, "README.md", "hello\n", "chore: start")
        self.git(self.wt, "push", "-q", "origin", "HEAD:main")
        self.git(self.tmp.name, "clone", "-q", self.origin, self.other)

    def git(self, cwd: str, *args: str) -> str:
        p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
        return p.stdout.strip()

    def commit(self, cwd: str, path: str, text: str, msg: str) -> str:
        full = os.path.join(cwd, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.git(cwd, "add", path)
        self.git(cwd, "commit", "-q", "-m", msg)
        return self.git(cwd, "rev-parse", "HEAD")

    def close(self) -> None:
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()
