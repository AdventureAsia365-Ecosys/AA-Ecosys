# S279: rà soát Linear, kết quả cho tech lead

## 1. Tóm tắt

**Số issue theo verdict (39 issue):**
- update_scope: 22
- keep: 8
- close_done_with_scope: 4
- reslot: 2
- merge_into: 2
- blocked: 1

**Số issue mở:**
- Trước khi làm: 39.
- Sau khi làm: 33. Đóng 4 issue (AA-998, AA-1079, AA-922, AA-1094) và hủy/gộp 2 issue (AA-781 vào AA-1048, AA-1082 vào AA-980).
- AA-998 đóng được ngay. AA-1079 và AA-922 chỉ đóng sau một bước $0. AA-1094 đóng khi việc Book now được chuyển sang AA-1086.

**Trạng thái Linear đang sai:**
- **AA-1082 đang In Progress nhưng không ai làm.** Theo quyết định S277, Dev chạy 1 task, việc còn lại là của go-live. Đề xuất gộp vào AA-980 rồi hủy.
- AA-1079 đang In Progress nhưng việc đã xong. Đề xuất đóng Done-with-scope.
- AA-1051 đang In Review nhưng chưa chạy lượt trả phí nào và không có comment. Đề xuất chuyển về Backlog.
- AA-1093 đang In Review nhưng mới merge phần CIS restore (#1470) và Infra #803. Đề xuất chuyển In Progress.
- AA-1094 đang In Review. Đề xuất đóng Done-with-scope.

**Các chỗ lệch phải sửa khi chốt phiên S279:**
- **Trùng số migration.**
  - AA-1096 L1 dùng CIS 407, L3 dùng bk-056.
  - Kế hoạch AA-1093 cũng giữ đúng CIS 407 và bk-056.
  - AA-1061 vẫn ghi bk-045, nhưng số này đã dùng (045..055 đều có trên main).
  - Cách xử lý: lane nào merge sau thì lấy số trống tiếp theo. Sửa lại `aa1093-plan.md` §3 ngay.
- Commit Booking `5ecd8e5` ghi `Refs AA-TBD`. Phải sửa thành `Refs AA-1096` trước khi mở PR.
- **plan.json:**
  - Slot "LLM path" của AA-790/1000/920/921 đã lỗi thời. Rào thật là TL-11, điều kiện gỡ theo S278 D4.
  - AA-1048/1050/1051 vẫn ở milestone "later".
  - AA-1004 vẫn ghi session S275.
  - M-P2 tiêu chí 2 (`v_tenant_tour_v1`) đã đạt.
  - Bỏ tiêu chí AA-855 vòng 2 trong M-P2 và các mục waiting 20/33.
- **docs/backlog/README.md:**
  - Sửa các dòng ghi sai trạng thái: AA-1050, AA-1051, AA-1079, AA-1082 (dòng 163) và AA-855 (dòng 94, 174).
  - Xóa các dòng AA-998 giả định "acc1 = 0 USD" (dòng 39–40, 145, 184).
- **Phần chưa có chủ:**
  - Mục "Reversal" của ADR 0001a Note S278 và buổi xem lại acc1 đầu tháng 12. Đề xuất thêm một dòng hẹn ngày ở §1 và một dòng scope cho AA-1004, không tạo issue mới.
  - `docs/legal/dpa-annex-3-subprocessors.md` v0.4 có từ trước S278, chưa nói acc1 đang chạy Bedrock.
- **Ngoài phạm vi rà soát:** AA-1087, AA-1088, AA-1092 (In Review trong plan.json) và AA-1070, AA-1095 (đã đóng) không có trong 39 verdict.

## 2. Hành động trên Linear

| ID | Tên ngắn | Verdict | Thay đổi cụ thể | Bằng chứng |
|---|---|---|---|---|
| AA-1050 | W4 promote claim instrument | update_scope | Viết lại Done-when. (1) MET S274/S275: shadow spend 0.12 USD (< 0.30); instrument right in 87.5% of object-level disagreements with F9; 0 holds from a non-pinned rung. (2) For each class AA-1048 measures as passing, flip enforce through AA-1096 admin settings (evidence_ref = W2 record), not taxonomy.yaml or env; every other class warns. (3) Truth-cut only for passing classes, clause first, tenant spans never cut (D6). (4) 100% of held / needs-review pieces carry a typed reason (live window). (5) Total spend < 0.50 USD. (6) AA-1052 carry-over: delete or promote t10_claims, seed-align tier 1, AA-1000 adjudicator; deleted stages need a 0-diff replay plus a grep showing 0 live paths. Blocked by AA-1048. | CIS #1398/#1399 live. Panel S275 cho 14/16. R1 S278 và panel FP S279 cho thấy chưa class nào đạt. |
| AA-1051 | W5 paid writer proofs | reslot | State: In Review → Backlog. Thêm: "Blocked by AA-1048: the null run's judge must be the instrument W2 pins; $0 code shipped in CIS #1452/#1453 (CIS 400)." Slot: null run ≤5 USD ở S280 hoặc phiên đầu sau khi AA-1048 pin; T9 ≤15 phiên sau; S1 ≤8 và T2 ≤5 sau nữa. | Prereg đang pin judge gpt-6-luna-openai, vốn đo được precision 0.22–0.27. Chưa chạy lượt trả phí nào. |
| AA-1077 | T9 blog length contract | update_scope | Done when: (1) MET: $0 replay, no approved piece under the floor (S277). (2) MET: T7 min seed decision (S277). (3) Seed ratio 3.364 chars per seed word (floor ≈1,398 words) stored as an admin-editable CIS setting (AA-1096 L1 key), not env. (4) F13_hygiene exact repeats feed the drop step before F13. (5) 3-piece paid trial on audit-atlas-hearth (≤0.5 USD) shows 0 F4 holds, cost from llm_call_log. Extend repair dropped (0/3, stays off). F17 out of scope. | Đã có #1431, #1450/#1451, #1462/#1463, #1468. Trial 3 của S279 vẫn còn Galle bị giữ F4 (4,228 ký tự). |
| AA-1079 | Judges: Debate rank-only, brand-fit, routes | close_done_with_scope | Trước khi đóng, làm 2 việc $0: (a) comment bằng chứng (replay S277 dropped_by_rank 0; số đo S278 kappa t2 0.63 trên 20 cặp, F9 -0.04) kèm tick option A của tech lead; (b) đọc ledger 24 h của t2_judge, t7_debate_judge, t10_judge, cần 0 dòng refusal non-shadow từ route v11. Phần nhãn brand-fit (≥40 cặp, ≥5 mỗi class) và việc có trả lại Debate cut hay không chuyển sang AA-790 (ADR 0020 D9). | CIS #1429, #1447. Verify S278 4/4 PASS. Route v10/v11 đã đưa judge sang acc1. |
| AA-790 | Tenant-voice rubric gate | update_scope | Scope: per-tenant voice rubric from T0 brand pack, report-only (Writing Lab signal + Debate rank input) until ADR 0020 D9 (kappa ≥0.6 on ≥40 labelled pairs, ≥5 per class), then a repair-only gate that never holds. Post-repair integrity check: MET (S251). Done when: (1) brand-fit labels ≥40 pairs per writer (from AA-1079); (2) rubric agreement measured; (3) 20-piece pilot catches ≥4 of 6 Trail Pulse-type false passes; (4) panel brand_voice ≥7 overall and per tenant on the S232 LinkedIn set (baseline 6.75). Blocked by: TL-11 lift (S278 D4), not the LLM path. | Các vòng r7–r10 đều fail. F9 brand-style kappa -0.04. Đường LLM đã có từ S269/S278. |
| AA-788 | Promote F12/F14/F9 to blocking | update_scope | Thêm vào Done-when: (1) F12_scope flip needs a measurement record (precision lower bound on labelled fires, ADR 0020) from the 20-piece pilot; (2) flip made on the admin settings page (AA-1096 L2), evidence_ref = pilot record; (3) F9_brand_style stays repair-once, never holds; (4) F14 under-length uses the AA-1077 floor / length_short code. Bỏ "LLM path" khỏi blocker, vẫn chờ ngày ≥19/11. | Replay S261 cho 5/300 hold, tất cả là F12. ADR 0020 có sau khi issue được viết. |
| AA-781 | F9 v2 place_background | merge_into AA-1048 | Comment trên AA-1048: "place_background / opinion classification from AA-781 is handled in the instrument prompt change (A-type place background exempt, D1/D3)." Hủy AA-781 vì trùng. | Panel FP S279: 14% là place background loại A. AA-1048 vốn đã ghi "absorbs AA-781". |
| AA-782 | T9 cheaper writer A/B | update_scope | Đổi tên: "[T9 cost] A/B a cheaper non-OpenAI blog writer vs Sonnet 5.5 on 8 paired blogs, blind panel". Scope: candidate from a different family than the pinned judge (e.g. Haiku 5.5 on anthropic-direct or acc1); W5-style pre-registered paired proof (AA-1051 runner), stage adhoc_aa782. Done when: candidate light count ≥ Sonnet's, held ≤ Sonnet's +1, blog cost ≤0.06 USD → route change proposed; else a documented no-go. Re-baseline cost from the current ledger. Gate: after the AA-1051 T9 proof passes. | ADR 0020 D7 cấm GPT-6 làm writer. Ghi chú S265 d18. |
| AA-1000 | Tier-2 LLM adjudicator | update_scope | Thay "Blocked by" bằng: (1) TL-11 lift (S278 D4); (2) AA-1050 delete-or-promote decision; nếu quyết delete thì hủy issue này. Thêm vào Scope: re-route t10_adjudicate from acc3-first to acc1 / openai-direct in route control (no migration) before calibration. Giữ nguyên Done-when. | CIS #1172 và mig 308 đang seed acc3 đi đầu. acc1 đã trả lời 13/13 model. |
| AA-920 | Writing memory: inject rules | update_scope | Đánh dấu WM-25 và WM-26 MET (bằng chứng S256). Thay dòng "Judge calibration: kappa ≥0.6 per stratum" bằng "R2 uses the claim instrument pinned by AA-1048 (ADR 0020 D7); the brand judge only per D9". Blocker: "TL-11 lift (S278 D4) + first approved rules". Release 1 quản lý trong Writing Lab › Releases. | CIS #1112/#1114, #1099, #1311. |
| AA-921 | Pinned examples + preference summaries | reslot | Slot trong plan.json: "LLM path" → "after AA-920 release 1 (TL-11 lift)". Thêm một dòng trên Linear: "$0 part verified live S261 (CIS #1186); remaining: WM-27 R2, WM-28 approved summary, WM-29 release check. Summary UI goes in Tenant 360 › Brand & voice." | CIS #1186 với 9 owner, 0 leak. |
| AA-922 | Weekly KPIs, soft-stop | close_done_with_scope | Đóng sau một lần đọc $0 `GET /admin/writing-memory/metrics` thấy ≥2 report có trigger=schedule. Commit file xu hướng vào `docs/audits/<date>-S28x-aa922-trend/`. Comment: "Rule expiry is proven by test_aa922_kpi_weekly; the first live expiry and soft-stop on real writes move to AA-920 (release 1)." | CIS #1187/#1192/#1311. Job KPI_WEEKLY đã được lên lịch (ops_metrics_sampler.py:324). |
| AA-998 | Remove acc1 | close_done_with_scope | Đóng ngay với comment: "S255–S257 delivered the removal: audit, cut-over, deletions, grep proof. The tech lead's S278 decision (AA-1095, ADR 0001a Note S278) brought acc1 back for Bedrock chat serving only, so Done-when 2–5 no longer apply. acc1 spend is watched by the AA-1096 alert-only budget. The way back is the 'Reversal' paragraph of ADR 0001a Note S278." Xóa các dòng AA-998 trong README (39–40, 145, 184) và 2 check trong plan.json. | Bằng chứng ở root #319, CIS #1102, TP #174, Infra #466/#476/#491. Quyết định đảo lại ở S278 (#730). |
| AA-1004 | Lean AWS model | update_scope | Scope 3: "Invite aa-nonprod (acc2) by Billing Transfer on 01/12 (S271 plan). aa-ai (acc3) stays in acc1's organization (S277); moving it to acc4 needs it to leave acc1's org first, decided with the acc1 review in early December." Scope 4: "Bedrock path: since S278 served from acc1, acc3 fallback (ADR 0001a Note S278). Revisit when the acc3/acc2 AWS cases are answered." Done-when: "aa-nonprod is a member; aa-ai and acc1 placement recorded as a tech-lead decision (early December)"; dòng đường AI ghi MET (AA-1095). Đổi session trong plan.json sang S280. Thêm một dòng cho Reversal của ADR 0001a. | S275 đã đạt (Infra #734, ADR 0018). Các check trước 20/11 chưa làm. |
| AA-1003 | Report engine R0–R7 | update_scope | Scope: "R0–R4 delivered (26 reports live on Dev; TP-03 retired S266; B2C KPIs historical). Remaining R5–R7 as B2B reports per ADR 0019: per-tenant entitlement and AI spend vs cap, SaaS/settlement invoicing and aging, agency pipeline (crm.ops.v1), partner KPIs (K-PART-PAYING, MRR, churn). B2C reports dropped. New KPI thresholds registered as settings (AA-1096)." Done-when: "Each of R5–R7: merged, deployed, a live report_run row from real Dev data with output in docs/audits; EX-06 shows catalog status of every report, retired ones listed." | Re-scope S265 chỉ nằm trong comment. Hotfix R0 S266 (root #493). |
| AA-1086 | Synthetic pilot rehearsal | update_scope | Viết lại theo thiết kế 2 tenant. `pilot-rehearsal-01` (demo) chạy bước 1–12 và giữ làm fixture. `pilot-rehearsal-01-marker` (agency, pilot_weeks 1) chạy bước 1b/12b. Done-when: "the marker tenant leaves pilot mode and is removed at teardown, and the Dev pilot slot is free again". Thêm: "X2 records the CRM part as PASS if AA-1093 L1 is merged, else as a gap owned by AA-1093". Dòng runbook ghi MET (#740). Thêm bước của AA-1091 (Excel import ≥3 tour → priced → tariff/From $X) và AA-1094 (Book now tạo dòng cùng source_id, ảnh 390 px). | Root #740 đã merge. Chưa có thư mục audit cho rehearsal. |
| AA-1089 | CRM Odoo add-ons | update_scope | Scope/Done when: "Ranks 46 and 47 are already live (cancellation.policy, AA-1067 #261; vouchers + visa on /c/t, AA-1070 #271); ranks 49–53 need nothing. Remaining: (1) a 'Booking confirmed' starter template (EN + VI) in CIS data/aa_content/seed_v1.json, importable in the CRM template library; (2) source AA tour and departure (title, date, link) on the CRM trip header. Done when: both live on Dev with a test each and a live check; CONTEXT.md updated if the trip view model changes." | Partner merge.py:30, PortalTravel.tsx, TripPanel.tsx:399. |
| AA-965 | CRM AI: supplier confirmations | update_scope | Thay description bằng scope ADR 0019 b6. R10: chỉ cho ancillary supplier ngoài AA, gắn vào crm-053; dòng tour AA lấy trạng thái từ booking.b2b.v1. R40: notes → options chỉ chọn trong danh sách đóng các tour_id/atom AA đang live. R41: voice profiles. Qua gateway với pii_class us, sau scrub F3, tính vào budget AI của tenant (hard_stop default true, AA-1096), có AI notice của kit, theo route control hiện hành; không bao giờ gửi ảnh hộ chiếu. Done when: trial 3 rồi ≤50 lượt trên agency tổng hợp, có cost từ llm_call_log; test cho closed-list và no-passport; agent review độc lập trước merge; live check. Bỏ ghi chú "needs an LLM path" (README dòng 257, plan.json). | Đường LLM có từ S278. Budget tenant đã có (Partner settings.py:253). |
| AA-968 | CRM Campaigns | update_scope | Thay description: "Campaigns (R14) sent only from the agency's own mailbox (BYO). Selling content passes the d21 gate. A tour flagged retired by the CRM fan-out (crm.tour_retired_flag, AA-1093 part 1) is pulled from scheduled campaigns. R: no-consent contacts excluded; unsubscribed re-imports stay suppressed. E: a list over the mailbox daily send limit is spread over days; that limit is a platform setting with an agency range (AA-1096), not a constant. Done when: Global Done + tests for consent, suppression, retired-tour pull, daily spread; independent review before enabling for a pilot tenant." | AA-1093 D9 đã chọn crm_catalog_sync, không dùng event d20. |
| AA-963 | CRM Search + library | update_scope | Viết lại: phần library đã live (AA-951, AA-959, crm-059); chỉ còn thêm Content pieces CIS vào picker nếu thiếu. Scope: global search R35 trên Content và CRM theo quyền người dùng, chỉ dùng blind index (không index PII plaintext, từ chối tìm F1 một phần), không phân biệt dấu ("Đà Lạt" = "Da Lat"). Done when: Global Done + test chứng minh không có plaintext index và luật bỏ dấu; review độc lập trước khi bật cho pilot. | Partner travellers.py:197, blind_index.py. |
| AA-1012 | PAdES signed PDF | update_scope | Scope mục 1: "Render the signed envelope as a new document kind on the existing server PDF renderer (api/app/documents/pdf.py, embedded Liberation Sans, AA-1070), no new font pipeline." Mục 2–3 và Done-when giữ nguyên. | Renderer có từ #271/#287. Chưa có code pyHanko. |
| AA-1011 | M365 + BYO calendar | update_scope | Scope: "(1) Entra multi-tenant app registration owned by the company (tech lead), values into crm/dev/mail-oauth; (2) live proof of the existing M365 and SMTP send-as connectors (AA-945 code: providers/oauth_mail.py, providers/smtp.py) with threading parity, held_reconnect + requeue; (3) build calendar OAuth one-way push (Google calendar.events, Microsoft Graph) with revoke on disconnect, tokens in the agency vault." Giữ Done-when. Blocker: Entra registration + một mailbox SMTP để test. | mailbox.py:37 MAIL_PROVIDERS. Thư mục calendar/ chỉ có ICS. |
| AA-980 | CRM Go-real | update_scope | Checklist chỉ còn nửa prod: placement theo AA-1004; prod partner pool cho một app agency; HA cho agency web (≥2 task hoặc on-demand base + Spot, dừng task ép buộc mà portal vẫn 200 trên probe 5 s, gộp AA-1082); WAF; tắt ECS exec; pentest b18; vendor verification; thanh toán chỉ qua Stripe Connect của agency (b14); data page, sub-processor, DPA từ AA-820 (cập nhật cho acc1 S278); saga erasure live ở prod (AA-1093). R: prod từ chối tenant tổng hợp. E: vendor verification còn chờ chỉ tắt đúng kênh đó. Bỏ "Stripe live" và "second public service". | Comment S265 b14. AA-1036 đã gộp portal. |
| AA-970 | Release train, help, data page | update_scope | Viết lại: Help (AA-962), Settings › Data (AA-942/967/971), annex DPA (AA-820) đã có. Scope còn: (1) feed What's new EN/VI và toggle preview theo agency; lint fail nếu logic privacy hoặc giá nằm sau preview flag; (2) public data page và sub-processor page render từ dpa-annex-3, cập nhật cho acc1 Bedrock (S278) trước khi đăng; (3) thêm help topic ngoài getting-started. Done when: Global Done + lint test + live check. | help/page.tsx, settings/data. Annex 3 v0.4 có từ trước S278. |
| AA-948 | CRM builder map | blocked | Viết lại description theo re-scope S265: dùng chung map/route engine của TripPlanner (mapbox-gl) dưới dạng package/kit, CRM builder chỉ hiện tour AA đang live của tenant. R: import trực tiếp app TripPlanner làm fail CI. E: ngày không có vị trí vẫn render, chỉ không có pin. Vẫn parked đến khi tech lead trả lời 2 câu (xem §5). | AA-1041 Done 11/11, tức điều kiện "sau R7" đã đạt. |
| AA-1082 | Agency web HA | merge_into AA-980 | Thêm vào checklist AA-980 (dòng HA ở trên, kèm "monthly cost stated and approved first; cost line in the monthly capacity review"). Hủy AA-1082 vì trùng, comment dẫn quyết định S277 và lần đọc ECS live. Sửa README dòng 163. | Live: desired 1, FARGATE_SPOT, min 100 / max 200, circuit breaker bật. |
| AA-1054 | Remove E2E exceptions at go-live | update_scope | Đổi tên: "[Identity] At go-live: remove every Dev-only E2E staff exception (A10, A10a, A10b + A10b-1..4, A10c, A10d, A10e + A10e-1) and the dormant Booking bridge code". Scope gồm 9 mục như verdict: các ngoại lệ, flag/map E2E_DEV_ONLY, e2e_staff.py, code bridge trong identity_config/staff/identity_verifier/tokens, cập nhật ADR 0006a/CONTEXT/secrets register. Done when: mọi user E2E bị disable/xóa trong Cognito (kiểm read-only); `git grep -i -E 'bridge¦e2e_dev_only' backend/app/auth` (dấu ¦ đứng thay cho ký tự alternation pipe của regex, để không vỡ bảng) trong Booking trả rỗng; CI xanh ở Booking, CIS, Partner; ADR ghi ngày gỡ từng ngoại lệ. | ADR 0006a dòng 672–673 và 715. |
| AA-1061 | Booking B2C table drop | update_scope | Đổi tên: "[Booking] R4c B2C table drop (bk-057 or next free key; apply from 2026-11-28 23:50Z)". Rebuild #200 từ main, cherry-pick 4 commit, lấy số bk trống tiếp theo lúc merge, đóng #200. Phối hợp với AA-1096 L3: issue này drop bảng B2C, L3 chỉ drop policy row. Job erasure của AA-1093 không được trỏ vào các bảng đã drop. Slot: phiên đầu tiên từ 29/11. | 045..055 đã dùng. PR #200 vẫn mở. |
| AA-1091 | Price setup workbench | update_scope | Done-when: "Shipped (S278–S279): Booking #233, #235/#236, #241/#242, CIS #1457/#1458, guide root #739. Done when, live on Dev as a customer-service user with only the pricing preset: (1) accept suggested components for one live tour; (2) one Excel DRY RUN then import making ≥3 synthetic/demo tours sellable in a published price list version; (3) 'priced' on /booking/catalog/price-readiness; (4) agency tariff (versioned) and TripPlanner 'From $X' of a synthetic tenant show them; (5) live-check record per item in the audit folder. Stored-only policy parameters → AA-1096 L3." Thêm bước (2)–(4) vào runbook của AA-1086. | Runbook #740 hiện chỉ định giá 1 plan, không có import ≥3 tour. |
| AA-1094 | v_tenant_tour_v1 + source_id | close_done_with_scope | Đóng với comment: mục 1–2 PASS live (verify/aa1094, comment S278), mục 3 PASS ở phần request key. Phần còn lại, "Book now on a synthetic agency trip page creates the line with the same source_id" và ảnh 390 px của danh sách tour tenant, chuyển sang AA-1086 (thêm bước vào pilot-rehearsal.md). | CIS #1459–#1461, TP #255/#258, Partner #292. Probe 13/11: 11 tour tenant / 844 tour AA. |
| AA-855 | UAT videos | update_scope | Mục "When"/"Round-1 gates": "Parked since S271 (06/11/2026, tech lead). Routine UAT videos stopped; Playwright evidence, Visual/Kit checks and live checks are the acceptance evidence. Reopen only on (1) a business-owner milestone sign-off (one short demo video) or (2) a real pilot agency onboarding (the synthetic AA-1086 does not count). Harness (root #575/#576/#577/#584) and 26 round-1 videos stay, not maintained." Done-when: "On a trigger: the requested video recorded with free local TTS, on Drive, linked in docs/audits, sign-off recorded." Bỏ các kịch bản B2C. | Comment 06/11. Không có commit nào sau #584. |

## 3. Giữ nguyên

Giữ nguyên 8 issue: AA-1048, AA-873, AA-881, AA-842, AA-1096, AA-1093, AA-704, AA-1090.
- AA-1093 giữ scope, chỉ đổi state In Review → In Progress và đổi số migration (CIS 408, bk-057 hoặc số trống tiếp theo).
- AA-1048: thêm comment đã nêu ở dòng AA-781.

## 4. Kế hoạch tiếp theo

Ký hiệu: **[TL-QĐ]** cần tech lead quyết, **[MFA]** cần tech lead nhập MFA hoặc đăng nhập, **[TIỀN]** lượt trả phí, **[NGÀY]** chờ đến ngày.

### S280 (Ultracode, 10 mục)
1. **AA-1096 L1 → L2.** Xong L1 (registry, trang admin, migration lấy số trống, review độc lập vì đụng auth và migration), merge và verify live. Sau đó làm L2: chế độ detector trong taxonomy.yaml chuyển thành setting có evidence_ref.
2. **AA-1093 L0 và phần CIS.** Làm contracts tenant.erasure.v1, entitlements 1.7, DPA §11 90 ngày. Viết migration erasure CIS (408) và saga. Merge Partner #298/#299 (crm-063 và fan-out).
3. **AA-1048.** Sửa prompt instrument ($0) nếu S279 chưa xong. Chạy subset có cổng: 3 claim rồi ≤50. Pin instrument, xác nhận revoke t9b-002. **[TIỀN]** trong trần 4 USD đã duyệt (còn khoảng 3.08 USD).
4. **AA-1051 null run** (≤5 USD), chỉ chạy khi mục 3 đã pin được. **[TIỀN]** theo yes D5 của S278.
5. **AA-1077.** Đưa seed ratio vào setting AA-1096 L1, nối F13_hygiene vào bước drop, chạy trial 3 bài. **[TIỀN]** ≤0.5 USD.
6. **AA-1086 rehearsal.** Chạy sau khi phần CRM tour của AA-1093 merge. Gộp luôn bước cuối của AA-1091 (import Excel ≥3 tour → priced → tariff và From $X) và của AA-1094 (Book now, ảnh 390 px). **[TIỀN]** LLM ≤10 USD.
7. **AA-1004, các check trước 20/11.** Kiểm cost allocation tag và chạy báo cáo untagged, chạy readiness 1.2–1.5/1.7, soạn tin TrueIDC R1–R6. **[MFA]** SSO aa-mgmt. **[TL-QĐ]** tech lead tự gửi tin Zalo. **[NGÀY]** hạn 20/11.
8. **Đóng AA-1079.** Comment bằng chứng, đọc ledger 24 h ($0). **[TL-QĐ]** tick option A.
9. **Đóng AA-922.** Đọc metrics và commit file xu hướng ($0).
10. **AA-1089** làm chen nếu còn sức: starter template "Booking confirmed" trong seed CIS và thông tin tour/departure trên header trip CRM.

### S281 (Ultracode, 10 mục)
1. **AA-1096 L3, L4, L5.** L3 là PR Booking (số bk trống, sửa `Refs AA-1096`, chốt chủ của các dòng B2C với AA-1061). Bật settings-lint thành required check ở từng repo. Đổi live 1 setting mỗi app.
2. **AA-1096 L6 (làm sau cùng).** Budget acc1 chỉ cảnh báo, kèm amendment ADR 0001a (Note S278 hiện ghi "no paid budget or anomaly monitor"). **[MFA]** apply bằng acc1-admin.
3. **AA-1093 các lane còn lại.** Booking bk_tenant_erase (DRY RUN / --expect-plan), TripPlanner tp-030 với backup và restore drill, crm-064 và erasure feed. Sau đó chạy drill offboarding tổng hợp và drill restore CIS/TripPlanner trên Dev.
4. **AA-1050.** Lật enforce cho class đã đạt qua setting AA-1096 (nếu S280 đã pin), đếm typed reason, đề xuất delete hoặc promote các lớp ngủ. **[TL-QĐ]** tick từng lớp.
5. **AA-1051 T9 proof** (≤15 USD), chỉ khi null run đạt. **[TIỀN]**
6. **AA-1000, AA-790, AA-920: phần code $0 và replay.** Chỉ làm khi TL-11 đã gỡ (AA-1077 đóng sạch và AA-1050 enforce ≥1 class). Trong đó có re-route t10_adjudicate sang acc1/openai-direct. Nếu chưa gỡ thì lùi sang S282.
7. **AA-1003 R5** (báo cáo B2B: entitlement và AI spend so với cap), đọc ngưỡng qua settings reader của L1.
8. **AA-1011 phần calendar OAuth** (làm được trước khi có Entra). Phần proof M365 live vẫn chờ **[TL-QĐ]** đăng ký Entra.
9. **AA-1012.** Tạo document kind envelope trên renderer có sẵn, dùng signer pyHanko qua kms:Sign, X.509 tự cấp trên Dev.
10. **AA-788.** Thiết kế pilot 20 bài. **[NGÀY]** chỉ chạy từ 19/11. **[TIỀN]** khoảng 2–5 USD ở S283.

### Các mốc theo ngày phía sau
- AA-1004: xuất Cost Explorer và invoice ngày 25–28/11, Billing Transfer acc2 vào org acc4 ngày 01/12 **[MFA]**.
- AA-1061: từ 29/11, 07:00 +07.
- AA-873: phiên đầu tiên từ 01/12.
- Xem lại acc1 và Reversal ADR 0001a: đầu tháng 12 **[TL-QĐ]**.
- AA-980, AA-1054: khi go-live.
- AA-881: 05/2027.

## 5. Cần anh quyết

1. **AA-1079, option A.** Giữ Debate ở chế độ rank-only. Brand-fit T2 chỉ báo cáo. Việc gắn nhãn đủ ≥40 cặp chuyển sang AA-790.
   - Mặc định đề xuất: **Đồng ý**, đóng AA-1079 Done-with-scope ở S280.
2. **AA-1082 gộp vào AA-980** rồi hủy, hay giữ riêng (Backlog, "at go-live")?
   - Mặc định đề xuất: **Gộp vào AA-980**. Dev vẫn 1 task, không phát sinh chi phí.
3. **AA-948.** Anh có chấp nhận dùng chung engine bản đồ của TripPlanner (không tách issue fork T13) không? Chi phí Mapbox cho lượt tải bản đồ trong CRM xử lý thế nào?
   - Mặc định đề xuất: **Chấp nhận engine dùng chung.** Báo giá Mapbox hằng tháng rồi anh duyệt riêng trước khi build. Issue vẫn parked tới lúc đó.
4. **acc1 sau S278.** Có 3 việc:
   - (a) Budget acc1 chỉ cảnh báo (AA-1096 L6), sửa luôn ADR 0001a trong cùng PR.
   - (b) Phần Reversal và buổi xem lại acc1 đầu tháng 12: thêm một dòng hẹn ngày ở backlog §1 và một dòng scope cho AA-1004, không tạo issue mới (quota Linear Free).
   - (c) Bỏ budget 1 USD cũ trên acc1.
   - Mặc định đề xuất: **Đồng ý cả 3.**
5. **`dpa-annex-3-subprocessors.md`** chưa nói acc1 (tài khoản cá nhân) đang chạy Bedrock cho nội dung agency.
   - Mặc định đề xuất: **Agent sửa annex 3 trong một root PR ($0) ở S280**, gắn với mục data page của AA-970. Bản sửa chỉ là kỹ thuật. Việc có đưa luật sư xem hay không là quyết định của business owner qua Jira lúc chốt phiên.

**File liên quan đã đọc:**
- `/home/nghiep/projects/AA-Ecosys/docs/backlog/tracker/plan.json`
- `/home/nghiep/projects/AA-Ecosys/docs/backlog/README.md` (§1–§3)
