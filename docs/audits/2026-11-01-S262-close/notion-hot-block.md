## S262 (31/10–01/11/2026, Claude Code — Ultracode, WSL): dọn In Progress, cổng AI v2 live (registry, ngân sách, probe acc2), CRM 7 issue Done, video review CRM, AA-997 đóng

**Quyết định của Nghiệp**

- Mở phiên: agent chọn 20 việc, trọng tâm dọn In Progress + dựng cổng AI cho hoàn chỉnh; "việc nào cần tôi thì duyệt cho làm luôn theo kế hoạch".
- 19:25 luật TL cho các mục review kiến trúc S261: "cái nào không tốn tiền thì duyệt làm luôn và kỹ thuật không quá phức tạp; còn cái nào tốn thêm tiền và phức tạp thì không duyệt, ghi note tính sau" → bảng phân loại `docs/audits/2026-10-31-S262-tl-decisions/` (làm: TL-1, TL-3 phần trần ≤ 8 In Progress, TL-4, TL-10 phần luật, TL-11, TL-13, TL-15, TL-24, TL-25; AA-922 → track đóng băng).
- "Dùng gpt api diễn tập gọi nhỏ" → diễn tập OpenAI API qua cổng.
- "Làm tiếp đi còn nhiều ram" / "còn nhiều ram thì đẩy tốc độ" / "cứ làm bình thường … khi nào hết tôi switch acc" → chạy tới 6 lane song song; đổi tài khoản Claude 2 lần rồi "tiếp tục".
- Duyệt Infra #568 (2 alarm break-glass CRM, ~0,20 USD/tháng) và Infra #575 (2 alarm Module 8 + BOOKING_ADMIN_URL, ~0,20 USD/tháng). Tắt auto mode 2 cửa sổ (Terraform Apply #553; ghi secret + apply + user E2E của AA-1019).
- 09:00: 7 nháp Jira **không đăng trong S262**, gom sang S263.
- 10:56: duyệt plan video kiến trúc ẩn danh (tài khoản cá nhân, kiểu engineering notes + blog kỹ thuật FB; mặc định giọng nam am_michael, nêu tên dịch vụ AWS, không nêu hãng model/vendor ngách, TripPlanner theo luật dev-phase); duyệt tạo AA-1020 (docs kiến trúc, slot S263) và AA-1021 (series video, pipeline + gate S264, pilot Ep1 S264–S265, ~2 tập/phiên S265–S267).

**Kết quả chính**

- **Done 17:** AA-964, AA-1013, AA-971, AA-1015, AA-1017, AA-804, AA-642, AA-1018, AA-1016, AA-952, AA-956, AA-954, AA-1009, AA-997, AA-1019, AA-957, AA-1014 (nhiều issue Done-with-scope, phần còn lại + trigger ghi trong Linear). In Progress còn 3: AA-896, AA-820, AA-900. Sang Backlog: AA-873, AA-1004, AA-922.
- **Cổng AI v2 (AA-642/1017/1018/804/1016):** mig 318–324 (CIS #1196, #1200, #1202, #1203, #1207, #1209; Infra #552, #559, #563, #571), code #1197, #1198, #1201, #1204, #1206 (lõi aa_llm dùng chung, TP #203 / Partner #158), #1208, #1210; UI providers/Calls/trace/ngân sách tenant #1195, #1199, #1205, #1211. Live: route hash LLM-only không đổi; registry v2 đủ nguồn; trần ngân sách connection chặn live 0 USD; tenant T-stage dừng chờ duyệt + chuông; chuông `llm_circuit_open`; diễn tập OpenAI ~0,000015 USD/lượt có dòng sổ v2; 5 model ứng viên acc2 (nova-lite, nova-2-lite, llama4-maverick, llama4-scout, kimi-k3) probe OK ≈0,0016 USD, **chưa route**; TP ghi `app=tripplanner`. Probe hằng ngày `LLM_DAILY_PROBE=on` (Infra #574).
- **TripPlanner (AA-1015, TL-24):** TP #198 fail-closed, #199 tp-023 limits, #200, #201 BotID Basic (curl/headless 403, headed 200) + cache narration master; burst 35 search → 30×200 + 5×429; `TP_DAILY_SPEND_CAP_USD=5.0` (Infra #553).
- **CRM (Partner):** AA-964 stub AI draft (crm-032, #152/#153); AA-971 (crm-033, #156/#157); AA-956 ops release (crm-034, #160/#162, alarm T-21 bắn thật); AA-954 PWA (#161, E2E 6b PASS); AA-957 hoa hồng + huỷ trip (crm-035, #165–#170, 3 vòng kiểm live); AA-1019 staff console S-02/S-04 (Infra #577, root #419 ADR 0006a A10c, Partner #164/#171; đăng nhập staff thật, revoke 403, break-glass mail + alarm, release live 74c05c77); AA-952 nhắc nợ + link hết hạn + tiền đến muộn; E2E Dev 9/9 xanh (#163); tải CSV token 30′ sửa (#172, root #423).
- **Booking AA-1013** (#163) live F1/F3 PASS. **AA-1009** UAT harness: dry run 23/23 PASS, record TP-02 PASS (root #415/#416).
- **AA-1014:** longform CRM-REVIEW_20261101_v1 (19:53, 21 chương, EN+VI) + highlight 8:30 lên Drive (rclone check 0 khác biệt); bảng kết quả `docs/audits/2026-11-01-S262-crm-review-video/`.
- **AA-997 Done-with-scope (TL-25):** chuỗi aa997.4 xong 1.024 dòng 0 lỗi; CIS #1213 (unhide P15); `hide_flagged` confirm 4919a61f (ẩn 2.517 dòng, 1.187 gắn tour); SERVED 88,0 % (phủ 50,8 %), gate toàn bộ 79,6 % FAIL như dự kiến; trả 3 dòng regressed.
- **Vệ sinh:** Secret Scan root xanh (#399); DB Freshness Probe 111 → 0 (CIS #1194, Infra #551, relink 0 USD); schema-ref tự cập nhật.
- **AA-896:** báo cáo chi phí tháng 10 SƠ BỘ ~471,70 USD (AWS acc2 202,85 + AI 268,85), +165 % so với tháng 9 → `docs/audits/2026-11-01-S262-capacity-review/` (bản chính thức ≥ 03/11).
- **AA-900** phần 0 USD (prompt register + CI gate + Experiments); **AA-820** phần kỹ thuật (danh sách nhà cung cấp + nháp điều khoản).
- Audit kiến trúc: tài liệu chưa as-built (ecosystem-architecture, sơ đồ, trang gateway, CONTEXT 4 app + Infra) → AA-1020; plan video 10 tập `docs/audits/2026-11-01-S262-arch-video-plan/`.
- Bài học S262 đã chuyển vào `skill/aa-lessons/lessons.md`; zip skill aa-lessons / aa-session / aa-ship / aa-uat-video; Linear export + archive 18 issue.

**Trạng thái kiểm cuối phiên** (snapshot 01/11 ~04:07Z, `docs/audits/2026-11-01-S262-close/state-snapshot.md`)

- ECS COMPLETED 1/1, revision mới nhất = đang chạy ở cả 6 family: cis-api :956 + worker :522 `dev-0982cbd9` (cùng SHA); booking :91 `16fbed68`; crm-api :107 `f2f72e92`; crm-web :81 `d395b7ac` (có STAFF_*); crm-portal :25 `7e452205`.
- Migration: CIS **324**, **bk-035**, **tp-023**, **crm-035** (khớp db-schema-reference). Health/ready 200 hết; CRM web `staff_auth_configured=true`; TP web `4fd7dcab`, Lambda browse/assembly/jobs cùng gói từ TP `c845b623`.
- Vercel Production: CIS admin `67668f85`, Booking admin `16fbed68`, TripPlanner `4fd7dcab` (các PR sau chỉ backend). Portal không còn project Vercel (ECS).
- Bảng job (điều phối kiểm 11:04 +07): `shared.job` idle, `booking.job` idle, `crm.job` 2 queued (job định kỳ); 0 wave.
- Repo head: root `4a4f32c3`, CIS `0982cbd9`, Booking `16fbed68`, TP `c845b623`, Partner `d395b7ac`, Infra `1370c7b5`; CI nhánh mặc định xanh (chỉ Dependabot Updates CIS/TP đỏ). PR mở: root #374 bot, #328 cũ; CIS #1212 dependabot, #1179 release; Booking #164 / Partner #159 kit-sync; release bot TP #196, Partner #133, Booking #161.
- Cố ý BẬT: `LLM_DAILY_PROBE=on` (api + worker); `hide_flagged` confirmed; CRM staff console + user E2E `e2e-crm-staff`; TP BotID Basic + trần 5 USD/ngày; 22 alarm aa-crm-dev OK (4 mới), chỉ AlarmLow autoscaling CIS ở ALARM (bình thường); model ứng viên acc2 chưa route; lượt dữ liệu video `rv202610317` giữ lại. MFA tới ~19:32 +07 01/11.

**Việc cần làm đầu phiên sau (S263)**

1. Nháp Jira 7 đích (`docs/audits/2026-11-01-S262-close/jira-drafts.md`, gồm nháp S261) → Nghiệp duyệt một lần → đăng (PR-20 báo cáo tuần từ thứ Hai 02/11).
2. Kiểm probe hằng ngày đầu tiên (≥ 05:00Z 01/11) có dòng sổ + chi phí đúng mức; xem kết quả đối chiếu mục review S261 (N1–N25/G1–G17) ↔ issue + thiết kế sync plan.json ↔ Linear (workflow chạy lúc chốt phiên).
3. Dọn còn lại của chốt phiên nếu chưa xong: pull 5 checkout sau origin, 72 worktree + nhánh lane đã merge, 12 script S3 từ 31/10; quyết PR bot kit-sync Booking #164 / Partner #159, root #374, #328.
4. AA-1020 docs kiến trúc as-built (lane docs) song song CRM W6: AA-959, AA-960.
5. AA-896 báo cáo chi phí tháng 10 CHÍNH THỨC (≥ 03/11) → đóng.
6. AA-820 (luật sư + báo tenant, chị Thư qua Jira), AA-900 (nhãn 40 mẫu + chạy thử trả phí khi có LLM) — giữ, chỉ làm khi hết chặn.
7. Follow-up nhỏ: narration master trả `cached=false`; R15 tải CSV đã sửa → theo dõi ở lượt video sau.

**Lưu ý kỹ thuật**

- CRM staff console đăng nhập Cognito WORKFORCE qua `portal.` (client crm-staff); trước khi ghi đủ secret staff thì KHÔNG chạy Terraform Apply nào chạm task def web (nó map key chưa có → deploy web kế tiếp hỏng). Thứ tự: ghi secret → apply → tạo user E2E → merge web.
- Đường "Test" của cổng AI cố ý bỏ qua trần ngân sách connection; muốn chứng minh trần chặn phải gọi `generate` (ConnectionBudgetExceeded, 0 USD). Đặt trần thử xong nhớ trả về NULL.
- Model ứng viên acc2 (mig 324) là miền sự cố thứ hai cho chấm/kiểm (judge/validate) khi acc3 lỗi — đã probe nhưng chưa route; route cần quyết định riêng.
- Mốc giờ trong checklist S262 có đoạn ghi lệch (đã chú thích trong file); khi đối chiếu dùng mốc Z của GitHub/Linear.
