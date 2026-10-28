"""AA-CIS-App view: admin console, API and job worker, data and the LLM path (AA-697).

Facts: apps/AA-CIS-App CONTEXT.md ("Architecture at a glance", "Deploy & CI", "Contracts with other apps") and
docs/ecosystem-architecture.md sections 4.1, 4.3-4.6.
"""
from diagrams import Cluster, Diagram, Edge
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

from _common import ACCOUNT, EDGE_ATTR, EXTERNAL, GRAPH_ATTR, GROUP, NODE_ATTR, VPC

XACC = {"style": "dashed", "color": "#D86613", "fontcolor": "#D86613"}


def draw(filename: str) -> None:
    with Diagram("AA-CIS-App: content system of record (Dev)", filename=filename, outformat="svg", show=False,
                 direction="LR", graph_attr=GRAPH_ATTR, node_attr=NODE_ATTR, edge_attr=EDGE_ATTR):
        staff = Users("AA staff")
        studio = Users("Content studio\n(AA-Partner portal)")

        with Cluster("Vercel", graph_attr=GROUP):
            admin = Vercel("Admin console\nNext.js + BFF")

        with Cluster("GitHub: AA-CIS-App", graph_attr=GROUP):
            deploy = GithubActions("Deploy Dev")

        with Cluster("AWS infrastructure account (acc2) · us-west-1", graph_attr=ACCOUNT):
            cognito = Cognito("Cognito WORKFORCE\nstaff sign-in")
            rest = APIGateway("REST API api-cis\n(WAF, VPC link)")
            role = IAMRole("deploy role")
            ecr = ECR("ECR\nimage per git SHA")
            with Cluster("VPC", graph_attr=VPC):
                alb = ElbApplicationLoadBalancer("NLB → ALB")
                with Cluster("ECS Fargate · one image", graph_attr=GROUP):
                    api = Fargate("aa-cis-dev-api\nadmin API · /v1 studio API\nModel Gateway")
                    worker = Fargate("aa-cis-dev-worker\nshared.job runner\nA-series · T-series jobs")
                rds = RDSPostgresqlInstance("RDS Postgres\nsilver · gold · acp_*\ngeo · catalog · shared")
                cache = ElastiCache("Valkey cache")
                probe = Lambda("ops probe Lambda")
            sched = EventbridgeScheduler("daily schedule")
            s3 = S3("S3 bronze\nuploads · photos\ndocs bundle")
            embed = Bedrock("Bedrock\nCohere Embed v4")
            cw = Cloudwatch("CloudWatch\nlogs · metrics · alarms")

        with Cluster("AWS LLM account (acc3)", graph_attr=ACCOUNT):
            invoker = IAMRole("Bedrock invoker role")
            llm = Bedrock("Bedrock\nwriter + judge models")

        with Cluster("Outside services", graph_attr=EXTERNAL):
            apis = Internet("Decision + SEO APIs\nJev · DataForSEO\nOpenAI (judge fallback)")
            channels = Internet("Photos + channels\nGoogle Drive\nWordPress · Facebook")

        staff >> admin >> rest
        admin >> Edge(label="sign-in", style="dotted") >> cognito
        studio >> Edge(label="tenant JWT") >> rest
        rest >> alb >> api
        api >> Edge(label="enqueue", style="dashed") >> rds
        worker >> rds
        api >> cache
        worker >> s3
        [api, worker] >> embed
        worker >> Edge(label="sts:AssumeRole", **XACC) >> invoker >> llm
        worker >> [apis, channels]
        sched >> probe >> Edge(label="admin checks") >> rest
        api >> Edge(style="dotted") >> cw
        deploy >> Edge(label="OIDC") >> role >> ecr
        ecr >> Edge(style="dotted") >> [api, worker]


if __name__ == "__main__":
    draw("cis")
