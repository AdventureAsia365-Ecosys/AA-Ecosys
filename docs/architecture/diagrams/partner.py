"""AA-Partner view: agency CRM and the tenant Content studio behind CloudFront, data and contracts (AA-697).

Facts: apps/AA-Partner CONTEXT.md ("Role in the ecosystem", "Route classes", "Job runner", "Web", "Tenant portal",
"LLM gateway", "F3 PII scrubber"), infra/AA-CIS-Infra CONTEXT.md (crm_edge.tf, crm_agency_edge.tf, crm_portal.tf)
and docs/ecosystem-architecture.md sections 1, 4.1, 4.6; S3 and KMS from the live aa365 state (2026-10-28).
Subnet tiers from AA-CIS-Infra modules/vpc.
"""
from diagrams.aws.compute import ECR, Fargate
from diagrams.aws.database import RDSPostgresqlInstance
from diagrams.aws.general import Users
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import APIGateway, CloudFront, ElbApplicationLoadBalancer, ElbNetworkLoadBalancer
from diagrams.aws.security import IAMRole, Cognito, KMS
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.network import Internet

from _common import diagram, group, legend, link, place


def draw(filename: str) -> None:
    with diagram("AA-Partner: agency CRM and Content studio (Dev)", filename):
        with group("people", "People"):
            agents = Users("Agency staff\n(CRM, Content studio)")
            clients = Users("Agency clients\n(proposals, forms)")

        with group("github", "GitHub: AA-Partner"):
            deploy = GithubActions("GitHub Actions\ndeploy api · web · portal")

        with group("cloud", "AWS Cloud", "infrastructure account (acc2)"):
            with group("generic", "Amazon CloudFront", "adds the origin secret header") as cdn:
                cf_agency = CloudFront("agency hosts\nCRM + Content studio")
                cf_client = CloudFront("client host\nproposals, forms")
            role = IAMRole("AWS IAM\ndeploy role (OIDC)")
            with group("region", "us-west-1"):
                ecr = ECR("Amazon ECR\nimage per git SHA")
                cognito = Cognito("Amazon Cognito\nPARTNER pool (MFA) · M2M")
                cis = APIGateway("Amazon API Gateway\nCIS API: catalog · membership\nContent studio /v1")
                booking = APIGateway("Amazon API Gateway\nBooking API: booking.b2b.v1")
                guard = Bedrock("Amazon Bedrock Guardrails\nPII scrubber")
                files = S3("Amazon S3\nCRM documents · ingest · audit\n(SSE-KMS)")
                kms = KMS("AWS KMS\n3 CMKs: data · ingest · seal")
                with group("vpc", "Shared VPC"):
                    with group("private", "Private subnets", "load balancer entry"):
                        nlb = ElbNetworkLoadBalancer("Network Load Balancer\ninternal (VPC origin)")
                    with group("public", "Public subnets"):
                        alb = ElbApplicationLoadBalancer("Application LB\nhost + secret rules")
                    with group("private", "Private subnets", "workloads"):
                        with group("ecs", "Amazon ECS cluster", "Fargate ARM64") as ecs:
                            web = Fargate("aa-crm-dev-web\nCRM (Next.js)")
                            portal = Fargate("aa-crm-dev-portal\nContent studio (Next.js)")
                            api = Fargate("aa-crm-dev-api\nFastAPI + crm.job worker")
                    with group("private", "Private subnets", "database"):
                        rds = RDSPostgresqlInstance("Amazon RDS for PostgreSQL\nschema crm (crm-NNN), RLS per agency")

        with group("outside", "Agency's own accounts", "bring your own"):
            byo = Internet("Twilio / WhatsApp · Stripe\nmailbox · e-sign")

        place({
            agents: (0, 1), cf_agency: (1, 1), nlb: (2, 1), alb: (3, 1), web: (4, 1), booking: (8, 1),
            clients: (0, 2), cf_client: (1, 2), api: (5, 2), cis: (8, 2),
            portal: (4, 3), cognito: (7, 3),
            rds: (6, 4), byo: (9, 4),
            deploy: (0, 5), role: (1, 5), ecr: (2, 5), files: (5, 5), kms: (6, 5), guard: (7, 5),
        })
        legend((9, 5))

        link(agents, cf_agency)
        link(clients, cf_client)
        # no "VPC origin" label: the NLB text says it, and two borders leave no room for a label there
        link(cf_agency, nlb, out_of=cdn)
        link(nlb, alb)
        link(alb, web, into=ecs)
        link(web, api, "BFF")
        link(api, rds)
        link(api, guard, "PII scrub")
        link(api, files)
        link(files, kms, "SSE-KMS", "control")
        link(web, cognito, "sign-in", "control")
        link(portal, cognito, "sign-in", "control")
        link(portal, cis, "tenant JWT")
        link(api, cis, "M2M token")
        link(api, booking, "M2M token")
        link(api, byo)
        link(deploy, role, "OIDC", "control")
        link(role, ecr, "push image", "control")
        link(ecr, web, "pull image", "control", into=ecs)


if __name__ == "__main__":
    draw("partner")
