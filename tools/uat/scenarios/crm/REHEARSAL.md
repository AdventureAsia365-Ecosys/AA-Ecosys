# CRM steps of the pilot rehearsal: agency setup and run order

The UAT scenarios `REH-02b` to `REH-10b` (this folder) run the CRM part of the pilot rehearsal (runbook
`docs/ops/runbooks/pilot-rehearsal.md`, steps 6, 7, 8 and 10) on the synthetic agency `pilot-rehearsal-01`
("E2E Pilot Rehearsal Travel", id `41ea21ee-77ee-5474-bd6d-aa738d2da990`). The pilot guard pins both rehearsal
identities to that agency.

## What the fresh seed lacks

The CRM seed (`python -m app.seed --apply --agency pilot-rehearsal-01 --member ...`) creates only the agency and its
owner and agent members. The later steps also need agency settings that the CRM review agency (Sen Vang) got by hand:

| Setting | Needed by | Without it | Who sets it |
|---|---|---|---|
| A manual payment method with bank-transfer instructions (Settings > Payments, "How clients pay you") | REH-08b step 3 (the client's pay details, `client-pay-details`) | The client page has no pay details (`payments/claims.py`: `pay_by` is null), so step 3 fails | Owner, in the UI: **REH-02b-agency-setup** |
| A published `booking_terms` agreement (Settings > Agreements) | REH-08 step 5 (the client accepts the terms with the proposal); REH-10 step 5 (`portal-doc-booking_terms`) | No terms to accept, and the signing envelope has no booking terms | Owner, in the UI: **REH-02b-agency-setup** |
| A published `waiver` agreement (Settings > Agreements) | REH-10 step 5 (`portal-waiver`) | The portal builds no signing envelope (`portal/public.py` `WAIVER_SQL`) | Owner, in the UI: **REH-02b-agency-setup** |
| No connected mailbox | Every step that mails the traveller | Nothing breaks. With a mailbox, mails go out through it. Without one they stay held (`no_sender`), and the links still show once in the UI | Leave it unconnected |
| The discount limit (Settings > Pricing) | REH-07 step 9 | Nothing: the agency keeps the registry default (`crm.agency_defaults.discount_owner_limit_pct`), and REH-07 reads the live limit from the builder | Nothing to do |
| The Booking partner link of the agency (`bk_tenant_pull`) and tour X in the CRM's AA catalogue | REH-06 step 5, REH-07 steps 5 and 6 | `GET /bff/aa/products/<X>` answers 404 `aa_product_not_found`, or has no `tour` row. `R.tourX` stops with that reason | Runbook step 1 (the CIS fixture) and the catalogue sync. Not an owner action |

`REH-02b-agency-setup` does the three owner rows in the UI and can be recorded. Run it once per fresh seed, before
REH-06. A second run reuses what is already there and writes nothing new.

## Hand-off from the other groups

Before REH-06, set these in the environment or in `tools/uat/work/rehearsal/handoff.json` (gitignored):

| Key (env / file) | What | Default |
|---|---|---|
| `UAT_REH_TOUR_X` / `tour_x` | The CIS source id of tour X (runbook "Tour X") | None: required |
| `UAT_REH_LEAD_NAME` / `lead_name` | The invented traveller name that the TripPlanner step 6 sent | None: required |
| `UAT_REH_TRAVELLER_EMAIL` / `traveller_email` | The invented address that the TripPlanner step 6 sent (same variable as the TripPlanner group) | `rehearsal.traveller@example.invalid` |

## Mail guard

Proposal send (REH-07b), the deposit's portal invites (REH-08b), the portal link (REH-08c), the acceptance (REH-08) and
the portal sign-in and signing codes (REH-10) mail the traveller. Before each of these clicks, `R.checkTraveller()`
stops the step unless all three checks pass:

- the hand-off address is on an invented domain: `*.invalid` (the runbook's `example.invalid`) or the E2E mailbox domain
  `e2e-mail.lumiguides.it.com`, whose mail lands only in the E2E S3 bucket;
- an exact e-mail search (`POST /bff/travelers/search`, a blind-index match, so the address is never revealed) for
  that address finds the trip's lead traveller;
- no other traveller of the trip has an address.

On the client host (REH-08, REH-10) the step requires the live check that an agency step already made for the same
trip (`work/rehearsal/crm.json` `traveller_check`).

## Run order

1. REH-02b-agency-setup (owner), once per fresh seed.
2. TripPlanner step 6 (the other group): the traveller sends the plan with a double click. Wait about a minute for
   `crm_tp_lead_pull`.
3. REH-06-lead (owner), REH-07-quote (agent), REH-07b-approve (owner), REH-08-accept (client phone), REH-08b-deposit
   (owner and client).
4. On-request departure only: the Booking group's step 8 (A10e staff confirms the case).
5. REH-08c-aa-confirmed (owner), REH-10-portal (traveller phone), then REH-10b-ops-view (`crm-staff`, read only,
   `bash tools/uat/run.sh scenarios/crm/reh-10b-ops-view.cjs`, after `crm_ops_release_sync`).

Write-set entries run by id: `node tools/uat/dryrun.cjs --record REH-02b-agency-setup --include-writable`. To check
only the read-only part, at no cost: `--preview --only <id>`.

## Write guards

Every writing scenario names the method and path of each write it may make (`allowWrites` entries such as
`POST ^https://…/bff/trips/<uuid>/owner(?:[?#]|$)`, `lib/net-guard.cjs` `parseAllow`), so an allowed create path never
lets a DELETE or PATCH of the same path through. In step 1 it also caps each write with `R.cap()`
(`lib/uat-page.cjs` `limitWrites`, any method), so a retry or a double click never creates, mails or deletes twice.
