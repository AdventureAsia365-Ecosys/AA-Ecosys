#!/usr/bin/env python3
"""Cross-app contract check (AA-928). Needs jsonschema + PyYAML (tools/contracts/requirements.txt).

Checks every contract in docs/contracts/:

  JSON Schema event / view contracts (`<name>.v<major>[.<minor>].json`):
    J1  the file is a valid JSON Schema 2020-12 document.

  HTTP contracts (`<name>.v<major>.openapi.yaml`, OpenAPI 3.1):
    O1  `openapi` is 3.1.x;
    O2  `info.title`, `info.version`, `info.x-aa-contract` (= the file name), `x-aa-producer`, `x-aa-consumers`;
    O3  every component schema is a valid JSON Schema 2020-12 schema;
    O4  every local `$ref` resolves;
    O5  operationIds are unique, every operation has responses, every `{param}` in a path is declared;
    O6  every security requirement names a declared scheme, and its scopes exist in that scheme;
    P1  the contract's field policy (POLICY below, from the CRM design): forbidden field names, PII markers
        (`x-pii`, keys starting `pii:`) and personal-data field names in contracts that must carry none.

  Samples (`docs/contracts/samples/<contract>/<case>.json`, see the folder README):
    S1  the sample names an existing contract and component schema;
    S2  `expect: valid` → the payload validates against the schema AND passes the field policy;
        `expect: invalid` → the schema or the policy rejects it;
    S3  a sample with `rule: <r>` must be rejected by that policy rule (proves the scan, independent of the schema);
    S4  every HTTP contract has at least one valid sample, and the negative samples the design requires exist
        (REQUIRED_NEGATIVES).

  Registry:
    R1  docs/contracts/README.md names every contract file.

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
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}

# Personal-data field names that a no-PII contract must not carry (heuristic on top of the x-pii / pii: markers).
PII_FIELD_NAMES = frozenset({
    "email", "email_address", "phone", "phone_number", "mobile", "display_name", "first_name", "last_name",
    "full_name", "given_name", "family_name", "dob", "date_of_birth", "birth_date", "birthday", "passport",
    "passport_number", "passport_no", "address", "street_address", "emergency_contact", "traveller_name",
    "traveler_name", "guest_name",
})


@dataclass(frozen=True)
class Policy:
    """Field rules for one contract. Sources: design v3 §3.1, §4.8 (L1), §5.2 (Fix B19); AA-813 addendum (S238)."""

    forbidden_keys: frozenset[str] = frozenset()
    forbidden_patterns: tuple[str, ...] = ()
    no_pii: bool = True
    allowed_pii_classes: frozenset[str] = frozenset()
    why: str = ""


POLICY: dict[str, Policy] = {
    # L1 console: "a response test forbids trip, pipeline and revenue keys"; no PII (design v3 §4.8, AA-928 R case).
    "crm.ops.v1": Policy(
        forbidden_keys=frozenset({"trip_count", "revenue"}),
        forbidden_patterns=(r"^trips?(_|$)", r"(^|_)trips?_count$", r"(^|_)revenue(_|$)", r"^pipeline",
                            r"(^|_)margin(_|$)", r"(^|_)commission(_|$)", r"(^|_)gmv(_|$)", r"(^|_)bookings?_value"),
        why="L1 console: no trip, pipeline, revenue, margin or commission figures and no personal data",
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
}

# The negative samples the design requires (AA-928 Done-when R case). rule = a forbidden key, or "pii:".
REQUIRED_NEGATIVES: dict[str, tuple[str, ...]] = {
    "crm.ops.v1": ("trip_count", "revenue", "pii:"),
    "booking.b2b.v1": ("supplier_net",),
}


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
            for fk in policy.forbidden_keys:  # report the design's key name when the pattern stands for it
                if re.search(pattern, fk):
                    return fk
            return pattern
    if policy.no_pii and low in PII_FIELD_NAMES:
        return "pii-name"
    return None


def scan_schema_doc(name: str, doc: dict, policy: Policy) -> list[str]:
    """Policy problems in a contract document: property names, required names and x-pii annotations."""
    problems: list[str] = []
    for trail, key, value in walk(doc):
        if key == "properties" and isinstance(value, dict):
            for prop in value:
                rule = key_violation(policy, str(prop))
                if rule:
                    problems.append(f"{trail}/{prop}: field '{prop}' is not allowed in {name} ({rule}; {policy.why})")
        elif key == "required" and isinstance(value, list):
            for prop in value:
                if isinstance(prop, str) and key_violation(policy, prop):
                    problems.append(f"{trail}: required field '{prop}' is not allowed in {name}")
        elif key == "x-pii":
            if policy.no_pii:
                problems.append(f"{trail}: {name} must carry no personal data, but a field is tagged x-pii '{value}'")
            elif str(value) not in policy.allowed_pii_classes:
                problems.append(f"{trail}: x-pii class '{value}' is not allowed in {name} (allowed: "
                                + ", ".join(sorted(policy.allowed_pii_classes)) + ")")
    return problems


def scan_payload(policy: Policy, payload: Any) -> list[tuple[str, str]]:
    """(rule, message) for every policy breach in a sample payload."""
    found: list[tuple[str, str]] = []
    for trail, key, value in walk(payload):
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
    policy = POLICY.get(expected_name)
    if policy is None:
        report.error(where, f"P1 no field policy for {expected_name}: add an entry to POLICY in "
                            "tools/contracts/check_contracts.py (reviewed code, not the contract file)")
    else:
        for problem in scan_schema_doc(expected_name, doc, policy):
            report.error(where, f"P1 {problem}")
    return expected_name


# ---------------------------------------------------------------- samples


def validator_for(name: str, doc: dict, schema_name: str) -> Draft202012Validator:
    uri = f"urn:aa:contract:{name}"
    registry = Registry().with_resource(uri, Resource.from_contents(doc, default_specification=DRAFT202012))
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
              "$ref": f"{uri}#/components/schemas/{schema_name}"}
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def check_samples(samples_dir: Path, docs: dict[str, dict], root: Path, report: Report) -> None:
    valid_count: dict[str, int] = {name: 0 for name in docs}
    negatives_seen: dict[str, set[str]] = {name: set() for name in docs}
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
        if name not in docs:
            report.error(where, f"S1 no HTTP contract named {name}")
            continue
        schema_name = sample.get("schema")
        if schema_name not in ((docs[name].get("components") or {}).get("schemas") or {}):
            report.error(where, f"S1 {name} has no component schema {schema_name!r}")
            continue
        expect = sample.get("expect")
        if expect not in ("valid", "invalid"):
            report.error(where, "S1 'expect' must be 'valid' or 'invalid'")
            continue
        payload = sample.get("payload")
        try:
            schema_errors = sorted(validator_for(name, docs[name], schema_name).iter_errors(payload),
                                   key=lambda e: [str(x) for x in e.absolute_path])
        except Exception as exc:  # noqa: BLE001 - a broken $ref (already reported as O4) must not crash the run
            report.error(where, f"S2 cannot validate against {schema_name}: {type(exc).__name__}: {str(exc)[:200]}")
            continue
        policy_hits = scan_payload(POLICY.get(name, Policy()), payload)
        if expect == "valid":
            for e in schema_errors:
                loc = "/".join(str(x) for x in e.absolute_path) or "(root)"
                report.error(where, f"S2 expected valid, schema error at {loc}: {e.message}")
            for _, msg in policy_hits:
                report.error(where, f"S2 expected valid, field policy: {msg}")
            if not schema_errors and not policy_hits:
                valid_count[name] += 1
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
            if name in docs and rule not in negatives_seen.get(name, set()):
                report.error(f"{CONTRACTS.as_posix()}/samples/{name}/",
                             f"S4 the design requires a rejected {name} sample with rule '{rule}'")


# ---------------------------------------------------------------- main


def run(root: Path) -> Report:
    report = Report()
    contracts = root / CONTRACTS
    readme = (contracts / "README.md").read_text(encoding="utf-8") if (contracts / "README.md").exists() else ""
    for path in sorted(contracts.glob("*.json")):
        if not SCHEMA_FILE.match(path.name):
            report.error(rel(path, root), "J1 file name must be <name>.v<major>[.<minor>].json")
            continue
        try:
            Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, SchemaError) as exc:
            report.error(rel(path, root), f"J1 not a valid JSON Schema 2020-12 document: {exc}")
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
    check_samples(contracts / "samples", docs, root, report)
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
