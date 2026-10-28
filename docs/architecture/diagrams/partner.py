"""AA-Partner view: agency CRM and the tenant Content studio behind CloudFront, data and contracts (AA-697).

Facts: apps/AA-Partner CONTEXT.md ("Role in the ecosystem", "Route classes", "Job runner", "Web", "Tenant portal",
"LLM gateway", "F3 PII scrubber"), infra/AA-CIS-Infra CONTEXT.md (crm_edge.tf, crm_agency_edge.tf, crm_portal.tf)
and docs/ecosystem-architecture.md sections 1, 4.1, 4.6; S3 and KMS from the live aa365 state (2026-10-28).
"""
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECR, Fargate
from diagrams.aws.database import RDSPostgresqlInstance
from diagrams.aws.general import Users
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import APIGateway, CloudFront, ElbApplicationLoadBalancer, ElbNetworkLoadBalancer
from diagrams.aws.security import IAMRole, Cognito, KMS
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.network import Internet

from _common import ACCOUNT, EDGE_ATTR, EXTERNAL, GRAPH_ATTR, GROUP, NODE_ATTR, VPC


def draw(filename: str) -> None:
    with Diagram("AA-Partner: agency CRM and Content studio (Dev)", filename=filename, outformat="svg",
                 show=False, direction="LR", graph_attr=GRAPH_ATTR, node_attr=NODE_ATTR, edge_attr=EDGE_ATTR):
        with Cluster("People", graph_attr=GROUP):
            agents = Users("Agency staff\n(CRM, Content studio)")
            clients = Users("Agency clients\n(proposals, forms)")

        with Cluster("GitHub: AA-Partner", graph_attr=GROUP):
            deploy = GithubActions("deploy workflows\napi · web · portal")

        with Cluster("AWS infrastructure account (acc2) · us-west-1", graph_attr=ACCOUNT):
            with Cluster("CloudFront (adds the origin secret header)", graph_attr=GROUP):
                cf_agency = CloudFront("agency hosts\nCRM + Content studio")
                cf_client = CloudFront("client host")
            cognito = Cognito("Cognito\nPARTNER pool (MFA)\nM2M client")
            role = IAMRole("deploy role")
            ecr = ECR("ECR\nimage per git SHA")
            guard = Bedrock("Bedrock Guardrails\n(PII scrubber)")
            files = S3("S3 crm buckets\ndocuments · ingest · audit\n(SSE-KMS)")
            kms = KMS("KMS, 3 CMKs\ndata · ingest · seal")
            with Cluster("Shared VPC", graph_attr=VPC):
                nlb = ElbNetworkLoadBalancer("Internal NLB\n(VPC origin)")
                alb = ElbApplicationLoadBalancer("ALB\nhost + secret rules")
                with Cluster("ECS Fargate ARM64", graph_attr=GROUP):
                    web = Fargate("aa-crm-dev-web\nCRM (Next.js)")
                    portal = Fargate("aa-crm-dev-portal\nContent studio (Next.js)")
                    api = Fargate("aa-crm-dev-api\nFastAPI + crm.job worker")
                rds = RDSPostgresqlInstance("RDS Postgres\nschema crm (crm-NNN)\nRLS per agency")
            cis = APIGateway("CIS API\ncatalog · membership\nContent studio /v1")
            booking = APIGateway("Booking API\nbooking.b2b.v1")

        with Cluster("Agency's own accounts (bring your own)", graph_attr=EXTERNAL):
            byo = Internet("Twilio / WhatsApp · Stripe\nmailbox · e-sign")

        agents >> cf_agency
        clients >> cf_client
        [cf_agency, cf_client] >> Edge(label="VPC origin") >> nlb >> alb
        alb >> [web, portal, api]
        web >> Edge(label="BFF") >> api
        api >> rds
        api >> Edge(style="dotted") >> guard
        api >> files
        files >> Edge(style="dotted") >> kms
        [web, portal] >> Edge(label="sign-in", style="dotted") >> cognito
        portal >> Edge(label="tenant JWT", style="dashed") >> cis
        api >> Edge(label="M2M token", style="dashed") >> [cis, booking]
        api >> Edge(style="dashed") >> byo
        deploy >> Edge(label="OIDC") >> role >> ecr
        ecr >> Edge(style="dotted") >> [web, portal, api]


if __name__ == "__main__":
    draw("partner")
