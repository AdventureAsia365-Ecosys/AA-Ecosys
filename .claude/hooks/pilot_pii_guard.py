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
2. The SQL: every string literal of a .py file (adjacent and `+` concatenations joined; an f-string hole, a `{}` /
   `%s` format slot and a shell `$VAR` count as a hole filled at run time), the whole text of any other file or an
   inline command (an inline `python3 -c` is read both ways). One left-to-right tokenizer (the approach of AA-CIS-Infra
   `sql_statements()`) drops comments (`--`, nested `/* */`) and blanks string literals (`'…'`, `E'…'`, `U&'…'`,
   `$tag$…$tag$`) together, so a literal `'--'` or `'/*'` cannot hide the rest of a statement; `U&"…"` identifiers are
   decoded (one with `UESCAPE` is refused).
3. A statement is refused when the select list of any SELECT (subqueries too, and a SELECT without FROM inside a
   statement that reads a tenant table: `LATERAL (SELECT c.email)`), a RETURNING list (in a CTE too), a COPY of a table
   or a `TABLE t` command names a personal-data column of a table the statement reads (qualified `t.email`, `(t).email`
   or `crm.traveler.email`, or a bare `email` when one of the tables in its FROM / JOIN has it), `*` / `t.*` of such a
   table, or such a table's whole row (a bare alias `t`, `t::text`, `row_to_json(t)`, `to_jsonb(t)`, …; the whole-row
   functions and `t::` casts are refused anywhere in the statement, since a cast error can echo the value). Also a
   function in FROM over such a column or row (`unnest(ARRAY[c.email])`, `jsonb_each_text(to_jsonb(c))`), a select list
   filled at run time over a tenant table, and `*` / the whole row of a FROM item filled at run time (a module string
   constant in an f-string is read as its text; `{schema}.traveler` is read by its table name). Tables are found
   qualified (`crm.traveler`, `"crm"."traveler"`, `crm . traveler`) or unqualified by name (a `search_path` change
   cannot hide them). Allowed: the column inside `count(...)` (with its FILTER) and in an `IS [NOT] NULL` test, and
   anywhere in WHERE / JOIN / GROUP BY / ORDER BY.
4. Also refused: SQL text run by a function (query_to_xml and the other *_to_xml, ts_stat, dblink), a dollar-quoted
   body (DO block, function) that names a tenant table with personal data or runs EXECUTE, a command that decodes or
   evaluates text on its way to the database (`base64 -d`, `b64decode`, `xxd -r`, `exec(`, … with an ECS exec or psql),
   and an upload, ECS exec script, psql file or run-script whose content cannot be read: stdin (`-`), a path in a
   variable, a binary or missing script, a directory with too many files, a run-script path the dispatch hides in a
   variable. Uploads are `aws s3 cp|mv|sync` (directories: every text file is read) and `aws s3api put-object --body`.
   A missing file that does not look like a script (no .py / .sql / .sh name, no `scripts/` in the S3 key) passes.
5. A script written in the same Bash call that uploads or runs it: the hook reads what the call writes into it (a
   `cat` / `tee` heredoc, `echo` / `printf` text, a `cp` / `mv` of a readable file) as well as the file on disk; when
   it cannot tell what the call writes (any other writer: curl, sed -i, dd, …) or the call also runs a command that
   could write it (python3, bash, git, make, …; only plain commands such as aws, echo, cat, grep, jq, sleep may share
   the call), the call is refused: write the script in one Bash call, upload or run it in the next.
6. Failure: unreadable hook input (not JSON) passes (exit 0: this hook saves an agent from a mistake; the review and the
   Infra guard remain). An error inside the hook (a recursion limit, an unreadable directory, …) refuses (exit 2) a
   command that reaches the database, and passes any other.

Known limits (static reading; the review covers them): single columns of a table whose name is filled at run time
(`f"SELECT email FROM {t}"`: column names alone are ambiguous across tables); SQL built at run time from pieces kept in
separate variables (each piece is read alone), or read at run time from a file, S3 object or environment variable; SQL a
container-side command fetches other than the uploaded script; a database error text a script prints (a cast error in
WHERE can echo a value: ECS exec scripts must print counts and error classes only, never database error messages); a
function created earlier and only called now; Python run locally with a DSN (no trigger word); a heredoc-like `<<WORD`
inside quotes (its following lines are read as a body, not as commands); columns without a `pii:` tag.

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
TRIGGERS = (AWS_S3_RE, ECS_EXEC_RE, ECSX_RE, DB_MIGRATE_RE, PSQL_RE)
INLINE_RE = re.compile(r"(?:--command|-c)\s+(\"(?:[^\"\\]|\\.)*\"|'[^']*')")
# Text decoded or evaluated on its way into an ECS exec / psql command: the hook cannot read what actually runs.
DECODE_RE = re.compile(r"\bbase(?:64|32)\s+(?:-\w*[dD]\w*|--decode)\b|\b(?:b64|b32|b16|a85|b85|urlsafe_b64)decode\b"
                       r"|\bxxd\s+(?:-\w+\s+)*-r\b|\bopenssl\s+(?:enc|base64)\b[^\n|;&]*\s-d\b|\bbytes\.fromhex\b"
                       r"|\bcodecs\.decode\b|\b(?:zlib|gzip|bz2|lzma)\.decompress\b|\b(?:gunzip|zcat|uudecode)\b"
                       r"|\b(?:exec|eval|compile|__import__)\s*\(")
SCRIPT_SUFFIXES = (".py", ".sql", ".sh")
MAX_WALKED_FILES = 500
MAX_FILE_BYTES = 2_000_000
# aws s3 cp / mv / sync options that take no value (every other --option takes one).
S3_FLAGS = frozenset({"--recursive", "--dryrun", "--quiet", "--only-show-errors", "--no-progress", "--follow-symlinks",
                      "--no-follow-symlinks", "--delete", "--exact-timestamps", "--size-only", "--no-guess-mime-type",
                      "--force-glacier-transfer", "--ignore-glacier-warnings", "--no-paginate", "--debug",
                      "--no-verify-ssl", "--no-sign-request", "--no-cli-pager"})
# Commands that may share a Bash call with an upload / run of a script: they write no file except through a shell
# redirection (which the hook reads). Anything else (python3, bash, curl, git, make, …) could write the script.
SAFE_COMMANDS = frozenset({
    "aws", "echo", "printf", "cat", "tee", "ls", "test", "[", "[[", "]]", "true", "false", ":", "sleep", "export",
    "cd", "pwd", "grep", "egrep", "fgrep", "rg", "head", "tail", "wc", "sha256sum", "sha1sum", "md5sum", "shasum",
    "jq", "date", "stat", "file", "diff", "cmp", "basename", "dirname", "realpath", "readlink", "set", "unset", "tr",
    "cut", "sort", "uniq", "awk", "sed", "column", "nl", "mkdir", "chmod", "touch", "rm", "wait", "exit", "return",
    "local", "declare", "readonly", "read", "if", "then", "else", "elif", "fi", "for", "do", "done", "while", "until",
    "case", "esac", "in", "!", "{", "}", "ecsx.sh",
})
WRAPPERS = frozenset({"sudo", "nohup", "command", "time", "exec", "nice", "env", "timeout", "stdbuf"})
COPIERS = frozenset({"cp", "mv", "install", "ln", "rsync"})
SHELLS = frozenset({"bash", "sh", "zsh", "dash"})

IDENT = r'(?:"(?:[^"]|"")+"|[A-Za-z_][A-Za-z0-9_$]*)'
HOLE = "__hole__"
_SCHEMAS = "|".join(TENANT_SCHEMAS + ("shared",))
TABLE_RE = re.compile(rf'(?<![\w$."])("?(?:{_SCHEMAS})"?)\s*\.\s*({IDENT})(?:\s+(?:AS\s+)?({IDENT}))?', re.I)
# An unqualified table of a FROM clause (the clause text starts right after FROM): the first item, after a comma, after
# a JOIN.
_KW = r"(?:JOIN|ON|USING|LEFT|RIGHT|INNER|OUTER|FULL|CROSS|NATURAL|LATERAL|ONLY|WHERE|AS|TABLESAMPLE)\b"
UNQUALIFIED_RE = re.compile(rf'(?:^|,|\bJOIN\b)\s*(?:ONLY\s+|LATERAL\s+)?(?!{_KW})({IDENT})(?![\w$]|\s*[.(])'
                            rf'(?:\s+(?:AS\s+)?(?!{_KW})({IDENT}))?', re.I)
# A function call that is a FROM item (unnest(...), jsonb_each_text(...), ROWS FROM (f(...))).
FROM_FUNC_RE = re.compile(rf"(?:^|,|\bJOIN\b|\bLATERAL\b|\bROWS\s+FROM\s*\()\s*(?:LATERAL\s+)?"
                          rf"(?!(?:LATERAL|ROWS|ONLY|SELECT|VALUES)\b)((?:{IDENT}\s*\.\s*)?{IDENT})\s*\(", re.I)
TABLE_CMD_RE = re.compile(rf"(?:^|[();]|\b(?:UNION|EXCEPT|INTERSECT)(?:\s+(?:ALL|DISTINCT))?)\s*TABLE\s+(?:ONLY\s+)?"
                          rf"((?:{IDENT}\s*\.\s*)?{IDENT})", re.I)
WHOLE_ROW_RE = re.compile(rf"\b(?:to_jsonb?|row_to_json|hstore|jsonb?_build_array|array_to_json|record_out)\s*\(\s*"
                          rf"({IDENT})\s*(?=[,)])|(?<![\w.\"$])({IDENT})\s*::", re.I)
SQL_TEXT_FUNCS_RE = re.compile(r"\b((?:query|cursor|table|schema|database)_to_(?:xml|json)\w*|ts_stat|dblink\w*)\s*\(",
                               re.I)
_DOLLAR_TAG_RE = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$")
_UNICODE_ESC_RE = re.compile(r"\\(?:(\\)|\+([0-9A-Fa-f]{6})|([0-9A-Fa-f]{4}))")
# Run-time holes left in the SQL text: a shell ${VAR} / $VAR, a str.format slot, a %-format slot.
HOLE_RE = re.compile(r"\$\{[^{}]*\}|\$[A-Za-z_]\w*|\{[^{}]*\}|%\(\w+\)[sdr]|%[sdr]\b")
KEYWORDS = {"where", "join", "left", "right", "inner", "outer", "full", "cross", "on", "using", "group", "order",
            "limit", "offset", "having", "window", "union", "except", "intersect", "returning", "for", "set",
            "values", "select", "from", "lateral", "natural", "and", "or", "not", "as", "when", "then", "else",
            "end", "fetch", "tablesample", "with", "into", "do", "default", "is", "null", "in", "only"}
END_SELECT_LIST = re.compile(r"\bFROM\b", re.I)
END_FROM = re.compile(r"\b(WHERE|GROUP|ORDER|LIMIT|HAVING|WINDOW|UNION|EXCEPT|INTERSECT|RETURNING|FOR|OFFSET|FETCH)\b",
                      re.I)
STMT_END = re.compile(r";")
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
def _str_expr(node, consts: dict | None = None) -> str | None:
    """The text of a string expression (constants, f-strings, a `+` chain of them; holes as __hole__, except an
    f-string hole that names a module-level string constant). Iterative, so a long `+` chain cannot hit the recursion
    limit."""
    consts = consts or {}
    leaves, stack = [], [node]
    while stack:
        n = stack.pop()
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            stack += [n.right, n.left]
        else:
            leaves.append(n)
    parts, any_text = [], False
    for leaf in leaves:
        if isinstance(leaf, ast.Constant) and isinstance(leaf.value, str):
            parts.append(leaf.value)
            any_text = True
        elif isinstance(leaf, ast.JoinedStr):
            parts.append("".join(v.value if isinstance(v, ast.Constant) else consts.get(_hole_name(v), f" {HOLE} ")
                                 for v in leaf.values))
            any_text = True
        elif leaf is node:
            return None
        else:
            parts.append(f" {HOLE} ")
    return "".join(parts) if any_text else None


def _hole_name(value) -> str | None:
    if isinstance(value, ast.FormattedValue) and value.conversion == -1 and value.format_spec is None \
            and isinstance(value.value, ast.Name):
        return value.value.id
    return None


def _module_constants(tree) -> dict:
    """NAME -> text of the module-level `NAME = "..."` string constants assigned once."""
    seen: dict = {}
    for node in tree.body if isinstance(tree, ast.Module) else ():
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    value = node.value
                    text = value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None
                    seen[t.id] = text if t.id not in seen else None
    return {k: v for k, v in seen.items() if v is not None}


def python_sql(source: str) -> list | None:
    """The string expressions of a Python source (the whole text when it does not parse; None when it is nested too
    deeply to read)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [source]
    except (RecursionError, MemoryError):
        return None
    found, inside, consts = [], set(), _module_constants(tree)
    for node in ast.walk(tree):
        if id(node) in inside:
            continue
        text = _str_expr(node, consts)
        if text is not None:
            found.append(text)
            inside.update(id(n) for n in ast.walk(node))
    return found


def _ident_char(ch: str) -> bool:
    return ch.isalnum() or ch in "_$"


def _quoted_end(sql: str, j: int, q: str) -> int:
    """The index just past the closing ``q`` of a quoted run that starts at ``j`` (a doubled quote is part of it)."""
    n = len(sql)
    while j < n:
        if sql.startswith(q * 2, j):
            j += 2
        elif sql[j] == q:
            return j + 1
        else:
            j += 1
    return n


def _unicode_unescape(raw: str) -> str:
    return _UNICODE_ESC_RE.sub(lambda m: "\\" if m.group(1) else chr(int(m.group(2) or m.group(3), 16)), raw)


def tokenize(sql: str) -> tuple:
    """One left-to-right pass over SQL text: (code, dollar-quoted bodies, problems). ``code`` is ``sql`` without
    comments, with every string literal as '' (quoted, E'…', U&'…', $tag$…$tag$), every U&"…" identifier decoded to a
    plain quoted one, and every run-time hole as __hole__; ``problems`` lists what it cannot read."""
    out, bodies, problems, i, n = [], [], [], 0, len(sql)
    while i < n:
        ch = sql[i]
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
            continue
        if sql.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if sql.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif sql.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            i = j
            out.append(" ")
            continue
        if ch in "uU" and sql.startswith("&", i + 1) and i + 2 < n and sql[i + 2] in "'\"" and not (
                i > 0 and _ident_char(sql[i - 1])):
            q = sql[i + 2]
            j = _quoted_end(sql, i + 3, q)
            if re.match(r"\s*UESCAPE\b", sql[j:j + 40], re.I):
                problems.append("a U&-quoted name or literal with UESCAPE (this hook cannot decode it)")
            if q == "'":
                out.append("''")
            else:
                name = _unicode_unescape(sql[i + 3:j - 1].replace('""', '"'))
                out.append('"' + name.replace('"', '""') + '"')
            i = j
            continue
        if ch == "'":
            esc = i > 0 and sql[i - 1] in "eE" and (i < 2 or not _ident_char(sql[i - 2]))
            j = i + 1
            while j < n:
                if esc and sql[j] == "\\":
                    j += 2
                elif sql.startswith("''", j):
                    j += 2
                elif sql[j] == "'":
                    j += 1
                    break
                else:
                    j += 1
            i = min(j, n)
            out.append("''")
            continue
        if ch == '"':
            j = _quoted_end(sql, i + 1, '"')
            out.append(sql[i:j])
            i = j
            continue
        if ch == "$" and not (i > 0 and _ident_char(sql[i - 1])):
            m = _DOLLAR_TAG_RE.match(sql, i)
            if m:
                end = sql.find(m.group(0), m.end())
                bodies.append(sql[m.end():n if end < 0 else end])
                i = n if end < 0 else end + len(m.group(0))
                out.append("''")
                continue
        out.append(ch)
        i += 1
    return HOLE_RE.sub(f" {HOLE} ", "".join(out)), bodies, problems


def _split_top(text: str, sep: str = ",") -> list:
    parts, depth, cur = [], 0, []
    for ch in text:
        depth += {"(": 1, ")": -1, "[": 1, "]": -1}.get(ch, 0)
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


def _balanced(text: str, open_at: int) -> int:
    """The index just past the paren that closes the one at ``open_at``."""
    depth, j = 0, open_at
    while j < len(text):
        depth += {"(": 1, ")": -1}.get(text[j], 0)
        j += 1
        if depth == 0:
            break
    return j


def _strip_allowed(item: str) -> str:
    out, i, low = [], 0, item.lower()
    while i < len(item):
        if low.startswith("count", i) and re.match(r"count\s*\(", low[i:]) and (
                i == 0 or not (item[i - 1].isalnum() or item[i - 1] in "_.")):
            j = _balanced(item, item.index("(", i))
            m = re.match(r"\s*FILTER\s*\(", item[j:], re.I)
            if m:
                j = _balanced(item, j + m.end() - 1)
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


def _merge(*maps: dict) -> dict:
    out: dict = {}
    for m in maps:
        for k, v in m.items():
            out.setdefault(k, set()).update(v)
    return out


def _qualified_tables(text: str, protected: dict) -> dict:
    out: dict = {}
    for schema, table, alias in TABLE_RE.findall(text):
        rel = (schema.strip('"').lower(), _unquote(table))
        if rel not in protected:
            continue
        out.setdefault(rel[1], set()).add(rel)
        if alias and alias.lower() not in KEYWORDS:
            out.setdefault(_unquote(alias), set()).add(rel)
    return out


def _tables(text: str, protected: dict) -> dict:
    """alias -> {(schema, table)} for every protected table the text names, qualified (the table name is its own alias
    too) or, in a FROM clause, unqualified (by name, in any of the protected schemas)."""
    out = _qualified_tables(text, protected)
    names = _by_name(protected)
    for table, alias in UNQUALIFIED_RE.findall(TABLE_RE.sub(" ", text)):
        rels = names.get(_unquote(table))
        if not rels or table.lower() in KEYWORDS:
            continue
        out.setdefault(_unquote(table), set()).update(rels)
        if alias and alias.lower() not in KEYWORDS:
            out.setdefault(_unquote(alias), set()).update(rels)
    return out


def _drop_subqueries(text: str) -> str:
    """``text`` with every parenthesized subquery as 0 (each SELECT is read on its own pass)."""
    while True:
        m = re.search(r"\(\s*(?:SELECT|WITH|VALUES|TABLE)\b", text, re.I)
        if not m:
            return text
        text = text[:m.start()] + " 0 " + text[_balanced(text, m.start()):]


def _list_reads(items: str, rels: dict, protected: dict) -> list:
    every = sorted({r for v in rels.values() for r in v})
    found = []
    for item in _split_top(_drop_subqueries(items)):
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


def _any_reads(items: str, from_text: str) -> list:
    """For a FROM item filled at run time (any table): the select list returns `*`, `t.*` or the whole row `t` of
    it. (Single columns of such a table are not judged: column names like label or error are personal data in one
    tenant table and plain elsewhere.)"""
    aliases = {_unquote(a) for a in re.findall(rf"\b{HOLE}\s+(?:AS\s+)?({IDENT})", from_text, re.I)
               if a.lower() not in KEYWORDS}
    found = []
    for item in _split_top(_drop_subqueries(items)):
        text = _strip_allowed(item)
        if re.fullmatch(r"\s*\*\s*", text) or any(_unquote(a) in aliases for a, c in QUALIFIED_RE.findall(text)
                                                  if c == "*"):
            found.append("* of a table filled at run time")
        if any(_unquote(n) in aliases for n in BARE_RE.findall(QUALIFIED_RE.sub(" ", text))):
            found.append("the whole row of a table filled at run time")
    return found


def _hole_at_top(text: str) -> bool:
    """A FROM item filled at run time (a hole outside parentheses; `catalog.{v}` names a table of a schema that is
    not a tenant one)."""
    for m in re.finditer(rf"\b{HOLE}\b", text):
        head = text[:m.start()]
        schema = re.search(rf"({IDENT})\s*\.\s*$", head)
        if schema and _unquote(schema.group(1)) not in TENANT_SCHEMAS + ("shared",):
            continue
        if head.count("(") == head.count(")"):
            return True
    return False


def _select_parts(text: str) -> list:
    """[(select list, FROM clause text or None)] of every SELECT of one statement."""
    parts = []
    for m in re.finditer(r"\bSELECT\b", text, re.I):
        start = m.end()
        dm = re.match(r"\s*(DISTINCT\s+ON\s*\([^)]*\)|DISTINCT|ALL)\b", text[start:], re.I)
        if dm:
            start += dm.end()
        fm, end = _top_level_search(END_SELECT_LIST, text, start)
        if fm is None:
            _m, stop = _top_level_search(END_FROM, text, start)
            parts.append((text[start:stop], None))
            continue
        _wm, from_end = _top_level_search(END_FROM, text, fm.end())
        parts.append((text[start:end], text[fm.end():from_end]))
    return parts


def _from_function_reads(from_text: str, rels: dict, protected: dict) -> list:
    found = []
    for m in FROM_FUNC_RE.finditer(from_text):
        if from_text[:m.start()].count("(") != from_text[:m.start()].count(")"):
            continue                                   # inside a subquery of the FROM clause: its own pass
        name = re.sub(r"\s+", "", m.group(1))
        open_at = m.end() - 1
        args = from_text[open_at + 1:_balanced(from_text, open_at) - 1]
        found += [f"{r} (through {name}() in FROM)" for r in _list_reads(args, rels, protected)]
    return found


def statement_reads(text: str, protected: dict) -> list:
    """The personal-data columns one tokenized statement would return (``schema.table.column``); empty = allowed."""
    text = re.sub(rf"\b{HOLE}\s*\.\s*(?={IDENT})", " ", text)      # {schema}.table: the table is read by its name
    parts = _select_parts(text)
    stmt_rels = _merge(_qualified_tables(text, protected),
                       *[_tables(f, protected) for _i, f in parts if f is not None])
    found = []
    for items, from_text in parts:
        if from_text is None:                          # LATERAL (SELECT c.email), (SELECT c.email) in a list
            if stmt_rels:
                found += _list_reads(items, stmt_rels, protected)
            continue
        rels = _tables(from_text, protected)
        found += _from_function_reads(from_text, _merge(rels, stmt_rels), protected)
        if _hole_at_top(from_text):
            found += _any_reads(items, from_text)
        if rels:
            found += _list_reads(items, rels, protected)
            if re.search(rf"\b{HOLE}\b", _strip_allowed(items)):
                found.append("a select list filled at run time over a tenant table")
    for m in WHOLE_ROW_RE.finditer(text):
        alias = _unquote(m.group(1) or m.group(2))
        found += [f"{s}.{t}.* (whole row)" for s, t in sorted(stmt_rels.get(alias, ()))]
    for m in TABLE_CMD_RE.finditer(text):
        found += [f"{s}.{t}.* (TABLE)" for s, t in sorted({r for v in _tables(m.group(1), protected).values()
                                                          for r in v})]
    for m in re.finditer(r"\bRETURNING\b", text, re.I):
        head = text[:m.start()]
        target = re.findall(rf"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+((?:{IDENT}\s*\.\s*)?{IDENT}"
                            rf"(?:\s+(?:AS\s+)?{IDENT})?)", head, re.I)
        rels = _merge(_tables(target[-1], protected) if target else {}, stmt_rels)
        _x, stop = _top_level_search(STMT_END, text, m.end())      # ends at ';' or at the ')' of a CTE
        if rels:
            found += _list_reads(text[m.end():stop], rels, protected)
    for m in re.finditer(rf"\bCOPY\s+((?:{IDENT}\s*\.\s*)?{IDENT})\s*(\([^)]*\))?\s+TO\b", text, re.I):
        rels = _tables(m.group(1), protected)
        for rel in sorted({r for v in rels.values() for r in v}):
            cols = [_unquote(c.strip()) for c in (m.group(2) or "").strip("()").split(",") if c.strip()]
            hit = [c for c in cols if c in protected[rel]] if cols else ["*"]
            found += [f"{rel[0]}.{rel[1]}.{c}" for c in hit]
    return sorted(set(found))


def code_reads(code: str, bodies: list, protected: dict) -> list:
    """What a statement runs that this hook cannot read: SQL text in a function argument, and a dollar-quoted body (DO
    block, function) that names a tenant table with personal data or runs EXECUTE."""
    found = []
    for text in [code, *bodies]:
        for m in SQL_TEXT_FUNCS_RE.finditer(text):
            found.append(f"{m.group(1).lower()}() (runs SQL text this hook cannot read)")
    for body in bodies:
        if re.search(r"\bEXECUTE\b", body, re.I):
            found.append("a dollar-quoted body that runs EXECUTE")
        elif _tables(body, protected) or any(re.search(rf"\b{re.escape(t)}\b", body) for (_s, t) in protected):
            found.append("a dollar-quoted body (DO block / function) that reads a tenant table with personal data")
    return found


def text_reads(text: str, protected: dict, *, python: bool) -> list:
    pieces = python_sql(text) if python else [text]
    if pieces is None:
        return ["a Python file nested too deeply to read (split the expression)"]
    found = []
    for piece in pieces:
        code, bodies, problems = tokenize(piece)
        found += problems + code_reads(code, bodies, protected)
        for stmt in _split_top(code, ";"):
            found += statement_reads(stmt, protected)
    return sorted(set(found))


# ── which commands reach the database ────────────────────────────────────────────────────────────────────────────────
def _path(path: str, cwd: str) -> Path:
    p = Path(os.path.expanduser(path))
    return Path(os.path.normpath(p if p.is_absolute() else Path(cwd) / p))


def _read_local(path: str, cwd: str) -> str | None:
    p = _path(path, cwd)
    try:
        if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
            return None
        data = p.read_bytes()
        return None if b"\x00" in data else data.decode("utf-8")
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
    """Shell words of one line, with ; & | ( ) < > as their own tokens (plain split when the quoting is unbalanced)."""
    try:
        lex = shlex.shlex(line, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return line.split()


def _line_commands(line: str) -> list:
    out, cur = [], []
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


def _expand(words: list) -> list:
    """``words``, or the simple commands of the string a `bash -c` / `sh -lc` / `eval` runs."""
    cw = _command_words(words)
    if cw and os.path.basename(cw[0]) in SHELLS:
        k = next((k for k, w in enumerate(cw[1:], 1) if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", w)), None)
        if k is not None and k + 1 < len(cw):
            return simple_commands(cw[k + 1])
    if cw and cw[0] == "eval":
        return simple_commands(" ".join(cw[1:]))
    return [words]


def simple_commands(command: str) -> list:
    """The word lists of every simple command (split at ; & | ( ) and line ends; `\\` line continuations joined;
    the string of a `bash -c` / `eval` read as commands too)."""
    return [e for line in command.replace("\\\n", " ").splitlines() for c in _line_commands(line)
            for e in _expand(c)]


def split_heredocs(command: str) -> tuple:
    """(the command's lines without heredoc bodies, {index of a kept line: [its heredoc bodies]})."""
    lines = command.replace("\\\n", " ").split("\n")
    kept, bodies, i = [], {}, 0
    while i < len(lines):
        line = lines[i]
        idx = len(kept)
        kept.append(line)
        i += 1
        words = _words(line)
        for k, w in enumerate(words):
            if w != "<<" or k + 1 >= len(words):
                continue
            tabs, delim = words[k + 1].startswith("-"), words[k + 1].lstrip("-")
            body = []
            while i < len(lines):
                cur = lines[i]
                i += 1
                if (cur.lstrip("\t") if tabs else cur) == delim:
                    break
                body.append(cur)
            bodies.setdefault(idx, []).append("\n".join(body))
    return kept, bodies


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


# ── what the same Bash call writes ───────────────────────────────────────────────────────────────────────────────────
def _command_words(words: list) -> list:
    """``words`` without leading VAR=value assignments and wrappers (env, timeout 30, nohup, sudo, …)."""
    i = 0
    while i < len(words):
        w = words[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w) or w == "$":     # an assignment, the $ of a $(…)
            i += 1
            continue
        base = os.path.basename(w)
        if base not in WRAPPERS:
            break
        i += 1
        while i < len(words) and (words[i].startswith("-") or re.match(r"^[A-Za-z_]\w*=", words[i])
                                  or (base == "timeout" and re.fullmatch(r"[\d.]+[smhd]?", words[i]))):
            i += 2 if base == "env" and words[i] in ("-u", "--unset", "-C", "--chdir", "-S") else 1
    return words[i:]


def _split_redirects(words: list) -> tuple:
    """(the words without redirections, [paths a > / >> / &> redirection writes])."""
    plain, targets, i = [], [], 0
    while i < len(words):
        w = words[i]
        nxt = words[i + 1] if i + 1 < len(words) else ""
        if w and set(w) <= set("<>&|") and ("<" in w or ">" in w):
            if ">" in w and not w.endswith("&") and nxt and not re.fullmatch(r"\d+|-", nxt) \
                    and not nxt.startswith("/dev/"):
                targets.append(nxt)
            i += 2
            continue
        if re.fullmatch(r"\d+", w) and nxt and set(nxt) <= set("<>&|") and (">" in nxt or "<" in nxt):
            i += 1                                     # the fd number of 2>/dev/null
            continue
        plain.append(w)
        i += 1
    return plain, targets


def _writes(lines: list, bodies: dict, cwd: str) -> tuple:
    """({path: the text the call writes into it, or None when it cannot tell}, [commands that could write any file],
    whether the call changes directory)."""
    written: dict = {}
    others: list = []
    changes_dir = False

    def content_of(word: str):
        p = _path(word, cwd)
        return written[p] if p in written else _read_local(word, cwd)

    for idx, line in enumerate(lines):
        heredoc = "\n".join(bodies[idx]) if idx in bodies else None
        for words in [e for c in _line_commands(line) for e in _expand(c)]:
            plain, targets = _split_redirects(_command_words(words))
            cmd = os.path.basename(plain[0]) if plain else ":"
            args = [a for a in plain[1:] if not a.startswith("-")]
            if cmd in ("bash", "sh", "zsh") and args and os.path.basename(args[0]) == "ecsx.sh":
                cmd = "ecsx.sh"
            if cmd == "cat":
                parts = [content_of(a) for a in args] if args else [heredoc]
                text = None if any(p is None for p in parts) else "\n".join(parts)
            elif cmd == "tee":
                text = heredoc
                targets = targets + args
            elif cmd in ("echo", "printf"):
                text = None if any("\\" in a for a in plain[1:]) else " ".join(plain[1:])
            elif cmd in (":", "true"):
                text = ""
            else:
                text = None
            for t in targets:
                written[_path(t, cwd)] = text
            if cmd in COPIERS:
                if any(a in ("-t", "--target-directory") or a.startswith("--target-directory=") for a in plain) \
                        or len(args) < 2:
                    others.append(f"{cmd} (its destination is unclear)")
                    continue
                dest = _path(args[-1], cwd)
                into_dir = dest.is_dir() or args[-1].endswith("/") or len(args) > 2
                for src in args[:-1]:
                    s = _path(src, cwd)
                    tgt = dest / s.name if into_dir else dest
                    from_dir = s.is_dir() or any(s in w.parents for w in written)
                    written[tgt] = None if from_dir else content_of(src)
            elif cmd in ("sed", "perl") and any(a.startswith(("-i", "--in-place")) or a == "-pi" for a in plain):
                for a in args:
                    written[_path(a, cwd)] = None
            elif cmd == "dd":
                for a in plain[1:]:
                    if a.startswith("of="):
                        written[_path(a[3:], cwd)] = None
            elif cmd == "cd":
                changes_dir = True
            elif cmd not in SAFE_COMMANDS:
                others.append(cmd)
    return written, others, changes_dir


def _written_into(path: Path, written: dict) -> list:
    """(path, text or None) of what the call writes at ``path``, inside it (a directory) or into a directory holding
    it."""
    out = []
    for w, text in written.items():
        if w == path or path in w.parents:
            out.append((w, text))
        elif w in path.parents:
            out.append((w, None))
    return out


def _input(word: str, cwd: str, written: dict, out: list, refused: list, *, python: bool, script: bool,
           label: str = "") -> None:
    """Reads one file the command sends (an upload source, an ECS exec script, a psql file): what the call writes
    into it and what is on disk; refuses what it cannot read."""
    label = label or word
    if "$" in word or "`" in word:
        if script:
            refused.append(f"{label}: a path in a variable cannot be checked (name the file literally)")
        return
    p = _path(word, cwd)
    hits = _written_into(p, written)
    for w, text in hits:
        if text is None:
            refused.append(f"{w}: this Bash call writes it with a command whose output this hook cannot read: write "
                           f"the script in one Bash call, then upload or run it in the next")
        else:
            out.append((f"{w} (as this call writes it)", text, python or str(w).endswith(".py")))
    if p.is_dir():
        try:
            files = [f for f in sorted(p.rglob("*")) if f.is_file()]
        except OSError as e:
            refused.append(f"{word}: the directory cannot be walked ({type(e).__name__})")
            return
        if len(files) > MAX_WALKED_FILES:
            refused.append(f"{word}: {len(files)} files in one upload are too many to check")
            return
        for f in files:
            text = _read_local(str(f), cwd)
            if text is not None:
                out.append((str(f), text, f.suffix == ".py"))
            elif f.suffix in SCRIPT_SUFFIXES:
                refused.append(f"{f}: cannot be read (binary, too large or unreadable)")
        return
    text = _read_local(word, cwd)
    if text is not None:
        out.append((label, text, python))
    elif script and not any(t is not None for _w, t in hits):
        refused.append(f"{label}: the script cannot be read (missing, binary or too large): write it in an earlier "
                       f"Bash call, then upload or run it")


def _looks_like_script(*names: str) -> bool:
    return any(n.lower().endswith(SCRIPT_SUFFIXES) or "scripts/" in n.lower() for n in names)


def sources(command: str, cwd: str) -> tuple:
    """((label, text, is_python) of every SQL-bearing input the command sends to the database, [refusals of inputs that
    cannot be read])."""
    out, refused = [], []
    lines, bodies = split_heredocs(command)
    written, others, changes_dir = _writes(lines, bodies, cwd)
    files = []
    for src, dst in uploads(command):
        if src == "-":
            refused.append(f"{dst}: an upload from stdin cannot be checked (write the file first, then upload it)")
            continue
        files.append(src)
        _input(src, cwd, written, out, refused, python=src.endswith(".py") or dst.endswith(".py"),
               script=_looks_like_script(src, dst))
    m = ECSX_RE.search(command)
    if m:
        words = [w for w in _words(m.group(1)) if not w.startswith("-")]
        for k, word in enumerate(words):
            if word.endswith((".py", ".sql")) or (k == 0 and ("$" in word or "`" in word)):
                files.append(word)
                _input(word, cwd, written, out, refused, python=word.endswith(".py"), script=True,
                       label=f"{word} (ECS exec script)")
    if DB_MIGRATE_RE.search(command):
        paths = RUN_SCRIPT_RE.findall(command)
        for path in paths:
            text = _read_infra_main(path)
            if text is not None:
                out.append((f"AA-CIS-Infra {path}", text, True))
            else:
                refused.append(f"AA-CIS-Infra {path}: the run-script cannot be read on origin/main or the checkout")
        asked = RUN_SCRIPT_ASKED_RE.search(command) and re.search(r"db[-_ ]?migrate|dbmig\.sh", command, re.I)
        if not paths and asked:
            refused.append("a run-script dispatch whose db/scripts/<name>.py path this hook cannot read (name the file "
                           "literally)")
    if ECS_EXEC_RE.search(command) or PSQL_RE.search(command):
        for raw in INLINE_RE.findall(command):
            inner = raw[1:-1].replace('\\"', '"')
            # the SQL may sit one quoting level further in (a psql -c inside an ECS exec --command)
            for piece in [inner, *re.findall(r"'([^']*)'", inner), *re.findall(r'"([^"]*)"', inner)]:
                out.append(("inline command", piece, False))
                out.append(("inline command", piece, True))
        for f in re.findall(r"(?:^|\s)(?:-f\s*|--file[=\s]|<\s*)(\S+\.sql)", command):
            files.append(f)
            _input(f, cwd, written, out, refused, python=False, script=True, label=f"{f} (SQL file)")
        if DECODE_RE.search(command):
            refused.append("the command decodes or evaluates text on its way to the database (base64 -d, b64decode, "
                           "exec(), …), which this hook cannot read: upload a plain script instead")
    if PSQL_RE.search(command):
        out.append(("psql command text", command, False))           # a heredoc or here-string carries the SQL
    if files and others:
        refused.append(f"this Bash call also runs {', '.join(sorted(set(others)))}, which could write the script it "
                       f"uploads or runs: write the script in one Bash call, then upload or run it in the next")
    if files and changes_dir and any(not os.path.isabs(os.path.expanduser(f)) for f in files):
        refused.append("this Bash call changes directory before it uploads or runs a script by a relative path: use "
                       "an absolute path")
    return out, refused


def has_trigger(command) -> bool:
    return isinstance(command, str) and any(r.search(command) for r in TRIGGERS)


def check(data: dict, protected: dict | None = None) -> str | None:
    """The refusal message, or None when the command may run."""
    if data.get("tool_name") not in (None, "Bash"):
        return None
    command = ((data.get("tool_input") or {}).get("command") or "")
    if not has_trigger(command):
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
    return ("BLOCKED by the pilot PII guard (AA-969, root ADR 0019 d16): this would read personal data of a tenant "
            "table into the agent / a public log, or sends SQL this hook cannot check — "
            + "; ".join(dict.fromkeys(problems))
            + ". Count or aggregate instead (count(...), count(DISTINCT ...), count(*) FILTER (WHERE col IS NULL), "
            "GROUP BY a non-personal column). Rules: .claude/hooks/pilot_pii_guard.py and AA-CIS-Infra "
            "db/scripts/README.md.")


def main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except Exception:  # noqa: BLE001 — unreadable input passes
        return 0
    try:
        msg = check(data)
    except Exception as e:  # noqa: BLE001 — fail closed for a command that reaches the database
        command = ((data.get("tool_input") or {}).get("command") if isinstance(data, dict) else None)
        if not has_trigger(command):
            return 0
        msg = (f"BLOCKED by the pilot PII guard (AA-969, root ADR 0019 d16): the guard failed ({type(e).__name__}) on "
               f"a command that reaches the database, so it refuses it. Split the command or simplify the script.")
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
