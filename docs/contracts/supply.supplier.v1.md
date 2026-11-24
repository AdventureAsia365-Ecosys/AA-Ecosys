# supply.supplier.v1 — the identity of AA's suppliers (AA-Booking → AA-CIS-App)

AA-Booking owns the supplier list (root ADR 0004a decision 1): the companies AA buys from, with their contacts, legal
and payment details, contracts and rates. CIS content staff create tours by hand in the CIS content workspace and link
every source tour to the AA supplier it comes from (AA-1148); before, the supplier of a tour was only the free text of
the Excel cell. Booking publishes the identity of each supplier, nothing else, so CIS can show a picker and keep the
chosen id.

| | |
|---|---|
| View | `booking.v_supply_suppliers` (Booking migration `bk-073`, AA-1148), owner `bk_owner`, security barrier |
| Readers | role `cis_app` (the content workspace: the supplier picker, the "Supplier links" report and its name match): `SELECT` on the view + `USAGE` on schema `booking` (held since bk-017), nothing else of `booking.suppliers` (Infra `db/owners.yaml` consumer grant, isolation probe cell `consumer.contract_grants.bk-073`); role `booking` itself |
| Key | `id` (uuid), the value CIS stores as a soft key in `silver_aa_internal.raw_tours.supplier_id` (CIS 478; no foreign key across owners) |
| Rows | one per supplier, every status (`pending`, `active`, `inactive`): a reader shows what an old tour is linked to and offers only `active` / `pending` ones for a new link |

## Columns

| Column | Type | Meaning |
|---|---|---|
| `id` | uuid | the supplier |
| `code` | text | Booking's code (`SUP-000123`), for search |
| `company_name` | text | the company name AA uses (a business name, never a contact person) |
| `categories` | text[] | 1 to 7 of `hotel`, `transport`, `guide`, `entrance`, `activity`, `meal`, `dmc` (bk-073: a destination management company that runs whole programs) |
| `country_code` | text, null | ISO 3166-1 alpha-2 of the supplier |
| `status` | text | `pending` (waits for a second person), `active` or `inactive` |
| `updated_at` | timestamptz | the supplier row's last change |

## Rules

- **Never** a contact, the internal notes, the legal entity, the tax code, the payment terms, a bank account or a
  price: the view is the company's identity only.
- Columns are **append-only**; a change of meaning is `supply.supplier.v2` (a new view).
- A reader treats `UndefinedTable` / `InsufficientPrivilege` as "the supplier list is not available" (fail soft) and
  never links a tour it cannot check; it may ship before `bk-073` is applied.
- CIS keeps the sheet's text (`raw_tours.provider`) beside the link; Booking's `trip_plans.supplier_id` (the operating
  DMC of a sold tour) stays Booking's own field. Pre-filling it from the CIS link is a later, separate change.

## Versions

- **1.0** (AA-1148, `bk-073`): the columns above.
