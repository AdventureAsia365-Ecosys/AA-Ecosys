"""AA-CIS-Infra view: what the two Terraform roots create and how traffic reaches the workloads (AA-697).

Facts: infra/AA-CIS-Infra CONTEXT.md ("Account model", "Main stack modules", "CI/CD and OIDC") and
docs/ecosystem-architecture.md sections 4.2-4.4 and 5, cross-checked against the live aa365 state on 2026-10-28
(TerraVision + a no-refresh plan, docs/audits/2026-10-28-S256-aa697-drift/). Subnet tiers from modules/vpc (public:
NAT instance, ALB; private: NLB, ECS tasks, VPC Lambdas, Valkey, EFS; database: RDS). Names only; IDs come from
Terraform outputs.
"""
from diagrams.aws.compute import EC2, ECR, ElasticContainerServiceService, ElasticContainerServiceTask, Lambda
from diagrams.aws.cost import Budgets, CostExplorer
from diagrams.aws.database import ElastiCache, RDSPostgresqlInstance
from diagrams.aws.engagement import SES
from diagrams.aws.integration import Eventbridge, EventbridgeScheduler, SNS
from diagrams.aws.management import Cloudtrail, Cloudwatch
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import APIGateway, CloudFront, ElbApplicationLoadBalancer, ElbNetworkLoadBalancer, Route53
from diagrams.aws.security import IAMRole, Cognito, KMS, SecretsManager, WAF
from diagrams.aws.storage import EFS, S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.iac import Terraform
from diagrams.onprem.network import Internet

from _common import diagram, group, legend, link, place


def draw(filename: str) -> None:
    with diagram("AA-CIS-Infra: Terraform roots and the Dev platform", filename):
        with group("github", "AA-CIS-Infra repo"):
            gha = GithubActions("GitHub Actions\nPlan / Apply · DB Migrate · Schema Dump")
            tf_main = Terraform("aa365 root\nCI apply")
            tf_llm = Terraform("acc3-bedrock root\nhuman apply, MFA")

        with group("outside", "Internet"):
            internet = Internet("Outside APIs\nLLM · SEO · maps")

        with group("cloud", "AWS Cloud", "infrastructure account (acc2)"):
            ci_roles = IAMRole("AWS IAM\nOIDC CI roles: plan (read) · apply (boundary)\none deploy role per app")
            dns = Route53("Amazon Route 53\npublic + private zones")
            cdn = CloudFront("Amazon CloudFront\npartner · agency · client\nphotos (S3 origin)")
            with group("region", "us-west-1"):
                with group("generic", "Edge"):
                    rest = APIGateway("Amazon API Gateway\nREST APIs: CIS · Booking")
                    waf = WAF("AWS WAF\nregional, on the ALB")
                    http = APIGateway("Amazon API Gateway\nHTTP API: TripPlanner")

                with group("vpc", "Shared VPC"):
                    with group("private", "Private subnets", "load balancer entry"):
                        nlb = ElbNetworkLoadBalancer("Network Load Balancer\ninternal: VPC link + origin")
                    with group("public", "Public subnets"):
                        nat = EC2("Amazon EC2\nNAT instance (t4g.nano)\n+ Elastic IP")
                        alb = ElbApplicationLoadBalancer("Application LB\nreachable from the NLB only")
                    with group("private", "Private subnets", "workloads") as workloads:
                        with group("ecs", "Amazon ECS cluster", "aa-cis-dev-cluster, Fargate + Spot") as ecs:
                            svc_cis = ElasticContainerServiceService("ECS service\nCIS api + worker")
                            svc_bk = ElasticContainerServiceService("ECS service\nBooking api + booking.job")
                            svc_crm = ElasticContainerServiceService("ECS service\nCRM api · web · portal")
                            migrate = ElasticContainerServiceTask("ECS task\none-off DB Migrate")
                        lambdas = Lambda("AWS Lambda in the VPC\nTripPlanner browse · assembly\nDFS balance probe")
                        cache = ElastiCache("Amazon ElastiCache\nValkey 8, TLS + AUTH")
                        efs = EFS("Amazon EFS\n(no task mounts it)")
                    with group("private", "Private subnets", "database"):
                        rds = RDSPostgresqlInstance("Amazon RDS for PostgreSQL 15\ndeletion protection")

                with group("generic", "Data, secrets, identity"):
                    ecr = ECR("Amazon ECR\n5 repos, immutable tags")
                    s3 = S3("Amazon S3, 15 buckets\nCIS + ACP tiers · CRM (SSE-KMS)\n"
                            "Booking media · TP artifacts\nCloudTrail · ALB logs")
                    secrets = SecretsManager("AWS Secrets Manager\none DSN secret per app")
                    kms = KMS("AWS KMS, 4 CMKs\nCloudTrail · CRM data\nCRM ingest · CRM seal")
                    bedrock2 = Bedrock("Amazon Bedrock\nembeddings · CRM guardrail")
                    cognito = Cognito("Amazon Cognito\nfour user pools")
                    waf_id = WAF("AWS WAF\non 3 user pools")
                    triggers = Lambda("AWS Lambda outside the VPC\n4 Cognito triggers\nRDS snapshot expiry")
                    sched = EventbridgeScheduler("EventBridge Scheduler\naa-cis-dev-acp group\n5 daily schedules")
                    ses = SES("Amazon SES\nno-reply sender\ninbound test mail")

                with group("generic", "Operations"):
                    budgets = Budgets("AWS Budgets\nper app + cost anomaly")
                    trail = Cloudtrail("AWS CloudTrail\n(KMS) + IAM Access Analyzer")
                    rules = Eventbridge("Amazon EventBridge\nsecurity rules · ACP bus + DLQ")
                    cw = Cloudwatch("Amazon CloudWatch\nlogs · alarms · flow logs")
                    sns = SNS("Amazon SNS\nalerts (e-mail) · SES feedback")

        with group("cloud", "AWS Cloud", "LLM account (acc3)") as acc3:
            invoker = IAMRole("AWS IAM\nBedrock invoker role")
            batch = IAMRole("AWS IAM\nBedrock Batch service role")
            ce_reader = CostExplorer("AWS IAM\nCost Explorer reader role")
            with group("region", "us-west-1"):
                bedrock = Bedrock("Amazon Bedrock\nchat models")
                budget3 = Budgets("AWS Budgets\nbudget + anomaly alerts")

        place({
            internet: (4, 0),
            gha: (0, 1), tf_main: (1, 1), tf_llm: (2, 1),
            ci_roles: (1, 3), nat: (4, 3), svc_cis: (5, 3), cache: (6, 3), budgets: (8, 3),
            dns: (1, 4), rest: (2, 4), nlb: (3, 4), alb: (4, 4), svc_bk: (5, 4), rds: (7, 4), trail: (8, 4),
            rules: (9, 4), invoker: (11, 4), bedrock: (12, 4),
            cdn: (1, 5), waf: (2, 5), svc_crm: (5, 5), efs: (6, 5), cw: (8, 5), sns: (9, 5), batch: (11, 5),
            http: (2, 6), migrate: (5, 6), ce_reader: (11, 6), budget3: (12, 6),
            lambdas: (5, 7),
            ecr: (2, 9), s3: (3, 9), secrets: (4, 9), kms: (5, 9), bedrock2: (6, 9),
            waf_id: (2, 10), cognito: (3, 10), triggers: (4, 10), sched: (5, 10), ses: (6, 10),
        })
        legend((12, 9))

        # CI/CD and the two Terraform roots
        link(gha, tf_main, "plan / apply", "control")
        link(gha, tf_llm, kind="control")
        link(gha, ci_roles, "OIDC", "control")
        link(tf_main, ci_roles, "creates", "control")
        # all three acc3 roles: one arrow to the account border
        link(tf_llm, invoker, "creates the acc3 roles", "control", into=acc3)
        link(ci_roles, ecr, "push image", "control")
        link(ci_roles, migrate, "run task", "control")
        # request path
        link(dns, rest)
        link(dns, cdn)
        link(rest, nlb, "VPC link")
        link(cdn, nlb, "VPC origin")
        link(cdn, s3, "OAC")
        link(nlb, alb)
        link(alb, svc_bk, into=ecs)
        link(waf, alb, "protects", "control")
        link(http, lambdas)
        # workloads (ECS services, the DB Migrate task, the VPC Lambdas)
        link(svc_cis, rds, out_of=workloads)
        link(svc_cis, cache)
        link(svc_cis, secrets, "DSN secret", "control")
        link(svc_crm, kms, "CRM keys", "control")
        link(svc_cis, bedrock2, "CIS, CRM, TripPlanner", out_of=workloads)
        link(svc_cis, nat, "egress (CIS, TripPlanner)", out_of=workloads)
        link(nat, internet)
        link(svc_cis, invoker, "sts:AssumeRole (CIS, TripPlanner)", "control", out_of=workloads)
        link(svc_cis, ce_reader, "cost read", "control")
        link(batch, bedrock)
        # identity and operations
        link(waf_id, cognito, "protects", "control")
        link(cognito, triggers, "triggers", "async")
        link(sched, triggers, kind="async")
        link(sched, lambdas, "daily", "async")
        link(trail, rules, kind="async")
        link(rules, sns, kind="async")
        link(cw, sns, "alarms", "async")


if __name__ == "__main__":
    draw("infra")
