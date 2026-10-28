"""AA-TripPlanner-Web view: map-first web app, two Lambdas split by statefulness, data and AI (AA-697).

Facts: apps/AA-TripPlanner-Web CONTEXT.md ("Architecture at a glance", "Backend", "Guest identity", "AI (Bedrock)",
"Deploy & CI") and docs/ecosystem-architecture.md sections 4.1-4.3.
"""
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Fargate, Lambda
from diagrams.aws.database import RDSPostgresqlInstance
from diagrams.aws.general import Users
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import APIGateway
from diagrams.aws.security import IAMRole, Cognito, SecretsManager
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.network import Internet
from diagrams.programming.framework import Vercel

from _common import ACCOUNT, EDGE_ATTR, EXTERNAL, GRAPH_ATTR, GROUP, NODE_ATTR, VPC

XACC = {"style": "dashed", "color": "#D86613", "fontcolor": "#D86613"}


def draw(filename: str) -> None:
    with Diagram("AA-TripPlanner-Web: map-first trip planner (Dev)", filename=filename, outformat="svg",
                 show=False, direction="LR", graph_attr=GRAPH_ATTR, node_attr=NODE_ATTR, edge_attr=EDGE_ATTR):
        travellers = Users("Travellers\n(guest or signed in)")

        with Cluster("Vercel", graph_attr=GROUP):
            fe = Vercel("Next.js web app\nmap UI + BFF")

        with Cluster("Outside services", graph_attr=EXTERNAL):
            mapbox = Internet("Mapbox\nmap tiles")

        with Cluster("GitHub: AA-TripPlanner-Web", graph_attr=GROUP):
            deploy = GithubActions("deploy-lambdas")

        with Cluster("AWS infrastructure account (acc2) · us-west-1", graph_attr=ACCOUNT):
            cognito = Cognito("Cognito EXTERNAL\ne-mail code sign-in")
            http = APIGateway("HTTP API\n/browse · /trip\n(X-TripPlanner-Key)")
            key = SecretsManager("API key secret")
            role = IAMRole("deploy role")
            artifacts = S3("S3\nLambda artifacts")
            embed = Bedrock("Bedrock\nCohere Embed v4")
            with Cluster("Shared VPC", graph_attr=VPC):
                browse = Lambda("browse\nstateless, cacheable reads\nsearch embedding")
                assembly = Lambda("assembly\ntrip writes + AI narration")
                with Cluster("RDS Postgres (shared instance)", graph_attr=GROUP):
                    own = RDSPostgresqlInstance("schema tripplanner\nevent-sourced trips\n(tp-NNN, owner)")
                    reads = RDSPostgresqlInstance("read only\ncatalog.* views (CIS)\nModel Gateway config")
                booking = Fargate("AA-Booking api\n(pulls the inquiry outbox)")

        with Cluster("AWS LLM account (acc3)", graph_attr=ACCOUNT):
            invoker = IAMRole("Bedrock invoker role")
            llm = Bedrock("Bedrock\nClaude (narration)")

        travellers >> fe
        fe >> Edge(style="dotted") >> mapbox
        fe >> Edge(label="sign-in", style="dotted") >> cognito
        fe >> Edge(label="server-side BFF") >> http
        http >> [browse, assembly]
        [browse, assembly] >> Edge(style="dotted") >> key
        browse >> Edge(label="read") >> reads
        assembly >> own
        browse >> embed
        assembly >> Edge(label="sts:AssumeRole", **XACC) >> invoker >> llm
        own >> Edge(label="inquiry.submitted", style="dashed") >> booking
        deploy >> Edge(label="OIDC") >> role >> artifacts
        role >> Edge(label="UpdateFunctionCode", style="dotted") >> [browse, assembly]


if __name__ == "__main__":
    draw("tripplanner")
