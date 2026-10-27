# Contract samples

Sample payloads for the HTTP contracts in [`docs/contracts/`](../README.md) (`*.openapi.yaml`) and for the JSON Schema
contracts added since AA-835 (`*.json`; the files that predate it have none). The root workflow
`contracts.yml` runs [`tools/contracts/check_contracts.py`](../../../tools/contracts/check_contracts.py) on every PR
that touches contracts, samples, the ADR folder or the checker.

One file per case, in the folder of its contract (`samples/<contract>/<case>.json`):

```json
{
  "contract": "crm.ops.v1",
  "schema": "UsageMeters",
  "expect": "invalid",
  "why": "L1 must never show how many trips an agency has",
  "rule": "trip_count",
  "payload": { "...": "..." }
}
```

- `schema` is a name under `components.schemas` of an HTTP contract. A JSON Schema contract sample has no `schema`:
  its folder is the file name without `.json` (`samples/inquiry.submitted.v1.4/`, `samples/supply.hotel.v1/`) and
  the payload is validated against the whole file.
- `expect: valid`: the payload must validate against the schema **and** pass the contract's field policy.
- `expect: invalid`: the schema or the field policy must reject it. With `rule`, the field policy itself must flag
  that rule (a forbidden key such as `trip_count`, `revenue`, `supplier_net`, `crm_role`; `pii:` for a `pii:`-tagged
  field; `pii-name` for a personal-data field name), so the check does not rest on `additionalProperties: false`
  alone.
- The rejected samples the designs require (AA-928: `crm.ops.v1` with `trip_count`, `revenue`, `pii:`;
  `booking.b2b.v1` with `supplier_net`; AA-682 S5: `booking.customer.v1` with `recorded_by`, `evidence_url`,
  `net_amount`, `supplier_id`, `notes`; AA-835: `supply.hotel.v1` and `supply.service.v1` with `net_amount`,
  `supplier_id`, `internal_notes`, `url`; AA-908: `inquiry.submitted.v1.4` with `access_token`) are listed in the
  checker (`REQUIRED_NEGATIVES`); deleting one fails CI.
- Samples use synthetic data only (`*.example` mail domains, made-up ids). Never paste real payloads.
