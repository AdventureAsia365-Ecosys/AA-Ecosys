#!/usr/bin/env python3
"""Find the gitleaks binary the local secret scans run (S281: a mise shim with no version blocked every push).

    python3 tools/github/gitleaks_resolve.py [--root DIR ...]   # prints the path; exit 0 found, 1 none

Used by the root scripts/pre-push.sh and the PR opener (tools/github, its gitleaks_check), so both pick the same
binary. Candidates, in order:

  1. AA_GITLEAKS: an explicit path or command name. When it runs it wins as given; the caller still checks its version
     against the CI pin.
  2. <root>/.tmp-session/gitleaks-8301/gitleaks (the download lanes and the orchestrator check against the release
     checksums), for each root: --root DIRs, else $AA_ECOSYS_ROOT, else the workspace path. Taken only when
     `gitleaks version` reports the CI pin.
  3. every `gitleaks` on PATH, in PATH order.

A candidate whose `gitleaks version` fails or prints no version is skipped, with the reason kept: the mise shim
answers "No version is set for shim: gitleaks" (exit 1) when no global gitleaks version is set, and `shutil.which`
used to pick it first. Among the working PATH candidates the first one at the CI pin wins, else the first working one
(the caller then reports the version gap). Python stdlib only; the version probe is injectable for the tests.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

PIN = "8.30.1"  # .github/workflows/secret-scan.yml GITLEAKS_IMAGE (every repo pins the same version)
LOCAL_REL = ".tmp-session/gitleaks-8301/gitleaks"  # where lanes and the orchestrator keep the checked download
WORKSPACE = "/home/nghiep/projects/AA-Ecosys"
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")

# version probe: (executable) -> (version or None, why it failed or "")
Probe = Callable[[str], "tuple[str | None, str]"]


@dataclass
class Found:
    path: str | None = None
    version: str | None = None
    skipped: list[str] = field(default_factory=list)  # "<candidate>: <why>" for every candidate passed over

    def note(self) -> str:
        return "; ".join(self.skipped)


def parse_version(text: str) -> str | None:
    m = VERSION_RE.search(text or "")
    return m.group(0) if m else None


def probe(exe: str, timeout: float = 30) -> tuple[str | None, str]:
    """Run `<exe> version`: (version, "") or (None, the reason)."""
    try:
        p = subprocess.run([exe, "version"], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return None, "not found"
    except PermissionError:
        return None, "not executable"
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"{type(e).__name__}"
    return version_of(p.returncode, (p.stdout or "") + "\n" + (p.stderr or ""))


def version_of(rc: int, output: str) -> tuple[str | None, str]:
    """(version, "") from a `gitleaks version` exit code and output, else (None, the first output line)."""
    first = next((x.strip() for x in output.splitlines() if x.strip()), "")
    if rc != 0:
        return None, f"`gitleaks version` exit {rc}" + (f" ({first[:160]})" if first else "")
    v = parse_version(output)
    return (v, "") if v else (None, f"`gitleaks version` printed no version ({first[:160] or 'empty'})")


def which_all(name: str = "gitleaks", path: str | None = None) -> list[str]:
    """Every executable `name` on PATH, in PATH order, without duplicates (shutil.which returns only the first)."""
    out: list[str] = []
    for d in (path if path is not None else os.environ.get("PATH", "")).split(os.pathsep):
        if not d:
            continue
        f = os.path.join(d, name)
        if os.path.isfile(f) and os.access(f, os.X_OK) and f not in out:
            out.append(f)
    return out


def default_roots() -> list[str]:
    return list(dict.fromkeys(x for x in (os.environ.get("AA_ECOSYS_ROOT", ""), WORKSPACE) if x))


def resolve(roots: Iterable[str | os.PathLike] | None = None, *, run_version: Probe = probe,
            env: dict | None = None, on_path: list[str] | None = None) -> Found:
    """The gitleaks to run (see the module doc). `on_path` replaces the PATH search (tests)."""
    env = os.environ if env is None else env
    found = Found()
    seen: set[str] = set()

    def key(p: str) -> str:
        return os.path.realpath(p) if os.sep in p else p

    explicit = (env.get("AA_GITLEAKS") or "").strip()
    if explicit:
        seen.add(key(explicit))
        v, why = run_version(explicit)
        if v:
            found.path, found.version = explicit, v
            return found
        found.skipped.append(f"AA_GITLEAKS={explicit}: {why}")
    for root in (list(roots) if roots is not None else default_roots()):
        local = str(Path(root) / LOCAL_REL)
        if key(local) in seen or not os.path.isfile(local):
            continue
        seen.add(key(local))
        if not os.access(local, os.X_OK):
            found.skipped.append(f"{local}: not executable")
            continue
        v, why = run_version(local)
        if v == PIN:
            found.path, found.version = local, v
            return found
        found.skipped.append(f"{local}: {why or f'version {v}, not the CI pin {PIN}'}")
    first: tuple[str, str] | None = None
    for cand in (on_path if on_path is not None else which_all("gitleaks", env.get("PATH", ""))):
        if key(cand) in seen:
            continue
        seen.add(key(cand))
        v, why = run_version(cand)
        if not v:
            found.skipped.append(f"{cand}: {why}")
            continue
        if v == PIN:
            found.path, found.version = cand, v
            return found
        if first is None:
            first = (cand, v)
    if first:
        found.path, found.version = first
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", action="append", default=None,
                    help=f"a workspace checkout holding {LOCAL_REL} (repeatable; default $AA_ECOSYS_ROOT, the workspace)")
    a = ap.parse_args(argv)
    found = resolve(a.root)
    if found.skipped:
        print(f"gitleaks candidates skipped: {found.note()}", file=sys.stderr)
    if not found.path:
        print(f"no working gitleaks: install v{PIN} at {LOCAL_REL} (github.com/gitleaks/gitleaks/releases, "
              f"linux_x64 tar.gz checked against the release checksums), or set AA_GITLEAKS", file=sys.stderr)
        return 1
    if found.version != PIN:
        print(f"gitleaks {found.version} at {found.path}, CI uses {PIN}", file=sys.stderr)
    print(found.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
