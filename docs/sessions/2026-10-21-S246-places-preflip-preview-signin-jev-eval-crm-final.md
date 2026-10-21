# S246 — 21/10/2026: AA-847 xong phần trước lật, đăng nhập Preview Booking, Q-2 + đóng băng lessons, đánh giá Jev, CRM chốt thiết kế + 53 issue

**Tác nhân:** Claude Code (Ultracode, nhiều workflow và subagent song song; agent điều phối tự merge/deploy/verify theo luật giai đoạn dev).

## Trạng thái cuối phiên

- **ECS (kiểm 21/10 ~16:35 UTC):**
  - CIS api và worker cùng image `dev-47ae118f` (CIS #904), rollout COMPLETED; `/health/ready` schema 260.
  - CIS #903 (gateway fix cho Claude 5.5) đã live; smoke 16:29 UTC: Haiku 5.5 + Sonnet 5.5 OK trên acc3 (cả plain và schema).
  - Booking `aa-booking-dev-api:35`, image `dcb9936` (Booking #54), rollout COMPLETED.
- **Migration đã apply trên Dev trong phiên (DB Migrate, check → apply, bảng job rảnh mỗi lần):** CIS 253, 255, 256, 257, 258, 259, 260; tp-017; bk-018; tp-016.
- **Repo:** main các repo con: CIS 47ae118f, Booking dcb9936, TripPlanner 6675519, Infra 3e81ce1. Root `master` + nhánh `docs/s246-master-plan` (PR đóng phiên này).
- **Linear (đọc lại cuối phiên):**
  - Done trong phiên (8): AA-844, AA-876, AA-877, AA-927, AA-729, AA-925, AA-915, AA-821.
  - In Progress: AA-847, AA-911, AA-845, AA-803 (mở lại, phạm vi mới), AA-886, AA-816, AA-903, AA-779, AA-780.
  - Backlog (giữ theo quyết định chất lượng): AA-926, AA-916, AA-924, AA-790. AA-905 Backlog.
  - Mới: AA-928…AA-980 (53 issue CRM, project "Partner CRM — AA-Partner"). Quota Linear: 90 → 143/250 chưa lưu trữ.
- **Kế hoạch phiên:** chốt 20 issue (plan.json S246→S249). **Kết quả: 8/20 Done**; 8 issue có phần đã ship nhưng còn mở (AA-847, AA-911, AA-845, AA-886, AA-816, AA-903, AA-779, AA-780); 4 issue giữ lại theo quyết định của Nghiệp (AA-926, AA-916, AA-924, AA-790). Ngoài kế hoạch: AA-803 mở lại và đánh giá xong 25 câu Jev; 53 issue CRM.
- **Chi phí trả phí có ghi trong phiên** (theo `llm_call_log`): AA-729 chạy lại score-only $0,205; drill Jev AA-925 $0,007; kiểm WM-01 AA-915 $0,056; thử model nơi chốn AA-847 $0,056; smoke model mới $0,0001.

## Quyết định của Nghiệp (trong phiên)

**Đầu phiên và CRM**
- Bật Ultracode. Chốt 20 issue: AA-925, AA-729, AA-779, AA-926, AA-915, AA-916, AA-927, AA-780, AA-924, AA-790, AA-845, AA-816 (A10), AA-911, AA-821, AA-886, AA-876 (không WAF), AA-877, AA-847, AA-844, AA-903.
- CRM: duyệt 16 đề xuất (R1–R10 vào thiết kế; R11–R14 vào bảng hỏi chị Thư); sau đó R15 (đặt giờ gọi + đồng bộ lịch) và R16 (PWA offline) đổi thành "thêm vào CRM luôn".
- CRM R17–R44: duyệt cả 28 = a; R41, R42 thêm vào thiết kế (đề xuất là để sau); R38, R43, R44 vào bảng hỏi chị Thư.
- Bảng hỏi CRM v2: chọn 12/12 theo khuyến nghị; **chưa gửi chị Thư, coi như đã chốt** (Nghiệp tự trao đổi sau), dùng ngay cho thiết kế.
- CRM v3: D1–D8 = a; D5 ghi "Làm luôn". Trang UI CRM <https://claude.ai/artifact/2mCk7BrajpTpLEFao7PRt3>: Nghiệp đã mở General access = Anyone at org (Editor). Jira: đưa link trang này vào comment Jira PR-19 cho chị Thư thay vì gửi lẻ qua Zalo.
- Cuối phiên: soạn draft Jira cho mọi việc liên quan theo `aa-jira-update`, gom một lần.

**Chất lượng nội dung**
- 14 câu quyết định chất lượng: duyệt hết, kèm nhận xét "các cách làm chưa mang lại hiệu quả và chất lượng nội dung thực sự, cần suy nghĩ tư vấn kỹ". Tạm giữ việc chất lượng có phí / code mới (AA-916, AA-924, AA-790, chạy lại có phí) tới khi có bản tư vấn; sửa lỗi rõ ràng vẫn làm.
- Tư vấn chất lượng: Q1 a (S1 trước; QS registry/taxonomy + WM P1+ sau; giữ AA-915). **Q2 b** (tiếp tục tinh chỉnh T9 song song). Q3 a. Q4 a ("cần tư vấn kỹ, chưa chắc A/B sẽ có hiệu quả"). Q5 a. Q6 a. Q7 a (tắt Jev văn xuôi, Jev chỉ A3). Q8 a ("chưa biết sao"). AA-926 giữ nhánh, chưa merge.
- Q4/Q8 follow-up: P1–P5 = a (thước đếm lỗi nghĩa + so cặp mù; sàng 3 model trên 12 tour rồi A+ vs W; nhánh E trang ngắn vào A/B; luật dừng; chưa gửi đề xuất biên tập cho chị Thư tới sau A/B).
- adventure.asia W1–W5 = a. W5: site do nhân viên AA viết — "bỏ qua đi, tập trung làm CIS để cho tenant dùng".
- AA-790: rubric xác định làm gate; LLM judge chỉ để đo/hiệu chỉnh.
- AA-803: thay vì tắt hết câu Jev văn xuôi theo Q7, đánh giá từng câu trên dữ liệu thật. Sau đó **đồng ý hết đề xuất** (25 câu). Báo nút Duyệt trên trang không hoạt động.

**Các issue khác**
- OpenBA-Kit: duyệt 29 mục. D14, D16, D19, D21 → áp dụng (đề xuất là để sau); D15, D17, D18, D20 để sau; D22–D29 bỏ.
- AA-816 A10: giữ mail ngoại lệ E2E (`e2e@e2e-mail…`) tới khi code xong toàn bộ dự án; không tạo mail @adventure.asia mới; 4 nhánh A10 giữ local.
- AA-847: tuyến phải **vẽ đúng** (không ẩn, không vẽ vòng tròn); gộp trùng phải **tự động** đúng (không admin gộp tay). L1, L2, D1–D5 = a. Ship trong phiên. Cuối phiên: **chuỗi lật dời sang phiên sau**.
- AA-911: phương án (a) domain Preview cố định, khai callback Cognito một lần, rồi gỡ cầu nối CIS → Booking. Không tạo issue tài khoản máy cho Preview Booking. Gate mới cho việc gỡ cầu nối: agent đăng nhập Booking (và CIS) qua Cognito bằng user E2E + spec Playwright xanh. Cuối phiên: **P5–P8 (gỡ cầu nối) để tới khi hết dự án**, như A10; P1–P4 đã ship giữ nguyên.
- AA-886: phần pháp lý chưa duyệt, **chưa vội** — giai đoạn này ưu tiên kỹ thuật; không đẩy pháp lý trong Jira/plan; issue giữ In Progress.
- Model Bedrock: "làm luôn" (refresh catalog + thử model). Cuối phiên: làm ngay model/gateway, luật bữa ăn (rồi tắt `a1_claim_supported` + promise, đóng AA-845), đóng phiên.
- Nhìn tổng thể các app (portal đã tách repo chưa) → master plan song song S247–S262.

## Kết quả chính (bằng chứng)

**Done**
- **AA-927** (CIS #888): mỗi lời gọi LLM đúng 1 dòng `llm_call_log`. Chạy lại AA-729 (run `2b98f2f2`, api :737): 210 call = 210 dòng, `unlogged_llm_calls` = 0, chi phí log $0,205361 = tính local. Guard AST + test hành vi.
- **AA-876** (CIS #889, Booking #52, TP #118, Infra #247/#249): 22 POST login sai → 20 × 401 rồi 429 `retry-after: 875`; throttle stage `*/*` 50/100, login 20/40, content GET 300/600; `/booking/openapi.json` và `/booking/docs` 403, `/booking/health` 200; CORS không trả `access-control-allow-origin` cho localhost; header CSP/nosniff/HSTS/… trên admin, portal, TripPlanner. WAF chuyển sang AA-908. Follow-up nhỏ: Booking admin thiếu CSP + Permissions-Policy.
- **AA-877** (Infra #245/#250, Booking #53 bk-018, TP #119 tp-016, root #148): 86 cột có tag, 0 ứng viên chưa tag ở booking/tripplanner; RoPA sinh từ tag (64 dòng).
- **AA-844** (Infra #246/#251, CIS #890): CDN `img.lumiguides.it.com` 200 + `x-cache: Hit`, S3 trực tiếp 403; `/content/photos/{id}` 302 sang CDN; gọi schedule đúng input → 7 job `photo_sync` `scheduler:aa-844` succeeded, 0 lỗi.
- **AA-729**: số trước/sau trên fixture 1.1.0 (S245 8f07b98f vs S246 2b98f2f2, $0,205): tổng lệch 43,6% → 46,8%, S1 không đổi (đúng kỳ vọng vì score-only không chạy writer/repair), T2/T9 dao động 1–2 mẫu; injection 10/10.
- **AA-925** (CIS #891, #893, #894): Q0 chặn PR demo #892 (đóng, không merge); oracle trên 892 tour published: 79 tour có lỗi ngày (8,9%); drill ép Jev hỏng (one-off task api:738, tour `9cf4b325`): `degraded = jev_unavailable` (138), `DEGRADED_DETECTOR`, `manual_check`, không publish; $0,007.
- **AA-915** (CIS #887, root #145): WM-01 PASS (api:739): `shared.pipeline_lessons` n_tup_ins 0 / idx_scan 1960 không đổi giữa 2 snapshot sau 1 lượt S1 thật + 1 rewrite T2 thật; $0,056. Tiêu đề Linear sửa thành app ADR 0010.
- **AA-821**: thiết kế CRM cuối (`docs/audits/2026-10-21-S246-crm-design-v3/final/`: thiết kế kỹ thuật, brief song ngữ, UI mockup) + 53 issue AA-928…AA-980 (map `linear-issue-map.json`). Linear Done 12:11 UTC.

**AA-847 — Places L4 + lật PLACES_SOURCE (In Progress)**
- Toàn bộ phần trước lật đã ship:
  - Migration trên Dev: CIS 253 (09:12), 255 (09:20), 256 (09:24), 257 (09:28), tp-017 (09:32), CIS 258 (11:49 UTC). Schema reference regenerate (root #150). DB Isolation Probe xanh sau mỗi apply.
  - Code: CIS #895 (migration), #896 (validity gate, line places vẽ thành đường, gộp trùng tự động; `/health/ready` schema 257), #897 (258 `raw_tours.source_key`); TP #120 (tp-017), **TP #121** (6c + 6d + redirect điểm đã gộp + sửa routes / route candidates, merge 6675519; Lambda + Vercel deploy xanh).
  - Probe (Infra #252–#258): **parity 21/21** (trung vị 3 lượt, run 39605461922). `assembly_route_candidates` Laos 886 → 25,4 ms (legacy 25,9); `routes` Laos 488 → 87 ms; HNSW dùng `tour_place_embedding_hnsw`.
  - **Contract pins v1.2: Infra #259** (Contract Copy Guard xanh).
  - Dưới `PLACES_SOURCE` legacy: `/`, `/destinations/laos`, `/destinations/vietnam`, `/plan` 200; `/api/browse?resource=shapes&level=lo` 200 `shapes: []` như mong đợi trước lật.
- **Kiểm bật/tắt tour: PASS** (13:59–14:05 UTC, tour `2bc45c55` Laos North to South): tắt → 6 view giảm đúng (`v_tour` 892 → 891 …); bật → `place_extract` `skipped_unchanged` ($0) + graph 46 tour + tính lại route.
- **Thử model cho pipeline nơi chốn** (Laos, 3 tour, 37 ngày, 24 call, $0,056; luật: anchor/overnight trên ngày đã quyết ≥ 0,95 và locate trong bán kính ≥ 0,95 so với Sonnet): **cả 3 model dưới ngưỡng**.
  - Haiku 4.5: anchor 0,89, overnight 0,95 (0,947), locate 0,53.
  - GPT-6 Luna: 0,79 / 0,74 / 0,76.
  - GPT-5.6 Luna: 0,84 / 0,74 / 0,76.
  - Nghiệp chốt: chỉ Haiku hoặc Luna, **dùng Haiku 4.5 hiện có** → CIS #904 (migration 260, Infra #263) apply 16:22 UTC: hai stage `haiku`, fallback `sonnet`, bỏ shadow. Rủi ro: locate lệch hơn (trung vị 21 km so với 5 km) → nhiều tên rơi `llm`/area hơn; S247 build 1 nước trước rồi đếm `located_by`.
  - Trial Haiku 5.5 (16:31 UTC, $0,01): locate trung vị 4,3 km (≈ Sonnet), nhưng 2/3 call days lỗi `max_tokens` (thinking ăn trần 4000) → chưa so được; S247 chỉnh effort/max_tokens rồi trial lại (`bedrock-models/place-trial-haiku-5-5.md`).
- Lưu ý: Linear tự đóng AA-847 lúc 11:39 UTC vì tiêu đề "fix: AA-847 …" (Infra #255, root #151); đã mở lại (bài học mới).
- Còn lại (chuỗi lật, phiên sau): lượt place có phí (AA-905 báo giá) để coverage gate về 0 thiếu (hiện 66 tour live thiếu trong CIS); Nghiệp sửa tay `PLACES_SOURCE` trên Lambda browse TP và `PLACE_SHAPES_ENABLED` trên CIS; parity + ảnh sau lật; cửa sổ 7 ngày.

**AA-911 — đăng nhập Preview (In Progress)**
- P1–P4 đã ship:
  - P1 CIS #899: route ghi của BFF từ chối request cross-site trước khi đọc session.
  - P4 CIS #900: bước từ chối của Cognito E2E nhắm được host Preview Booking.
  - P2 Infra #260: Cognito client chỉ cho Preview + DNS cho 2 host Preview cố định (6 add / 0 change / 0 destroy, $0/tháng).
  - P3 Booking #54: đăng nhập staff trên host Preview cố định qua client Preview chỉ-đọc; deploy Booking :35. **Đăng nhập Booking Preview đã verify.**
- Branch `preview-signin` tạo = main và khoá bằng GitHub ruleset (Vercel cần branch có thật mới gắn domain).
- P5–P8 (gỡ cầu nối CIS → Booking, xoá signing key, xử lý 3 dòng `booking.staff_users` thời cầu nối, docs root) **để tới khi hết dự án** theo Nghiệp; nhánh local giữ nguyên trong `.tmp-session/wt/aa911-*`, kế hoạch `.tmp-session/aa911/ship-plan.md`.

**AA-803 — đánh giá câu hỏi Jev (mở lại, In Progress)** (`docs/audits/2026-10-21-S246-jev-question-eval/`)
- 25 câu: giữ 9, chỉnh ngưỡng 2, tắt mới 5 (3 câu sau một bước kiểm $0), 9 câu T-series giữ OFF. Nghiệp duyệt hết.
- Đã áp: `a1_brand_fit` OFF (J06); `a1_keyword_about_tour` reject 0,30 → 0,40, accept giữ 0,80 (J07, threshold_version 2); `a3_question_foreign` OFF (J16: chỉ 0,45% câu nước ngoài).
- J09: luật lodging bỏ sót 24 reject, cả 24 là câu tìm khách sạn → **giữ** `a3_idea_traveller` enforce.
- J04: trust gate FAIL (55% unit không có verdict; 71 waiver bị sót) nên không quyết tự động. Jev miễn mã bữa ăn cho 71/914 tour (7,8% > 5%) → theo luật đã duyệt: ship luật bữa ăn trước, rồi mới OFF `a1_claim_supported` + `a1_promise_unsupported`. **Luật bữa ăn đang làm** (worktree `cis-aa803-meal`, chưa có commit).
- Chi phí Jev ước sau đề xuất: ~$1–1,5/tháng (hiện ~$3,5–4).

**AA-845 — Jev (In Progress)**
- CIS #898 (deploy c81b978b): cảnh báo credit thấp (< $3, kiểm 30 phút/lần) + e-mail khi hết credit (402), dedupe 1/loại/ngày; sweep 402 bắt cả `credit_exhausted%`.
- Verify bằng mail test: kiểm thật $8,19 còn lại → không cảnh báo; ép test (`threshold_usd: 1000`, `test_exhausted_alert: true`) → 2 job `ops_alert_email` `sent` tới người nhận cảnh báo + 2 thông báo admin.
- Panel (`docs/audits/2026-10-21-S246-eval-panels/aa-845.md`): không trần reject nào đạt (0,15/0,20 chỉ 47–48% là vi phạm thật) → giữ `reject_ceiling` NULL; 402 do credit TypeSafe trả trước hết 2 lần (03/10, 10/10).
- Đóng khi luật bữa ăn ship và `a1_claim_supported` OFF.

**Làm mới model (Bedrock + gateway)** (`docs/audits/2026-10-21-S246-bedrock-models/`)
- Liệt kê model 3 account × 3 region: cùng danh sách (us-west-1 40, us-west-2 92, us-east-1 95). Mới nhất: Haiku 5.5, Sonnet 5.5, Opus 5.5, GPT-6 Luna/Sol. Catalog thiếu Haiku 5.5/Sonnet 5.5; route acc2 của `sonnet` trỏ Sonnet 4.5 LEGACY.
- IAM: Infra #261 (role invoker được gọi Haiku 5.5 + Sonnet 5.5), apply trên acc3 và acc1.
- CIS #902: thêm Haiku 5.5 + Sonnet 5.5 vào catalog, bỏ profile Sonnet 4.5 acc2 cũ → **CIS 259** (Infra #262) apply Dev 15:41 UTC.
- Smoke: 14:59 UTC OK trên acc3; 15:56–16:00 UTC bị từ chối "aws-marketplace:Subscribe" (kể cả user admin) — lần gọi đầu khởi động subscription Marketplace nền, role invoker không có quyền Marketplace nên subscription hỏng; sau `create-foundation-model-agreement` (15:58, admin) khoảng 30 phút thì có hiệu lực → 16:29 UTC OK cả 4 lượt. Không cần nhờ eCloudvalley (nháp giữ làm hồ sơ). acc1 vẫn báo "not available for this account".
- **Gateway fix CIS #903** (structured output của Claude 5.5 dùng auto tool choice): live, smoke schema OK.
- A/B 7 stage `gpt-5.6-luna` → `gpt-6-luna` (fixture 1.1.0, n=10/stage, ~$0,65): **giữ nguyên cả 7**. 6 stage dưới ngưỡng; `t2_brand_audit` đạt ngưỡng nhưng GPT-6 chỉ bắt nửa số lỗi (4 so với ~8), chậm 3 lần, tiết kiệm ~$0,0003/call → không đổi judge (`bedrock-models/stage-ab-gpt6.md`).

**AA-886 — pháp lý (In Progress)**
- `/privacy`, `/terms` 200 trên TripPlanner và portal (nhãn "Draft — pending legal review"); kiểm consent lần đầu (run-script 39596391333, chỉ đọc): 0 consent thiếu thời gian, 0 lệch giá trị/thời gian/nguồn trong chuỗi TP → Booking.
- Gói tài liệu root #144. Còn: upload GDrive (connector Google Drive cần đăng nhập lại). Theo Nghiệp: chưa vội.

**Issue khác còn mở**
- **AA-779** (`eval-panels/aa-779.md`): bộ 200 câu PAA có nhãn (κ 0,913). Không ship nhánh luật (không hơn main: McNemar p = 0,68, sai 49/60 bẫy vòng 2). Main cũng chưa đạt (precision KEEP 0,64). Khuyến nghị phương án LLM nhỏ (~$0,18 cho 200 câu với Haiku), ship chỉ khi qua ngưỡng.
- **AA-780** (`eval-panels/aa-780.md`): chỉnh, chưa đóng. Sàn 120 từ đạt (bài ngắn nhất 149 từ); light 4/15, false pass 11, Trail Pulse 1/3 không đạt; đa số lỗi ngoài phạm vi AA-780.
- **AA-816**: A10 dời cuối dự án (comment Linear 04:34 UTC); S2 (tắt cờ legacy API) chờ AA-911.
- **AA-903**: sửa đã có trên main 3 repo từ 19/10; chưa có PR Dependabot chạm path Vercel để làm bằng chứng. Cuối phiên có **CIS #901** (Dependabot, `/frontend`) đang mở — ứng viên bằng chứng.

**Tài liệu và audit (repo gốc, PR này)**
- `docs/audits/2026-10-21-S246-*`: master-plan, crm-design-v3 (+ final), crm-more-ideas, thu-questionnaire, content-quality-advisory (kèm adventure-asia house style), eval-panels (AA-779/780/845), jev-question-eval, bedrock-models, aa847 + aa847-lines-dedupe, legal-packet, openba-kit, jira-drafts.
- Master plan S247–S262: 9 lane song song (L0–L7, LP), 16 phiên, 11 mốc (thêm C-M1, P-M1, C-M2, C-M3).
- Tracker chuyển sang artifact của tài khoản hiện tại <https://claude.ai/artifact/2VSP2stGG1TF7uXvqgQTUY>.
- Bài học mới trong `skill/aa-lessons/lessons.md`: tiêu đề PR `fix: AA-xxx` tự đóng issue; reset test phải đặt lại đồng hồ module; `method_path` API Gateway; check theo nhãn khi rerun; Vercel cần branch có thật.

## Còn lại / việc phiên sau (S247)

**Thứ tự đề xuất**
1. **AA-847 chuỗi lật.** Model đã chốt: Haiku 4.5 (migration 260). Tuỳ chọn trước: cho place stage gửi effort/max_tokens hợp với Claude 5.5 rồi trial lại Haiku 5.5 (rẻ hơn 3 lần, locate ≈ Sonnet) — đổi thì Nghiệp duyệt. Build 1 nước trước, đếm `located_by` geoapify/llm; tăng mạnh thì chỉ đưa `a3_place_locate` về Sonnet. Sau đó báo giá + Nghiệp duyệt lượt place có phí (AA-905; ~$1–10), chạy để coverage gate về 0, Nghiệp sửa tay `PLACES_SOURCE` (Lambda browse TP) + `PLACE_SHAPES_ENABLED` (CIS), parity + ảnh sau lật, bắt đầu cửa sổ 7 ngày.
2. (đã xong trong S246) #903 live + smoke.
3. **AA-803 / AA-845:** ship luật bữa ăn, rồi OFF `a1_claim_supported` + `a1_promise_unsupported`; đóng AA-845 (và AA-803 khi xong J-items).
4. Các slot S247 còn lại của master plan: L1 S1 bước 0/1 ($0: bảng dữ kiện, bộ kiểm code trên 50 bài S1, panel chấm lại ×2); L6 AA-928 (ADR AA-Partner, contracts, errata, re-scope AA-813, memo lõi thương mại Booking) + AA-929 + AA-930 (chỉ docs/root).
5. **AA-903:** kiểm CIS #901 — job "Vercel deploy" phải skipped, required check xanh → đóng.
6. (đã xong trong S246) A/B 7 stage → giữ nguyên; chỉ xem lại với n ≥ 30 + recall theo mã lỗi.

**Chờ Nghiệp**
- Duyệt + đăng draft Jira (`docs/audits/2026-10-21-S246-jira-drafts/README.md`), gồm link trang UI CRM cho PR-19.
- Sửa tay biến môi trường lật AA-847 (có gạch dưới — sửa trong VSCode/console); duyệt báo giá AA-905.
- AA-886: upload gói pháp lý lên GDrive khi tiện (không vội).

**Để tới cuối dự án**
- AA-911 P5–P8 (gỡ cầu nối) và AA-816 A10 (mail ngoại lệ E2E).

## Lưu ý kỹ thuật cho phiên sau

- **Lệch phát hiện đầu phiên:** ECS lúc đó là api :731 / worker :288 (memory ghi :730/:287); plan.json còn AA-889/AA-890 In Progress dù Linear Done; AA-886 Linear In Progress (plan ghi Backlog).
- **Pipeline nơi chốn:** `a3_place_days` / `a3_place_locate` chạy Haiku 4.5 từ migration 260 (fallback Sonnet). Tour đã build không làm lại (model không nằm trong `days_hash`).
- **Haiku 5.5 / Sonnet 5.5 chỉ gọi được trên acc3.** acc1 (fallback) báo model không khả dụng cho account → nếu acc3 lỗi thì không có fallback cho hai model này.
- **Model Bedrock mới trên account mới:** lần gọi đầu khởi động subscription Marketplace; role invoker không có quyền `aws-marketplace:*` → tạo agreement bằng user admin (`create-foundation-model-agreement`) rồi chờ ~30 phút trước khi kết luận bị chặn.
- **Claude 5.5 + `max_tokens` nhỏ:** adaptive thinking tính vào `maxTokens`; stage đặt 4000 (place days) bị cắt → cần effort/max_tokens riêng trước khi route stage sang 5.5.
- **Kế hoạch đổi model qua admin:** `PATCH /admin/llm-catalog/{key}` chỉ sửa giá, `price_source`, `enabled`; thêm dòng mới hay profile Bedrock cần migration (như 259).
- **Probe AA-847:** phán parity theo trung vị 3 lượt; HNSW kiểm theo cấu trúc plan (forced plan), plan tự nhiên ở cỡ Dev là exact sort (chỉ báo cáo).
- **Hook subagent** chặn cả chuỗi lệnh có `gh run rerun` dù chỉ nằm trong heredoc/chuỗi văn bản → viết nội dung qua file rồi chạy.
