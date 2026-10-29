---
id: SEC-04-2026-10-28-s256
title: "AA-873 — phân loại phát hiện IAM Access Analyzer và chuẩn bị kiểm thử cảnh báo bảo mật (S256)"
description: "11 phát hiện ACTIVE của analyzer đều là truy cập có chủ đích (9 role OIDC GitHub, 1 permission set Identity Center, 1 quyền bucket bronze cho batch Bedrock); 3 archive rule + vá lỗ hổng cảnh báo đổi tag IAM; runbook kiểm thử cảnh báo cho điều phối."
type: report
status: draft
owner: nghiep
audience: [owner, engineer, agent]
applies_to: [aa-cis-infra, ecosystem]
last_reviewed: 2026-10-28
related: [AA-873, FIN-03-2026-10-28-s255]
---

# AA-873 — phân loại phát hiện Access Analyzer + kiểm thử cảnh báo (S256)

- Phiên S256, 28/10/2026 khoảng 14:20–14:45 UTC. Tác nhân: Claude Code (lane Infra, **chỉ đọc** trên AWS; code + commit
  local). **GuardDuty vẫn TẮT** (bài học S255: dịch vụ trả phí chỉ bật khi tech lead nói "có" riêng cho mục đó).
- Nối tiếp [`../2026-10-28-S255-finops-security/README.md`](../2026-10-28-S255-finops-security/README.md) §7 (PR 1 nền miễn phí và
  PR 2 CloudTrail/KMS đã apply trong S255).
- Nhánh Infra: `chore/aa-873-access-analyzer-archive-rules` (1 commit, chưa push). Ghi chú triển khai:
  `docs/implementation-notes/AA-873-s256-triage.md` trong repo Infra.
- Runbook kiểm thử cảnh báo (điều phối chạy): `.tmp-session/S256/aa873/alert_test.sh` (repo gốc, không commit).
- **Chi phí:** 0 USD (archive rule miễn phí; mọi lệnh đọc ở đây miễn phí; `test-event-pattern` miễn phí).

## 1. Tóm tắt

1. Account hạ tầng (acc2) chỉ có **1 analyzer** (`aa-sec-dev-external-access`, us-west-1). Không region nào khác có analyzer;
   cả 16 bucket đều ở us-west-1, nên 1 analyzer là đủ (role IAM là global).
2. **12 phát hiện: 11 ACTIVE, 1 RESOLVED.** Cả 11 ACTIVE đều là **truy cập có chủ đích**, **không có lộ lọt thật**:
   9 role được GitHub Actions OIDC tin cậy, 1 role của permission set `AdministratorAccess` (IAM Identity Center của tổ chức),
   1 câu lệnh trong policy bucket bronze cho role batch Bedrock của account LLM. Phát hiện RESOLVED là quyền cũ của account
   cá nhân đã gỡ (AA-998) — đúng như mong đợi.
3. **3 archive rule** (Terraform, nhánh Infra) lưu trữ đúng 11 phát hiện đó. Đã chạy thử bộ lọc trên dữ liệu thật
   (`list-findings-v2 --filter`, chỉ đọc): khớp đúng 9 + 1 + 1, AWS chấp nhận mọi khoá lọc.
4. **Tìm ra 1 lỗ hổng cảnh báo thật** khi chuẩn bị test: rule `aa-sec-dev-iam-change` **không bắt** `TagRole`, `UntagRole`,
   `TagPolicy`, `UntagPolicy`, `Upload*`, `ChangePassword`, `Set*` (kiểm bằng EventBridge `test-event-pattern`: 7 ca trượt).
   Tag ở đây quyết định quyền (key policy break-glass của CRM đọc `aws:PrincipalTag/tenant_id`; boundary của role apply dựa
   trên tag `App`), nên đổi tag mà không báo là lỗ hổng. Nhánh Infra vá (thêm tiền tố `Tag`, `Untag`, `Upload`, `Set`,
   `Reset`, `Change`, `Enable`, `Deactivate`, `Resync`); pattern mới thử trên EventBridge thật: 21/21 đúng.
5. **Đường gửi mail đã chạy thật**: từ lúc apply PR 1 (28/10), rule Access Analyzer gọi SNS 12 lần, rule trail 1 lần (apply PR 2),
   forwarder us-east-1 2 lần — **0 lần lỗi** (CloudWatch `AWS/Events`). Topic có 2 người nhận e-mail đã xác nhận.

## 2. Bảng phân loại (11 ACTIVE + 1 RESOLVED)

Loại: **A** = cross-account / bên ngoài có chủ đích; **B** = công khai theo thiết kế (không có cái nào); **C** = lộ lọt thật (không có cái nào).

| # | Tài nguyên | Ai truy cập được | Hành động | Điều kiện thật (đọc trong Terraform) | Loại | Xử lý |
|---|---|---|---|---|---|---|
| 1 | Role `aa-cis-dev-app-deploy` | GitHub OIDC | AssumeRoleWithWebIdentity | `aud` + subject AA-CIS-App (id repo bất biến), environment `dev`, `ref` = main | A | archive rule `github-oidc-deploy-roles` |
| 2 | Role `aa-cis-dev-e2e-mail-reader` | GitHub OIDC | như trên | AA-CIS-App env `e2e` + AA-Partner env `e2e`, `ref` = main | A | như trên |
| 3 | Role `aa-cis-infra-tf-plan` | GitHub OIDC | như trên | AA-CIS-Infra `pull_request` hoặc ref main (chỉ đọc) | A | như trên |
| 4 | Role `aa-cis-infra-tf-apply` | GitHub OIDC | như trên | AA-CIS-Infra env `prod`, `ref` = main | A | như trên |
| 5 | Role `aa-cis-dev-docs-sync` | GitHub OIDC | như trên | repo gốc, ref master (cả `sub` và `ref`) | A | như trên |
| 6 | Role `aa-booking-dev-app-deploy` | GitHub OIDC | như trên | AA-Booking (id repo bất biến), env `dev` hoặc ref main | A | như trên |
| 7 | Role `aa-tripplanner-dev-app-deploy` | GitHub OIDC | như trên | AA-TripPlanner-Web, ref main | A | như trên |
| 8 | Role `aa-crm-dev-app-deploy` | GitHub OIDC | như trên | AA-Partner, env `dev` | A | như trên |
| 9 | Role `aa-crm-dev-scrub-corpus` | GitHub OIDC | như trên | AA-Partner, env `scrub-corpus` | A | như trên |
| 10 | Role `AWSReservedSSO_AdministratorAccess_…` | IAM Identity Center (SAML của tổ chức) | AssumeRoleWithSAML | do Identity Center của tổ chức quản lý, không nằm trong Terraform | A | archive rule `identity-center-admin-permission-set` + câu hỏi Q1 |
| 11 | Bucket bronze | Role batch Bedrock của account LLM | Get/PutObject, ListBucket | chỉ các prefix `batch-input/` và `batch-output/` (atom-decompose, s1-rewrite) | A | archive rule `bronze-bedrock-batch-satellite` |
| 12 | Bucket bronze (RESOLVED) | Role batch của account cá nhân đã rời hệ | — | đã gỡ khỏi policy (AA-998) | — | không cần làm gì |

Ghi chú quan trọng:

- **Access Analyzer không thấy claim của GitHub**: mọi phát hiện OIDC hiện `condition: {}`, nên chỉ nhìn phát hiện thì không
  chứng minh được role đã khoá theo repo. Lane kiểm trong Terraform (`accounts/aa365`): cả 9 trust đều khoá `aud` =
  `sts.amazonaws.com` + subject chính xác theo id repo bất biến, không có ký tự đại diện (biến id repo của Booking và CRM đã
  đặt trong `terraform.tfvars`, nên nhánh dự phòng `*` không dùng). Hook của subagent chặn mọi lệnh `aws iam`, nên **đối chiếu
  live = Terraform là bước của điều phối** (mục 5, bước 1).
- **Vì sao liệt kê từng role thay vì "mọi role tin OIDC"**: nếu sau này có role OIDC mới với trust lỏng (`repo:*`, nhánh bất kỳ),
  phát hiện của nó trông y hệt. Liệt kê từng role → role mới vẫn báo 1 mail `[aa-sec] access_analyzer`; xem trust rồi thêm 1
  dòng. Test `tools/terraform/tests/test_sec_access_analyzer.py` (chạy trong CI) đỏ khi có role OIDC chưa được liệt kê hoặc
  trust có ký tự đại diện.
- **Bộ lọc OIDC còn khoá `principal.Federated`** = provider GitHub: nếu một trong 9 role sau này tin thêm một account khác,
  phát hiện đó vẫn ACTIVE.
- **Identity Center**: chỉ lưu trữ đúng permission set `AdministratorAccess`. Permission set mới gán vào account vẫn báo.

## 3. Q1 — ai dùng role Identity Center `AdministratorAccess`? (đề xuất câu trả lời)

CloudTrail 90 ngày (chỉ đọc): user SAML tên **"Admin"** đăng nhập console qua cổng Identity Center khoảng 10 lần (25/08 → 13/10),
lần cuối 13/10/2026; việc làm là xem chi phí/billing (Cost Explorer, Billing, Cost Optimization Hub, Health, Service Quotas,
Free Tier), đọc 1 role và SAML provider — **không ghi gì**. Role này do Identity Center của tổ chức thanh toán (account quản lý,
bên đại lý thanh toán AWS) tạo; repo không xoá được (xoá thì Identity Center tạo lại).

- **Đề xuất:** giữ + archive (đã làm trong nhánh). Lần tới liên hệ đại lý thanh toán, hỏi "Admin" là ai và đề nghị đổi sang
  permission set chỉ xem billing (ví dụ `Billing` / `ViewOnlyAccess`) nếu họ chỉ cần xem chi phí. Không chặn việc gì khác.
- Cảnh báo vẫn bao phủ: mọi thay đổi IAM/SG/trail do phiên "Admin" này làm đều bắn mail (rule chỉ loại trừ role apply của CI).

## 4. Kiểm thử cảnh báo

### 4.1 Đã làm trong lane (chỉ đọc, không gửi mail)

`tools/terraform/sec_alert_check.py` (nhánh Infra) dựng 44 sự kiện mẫu và hỏi chính EventBridge (`describe-rule` +
`test-event-pattern`) xem rule đang chạy có khớp không:

| Rule | Ca | Kết quả trên rule đang chạy (trước nhánh) |
|---|---|---|
| `security-group-change` | 5 thao tác SG của admin + 1 IAM user → khớp; role apply CI, `DescribeSecurityGroups` → không | 8/8 đúng |
| `iam-change` | 11 động từ ghi + IAM user → khớp; role apply CI, `GetRole` → không; **7 động từ tag/upload/set/change** | 14/21 — **7 trượt = lỗ hổng mục 1.4**; pattern của nhánh: 21/21 |
| `root-activity` | ConsoleLogin root, gọi API root → khớp; admin ConsoleLogin → không | 3/3 |
| `cloudtrail-tamper` | UpdateTrail/StopLogging/PutEventSelectors/DeleteTrail (kể cả role CI) → khớp; LookupEvents → không | 5/5 |
| `access-analyzer-finding` | ACTIVE → khớp; ARCHIVED → không | 2/2 |
| `global-forward` (us-east-1) | IAM ghi, IAM tag, root ConsoleLogin → chuyển; IAM đọc, STS của admin → không | 5/5 |

Chạy `--skip-after-s256` (bỏ 7 ca mới) trên rule hiện tại: **0 lỗi**. Test offline trong CI giữ các pattern không trôi.

### 4.2 Runbook thay đổi thật (điều phối chạy) — `.tmp-session/S256/aa873/alert_test.sh`

Chế độ: `preflight` (chỉ đọc; lane đã chạy: account đúng, MFA còn ~11 giờ, 6 rule bật + có target, 2 người nhận đã xác nhận),
`run`, `verify` (chỉ đọc: metric EventBridge/SNS, CloudTrail, trạng thái phát hiện), `cleanup` (idempotent), `all`.
Mọi đối tượng thử tên `aa-sec-alert-test-<giờ>`, không gắn vào gì, không truy cập được; `run` tự dọn khi lỗi giữa chừng.

| Rule | Thay đổi vô hại | Mail mong đợi `[aa-sec] …` |
|---|---|---|
| sg_change | tạo SG trong VPC dev → mở tcp/9 từ 192.0.2.10/32 (dải TEST-NET) → thu hồi → xoá | **4** |
| iam_change | tạo customer managed policy (1 câu Deny, không gắn) → tag → bỏ tag → xoá | **2** trước khi apply nhánh, **4** sau (thêm TagPolicy/UntagPolicy) |
| access_analyzer + iam_change | tạo role **không có quyền nào**, chỉ tin account LLM kèm ExternalId ngẫu nhiên → chờ phát hiện (≤ ~30 phút) → xoá | **1** access_analyzer + **2** iam_change (CreateRole, DeleteRole) |
| trail_tamper | `update-trail --enable-log-file-validation` (vốn đã bật → không đổi gì) | **1** |
| (âm tính) | `describe-security-groups` | **0** |
| root | không script (cần mật khẩu root + MFA trên trình duyệt). Tuỳ chọn: tech lead đăng nhập console bằng root 1 lần | 1 nếu làm |

Tổng: 10 mail trước khi apply nhánh, 12 sau (mỗi mail tới cả 2 hộp thư). Tiêu đề SNS mặc định "AWS Notification Message".

## 5. Các bước của điều phối (theo thứ tự)

1. **Đối chiếu trust live = Terraform** (subagent không gọi được `aws iam`): CI `terraform plan` của PR không đổi 9 role OIDC
   (hoặc `aws iam get-role --role-name <tên> --query Role.AssumeRolePolicyDocument` từng role, 1 dòng).
2. Push nhánh `chore/aa-873-access-analyzer-archive-rules` (Infra) → PR → CI xanh (Terraform Plan + "ALB Rule Order" chạy test mới)
   → review agent (PR có IAM: grant cho role apply) → merge.
3. **Bootstrap local MFA** từ `main` đã pull: apply có target `aws_iam_policy.tf_apply_sec` (các bước trong đầu `cicd_sec.tf`;
   thêm `access-analyzer:*ArchiveRule` + `ListArchiveRules`). Plan có target phải chỉ đổi policy đó (1 in-place).
4. CI apply: mong đợi **3 thêm** (3 archive rule) + **1 sửa tại chỗ** (`aws_cloudwatch_event_rule.sec_iam_change`), không xoá gì.
5. Lưu trữ 11 phát hiện cũ (archive rule chỉ tự áp cho phát hiện MỚI), mỗi rule 1 lệnh:
   `aws accessanalyzer apply-archive-rule --analyzer-arn <arn analyzer> --rule-name github-oidc-deploy-roles --profile aa365-admin --region us-west-1`
   (lặp với `identity-center-admin-permission-set`, `bronze-bedrock-batch-satellite`). Kiểm: `list-findings-v2` lọc
   `status = ACTIVE` → **0**.
6. `python3 tools/terraform/sec_alert_check.py --profile aa365-admin --region us-west-1 --env dev` → **0 failed** (44 ca).
7. `bash .tmp-session/S256/aa873/alert_test.sh all` (chạy nền ~45 phút vì chờ phát hiện analyzer) → đếm mail theo bảng 4.2;
   `verify` in TriggeredRules/Invocations/FailedInvocations từng rule. FailedInvocations phải = 0.
8. Cập nhật Linear AA-873 bằng bằng chứng (số mail, metric, 0 ACTIVE) — Done-when "alert test" của issue.

## 6. Việc còn lại / không làm

- **GuardDuty**: không bật (cần tech lead đồng ý riêng, ~15–20 USD/tháng — S255 §7).
- **Q1** (permission set Identity Center): câu hỏi cho đại lý thanh toán, không chặn.
- Đọc trust live của 9 role: bước 1 của điều phối.
- Phân tích "unused access" (trả phí 0,20 USD/role/tháng): không bật.
