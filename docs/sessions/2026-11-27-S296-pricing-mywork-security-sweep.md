# S296 — Giá đại lý, My work, khoá state + xoay secret, sweep bảo mật 0 USD, E2E CRM

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 27/11 ~15:30 → ~21:30 +07.
**Snapshot cuối phiên:** [state-snapshot.md](../audits/2026-11-27-S296-session/state-snapshot.md) · **Jira:** [jira-drafts.md](../audits/2026-11-27-S296-session/jira-drafts.md)

## Trạng thái

- Đầu phiên: rotate memory Notion theo yêu cầu (S281→S290 sang `memory_archive_2026H10`, HOT giữ S291→S295).
- Nghiệp "Ok" danh sách 10 việc; 11 lane (lane.js) + 4 workflow kiểm/tư vấn chạy song song; mỗi PR qua review đa góc nhìn, kiểm live bằng workflow verifier + skeptic.
- **Đóng 3 issue:** AA-1188 (giá đại lý), AA-1190 (My work lát 1), AA-1196 (E2E CRM, tạo trong phiên theo yêu cầu Nghiệp).
- **Có tiến độ, còn mở:** AA-1182, AA-1183, AA-1185, AA-1187, AA-1173, AA-873, AA-1166.

## Thay đổi Codebase

| Repo | PR | Nội dung |
|---|---|---|
| AA-CIS-App | #1676 | Savepoint đặt tên theo độ sâu (rebase, sửa code-health) |
| AA-CIS-App | #1720 / #1721 / #1722 / #1724 | Khớp upload chung một hàm (AA-1187); security.txt; My work lát 1; ô My work giữ bộ lọc khi bấm |
| AA-Booking | #276 / #331 / #337 / #338 / #339 / #340 / #341 | Kit sync; savepoint; Meal plan; tariff twin share + quote rules; security.txt; My work; thẻ Price setup 2 dòng |
| AA-Partner | #355 / #405 / #406 / #407 / #408 | Kit sync; AA prices + điều kiện đặt tour; security.txt; sửa 500 `/aa-tariff` (allow-list BFF + test quét); E2E Dev theo lịch |
| AA-TripPlanner-Web | #308 | security.txt + link "Report AI content" |
| AA-CIS-Infra | #1045 / #1046 / #1047 / #1048 / #1049 / #1050 / #1051 / #1052 / #1053 / #1054 | Cảnh báo ACM; khoá state + thu hẹp task role CIS; sweep S295; tắt execute-api + lint error; xoá SG cũ; thu hẹp egress; design note NAT; seed B2B (DRY RUN → apply → DRY RUN) |
| AA-Ecosys (root) | #1046 / #1047 / #1049 / #1050 / #1051 / #1052 / #1053 / #1054 | DPA Annex 2 v0.7; sổ secret v2; guide Meal plan; contract b2b 1.12; lint ID error; guide My work; baseline bảo mật |

## Thay đổi Hạ tầng

- Terraform Apply CI 6 lần + 3 apply local MFA có `-target` (bootstrap IAM / thay khoá), CI apply cuối "No changes".
- Khoá bucket state (bucket policy 4 Sid), managed policy task role CIS; task role đọc state = 403.
- Xoay (P6): 7 client secret Cognito, mật khẩu DB TripPlanner (DB Migrate set-password), 3 khoá TripPlanner.
- EBS mã hoá mặc định, snapshot BPA, rule AWS Health / nhóm admin / enable-user, CAA, DMARC rua, ALB/NLB deletion protection, execute-api mặc định tắt, SG `sg-app` xoá, egress 10 SG thu hẹp, test-wp tắt (sidecar gỡ).
- AA-873 chạy thử Security Hub (CSPM FSBP + bản hợp nhất), Inspector (ECR + Lambda), Macie; 4 lịch tự tắt 29/11 09:17–09:32 UTC (0 USD dự kiến, trial).
- NAT patch association chạy lần đầu (13:47Z, lúc chốt vẫn đang cài gói; app ready 200 suốt).
- Seed B2B Dev: tour giả lập có phòng mọi đêm (DB Migrate run-script, 10 bước, không xoá).
- Gói ISMS v0.2 + owner pack lên kho ISMS riêng (bucket bronze, versioned).

## Bằng chứng verify

- Workflow kiểm live (8 agent + recheck 4 agent): AA-1188, AA-1190 done-with-scope; AA-1185 các mục đã ship đạt; AA-1187 bước 1 (cột Meal plan, chuỗi mới trong build; nhập lại thật = test CI vì E2E chỉ đọc).
- AA-1182: CloudTrail 0 AccessDenied 40′ sau apply; Drift xanh; E2E Cognito CIS xanh; job CRM M2M 92/92 + 206/206.
- AA-1185: execute-api mặc định 403/403/404, custom domain 200; rule nhóm admin kích hoạt (2 invocations 12:41Z); sau egress: ready 200 ×2, job CIS/CRM thành công.
- AA-1196: E2E Dev CRM run 46008767583: 9 passed, 3 skipped.
- Prowler 27/11: 0 Critical, 6 High (đều "Security Hub chưa bật" theo Q11).

## Quyết định của Nghiệp

- Rotate memory Notion: 10 phiên cũ nhất thành H10.
- "Ok" danh sách 10 việc S296.
- Giữ Security Hub bản mới (2025) trong đợt thử AA-873.
- Tạo issue cho E2E Partner đỏ (→ AA-1196) và làm luôn trong phiên.
- Jira: "Đăng hết" 5 comment.

## Jira

Đã đăng: PR-26 10712 (4 ảnh), PR-25 10713 (1 ảnh), PR-22 10714 (2 ảnh), PR-23 10715 (2 ảnh), PR-31 10716.

## Còn lại

- 28/11 03:17Z: lượt E2E CRM theo lịch đầu tiên. ≥ 28/11 23:50Z: chuỗi AA-1061 (bk-076).
- 29/11: AA-873 xuất số đếm ~05:00Z, kiểm tự tắt, dọn role + service-linked role, kiểm hoá đơn; rồi bật scan-on-push BASIC cho ECR.
- S297: AA-1182 (sửa tools/identity, RDS tự quản master, runbook key ceremony), AA-1183 phần 2, AA-1187 bước 2.
- Việc tay tech lead: TXT DMARC report trên zone adventure.asia; revoke token Vercel + 3 PAT, xoá key acc1 cũ; 4 câu quyết NAT allow-list.
- Kiểm lệnh vá NAT đã xong (Success) đầu phiên sau.

## Lưu ý kỹ thuật cho phiên sau

- Xoay client secret Cognito: giá trị chỉ có trong response `add-user-pool-client-secret`; Describe không trả secret nữa (lessons.md).
- EventBridge Scheduler: trust SourceArn = schedule-group; universal target dùng tên trường PascalCase.
- Terraform apply đụng task def CRM để lại revision mẫu (image bootstrap) → chạy deploy lại để chạy đúng revision.
- Push Infra cần `MISE_SHELLCHECK_VERSION=0.10.0`; lane cần `npm ci` trong worktree trước pre-push frontend.
