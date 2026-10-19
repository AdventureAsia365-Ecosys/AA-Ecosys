# CIS investigations kept in the private root repo

These five investigations were written in the AA-CIS-App working tree but never committed, because
`docs/` was ignored there. AA-889 (S243, 19/10/2026) starts tracking CIS `docs/**/*.md`; AA-CIS-App is a
**public** repo, so pages that describe security gaps, authentication internals, secret names or
infrastructure details live here instead (data standards DM-6.10, S241 D-14/D-25). They are journals:
true on the date they were written, not current truth. Copied unchanged; the local copies in AA-CIS-App
can be deleted once this folder is merged.

| File | Written (file date) | Why it is here |
|---|---|---|
| `AA-432-per-tenant-api-key-feasibility.md` | 22/08/2026 | Tenant API-key storage and verification internals |
| `AA-543-platform-wide-design-investigation.md` | 06/09/2026 | Describes the CIS runtime role and how RLS was bypassed at that time |
| `AA-544-seo-context-rls-gap-investigation.md` | 10/09/2026 | Scope of a tenant-isolation (RLS) gap, with private network addresses |
| `aa-social-media-audit.md` | 04/09/2026 | Admin-secret paths without a tenant filter, token-forging attempts |
| `llm-otel-tracing.md` | 15/10/2026 | Secret names, account id, which monitoring is off (AA-842) |

Scan before copying (S243): gitleaks 8.28.0 with the AA-CIS-Infra rules found no secret in any of them.
