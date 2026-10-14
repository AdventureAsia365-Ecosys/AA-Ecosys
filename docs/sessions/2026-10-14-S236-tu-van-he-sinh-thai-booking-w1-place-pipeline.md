# S236 — 14/10/2026 — Tư vấn hệ sinh thái, Booking đợt 1, TripPlanner trang tour, identity Cognito, AA-712 place pipeline

**Tác nhân:** Claude Code (WSL → VS Code giữa phiên, Ultracode bật) — điều phối + workflow nhiều agent (lane code, review đối kháng, panel).
**Audit / artifact:** `docs/audits/2026-10-14-S236-design-review/` (README tư vấn thiết kế, panel thẻ trùng, ui-verify, aa712 thiết kế + nghiên cứu geocoder + bake-off, AUP 2026-11).

## Trạng thái cuối phiên
- ECS CIS: api :596 / worker :152 (COMPLETED, /health 200). Worker có `T2_JUDGE_ANCHORS=on`, `T2_JUDGE_GATE=brand_fit`; job kind mới `place_extract`, `place_geocode`, `tour_graph_build` (công tắc `PLACE_PIPELINE_AUTO` **tắt** → chưa có lời gọi tốn phí).
- Booking: `aa-booking-dev-api` (deploy 4063c3a), `/booking/health/ready` → bk-006. Admin nhân viên trên Vercel project `aa-booking-admin` (root `frontend/`).
- Migration áp trong phiên: CIS **225** (catalog views, thiết kế lại `catalog_owner`), **227** (sonnet-5/opus-5-5 không temperature), **226** (schema geo — áp sau 227); TripPlanner **tp-010**; Booking **bk-003 → bk-006**. `db-schema-reference.md` đã regenerate.
- Lambda concurrency acc2 = **10** → đã xin tăng lên 1.000 (case AWS mở, chờ duyệt).
- MFA `aa365-admin` phiên 12h (role max 43200, `~/.aws/config` đã đổi; role agent 12h qua Infra #103).

## Quyết định của Nghiệp
- Duyệt toàn bộ kế hoạch tư vấn (CIS admin/tenant, TripPlanner theo trip.com/adventure.asia, Booking) + tạo issue mới AA-810→821.
- Thẻ trùng: áp đề xuất panel (gộp Paro→Paro Town, Rongbuk→Rongbuk Valley, chuyển 2 atom, 34 sửa fact).
- TripPlanner: trang chủ **search-first** + bản đồ; "Customise this trip" dựng từ địa điểm chỉ khi ≥ 50% số ngày; làm AA-712 rồi chạy toàn catalog.
- Booking: build **cả 3 đợt** thật (phiên này xong đợt 1); giao diện = token adventure.asia (kit CIS) + layout Figma; cọc 30%, báo giá 14 ngày (cấu hình); khách sạn/hoạt động **phương án lai** (Booking giữ dữ liệu cung ứng/thương mại, CIS viết nội dung khách) → ADR 0004a.
- Identity: **AA-703 làm epic** (680/811/813/816 là con); **Amazon Cognito** acc2 (ADR 0006); nhân viên đăng nhập **mã email** (email công ty ở DreamHost, không có Google Workspace → bỏ Google).
- AA-801: so 3 cách → **bật anchors + gate brand_fit**, mission chỉ chẩn đoán (đối chứng brand-swap cho thấy mission còn dễ dãi).
- Geocoder: **Geoapify** (Mapbox Permanent cấm hiển thị công khai; Amazon Location phủ kém) — Nghiệp đã đăng ký, key ở `aa-cis/dev/geoapify`.
- AA-712: duyệt toàn bộ khuyến nghị thiết kế (schema `geo`, ADR 0007); phiên này **chỉ áp 226 + merge**, chạy thử 3 tour để phiên sau.
- Infra #103 (tách role CI) apply + chuyển CI sang role mới; tăng quota Lambda 1.000; DNS `lumiguides.it.com` sang Route 53 (AA-818); đối chiếu Anthropic AUP + tạo AA-819/820.
- Mở AA-817 (RLS `aa_cis_admin`) cho phiên sau. Ghi ý tưởng CRM cho tenant của chị Thư (AA-821, chưa làm).
- Linear: mỗi project ≤ 100 issue chưa lưu trữ; Done hẳn → lưu trữ sớm (skill aa-linear-issue đã sửa).

## Thay đổi Codebase
- **CIS:** #720 AA-766 (Tenant 360 Cost/Quality/Markets + Settings editors), #721 AA-680 (CIS cấp RS256 `aud=booking` + JWKS), #722 AA-801 median3 (cờ), #723 AA-679 (migration 225 catalog views, `catalog_owner` + policy, `tenant_isolation` NULLIF), #724 AA-801 anchors + model override adhoc, #725 AA-801 mission + 227, #726 AA-712 (226 geo, 3 job, Geoapify, `PLACE_PIPELINE_AUTO`).
- **TripPlanner:** #71 AA-805 (thứ tự chặng, /narrate owner + cache + trần chi phí, search_query, payload 1.1, tp-010), #72 AA-812 (search-first home, `/tours/[slug]` 892 trang + `/destinations/[country]` 14 trang SSR, sitemap, JSON-LD), #73 hotfix (tile ≤16 request/lần xem, Customise từ địa điểm ≥50%), #74 AA-712 (top-k vector search trên HNSW).
- **Booking:** #2 bk-003 (staff JWT, trip case workflow, versions), #3 bk-005 (đợt 1 backend, D2–D4), #4 AA-810 pricing (bk-004, bk-006), #5 AA-683 admin nhân viên Next.js.
- **Gốc:** #65 contract `catalog.tour.v1`, #66 ADR 0006 + 0004a + nghiên cứu Cognito, #67 ADR 0006 chỉ mã email, #68 ADR 0007 + bằng chứng AA-712.
- **Infra:** #102/#104/#106/#107/#109 bản copy migration; #103 tách role CI + throttle TripPlanner (narrate 2 rps, search 10 rps) + role agent 12h; #105 Cognito (draft, chưa apply); #108 worker anchors on.

## Thay đổi Hạ tầng / AWS
- Secret `aa-cis/dev/booking-jwt-signing-key` (kid bk-2026-10); `aa-cis/dev/geoapify` (Nghiệp tạo).
- Role `nghiep-admin-8h-session` MaxSessionDuration 12h; Infra #103 local apply (22 add/9 change/1 destroy); CI secret `AWS_ROLE_ARN` chuyển sang tf-plan / tf-apply / app-deploy — plan, apply, migrate-check, deploy đều xanh.
- Vercel project `aa-booking-admin` (tạo bằng CLI; MCP không có quyền tạo).
- Service Quotas: Lambda concurrent executions 10 → 1.000 (CASE_OPENED).

## Bằng chứng verify
- AA-766: cost endpoint $8,4833 = `llm_call_log` (shadow loại trừ) $8,483304; UI 1440/390 sáng/tối 0 lỗi → **Done**.
- Booking: đăng nhập CIS → booking-token → `/booking/staff/me` 200, `/booking/trip-cases` (TC-000001); preview admin 10 trang PASS, 0 lỗi console, máy tính giá 1000 USD → 1.495 USD.
- 225: `booking`/`tripplanner` đọc `catalog.v_tour` = 892, `booking` đọc thẳng `published_tours` → InsufficientPrivilege.
- TripPlanner: sitemap 892 tour + 14 điểm đến, SEO 100 (alias); hotfix: `/plan` 16 request, zoom/pan 0, throttle 0, Kailash 21 ngày, Sri Lanka 404 + 10 ngày.
- AA-801: anchors + Luna spread ≤1 9/9, mission ổn định 9/9, $0,0026/lần; đối chứng brand-swap brand_fit 7–8 → 5,67 (mission 5/9 "không" → chỉ chẩn đoán).
- Geocoder bake-off 71 tên: Geoapify 38/64 vs AWS 14/64; khó 18/29 vs 1/29.
- Thẻ trùng: gộp 2, chuyển 2 atom, 34 sửa fact (snapshot S3 trước mỗi bước, audit_log).

## Linear
- Done: AA-766. Mới: AA-810→AA-821. Epic AA-703 (con 680/811/813/816).
- In Progress có comment bằng chứng: 679, 680, 681, 683, 712, 801, 805, 806, 810, 812.
- Số issue chưa lưu trữ: CIS Core ~93 (45 mở + 48 Done), Portal ~29, TP&Booking ~24, không project 4 → **Nghiệp lưu trữ Done trên UI** + bật auto-archive.

## Còn lại (phiên sau)
1. AA-712: admin dry-run → **thử 3 tour** (≈ $0,10–0,30) → báo cáo → 1 nước → bật `PLACE_PIPELINE_AUTO` → catalog views 228 → TripPlanner cut-over.
2. AA-817 (RLS `aa_cis_admin`) — bảo mật, High.
3. AA-801: chờ job T2 thật trên worker mới + theo dõi 1 tuần.
4. Booking đợt 2 (NCC, khách sạn/dịch vụ, template) → đợt 3 (hoá đơn, thanh toán, trip check); FX rates; 2 lỗi nhẹ dashboard/giá.
5. AA-818 sub-domain + Route 53; AA-811 SES; Cognito apply (#105) sau khi chốt domain `auth.`.
6. AA-819/820 trước 11/11 (AUP Anthropic).
7. AA-806 bước 3 (bỏ role CI cũ sau vài ngày xanh) + WAF enforce.

## Lưu ý kỹ thuật
- RDS: `aa_cis_admin` không BYPASSRLS nhưng **đọc mọi dòng dưới tenant lạ** (thành viên `rds_superuser`) → AA-817; view đọc bảng FORCE RLS dùng role chủ riêng + policy (mẫu 225).
- Account Lambda concurrency 10 — burst tile của `/plan` từng gây 1.591 throttle; đã sửa client + xin quota.
- zsh không tách biến `$P` thành nhiều tham số → dùng `bash -c` cho lệnh aws nhiều cờ.
- Phiên Claude Code bị ngắt 2 lần (Kiro lỗi, chuyển VS Code; hạn mức agent) → việc dài chạy bằng **one-off ECS task** thay vì ECS exec.
- Vercel MCP không tạo/đọc được project mới → dùng Vercel CLI (đã đăng nhập).
- `.claude/settings.json` có quyền tự thêm khi duyệt lệnh — không commit.
