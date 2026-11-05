"""PreToolUse guard (AA-969 part 2, root ADR 0019 d16): agents never read row-level personal data of tenant tables.

ADR 0019 d16 puts one real agency (the pilot) on Dev. Agents reach the shared RDS in three ways, all through Bash:
an S3-mediated ECS exec script (`aws s3 cp <file> s3://…` + `aws ecs execute-command`, or `tools/ecs/ecsx.sh <file>`),
an inline `--command` / `python3 -c` / `psql -c`, and a DB Migrate `run-script` dispatch (`gh workflow run db-migrate.yml
… script=db/scripts/<name>.py`, or `tools/github/dbmig.sh`), whose log is public. This hook reads the SQL those commands
carry before they run and refuses (exit 2) a statement that would return a value of a personal-data column; counts and
aggregates pass. The orchestrator and subagents alike.

How it decides (static, so a heuristic; AA-CIS-Infra's run-script guard plans every statement on the live database and
is the precise gate for run-scripts, db/scripts/README.md "Personal data"):

1. Personal-data columns: the ` · pii:<class>` tags of `docs/architecture/db-schema-reference.md` (the live dump of the
   DM-6.1 column comments), in schemas crm, booking, tripplanner and in the shared tables that have a tenant_id column;
   not the AA staff directory booking.staff_users (staff identities, not tenant or traveller data).
2. The SQL: every string literal of a .py file (adjacent and `+` concatenations joined, f-string holes as `?`), the
   whole text of a .sql file or an inline command. Comments and quoted literals are dropped.
3. A statement is refused when the select list of any SELECT (including subqueries), a RETURNING list, or a COPY of a
   table names a personal-data column of a table the statement reads (qualified `t.email` through its alias, or a bare
   `email` when one of the tables in its FROM / JOIN has it), `*` / `t.*` of such a table, or such a table's whole row
   (`row_to_json(t)`, `to_jsonb(t)`, `json_agg(t)`, `array_agg(t)`). Allowed: the column inside `count(...)` (with its
   FILTER) and in an `IS [NOT] NULL` test, and anywhere in WHERE / JOIN / GROUP BY / ORDER BY.
4. Unreadable input passes (exit 0): this hook saves an agent from a mistake; the review and the Infra guard remain.

Test: python3 -m unittest .claude/hooks/test_pilot_pii_guard.py (or bash .claude/hooks/pilot-pii-guard.sh < input).
"""
from __future__ import annotations

import ast
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
REFERENCE = ROOT / "docs/architecture/db-schema-reference.md"
INFRA = ROOT / "infra/AA-CIS-Infra"
TENANT_SCHEMAS = ("crm", "booking", "tripplanner")
# AA staff directories: staff identities, not a tenant's or a traveller's data (seeds link created_by through them).
STAFF_TABLES = frozenset({("booking", "staff_users")})

_AWS = r"aws(?:\s+--[a-z-]+(?:\s+[^-\s]\S*)?)*"
S3_CP_RE = re.compile(rf"{_AWS}\s+s3\s+cp\s+(\S+)\s+s3://")
ECS_EXEC_RE = re.compile(rf"{_AWS}\s+ecs\s+execute-command\b")
ECSX_RE = re.compile(r"(?:^|[\s/;&|(])ecsx\.sh\s+((?:\S+\s*)+)")
RUN_SCRIPT_RE = re.compile(r"(?:script=|run-script:)(db/scripts/[A-Za-z0-9_]+\.py)")
DB_MIGRATE_RE = re.compile(r"(gh\s+workflow\s+run\b|dbmig\.sh)")
PSQL_RE = re.compile(r"(?:^|[\s;&|(])psql\b")
INLINE_RE = re.compile(r"(?:--command|-c)\s+(\"(?:[^\"\\]|\\.)*\"|'[^']*')")

IDENT = r'(?:"(?:[^"]|"")+"|[A-Za-z_][A-Za-z0-9_$]*)'
TABLE_RE = re.compile(rf"\b({'|'.join(TENANT_SCHEMAS + ('shared',))})\.({IDENT})(?:\s+(?:AS\s+)?({IDENT}))?", re.I)
KEYWORDS = {"where", "join", "left", "right", "inner", "outer", "full", "cross", "on", "using", "group", "order",
            "limit", "offset", "having", "window", "union", "except", "intersect", "returning", "for", "set",
            "values", "select", "from", "lateral", "natural", "and", "or", "not", "as", "when", "then", "else",
            "end", "fetch", "tablesample", "with", "into", "do", "default", "is", "null", "in"}
END_SELECT_LIST = re.compile(r"\bFROM\b", re.I)
END_FROM = re.compile(r"\b(WHERE|GROUP|ORDER|LIMIT|HAVING|WINDOW|UNION|EXCEPT|INTERSECT|RETURNING|FOR|OFFSET|FETCH)\b",
                      re.I)
WHOLE_ROW_RE = re.compile(rf"\b(?:row_to_json|to_json|to_jsonb|json_agg|jsonb_agg|array_agg|json_build_array)\s*\(\s*"
                          rf"({IDENT})\s*\)", re.I)
NULL_TEST_RE = re.compile(rf"(?:{IDENT}\.)?{IDENT}\s+IS\s+(?:NOT\s+)?NULL", re.I)
QUALIFIED_RE = re.compile(rf"({IDENT})\.({IDENT}|\*)")
BARE_RE = re.compile(rf"(?<![\w.\"$])({IDENT})(?![\w\"$]|\s*\(|\.)")


# ── the protected columns ────────────────────────────────────────────────────────────────────────────────────────────
def load_protected(text: str) -> dict:
    """(schema, table) -> the personal-data column names, from the schema reference text."""
    out: dict = {}
    table, cols, has_tenant, in_block = None, set(), False, False

    def close():
        if table and cols and table not in STAFF_TABLES and (
                table[0] in TENANT_SCHEMAS or (table[0] == "shared" and has_tenant)):
            out[table] = set(cols)

    for line in text.splitlines():
        m = re.match(r"^### `([a-z_]+)\.([A-Za-z0-9_]+)`", line)
        if m:
            close()
            table, cols, has_tenant, in_block = (m.group(1), m.group(2)), set(), False, False
            continue
        if table is None:
            continue
        if line.startswith("```"):
            in_block = not in_block
            continue
        if in_block:
            name = line.split(" ", 1)[0]
            has_tenant = has_tenant or name == "tenant_id"
            if "· pii:" in line:
                cols.add(name)
    close()
    return out


# ── SQL out of a file or a command ───────────────────────────────────────────────────────────────────────────────────
def _str_expr(node) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else " ? " for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _str_expr(node.left), _str_expr(node.right)
        if left is not None or right is not None:
            return (left or " ? ") + (right or " ? ")
    return None


def python_sql(source: str) -> list:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [source]
    found, inside = [], set()
    for node in ast.walk(tree):
        if id(node) in inside:
            continue
        text = _str_expr(node)
        if text is not None:
            found.append(text)
            inside.update(id(n) for n in ast.walk(node))
    return found


def _clean(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def _split_top(text: str, sep: str = ",") -> list:
    parts, depth, cur = [], 0, []
    for ch in text:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _top_level_search(pattern, text: str, start: int):
    """The first match of ``pattern`` at paren depth 0 from ``start`` (stops at a closing paren of depth -1)."""
    depth, i = 0, start
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return None, i
        elif depth == 0:
            m = pattern.match(text, i)
            if m and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
                return m, i
        i += 1
    return None, len(text)


def _strip_allowed(item: str) -> str:
    out, i, low = [], 0, item.lower()
    while i < len(item):
        if low.startswith("count", i) and re.match(r"count\s*\(", low[i:]) and (
                i == 0 or not (item[i - 1].isalnum() or item[i - 1] in "_.")):
            j = item.index("(", i)
            depth = 0
            while j < len(item):
                depth += {"(": 1, ")": -1}.get(item[j], 0)
                j += 1
                if depth == 0:
                    break
            m = re.match(r"\s*FILTER\s*\(", item[j:], re.I)
            if m:
                depth, j = 1, j + m.end()
                while j < len(item) and depth:
                    depth += {"(": 1, ")": -1}.get(item[j], 0)
                    j += 1
            out.append(" 0 ")
            i = j
            continue
        out.append(item[i])
        i += 1
    text = NULL_TEST_RE.sub(" true ", "".join(out))
    return re.sub(rf"\s+AS\s+{IDENT}\s*$", "", text, flags=re.I)


def _unquote(name: str) -> str:
    return name[1:-1].replace('""', '"') if name.startswith('"') else name.lower()


def _tables(text: str, protected: dict) -> dict:
    """alias -> (schema, table) for every protected table the text names (the table name is its own alias too)."""
    out = {}
    for schema, table, alias in TABLE_RE.findall(text):
        rel = (schema.lower(), _unquote(table))
        if rel not in protected:
            continue
        out[rel[1]] = rel
        if alias and alias.lower() not in KEYWORDS:
            out[_unquote(alias)] = rel
    return out


def _list_reads(items: str, rels: dict, protected: dict) -> list:
    found = []
    for item in _split_top(items):
        text = _strip_allowed(item)
        if re.fullmatch(r"\s*\*\s*", text):
            found += [f"{s}.{t}.*" for s, t in sorted(set(rels.values()))]
            continue
        for alias in WHOLE_ROW_RE.findall(text):
            rel = rels.get(_unquote(alias))
            if rel:
                found.append(f"{rel[0]}.{rel[1]}.* (whole row)")
        for alias, col in QUALIFIED_RE.findall(text):
            rel = rels.get(_unquote(alias))
            if rel and (col == "*" or _unquote(col) in protected[rel]):
                found.append(f"{rel[0]}.{rel[1]}.{_unquote(col) if col != '*' else '*'}")
        bare = QUALIFIED_RE.sub(" ", WHOLE_ROW_RE.sub(" ", text))
        for name in BARE_RE.findall(bare):
            col = _unquote(name)
            for rel in sorted(set(rels.values())):
                if col in protected[rel]:
                    found.append(f"{rel[0]}.{rel[1]}.{col}")
    return found


def statement_reads(sql: str, protected: dict) -> list:
    """The personal-data columns one SQL text would return (``schema.table.column``); empty = allowed."""
    text = _clean(sql)
    found = []
    for m in re.finditer(r"\bSELECT\b", text, re.I):
        start = m.end()
        dm = re.match(r"\s*(DISTINCT\s+ON\s*\([^)]*\)|DISTINCT|ALL)\b", text[start:], re.I)
        if dm:
            start += dm.end()
        fm, end = _top_level_search(END_SELECT_LIST, text, start)
        if fm is None:
            continue                                   # SELECT without FROM: no table
        items = text[start:end]
        wm, from_end = _top_level_search(END_FROM, text, fm.end())
        rels = _tables(text[fm.end():from_end], protected)
        if rels:
            found += _list_reads(items, rels, protected)
    for m in re.finditer(r"\bRETURNING\b", text, re.I):
        head = text[:m.start()]
        target = re.findall(r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(\w+\.\w+(?:\s+(?:AS\s+)?\w+)?)", head, re.I)
        if target:
            rels = _tables(target[-1], protected)
            stop = re.search(r";", text[m.end():])
            items = text[m.end():m.end() + stop.start()] if stop else text[m.end():]
            if rels:
                found += _list_reads(items, rels, protected)
    for m in re.finditer(rf"\bCOPY\s+({IDENT}\.{IDENT})\s*(\([^)]*\))?\s+TO\b", text, re.I):
        rels = _tables(m.group(1), protected)
        if rels:
            (rel,) = set(rels.values())
            cols = [_unquote(c.strip()) for c in (m.group(2) or "").strip("()").split(",") if c.strip()]
            hit = [c for c in cols if c in protected[rel]] if cols else ["*"]
            found += [f"{rel[0]}.{rel[1]}.{c}" for c in hit]
    return sorted(set(found))


def text_reads(text: str, protected: dict, *, python: bool) -> list:
    pieces = python_sql(text) if python else [text]
    found = []
    for piece in pieces:
        for stmt in _split_top(piece, ";"):
            found += statement_reads(stmt, protected)
    return sorted(set(found))


# ── which commands reach the database ────────────────────────────────────────────────────────────────────────────────
def _read_local(path: str, cwd: str) -> str | None:
    p = Path(os.path.expanduser(path))
    if not p.is_absolute():
        p = Path(cwd) / p
    try:
        return p.read_text(encoding="utf-8") if p.is_file() else None
    except (OSError, UnicodeDecodeError):
        return None


def _read_infra_main(path: str) -> str | None:
    """The run-script file DB Migrate would run: the Infra repo's origin/main copy, else the checkout's file."""
    try:
        out = subprocess.run(["git", "-C", str(INFRA), "show", f"origin/main:{path}"], capture_output=True, text=True,
                             timeout=10)
        if out.returncode == 0:
            return out.stdout
    except (OSError, subprocess.SubprocessError):
        pass
    return _read_local(str(INFRA / path), str(ROOT))


def sources(command: str, cwd: str) -> list:
    """(label, text, is_python) of every SQL-bearing input the command sends to the database."""
    out = []
    for m in S3_CP_RE.finditer(command):
        path = m.group(1).strip("'\"")
        text = _read_local(path, cwd)
        if text is not None:
            out.append((path, text, path.endswith(".py")))
    m = ECSX_RE.search(command)
    if m:
        for word in shlex.split(m.group(1), posix=True) if m.group(1) else []:
            if word.endswith((".py", ".sql")):
                text = _read_local(word, cwd)
                if text is not None:
                    out.append((word, text, word.endswith(".py")))
    if DB_MIGRATE_RE.search(command):
        for path in RUN_SCRIPT_RE.findall(command):
            text = _read_infra_main(path)
            if text is not None:
                out.append((f"AA-CIS-Infra {path}", text, True))
    if ECS_EXEC_RE.search(command) or PSQL_RE.search(command):
        for raw in INLINE_RE.findall(command):
            inner = raw[1:-1].replace('\\"', '"')
            # the SQL may sit one quoting level further in (a psql -c inside an ECS exec --command)
            for piece in [inner, *re.findall(r"'([^']*)'", inner), *re.findall(r'"([^"]*)"', inner)]:
                out.append(("inline command", piece, False))
        for f in re.findall(r"(?:^|\s)-f\s+(\S+\.sql)", command):
            text = _read_local(f, cwd)
            if text is not None:
                out.append((f, text, False))
    return out


def check(data: dict, protected: dict | None = None) -> str | None:
    """The refusal message, or None when the command may run."""
    if data.get("tool_name") not in (None, "Bash"):
        return None
    command = ((data.get("tool_input") or {}).get("command") or "")
    if not isinstance(command, str) or not (S3_CP_RE.search(command) or ECS_EXEC_RE.search(command)
                                            or ECSX_RE.search(command) or DB_MIGRATE_RE.search(command)
                                            or PSQL_RE.search(command)):
        return None
    srcs = sources(command, data.get("cwd") or os.getcwd())
    if not srcs:
        return None
    if protected is None:
        try:
            protected = load_protected(REFERENCE.read_text(encoding="utf-8"))
        except OSError:
            return None
    problems = []
    for label, text, is_python in srcs:
        reads = text_reads(text, protected, python=is_python)
        if reads:
            problems.append(f"{label}: {', '.join(reads[:6])}")
    if not problems:
        return None
    return ("BLOCKED by the pilot PII guard (AA-969, root ADR 0019 d16): this would read personal data of a tenant table "
            "into the agent / a public log — " + "; ".join(problems) + ". Count or aggregate instead "
            "(count(...), count(DISTINCT ...), count(*) FILTER (WHERE col IS NULL), GROUP BY a non-personal column). "
            "Rules: .claude/hooks/pilot_pii_guard.py and AA-CIS-Infra db/scripts/README.md.")


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except Exception:  # noqa: BLE001 — unreadable input passes
        return 0
    msg = check(data)
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
