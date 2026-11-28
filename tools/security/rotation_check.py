#!/usr/bin/env python3
"""Weekly secret rotation and expiry check (AA-1183 part 2). METADATA ONLY: it never reads a secret value.

It compares the secrets register (docs/security/secrets-register.yaml, v2 rotation blocks, parsed by
secrets_register.py) with what the stores say about each row, and turns every overdue, unknown or missing item into a
finding:

  Secrets Manager   names, rotation settings, the creation date of the AWSCURRENT version (list-secrets,
                    list-secret-version-ids). The version date is an upper bound only (a host-only edit makes a new
                    version), so it can prove a recorded rotation did NOT happen, never that one did.
  GitHub            Actions secret names and updated_at per repo and environment (updated_at moves only when the value
                    is set). The API never returns a value.
  Cognito           the creation date of each app client secret (list-user-pool-client-secrets, which never reveals the
                    value). The app client "describe" call is never used: it returns the client secret.
  ACM               expiry, renewal status and eligibility per certificate in every acm:<region> of the register.
  KMS               key state and automatic rotation status (describe-key, get-key-rotation-status).
  IAM               the age of the active access keys of the account (list-users, list-access-keys; no user name is
                    ever printed).
  RDS               the server certificate CA and its expiry (describe-db-instances).
  Domains           the RDAP "expiration" event (RFC 9083).

Levels (windows and caps: tools/security/rotation_check.toml, never constants here):
  RED    overdue, last rotation unknown, missing from its store, a copy not updated after its primary rotated, the
         register claiming a rotation the store does not show, a certificate or domain within expiry_red_days of
         expiry (not renewed), automatic rotation off, or a source the check could not read.
  AMBER  due within amber_days (amber_days_short_interval for items of short_interval_max_days or less), an expiry
         within expiry_amber_days, a retired row whose revocation deadline is near, unregistered names.
  GREEN  everything else.

Outputs: one GitHub issue per finding in the root repo, label `secret-rotation` (deduplicated by title, edited when the
finding changes, closed when the row turns green in a run that READ its store: an issue whose store (or the whole
AWS / GitHub side) could not be read stays open, because its finding may only have dropped out); a machine-readable JSON of every row's due date for the ops
calendar (--json-out); a Markdown summary (--summary). Dry run by default: --apply writes issues.

Every AWS call goes through AwsCli, which refuses any operation outside AWS_CALLS; `iam-actions` prints the IAM
actions those calls need (the compliance evidence role in AA-CIS-Infra grants exactly these). Anything printed or
written is checked by assert_publishable first (public repo: no account ID, ARN, S3 URI or e-mail address).

Commands:
  python3 tools/security/rotation_check.py collect-github --out gh.json        (GH_TOKEN with Secrets + Environments read)
  python3 tools/security/rotation_check.py run [--github-inventory gh.json] [--aws] [--rdap]
                                               [--json-out due.json] [--summary s.md] [--apply] [--as-of YYYY-MM-DD]
  python3 tools/security/rotation_check.py iam-actions
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secrets_register as sr  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY = REPO_ROOT / "tools/security/rotation_check.toml"
SCHEMA_VERSION = 1
TITLE_PREFIX = "Secret rotation: "
KEY_MARKER = "<!-- rotation-check:key="
UPDATED_LINE = "Updated by the weekly Secret rotation check"
RUNBOOK = "docs/ops/runbooks/secret-rotation.md"
CERT_RUNBOOK = "docs/ops/runbooks/certificate-expiry.md"

GREEN, AMBER, RED = "green", "amber", "red"
_RANK = {GREEN: 0, AMBER: 1, RED: 2}

# The ONLY AWS calls of this tool: (CLI service, CLI operation) -> the IAM action it needs. All return metadata; none
# returns a secret value, a private key or a client secret. AwsCli refuses anything else.
AWS_CALLS: dict[tuple[str, str], str] = {
    ("secretsmanager", "list-secrets"): "secretsmanager:ListSecrets",
    ("secretsmanager", "list-secret-version-ids"): "secretsmanager:ListSecretVersionIds",
    ("cognito-idp", "list-user-pools"): "cognito-idp:ListUserPools",
    ("cognito-idp", "list-user-pool-clients"): "cognito-idp:ListUserPoolClients",
    ("cognito-idp", "list-user-pool-client-secrets"): "cognito-idp:ListUserPoolClientSecrets",
    ("acm", "list-certificates"): "acm:ListCertificates",
    ("acm", "describe-certificate"): "acm:DescribeCertificate",
    ("kms", "list-aliases"): "kms:ListAliases",
    ("kms", "describe-key"): "kms:DescribeKey",
    ("kms", "get-key-rotation-status"): "kms:GetKeyRotationStatus",
    ("iam", "list-users"): "iam:ListUsers",
    ("iam", "list-access-keys"): "iam:ListAccessKeys",
    ("rds", "describe-db-instances"): "rds:DescribeDBInstances",
}

# Keys dropped from every AWS answer before anything else sees it (defence in depth: e.g. the ClientSecretValue member
# of the Cognito descriptor shape, which list-user-pool-client-secrets leaves empty).
_SECRET_KEY = re.compile(r"(secret(value|string|binary)|privatekey|password|plaintext)", re.I)

ACM_KEY_TYPES = ["RSA_1024", "RSA_2048", "RSA_3072", "RSA_4096", "EC_prime256v1", "EC_secp384r1", "EC_secp521r1"]

_PUBLISH_BLOCKERS = [
    (re.compile(r"(?<![0-9A-Za-z])\d{12}(?![0-9A-Za-z])"), "an account ID"),
    (re.compile(r"arn:aws", re.I), "an ARN"),
    (re.compile(r"s3://", re.I), "an S3 URI (a bucket name)"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "an e-mail address"),
]


class CheckError(Exception):
    """The check cannot run (bad policy, register or arguments)."""


class SourceError(Exception):
    """One store could not be read; the run records it as a coverage finding and goes on."""


_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)


def assert_publishable(text: str, where: str) -> None:
    text = _UUID.sub("<uuid>", text)   # a UUID's last group is 12 digits at times (tenant secret names); not an account
    for rx, what in _PUBLISH_BLOCKERS:
        if rx.search(text):
            raise CheckError(f"{where} would publish {what}; refusing (public repo)")


def redact(text: str) -> str:
    """An error message made safe to publish (AWS errors carry the caller ARN and the account ID)."""
    text = re.sub(r"arn:aws[\w-]*:[^\s'\"]*", "<arn>", text)
    text = re.sub(r"(?<![0-9A-Za-z])\d{12}(?![0-9A-Za-z])", "<account>", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "<e-mail>", text)
    text = re.sub(r"s3://\S+", "<s3-uri>", text)
    return " ".join(text.split())[:300]


def scrub(obj):
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items() if not _SECRET_KEY.search(str(k))}
    if isinstance(obj, list):
        return [scrub(v) for v in obj]
    return obj


def to_date(value) -> Optional[dt.date]:
    """A date from an AWS/GitHub/RDAP timestamp (ISO 8601 string or epoch seconds) or a register string."""
    if value is None or value == "" or value == sr.UNKNOWN:
        return None
    if isinstance(value, dt.datetime):
        return value.astimezone(dt.timezone.utc).date() if value.tzinfo else value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc).date()
    text = str(value).strip()
    try:
        if len(text) == 10:
            return dt.date.fromisoformat(text)
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.astimezone(dt.timezone.utc).date() if parsed.tzinfo else parsed.date()
    except ValueError:
        return None


# ── Policy ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Policy:
    amber_days: int
    amber_days_short_interval: int
    short_interval_max_days: int
    expiry_amber_days: int
    expiry_red_days: int
    date_tolerance_days: int
    label: str
    label_color: str
    label_description: str
    max_writes_per_run: int
    github_owner: str
    github_repos: tuple[str, ...]
    aws_account_label: str
    aws_region: str
    rdap_default_base: str
    rdap_timeout_seconds: int
    rdap_overrides: dict

    def amber_window(self, interval_days: Optional[int]) -> int:
        if interval_days is not None and interval_days <= self.short_interval_max_days:
            return self.amber_days_short_interval
        return self.amber_days


def load_policy(path: Path = POLICY) -> Policy:
    import tomllib
    try:
        doc = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CheckError(f"cannot read the policy {path.name}: {type(exc).__name__}") from None
    try:
        w, i, s, r = doc["windows"], doc["issues"], doc["scope"], doc["rdap"]
        policy = Policy(
            amber_days=w["amber_days"], amber_days_short_interval=w["amber_days_short_interval"],
            short_interval_max_days=w["short_interval_max_days"], expiry_amber_days=w["expiry_amber_days"],
            expiry_red_days=w["expiry_red_days"], date_tolerance_days=w["date_tolerance_days"],
            label=i["label"], label_color=i["label_color"], label_description=i["label_description"],
            max_writes_per_run=i["max_writes_per_run"], github_owner=s["github_owner"],
            github_repos=tuple(s["github_repos"]), aws_account_label=s["aws_account_label"],
            aws_region=s["aws_region"], rdap_default_base=r["default_base"], rdap_timeout_seconds=r["timeout_seconds"],
            rdap_overrides=dict(r.get("overrides") or {}),
        )
    except (KeyError, TypeError) as exc:
        raise CheckError(f"policy {path.name}: missing or bad key {exc}") from None
    ints = ("amber_days", "amber_days_short_interval", "short_interval_max_days", "expiry_amber_days",
            "expiry_red_days", "date_tolerance_days", "max_writes_per_run", "rdap_timeout_seconds")
    for name in ints:
        value = getattr(policy, name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise CheckError(f"policy {path.name}: {name} must be a non-negative integer")
    if policy.expiry_red_days > policy.expiry_amber_days:
        raise CheckError(f"policy {path.name}: expiry_red_days must not exceed expiry_amber_days")
    if policy.amber_days_short_interval > policy.amber_days:
        raise CheckError(f"policy {path.name}: amber_days_short_interval must not exceed amber_days")
    if not policy.github_repos or not policy.label:
        raise CheckError(f"policy {path.name}: github_repos and label are required")
    return policy


# ── Inventory (what the stores say) ─────────────────────────────────────────────────────────────────────────────────
@dataclass
class Inventory:
    sources: dict = field(default_factory=dict)      # source -> "ok" | "error: <redacted message>"
    sm: dict = field(default_factory=dict)           # name -> {rotation_enabled, last_rotated, next_rotation, current_created}
    github: dict = field(default_factory=dict)       # "github:<repo>[/<env>]" -> {name: "YYYY-MM-DD"}
    cognito: dict = field(default_factory=dict)      # pool name -> {client name: [secret creation dates]} (pool absent = missing)
    kms: dict = field(default_factory=dict)          # alias -> {state, spec, rotation_enabled, next_rotation}
    acm: dict = field(default_factory=dict)          # region -> {domain: {not_after, renewal_status, eligibility, in_use, status}}
    rds: dict = field(default_factory=dict)          # instance -> {ca, valid_till}
    iam: dict = field(default_factory=dict)          # account label -> [creation dates of active access keys]
    domains: dict = field(default_factory=dict)      # domain -> expiry date | "error: ..."

    def ok(self, source: str) -> bool:
        return self.sources.get(source) == "ok"

    def to_json(self) -> dict:
        return {k: getattr(self, k) for k in ("sources", "sm", "github", "cognito", "kms", "acm", "rds", "iam",
                                              "domains")}

    @classmethod
    def from_json(cls, doc: dict) -> "Inventory":
        inv = cls()
        for k in ("sources", "sm", "github", "cognito", "kms", "acm", "rds", "iam", "domains"):
            if isinstance(doc.get(k), dict):
                setattr(inv, k, doc[k])
        return inv

    def merge(self, other: "Inventory") -> None:
        for k in ("sources", "sm", "github", "cognito", "kms", "acm", "rds", "iam", "domains"):
            getattr(self, k).update(getattr(other, k))


Runner = Callable[[list], tuple]


def _subprocess_runner(argv: list) -> tuple:
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
    return proc.returncode, proc.stdout, proc.stderr


class AwsCli:
    """The AWS CLI v2 with JSON output, limited to AWS_CALLS (credentials come from the environment)."""

    def __init__(self, runner: Runner = _subprocess_runner):
        self.runner = runner

    def call(self, service: str, operation: str, region: str, *args: str) -> dict:
        if (service, operation) not in AWS_CALLS:
            raise CheckError(f"aws {service} {operation} is not an allowed metadata call")
        argv = ["aws", service, operation, "--region", region, "--output", "json", "--no-cli-pager", *args]
        try:
            code, out, err = self.runner(argv)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SourceError(f"aws {service} {operation}: {type(exc).__name__}") from None
        if code != 0:
            first = (err or "").strip().splitlines()[-1:] or ["no error text"]
            raise SourceError(f"aws {service} {operation}: {redact(first[0])}")
        try:
            return scrub(json.loads(out or "{}"))
        except json.JSONDecodeError:
            raise SourceError(f"aws {service} {operation}: the answer is not JSON") from None


def _store_kind(store: str) -> tuple[str, str]:
    kind, _, rest = store.partition(":")
    return kind, rest


def _expected(entry: sr.Entry) -> bool:
    """A row that must exist in its store now."""
    return entry.status in ("keep", "open-item", "pending-x1")


def collect_aws(reg: sr.Register, policy: Policy, aws: AwsCli) -> Inventory:
    inv = Inventory()
    region, label = policy.aws_region, policy.aws_account_label
    rows = [e for e in reg.entries if e.status != "planned"]

    def guarded(source: str, fn) -> None:
        try:
            fn()
            inv.sources[source] = "ok"
        except SourceError as exc:
            inv.sources[source] = f"error: {exc}"

    sm_rows = [e for e in rows if e.store == f"secretsmanager:{label}"]
    if sm_rows:
        def sm():
            listed = aws.call("secretsmanager", "list-secrets", region)
            for s in listed.get("SecretList", []):
                inv.sm[s.get("Name", "")] = {
                    "rotation_enabled": bool(s.get("RotationEnabled")),
                    "last_rotated": _iso(s.get("LastRotatedDate")),
                    "next_rotation": _iso(s.get("NextRotationDate")),
                    "current_created": None,
                }
            for e in sm_rows:
                if e.name in inv.sm and _expected(e) and e.rotation and e.rotation.cls in ("scheduled", "on-incident"):
                    versions = aws.call("secretsmanager", "list-secret-version-ids", region, "--secret-id", e.name)
                    for v in versions.get("Versions", []):
                        if "AWSCURRENT" in (v.get("VersionStages") or []):
                            inv.sm[e.name]["current_created"] = _iso(v.get("CreatedDate"))
        guarded("aws:secretsmanager", sm)

    pools = sorted({_store_kind(e.store)[1] for e in rows if e.store.startswith("cognito:")})
    if pools:
        def cognito():
            listed = aws.call("cognito-idp", "list-user-pools", region, "--max-results", "60")
            ids = {p.get("Name"): p.get("Id") for p in listed.get("UserPools", [])}
            for pool in pools:
                if pool not in ids:
                    continue
                clients = aws.call("cognito-idp", "list-user-pool-clients", region, "--user-pool-id", ids[pool],
                                   "--max-results", "60")
                wanted = {e.name for e in rows if e.store == f"cognito:{pool}"}
                found: dict = {}
                for c in clients.get("UserPoolClients", []):
                    name = c.get("ClientName")
                    if name not in wanted:
                        found.setdefault(name, None)
                        continue
                    secrets = aws.call("cognito-idp", "list-user-pool-client-secrets", region, "--user-pool-id",
                                       ids[pool], "--client-id", c.get("ClientId", ""))
                    found[name] = sorted(d for d in (_iso(s.get("ClientSecretCreateDate"))
                                                     for s in secrets.get("ClientSecrets", [])) if d)
                inv.cognito[pool] = {k: v for k, v in found.items() if k in wanted}
        guarded("aws:cognito", cognito)

    kms_rows = [e for e in rows if e.store == f"kms:{label}"]
    if kms_rows:
        def kms():
            aliases = aws.call("kms", "list-aliases", region)
            targets = {a.get("AliasName"): a.get("TargetKeyId") for a in aliases.get("Aliases", [])}
            for e in kms_rows:
                key_id = targets.get(e.name)
                if not key_id:
                    continue
                meta = aws.call("kms", "describe-key", region, "--key-id", key_id).get("KeyMetadata", {})
                info = {"state": meta.get("KeyState"), "spec": meta.get("KeySpec"),
                        "rotation_enabled": None, "next_rotation": None}
                if meta.get("KeySpec") == "SYMMETRIC_DEFAULT" and meta.get("KeyManager") == "CUSTOMER":
                    rot = aws.call("kms", "get-key-rotation-status", region, "--key-id", key_id)
                    info["rotation_enabled"] = bool(rot.get("KeyRotationEnabled"))
                    info["next_rotation"] = _iso(rot.get("NextRotationDate"))
                inv.kms[e.name] = info
        guarded("aws:kms", kms)

    acm_regions = sorted({_store_kind(e.store)[1] for e in rows if e.store.startswith("acm:")})
    for acm_region in acm_regions:
        def acm(acm_region=acm_region):
            wanted = {e.name for e in rows if e.store == f"acm:{acm_region}"}
            listed = aws.call("acm", "list-certificates", acm_region, "--includes",
                              json.dumps({"keyTypes": ACM_KEY_TYPES}))
            best: dict = {}
            for c in listed.get("CertificateSummaryList", []):
                domain = c.get("DomainName")
                if domain not in wanted:
                    continue
                d = aws.call("acm", "describe-certificate", acm_region, "--certificate-arn",
                             c.get("CertificateArn", "")).get("Certificate", {})
                info = {"not_after": _iso(d.get("NotAfter")), "status": d.get("Status"),
                        "renewal_status": (d.get("RenewalSummary") or {}).get("RenewalStatus"),
                        "eligibility": d.get("RenewalEligibility"), "in_use": bool(d.get("InUseBy"))}
                cur = best.get(domain)
                if cur is None or _better_cert(info, cur):
                    best[domain] = info
            inv.acm[acm_region] = best
        guarded(f"aws:acm:{acm_region}", acm)

    rds_rows = [e for e in rows if e.store.startswith("rds:")]
    if rds_rows:
        def rds():
            for instance in sorted({_store_kind(e.store)[1] for e in rds_rows}):
                listed = aws.call("rds", "describe-db-instances", region, "--db-instance-identifier", instance)
                for db in listed.get("DBInstances", []):
                    details = db.get("CertificateDetails") or {}
                    inv.rds[instance] = {"ca": details.get("CAIdentifier") or db.get("CACertificateIdentifier"),
                                         "valid_till": _iso(details.get("ValidTill"))}
        guarded("aws:rds", rds)

    if any(e.store == f"iam:{label}" for e in rows):
        def iam():
            users = aws.call("iam", "list-users", region)
            dates: list = []
            for u in users.get("Users", []):
                keys = aws.call("iam", "list-access-keys", region, "--user-name", u.get("UserName", ""))
                for k in keys.get("AccessKeyMetadata", []):
                    if k.get("Status") == "Active" and _iso(k.get("CreateDate")):
                        dates.append(_iso(k.get("CreateDate")))
            inv.iam[label] = sorted(dates)
        guarded("aws:iam", iam)
    return inv


def _iso(value) -> Optional[str]:
    d = to_date(value)
    return d.isoformat() if d else None


def _better_cert(new: dict, cur: dict) -> bool:
    """Prefer an issued certificate, then the later expiry."""
    if (new.get("status") == "ISSUED") != (cur.get("status") == "ISSUED"):
        return new.get("status") == "ISSUED"
    return (new.get("not_after") or "") > (cur.get("not_after") or "")


# ── GitHub ──────────────────────────────────────────────────────────────────────────────────────────────────────────
Transport = Callable[[str, str, Optional[dict], dict], tuple]


def _urllib_transport(method: str, url: str, body: Optional[dict], headers: dict) -> tuple:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed https hosts
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = None
        return exc.code, payload, dict(exc.headers or {})


class GitHub:
    def __init__(self, token: str, transport: Transport = _urllib_transport, api: str = "https://api.github.com"):
        self.token, self.transport, self.api = token, transport, api.rstrip("/")

    def request(self, method: str, path: str, body: Optional[dict] = None) -> tuple:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                   "User-Agent": "aa-rotation-check"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        url = path if path.startswith("https://") else f"{self.api}{path}"
        return self.transport(method, url, body, headers)

    def get_all(self, path: str, key: Optional[str]) -> list:
        """Every page of a list endpoint (key: the list member of the object, None for a bare list)."""
        out: list = []
        sep = "&" if "?" in path else "?"
        page = 1
        while True:
            status, payload, _ = self.request("GET", f"{path}{sep}per_page=100&page={page}")
            if status != 200:
                message = (payload or {}).get("message", "") if isinstance(payload, dict) else ""
                raise SourceError(f"GET {path.split('?')[0]}: HTTP {status} {redact(str(message))}".strip())
            items = payload if key is None else (payload or {}).get(key, [])
            out += items or []
            if not items or len(items) < 100:
                return out
            page += 1


def collect_github(reg: sr.Register, policy: Policy, gh: GitHub) -> Inventory:
    inv = Inventory()
    owner = policy.github_owner
    register_envs: dict = {}
    for e in reg.entries:
        kind, rest = _store_kind(e.store)
        if kind == "github" and "/" in rest:
            repo, env = rest.split("/", 1)
            register_envs.setdefault(repo, set()).add(env)
    for repo in policy.github_repos:
        source = f"github:{repo}"
        try:
            secrets = gh.get_all(f"/repos/{owner}/{repo}/actions/secrets", "secrets")
            inv.github[source] = {s["name"]: _iso(s.get("updated_at")) for s in secrets}
            try:
                envs = {e["name"] for e in gh.get_all(f"/repos/{owner}/{repo}/environments", "environments")}
            except SourceError:
                envs = set()
            for env in sorted(envs | register_envs.get(repo, set())):
                quoted = urllib.parse.quote(env, safe="")
                try:
                    env_secrets = gh.get_all(f"/repos/{owner}/{repo}/environments/{quoted}/secrets", "secrets")
                except SourceError as exc:
                    if "HTTP 404" in str(exc):     # the environment does not exist (any more)
                        inv.github[f"{source}/{env}"] = {}
                        continue
                    raise
                inv.github[f"{source}/{env}"] = {s["name"]: _iso(s.get("updated_at")) for s in env_secrets}
            inv.sources[source] = "ok"
        except SourceError as exc:
            inv.sources[source] = f"error: {exc}"
    return inv


# ── RDAP ────────────────────────────────────────────────────────────────────────────────────────────────────────────
Fetch = Callable[[str, int], tuple]


def _urllib_fetch(url: str, timeout: int) -> tuple:
    req = urllib.request.Request(url, headers={"Accept": "application/rdap+json", "User-Agent": "aa-rotation-check"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - https RDAP servers
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        return exc.code, None


def collect_rdap(reg: sr.Register, policy: Policy, fetch: Fetch = _urllib_fetch) -> Inventory:
    inv = Inventory()
    for e in reg.entries:
        if not e.store.startswith("domain:") or not _expected(e):
            continue
        base = policy.rdap_overrides.get(e.name, policy.rdap_default_base)
        try:
            status, payload = fetch(f"{base}{urllib.parse.quote(e.name)}", policy.rdap_timeout_seconds)
        except (OSError, ValueError) as exc:
            inv.domains[e.name] = f"error: {type(exc).__name__}"
            continue
        if status != 200 or not isinstance(payload, dict):
            inv.domains[e.name] = f"error: RDAP HTTP {status}"
            continue
        expiry = next((_iso(ev.get("eventDate")) for ev in payload.get("events", [])
                       if ev.get("eventAction") == "expiration"), None)
        inv.domains[e.name] = expiry or "error: no expiration event"
    inv.sources["rdap"] = "ok"
    return inv


# ── Evaluation ──────────────────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class Item:
    entry: sr.Entry
    level: str = GREEN
    reasons: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    due: Optional[dt.date] = None
    due_from: Optional[str] = None           # "register" | "<store> <name>" (a copy's primary) | "store"
    last_rotated: Optional[str] = None
    last_source: str = "register"
    store_last: Optional[str] = None
    expires: Optional[dt.date] = None
    expires_source: Optional[str] = None
    days_left: Optional[int] = None

    def flag(self, level: str, reason: str) -> None:
        self.reasons.append(reason)
        if _RANK[level] > _RANK[self.level]:
            self.level = level


@dataclass
class Finding:
    title: str
    level: str
    body: str
    key: str


@dataclass
class Report:
    as_of: dt.date
    items: list
    findings: list
    coverage: dict


def _live_names(entry: sr.Entry, inv: Inventory, policy: Policy) -> tuple[Optional[bool], Optional[str], str]:
    """(present, trusted last-set date, source label) for a machine-checked store; present None = not checkable."""
    kind, rest = _store_kind(entry.store)
    label = policy.aws_account_label
    if kind == "github":
        repo = rest.split("/", 1)[0]
        if not inv.ok(f"github:{repo}") or entry.store not in inv.github:
            return None, None, ""
        names = inv.github[entry.store]
        return (entry.name in names), names.get(entry.name), "GitHub updated_at"
    if kind == "secretsmanager" and rest == label and inv.ok("aws:secretsmanager"):
        info = inv.sm.get(entry.name)
        if info is None:
            return False, None, ""
        if info.get("rotation_enabled") and info.get("last_rotated"):
            return True, info["last_rotated"], "Secrets Manager rotation"
        return True, None, ""
    if kind == "cognito" and inv.ok("aws:cognito"):
        clients = inv.cognito.get(rest)
        if clients is None or entry.name not in clients:
            return False, None, ""
        dates = clients[entry.name] or []
        return True, (dates[-1] if dates else None), "Cognito client secret creation"
    if kind == "kms" and rest == label and inv.ok("aws:kms"):
        return (entry.name in inv.kms), None, ""
    if kind == "acm" and inv.ok(f"aws:acm:{rest}"):
        return (entry.name in inv.acm.get(rest, {})), None, ""
    if kind == "rds" and inv.ok("aws:rds"):
        return (rest in inv.rds), None, ""
    if kind == "iam" and rest == label and inv.ok("aws:iam"):
        dates = inv.iam.get(label) or []
        return bool(dates), (dates[0] if dates else None), "oldest active IAM access key"
    return None, None, ""


def _sm_upper_bound(entry: sr.Entry, inv: Inventory, policy: Policy) -> Optional[dt.date]:
    """Creation date of the AWSCURRENT version: the value was set on or before it (never after)."""
    if entry.store != f"secretsmanager:{policy.aws_account_label}" or not inv.ok("aws:secretsmanager"):
        return None
    return to_date((inv.sm.get(entry.name) or {}).get("current_created"))


def evaluate(reg: sr.Register, inv: Inventory, policy: Policy, today: dt.date) -> Report:
    tol = dt.timedelta(days=policy.date_tolerance_days)
    keys = reg.by_key()
    items: list = []
    for e in reg.entries:
        r = e.rotation
        if r is None or e.status == "planned" or r.cls == "identifier":
            continue
        item = Item(entry=e)
        eff = sr.effective(e, reg)
        item.last_rotated = r.last_rotated
        present, store_last, store_label = _live_names(e, inv, policy)
        item.store_last = store_last

        if r.cls == "retired":
            _retired(item, present, eff, policy, today)
            items.append(item)
            continue

        if present is False and _expected(e):
            item.flag(RED, f"missing from {e.store}: the register says {e.status}, the store has no such name")

        reg_last = to_date(r.last_rotated)
        live_last = to_date(store_last)
        upper = _sm_upper_bound(e, inv, policy)
        claimed_by = None
        if live_last and reg_last and live_last + tol < reg_last:
            claimed_by = f"{store_label} {live_last}"
        elif upper and reg_last and upper + tol < reg_last:
            claimed_by = f"the current Secrets Manager version, created {upper}"
        if claimed_by:
            item.flag(RED, f"the register records a rotation on {reg_last}, but the store shows {claimed_by}: the "
                           "new value never reached this store, or last_rotated is wrong")
        if live_last and reg_last and live_last > reg_last + tol:
            item.notes.append(f"{store_label} is {live_last}, later than last_rotated {reg_last}: record it")
        if live_last and (reg_last is None or live_last > reg_last):
            item.last_rotated, item.last_source = live_last.isoformat(), store_label

        if r.copy_of is not None:
            _copy(item, keys.get(r.copy_of), eff, live_last or upper, policy, today)
        elif r.cls == "scheduled":
            _scheduled(item, eff, live_last if (live_last and (not reg_last or live_last > reg_last + tol)) else None,
                       policy, today)
        elif r.cls == "auto":
            _auto(item, inv, policy, today)

        exp_text, exp_source = _expiry(e, eff, inv, policy, item)
        if exp_text:
            item.expires, item.expires_source = to_date(exp_text), exp_source
            _expiry_window(item, policy, today)
        if e.store.startswith("cognito:") and len((inv.cognito.get(_store_kind(e.store)[1]) or {}).get(e.name)
                                                  or []) > 1:
            item.flag(AMBER, "the client has two secrets: delete the old one once every consumer uses the new one")
        items.append(item)

    findings = [_row_finding(i, policy, today) for i in items if i.level != GREEN]
    findings += _unregistered(reg, inv, policy)
    for source, state in sorted(inv.sources.items()):
        if state != "ok":
            findings.append(Finding(
                title=f"{TITLE_PREFIX}check could not read {source}", level=RED, key=f"source {source}",
                body=_coverage_body(source, state)))
    return Report(as_of=today, items=items, findings=findings, coverage=dict(inv.sources))


def _retired(item: Item, present: Optional[bool], eff: sr.Rotation, policy: Policy, today: dt.date) -> None:
    e = item.entry
    if e.status in ("deleted", "removed"):
        if present:
            item.flag(RED, f"still exists in {e.store} although the register marks it {e.status}: delete it (or fix "
                           "the row)")
        return
    if present is False:
        item.flag(AMBER, f"already gone from {e.store}: flip the row's status to deleted")
        return
    due = to_date(eff.next_due)
    if due is None:
        return
    item.due, item.due_from = due, "register"
    item.days_left = (due - today).days
    if item.days_left < 0:
        item.flag(RED, f"revocation overdue since {due} ({-item.days_left} days): revoke or delete it, then flip the "
                       "row to deleted")
    elif item.days_left <= policy.amber_days:
        item.flag(AMBER, f"revocation due {due} (in {item.days_left} days)")


def _copy(item: Item, primary: Optional[sr.Entry], eff: sr.Rotation, store_set: Optional[dt.date], policy: Policy,
          today: dt.date) -> None:
    """A copy row: stale when its store was last set before the primary's recorded rotation. Its due date is the
    primary's (reported in the JSON) and the primary row's own finding covers it, so it raises no due finding."""
    tol = dt.timedelta(days=policy.date_tolerance_days)
    e = item.entry
    p_last = to_date(primary.rotation.last_rotated) if (primary and primary.rotation) else None
    own_last = to_date(e.rotation.last_rotated)
    set_on = store_set or own_last
    if p_last and set_on and set_on + tol < p_last:
        where = "the store shows it set on" if store_set else "the register says it was set on"
        item.flag(RED, f"copy not updated after its primary ({e.rotation.copy_of}) rotated on {p_last}: {where} "
                       f"{set_on}")
    due = to_date(eff.next_due)
    if due:
        item.due, item.due_from = due, e.rotation.copy_of
        item.days_left = (due - today).days


def _scheduled(item: Item, eff: sr.Rotation, newer_live: Optional[dt.date], policy: Policy, today: dt.date) -> None:
    due = to_date(eff.next_due)
    source = "register"
    if newer_live and eff.interval_days:
        due, source = newer_live + dt.timedelta(days=eff.interval_days), "store"
    if due is None:
        item.flag(RED, "last rotation unknown: rotate it (or find the date) and record last_rotated and next_due")
        return
    item.due, item.due_from = due, source
    item.days_left = (due - today).days
    window = policy.amber_window(eff.interval_days)
    if item.days_left < 0:
        item.flag(RED, f"rotation overdue since {due} ({-item.days_left} days)")
    elif item.days_left <= window:
        item.flag(AMBER, f"rotation due {due} (in {item.days_left} days)")


def _auto(item: Item, inv: Inventory, policy: Policy, today: dt.date) -> None:
    e = item.entry
    tol = dt.timedelta(days=policy.date_tolerance_days)
    kind, rest = _store_kind(e.store)
    reg_due = to_date(e.rotation.next_due)
    if reg_due:
        item.due, item.due_from = reg_due, "register"
    if kind == "kms" and rest == policy.aws_account_label and e.name in inv.kms:
        info = inv.kms[e.name]
        if info.get("state") not in (None, "Enabled"):
            item.flag(RED, f"the key is {info.get('state')}")
        if info.get("rotation_enabled") is False:
            item.flag(RED, "automatic key rotation is off")
        nxt = to_date(info.get("next_rotation"))
        if nxt:
            item.due, item.due_from = nxt, "store"
            if nxt + tol < today:
                item.flag(RED, f"AWS rotation was due {nxt} and has not happened")
            if reg_due and abs((nxt - reg_due).days) > policy.date_tolerance_days:
                item.notes.append(f"KMS next rotation is {nxt}; the register says {reg_due}: update next_due")
    if item.due:
        item.days_left = (item.due - today).days


def _expiry(e: sr.Entry, eff: sr.Rotation, inv: Inventory, policy: Policy, item: Item) -> tuple:
    """(expiry date, source) from the store when it can be read, else the register's `expires`."""
    kind, rest = _store_kind(e.store)
    reg = eff.expires
    live, source = None, None
    if kind == "acm" and inv.ok(f"aws:acm:{rest}"):
        cert = (inv.acm.get(rest) or {}).get(e.name)
        if cert:
            live, source = cert.get("not_after"), "ACM"
            if cert.get("renewal_status") == "FAILED":
                item.flag(RED, "ACM managed renewal FAILED (see the certificate's renewal summary)")
            if cert.get("eligibility") == "INELIGIBLE":
                item.notes.append("ACM says the certificate is not eligible for managed renewal (not in use?): it will "
                                  "expire unless it is attached again or replaced")
    elif kind == "rds" and inv.ok("aws:rds"):
        db = inv.rds.get(rest)
        if db:
            live, source = db.get("valid_till"), "RDS"
            if db.get("ca") and db["ca"] not in e.name:
                item.flag(AMBER, f"the register names {e.name!r}, the instance uses the CA {db['ca']}: update the row")
    elif kind == "domain" and inv.ok("rdap"):
        got = inv.domains.get(e.name)
        if got and not str(got).startswith("error"):
            live, source = got, "RDAP"
        elif got:
            item.notes.append(f"RDAP lookup failed ({str(got)[7:]}): the register's expires date is used")
    if live:
        if reg and abs((to_date(live) - to_date(reg)).days) > policy.date_tolerance_days:
            item.notes.append(f"{source} expiry is {live}; the register says {reg}: update expires")
        return live, source
    return (reg, "register") if reg else (None, None)


def _expiry_window(item: Item, policy: Policy, today: dt.date) -> None:
    left = (item.expires - today).days
    if item.days_left is None or left < item.days_left:
        item.days_left = left
    what = "expired" if left < 0 else f"expires {item.expires} (in {left} days)"
    if left <= policy.expiry_red_days:
        renewal = " and has not been renewed" if left >= 0 else ""
        item.flag(RED, f"{what}{renewal}: see {CERT_RUNBOOK}" if item.entry.store.startswith(("acm:", "rds:"))
                  else f"{what}{renewal}")
    elif left <= policy.expiry_amber_days:
        item.flag(AMBER, what)


def _unregistered(reg: sr.Register, inv: Inventory, policy: Policy) -> list:
    known: dict = {}
    for e in reg.entries:
        known.setdefault(e.store, set()).add(e.name)
    out = []
    groups: dict = {}
    if inv.ok("aws:secretsmanager"):
        store = f"secretsmanager:{policy.aws_account_label}"
        groups[store] = sorted(n for n in inv.sm if n not in known.get(store, set()))
    for store, names in sorted(inv.github.items()):
        repo = store.split(":", 1)[1].split("/", 1)[0]
        if inv.ok(f"github:{repo}"):
            groups[store] = sorted(n for n in names if n not in known.get(store, set()))
    for store, names in sorted(groups.items()):
        if not names:
            continue
        lines = "\n".join(f"- `{n}`" for n in names)
        out.append(Finding(
            title=f"{TITLE_PREFIX}unregistered names in {store}", level=AMBER, key=f"unregistered {store}",
            body=(f"**AMBER**: {len(names)} name(s) in `{store}` have no row in docs/security/secrets-register.yaml.\n\n"
                  f"{lines}\n\nAdd a row for each (with its rotation block) or delete the secret if nothing uses it. "
                  "The register drift check (AA-CIS-Infra tools/secrets/register_check.py) reports the same.")))
    return out


def _row_finding(item: Item, policy: Policy, today: dt.date) -> Finding:
    e = item.entry
    r = e.rotation
    eff_interval = r.interval_days
    lines = [f"**{item.level.upper()}**: " + "; ".join(item.reasons), "", "| Field | Value |", "|---|---|",
             f"| Store | `{e.store}` |", f"| Name | `{e.name}` |", f"| Status | {e.status} |",
             f"| Class | {r.cls}" + (f", every {eff_interval} days" if eff_interval else "") + " |"]
    if r.copy_of:
        lines.append(f"| Copy of | `{r.copy_of}` |")
    if r.owner_role:
        lines.append(f"| Owner role | {r.owner_role} |")
    lines.append(f"| Last rotated | {item.last_rotated or '—'} ({item.last_source}) |")
    if item.due:
        lines.append(f"| Next due | {item.due} ({item.days_left} days) |")
    if item.expires:
        lines.append(f"| Expires | {item.expires} ({item.expires_source}) |")
    if r.method:
        lines.append(f"| Method | {r.method} |")
    body = "\n".join(lines)
    if r.how:
        body += f"\n\nHow: {r.how}"
    if item.notes:
        body += "\n\nNotes:\n" + "\n".join(f"- {n}" for n in item.notes)
    runbook = CERT_RUNBOOK if e.store.startswith(("acm:", "rds:")) else RUNBOOK
    body += (f"\n\nRunbook: `{runbook}`. Register: `docs/security/secrets-register.yaml` (record the new "
             "`last_rotated` and `next_due` in the same PR as any copy change).")
    return Finding(title=f"{TITLE_PREFIX}{e.store} {e.name}", level=item.level, body=body, key=e.key)


def _coverage_body(source: str, state: str) -> str:
    return (f"**RED**: the weekly check could not read `{source}`, so its rows were checked against the register dates "
            f"only.\n\nError: {state[len('error: '):] if state.startswith('error: ') else state}\n\n"
            "Usual causes: the compliance evidence role lacks the metadata permission (AA-CIS-Infra "
            "accounts/aa365/compliance_evidence.tf), the aa-ecosys-ci-bot App lacks Secrets / Environments read, or "
            "the ci-bot environment secret is missing (see the header of .github/workflows/secret-rotation.yml).")


# ── Outputs ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def due_json(report: Report, policy: Policy) -> dict:
    rows = []
    for i in sorted(report.items, key=lambda x: (x.due or dt.date.max, x.entry.store, x.entry.name)):
        r = i.entry.rotation
        rows.append({
            "store": i.entry.store, "name": i.entry.name, "status": i.entry.status, "class": r.cls,
            "interval_days": r.interval_days, "owner_role": r.owner_role, "method": r.method,
            "copy_of": r.copy_of, "last_rotated": i.last_rotated, "last_rotated_source": i.last_source,
            "next_due": i.due.isoformat() if i.due else None, "next_due_source": i.due_from,
            "expires": i.expires.isoformat() if i.expires else None, "expires_source": i.expires_source,
            "days_left": i.days_left, "level": i.level, "reasons": i.reasons, "notes": i.notes,
        })
    counts = {lvl: sum(1 for i in report.items if i.level == lvl) for lvl in (RED, AMBER, GREEN)}
    return {"schema_version": SCHEMA_VERSION, "generated_by": "tools/security/rotation_check.py",
            "as_of": report.as_of.isoformat(), "counts": counts, "coverage": report.coverage,
            "policy": {"amber_days": policy.amber_days, "amber_days_short_interval": policy.amber_days_short_interval,
                       "short_interval_max_days": policy.short_interval_max_days,
                       "expiry_amber_days": policy.expiry_amber_days, "expiry_red_days": policy.expiry_red_days},
            "items": rows,
            "findings": [{"title": f.title, "level": f.level, "key": f.key} for f in report.findings]}


def summary_md(report: Report) -> str:
    counts = {lvl: sum(1 for f in report.findings if f.level == lvl) for lvl in (RED, AMBER)}
    lines = [f"### Secret rotation check ({report.as_of})", "",
             f"- rows checked: {len(report.items)}; findings: {counts[RED]} red, {counts[AMBER]} amber",
             "- sources: " + (", ".join(f"{k} {'ok' if v == 'ok' else 'ERROR'}" for k, v in
                                        sorted(report.coverage.items())) or "register only"), ""]
    if report.findings:
        lines += ["| Level | Finding |", "|---|---|"]
        for f in sorted(report.findings, key=lambda f: (-_RANK[f.level], f.title)):
            lines.append(f"| {f.level} | {f.title[len(TITLE_PREFIX):]} |")
    return "\n".join(lines) + "\n"


def _normal(body: str) -> str:
    return "\n".join(line for line in body.strip().splitlines() if not line.startswith(UPDATED_LINE)).strip()


def issue_body(finding: Finding, as_of: dt.date, run_url: str) -> str:
    run = f" ({run_url})" if run_url else ""
    return (f"{finding.body}\n\n{UPDATED_LINE} on {as_of}{run}. It closes this issue when the row is green.\n"
            f"{KEY_MARKER}{finding.key} -->")


def _issue_key(body: str) -> Optional[str]:
    start = body.rfind(KEY_MARKER)
    if start < 0:
        return None
    end = body.find(" -->", start)
    return body[start + len(KEY_MARKER):end].strip() if end > 0 else None


def _store_source(store: str, policy: Policy) -> Optional[str]:
    """The source a store's live findings come from (the same stores _live_names reads); None = register only."""
    kind, rest = _store_kind(store)
    label = policy.aws_account_label
    if kind == "github":
        return f"github:{rest.split('/', 1)[0]}"
    if kind in ("secretsmanager", "kms", "iam") and rest == label:
        return f"aws:{kind}"
    if kind in ("cognito", "rds"):
        return f"aws:{kind}"
    if kind == "acm":
        return f"aws:acm:{rest}"
    if kind == "domain":
        return "rdap"
    return None


def _unchecked(key: Optional[str], coverage: dict, policy: Policy) -> Optional[str]:
    """Why an open issue was NOT checked this run (so a missing finding does not mean green), or None if it was.

    A store-backed finding drops out when its source could not be read (_live_names / _unregistered skip it), so
    closing it then would post a false 'Green'. Fails closed: an issue without a key marker is never closed."""
    if key is None:
        return "the issue has no rotation-check key marker"
    if key.startswith("source "):
        source = key[len("source "):]
        if source in coverage or (source in ("aws", "github") and any(k.startswith(source + ":") for k in coverage)):
            return None
        return f"{source} was not attempted"
    store = key[len("unregistered "):] if key.startswith("unregistered ") else key.split(" ", 1)[0]
    source = _store_source(store, policy)
    if source is None or coverage.get(source) == "ok":
        return None
    return f"{source} was not read" if source in coverage else f"{source} was not attempted"


def sync_issues(report: Report, policy: Policy, gh: GitHub, repo: str, apply: bool, run_url: str = "") -> list:
    """Open, edit and close the labelled issues so they match the findings. Returns the plan / action lines."""
    log: list = []
    writes = 0
    path = f"/repos/{repo}"
    if apply:
        status, _, _ = gh.request("GET", f"{path}/labels/{urllib.parse.quote(policy.label)}")
        if status == 404:
            gh.request("POST", f"{path}/labels", {"name": policy.label, "color": policy.label_color,
                                                   "description": policy.label_description})
            writes += 1
    try:
        issues = gh.get_all(f"{path}/issues?state=open&labels={urllib.parse.quote(policy.label)}", None)
    except SourceError as exc:
        if apply:
            raise CheckError(f"cannot list the open {policy.label} issues: {exc}") from None
        log.append(f"note: open issues not listed ({exc}); the plan assumes none are open")
        issues = []
    open_by_title: dict = {}
    for issue in sorted((i for i in issues if "pull_request" not in i), key=lambda i: i["number"]):
        open_by_title.setdefault(issue["title"], issue)
    wanted = {f.title: f for f in report.findings}

    def write(method: str, url: str, body: dict, line: str) -> bool:
        nonlocal writes
        if writes >= policy.max_writes_per_run:
            log.append(f"cap: max_writes_per_run={policy.max_writes_per_run} reached; skipped: {line}")
            return False
        if apply:
            status, payload, _ = gh.request(method, url, body)
            if status not in (200, 201):
                raise CheckError(f"{line}: HTTP {status}")
        writes += 1
        log.append(("" if apply else "would ") + line)
        return True

    for title, f in sorted(wanted.items(), key=lambda kv: (-_RANK[kv[1].level], kv[0])):
        body = issue_body(f, report.as_of, run_url)
        assert_publishable(title + "\n" + body, f"issue {title!r}")
        existing = open_by_title.get(title)
        if existing is None:
            write("POST", f"{path}/issues", {"title": title, "body": body, "labels": [policy.label]},
                  f"create [{f.level}] {title}")
        elif _normal(existing.get("body") or "") != _normal(body):
            write("PATCH", f"{path}/issues/{existing['number']}", {"body": body},
                  f"edit #{existing['number']} [{f.level}] {title}")
        else:
            log.append(f"unchanged #{existing['number']} [{f.level}] {title}")
    for title, issue in sorted(open_by_title.items()):
        if title in wanted or not title.startswith(TITLE_PREFIX):
            continue
        n = issue["number"]
        why = _unchecked(_issue_key(issue.get("body") or ""), report.coverage, policy)
        if why:
            log.append(f"kept #{n} open, not checked this run: {why}")
            continue
        comment = f"Green in the Secret rotation check of {report.as_of}" + (f" ({run_url})" if run_url else "") + "."
        assert_publishable(comment, f"comment on #{n}")
        if write("POST", f"{path}/issues/{n}/comments", {"body": comment}, f"comment #{n} green"):
            write("PATCH", f"{path}/issues/{n}", {"state": "closed", "state_reason": "completed"},
                  f"close #{n} {title}")
    return log


# ── CLI ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _write(path: Path, text: str, where: str) -> None:
    assert_publishable(text, where)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--register", type=Path, default=sr.REGISTER)
    ap.add_argument("--policy", type=Path, default=POLICY)
    sub = ap.add_subparsers(dest="cmd", required=True)
    cg = sub.add_parser("collect-github", help="GitHub secret names + updated_at (needs GH_TOKEN)")
    cg.add_argument("--out", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--github-inventory", type=Path, help="JSON written by collect-github")
    run.add_argument("--aws", action="store_true", help="read AWS metadata (credentials from the environment)")
    run.add_argument("--aws-unavailable", metavar="REASON", default="",
                     help="AWS could not be read this run (e.g. the role was not assumed): one coverage finding")
    run.add_argument("--rdap", action="store_true", help="look up domain expiry over RDAP")
    run.add_argument("--json-out", type=Path)
    run.add_argument("--summary", type=Path)
    run.add_argument("--apply", action="store_true", help="write GitHub issues (default: dry run)")
    run.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "AdventureAsia365-Ecosys/AA-Ecosys"))
    run.add_argument("--run-url", default="")
    run.add_argument("--as-of", type=dt.date.fromisoformat, default=None)
    sub.add_parser("iam-actions", help="the IAM actions of every AWS call this tool makes (JSON)")
    args = ap.parse_args(argv)

    if args.cmd == "iam-actions":
        print(json.dumps(sorted(set(AWS_CALLS.values())), indent=2))
        return 0
    try:
        policy = load_policy(args.policy)
        reg = sr.load(args.register)
        errors = sr.validate(reg)
        if errors:
            raise CheckError(f"the register has {len(errors)} validation errors (secrets_register.py validate)")
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
        if args.cmd == "collect-github":
            inv = collect_github(reg, policy, GitHub(token))
            _write(args.out, json.dumps({"sources": inv.sources, "github": inv.github}, indent=1, sort_keys=True),
                   "the GitHub inventory")
            print(f"github inventory: {sum(len(v) for v in inv.github.values())} names in {len(inv.github)} scopes; "
                  + ", ".join(f"{k} {v if v == 'ok' else 'ERROR'}" for k, v in sorted(inv.sources.items())))
            return 0
        inv = Inventory()
        if args.github_inventory:
            try:
                inv.merge(Inventory.from_json(json.loads(args.github_inventory.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError):
                inv.sources["github"] = "error: the GitHub inventory file is missing or not JSON"
        else:
            inv.sources["github"] = "error: no GitHub inventory (collect-github did not run or had no token)"
        if args.aws:
            inv.merge(collect_aws(reg, policy, AwsCli()))
        elif args.aws_unavailable:
            inv.sources["aws"] = f"error: {redact(args.aws_unavailable)}"
        if args.rdap:
            inv.merge(collect_rdap(reg, policy))
        today = args.as_of or dt.datetime.now(dt.timezone.utc).date()
        report = evaluate(reg, inv, policy, today)
        if args.json_out:
            _write(args.json_out, json.dumps(due_json(report, policy), indent=1) + "\n", "the due-dates JSON")
        text = summary_md(report)
        assert_publishable(text, "the summary")
        if args.summary:
            _write(args.summary, text, "the summary")
        print(text)
        for line in sync_issues(report, policy, GitHub(token), args.repo, args.apply, args.run_url):
            print(line)
        return 0
    except CheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except sr.RegisterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
