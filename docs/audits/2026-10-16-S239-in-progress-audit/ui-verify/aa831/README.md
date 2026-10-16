# UI verify: AA-831 (Facebook Page connect guide), S239, 16/10/2026

- Target: Dev portal https://aa-cis.lumiguides.it.com, tenant **terra-family** (tenant-login with API key from Secrets Manager `aa-cis/dev/e2e-tenant/terra-family`; key not printed or saved).
- Tool: Playwright Chromium (headless). Scripts: `.tmp-session/s239/aa831_ui.mjs` (pass 1), `.tmp-session/s239/aa831_ui2.mjs` (pass 2: request attribution + full-length guide).
- Read-only: no form was submitted. Test & Connect was not clicked, and no Dev data was changed.
- Theme: `localStorage.cis_theme` + `prefers-color-scheme` emulation. `<html data-theme>` resolved to `dark` / `light` as requested.
- Redaction: nothing to redact. The token field shows only its placeholder `EAAB…`, and no real token appears in any screenshot.

## Pages opened

| Page | Viewports | Theme |
|---|---|---|
| Publish → Connections `/portal/t11-publish/connection` | 1440x900, 390x844 | dark, light |
| Guide `/portal/help/facebook` (reached by clicking "Step-by-step guide" on the card) | 1440x900, 390x844 | dark |

## Files

| File | What |
|---|---|
| `card-dark-1440.png`, `card-dark-390.png` | Full "Connect Facebook Page" card (element shot), including the guide link |
| `card-light-1440.png`, `card-light-390.png` | Same card, light theme |
| `connections-{dark,light}-{1440,390}-full.png` | Uncropped viewport of the Connections page with the card in view |
| `guide-dark-1440.png`, `guide-dark-390.png` | Guide page as rendered (viewport) after the click |
| `guide-dark-1440-fulllength.png`, `guide-dark-390-fulllength.png` | Whole guide. For this capture the inner `<main>` scroll container was unclipped locally, so the sidebar ends early in the 1440 image. That is a capture artifact, not a UI bug. |

## Results

| # | Check | 1440 dark | 390 dark | 1440 light | 390 light | Verdict |
|---|---|---|---|---|---|---|
| 1 | Card names all 3 permissions (`pages_show_list`, `pages_read_engagement`, `pages_manage_posts`) as separate chips with correct spacing. No "pages_manage_postspermission" glue. | yes | yes | yes | yes | PASS |
| 2 | Card states that the Meta app must be in **Live** mode (Development = only you see posts) | yes | yes | yes | yes | PASS |
| 3 | Card says the token must be a **long-lived** Page token | yes | yes | yes | yes | PASS |
| 4 | Card says where the Page ID is (About → Page transparency) | yes | yes | yes | yes | PASS |
| 5 | "Step-by-step guide" link present (`href=/portal/help/facebook`), exactly 1 | yes | yes | yes | yes | PASS |
| 6 | Click guide → `/portal/help/facebook` renders, h1 "Connect your Facebook Page" | yes | yes | n/a | n/a | PASS |
| 7 | No horizontal overflow on the guide. Document scrollWidth = clientWidth (1440/1440, 390/390); `<main>` 1204/1204 and 390/390; 0 elements past the viewport edge | yes | yes | n/a | n/a | PASS |
| 8 | No horizontal overflow on the Connections page (same measure) | yes | yes | yes | yes | PASS |
| 9 | Console errors (Connections + guide) | 0 | 0 | 0 | 0 | PASS (0 warnings too) |
| 10 | Failed API calls | 0 | 0 | 0 | 0 | PASS. See note A. |

Card text as rendered (identical in all 4 runs):

> Publish posts to your own Facebook Page. You need two things from Meta:
> - **Page ID** — the number under your Page's About → Page transparency.
> - **Page Access Token** — a long-lived Page token with the permissions `pages_show_list`, `pages_read_engagement` and `pages_manage_posts`.
>
> Your Meta app must be in **Live** mode. While it is in Development mode, only you can see the posts.
> Step-by-step guide →

Guide content vs. AA-831 scope item 2:
- 7 steps in the requested order: Meta app → privacy policy + Live → User token with 3 permissions → long-lived token → Page token → Page ID → Test & Connect.
- "Common problems" covers 5 cases: invalid/expired token, Page not found, missing permission, User token pasted instead of Page token, and posts visible only to app roles.

All three error cases required by the scope are covered.

Network (pass 2, every `/api/` request logged with the page it came from):
- Connections page: `GET /api/tenant/v1/integrations/facebook`, `/integrations/wordpress`, `/tenant/me`, `/v1/billing`, `/v1/tours/pool`, `/v1/tours/my-versions`. All returned 200.
- Guide: client-side navigation, 0 API calls.

## Notes / findings

- **A. Pass-1 `net::ERR_ABORTED` (not a defect).** Pass 1 logged 4 aborted GETs (`/tenant/me`, `/v1/billing`, `/v1/tours/pool`, `/v1/tours/my-versions`). Pass 2 shows they come from `/portal/dashboard`. The script navigated away from the dashboard before its fetches finished, so they were test artifacts. When the dashboard is allowed to settle, all of them return 200.
- **B. Dark theme does not apply to the portal (by design).** `<html data-theme="dark">` and the body background (rgb(15,20,27)) do switch. But `app/(tenant)/portal/layout.tsx:150` pins `data-theme="light"` on the portal wrapper (see the globals.css comment), so the card and guide render light in "dark" mode. The card background is rgb(255,255,255) in both themes. The dark screenshots therefore look the same as the light ones. No dark-on-dark or contrast issue was seen, and no dark background leaks into the visible viewport.
- **C. Gap vs. Linear scope (content).** AA-831 scope item 2 asks for the guide "with screenshots from the Live-mode run". The guide has no step screenshots. The only `<img>` is the Adventure Asia logo, and it loads OK. The text is complete, but the screenshots are missing.
- **D. Cosmetic, 390 only.** The top-bar breadcrumb on the guide page is clipped at "Connect your Facebook Pag" next to the bell icon, with no visible ellipsis (`guide-dark-390.png`, top bar). It causes no overflow. Minor.
- Not in scope here: the planner-generated facebook piece through T11 (scope item 3) and the PR-7 Jira reply (scope item 4).

## Verdict

**PASS** for the card text (3 permissions, Live mode, long-lived token, Page ID, guide link) at 1440 and 390, light and dark. **PASS** for the guide render: no overflow, 0 console errors, 0 failed API calls.

Two content gaps remain open: C (no screenshots in the guide) and D (cosmetic breadcrumb clip at 390). "Dark" screenshots show the portal's pinned light theme (B).
