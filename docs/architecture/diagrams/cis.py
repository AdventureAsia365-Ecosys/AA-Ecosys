"""AA-CIS-App view: admin console, API and job worker, data and the LLM path (AA-697).

Facts: apps/AA-CIS-App CONTEXT.md ("Architecture at a glance", "Deploy & CI", "Contracts with other apps") and
docs/ecosystem-architecture.md sections 4.1, 4.3-4.6. Subnet tiers from AA-CIS-Infra modules/vpc.
"""
from diagrams.aws.compute import ECR, Fargate, Lambda
from diagrams.aws.database import ElastiCache, RDSPostgresqlInstance
from diagrams.aws.general import Users
from diagrams.aws.integration import EventbridgeScheduler
from diagrams.aws.management import Cloudwatch
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import APIGateway, ElbApplicationLoadBalancer
from diagrams.aws.security import IAMRole, Cognito
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.network import Internet
from diagrams.programming.framework import Vercel

from _common import diagram, group, legend, link, place


def draw(filename: str) -> None:
    with diagram("AA-CIS-App: content system of record (Dev)", filename):
        with group("people", "People"):
            staff = Users("AA staff")
            studio = Users("Content studio users\n(AA-Partner portal)")

        with group("vercel", "Vercel"):
            admin = Vercel("Admin console\nNext.js + BFF")

        with group("github", "GitHub: AA-CIS-App"):
            deploy = GithubActions("GitHub Actions\nDeploy Dev")

        with group("cloud", "AWS Cloud", "infrastructure account (acc2)"):
            role = IAMRole("AWS IAM\ndeploy role (OIDC)")
            with group("region", "us-west-1"):
                cognito = Cognito("Amazon Cognito\nWORKFORCE staff sign-in")
                rest = APIGateway("Amazon API Gateway\nREST api-cis (VPC link)")
                sched = EventbridgeScheduler("EventBridge Scheduler\ndaily schedule")
                with group("vpc", "Shared VPC"):
                    lb = ElbApplicationLoadBalancer("Elastic Load Balancing\nNLB → ALB, regional WAF")
                    with group("private", "Private subnets", "workloads"):
                        with group("ecs", "Amazon ECS cluster", "Fargate, one image") as ecs:
                            api = Fargate("aa-cis-dev-api\nadmin API · /v1 studio · Model Gateway")
                            worker = Fargate("aa-cis-dev-worker\nshared.job runner (A- and T-series)")
                        cache = ElastiCache("Amazon ElastiCache\nValkey cache")
                        probe = Lambda("AWS Lambda\nops probe")
                    with group("private", "Private subnets", "database"):
                        rds = RDSPostgresqlInstance("Amazon RDS for PostgreSQL\nsilver · gold · acp_* · geo · catalog")
                ecr = ECR("Amazon ECR\nimage per git SHA")
                s3 = S3("Amazon S3\nbronze: uploads · photos · docs")
                embed = Bedrock("Amazon Bedrock\nCohere Embed v4")
                cw = Cloudwatch("Amazon CloudWatch\nlogs · metrics · alarms")

        with group("cloud", "AWS Cloud", "LLM account (acc3)"):
            invoker = IAMRole("AWS IAM\nBedrock invoker role")
            with group("region", "us-west-1"):
                llm = Bedrock("Amazon Bedrock\nwriter + judge models")

        with group("outside", "Outside services") as outside:
            apis = Internet("Decision + SEO APIs\nJev · DataForSEO · OpenAI (judge)")
            channels = Internet("Photos + channels\nGoogle Drive · WordPress · Facebook")

        place({
            cognito: (3, 0),
            staff: (0, 1), admin: (1, 1), rest: (3, 1), lb: (4, 1), api: (5, 1), cache: (6, 1),
            studio: (0, 2), worker: (5, 2), rds: (7, 2),
            sched: (3, 3), probe: (6, 3), invoker: (8, 3), llm: (9, 3),
            apis: (8, 4), channels: (9, 4),
            deploy: (0, 5), role: (2, 5), ecr: (3, 5), s3: (5, 5), embed: (6, 5), cw: (7, 5),
        })
        legend((9, 5))

        link(staff, admin)
        link(admin, rest)
        link(admin, cognito, "sign-in", "control")
        link(studio, rest, "tenant JWT")
        link(rest, lb, "VPC link")
        link(lb, api)
        link(api, cache)
        link(api, rds, "enqueue jobs", "async")
        link(worker, rds)
        link(worker, s3)
        link(api, embed, "embeddings", out_of=ecs)
        link(worker, invoker, "sts:AssumeRole", "control")
        link(invoker, llm)
        link(worker, apis, into=outside)
        link(sched, probe, "daily", "async")
        link(probe, rest, "admin checks")
        link(api, cw, "logs, metrics", "async", out_of=ecs)
        link(deploy, role, "OIDC", "control")
        link(role, ecr, "push image", "control")
        link(ecr, api, "pull image", "control", into=ecs)


if __name__ == "__main__":
    draw("cis")
