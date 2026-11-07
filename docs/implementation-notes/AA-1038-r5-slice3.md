# AA-1038 R5 slice 3 — leads, brand and the per-tenant AI cap (root repo part)

Session S272 (lane l10). Root ADR 0019 d10, d11, d2 / b19.

## Decisions

- `lead.submitted.v1` is an **HTTP contract** (OpenAPI 3.1, rule 8 of `docs/contracts/README.md`): the CRM has no grant
  on another schema (ADR 0008a), so it pulls its agency's leads from TripPlanner and acknowledges each one. The same
  `LeadSubmitted` component is the signed webhook body and the e-mail content, so one schema covers every channel.
- Minimal traveller data: name, e-mail, optional phone (`x-pii: contact`), optional start date and message
  (`x-pii: travel`), party counts and ages, the trip draft summary (AA tour keys and titles, stops per day), budget band
  and the contact consent (a lead never exists without it). Field policy: no session, token, IP, user agent or price
  (`tools/contracts/check_contracts.py` POLICY + three required rejected samples).
- `tenant.entitlements.v1` 1.5 documents the CIS 390 view parts (lead route columns, `catalog.v_tenant_ai_budget_v1`).
- ADR 0019 d11 amendment (S272) records the transport choice, the 7-day hold and the per-tenant AI cap.

## Changed

- `docs/contracts/lead.submitted.v1.openapi.yaml`, `docs/contracts/samples/lead.submitted.v1/` (5 valid, 6 rejected),
  `docs/contracts/README.md` (registry rows), `docs/contracts/samples/README.md`, `tools/contracts/check_contracts.py`.
- `docs/contracts/tenant.entitlements.v1.openapi.yaml` 1.5 (byte copy in AA-CIS-App, its sha256 pin updated there).
- `docs/adr/0019-b2b-only-ecosystem-model.md` (d11 amendment), `docs/architecture/data-standards/02-data-management.md`
  (DM-7.1 rows of `tripplanner.outbox` and `shared.tenant_tripplanner_site`), `docs/architecture/erd/design/tripplanner.md`
  (tp-026 columns).

- Review fix pass (S272): `Traveller.phone` pinned to E.164 with its country code (pattern + the rejected sample
  `local-phone-invalid.json`), because the CRM normalises a phone without a region and dropped local numbers; the
  CRM also keeps a phone it cannot normalise as text. The contract now says a channel the deployment cannot hand over
  on (the CRM pull switched off, no key, no sender) is refused with 503 and nothing stored, and that an expired
  undelivered lead is reported, not only redacted.

## Tradeoffs

- No separate retention row: tp-026 adds columns to `tripplanner.outbox`, CIS 390 to `shared.tenant_tripplanner_site`;
  both rows are updated in place.

## Should know

- Merge this PR before the Infra bot copy PRs of tp-026 and CIS 390 (DM-7.1 text, ERD design page drift check).
