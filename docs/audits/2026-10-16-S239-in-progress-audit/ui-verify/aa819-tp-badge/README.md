# AA-819 item 4: TripPlanner AI badge audit (S239, 2026-10-16)

Target: https://tripplanner.lumiguides.it.com (the Dev production domain, not a preview). The site is anonymous, so no login and no secrets were used.
Script: `.tmp-session/s239/aa819_tp_badge.mjs` (Playwright, headless Chromium). Raw output: `.tmp-session/s239/aa819_tp_badge_out.json`.
Frontend code read at AA-TripPlanner-Web `origin/main` 5e54856 (the local checkout was at 420d2e5; that diff touches no frontend files).

## Where the code renders AI text, and what draws the badge

| # | Block | Source of the text | Badge component and wording |
|---|---|---|---|
| A | Planner "Day-by-day narration" (`components/TripPanel.tsx` 519-582) | Assembly `POST /trip/{id}/narrate`, which returns `source` = `master` / `llm` / `mixed` / `basic` | An inline `<span>` in TripPanel.tsx 527-549: `AA ITINERARY` (master, tooltip "Straight from Adventure Asia's own tour itineraries"), `AA + AI` (mixed, "Mostly AA's own itinerary text, with AI filling any gaps"), `AI NARRATION` (llm, "Written by AI from the tour descriptions. Your advisor confirms every detail."). `basic` gets no badge. |
| B | Site-wide "AI-assisted" pill | — | `components/Header.tsx` 23-29 (planner) and `components/site/SiteHeader.tsx` 15-21 (home, tour, destination pages). Tooltip: "Suggestions, search and some narration are AI-assisted. An Adventure Asia advisor reviews every trip." |
| C | Home and tour TrustStrip | — | `components/site/TrustStrip.tsx` 5: "AI-assisted itineraries, reviewed by advisors / AI helps you explore; a person checks every trip." |
| D | Tour page summary, highlights and day bodies (`app/tours/[slug]/page.tsx` 200-248) | CIS `published_tours`, which holds the CIS S1 writer (LLM) output | No label on the block. Only B and C cover it. |
| E | Map popup `text_extract` (`components/DestinationPopup.tsx` 124) | CIS atom text | No label on the block. Checked in code only. |
| — | "You might also like" suggestions (`why` tooltip) | `backend/assembly/suggestions.py`: rule-based, no LLM | None needed. Note that the B tooltip still says suggestions are AI-assisted. |

Share, export and print paths in the code: **there are none**. No share link, no copy, print or PDF button, no `navigator.share` and no `mailto`. "Send to an advisor" (`sendToAdvisor`) sends only the trip and the customer. The narration and its `ai_generated` flag are not in the hand-off, because the backend `send-to-advisor` / events do not read the narration. The narration lives only in React state (`useTrip.tsx` 160-161) and is not stored in localStorage.

## What was opened

1. `/plan?tour=78c5f4b7…&source=a4966d23…` ("Delhi, Agra & Jaipur: Three Capitals in 2 Days"). The route prefill pinned 2 stops: Day 1 Fatehpur Sikri, Day 2 Amber Fort.
2. Clicked "✨ Compose" **once**. The response was `200`, `source=master`, `ai_generated=false`, `cached=false`, 2 days, 868 chars. Because every day resolved from master text, the backend made **no LLM call ($0)**. A route guard would have aborted any second narrate call; none was attempted (`narrate_calls_total=1`).
3. The same page (state kept, no new call) was shot at 1440 light, 1440 dark (OS dark plus a stored `tp_theme=dark`), 390 light ("Your trip" tab) and 390 dark.
4. Browser print media (`emulateMedia print`) at 1440.
5. Reload of `/plan`, to test whether the narration survives.
6. Home `/` and the tour page at 1440 and 390, light and dark (header pill).

| File | Viewport / theme | What it shows |
|---|---|---|
| 01-plan-1440-light-pinned.png | 1440 light | 2 stops pinned, before narration |
| 02-plan-1440-light.png + `-narration-block.png` | 1440 light | Narration with the `AA ITINERARY` badge |
| 03-plan-1440-dark.png + block | 1440 dark requested | Planner stays light (`data-theme=light`, by design per AA-812); badge visible |
| 04-plan-390-light.png + block | 390 light | Badge visible, no horizontal overflow |
| 05-plan-390-dark.png + block | 390 dark requested | Same as 04 (light pinned) |
| 06-plan-1440-print-media.png | 1440 print | Header pill and narration badge both still render |
| 07-plan-after-reload.png + block | 1440 light | Narration is gone after reload; "✨ Compose" is shown again; no badge |
| 10-home-{1440,390}-{light,dark}.png | 4 variants | `AI-ASSISTED` pill visible in all 4; dark applied (`data-theme=dark`) |
| 11-tour-{1440,390}-{light,dark}.png | 4 variants | `AI-ASSISTED` pill visible in all 4; the tour text has no block label |

Console: **0 errors** on every page. The planner showed only Mapbox WebGL "GPU stall due to ReadPixels" warnings, which come from the headless browser. Network: **0 responses ≥ 400**. No tokens are visible in any screenshot. The session id lives only in POST bodies and was not logged.

## Verdict per AI block

| Block | Badge present | Wording seen live | Verdict |
|---|---|---|---|
| A, source `master` | Yes, at all 4 viewport/theme variants and in print | `AA ITINERARY` | **PASS (badge shown), with defects D1, D2 and D3 below** |
| A, source `llm` / `mixed` | Not exercised live: this run returned `master` | Code: `AI NARRATION` / `AA + AI` | **Not verified live.** Needs a trip whose days lack master text, which costs one paid call. |
| A, source `basic` (budget spent) | No badge, by design (no AI text) | — | Code only |
| B, header pill | Yes: planner, home and tour at 1440/390, light and dark, print | `AI-ASSISTED` | PASS (see D5 for tooltip wording) |
| D, tour page catalog text | No block label | — | **GAP** (D4) |
| E, popup text_extract | No block label | — | GAP, code only |
| Share / export / print | No such path in the code. Browser print keeps both badges. | — | PASS: no path shows AI text without its badge |
| Persistence / hand-off | Narration is dropped on reload and not sent to the advisor | — | Info (D6) |

## Defects and gaps

- **D1, wrong-place narration (content).** In the TripPanel "Day-by-day narration", the Day 2 block reads "Khimsar to Jaisalmer 290-kilometer drive to Jaisalmer…" while the pinned Day 2 stop is **Amber Fort (Jaipur)**. The prefill pinned components whose source tours are other tours (the panel says: "North India: Delhi to Varanasi — 22 Days · tour day 16" and "Rajasthan: Forts, Havelis & Desert — 22 Days · tour day 5"). `master_content` takes that tour-day's authored text as-is under the `AA ITINERARY` badge. Screenshots 02, 04 and 05.
- **D2, "AA ITINERARY" is not AI-free (disclosure).** The tooltip says "Straight from Adventure Asia's own tour itineraries", and the handler sets `ai_generated=false` for `master`. But `published_tours.aa_itineraries` is CIS S1 writer output (AA-CIS-App `services/content_generation/graph.py` `_process_itineraries`: "the model's structured itineraries array"). So model-written (reviewed) text carries a non-AI label. A policy decision is needed on whether reviewed CIS text counts as "AA's own".
- **D3, title runs into body.** In the narration Day 1 block, "…Arrival in Agra A 2-3 hour private vehicle journey…". `parseNarration` joins the day title and the prose with no separator. Minor.
- **D4, no block-level label on AI-derived catalog text.** The tour page summary, highlights and "Day by day" bodies (`app/tours/[slug]/page.tsx` 200-248) and the map popup `text_extract` are covered only by the header pill and the TrustStrip.
- **D5, badge reachability and wording.** The badges are 9px `<span title>` elements. The tooltip text is unreachable on touch (390) and by keyboard (not focusable), so mobile users see only "AA ITINERARY" / "AI-ASSISTED". The header tooltip also says "Suggestions … are AI-assisted", but suggestions are rule-based (`suggestions.py`).
- **D6, info.** The narration is not persisted (lost on reload) and not part of the advisor hand-off, so the advisor never sees which text was AI-written. There is no share or export surface where a badge could be lost.
- Not a defect: the planner ignores dark mode on purpose (`RESTORE_THEME_SCRIPT` / `pinLightTheme`, AA-812). The dark shots at 1440 and 390 are therefore light.
- Seen in passing, out of scope: the tour page cover image showed the camera placeholder in all 4 shots (11-*).
