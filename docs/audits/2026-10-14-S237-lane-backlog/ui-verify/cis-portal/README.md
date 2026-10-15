# UI verify: S237 CIS tenant portal (15/10/2026)

This run was read-only. The only write was the tenant login POST. A Playwright route aborted every other
non-GET request, and `blocked_writes` in `results.json` is empty in every run, so the pages never tried a
write. Nothing was connected, disconnected, published or unpublished. "Test connection", "Test & Connect",
"Request Rewrite" and "Disconnect" were never clicked.

Tooling: Playwright (Chromium, headless), one browser at a time, a fresh non-persistent context per run.
Scripts are in `.tmp-session/s237/uiv/cis-portal/`.

## Targets

- Portal: `https://aa-cis.lumiguides.it.com`. The Vercel Production deployment is `35d305c5` (current
  `main`), and ECS Dev is also on `35d305c5`. That build includes PR #727, PR #730 and PR #731.
- Login: the tenant login page `/tenant-login` takes an API key and calls `POST /api/auth/tenant-login`,
  which sets httpOnly JWT cookies.
- Account: E2E tenant **atlas-hearth** (Atlas & Hearth, `9149d3c6-…`). Its API key comes from the secret
  `aa-cis/dev/e2e-tenant/atlas-hearth` (a plain string, not JSON). The key was read into process memory
  only and was never printed or written anywhere.
- Pages checked: `/portal/t11-publish`, `/portal/t11-publish/connection`, `/portal/t10-review`,
  `/portal/t4-pool` (My Catalog Tours) and `/portal/dashboard`.

### Tenant state (read-only probe of all 4 E2E tenants)

| Tenant | WordPress | Facebook | publish_log rows | Ready to Publish |
|---|---|---|---|---|
| atlas-hearth | not connected | not connected | 0 | 46 (3 unique titles) |
| terra-family | not connected | not connected | 0 | 46 (3 unique titles) |
| trail-pulse | not connected | not connected | 0 | 0 |
| wildkind-travel | not connected | not connected | 0 | 0 |

**No test tenant has a connected channel or a published post.** The connected-state card, the Disconnect
control and the Unpublish control only render in those states, so they cannot be seen on Dev without a write.

## Matrix (1440 / 390 × light / dark)

The portal is **pinned light by design**. The portal `T` tokens are hex values (see the `globals.css`
header), so the dark runs look the same as the light runs. `<html data-theme>` does switch to `dark`, and
the kit tables and drawers stay readable in it.

| Page | HTTP | Console errors | API non-2xx | Data | Overflow @390 | Leak scan | Screenshots |
|---|---|---|---|---|---|---|---|
| T11 Publish | 200 ×4 | 0 | none (`integrations/wordpress`, `integrations/facebook`, `publish-log`, `publish-log/pending` all 200) | WP + FB connect forms, 46 Ready-to-Publish cards, Published card shows its empty state | none | 0 hits | `t11-publish-*`, `t11-published-empty-*`, `t11-ready-cards-390-light` |
| T11 Connections | 200 ×4 | 0 | none | WordPress and Facebook Page sections, both showing the connect form | none | 0 hits | `t11-connection-*` |
| T10 My Content | 200 ×4 | 0 | none | 5 rows (`content-writing/reviews` total 5) | none | 0 hits (page and drawer) | `t10-review-*`, `t10-review-drawer*` |
| T4 My Catalog Tours | 200 ×4 | 1 in each run that opened the drawer | `GET /api/tenant/v1/tours/pool/caf4bf16-…` **404** `{"detail":"Not Found"}`, fired by the drawer (D4) | 3 tours | none | 0 hits (page and drawer) | `t4-pool-*`, `t4-pool-drawer*` |
| Dashboard | 200 ×4 | 0 | none (`quota`, `billing`, `brand-identity`, …) | real plan, quota and activity | none | 0 hits | `dashboard-*` |

The leak scan regex was `gate(s)|gated|ledger|F<nn>_*|held|hold reason|flag(s/ged)|QA|Jev|judge|authenticity|quality score|verdict|waived|testimonial`.
It ran over the rendered text of each page and of each opened drawer, and found no hits.

## Per issue

### AA-815 (PR #731): Facebook Page connect, unpublish, disconnect

| Item | Verdict | Evidence |
|---|---|---|
| Facebook connect option on Publish and on Connections | **PASS** | "Connect Facebook Page" card (Page ID, Page Access Token, Test & Connect) next to WordPress on `/portal/t11-publish` and in its own "Facebook Page" section on `/connection`. Seen at both widths and both themes. `GET /integrations/facebook` returns 200 `connected:false`. |
| Pending list gated per channel | **PASS** | All 46 cards show a disabled "Connect WordPress to publish" button. |
| "Published" card | **PASS** (empty state only) | `GET /publish-log` 200, total 0. The card shows "Nothing published yet" plus help text that mentions unpublishing (`t11-published-empty-*`). |
| Connected-channel state and the Disconnect control | **NOT VERIFIABLE** | No E2E tenant has a connected WordPress site or Facebook Page. The status card, "Manage connections" link and "Disconnect …" only render when connected, and connecting would be a write. Code read only (`FacebookStatusCard`, `DisconnectConnection`). |
| Unpublish control and its confirm dialog | **NOT VERIFIABLE** | `publish_log` is empty for all 4 tenants, so there is no Unpublish button. Producing one would need a connect plus a publish (writes). |
| Refusal to unpublish a post on a previously connected site or Page (422) | **NOT VERIFIABLE** | Backend behaviour that needs published posts and a changed connection. |

Overall AA-815: **NOT VERIFIABLE** for the parts the issue's Done-when needs (connect a test Page, publish,
unpublish). What can be seen without a write passes. A run with a test tenant that has a connected test
WordPress site or test Facebook Page and one published post is needed. Nghiệp has to approve that write.

### AA-819 (PRs #727, #730): AI notice and daily publish limit

| Item | Verdict | Evidence |
|---|---|---|
| AI notice at review, publish and export | **PASS** | The exact sentence "This content was generated with AI. Review it before publishing; you are responsible for what you publish." appears on T10 under the subtitle and in the piece drawer, on T11 in the Ready to Publish card, and on My Catalog under the tour count and in the drawer footer beside Export DOCX. The footer wraps on a phone (`t4-pool-drawer-notice-390-light.jpg`). Seen at both widths and both themes. The notice has no gate, score or flag wording. |
| A daily publish limit notice or quota where publishing happens | **NOT VERIFIABLE**, and not built as a visible notice | No page shows the limit up front: no "20/day" line, no publishes-left counter, and no limit hits on T11 or the Dashboard. The Dashboard shows only "Rate limit 300 RPM", which is the API rate. By design (PR #730) the limit only appears when a publish is refused: a 429 whose `detail` T11 shows verbatim in the card. Seeing it needs a 21st publish in one UTC day, which is a write, and atlas-hearth has no channel connected anyway. If the issue expects a visible quota line, it does not exist. |

### Product rule: the tenant sees content only

**PASS on the pages opened.** There are no gate, ledger, QA, held-reason or flag words on T11, Connections,
T10 (page and drawer), My Catalog (page and drawer) or the Dashboard. T11 lists `held` pieces among the
Ready-to-Publish cards (AA-770) without any held label. The status filter on T10 offers only Ready, Writing…
and Not ready.

## Defects

| # | Sev | Page | Description | Evidence |
|---|---|---|---|---|
| D1 | **Medium** | T11 Publish | "Ready to Publish" lists **46** pieces for atlas-hearth, but only 3 titles are unique (20 cards are "Where Two Worlds Meet…"). My Content lists 5 for the same tenant, and terra-family shows the same pattern. `GET /v1/publish-log/pending` returns every `approved`/`held` `content_piece` with no publish_log row, so earlier attempts or versions of the same piece all appear as publishable. A tenant could publish duplicates. This is probably pre-existing, not from #731. | `t11-published-empty-1440-light.jpg` (two "The Market as Cultural Decoder" cards with different text), `results.json › tenant_state_probe` |
| D2 | **Medium** | T11 Publish @390 | On a phone the Ready-to-Publish card content column shrinks to about 90 px beside the "Connect WordPress to publish" button. Titles wrap one word per line and the preview is cut to "A weaver…". The button does not stack under the content. | `t11-ready-cards-390-light.jpg`, `t11-published-empty-390-dark.jpg` |
| D3 | Low | T11 Publish | The Ready-to-Publish StickyBar's white background extends about 27 px above its card and covers the bottom border of the card above it (WordPress at 1440, Facebook at 390). The layout gap itself is 20 px. | `t11-publish-1440-light.jpg`, `t11-ready-cards-390-light.jpg`, `results.json › t11_geometry_1440` |
| D4 | Low | My Catalog drawer | Opening a tour fires `GET /api/tenant/v1/tours/pool/caf4bf16-…` → 404 `{"detail":"Not Found"}`, which logs a console error. It comes from the "See original content" source fetch. The drawer itself renders fine. This is probably pre-existing (#727 only added the notice). | `results.json › pages[t4-pool 1440/390 light].api_failed` |
| D5 | Low | Facebook connect card | "pages_manage_posts permission" renders with no space ("pages_manage_postspermission" in innerText and in the screenshot), although the JSX has one. | `t11-connection-1440-light.jpg` |
| D6 | Info | T11 Publish | Ready-to-Publish previews start with raw markdown (`## Title …`), and the T10 drawer shows the body as raw markdown. | `t10-review-drawer-1440-light.jpg` |

Capture note: to get whole-page shots, the run expanded the portal's inner scroll container. In the
`t11-connection-1440-*` and `dashboard-1440-*` shots the dark sidebar therefore stops at 900 px. That is a
capture artefact, not a page defect.

## Blocking Done

- **AA-815: cannot be marked Done from this run.** Its Done-when (connect a test Page, publish, unpublish)
  needs writes and a test channel, and no E2E tenant has one. What is visible without a write passes.
  D1 and D2 are on the same page and should be triaged, but neither comes from #731.
- **AA-819 (portal part): the AI notice passes everywhere.** No up-front daily-limit notice exists. The 429
  message is only visible on a refused publish, so it is not verified here. The other Done-when items (T9
  testimonial gate evidence, the 21st publish returning 429, the TripPlanner badge audit) are outside this
  UI run.

## Hygiene

- No password, API key or JWT is written in this folder. `results.json` was scanned for `eyJ…`, `Bearer`
  and key prefixes, with no matches. No browser profile or storageState was saved; contexts were in memory
  only.
- The browser was closed at the end of each script.
