---
id: ARCH-01-diagrams
title: Architecture diagrams with AWS icons
description: The ecosystem and each repo drawn with the official AWS Architecture Icons, as code (Python diagrams) rendered to checked SVG.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, cis, booking, tripplanner, partner, infra]
last_reviewed: 2026-10-28
review_every_days: 90
related: [ARCH-01, ARCH-06, AA-697]
---

# Architecture diagrams with AWS icons

Six deployment views of the Dev platform, drawn as code with the Python [`diagrams`](https://diagrams.mingrammer.com/)
package, which ships the official AWS Architecture Icons and lays out with Graphviz. Each view is a `.py` source next
to its rendered `.svg`. The prose they illustrate is the source of truth:
[ecosystem architecture](../../ecosystem-architecture.md) and each repo's `CONTEXT.md`. When a view and the prose
disagree, fix the view.

Conventions: account boxes are outlined dark, the VPC is purple, outside services are orange and dashed. A solid arrow is
a request or a write, a dashed arrow is a contract or an outside call, an orange dashed arrow crosses into the LLM
account (`sts:AssumeRole`), a dotted arrow is a supporting link (sign-in, secret, deploy). Labels name services and
roles only: never an account ID, an ARN or a network ID.

## Ecosystem

The four apps on the infrastructure account (acc2), the shared VPC and RDS, the edge (API Gateway, CloudFront) and the
LLM account (acc3). Source: [`ecosystem.py`](ecosystem.py).

![Ecosystem architecture with AWS icons](ecosystem.svg)

## AA-CIS-Infra

What the two Terraform roots create: edge and DNS, the VPC with the ECS cluster, Lambdas, RDS and Valkey, data and
identity services, operations, and the acc3 roles. Source: [`infra.py`](infra.py). Cross-checked on 2026-10-28 against
the live `accounts/aa365` state (a no-refresh plan reported no changes) with TerraVision 0.56.0: every service group in
the state has a node and no node draws something that does not exist. The drift table and how to repeat the check are in
the root audit folder `docs/audits/2026-10-28-S256-aa697-drift/`.

![AA-CIS-Infra Terraform roots and the Dev platform](infra.svg)

## AA-CIS-App

The admin console on Vercel, the API and the `shared.job` worker on one image, the CIS schemas, and the Model Gateway
path to Bedrock on both accounts and to the outside APIs. Source: [`cis.py`](cis.py).

![AA-CIS-App with AWS icons](cis.svg)

## AA-Booking

The staff admin, the API with its `booking.job` worker behind the `/booking/*` ALB rule, its own schema, the read-only
grants it consumes, the B2B API for AA-Partner, and its S3, KMS and SES pieces. Source: [`booking.py`](booking.py).

![AA-Booking with AWS icons](booking.svg)

## AA-TripPlanner-Web

The Next.js web app, the HTTP API and the two Lambdas split by statefulness, the `tripplanner` schema and the read-only
catalog views, the embedding and narration models, and the inquiry hand-off to AA-Booking.
Source: [`tripplanner.py`](tripplanner.py).

![AA-TripPlanner-Web with AWS icons](tripplanner.svg)

## AA-Partner

The agency CRM and the Content studio behind CloudFront (VPC origin on the shared NLB), the three ECS services, the
`crm` schema with row-level security, the PARTNER and M2M identity, and the HTTP contracts with CIS and AA-Booking.
Source: [`partner.py`](partner.py).

![AA-Partner with AWS icons](partner.svg)

## Change a diagram

1. Edit the `.py` file (or add one and list it in `VIEWS` in [`render.py`](render.py)). Shared styles and the SVG
   clean-up live in [`_common.py`](_common.py).
2. Render with Graphviz `dot` on the `PATH` and a virtual environment that has `diagrams`, Pillow (smaller inline
   icons) and the docs tool requirements:

   ```bash
   python3 -m venv .tmp-session/diagrams-venv
   .tmp-session/diagrams-venv/bin/pip install diagrams pillow -r tools/docs/requirements.txt
   .tmp-session/diagrams-venv/bin/python docs/architecture/diagrams/render.py
   ```

   Without root rights, `apt-get download graphviz` and its libraries, unpack them with `dpkg -x` into a local folder
   and point `PATH`, `LD_LIBRARY_PATH` and `GVBINDIR` at it (run `dot -c` once).
3. `render.py` inlines every icon as a PNG data URI, numbers the node ids (an unchanged view renders to the same file)
   and refuses an unsafe SVG. Commit the `.py` and the `.svg` together.

The docs reader publishes each SVG byte for byte only when it passes rule 9 of
[`build_docs_reader.py`](../../../tools/docs/build_docs_reader.py): no script, `foreignObject`, event handler or
outside reference, and no account or resource ID in its text. `python3 render.py --check` runs the same check on the
committed files; the docs lint unit tests run it in CI.

## Check a view against Terraform

Repeat the drift check after an infrastructure change that adds or removes a service:

1. In an AA-CIS-Infra checkout of `main`, with read-only credentials, run
   `terraform plan -lock=false -refresh=false -out=<plan>` in `accounts/aa365`. "No changes" means the code and the
   state agree, so the plan lists what exists.
2. `terraform show -json <plan>` and `terraform graph -plan=<plan>`, then
   `terravision graphdata --planfile <plan.json> --graphfile <graph.dot> --source accounts/aa365 --show_services`.
   TerraVision skips a few types (RDS instance, ElastiCache, SQS, EC2), so also list the managed resource types of the
   plan JSON.
3. Compare with the nodes of the views, fix the `.py` sources, render, and commit. Keep the plan, the JSON and any
   TerraVision image out of the repo: they hold account IDs and, for `show -json`, sensitive values.

Each repo's `CONTEXT.md` links this page.

## Not covered yet

- Inline Mermaid `architecture-beta` diagrams with an AWS icon pack in the docs reader.
