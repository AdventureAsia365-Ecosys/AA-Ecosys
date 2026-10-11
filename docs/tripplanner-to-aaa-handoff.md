# Spec (draft) — TripPlanner → AA-Booking (AAA) handoff

> **Status:** G0 draft, **no AAA code yet**. Waiting for the **AA-Booking (AAA)** repo/product.
> Updated 11/10/2026 (S225, AA-654 — translated to English; transport and data placement now follow
> ADR 0001). **[FACT]** = verified in current TripPlanner code; **[TODO-AAA]** = depends on AAA, not
> settled; **[TO CONFIRM]** = an assumption Nghiệp has to approve.
> AAA sources: `apps/AA-TripPlanner-Web/docs/AAA/` — `Adventure Asia PRD and Technical Spec Doc [Final].pdf`,
> `AA ERD.pdf`, `AAA_Quanskill_Handover_Review.docx`, `figma_AAA/` (screens). They are binary files;
> this spec cites them as sources but does not extract their details yet.

## 1. Context and goal

- **TripPlanner** [FACT]: B2C map-first web app. An anonymous guest browses destinations, pins
  components (place + activity), assembles a day-by-day itinerary, then **"Send to advisor"** and leaves
  contact details. The TripPlanner flow ends with a **draft trip + customer record**, not a booking.
- **AA-Booking (AAA)** [TODO-AAA]: Adventure Asia's operations system (admin: activity / hotel / supplier /
  trip, audit log — per `figma_AAA/`) where an advisor **receives the draft**, advises, confirms and
  manages the booking.
- **Handoff point:** a draft trip created by the guest in TripPlanner → handled by an advisor in AAA.
  This spec describes that boundary.

## 2. Current state of the handoff (TripPlanner side) [FACT]

Source: `apps/AA-TripPlanner-Web/docs/architecture-overview.md`,
`backend/assembly/{handler,registration,notify,events}.py`.

- `send-to-advisor` is a route in Lambda B (assembly), next to add / remove / reorder / narrate.
- It is **idempotent** (AA-731): one transaction serialized per trip by
  `pg_advisory_xact_lock(hashtext('tp_send:<trip_id>'))`. If the trip's latest event is already `sent`, the
  call returns that handoff (`handoff_id`, `already_sent: true`) without a second event or email. Sending
  again after a real edit is a new handoff by design.
- `registration.py`: dedupes the customer by **phone / email** and claims the session for that customer.
- `notify.py`: the advisor notification is still a **logging stub** — real email (SES + verified domain)
  is deferred; `ADVISOR_NOTIFY_EMAIL` still defaults to a test address.
- Draft data lives in schema `tripplanner`: `trip_events` (append-only), `trip_drafts` (projection),
  `customers`, `sessions`, `itinerary_components`.

→ **Conclusion:** TripPlanner already produces the output (draft + customer) but has **no real channel**
to AAA yet; it stops at the logging stub. That channel is what this spec defines.

## 3. Handoff interface

### 3.1 Transport — decided by ADR 0001 (28/09/2026) [FACT]

AA-Booking shares the acc2 RDS with its own schema `booking` (ADR 0001 decision 6). The transport is a
**transactional outbox**:

- TripPlanner writes an `inquiry.submitted` event into an outbox table in its own schema, **in the same
  transaction** as the `sent` event (so a handoff is never lost or duplicated).
- AA-Booking's job runner consumes the outbox and creates the Trip Case, using the event's
  **idempotency key** so one draft never creates two leads.
- Neither app writes the other's schema; AA-Booking reads the outbox through a granted view.
- **Placement (decided S225, AA-676):** `tripplanner.outbox` (append-only), read by AA-Booking
  through `tripplanner.v_inquiry_outbox` (migration tp-008).

The earlier options — A: push webhook, B: AAA reads `tripplanner.trip_drafts` directly, C: SNS/SQS/
EventBridge — are superseded: B blurs ownership, and A/C add an endpoint or infrastructure that the
shared database makes unnecessary.

### 3.2 Payload — `inquiry.submitted` v1 (draft) [TODO-AAA]

Normative schema: [`contracts/inquiry.submitted.v1.json`](contracts/inquiry.submitted.v1.json) (AA-676). The sketch below predates it;
when they differ, the JSON Schema wins (v1 has no narration; consent carries `consent_at`; legs carry `position`).

```jsonc
{
  "contract": "inquiry.submitted",
  "version": 1,
  "idempotency_key": "string",      // e.g. <trip_id>:<handoff_id>
  "source": "tripplanner",
  "trip_id": "uuid",
  "handoff_id": "uuid",             // the `sent` event in trip_events
  "created_at": "iso8601",
  "customer": {                     // from customers (deduped by phone/email)
    "name": "string",
    "phone": "string|null",
    "email": "string|null",
    "consent": true                 // [TO CONFIRM] contact-consent mechanism
  },
  "itinerary": {
    "legs": [                       // ADR 0001 decision 5: chain of legs over real AA tours
      { "tour_id": "string", "from_day": 1, "to_day": 3 }
    ],
    "days": [
      {
        "day": 1,
        "components": [
          {
            "component_id": "uuid",       // tripplanner.itinerary_components
            "place": "string",
            "activity": "string",
            "country": "string",
            "lat": 0.0, "lng": 0.0,       // [FACT] geocoded, may be slightly off
            "source_tour_atom": "string|null" // trace to acp_contract.v_active_tour_atoms
          }
        ]
      }
    ],
    "narration": "string|null"      // AI compose / renarrate text, if any (grounded, AA-731)
  }
}
```

### 3.3 Data mapping TripPlanner ↔ AAA [TODO-AAA]

| TripPlanner | AAA (expected, per `AA ERD.pdf`) | Notes |
|---|---|---|
| `customers` | AAA Customer / Lead | AA-Booking owns the customer identity (OTP, ADR 0001); agree on the identity key used to match TripPlanner's phone/email dedupe |
| `trip_drafts` + legs | Trip Case / enquiry | Initial state in AAA's booking pipeline |
| `itinerary_components` | AAA Activity / Destination | **[TO CONFIRM]** whether a TripPlanner component (from a tour atom) maps 1-1 to an AAA "Activity" |
| `shared.destinations` | Destination golden record | Owned by CIS (ADR 0002); both apps read it |
| tours, photos | `catalog.tour.*` from CIS, `shared.v_tour_photos` | AA-Booking catalog sync (AA-679) |

## 4. Ownership

- **TripPlanner owns:** guest session, draft, customer capture, narration, the outbox rows it writes. No
  booking or payment.
- **AAA owns:** advisor workflow, booking lifecycle, customer identity, supplier / hotel / activity
  master data, audit log; schema `booking` (version key `bk-NNN`).
- **CIS owns:** tours, atoms, places (`shared.destinations`), photos — content is written only by CIS
  (ADR 0002).
- **Shared:** the acc2 RDS (separate schemas). Any infrastructure for AAA (ECS service, ECR, DB role, API
  route) is Terraform in `AA-CIS-Infra` — "apps own code, Infra owns resources". Schema owners:
  `docs/database/schema-ownership.md`.

## 5. Security / auth [TODO-AAA]

- TripPlanner uses an **edge shared secret** (`X-TripPlanner-Key`) between the BFF and the Lambdas [FACT].
- With an outbox there is no service-to-service HTTP call; access is a DB grant: the AA-Booking role gets
  `SELECT` on the outbox view only (and an ack/cursor in its own schema). **[TO CONFIRM]** exact grant
  shape.
- Customer PII (phone / email) crossing the boundary must follow contact consent — **[TO CONFIRM]**.

## 6. Open items (waiting on AA-Booking)

- [x] Outbox table + view in `tripplanner` (tp-008) and the `inquiry.submitted` row written in the
      send-to-advisor transaction (AA-676).
- [x] `inquiry.submitted` v1 published in `docs/contracts/` — [ ] **[TODO-AAA]** agree on it with AAA.
- [ ] **[TODO-AAA]** Detailed entity mapping from `AA ERD.pdf` (read the ERD when AAA starts).
- [ ] **[TODO-AAA]** Replace the `notify.py` stub (real advisor email, or AAA's own notification).
- [ ] **[TO CONFIRM]** Consent mechanism and PII handling across the boundary.
- [ ] **[TODO-AAA]** Create repo `AA-Booking` in org `AdventureAsia365-Ecosys` and add it to the
      architecture table.

## 7. Out of scope

- Booking lifecycle, payment, supplier management (AAA).
- Auto-refresh of extraction when new tours arrive (tracked in TripPlanner's deferred list; the place
  pipeline moves to CIS under AA-712).
- Advisor UI details on the AAA side (see `figma_AAA/`).

## 8. References

- `docs/adr/0001-ecosystem-target-architecture.md` — decisions 5 (legs), 6 (contracts, outbox), 7 (IaC).
- `docs/adr/0002-only-cis-writes-content.md` — content write rule.
- `apps/AA-TripPlanner-Web/docs/architecture-overview.md` — TripPlanner architecture.
- `apps/AA-TripPlanner-Web/backend/assembly/{handler,registration,notify,events}.py` — current handoff code.
- `apps/AA-TripPlanner-Web/docs/AAA/*` — AAA PRD, ERD, handover review, Figma screens.
- `docs/ecosystem-architecture.md` — ecosystem architecture.
