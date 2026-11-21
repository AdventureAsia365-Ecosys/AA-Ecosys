# S287 — 21/11/2026 — vai trò tuỳ chỉnh xong phần code, trang Compliance, Alerts catalogue, viết lại lịch sử repo, bảo mật D1–D12

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). 21/11 ~03:00 → tối +07, phiên dài cả ngày. Đổi tài khoản claude.ai 1 lần
(lane không mất việc). Tối đa 4 lane code song song + 2 workflow tư vấn (tuân thủ, cảnh báo). Auto mode tắt 2 cửa sổ (gắn
nhãn baseline gitleaks; gh secret do tech lead tự đặt).

## Trạng thái

Done có bằng chứng live (Linear): AA-1164, AA-1167, AA-1147, AA-1165, AA-1163, AA-1170, AA-788, AA-1137, AA-1162, AA-1171 (xem mục
AA-1171 bên dưới). Còn mở: AA-1155 (code + live xong; còn T12: chuyển người content + ops sang vai trò tuỳ chỉnh, cần tài khoản
staff của người đó), AA-1161 (đã viết lại lịch sử; chờ GitHub GC để số dung lượng trên GitHub giảm). Issue mới: AA-1170,
AA-1171, AA-1172. Snapshot: [state-snapshot](../audits/2026-11-21-S287-session/state-snapshot.md).

## Quyết định của Nghiệp (21/11)

- Duyệt danh sách 10 việc; làm luôn AA-1161 giai đoạn 2 (viết lại lịch sử git) trong phiên.
- Ảnh repo lưu S3 công ty (acc2 `archive/repo-media/`), không dùng Drive cá nhân.
- Chốt 17 câu tuân thủ (15 theo đề xuất; Q13 chưa cần người ký thứ 2; Q14 PDPL/GDPR để sau pilot) → AA-1170.
- Giữ vai trò CIS "Content" có `tenant.read` (đọc mọi tenant, gồm Tenant 360).
- Đồng ý alarm WAF 0,10 USD/tháng (AA-1165).
- Duyệt 10 câu cảnh báo D1–D11 theo đề xuất; D5 làm topic page ngay P0 → tạo AA-1171 "làm đầy đủ".
- AA-1167: giữ fence tắt, mức nền trap 8/9, tạo AA-1172. AA-788: đóng, F12 giữ warn.
- AA-1163: 6 dòng P1 "sửa trong code"; ký biên bản tháng 11 bằng review + merge root #940 của chính tech lead.

## Thay đổi Codebase (merged)

- **AA-1161 giai đoạn 2** — viết lại lịch sử + force push root (915 → 112 MB clone) và Infra (89 → 6 MB), cây không đổi; backup
  bundle + 3.909 ảnh gốc (922 MB) ở S3 private acc2 `archive/`; re-pin + remap gitleaks: root #921, #922 `ca1dce75`, CIS #1623,
  Booking #293, Partner #373, TP #290, Infra #953 `89f4cc4b`. Trang mới `docs/ops/repo-media-archive.md`.
- **AA-1162** — root #923 `47bb25c0` (`post_agent_review.py`, công tắc `change_control.json` TẮT tới pilot, baseline.md);
  ruleset chặn xoá + force-push trên nhánh mặc định cả 6 repo (root 27781683, Partner 27781685); CodeQL default setup root +
  Infra. Phép thử 18:20 (tech lead duyệt lệnh): force-push `master` bị từ chối "repository rule violations", xoá nhánh bị từ
  chối, `master` không đổi (`live/aa1162/`).
- **AA-1163** — root #924 `556d0701` (SEC-03 v2, `vuln_triage.py` KEV / EPSS / CVSS v4 / SLA, biên bản 11/2026: 0 P0, 6 P1, 44
  P2), root #940 `b3632949` (tech lead ký bằng review).
- **AA-1164** — Infra #960 (quét đêm các image đang chạy, 1 role upload), Node pin digest + Alpine fix: CIS #1625, Booking #295,
  Partner #376, TP #291; WordPress thử 7.1.5; quét lần 2 run 44874784276 gate xanh 8/8.
- **AA-1165** — Infra #954, #956 (rule WAF theo người xem trên đường CloudFront của CRM, COUNT rồi BLOCK 429), #961 (alarm
  `aa-cis-dev-crm-edge-rate-blocked`).
- **AA-1167** — CIS #1630 (mig **467** setting fence), CIS #1634 (làm sạch HTML bài AI trước khi đăng, fence dữ kiện không tin
  cậy trong prompt), root #930 (AI Use Register dẫn chứng LLM01, LLM05).
- **AA-1147** — Partner #374 (crm-083), #375 `bf663b9e` (dịch vụ đại lý đi theo chuyến từ báo giá tới hoá đơn), crm-084.
- **AA-1155** — Booking #294 `d704f327` (resolver vai trò tuỳ chỉnh, editor chỉ owner, trang theo capability), CIS #1624
  `60867997` (staff_authz đọc vai trò tuỳ chỉnh, trang Roles & permissions, AI controls chỉ Cognito), CIS #1627 (mig **465**
  preset + quyền editor), CIS #1628 `bf4c6e6e` (editor vai trò CIS + preset dạng dữ liệu trên trang Staff), root #928 (DM-7.1,
  ownership, tick spec T1–T11), Infra #955/#957/#958 (grant maker A10g qua DRY RUN rồi apply).
- **AA-788** — CIS #1632 `bd9565e3` (mig **468**: F12 thành setting + luật lật theo bản ghi đo, F14 thiếu độ dài = `length_short`,
  script pilot T10).
- **AA-1170** — root #929 (collector bằng chứng hằng ngày, retention), CIS #1629, CIS #1631 (mig **466** schema `compliance`),
  Infra #963 (owner registry, RLS catalogue, isolation probe), CIS #1633 `102b05cb` (trang Platform › Compliance readiness);
  register riêng 48 control / 399 mapping nạp bằng DRY RUN rồi apply.
- **AA-1171** — Infra #968 `ddf1e36c` (tag Severity / Component / Mutable cho mọi alarm + rule, topic page, 4 alarm phủ sóng,
  0,70 USD/tháng), CIS #1635 (mig **469** ngưỡng in-app + topic theo người nhận), Booking #297 (bk-063) + #298 `cac94b28`, Partner
  #378 `52ec4413` (crm-085, crm.ops.v1 1.17), root #935 `d9bfc878`, CIS #1636 (tab Catalogue, Apps health theo tag App, 15 reader
  `cis.ops.*`; sửa guard AA-998: tài khoản LLM phục vụ đọc từ registry, không viết khoá `acc1`), CIS #1637 `15814d6e` (sau
  kiểm live: bỏ mã issue khỏi mô tả alarm/rule trên Catalogue, timeout CRM `/ops-checks` 5 s, cache peer 30 s, Overview ghi
  "CloudWatch alarms"), root #936 `b81ab55f` (infra docs tự sinh: `alarms.md` hết đuôi ID ALB / target group).

## Thay đổi Hạ tầng

- Terraform Apply Dev: Infra #968 (26 thêm / 49 đổi / 3 xoá), #961, #954/#956, #960.
- Migration áp qua copy + apply khi 3 bảng job rảnh: CIS **465, 466, 467, 468, 469**, Booking **bk-063**, CRM **crm-083, 084, 085**.
- Secret Actions Infra `IMAGE_SCAN_UPLOAD_ROLE_ARN` do tech lead đặt (auto mode chặn agent).
- S3 acc2 (private, AES256): `archive/repo-backups/2026-11-21-aa1161/`, `archive/repo-media/AA-Ecosys/`.

## Bằng chứng verify

Thư mục `docs/audits/2026-11-21-S287-session/live/` (aa1147, aa1155, aa1167, aa1170).

- AA-1155: maker PASS 2/2 (CIS Content đọc, ghi bị chặn; Booking 24 quyền, đọc 200, 13/13 lệnh duyệt 403); readonly PASS 2/2;
  tech lead tạo + ngừng dùng vai trò, sửa preset rồi trả lại (ảnh trong chat, audit trước/sau).
- AA-1170: tổng quan 200, 6 bộ chuẩn, 253 yêu cầu, 48 control; tech lead rút validity còn 1 giờ → 10 bằng chứng STALE, đạt 8 → 0,
  rồi đặt lại 72 giờ (setting v2 duyệt).
- AA-1167: bài thử WordPress sạch (script / iframe / on* / javascript: bị bỏ); trap 8/9 cả fence bật và tắt, 0,81 USD.
- AA-1147: live 5/5 PASS. AA-1165: COUNT 10.647, BLOCK 10.205 × 429. AA-788: pilot 1,73 USD (có 1 lượt chạy trùng do SSM rớt
  output, đã dừng).
- AA-1171 (`live/aa1171/evidence.md`, workflow kiểm 3 lane + phản biện): Catalogue 123 dòng, 37 alarm + 15 rule khớp AWS,
  không thiếu/thừa; Apps health theo tag (CIS 4, tổng 37); đổi `cis.ops.xid_age_limit` 1 tỷ → 500 triệu qua maker-checker →
  `rds_xid_age` OK → ALARM trên số đo tổng hợp, tiến trình api đang chạy hiện 500 triệu (đọc từ ngoài) rồi trả về 1 tỷ; 11
  alarm page có topic page; 5 alarm mới OK; mã issue trên trang sửa ở #1637.
- Snapshot: Booking smoke đỏ do WAF geo chặn runner → chạy lại xanh; Terraform Drift chạy tay xanh; Catalogue (schedule) đỏ
  4 ngày → sửa surface + features (CIS-F051, CIS-F052) trong root PR.

## Tư vấn trong phiên

- Theo dõi tuân thủ bảo mật: `docs/audits/2026-11-21-S287-compliance-tracking/` (trang quyết định 17 câu).
- Kiểm kê cảnh báo / thông báo: `docs/audits/2026-11-21-S287-alerting-inventory/` (trang quyết định 10 câu).

## Jira

Tech lead duyệt cả 4 nháp. Đã đăng: PR-26 comment 10684 (4 ảnh), PR-23 10685, PR-27 10686 (3 ảnh). PR-20 kỳ 6 (J4) giữ lại
tới phiên sáng thứ Hai 23/11 mới đăng (nháp có số đo 21/11 18:14 trong `jira-drafts.md`).

## Việc đầu phiên sau (S288)

1. AA-1155 T12: người content + ops có tài khoản staff → gán vai trò tuỳ chỉnh, đóng issue.
2. AA-1161: đọc lại dung lượng repo trên GitHub sau GC → đóng.
3. Theo plan.json slot S288 (AA-1157 view-as, AA-1158, AA-1149, AA-1172, AA-1169…).
4. Follow-up nhỏ: nút Refresh evidence (Compliance) chưa báo kết quả; nhãn "SCHEDULED" sai trên setting đã hiệu lực.

## Còn lại

- AA-1155 T12 (bước tay: người content + ops cần tài khoản staff), AA-1161 (đóng khi GitHub báo dung lượng sau GC).
- Đăng PR-20 kỳ 6 (J4) ở phiên sáng thứ Hai 23/11 (đọc lại số trước khi đăng).
- CIS #1586 (dependabot frontend-security) vẫn đỏ từ S285.
- Follow-up nhỏ của AA-1171 / AA-1170: người nhận cho topic page trước prod, alarm delivery-failed cho topic page, bỏ mã
  issue khỏi mô tả Terraform, chữ điều kiện alarm anomaly-band ("above band None"), nút Refresh evidence chưa báo kết quả,
  nhãn "SCHEDULED" trên setting đã hiệu lực.

## Lưu ý kỹ thuật cho phiên sau

- Guard AA-998 (`test_aa998_no_acc1_runtime.py`) chặn chữ `acc1` trong code CIS kể cả comment: tài khoản LLM phục vụ là dữ
  liệu registry (`accounts.satellite_connections()`); riêng đường dẫn `accounts/acc1-bedrock/` được phép (S287).
- Hằng số chính sách mới phải có `# technical-constant:` cùng dòng (settings lint), và body PR CIS không chứa mã issue ngoài
  dòng `Refs` (check PR title đọc body).
- Thử ruleset phá huỷ cần tech lead tắt auto mode và duyệt lệnh; `ship_wave.py --wait-idle` cần số N; vòng chờ dùng
  `kill -0 <pid>` (guard PKILL-1 chặn `pgrep -f` trong vòng lặp).
- Chứng minh "đổi ngưỡng trên Settings đổi hành vi": script đi qua `settings_registry.propose` + `decide`, số đo tổng hợp
  nằm giữa hai ngưỡng, giữ giá trị > `cache_s` để đọc từ ngoài, rồi trả lại (`.tmp-session/S287/verify-1171/proof/`).
