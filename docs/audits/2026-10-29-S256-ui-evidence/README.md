# S256 live UI evidence (29/10/2026, 08:10–08:25 +07)

Agent-run Playwright (headless Chromium, one run at a time, light theme) against the live Dev hosts. Read-only: no
rewrite, save or other write was sent. Identities:

- **CIS admin** `https://aa-cis.lumiguides.it.com`: the Dev-only E2E CIS admin (Cognito managed login, email code read
  from the `inbound-admin/` mailbox prefix with the MFA admin profile). Header shows "E2E CIS admin".
- **Tenant portal** `https://portal.lumiguides.it.com`: the partner-pool e2e studio user (password + authenticator, read
  at run time from Secrets Manager `crm/dev/e2e-test-studio/viewer`; studio role is now **owner**), tenant Atlas & Hearth.

Console errors = `console.error` on the app origin. Failing requests = any response ≥ 400 on the app origin (CIS: every
host except the managed-login host). Raw per-step records: [`data/`](data/).

| # | Page | What it proves | Console errors | Failing requests | Screenshots |
|---|---|---|---|---|---|
| 1 | Portal Marketplace `/portal/tours` (AA-671) | Grid loads 892 tours; **Activity filter** "Trekking & hiking" narrows to 454; filters Country = China + Activity = "Culture & heritage" → 105 matches, 14 of the first 24 cards show a **cover photo** (14 of 14 images loaded, CIS photo route answers 200 `image/webp`); the **detail drawer** opens with cover, chips, summary, highlights, itinerary and the rewrite footer; 390 px has no sideways scroll (scrollWidth 390 = innerWidth 390) | 0 | 0 | 1440: `01a` grid, `01b` activity filter, `01c` full, `01d` drawer, `01h` covers + filters, `01i` full, `01j` drawer with cover · 390: `01e` drawer, `01f` filter, `01g` grid, `01k` drawer with cover, `01l` grid with cover |
| 2 | Portal Brand Identity `/portal/brand` | Page loads; all 7 `/api/` calls 2xx, including `POST /api/tenant/v1/content-writing/cta-check` → **200** | 0 | 0 | `02a` 1440, `02b` 1440 full |
| 3a | CIS admin Docs `?path=docs/architecture/diagrams/README.md` (AA-697) | The bundle was published from AA-Ecosys@72c17e14 (root #315); the page shows the new AWS-standard diagrams; all 6 SVG assets load (natural sizes 3245–4919 px wide) | 0 | 0 | `03a` viewport, `03b` ecosystem diagram, `03c` full page |
| 3b | CIS admin Docs `?path=docs/ecosystem-architecture.md` (Mermaid, AA-898 follow-up) | The Mermaid diagram renders (1 on the page). **Labels are still broken mid-word** (see finding F1) | 0 | 0 | `03d` 1440, `03e` close-up |
| 4 | CIS admin Content Quality → Tour versions (T2) → drawer (AA-795) | Latest version (Pikey Peak Trek, Terra Family Expeditions v1, written 29 Oct 01:45) shows the **Judge breakdown** section: score set by `brand_fit`, draft 2, per-criterion scores (brand fit 6, cross-brand distinctness 6, mission present "no (caps at 6)", judge 6, structure 10, stored 6), the judge note, brand claims 0, flagged sentences 0, cost by stage | 0 | 0 | `04b` 1440 viewport, `04c` 1440 tall |
| 5 | CIS admin Cost Operations → DataForSEO, window 2026-09-20 → 2026-09-30 (AA-665) | The **recorded incident card** for 25/09: "DataForSEO research sweep after a tenant rewrite (balance exhausted)", 12:00 → 18:00, DataForSEO $49.02 (1,169 calls), LLM same run $10.27 (7,856 calls, `a3_search_demand`), first/last paid call 12:05 / 15:51, per-endpoint split, trigger / scope / failure point / cause / changed-since | 0 | 0 | `05a` 1440, `05b` card, `05c` full |
| 7a | CIS admin Overview `/admin/overview`, default language (AA-994, CIS #1129; production deployment = `f80429a9`, which includes `3994a1a8`; run 09:20 +07) | Fresh sign-in, no `cis_lang` cookie: the topbar shows the **EN \| VI** switch (EN pressed); `<html lang="en">`; every label is English ("Apps health — last 24 hours", "Requests", "Refresh") | 0 | 0 | `07a` 1440 |
| 7b | Same page after clicking **VI** | `<html lang="vi">`, VI pressed, cookie `cis_lang=vi`; heading "Tổng quan", nav "Nhân sự / Nhật ký kiểm tra / Vận hành chi phí", cards "Sức khoẻ ứng dụng — 24 giờ qua", "Yêu cầu / Lỗi / Tốc độ". API text stays English as the PR intends (for example "Health check passes and traffic looks normal") | 0 | 0 | `07b` 1440 |
| 7c | Review Queue `/admin/review` and Jobs `/admin/jobs` in VI, then back to EN | Review Queue: "Hàng chờ duyệt", columns "Quốc gia / Phiên bản / Ngày viết / Điểm / Lý do / Thao tác", buttons "Từ chối / Duyệt", dates "11 thg 10, 2026"; Jobs: tabs "Job / Hàng đợi & worker / Loại job", status chips "ĐANG CHỜ / THÀNH CÔNG / LỖI / ĐÃ HUỶ", columns "Loại / Trạng thái / Lần chạy / Tiến độ / Thời lượng / Chi phí". `<html lang="vi">` on both. Clicking **EN** brings back "Jobs / Queue & workers / Kind / Status" and `lang="en"`; this also clears the cookie, and the page stays English after a reload | 0 | 0 | `07c` 1440 (Jobs, VI) |
| 7d | CIS admin Docs `?path=docs/ecosystem-architecture.md` (Mermaid, CIS #1128) | **F1 fixed:** all 28 labels (nodes, clusters and edge labels) break only at spaces, never inside a word. For example "ECS Fargate: \| aa-booking-dev-api", "Lambdas: \| aa-tripplanner-dev-browse + \| assembly", "acc3: AA3-Bedrock-Invoker" and "AA-TripPlanner-Web" each stay whole. The check reads the SVG `<tspan>` lines (`data/cis-run3.json`) | 0 | 0 | `07d` 1440 |

## Findings

- **F1 — Mermaid labels still break mid-word (AA-898 follow-up; CIS #1115 merged, its deploy not re-checked here).** On
  `docs/ecosystem-architecture.md` long tokens without spaces wrap inside the token: `AA-TripPlanne|r-Web`,
  `aa-cis-dev-ap|i + worker`, `aa-crm-dev-a|pi`, `aa-booking-d|ev-api`, `AA3-Bedrock-I|nvoker` (`03e`; shot after
  `document.fonts.ready` plus 1.5 s). Every broken label is one hyphenated token longer than the node width, which
  points at the label wrap width rather than font timing: Mermaid splits a single word that does not fit, character by
  character. The diagram renders SVG `<text>` labels (no
  `foreignObject`), so the automatic overflow check in `data/cis-run*.json` reports 0 — the evidence is the close-up.
  Fix options: a larger `flowchart.wrappingWidth` in the reader's Mermaid config, or break the source labels at `-`
  / add `<br>` in the diagram text.
- **F2 — cover photos are sparse (AA-671).** 162 of 892 pool tours carry a cover URL (China 69, Taiwan 30, Bhutan 29,
  Mongolia 16, South Korea 16, Sri Lanka 2; `data/portal-pool-covers.json`). The default "newest first" grid and the
  Trekking filter show placeholders on every first-page card (`01a`, `01b`), so a cover only appears with filters such
  as China (`01h`). The UI is correct (placeholder, never a broken image); coverage is a data gap.
- **F3 — viewer CTA check not exercised.** The cta-check call is 200, but the e2e studio user is now **owner**, so the
  viewer path of the bug (403 on cta-check for a viewer) was not tested here. No Partner PR with the viewer fix is
  merged yet (latest Partner `main`: #115 `a6d6f28`); recheck with a viewer studio user after that fix deploys.
- **Minor:** the drawer price chip on a multi-tier price starts with a stray `·` (`01k`, "· 2-5 Traveller : …").
- **Transient:** one sign-in attempt at ~08:19 got `503 Service Temporarily Unavailable` from the portal host; it
  answered normally seconds later (CRM web / api services steady, rollout COMPLETED) and the rerun passed.

## Not covered

Dark theme and 390 px for the CIS admin pages (not asked); the viewer role on the portal (F3).
