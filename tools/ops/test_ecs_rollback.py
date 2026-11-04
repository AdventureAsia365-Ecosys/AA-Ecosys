"""Run: python3 -m unittest discover -s tools/ops -p 'test_*.py' (from the repo root). No AWS, no network.

tools/ops/ecs_rollback.sh runs against a fake `aws` and a fake `curl` on PATH (scripts written by the tests) that
answer from a JSON state file and record every call. Checks: dry run is the default and never writes, how the target
revision is picked (--previous skips a redeploy of the same image, --to, --to-sha), the refusals (INACTIVE revision,
expired image, config difference without --allow-config-diff, already running), and --apply (update-service, wait,
rollout and health SHA checks). Invented revision numbers and SHAs only.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "ecs_rollback.sh"
REGISTRY = "111122223333.dkr.ecr.us-west-1.amazonaws.com"

FAKE_AWS = r'''#!/usr/bin/env python3
import json, os, sys
d = os.environ["FAKE_DIR"]
args = sys.argv[1:]
with open(os.path.join(d, "calls"), "a") as fh:
    fh.write(" ".join(args) + "\n")
st = json.load(open(os.path.join(d, "state.json")))

def opt(name):
    return args[args.index(name) + 1] if name in args else None

def save():
    json.dump(st, open(os.path.join(d, "state.json"), "w"))

def service():
    return {"services": [{"taskDefinition": st["fam"] + ":" + str(st["running"]),
                          "deployments": [{"status": "PRIMARY", "rolloutState": st.get("rollout", "COMPLETED")}]}]}

def td(ref):
    rev = int(ref.rsplit(":", 1)[1])
    r = st["revs"].get(str(rev))
    if r is None:
        sys.stderr.write("An error occurred (ClientException): Unable to describe task definition.\n"); sys.exit(254)
    c = {"name": "api", "image": r["image"], "environment": [{"name": n, "value": "x"} for n in r.get("env", ["A", "B"])],
         "secrets": [{"name": "DATABASE_URL", "valueFrom": r.get("secret", "arn:secret:db")}]}
    return {"taskDefinition": {"family": st["fam"], "revision": rev, "status": r.get("status", "ACTIVE"),
                               "containerDefinitions": [c]}}

cmd = " ".join(args[:2])
if cmd == "ecs describe-services":
    print(json.dumps(service()))
elif cmd == "ecs describe-task-definition":
    print(json.dumps(td(opt("--task-definition"))))
elif cmd == "ecs list-task-definitions":
    revs = sorted((int(k) for k, v in st["revs"].items() if v.get("status", "ACTIVE") == "ACTIVE"), reverse=True)
    arns = ["arn:aws:ecs:us-west-1:111122223333:task-definition/%s:%d" % (st["fam"], r) for r in revs]
    arns.insert(1, "arn:aws:ecs:us-west-1:111122223333:task-definition/%s-other:99" % st["fam"])
    print(json.dumps(arns))
elif cmd == "ecr describe-images":
    tag = opt("--image-ids").split("=", 1)[1]
    if tag in st.get("expired", []):
        sys.stderr.write("ImageNotFoundException\n"); sys.exit(254)
    print("2026-10-30T10:00:00+00:00")
elif cmd == "ecs update-service":
    st["running"] = int(opt("--task-definition").rsplit(":", 1)[1]); save()
    print("IN_PROGRESS")
elif cmd == "ecs wait":
    sys.exit(st.get("wait_rc", 0))
else:
    sys.stderr.write("unexpected aws call: %s\n" % " ".join(args)); sys.exit(9)
'''

FAKE_CURL = r'''#!/usr/bin/env python3
import json, os, sys
d = os.environ["FAKE_DIR"]
with open(os.path.join(d, "calls"), "a") as fh:
    fh.write("curl " + " ".join(sys.argv[1:]) + "\n")
st = json.load(open(os.path.join(d, "state.json")))
image = st["revs"][str(st["running"])]["image"]
sha = image.rsplit(":", 1)[1]
sha = sha[4:] if sha.startswith("dev-") else sha
field = st.get("health_field", "git_sha")
print(json.dumps({"status": "ok", field: st.get("health_sha_override", sha)}))
'''

SHA_A = "a1" * 20           # invented 40-character SHAs
SHA_B = "b2" * 20
SHA_C = "c3" * 20


def booking_state():
    return {"fam": "aa-booking-dev-api", "running": 14, "revs": {
        "14": {"image": f"{REGISTRY}/aa-booking-dev-api:{SHA_C}"},
        "13": {"image": f"{REGISTRY}/aa-booking-dev-api:{SHA_C}"},     # redeploy of the same image
        "12": {"image": f"{REGISTRY}/aa-booking-dev-api:{SHA_B}"},
        "11": {"image": f"{REGISTRY}/aa-booking-dev-api:{SHA_A}"},
        "10": {"image": f"{REGISTRY}/aa-booking-dev-api:{SHA_A}", "status": "INACTIVE"},
    }}


@unittest.skipUnless(shutil.which("jq") and shutil.which("bash"), "needs bash + jq")
class EcsRollbackTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="ecs-rollback-test-"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        bin_dir = self.dir / "bin"
        bin_dir.mkdir()
        for name, body in (("aws", FAKE_AWS), ("curl", FAKE_CURL)):
            (bin_dir / name).write_text(body)
            (bin_dir / name).chmod(0o755)
        (self.dir / "calls").write_text("")

    def run_tool(self, state, *args):
        (self.dir / "state.json").write_text(json.dumps(state))
        (self.dir / "calls").write_text("")
        env = {**os.environ, "PATH": f"{self.dir / 'bin'}:{os.environ['PATH']}", "FAKE_DIR": str(self.dir),
               "ROLLBACK_SLEEP_S": "0", "ROLLBACK_HEALTH_TRIES": "2"}
        r = subprocess.run(["bash", str(SCRIPT), *args], env=env, capture_output=True, text=True, timeout=60)
        return r, (self.dir / "calls").read_text(), json.loads((self.dir / "state.json").read_text())

    def test_usage_errors(self):
        for args in ((), ("aa-booking-dev-api",), ("aa-unknown",  "--list"), ("aa-booking-dev-api", "--to", "x"),
                     ("aa-booking-dev-api", "--to-sha", "zz"), ("aa-booking-dev-api", "--bogus")):
            with self.subTest(args=args):
                r, calls, _ = self.run_tool(booking_state(), *args)
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertEqual(calls, "")

    def test_list_marks_the_running_revision_and_skips_other_families(self):
        r, calls, _ = self.run_tool(booking_state(), "aa-booking-dev-api", "--list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"aa-booking-dev-api:14  {SHA_C}  ACTIVE   <- running", r.stdout)
        self.assertIn(f"aa-booking-dev-api:12  {SHA_B}  ACTIVE", r.stdout)
        self.assertNotIn("-other:99", r.stdout)
        self.assertNotIn("update-service", calls)

    def test_previous_skips_a_redeploy_of_the_same_image_and_dry_run_writes_nothing(self):
        r, calls, state = self.run_tool(booking_state(), "aa-booking-dev-api", "--previous")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"target:   aa-booking-dev-api:12  image tag {SHA_B}", r.stdout)
        self.assertIn("command (WRITE):  aws ecs update-service --cluster aa-cis-dev-cluster --service "
                      "aa-booking-dev-api --task-definition aa-booking-dev-api:12 --profile aa365-admin "
                      "--region us-west-1", r.stdout)
        self.assertIn("way back (WRITE): aws ecs update-service --cluster aa-cis-dev-cluster --service "
                      "aa-booking-dev-api --task-definition aa-booking-dev-api:14", r.stdout)
        self.assertIn("curl -s https://api-booking.lumiguides.it.com/booking/health", r.stdout)
        self.assertIn("DRY RUN: nothing changed", r.stdout)
        self.assertNotIn("update-service", calls)
        self.assertEqual(state["running"], 14)
        for line in r.stdout.splitlines():                   # one-line commands only (WSL2 rule)
            self.assertFalse(line.rstrip().endswith("\\"), line)

    def test_terraform_template_revisions_are_never_a_target(self):
        state = booking_state()
        state["revs"]["13"] = {"image": f"{REGISTRY}/aa-booking-dev-api:bootstrap", "env": ["TEMPLATE_ONLY"]}
        r, _, _ = self.run_tool(state, "aa-booking-dev-api", "--previous")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("target:   aa-booking-dev-api:12", r.stdout)
        r, _, _ = self.run_tool(state, "aa-booking-dev-api", "--list")
        self.assertIn("aa-booking-dev-api:13  bootstrap  ACTIVE   (Terraform template, not a target)", r.stdout)
        r, calls, _ = self.run_tool(state, "aa-booking-dev-api", "--to", "13", "--apply", "--allow-config-diff")
        self.assertEqual(r.returncode, 1)
        self.assertIn("placeholder image tag 'bootstrap'", r.stderr)
        self.assertNotIn("update-service", calls)

    def test_every_printed_aws_command_names_profile_and_region(self):
        r, calls, _ = self.run_tool(booking_state(), "aa-booking-dev-api", "--previous")
        for line in calls.splitlines():
            if not line.startswith("curl"):
                self.assertIn("--profile aa365-admin", line)
                self.assertIn("--region us-west-1", line)

    def test_to_sha_accepts_a_short_prefix_and_cis_dev_tags(self):
        r, _, _ = self.run_tool(booking_state(), "aa-booking-dev-api", "--to-sha", SHA_A[:9])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("target:   aa-booking-dev-api:11", r.stdout)
        cis = {"fam": "aa-cis-dev-api", "running": 501, "revs": {
            "501": {"image": f"{REGISTRY}/aa-cis-dev-api:dev-{SHA_B}"},
            "500": {"image": f"{REGISTRY}/aa-cis-dev-api:dev-{SHA_A}"}}}
        r, _, _ = self.run_tool(cis, "aa-cis-dev-api", "--to-sha", SHA_A[:8])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"image tag dev-{SHA_A}", r.stdout)
        self.assertIn("CIS api and worker must run the same image", r.stdout)

    def test_refusals(self):
        cases = {
            "running already": (booking_state(), ("--to", "14"), "already the running revision"),
            "inactive": (booking_state(), ("--to", "10"), "is not ACTIVE"),
            "missing revision": (booking_state(), ("--to", "3"), "cannot read"),
            "expired image": ({**booking_state(), "expired": [SHA_B]}, ("--previous",), "not in ECR any more"),
            "no other image": ({"fam": "aa-booking-dev-api", "running": 2, "revs": {
                "2": {"image": f"{REGISTRY}/aa-booking-dev-api:{SHA_A}"},
                "1": {"image": f"{REGISTRY}/aa-booking-dev-api:{SHA_A}"}}}, ("--previous",), "no ACTIVE revision older"),
        }
        for name, (state, args, msg) in cases.items():
            with self.subTest(name):
                r, calls, _ = self.run_tool(state, "aa-booking-dev-api", *args, "--apply")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(msg, r.stderr)
                self.assertNotIn("update-service", calls)

    def test_config_difference_is_shown_and_blocks_apply_without_the_flag(self):
        state = booking_state()
        state["revs"]["12"]["env"] = ["A", "OLD_FLAG"]
        state["revs"]["12"]["secret"] = "arn:secret:old"
        r, calls, _ = self.run_tool(state, "aa-booking-dev-api", "--previous")
        self.assertEqual(r.returncode, 0)
        self.assertIn("env only in running: B", r.stdout)
        self.assertIn("env only in target:  OLD_FLAG", r.stdout)
        self.assertIn("secret only in target:  DATABASE_URL", r.stdout)
        self.assertNotIn("arn:secret", r.stdout)                 # names only, never the reference
        r, calls, _ = self.run_tool(state, "aa-booking-dev-api", "--previous", "--apply")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--allow-config-diff", r.stderr)
        self.assertNotIn("update-service", calls)
        r, calls, after = self.run_tool(state, "aa-booking-dev-api", "--previous", "--apply", "--allow-config-diff")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(after["running"], 12)

    def test_apply_updates_waits_and_verifies_the_health_sha(self):
        r, calls, state = self.run_tool(booking_state(), "aa-booking-dev-api", "--previous", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(state["running"], 12)
        self.assertIn("ecs update-service --cluster aa-cis-dev-cluster --service aa-booking-dev-api "
                      "--task-definition aa-booking-dev-api:12", calls)
        self.assertIn("ecs wait services-stable --cluster aa-cis-dev-cluster --services aa-booking-dev-api", calls)
        self.assertIn(f"health:   https://api-booking.lumiguides.it.com/booking/health git_sha={SHA_B}", r.stdout)
        self.assertIn("DONE: aa-booking-dev-api on aa-booking-dev-api:12", r.stdout)
        # ... and forward again with --to (the drill's second half).
        r, _, state = self.run_tool(state, "aa-booking-dev-api", "--to", "14", "--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(state["running"], 14)

    def test_apply_fails_when_health_reports_another_sha(self):
        state = {**booking_state(), "health_sha_override": SHA_C}
        r, _, _ = self.run_tool(state, "aa-booking-dev-api", "--previous", "--apply")
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not report git_sha=" + SHA_B, r.stderr)
        self.assertIn("go back: aws ecs update-service", r.stderr)

    def test_apply_fails_when_the_wait_gives_up(self):
        r, _, _ = self.run_tool({**booking_state(), "wait_rc": 255}, "aa-booking-dev-api", "--previous", "--apply")
        self.assertEqual(r.returncode, 1)
        self.assertIn("services-stable did not return", r.stderr)

    def test_crm_web_checks_the_agency_host_and_worker_has_no_http_check(self):
        web = {"fam": "aa-crm-dev-web", "running": 7, "revs": {
            "7": {"image": f"{REGISTRY}/aa-crm-dev-web:{SHA_B}"},
            "6": {"image": f"{REGISTRY}/aa-crm-dev-web:{SHA_A}"}}}
        r, _, _ = self.run_tool(web, "aa-crm-dev-web", "--previous", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("https://portal.lumiguides.it.com/healthz git_sha=" + SHA_A, r.stdout)
        # AA-1036: the separate Content studio service is retired; the tool refuses it before any AWS call.
        r, calls, _ = self.run_tool(web, "aa-crm-dev-portal", "--list")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(calls, "")
        worker = {"fam": "aa-cis-dev-worker", "running": 9, "revs": {
            "9": {"image": f"{REGISTRY}/aa-cis-dev-api:dev-{SHA_B}"},
            "8": {"image": f"{REGISTRY}/aa-cis-dev-api:dev-{SHA_A}"}}}
        r, calls, _ = self.run_tool(worker, "aa-cis-dev-worker", "--previous", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("curl", calls)


if __name__ == "__main__":
    unittest.main()
