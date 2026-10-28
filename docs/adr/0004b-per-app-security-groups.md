# ADR 0004 — Amendment B: one security group per caller (per-app network isolation)

- **Status:** Accepted (18/10/2026, S242). The tech lead approved X1 with "SG in the same wave" (S241 D-05/D-06).
  Separate file referenced from `docs/adr/0004-aa-booking-stack-and-bootstrap.md` (Decision 5 points here).
- **Amends:** ADR 0004 decision 5 ("existing private subnets and app security group") and its module
  boundary ("no other change to `modules/ecs`, `modules/api_gateway` or `modules/alb` resources"), for
  `modules/vpc`, `modules/ecs`, `modules/elasticache` and `modules/efs` only.
- **Implements:** ADR 0008 decision 6 (each app isolated from the others at the data layer) and data standards
  SEC-1 for the network layer. Plan: `docs/audits/2026-10-17-S241-x1/x1-plan.md` §2 and steps S11–S14 (AA-852).
- **Related Linear:** AA-852 (X1), AA-860 (CIS runtime role split), AA-874 (Redis AUTH/TLS).
- **Update 2026-10-28:** the rollout is finished. S14 removed the shared app group from the RDS, Redis and EFS
  lists; the group itself is still defined in `modules/vpc`. AA-Partner got its own groups under decision 6:
  `aa-cis-dev-sg-crm-api` (admitted by RDS), `aa-cis-dev-sg-crm-web` and `aa-cis-dev-sg-crm-portal` (no data-store
  access). The current lists are in AA-CIS-Infra `accounts/aa365/app_security_groups.tf`.

## Context

On acc2 Dev every workload shares one app security group `aa-cis-dev-sg-app`: the CIS
api and worker services, the Booking service, both TripPlanner Lambdas, the dfs-balance Lambda, every DB
Migrate / Schema Dump task, and two orphan ENIs of the deleted `aa-cis-dev-ingestion` Lambda. The RDS, Redis
and EFS security groups admit only that group. So:

- Booking and TripPlanner can open connections to Redis (no AUTH today) and to every port of each other's tasks;
- a database role split (X1) can be bypassed at the network layer by any workload in the shared group;
- nobody can tell from a security group rule which app needs which data store.

The app group also carries a vestigial self-ingress on 443 for a Secrets Manager VPC endpoint that does not
exist (AWS APIs go through the NAT instance).

## Decision

1. **One security group per caller**, created in `accounts/aa365/app_security_groups.tf`:
   `aa-cis-dev-sg-cis-api`, `aa-cis-dev-sg-cis-worker`, `aa-cis-dev-sg-booking-api`, `aa-cis-dev-sg-tp-lambda`,
   `aa-cis-dev-sg-db-migrate`, `aa-cis-dev-sg-ops-lambda`. Ingress only where a caller serves traffic
   (cis-api and booking-api: tcp 8000 from the ALB group); egress `0.0.0.0/0` (NAT for AWS APIs, Bedrock,
   third-party APIs).
2. **Data stores admit callers by group, least access:**
   - RDS: cis-api, cis-worker, booking-api, tp-lambda, db-migrate;
   - Redis: cis-api, cis-worker only (Booking and TripPlanner never reach Redis);
   - EFS: cis-api, cis-worker only.
3. **Inline ingress lists.** The RDS, Redis and EFS groups keep their inline `ingress {}` blocks (authoritative),
   driven by one list variable per module (`rds_ingress_sg_ids`, `ingress_sg_ids`) whose default is the old
   app group, so the change is expand → switch → contract with no window where a caller loses access.
4. **DB Migrate, Schema Dump and the isolation probe run from their own task definition**
   (`aa-cis-dev-db-migrate`) in the db-migrate group, not as an override of the CIS api task.
5. **Removed:** the self-443 rule; the old app group once no live ENI uses it (orphan ENIs deleted by hand first).
6. **Production uses the same shape.** A new app gets its own group from day one (ADR 0008 new-app playbook).

## Rollout (X1 plan S11–S14)

- S11 expand: create the groups and the migrator task definition; add the new groups to the data-store lists
  next to the old one. No service change.
- S12: the database workflows move to the migrator task definition.
- S13 switch, three applies behind the job-idle gate: Booking → TripPlanner + ops Lambdas → CIS api + worker.
- S14 contract: drop the old group from every data-store list, after an ENI gate (only orphan ENIs remain on it).

Rollback of an S13 sub-step before S14: revert and apply (the caller returns to the old group, still allowed).
After S14 the old group must be re-added to the lists first.

## Consequences

- A compromised Booking or TripPlanner workload can no longer reach Redis or the CIS tasks; with X1's database
  roles and the S19 secret deny, the CIS runtime can no longer read Booking or TripPlanner data.
- Each new data store or caller needs an explicit list entry, which makes access reviewable in one file.
- Cost: security groups are free; the two placeholder secrets that ship in S11 add about $0.80/month.
- `modules/vpc`, `modules/ecs`, `modules/elasticache` and `modules/efs` gain optional variables whose defaults
  keep today's behaviour, so other callers of the modules are unaffected.
