# Contract and ADR-number checks (AA-928)

Run by the root workflow [`.github/workflows/contracts.yml`](../../.github/workflows/contracts.yml) on every PR that
touches `docs/contracts/`, `docs/adr/`, these tools or the workflow.

| Tool | Checks | Level |
|---|---|---|
| `tools/contracts/check_contracts.py` | Every JSON Schema contract in `docs/contracts/` is valid 2020-12; every HTTP contract (`*.openapi.yaml`, OpenAPI 3.1) is well formed (local `$ref`, unique operationIds, declared path parameters and scopes, valid component schemas); every sample in `docs/contracts/samples/` validates (or is rejected) as it says; each contract's field policy (`POLICY`: `trip_count` / `revenue` / `pii:` banned in `crm.ops.v1`, `supplier_net` in `booking.b2b.v1`, no CRM role or email in `tenant.membership.v1`, no prices in `catalog.http.v1`); the rejected samples the design requires exist (`REQUIRED_NEGATIVES`); the contracts README lists every file | error |
| `tools/adr/check_adr_numbers.py` | ADR numbers in `docs/adr/`: no duplicate number or amendment letter, amendments have a base, reserved numbers unused, every reservation names its issue, the index's "Next free root numbers" line is exact. With `--base <ref>` (PRs): an added ADR takes a next-free number of the base (no reuse, no skipping), a reserved number only with the reserving issue cited in its header and the reservation removed, an amendment the next letter | error |

The field policy lives in the checker on purpose: loosening it is a reviewed code change, not an edit next to the
schema it guards. A new HTTP contract fails until it has a `POLICY` entry.

## Run locally

From the repo root:

```bash
python3 -m pip install -r tools/contracts/requirements.txt
python3 -m unittest discover -s tools/contracts -p 'test_*.py'
python3 -m unittest discover -s tools/adr -p 'test_*.py'
python3 tools/contracts/check_contracts.py
python3 tools/adr/check_adr_numbers.py --base origin/master
python3 tools/adr/check_adr_numbers.py --propose 0011
```

`check_adr_numbers.py` is stdlib only. It is separate from `tools/docs/check_adr_index.py` because the docs-lint tools
must stay byte-identical in four repos ([`tools/docs/README.md`](../docs/README.md)).
