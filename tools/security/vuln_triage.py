#!/usr/bin/env python3
"""Vulnerability triage by CISA KEV, FIRST EPSS and CVSS v4 with SLA due dates (AA-1163, SEC-03). Stdlib only.

Reads open findings, enriches each CVE with the CISA KEV catalog and FIRST EPSS (both free public feeds), applies the
SEC-03 rule (tools/security/vuln_triage.toml) and writes the monthly triage record as Markdown (or JSON).

Inputs (any mix):
  --github                  open Dependabot + code scanning alerts, dismissals and exception files of the repos in the
                            config, read through `gh api` (GET only; the caller's gh login). A refused call is recorded
                            as "not readable", never guessed.
  --input REPO=FILE         a local file: Dependabot alerts JSON, code scanning alerts JSON, Trivy JSON or SARIF
                            (the shape is detected).
  --ignore-file REPO=FILE   a local .github/pip-audit-ignore.txt or .trivyignore to cross-check against the register.

    python3 tools/security/vuln_triage.py --github --month 2026-11 --public --out docs/security/triage/2026-11.md
    python3 tools/security/vuln_triage.py --input AA-CIS-App=trivy.json --offline

The exception register (docs/security/vuln-exceptions.toml) is the one list of accepted findings: every pip-audit
ignore, Trivy ignore and GitHub "tolerable risk" dismissal must have a row there with the same expiry. Feed downloads
are cached (default tools/security/.cache/, gitignored). --offline skips the feeds: KEV shows "not checked" and the
EPSS value GitHub attaches to an alert is used.

--public keeps the record safe for a public repo: code scanning alerts (visible to repo members only) appear as counts and
alert numbers per repo, class and exposure, without rule or file; no advisory text is ever copied. --record adds the
front matter of the monthly record (SEC-03-triage-<month>) and the decisions and sign-off section.

Exit: 0 record written | 1 --strict and a P0/P1 is past due, an exception is expired or unregistered | 2 bad input.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import subprocess
import sys
import time
import tomllib
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEFAULT_CONFIG = HERE / "vuln_triage.toml"
DEFAULT_REGISTER = ROOT / "docs" / "security" / "vuln-exceptions.toml"
DEFAULT_CACHE = HERE / ".cache"
CLASSES = ("P0", "P1", "P2", "P3")
CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$")
USER_AGENT = "vuln-triage/1.0 (stdlib urllib)"

Fetch = Callable[[str], bytes]


class GhError(Exception):
    """A GitHub API call was refused or failed (the message is the first line gh printed)."""


GhClient = Callable[[str, bool], object]   # (api path, raw) -> parsed JSON list/dict, or text when raw


# --------------------------------------------------------------------------------------------------------------------
# Config and data model


def load_config(path: Path) -> dict:
    with open(path, "rb") as fh:
        cfg = tomllib.load(fh)
    for key in ("rule", "sla", "severity_scores", "exceptions", "feeds", "github", "exposure"):
        if key not in cfg:
            raise ValueError(f"{path}: missing [{key}]")
    return cfg


@dataclass
class Finding:
    repo: str
    source: str                     # dependabot | code-scanning | trivy | sarif
    ref: str                        # alert number or scan target
    package: str                    # package name, or the rule id of a code scanning alert
    location: str                   # manifest path, file path or scan target
    ids: list[str]                  # GHSA / CVE / rule ids, most specific first
    severity: str                   # vendor severity, lower case
    opened: dt.date
    cvss: float | None = None
    cvss_version: str = ""          # "4.0", "3.1", or "severity" when the band stands in
    epss: float | None = None
    epss_percentile: float | None = None
    epss_source: str = ""           # first | github | ""
    kev: bool | None = None         # None = not checked
    fixed_in: str | None = None
    scope: str = ""                 # runtime | development (Dependabot)
    owner: str = ""
    url: str = ""
    # set by triage
    exposure: str = ""
    cls: str = ""
    reasons: list[str] = field(default_factory=list)
    due: dt.date | None = None
    status: str = ""                # past due | due soon | open | accepted until YYYY-MM-DD
    action: str = ""

    @property
    def cve(self) -> str | None:
        return next((i for i in self.ids if CVE_RE.match(i)), None)


@dataclass
class Exception_:
    repo: str
    id: str
    source: str
    package: str
    expires: dt.date
    reason: str
    way_out: str
    approved_by: str
    approved_on: dt.date


@dataclass
class SourceEntry:
    """An exception as a repo's own file or GitHub dismissal holds it."""
    repo: str
    source: str           # pip-audit | trivy | dependabot | code-scanning
    id: str
    expires: dt.date | None
    where: str


def _date(value: object) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and value:
        try:
            return dt.date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _float(value: object) -> float | None:
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return f


# --------------------------------------------------------------------------------------------------------------------
# Parsers (one per input shape)


def parse_dependabot(repo: str, alerts: list) -> list[Finding]:
    out = []
    for a in alerts:
        if not isinstance(a, dict) or a.get("state", "open") != "open":
            continue
        adv = a.get("security_advisory") or {}
        vul = a.get("security_vulnerability") or {}
        dep = a.get("dependency") or {}
        ids = [adv.get("ghsa_id")] + [i.get("value") for i in adv.get("identifiers") or [] if isinstance(i, dict)]
        if adv.get("cve_id"):
            ids.append(adv["cve_id"])
        ids = list(dict.fromkeys(i for i in ids if i))
        cvss, version = None, ""
        sev = adv.get("cvss_severities") or {}
        for key, ver in (("cvss_v4", "4.0"), ("cvss_v3", "3.1")):
            score = _float((sev.get(key) or {}).get("score"))
            if score:
                cvss, version = score, ver
                break
        if cvss is None:
            score = _float((adv.get("cvss") or {}).get("score"))
            if score:
                cvss, version = score, "3.1"
        epss = adv.get("epss") or {}
        if isinstance(epss, list):
            epss = epss[0] if epss else {}
        f = Finding(
            repo=repo, source="dependabot", ref=f"#{a.get('number')}",
            package=((dep.get("package") or {}).get("name") or "?"),
            location=dep.get("manifest_path") or "", ids=ids,
            severity=str(adv.get("severity") or vul.get("severity") or "unknown").lower(),
            opened=_date(a.get("created_at")) or dt.date.today(),
            cvss=cvss, cvss_version=version,
            fixed_in=(vul.get("first_patched_version") or {}).get("identifier"),
            scope=dep.get("scope") or "",
            owner=", ".join(x.get("login", "") for x in a.get("assignees") or [] if isinstance(x, dict)),
            url=a.get("html_url") or "",
        )
        f.epss = _float(epss.get("percentage"))
        f.epss_percentile = _float(epss.get("percentile"))
        f.epss_source = "github" if f.epss is not None else ""
        out.append(f)
    return out


def parse_code_scanning(repo: str, alerts: list) -> list[Finding]:
    out = []
    for a in alerts:
        if not isinstance(a, dict) or a.get("state", "open") != "open":
            continue
        rule = a.get("rule") or {}
        loc = ((a.get("most_recent_instance") or {}).get("location") or {})
        sev = str(rule.get("security_severity_level") or rule.get("severity") or "unknown").lower()
        out.append(Finding(
            repo=repo, source="code-scanning", ref=f"#{a.get('number')}",
            package=rule.get("id") or "?", location=loc.get("path") or "", ids=[rule.get("id") or "?"],
            severity=sev, opened=_date(a.get("created_at")) or dt.date.today(),
            owner=", ".join(x.get("login", "") for x in a.get("assignees") or [] if isinstance(x, dict)),
            url=a.get("html_url") or "",
        ))
    return out


def parse_trivy(repo: str, doc: dict, as_of: dt.date) -> list[Finding]:
    opened = _date(doc.get("CreatedAt")) or as_of
    out = []
    for res in doc.get("Results") or []:
        for v in (res or {}).get("Vulnerabilities") or []:
            cvss, version = None, ""
            for vendor in (v.get("CVSS") or {}).values():
                if not isinstance(vendor, dict):
                    continue
                for key, ver in (("V40Score", "4.0"), ("V3Score", "3.1")):
                    score = _float(vendor.get(key))
                    if score and (cvss is None or (ver == "4.0" and version != "4.0")):
                        cvss, version = score, ver
            out.append(Finding(
                repo=repo, source="trivy", ref=res.get("Target") or "",
                package=v.get("PkgName") or "?", location=res.get("Target") or "",
                ids=[v.get("VulnerabilityID") or "?"], severity=str(v.get("Severity") or "unknown").lower(),
                opened=opened, cvss=cvss, cvss_version=version, fixed_in=v.get("FixedVersion") or None,
            ))
    return out


def parse_sarif(repo: str, doc: dict, as_of: dt.date) -> list[Finding]:
    out = []
    for run in doc.get("runs") or []:
        rules = {}
        for r in ((run.get("tool") or {}).get("driver") or {}).get("rules") or []:
            rules[r.get("id")] = r
        for res in run.get("results") or []:
            rid = res.get("ruleId") or "?"
            props = (rules.get(rid) or {}).get("properties") or {}
            score = _float(props.get("security-severity"))
            loc = ""
            for location in res.get("locations") or []:
                loc = ((location.get("physicalLocation") or {}).get("artifactLocation") or {}).get("uri") or ""
                break
            level = str(res.get("level") or "warning").lower()
            out.append(Finding(
                repo=repo, source="sarif", ref=loc, package=rid, location=loc, ids=[rid],
                severity=_band_name(score) if score is not None else level, opened=as_of,
                cvss=score, cvss_version="sarif" if score is not None else "",
            ))
    return out


def _band_name(score: float) -> str:
    return "critical" if score >= 9 else "high" if score >= 7 else "medium" if score >= 4 else "low"


def parse_any(repo: str, doc: object, as_of: dt.date) -> list[Finding]:
    """Detect the shape of one input file."""
    if isinstance(doc, dict) and "runs" in doc:
        return parse_sarif(repo, doc, as_of)
    if isinstance(doc, dict) and "Results" in doc:
        return parse_trivy(repo, doc, as_of)
    if isinstance(doc, list):
        first = next((x for x in doc if isinstance(x, dict)), {})
        if "security_advisory" in first:
            return parse_dependabot(repo, doc)
        if "rule" in first:
            return parse_code_scanning(repo, doc)
        if not doc:
            return []
    raise ValueError("not a Dependabot or code scanning alert list, Trivy JSON or SARIF")


# --------------------------------------------------------------------------------------------------------------------
# Exception register and the per-repo sources it must match


def load_register(path: Path) -> list[Exception_]:
    if not path.exists():
        return []
    with open(path, "rb") as fh:
        doc = tomllib.load(fh)
    rows = []
    for n, r in enumerate(doc.get("exception") or [], start=1):
        missing = [k for k in ("repo", "id", "source", "expires", "reason", "way_out", "approved_by", "approved_on")
                   if not r.get(k)]
        if missing:
            raise ValueError(f"{path}: exception {n} misses {', '.join(missing)}")
        rows.append(Exception_(
            repo=r["repo"], id=r["id"], source=r["source"], package=r.get("package", ""),
            expires=_date(r["expires"]), reason=r["reason"], way_out=r["way_out"],  # type: ignore[arg-type]
            approved_by=r["approved_by"], approved_on=_date(r["approved_on"]),  # type: ignore[arg-type]
        ))
    return rows


def parse_ignore_file(repo: str, name: str, text: str) -> list[SourceEntry]:
    """pip-audit list (`<id> <YYYY-MM-DD> <reason>`) or .trivyignore (`<id> exp:YYYY-MM-DD`)."""
    trivy = name.endswith(".trivyignore") or "trivy" in name
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if trivy:
            exp = next((p[4:] for p in parts[1:] if p.startswith("exp:")), None)
            out.append(SourceEntry(repo, "trivy", parts[0], _date(exp), name))
        else:
            out.append(SourceEntry(repo, "pip-audit", parts[0], _date(parts[1]) if len(parts) > 1 else None, name))
    return out


_EXPIRY_IN_COMMENT = re.compile(r"exception until (\d{4}-\d{2}-\d{2})")


def dismissals(repo: str, source: str, alerts: list, reasons: Iterable[str]) -> list[SourceEntry]:
    wanted = {r.lower() for r in reasons}
    out = []
    for a in alerts:
        if not isinstance(a, dict) or str(a.get("dismissed_reason") or "").lower() not in wanted:
            continue
        if source == "dependabot":
            ident = (a.get("security_advisory") or {}).get("ghsa_id") or f"#{a.get('number')}"
        else:
            ident = (a.get("rule") or {}).get("id") or f"#{a.get('number')}"
        m = _EXPIRY_IN_COMMENT.search(a.get("dismissed_comment") or "")
        out.append(SourceEntry(repo, source, ident, _date(m.group(1)) if m else None,
                               f"GitHub dismissal #{a.get('number')}"))
    return out


def check_exceptions(register: list[Exception_], entries: list[SourceEntry], findings: list[Finding],
                     as_of: dt.date, max_days: int) -> list[tuple[str, str, str]]:
    """Problems as (repo, id, text). Every entry needs a register row with the same expiry; rows expire."""
    problems = []
    index = {(e.repo, e.id): e for e in register}
    for row in register:
        if row.expires < as_of:
            problems.append((row.repo, row.id, f"expired on {row.expires}"))
        if (row.expires - row.approved_on).days > max_days:
            problems.append((row.repo, row.id, f"expiry is more than {max_days} days after approval"))
        in_source = any(s.repo == row.repo and s.id == row.id for s in entries)
        in_findings = any(f.repo == row.repo and row.id in f.ids for f in findings)
        if not in_source and not in_findings:
            problems.append((row.repo, row.id, "no open finding or ignore entry matches: remove the row"))
    for s in entries:
        row = index.get((s.repo, s.id))
        if row is None:
            problems.append((s.repo, s.id, f"in {s.where} but not in the exception register"))
        elif s.expires and s.expires != row.expires:
            problems.append((s.repo, s.id, f"{s.where} expires {s.expires}, register says {row.expires}"))
        elif s.expires is None and s.source in ("trivy", "pip-audit", "dependabot"):
            problems.append((s.repo, s.id, f"{s.where} carries no expiry"))
    return problems


# --------------------------------------------------------------------------------------------------------------------
# Feeds (CISA KEV, FIRST EPSS) with a file cache; the network call is injected


def default_fetch(timeout: float) -> Fetch:
    def fetch(url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https feed URLs from config
            return resp.read()
    return fetch


def _cache_fresh(path: Path, hours: float, now: float) -> bool:
    return path.exists() and now - path.stat().st_mtime < hours * 3600


def load_kev(cfg: dict, fetch: Fetch, cache_dir: Path, now: float) -> tuple[set[str], str]:
    """(KEV CVE ids, 'catalog <version>, <count> entries')."""
    feeds = cfg["feeds"]
    path = cache_dir / "kev.json"
    if _cache_fresh(path, feeds["cache_hours"], now):
        body = path.read_bytes()
    else:
        body = fetch(feeds["kev_url"])
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    doc = json.loads(body)
    ids = {v.get("cveID") for v in doc.get("vulnerabilities") or [] if isinstance(v, dict)}
    ids.discard(None)
    return ids, f"catalog {doc.get('catalogVersion', '?')}, {doc.get('count', len(ids))} entries"  # type: ignore


def load_epss(cfg: dict, cves: list[str], fetch: Fetch, cache_dir: Path, now: float) -> tuple[dict, str]:
    """({cve: (epss, percentile)}, 'scores of <date>'). Cached per CVE for cache_hours."""
    feeds = cfg["feeds"]
    path = cache_dir / "epss.json"
    cache: dict = {}
    if path.exists():
        try:
            cache = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            cache = {}
    max_age = feeds["cache_hours"] * 3600
    todo = [c for c in cves if c not in cache or now - cache[c].get("fetched", 0) >= max_age]
    for i in range(0, len(todo), int(feeds["epss_batch"])):
        batch = todo[i:i + int(feeds["epss_batch"])]
        doc = json.loads(fetch(f"{feeds['epss_url']}?cve={','.join(batch)}"))
        for row in doc.get("data") or []:
            cache[row["cve"]] = {"epss": _float(row.get("epss")), "percentile": _float(row.get("percentile")),
                                 "date": row.get("date", ""), "fetched": now}
        for cve in batch:   # a CVE FIRST does not score yet: remember that too, so it is not asked again
            cache.setdefault(cve, {"epss": None, "percentile": None, "date": "", "fetched": now})
    if todo:
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    scores = {c: (cache[c]["epss"], cache[c]["percentile"]) for c in cves if c in cache}
    dates = sorted({cache[c]["date"] for c in cves if c in cache and cache[c]["date"]})
    return scores, f"scores of {dates[-1]}" if dates else "no score returned"


def enrich(findings: list[Finding], kev: set[str] | None, epss: dict) -> None:
    for f in findings:
        cve = f.cve
        if kev is not None and f.source != "code-scanning":
            f.kev = bool(cve and cve in kev)
        if cve and cve in epss and epss[cve][0] is not None:
            f.epss, f.epss_percentile = epss[cve]
            f.epss_source = "first"


# --------------------------------------------------------------------------------------------------------------------
# Triage rule


def exposure_of(f: Finding, cfg: dict) -> str:
    exp = cfg["exposure"]
    if f.scope == "development":
        return exp.get("development_scope", "build")
    for rule in exp.get("rules") or []:
        if fnmatch.fnmatch(f.repo, rule.get("repo", "*")) and fnmatch.fnmatch(f.location, rule["path"]):
            return rule["exposure"]
    return exp["default"]


def classify(f: Finding, cfg: dict) -> tuple[str, list[str]]:
    rule = cfg["rule"]
    score = f.cvss
    if score is None:
        score = cfg["severity_scores"].get(f.severity)
        if score is not None:
            f.cvss_version = "severity"
    reasons: list[str] = []
    label = f"{f.severity} band {score:.1f}" if f.cvss_version == "severity" and score is not None else (
        f"CVSS {score:.1f}" if score is not None else "no score")
    if f.kev:
        cls = "P0"
        reasons.append("in CISA KEV")
    elif f.epss is not None and f.epss >= rule["p0_epss"]:
        cls = "P0"
        reasons.append(f"EPSS {f.epss:.2f} >= {rule['p0_epss']}")
    elif score is not None and score >= rule["p0_cvss"] and f.exposure == "internet":
        cls = "P0"
        reasons.append(f"{label} on internet-facing code")
    elif score is not None and score >= rule["p1_cvss"]:
        cls = "P1"
        reasons.append(label)
    elif f.epss_percentile is not None and f.epss_percentile >= rule["p1_epss_percentile"]:
        cls = "P1"
        reasons.append(f"EPSS percentile {f.epss_percentile:.2f}")
    elif score is not None and score >= rule["p2_cvss"]:
        cls = "P2"
        reasons.append(label)
    else:
        cls = "P3"
        reasons.append(label)
    if f.exposure == "build" and rule.get("build_moves_down") and cls != "P3":
        if not (f.kev and not rule.get("kev_moves_down")):
            cls = CLASSES[CLASSES.index(cls) + 1]
            reasons.append("build-only: one class down")
    return cls, reasons


def next_triage(as_of: dt.date) -> dt.date:
    year, month = (as_of.year + 1, 1) if as_of.month == 12 else (as_of.year, as_of.month + 1)
    return dt.date(year, month, 1)


def triage(findings: list[Finding], cfg: dict, register: list[Exception_], as_of: dt.date, env: str) -> None:
    sla = cfg["sla"][env]
    soon = int(cfg["sla"].get("due_soon_days", 7))
    default_owner = cfg["github"].get("default_owner", "tech lead")
    for f in findings:
        f.exposure = exposure_of(f, cfg)
        f.cls, f.reasons = classify(f, cfg)
        f.owner = f.owner or default_owner
        f.due = f.opened + dt.timedelta(days=int(sla[f.cls])) if f.cls in sla else None
        accepted = next((e for e in register if e.repo == f.repo and e.id in f.ids and e.expires >= as_of), None)
        if accepted:
            f.status = f"accepted until {accepted.expires}"
        elif f.due is None:
            f.status = f"next triage {next_triage(as_of)}"
        elif f.due < as_of:
            f.status = "past due"
        elif (f.due - as_of).days <= soon:
            f.status = "due soon"
        else:
            f.status = "open"
        if accepted:
            f.action = "exception (register)"
        elif f.source in ("dependabot", "trivy") and f.fixed_in:
            f.action = f"bump to {f.fixed_in}"
        elif f.source in ("dependabot", "trivy"):
            f.action = "no fix yet: exception or replace"
        elif f.exposure == "build":
            f.action = "fix or dismiss with a reason (build/test code)"
        else:
            f.action = "fix in code"


# --------------------------------------------------------------------------------------------------------------------
# GitHub reads (GET only, through an injected client)


def gh_cli(path: str, raw: bool = False) -> object:
    """Default client: `gh api` GET with the caller's login. Paginated lists come back one item per line."""
    if raw:
        cmd = ["gh", "api", "-H", "Accept: application/vnd.github.raw", path]
    else:
        cmd = ["gh", "api", "--paginate", "--jq", ".[]", path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise GhError(msg[0] if msg else f"gh exit {proc.returncode}")
    if raw:
        return proc.stdout
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


@dataclass
class RepoRead:
    repo: str
    dependabot: str = "not read"        # "<n> open" or "not readable: <reason>"
    code_scanning: str = "not read"


def read_github(cfg: dict, gh: GhClient, as_of: dt.date) -> tuple[list[Finding], list[SourceEntry], list[RepoRead]]:
    org = cfg["github"]["org"]
    ex = cfg["exceptions"]
    findings: list[Finding] = []
    entries: list[SourceEntry] = []
    reads: list[RepoRead] = []
    for repo in cfg["github"]["repos"]:
        rr = RepoRead(repo)
        base = f"repos/{org}/{repo}"
        try:
            open_alerts = gh(f"{base}/dependabot/alerts?state=open&per_page=100", False)
            got = parse_dependabot(repo, open_alerts)  # type: ignore[arg-type]
            findings += got
            rr.dependabot = f"{len(got)} open"
            dismissed = gh(f"{base}/dependabot/alerts?state=dismissed&per_page=100", False)
            entries += dismissals(repo, "dependabot", dismissed, ex["dependabot_reasons"])  # type: ignore[arg-type]
        except GhError as exc:
            rr.dependabot = f"not readable: {exc}"
        try:
            open_alerts = gh(f"{base}/code-scanning/alerts?state=open&per_page=100", False)
            got = parse_code_scanning(repo, open_alerts)  # type: ignore[arg-type]
            findings += got
            rr.code_scanning = f"{len(got)} open"
            dismissed = gh(f"{base}/code-scanning/alerts?state=dismissed&per_page=100", False)
            entries += dismissals(repo, "code-scanning", dismissed, ex["code_scanning_reasons"])  # type: ignore
        except GhError as exc:
            rr.code_scanning = f"not readable: {exc}"
        for name in cfg["github"].get("ignore_files") or []:
            try:
                text = gh(f"{base}/contents/{name}", True)
            except GhError:
                continue   # absent file: nothing accepted there
            entries += parse_ignore_file(repo, name, str(text))
        reads.append(rr)
    return findings, entries, reads


# --------------------------------------------------------------------------------------------------------------------
# Output


def cell(value: object) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def _ref_key(ref: str) -> tuple[int, str]:
    """#9 sorts before #10."""
    return (int(ref[1:]), "") if ref[1:].isdigit() else (1 << 30, ref)


def is_code_finding(f: Finding) -> bool:
    """A first-party code finding (CodeQL, or SARIF without a CVE), not a known vulnerability in a dependency."""
    return f.source == "code-scanning" or (f.source == "sarif" and not f.cve)


def label(f: Finding, public: bool) -> str:
    if public and is_code_finding(f):
        return f"{f.repo} code scanning {f.ref}"
    return f"{f.repo} {f.source} {f.ref} {f.package}"


def render_markdown(findings: list[Finding], problems: list[tuple[str, str, str]], register: list[Exception_],
                    reads: list[RepoRead], meta: dict, public: bool, record: bool = False) -> str:
    out: list[str] = []
    w = out.append
    if record:
        w("---")
        w(f"id: SEC-03-triage-{meta['month']}")
        w(f"title: Vulnerability triage {meta['month']}")
        w(f"description: Monthly vulnerability triage record for {meta['month']}: open findings by class, due dates, "
          "exceptions and the tech lead's decisions.")
        w("type: report")
        w("status: draft")
        w("owner: nghiep")
        w("audience: [engineer, devops, cto, agent]")
        w("applies_to: [ecosystem]")
        w(f"last_reviewed: {meta['as_of']}")
        w("related: [SEC-03]")
        w("---")
        w("")
    w(f"# Vulnerability triage record {meta['month']}")
    w("")
    w(f"Generated by `tools/security/vuln_triage.py` on {meta['as_of']} for the {meta['env']} SLA "
      f"(rule: [SEC-03](../vulnerability-management.md), config `tools/security/vuln_triage.toml`).")
    w("")
    w("## Sources")
    w("")
    w("| Source | State |")
    w("|---|---|")
    for rr in reads:
        w(f"| {rr.repo} Dependabot | {cell(rr.dependabot)} |")
        w(f"| {rr.repo} code scanning | {cell(rr.code_scanning)} |")
    for name, state in meta.get("inputs", []):
        w(f"| {cell(name)} | {cell(state)} |")
    w(f"| CISA KEV | {cell(meta['kev'])} |")
    w(f"| FIRST EPSS | {cell(meta['epss'])} |")
    w("")
    w("## Summary")
    w("")
    w("| Class | Fix within | Open | Past due | Due soon | Accepted |")
    w("|---|---|---|---|---|---|")
    sla = meta["sla"]
    for c in CLASSES:
        rows = [f for f in findings if f.cls == c]
        within = f"{sla[c]} days" if c in sla else "next triage"
        w(f"| {c} | {within} | {len(rows)} | {sum(f.status == 'past due' for f in rows)} | "
          f"{sum(f.status == 'due soon' for f in rows)} | {sum(f.status.startswith('accepted') for f in rows)} |")
    w("")
    order = {"past due": 0, "due soon": 1}
    for c in CLASSES:
        rows = sorted((f for f in findings if f.cls == c),
                      key=lambda f: (order.get(f.status, 2), f.due or dt.date.max, f.repo, _ref_key(f.ref)))
        w(f"## {c} ({len(rows)})")
        w("")
        withheld = [f for f in rows if public and is_code_finding(f)]
        rows = [f for f in rows if f not in withheld]
        if not rows:
            w("None." if not withheld else f"Code scanning only: {len(withheld)} (see the code scanning summary).")
            w("")
            continue
        if withheld:
            w(f"Plus {len(withheld)} code scanning findings (see the code scanning summary).")
            w("")
        w("| Repo | Source | Alert | Package or rule | Where | Advisory | Score | EPSS (pctl) | KEV | Exposure "
          "| Why | Opened | Due | Status | Owner | Proposed action |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for f in rows:
            score = f"{f.cvss:.1f} (v{f.cvss_version})" if f.cvss is not None else f.severity
            if f.cvss is None and f.cvss_version == "severity":
                score = f"{f.severity} (band)"
            epss = f"{f.epss:.3f} ({f.epss_percentile:.2f})" if f.epss is not None else "n/a"
            kev = "n/a" if is_code_finding(f) else ("not checked" if f.kev is None else "yes" if f.kev else "no")
            adv = ", ".join(i for i in f.ids if i.startswith(("GHSA-", "CVE-"))) or "—"
            w("| " + " | ".join(cell(x) for x in (
                f.repo, f.source, f.ref, f.package, f.location or "—", adv, score, epss, kev, f.exposure,
                "; ".join(f.reasons), f.opened, f.due or "—", f.status, f.owner, f.action)) + " |")
        w("")
    if public:
        render_code_summary(w, [f for f in findings if is_code_finding(f)])
    w("## Exceptions")
    w("")
    if register:
        w("| Repo | Finding | Source | Expires | Reason | Way out | Approved |")
        w("|---|---|---|---|---|---|---|")
        for e in register:
            w("| " + " | ".join(cell(x) for x in (
                e.repo, e.id, e.source, e.expires, e.reason, e.way_out, f"{e.approved_by}, {e.approved_on}")) + " |")
    else:
        w("The exception register (`docs/security/vuln-exceptions.toml`) has no row.")
    w("")
    if problems:
        w("Register cross-check:")
        w("")
        for repo, ident, text in problems:
            w(f"- {cell(repo)} `{cell(ident)}`: {cell(text)}")
    else:
        w("Register cross-check: every pip-audit ignore, Trivy ignore and risk-acceptance dismissal that was readable "
          "has a matching row, and no row is expired.")
    w("")
    if record:
        render_signoff(w, findings, problems, meta, public)
    return "\n".join(out)


def render_code_summary(w, code: list[Finding]) -> None:
    """Public record: code scanning alerts are visible to repo members only, so only counts and alert numbers."""
    w("## Code scanning (public summary)")
    w("")
    if not code:
        w("No open code scanning finding.")
        w("")
        return
    w("Code scanning alerts are visible only to members of each repo; this public record keeps counts and alert "
      "numbers, not rules or files.")
    w("")
    w("| Repo | Class | Exposure | Open | Alerts | Earliest due | Past due |")
    w("|---|---|---|---|---|---|---|")
    groups: dict[tuple[str, str, str], list[Finding]] = {}
    for f in code:
        groups.setdefault((f.repo, f.cls, f.exposure), []).append(f)
    for (repo, cls, exposure), rows in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
        refs = ", ".join(f.ref for f in sorted(rows, key=lambda f: _ref_key(f.ref)))
        dues = [f.due for f in rows if f.due]
        w("| " + " | ".join(cell(x) for x in (
            repo, cls, exposure, len(rows), refs, min(dues) if dues else "next triage",
            sum(f.status == "past due" for f in rows))) + " |")
    w("")


def render_signoff(w, findings: list[Finding], problems: list[tuple[str, str, str]], meta: dict,
                   public: bool = False) -> None:
    """The part the tech lead completes: one decision per P0/P1 or past-due row, then the sign-off line."""
    w("## Decisions and sign-off")
    w("")
    w(f"Prepared by Claude Code (agent) on {meta['as_of']}. Each row below needs a decision by the tech lead; P2 and "
      "P3 rows follow their proposed action unless a line here says otherwise.")
    w("")
    due = [f for f in findings if f.cls in ("P0", "P1") or f.status == "past due"]
    if due:
        w("| Finding | Class | Due | Owner | Proposed | Decision |")
        w("|---|---|---|---|---|---|")
        for f in sorted(due, key=lambda f: (f.cls, f.due or dt.date.max, f.repo, _ref_key(f.ref))):
            w("| " + " | ".join(cell(x) for x in (
                label(f, public), f.cls, f.due or "—", f.owner, f.action, "pending")) + " |")
    else:
        w("No P0 or P1 finding and nothing past due.")
    w("")
    for repo, ident, text in problems:
        w(f"- Exception {cell(repo)} `{cell(ident)}`: {cell(text)}. Decision: pending.")
    if problems:
        w("")
    w("Sign-off: tech lead, date: pending.")
    w("")


def render_json(findings: list[Finding], problems: list, register: list[Exception_], reads: list[RepoRead],
                meta: dict) -> str:
    def enc(o):
        if isinstance(o, dt.date):
            return o.isoformat()
        raise TypeError(type(o))
    return json.dumps({
        "meta": meta, "reads": [asdict(r) for r in reads],
        "findings": [{**asdict(f), "cve": f.cve} for f in findings],
        "exceptions": [asdict(e) for e in register],
        "problems": [{"repo": r, "id": i, "text": t} for r, i, t in problems],
    }, default=enc, indent=1)


# --------------------------------------------------------------------------------------------------------------------
# CLI


def _pairs(values: list[str], flag: str) -> list[tuple[str, Path]]:
    out = []
    for v in values:
        if "=" not in v:
            raise ValueError(f"{flag} wants REPO=FILE, got {v!r}")
        repo, path = v.split("=", 1)
        out.append((repo, Path(path)))
    return out


def run(argv: list[str] | None = None, *, fetch: Fetch | None = None, gh: GhClient | None = None,
        now: float | None = None, stdout=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    p.add_argument("--github", action="store_true", help="read the repos in the config through gh api (GET only)")
    p.add_argument("--input", action="append", default=[], metavar="REPO=FILE")
    p.add_argument("--ignore-file", action="append", default=[], metavar="REPO=FILE")
    p.add_argument("--as-of", type=dt.date.fromisoformat, default=None, help="record date (default today, UTC)")
    p.add_argument("--month", default=None, help="record month YYYY-MM (default: the month of --as-of)")
    p.add_argument("--env", choices=("dev", "prod"), default="dev")
    p.add_argument("--offline", action="store_true", help="skip the KEV and EPSS feeds")
    p.add_argument("--public", action="store_true", help="code scanning as counts and alert numbers only (no rule, no file)")
    p.add_argument("--record", action="store_true",
                   help="write the monthly record: front matter (SEC-03-triage-<month>) and a decisions section")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--strict", action="store_true", help="exit 1 on a past-due P0/P1 or an exception problem")
    args = p.parse_args(argv)
    stdout = stdout or sys.stdout
    now = time.time() if now is None else now
    as_of = args.as_of or dt.datetime.fromtimestamp(now, dt.timezone.utc).date()
    month = args.month or as_of.strftime("%Y-%m")

    try:
        cfg = load_config(args.config)
        register = load_register(args.register)
        if args.env not in cfg["sla"]:
            raise ValueError(f"no [sla] {args.env} in {args.config}")
        findings: list[Finding] = []
        entries: list[SourceEntry] = []
        reads: list[RepoRead] = []
        inputs: list[tuple[str, str]] = []
        for repo, path in _pairs(args.input, "--input"):
            got = parse_any(repo, json.loads(path.read_text(encoding="utf-8")), as_of)
            findings += got
            inputs.append((f"{repo} {path.name}", f"{len(got)} findings"))
        for repo, path in _pairs(args.ignore_file, "--ignore-file"):
            entries += parse_ignore_file(repo, path.name, path.read_text(encoding="utf-8"))
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"vuln_triage: {exc}", file=sys.stderr)
        return 2
    if args.github:
        got, ent, reads = read_github(cfg, gh or gh_cli, as_of)
        findings += got
        entries += ent

    kev_state, epss_state, kev, epss = "not checked (--offline)", "GitHub alert values only (--offline)", None, {}
    if not args.offline:
        fetch = fetch or default_fetch(cfg["feeds"]["timeout_seconds"])
        try:
            kev, kev_state = load_kev(cfg, fetch, args.cache_dir, now)
        except (OSError, ValueError) as exc:
            kev_state = f"not readable ({exc.__class__.__name__}): KEV not checked"
        cves = sorted({f.cve for f in findings if f.cve})
        try:
            epss, epss_state = load_epss(cfg, cves, fetch, args.cache_dir, now) if cves else ({}, "no CVE to score")
        except (OSError, ValueError, KeyError) as exc:
            epss_state = f"not readable ({exc.__class__.__name__}): GitHub alert values used"
    enrich(findings, kev, epss)
    triage(findings, cfg, register, as_of, args.env)
    problems = check_exceptions(register, entries, findings, as_of, int(cfg["exceptions"]["max_days"]))

    meta = {"month": month, "as_of": as_of.isoformat(), "env": args.env, "kev": kev_state, "epss": epss_state,
            "sla": cfg["sla"][args.env], "inputs": inputs}
    if args.format == "json":
        text = render_json(findings, problems, register, reads, meta)
    else:
        text = render_markdown(findings, problems, register, reads, meta, args.public, args.record)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    else:
        stdout.write(text if text.endswith("\n") else text + "\n")
    late = [f for f in findings if f.cls in ("P0", "P1") and f.status == "past due"]
    return 1 if args.strict and (late or problems) else 0


def main(argv: list[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":
    sys.exit(main())
