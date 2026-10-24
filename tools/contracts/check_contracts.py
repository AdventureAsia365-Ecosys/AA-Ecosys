#!/usr/bin/env python3
"""Cross-app contract check (AA-928). Needs jsonschema + PyYAML (tools/contracts/requirements.txt).

Checks every contract in docs/contracts/:

  JSON Schema event / view contracts (`<name>.v<major>[.<minor>].json`):
    J1  the file is a valid JSON Schema 2020-12 document;
    P1  the field policy of its major (`supply.hotel.v1` for `supply.hotel.v1.json` and `supply.hotel.v1.1.json`),
        as for HTTP contracts. A contract file added after the checker learnt JSON Schema contracts (AA-835) fails
        without a POLICY entry; the files that predate it are listed in JSON_PRE_CHECKER.

  HTTP contracts (`<name>.v<major>.openapi.yaml`, OpenAPI 3.1):
    O1  `openapi` is 3.1.x;
    O2  `info.title`, `info.version`, `info.x-aa-contract` (= the file name), `x-aa-producer`, `x-aa-consumers`;
    O3  every component schema is a valid JSON Schema 2020-12 schema;
    O4  every local `$ref` resolves;
    O5  operationIds are unique, every operation has responses, every `{param}` in a path is declared;
    O6  every security requirement names a declared scheme, and its scopes exist in that scheme;
    P1  the contract's field policy (POLICY below, from the CRM design): forbidden field names, PII markers
        (`x-pii`, keys starting `pii:`) and personal-data field names in contracts that must carry none.

  Samples (`docs/contracts/samples/<contract>/<case>.json`, see the folder README; <contract> is the HTTP contract
  name or the JSON Schema file name without `.json`):
    S1  the sample names an existing contract and, for an HTTP contract, a component schema (a JSON Schema contract
        sample has no `schema`: the payload is validated against the whole file);
    S2  `expect: valid` → the payload validates against the schema AND passes the field policy;
        `expect: invalid` → the schema or the policy rejects it;
    S3  a sample with `rule: <r>` must be rejected by that policy rule (proves the scan, independent of the schema);
    S4  every HTTP contract and every JSON Schema contract outside JSON_PRE_CHECKER has at least one valid sample,
        and the negative samples the design requires exist (REQUIRED_NEGATIVES).

  Registry:
    R1  docs/contracts/README.md names every contract file.

  App copies:
    M1  an app that vendors a contract (`apps/<repo>/docs/contracts/<same file name>`, e.g. AA-CIS-App's copy of
        catalog.http.v1 that its conformance test reads) holds a byte-identical copy. The app repos are separate
        checkouts under the workspace, so this runs where they are present (the workspace) and is skipped in this
        repo's CI, where apps/ is absent.

Usage:  python tools/contracts/check_contracts.py [--root <repo>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = Path("docs/contracts")
OPENAPI_FILE = re.compile(r"^(?P<name>[a-z0-9_.-]+\.v\d+)\.openapi\.yaml$")
SCHEMA_FILE = re.compile(r"^[a-z0-9_.-]+\.v\d+(\.\d+)?\.json$")
MAJOR = re.compile(r"^(?P<major>[a-z0-9_.-]+?\.v\d+)(\.\d+)?$")
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}

# Personal-data field names that a no-PII contract must not carry (heuristic on top of the x-pii / pii: markers).
PII_FIELD_NAMES = frozenset({
    "email", "email_address", "phone", "phone_number", "mobile", "display_name", "first_name", "last_name",
    "full_name", "given_name", "family_name", "dob", "date_of_birth", "birth_date", "birthday", "passport",
    "passport_number", "passport_no", "address", "street_address", "emergency_contact", "traveller_name",
    "traveler_name", "guest_name",
})
# Name endings that mark personal data whatever the prefix ("owner_email", "guest_phone").
PII_FIELD_SUFFIXES = ("_email", "_email_address", "_phone", "_phone_number")


@dataclass(frozen=True)
class Policy:
    """Field rules for one contract. Sources: design v3 §3.1, §4.8 (L1), §5.2 (Fix B19); AA-813 addendum (S238)."""

    forbidden_keys: frozenset[str] = frozenset()
    forbidden_patterns: tuple[str, ...] = ()
    no_pii: bool = True
    allowed_pii_classes: frozenset[str] = frozenset()
    # (component schema, property, x-pii class): the only personal-data fields a no-PII contract may carry. Each one
    # must be tagged with exactly that class and be writeOnly (sent once, never returned) — AA-941 first-owner invite.
    pii_write_only_fields: frozenset[tuple[str, str, str]] = frozenset()
    # Field names the personal-data name heuristic must not flag in this contract: business data that shares a name
    # with personal data (a hotel's street address). Forbidden keys and x-pii / pii: markers still apply.
    pii_name_exempt: frozenset[str] = frozenset()
    why: str = ""

    def write_only_pii(self, schema: str | None, prop: str) -> str | None:
        """The x-pii class allowed for this write-only field, or None."""
        for s_name, p_name, cls in self.pii_write_only_fields:
            if s_name == schema and p_name == prop:
                return cls
        return None


_SUPPLY_POLICY = Policy(
    forbidden_keys=frozenset({"supplier", "supplier_id", "net_amount", "net_rate", "rate", "rates", "margin",
                              "internal_notes", "notes", "links", "url"}),
    forbidden_patterns=(r"^suppliers?(_|$)", r"(^|_)net(_|$)", r"^rates?(_|$)", r"(^|_)rates?$",
                        r"(^|_)margins?(_|$)", r"(^|_)notes?$", r"(^|_)links?$", r"(^|_)urls?(_|$)",
                        r"(^|_)(price|cost|commission)s?(_|$)"),
    pii_name_exempt=frozenset({"address"}),
    why="supply facts only: no supplier identity, rates, margins, notes or links, and photos by entity_media id, "
        "never a URL (ADR 0004a decision 3); a hotel's address is business data",
)

POLICY: dict[str, Policy] = {
    # L1 console: "a response test forbids trip, pipeline and revenue keys"; no PII (design v3 §4.8, AA-928 R case).
    "crm.ops.v1": Policy(
        forbidden_keys=frozenset({"trip_count", "revenue"}),
        forbidden_patterns=(r"^trips?(_|$)", r"(^|_)trips?_count$", r"(^|_)revenue(_|$)", r"^pipeline",
                            r"(^|_)margin(_|$)", r"(^|_)commission(_|$)", r"(^|_)gmv(_|$)", r"(^|_)bookings?_value"),
        # AA-941: the first-owner invite sends the owner's address once (vault-encrypted by the CRM, never returned).
        pii_write_only_fields=frozenset({("OwnerInviteRequest", "owner_email", "contact")}),
        why="L1 console: no trip, pipeline, revenue, margin or commission figures and no personal data "
            "(one write-only field: the first-owner invite address)",
    ),
    # Fix B19: the agency price is b2b_price; the supplier net never leaves Booking. No PII crosses the API.
    "booking.b2b.v1": Policy(
        forbidden_keys=frozenset({"supplier_net"}),
        forbidden_patterns=(r"supplier_net", r"(^|_)net_cost(_|$)", r"(^|_)supplier_cost(_|$)",
                            r"(^|_)supplier_rate(_|$)"),
        why="b2b_price only; supplier net cost never leaves Booking; pax counts only",
    ),
    # Content only: prices come from booking.b2b.v1.
    "catalog.http.v1": Policy(
        forbidden_keys=frozenset({"supplier_net", "b2b_price"}),
        forbidden_patterns=(r"supplier_net",),
        why="published content only, no prices, no personal data",
    ),
    # Membership only: (iss, sub) is pii:online_id; no email, no display name, no CRM role (AA-978 R case).
    "tenant.membership.v1": Policy(
        forbidden_keys=frozenset({"crm_role", "role", "email", "display_name", "phone"}),
        no_pii=False,
        allowed_pii_classes=frozenset({"online_id"}),
        why="identity (iss, sub) and Content studio role only; never a CRM role, email or name",
    ),
    # Signed cache purge notice (AA-987): served-state events only; no prices, no personal data.
    "catalog.tour.lifecycle.v1": Policy(
        forbidden_keys=frozenset({"supplier_net", "b2b_price", "price"}),
        forbidden_patterns=(r"supplier_net",),
        why="tour keys and served-state events only, no prices, no personal data",
    ),
    # ISO 3166-1 reference data (AA-851, CIS 279): codes and names only, no prices, no personal data.
    "catalog.country.v1": Policy(
        forbidden_keys=frozenset({"supplier_net", "b2b_price", "price"}),
        forbidden_patterns=(r"supplier_net", r"(^|_)prices?(_|$)"),
        why="ISO 3166-1 reference data and destination country keys only; no prices, no personal data",
    ),
    # ADR 0004a decision 3 (AA-835): supply facts only. Supplier identity, contracts, rates, margins and internal
    # notes never reach CIS; photos travel as entity_media ids, never a free URL (SSRF, unlicensed images).
    "supply.hotel.v1": _SUPPLY_POLICY,
    "supply.service.v1": _SUPPLY_POLICY,
    # TripPlanner hand-off (AA-908 v1.4): the contact the traveller gave and, when signed in, the verified identity
    # (iss, sub) read from the token. The token itself, a password or a one-time code never crosses.
    "inquiry.submitted.v1": Policy(
        forbidden_keys=frozenset({"access_token", "id_token", "refresh_token", "token", "password", "otp"}),
        forbidden_patterns=(r"(^|_)tokens?$", r"(^|_)password", r"(^|_)otp(_|$)"),
        no_pii=False,
        why="the traveller's contact and verified identity only; never a token, password or one-time code",
    ),
}

# The negative samples the design requires (AA-928 Done-when R case). rule = a forbidden key, or "pii:".
REQUIRED_NEGATIVES: dict[str, tuple[str, ...]] = {
    "crm.ops.v1": ("trip_count", "revenue", "pii:"),
    "booking.b2b.v1": ("supplier_net",),
    # AA-835 S1: a supplier net amount, the supplier id, internal notes and a free photo URL are each refused.
    "supply.hotel.v1": ("net_amount", "supplier_id", "internal_notes", "url"),
    "supply.service.v1": ("net_amount", "supplier_id", "internal_notes", "url"),
    # AA-908: the hand-off never carries the traveller's token.
    "inquiry.submitted.v1.4": ("access_token",),
}

# JSON Schema contract files that predate the JSON field policy (AA-835): no POLICY entry or sample is required
# for them. A new file, including a new minor of these families, needs both (its family may add the entry).
JSON_PRE_CHECKER: frozenset[str] = frozenset({
    "catalog.graph.v1", "catalog.graph.v1.1", "catalog.graph.v1.2",
    "catalog.tour.v1", "catalog.tour.v1.1", "catalog.tour.v1.2", "catalog.tour.v1.3",
    "inquiry.submitted.v1", "inquiry.submitted.v1.1", "inquiry.submitted.v1.2", "inquiry.submitted.v1.3",
})


def policy_name(contract: str) -> str:
    """The POLICY key of a contract: its major (`supply.hotel.v1.1` -> `supply.hotel.v1`)."""
    m = MAJOR.match(contract)
    return m.group("major") if m else contract


@dataclass
class Report:
    errors: list[tuple[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, path: str, msg: str) -> None:
        self.errors.append((path, msg))


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------- field policy


def walk(node: Any, trail: str = "") -> Iterator[tuple[str, Any, Any]]:
    """Yield (trail, key, value) for every dict entry, depth first."""
    if isinstance(node, dict):
        for k, v in node.items():
            here = f"{trail}/{k}"
            yield here, k, v
            yield from walk(v, here)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{trail}/{i}")


def key_violation(policy: Policy, key: str) -> str | None:
    """The rule a field name breaks, or None. Returned value: the forbidden key, the pattern, 'pii:' or 'pii-name'."""
    low = key.lower()
    if low.startswith("pii:"):
        return "pii:"
    if low in policy.forbidden_keys:
        return low
    for pattern in policy.forbidden_patterns:
        if re.search(pattern, low):
            for fk in sorted(policy.forbidden_keys):  # report the design's key name when the pattern stands for it
                if re.search(pattern, fk):
                    return fk
            return pattern
    if policy.no_pii and low not in policy.pii_name_exempt and (low in PII_FIELD_NAMES
                                                                or low.endswith(PII_FIELD_SUFFIXES)):
        return "pii-name"
    return None


def scan_schema_doc(name: str, doc: dict, policy: Policy) -> list[str]:
    """Policy problems in a contract document: property names, required names and x-pii annotations."""
    problems: list[str] = []
    schemas = (doc.get("components") or {}).get("schemas") or {}

    def schema_of(trail: str) -> str | None:  # "/components/schemas/<S>/..." -> S
        parts = trail.split("/")
        return parts[3] if len(parts) > 3 and parts[1:3] == ["components", "schemas"] else None

    def allowed_field(trail: str, prop: str) -> str | None:
        cls = policy.write_only_pii(schema_of(trail), prop)
        if cls is None or trail != f"/components/schemas/{schema_of(trail)}/properties":
            return None
        return cls

    for trail, key, value in walk(doc):
        if key == "properties" and isinstance(value, dict):
            for prop in value:
                cls = allowed_field(trail, str(prop))
                if cls is not None:
                    spec = value[prop] if isinstance(value[prop], dict) else {}
                    if spec.get("x-pii") != cls or spec.get("writeOnly") is not True:
                        problems.append(f"{trail}/{prop}: {name} allows '{prop}' only as a writeOnly field tagged "
                                        f"x-pii '{cls}'")
                    continue
                rule = key_violation(policy, str(prop))
                if rule:
                    problems.append(f"{trail}/{prop}: field '{prop}' is not allowed in {name} ({rule}; {policy.why})")
        elif key == "required" and isinstance(value, list):
            for prop in value:
                if not isinstance(prop, str) or policy.write_only_pii(schema_of(trail), prop) is not None:
                    continue
                if key_violation(policy, prop):
                    problems.append(f"{trail}: required field '{prop}' is not allowed in {name}")
        elif key == "x-pii":
            parts = trail.split("/")
            prop = parts[-2] if len(parts) >= 2 else ""
            if allowed_field("/".join(parts[:-2]), prop) == str(value):
                continue
            if policy.no_pii:
                problems.append(f"{trail}: {name} must carry no personal data, but a field is tagged x-pii '{value}'")
            elif str(value) not in policy.allowed_pii_classes:
                problems.append(f"{trail}: x-pii class '{value}' is not allowed in {name} (allowed: "
                                + ", ".join(sorted(policy.allowed_pii_classes)) + ")")
    return problems


def scan_payload(policy: Policy, payload: Any, schema: str | None = None) -> list[tuple[str, str]]:
    """(rule, message) for every policy breach in a sample payload (a top-level write-only PII field the policy allows
    for that schema is accepted)."""
    found: list[tuple[str, str]] = []
    for trail, key, value in walk(payload):
        if trail.count("/") == 1 and policy.write_only_pii(schema, str(key)) is not None:
            continue
        rule = key_violation(policy, str(key))
        if rule:
            found.append((rule, f"{trail}: field '{key}' is forbidden ({rule})"))
        if isinstance(value, str) and value.lower().startswith("pii:"):
            found.append(("pii:", f"{trail}: value '{value[:40]}' is a pii: tag"))
    return found


# ---------------------------------------------------------------- OpenAPI structure


def resolve_pointer(doc: Any, pointer: str) -> Any:
    node = doc
    for part in pointer.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            raise KeyError(pointer)
    return node


def deref(doc: dict, node: Any) -> Any:
    seen = 0
    while isinstance(node, dict) and "$ref" in node and seen < 20:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return node
        node = resolve_pointer(doc, ref[1:])
        seen += 1
    return node


def check_openapi(path: Path, doc: Any, root: Path, report: Report) -> str | None:
    where = rel(path, root)
    m = OPENAPI_FILE.match(path.name)
    expected_name = m.group("name") if m else path.name
    if not isinstance(doc, dict):
        report.error(where, "not a YAML mapping")
        return None
    if not str(doc.get("openapi", "")).startswith("3.1."):
        report.error(where, f"O1 openapi must be 3.1.x, found {doc.get('openapi')!r}")
    info = doc.get("info") or {}
    for key in ("title", "version", "x-aa-contract", "x-aa-producer", "x-aa-consumers"):
        if not info.get(key):
            report.error(where, f"O2 info.{key} is missing")
    if info.get("x-aa-contract") and info["x-aa-contract"] != expected_name:
        report.error(where, f"O2 info.x-aa-contract is {info['x-aa-contract']!r}, the file name says {expected_name!r}")
    schemas = (doc.get("components") or {}).get("schemas") or {}
    for sname, schema in schemas.items():
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            report.error(where, f"O3 components.schemas.{sname} is not a valid 2020-12 schema: {exc.message}")
    for trail, key, value in walk(doc):
        if key == "$ref" and isinstance(value, str):
            if not value.startswith("#/"):
                report.error(where, f"O4 {trail}: only local $ref are allowed, found {value}")
                continue
            try:
                resolve_pointer(doc, value[1:])
            except KeyError:
                report.error(where, f"O4 {trail}: $ref {value} does not resolve")
    schemes = (doc.get("components") or {}).get("securitySchemes") or {}

    def check_security(reqs: Any, trail: str) -> None:
        for req in reqs or []:
            for scheme, scopes in (req or {}).items():
                if scheme not in schemes:
                    report.error(where, f"O6 {trail}: security scheme '{scheme}' is not declared")
                    continue
                declared: set[str] = set()
                for flow in ((schemes[scheme] or {}).get("flows") or {}).values():
                    declared |= set((flow or {}).get("scopes") or {})
                for scope in scopes or []:
                    if scope not in declared:
                        report.error(where, f"O6 {trail}: scope '{scope}' is not declared in '{scheme}'")

    check_security(doc.get("security"), "security")
    op_ids: dict[str, str] = {}
    for p, item in (doc.get("paths") or {}).items():
        item = item or {}
        path_params = {deref(doc, x).get("name") for x in item.get("parameters") or []
                       if isinstance(deref(doc, x), dict) and deref(doc, x).get("in") == "path"}
        for method, op in item.items():
            if method not in HTTP_METHODS:
                continue
            trail = f"paths.{p}.{method}"
            op = op or {}
            oid = op.get("operationId")
            if not oid:
                report.error(where, f"O5 {trail}: no operationId")
            elif oid in op_ids:
                report.error(where, f"O5 {trail}: operationId '{oid}' is also used by {op_ids[oid]}")
            else:
                op_ids[oid] = trail
            if not op.get("responses"):
                report.error(where, f"O5 {trail}: no responses")
            declared = set(path_params)
            for x in op.get("parameters") or []:
                x = deref(doc, x)
                if isinstance(x, dict) and x.get("in") == "path":
                    declared.add(x.get("name"))
            for needed in re.findall(r"{([^}]+)}", p):
                if needed not in declared:
                    report.error(where, f"O5 {trail}: path parameter '{needed}' is not declared")
            check_security(op.get("security"), trail)
    check_policy(where, expected_name, doc, report)
    return expected_name


def check_policy(where: str, name: str, doc: dict, report: Report, required: bool = True) -> None:
    """P1: the contract's field policy (by major) exists and its document breaks none of it."""
    policy = POLICY.get(policy_name(name))
    if policy is None:
        if required:
            report.error(where, f"P1 no field policy for {policy_name(name)}: add an entry to POLICY in "
                                "tools/contracts/check_contracts.py (reviewed code, not the contract file)")
        return
    for problem in scan_schema_doc(name, doc, policy):
        report.error(where, f"P1 {problem}")


# ---------------------------------------------------------------- samples


def validator_for(name: str, doc: dict, schema_name: str) -> Draft202012Validator:
    uri = f"urn:aa:contract:{name}"
    registry = Registry().with_resource(uri, Resource.from_contents(doc, default_specification=DRAFT202012))
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
              "$ref": f"{uri}#/components/schemas/{schema_name}"}
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def check_samples(samples_dir: Path, docs: dict[str, dict], root: Path, report: Report,
                  json_docs: dict[str, dict] | None = None) -> None:
    """Samples of HTTP contracts (`docs`, by contract name) and JSON Schema contracts (`json_docs`, by file stem)."""
    json_docs = json_docs or {}
    need_samples = set(docs) | {n for n in json_docs if n not in JSON_PRE_CHECKER}
    valid_count: dict[str, int] = {name: 0 for name in need_samples}
    negatives_seen: dict[str, set[str]] = {name: set() for name in set(docs) | set(json_docs)}
    if samples_dir.is_dir():
        files = sorted(p for p in samples_dir.rglob("*.json"))
    else:
        files = []
    for path in files:
        where = rel(path, root)
        try:
            sample = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.error(where, f"S1 not valid JSON: {exc}")
            continue
        name = sample.get("contract")
        if name != path.parent.name:
            report.error(where, f"S1 'contract' is {name!r} but the sample sits in {path.parent.name}/")
            continue
        schema_name = sample.get("schema")
        if name in json_docs:
            if schema_name is not None:
                report.error(where, f"S1 {name} is a JSON Schema contract: drop 'schema' (the whole file is the "
                                    "schema)")
                continue
            validator = Draft202012Validator(json_docs[name], format_checker=FormatChecker())
        elif name in docs:
            if schema_name not in ((docs[name].get("components") or {}).get("schemas") or {}):
                report.error(where, f"S1 {name} has no component schema {schema_name!r}")
                continue
            validator = validator_for(name, docs[name], schema_name)
        else:
            report.error(where, f"S1 no contract named {name}")
            continue
        expect = sample.get("expect")
        if expect not in ("valid", "invalid"):
            report.error(where, "S1 'expect' must be 'valid' or 'invalid'")
            continue
        payload = sample.get("payload")
        try:
            schema_errors = sorted(validator.iter_errors(payload), key=lambda e: [str(x) for x in e.absolute_path])
        except Exception as exc:  # noqa: BLE001 - a broken $ref (already reported as O4) must not crash the run
            report.error(where, f"S2 cannot validate against {schema_name}: {type(exc).__name__}: {str(exc)[:200]}")
            continue
        policy_hits = scan_payload(POLICY.get(policy_name(name), Policy()), payload, schema_name)
        if expect == "valid":
            for e in schema_errors:
                loc = "/".join(str(x) for x in e.absolute_path) or "(root)"
                report.error(where, f"S2 expected valid, schema error at {loc}: {e.message}")
            for _, msg in policy_hits:
                report.error(where, f"S2 expected valid, field policy: {msg}")
            if not schema_errors and not policy_hits:
                valid_count[name] = valid_count.get(name, 0) + 1
        else:
            if not schema_errors and not policy_hits:
                report.error(where, "S2 expected invalid, but both the schema and the field policy accept it")
            rule = sample.get("rule")
            if rule:
                if rule not in {r for r, _ in policy_hits}:
                    report.error(where, f"S3 the field policy does not flag rule '{rule}' (found: "
                                 + (", ".join(sorted({r for r, _ in policy_hits})) or "nothing") + ")")
                else:
                    negatives_seen[name].add(rule)
                    report.notes.append(f"{where}: rejected by field policy '{rule}'"
                                        + (f" and by the schema ({len(schema_errors)} errors)" if schema_errors
                                           else " (the schema alone would accept it)"))
    for name, count in valid_count.items():
        if count == 0:
            report.error(f"{CONTRACTS.as_posix()}/samples/{name}/", f"S4 {name} has no valid sample")
    for name, rules in REQUIRED_NEGATIVES.items():
        for rule in rules:
            if (name in docs or name in json_docs) and rule not in negatives_seen.get(name, set()):
                report.error(f"{CONTRACTS.as_posix()}/samples/{name}/",
                             f"S4 the design requires a rejected {name} sample with rule '{rule}'")


# ---------------------------------------------------------------- main


def check_app_copies(root: Path, report: Report) -> None:
    """M1: every app copy of a contract file equals the root file byte for byte."""
    compared = 0
    for path in sorted((root / CONTRACTS).glob("*")):
        if path.suffix not in (".json", ".yaml") or not path.is_file():
            continue
        for copy in sorted((root / "apps").glob(f"*/{CONTRACTS.as_posix()}/{path.name}")):
            compared += 1
            if copy.read_bytes() != path.read_bytes():
                report.error(rel(copy, root), f"M1 differs from the root {rel(path, root)}: copy the root file "
                                              "into the app (change the root first)")
    if compared:
        report.notes.append(f"M1 {compared} app contract copies compared")


def run(root: Path) -> Report:
    report = Report()
    contracts = root / CONTRACTS
    readme = (contracts / "README.md").read_text(encoding="utf-8") if (contracts / "README.md").exists() else ""
    json_docs: dict[str, dict] = {}
    for path in sorted(contracts.glob("*.json")):
        if not SCHEMA_FILE.match(path.name):
            report.error(rel(path, root), "J1 file name must be <name>.v<major>[.<minor>].json")
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except (json.JSONDecodeError, SchemaError) as exc:
            report.error(rel(path, root), f"J1 not a valid JSON Schema 2020-12 document: {exc}")
        else:
            json_docs[path.stem] = schema
            check_policy(rel(path, root), path.stem, schema, report, required=path.stem not in JSON_PRE_CHECKER)
        if path.name not in readme:
            report.error(rel(path, root), "R1 not listed in docs/contracts/README.md")
    docs: dict[str, dict] = {}
    for path in sorted(contracts.glob("*.yaml")):
        if not OPENAPI_FILE.match(path.name):
            report.error(rel(path, root), "O2 file name must be <name>.v<major>.openapi.yaml")
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            report.error(rel(path, root), f"O1 not valid YAML: {exc}")
            continue
        name = check_openapi(path, doc, root, report)
        if name:
            docs[name] = doc
        if path.name not in readme:
            report.error(rel(path, root), "R1 not listed in docs/contracts/README.md")
    check_samples(contracts / "samples", docs, root, report, json_docs)
    check_app_copies(root, report)
    report.notes.insert(0, f"{len(list(contracts.glob('*.json')))} JSON Schema contracts, {len(docs)} HTTP contracts")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    report = run(args.root.resolve())
    for note in report.notes:
        print(f"  {note}")
    for where, msg in report.errors:
        print(f"::error file={where},title=contracts::{msg}")
    print(f"contracts: {len(report.errors)} errors")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
