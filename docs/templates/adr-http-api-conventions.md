# ADR NNNN — HTTP API conventions

<!-- Generic ADR template for a new project's HTTP API conventions (new-project playbook, phase 2 Architecture; the kit
gap "HTTP API conventions ADR unwritten"). Copy it to docs/adr/NNNN-http-api-conventions.md, adjust each decision to
the project, then propose it. The defaults below are common practice, not a standard; change any of them with a reason.
ADRs carry no front-matter and no translation. Delete this comment. -->

- **Status:** Proposed (<dd/mm/yyyy>).
- **Scope:** every HTTP API the project publishes, internal or external.
- **Amends / Supersedes:** none.

## Context

Clients, agents and contract tests need one predictable shape for URLs, versions, errors, lists and retries. Without it,
every endpoint invents its own and every client handles each one by hand.

## Decisions

### 1. URLs

- Prefix every route with the app and the major version: `/<app>/v1/...`. Health routes stay unversioned:
  `/health` (process up, returns the commit SHA) and `/health/ready` (dependencies reachable).
- Plural nouns for collections (`/v1/bookings`), the ID as the next segment (`/v1/bookings/{id}`), verbs only for
  actions that are not CRUD (`/v1/bookings/{id}:cancel` or `POST /v1/bookings/{id}/cancel`; pick one).
- JSON field names in `snake_case`; timestamps in ISO 8601 UTC; money as an integer of minor units plus a currency code.

### 2. Versions

- A breaking change (a removed or renamed field, a new required input, a changed meaning) ships as `/v2` beside `/v1`.
  `/v1` is served for at least 30 days after every known client has moved, then removed with a notice.
- Additive changes (a new optional field, a new endpoint) stay in the same version. Clients ignore unknown fields.
- The OpenAPI file is generated from the code and diffed in CI; a breaking diff on a published version fails the PR.

### 3. Errors

Every error uses the RFC 9457 problem details shape:

```json
{"type": "https://<docs>/errors/booking-closed", "title": "Booking closed", "status": 409, "detail": "...", "instance": "/v1/bookings/123", "code": "booking_closed", "request_id": "..."}
```

- `code` is a stable machine string; `detail` is safe to show and never holds a secret, a stack trace or another
  tenant's data. 4xx = the caller can fix it; 5xx = the server must.

### 4. Lists

- Cursor pagination: `?limit=50&cursor=<opaque>`; the response carries `items` and `next_cursor` (null at the end).
  `limit` has a maximum that is an admin-editable setting.
- Filters as query parameters with the field name; sort with `?sort=field` or `?sort=-field`.

### 5. Retries and idempotency

- Every `POST` that creates something or moves money accepts an `Idempotency-Key` header; the server stores the key
  with the first response for at least 24 hours and replays it for a repeat.
- `429` and `503` carry `Retry-After`. Clients retry with exponential back-off and jitter, at most a few times.

### 6. Auth and tenancy

- Bearer tokens; the tenant comes from the verified token, never from a path or body field the caller controls.
- Every route states its access tier in the code (public, user, staff, admin, machine).

## Consequences

- **Positive:** one client pattern, contract tests that mean something, clear errors for users and agents.
- **Negative / cost:** existing endpoints that differ need an expand / contract migration when they are touched.

## Follow-ups

- Add the OpenAPI diff check to CI. Write the error `type` pages. **Prune:** re-read when the first external client or
  public API launches.
