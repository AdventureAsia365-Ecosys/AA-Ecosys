# S280 — 14/11/2026 — Xoá dữ liệu thật khi offboard, sửa toàn bộ UI Settings, giá giả lập E2E, Academy schema + host

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 14/11 ~13:00 → ~21:45 +07. Tech lead vắng ~13:40–17:40
(việc code chạy trước, việc cần tech lead gom một cửa sổ). MFA `aa365-admin` hết ~21:01 (sớm hơn giờ tool báo), làm mới
~21:05. Đổi tài khoản Claude 1 lần giữa phiên (chạm giới hạn 5 giờ).

## Trạng thái

- **Done (có bằng chứng live):**
  - AA-1104: root #767 + #775. Thêm trang Docs đánh số và gom/mở nhóm, CIS #1509; ảnh ở `verify/shots/docs-groups-*`.
  - AA-1091: giá giả lập E2E chạy trọn trên Dev; dữ liệu supply giả lập đã gỡ sau khi kiểm.
  - `LAG_SQL` (Refs AA-1056): #1495, live 2 ms / 134 buffer (trước 2,33 s).
  - C4.3 tuần W46.
- **Done sau root PR này:** AA-1102. Done-when cuối là đưa bài học vào lesson log, nằm trong root PR này.
- **Còn mở:**
  - **AA-1096 (In Review).** Mọi lane live, live proof CIS + TP PASS, Settings Lint là required check ở Booking/Partner/TP,
    toàn bộ audit UI Settings đã sửa và deploy. Còn Done-when "env var của setting đã chuyển phải gỡ sau một release".
  - **AA-1093.** Xoá thật lần đầu trên tenant tổng hợp PASS ở CIS / Booking / TripPlanner / ngoài DB; công tắc đã tắt.
    Còn: xoá RDS snapshot trước khi xoá (sau root PR), stage 2 cho CRM chưa làm.
  - **AA-1105.** S1 docs + ADR, S2 Infra (#841), S3 migration 420 (#1508) đều live. Còn S4 API, S5 web.
  - **AA-1106.** Catalogue + guard + Product map live. Còn: tech lead duyệt YAML; Catalogue guard thành required check.
  - **AA-1086.** REH-06, REH-08a, X1 PASS. Còn marker 1b/12b (giờ chạy được vì công tắc AA-1093 đã tắt).
  - **AA-1048.** v3, v4 no_go. Đề xuất instrument 2 bước trên pool mới (ghi trong Linear).
  - **AA-1077.** Trial 5 chưa đạt: 2 bài, 1 bị giữ F4, 0,2283 USD. Phân tích $0 ở phiên sau.
  - **AA-1051.** Code live, campaign live bị chặn bởi null run.
- Số liệu live cuối phiên: `docs/audits/2026-11-14-S280-session/state-snapshot.md`.

## Quyết định của tech lead (trong phiên)

- ~13:10 duyệt cả 10 việc; trần LLM trả phí phiên 5 USD.
- ~13:40 việc code làm trước, việc cần tech lead dồn lại khi quay về, không đứng chờ (memory `hand-steps-wait-for-return`).
- ~17:43 bật `cis.erasure.saga_apply_enabled`; 17:52 duyệt AA-1093 (fingerprint `c42fbb43`, có RDS snapshot trước khi xoá).
- ~17:55 "kiểm tra và sửa cho toàn bộ" UI settings / tìm kiếm ở mọi app.
- ~18:00 duyệt:
  - ADR 0022 quyết định 6–11;
  - AA-1091 A10e-3 + ~0,42 USD LLM nháp nội dung supply;
  - accept ADR 0011 + ADR 0014.
- Muốn mọi bước tay đưa một lần, không nhỏ giọt ("sao cứ lắc nhắc vậy").
- "khi tìm thì ẩn các nhóm à" → chip theo nhóm có số đếm khi tìm (CIS #1507).
- "làm xong hết việc chưa, rồi dừng phiên thôi"; "Đăng" 4 comment Jira.
- "Trang Docs nên đánh số và cho gom/mở rộng group" → CIS #1509.

## Thay đổi Codebase (PR đã merge, chính)

- **CIS:**
  - Settings: #1492 Infra limits, #1503 lint toàn repo, #1504/#1505/#1506 sửa audit UI settings, #1507 chip theo nhóm.
  - #1496 Product map.
  - AA-1077: #1497, #1500. AA-1048: #1491, #1499.
  - AA-1051: #1494 (419), #1498. #1493 (418).
  - #1495 LAG_SQL, #1490 preset Pricing cho E2E.
  - #1502 RLS map learn, #1508 migration 420 (kèm nâng mốc ghim Infra của Migration preflight), #1509 Docs đánh số.
- **Booking:**
  - #249/#252 cặp E2E định giá và supply giả lập.
  - #250 settings-lint.
  - #253/#254 sửa UI policy.
  - #255 bk-058 từ chối/rút dòng policy đang chờ, #257 code từ chối/rút.
  - #256 kit sync.
- **Partner:** #308 settings-lint, #310/#311 sửa settings CRM, #312 kit sync.
- **TripPlanner:** #266 settings-lint.
- **Root:**
  - #767/#770/#775/#776/#778 docs Academy + kit dự án, #779 ADR accept.
  - #774 catalogue + guard, #777 journeys.
  - #768/#769/#773 kịch bản diễn tập.
  - #780 dòng retention bk-058.
  - #781, #783 schema dump (#783 tự merge sau apply 420).
  - #782 guard catalogue bỏ qua 12 chữ số nằm trong SHA hex: báo nhầm do SHA merge `40087e38b950257287406…`.

## Thay đổi Hạ tầng

- **Infra #833:** trigger WORKFORCE + mailbox cho cặp E2E định giá.
- **Infra #834, #835, #839:** dây công tắc xoá dữ liệu của Booking; bật cho lượt xoá thật rồi tắt lại. Mỗi lần có Terraform
  Apply + deploy.
- **Copy migration:** #836 (418), #837 (419), #840 (bk-058), #842 (420).
- **Infra #841 (AA-1105 S2):**
  - Đăng ký schema `learn`.
  - Host `academy.lumiguides.it.com` là alias thứ hai của distribution đại lý, kèm luật ALB.
  - Client WORKFORCE `academy-web`.
  - Route API Gateway `learn/{proxy+}`.
  - Task role CIS chỉ đọc `learn-media/`.
  - Terraform Apply: 11 add / 4 change / 2 destroy.
  - Ghi 2 key academy vào `crm/dev/web` (`crm_dev_identity.py academy-web-secret --apply`).
  - Deploy tay CRM web lên :151.
- **Branch protection:** Settings Lint là required check ở Booking, Partner, TripPlanner (qua gh API).

## Bằng chứng verify (chọn lọc)

- **AA-1093:** E1 CIS, E2 Booking, E3 run-script TP + Booking, E4 ngoài DB đều PASS; F3 công tắc tắt PASS. File ở
  `verify/aa1093/`.
- **AA-1096 live proof:**
  - CIS: 20→21→20, 14 tenant đọc được giá trị mới.
  - TP: 30→31→30, Lambda đọc được.
  - Cả hai trong khoảng 1 phút, không cần deploy.
- **AA-1091:** SUP-000009 (JP, 4 tour, 4 dịch vụ) định giá, tariff 1.250/1.500/1.750/2.000 USD, giá "Từ" đúng; dữ liệu giả
  lập và preset đã gỡ. File ở `verify/aa1091/` (trường `tour_key` trong `04-import-dryrun.json` / `05-import.json`
  rút còn 8 ký tự đầu của UUID tour giả lập: gitleaks đọc nhầm là API key).
- **AA-1105:**
  - `/health/ready` schema_version 420.
  - Isolation Probe success sau apply.
  - Edge academy 13/13 PASS (`/healthz` 200 auth_configured=True; `/crm/*` không lộ).
  - Review độc lập: ship cả hai PR, không có must-fix code.
  - Runbook + việc tiếp theo: `aa1105-ship-runbook.md`.
- **Docs + chip Settings:** desktop/phone × sáng/tối, không cuộn ngang.
  - Docs: 23 nhóm, số 1.1…; Expand all → 169 trang, Collapse all → 0.
  - Chip khi tìm "budget": `All 3 | Retention 1 | Spend 2`, chip chọn có `aria-pressed=true`.
- **C4.3 W46:** 0 target trượt; LAG_SQL 2,33 s → 2 ms (`c43-w46/`).
- **Chi phí LLM phiên:** ~0,31 USD theo gateway (MTD 34,01 → 34,32), dưới trần 5 USD.

## Jira

Đã đăng ~20:45 sau khi tech lead duyệt: PR-25 comment 10653 (3 ảnh), PR-26 10654, PR-22 10655, PR-27 10656
(`docs/audits/2026-11-14-S280-session/jira-drafts.md`). Trang Docs và chip Settings làm sau khi đăng → báo ở phiên sau.

## Còn lại (việc chưa xong)

1. Xoá RDS snapshot `tenant-erase-20261114-pre` sau khi root PR này merge (làm ngay cuối phiên nếu kịp).
2. AA-1105:
   - S4 learning API, S5 Academy web.
   - Việc tiếp theo từ review: CORS caption, ràng buộc tenant cho dòng con, index `lab_run.learner_id`, saga xoá phủ
     `learn.*`, lấy tên trên chứng chỉ từ danh bạ staff, rate limit theo IP thật.
3. AA-1093: stage 2 CRM.
4. AA-1086: marker 1b/12b.
5. AA-1077: phân tích $0 vì trial 5 chưa đạt.
6. AA-1048: instrument 2 bước.
7. AA-1106: tech lead duyệt YAML; required check Catalogue guard ở root.
8. AA-1096: gỡ env var sau một release.
9. AA-1051: gỡ chặn null run.

## Lưu ý kỹ thuật cho phiên sau

- **Migration preflight của CIS đọc AA-CIS-Infra ở SHA ghim (`INFRA_TOOLS_SHA` trong `ci.yml`), không đọc Infra main.**
  Schema mới cần nâng mốc ghim cùng PR migration. Nay ghim ở `56d553ba` (#841).
- **`crm_dev_identity.py` mặc định dùng `--profile aa365-admin`.** boto3 không dùng chung cache MFA với CLI nên vẫn hỏi
  mã. Dùng mẫu `export-credentials` của steering, kèm `--profile ""`, `</dev/null`.
- **`ship_merge.py` dừng cả lô khi một PR bị DIRTY.** PR xanh còn lại trong lô phải ship lại riêng.
- **Smoke signed-in của Deploy Admin Dev có thể đỏ hàng loạt khi host đang rollout**, kể cả trang công khai `/login`;
  chạy lại job trước khi nghi code.
