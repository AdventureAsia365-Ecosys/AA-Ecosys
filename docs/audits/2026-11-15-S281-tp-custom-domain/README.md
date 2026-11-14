# AA-1090 TripPlanner R8 — tên miền riêng của đại lý: thiết kế, chi phí và các bước sau khi duyệt

*15/11/2026, phiên S281 (Claude Code, lane l12-tp-domain), viết cho tech lead. Chưa apply gì: Terraform, IAM và job chỉ
chạy sau khi tech lead duyệt phần chi phí (luật "cost before new AWS services"). Bản này đã sửa theo vòng review độc
lập (mục 7).*

## 1. Tóm tắt

1. Đại lý chạy planner trên địa chỉ của mình (ví dụ `trip.<tên miền đại lý>`) bên cạnh đường dẫn `/{slug}` của mình.
2. Nhân viên thêm tên miền ở **Tenant 360 › Subscription › TripPlanner own domains** (cùng chỗ với lead route, vì cài
   đặt site TripPlanner của đại lý hiện do AA làm). Trang hiện **2 bản ghi DNS** cho đại lý: CNAME của host về
   distribution CloudFront dành cho đại lý, CNAME xác thực ACM. Trạng thái: pending → validating → attaching → active
   (failed / removing).
3. **Host đại lý nằm trên một distribution CloudFront riêng** (`tripplanner_agency`, bản sao của distribution công
   khai, không alias, chứng chỉ mặc định của CloudFront). Host công khai `tripplanner.<zone>` giữ nguyên distribution
   và chứng chỉ wildcard của Terraform, **không bao giờ** dùng chung chứng chỉ với đại lý.
4. Job CIS `tripplanner_custom_domain` (bảng job `shared.job`) xin chứng chỉ ACM cho host ở us-east-1 (xác thực DNS,
   có tag), chờ bản ghi, rồi giữ **một chứng chỉ "edge"** trên distribution đại lý gồm mọi host đại lý đang gắn, đổi
   alias và chứng chỉ trong **một** `UpdateDistribution`. Gỡ host: job tháo alias, xoá chứng chỉ; hết host thì
   distribution đại lý trở lại đúng trạng thái Terraform (không alias, chứng chỉ mặc định).
5. TripPlanner nhận request theo Host: host lạ → tra `catalog.v_tenant_tripplanner_v1.custom_domains` (CIS 428) → đúng
   tenant (branding, tour, lead route như `/{slug}`); host không biết → trang 404 trơn, không bao giờ hiện site AA.
6. WAF giữ nguyên tác dụng: 3 rule TripPlanner trong web ACL của ALB chuyển từ khớp **Host** sang khớp **header riêng**
   (`x-aa-tp-site`, secret ngẫu nhiên, cả hai distribution cùng gắn), nên áp cho mọi alias. Rule ALB mới chuyển mọi
   alias về service TripPlanner.
7. Giới hạn là **setting** (Platform › Settings, CIS 427): số host mỗi đại lý (mặc định 1, chỉnh riêng từng đại lý),
   tổng số host trên edge (10), thời gian chờ bản ghi DNS (72 giờ), chu kỳ kiểm (120 giây), thời gian chờ chứng chỉ
   edge mới (6 giờ), số ngày ân hạn trước khi hết hạn (30 ngày).
8. **Chi phí ước tính: khoảng 0 USD/tháng** trên Dev (mục 3).

## 2. Vì sao một chứng chỉ edge trên một distribution riêng (và khi nào phải đổi)

CloudFront chỉ gắn **một** viewer certificate cho một distribution, và chứng chỉ đó phải chứa mọi alias.

| Phương án | Ưu | Nhược | Chi phí |
|---|---|---|---|
| SAN edge cert trên distribution công khai (bản đầu, đã bỏ) | Không thêm distribution | Chứng chỉ của host công khai phụ thuộc DNS của mọi đại lý: một đại lý xoá bản ghi là gia hạn hỏng cho cả host của mình | 0 |
| **Chọn: SAN edge cert trên distribution riêng cho đại lý** | Host công khai tách hẳn; không dịch vụ mới; IAM chỉ `UpdateDistribution` trên distribution đại lý | Trần = quota "domain names per ACM certificate" (mặc định 10, xin nâng tới 100); các đại lý vẫn phụ thuộc bản ghi của nhau (mục 6, có chặn tự động) | 0 (CloudFront trả theo dùng, không phí cố định mỗi distribution) |
| Một distribution cho mỗi đại lý | Cô lập hoàn toàn từng đại lý | Job phải Create/Disable/Delete distribution (chờ deploy 5–15 phút), IAM rộng hơn, cấu hình nhân bản | 0 ở Dev |
| CloudFront SaaS Manager (multi-tenant distribution) | Dịch vụ AWS làm đúng bài toán này, chứng chỉ riêng từng tenant do CloudFront quản lý | Loại distribution mới, **có phí theo tenant — giá chưa kiểm trong lane** | chưa kiểm |

**Ngưỡng đổi phương án:** khi số host đại lý cần vượt quota ACM đã nâng, hoặc khi việc tháo host của một đại lý (mục
6) xảy ra thường xuyên — lúc đó so lại SaaS Manager với giá thật (kiểm trang giá AWS trước).

## 3. Chi phí hằng tháng (ước tính, Dev)

| Hạng mục | Giá AWS | Dev |
|---|---|---|
| Distribution CloudFront thứ hai (đại lý) | không phí cố định (pay-as-you-go: chỉ tính request + băng thông) | 0 |
| Chứng chỉ ACM public (mỗi host + edge) | 0 USD (ACM public certificate dùng với CloudFront không tính phí) | 0 |
| Alternate domain names (CNAME) trên CloudFront, SNI | 0 USD (chỉ IP riêng mới tính phí, không dùng) | 0 |
| Gọi API ACM / CloudFront của job (Describe, Get, Update, Request), kể cả kiểm tra hằng ngày | control plane, không tính phí | 0 |
| Cảnh báo (chuông admin + tối đa 1 e-mail/ngày qua SNS sẵn có) | trong mức SNS miễn phí | 0 |
| Header `x-aa-tp-site` (origin custom header), IAM policy | 0 | 0 |
| Rule ALB mới (`tripplanner_web_alias`) | LCU tính theo lượt đánh giá rule vượt 10 rule miễn phí | < 0,01 USD |
| WAF: không thêm rule, chỉ đổi phạm vi; request của host đại lý bị kiểm như host công khai | 0,60 USD / triệu request | ~0 (traffic Dev) |
| CloudFront request/băng thông của host đại lý | như host công khai; free tier 1 TB + 10 triệu request/tháng | 0 |
| **Tổng** | | **≈ 0 USD/tháng** |

Prod (sau này): chi phí tăng theo traffic của đại lý như traffic host công khai (băng thông + request + WAF), không có
phí cố định mới.

## 4. Thay đổi theo repo (các PR của lane)

| Repo | PR | Nội dung |
|---|---|---|
| AA-CIS-App | migration-only (CIS 427–428) | bảng `shared.tenant_tripplanner_domain`, 6 setting, cột view `custom_domains`, contract 1.8, dòng erasure, allowlist RLS |
| AA-CIS-App | code (sau 427–428) | editor Tenant 360 (kể cả "Retry removal"), job `tripplanner_custom_domain` + kiểm tra edge hằng ngày, `tp_edge.py`, cảnh báo `tripplanner_custom_domain_dns`, readiness 427 |
| AA-TripPlanner-Web | code | `GET /browse/tenant-host/{host}`, `proxy.ts` + `lib/tenantHost.ts` (Host → tenant, map đường dẫn) |
| AA-CIS-Infra | code (không apply) | distribution `tripplanner_agency`, header site, rule ALB alias, phạm vi WAF, IAM policy (Deny chứng chỉ Terraform) + env cho CIS |
| AA-CIS-Infra | bản sao allowlist RLS | sau migration CIS (Copy Guard) |
| Root | docs | dòng lưu trữ DM-7.1, contract 1.8, ghi chú này, amendment ADR 0019 |

## 5. Các bước sau khi tech lead duyệt chi phí

1. Terraform plan (CI Terraform Plan của PR Infra) — đọc kỹ: phải thấy `random_password.tp_web_site_marker` (mới),
   `aws_cloudfront_distribution.tripplanner_web` (update in place: thêm custom header; alias và chứng chỉ **không**
   đổi), `aws_cloudfront_distribution.tripplanner_agency` (mới), `aws_lb_listener_rule.tripplanner_web_alias` (mới),
   `module.waf.aws_wafv2_web_acl.this` (update: 3 rule đổi statement), `module.ecs.aws_iam_role_policy.ecs_task_tripplanner_custom_domain[0]`
   (mới), 2 task definition CIS (env `TP_AGENCY_DISTRIBUTION_ID`). **Không** có destroy.
2. Apply bước 1 (`-target` distribution công khai, secret, rule alias), chờ distribution `Deployed`; bước 2 apply phần
   còn lại.
3. Kiểm danh sách chứng chỉ us-east-1: mỗi chứng chỉ phải có tag `ManagedBy = terraform` hoặc tag của job (chứng chỉ
   tạo tay ngoài Terraform thì thêm ARN vào danh sách bảo vệ trước).
4. Deploy lại CIS (task def mới có env), kiểm `/health/ready` (cần 427).
5. Chạy thử với host phụ của zone thử nghiệm của mình (không dùng tên miền khách thật): thêm host trên Tenant 360 của
   tenant giả lập, tạo 2 bản ghi trong Route 53 của zone đó, chờ `active`, `curl -sI https://<host>/` → 200 và trang
   mang branding đại lý; `curl -sI https://<host>/destinations` → 404; WAF: `curl` không token lên `/api/trip/send` →
   202 + `x-amzn-waf-action: challenge`. Xoá bản ghi xác thực của host thử thứ hai rồi thêm/gỡ host thứ nhất: sau
   6 giờ (setting) host thứ hai bị tháo (`validation_record_gone`, có chuông), host thứ nhất vẫn chạy. Gỡ host → job
   tháo alias, xoá chứng chỉ; distribution đại lý về không alias + chứng chỉ mặc định; distribution công khai không
   đổi (`aws cloudfront get-distribution-config`).

## 6. Rủi ro và cách chặn

- **Một đại lý xoá bản ghi xác thực (hoặc bỏ tên miền).** ACM chỉ tự gia hạn chứng chỉ edge dùng chung khi **mọi** đại
  lý còn giữ bản ghi; mỗi lần thêm/gỡ host cũng cần cấp lại chứng chỉ edge với mọi tên còn lại. Nếu không chặn: chứng
  chỉ edge mới treo `PENDING_VALIDATION`, việc thêm/gỡ host của đại lý khác bị kẹt; tới hạn (khoảng 13 tháng sau khi
  cấp) chứng chỉ hết hạn và **mọi** tên miền đại lý báo lỗi TLS. Host công khai **không** bị ảnh hưởng (distribution
  riêng). Cách chặn (đã code, có test):
  1. Chứng chỉ edge mới còn `PENDING_VALIDATION` quá `cis.tripplanner.custom_domain_edge_pending_hours` (6 giờ): job
     đọc trạng thái từng tên, **tháo đúng host thiếu bản ghi** (failed, `validation_record_gone`, chuông + e-mail), xin
     lại chứng chỉ không có host đó. Việc của đại lý khác đi tiếp.
  2. Kiểm tra edge **hằng ngày** (cùng job kind, xếp hàng bởi sampler của api, một lần mỗi ngày UTC): đọc
     `RenewalSummary` của chứng chỉ đang phục vụ. Host chặn gia hạn → **cảnh báo ngay**; khi chứng chỉ còn ≤
     `cis.tripplanner.custom_domain_renewal_grace_days` (30) ngày → tháo host đó và thay chứng chỉ không có nó, để các
     đại lý khác không bao giờ phục vụ chứng chỉ hết hạn. ACM bắt đầu gia hạn từ 60 ngày trước hạn, nên đại lý có
     khoảng 30 ngày sửa bản ghi sau cảnh báo.
  - Đổi lại: đại lý thiếu bản ghi mất tên miền riêng tới khi sửa và nhân viên bấm Retry (planner vẫn chạy trên
    `/{slug}`).
- Quyền IAM: job chỉ tag được bằng tag của mình với 3 khoá cố định; mọi chứng chỉ tag `ManagedBy = terraform` và
  wildcard của host công khai bị **Deny** tag/gỡ tag/xoá. Chứng chỉ tạo tay ngoài Terraform: kiểm ở bước 5.3.
- Chứng chỉ riêng của từng host không gắn vào đâu nên ACM không gia hạn; hết hạn sau khoảng 13 tháng, không ảnh hưởng
  (chứng chỉ edge dùng chung bản ghi xác thực). Dọn dần trong job dọn chứng chỉ (nối tiếp).
- Nối tiếp: trang tự phục vụ cho đại lý trong CRM web; migration đánh dấu 6 setting `enforced`; job dọn chứng chỉ mồ
  côi / hết hạn có tag; canonical/sitemap theo host đại lý.

## 7. Sửa theo review độc lập (S281)

| Phát hiện | Xử lý |
|---|---|
| Retry sau `validation_timeout` thất bại lại ngay (cửa sổ vẫn tính từ lúc thêm) | Retry đặt `requested_at = now()`, xoá `validated_at` / `active_at`; xin chứng chỉ mới cũng đặt lại `requested_at` |
| Gỡ host có thể kẹt ở `removing` không cách nào chạy lại | Gỡ lại = job mới (khoá mới); lý do kẹt hiện trên Tenant 360 với nút "Retry removal"; host chưa từng gắn không cần đụng edge; xoá xong chứng chỉ là xoá `certificate_arn`; AccessDenied khi xoá ARN đã mất = coi như đã xoá |
| `AddTagsToCertificate` chung statement với điều kiện `acm:ValidationMethod` → mọi request có tag bị từ chối | Tách statement riêng (không điều kiện ValidationMethod), giới hạn khoá tag |
| `AddTagsToCertificate` trên `*` cho phép tự gắn tag vào chứng chỉ khác rồi xoá nó | Deny tag/gỡ tag/xoá mọi chứng chỉ `ManagedBy = terraform` + danh sách bảo vệ; `aws:TagKeys` chỉ 3 khoá của job; quyền đọc chứng chỉ gốc bỏ hẳn |
| Một đại lý làm hỏng gia hạn chứng chỉ chung, kéo cả host công khai | Distribution riêng cho đại lý + 2 cơ chế chặn ở mục 6 |
