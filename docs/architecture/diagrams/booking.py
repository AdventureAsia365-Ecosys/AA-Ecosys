"""AA-Booking view: staff admin, API with its booking.job worker, data and contracts (AA-697).

Facts: apps/AA-Booking CONTEXT.md ("Role in the ecosystem", "Runtime and request path", "Staff authentication",
"B2B API", "Deferred work") and docs/ecosystem-architecture.md sections 3.4, 4.1, 4.2, 4.6. Subnet tiers from
AA-CIS-Infra modules/vpc; AA-Partner's API runs on the same ECS cluster (ecosystem view).
"""
from diagrams.aws.compute import ECR, Fargate
from diagrams.aws.database import RDSPostgresqlInstance
from diagrams.aws.engagement import SES
from diagrams.aws.general import Users
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import APIGateway, ElbApplicationLoadBalancer
from diagrams.aws.security import IAMRole, Cognito, KMS
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.programming.framework import Vercel

from _common import diagram, group, legend, link, place


def draw(filename: str) -> None:
    with diagram("AA-Booking: advisor workflow and booking lifecycle (Dev)", filename):
        with group("people", "People"):
            staff = Users("AA staff\n(advisors, operations)")

        with group("vercel", "Vercel"):
            admin = Vercel("Booking admin\nNext.js + BFF")

        with group("github", "GitHub: AA-Booking"):
            deploy = GithubActions("GitHub Actions\nDeploy Dev (deploy-gate)")

        with group("cloud", "AWS Cloud", "infrastructure account (acc2)"):
            role = IAMRole("AWS IAM\ndeploy role (OIDC)")
            with group("region", "us-west-1"):
                cognito = Cognito("Amazon Cognito\nWORKFORCE staff · M2M · EXTERNAL")
                rest = APIGateway("Amazon API Gateway\nREST aa-booking-dev")
                ecr = ECR("Amazon ECR\nimage per git SHA")
                with group("vpc", "Shared VPC"):
                    lb = ElbApplicationLoadBalancer("Elastic Load Balancing\nVPC link → NLB → ALB /booking/*")
                    with group("private", "Private subnets", "workloads"):
                        with group("ecs", "Amazon ECS cluster", "Fargate"):
                            api = Fargate("aa-booking-dev-api\nFastAPI + booking.job worker")
                            partner = Fargate("AA-Partner api\nB2B client")
                    with group("private", "Private subnets", "database"):
                        with group("generic", "Amazon RDS for PostgreSQL", "shared instance"):
                            own = RDSPostgresqlInstance("schema booking\nowner (bk-NNN)")
                            reads = RDSPostgresqlInstance("read through grants\ncatalog.* (CIS) · inquiry outbox (TP)")
                media = S3("Amazon S3\nsupplier media")
                ses = SES("Amazon SES\nstaff e-mail")
                docs = S3("Amazon S3\nops documents (not provisioned)")
                kms = KMS("AWS KMS\nCMK (not provisioned)")
                cw = Cloudwatch("Amazon CloudWatch\nlogs · AA/Jobs/Booking")

        place({
            cognito: (3, 0),
            staff: (0, 1), admin: (1, 1), rest: (3, 1), lb: (4, 1), api: (5, 1), own: (6, 1),
            partner: (5, 2), reads: (6, 2),
            deploy: (0, 4), role: (2, 4), ecr: (3, 4), media: (4, 4), ses: (5, 4), docs: (6, 4), kms: (7, 4),
            cw: (7, 2),
        })
        legend((8, 4))

        link(staff, admin)
        link(admin, rest)
        link(admin, cognito, "sign-in", "control")
        link(partner, rest, "booking.b2b.v1 (M2M token)")
        link(rest, lb, "VPC link")
        link(lb, api)
        link(api, own)
        link(api, reads, "read only")
        link(api, media)
        link(api, ses)
        link(api, docs, "uploads: 503 until provisioned", "async")
        link(docs, kms, kind="async")
        link(api, cw, "logs, metrics", "async")
        link(deploy, role, "OIDC", "control")
        link(role, ecr, "push image", "control")
        link(ecr, api, "pull image", "control")


if __name__ == "__main__":
    draw("booking")
