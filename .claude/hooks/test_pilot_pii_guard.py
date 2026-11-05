"""Red-team table for pilot_pii_guard.py (AA-969 part 2, root ADR 0019 d16).

Run: python3 -m unittest .claude/hooks/test_pilot_pii_guard.py   (or python3 .claude/hooks/test_pilot_pii_guard.py)
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pilot_pii_guard as g  # noqa: E402

PROTECTED = {
    ("crm", "traveler"): {"email", "display_name", "phone"},
    ("crm", "trip"): {"notes"},
    ("booking", "customers"): {"email"},
    ("shared", "tenants"): {"billing_email"},
}

REFUSED = [
    "SELECT email FROM crm.traveler",
    "select t.display_name, t.status from crm.traveler t where t.status = 'active'",
    "SELECT * FROM crm.traveler",
    "SELECT t.* FROM crm.traveler AS t",
    "SELECT row_to_json(t) FROM crm.traveler t",
    "SELECT lower(email) AS e FROM crm.traveler",
    "SELECT min(display_name) FROM crm.traveler",
    "SELECT string_agg(phone, ',') FROM crm.traveler",
    "SELECT tr.trip_id, t.email FROM crm.trip tr JOIN crm.traveler t ON t.traveler_id = tr.traveler_id",
    "SELECT s.e FROM (SELECT email AS e FROM crm.traveler) s",
    "WITH c AS (SELECT notes FROM crm.trip) SELECT count(*) FROM c",          # the inner select list (strict)
    "SELECT DISTINCT email FROM booking.customers",
    "SELECT billing_email FROM shared.tenants",
    "UPDATE crm.traveler SET status = 'x' WHERE traveler_id = $1 RETURNING email",
    "COPY crm.traveler TO STDOUT",
    "COPY crm.traveler (traveler_id, email) TO STDOUT",
    'SELECT "email" FROM crm."traveler"',
    # review fix pass: whole rows through a bare alias, (t).col, quoted / spaced schema, unqualified tables
    "SELECT t FROM crm.traveler t",
    "SELECT t::text FROM crm.traveler t",
    "SELECT hstore(t) FROM crm.traveler t",
    "SELECT (t).email FROM crm.traveler t",
    "SELECT crm.traveler.email FROM crm.traveler",
    'SELECT email FROM "crm"."traveler"',
    "SELECT email FROM crm . traveler",
    "SET search_path = crm; SELECT email FROM traveler",
    "SELECT x.notes FROM crm.trip t JOIN trip x ON x.trip_id = t.trip_id",
    "SELECT t.email FROM traveler AS t WHERE t.status = 'active'",
    # SQL text the hook cannot read: functions running a query string, dollar-quoted bodies
    "SELECT query_to_xml($$SELECT email FROM crm.traveler$$, true, false, '')",
    "SELECT query_to_xml('SELECT email FROM crm.traveler', true, false, '')",
    "SELECT table_to_xml('crm.traveler'::regclass, true, false, '')",
    "SELECT * FROM dblink('dbname=x', 'SELECT 1') AS d(n int)",
    "DO $$ DECLARE r record; BEGIN FOR r IN SELECT email FROM crm.traveler LOOP RAISE NOTICE '%', r; END LOOP; END $$",
    "DO $do$ BEGIN EXECUTE 'SELECT 1'; END $do$",
    # re-review fix pass: one tokenizer for literals and comments (a literal '--' or '/*' hid the rest)
    "SELECT coalesce(email,'--') FROM booking.customers",
    "SELECT '/*', email, '*/' FROM booking.customers",
    "SELECT E'\\'--', email FROM crm.traveler",
    "SELECT /* a /* nested */ comment */ email FROM crm.traveler",
    'SELECT U&"\\0065mail" FROM crm.traveler',
    "SELECT U&\"!0065mail\" UESCAPE '!' FROM crm.traveler",
    # TABLE, RETURNING * in a CTE, functions in FROM, LATERAL subqueries, whole rows anywhere
    "TABLE booking.customers",
    "TABLE customers",
    "SELECT count(*) FROM crm.trip UNION ALL TABLE crm.traveler",
    "WITH u AS (UPDATE crm.traveler SET status = 'x' RETURNING *) SELECT count(*) FROM u",
    "WITH u AS (DELETE FROM crm.trip RETURNING notes) SELECT count(*) FROM u",
    "SELECT x FROM crm.traveler c, unnest(ARRAY[c.email]) x",
    "SELECT k, v FROM crm.traveler c, jsonb_each_text(to_jsonb(c)) AS j(k, v)",
    "SELECT x FROM crm.traveler c CROSS JOIN LATERAL unnest(ARRAY[c.phone]) x",
    "SELECT s.e FROM crm.traveler c, LATERAL (SELECT c.email AS e) s",
    "SELECT count(*) FROM crm.traveler c WHERE to_jsonb(c)::text::int = 0",
    "SELECT count(*) FROM crm.traveler c WHERE c::text = ''",
]
ALLOWED = [
    "SELECT count(*) AS n FROM crm.traveler",
    "SELECT count(DISTINCT email) AS n FROM crm.traveler",
    "SELECT count(*) FILTER (WHERE email IS NOT NULL) AS n FROM crm.traveler",
    "SELECT (email IS NULL) AS missing, count(*) AS n FROM crm.traveler GROUP BY 1",
    "SELECT status, count(*) FROM crm.traveler WHERE email LIKE '%@example.test' GROUP BY status",
    "SELECT traveler_id FROM crm.traveler WHERE display_name = 'x' ORDER BY email",
    "SELECT 1 FROM crm.traveler WHERE EXISTS (SELECT 1 FROM crm.trip WHERE notes IS NULL)",
    "SELECT name, slug FROM shared.tenants",
    "SELECT email FROM shared.admin_users",                                  # not a tenant table
    "SELECT 'email' AS label FROM crm.traveler",
    "SELECT now()",
    "UPDATE crm.traveler SET email = NULL WHERE traveler_id = $1 RETURNING traveler_id",
    "COPY crm.traveler (traveler_id, status) TO STDOUT",
    "-- SELECT email FROM crm.traveler\nSELECT count(*) FROM crm.traveler",
    "SELECT t.traveler_id FROM crm.traveler t JOIN crm.trip tr ON tr.traveler_id = t.traveler_id",
    "SELECT count(*) FROM traveler WHERE email IS NULL",
    "SELECT g FROM generate_series(1, 3) g",
    "SELECT n FROM crm.traveler t, LATERAL (SELECT 1 AS n) s",
    "DO $$ BEGIN RAISE NOTICE 'hello'; END $$",
    "SELECT 'a $$ b' AS x FROM crm.traveler",
    "SELECT count(*) FROM crm.traveler WHERE status <> '--' /* note */",
    "SELECT (SELECT count(*) FROM traveler) AS n",
    "SELECT n FROM crm.traveler c, LATERAL (SELECT 1 AS n) s",
    "SELECT count(*) FROM crm.traveler c, generate_series(1, 3) g",
    "SELECT t.traveler_id FROM crm.traveler t WHERE t.email::text LIKE 'x%'",
    "ALTER TABLE crm.traveler ADD COLUMN x int",
    "WITH u AS (UPDATE crm.traveler SET status = 'x' RETURNING traveler_id) SELECT count(*) FROM u",
]

SCRIPT = '''
import asyncio, asyncpg, os
SQL = """
SELECT t.traveler_id, t.email
  FROM crm.traveler t
"""
async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    print(await conn.fetch(SQL))
    print(await conn.fetchval("SELECT count(*) FROM " + "crm.traveler"))
asyncio.run(main())
'''
SAFE_SCRIPT = '''
import asyncio, asyncpg, os
async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    n = await conn.fetchval("SELECT count(*) FILTER (WHERE " + "email IS NULL) FROM crm.traveler")
    print(f"SCRIPT missing={n}")
asyncio.run(main())
'''


def bash(command, cwd):
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}


class StatementTest(unittest.TestCase):
    def test_refused(self):
        for sql in REFUSED:
            with self.subTest(sql=sql):
                self.assertTrue(g.text_reads(sql, PROTECTED, python=False), sql)

    def test_allowed(self):
        for sql in ALLOWED:
            with self.subTest(sql=sql):
                self.assertEqual(g.text_reads(sql, PROTECTED, python=False), [], sql)

    def test_python_strings_are_joined(self):
        self.assertEqual(g.text_reads(SCRIPT, PROTECTED, python=True), ["crm.traveler.email"])
        self.assertEqual(g.text_reads(SAFE_SCRIPT, PROTECTED, python=True), [])
        joined = 'q = "SELECT t.email " + "FROM crm.traveler t"\n'
        self.assertEqual(g.text_reads(joined, PROTECTED, python=True), ["crm.traveler.email"])

    def test_sql_filled_at_run_time(self):
        for src in ('q = "SELECT {} FROM crm.traveler".format("email")\n',
                    'q = "SELECT %s FROM crm.traveler" % col\n',
                    'q = f"SELECT {cols} FROM crm.traveler"\n',
                    'q = f"SELECT * FROM {table}"\n',
                    'q = f"SELECT t.* FROM {table} t"\n',
                    'q = f"SELECT to_jsonb(t) FROM {table} t"\n',
                    'C = "email"\nq = f"SELECT {C} FROM crm.traveler"\n',             # a module constant is read
                    'q = f"SELECT email FROM {schema}.traveler"\n'):
            with self.subTest(src=src):
                self.assertTrue(g.text_reads(src, PROTECTED, python=True), src)
        for src in ('q = f"SELECT count(*) FROM {table}"\n',
                    "q = f\"SELECT traveler_id FROM crm.traveler WHERE tenant_id = '{tid}' LIMIT {n}\"\n",
                    'print(f"SCRIPT n={n} {status}")\n',
                    'T = "drill.rehearsal"\nq = f"SELECT id, label FROM {T}"\n',
                    'q = f"SELECT * FROM ({inner}) r WHERE n <= $2"\n'):
            with self.subTest(src=src):
                self.assertEqual(g.text_reads(src, PROTECTED, python=True), [], src)

    def test_long_concatenations(self):
        ok = 'q = "SELECT count(*) FROM crm.traveler"' + ' + " "' * 5000 + "\n"
        self.assertEqual(g.text_reads(ok, PROTECTED, python=True), [])
        leak = 'q = "SELECT email "' + ' + " "' * 5000 + ' + "FROM crm.traveler"\n'
        self.assertEqual(g.text_reads(leak, PROTECTED, python=True), ["crm.traveler.email"])
        deep = 'q = "a"' + ' + "x"' * 20000 + "\n"
        self.assertIn("nested too deeply", g.text_reads(deep, PROTECTED, python=True)[0])


class CommandTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="l1-aa969-hook-")
        Path(self.tmp, "leak.py").write_text(SCRIPT)
        Path(self.tmp, "safe.py").write_text(SAFE_SCRIPT)

    def refused(self, command):
        return g.check(bash(command, self.tmp), PROTECTED)

    def test_s3_upload_of_an_ecs_exec_script(self):
        cp = "aws s3 cp {} s3://aa-cis-bronze-example/scripts/x.py --profile aa365-admin --region us-west-1"
        self.assertIn("leak.py: crm.traveler.email", self.refused(cp.format("leak.py")))
        self.assertIsNone(self.refused(cp.format("safe.py")))
        # fail closed: a script that cannot be read is refused (missing, written in the same call, binary)
        self.assertIn("missing.py: the script cannot be read", self.refused(cp.format("missing.py")))
        Path(self.tmp, "blob.py").write_bytes(b"\xff\xfe\x00")
        self.assertIsNotNone(self.refused(cp.format("blob.py")))
        # a missing file that is not a script and not bound for scripts/ passes
        self.assertIsNone(self.refused("aws s3 cp shot.png s3://bucket/evidence/shot.png"))

    def test_a_script_written_in_the_same_call(self):
        cp = "aws s3 cp {} s3://aa-cis-bronze-example/scripts/x.py --profile aa365-admin --region us-west-1"
        # a heredoc: what it writes is read, not the old file on disk
        self.assertIsNone(self.refused(f"cat > {self.tmp}/new.py <<'EOF'\n{SAFE_SCRIPT}\nEOF\n" + cp.format("new.py")))
        self.assertIn("crm.traveler.email", self.refused(f"cat > safe.py <<'EOF'\n{SCRIPT}\nEOF\n"
                                                         + cp.format("safe.py")))
        self.assertIsNotNone(self.refused(f"tee new.py <<-EOF >/dev/null\n{SCRIPT}\n\tEOF\n" + cp.format("new.py")))
        self.assertIsNotNone(self.refused("cat <<EOF > new.sql\nSELECT email FROM crm.traveler;\nEOF\n"
                                          "aws s3 cp new.sql s3://bucket/scripts/q.sql"))
        self.assertIsNotNone(self.refused(f"mkdir -p d && cat > d/x.py <<'EOF'\n{SCRIPT}\nEOF\n"
                                          f"aws s3 sync d s3://bucket/scripts/"))
        self.assertIsNotNone(self.refused(f"cat > new.py <<'EOF'\n{SCRIPT}\nEOF\ntools/ecs/ecsx.sh new.py"))
        # cp / mv of another file, echo / printf text
        self.assertIsNotNone(self.refused("cp leak.py safe.py && " + cp.format("safe.py")))
        self.assertIsNotNone(self.refused("mv leak.py fresh.py; " + cp.format("fresh.py")))
        Path(self.tmp, "d2").mkdir()
        self.assertIsNotNone(self.refused("cp leak.py d2/ && aws s3 sync d2 s3://bucket/scripts/"))
        self.assertIsNotNone(self.refused("""echo 'q = "SELECT email FROM crm.traveler"' > safe.py && """
                                          + cp.format("safe.py")))
        # a writer the hook cannot read, or a command that could write the script: two calls
        for cmd in ("python3 gen.py && " + cp.format("safe.py"),
                    "curl -s -o safe.py https://example.test/x.py && " + cp.format("safe.py"),
                    "sed -i 's/count/min/' safe.py && " + cp.format("safe.py"),
                    "git show HEAD:x.py > safe.py && " + cp.format("safe.py"),
                    "bash -c 'aws s3 cp leak.py s3://bucket/scripts/x.py'",
                    "cd sub && aws s3 cp ok.sql s3://bucket/scripts/ok.sql",
                    "aws s3 cp $F s3://bucket/scripts/x.py"):
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(self.refused(cmd))
        # plain commands around an upload still pass (the MFA wrapper of the steering file too)
        mfa = ("bash -c 'C=$(aws configure export-credentials --profile p --format env-no-export </dev/null) ; "
               "grep -q \"^AWS_ACCESS_KEY_ID=\" <<<\"$C\" || exit 1 ; env -u AWS_PROFILE $(tr \"\\n\" \" \" <<<\"$C\") "
               f"aws s3 cp {self.tmp}/safe.py s3://bucket/scripts/x.py'")
        for cmd in (mfa,
                    "sha256sum safe.py && " + cp.format("safe.py") + " && aws s3 presign s3://b/scripts/x.py",
                    cp.format("safe.py") + ' && URL=$(aws s3 presign s3://b/scripts/x.py --expires-in 300) && '
                    'echo "$URL" | head -c 20'):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.refused(cmd))

    def test_decoded_text_into_a_database_command(self):
        ex = ("aws ecs execute-command --cluster c --task t --container api --interactive --command "
              "\"sh -c 'echo cHJpbnQoMSk= | base64 -d | python3'\"")
        self.assertIn("decodes or evaluates", self.refused(ex))
        self.assertIsNotNone(self.refused("echo U0VMRUNU | base64 --decode | psql -h h"))
        self.assertIsNone(self.refused("echo U0VMRUNU | base64 -d"))                 # no database command

    def test_other_upload_forms(self):
        for cmd in ("cat leak.py | aws s3 cp - s3://bucket/scripts/x.py",
                    "aws s3 cp - s3://bucket/anything",
                    "aws s3api put-object --bucket b --key scripts/x.py --body leak.py",
                    "aws --profile p s3api put-object --body=leak.py --bucket b --key k",
                    "aws s3 mv leak.py s3://bucket/scripts/x.py",
                    f"aws s3 sync {self.tmp} s3://bucket/scripts/",
                    f"aws s3 cp --recursive {self.tmp} s3://bucket/scripts/ --exclude '*.png'",
                    "aws s3 cp --only-show-errors leak.py s3://bucket/x.py",
                    "aws s3api put-object --bucket b --key scripts/y.py --body missing.py"):
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(self.refused(cmd))
        for cmd in ("aws s3 cp safe.py s3://bucket/scripts/x.py --profile aa365-admin --region us-west-1",
                    "aws s3api put-object --bucket b --key k --body safe.py",
                    "aws s3 cp s3://bucket/scripts/x.py s3://bucket/backup/x.py",
                    "aws s3 presign s3://bucket/scripts/x.py --expires-in 300"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.refused(cmd))
        Path(self.tmp, "sub").mkdir()
        Path(self.tmp, "sub", "ok.sql").write_text("SELECT count(*) FROM crm.traveler")
        Path(self.tmp, "sub", "shot.png").write_bytes(b"\x89PNG\x00\x00")
        self.assertIsNone(self.refused(f"aws s3 sync {self.tmp}/sub s3://bucket/scripts/"))
        # every text file of a directory is read, not only .py / .sql
        Path(self.tmp, "sub", "q.txt").write_text("SELECT email FROM crm.traveler")
        self.assertIn("q.txt: crm.traveler.email", self.refused(f"aws s3 sync {self.tmp}/sub s3://bucket/scripts/"))
        self.assertEqual(g.uploads("aws s3 cp a.py s3://b/k && aws s3 sync d s3://b/p ; aws s3 cp s3://b/k ."),
                         [("a.py", "s3://b/k"), ("d", "s3://b/p")])

    def test_ecsx_wrapper(self):
        self.assertIsNotNone(self.refused(f"tools/ecs/ecsx.sh {self.tmp}/leak.py ACTION=read"))
        self.assertIsNone(self.refused(f"bash tools/ecs/ecsx.sh {self.tmp}/safe.py"))

    def test_inline_ecs_exec_and_psql(self):
        ex = ('aws ecs execute-command --cluster c --task t --container api --interactive --command '
              '"python3 -c \\"print(1)\\" ; psql -c \'SELECT email FROM crm.traveler\'"')
        self.assertIsNotNone(self.refused(ex))
        self.assertIsNotNone(self.refused("psql -h h -c 'SELECT t.email FROM crm.traveler t'"))
        self.assertIsNone(self.refused("psql -h h -c 'SELECT count(*) FROM crm.traveler'"))

    def test_run_script_dispatch_reads_the_infra_file(self):
        infra = Path(self.tmp, "infra/AA-CIS-Infra/db/scripts")
        infra.mkdir(parents=True)
        (infra / "aa969_leak.py").write_text(SCRIPT.replace("asyncio.run(main())", ""))
        old = g.INFRA
        g.INFRA = Path(self.tmp, "infra/AA-CIS-Infra")
        try:
            msg = self.refused("gh workflow run db-migrate.yml -f mode=run-script -f script=db/scripts/aa969_leak.py")
            self.assertIn("AA-CIS-Infra db/scripts/aa969_leak.py: crm.traveler.email", msg)
            self.assertIsNotNone(self.refused("tools/github/dbmig.sh run-script:db/scripts/aa969_leak.py"))
            api = ("gh api -X POST repos/o/AA-CIS-Infra/actions/workflows/db-migrate.yml/dispatches -f ref=main "
                   "-f 'inputs[mode]=run-script' -f 'inputs[script]=db/scripts/aa969_leak.py'")
            self.assertIn("aa969_leak.py: crm.traveler.email", self.refused(api))
            body = ("gh api repos/o/AA-CIS-Infra/actions/workflows/db-migrate.yml/dispatches --input - <<'EOF'\n"
                    '{"ref": "main", "inputs": {"mode": "run-script", "script": "db/scripts/aa969_leak.py"}}\nEOF')
            self.assertIsNotNone(self.refused(body))
            # fail closed: a script the hook cannot read, or a path hidden in a variable
            self.assertIn("cannot be read", self.refused(
                "gh workflow run db-migrate.yml -f mode=run-script -f script=db/scripts/aa969_nope.py"))
            self.assertIn("cannot read", self.refused(
                'gh workflow run db-migrate.yml -f mode=run-script -f script="$S"'))
            self.assertIsNone(self.refused("gh workflow run db-migrate.yml -f mode=apply -f owner=cis"))
        finally:
            g.INFRA = old

    def test_other_commands_pass(self):
        for cmd in ("git status", f"cat {self.tmp}/leak.py", f"python3 {self.tmp}/leak.py",
                    "aws s3 cp s3://b/k ./local.py", "grep -rn 'SELECT email FROM crm.traveler' ."):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.refused(cmd))
        self.assertIsNone(g.check({"tool_name": "Edit", "tool_input": {"file_path": "x"}}, PROTECTED))

    def test_the_hook_script_exits_2_with_a_message(self):
        hook = HERE / "pilot-pii-guard.sh"
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(HERE.parents[1]))
        # the real schema reference: crm.traveler keeps its e-mail in email_enc (pii:contact)
        Path(self.tmp, "real.py").write_text('SQL = "SELECT t.email_enc FROM crm.traveler t"\n')
        data = json.dumps(bash(f"aws s3 cp {self.tmp}/real.py s3://bucket/scripts/x.py", self.tmp))
        out = subprocess.run(["bash", str(hook)], input=data, capture_output=True, text=True, env=env)
        self.assertEqual(out.returncode, 2, out.stderr)
        self.assertIn("BLOCKED by the pilot PII guard", out.stderr)
        ok = subprocess.run(["bash", str(hook)], input=json.dumps(bash("git status", self.tmp)), capture_output=True,
                            text=True, env=env)
        self.assertEqual(ok.returncode, 0)
        bad = subprocess.run(["bash", str(hook)], input="not json", capture_output=True, text=True, env=env)
        self.assertEqual(bad.returncode, 0)

    def test_an_error_inside_the_hook_refuses_a_database_command(self):
        def run(command):
            with mock.patch.object(g, "check", side_effect=RecursionError), \
                    mock.patch("sys.stdin", io.StringIO(json.dumps(bash(command, self.tmp)))), \
                    mock.patch("sys.stderr", io.StringIO()) as err:
                return g.main(), err.getvalue()
        code, err = run("aws s3 cp safe.py s3://bucket/scripts/x.py")
        self.assertEqual(code, 2)
        self.assertIn("the guard failed (RecursionError)", err)
        self.assertEqual(run("git status")[0], 0)


class ReferenceTest(unittest.TestCase):
    """The live schema reference gives the scope the rule promises."""

    def test_scope_of_the_reference(self):
        protected = g.load_protected(g.REFERENCE.read_text(encoding="utf-8"))
        self.assertIn(("crm", "traveler"), protected)
        self.assertIn("billing_email", protected[("shared", "tenants")])
        self.assertNotIn(("shared", "admin_users"), protected)               # staff, no tenant_id
        self.assertNotIn(("booking", "staff_users"), protected)              # the AA staff directory
        self.assertIn(("booking", "customers"), protected)
        self.assertTrue(all(s in ("crm", "booking", "tripplanner", "shared") for s, _ in protected))


if __name__ == "__main__":
    unittest.main()
