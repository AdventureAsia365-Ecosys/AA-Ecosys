"""Ecosystem view: the four apps, the shared platform on the infrastructure account, the LLM account (AA-697).

Facts: docs/ecosystem-architecture.md sections 1, 2, 4.1-4.3, 4.6 and 5 (reviewed 2026-10-28, S255), cross-checked
against the live aa365 Terraform state on 2026-10-28 (docs/audits/2026-10-28-S256-aa697-drift/). Subnet tiers from
AA-CIS-Infra modules/vpc (public: ALB; private: NLB, ECS tasks, VPC Lambdas, Valkey; database: RDS).
"""
from diagrams.aws.compute import ECR, Fargate, Lambda
from diagrams.aws.database import ElastiCache, RDSPostgresqlInstance
from diagrams.aws.general import Users
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import APIGateway, CloudFront, ElbApplicationLoadBalancer, ElbNetworkLoadBalancer
from diagrams.aws.security import IAMRole, Cognito
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.network import Internet
from diagrams.programming.framework import Vercel

from _common import diagram, group, legend, link, place


def draw(filename: str) -> None:
    with diagram("AA-Ecosys: ecosystem architecture (Dev)", filename):
        with group("people", "People"):
            staff = Users("AA staff")
            agencies = Users("Partner agencies")
            travellers = Users("Travellers")

        with group("vercel", "Vercel"):
            cis_admin = Vercel("CIS admin\nNext.js")
            bk_admin = Vercel("Booking admin\nNext.js")
            tp_fe = Vercel("TripPlanner web\nNext.js")

        with group("github", "GitHub org"):
            ci = GithubActions("GitHub Actions\nCI and deploy")

        with group("cloud", "AWS Cloud", "infrastructure account (acc2)"):
            # global services sit in the AWS Cloud, outside the Region
            cdn = CloudFront("Amazon CloudFront\nagency hosts + photos")
            oidc = IAMRole("AWS IAM\nOIDC deploy roles")
            with group("region", "us-west-1"):
                rest = APIGateway("Amazon API Gateway\nREST: CIS · Booking")
                http = APIGateway("Amazon API Gateway\nHTTP: TripPlanner")

                with group("vpc", "Shared VPC"):
                    with group("private", "Private subnets", "load balancer entry"):
                        nlb = ElbNetworkLoadBalancer("Network Load Balancer\ninternal")
                    with group("public", "Public subnets"):
                        alb = ElbApplicationLoadBalancer("Application LB\nregional WAF")
                    with group("private", "Private subnets", "workloads") as workloads:
                        with group("ecs", "Amazon ECS cluster", "Fargate") as ecs_cluster:
                            cis = Fargate("AA-CIS-App\napi + job worker")
                            booking = Fargate("AA-Booking\napi + booking.job")
                            crm = Fargate("AA-Partner\napi · web · portal")
                        lambdas = Lambda("AWS Lambda\nTripPlanner browse · assembly")
                        cache = ElastiCache("Amazon ElastiCache\nValkey (CIS cache)")
                    with group("private", "Private subnets", "database"):
                        rds = RDSPostgresqlInstance("Amazon RDS for PostgreSQL\none schema per app")

                with group("generic", "Platform services"):
                    ecr = ECR("Amazon ECR\ncontainer images")
                    cognito = Cognito("Amazon Cognito\nstaff · partner · traveller · M2M")
                    s3 = S3("Amazon S3\nbronze · docs · media · CRM")
                    embed = Bedrock("Amazon Bedrock\nembeddings · CRM guardrail")

        with group("cloud", "AWS Cloud", "LLM account (acc3)"):
            invoker = IAMRole("AWS IAM\nBedrock invoker role")
            with group("region", "us-west-1"):
                llm = Bedrock("Amazon Bedrock\nchat models")

        with group("outside", "Outside services"):
            external = Internet("External APIs\nOpenAI · Jev · DataForSEO · Mapbox · Drive")

        place({
            agencies: (0, 0), cdn: (2, 0),
            staff: (0, 1), cis_admin: (1, 1), rest: (3, 1), nlb: (4, 1), alb: (5, 1), booking: (6, 1), rds: (8, 1),
            bk_admin: (1, 2), cis: (6, 2), cache: (7, 2),
            crm: (6, 3), invoker: (9, 3), llm: (10, 3),
            travellers: (0, 4), tp_fe: (1, 4), http: (3, 4), lambdas: (6, 4),
            external: (9, 6),
            ci: (0, 6), oidc: (2, 6), ecr: (3, 6), cognito: (4, 6), s3: (5, 6), embed: (6, 6),
        })
        legend((10, 6))

        # request path, left to right
        link(staff, cis_admin)
        link(staff, bk_admin)
        link(travellers, tp_fe)
        link(agencies, cdn)
        link(cis_admin, rest)
        link(bk_admin, rest)
        link(tp_fe, http)
        link(http, lambdas)
        link(rest, nlb, "VPC link")
        link(cdn, nlb, "VPC origin")
        link(nlb, alb)
        link(alb, booking, into=ecs_cluster)
        link(crm, rest, "HTTP contracts")
        link(booking, rds, out_of=workloads)   # ECS services and the Lambdas: one arrow from the workloads tier
        link(cis, cache)
        link(cis, external)
        link(lambdas, embed, "embeddings")
        # identity and control
        # CIS and the TripPlanner Lambdas: one arrow from the workloads tier
        link(cis, invoker, "sts:AssumeRole\n(CIS, TripPlanner)", "control", out_of=workloads)
        link(invoker, llm)
        link(ci, oidc, "OIDC", "control")
        link(oidc, ecr, "push image", "control")


if __name__ == "__main__":
    draw("ecosystem")
