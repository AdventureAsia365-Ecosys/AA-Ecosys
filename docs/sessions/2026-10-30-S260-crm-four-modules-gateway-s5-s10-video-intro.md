# S260 (30/10/2026): CRM 4 module, gateway S5/S6/S9/S10, writing memory P3, nút kit, AA-997 ẩn điểm, video giới thiệu TripPlanner

Tác nhân: **Claude Code** (Ultracode; workflow lane: code trong worktree → 2 reviewer theo góc → sửa; tối đa 3 lane nặng
vì RAM). 30/10 15:00 → ~23:00 +07. Chạm hạn mức 5 h của tài khoản cũ ~17:50 → đổi tài khoản claude.ai, lane bị ngắt
chạy tiếp từ trạng thái worktree. MFA acc2: phiên 12 h (không phải 8 h như tên role), hết hạn 20:46, tech lead gửi mã,
làm mới tới 31/10 ~08:47. 3 cửa sổ tắt auto mode (Terraform apply Infra #521, #525; đọc cấu hình rclone/AWS). Số liệu
cuối: `docs/audits/2026-10-30-S260-session-close/state-snapshot.md`.

## Quyết định của tech lead (trong phiên)

- 15:00: agent tự chọn 20 việc từ master plan + tồn S259, coi như duyệt theo kế hoạch; chạy liên tục, không hỏi.
- 15:25: **AA-1004 chưa làm, chờ** (các tài khoản chưa có billing); chỉ kiểm LLM acc3.
- Lên phương án UAT video + audit thiết kế tổng thể khi code xong; ~16:05 **đồng ý thứ tự**: chạy thử nội bộ từ S261
  (kịch bản = test hồi quy), quay vòng 1 chính thức khi UI ổn định (AA-994) + có LLM + có quyền UAT E2E ghi.
- **TTS chỉ loại miễn phí chạy local** (Kokoro / Piper / thư viện mở), không Polly, không OpenAI TTS.
- ~19:00: giọng nữ tiếng Anh (Kokoro af_heart) hay; **tiếng Việt phải giọng miền Nam** (bỏ Piper vais1000 giọng Bắc) →
  chọn VieNeu-TTS v3 Turbo "Thục Đoan" (Apache-2.0). Tech lead muốn thu giọng của chính mình → hướng dẫn thu âm.
- ~19:10: làm **video giới thiệu TripPlanner 3–5 phút, bản EN + VI** để gửi chị Thư; ~20:15 **mỗi video một gói zip**
  (video, giọng đọc, phụ đề, kịch bản).
- Case AWS acc3 (Error 002): tech lead mở case + live chat; service team gỡ trong 3–5 ngày làm việc (~04–06/11).
- **Xoá khoá Anthropic chữ thường khỏi `~/.zshrc`** (đã xoá; tech lead revoke trên Console). Terminal: prompt hiện venv
  + acc:profile (vàng) + vùng (xanh); mặc định `AWS_PROFILE=aa365-admin` (acc2), vùng theo `~/.aws/config`, lệnh `awsp`.
- Câu hỏi gửi Hân (Sunny Cloud): tình hình → nhu cầu → câu hỏi; không dán link artifact nội bộ.
- Drive AdventureAsia: **thư mục theo loại việc**, gom video vào một thư mục `01 Video`; **cài rclone** (tech lead
  đăng nhập Google một lần) để agent tự đẩy file lớn.
- Dựng skill từ cách làm của phiên, **soi skill cũ để tránh trùng**, đóng gói zip cho claude.ai.

## Done / ship (code đã merge + deploy; issue vẫn In Progress theo Done-when, xem bảng Linear)

| Việc | Kết quả |
|---|---|
| AA-1002 S5 | CIS #1180 `459d4cda`, mig 311 (DB Migrate 41041084214 / 41041321869); live `/admin/llm-config`: 38 stage, đúng 8 có `vendor_direct`, 30 `aws_only`, 0 null |
| AA-1002 S6 | CIS #1181 `6d721cfc` (gitleaks báo nhầm nhãn model → tách dòng + gộp commit), mig 312 (41044219001 / 41044432518); `pricing.quote` + log cache/pricing_mode ở 38 call site |
| AA-1002 S10 / S9 | CIS #1190 `0be32ff8` (budget theo connection + đối soát chi phí đêm, mig 317 expand tự áp; 4 vòng sửa test integration cis_app) + #1191 `041ba9a2` (client OpenAI/Azure theo connection, key từ secret runtime); root #382 |
| AA-1003 | CIS #1182 `55828c5b` (KPI nightly_probes: liệt kê stream migrator rồi tìm theo tên, ~6 s thay vì timeout; TP-01, SEC-03/08, DEV-01/03, OPS-15) + Infra #521 (TF apply 41041898649, IAM kiểm) + root #371 (checklist OPS-17, SEC-10); chạy tay 6/6 báo cáo succeeded |
| AA-994 | CIS #1177 `539fc587` (biến thể nút kit core) → Kit Sync Booking #157 / Partner #129 / TP #194; Booking #158 (66 → 0 nút tự style, layout-mock 282/282); CIS #1183 S6b PR2 (672 → 659); bằng chứng live PASS |
| AA-952 | Partner #130 (crm-024) → #131 hoá đơn → #132 thanh toán/hoàn tiền; root #370; proof live: INV-000001, 409 `invoice_issued_for_row`, trả 200 + 340 → paid, Booked, hoàn 50 duyệt + executed |
| AA-955 | Partner #135 (crm-025) + #136 `021d68e6` e-sign v1; Infra #525 (TF apply 41055564948: kms:Sign/Verify RSASSA-PSS) + root #376; proof live: người giám hộ ký thay, sửa hash 409, sai mã 422, `seal.verified=true` |
| AA-967 | Partner #137 (crm-026) + #138 `7e9d8db0`; root #380; proof live: export 24/24, link dùng 1 lần, SHA khớp, erasure dry run (không xoá thật) |
| AA-961 | Partner #139 (crm-027) + #140 `3718242a` + Infra #533 + root #385; proof live: travelling/reach không lộ tên, reveal >5 không lý do 422, lịch đủ loại sự kiện, ICS tạo → 404 sau thu hồi; F4 (giờ lịch theo UTC) sửa Partner #142 `3a116512` |
| AA-921 / 922 / 923 | CIS #1186 (mig 313) / #1187 (314) / #1188 (315, nhãn `api-breaking` vì gỡ `/v1/rules` chỉ của staff) / #1189 (316 contract, Infra #532, DB Migrate 41070447288 / 41070702600) + Infra #527 + root #378; `staff_secret.py` bị lane cũ xoá nhầm đã khôi phục; tab Exemplars/Metrics live PASS; F3 tab Metrics tràn sửa CIS #1192 |
| AA-788 | CIS #1184 `484e0924` (3 công tắc env, mặc định TẮT tới hết freeze ~19/11); golden-set guard đỏ 2 lần (fixture thật → hư cấu; định dạng violation SUMMARY_OFF_BRAND); replay hold-rate qua ecsx chưa ra kết quả (>15 phút) |
| AA-997 / AA-990 | Audit giữa chừng 78,4 % (dự phóng ~80 %, FAIL mốc 90 %); CIS #1178 `hide_flagged` (3 vòng review, adversarial 4 lớn); báo cáo live 2.017 dòng (1.015 gắn tour), confirm 409 khi chuỗi còn queued; pin phục vụ 80,6 % → nếu ẩn 86,6 %; 5 chỗ đọc điểm ẩn sửa CIS #1185 / Booking #160 / TP #195; recheck_14 route 13/16 |
| Sửa nhỏ | CIS #1192 (tab Metrics), Partner #141 (câu xoá khách), TP #197 (bản đồ planner không bay tới nước — lỗi thật, `mapReady`), Partner #142 (giờ lịch) |

## Ngoài 20 việc

- **LLM:** probe 15:14 mọi đường vẫn chặn. acc3: Error 002 với mọi model (cả Nova), cả IAM admin, 2 vùng; use-case form
  đã nộp; acc3 không còn trong org; call thành công cuối 29/10 07:11Z. Đối chứng acc1 (độc lập): Bedrock chạy → khoá riêng acc3.
- **UAT video:** kế hoạch `docs/audits/2026-10-30-S260-uat-video-plan/` (EN + VI); thử PORTAL-PUB-01 6/6, TP-PUB-01 7/7 (v2 giọng Nam).
- **Video giới thiệu TripPlanner:** EN 3:57 + VI 4:14, 23 cảnh, quay trên app thật; gói zip 73 MB; đã đẩy lên Drive
  `01 Video/Giới thiệu sản phẩm/TripPlanner video giới thiệu (30-10-2026)/` bằng rclone, `rclone check` 14/14 khớp.
- **Bằng chứng live:** 5 lượt, `docs/audits/2026-10-30-S260-evidence/` (mục 1–9, finding F1–F4; F3, F4 đã sửa live).
- **Kế hoạch CRM W5–W8** lập lại theo nhịp thật (3–4 issue CRM/phiên); **bài học** chuyển vào `aa-lessons`.

## LLM / chi phí

LLM: $0 (mọi lệnh sinh văn bản bị từ chối). Đối chứng acc1: 3 lệnh × 5 token ≈ $0,00002 (tài khoản cá nhân).
Geoapify: chuỗi relocate theo credit ngày miễn phí. AWS: không thêm dịch vụ trả phí (KMS sign trên khoá sẵn có, vài lệnh).

## Sự cố / bài học (đã vào `skill/aa-lessons/lessons.md`)

1. Sinh lại `openapi.json` bằng venv local (fastapi/pydantic khác CI) làm mất schema ValidationError.
2. Script merge nền merge khi check còn đỏ (Infra #522); bản chép migration contract không tự merge (#532); bot cập nhật PR làm check chạy lại (#534).
3. Fixture dùng tên tenant/câu tour thật → golden-set guard; cách tìm cụm trùng không cần key (shingle 8 từ so với main).
4. gitleaks bắt nhãn model "anthropic-api-…" đứng sát nhau; quét từng commit nên phải viết lại lịch sử nhánh.
5. Guard `**billed_fields` của S6 bắt call site mới của lane song song.
6. Đổi số migration bằng `\b316\b` bỏ sót `316_tên`; FK mới tới bảng của 304 làm đỏ test replay 304; test cấp quyền tạm cho `cis_app` phải theo kiểu cursor của module.
7. ecsx > 15 phút không trả kết quả; cron GitHub chạy trễ hàng giờ; phiên MFA 12 h.

## Jira

Nháp gộp S258 + S259 + S260: `docs/audits/2026-10-30-S260-session-close/jira-drafts.md` (PR-25 Booking, PR-26 CRM,
PR-24 TripPlanner kèm link Drive video, PR-22 CIS) — tech lead duyệt ~22:45, **đã đăng** 4 comment: PR-25 #10563 (3 ảnh),
PR-26 #10564 (9 ảnh; bỏ ảnh lịch chụp trước bản sửa giờ), PR-24 #10565, PR-22 #10566.

## Việc cần làm đầu phiên sau (S261)

0. **Dọn In Progress trước mọi việc mới** (tech lead, 30/10 ~23:15: "phiên sau nên xử lý các inprogress quá nhiều rồi").
   Kế hoạch: `docs/audits/2026-10-30-S260-inprogress-triage/` — 31 issue: 0 đóng thẳng, 9 làm nốt, 13 bị chặn (về
   Backlog/Todo kèm blocker + trigger), 9 chia lại (Done-with-scope, câu chữ + follow-up gom vào **một trang quyết định**).
   Chưa nhận issue mới tới khi mọi issue In Progress đã đóng / làm xong / về Backlog.
1. AA-997: sau lượt relocate 31/10 → chạy lại báo cáo `hide_flagged` + audit → sửa điểm của 16 tour AA-990 → confirm ẩn;
   AA-990 recheck_14.
2. Lượt kiểm cuối S260 (mục 9, 22:38) đã PASS: AA-961 429 giới hạn reveal + giờ lịch theo đại lý, AA-923 `/v1/rules` 404,
   AA-922 tab Metrics không tràn, AA-1002 cột budget + bảng chi phí. Còn cho Done: AA-961 banner khi token đồng bộ lịch
   bị thu hồi + banner sự cố; AA-955 mã hết hạn bị từ chối + ghi log; AA-967 xoá thật trong thời hạn khiếu nại (giữ bằng
   chứng ký) + AA staff tải 403; AA-1002 dòng chi phí đối soát thật khi có LLM. Ghi chú: BFF CRM không chuyển `Retry-After`.
3. AA-855: chuyển công cụ UAT vào `tools/uat/`, ~20 kịch bản chạy thử nội bộ; tạo client id OAuth riêng cho rclone.
4. CRM theo kế hoạch mới: AA-952 lát 4, AA-953, AA-966, AA-962.
5. Đến hạn ≥ 01/11: AA-896 báo cáo chi phí tháng + C8 capacity review; C4.3 W45 từ 02/11.
6. Có LLM (acc3 ~04–06/11): AA-919 kappa, AA-790, AA-1000, AA-900, replay AA-788 + pilot 20 bài.
