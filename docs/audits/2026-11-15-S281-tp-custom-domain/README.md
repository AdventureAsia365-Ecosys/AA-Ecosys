# AA-1090 TripPlanner R8 — tên miền riêng của đại lý: thiết kế, chi phí và các bước sau khi duyệt

*15/11/2026, phiên S281 (Claude Code, lane l12-tp-domain), viết cho tech lead. Chưa apply gì: Terraform, IAM và job chỉ
chạy sau khi tech lead duyệt phần chi phí (luật "cost before new AWS services").*

## 1. Tóm tắt

1. Đại lý chạy planner trên địa chỉ của mình (ví dụ `trip.<tên miền đại lý>`) bên cạnh đường dẫn `/{slug}` của mình.
2. Nhân viên thêm tên miền ở **Tenant 360 › Subscription › TripPlanner own domains** (cùng chỗ với lead route, vì cài
   đặt site TripPlanner của đại lý hiện do AA làm). Trang hiện **2 bản ghi DNS** cho đại lý: CNAME của host về
   distribution CloudFront, CNAME xác thực ACM. Trạng thái: pending → validating → attaching → active (failed / removing).
3. Job CIS `tripplanner_custom_domain` (bảng job `shared.job`) xin chứng chỉ ACM ở us-east-1 (xác thực DNS, có tag),
   chờ bản ghi, rồi giữ **một chứng chỉ "edge"** trên distribution gồm tên của chứng chỉ gốc (wildcard zone của mình)
   + mọi host đại lý, đổi alias và chứng chỉ trong **một** `UpdateDistribution`. Gỡ host: job tháo alias, xoá chứng
   chỉ; hết host thì distribution trở lại đúng trạng thái Terraform (host công khai + wildcard).
4. TripPlanner nhận request theo Host: host lạ → tra `catalog.v_tenant_tripplanner_v1.custom_domains` (CIS 428) → đúng
   tenant (branding, tour, lead route như `/{slug}`); host không biết → trang 404 trơn, không bao giờ hiện site AA.
5. WAF giữ nguyên tác dụng: 3 rule TripPlanner trong web ACL của ALB chuyển từ khớp **Host** sang khớp **header riêng
   của distribution** (`x-aa-tp-site`, secret ngẫu nhiên), nên áp cho mọi alias. Rule ALB mới chuyển mọi alias về
   service TripPlanner.
6. Giới hạn là **setting** (Platform › Settings, CIS 427): số host mỗi đại lý (mặc định 1, chỉnh riêng từng đại lý),
   tổng số host trên edge (8), thời gian chờ bản ghi DNS (72 giờ), chu kỳ kiểm (120 giây).
7. **Chi phí ước tính: khoảng 0 USD/tháng** trên Dev (mục 3).

## 2. Vì sao một chứng chỉ edge (và khi nào phải đổi)

CloudFront chỉ gắn **một** viewer certificate cho một distribution, và chứng chỉ đó phải chứa mọi alias. Vì vậy:

| Phương án | Ưu | Nhược | Chi phí |
|---|---|---|---|
| **Chọn: SAN edge cert trên distribution hiện có** | Không thêm distribution, không dịch vụ mới; IAM chỉ `UpdateDistribution` trên 1 distribution | Trần = quota "domain names per ACM certificate" (mặc định 10, xin nâng được); mỗi lần thêm/gỡ host là xin lại chứng chỉ edge (miễn phí, cấp ngay vì ACM dùng lại bản ghi xác thực trong cùng account) | 0 |
| Một distribution cho mỗi đại lý | Cô lập từng đại lý, chứng chỉ riêng | Job phải Create/Disable/Delete distribution (chờ deploy 5–15 phút), IAM rộng hơn, cấu hình nhân bản | 0 ở Dev (free tier dùng chung) |
| CloudFront SaaS Manager (multi-tenant distribution) | Dịch vụ AWS làm đúng bài toán này, chứng chỉ do CloudFront quản lý | Loại distribution mới (không chuyển distribution cũ được), **có phí theo tenant — giá chưa kiểm trong lane** | chưa kiểm |

**Ngưỡng đổi phương án:** khi số host đại lý cần vượt quota ACM đã nâng, hoặc cần cô lập chứng chỉ từng đại lý — lúc
đó so lại SaaS Manager với giá thật (kiểm trang giá AWS trước).

## 3. Chi phí hằng tháng (ước tính, Dev)

| Hạng mục | Giá AWS | Dev |
|---|---|---|
| Chứng chỉ ACM public (mỗi host + edge) | 0 USD (ACM public certificate dùng với CloudFront không tính phí) | 0 |
| Alternate domain names (CNAME) trên CloudFront, SNI | 0 USD (chỉ IP riêng mới tính phí, không dùng) | 0 |
| Gọi API ACM / CloudFront của job (Describe, Get, Update, Request) | control plane, không tính phí | 0 |
| Header `x-aa-tp-site` (origin custom header), IAM policy | 0 | 0 |
| Rule ALB mới (`tripplanner_web_alias`, rule thứ 14 trên listener :80) | LCU tính theo lượt đánh giá rule vượt 10 rule miễn phí | < 0,01 USD |
| WAF: không thêm rule, chỉ đổi phạm vi; request của host đại lý bị kiểm như host công khai | 0,60 USD / triệu request | ~0 (traffic Dev) |
| CloudFront request/băng thông của host đại lý | như host công khai; free tier 1 TB + 10 triệu request/tháng | 0 |
| **Tổng** | | **≈ 0 USD/tháng** |

Prod (sau này): chi phí tăng theo traffic của đại lý như traffic host công khai (băng thông + request + WAF), không có
phí cố định mới.

## 4. Thay đổi theo repo (các PR của lane)

| Repo | PR | Nội dung |
|---|---|---|
| AA-CIS-App | migration-only (CIS 427–428) | bảng `shared.tenant_tripplanner_domain`, 4 setting, cột view `custom_domains`, contract 1.8, dòng erasure, allowlist RLS |
| AA-CIS-App | code (sau 427–428) | editor Tenant 360, job `tripplanner_custom_domain`, `tp_edge.py`, readiness 427 |
| AA-TripPlanner-Web | code | `GET /browse/tenant-host/{host}`, `proxy.ts` + `lib/tenantHost.ts` (Host → tenant, map đường dẫn) |
| AA-CIS-Infra | code (không apply) | header site, rule ALB alias, phạm vi WAF, `ignore_changes` alias/cert, IAM policy + env cho CIS |
| AA-CIS-Infra | bản sao allowlist RLS | sau migration CIS (Copy Guard) |
| Root | docs | dòng lưu trữ DM-7.1, contract 1.8, ghi chú này, amendment ADR 0019 |

## 5. Các bước sau khi tech lead duyệt chi phí

1. Terraform plan (CI Terraform Plan của PR Infra) — đọc kỹ: phải thấy `random_password.tp_web_site_marker` (mới),
   `aws_cloudfront_distribution.tripplanner_web` (update in place: thêm custom header), `aws_lb_listener_rule.tripplanner_web_alias`
   (mới), `module.waf.aws_wafv2_web_acl.this` (update: 3 rule đổi statement), `module.ecs.aws_iam_role_policy.ecs_task_tripplanner_custom_domain[0]`
   (mới), 2 task definition CIS (env mới). **Không** có destroy.
2. Apply bước 1 (`-target` distribution, secret, rule alias), chờ distribution `Deployed`; bước 2 apply phần còn lại.
3. Deploy lại CIS (task def mới có env), kiểm `/health/ready` (cần 427).
4. Chạy thử với host phụ của zone thử nghiệm của mình (không dùng tên miền khách thật): thêm host trên Tenant 360 của
   tenant giả lập, tạo 2 bản ghi trong Route 53 của zone đó, chờ `active`, `curl -sI https://<host>/` → 200 và trang
   mang branding đại lý; `curl -sI https://<host>/destinations` → 404; WAF: `curl` không token lên `/api/trip/send` →
   202 + `x-amzn-waf-action: challenge`. Gỡ host → job tháo alias, xoá chứng chỉ, `curl` host → lỗi TLS/403, distribution
   về đúng alias + chứng chỉ Terraform (`aws cloudfront get-distribution-config`).

## 6. Rủi ro và việc nối tiếp

- Đại lý phải **giữ** CNAME xác thực để ACM tự gia hạn chứng chỉ edge.
- Nếu lần chạy job đầu báo AccessDenied ở điều kiện `acm:ValidationMethod`, bỏ điều kiện đó (giữ điều kiện tag) — ghi
  ở notes của Infra, không nới rộng mặc định.
- Nối tiếp: trang tự phục vụ cho đại lý trong CRM web; migration đánh dấu 4 setting `enforced`; job dọn chứng chỉ mồ
  côi có tag; cảnh báo khi một host `failed`; canonical/sitemap theo host đại lý.
