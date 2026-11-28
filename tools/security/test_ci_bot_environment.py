"""AA-1183 part 2: the aa-ecosys-ci-bot private key is read only by jobs of this repo that run in the environment
`ci-bot` (deployment branches: master only), and such a job never assumes an AWS role (an environment changes the
OIDC subject the AWS roles trust). The same guard runs in AA-CIS-Infra (tools/security/tests/
test_aa1183_ci_bot_environment.py). Run: python3 -m unittest discover -s tools/security -p 'test_*.py'.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
KEY = "secrets.AA_CI_BOT_PRIVATE_KEY"


def _jobs():
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for job_id, job in (doc.get("jobs") or {}).items():
            if isinstance(job, dict):
                yield path.name, job_id, job


def _env(job: dict):
    env = job.get("environment")
    return env.get("name") if isinstance(env, dict) else env


class CiBotEnvironmentTest(unittest.TestCase):
    def test_key_only_in_ci_bot_jobs(self):
        bad = [f"{n}:{j} ({_env(job)!r})" for n, j, job in _jobs()
               if KEY in yaml.safe_dump(job) and _env(job) != "ci-bot"]
        self.assertEqual(bad, [], "jobs that read the CI bot key outside environment ci-bot")

    def test_ci_bot_jobs_assume_no_aws_role(self):
        bad = [f"{n}:{j}" for n, j, job in _jobs() if _env(job) == "ci-bot"
               and ("configure-aws-credentials" in yaml.safe_dump(job)
                    or (job.get("permissions") or {}).get("id-token"))]
        self.assertEqual(bad, [])

    def test_some_job_uses_it(self):
        self.assertTrue(any(_env(job) == "ci-bot" for _, _, job in _jobs()))


if __name__ == "__main__":
    unittest.main()
