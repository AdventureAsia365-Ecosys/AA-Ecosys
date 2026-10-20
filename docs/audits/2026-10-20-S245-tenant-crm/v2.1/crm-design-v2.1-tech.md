# Tenant CRM — v2.1: phụ lục kỹ thuật cho thiết kế v2 (AA-821 / PR-19)

Ngày 20/10/2026, phiên S245 (vòng 3). Tác nhân: Claude Code. Tài liệu này **chỉ bổ sung** cho
`out/crm-design-v2.md` ("v2"), không viết lại. Chỗ nào phụ lục không nhắc thì v2 vẫn giữ nguyên. Chỉ đọc và viết
tài liệu: không đổi repo, không ghi AWS, Linear hay Jira, không gọi API trả phí.

**Đã đọc đầy đủ:**
- ý kiến của anh: `owner-input.md` (vòng 1) và `owner-approvals-r2.md` (vòng 2; khi lệch với v2 thì vòng 2 thắng);
- spec của chị Thư: `docs/research/partner-crm-spec.md`;
- các tài liệu thiết kế: `out/crm-design-v2.md`, `out/crm-questions.json`, `out/crm-01-current-state.md`,
  `out/crm-judges.md`;
- ba bản review: `r3/review-security.md` (mã S1–S19), `r3/review-architecture.md` (F1–F17) và
  `r3/review-integration.md` (C1–C2, H1–H7, M1–M7, L1–L5).

**Mốc code tôi tự đọc lại** (bằng `git show origin/main:…`, vì checkout local đang chậm):

| Repo | Mốc |
|---|---|
| AA-CIS-App | `446dcfc5` |
| AA-CIS-Infra | `ede5e67` |
| AA-Booking | `e478663` |
| AA-TripPlanner-Web | `db7bb7b` |
| root | `3336bd2` |

**Ranh giới quyết định.** Engineering chỉ chốt chuyện kỹ thuật. Những gì là kinh doanh, pháp lý, giá cho đại lý, hay
chọn vendor/app ngoài có phí đều nằm trong `r3/thu-questions.md` để chị Thư cho ý kiến. Ở đây chỉ nêu chi phí và
mặt kỹ thuật của chúng.

---

## 0. Tóm tắt

1. **N3 b (app đại lý chạy container Fargate sau CloudFront) làm được, nhưng không theo cách v2 giả định.** Gói
   CloudFront Free và Pro **không có** "Private origins within VPC". Còn ALB dùng chung thì public, chỉ mở :80 cho dải
   VPC, và có chặn theo nước. Đường đi chốt là **CloudFront trả theo lượt (pay-as-you-go) → VPC origin trỏ vào NLB nội
   bộ đang có sẵn → một rule trên ALB**. Ở mức Dev chi phí ≈ $0. Không dùng WAF trên Dev; WAF CloudFront (không chặn
   nước) ≈ $7–8/tháng thì để tới lúc có dữ liệu thật (§3.1).
2. **D12 đổi:** CRM có gateway LLM riêng và sổ `crm.llm_call` riêng. **D22 đổi:** CRM có job runner `crm.job` riêng.
   CIS admin xem cả hai **chỉ đọc**, qua một hợp đồng HTTP `ops-feed.v1`, xác thực bằng token WORKFORCE của chính nhân
   viên đang đăng nhập. Không có grant DB nào giữa hai app, và không dùng `ADMIN_SECRET` (§3.2, §3.3).
3. **Chạy trên Dev bằng đại lý giả.** Prod cell, gói Documenso, các thủ tục xác minh với Meta/Google/Microsoft và
   service public thứ hai đều chuyển sang một đợt riêng gọi là **Go-real**, ra khỏi đường găng. Đợt này chỉ mở khi chị
   Thư chọn đại lý thật đầu tiên (§3.5).
4. **Lát cắt đầu tiên chạy được trên Dev:** 18 issue, ≈ **3–4 phiên** (thêm một lần anh apply bằng MFA). Kết quả: một
   đại lý giả đăng nhập; khách điền form; job CRM xử lý; chuyến hiện trên bảng của đại lý; dữ liệu danh tính đã mã hoá
   bằng khoá KMS của đúng đại lý đó; CIS admin thấy job của CRM (§4).
5. **Đủ 23 module trên Dev:** thêm ≈ 105–110 issue, tức ≈ 18–20 phiên nữa sau lát cắt. Ở nhịp ~2,8 phiên CRM mỗi tuần
   (≈ 22 phiên ≈ 8 tuần từ S246) thì xong khoảng **giữa tháng 12/2026 nếu không gián đoạn; ghi "giữa 12/2026 – giữa
   1/2027"** để chừa chỗ cho chờ MFA, review và nghỉ lễ (ước tính; sửa ở kiểm tra cuối, bản trước ghi "giữa 1/2027"). Cột dài nhất là phần hàng AA trong Booking: **12–16 issue**,
   không phải 6–7 như v2 ghi (§4.3).
6. **Chi phí Dev tăng thêm:** ≈ **$10–15/tháng** trong tháng 11, rồi ≈ **$14–21/tháng** từ tháng 1. Nếu không có Spot
   thì tối đa ≈ $32. So với cái anh đã duyệt (v2 + N3 b ≈ $19–21, cộng prod cell $27 và Documenso $3.000/năm), bản
   này rẻ hơn vì hai khoản sau được hoãn (§5).
7. **Review bảo mật tìm ra một lỗi nghiêm trọng (S1):** thiết kế khoá KMS trong v2 **không** ngăn được admin acc2 giải
   mã, và câu IAM viết trong v2 thực ra không cấp gì. Đã sửa bằng key policy mẫu có `Deny` tường minh, kèm cảnh báo
   hiện trong audit của đại lý. Hệ quả là câu H3 phải sửa thêm một lần nữa, và câu đó là việc của chị Thư.
8. Có 14 quyết định kỹ thuật mới, T1–T14, đều có khuyến nghị (§3.6). Các câu trả lời cho câu hỏi của anh nằm ở §7:
   CASA, Documenso và các phương án ký điện tử khác, N4, N5, N8, N10.

---

## 1. Những gì tôi tự kiểm lại (không dựa vào lời của v2 hay của review)

| # | Điều được dùng trong phụ lục | Bằng chứng (đọc ngày 20/10/2026) | Kết quả |
|---|---|---|---|
| K1 | CloudFront Free/Pro không có VPC origin | [aws.amazon.com/cloudfront/pricing](https://aws.amazon.com/cloudfront/pricing/): Free "$0/month", Pro "$15/month", "Private Origins Within VPC: Not included"; Business $200 và Premium $1.000 thì "Included" | ✔ (F1, C2 đúng) |
| K2 | VPC origin nhận NLB có SG, không listener TLS; us-west-1 loại trừ AZ `usw1-az2` | [VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html): "a Network Load Balancer must have a security group attached", "NLB with TLS listeners cannot be added"; mục "Option 2" cho phép mở SG từ `CloudFront-VPCOrigins-Service-SG` | ✔ |
| K3 | NLB VPC link là internal, trong private subnet, có SG, listener TCP :80, target là ALB | Infra `modules/alb/vpc_link.tf:9-20,35-39,61-65,84-88` | ✔ (vào làm VPC origin được) |
| K4 | ALB dùng chung là public; default action :80 và :443 đi thẳng vào target group CIS; SG chỉ mở :80 cho VPC | `modules/alb/main.tf:13,16,78-85,92-101`; `modules/vpc/main.tf:256-270` | ✔ (vì vậy loại phương án mở :443) |
| K5 | CloudFront pay-as-you-go: lấy dữ liệu từ origin AWS/VPC miễn phí; free tier 1 TB + 10 triệu request mỗi tháng | [pay-as-you-go](https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/): "Free for origin fetches from any AWS origin", "1 TB … 10,000,000 HTTP or HTTPS Requests per month"; $0,085/GB, $0,0100/10k HTTPS | ✔ |
| K6 | Role apply chỉ có `cloudfront:UpdateDistribution`; ECR chỉ cho tên `aa-booking-<env>-*` | `accounts/aa365/cicd_split.tf:683-689`; `accounts/aa365/cicd.tf:305-322` | ✔ (cần bootstrap, F3) |
| K7 | Role apply **đã có** `apigateway:SetWebACL` (comment cũ nói ngược lại) | `cicd_split.tf:582-590` | ✔ (F15) |
| K8 | WAF dùng chung chặn mọi nước ngoài 10 nước | `modules/waf/variables.tf:20-25` | ✔ |
| K9 | Role invoker acc3 chỉ tin CIS + TripPlanner; chỉ có profile `global.` (Sonnet 4.6, Haiku 4.5, Sonnet 5, Opus 5.5, GPT); không `us.`, không Haiku 5.5, không `ApplyGuardrail` | `accounts/acc3-bedrock/main.tf:21-52,69-106` | ✔ (S6, H2) |
| K10 | Giá Claude (bảng của Anthropic): Haiku 5.5 $0,10/$0,50 cho prompt ≤ 100K; Sonnet 5.5 $2/$10; **Haiku 4.5 $1/$5** (đắt gấp 10 lần Haiku 5.5). Giá trên Bedrock do đối tác đặt, chưa kiểm | skill `claude-api` (bảng cache 06/10/2026) | ✔ list; Bedrock = **ước tính** |
| K11 | IAM không dùng được alias để chỉ định khoá KMS | [KMS keys in IAM policies](https://docs.aws.amazon.com/kms/latest/developerguide/cmks-in-iam-policies.html): "You cannot use a key id, alias name, or alias ARN to identify a KMS key in an IAM policy statement" | ✔ (S1) |
| K12 | Guardrails: loại hộ chiếu chỉ có `US_PASSPORT_NUMBER`; trường `match` chứa giá trị gốc | [GuardrailPiiEntityFilter](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailPiiEntityFilter.html) | ✔ (S6) |
| K13 | SES: mỗi rule set tối đa 200 rule, không xin tăng được | [SES quotas](https://docs.aws.amazon.com/ses/latest/dg/quotas.html): "Maximum number of rules per receipt rule set: 200, No" | ✔ (F7, M1) |
| K14 | Ngân sách kết nối: trần 75 % × 181 ≈ 135; tổng hiện ~126 | root `docs/architecture/data-standards/03-scaling.md:99,115,125,139,154` | ✔ (F4) |
| K15 | Pool Booking `max_size=5`; runner Booking 675 dòng; lỗi job lưu `error` dạng chữ tự do | Booking `backend/app/db.py:68-69`; `backend/app/jobs/*.py` (675 dòng); `jobs/queue.py:123,143,158` | ✔ (S7) |
| K16 | `booking.trip_cases.customer_id` NOT NULL, không có `tenant_id` | `docs/architecture/db-schema-reference.md` (root `3336bd2`), bảng `booking.trip_cases` | ✔ (C1) |
| K17 | CIS có app registry (AA-884); TripPlanner báo chi phí LLM bằng cách ghi vào `shared.llm_call_log` | CIS `api/core/app_registry.py:1-20,54-68`; `api/routers/admin_job_runner.py:7` | ✔ (F8, H7) |
| K18 | Cognito EXTERNAL: `mfa_configuration = "OFF"`; client `cis-portal` có sẵn callback `localhost:3004` | Infra `identity.tf:445`; `identity_variables.tf:163-168` | ✔ (S12, F6) |
| K19 | `alert_email` đã là `nghieppham@adventure.asia` | Infra `accounts/aa365/variables.tf:152-156` (commit `08f73f6`) | ✔ (L1: bỏ khỏi kế hoạch) |
| K20 | MapView của TripPlanner kéo theo `@/lib/api` (backend TP), `@/lib/useTrip`, `@/lib/tileLoader`; TP chạy Next 15.5.28 + Tailwind 3.4.14 | TP `frontend/components/MapView.tsx:6-16`; `frontend/package.json:15,29` | ✔ (H3) |
| K21 | Gmail: `gmail.send` thuộc nhóm *Sensitive*; `readonly`, `modify`, `compose` thuộc nhóm *Restricted*; "If you store restricted scope data on servers (or transmit), then you must go through a security assessment" | [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes) | ✔ (§7.1) |
| K22 | Giá Documenso | [documenso.com/pricing](https://documenso.com/pricing): Free 5 tài liệu/tháng, không ghi API; Teams $40 ($480 trả theo năm), 5 user, "API Access for Automation", "Embedded Signing"; Platform $250 ($3.000 trả theo năm), "Embedded Signing (Whitelabel)"; tự host Enterprise phải xin báo giá | ✔ |
| K23 | Fargate us-west-1: ARM $0,03725/vCPU-h, $0,00409/GB-h; x86 $0,04656/$0,00511 | price list `AmazonECS/current/us-west-1`, publicationDate 2026-10-19T22:43:17Z | ✔ |

---

## 2. (a) Mọi phát hiện của ba bản review: nhận hay không, và vì sao

Quy ước: **Nhận** = làm đúng như review đề xuất. **Nhận, sửa** = nhận phần chẩn đoán nhưng chọn cách sửa khác.
**Không nhận** = có lý do bác. **Hoãn** = nhận, nhưng làm ở đợt Go-real.

### 2.1 Năm chỗ ba bản review mâu thuẫn nhau, và tôi chốt thế nào

| Chủ đề | Các phương án | Chốt | Vì sao |
|---|---|---|---|
| Đường từ CloudFront vào container (N3 b) | F1-O2: PAYG + VPC origin trên NLB nội bộ · C2-b: giữ gói Free, mở :443 của ALB cho prefix list CloudFront · S5: VPC origin trên NLB (giống O2) | **O2** | C2-b đảo ngược việc đóng :443 ở S235. Default action của :443 đi vào CIS (K4), nên mọi distribution CloudFront (kể cả của người lạ) chạm được CIS, và quota rule SG còn bị prefix list ăn mất. O2 chỉ chạm một rule SG của NLB và một rule ALB, ≈ $0 (K1–K5) |
| CIS xem job và LLM của CRM bằng cách nào | F8: API Gateway `AWS_IAM` + SigV4 · S7: chuyển tiếp token WORKFORCE của nhân viên | **S7** (token người dùng, gọi qua NLB nội bộ) | S4/H1 chỉ ra `AWS_IAM` bị vượt được từ trong VPC. Token WORKFORCE được CRM tự kiểm (issuer, `client_id = cis-admin`, nhóm `cis-admin`), giống cách CIS đang kiểm staff (CIS `api/core/identity_config.py:3,78`). Không cần secret mới hay quyền IAM mới |
| Xác thực service-to-service (CRM → CIS feed/catalog, CRM → Booking B2B) | S4: resource policy + header bí mật do API Gateway gắn + rule ALB · H1: JWT dịch vụ ký bằng KMS, bên nhận tự kiểm | **H1** (JWT ký bằng khoá KMS bất đối xứng, $1/tháng); `AWS_IAM` chỉ là lớp phòng thủ thêm | Bên nhận tự kiểm thì không phụ thuộc mạng. Thắt SG của ALB theo SG của NLB vẫn làm, nhưng chỉ là vệ sinh, vì NLB vẫn mở cho cả dải VPC (K3). Chưa cần trong lát cắt đầu |
| Ai nắm vai trò CRM (owner/agent/assistant) | S2: CRM quyết; feed từ CIS chỉ được gỡ · H5: lưu quyền theo từng app trong bảng membership của CIS (AA-813) | **S2, cộng phần tốc độ của H5** | Spec F1 ghi "No access outside the agency, AA included" (`partner-crm-spec.md:113`): nếu nhân viên AA sửa được CIS membership để tự cấp quyền CRM thì câu này sai. Nên CIS membership (AA-813) chỉ quyết "người này thuộc đại lý nào" và quyền content studio; còn `crm.member_role` chỉ do API CRM ghi, theo thao tác của **owner đại lý**. Khi gỡ người: CIS gọi CRM để vô hiệu cache ngay, cache ≤ 60 giây (lấy từ H5). Một màn hình "Đội" duy nhất trong AA-Partner |
| Guardrails khi acc2 bị reseller chặn | v2: chạy sang acc3 · S6: dừng (fail closed) | **Mặc định dừng**; chỉ dùng acc3 sau khi có role CRM riêng trên acc3 **và** acc3 đã nằm trong danh sách sub-processor | Gửi text chưa lọc sang tài khoản khác, qua reseller khác, là chuyện danh sách sub-processor, tức chuyện của chị Thư. AI vốn tắt mặc định (D12) và chỉ tới ở đợt D7, nên không chặn gì |

### 2.2 Review bảo mật (S1–S19)

| ID | Kết luận | Lý do / làm ở đâu |
|---|---|---|
| S1 KMS chưa chặn được admin, câu IAM sai | **Nhận** | K11. Key policy mẫu có 3 câu: dùng / quản trị / `Deny` mọi principal khác; IAM theo `kms:ResourceAliases = alias/crm-<env>/*` + `RequestTag`; không bao giờ cấp `PutKeyPolicy`/`ScheduleKeyDeletion` cho task role; kiểm lệch policy mỗi đêm; EventBridge → SNS + `access_event` hiện trong audit đại lý. Issue CRM-07, CRM-11. Câu H3 → chị Thư |
| S2 CIS membership quyết quyền CRM | **Nhận** | §2.1. Thêm cảnh báo cho các lệnh `Admin*` trên pool EXTERNAL. Phạm vi AA-813 cần sửa (ghi trong CRM-01) |
| S3 Prod cell tin Dev (cùng pool, client, host preview) | **Hoãn** (Go-real) | Không có prod lúc này. Khi có: client prod riêng (hoặc pool partner riêng), không localhost, không preview; sửa ADR 0006. Ghi trong ADR ở CRM-01 |
| S4 `AWS_IAM` bị vượt từ trong VPC | **Nhận, sửa** | Sửa theo H1 (§2.1). Làm ở D4, khi CRM bắt đầu gọi CIS/Booking |
| S5 N3 b chưa có đường origin | **Nhận** | = F1 → O2, kèm header bí mật của origin + `CloudFront-Viewer-Address`. Spike CRM-04 |
| S6 Guardrails che bằng `{NAME}` không đánh số, `match` lộ PII, chỉ hộ chiếu Mỹ; acc3 trái D12 | **Nhận** | K9, K12. Chạy chế độ detect (`NONE`) rồi tự đánh số placeholder; thêm regex hộ chiếu chung, CCCD 12 số, ngày sinh; không bao giờ log `match`; Stage 3 không vào prompt; role acc3 riêng cho CRM, chỉ profile `us.` + `ApplyGuardrail`. CRM-18 kiểm sẵn sàng; làm thật ở D1/D7 |
| S7 Feed giám sát: xác thực, payload, lỗi chứa PII | **Nhận** | §3.2–3.3. Lưu `error_class` + thông điệp đã lọc, có unit test; metric EMF |
| S8 Audit log: khối lượng, tranh chấp chuỗi hash, không có mỏ neo chống sửa | **Nhận** | Mỗi request một event; partition theo tháng; job niêm phong mỗi phút (Merkle); S3 Object Lock; runtime chỉ `INSERT, SELECT`. Lát cắt: bảng tối giản; bản đầy đủ ở D1. Thời hạn giữ → chị Thư |
| S9 DEK mỗi khách = mỗi lần xem một lời gọi KMS; xoá mật mã vẫn bị backup giữ | **Nhận** | Cache DEK ~5 phút; encryption context có `traveller_id`; câu "không đọc lại được sau N ngày" → chị Thư |
| S10 Hộp thư nằm ngoài F1; XSS từ HTML email; mỗi đại lý một rule | **Nhận** | = F7/M1: một rule cho cả domain + khoá ingest + mã hoá lại + xem thư trong iframe sandbox ở origin riêng, không cookie. D3 |
| S11 RLS đụng các đường đọc chéo tenant | **Nhận** | `crm.job` không RLS, payload chỉ chứa id; helper `tenant_tx()` + lint; probe "không set tenant = 0 dòng". CRM-09 |
| S12 Đại lý đăng nhập một lớp, MFA tắt, refresh 7 ngày | **Hoãn** (Go-real) | Dev dùng đại lý giả. Passkey/TOTP cho owner/agent, refresh ≤ 24 giờ ở prod. Cảm nhận khi đăng nhập → câu hỏi cho chị Thư |
| S13 Token link khách lộ qua URL; một origin cho mọi đại lý | **Nhận** | Đổi token sang cookie ở lần mở đầu; `Referrer-Policy: no-referrer`; giới hạn OTP; không HTML tuỳ ý. D3/D5 |
| S14 Đường công khai "chỉ Encrypt" mâu thuẫn với Twilio của đại lý | **Nhận** | Nhóm khoá riêng cho thông tin tích hợp; ghi trong ADR (CRM-01) |
| S15 Trang ops ở Booking admin đưa PII đi qua Vercel | **Nhận** | Trang ops-release đặt trong AA-Partner, host staff, nhóm WORKFORCE `crm-ops` (T12). D5 |
| S16 Tách JWT secret | **Nhận** | AA-Partner không bao giờ nhận `JWT_SECRET` HS256, chỉ nhận RS256 của Cognito. Ghi trong ADR |
| S17 Đếm thiếu secret | **Nhận** | Mỗi env 4 secret: DSN, BFF JSON, Cognito client, nhà cung cấp JSON. Đăng ký trước ở `secrets-register` (trạng thái planned). CRM-05 |
| S18 Log thành đường rò khi tắt exec | **Nhận** | Bộ lọc log + data protection policy (cent/tháng). CRM-09 |
| S19 Map tenant ở webhook; uy tín SES | **Nhận** | Map theo id tài khoản của nhà cung cấp; mail khách qua configuration set `transactional` có trần. D3/D5 |

### 2.3 Review kiến trúc (F1–F17)

| ID | Kết luận | Lý do |
|---|---|---|
| F1 Đường origin | **Nhận (O2)** | K1–K5; §2.1 |
| F2 Đưa prod cell, vendor, xác minh ra khỏi đường găng | **Nhận** | Đúng H1 = b, H4 = c. Đợt Go-real (§3.5) |
| F3 Role apply thiếu quyền CloudFront/ECR | **Nhận** | K6. CRM-03 (anh apply local bằng MFA, như AA-811) |
| F4 Ngân sách kết nối tính sai thước đo | **Nhận** | K14. `crm_app` limit 6, pool 3 → tổng ~132 ≤ 135. Sửa câu N17 |
| F5 BFF đi API Gateway qua NAT | **Nhận** | BFF gọi NLB nội bộ; `api-crm` công khai chỉ cho webhook |
| F6 Preview cố định | **Nhận** | Preview chạy tạm trong CI ở `localhost:3004` (K18). Bỏ `portal-pr.` |
| F7 SES 200 rule | **Nhận** | K13 |
| F8 Hợp đồng giám sát | **Nhận, sửa** | Nhận hợp đồng `ops-feed.v1`; xác thực đổi sang token WORKFORCE (§2.1) |
| F9 Khoá tạo lúc chạy, nằm ngoài Terraform | **Nhận** | Gộp vào S1 + dọn khoá đại lý giả sau 7 ngày không dùng |
| F10 Next 16 trên Fargate | **Nhận** | Web 0,25 vCPU / 1 GB ARM; session lưu phía server (cookie chỉ chứa id); `redirect_uri` lấy từ cấu hình |
| F11 Image ARM cần repo public | **Nhận** | Giữ AA-Partner public; runner `ubuntu-24.04-arm`; ID tài khoản để trong biến repo, không vào code (DM-6.10) |
| F12 CI/CD và đăng ký owner DB bị đếm thiếu | **Nhận** | CRM-06 tách riêng; hai workflow deploy |
| F13 Spot không có dự phòng | **Nhận** | Một dòng runbook (CRM-05) |
| F14 ECS exec | **Nhận** | Dev bật, prod tắt (T10) |
| F15 Comment cũ về `SetWebACL` | **Nhận** | K7; sửa khi tiện trong PR Infra |
| F16 Lát cắt không chờ chuyển portal | **Nhận** | Host mới `partner-dev.` / `go-dev.` |
| F17 Documenso trên Dev | **Nhận** | Chỉ là container trong CI + stub trên Dev; không bao giờ đặt trên RDS dùng chung |

### 2.4 Review tích hợp + truy vết spec

| ID | Kết luận | Lý do |
|---|---|---|
| C1 Hàng AA cần những thứ Booking chưa có | **Nhận** | K16. Hợp đồng `booking.b2b.v1`; lane Booking 12–16 issue; giá giả trên Dev; ma trận giá + thanh toán AA↔đại lý → chị Thư |
| C2 Đường origin | **Nhận chẩn đoán; không nhận phương án b** | §2.1 |
| H1 `AWS_IAM` bị vượt | **Nhận** | JWT dịch vụ ký KMS (T8) |
| H2 acc3 | **Nhận** | = S6; nếu Haiku 5.5 không có profile `us.` thì Haiku 4.5 đắt gấp 10 lần (K10) → anh quyết lại N10 |
| H3 Builder cần logic backend của TP | **Nhận** | Gắn vào issue điều tra ghép tuyến mà anh vừa duyệt; quyết `tp.routes.v1` hay API graph trong CIS sau khi điều tra (T13) |
| H4 `catalog.v1` không tồn tại | **Nhận** | Thêm `catalog.http.v1` + `tenant.membership.v1` (snapshot + ETag); 3 issue CIS ở D2/D4 |
| H5 Hai mô hình vai trò | **Nhận, sửa** | §2.1; nhóm `crm-ops`, `crm-insights` (nhận) |
| H6 Thứ tự cắt chuyển portal | **Nhận** | Các bước S0–S6 của review thành đợt D2. Giữ 301 từ `aa-cis…/trip/*`: đó là URL của khách, không phải link admin↔portal, nhưng anh xác nhận (T-ghi chú ở §3.6) |
| H7 Ba hợp đồng | **Nhận** | `ops-feed.v1` (gộp job + LLM) + `tenant.entitlements.v1` (khung gói đồng bộ với portal; nội dung gói → chị Thư) |
| M1 Email | **Nhận** | Dev dùng ứng dụng Google ở chế độ "Testing": refresh token hết hạn sau 7 ngày |
| M2 Xoá có kiểm vs backup + bên thứ ba | **Nhận** | Biên nhận xoá ghi rõ ngày backup hết hạn |
| M3 Danh sách khách gửi NCC | **Nhận** | Thêm export có audit; phạm vi dữ liệu → chị Thư |
| M4 Stripe | **Nhận** | Thêm webhook thất bại/hoàn tiền/`account.updated`; Stripe không có ở VN |
| M5 WhatsApp | **Nhận** | Ghi điểm lệch spec: spec ghi "Twilio / 360dialog" (`partner-crm-spec.md:128,180`) |
| M6 Domain khách nhìn thấy | **Nhận** | → chị Thư; Dev dùng `go-dev.lumiguides.it.com` |
| M7 Phụ thuộc AI | **Nhận** | = S6/H2 |
| L1 `alert_email` đã xong | **Nhận** | K19; bỏ khỏi kế hoạch |
| L2 Báo cho agent khi có Inquiry | **Nhận** | CRM-12 |
| L3 BFF qua NAT | **Nhận** | = F5 |
| L4 OTP | **Nhận** | Lấy luật khoá/giới hạn của Booking làm spec |
| L5 Sự kiện builder | **Nhận** | Giữ tên `itinerary.*` trong `crm.metric_event` |

**Không nhận:** C2-b (mở :443), F8 phần SigV4, S4 phần header bí mật (thay bằng H1), H5 phần "quyền CRM lưu trong CIS".
**Hoãn sang Go-real:** S3, S12, N15 (service công khai thứ hai), prod cell, WAF CloudFront.

---

## 3. (b) Thay đổi theo quyết định vòng 2

### 3.1 N3 = b: container Fargate sau CloudFront

```
Người dùng ─► CloudFront (pay-as-you-go, 1 distribution, alias partner-dev. + go-dev.)
              │  hành vi /_next/static/* : CachingOptimized
              │  origin request policy: AllViewerAndCloudFrontHeaders-2022-06 (+ header bí mật X-AA-Origin)
              ▼
          VPC origin = NLB nội bộ có sẵn (:80, SG + rule từ CloudFront-VPCOrigins-Service-SG)
              ▼
          ALB dùng chung, rule mới: host ∈ {partner-dev., go-dev.} VÀ X-AA-Origin khớp → TG web
              ▼
          aa-crm-dev-web (Fargate ARM 0,25 vCPU / 1 GB, Spot) ── BFF ──► NLB nội bộ /crm/v1/* → aa-crm-dev-api
                                                                 └──► NLB nội bộ /v1/*     → CIS (về sau)
```

- **Ai chạm tài nguyên dùng chung:** một rule ingress trên SG của NLB, cộng các rule listener ALB.
- **Thứ tự rule (sửa ở kiểm tra cuối):** rule web **không được** lấy số sau 100. Default action của :80 là CIS
  (`modules/alb/main.tf:78-85`), rule Booking priority 100 chỉ xét path (`booking.tf:356-372`). Nếu rule web nằm sau
  100 thì `partner-dev.…/booking/*` đi vào Booking API, còn request tới tên `*.cloudfront.net` của distribution (Host
  không khớp) rơi vào CIS API: CIS và Booking bị lộ qua CloudFront, đi vòng qua API Gateway. Chốt: rule web
  (host + `X-AA-Origin`) ở priority < 100, ngay sau đó rule "có `X-AA-Origin` bất kỳ → 403", rồi mới tới rule
  api `/crm*`. Như vậy mọi traffic từ CloudFront chỉ có hai đích: web hoặc 403. Đã ghi vào CRM-04, CRM-05.
- **WAF:** traffic đi qua NLB vẫn qua rule 1 của ACL ALB (CommonRuleSet), rồi được rule 2 `VpcLinkInternalAllow` cho
  qua phần rate/geo. Vì vậy khách ở Đức, Pháp… mở được trang. Rate limit trong app dùng `CloudFront-Viewer-Address`,
  không dùng `X-Forwarded-For` do client gửi.
- **Kiểm ở spike CRM-04:** SSR streaming; host đến được `proxy.ts`; timeout 30 giây; cookie nhỏ hơn giới hạn
  CommonRuleSet (session lưu phía server); mở từ một nước ngoài danh sách 10 nước (qua VPN).
- **Dự phòng nếu spike hỏng:** O1, tức gói Free → HTTP API → VPC link v2 (giới hạn header 10.240 byte, không stream).
  Không mở :443, không mua Business.
- **Previews:** chạy tạm trong CI (`docker compose`, web ở :3004, đăng nhập Cognito Dev bằng user `e2e-test-*`). Dev
  chỉ deploy `main`.

### 3.2 D12 đổi: CRM có gateway LLM riêng, CIS vẫn xem được

| Phần | Thiết kế |
|---|---|
| Gateway | `api/app/llm/gateway.py` trong AA-Partner. Thứ tự: `scrub()` → kiểm `crm.spend_budget` theo tenant (vượt là dừng) → gọi Bedrock qua role **`AA3-Bedrock-Invoker-CRM`** (role mới trên acc3, ExternalId riêng, chỉ profile `us.` + `ApplyGuardrail`) → ghi `crm.llm_call` → bắn metric EMF. Không import code gateway của CIS, không ghi `shared.llm_call_log` |
| `crm.llm_call` | `id, tenant_id, stage, role, model, input_tokens, output_tokens, cache_read_tokens, cost_usd_est, latency_ms, outcome, error_class, created_at`. **Không lưu text, không lưu traveller_token** |
| CIS xem | `GET /crm/ops/v1/llm-usage?from&to` trả về: theo ngày × model × stage, số lượt, token, chi phí ước tính, cùng một hash tenant ẩn danh. CIS api gọi qua NLB nội bộ, mang theo token WORKFORCE của nhân viên; CRM chỉ nhận `client_id = cis-admin` + nhóm `cis-admin`. Trang chi phí LLM của CIS hiện thêm một dòng "CRM" cạnh `shared.llm_call_log`, và app registry thêm `AppInfo("crm")` (K17) |
| Ngân sách và cảnh báo khi không có người mở trang | Metric EMF `AA/CRM LlmCostUsd`, `LlmErrors` → alarm và budget `crm` sẵn có. CIS không cần đọc chéo DB |
| Tách hoá đơn acc3 | Tạo application inference profile gắn tag `App=crm` (kiểm được hay không ở CRM-18; nếu không thì dùng số ước tính trong `crm.llm_call`) |
| Lát cắt | Gateway chạy với provider **stub** (không gọi model, $0), để đường giám sát chạy thông từ đầu (CRM-17). Gọi model thật ở D7 |

### 3.3 D22 đổi: CRM có `crm.job` riêng, CIS vẫn xem được

- **Runner:** chép từ Booking (`backend/app/jobs/`, 675 dòng, chạy trong process), kind `crm_*`, bảng `crm.job` theo
  template ADR 0003a. Không chạm `shared/jobs` của CIS.
- **Khác Booking ở hai điểm:**
  - lỗi lưu `error_class` cộng thông điệp đã lọc PII, có unit test (K15, S7);
  - payload chỉ chứa id, có CI kiểm không có khoá `pii:`.
- **Bộ test tuân thủ chung** (claim / lease / release / cancel) chép vào cả ba repo.
- **CIS xem:** `GET /crm/ops/v1/job-runner/summary` cùng dạng với `/admin/job-runner/summary` của CIS (K17): số job
  theo kind × trạng thái, tuổi job chờ lâu nhất, heartbeat của worker, SHA đang chạy, trạng thái deploy gate. Không có
  payload, không có tên tenant. Trang Jobs của CIS admin thêm tab "CRM" chỉ đọc. Xác thực như §3.2.
- **DB Migrate:** idle check tự thấy mọi `<schema>.job` (`.github/workflows/db-migrate.yml:21`), nên các kind định kỳ
  của CRM (heartbeat, mail ingest, workflow tick, dọn khoá) phải nằm trong `IDLE_EXEMPT_KINDS` ngay từ ngày đầu
  (CRM-06), nếu không thì mọi migration của CIS/Booking/TP sẽ bị chặn.

### 3.4 Đại lý giả (synthetic) trên Dev

- **Luật:** C7.1a ("Dev seed data MUST be synthetic or masked", `03-scaling.md:364`). Mỗi tenant CRM có cờ
  `is_synthetic = true`. Ở Dev, API từ chối tạo tenant không có cờ này. Đây là guard, có test.
- **Seeder (CRM-15):** 2–3 đại lý giả (ví dụ "Kangaroo Treks Test"), user `e2e-test-crm-*` trong pool EXTERNAL Dev,
  khách giả tạo bằng Faker (EN/VI, có tên tiếng Việt để thử scrubber), email về hộp `e2e-mail.` sẵn có. Chạy DRY RUN
  trước. Tên secret theo mẫu `e2e-test-*` (memory e2e-admin-login), chỉ ghi tên, không ghi giá trị.
- **Khoá KMS của đại lý giả:** tạo lười; job dọn lên lịch xoá sau 7 ngày không dùng. Khoá chờ xoá không bị tính tiền
  (KMS pricing).
- **Vendor trên Dev:** Stripe test mode, số test của Meta, Twilio trial, Google ở chế độ "Testing", Documenso trong CI
  + stub. Không cần gói trả phí hay hợp đồng nào.

### 3.5 Không có prod cell trên đường găng: đợt Go-real

**Mở khi:** chị Thư chọn đại lý thật đầu tiên **và** đủ 23 module trên Dev (H1 = b).

**Nội dung:**
- **Nơi đặt prod:** prod cell của CRM (v2 §10.1), hoặc dùng prod chung nếu AA-880 có trước. Quyết lúc đó, theo ngày
  đã có.
- **Danh tính:** client/pool riêng cho partner ở prod, passkey (S3, S12).
- **Biên:** WAF CloudFront không chặn nước (≈ $7–8); tắt ECS exec ở prod.
- **Quyền:** service công khai thứ hai chỉ có quyền Encrypt (N15).
- **Bên ngoài:** gói và vendor ký điện tử; xác minh Meta, Google, Microsoft; DPA; trang dữ liệu công khai; các ngưỡng
  gửi luật sư (D15).

**Ước tính:** ≈ 12–15 issue (2–3 phiên) **cộng đồng hồ của bên ngoài**: Meta 2–4 tuần (spec §10), Google, Microsoft.
Câu "nên bấm đồng hồ sớm hay chờ" là việc của chị Thư.

### 3.6 Quyết định kỹ thuật cho anh (T1–T14) và các câu N/D thay đổi

| # | Quyết định | Khuyến nghị | Ảnh hưởng |
|---|---|---|---|
| T1 | Đường origin cho N3 b | **O2** (PAYG + VPC origin trên NLB nội bộ); dự phòng O1 | ≈ $0 Dev; thay câu chữ N3 |
| T2 | WAF | **Tắt trên Dev**; CloudFront ACL không chặn nước ở Go-real | Thay N14 a (≈ $7–8/tháng lúc đó) |
| T3 | N4 (prod cell), N8 (gói Documenso), N15 | **Hoãn sang Go-real**, chưa quyết bây giờ | −$27/tháng, −$3.000 hoặc −$480/năm cho tới lúc đó |
| T4 | Ngân sách kết nối (N17) | **`crm_app` limit 6, pool 3**, thêm dòng C2.2 trong cùng PR | $0 |
| T5 | Preview | **Chạy tạm trong CI**, không dùng host `portal-pr.` | −1–2 issue |
| T6 | SES nhận thư | **Một rule cho cả domain** + khoá ingest; chuyển rule set sang `App=shared` | Bỏ trần 200 |
| T7 | Giám sát chéo app | **`ops-feed.v1`** + token WORKFORCE + EMF | Đáp D12/D22 mới |
| T8 | Xác thực service-to-service | **JWT dịch vụ ký bằng KMS**; bên nhận tự kiểm | +$1/tháng; 2 issue ở D4 |
| T9 | Ai nắm quyền CRM | **CRM**; CIS chỉ được gỡ; sửa phạm vi AA-813 | Giữ được câu F1 |
| T10 | ECS exec | **Dev bật, prod tắt** | Debug nhanh trên Dev |
| T11 | Scrubber + model | Guardrails chế độ detect + placeholder tự đánh số; lỗi thì dừng; role acc3 riêng `us.`. **Nếu Haiku 5.5 không có `us.` ở acc3:** chọn lại giữa Haiku 4.5 (đắt gấp 10 lần, ≈ +$3,8/đại lý/tháng) và `global.` (trái D12) | Kiểm ở CRM-18 |
| T12 | Trang AA ops (module 8) | Đặt **trong AA-Partner**, host staff, nhóm `crm-ops`; không đặt ở Booking admin trên Vercel | Thay chi tiết N6 |
| T13 | Builder | Quyết `tp.routes.v1` (TripPlanner cung cấp) hay API graph trong CIS **sau** issue điều tra ghép tuyến | Chặn module 3 |
| T14 | Cognito cho partner | Dev: client `cis-portal` + host mới. Prod: client/pool riêng + passkey ở Go-real, sửa ADR 0006 lúc đó | $0 |

**Câu N/D cũ đổi nghĩa:**

| Câu | Đổi thành |
|---|---|
| N3 | b, theo cách T1 |
| N4, N8, N15 | Hoãn (T3) |
| N5 | Giữ: chỉ đọc qua HTTP, không grant |
| N6 | Giữ: dữ liệu ở trong CRM; trang đổi chỗ (T12) |
| N14 | T2 |
| N17 | T4 |
| D16 | Tên project "Tenant CRM", tạo issue theo đợt |
| D23 | ADR ghi ranh giới portal ↔ CRM trong repo và điều kiện dời DB/đổi runtime |

**Ghi chú cần anh xác nhận:** redirect 301 từ `aa-cis…/trip/*` sang host khách (H6 S6) là URL của khách, không phải
link giữa admin và portal.

---

## 4. (c) Chạy trên Dev sớm nhất

### 4.1 Lát cắt nhỏ nhất chạy từ đầu tới cuối

**Mục tiêu (Done):** trên Dev, sau CloudFront:
1. user đại lý giả đăng nhập `partner-dev.` bằng Cognito;
2. khách giả điền form trên `go-dev.`;
3. job `crm_intake_process` tạo khách (F1: tên, email, điện thoại đã mã hoá bằng khoá KMS của đại lý đó), profile
   (F2 tối giản) và trip ở bước **Inquiry**, rồi báo cho agent bằng email;
4. trip hiện trên bảng của đại lý trong vòng 1 phút;
5. mỗi lần xem tên khách sinh một `access_event`;
6. dump DB chỉ thấy ciphertext;
7. CIS admin có tab "CRM" thấy số job.

**Module của spec được chạm (một phần):** F1, F2, F4, F5 tối giản, module 1, module 2 (bảng Inquiry). Đây là cái
khung để các đợt sau đổ module vào. Lát cắt **chưa đếm** là xong module nào.

**Hạ tầng:**
- mới: 1 distribution CloudFront + VPC origin; 2 service Fargate ARM Spot (api 0,25/0,5; web 0,25/1); 2 repo ECR;
  4 secret; khoá KMS lười;
- chạm vào đồ dùng chung: 1 rule SG trên NLB, 2 rule ALB, schema `crm` và role trên RDS Dev, 2 bản ghi Route 53 +
  ACM us-east-1, budget `crm`.

**Repo:** root (ADR, hợp đồng, dòng C2.2), AA-CIS-Infra, **AA-Partner (mới, public)**, AA-CIS-App (một tab chỉ đọc).
**Không chạm:** chuyển portal, AA-813, Booking, TripPlanner, vendor nào.

**Thứ tự issue** (chi tiết ở `r3/crm-w0-w1-issues.json`):

| Bước | Issue | Repo | Song song được với |
|---|---|---|---|
| W0 | CRM-01 ADR app Partner (ranh giới, runtime, Dev trước, Go-real, KMS, quyền, hợp đồng) | root | — |
| W0 | CRM-02 Hợp đồng `ops-feed.v1` | root | CRM-03 |
| W0 | CRM-03 Bootstrap role apply (anh apply bằng MFA) | Infra | CRM-01 |
| W0 | CRM-04 Spike O2 với container hello | Infra | sau CRM-03 |
| W0 | CRM-18 Kiểm sẵn sàng Bedrock (chỉ đọc) + thiết kế role acc3 CRM | Infra (acc3) | bất kỳ |
| W1 | CRM-05 `crm.tf` (ECR, task, service desired 0, SG, rule, secret, OIDC, CloudFront, DNS, budget) | Infra | CRM-06, CRM-08 |
| W1 | CRM-06 Đăng ký owner DB `crm` + role + C2.2 + kind miễn idle + probe | Infra + root | CRM-05 |
| W1 | CRM-07 Rào chắn KMS (IAM theo điều kiện, key policy mẫu, alarm, kiểm lệch) | Infra | sau CRM-05 |
| W1 | CRM-08 Khởi tạo repo AA-Partner + CI ARM + test ranh giới import + workflow deploy | AA-Partner | CRM-05 (phần CI); Done cần CRM-05 (ECR + OIDC) |
| W1 | CRM-09 Khung API + xác thực + `tenant_tx` + `crm-001` | AA-Partner | — |
| W1 | CRM-10 Runner + deploy gate + summary `ops-feed` | AA-Partner | CRM-11 |
| W1 | CRM-11 KeyProvider + mã hoá trường + migration vault (số `crm-NNN` lấy theo thứ tự merge) | AA-Partner | CRM-10 |
| W1 | CRM-13 Khung web (Next 16, host routing, session Cognito, BFF allow-list, EN/VI) | AA-Partner | CRM-10/11 |
| W1 | CRM-15 Seeder đại lý giả | AA-Partner | CRM-10, CRM-13 |
| W1 | CRM-12 Intake → Inquiry + báo agent (cần CRM-15: đại lý giả để nhận mail) | AA-Partner | CRM-13 |
| W1 | CRM-14 Trang form + bảng + E2E Playwright trên Dev | AA-Partner | — |
| W1 | CRM-16 CIS: app registry + tab "CRM" | CIS | sau CRM-10 |
| W1 | CRM-17 Khung gateway LLM (stub) + `llm-usage` + dòng chi phí ở CIS | AA-Partner + CIS | sau CRM-16 |

**Ước tính:**
- 18 issue, phần lớn cỡ S;
- ở nhịp ~6 issue/phiên (D4 a) là **3 phiên**, cộng thời gian chờ anh apply bằng MFA và chờ spike → thực tế
  **3–4 phiên**;
- nếu lane CRM bắt đầu từ S246 với ~2,8 phiên/tuần, "CRM chạy trên Dev" vào khoảng **1–1,5 tuần sau khi bắt đầu**
  (ước tính).

**Điểm nghẽn:**
- CRM-03 cần anh có mặt để nhập MFA;
- thêm ba việc tay của anh (đã ghi vào issue): nhập giá trị secret DSN + client Cognito rồi chạy DB Migrate
  `set-password` cho `crm_app` (CRM-06/09); tạo user Cognito + secret `e2e-test-crm-*` bằng profile MFA (CRM-15);
- hộp thư E2E hiện chỉ nhận đúng một địa chỉ và chỉ AA-CIS-App đọc được (`e2e_mailbox.tf:9,27,213,248`): phải mở
  thêm địa chỉ cho đại lý giả và cho AA-Partner đọc (đã thêm vào CRM-05), nếu không mail báo agent bị bounce;
- CRM-04 có thể buộc chuyển sang O1;
- có thể phải xin tăng quota "managed policies per role" (miễn phí, có thể mất 1–2 ngày).

### 4.2 Sau lát cắt: thứ tự để đủ 23 module trên Dev (đại lý giả, không có prod)

| Đợt | Nội dung (module spec) | Repo | Issue (ước tính) | Phiên |
|---|---|---|---|---|
| D1 Nền riêng tư | F1 đầy đủ (blind index, `reveal()`, bucket tài liệu, BYOK), F2 + role NOLOGIN, F3 scrubber (detect mode, regex VN, corpus 0 rò), F4 RLS + UI quyền (CRM nắm vai trò), F5 audit đầy đủ (partition, niêm phong, Object Lock, trang audit) | Partner, Infra | 13 | 2,2 |
| D2 Tách CIS ↔ portal (lane song song) | Các bước S0–S6 của H6: sửa B3, CTA D18, `/v1/brand-identity`, hợp đồng `cis.tenant-api.v1`; chuyển `portal/` sang AA-Partner giữ lịch sử; lật `portal.` sang CloudFront; xoá phía CIS + đảo test guard; AA-813 đã sửa phạm vi (cửa sổ hai kiểu đăng nhập); allow-list BFF; trang trip sang host khách + 301; `tenant.membership.v1` | CIS, Partner, Infra, root | 18 | 3,0 |
| D3 Bán một chuyến + email | Module 1 đầy đủ (widget nhúng), 2 (timeline, panel Traveler info, cổng Stage 2), 15, 4, 6 (dòng của đại lý), 16 cơ bản, `crm.metric_event`, module 5 (một rule domain, ingest + mã hoá lại, `gmail.send` ở chế độ Testing / Graph, xem thư trong sandbox, trả lời mẫu, ghi chú), import CSV/mbox, tiền tệ/múi giờ/mobile | Partner, Infra | 18 | 3,0 |
| D4 Hàng AA + proposal | Booking: `booking.b2b.v1` (xác thực dịch vụ, danh mục thành phần, quote, `on_request`, hold + reaper, trip case B2B, feed sự kiện, UI ops) với giá giả; CIS `catalog.http.v1`; JWT dịch vụ (T8) + thắt SG; builder sau khi có kết quả điều tra (T13); module 3, 6 (dòng AA) | Booking, CIS, TP/CIS, Partner, Infra | 28 (Booking 12–16) | 4,7 |
| D5 Thu tiền + giao | Module 7 (Stripe test, webhook thất bại/hoàn tiền; VN ghi tay), 11 (client portal, OTP, Stage 3), 12 (adapter ký điện tử trung lập: Documenso trong CI + stub), 13, 8 (khoá AA-ops, trang `crm-ops` trong AA-Partner, export NCC, xoá sau 90 ngày), 18 phần xuất/xoá khách | Partner, Infra | 11 | 1,8 |
| D6 Tự động hoá | Module 9 (số test Meta, Twilio trial của đại lý), 10, Messenger/IG | Partner | 7 | 1,2 |
| D7 AI + insights + gia cố | Module 14 (role acc3 CRM, gọi model thật, duyệt nháp, eval), 16 đầy đủ, 17 (k ≥ 10, ≥ 3 đại lý, opt-in, trang CIS), 18 đầy đủ (crypto-shred), load test, SLO | Partner, Infra (acc3), CIS | 12 | 2,0 |
| **Cộng sau lát cắt** | | | **≈ 107** | **≈ 18** |
| Go-real (chờ chị Thư) | §3.5 | Infra, Partner, root | 12–15 | 2–3 |

**Thứ tự và song song:**
- D1 đi trước mọi dữ liệu có nghĩa (spec `partner-crm-spec.md:21,199`).
- D2 chạy lane song song ngay sau lát cắt.
- Lane Booking của D4 nên khởi động sớm, song song với D1–D3, vì là cột dài nhất.

**Tổng kế hoạch** (lát cắt + D1–D7) ≈ **125 issue, ≈ 21–22 phiên**. Ở ~2,8 phiên CRM/tuần là ≈ 8 tuần, nên đủ 23
module trên Dev vào khoảng **giữa tháng 12/2026 nếu không gián đoạn, ghi "giữa 12/2026 – giữa 1/2027"** (ước tính,
chưa tính lane song song). "Đủ module trên Dev" ở đây là chạy được với dữ liệu giả và vendor ở chế độ test, xem
"Kiểm tra cuối" mục 3. So với v2: thêm Booking (+6–9), các hợp đồng
(+5), bảo mật (+7); bớt prod cell, preview, Lambda (−8).

---

## 5. (d) Chi phí Dev tăng thêm mỗi tháng (N3 b, đại lý giả, không prod)

Giá đơn vị đọc ngày 20/10/2026 (K5, K23, KMS $1/khoá-tháng, Secrets $0,40, SES như v2). Mức giảm của Spot (60–70 %)
là **ước tính**. Không giả định free tier khi acc2 tính tiền qua TrueIDC; CloudFront ghi ≤ $0,2.

| Khoản | T11/2026 (lát cắt + D1) | T12 (D2–D4) | T1/2027 → (D5–D7) | Cơ sở |
|---|---|---|---|---|
| API CRM ARM 0,25/0,5, Spot | 2,5–3,3 | 2,5–3,3 | 2,5–3,3 | on-demand $8,29 |
| Web ARM 0,25/1 GB, Spot | 2,9–3,9 | 2,9–3,9 | 2,9–3,9 | on-demand $9,78 |
| CloudFront PAYG + VPC origin | ≤ 0,2 | ≤ 0,2 | ≤ 0,2 | K5 |
| CloudWatch Logs (2 service) + ~5 alarm | 1–2 | 1–2 | 1–2 | ước tính |
| ECR (2 repo, ≤ 10 image mỗi repo) | ≤ 0,6 | ≤ 0,6 | ≤ 0,6 | $0,10/GB |
| Secrets (4) | 1,6 | 1,6 | 1,6 | S17 |
| KMS: khoá đại lý giả (≤ 3, có dọn) / + khoá ingest + khoá ký dịch vụ / + khoá AA-ops | 2–3 | 4–5 | 5–6 | $1/khoá |
| Guardrails corpus | 0 | 0,7 | 0,7 | v2 §9.2 |
| SES, S3, REST `api-crm` (chỉ webhook) | ≤ 0,3 | ≤ 0,5 | ≤ 0,5 | ước tính |
| Haiku test (trần do mình đặt) | 0 | 0 | ≤ 2 | trần |
| Data protection cho log | 0 | 0 | ~0,1 | $0,12/GB quét |
| RDS, NAT, ALB, NLB, cluster, Cognito | 0 | 0 | 0 | đã trả; C2.2 vừa (T4) |
| Documenso CI, Stripe test, Meta test, Twilio trial, Google Testing | 0 | 0 | 0 | §3.4 |
| **Tổng** | **≈ $10–15** | **≈ $13–18** | **≈ $14–21** | |
| Xấu nhất (hết Spot, cả hai service on-demand) | ≈ $23–26 | ≈ $25–29 | ≈ $26–32 | +$12,7 |
| Tuỳ chọn: WAF CloudFront ngay trên Dev | +7–8 | +7–8 | +7–8 | $5 ACL + $1/rule + $0,60/M |

**So sánh:**
- v2 + N3 b đã duyệt: ≈ $19–21 trên Dev, **cộng** prod cell $27/tháng từ 30/11 và Documenso Platform $3.000/năm.
- Ở trạng thái ổn định ($14–21 so với $19–21) bản này rẻ hơn tối đa ≈ $5/tháng (web chạy Spot, bù lại thêm secret và
  khoá KMS), và không có hai khoản lớn kia cho tới Go-real. (Sửa ở kiểm tra cuối: bản trước ghi "≈ $4–6".)
- Chưa tính: 2–3 secret `e2e-test-crm-*` cho user đại lý giả (CRM-15, +$0,8–1,2) và khoá KMS canary (CRM-07, +$1),
  tổng ≈ +$2/tháng, vẫn nằm trong khoảng "xấu nhất".

**Ghi chú cho lúc Go-real** (không tính vào Dev). 10 đại lý ≈ $79–86/tháng **trước** tiền ký điện tử. Con số này lấy
v2 bỏ Documenso, đổi portal Lambda sang web on-demand (+$9,8) và cộng WAF (+$7,5). Tiền ký điện tử cộng thêm:
- **+$40** nếu Documenso Teams;
- **+$250** nếu Documenso Platform;
- **≈ $0–17** nếu tự host hoặc tự làm (§7.2).

Nếu phải dùng Haiku 4.5 thay Haiku 5.5: **+≈ $38/tháng** ở 10 đại lý (K10, giả định 100 % bật AI).

---

## 6. (e) Rủi ro kỹ thuật còn mở

| Rủi ro | Mức | Giảm thiểu / cách biết sớm |
|---|---|---|
| Spike O2 hỏng (NLB target là ALB làm VPC origin, header Host, streaming) | TB | CRM-04 kiểm trước khi viết `crm.tf`; dự phòng O1; không mở :443 |
| Quota "managed policies per role" đã đủ 10; cần anh MFA | TB | CRM-03 làm đầu tiên; xin tăng quota (miễn phí) song song |
| Lane Booking B2B (12–16 issue) + ma trận giá chưa được quyết | **Cao** | Bắt đầu sớm với giá giả trên Dev; chế độ `on_request`; quyết định giá → chị Thư |
| Builder phụ thuộc logic ghép tuyến của TP | Cao | Issue điều tra ghép tuyến anh vừa duyệt phải trả lời "CRM dùng lại thế nào" (T13) |
| Haiku 5.5 không có `us.` trên acc3 / Guardrails bị chặn trên acc2 | TB | CRM-18 kiểm chỉ đọc ngay ở W0; AI tắt mặc định |
| Ngân sách kết nối RDS sát trần (~132/135) | TB | T4; alarm theo role; thay đổi pool nào cũng phải sửa C2.2 |
| Sửa phạm vi AA-813 (vai trò CRM ở CRM) đụng thiết kế ADR 0006 | TB | Ghi trong CRM-01; sửa mô tả AA-813 trước khi build (D2) |
| Bản sao runner thứ ba lệch ngữ nghĩa | Thấp | Bộ test tuân thủ chung |
| KMS: lệch key policy, khoá mồ côi, tiếng ồn CloudTrail | TB | Kiểm lệch mỗi đêm, tag lúc tạo, dọn khoá giả, cache DEK |
| Spot hết chỗ trên Dev | Thấp | Runbook chuyển `FARGATE` base 1 (+≈ $6/service) |
| Next 16 standalone ARM + `sharp` cần RAM | Thấp | Web 1 GB; đo RSS trong spike |
| Chuyển portal làm vỡ tính năng nội dung đang chạy | TB | Các bước S0–S6, mỗi bước deploy độc lập; giữ Vercel một tuần để rollback |
| Repo public lộ ID tài khoản / DNS NLB | TB | Biến repo; secret scanning; review DM-6.10 trong CI |
| ⚠️ Biến môi trường có dấu gạch dưới (cấu hình web, Cognito, token Mapbox) | — | **This contains underscore env vars — edit manually in VSCode.** Anh sửa tay trong VSCode/console; agent không sinh script cho các biến này |
| Độ trễ do các đồng hồ xác minh bên ngoài (Meta, Google, Microsoft) khi Go-real | TB | Không chặn Dev; thời điểm bắt đầu → chị Thư |

---

## 7. (f) Trả lời ngắn các câu anh hỏi

### 7.1 CASA là gì, và vì sao D6 b tránh được nó

**CASA** (Cloud Application Security Assessment) là đợt kiểm định bảo mật do một phòng lab độc lập làm theo yêu cầu
của Google. App nào xin quyền **Restricted** trên Gmail, nghĩa là đọc hoặc sửa hộp thư (`gmail.readonly`,
`gmail.modify`, `gmail.compose`), mà lưu hoặc chuyển dữ liệu đó qua server thì **phải qua CASA, và qua lại mỗi
năm** ([Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes);
[Google security assessment](https://support.google.com/cloud/answer/13465431), đọc 20/10/2026). Chi phí: nghiên cứu
v1 ghi $675–5.400/năm; các nguồn trên mạng ghi từ vài trăm tới hàng chục nghìn USD, tuỳ tier. Google không công bố bảng
giá chính thức, nên coi là chưa kiểm.

**D6 b** chỉ dùng `gmail.send`, thuộc nhóm **Sensitive** (K21). Thư khách gửi tới đại lý đi vào CRM bằng **chuyển
tiếp** (forward/BCC) tới SES, không đọc hộp thư qua API. Vì vậy:
- không có quyền Restricted, nên không có CASA;
- chỉ còn bước xác minh OAuth thông thường (miễn phí, cần trang chủ + chính sách riêng tư trên domain đã xác minh);
- trên Dev thì chạy ứng dụng ở chế độ "Testing", không cần xác minh.

Cái giá là spec ghi "Two-way Gmail / Outlook sync" (`partner-crm-spec.md:112`), nên đây là một điểm lệch spec đã ghi
lại.

### 7.2 Documenso là gì; các phương án ký điện tử khác; spec thực sự đòi gì

**Documenso** là phần mềm ký điện tử mã nguồn mở (giấy phép AGPL-3.0), tương tự DocuSign. Có hai cách dùng: dùng bản
cloud của họ (trả phí theo năm), hoặc tự cài trên máy của mình. CRM gửi điều khoản và waiver cho khách ký ngay trong
client portal (ký nhúng), rồi nhận PDF đã ký kèm nhật ký ký.

**Spec đòi gì** (nguyên văn):
- `partner-crm-spec.md:121`: "| 12 | Contracts & waivers | E-signature for terms and trekking waiver | 100% signed
  before departure; accepted by insurer |"
- `:181`: "| E-sign provider | Terms + waiver | Signed PDF storage, audit trail |"
- `:46`: "| Booked | Deposit paid | Stage 3 info complete + waiver signed |"
- `:211`: "| 2 | Trekking waiver reviewed by AA's insurer |"
- `:30`: Traveler dùng "… payments, e-sign"

Spec **không chỉ định nhà cung cấp**. Nó chỉ đòi bốn thứ: ký điện tử được, lưu PDF đã ký, có audit trail, và **hãng
bảo hiểm chấp nhận**. Điều kiện cuối mới là cổng thật sự.

**Các phương án** (giá đọc 20/10/2026; chọn là việc của chị Thư, xem `thu-questions.md`):

| Loại | Phương án | AA trả | Công dev | Ghi chú pháp lý / kỹ thuật |
|---|---|---|---|---|
| Vendor cloud | Documenso Teams | $40/tháng, **$480 trả theo năm**, 5 user | Adapter + webhook ≈ 2–3 issue | Không ghi white-label (khách có thể thấy chữ Documenso); dùng cho nhiều đại lý dưới một team cần Documenso đồng ý bằng văn bản |
| Vendor cloud | Documenso Platform | $250/tháng, **$3.000 trả theo năm** | như trên | "Embedded Signing (Whitelabel)", không giới hạn user/tài liệu |
| Vendor cloud | BoldSign Enterprise API | "Starts at $30/month", gồm 40 phong bì, sau đó $0,75/phong bì ([boldsign.com/pricing](https://boldsign.com/pricing)) | như trên | Có ký nhúng, "Custom branding"; rẻ nhất khi ít tài liệu |
| Vendor cloud | Dropbox Sign API Essentials | $75/tháng ($900/năm), từ 50 yêu cầu ký/tháng; Standard $250/tháng ([sign.dropbox.com API pricing](https://sign.dropbox.com/products/dropbox-sign-api/pricing)) | như trên | Trang không ghi rõ gói nào có ký nhúng/white-label |
| Vendor cloud | SignWell API | 25 tài liệu API miễn phí/tháng, sau đó tính theo tài liệu; **trang ghi giá mâu thuẫn** ($0,66 hay $0,85) ([signwell.com/api-pricing](https://www.signwell.com/api-pricing/)) | như trên | Phải hỏi lại giá trước khi dùng |
| Tự host mã nguồn mở | Documenso Community Edition trên acc2 | ≈ $5–17/tháng compute (**ước tính**) + chứng thư ký số của CA (giá **chưa kiểm**) | Adapter như trên + vận hành: nâng cấp, DB riêng ngoài DB Migrate, ngân sách kết nối | Nghĩa vụ AGPL nếu sửa code; ký nhúng có chạy ở bản CE hay không **chưa rõ** → kiểm bằng container CI. OpenSign (AGPL, cần MongoDB) là lựa chọn khác nhưng thêm loại DB mới |
| Tự làm | Chữ ký điện tử đơn giản trong CRM | ≈ $0–1/tháng (khoá KMS để niêm phong PDF) | ≈ 3–4 issue: PDF từ server; OTP email; gõ tên + bấm "Tôi đồng ý"; lưu giờ, IP, trình duyệt, SHA-256 tài liệu; niêm phong PAdES bằng `kms:Sign`; chứng nhận audit; lưu bằng khoá của đại lý | Dữ liệu không rời CRM. Đây là mức "simple electronic signature". Hãng bảo hiểm có chấp nhận hay không là cổng quyết định |

**Lưu ý pháp lý chung (không phải tư vấn luật):**
- Ở Mỹ (ESIGN/UETA), Úc (Electronic Transactions Act 1999) và EU (eIDAS, mức "simple"), chữ ký điện tử đơn giản
  thường được công nhận cho hợp đồng dân sự thông thường.
- Waiver miễn trách nhiệm thì tuỳ nước và tuỳ hãng bảo hiểm.
- Việt Nam có Luật Giao dịch điện tử 2023, nhưng đại lý VN chưa dùng dữ liệu thật (N13).
- Mọi kết luận về giá trị pháp lý thuộc luật sư (D15).

**Về kỹ thuật, engineering chỉ chốt một điều:** adapter viết **trung lập** (`esign.create_envelope / status /
signed_pdf / delete`) để đổi qua lại các phương án trên mà không phải viết lại. Dev dùng Documenso trong CI + stub,
nên $0 và chưa cần chọn nhà cung cấp.

### 7.3 N4 (prod cell) nghĩa là gì

"Prod cell" là **một bộ máy riêng cho CRM chứa dữ liệu khách thật**: một DB Postgres nhỏ riêng (`aa-crm-prod-db`,
t4g.micro) và một máy chủ API riêng, tách hẳn khỏi Dev. Mục đích là để dữ liệu thật không bao giờ nằm trên Dev, đúng
luật C7.1a. Chi phí ≈ $27/tháng. Vì anh đã chọn "chỉ cho đại lý thật dùng khi xong đủ 23 module" và "thử bằng đại lý
giả trước", **bây giờ chưa cần**. Nó nằm trong đợt Go-real. Tới lúc đó có thể dùng luôn môi trường prod chung (AA-880)
nếu đã có.

### 7.4 N5: có phải DB mới không?

**Không.** Trên Dev, CRM chỉ có thêm **một schema `crm`** trong RDS Dev đang chạy (`aa-cis-dev-db`), cùng role riêng
`crm_app`. Không tạo instance mới, không tốn thêm tiền DB. N5 nói một chuyện khác: khi CRM cần dữ liệu của app khác
(thành viên đại lý từ CIS, danh mục tour, giá và chỗ từ Booking), CRM **hỏi qua HTTP**, không được cấp quyền đọc thẳng
bảng của app kia. DB mới duy nhất trong cả kế hoạch là DB của prod cell (§7.3), và chỉ có khi có dữ liệu thật.

### 7.5 N8 nghĩa là gì

N8 là câu "dùng **gói** Documenso nào": Teams ($480/năm, có thể hiện chữ Documenso trên trang ký) hay Platform
($3.000/năm, mang thương hiệu riêng). Anh chọn b (Teams nếu Documenso đồng ý bằng văn bản). Phụ lục này **hoãn** N8:
- Dev không cần gói trả phí (§7.2);
- đây là chuyện vendor và tiền, nên đưa sang chị Thư cùng các phương án khác (BoldSign, tự host, tự làm), để chị chọn
  trước Go-real.

### 7.6 N10: AI model dùng để làm gì

Đây là **module 14** của spec ("AI agent layer": drafts replies, proposals, follow-ups … approval required,
`partner-crm-spec.md:131`). Haiku sẽ:
- soạn **nháp** email/tin nhắn trả lời khách, dựa trên trip và các trả lời Stage 1–2;
- soạn nháp tin nhắc cho khách im lặng, hoặc nhắc điền form Stage 2;
- soạn phần chữ của proposal (module 4: bản email hoặc WhatsApp ngắn), tóm tắt một thread dài, dịch EN ↔ VI.

Haiku chỉ thấy dữ liệu đã lọc (F2 + text đã scrub, không có Stage 3). **Không bao giờ tự gửi**: agent đọc, sửa, bấm
gửi. AI tắt mặc định với mỗi đại lý, trần $2/đại lý/tháng. Chọn Haiku vì rẻ (≈ $1,3/đại lý/tháng nếu bật hết). Sonnet
chỉ dùng khi đại lý bật cho proposal dài. Việc này rơi vào đợt D7. Trước đó cần kiểm Haiku 5.5 có profile `us.` trên
acc3 không (T11, CRM-18).

---

## 8. Nguồn

**Repo (mốc ở đầu tài liệu):**
- Infra:
  - `modules/alb/{main.tf,vpc_link.tf}`, `modules/vpc/main.tf:256-270`, `modules/waf/variables.tf:20-25`;
  - `accounts/aa365/{cicd.tf,cicd_split.tf,identity.tf,identity_variables.tf,e2e_mailbox.tf,booking.tf,variables.tf}`;
  - `accounts/acc3-bedrock/main.tf`.
- CIS: `api/core/app_registry.py`, `api/routers/admin_job_runner.py`, `api/core/identity_config.py`,
  `api/routers/v1_trip_page.py:157`, `frontend/app/trip/[tourId]/page.tsx:146`, `frontend/lib/auth-server.ts:190-205`.
- Booking: `backend/app/{db.py,jobs/}`.
- TripPlanner: `frontend/components/MapView.tsx`, `frontend/package.json`.
- Root: spec, `docs/architecture/data-standards/03-scaling.md`, `docs/architecture/db-schema-reference.md`,
  `docs/backlog/README.md:35,86,112,130,132`.

**Web (đọc 20/10/2026):**
- [CloudFront pricing](https://aws.amazon.com/cloudfront/pricing/)
- [CloudFront pay-as-you-go](https://aws.amazon.com/cloudfront/pricing/pay-as-you-go/)
- [CloudFront VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html)
- [KMS in IAM policies](https://docs.aws.amazon.com/kms/latest/developerguide/cmks-in-iam-policies.html)
- [GuardrailPiiEntityFilter](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailPiiEntityFilter.html)
- [SES quotas](https://docs.aws.amazon.com/ses/latest/dg/quotas.html)
- [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [Google security assessment](https://support.google.com/cloud/answer/13465431)
- [Documenso pricing](https://documenso.com/pricing)
- [BoldSign pricing](https://boldsign.com/pricing)
- [Dropbox Sign API pricing](https://sign.dropbox.com/products/dropbox-sign-api/pricing)
- [SignWell API pricing](https://www.signwell.com/api-pricing/)
- AWS price list `AmazonECS/current/us-west-1`
- Bảng giá model Claude (skill `claude-api`, cache 06/10/2026)

Các nguồn web còn lại lấy từ ba bản review, có ghi ở từng bản.

**Ước tính chưa kiểm:**
- mức giảm của Spot;
- free tier CloudFront khi tính tiền qua TrueIDC;
- giá Bedrock của Claude;
- Haiku 5.5 có profile `us.` trên acc3 hay không;
- chi phí CASA;
- giá chứng thư ký số;
- ký nhúng trong Documenso CE;
- số issue và số phiên.

---

## Kiểm tra cuối

Vòng kiểm cuối ngày 20/10/2026, Claude Code. Tôi đọc lại toàn bộ các file đầu vào và các bản review, rồi kiểm lại
bằng code ở `origin/main` (cùng mốc commit ghi ở đầu tài liệu) và tài liệu AWS. Lỗi nhỏ thì sửa thẳng vào file. Lỗi
lớn thì ghi ở đây, kèm cách xử lý đề xuất.

### A. Các quyết định vòng 2 đã áp dụng chưa

| Quyết định | Đã áp dụng? | Ở đâu |
|---|---|---|
| N3 b: Fargate sau CloudFront | ✔, nhưng thứ tự rule ALB sai, đã sửa (mục B1) | §3.1, CRM-04, CRM-05 |
| D12 đổi: CRM có gateway riêng, CIS vẫn xem được | ✔ | §3.2, CRM-02, CRM-17 |
| D22 đổi: CRM có runner riêng, CIS vẫn xem được | ✔ | §3.3, CRM-10, CRM-16 |
| H1 b: chỉ cho đại lý thật dùng khi đủ 23 module | ✔. Ngày dự kiến đã sửa từ "giữa 1/2027" thành "giữa 12/2026 – giữa 1/2027" | §0.5, §4.2, `thu-questions.md` 5.1 |
| H4: thử bằng đại lý giả | ✔. Phần ghi AWS của seeder đã ghi rõ ai chạy | §3.4, CRM-15 |
| Dev trước, không có prod cell | ✔ | §3.5, T3 |
| Việc kinh doanh, pháp lý, vendor có phí → chị Thư | ✔. Đã sửa các câu "chị đã duyệt" thành "anh Nghiệp tạm trả lời thay chị", và thêm câu về tài khoản Stripe nền tảng | `thu-questions.md` |

Tôi không thấy chỗ nào engineering tự chốt chuyện kinh doanh. T1–T14 đều là quyết định kỹ thuật. Chi phí, vendor,
domain, thời hạn giữ dữ liệu và câu hứa về quyền riêng tư đều nằm trong `thu-questions.md`.

### B. Lỗi lớn tìm thấy

**B1. CloudFront có thể làm lộ CIS API và Booking API (mức Cao, đã sửa trong thiết kế và issue).**
- §3.1 bản trước ghi "CRM lấy số sau 100".
- Default action của listener :80 là CIS (`modules/alb/main.tf:78-85`). Rule Booking ở priority 100 chỉ xét path
  (`booking.tf:356-372`).
- Vì vậy, nếu rule web nằm sau 100:
  - `partner-dev.…/booking/*` đi vào Booking API;
  - mọi request có Host không khớp (ví dụ tên `dXXXX.cloudfront.net` của distribution) rơi vào CIS API;
  - cả hai đều đi vòng qua API Gateway. Rule `VpcLinkInternalAllow` còn bỏ qua rate limit và chặn theo nước của WAF
    cho traffic đến từ NLB.
- Bản trước còn có một xung đột path: rule api `/crm*` sẽ nuốt trang `partner-dev./crm/trips` của CRM-14.
- **Đã sửa:**
  - rule web (host + `X-AA-Origin`) đặt ở priority < 100;
  - ngay sau đó là rule "có `X-AA-Origin` bất kỳ → 403";
  - rule api đặt sau cùng.
  - Done-when của CRM-04 kiểm cả hai đường lộ trên.

**B2. Khoá KMS của từng đại lý có thể không tạo được (mức Cao, phải kiểm ở CRM-07).**
- API `CreateKey` ghi: "The key policy must allow the calling principal to make a subsequent `PutKeyPolicy` request
  … (To omit this condition, set `BypassPolicyLockoutSafetyCheck` to true)"
  ([CreateKey](https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html), đọc 20/10/2026).
- Thiết kế S1 lại đặt ba điều cùng lúc:
  - task role tự tạo khoá;
  - task role **không bao giờ** có `PutKeyPolicy`;
  - `BypassPolicyLockoutSafetyCheck = false`.
- Ba điều này nhiều khả năng mâu thuẫn nhau, nên `CreateKey` sẽ lỗi `MalformedPolicyDocumentException`.
- Đề xuất kỹ thuật: cho phép `CreateKey` chỉ khi `kms:BypassPolicyLockoutSafetyCheck = true`. Cách này an toàn vì câu
  (b) của template giao quyền quản trị khoá cho account root, và job kiểm lệch mỗi đêm giữ cho template không bị đổi.
- Phương án khác: dùng một role "cấp khoá" do Terraform quản lý.
- Đã ghi vào CRM-07, và sửa Done-when của CRM-07 để không còn vòng phụ thuộc với CRM-11. Bước kiểm "khoá do role CRM
  tạo mang đúng template" đã chuyển sang CRM-11.
- ADR (CRM-01) cần ghi lại lựa chọn sau khi kiểm.

**B3. Lát cắt đầu chưa phải một vòng trọn vẹn (mức TB, cần anh chọn thứ tự).**
- Lát cắt 18 issue dừng ở các bước: đăng nhập → đại lý → khách → trip ở bước Inquiry → bảng. Nó **chưa** đi qua
  proposal → booking → hoá đơn/thanh toán test → client portal.
- Theo thứ tự D1–D7 hiện tại, vòng đó chỉ chạy được sau D5, khoảng phiên thứ 17–19. Lý do là D5 xếp sau D4, mà D4
  (hàng AA trong Booking + builder) là cột dài nhất, lại phụ thuộc vào kết quả issue điều tra ghép tuyến.
- Đề xuất: thêm **"Lát cắt 2: trọn vòng đời bằng hàng của chính đại lý"** ngay sau D1, khoảng 9–10 issue. Đây không
  phải issue mới mà là kéo lên từ D3/D5:
  - module 15 tối giản: nhà cung cấp riêng của đại lý;
  - module 4: proposal dạng email kèm link chấp nhận;
  - chuyển trip sang Proposal, rồi Booked khi khách trả cọc;
  - module 6: dòng ledger của đại lý;
  - module 7: hoá đơn + Stripe test pay link + webhook;
  - module 11 tối giản: OTP + xem proposal/hoá đơn + form Stage 3;
  - module 12: qua adapter trung lập với provider stub.
- Lát cắt này không phụ thuộc Booking B2B, builder, hay vendor nào chưa được chọn. Như vậy "chạy trên Dev" có nghĩa
  là chạy cả vòng đời, khoảng phiên thứ 7–8 thay vì 17–19.
- Tổng số issue không đổi; D3/D5 bớt đi đúng phần đã kéo lên.
- **Anh chọn:** giữ thứ tự cũ, hay chèn Lát cắt 2 (khuyến nghị).

**B4. Những tài khoản test mà Dev vẫn cần có người tạo (mức TB, chưa ghi ở bản trước).**
- §3.4 ghi "không cần gói trả phí hay hợp đồng". Đúng là không mất tiền, nhưng mỗi mục dưới đây vẫn cần **một tài
  khoản do người thật tạo**. Hiện chưa repo nào có tích hợp Stripe (`git grep stripe` không thấy gì).
  - Stripe ở chế độ test: tài khoản nền tảng Connect;
  - Meta: developer app + số test;
  - Twilio: trial;
  - Google Cloud: project ở chế độ "Testing";
  - Microsoft: Entra tenant + một hộp Outlook test, cho module 5 nhánh Outlook.
- **Anh chọn:** anh tạo các tài khoản test này để làm Dev (khuyến nghị: miễn phí, không kích hoạt thanh toán), hay chờ
  chị Thư.
- Việc tài khoản thật đứng tên pháp nhân nào đã nằm trong `thu-questions.md` (3.2, 3.4, 3.6, 3.7).
- Mỗi tài khoản là một điều kiện chặn của đợt dùng nó: Stripe chặn Lát cắt 2/D5, Google và Microsoft chặn D3, Meta
  và Twilio chặn D6.

**B5. "Đủ 23 module trên Dev" cần một định nghĩa (mức TB).**
- Có sáu module không thể "xong" chỉ trên Dev:
  - module 12: chưa có provider ký điện tử, và cần hãng bảo hiểm chấp nhận;
  - module 9: số thật cần Meta Tech Provider;
  - module 7: nhánh đại lý Việt Nam chưa có cổng thanh toán;
  - module 5: nhánh Outlook (B4);
  - module 14: còn tuỳ Haiku 5.5 có profile `us.` hay không (CRM-18);
  - module 17: spec ghi "needs 3–6 months of real data".
- Đề xuất định nghĩa: "xong trên Dev" = chức năng chạy với dữ liệu giả, vendor ở chế độ test hoặc stub qua adapter,
  và có test E2E. Chỉ số thành công của spec chỉ đo được sau khi có đại lý thật.
- H1 b ("đủ 23 module rồi mới cho đại lý thật dùng") vì vậy phụ thuộc ba câu của chị Thư: 3.1 (ký điện tử), 4.1
  (hãng bảo hiểm) và 5.3 (khi nào bắt đầu thủ tục với Meta, Google, Microsoft). Nên ghi rõ điều này trong ADR
  (CRM-01).

**B6. Issue điều tra ghép tuyến chưa có bản nháp trong bộ này (mức TB).**
- T13 và đợt D4 đều chờ issue này, nhưng `crm-w0-w1-issues.json` không có nó, và không file nào trong `s245-r2/`
  chứa bản nháp.
- Khi tạo issue này (anh đã duyệt), Done-when cần có một câu: "ghi rõ CRM builder dùng lại logic ghép tuyến bằng
  cách nào: `tp.routes.v1` hay API graph trong CIS". Như vậy T13 mới quyết được.

### C. Lỗi nhỏ đã sửa thẳng vào file

**Trong `crm-w0-w1-issues.json`:**

| Issue | Sửa gì |
|---|---|
| CRM-01 | Done-when lẫn lộn "description" với "comment" |
| CRM-05 | Thêm: quyền gửi SES cho task role (chỉ From đã định, chỉ configuration set `transactional`); mở hộp thư E2E cho địa chỉ của đại lý giả và cho AA-Partner đọc; thứ tự rule ALB |
| CRM-06 | Đường dẫn đúng `db/migrations/roles/`; thêm `crm_app` vào `password_roles` và vào mode `set-password` |
| CRM-07 | Kiểm lockout (B2); Done-when dùng khoá canary, không còn vòng phụ thuộc |
| CRM-08 | Thêm `blocked_by` CRM-05, vì Done-when cần ECR và OIDC |
| CRM-09 | Thêm bước tay: secret DSN + `set-password` trước khi scale lên 1 |
| CRM-10, 11, 12, 13, 17 | Số migration lấy theo thứ tự merge (CRM-10 và CRM-11 chạy song song nên có thể trùng `crm-002`). Thêm các bảng chưa issue nào tạo: `crm.task`, `crm.metric_event` (CRM-12) và `crm.web_session` (CRM-13) |
| CRM-12 | Thêm `blocked_by` CRM-15, vì Done-when cần mail tới đại lý giả |
| CRM-14 | Ghi nguồn credential cho Playwright |
| CRM-15 | Phần Cognito và Secrets chạy bằng profile MFA của anh, không chạy từ task role |
| CRM-16 | Route ở CIS phải nằm dưới prefix `admin/` thì BFF mới gửi bearer (`frontend/lib/auth-server.ts:174`). Token là access token, `client_id` |

**Trong tài liệu này:**
- §0.5 và §4.2: sửa ngày dự kiến;
- §5: sửa phần so sánh chi phí, và ghi thêm ≈ $2/tháng chưa tính;
- §3.1: sửa thứ tự rule ALB;
- §4.1: sửa cột "song song" và các điểm nghẽn.

**Trong `thu-questions.md`:** CASA ghi đúng một khoảng giá như §7.1; ghi rõ các mục anh Nghiệp tạm trả lời thay chị;
thêm câu về tài khoản Stripe nền tảng; sửa ngày ở 5.1.

### D. Đối chiếu chi phí giữa các file

| Con số | Các file | Kết quả |
|---|---|---|
| Fargate on-demand: api $8,29, web $9,78 | §5 so với K23 | Tính lại ra đúng |
| Tổng Dev $10–15 / $13–18 / $14–21; xấu nhất $23–32 | §5 | Cộng lại khớp |
| 10 đại lý ≈ $79–86 trước tiền ký điện tử (bằng v2 §9.3 bỏ Documenso, + $8,3 web, + $7,5 WAF) | §5, `thu-questions.md` 1.1 ($8–9/đại lý) | Khớp |
| WAF ≈ $7–8, Documenso $480 / $3.000, BoldSign, Dropbox | §5, §7.2, `thu-questions.md` 3.1, 3.8 | Khớp |
| CASA | §7.1 so với `thu-questions.md` 3.6 | Bản trước lệch ("vài trăm tới vài nghìn"), đã sửa |
