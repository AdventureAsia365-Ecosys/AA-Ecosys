"""Git hooks and root test helpers never inherit git's repo-local variables (AA-1024, S272 incident).

Git exports GIT_DIR (and in some setups GIT_WORK_TREE, GIT_INDEX_FILE, ...) to the hooks it runs. In S272 a test run
by an app's pre-push hook inherited GIT_DIR, so its "temporary" repo was the real clone: `git init --bare` set
core.bare=true there, and the fixture wrote a [user] identity, a fake branch and tag and an origin/main ref into it.

The guard has three layers, all tested here:
  1. .githooks/pre-push cds to the top level and unsets `git rev-parse --local-env-vars` before running the checks;
  2. scripts/pre-push.sh unsets them again (it is also run by hand) and its --self-test checks it;
  3. every root test helper that runs git in a temporary repo drops them at import (Python) or start (bash).

Offline: git runs only in temporary repositories. Run: python3 -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# This test runs git itself: same scrub as every other helper.
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

BASE_ENV = {**os.environ, "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "T",
            "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

# Where helpers live and what counts as "runs git" (statement position in bash, an argv list in Python).
HELPER_DIRS = ("tools/", ".claude/hooks/", "scripts/")
PY_GIT = re.compile(r"""(\[\s*["']git["']\s*,|\(\s*["']git["']\s*,)""")
SH_GIT = re.compile(r"(^|[;&|({]\s*|\$\(\s*)git\s+(-C|-c|init|clone|config|commit|worktree|add|checkout|fetch|push|"
                    r"tag|branch|remote)\b", re.MULTILINE)
SH_UNSET = "unset $(git rev-parse --local-env-vars)"
# Files that must be found, so a regex change cannot silently make the scan empty.
KNOWN = {"tools/github/ship_fakes.py", "tools/docs/test_check_lessons.py", "tools/adr/test_check_adr_numbers.py",
         ".claude/hooks/test_aa_shell_guard.py", ".claude/hooks/test_kit_core_edit_guard.sh"}


def local_vars() -> list[str]:
    out = subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True, text=True, check=True)
    names = out.stdout.split()
    assert "GIT_DIR" in names and "GIT_INDEX_FILE" in names, names
    return names


def git(cwd: Path, *args: str, env: dict | None = None) -> str:
    p = subprocess.run(["git", *args], cwd=cwd, env=env or BASE_ENV, capture_output=True, text=True, check=True)
    return p.stdout.strip()


def is_helper(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    if not path.startswith(HELPER_DIRS):
        return False
    return (name.startswith("test_") and name.endswith((".py", ".sh"))) or name.endswith("_fakes.py") or \
        ("/tests/" in path and name.endswith(".py"))


def git_running_helpers() -> dict[str, str]:
    files = git(ROOT, "ls-files", "--", *HELPER_DIRS).splitlines()
    out = {}
    for rel in files:
        if not is_helper(rel) or rel == "tools/github/test_git_env_isolation.py":
            continue
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        pattern = PY_GIT if rel.endswith(".py") else SH_GIT
        if pattern.search(text):
            out[rel] = text
    return out


class SentinelRepo:
    """A repo standing in for the real clone; snapshot() captures what the S272 incident rewrote."""

    def __init__(self, base: Path) -> None:
        self.path = base / "real-clone"
        self.path.mkdir()
        git(self.path, "init", "-q", "-b", "main")
        (self.path / "README.md").write_text("real\n", encoding="utf-8")
        git(self.path, "add", "README.md")
        git(self.path, "commit", "-q", "-m", "start")

    def env(self) -> dict:
        d = self.path / ".git"
        return {**BASE_ENV, "GIT_DIR": str(d), "GIT_WORK_TREE": str(self.path), "GIT_INDEX_FILE": str(d / "index")}

    def snapshot(self) -> tuple[str, str]:
        return ((self.path / ".git" / "config").read_text(encoding="utf-8"),
                git(self.path, "for-each-ref", "--format=%(refname) %(objectname)"))


class HelpersScrubTest(unittest.TestCase):
    def test_every_git_running_helper_drops_the_repo_local_variables(self):
        names = local_vars()
        found = git_running_helpers()
        self.assertTrue(KNOWN <= set(found), f"scan missed {sorted(KNOWN - set(found))}: fix PY_GIT / SH_GIT")
        problems = []
        for rel, text in sorted(found.items()):
            if rel.endswith(".sh") and SH_UNSET in text:
                continue
            missing = [n for n in names if f'"{n}"' not in text]
            if missing:
                problems.append(f"{rel}: does not drop {', '.join(missing)}")
        self.assertEqual(problems, [], "a test helper that runs git in a temporary repo must drop git's repo-local "
                         "variables first (Python: the os.environ.pop loop of tools/github/ship_fakes.py; bash: "
                         f"`{SH_UNSET}` after set -u):\n" + "\n".join(problems))

    def test_python_snippets_list_every_variable_git_reports(self):
        # the static tuple in the Python helpers must follow git: a newer git adding a variable fails here
        names = set(local_vars())
        tuple_text = re.search(r"for _git_var in \((.*?)\):", Path(__file__).read_text(encoding="utf-8"), re.S)
        listed = set(re.findall(r'"(GIT_[A-Z_]+)"', tuple_text.group(1)))
        self.assertEqual(names - listed, set())


class HookEnvTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="git-env-")
        self.base = Path(self.tmp.name)
        self.real = SentinelRepo(self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def test_hook_runs_the_checks_without_git_variables(self):
        repo = self.real.path
        (repo / ".githooks").mkdir()
        shutil.copy(ROOT / ".githooks" / "pre-push", repo / ".githooks" / "pre-push")
        (repo / "scripts").mkdir()
        seen = self.base / "seen.env"
        (repo / "scripts" / "pre-push.sh").write_text(f'env > "{seen}"\npwd >> "{seen}"\n', encoding="utf-8")
        sub = repo / "deep"
        sub.mkdir()
        r = subprocess.run(["bash", str(repo / ".githooks" / "pre-push"), "origin", "https://example.invalid/x.git"],
                           cwd=sub, env=self.real.env(), input="", capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = seen.read_text(encoding="utf-8").splitlines()
        leaked = [ln.split("=", 1)[0] for ln in lines if ln.split("=", 1)[0] in set(local_vars())]
        self.assertEqual(leaked, [], "the hook passed git's repo-local variables to the checks")
        self.assertEqual(lines[-1], str(repo), "the checks must run from the top level")

    def test_prepush_script_drops_them_too(self):
        before = self.real.snapshot()
        r = subprocess.run(["bash", str(ROOT / "scripts" / "pre-push.sh"), "--self-test"], cwd=ROOT,
                           env=self.real.env(), capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
        self.assertIn("ok   no GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE in the environment", r.stdout)
        self.assertEqual(self.real.snapshot(), before)

    def test_ship_sandbox_never_touches_the_inherited_repo(self):
        # the exact S272 shape: a fixture that inits a bare origin and clones it, run with GIT_DIR inherited
        before = self.real.snapshot()
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import ship_fakes; "
                "s = ship_fakes.GitSandbox(); s.commit(s.wt, 'x.txt', 'x', 'chore: x'); s.close()")
        r = subprocess.run([sys.executable, "-c", code, str(HERE)], cwd=self.real.path, env=self.real.env(),
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        config, refs = self.real.snapshot()
        self.assertNotIn("bare = true", config)
        self.assertEqual((config, refs), before, "a test fixture rewrote the repo it inherited through GIT_DIR")


if __name__ == "__main__":
    unittest.main()
