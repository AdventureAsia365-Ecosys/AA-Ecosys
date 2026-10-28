"""AA-CIS-Infra view: what the two Terraform roots create and how traffic reaches the workloads (AA-697).

Facts: infra/AA-CIS-Infra CONTEXT.md ("Account model", "Main stack modules", "CI/CD and OIDC") and
docs/ecosystem-architecture.md sections 4.2-4.4 and 5. Names only; IDs come from Terraform outputs.
"""
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECR, ElasticContainerServiceService, ElasticContainerServiceTask, Lambda
from diagrams.aws.database import ElastiCache, RDSPostgresqlInstance
from diagrams.aws.engagement import SES
from diagrams.aws.integration import EventbridgeScheduler, SNS
from diagrams.aws.management import Cloudwatch
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import (APIGateway, CloudFront, ElbApplicationLoadBalancer, ElbNetworkLoadBalancer,
                                  NATGateway, Route53)
from diagrams.aws.security import IAMRole, Cognito, KMS, SecretsManager, WAF
from diagrams.aws.cost import Budgets, CostExplorer
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.iac import Terraform
from diagrams.onprem.network import Internet

from _common import ACCOUNT, EDGE_ATTR, GRAPH_ATTR, GROUP, NODE_ATTR, VPC, cluster_ref

XACC = {"style": "dashed", "color": "#D86613", "fontcolor": "#D86613"}


def draw(filename: str) -> None:
    with Diagram("AA-CIS-Infra: Terraform roots and the Dev platform", filename=filename, outformat="svg",
                 show=False, direction="TB", graph_attr=GRAPH_ATTR, node_attr=NODE_ATTR, edge_attr=EDGE_ATTR):
        with Cluster("AA-CIS-Infra repo", graph_attr=GROUP):
            gha = GithubActions("Terraform Plan / Apply\nDB Migrate · Schema Dump")
            tf_main = Terraform("aa365 root\n(CI apply)")
            tf_llm = Terraform("acc3-bedrock root\n(human, MFA)")

        with Cluster("AWS infrastructure account (acc2) · us-west-1", graph_attr=ACCOUNT):
            ci_roles = IAMRole("OIDC CI roles\nplan (read) · apply (boundary)\none deploy role per app")

            with Cluster("DNS and edge", graph_attr=GROUP):
                dns = Route53("Route 53\npublic + private zones")
                waf = WAF("Regional WAF")
                rest = APIGateway("REST APIs\nCIS · Booking")
                http = APIGateway("HTTP API\nTripPlanner")
                cdn = CloudFront("CloudFront\npartner · agency · client")

            with Cluster("VPC", graph_attr=VPC):
                nat = NATGateway("NAT gateway")
                nlb = ElbNetworkLoadBalancer("Internal NLB\nVPC link + VPC origin")
                alb = ElbApplicationLoadBalancer("ALB\n(reachable from the NLB only)")
                with Cluster("ECS cluster aa-cis-dev-cluster", graph_attr=GROUP) as ecs:
                    svc_cis = ElasticContainerServiceService("CIS api + worker")
                    svc_bk = ElasticContainerServiceService("Booking api")
                    svc_crm = ElasticContainerServiceService("CRM api · web · portal")
                    migrate = ElasticContainerServiceTask("one-off task\nDB Migrate")
                lambdas = Lambda("Lambdas\nTripPlanner + ops probe")
                rds = RDSPostgresqlInstance("RDS Postgres 15\ndeletion protection")
                cache = ElastiCache("Valkey\nTLS + AUTH")

            with Cluster("Data, secrets, identity", graph_attr=GROUP):
                ecr = ECR("ECR\nimmutable tags")
                s3 = S3("S3 buckets\nbronze · artifacts\nmedia · ops docs")
                secrets = SecretsManager("Secrets Manager\none DSN secret per app")
                kms = KMS("KMS\n(ops docs CMK)")
                cognito = Cognito("Cognito\nfour user pools")
                ses = SES("SES\nno-reply sender")

            with Cluster("Operations", graph_attr=GROUP):
                sched = EventbridgeScheduler("Scheduler group\naa-cis-dev-acp")
                cw = Cloudwatch("CloudWatch\nlogs · alarms")
                sns = SNS("SNS alerts topic\n(e-mail)")
                budgets = Budgets("Budgets per App\n+ cost anomaly")

        with Cluster("AWS LLM account (acc3) · us-west-1", graph_attr=ACCOUNT):
            invoker = IAMRole("Bedrock invoker role")
            batch = IAMRole("Bedrock Batch\nservice role")
            ce_reader = CostExplorer("Cost Explorer\nreader role")
            bedrock = Bedrock("Bedrock")
            budget3 = Budgets("Budget + anomaly\nalerts")

        internet = Internet("Internet\n(LLM, SEO, map APIs)")

        gha >> Edge(label="OIDC") >> ci_roles
        gha >> [tf_main, tf_llm]
        tf_main >> Edge(style="dotted") >> ci_roles
        ci_roles >> Edge(style="dotted") >> [ecr, migrate]
        dns >> [rest, cdn]
        waf - Edge(style="dotted") - rest
        rest >> Edge(label="VPC link") >> nlb
        cdn >> Edge(label="VPC origin") >> nlb
        http >> lambdas
        nlb >> alb >> Edge(**cluster_ref(ecs)) >> svc_bk
        [svc_cis, svc_bk, svc_crm, migrate, lambdas] >> rds
        svc_cis >> cache
        svc_cis >> Edge(style="dotted") >> secrets
        svc_bk >> Edge(style="dotted") >> kms
        [svc_cis, lambdas] >> nat >> internet
        sched >> lambdas
        cw >> sns
        tf_llm >> Edge(style="dotted") >> invoker
        [svc_cis, lambdas] >> Edge(label="sts:AssumeRole", **XACC) >> invoker >> bedrock
        svc_cis >> Edge(label="cost read", **XACC) >> ce_reader
        batch >> bedrock
        budget3 - Edge(style="invis") - ce_reader
        ecr - Edge(style="invis") - s3
        cognito - Edge(style="invis") - ses
        budgets - Edge(style="invis") - sns


if __name__ == "__main__":
    draw("infra")
