# AA-898 docs reader: local UI evidence (S255, 28/10/2026)

What these screenshots are: the `/admin/docs` page of the AA-CIS-App branch `feat/aa-898-admin-docs`, as a
production `next build` + `next start`, talking through its real BFF (`/api/admin/[...path]`) to a **local mock API**
that serves a bundle built by `tools/docs/build_docs_reader.py` from this repo (98 pages, 10 owner only, 55 values
redacted at the time). The mock signs the session in as a non-owner admin, like the Dev E2E CIS admin.

They are **not** live evidence: the backend routes and the S3 bundle are not deployed yet. After the CIS deploy, the
Infra apply and the first Docs sync run, the orchestrator retakes them with the E2E admin (`admin-evidence`).

| File | Shows |
|---|---|
| `docs-list-1440-{light,dark}.png`, `docs-list-390-{light,dark}.png` | The list: search, type and audience filters, pages grouped by folder |
| `docs-reader-1440-{light,dark}.png`, `docs-reader-390-{light,dark}.png` | A runbook rendered from Markdown: badges, catalog facts, table of contents, links between pages |
| `docs-catalog-table-390-light.png` | The catalog page (wide tables) at phone width |
| `docs-owner-page-hidden-390-light.png` | An owner-only page (`docs/legal/register.md`) opened by a non-owner admin: "Page not found" |

Checks from the same run (Playwright, all four viewport/theme pairs): no horizontal overflow of the document or of
the page frame (0 px at 1440 and 390, the table page included); 0 `script` / `iframe` / `img` elements inside the
rendered Markdown; the type filter narrows the list (22 ADRs of 88 pages); no failed `/api/admin/docs/*` call.

Known harness gaps: the sidebar nav is empty and the role chip says "Content" because the mock does not answer the
shell's identity calls; the console errors in that run (403 / 404) are those unanswered shell calls, not the docs page.
