"""AI gateway view: who calls the gateway, where its control plane and ledger live, and which providers it reaches
(root ADR 0009, AA-1020).

Facts: docs/architecture/ai-gateway.md (as built 2026-11-01: CIS 319-324, crm-032, the 323 contract views, the acc2
candidate models of 324, no Anthropic key, the CRM on the stub provider) and docs/ecosystem-architecture.md 4.3.
Dotted arrows are paths that are built but not live (no key, stub provider, no route). Names only, no IDs.
"""
from diagrams.aws.compute import Fargate, Lambda
from diagrams.aws.database import RDSPostgresqlInstance
from diagrams.aws.general import Users
from diagrams.aws.ml import Bedrock
from diagrams.aws.security import IAMRole
from diagrams.onprem.network import Internet
from diagrams.programming.framework import Vercel

from _common import diagram, group, legend, link, place


def draw(filename: str) -> None:
    with diagram("AA-Ecosys: AI gateway (Dev, as built)", filename):
        with group("people", "People"):
            staff = Users("AA staff")

        with group("vercel", "Vercel"):
            admin = Vercel("CIS admin\nAI providers · Cost Operations")

        with group("cloud", "AWS Cloud", "infrastructure account (acc2)"):
            with group("region", "us-west-1"):
                with group("generic", "Callers", "gateway code inside each app") as callers:
                    cis = Fargate("AA-CIS-App api + worker\nshared/llm_client\ncontrol plane owner")
                    crm = Fargate("AA-Partner CRM api\nvendored aa_llm core\nown control plane")
                    tp = Lambda("TripPlanner Lambdas\nvendored aa_llm core")
                with group("generic", "Amazon RDS for PostgreSQL", "shared instance"):
                    registry = RDSPostgresqlInstance("shared: registry v2\nroutes · scopes · budgets\ncircuit state")
                    ledger = RDSPostgresqlInstance("shared.llm_call_log\nledger v2: one row per attempt")
                    views = RDSPostgresqlInstance("catalog contract views\nconfig + today's spend\n(TripPlanner only)")
                    crm_db = RDSPostgresqlInstance("schema crm\nAI settings + crm.llm_call\n(ledger v2 shape)")
                with group("generic", "Amazon Bedrock on acc2") as acc2_bedrock:
                    embed = Bedrock("Amazon Bedrock\nCohere Embed v4")
                    candidates = Bedrock("Amazon Bedrock\n5 chat candidates\ncatalogued, no route")
                    guard = Bedrock("Amazon Bedrock Guardrails\nCRM PII scrub")

        with group("cloud", "AWS Cloud", "LLM account (acc3)") as acc3:
            invoker = IAMRole("AWS IAM\nBedrock invoker role")
            with group("region", "us-west-1"):
                chat = Bedrock("Amazon Bedrock\nmain chat models\n(refusing since 2026-10-29)")

        with group("outside", "Outside services", "other failure domains") as outside:
            openai = Internet("OpenAI API\njudge last resort")
            anthropic = Internet("Anthropic API\nbuilt, no key yet")
            data = Internet("Jev · DataForSEO\nGeoapify")

        place({
            staff: (0, 0), admin: (1, 0),
            cis: (2, 1), registry: (4, 1), embed: (6, 1), invoker: (8, 1), chat: (9, 1),
            tp: (2, 2), ledger: (4, 2), candidates: (6, 2),
            crm: (2, 3), views: (4, 3), guard: (6, 3), openai: (8, 3), anthropic: (9, 3),
            crm_db: (4, 4), data: (8, 4),
        })
        legend((9, 5))

        link(staff, admin)
        link(admin, cis, "AI providers API")
        # configuration and ledger
        link(cis, registry)
        link(cis, ledger, "ledger rows")
        link(tp, views, "config + spend")
        link(tp, ledger, "INSERT")
        link(crm, crm_db, "settings, ledger")
        link(views, registry, "reads", "async")
        # providers
        link(cis, embed, "embeddings", into=acc2_bedrock)
        link(cis, invoker, "sts:AssumeRole (CIS, TripPlanner)", "control", out_of=callers)
        link(invoker, chat)
        link(crm, guard, "PII scrub")
        link(cis, candidates, "eval only after the ladder", "async")
        link(cis, openai, "direct and data APIs (CIS)", out_of=callers, into=outside)


if __name__ == "__main__":
    draw("gateway")
