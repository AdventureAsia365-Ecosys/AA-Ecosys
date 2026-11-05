"""PreToolUse guard (AA-969 part 2, root ADR 0019 d16): agents never read row-level personal data of tenant tables.

ADR 0019 d16 puts one real agency (the pilot) on Dev. Agents reach the shared RDS in three ways, all through Bash:
an S3-mediated ECS exec script (an upload to S3 + `aws ecs execute-command`, or `tools/ecs/ecsx.sh <file>`), an inline
`--command` / `python3 -c` / `psql -c` (or a psql heredoc / `-f` / `<` file), and a DB Migrate `run-script` dispatch
(`gh workflow run db-migrate.yml … script=db/scripts/<name>.py`, `tools/github/dbmig.sh`, or `gh api
…/actions/workflows/db-migrate.yml/dispatches`), whose log is public. This hook reads the SQL those commands carry
before they run and refuses (exit 2) a statement that would return a value of a personal-data column; counts and
aggregates pass. The orchestrator and subagents alike.

How it decides (static, so a heuristic; AA-CIS-Infra's run-script guard plans every statement on the live database and
is the precise gate for run-scripts, db/scripts/README.md "Personal data"; for an ECS exec script this hook is the only
gate, so it fails closed on what it cannot read):

1. Personal-data columns: the ` · pii:<class>` tags of `docs/architecture/db-schema-reference.md` (the live dump of the
   DM-6.1 column comments), in schemas crm, booking, tripplanner and in the shared tables that have a tenant_id column;
   not the AA staff directory booking.staff_users (staff identities, not tenant or traveller data).
2. The SQL: every string literal of a .py file (adjacent and `+` concatenations joined, f-string holes as `?`), the
   whole text of a .sql file or an inline command. Comments and quoted literals (dollar quotes too) are dropped.
3. A statement is refused when the select list of any SELECT (including subqueries), a RETURNING list, or a COPY of a
   table names a personal-data column of a table the statement reads (qualified `t.email`, `(t).email` or
   `crm.traveler.email`, or a bare `email` when one of the tables in its FROM / JOIN has it), `*` / `t.*` of such a
   table, or such a table's whole row (a bare alias `t`, `t::text`, `row_to_json(t)`, `to_jsonb(t)`, …). Tables are
   found qualified (`crm.traveler`, `"crm"."traveler"`, `crm . traveler`) or unqualified by name (a `search_path`
   change cannot hide them). Allowed: the column inside `count(...)` (with its FILTER) and in an `IS [NOT] NULL`
   test, and anywhere in WHERE / JOIN / GROUP BY / ORDER BY.
4. Also refused: SQL text run by a function (query_to_xml and the other *_to_xml, ts_stat, dblink), a dollar-quoted
   body (DO block, function) that names a tenant table with personal data or runs EXECUTE, and an upload, ECS exec
   script or run-script whose file cannot be read: stdin (`-`), a file not written yet (write it in an earlier Bash
   call), a binary or missing script, a directory with too many scripts, or a run-script path the dispatch hides in a
   variable. Uploads are `aws s3 cp|mv|sync` (directories walked for .py / .sql files) and `aws s3api put-object
   --body`. A missing file that does not look like a script (no .py / .sql / .sh name, no `scripts/` in the S3 key)
   passes.
5. Unreadable hook input (not JSON) passes (exit 0): this hook saves an agent from a mistake; the review and the Infra
   guard remain.

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
AWS_S3_RE = re.compile(rf"{_AWS}\s+(?:s3\s+(?:cp|mv|sync)|s3api\s+put-object)\b")
ECS_EXEC_RE = re.compile(rf"{_AWS}\s+ecs\s+execute-command\b")
ECSX_RE = re.compile(r"(?:^|[\s/;&|(])ecsx\.sh\s+((?:\S+\s*)+)")
RUN_SCRIPT_RE = re.compile(r"(?:script\]?\s*=|run-script:|\"script\"\s*:\s*\")\s*['\"]?(db/scripts/[A-Za-z0-9_]+\.py)")
RUN_SCRIPT_ASKED_RE = re.compile(r"run-script|\bscript\]?\s*=|\"script\"\s*:")
DB_MIGRATE_RE = re.compile(r"gh\s+workflow\s+run\b|dbmig\.sh|gh\s+api\b[^\n]*?/dispatches\b")
PSQL_RE = re.compile(r"(?:^|[\s;&|(])psql\b")
INLINE_RE = re.compile(r"(?:--command|-c)\s+(\"(?:[^\"\\]|\\.)*\"|'[^']*')")
SCRIPT_SUFFIXES = (".py", ".sql", ".sh")
MAX_WALKED_FILES = 500
# aws s3 cp / mv / sync options that take no value (every other --option takes one).
S3_FLAGS = frozenset({"--recursive", "--dryrun", "--quiet", "--only-show-errors", "--no-progress", "--follow-symlinks",
                      "--no-follow-symlinks", "--delete", "--exact-timestamps", "--size-only", "--no-guess-mime-type",
                      "--force-glacier-transfer", "--ignore-glacier-warnings", "--no-paginate", "--debug",
                      "--no-verify-ssl", "--no-sign-request", "--no-cli-pager"})

IDENT = r'(?:"(?:[^"]|"")+"|[A-Za-z_][A-Za-z0-9_$]*)'
_SCHEMAS = "|".join(TENANT_SCHEMAS + ("shared",))
TABLE_RE = re.compile(rf'(?<![\w$."])("?(?:{_SCHEMAS})"?)\s*\.\s*({IDENT})(?:\s+(?:AS\s+)?({IDENT}))?', re.I)
# An unqualified table of a FROM clause (the clause text starts right after FROM): the first item, after a comma, after
# a JOIN.
_KW = r"(?:JOIN|ON|USING|LEFT|RIGHT|INNER|OUTER|FULL|CROSS|NATURAL|LATERAL|ONLY|WHERE|AS|TABLESAMPLE)\b"
UNQUALIFIED_RE = re.compile(rf'(?:^|,|\bJOIN\b)\s*(?:ONLY\s+|LATERAL\s+)?(?!{_KW})({IDENT})(?![\w$]|\s*[.(])'
                            rf'(?:\s+(?:AS\s+)?(?!{_KW})({IDENT}))?', re.I)
SQL_TEXT_FUNCS_RE = re.compile(r"\b((?:query|cursor|table|schema|database)_to_(?:xml|json)\w*|ts_stat|dblink\w*)\s*\(",
                               re.I)
DOLLAR_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)?\$(.*?)\$\1\$", re.S)
KEYWORDS = {"where", "join", "left", "right", "inner", "outer", "full", "cross", "on", "using", "group", "order",
            "limit", "offset", "having", "window", "union", "except", "intersect", "returning", "for", "set",
            "values", "select", "from", "lateral", "natural", "and", "or", "not", "as", "when", "then", "else",
            "end", "fetch", "tablesample", "with", "into", "do", "default", "is", "null", "in", "only"}
END_SELECT_LIST = re.compile(r"\bFROM\b", re.I)
END_FROM = re.compile(r"\b(WHERE|GROUP|ORDER|LIMIT|HAVING|WINDOW|UNION|EXCEPT|INTERSECT|RETURNING|FOR|OFFSET|FETCH)\b",
                      re.I)
NULL_TEST_RE = re.compile(rf"(?:{IDENT}\s*\.\s*){{0,2}}{IDENT}\s+IS\s+(?:NOT\s+)?NULL", re.I)
# alias.col, schema.table.col, (alias).col (the optional first part is a schema).
QUALIFIED_RE = re.compile(rf"(?:{IDENT}\s*\.\s*)?(?:\(\s*)?({IDENT})\s*\)?\s*\.\s*({IDENT}|\*)")
BARE_RE = re.compile(rf"(?<![\w.\"$])({IDENT})(?![\w\"$]|\s*\(|\s*\.)")


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
    sql = DOLLAR_RE.sub(" '' ", sql)
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


def _by_name(protected: dict) -> dict:
    out: dict = {}
    for rel in protected:
        out.setdefault(rel[1], set()).add(rel)
    return out


def _tables(text: str, protected: dict) -> dict:
    """alias -> {(schema, table)} for every protected table the text names, qualified (the table name is its own alias
    too) or, in a FROM clause, unqualified (by name, in any of the protected schemas)."""
    out: dict = {}
    for schema, table, alias in TABLE_RE.findall(text):
        rel = (schema.strip('"').lower(), _unquote(table))
        if rel not in protected:
            continue
        out.setdefault(rel[1], set()).add(rel)
        if alias and alias.lower() not in KEYWORDS:
            out.setdefault(_unquote(alias), set()).add(rel)
    names = _by_name(protected)
    for table, alias in UNQUALIFIED_RE.findall(TABLE_RE.sub(" ", text)):
        rels = names.get(_unquote(table))
        if not rels or table.lower() in KEYWORDS:
            continue
        out.setdefault(_unquote(table), set()).update(rels)
        if alias and alias.lower() not in KEYWORDS:
            out.setdefault(_unquote(alias), set()).update(rels)
    return out


def _list_reads(items: str, rels: dict, protected: dict) -> list:
    every = sorted({r for v in rels.values() for r in v})
    found = []
    for item in _split_top(items):
        text = _strip_allowed(item)
        if re.fullmatch(r"\s*\*\s*", text):
            found += [f"{s}.{t}.*" for s, t in every]
            continue
        for alias, col in QUALIFIED_RE.findall(text):
            for rel in sorted(rels.get(_unquote(alias), ())):
                if col == "*" or _unquote(col) in protected[rel]:
                    found.append(f"{rel[0]}.{rel[1]}.{_unquote(col) if col != '*' else '*'}")
        for name in BARE_RE.findall(QUALIFIED_RE.sub(" ", text)):
            col = _unquote(name)
            for rel in every:
                if col in protected[rel]:
                    found.append(f"{rel[0]}.{rel[1]}.{col}")
            for rel in sorted(rels.get(col, ())):            # a bare alias is the whole row (t, t::text, f(t))
                found.append(f"{rel[0]}.{rel[1]}.* (whole row)")
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
        target = re.findall(rf"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+((?:{IDENT}\s*\.\s*)?{IDENT}"
                            rf"(?:\s+(?:AS\s+)?{IDENT})?)", head, re.I)
        if target:
            rels = _tables(target[-1], protected)
            stop = re.search(r";", text[m.end():])
            items = text[m.end():m.end() + stop.start()] if stop else text[m.end():]
            if rels:
                found += _list_reads(items, rels, protected)
    for m in re.finditer(rf"\bCOPY\s+((?:{IDENT}\s*\.\s*)?{IDENT})\s*(\([^)]*\))?\s+TO\b", text, re.I):
        rels = _tables(m.group(1), protected)
        for rel in sorted({r for v in rels.values() for r in v}):
            cols = [_unquote(c.strip()) for c in (m.group(2) or "").strip("()").split(",") if c.strip()]
            hit = [c for c in cols if c in protected[rel]] if cols else ["*"]
            found += [f"{rel[0]}.{rel[1]}.{c}" for c in hit]
    return sorted(set(found))


def code_reads(sql: str, protected: dict) -> list:
    """What a statement runs that this hook cannot read: SQL text in a function argument, and a dollar-quoted body (DO
    block, function) that names a tenant table with personal data or runs EXECUTE."""
    found = []
    for m in SQL_TEXT_FUNCS_RE.finditer(re.sub(r"--[^\n]*", " ", sql)):
        found.append(f"{m.group(1).lower()}() (runs SQL text this hook cannot read)")
    for _tag, body in DOLLAR_RE.findall(sql):
        if re.search(r"\bEXECUTE\b", body, re.I):
            found.append("a dollar-quoted body that runs EXECUTE")
        elif _tables(body, protected) or any(
                re.search(rf"\b{re.escape(t)}\b", body) for (_s, t) in protected):
            found.append("a dollar-quoted body (DO block / function) that reads a tenant table with personal data")
    return found


def text_reads(text: str, protected: dict, *, python: bool) -> list:
    pieces = python_sql(text) if python else [text]
    found = []
    for piece in pieces:
        found += code_reads(piece, protected)
        stripped = DOLLAR_RE.sub(" '' ", piece)
        for stmt in _split_top(stripped, ";"):
            found += statement_reads(stmt, protected)
    return sorted(set(found))


# ── which commands reach the database ────────────────────────────────────────────────────────────────────────────────
def _path(path: str, cwd: str) -> Path:
    p = Path(os.path.expanduser(path))
    return p if p.is_absolute() else Path(cwd) / p


def _read_local(path: str, cwd: str) -> str | None:
    p = _path(path, cwd)
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


def _words(line: str) -> list:
    """Shell words of one line, with ; & | ( ) as their own tokens (plain split when the quoting is unbalanced)."""
    try:
        lex = shlex.shlex(line, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return line.split()


def simple_commands(command: str) -> list:
    """The word lists of every simple command (split at ; & | ( ) and line ends; `\\` line continuations joined)."""
    out = []
    for line in command.replace("\\\n", " ").splitlines():
        cur = []
        for w in _words(line):
            if w and all(ch in ";&|()" for ch in w):
                if cur:
                    out.append(cur)
                cur = []
            else:
                cur.append(w)
        if cur:
            out.append(cur)
    return out


def uploads(command: str) -> list:
    """(source, destination) of every local-to-S3 upload: aws s3 cp / mv / sync and aws s3api put-object --body."""
    out = []
    for words in simple_commands(command):
        idx = next((i for i, w in enumerate(words) if os.path.basename(w) == "aws"), None)
        if idx is None:
            continue
        rest, i = words[idx + 1:], 0
        while i < len(rest) and rest[i].startswith("--"):          # global options
            i += 1 if "=" in rest[i] or rest[i] in S3_FLAGS else 2
        if i + 1 >= len(rest):
            continue
        service, op, args = rest[i], rest[i + 1], rest[i + 2:]
        if service == "s3" and op in ("cp", "mv", "sync"):
            pos, j = [], 0
            while j < len(args):
                a = args[j]
                if a.startswith("--"):
                    j += 1 if "=" in a or a in S3_FLAGS else 2
                    continue
                pos.append(a)
                j += 1
            if len(pos) >= 2 and pos[1].startswith("s3://") and not pos[0].startswith("s3://"):
                out.append((pos[0], pos[1]))
        elif service == "s3api" and op == "put-object":
            opts = {}
            for j, a in enumerate(args):
                if a.startswith("--"):
                    k, eq, v = a.partition("=")
                    opts[k] = v if eq else (args[j + 1] if j + 1 < len(args) else "")
            if "--body" in opts:
                out.append((opts["--body"], f"s3://{opts.get('--bucket', '')}/{opts.get('--key', '')}"))
    return out


def _looks_like_script(*names: str) -> bool:
    return any(n.lower().endswith(SCRIPT_SUFFIXES) or "scripts/" in n.lower() for n in names)


def _upload_sources(src: str, dst: str, cwd: str, out: list, refused: list) -> None:
    if src == "-":
        refused.append(f"{dst}: an upload from stdin cannot be checked (write the file first, then upload it)")
        return
    p = _path(src, cwd)
    if p.is_dir():
        files = [f for f in sorted(p.rglob("*")) if f.is_file() and f.suffix in (".py", ".sql")]
        if len(files) > MAX_WALKED_FILES:
            refused.append(f"{src}: {len(files)} scripts in one upload are too many to check")
            return
        for f in files:
            text = _read_local(str(f), cwd)
            if text is None:
                refused.append(f"{f}: cannot be read")
            else:
                out.append((str(f), text, f.suffix == ".py"))
        return
    text = _read_local(src, cwd)
    if text is not None:
        out.append((src, text, src.endswith(".py") or dst.endswith(".py")))
    elif _looks_like_script(src, dst):
        refused.append(f"{src}: the script cannot be read (missing, not written yet, or binary): write it in an earlier "
                       f"Bash call, then upload it")


def sources(command: str, cwd: str) -> tuple:
    """((label, text, is_python) of every SQL-bearing input the command sends to the database, [refusals of inputs that
    cannot be read])."""
    out, refused = [], []
    for src, dst in uploads(command):
        _upload_sources(src, dst, cwd, out, refused)
    m = ECSX_RE.search(command)
    if m:
        for word in _words(m.group(1)):
            if word.endswith((".py", ".sql")):
                text = _read_local(word, cwd)
                if text is not None:
                    out.append((word, text, word.endswith(".py")))
                else:
                    refused.append(f"{word}: the ECS exec script cannot be read")
    if DB_MIGRATE_RE.search(command):
        paths = RUN_SCRIPT_RE.findall(command)
        for path in paths:
            text = _read_infra_main(path)
            if text is not None:
                out.append((f"AA-CIS-Infra {path}", text, True))
            else:
                refused.append(f"AA-CIS-Infra {path}: the run-script cannot be read on origin/main or the checkout")
        if not paths and RUN_SCRIPT_ASKED_RE.search(command) and re.search(r"db[-_ ]?migrate|dbmig\.sh", command,
                                                                          re.I):
            refused.append("a run-script dispatch whose db/scripts/<name>.py path this hook cannot read (name the file "
                           "literally)")
    if ECS_EXEC_RE.search(command) or PSQL_RE.search(command):
        for raw in INLINE_RE.findall(command):
            inner = raw[1:-1].replace('\\"', '"')
            # the SQL may sit one quoting level further in (a psql -c inside an ECS exec --command)
            for piece in [inner, *re.findall(r"'([^']*)'", inner), *re.findall(r'"([^"]*)"', inner)]:
                out.append(("inline command", piece, False))
        for f in re.findall(r"(?:^|\s)(?:-f\s*|--file[=\s]|<\s*)(\S+\.sql)", command):
            text = _read_local(f, cwd)
            if text is not None:
                out.append((f, text, False))
            else:
                refused.append(f"{f}: the SQL file cannot be read")
    if PSQL_RE.search(command):
        out.append(("psql command text", command, False))           # a heredoc or here-string carries the SQL
    return out, refused


def check(data: dict, protected: dict | None = None) -> str | None:
    """The refusal message, or None when the command may run."""
    if data.get("tool_name") not in (None, "Bash"):
        return None
    command = ((data.get("tool_input") or {}).get("command") or "")
    if not isinstance(command, str) or not (AWS_S3_RE.search(command) or ECS_EXEC_RE.search(command)
                                            or ECSX_RE.search(command) or DB_MIGRATE_RE.search(command)
                                            or PSQL_RE.search(command)):
        return None
    srcs, problems = sources(command, data.get("cwd") or os.getcwd())
    if not srcs and not problems:
        return None
    if srcs and protected is None:
        try:
            protected = load_protected(REFERENCE.read_text(encoding="utf-8"))
        except OSError:
            protected = None
            problems.append("docs/architecture/db-schema-reference.md cannot be read (no personal-data column list)")
    for label, text, is_python in srcs if protected is not None else ():
        reads = text_reads(text, protected, python=is_python)
        if reads:
            problems.append(f"{label}: {', '.join(reads[:6])}")
    if not problems:
        return None
    return ("BLOCKED by the pilot PII guard (AA-969, root ADR 0019 d16): this would read personal data of a tenant table "
            "into the agent / a public log, or sends SQL this hook cannot check — " + "; ".join(problems) + ". Count "
            "or aggregate instead (count(...), count(DISTINCT ...), count(*) FILTER (WHERE col IS NULL), GROUP BY a "
            "non-personal column). Rules: .claude/hooks/pilot_pii_guard.py and AA-CIS-Infra db/scripts/README.md.")


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
