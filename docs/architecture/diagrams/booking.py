"""AA-Booking view: staff admin, API with its booking.job worker, data and contracts (AA-697).

Facts: apps/AA-Booking CONTEXT.md ("Role in the ecosystem", "Runtime and request path", "Staff authentication",
"B2B API", "Deferred work") and docs/ecosystem-architecture.md sections 3.4, 4.1, 4.2, 4.6.
"""
from diagrams import Cluster, Diagram, Edge
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

from _common import ACCOUNT, EDGE_ATTR, GRAPH_ATTR, GROUP, NODE_ATTR, VPC


def draw(filename: str) -> None:
    with Diagram("AA-Booking: advisor workflow and booking lifecycle (Dev)", filename=filename, outformat="svg",
                 show=False, direction="LR", graph_attr=GRAPH_ATTR, node_attr=NODE_ATTR, edge_attr=EDGE_ATTR):
        staff = Users("AA staff\n(advisors, operations)")

        with Cluster("Vercel", graph_attr=GROUP):
            admin = Vercel("Booking admin\nNext.js + BFF")

        with Cluster("GitHub: AA-Booking", graph_attr=GROUP):
            deploy = GithubActions("Deploy Dev\n(deploy-gate preflight)")

        with Cluster("AWS infrastructure account (acc2) · us-west-1", graph_attr=ACCOUNT):
            cognito = Cognito("Cognito\nWORKFORCE staff\nM2M · EXTERNAL")
            partner = Fargate("AA-Partner api\n(B2B client)")
            rest = APIGateway("REST API\naa-booking-dev")
            role = IAMRole("deploy role")
            ecr = ECR("ECR\nimage per git SHA")
            with Cluster("Shared VPC", graph_attr=VPC):
                alb = ElbApplicationLoadBalancer("VPC link → NLB → ALB\nrule /booking/*")
                api = Fargate("aa-booking-dev-api\nFastAPI + booking.job worker")
                with Cluster("RDS Postgres (shared instance)", graph_attr=GROUP):
                    own = RDSPostgresqlInstance("schema booking\n(bk-NNN, owner)")
                    reads = RDSPostgresqlInstance(
                        "read through grants\ncatalog.* views (CIS)\ninquiry outbox (TripPlanner)")
            media = S3("S3\nsupplier media")
            docs = S3("S3\nops documents")
            kms = KMS("KMS CMK\n(ops documents)")
            ses = SES("SES\nstaff e-mail")
            cw = Cloudwatch("CloudWatch\nlogs · AA/Jobs/Booking")

        staff >> admin >> rest
        admin >> Edge(label="sign-in", style="dotted") >> cognito
        partner >> Edge(label="booking.b2b.v1 (M2M token)") >> rest
        rest >> alb >> api
        api >> own
        api >> Edge(label="read only", style="dashed") >> reads
        api >> [media, docs, ses]
        docs >> Edge(style="dotted") >> kms
        api >> Edge(style="dotted") >> cw
        deploy >> Edge(label="OIDC") >> role >> ecr
        ecr >> Edge(style="dotted") >> api


if __name__ == "__main__":
    draw("booking")
