# AA-1066 live check on Dev (CRM retail pricing)

- When: 2026-11-10, 09:19–09:26 UTC. Build: AA-Partner `main` 451e5011 (`/crm/health` git_sha 451e5011), schema crm-048.
- Where: `https://portal.lumiguides.it.com` (CRM web) and `https://go-dev.lumiguides.it.com` (the client's proposal page).
- Who: the e2e owner and the e2e agent of the synthetic agency "Lữ hành Sen Vàng" (partner pool, password and
  authenticator). Playwright 1.59.1, headless Chromium, desktop 1440x900, light theme, locale en-US (the agency shows EN (AU)).
- Data: synthetic only. Trip from the agency's synthetic web form (client "S275 AA-1066 check <run>",
  `@example.invalid` e-mail, 2 adults + 1 child aged 7), trip `ca9513f1`, proposal `701b7598`, trip dates
  5–8 Dec 2026.
- Set up through the BFF, not the UI: the inquiry, assigning the trip to the agent, trip dates, stage moves,
  creating the builder draft, the "Day tour" block, the AA tour option, and the send. The AA tour was added with
  the exact body the builder drawer sends (`BuilderAaDrawer.addAa`) and no `sell_amount`. The tour was picked by ID,
  so the drawer's search was not clicked through.

## Steps

| # | Step | Result | What was seen |
|---|------|--------|---------------|
| 1 | Owner: Settings > Pricing, add a season rule over the trip's dates | PASS | Added in the UI: "S275 AA-1066 check season +10%", Season 30 Nov–20 Dec 2026, +10 %, All AA products, adds up, priority 1. It is listed as "Season (service dates): 30 Nov 2026 to 20 Dec 2026 · All AA products · Adds up with other rules · 1". The API stores kind `season`, adjust 10, active. Shot `01`. |
| 2 | Agent: agency option with adult x2 / child x1 / single supplement x1 rows, sell = their sum | PASS | Added the item in the drawer (sell 500, net 300). "Prices per traveller" opened with adult and child rows filled from the party. Added "+ Single room supplement" and entered adult 2 x 200 (net 120), child 1 x 100 (net 60), single 1 x 50 (net 30). After saving, the row shows "sell 550.00 USD · Adult × 2 · Child × 1 · Single room × 1" and net 330.00 (the API agrees: sell 550.00, net 330.00). Shots `02a`, `02`. |
| 3 | AA tour added without a sell: sell = suggestion with the season rule, "Price rules used" shown | PASS | Tour "Tropical Jewels: Bohol, Dumaguete and Siquijor — 6 Days" (trip plan). The sell came out as 330.00 USD: AA's RRP 100 x party 3 = 300, plus 10 % = 330. The row shows "Suggested 330.00 USD · AA's suggested retail price · with S275 AA-1066 check season +10%" and "Price rules used: S275 AA-1066 check season +10%". Shot `02b`. |
| 4 | Agent: discount 15 % (above the 10 % limit) disables Publish with "The discount needs the owner's approval" | PASS | After "Save discount" with 15: the "Publish v1" button is disabled. The header shows the blocking check "The discount needs the owner's approval" and the totals "Before discount 880.00 · Discount 15%: −132.00 · Sell 748.00". The discount box shows "This discount needs the owner's approval before the proposal is published." The API view returns blocking `["discount_needs_approval"]`. A direct `POST /bff/proposals/<id>/publish` as the agent gets 409 `discount_needs_approval` (a probe I sent on purpose; the UI never sent it). Shots `03a`, `03b`. |
| 5 | Agent: "Ask the owner to approve" creates the owner's task | PASS | The message "The owner has a task to approve this discount." appeared, with "Waiting for the owner: 15% asked on 10 Nov 2026." The trip's tasks contain an urgent `discount_approval` task, created 09:25:36 and due one day later. It is assigned to the agency's first-created active owner (`a78e8cf1`), which is not the e2e owner who signed in (`b85c6b16`); see observation 1. Shot `03c`. |
| 6 | Owner approves on the builder page | PASS | The owner's builder page shows the pending request with "Approve" / "Reject" and the note "As the owner, publishing records your approval of this discount." Clicking "Approve" gave "Discount approved." and "The owner approved discounts up to 15% on this trip." The pending line went away, and the `discount_approval` task moved to done at 09:25:45. Shots `04a`, `04b`. |
| 7 | Publish then succeeds | PASS | In the agent's view the blocking checks were empty (publishable true) and "Publish v1" was enabled. The click published version 1: "Version 1 is published. Sending it to the client comes next." The totals stayed 880.00 / −132.00 / 748.00, deposit 224.40. Shots `05a`, `05b`. |
| 8 | Client page shows "Adult × 2 · Child × 1 · Single room × 1" and the discount line | PASS | After the send (200), the client page shows on the agency item "Adult × 2 · Child × 1 · Single room × 1" (no unit prices) and in the totals "Before discount 880.00 USD · Discount (15%) -132.00 USD · Total 748.00 USD · Deposit now 224.40 USD · Balance 523.60 USD". The public API `price_lines` has types and counts only. Shots `06a`, `06b`. |
| – | Owner publishing their own discount above the limit (approval recorded at publish) | NOT TESTED | The agent published this version after the owner approved. The owner-self-publish path was not run live. |

## Console errors and 4xx/5xx on `/bff/` and `/crm/`

- Owner session: no console errors, no 4xx/5xx.
- Client page: no console errors, no 4xx/5xx.
- Agent session: one `POST /bff/proposals/<id>/publish 409` and the matching browser console line. Both come from
  the deliberate API probe in step 4 (the expected `discount_needs_approval` refusal), not from the UI.

## Observations (no defects that block the feature)

1. The discount task goes to the agency's first-created active owner (`ORDER BY m.created_at LIMIT 1` in
   `app/proposals/discount.py`), so in an agency with several owners it can land with an owner other than the one who
   approves. Any owner's approval on the builder closes it (seen live). This matches the implementation note ("an
   urgent `discount_approval` task for the first active owner"); flag it only if the task should go to every owner or
   to the trip owner's lead.
2. Settings > Pricing: after "Save rule" the message reads "Pricing settings saved." (the age-bands message), not
   a rule-specific one. Cosmetic.
3. Settings > Pricing: the season "From" date box is a little wider than its grid column and touches the "To" box
   at 1440 px (shot `01`, bottom). Cosmetic.
4. Not AA-1066: the client page title is the trip title "Việt Nam, 3 đêm" (Vietnamese), set when the intake form
   created the trip, on an English page.

## Test data left on Dev (synthetic)

- Price rule "S275 AA-1066 check season +10%" (active, 30 Nov–20 Dec 2026, all AA products) on the Sen Vàng
  agency. It raises AA suggestions by 10 % for service dates in that window. Pause or delete it in Settings > Pricing if
  other checks need unadjusted suggestions.
- Trip `ca9513f1` (client "S275 AA-1066 check …", `@example.invalid`), stage Proposal, owned by the e2e agent;
  proposal version 1 published and sent; discount approval approved at 15 %. One duplicate AA option made by a rerun
  was deleted from the draft before publishing.

## Screenshots

`01-settings-pricing-rule.png`, `02a-builder-prices-editor.png`, `02-builder-per-traveller-rows.png`,
`02b-builder-aa-price-rules-used.png`, `03a-agent-publish-disabled.png`, `03b-agent-discount-needs-approval.png`,
`03c-agent-asked-owner.png`, `04a-owner-sees-pending.png`, `04b-owner-approved.png`, `05a-agent-publish-enabled.png`,
`05b-agent-published.png`, `06a-client-price-lines.png`, `06b-client-discount-line.png`. Each is under 125 KB. No
e-mail address, secret or link token appears in them; the client name and trip are synthetic.
