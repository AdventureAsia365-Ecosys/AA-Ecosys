"""Ecosystem view: the four apps, the shared platform on the infrastructure account, the LLM account (AA-697).

Facts: docs/ecosystem-architecture.md sections 1, 2, 4.1-4.3, 4.6 and 5 (reviewed 2026-10-28, S255), cross-checked
against the live aa365 Terraform state on 2026-10-28 (docs/audits/2026-10-28-S256-aa697-drift/).
"""
from diagrams import Cluster, Diagram, Edge
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

from _common import ACCOUNT, EDGE_ATTR, GRAPH_ATTR, GROUP, NODE_ATTR, VPC, cluster_ref

XACC = {"style": "dashed", "color": "#D86613", "fontcolor": "#D86613"}


def draw(filename: str) -> None:
    with Diagram("AA-Ecosys: ecosystem architecture (Dev)", filename=filename, outformat="svg", show=False,
                 direction="LR", graph_attr=GRAPH_ATTR, node_attr=NODE_ATTR, edge_attr=EDGE_ATTR):
        with Cluster("People", graph_attr=GROUP):
            staff = Users("AA staff")
            agencies = Users("Partner agencies")
            travellers = Users("Travellers")

        with Cluster("Vercel", graph_attr=GROUP):
            cis_admin = Vercel("CIS admin")
            bk_admin = Vercel("Booking admin")
            tp_fe = Vercel("TripPlanner web")

        with Cluster("GitHub org", graph_attr=GROUP):
            ci = GithubActions("CI and deploy\nworkflows")

        with Cluster("AWS infrastructure account (acc2) · us-west-1", graph_attr=ACCOUNT):
            with Cluster("Edge", graph_attr=GROUP):
                cdn = CloudFront("CloudFront\nagency hosts\n+ photos")
                rest = APIGateway("API Gateway REST\nCIS · Booking")
                http = APIGateway("API Gateway HTTP\nTripPlanner")

            with Cluster("Shared VPC", graph_attr=VPC):
                nlb = ElbNetworkLoadBalancer("Internal NLB")
                alb = ElbApplicationLoadBalancer("ALB\n(regional WAF)")
                with Cluster("ECS Fargate cluster", graph_attr=GROUP) as ecs_cluster:
                    cis = Fargate("AA-CIS-App\napi + job worker")
                    booking = Fargate("AA-Booking\napi + booking.job")
                    crm = Fargate("AA-Partner\napi · web · portal")
                lambdas = Lambda("TripPlanner\nbrowse · assembly")
                rds = RDSPostgresqlInstance("RDS Postgres\none schema per app")
                cache = ElastiCache("Valkey\n(CIS cache)")

            with Cluster("Platform services", graph_attr=GROUP):
                cognito = Cognito("Cognito\nstaff · partner\ntraveller · M2M")
                s3 = S3("S3\nbronze · docs bundle\nmedia · CRM documents")
                embed = Bedrock("Bedrock\nembeddings\nCRM guardrail")
                oidc = IAMRole("OIDC deploy\nroles")
                ecr = ECR("ECR")

        with Cluster("AWS LLM account (acc3) · us-west-1", graph_attr=ACCOUNT):
            invoker = IAMRole("Bedrock\ninvoker role")
            llm = Bedrock("Bedrock\nchat models")

        external = Internet("External APIs\nOpenAI · Jev · DataForSEO\nMapbox · Google Drive")

        staff >> [cis_admin, bk_admin]
        travellers >> tp_fe
        agencies >> cdn
        [cis_admin, bk_admin] >> rest
        tp_fe >> http >> lambdas
        rest >> Edge(label="VPC link") >> nlb
        cdn >> Edge(label="VPC origin") >> nlb
        nlb >> alb >> Edge(**cluster_ref(ecs_cluster)) >> booking
        crm >> Edge(label="HTTP contracts", style="dashed") >> rest
        [cis, booking, crm, lambdas] >> rds
        cis >> cache
        cis >> Edge(style="dashed") >> external
        [cis, lambdas] >> Edge(label="sts:AssumeRole", **XACC) >> invoker >> llm
        lambdas >> Edge(style="dotted") >> embed
        rds >> Edge(style="invis") >> cognito
        ci >> Edge(label="OIDC") >> oidc >> ecr


if __name__ == "__main__":
    draw("ecosystem")
