"""AA-TripPlanner-Web view: map-first web app, two Lambdas split by statefulness, data and AI (AA-697).

Facts: apps/AA-TripPlanner-Web CONTEXT.md ("Architecture at a glance", "Backend", "Guest identity", "AI (Bedrock)",
"Deploy & CI") and docs/ecosystem-architecture.md sections 4.1-4.3. Subnet tiers from AA-CIS-Infra modules/vpc
(the Lambdas run in the private subnets, AA-Booking on the shared ECS cluster).
"""
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

from _common import diagram, group, legend, link, place


def draw(filename: str) -> None:
    with diagram("AA-TripPlanner-Web: map-first trip planner (Dev)", filename):
        with group("people", "People"):
            travellers = Users("Travellers\n(guest or signed in)")

        with group("vercel", "Vercel"):
            fe = Vercel("Next.js web app\nmap UI + BFF")

        with group("outside", "Outside services"):
            mapbox = Internet("Mapbox\nmap tiles")

        with group("github", "GitHub: AA-TripPlanner-Web"):
            deploy = GithubActions("GitHub Actions\ndeploy-lambdas")

        with group("cloud", "AWS Cloud", "infrastructure account (acc2)"):
            role = IAMRole("AWS IAM\ndeploy role (OIDC)")
            with group("region", "us-west-1"):
                cognito = Cognito("Amazon Cognito\nEXTERNAL e-mail code sign-in")
                http = APIGateway("Amazon API Gateway\nHTTP /browse · /trip (API key)")
                key = SecretsManager("AWS Secrets Manager\nAPI key secret")
                artifacts = S3("Amazon S3\nLambda artifacts")
                embed = Bedrock("Amazon Bedrock\nCohere Embed v4")
                with group("vpc", "Shared VPC"):
                    with group("private", "Private subnets", "TripPlanner Lambdas"):
                        with group("generic", "AWS Lambda functions") as fns:
                            browse = Lambda("browse\nstateless reads · search embedding")
                            assembly = Lambda("assembly\ntrip writes + AI narration")
                    with group("private", "Private subnets", "database"):
                        with group("generic", "Amazon RDS for PostgreSQL", "shared instance"):
                            reads = RDSPostgresqlInstance("read only\ncatalog.* (CIS) · Model Gateway config")
                            own = RDSPostgresqlInstance("schema tripplanner\nevent-sourced trips (tp-NNN)")
                    with group("private", "Private subnets", "ECS workloads"):
                        booking = Fargate("AA-Booking api\npulls the inquiry outbox")

        with group("cloud", "AWS Cloud", "LLM account (acc3)"):
            invoker = IAMRole("AWS IAM\nBedrock invoker role")
            with group("region", "us-west-1"):
                llm = Bedrock("Amazon Bedrock\nClaude (narration)")

        place({
            cognito: (3, 0),
            travellers: (0, 1), fe: (1, 1), http: (3, 1), browse: (4, 1), reads: (5, 1),
            mapbox: (1, 3), assembly: (4, 3), own: (5, 3), booking: (6, 3),
            invoker: (7, 4), llm: (8, 4),
            deploy: (0, 5), role: (2, 5), artifacts: (3, 5), key: (4, 5), embed: (5, 5),
        })
        legend((8, 5))

        link(travellers, fe)
        link(fe, mapbox, "map tiles")
        link(fe, cognito, "sign-in", "control")
        link(fe, http, "server-side BFF")
        link(http, browse, "/browse")
        link(http, assembly, "/trip")
        link(browse, reads, "read")
        link(assembly, own)
        link(browse, embed, "search embedding")
        link(browse, key, "API key", "control", out_of=fns)
        link(assembly, invoker, "sts:AssumeRole", "control")
        link(invoker, llm)
        link(own, booking, "inquiry.submitted", "async")
        link(deploy, role, "OIDC", "control")
        link(role, artifacts, "upload", "control")
        link(role, browse, "UpdateFunctionCode", "control", into=fns)


if __name__ == "__main__":
    draw("tripplanner")
