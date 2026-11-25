# S294: 25–26/11/2026: Image Scan, header bảo mật trên trả lời bị WAF chặn, đồng bộ lịch CRM, red-team AI đầu tiên, Product map

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). Khoảng 18:30 25/11 → 07:00 26/11 +07. Lane song song qua
`tools/workflows/lane.js` (l2–l26), tối đa 3 lane, guard RAM ≥ 4 GB. Đổi tài khoản Claude giữa phiên (tracker đọc lại rồi
publish). Sự cố GitHub một phần lúc 22:58 (API 502, token App bị từ chối) → tạm dừng ship, thử lại khi hồi phục.
MFA hết hạn 06:40 26/11.

## Trạng thái

- **Done:** AA-1174 (Done-with-scope, D1 S288), AA-1172 (tech lead bật `cis.llm.fact_instruction_guard`), AA-1103
  (khoá L8 xuất bản + template v1.3.1).
- **Mới:** AA-1181 (follow-up AA-1148; phần (a) là CIS #1713 nháp, ship sau buổi họp).
- **Đã ship, còn bước của người:** AA-1154 (bấm "I ran this" một thẻ), AA-1169 (đọc 12 mẫu), AA-1011 (token Mapbox cho
  bản đồ builder; đăng ký quyền lịch Google), AA-1166 (duyệt trần red-team CRM 0,05 / TP 0,25 USD), ASVS nhóm C.
- `done_audit.py` báo 3 issue thiếu gạch Done-when: báo nhầm, mỗi issue đã có comment "S294 … Done-when check" đối chiếu
  từng gạch (heuristic chỉ đọc comment có tiền tố `Done-with-scope:` / `Done-evidence:`).
- LLM trả phí: **0,3949 USD** (red-team AA-1166, ledger `adhoc_aa1166_redteam_*`); replay AA-1050 0 USD.
- Snapshot: [state-snapshot](../audits/2026-11-25-S294-session/state-snapshot.md).

## Quyết định của Nghiệp

- ~18:50: "tiếp" — duyệt 7 việc.
- ~19:30: "đánh giá lại hết issue còn lại, kéo tiếp việc code, tăng tốc" → workflow đánh giá lại (wf_28eaf318-e50).
- ~19:40: làm bình thường tới 07:00 26/11, rồi chốt + cập nhật live trước buổi họp chị Thư 11:00.
- ~20:38: "đã duyệt hết" D1–D10 trên trang quyết định ([decisions.md](../audits/2026-11-25-S294-session/decisions.md)).
- 19:44: tech lead bật `cis.llm.fact_instruction_guard`; AA-1110 kênh báo động thứ hai hoãn, sau dùng info@ hoặc admin@.
- ~21:00: rà bảng tính năng (Product map) cho khớp live.
- ~21:25: kéo thêm việc code tới 07:00, "phân bố đều theo limit và OOM".

## Thay đổi Codebase (merged)

- **Image Scan / Catalogue (guard đỏ đầu phiên):** Booking #332 (build lại `--pull`), root #1020, Infra #1033 (ngoại lệ
  WordPress test-wp tới 02/12, Trivy `--ignorefile /dev/null`); scan gate passed (0 lỗi).
- **CIS:** #1703 (Content workspace 390 không tràn), #1704 (pre-push gitleaks bỏ shim mise, ghim đồng hồ rate limiter),
  #1705 (thay #1586), #1706 (bộ red-team 16 ca), #1707, #1708 (đo kappa offline), #1711 (smoke header), #1712 (model từ
  chối = đạt), #1714 (visual supply-content-item), #1715 (T2 có câu ghi chú trước JSON → parse an toàn + tín hiệu
  `writer_note`).
- **Booking:** #332, #333 (notes KMS khoá ngân hàng NCC), #334, #335 (smoke header).
- **Partner:** #392 (vệ sinh bảo mật), #394 (crm-089), #395 (đẩy một chiều chuyến khởi hành + việc vào lịch Google /
  Microsoft 365 của từng nhân viên, crm-090), #396 (HSTS + nosniff CRM API), #397 (bản đồ builder), #398
  (`ENVIRONMENT=test`), #400 (script red-team CRM), #401 (thẻ lịch studio gọi handler studio, không gọi BFF CRM),
  #402 (JSON charset).
- **TripPlanner:** #304 (engine), #305 (script red-team chat), #306 (JSON charset + trang kiểm input), #307 (redirect gọn).
- **Infra:** #1033, #1034 (báo động KMS tên `aa-sec-dev-booking-kms-*`), #1035, #1037 (cờ token Mapbox), #1038 (mọi quy
  tắc WAF chặn trả 403 kèm 4 header), #1040 (WAF_FILTERED riêng, hết HSTS trùng).
- **Root:** #1020–#1037 (go-live gate, ZAP chạy bằng docker, guard ship AA-1024, lịch sử chi phí acc2, ASVS, Product map
  136 dòng, khoá L8 xuất bản, follow-up tài liệu) + bot #1035, #1026.
- **project-template:** #4 + tag v1.3.1.

## Thay đổi Hạ tầng / dữ liệu Dev

- Migration áp: crm-089, crm-090. CIS vẫn 494, bk-075, tp không đổi.
- Terraform apply: KMS alarm (2 rule + 4 target), WAF custom response (#1038, 0/1/0), gateway response WAF_FILTERED
  (#1040, 4 add / 2 change / 2 destroy).
- ECS cuối phiên: cis-api :1299 / worker :868 (ba5d2ffc), admin :109 (9fba482f), booking-api :176 (8844fd00),
  booking-admin :70 (b89f18f4), crm-api :225 / crm-web :195 (10d1f134), tp-web :32 (4d6919e7).
- Dữ liệu demo: tour tay SYNTHETIC 3 ngày (draft, SUP-000019) cho buổi họp.
- Setting: `cis.llm.fact_instruction_guard` = On (v1, approved).

## Bằng chứng verify

- Health 8/8 service 200, git_sha khớp ECS (snapshot).
- Product map live 03:09 26/11: 5 app, 136 tính năng (128 live), 38 liên kết, 4 hành trình, 146 UAT
  ([ảnh](../audits/2026-11-25-S294-session/live/jira/product-map-1440-light.png)).
- curl không User-Agent → 403 kèm 4 header, 1 dòng HSTS trên api-cis + api-booking; ZAP chạy lại 0 High
  ([zap-baseline.md](../audits/2026-11-25-S294-session/zap-baseline.md)).
- Red-team: 12 đạt / 1 dương tính giả / 3 chưa chạy (trần); báo cáo private trên S3 ISMS.
- Replay AA-1050 (0 USD): t10_claims 0 khác biệt → nháp gỡ CIS #1709/#1710 chờ AA-1169
  ([aa1050-claim-layer-replay.json](../audits/2026-11-25-S294-session/aa1050-claim-layer-replay.json)).
- Guard theo lịch 0 đỏ / 43.

## Jira

Nháp 3 bài (PR-22, PR-26, PR-27) chờ tech lead duyệt: [jira-drafts.md](../audits/2026-11-25-S294-session/jira-drafts.md).

## Còn lại

- Sau buổi họp 26/11: ship CIS #1713 (AA-1181 a), Partner #403, Infra #1041; bật `cis.content.publish_two_person` trong buổi
  họp; savepoint #1676 / Booking #331.
- Bước tech lead: token Mapbox; đăng ký quyền lịch Google; trần red-team CRM / TP; ASVS nhóm C (đổi mật khẩu tự phục vụ,
  Cognito Plus, access token 15 phút, sanitizer HTML mail, WAF pool partner); AA-1169 đọc 12 mẫu; AA-1154 bấm một thẻ;
  chính sách giữ `writer_note`.
- Ngoại lệ ảnh WordPress test-wp hết hạn 02/12.

## Lưu ý kỹ thuật cho phiên sau

- 22 bài học mới đã vào `skill/aa-lessons/lessons.md` (Vận hành, Frontend, Pipeline), mỗi dòng có Guard.
- Spec `admin-evidence` chờ bảng (`table tbody tr`): trang Product map dạng thẻ nên spec báo lỗi dù trang đúng; ảnh lỗi
  `99-failure.png` vẫn dùng được làm bằng chứng.
