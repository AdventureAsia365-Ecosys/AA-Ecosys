"""Unit tests for the repo facts of the generated docs blocks (AA-1132 A3): tools/docs/repo_facts.py and the A3 parts
of tools/docs/gen_sections.py.

Run: python -m unittest tools/docs/test_repo_facts.py  (needs PyYAML for gen_sections)
Fixtures are an invented workspace (folder mode) and one git repo (ref mode); no network, no app import.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_sections as g  # noqa: E402
import repo_facts as r  # noqa: E402
from test_gen_sections import INVENTORY, PLATFORM  # noqa: E402

CIS_FILES = {
    "shared/jobs/registry.py": '''
from dataclasses import dataclass
@dataclass(frozen=True)
class JobKind:
    name: str
    concurrency: int = 1
    max_attempts: int = 3
    expected_seconds: int = 600
    background: bool = False
    deploy_gate_exempt: bool = False
    deploy_blocking: bool = False
def job_kind(name, **kw):
    return lambda f: f
''',
    "services/heron/names.py": 'HERON_KIND = "heron_count"\nLIMIT = 7\n',
    "services/jobs/heron_job.py": '''
from shared.jobs.registry import job_kind
from services.heron import names
from services.heron.names import LIMIT
KIND = names.HERON_KIND
@job_kind(KIND, concurrency=2, max_attempts=LIMIT, background=True)
async def run(ctx):
    return None
''',
    "services/jobs/kite_job.py": '''
from shared.jobs.registry import job_kind
@job_kind("kite_fly", expected_seconds=60, deploy_blocking=True)
async def run(ctx):
    return None
@job_kind(make_name(), concurrency=1)
async def other(ctx):
    return None
''',
    "services/marsh/policy.py": '''
SPECS = {s.kind: s for s in (
    Spec(kind="marsh_trim_a", table="t.a"),
    Spec(kind="marsh_trim_b", table="t.b"),
)}
''',
    "services/jobs/marsh_job.py": '''
from shared.jobs.registry import job_kind
from services.marsh.policy import SPECS
def _register(spec):
    @job_kind(spec.kind, max_attempts=2)
    async def run(ctx):
        return None
    return run
for _spec in SPECS.values():
    _register(_spec)
''',
    "services/jobs/sub/ignored_job.py": 'from shared.jobs.registry import job_kind\n@job_kind("nested")\nasync def r(c): pass\n',
    ".release-please-manifest.json": '{".": "1.2.3"}',
    ".github/workflows/ci.yml": "name: CI\n",
    ".github/workflows/deploy.yaml": "name: Deploy\n",
}

TABLE_KINDS = '''
PULL = "fen_pull"
DEFAULT_EXPECTED_SECONDS = 300
DEPLOY_GATE_EXEMPT: frozenset[str] = frozenset({PULL, "fen_noop"})
DEPLOY_BLOCKING_KINDS: frozenset[str] = frozenset({"fen_purge"})
TEST_KINDS: frozenset[str] = frozenset({"fen_noop"})
EXPECTED_SECONDS: dict[str, int] = {PULL: 60, "fen_purge": 900, "fen_noop": 3660}
'''

TP_FILES = {
    "backend/jobs/glade.py": 'KIND = "tp_glade_sweep"\nMAX_ATTEMPTS = 4\n',
    "backend/jobs/brook.py": 'KIND = "tp_brook_drill"\nMAX_ATTEMPTS = 1\n',
    "backend/jobs/handler.py": '''
from backend.jobs import glade, brook
HANDLERS: dict = {glade.KIND: glade.run, brook.KIND: brook.run}
DAILY: dict = {glade.KIND: ({}, glade.MAX_ATTEMPTS, None)}
MAX_ATTEMPTS: dict[str, int] = {glade.KIND: glade.MAX_ATTEMPTS, brook.KIND: brook.MAX_ATTEMPTS}
''',
    ".release-please-manifest.json": '{".": "0.4.0"}',
}

INFRA_FILES = {
    "modules/rds/main.tf": 'resource "aws_db_instance" "main" {\n  engine = "postgres"\n  backup_retention_period = 9\n}\n',
    "accounts/aa365/rds_snapshot_expiry.tf": ('variable "rds_backup_copy_max_age_days" {\n  type    = number\n'
                                              '  default = 21\n}\n'),
    ".github/workflows/plan.yml": "name: Plan\n",
}


def write_tree(base: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


class Workspace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self._tmp.name)
        write_tree(self.ws / r.REPO_DIRS["AA-CIS-App"], CIS_FILES)
        write_tree(self.ws / r.REPO_DIRS["AA-Booking"], {r.KINDS_FILES["AA-Booking"]: TABLE_KINDS,
                                                        ".release-please-manifest.json": '{".": "2.0.0"}'})
        write_tree(self.ws / r.REPO_DIRS["AA-Partner"], {r.KINDS_FILES["AA-Partner"]: TABLE_KINDS.replace("fen_", "crm_")})
        write_tree(self.ws / r.REPO_DIRS["AA-TripPlanner-Web"], TP_FILES)
        write_tree(self.ws / r.REPO_DIRS["AA-CIS-Infra"], INFRA_FILES)

    def tearDown(self):
        self._tmp.cleanup()

    def readers(self):
        return r.readers_for(self.ws)


class CisKindsTest(Workspace):
    def test_decorators_constants_and_registry_loop(self):
        kinds, unresolved = r.cis_job_kinds(self.readers()["AA-CIS-App"])
        by = {k["kind"]: k for k in kinds}
        self.assertEqual(sorted(by), ["heron_count", "kite_fly", "marsh_trim_a", "marsh_trim_b"])
        self.assertEqual((by["heron_count"]["concurrency"], by["heron_count"]["max_attempts"],
                          by["heron_count"]["background"], by["heron_count"]["expected_seconds"]), (2, 7, True, 600))
        self.assertTrue(by["kite_fly"]["deploy_blocking"])
        self.assertEqual(by["marsh_trim_b"]["max_attempts"], 2)
        self.assertEqual(by["marsh_trim_a"]["code"], "services/jobs/marsh_job.py")
        self.assertEqual(unresolved, ["services/jobs/kite_job.py:6"])     # make_name(): kept as a note, no crash

    def test_nested_folders_are_not_registrations(self):
        kinds, _ = r.cis_job_kinds(self.readers()["AA-CIS-App"])
        self.assertNotIn("nested", {k["kind"] for k in kinds})


class OtherReposTest(Workspace):
    def test_table_kinds(self):
        kinds, unresolved = r.table_job_kinds(self.readers()["AA-Booking"], r.KINDS_FILES["AA-Booking"])
        self.assertEqual(unresolved, [])
        by = {k["kind"]: k for k in kinds}
        self.assertEqual(sorted(by), ["fen_noop", "fen_pull", "fen_purge"])
        self.assertEqual(by["fen_pull"]["expected_seconds"], 60)
        self.assertTrue(by["fen_pull"]["deploy_gate_exempt"])
        self.assertTrue(by["fen_purge"]["deploy_blocking"])
        self.assertTrue(by["fen_noop"]["test_only"])

    def test_tripplanner_handlers(self):
        kinds, unresolved = r.tripplanner_job_kinds(self.readers()["AA-TripPlanner-Web"])
        self.assertEqual(unresolved, [])
        self.assertEqual([(k["kind"], k["daily"], k["max_attempts"]) for k in kinds],
                         [("tp_brook_drill", False, 1), ("tp_glade_sweep", True, 4)])

    def test_collect_everything(self):
        facts = r.collect(self.readers())
        self.assertEqual(facts["versions"], {"AA-CIS-App": "1.2.3", "AA-Booking": "2.0.0", "AA-Partner": None,
                                             "AA-TripPlanner-Web": "0.4.0"})
        self.assertEqual(facts["backup"]["rds_pitr_days"], 9)
        self.assertEqual(facts["backup"]["copy_max_age_days"], 21)
        self.assertEqual(facts["workflows"]["AA-CIS-App"], ["ci.yml", "deploy.yaml"])
        self.assertEqual(facts["unresolved"], ["AA-CIS-App services/jobs/kite_job.py:6"])
        self.assertEqual(sorted(facts["job_kinds"]), ["AA-Booking", "AA-CIS-App", "AA-Partner", "AA-TripPlanner-Web"])

    def test_missing_repo_is_skipped(self):
        readers = self.readers()
        readers["AA-Booking"] = r.RepoReader(self.ws / "nowhere")
        facts = r.collect(readers)
        self.assertNotIn("AA-Booking", facts["job_kinds"])
        self.assertNotIn("AA-Booking", facts["versions"])


class GitRefTest(unittest.TestCase):
    def test_reads_the_ref_not_the_working_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_tree(repo, TP_FILES)
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t.invalid"]
            subprocess.run(["git", "init", "-q", tmp], check=True)
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-q", "-m", "one"], check=True)
            (repo / ".release-please-manifest.json").write_text('{".": "9.9.9"}', encoding="utf-8")  # uncommitted
            reader = r.RepoReader(repo, "HEAD")
            self.assertEqual(r.versions(reader), "0.4.0")
            self.assertEqual(r.versions(r.RepoReader(repo)), "9.9.9")
            self.assertEqual(len(reader.head()), 8)
            self.assertIn("backend/jobs/handler.py", reader.files("backend/"))


SCHEMA_REF = ("# Ref\n\n**Verified:** 2026-01-02 03:04 UTC - live dump. Latest migration per owner: CIS **101**, "
              "TripPlanner **tp-002**, Booking **bk-003**, CRM **crm-004** (9 versions registered).\n")


class GenSectionsA3Test(Workspace):
    def setUp(self):
        super().setUp()
        self.root = self.ws / "root"
        write_tree(self.root, {g.PLATFORM: PLATFORM, g.INVENTORY: INVENTORY, g.SCHEMA_REF: SCHEMA_REF,
                               "docs/ops/kinds.md": ("# Kinds\n\n<!-- gen:job-kinds-cis -->\n<!-- /gen -->\n\n"
                                                     "<!-- gen:latest-migrations -->\n<!-- /gen -->\n\n"
                                                     "<!-- gen:backup-days -->\n<!-- /gen -->\n\n"
                                                     "<!-- gen:required-checks -->\n<!-- /gen -->\n")})

    def runner(self, checks):
        def run(args):
            path = args[1]
            if "/rules/branches/" in path:
                return ""
            repo = path.split("/")[2]
            return "\n".join(checks.get(repo, [])) + "\n"
        return run

    def test_migrations_line(self):
        m = g.parse_migrations(SCHEMA_REF)
        self.assertEqual(m["as_of"], "2026-01-02")
        self.assertEqual([o["latest"] for o in m["owners"]], ["101", "tp-002", "bk-003", "crm-004"])
        self.assertIsNone(g.parse_migrations("# no verified line\n"))

    def test_required_checks_merge_classic_and_rulesets(self):
        def run(args):
            return "Lint\nUnit\n" if "/branches/" in args[1] and "/rules/" not in args[1] else "Unit\nPlan\n"
        self.assertEqual(g.gh_required_checks("AA-Booking", "main", run), ["Lint", "Plan", "Unit"])

    def test_without_repo_facts_blocks_say_not_collected(self):
        g.write(self.root)
        page = (self.root / "docs/ops/kinds.md").read_text(encoding="utf-8")
        self.assertIn("Not collected yet", page)
        self.assertIn("| CRM | `crm-NNN` | `crm-004` |", page)
        self.assertEqual(g.check(self.root), ([], []))

    def test_write_with_repos_then_plain_write_keeps_them(self):
        repos = r.collect(self.readers())
        required = g.collect_required_checks(self.runner({"AA-CIS-App": ["Lint", "Unit Tests"]}))
        g.write(self.root, repos, required)
        page = (self.root / "docs/ops/kinds.md").read_text(encoding="utf-8")
        self.assertIn("| `heron_count` | `services/jobs/heron_job.py` | 2 | 7 | 600 | **yes** | no | no |", page)
        self.assertIn("`services/jobs/kite_job.py:6`", page)                       # unresolved note
        self.assertIn("| Automated backups, point-in-time recovery | 9 |", page)
        self.assertIn("| AA-CIS-App | `main` | `Lint`, `Unit Tests` |", page)
        g.write(self.root)                                                          # no sources: keep stored facts
        self.assertEqual((self.root / "docs/ops/kinds.md").read_text(encoding="utf-8"), page)
        self.assertEqual(g.check(self.root), ([], []))
        self.assertEqual(g.check(self.root, repos, required), ([], []))

    def test_drift_of_collected_sources_only_warns(self):
        repos = r.collect(self.readers())
        g.write(self.root, repos, {})
        moved = json.loads(json.dumps(repos))
        moved["collected_from"]["AA-CIS-App"] = "ffffffff"                          # a head move alone is no drift
        self.assertEqual(g.check(self.root, moved), ([], []))
        moved["versions"]["AA-CIS-App"] = "1.3.0"
        errors, warnings = g.check(self.root, moved, {"AA-CIS-App": {"branch": "main", "checks": ["Lint"]}})
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 2)
        self.assertIn("versions", warnings[0])
        (self.root / g.SCHEMA_REF).write_text(SCHEMA_REF.replace("**101**", "**102**"), encoding="utf-8")
        errors, warnings = g.check(self.root)
        self.assertEqual(errors, [])
        self.assertIn("latest migrations", warnings[0])

    def test_main_reads_a_workspace(self):
        self.assertEqual(g.main(["--write", "--root", str(self.root), "--repos-root", str(self.ws)]), 0)
        self.assertIn("`heron_count`", (self.root / "docs/ops/kinds.md").read_text(encoding="utf-8"))
        self.assertEqual(g.main(["--check", "--root", str(self.root), "--repos-root", str(self.ws / "none")]), 1)


if __name__ == "__main__":
    unittest.main()
