# S238 — Rà soát backlog (15/10/2026)
**Tác nhân:** Claude Code (workflow 41 agent, Ultracode, tối đa 3 agent song song). Chỉ đọc repo/Linear/Jira; ghi Linear do phiên chính làm.
**Phạm vi:** 69 issue mở (35 In Progress + 34 Backlog) + bộ tiêu chuẩn dữ liệu v1.0 (artifact R1YLp4i1QCt3kjnKd6yvvJ) + log S233–S237 + ui-verify S237 + code/ADR/CONTEXT + Jira PR/KAN/CON.
**Phương pháp:** 6 cụm audit issue (đối chiếu Done-when với git/code/audit) + 4 hướng quét việc sót (standards, log+UI verify, code/ADR, Jira) → gộp trùng (40 → 29) → mỗi gap 1 agent phản biện (tìm Linear kể cả Done/Canceled, kiểm code) → tổng hợp thứ tự.
Kết quả thô đầy đủ: `backlog_audit.json`.

## Kết quả
- Phân loại 69 issue: not_started 23, mostly_done 21, partially_done 15, stale_rethink 5, blocked 2, done_not_closed 2, superseded_or_duplicate 1.
- 29 gap → 10 issue mới (AA-830…AA-839), 17 gộp vào issue có sẵn (comment "Scope addition" trên AA-817, 806, 751, 825, 807, 802, 712×3, 708, 683, 741, 813, 829, 804, 828), 2 không cần (Jev DPA — T-axis đã tắt; dọn Jira — đã có bước 4b cuối phiên).
- Đổi trạng thái (có bằng chứng / theo quyết định cũ của Nghiệp): AA-634, AA-709 → Done; AA-696, AA-699 → Canceled (T-axis Jev tắt từ S234); AA-708 → In Progress; bỏ blockedBy AA-662 (Done) khỏi AA-668, AA-671.
- Gap "throttle" (AA-833): gốc đã sửa trong phiên bằng CIS migration 235 (#746, Infra #132); issue còn lại là chỉnh alarm + prefetch.

## Đề xuất đổi trạng thái chờ Nghiệp quyết
- **AA-701** → Re-scope to dead-code chore; Canceled once merged: observe_t10 has been off since S234 (2,290 answers, 100% grey). The remaining work is removing service.py:1523-1528, jev_observe.py and facts.select_relevant_facts.
- **AA-751** → Re-scope to roadmap X6 (per-owner job tables) and move to the Data Platform project: docs/adr/0003a-per-owner-job-tables.md decision 8 says the original premise is superseded. Data-standards open item #4 recommends a re-scope. Booking deploy-dev.yml:16 still says 'No job guard', even though booking.job exists.
- **AA-768** → Done (umbrella), if Nghiệp accepts S235 r5 as evidence: r5 result: 16/20 approved, 0 F1 holds; all 4 holds are F9_cta_fact, which AA-777 owns. Scope items 1-3 shipped across #665..#715. Since AA-770, a hold is an admin-only label.
- **AA-771** → Done; move Done-when 3 (LinkedIn brand_voice ≥7) to AA-800/AA-790: Criteria 1 and 2 are met: the F9 rubric head is the tenant brand, and grep finds AA/premium only in code comments. Criterion 3 (6.32 mean in r5) depends on AA-800 and AA-790.
- **AA-678** → Done: Repo, CI, ECS and health are live through bk-010. The deploy job guard is now item 3 of the AA-751/X6 re-scope. The §3.4 doc refresh and the Done-when rewording (bk-001 replaces 'schema v2') are small edits.
- **AA-681** → Done on the staff-side demo; move 'My Trips' to AA-680: The TP→Booking intake (TC-000001, S235) and V1→V2→approve→confirmed (TC-000003, S237) are both proven with an audit trail. My Trips is blocked on customer identity (AA-680).
- **AA-788** → Merge the F14 under-length item into AA-780 (duplicate scope): AA-788 overlaps AA-780 by its own description, and r5 had 0 LinkedIn posts under 120 words. The F12/F9_brand_style part stays and is sequenced after AA-777.
- **AA-756** → Remove item 3 (a1_promise_unsupported) because AA-803 duplicates it: AA-803 scopes the same calibration and starts from the S228 0.70/0.30 floors.
- **AA-729** → Rewrite as a per-stage eval harness, or Cancel as superseded by AA-783 + AA-791 + AA-803: The Done-when is impossible: AA-724 shipped on 07/10 without a golden set. The Jev T-axis is off, and AA-801 solved T2 judge stability.
- **AA-763** → Done on unit-test evidence (if Nghiệp accepts): T2 jobs log only t2_*, verified live (job 53626b6f). The only thing pending is a natural S1 job, and none has run since S233. Nghiệp declined to trigger one.
- **AA-791** → Keep In Progress; correct the S237 log: The 30-piece fault-injection set already shipped in CIS #735 (tests/unit/test_aa791_fault_injection.py), so 'Còn lại' item 8 is wrong. Remaining: the Label form default (PieceLabel.tsx:38 pre-selects as_is), the LABEL column at 1440, and the first label save.
- **AA-781** → Backlog, Low (parked): F9 v1.1 is live (AA-786 #709), and AA-777 targets the same F9 holds. The S234 replay baseline is stale.
- **AA-679** → Rewrite the Done-when to the S237 D4 design (live read of catalog.v_tour, no outbox): The description still describes the outbox design. What remains is one live write verify ('Use for trip case').
- **AA-703** → Rewrite as the ADR 0006 epic (staff = email code only): ADR 0006 dropped Google sign-in for staff. The 'Google/Facebook for admin' Done-when is stale.
- **AA-813** → Rescope to ADR 0006 Phase 3 (Cognito invitations, shared.tenant_members): The description still says acp_shared.tenant_users and 'password now', which contradicts golden rule 14 and DM-1.5.
- **AA-816** → Rescope to ADR 0006 Phase 1 (Cognito groups, no password reset): Staff sign in by Cognito email code, and roles become cognito:groups.

## Danh sách việc theo thứ tự (tier now / next / later / parked)
| # | Tier | Issue | Việc | Lane | Size | Cần Nghiệp |
|---|---|---|---|---|---|---|
| 1 | now | AA-833 | TripPlanner browse still throttles at concurrency 15 + throttle alarms page on every 5-min blip | Infra/ops + TripPlanner | M | Approve creating the issue and the targeted alarm apply. Any raise in browse concurrency must stay within the tripplanner CONNECTION LIMIT 30. |
| 2 | now | AA-792 | T2 tenant voice: export Trail Pulse / A&H versions for the voice read, then send PR-17 samples to Ms. Thư | CIS T-series | S | Voice read of the Trail Pulse and A&H versions. Approve the PR-17 Jira draft. |
| 3 | now | AA-831 | Facebook Page connect: tenant guide (promised on PR-7) + correct connect-card help text | CIS portal | S | Approve creating the issue and the PR-7 Jira draft. |
| 4 | now | AA-819 | AUP 2026-11: live evidence for the daily publish limit (429), F19 block path, TripPlanner AI badge audit | CIS portal | S | Policy on review claims in a tenant's own CTA, with Ms. Thư. Decide whether a visible daily-quota counter is wanted. |
| 5 | now | AA-811 | SES transactional email, app half: TripPlanner advisor notify sender + bounce/complaint suppression | TripPlanner + platform | M | Staff inbox address. Edit the ADVISOR_NOTIFY_EMAIL env var by hand (underscore). Decide whether the advisor email stays in TP notify.py or moves to Booking. |
| 6 | next | AA-820 | Tenant Terms AUP clause: counsel review + Booking high-risk boundary line in CONTEXT.md | Legal/docs | M | Engage counsel this week, approve the clause, and have Ms. Thư notify tenants before 11/11. |
| 7 | next | AA-778 | Em-dash: deterministic autofix, strip em-dashes from prompts, residue guard | CIS T-series | S |  |
| 8 | next | AA-703 | Cognito identity epic, Phase 0: ACM us-east-1, spike, apply Infra #105, break-glass, first staff email-code login | Identity/infra | XL | Approve the rewritten epic scope. Break-glass TOTP device. EXTERNAL Google OAuth client (later). |
| 9 | next | AA-817 | RLS follow-up: observed flag flip, move tenant route groups, fix remaining policies; plus tenant_integrations RLS/DELETE grant and the X2 catalogue guard (folded) | Data platform / CIS | L | Approve the observed flag-flip window on Dev and the order in which route groups move. |
| 10 | next | AA-806 | CI role split step 3 + WAF enforce; plus a clean full-root Terraform plan (hidden drift on secrets/RDS/random_password, folded) | Infra/security | M | Geo list for Booking customers before WAF goes onto the Booking REST stage. |
| 11 | next | AA-828 | Per-app cost allocation tags + budgets; clean up stale AA-360/AA-364 alarm comments (folded) | Infra/ops | S | Budget amounts per app. |
| 12 | next | AA-830 | Tour key fix (X3): inquiry.submitted v1.2 with source_system + source_id per leg, trip_case_legs key columns, backfill | TripPlanner + Booking | M | Approve creating the issue. |
| 13 | next | AA-708 | Photos: CloudFront in front of photos/ + daily scheduled sync (PR-11 promise, folded), Laos sync | Infra + CIS | M | Ask Ms. Thư about photo usage rights and the Laos/Seorak folders. |
| 14 | next | AA-802 | Silent correction live check + latest-piece rule on /v1/publish-log/pending (46 duplicate Ready-to-Publish cards, folded) | CIS portal | S | Approve one admin edit on a test tenant's content as evidence. |
| 15 | next | AA-834 | Fix flaky AA-752 smoke test (b): the click lands before hydration | CIS portal/CI | S | Approve creating the issue. |
| 16 | next | AA-712 | Place pipeline: L4 catalog read-model latency, PLACES_SOURCE=cis flip, content-validity checks, photo_sync off frozen TP tables, a3_place_days shadow decision (folded) | CIS platform + TripPlanner | L | Approve creating an L4 issue, or fold L4 in here. Paid catalog run (≈$15-20) after the flip. Laos replaces Korea in the Done-when. |
| 17 | next | AA-800 | Tenant signature vocabulary: 3-layer forbidden lists, per-tenant writer rule | CIS T-series | M | Paid verification run (<$1). |
| 18 | next | AA-777 | F9 judge consistency: sticky pass, attempt-3 cut for blogs, judge A/B (drop the gpt-4.1 arm) | CIS T-series | M | Approve the paid A/B (≤$1) and r6 (~$1.1), and the A/B arms. |
| 19 | next | AA-780 | LinkedIn: Trail Pulse voice fields, broetry + stock lines, hashtag place-name check | CIS T-series | S | Review the Trail Pulse T0 voice fields (data change). |
| 20 | next | AA-816 | Staff directory + Cognito groups (ADR 0006 Phase 1); retire create_staff_user.py | Identity / CIS admin | L | Confirm the Done-when rewrite. Booking roles move to cognito:groups. |
| 21 | next | AA-682 | Booking wave 3: supplier bookings + trip checks, then invoices/payment schedule | Booking | XL | Manual payment marking only for the MVP. Tax handling while the accountant is pending. Approve the split. |
| 22 | next | AA-822 | Wave 2a: UI verify /suppliers + live create of a supplier/contract | Booking | S | Allow test write data. Act as second approver for publish. |
| 23 | next | AA-823 | Wave 2b: hotel + service as trip-case items with net-rate default and AA-810 sell price, UI verify | Booking | M | Act as second supply.write approver. |
| 24 | next | AA-679 | Catalog read in Booking: Done-when rewrite to D4 + live 'Use for trip case' verify + low UI defects | Booking | S | Approve the D4 Done-when rewrite. Allow marking one plan sellable on Dev. |
| 25 | next | AA-832 | Remaining C4.1 RDS alarms: latency, disk queue, XID, per-role connections vs CONNECTION LIMIT | Infra/data platform | M | Approve creating the issue. |
| 26 | next | AA-827 | TripPlanner guest_token: random token, store the hash only | TripPlanner | M |  |
| 27 | next | AA-825 | Retention: observed DRY RUN per kind, then real archive-delete; Booking job TTL + inbox PII redaction (folded) | Data platform | M | OK each kind from DRY RUN to real delete after reading the counts. |
| 28 | next | AA-751 | Re-scope to X6: job DDL template, booking.job columns, Booking deploy job guard, DB Migrate idle check, backlog-age alarm | Data platform / Booking / Infra | M | Confirm the re-scope (data-standards open item #4). |
| 29 | next | AA-791 | Label form: no pre-selected verdict, LABEL column visible at 1440, first label save | CIS portal | S |  |
| 30 | next | AA-801 | T2 judge: 1-week watch readout after ~21/10, then close | CIS T-series | S |  |
| 31 | next | AA-714 | Pick the single judge primary on/after 31/10, turn the shadow off, PR-16 update | CIS platform | S | The 31/10 model decision and the PR-16 wording. |
| 32 | next | AA-836 | Portal layout at 390 px + My Catalog source 404 + raw markdown previews (D2/D3/D4/D6) | CIS portal | M | Approve creating the issue. |
| 33 | next | AA-818 | Switch app base URLs/canonical to the custom domains; booking. staff host | Infra/TripPlanner/Booking | S | Edit the Vercel env vars by hand (underscore names). Confirm the name booking.lumiguides.it.com. |
| 34 | next | AA-768 | Close the T9 source-fidelity umbrella on r5 evidence | CIS T-series | S | Accept r5 instead of re-running the 5 S231 requests. |
| 35 | next | AA-771 | Close the brand pack: criteria 1+2 met, criterion 3 moves to AA-800/AA-790 | CIS T-series | S | Choose close now or keep open. |
| 36 | next | AA-763 | Close the G4 stage keys on unit-test evidence or the next natural S1 job | CIS platform | S | Accept unit-test evidence. |
| 37 | later | AA-680 | Customer sign-in on Cognito EXTERNAL + TP guest linking | Identity/Booking/TripPlanner | L | Confirm the split and the order (staff first). |
| 38 | later | AA-790 | Post-repair integrity check + T9 tenant-voice rubric gate | CIS T-series | L | LLM judge vs deterministic rubric. Terra voice direction. |
| 39 | later | AA-807 | Data Phase 1: dead-table registry (N6), owner roles (X1), shared.countries (X5), drift diff, TripPlanner migration replay CI (folded) | Data platform | L | Split into smaller issues? Pick the owner of owners.yaml. |
| 40 | later | AA-804 | AI platform ADR 0009 + ledger v2 + AI Use Register; PII-on-LLM-path decision (folded) | CIS platform | XL | Accept ADR 0009. Approve the ledger v2 migration. Decide DM-6.4 enforcement. |
| 41 | later | AA-783 | Human calibration of the T9 panel: 40 labels through the Label UI | Eval | M | Do the labelling. Choose the piece set. |
| 42 | later | AA-779 | FAQ: questions from People Also Ask + subject check | CIS T-series | M |  |
| 43 | later | AA-789 | Gate recall tunes (openers, F15/F18/F13) | CIS T-series | M |  |
| 44 | later | AA-787 | Drop/merge T10 gates (F8 LLM call, F3, F5, merges) | CIS T-series | M | Still drop promises_an_option now that it is quiet (0/8)? |
| 45 | later | AA-788 | Promote F12_scope / F9_brand_style to blocking (F14 moved to AA-780) | CIS T-series | S |  |
| 46 | later | AA-813 | Tenant users on Cognito invitations + membership contract view and PII tags (folded) | Identity/CIS portal | L | Confirm the rescope to ADR 0006 Phase 3. |
| 47 | later | AA-668 | Writer panel: move tour rewrite into the panel + live paid E2E | CIS portal | M | Split vs keep. Is market needed in the header? |
| 48 | later | AA-681 | Trip case MVP: close on the staff demo, move My Trips to AA-680 | Booking | S | Close decision. |
| 49 | later | AA-678 | Booking bootstrap: close (guard moves to AA-751) | Booking/docs | S | Close by hand. |
| 50 | later | AA-683 | Booking UI spec close-out + /pricing/rules table at 1440 (folded) | Booking | S | Waive the Ms. Thư review or schedule it. Decide Q1a-f. |
| 51 | later | AA-829 | Restore drill + private DSN CNAME + secure the 2026-09-16 dumps + single-schema restore runbook (folded) | Infra/data platform | M | Edit the DSN secrets by hand. Approve deleting the local dumps. |
| 52 | later | AA-826 | New-app playbook tooling: owners.yaml, role bootstrap template, contract hash guard | Data platform | M | Pick the owner of owners.yaml. |
| 53 | later | AA-835 | ADR 0004a supply content: contracts, Booking supply outbox/views, CIS consumer with review, read-back, entity_media | Booking + CIS | XL | Approve creating the issue. |
| 54 | later | AA-837 | /plan: 7 WCAG contrast violations, Customise 404 console error, '1 DAYS' | TripPlanner | S | Approve creating the issue. |
| 55 | later | AA-838 | Wire the weekly/monthly/quarterly DB reviews into the session ritual; first capacity review | Data platform/process | S | Approve creating the issue. |
| 56 | later | AA-741 | T-series audit G7/G8 (48-tour run) re-scoped, without the Jev layer; s237 FB test-piece cleanup (folded) | CIS T-series | XL | Approve the re-scope and the paid G7 run (~$10-20). |
| 57 | later | AA-784 | Platform-wide place card build (~$15-25) | CIS platform | L | Paid run approval and country order. |
| 58 | later | AA-772 | Place cards: G7 list cards / thin-vs-card A/B | CIS platform | S | Is the A/B still worth paying for? |
| 59 | later | AA-756 | Jev A-axis recalibration leftovers (S228 decision set, record_rejected_outcome, 402s) | CIS platform | L | Answer the S228 decision set. |
| 60 | later | AA-803 | Calibrate a1_promise_unsupported, or switch it off | CIS platform | M | Calibrate or switch off. |
| 61 | later | AA-765 | Gateway refactor: judge client, T11 dispatch into acp_publish, docstrings | CIS platform | M |  |
| 62 | later | AA-701 | Dead-code chore: remove observe_t10 + facts.select_relevant_facts | CIS platform | S | Close as superseded after the chore. |
| 63 | later | AA-729 | Golden set: rewrite as a per-stage eval harness or cancel | Eval | L | Rewrite or cancel. |
| 64 | later | AA-795 | T2 judge breakdown per version + brand-claim fidelity | CIS T-series | M | Still wanted? |
| 65 | later | AA-814 | Facts Entry API + UI | CIS portal | L | Priority relative to place cards. |
| 66 | parked | AA-781 | F9 v2 claim rules | CIS T-series | M | Keep or park. |
| 67 | parked | AA-782 | Cheaper T9 blog writer A/B | CIS T-series | M | Vendor rule. Paid A/B (~$1.20). |
| 68 | parked | AA-696 | Jev T-series parent: cancel as superseded | CIS platform | S | Confirm cancel. |
| 69 | parked | AA-699 | Jev T0/T2/T3: cancel as superseded | CIS platform | S | Confirm cancel. |
| 70 | parked | AA-634 | Jev research: close Done | Research | S | Confirm close. |
| 71 | parked | AA-709 | Pricing research: close Done (ADR 0005) | Booking | S | Confirm close. Is a follow-up needed for trip_plan_prices? |
| 72 | parked | AA-710 | Asian Trails B2B benchmark | Booking/research | S | Close or keep as a trigger. |
| 73 | parked | AA-697 | Architecture diagrams | Docs | L | Park. |
| 74 | parked | AA-655 | Shared design system package | Design | M | Package vs copies + drift guard. |
| 75 | parked | AA-671 | Marketplace redesign | CIS portal | M | Merge with Browse Tours? |
| 76 | parked | AA-704 | In-app AI assistant | CIS portal | L | Keep on the roadmap? |
| 77 | parked | AA-821 | Tenant CRM research | Research | M | When to schedule it. |
| 78 | parked | AA-628 | Engagement feedback loop | CIS T-series | L | Park or cancel. |
| 79 | parked | AA-839 | Erasure runbook + DRY RUN job for a traveller and an offboarded tenant | Data platform/privacy | M | Approve creating it as a parked Low issue. |

## Ghi chú rủi ro (từ bước tổng hợp)

1) "Bị thông báo hoài": nguồn chính là alarm SNS aa-tripplanner-dev-browse-throttles. Alarm này lật OK↔ALARM 7 lần, tức 14 tin trên topic aa-cis-dev-acp-alerts, từ 14/10, do có cả ok_actions và Sum(Throttles)>0 trên 1 kỳ 5 phút. Throttle là thật: sau Infra #125 vẫn còn 75 lúc 16:10 và 17 lúc 17:55. UI Smoke chỉ hỏng 1/35 lần nên không phải nguồn chính. Chưa kiểm hộp thư/GitHub notifications của Nghiệp.
2) Nâng concurrency browse bị chặn bởi CONNECTION LIMIT 30 của role tripplanner (pool max 1/instance). Nên tìm nguồn burst trước, ứng viên: crawler trên sitemap 892 URL từ khi tripplanner.lumiguides.it.com live, prefetch /plan, các lần chạy UI-verify.
3) KHÔNG dispatch terraform-apply.yml cho toàn root: CI plan run 38727028673 có 16 thay đổi, gồm secret versions, random_password và RDS. Sửa alarm chỉ dùng targeted apply, đọc plan trước.
4) Hạn AUP 12/11. Engineering của AA-819 chỉ còn evidence. AA-820 cần Nghiệp mời counsel ngay tuần này (issue due 11/11). Đây là việc của Nghiệp, agent không làm thay được.
5) Gửi mẫu PR-17 cho chị Thư: AA-778 chưa ship nên phải soát em-dash bằng tay trước khi gửi.
6) Phiên này chạy tối đa 3 lane song song: (A) Infra/TP throttle, (B) CIS portal: FB guide + bằng chứng 429 AA-819 dùng chung kênh test, (C) TP SES sender AA-811. AA-792 nhẹ: export + Nghiệp đọc.
7) Có 10 issue NEW, theo quy tắc Linear phải hỏi Nghiệp trước khi tạo. Phần lớn rơi vào project Data Platform, cần để ý quota 100 issue/project.
8) Các run tốn tiền đang chờ duyệt: AA-777 (~$2.1), AA-800 (<$1), AA-784 ($15–25), AA-741 G7 ($10–20), AA-712 cả catalog (~$15–20), AA-782 (~$1.2).
9) Chưa kiểm được: DB live (read-only), nội dung từng comment Jira, PR-7 Live round trip (coi như xong theo lời Nghiệp). 2 gap không cần issue: jev-typesafe-dpa (T-axis Jev đã tắt, câu hỏi DPA nằm ở AA-820 Q11) và jira-closeout (đã có sweep bước 4b cuối phiên).
