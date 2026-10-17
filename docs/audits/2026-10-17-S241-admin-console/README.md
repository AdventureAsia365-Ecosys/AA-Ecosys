# S241: Tổ chức lại khu admin: Platform, staff, app con và nội dung CIS

- **Ngày:** 17/10/2026 (S241). **Tác nhân:** Claude Code (workflow 3 thiết kế + 2 giám khảo mỗi thiết kế).
- **Câu hỏi của Nghiệp:** admin chưa có trang quản lý staff, chưa quản lý các app con, và đang trộn nội dung CIS với việc của cả nền tảng. Nên tổ chức thế nào?
- **Phạm vi:** khuyến nghị. Không đổi code, không tạo issue. Issue mới ở §7 chỉ là đề xuất, cần Nghiệp đồng ý trước khi tạo.
- **Nguồn:** khảo sát code CIS admin (`apps/AA-CIS-App/frontend/app/admin/*`, `_kit/adminNav.tsx`, `lib/rbac.ts`, `api/routers/admin_*.py`), Booking admin (`apps/AA-Booking/frontend/app/(staff)/*`, `backend/app/auth/staff.py`), TripPlanner, AA-CIS-Infra (`observability*.tf`), ADR 0004/0006/0008, báo cáo SDLC S241 (`../2026-10-17-S241-sdlc-review/README.md`).
- **Phản biện:** đã qua một vòng phản biện (kỹ sư solo + bảo mật), đối chiếu lại với code (CIS `cafd13a8`, Booking `dc51c8b`) và probe live chỉ-đọc trên Dev ngày 17/10. Các điểm đã sửa ghi ở §11.

---

## 1. Tóm tắt khuyến nghị

1. **Chọn phương án A, "một console có phân khu"** (điểm TB 7,0, cao nhất). Vẫn là app `aa-cis-frontend`, nhưng sidebar tách hai khu: **Platform** (người, app, tenant, tiền, máy móc) và **CIS Content** (pipeline, A3/A4, SEO, ảnh). Booking admin giữ app riêng và chỉ được link tới. TripPlanner không có admin riêng, chỉ có trang trạng thái trong Platform.
2. **Bảo mật đi trước, và có một lỗ P0 mới phải vá trước mọi thứ.** Phản biện tìm thấy **26 route `GET /admin/*` không cần secret** trên API public (job list có `payload`/`result`/`error`, llm-config, chi tiêu, budgets, photos…; probe live 17/10 trả 200 không header; chi tiết §2). Báo cáo SDLC S241 chưa ghi lỗ này. Vá ở **GĐ −1** (nửa ngày). Sau đó mới tới các bước khác. Chưa bật trang staff có quyền *ghi* khi backend còn tin header `x-admin-role` đi kèm `ADMIN_SECRET` (S241 P0-5/P1-3). Riêng danh sách staff *chỉ đọc* (admin-only) thì ra sớm được, ngay sau PR authz đầu tiên.
3. **Phân quyền theo capability** (`require_perm("staff.write")`…), copy pattern `PERMISSIONS + require()` của Booking. Không rải tên role khắp router. Policy tra theo **(method, route template)**, không gắn một quyền cho cả `APIRouter` (§5.2). Từ GĐ1, secret đi **không kèm** role được coi là *machine principal* với allow-list hẹp, để CI deploy-gate, smoke và Lambda scheduler không bị khoá. Backend **verify staff JWT** từ GĐ4, lúc đó mới thôi tin header.
4. **Không đổi URL hiện có.** Trang nền tảng mới nằm dưới `/admin/platform/*` (đã nằm trong `matcher` `/admin/:path*`). Settings tách đôi, link cũ được redirect.
5. **Không thêm Vercel project, không thêm dịch vụ AWS.** Chi phí chạy mới ≈ 0–1 USD/tháng tới hết GĐ11. Cognito (GĐ12) thì **không** bằng 0: ADR 0006 tính WAF cho pool khoảng 12–15 USD/tháng (§8).
6. **Tuần này (S241–S242) chỉ làm GĐ −1 + GĐ1 + GĐ2**, khoảng 3,5–4,5 ngày công: vá GET public, authz phần 1 cho route tiền/model, trang Staff chỉ đọc. GĐ0 (nav phân khu, chỉ FE) là phần làm thêm nếu ba việc kia xong. **Mốc MVP** (GĐ −1…6, khoảng 13–17 ngày công kể cả verify): authz server-side, nav phân khu + tách Settings, staff đọc/sửa role-active, audit vào `acp_shared.audit_log`. Apps health, audit view, cost theo app, Cognito là các bước sau và chỉ kéo vào khi thắng việc CIS.

---

## 2. Hiện trạng: admin đang trộn gì

17 trang `/admin/*` dùng chung một shell (`app/admin/layout.tsx` → `_kit/AdminShell.tsx`) và một nav model (`_kit/adminNav.tsx` `NAV_GROUPS`: Overview · Content · Intelligence · Tenants · Operations, cộng Settings). Nhóm được đặt tên theo **cơ chế**, không theo **người dùng** hay **app**.

| Route / mục | Nội dung thật | Thuộc về | Ghi chú lệch |
|---|---|---|---|
| `/admin/upload` | S0 ingest, staging | CIS Content | ALL_STAFF; backend chỉ check secret |
| `/admin/s1-rewrite` | S1 rewrite, live writer | CIS Content | đọc `llm-config` (việc nền tảng) |
| `/admin/review` | A1 review queue | CIS Content | landing của reviewer/content; còn shim `x-reviewer-id` |
| `/admin/master-content` | A2 masters, versions, export | CIS Content | ghi activate/trash: mọi staff gọi được |
| `/admin/photos` | Drive sync, gán ảnh | CIS Content (tài sản dùng chung) | page admin-only, nhưng sync/assign mọi staff gọi được; 6 route `GET /admin/photos*` **không cần secret** |
| `/admin/atom-curation` | Social Content 01–05 (A3) | CIS Content | dưới nhóm "Intelligence" |
| `/admin/content-quality` | T2/T9 quality | CIS Content | chỉ vào được qua sub-nav; một trong hai chỗ có check role server-side thật |
| `/admin/seo-intelligence` | SEO demand | CIS Content | chỉ đọc |
| `/admin/platform-stats` | Social 07: A4 review log, gate telemetry | CIS Content (QA output tenant) | tên có chữ "platform" nhưng nội dung là QA nội dung |
| `/admin/tenant-activity` | Social 06: Content Trace, unpublish | CIS Content › Tenant output | nằm dưới "Intelligence"; unpublish không check role |
| `/admin/tenants` (+ Tenant 360) | tài khoản, billing, cost, audit theo tenant | Platform › Tenants | ghi đã check role; đọc cost/billing thì mọi staff gọi được |
| `/admin/overview` | funnel nội dung + intelligence + tenants + jobs + cost + alerts | **trộn** | chỉ có CIS; AA-858 chờ chị Thư |
| `/admin/jobs` | job runner, worker health | Platform | cancel/retry không check role; chỉ `shared.job`; `GET jobs`, `jobs/{id}`, `jobs/{id}/llm-calls`, `summary`, `workers`, `retention` **không cần secret** |
| `/admin/llm-usage` | External Spend, Budgets | Platform | `PUT budgets` không check role; Cost Explorer nhóm theo SERVICE, không theo app; `GET budgets`, `llm-usage/*`, `spend/daily`, `cost-explorer`, `dfs-*` **không cần secret** |
| `/admin/decisions` | Jev Decisions | Platform (AI) | `PUT questions` không check role |
| `/admin/api-docs` | OpenAPI | Platform (Developer) | admin-only ở cả 3 lớp |
| Settings: Pipeline Gates, Brand, SEO Config | cấu hình nội dung | CIS Content | ALL_STAFF, không gate theo tab |
| Settings: LLM Models, Jev Credit, UI Kit | cấu hình nền tảng | **Platform** | reviewer/content mở được và PATCH được model route, top-up Jev: **chỗ trộn nguy hiểm nhất** |
| Settings: Tenant Info | dữ liệu tenant | Platform › Tenants | lạc chỗ |
| Shell: BottomNav | điều hướng mobile | — | hard-code Overview/Jobs, không lọc theo role |
| `PAGE_RULES /admin/pipeline` | — | — | rule thừa, không có trang |

**Chưa có:** quản lý staff (tài khoản `shared.admin_users` chỉ tạo bằng `scripts/create_staff_user.py` qua ECS exec), health/version từng app, view deploy, audit log staff thống nhất, plan catalog, cost theo app. Booking admin đã có `/staff` và `/staff/[cisUserId]`, `/audit-log`. Hai trang staff của Booking ghi "Staff accounts and passwords are managed in CIS admin" (`app/(staff)/staff/page.tsx:78`, `[cisUserId]/page.tsx:161`), nhưng không có link nào, và phía CIS cũng **chưa có trang** tương ứng. (`ManagedInCisLink` trong `ui/booking/FromCis.tsx:16` là component link chung nhận `path`; hôm nay nó chỉ trỏ tới trang CIS có thật, như Master Content và trang chủ admin.)

**Kiểm quyền hôm nay:** page có allow-list (`middleware.ts` + `PAGE_RULES`). BFF `canWriteAdminPath` **cho ghi mặc định** (`rbac.ts:117-121`). Backend: phần lớn route `/admin` chỉ `verify_admin_secret` (`admin.py:110`, so sánh `!=`, không constant-time). Role chỉ được check lại ở 3 nơi: tenant writes, content-quality writes, `openapi.json`. Hệ quả: reviewer/content gọi được endpoint admin-only qua `/api/admin`, kể cả ghi.

**Lỗ P0 mới (phản biện, verify live 17/10):** 26 route `GET /admin/*` **không kiểm secret nào**, nên ai trên internet cũng gọi được qua `api-cis.lumiguides.it.com`:
- `admin_job_runner.py`: `jobs`, `jobs/{id}`, `jobs/{id}/llm-calls`, `summary`, `workers`, `retention`. Job list trả `payload`, `result`, `error`, `created_by`, `cost_usd`.
- `admin_llm_ops.py`: `llm-config`, `llm-catalog`, `llm-shadow/report`, `llm-usage/tree`, `llm-usage/calls`, `dfs-usage`, `dfs-usage/by-country`, `spend/daily`, `dfs-balance`, `cost-explorer`, `unmapped-market-requests`.
- `admin_budgets.py`: `GET /admin/budgets`.
- `admin_photos.py`: `summary`, `/`, `folders`, `tour-coverage`, `destinations`, `tours`.
- `admin_segment_research.py`: `GET status`, cùng `POST preview` (dry run, không tốn tiền, nhưng vẫn chạy query nặng).

Đã curl không header: `workers`, `summary`, `jobs`, `retention`, `llm-config`, `llm-catalog`, `llm-usage/calls`, `budgets`, `photos/summary`, `cost-explorer`, `dfs-balance`, `segment-research/status`, `unmapped-market-requests`, `spend/daily` đều trả **200**. Bước smoke trong `deploy-dev.yml` (dòng 292) còn gọi `/admin/job-runner/workers` **không gửi secret** và dựa vào lỗ này để chạy. Báo cáo SDLC S241 chưa ghi lỗ này. Danh sách lấy bằng cách quét AST các router `admin_*.py` tìm route không có `verify_admin_secret`/`Depends`. GĐ −1 phải chạy lại phép quét này thành test CI.

---

## 3. Ba phương án và điểm chấm

Mỗi phương án do 2 giám khảo chấm độc lập: một người nhìn từ góc độ **một kỹ sư làm một mình + Vercel Hobby**, một người nhìn từ góc độ **bảo mật / phân quyền / B2B**.

| | A: một console, phân khu trong `aa-cis-frontend` | B: app riêng "Platform Console" (`console.lumiguides.it.com`) | C: hub `/hub` liên bang + AppSwitcher dùng chung |
|---|---|---|---|
| Điểm giám khảo 1 (solo/Hobby) | 7 | 4 | 6,5 |
| Điểm giám khảo 2 (bảo mật) | 7 | 7 | 7 |
| **Trung bình** | **7,0** | 5,5 | 6,75 |
| Vercel project mới | không | **có** (aa-console) + package kit | không |
| URL hiện có | giữ nguyên | dời nhiều trang | giữ `/admin`, dời spend/AI sang `/hub` |
| Thời gian tới trang staff đầu tiên | ~3,5–4,5 ngày (GĐ −1 + GĐ1 + GĐ2; con số ~2 ngày ban đầu chưa tính lỗ GET public và machine principal) | ~7–8 phiên | ~10–12 ngày công |
| Rủi ro chính | blast radius dồn vào một Vercel project (cả portal) | BFF + login + smoke suite x2; mâu thuẫn ADR 0006 | `/hub` cần thêm `matcher`; 3 nav model; landing đổi làm vỡ smoke |
| Phù hợp ADR 0006 | khớp (directory ở CIS admin) | cần amendment + ADR mới | khớp, cần ADR "federation" |

**Vì sao chọn A.** A rẻ nhất, không đổi URL, không thêm project, và hiện thực đúng chỗ ADR 0006 §3 đã định cho staff directory (CIS admin). B sạch hơn về lâu dài nhưng tốn khoảng 1,7–2 lần công cho cùng kết quả, lại thêm một frontend thứ tư phải giữ an toàn (giám khảo solo chấm 4). C gần A nhưng thêm prefix `/hub`: phải thêm `matcher` (sót là trang không có auth, lỗi loại AA-252 #5), có nav model thứ ba, và đổi landing làm vỡ `ui-smoke.spec.ts:134` cùng `aa752-shell.spec.ts:25`.

**Ý tưởng ghép vào A** (từ phần "steal" của các giám khảo; chi tiết ở §4–§7):

| Ý tưởng | Nguồn | Ở đâu |
|---|---|---|
| Danh sách staff **chỉ đọc** ra sớm (3a), ghi sau (3b) | giám khảo A1, C1 | §7 GĐ2 |
| Header khu trong sidebar thay cho AppSwitcher; Booking là một dòng link ngoài | A1, B1 | §4 |
| Project Playwright `smoke-reviewer` với tài khoản reviewer e2e | A1 | §7 GĐ4 |
| Apps health cắt về lát CIS-first (không đụng TP/Booking repo ở v1) | A1, C1 | §7 GĐ6 |
| `require_staff` verify **staff JWT** (Bearer); header chỉ để chuyển tiếp | A2, C2 | §5 |
| Lớp capability (`ROLE_PERMS` dùng chung backend + `rbac.ts`) | A2, B2, C2 | §5 |
| Tách quyền "quản lý người" (`staff.write`) khỏi "admin nội dung" | A2 | §5 |
| Audit chống sửa: trigger chặn UPDATE/DELETE + hash chain, **trên bảng `acp_shared.audit_log` có sẵn** (DM-2.4) | A2, B2, C2 | §5 |
| Route-policy test phủ cả `/v1/*` + nhánh staff của tenant proxy | A2, C1 | §5, §7 |
| Báo đổi quyền qua chuông in-app có sẵn (SNS e-mail để sau, vì task role CIS chưa có `sns:Publish`) | A2 (sửa sau phản biện) | §5 |
| `shared.staff_app_grant` (một dòng cho mỗi lần cấp) thay cột role theo app | B1, B2 | §5, §10 |
| Role CIS nullable để người chỉ dùng Booking không thấy nội dung CIS | C2 | §5, §10 |
| Registry app là file typed `lib/apps.ts`, không phải bảng DB | B1 | §6 |
| Deep link chỉ dựng từ registry, không có return-URL tự do, không gắn token | C2 | §6 |
| IAM read **giới hạn theo ARN**; không cấp `lambda:GetFunctionConfiguration` khi env Lambda còn chứa `ADMIN_SECRET` | B2 | §6, §9 |
| Hạ tài khoản E2E xuống chỉ đọc **trước** khi ship ghi staff (P1-2) | B2 | §7 |
| Tách PR Bearer thành 2 bước: dual-accept rồi cắt | C1 | §7 GĐ4 |
| Ghi sự kiện "support access" khi staff vào tenant | A2, B2 | §5, sau MVP |
| Đặt điều kiện kích hoạt việc tách portal khỏi `aa-cis-frontend` | A2 | §9, §10 |

---

## 4. Kiến trúc đích: sơ đồ thông tin

**Luật xếp trang:** một trang nằm ở khu của **người nó phục vụ**, không theo cách nó chạy. Platform là người, app, tenant (tài khoản), tiền và máy móc. CIS Content là những gì CIS sản xuất, kể cả QA output tenant (giữ luật *tenant-sees-content-only*).

**Shell (chỉ sửa `_kit`):**
- `NavGroup` thêm trường `section: "platform" | "cis"`. Sidebar vẽ **hai header khu thu gọn được** ("Platform", "CIS Content"). Header chỉ hiện khi role thấy cả hai khu, nên reviewer/content chỉ thấy CIS Content và trải nghiệm của họ không đổi.
- Booking là một dòng link ngoài ở cuối sidebar (mở tab mới, tooltip "đăng nhập riêng bằng tài khoản CIS cho tới khi có Cognito"). URL lấy từ registry `lib/apps.ts` dưới dạng **hằng số Dev**, giống `DEV_CIS_ADMIN_URL` bên Booking `lib/config.ts`, nên Dev không cần env var mới. Chỉ cần env khi có prod.
- Chỉ dựng AppSwitcher thật khi có khu nội bộ thứ ba hoặc khi đã có Cognito SSO.
- CommandPalette thêm tiền tố "Platform ›" / "CIS ›". Breadcrumb thành "<Khu> / <Trang>".
- BottomNav dựng từ nav model, lọc qua `canSeePage`, nên reviewer/content hết thấy Overview/Jobs.

```
AA Console (aa-cis.lumiguides.it.com)
│
├── PLATFORM  (admin; quyền chi tiết theo capability ở §5)
│   ├── Overview ............... /admin/overview  → AA-858 thành Ops overview (app strip, alarms, jobs, cost/budget)
│   ├── People & access
│   │   ├── Staff  [MỚI] ........ /admin/platform/staff, /admin/platform/staff/[id]   (AA-816)
│   │   ├── Audit log [MỚI] ..... /admin/platform/audit   (sau MVP)
│   │   └── Access matrix [sau] . render read-only từ ROLE_PERMS
│   ├── Tenants
│   │   ├── Tenants + Tenant 360  /admin/tenants   (giữ; nhận tab Tenant Info từ Settings)
│   │   │   └── Members [sau] .. tab trong Tenant 360 (AA-813)
│   │   └── Plans [sau] ......... /admin/platform/plans  (chỉ khi chị Thư chốt giá)
│   ├── Apps  [MỚI]
│   │   ├── Apps ................ /admin/platform/apps  (thẻ CIS / Booking / TripPlanner)
│   │   └── App detail .......... /admin/platform/apps/{cis|booking|tripplanner}
│   ├── Jobs ................... /admin/jobs  (giữ; sau thêm tab deploy-gate, retention)
│   ├── AI & spend
│   │   ├── External Spend ...... /admin/llm-usage  (giữ; sau thêm nhóm theo App tag)
│   │   ├── Jev Decisions ....... /admin/decisions  (giữ)
│   │   └── Platform settings [MỚI] /admin/platform/settings  (tab: LLM Models, Jev Credit, UI Kit)
│   └── Developer
│       └── API Docs ............ /admin/api-docs  (giữ)
│
├── CIS CONTENT  (role như hôm nay)
│   ├── Pipeline: Upload (S0) · Rewrite (S1) · Review Queue · Master Content
│   ├── Assets: Photos
│   ├── Intelligence: Social Content 01–05 · SEO Intelligence
│   ├── Tenant output: Content Trace (/admin/tenant-activity) · A4 Quality (/admin/platform-stats, đổi nhãn)
│   │                  · Content Quality (/admin/content-quality, thành mục nav riêng)
│   └── Content settings ...... /admin/settings  (chỉ còn Pipeline Gates, Brand Identity, SEO Config)
│
├── BOOKING ↗  (link ngoài → aa-booking-admin; app riêng, giữ nguyên 30+ trang)
└── TRIPPLANNER → /admin/platform/apps/tripplanner  (không xây admin riêng)
```

**Mỗi route hiện có đi đâu:**

| Route hiện tại | Đích | Đổi URL? |
|---|---|---|
| `/admin/overview` | Platform › Overview (funnel nội dung tách thành thẻ "Pipeline status" ở CIS khi làm AA-858) | không |
| `/admin/upload`, `/s1-rewrite`, `/review`, `/master-content` | CIS Content › Pipeline | không |
| `/admin/photos` | CIS Content › Assets | không |
| `/admin/atom-curation`, `/seo-intelligence` | CIS Content › Intelligence | không |
| `/admin/tenant-activity` | CIS Content › Tenant output ("Content Trace") | không |
| `/admin/platform-stats` | CIS Content › Tenant output, nhãn "A4 Quality" | không (có thể redirect sang `/admin/a4-quality` sau) |
| `/admin/content-quality` | CIS Content › Tenant output (mục riêng) | không |
| `/admin/tenants` | Platform › Tenants | không |
| `/admin/jobs` | Platform › Jobs | không |
| `/admin/llm-usage`, `/decisions` | Platform › AI & spend | không |
| `/admin/api-docs` | Platform › Developer | không |
| `/admin/settings?tab=models\|jev-credit\|ui-kit` | `/admin/platform/settings?tab=…` | **có**: `next.config` redirect với `has` query |
| `/admin/settings?tab=tenant` | Tenant 360 › Settings (kiểm trước: nếu là record AA_INTERNAL thì thành dòng "AA internal" ở Tenants) | **có**: redirect |
| `PAGE_RULES /admin/pipeline`, re-export `AdminSidebar.tsx` | xoá | — |

**Trang mới cần có** (theo thứ tự ưu tiên): Staff & roles (AA-816), Platform settings, Apps & health, Audit log, Ops overview (AA-858, dựng trên cùng aggregator với Apps), Plans (chờ chị Thư), Members trong Tenant 360 (AA-813).

`PAGE_RULES` chỉ cần thêm một rule `{prefix: "/admin/platform", roles: ["admin"]}`. Quyền chi tiết hơn do capability ở backend lo.

- **Không đụng `/admin/platform-stats`:** `pageRule()` và `navActive()` so khớp `prefix` hoặc `prefix + "/"`, nên rule `/admin/platform` không bắt nhầm `/admin/platform-stats` (đã đọc `rbac.ts:56-58`, `adminNav.tsx:61-64`).
- **BFF thì khác:** `API_WRITE_RULES` và `canWriteAdminPath` dùng `path.startsWith(prefix)` **không có dấu `/`**. Rule ghi cho route mới phải viết `"platform/"` (có `/`), nếu không sẽ bắt luôn các path backend bắt đầu bằng `platform…`. Khi BFF chuyển sang deny mặc định (GĐ4b) thì nên sửa luôn matcher này cho giống `pageRule`.

---

## 5. Mô hình staff và phân quyền

### 5.1 Vai trò và capability

- **Giữ 3 role CIS** (`admin`, `reviewer`, `content`) trong giai đoạn này. Không thêm role mới khi chưa có người thứ hai cần.
- **Thêm lớp capability** (một map `ROLE_PERMS` duy nhất, dùng cho cả backend và `lib/rbac.ts`, được snapshot trong test). Gợi ý tập ban đầu, bám pattern Booking `staff.py`:

| Capability | admin | reviewer | content | Ghi chú |
|---|:-:|:-:|:-:|---|
| `content.read` | ✓ | ✓ | ✓ | |
| `content.write` (upload, S1, regenerate) | ✓ | ✓ | ✓ | lấy từ route snapshot, không đoán |
| `review.act` | ✓ | ✓ | ✓ | |
| `master.admin`, `atoms.write`, `photos.write`, `a4.unpublish` | ✓ | | | |
| `content.settings.write` (gates, brand, SEO) | ✓ | | | Settings đọc cho mọi staff, ghi admin |
| `tenant.read`, `tenant.write` | ✓ | | | |
| `ops.read`, `ops.write` (jobs cancel/retry, deploy-gate) | ✓ | | | |
| `ai.admin` (model routes, catalog, Jev) | ✓ | | | |
| `spend.read`, `spend.write` (budgets) | ✓ | | | |
| `staff.read` | ✓ | | | |
| **`staff.write`** (đổi role/active) | chỉ người có cờ `owner` | | | Nghiệp + break-glass; xem §10 Q2 |
| `audit.read` | ✓ | | | |

Khi có người mới (ops, sales, content lead), chỉ cần thêm một dòng vào map và sau này là một Cognito group. Không phải sửa 20 router.

### 5.2 Kiểm quyền ở đâu

| Lớp | Hôm nay | Đích |
|---|---|---|
| Page (`middleware.ts` + `PAGE_RULES`) | allow-list, deny unlisted | giữ; thêm `/admin/platform` |
| BFF (`/api/admin/[...path]`) | mọi staff; ghi **cho mặc định** | `canWriteAdminPath` **deny mặc định**; allow-list ghi sinh từ route snapshot |
| Backend | phần lớn chỉ `verify_admin_secret`; 26 GET không kiểm gì; tin header `x-admin-role` | một dependency `staff_policy` gắn ở mức router (`dependencies=[…]`), **tra quyền theo `(method, route template)`** trong map `POLICY` (snapshot), áp cho **mọi** router `/admin/*`, `/v1/*` mà BFF gọi bằng secret, và nhánh staff của tenant proxy; **verify staff JWT Bearer** (GĐ4), đọc lại role + `is_active` từ DB (cache 30–60 s, xoá cache khi directory ghi) |
| CI | không có | test duyệt `app.routes`: route `/admin/*` nào không có dependency secret/policy thì fail (bắt lại đúng lỗ GĐ −1), route nào chấp nhận secret hoặc staff token mà thiếu policy thì fail. Chạy report-only trước, rồi enforcing; snapshot `(method, path) → perms` |

**Vì sao không gắn một quyền cho cả `APIRouter`.** Sáu router dùng `prefix="/admin"` trộn nhiều nhóm việc: `admin.py` (tenants và nhiều thứ khác), `admin_atoms`, `admin_pipeline`, `admin_llm_ops`, `admin_settings`, `admin_search`. Ví dụ `admin_llm_ops` có `GET /admin/llm-config`, mà trang S1 của reviewer/content cần đọc, nằm chung với `PATCH llm-config/{stage}` chỉ dành cho admin. Gắn `require_perm("ai.admin")` cho cả router sẽ làm hỏng S1. Vì vậy policy phải tra theo method + route.

**Machine principal phải có ngay từ GĐ1, không đợi GĐ4.** Hôm nay có ba nhóm gọi `/admin` bằng secret mà **không** gửi `x-admin-role`:
- CI `deploy-dev.yml`: preflight `GET /admin/job-runner/deploy-gate` (dòng 45); smoke `summary`, `deploy-gate`, `overview`, `workers` (dòng 249-292).
- Lambda scheduler `dfs_balance_check`: `POST /admin/dfs-balance/check`, `jev-canary/check`, `jev/402-sweep`, `waves/check`, `job-runner/retention/schedule`.
- Agent/Nghiệp curl tay để verify live (aa-ship).

Nếu `require_perm` coi "thiếu role" là từ chối, smoke sau deploy sẽ fail, preflight ở lần deploy kế tiếp nhận 403 nên `safe_to_deploy` rỗng, và **mọi deploy CIS bị chặn**. Luật từ GĐ1:
- secret **không** kèm role → principal `machine`, chỉ được gọi đúng allow-list path ở trên;
- secret **kèm** role → tin header như hôm nay (vẫn là god-key cho người giữ secret, cắt ở GĐ4);
- so sánh secret bằng `hmac.compare_digest` (P0-5).

### 5.3 Lộ trình định danh: `admin_users` + `ADMIN_SECRET` → staff JWT → Cognito

1. **Hôm nay:** HS256 24 h, dùng chung `JWT_SECRET` với tenant, không có `iss`/`aud`. Backend tin header. `verify-admin` không check lại `is_active`.
2. **Bước chuyển (MVP, chưa có Cognito):**
   - BFF chuyển tiếp `cis_admin_token` dưới dạng `Authorization: Bearer`. Backend verify và lấy actor/role từ claims cùng DB, **không** từ header.
   - Token staff có `aud=cis-staff` và `iss` riêng (hoặc dùng lại signer RS256 `booking_jwt`), nên token tenant bị từ chối bằng claim/key chứ không phải chỉ nhờ DB lookup trượt. TTL staff 8 h (P1-3).
   - `ADMIN_SECRET` thôi honour `x-admin-role`: lúc này secret chỉ còn là *machine principal* hẹp (principal này đã có từ GĐ1, xem §5.2). Như ADR 0006 quyết định, machine caller không có Cognito client.
3. **Cognito (ADR 0006 Phase 1, AA-703/AA-816):**
   - Trang Staff thành **writer duy nhất** của WORKFORCE users/groups (`AdminCreateUser`, Add/RemoveUserFromGroup, Disable → GlobalSignOut).
   - Có panel drift cho reconcile job (chỉ báo cáo, không tự sửa).
   - Tắt `LEGACY_ADMIN_LOGIN_ENABLED`, BFF thôi gửi `X-Admin-Secret`, rồi xoay secret.

### 5.4 Staff directory (AA-816)

- **Lát chỉ đọc (GĐ2) dùng cột có sẵn:** hôm nay `shared.admin_users` chỉ có `id`, `username`, `role`, `is_active`, `created_at`, `updated_at` (`db-schema-reference.md`, dump 16/10). Không có email, không có lần đăng nhập cuối. Trang GĐ2 vì thế khá mỏng: chỉ là danh sách + role + active + ngày tạo + link Booking. Như vậy là chấp nhận được, vì mục đích của GĐ2 là "thấy ai đang có quyền".
- **Migration CIS-owned (GĐ5):** `shared.admin_users` thêm `email` (unique, lower-case, check `@adventure.asia` khi có), `display_name`, `last_login_at`, và **`is_owner boolean NOT NULL DEFAULT false`**. Cờ `owner` của `staff.write` (§5.1) phải được lưu ở đâu đó; không dùng env var hay list id hard-code. Cột ADR 0006 (`cognito_sub`, `iss`) có thể thêm sớm mà chưa dùng. Migration đi theo luồng D8: file ở CIS, bản copy y hệt ở `infra/AA-CIS-Infra/db/migrations/cis/`, áp qua workflow **DB Migrate**. Như vậy là thêm **một PR Infra**. `db-schema-reference.md` do workflow DB Schema Dump của Infra tự regenerate và tự mở PR, không làm tay.
- **Quyền theo app:** đề xuất `shared.staff_app_grant (admin_user_id, app, role, granted_by, granted_at, revoked_at)` thay cho các cột role theo app trong ADR 0006. App mới không cần migration và có sẵn lịch sử cấp quyền. Việc này cần ADR 0006 amendment (§10 Q3).
- **Router `admin_staff.py`:** `GET` list/detail (`staff.read`), `PATCH {role, is_active, display_name, email}` (`staff.write`). Guard copy từ Booking `auth/admin.py`: không tự hạ quyền hoặc tự khoá mình, không gỡ admin active cuối cùng.
- **Tạo tài khoản / reset mật khẩu:** vẫn dùng `scripts/create_staff_user.py`. Chỉ làm UI tạo kèm temp password nếu Cognito trượt quá khoảng 4–6 tuần, vì ADR 0006 bỏ mật khẩu và cấm `AdminSetUserPassword`.
- **Role Booking:** chỉ hiện read-only. CIS không đọc thẳng `booking.staff_users` (ADR 0008). MVP dùng link "Open in Booking" → `aa-booking-admin/staff/{cisUserId}` (trang này có thật: `app/(staff)/staff/[cisUserId]`). Có thể làm sau: BFF mint booking-token cho admin đang thao tác rồi gọi `GET /booking/staff`.
- **Role CIS vẫn `NOT NULL` tới khi có Cognito** (đổi khuyến nghị Q4). Lý do: cầu nối Booking hiện tại dựa vào role CIS. Booking `auth/staff.py` suy role Booking từ `claims.cis_role` qua `ROLE_FROM_CIS`, và `middleware.ts` của CIS đá mọi role không thuộc `isStaffRole` về `/login`. Nếu cho role CIS nullable trước Cognito thì phải sửa cả hai app, trong khi ADR 0006 sẽ thay hẳn cơ chế này bằng `cognito:groups`.
- **Tenant members (AA-813):** là tab trong Tenant 360, không nằm trong People, để định danh staff và tenant tách nhau.

### 5.5 Audit

- **Không tạo bảng audit mới.** Data standards DM-2.4 / KEY-9 quy định mỗi owner có một bảng `<schema>.audit_log` append-only, không có bảng audit cấp hệ sinh thái. Bảng của CIS là `acp_shared.audit_log`, đã có `actor`, `actor_type`, `action`, `resource_type`, `resource_id`, `details jsonb`, `created_at`; `admin.py` đã ghi `actor = "admin:<uuid>"` vào đó. Bản thiết kế trước đề xuất `shared.admin_audit_event`, như vậy là trái chuẩn. Cách đúng: migration CIS thêm vào `acp_shared.audit_log` các cột `prev_hash`, `http_method`, `route`, `status`, và một giá trị `actor_type` cho staff nếu enum chưa có. `before/after` của thay đổi directory nằm trong `details`.
- `actor` lấy từ token đã verify (GĐ4). Trước GĐ4 thì lấy từ `x-admin-user-id`, và phải ghi rõ giới hạn đó trong code.
- Một FastAPI dependency ghi mọi request **khác GET** vào `/admin`, `/v1` (staff). Các sự kiện login, booking-token mint và support access vào tenant cũng được ghi.
- **Chống sửa:** `REVOKE UPDATE, DELETE` **không đủ**, vì runtime đang chạy bằng `aa_cis_admin`, role sở hữu mọi object. Cần thêm trigger `BEFORE UPDATE OR DELETE … RAISE` cùng hash chain. Phải ghi rõ rằng `aa_cis_admin` vẫn bypass được cho tới khi AA-817 D2 đưa runtime sang `cis_app`. Kiểm trước khi bật trigger: không có job retention nào xoá `acp_shared.audit_log`; nếu có thì phải đổi sang archive theo DM-7.3. Bản export lên S3 Object Lock thuộc P1-7.
- **Báo động:** đổi role, đổi `is_active`, hoặc chạm guard last-admin thì bắn **chuông in-app** có sẵn (sự kiện `platform.*`, giống `platform.dfs_balance.low`) và ghi một dòng structlog. Không publish thẳng lên SNS `aa-cis-dev-acp-alerts`, vì task role ECS của CIS **không có `sns:Publish`** (Infra chỉ cấp cho Lambda). Muốn có e-mail thì sau này làm metric filter trên dòng log đó, đổ vào topic có sẵn (một PR Infra, ≈ 0,30 USD/tháng).

---

## 6. Quản lý app con

**"Quản lý app" ở đây nghĩa là quan sát và dẫn đường, không phải deploy.** Deploy vẫn đi qua CI (aa-ship). Console không có nút deploy, start/stop/scale, và không giữ Vercel token, GitHub token hay AWS write token.

### 6.1 Registry

File typed `frontend/lib/apps.ts` (là code, không phải bảng DB, đúng ADR 0008 §5). Mỗi app: `{id, name, adminUrl, apiBase, healthPath, readyPath, ecsServices[], lambdas[], vercelProject, costTag, ownerRepo, deepLinks}`. Thêm app thứ tư (ví dụ tenant CRM) bằng một PR. ADR 0004 decision 9 (`/health` + `/health/ready` có `git_sha`) trở thành hợp đồng chung cho mọi app.

### 6.2 Health, version, deploy

| App | Có sẵn | Cần thêm | Đọc thế nào |
|---|---|---|---|
| CIS | `/health` (version cứng `0.3.0`), `/admin/job-runner/workers`, `/deploy-gate` (chưa có UI) | `GIT_SHA` env trong task def (CI), `/health` trả `git_sha`, `/health/ready`, worker heartbeat có sha | in-process; so parity api vs worker (thay cho bước kiểm tay ở đầu phiên) |
| Booking | `/booking/health` (`git_sha`), `/booking/health/ready` (`schema_version`) | không | HTTP từ backend CIS, timeout 2 s, lỗi thì hiện "unknown" |
| TripPlanner | không có gì | (sau MVP) `GET /browse/health` + `GIT_SHA` env khi deploy Lambda | v1: chi tiêu `tp_*` hôm nay so với cap 5 USD (giá trị mặc định trong `backend/config.py` của TripPlanner), lấy từ `shared.llm_call_log` (CIS-owned) với điều kiện `stage LIKE 'tp\_%'`. Bảng này **không có cột `app`**. **Không** đọc `tripplanner.llm_spend_daily` |
| Frontends | — | (sau MVP) route `/api/version` trả `VERCEL_GIT_COMMIT_SHA` | link-out tới Vercel project |
| Alarms | 1 SNS e-mail topic | (sau MVP) `cloudwatch:DescribeAlarms`, nhóm theo prefix | IAM read **giới hạn theo resource** trên task role CIS |

- **Backend:** `api/routers/admin_platform.py` (`ops.read`) gồm `GET /admin/platform/apps` và `/apps/{app}`. Kết quả cache 60 s trong Redis có sẵn.
- **UI:** tải một lần khi mở trang và có nút Refresh. **Không poll**, vì Fluid CPU đã ở mức 52% (bài học S240).

### 6.3 Liên kết sâu sang Booking admin

- Booking giữ app riêng. Lý do: stack riêng (Next 16 `proxy.ts`, kit `ui/`, BFF, RBAC deny-by-default), 30+ trang, và nếu gộp thì một deploy lỗi có thể làm sập cả admin, portal lẫn Booking.
- Booking PR (GĐ5) **dùng lại** `ManagedInCisLink` (`ui/booking/FromCis.tsx`, đã nhận `path`) trên trang `app/(staff)/staff/[cisUserId]`, với `path={"/admin/platform/staff/" + cisUserId}`, ngay cạnh dòng "managed in CIS admin". Không sửa component. Trang `/staff` thêm link "Open CIS staff". Như vậy câu "managed in CIS admin" có trang thật để mở.
- Deep link chỉ được dựng từ registry: không có return-URL tự do (tránh open redirect), không gắn token. `?from=cis` chỉ để hiện breadcrumb "Back to".
- Chỉ xét gộp vào một hostname (Next.js multi-zones, không port code) **sau** Cognito SSO, và chỉ khi việc dùng hai tab gây khó cho người dùng thật.

### 6.4 TripPlanner ops

TripPlanner **không bao giờ có admin riêng**. Trang `/admin/platform/apps/tripplanner` hiện các mục sau:
- chi tiêu so với cap;
- route model `tp_*` (link sang Platform settings › LLM Models);
- (sau, GĐ9) giá trị flag `PLACES_SOURCE`, đọc **qua `/browse/health`** khi TripPlanner trả nó ra. Không đọc qua `lambda:GetFunctionConfiguration`, vì lệnh đó trả cả env Lambda (§9);
- (sau) alarm Lambda và `git_sha`.

Hai việc chỉ ghi backlog: metric filter cho `evt=search_embed outcome=fallback` (≈ 0,30 USD/tháng/metric) và view inquiry pipeline (outbox lag, inbox parked), vốn cần Booking/TripPlanner công bố endpoint đọc trước.

---

## 7. Lộ trình theo giai đoạn nhỏ

Mỗi giai đoạn gồm 1–2 PR theo trunk-based (branch → PR → CI → Nghiệp merge), commit `feat|fix|chore: …` + `Refs AA-xxx`. **Không phá UI smoke:** URL giữ nguyên, PR nào đổi đường dẫn hoặc landing thì sửa spec smoke trong **cùng PR**. Các PR frontend được gom để mỗi giai đoạn chỉ tốn 1–3 deploy.

| GĐ | Nội dung | PR | Issue | Công |
|---|---|---|---|---|
| **−1** | **Vá 26 GET `/admin/*` public (P0, phản biện):** gắn `dependencies=[Depends(verify_admin_secret)]` ở mức router cho `admin_job_runner`, `admin_llm_ops`, `admin_budgets`, `admin_photos`, `admin_segment_research` (route nào đã tự gọi secret thì vẫn chạy bình thường). **Không** gắn vào `public_router` của `admin_photos.py` (`/content/photos/{id}`, ảnh public cho tenant/Booking). So sánh secret bằng `hmac.compare_digest`. **Cùng PR**, sửa `deploy-dev.yml:292` để smoke `workers` gửi `x-admin-secret`. Thêm test CI: mọi route `/admin/*` (trừ allow-list công khai rỗng) phải có dependency secret/policy. Verify live: curl không header thì 403, curl có secret thì 200, smoke deploy xanh. Không đổi FE (BFF đã luôn gửi secret). | 1 API | *P1-3 authz* (PR đầu tiên) | 0,5 ngày |
| **0** | **IA + dọn dẹp (chỉ FE, không đổi quyền):** `section` trong nav, header khu Platform / CIS Content, nhóm "Tenant output", Content Quality thành mục riêng, đổi nhãn "A4 Quality", BottomNav lọc theo role, xoá `/admin/pipeline` + `AdminSidebar`, dòng link Booking. Gate Settings theo tab ở UI cho non-admin (tạm thời). | 1 FE | *mới: Admin IA* | 1–1,5 ngày |
| **1** | **Authz backend phần 1 (P0-5):** `api/core/staff_authz.py` (`ROLE_PERMS`, `POLICY` theo `(method, route)`, dependency `staff_policy`, principal `machine` với allow-list cho CI + Lambda scheduler, §5.2), route-policy test report-only + snapshot. Áp **chỉ cho route ghi** tiền/model: `PATCH llm-config/{stage}` và các route ghi model/catalog/Jev trong `admin_llm_ops`, `PUT budgets`, cancel/retry/retention của `admin_job_runner`, `PUT` của `admin_decisions`, ghi của `admin_settings`. Mọi GET vẫn mở cho mọi staff (S1 cần `GET llm-config`). Role đọc từ `x-admin-role` (BFF chuyển tiếp từ JWT đã verify) cho tới GĐ4. **Verify sau deploy:** smoke CI xanh, preflight lần deploy kế tiếp vẫn xanh, Lambda scheduler chạy được (invoke tay một lần, xem log), reviewer test bị 403 khi `PATCH llm-config`. | 1 API | *mới: P1-3 server-side staff authz*; AA-816 | 1,5–2 ngày |
| **2** | **Staff chỉ đọc (AA-816 lát 3a):** `admin_staff.py` `GET /admin/platform/staff`, `/admin/platform/staff/{id}` (`staff.read`) trên các cột có sẵn (`username`, `role`, `is_active`, `created_at`, `updated_at`); trang `/admin/platform/staff` (kit DataTable + Drawer) có link "Open in Booking"; `PAGE_RULES /admin/platform`; `API_READ_RULES` thêm `{prefix: "platform", roles: ["admin"]}`. `canReadAdminPath` so khớp `prefix` hoặc `prefix + "/"`, nên rule này không bắt `platform-stats`. Mục đích là để reviewer/content không đọc được danh sách staff qua BFF. | 1 API + 1 FE | AA-816 | 1,5–2 ngày |
| **3** | **Authz backend phần 2:** áp cho các router còn lại (`admin.py`, pipeline, atoms, a4, photos, waves, places, segment_research, tenant360, seo, overview, dashboard, search, trip-pages, master writes) + `/v1/*` mà BFF gọi bằng secret + nhánh staff của tenant proxy; test chuyển **enforcing**. Smoke tay trên Dev bằng reviewer test. | 1–2 API | *P1-3* | 2–3 ngày |
| **4** | **Staff JWT + deny mặc định:** (4a) backend chấp nhận **cả** Bearer staff JWT (`aud=cis-staff`, TTL 8 h) **lẫn** secret + header, `verify-admin` check lại `is_active`; (4b) BFF chuyển sang Bearer, `canWriteAdminPath` deny mặc định với allow-list sinh từ snapshot; thêm Playwright project `smoke-reviewer` (tài khoản reviewer e2e, chỉ lưu tên secret). | 2 (API, FE) | *P1-3*; P1-2 | 2–3 ngày |
| **5** | **Audit + staff ghi (AA-816 lát 3b):** migration CIS (`admin_users`: email, display_name, last_login_at, `is_owner`; `acp_shared.audit_log`: `prev_hash`, `http_method`, `route`, `status` + trigger chặn UPDATE/DELETE) qua luồng D8 (bản copy ở Infra, workflow DB Migrate); dependency ghi non-GET; `PATCH` role/active với guard + chuông in-app; `API_WRITE_RULES` thêm `"platform/"` → admin; Booking PR: dùng lại `ManagedInCisLink` trên `staff/[cisUserId]`. **Gate:** tài khoản E2E đã hạ xuống chỉ đọc (P1-2). | 1 API + 1 FE + 1 Infra (copy migration) + 1 Booking | AA-816; P1-7 | 3–4 ngày |
| **6** | **Tách Settings:** `/admin/platform/settings` (dùng lại ModelsTab, JevCreditTab, SettingsKitTab không sửa), Tenant Info → Tenant 360, redirect `?tab=`; sửa entry `settings-models` trong `ui-smoke.spec.ts` sang URL mới và giữ một assert rằng link cũ vẫn redirect. | 1 FE | *Admin IA* | 0,5–1 ngày |
| — | **MỐC MVP** (GĐ −1…6), cộng dồn ≈ 13,5–17,5 ngày công kể cả verify (lõi "staff + nav sạch" ≈ 8–11 ngày, phần còn lại là authz bắt buộc theo S241). Với một người còn phải làm việc CIS, đây là **2–3 tuần lịch**, không phải một tuần. Dừng lại để Nghiệp xét ưu tiên so với việc CIS. | | | |
| 7 | **Apps & health lát CIS-first:** `GIT_SHA` vào task def + `/health` `git_sha` + `/health/ready`; `admin_platform.py` (workers, parity, deploy-gate, Booking `/booking/health*`, chi tiêu TP từ `llm_call_log`); trang `/admin/platform/apps`. | 1 API(+CI) + 1 FE | *mới: Apps & health*; AA-858 dựng trên đây | 2–3 ngày |
| 8 | **Audit view:** `/admin/platform/audit` (đọc `acp_shared.audit_log`, link sang Booking `/audit-log`). | 1 FE(+API) | P1-7 | 1–2 ngày |
| 9 | **Mở rộng health:** TP `/browse/health` + `GIT_SHA` Lambda (Nghiệp merge TP), `/api/version` trên 3 frontend, `cloudwatch:DescribeAlarms` (Infra PR, ARN/prefix-scoped). | 3–4 (nhiều repo) | *Apps & health* | 2–3 ngày |
| 10 | **Cost theo app:** Cost Explorer `GroupBy TAG App` trong job lưu trữ, External Spend thêm bộ lọc App, hiện riêng spend "untagged". | 1 API + 1 FE | *mới: per-App cost* | 1,5–2 ngày |
| 11 | **Overview → Ops overview:** thẻ app, alarm, jobs, cost/budget; funnel nội dung chuyển sang thẻ CIS. | 1 FE(+API) | AA-858 (chờ chị Thư) | 1–2 ngày |
| 12 | **Cognito Phase 1/2:** directory thành writer của Cognito, drift panel, cắt login cũ, xoay `ADMIN_SECRET`, Booking đọc `cognito:groups`. | epic | AA-703, AA-816, AA-811 | XL, ngoài ước tính |
| sau | Tenant members (AA-813) trong Tenant 360; plan catalog; tính năng khách hàng của AA-680; kit dùng chung (AA-655) để Booking và CIS trông như nhau. | | AA-813, AA-680, AA-655 | — |

**Thứ tự cứng:** GĐ −1 trước tất cả. GĐ1 → GĐ2 (route staff mới có guard ngay từ đầu). GĐ3 + GĐ4 + gate E2E (P1-2) phải xong → GĐ5 (ghi staff). GĐ0 và GĐ6 chỉ đụng FE, có thể chạy song song với GĐ1–GĐ4 (agent làm được). GĐ7–GĐ11 độc lập với nhau. GĐ −1, GĐ1, GĐ3, GĐ4a là PR backend, nên phải theo luật deploy-gate: không merge khi `shared.job` còn job hoặc đang có wave.

**Tuần này (cắt cho một người + agent):**

| Việc | Công | Vì sao trong tuần |
|---|---|---|
| GĐ −1 vá GET public | 0,5 ngày | P0, lộ dữ liệu job/chi tiêu ra internet; PR nhỏ, ít rủi ro |
| GĐ1 authz route ghi tiền/model + machine principal | 1,5–2 ngày | P0-5 S241; là nền cho mọi route `/admin/platform/*` |
| GĐ2 trang Staff chỉ đọc | 1,5–2 ngày | thứ Nghiệp thấy được ngay; không đổi quyền ai |
| *(làm thêm nếu còn sức)* GĐ0 nav phân khu | 1–1,5 ngày | chỉ FE, agent làm song song; gom vào **một** deploy cùng FE của GĐ2 nếu kịp |

Tổng ≈ 3,5–4,5 ngày công trong tuần vẫn có việc CIS (memory "CIS first"). Nếu tuần chỉ còn 2 ngày thì làm GĐ −1 + GĐ1 trước, GĐ2 sang tuần sau. Không kéo GĐ3–6 vào tuần này.

**Issue mới đề xuất (chỉ liệt kê, hỏi Nghiệp trước khi tạo):**
1. *chore: server-side staff authz for all admin routes + route-policy test* (P1-3 + P0-5; PR đầu tiên là GĐ −1 vá GET public; gồm machine principal, Bearer staff JWT, deny mặc định ở BFF).
2. *feat: admin IA — Platform / CIS Content sections + Settings split*.
3. *feat: platform apps & health page (CIS-first slice)*.
4. *feat: append-only staff audit on acp_shared.audit_log + audit view* (P1-7, phần CIS).
5. *chore: reviewer e2e account + smoke-reviewer project* (gắn P1-2).
6. *feat: per-App cost grouping in Cost Explorer job*.
7. *docs: ADR 0006 amendment — staff_app_grant, booking-content_creator group, platform capabilities*.

---

## 8. Chi phí và vận hành

**Vercel (Hobby):**
- **Không thêm project.** Mọi thứ nằm trong `aa-cis-frontend`. Booking chỉ thêm một chỗ dùng `ManagedInCisLink` trên trang staff (GĐ5), tức một PR và một lần deploy `aa-booking-admin`.
- **Đếm theo lần push, không theo PR.** Mỗi lần push vào nhánh có đổi `frontend/**` là một preview deploy. Vòng Kiro "tự lặp tới khi preview xanh" có thể đốt 5–10 deploy cho một PR. Ước tính thật cho cả lộ trình: 8–12 PR FE (cộng 1 Booking, 1–2 TripPlanner ở GĐ9), mỗi PR 2–5 push, tức khoảng 25–60 deploy rải trên vài tuần. Vẫn xa ngưỡng ~100/24 h nếu: build + lint + test FE ở local trước khi push, không mở song song nhiều PR FE trong cùng một ngày, và PR backend (GĐ −1, 1, 3) không đụng `frontend/**`.
- Ngưỡng deploy tính chung cả team (CIS + Booking + TripPlanner), nên ngày nào có wave UI bên Booking thì dời PR FE của console sang hôm khác.
- **Không poller mới.** Aggregator chạy trên ECS, nên Fluid Active CPU (đang ở 52%) không tăng.

**AWS (không thêm dịch vụ):**
- `DescribeAlarms`: gọi tối đa một lần mỗi 60 s và chỉ khi có admin đang xem, nằm trong free tier.
- Cost Explorer GroupBy TAG: khoảng 0,01 USD/request, gom vào job hằng ngày, ≈ 0,30–1 USD/tháng.
- Bảng audit trên RDS có sẵn: vài nghìn dòng/tháng, không đáng kể.
- (tuỳ chọn, sau) metric filter TripPlanner: ≈ 0,30 USD/tháng/metric. Metric filter cho cảnh báo đổi quyền staff (§5.5) tính giá tương tự.
- GĐ −1 → GĐ11 không tạo resource AWS mới. Chỉ có một IAM statement (`DescribeAlarms`, GĐ9) và có thể một metric filter.
- Cognito (GĐ12): staff MAU nằm trong free tier 10.000 MAU, nhưng **không bằng 0**. ADR 0006 (mục Costs) tính WAF cho hai pool khoảng **12–15 USD/tháng**, cộng SES ≈ 0,10 USD/1.000 mail và Plus tuỳ chọn ≈ 0,62 USD/tháng. Theo memory "cost before new AWS services", phải báo con số này với Nghiệp trước khi apply Infra #105.

**Vận hành:**
- Bớt việc tay: kiểm parity SHA api/worker, tạo/khoá staff qua ECS exec + script, invoke Lambda để xem TripPlanner còn sống không.
- Thêm việc: cập nhật snapshot route-policy khi thêm route (CI sẽ nhắc), một IAM statement trong Terraform.

**Bước tay của Nghiệp:**
- Trên Dev **không cần env var mới**. URL Booking admin nằm trong `lib/apps.ts` dưới dạng hằng số Dev, còn Booking đã có hằng số `DEV_CIS_ADMIN_URL`. ⚠️ Khi có prod, mọi biến env có dấu gạch dưới (URL Booking admin, URL CIS admin) do Nghiệp sửa tay trong VSCode hoặc Vercel dashboard, agent không tự sinh.
- Bật cost allocation tag `App` trong Billing nếu chưa bật.
- Merge PR TripPlanner.
- Tiền đề Cognito: Infra #105, AA-811 SES.

---

## 9. Rủi ro và những gì KHÔNG nên làm

**Rủi ro:**

| Rủi ro | Giảm thiểu |
|---|---|
| 26 GET `/admin/*` đang public, lộ payload/result/error của job, cấu hình model, chi tiêu, budgets | GĐ −1 trước mọi việc khác; test CI quét route để lỗ này không quay lại |
| PR authz khoá luôn đường deploy: smoke CI, preflight deploy-gate, Lambda scheduler gọi bằng secret không kèm role, nên nhận 403 và mọi deploy CIS sau đó bị chặn | principal `machine` + allow-list ngay từ GĐ1 (§5.2); sửa `deploy-dev.yml` trong cùng PR; verify sau deploy gồm cả lần deploy kế tiếp và một lần invoke Lambda |
| `require_perm` gắn nguyên router làm hỏng S1 (`GET llm-config`) và các route trộn trong router prefix `/admin` | policy tra theo `(method, route)`; GĐ1 chỉ đụng route ghi |
| Deny mặc định hoặc capability quá hẹp làm hỏng flow thật của reviewer/content (approve, regenerate, upload, S1, GET llm-config ở S1, polling job) | allow-list sinh từ route snapshot; test report-only trước; dual-accept rồi mới cắt; `smoke-reviewer` thành check bắt buộc trước GĐ4b |
| Ai giữ `ADMIN_SECRET` vẫn mạo danh được admin cho tới GĐ4; secret nằm ở 6 nơi, có cả env Lambda plaintext (`dfs_balance.tf:161`) | GĐ4 thu secret về machine principal hẹp; P1-2 bỏ secret khỏi env Lambda; xoay secret sau GĐ4 và lần nữa sau Cognito |
| Audit bị sửa hoặc bị giả actor | actor lấy từ token đã verify; trigger + hash chain; nói rõ giới hạn khi runtime còn là `aa_cis_admin` |
| Blast radius: admin, Platform và portal tenant dùng chung một Vercel project | không đụng layout `(tenant)`; smoke `/portal` chạy ở mọi PR FE; đặt điều kiện tách portal (§10 Q8) |
| Lệch từ vựng role: Booking có `content_creator` nhưng Infra #105 không có group tương ứng; CIS `CONTEXT.md:463` sai | role Booking chỉ read-only trong CIS cho tới GĐ12; sửa ADR 0006 + #105 trước khi apply |
| Lối tắt đọc chéo schema (`booking.*`, `tripplanner.*`) | chỉ dùng HTTP health, `shared.llm_call_log` và link-out; contract view chỉ khi app chủ sở hữu công bố |
| Cấp IAM describe cho task role CIS làm lộ secret (`GetFunctionConfiguration` trả về env) | không cấp quyền này; lấy SHA qua `/health` hoặc tag; mọi grant read đều giới hạn theo ARN/prefix |
| Người dùng tưởng Booking là một phần của console (phải đăng nhập lần hai) | gắn nhãn link ngoài, mở tab mới, có tooltip |
| Phần Platform phình ra, lấn việc CIS (memory: CIS first) | mốc MVP rõ ràng; GĐ7+ là các dòng backlog riêng |

**KHÔNG nên làm:**
1. Ship bất kỳ endpoint **ghi** staff hoặc Cognito nào khi backend còn tin `x-admin-role` từ `ADMIN_SECRET`.
2. Tách Platform ra Vercel project hoặc app thứ tư lúc này (phương án B). Chỉ xét lại khi có người thứ hai phụ trách nền tảng hoặc sau Cognito SSO.
3. Gộp hoặc port Booking admin vào kit CIS.
4. Xây admin riêng cho TripPlanner.
5. Nút deploy, start/stop/scale, log viewer, hay lưu Vercel/GitHub/AWS write token trong console.
6. Đọc thẳng `booking.*` / `tripplanner.*` từ CIS.
7. Đổi URL nội dung CIS hàng loạt, hoặc đổi landing của admin mà không sửa smoke trong cùng PR.
8. Viết lại toàn bộ auth trước Cognito (S241 §7 #10). Chỉ vá tới mức staff JWT + capability.
9. Làm UI tạo staff / reset mật khẩu khi Cognito còn gần, vì sẽ thành việc vứt đi.
10. Thêm poller cho trang Apps/Overview.
11. Đưa QA, gate hay held items ra portal tenant (luật *tenant-sees-content-only*). Trang Platform (Staff, Apps, Audit, spend) cũng không bao giờ được link từ `/portal`. `PAGE_RULES /admin/platform` chỉ cho `admin`, không có `tenant`.
12. Tạo bảng audit mới (`shared.admin_audit_event` hay tương tự). Phải dùng `acp_shared.audit_log` (DM-2.4).
13. Gắn một quyền cho cả `APIRouter` có prefix `/admin` dùng chung, hoặc coi "secret không kèm role" là bị từ chối khi chưa có allow-list machine.
14. Cho role CIS nullable trước Cognito (gãy cầu nối Booking `ROLE_FROM_CIS`).

---

## 10. Câu hỏi cần Nghiệp quyết

| # | Câu hỏi | Phương án | Khuyến nghị |
|---|---|---|---|
| Q1 | Chốt hướng tổ chức | A một console phân khu · B app console riêng · C hub `/hub` | **A** (điểm cao nhất, rẻ nhất, khớp ADR 0006) |
| Q2 | Ai được đổi quyền người khác (`staff.write`)? | (a) mọi admin · (b) chỉ cờ `owner` (Nghiệp + break-glass) · (c) role `platform-admin` mới | **(b)** ngay bây giờ; thành group Cognito `platform-admin` trong amendment ADR 0006 |
| Q3 | Lưu quyền theo app thế nào? | (a) cột role theo app (ADR 0006 hiện tại) · (b) bảng `staff_app_grant` | **(b)**: app mới không cần migration, có lịch sử cấp quyền; ghi vào amendment |
| Q4 | Người chỉ làm Booking (sales/contracting) có cần role CIS? | (a) giữ `role NOT NULL` · (b) role CIS nullable / theo grant | **(a) tới Cognito, (b) sau Cognito** (đổi sau phản biện). Trước Cognito, Booking suy role từ `cis_role` (`ROLE_FROM_CIS`), nên role CIS null sẽ làm gãy đăng nhập Booking. Tạm thời cho người chỉ làm Booking role `reviewer`, vì `reviewer` → `sales` |
| Q5 | `content_creator` của Booking | (a) thêm group `booking-content_creator` vào Infra #105 · (b) bỏ role này | **(a)**, sửa trước khi apply #105 |
| Q6 | UI tạo staff / reset mật khẩu trước Cognito? | (a) có · (b) không, vẫn dùng script | **(b)**, trừ khi Cognito trượt quá khoảng 4–6 tuần |
| Q7 | Tạo các issue mới ở §7 không? Gắn project nào? | tạo cả 7 · gộp thành 3 (authz, IA+staff, apps/audit/cost) | **gộp 3**, vì quota 100 issue/project |
| Q8 | Khi nào tách portal tenant khỏi `aa-cis-frontend`? | không bao giờ · khi có tenant trả tiền đầu tiên · khi lên Vercel Pro | **khi có tenant ngoài trả tiền đầu tiên** (trùng với mốc P0-B) |
| Q9 | Overview: khi làm AA-858 có chuyển funnel nội dung sang thẻ CIS? | có · giữ trộn | **có**, sau khi chị Thư chốt ưu tiên AA-858 |
| Q10 | Thứ tự so với việc CIS đang chạy | làm cả GĐ −1…6 liền · xen kẽ | **xen kẽ**: tuần này GĐ −1 + GĐ1 + GĐ2 (GĐ0 nếu còn sức, xem bảng "Tuần này" ở §7); GĐ3–6 trong 2–3 tuần sau, xen với việc CIS |
| Q11 | Vá 26 GET public ngay (GĐ −1), trước cả việc chốt Q1? | có · đợi chốt cả kế hoạch | **có**: lỗ này không phụ thuộc phương án A/B/C, và PR chỉ đụng backend |

---

## Liên hệ với báo cáo SDLC S241

| Mục SDLC | Nội dung | Ở kế hoạch này |
|---|---|---|
| **(mới, ngoài SDLC)** | 26 GET `/admin/*` không kiểm secret, public trên internet | GĐ −1 + test quét route; nên ghi bổ sung vào báo cáo SDLC S241 như một mục P0 |
| **P0-5** | backend không check role trên route ghi nhạy cảm (llm-config, budgets, job-runner) | GĐ1: `require_perm` ở cấp router cho nhóm tiền/model trước |
| **P1-3** | RBAC staff chỉ ở BFF; HS256 dùng chung staff/tenant; test route-policy; verify JWT staff; TTL 8 h | GĐ1, GĐ3, GĐ4: capability ở mọi router `/admin` + `/v1` + tenant proxy, test enforcing, Bearer staff JWT `aud=cis-staff`, TTL 8 h, BFF deny mặc định |
| **P1-2** | `ADMIN_SECRET` ở 6 nơi (có env Lambda plaintext); tài khoản E2E là admin đầy đủ | gate trước GĐ5: E2E chỉ đọc; không cấp `GetFunctionConfiguration`; thu secret về machine principal (GĐ4), xoay secret sau GĐ4 và GĐ12 |
| **P1-7** | không có audit thống nhất cho thao tác staff/tenant | GĐ5 mở rộng `acp_shared.audit_log` thành append-only (trigger + hash chain) + chuông in-app; GĐ8 audit view; export Object Lock thuộc P1-7 hạ tầng |
| **P0-5** (phần secret) | so sánh secret không constant-time | GĐ −1: `hmac.compare_digest` |
| **P0-10** | login không giới hạn, không lockout | ngoài phạm vi trang; nhắc rằng trang Staff càng cần P0-10 + MFA (Cognito) |
| **§7 #10** | không viết lại auth trước ADR 0006 Phase 1 | chỉ vá tới staff JWT + capability, rồi đi thẳng sang Cognito (GĐ12) |
| **ADR 0006 Phase 1** | directory CIS là writer Cognito duy nhất | trang `/admin/platform/staff` chính là nơi đó; GĐ12 chỉ đổi backend writer |

---

## 11. Phản biện đã xử lý

Một vòng phản biện hai vai: (1) kỹ sư làm một mình, thực dụng; (2) bảo mật. Mọi điểm đều được đối chiếu với code (CIS `cafd13a8`, Booking `dc51c8b`, Infra working tree) và với probe live **chỉ đọc** (GET không header tới `api-cis.lumiguides.it.com`, 17/10). Không đổi code, không tạo issue.

### 11.1 Điểm đúng, đã sửa trong file

| # | Vai | Phát hiện | Bằng chứng | Đã sửa ở |
|---|---|---|---|---|
| R1 | Bảo mật | **26 GET `/admin/*` không kiểm secret**, public trên internet (job list có `payload`/`result`/`error`/`created_by`; llm-config, chi tiêu, budgets, photos). Bản trước ghi sai rằng "mọi router `/admin` chỉ `verify_admin_secret`". Báo cáo SDLC S241 cũng chưa ghi lỗ này. | Quét AST `api/routers/admin_*.py`; 14 route đã curl không header và nhận 200 | §1, §2, §7 GĐ −1, §9, bảng SDLC, Q11 |
| R2 | Bảo mật + solo | `require_perm` mà coi "thiếu role" là từ chối thì sẽ khoá CI: smoke `deploy-dev.yml:249-292`, preflight deploy-gate dòng 45, và 5 POST của Lambda `dfs_balance_check` đều gửi secret mà không gửi `x-admin-role`. Kết quả là mọi deploy CIS sau đó bị chặn. Ngoài ra smoke đang gọi `/workers` không secret. | `deploy-dev.yml`, `lambda_src/dfs_balance_check/handler.py` | §5.2 (machine principal từ GĐ1), §5.3, GĐ −1/GĐ1, §9 |
| R3 | Solo | "`require_perm` ở cấp `APIRouter`" không làm được: 6 router dùng chung prefix `/admin`, và `admin_llm_ops` trộn `GET llm-config` (S1 của reviewer/content cần) với `PATCH` admin-only | `main.py:207-249`, khai báo `APIRouter(prefix=…)` | §5.2 (policy theo method + route), GĐ1 chỉ áp cho route ghi |
| R4 | Chuẩn dữ liệu | `shared.admin_audit_event` trái DM-2.4 / KEY-9 (mỗi owner một `audit_log`, không có bảng audit cấp hệ sinh thái). CIS đã có `acp_shared.audit_log`, và `admin.py` đang ghi vào đó | `02-data-management.md` DM-2.4; `db-schema-reference.md:473` | §3, §5.5, GĐ5, GĐ8, issue #4, KHÔNG #12 |
| R5 | Chi phí / IAM | Báo động qua SNS: task role ECS của CIS không có `sns:Publish` (Infra chỉ cấp cho Lambda), nên "≈ 0 USD" thực ra kèm một PR Infra ẩn | grep `sns:Publish` trong Infra | §5.5 (dùng chuông in-app + structlog; e-mail để sau qua metric filter) |
| R6 | Route mapping | Booking: `FromCis.tsx:16` `ManagedInCisLink` là component link chung (nhận `path`), không trỏ tới trang CIS nào chưa có. Chỗ thật sự thiếu là câu "managed in CIS admin" trên `staff/page.tsx:78` và `[cisUserId]/page.tsx:161`, không có link nào | đọc file Booking | §2, §6.3, GĐ5, §8 |
| R7 | Route mapping | `shared.llm_call_log` **không có cột `app`**. Chi tiêu TripPlanner phải lọc theo `stage LIKE 'tp\_%'` | `db-schema-reference.md`; TP `config.py:130` | §6.2 |
| R8 | Bảo mật / nhất quán | §6.4 đọc `PLACES_SOURCE` mâu thuẫn với §9 "không cấp `GetFunctionConfiguration`" | — | §6.4: chỉ đọc qua `/browse/health` (GĐ9) |
| R9 | ADR 0004 / 0006 | Q4 "role CIS nullable" làm gãy cầu nối Booking hiện tại: `ROLE_FROM_CIS` suy role Booking từ `cis_role`, còn `isStaffRole` trong middleware CIS đá role null về `/login` | Booking `auth/staff.py:27-30`, CIS `middleware.ts` | §5.4, Q4 → (a) tới Cognito; KHÔNG #14 |
| R10 | Bảo mật | Cờ `owner` của `staff.write` không có chỗ lưu | `admin_users` chỉ có 7 cột | §5.4, GĐ5: cột `is_owner` |
| R11 | Bảo mật | GĐ2 chỉ thêm `PAGE_RULES`. BFF `/api/admin` cho mọi staff đọc mọi path, nên reviewer vẫn đọc được danh sách staff qua API | `rbac.ts:67-104` | GĐ2: `API_READ_RULES {prefix:"platform"}`; GĐ5: `API_WRITE_RULES "platform/"`; §4 ghi chú khác biệt giữa matcher có và không có `/` |
| R12 | Solo | "Ship tuần này" chưa rõ: Q10 dồn GĐ0+1+2 (≈ 4–5,5 ngày) vào một phiên, trong khi vẫn phải làm việc CIS. MVP 13–17 ngày tức là 2–3 tuần lịch | memory "CIS first", "3–5 issue/phiên" | §1.6, bảng "Tuần này" ở §7, Q10, dòng MVP |
| R13 | Chi phí Vercel | Ước tính deploy tính theo PR; thật ra mỗi push là một preview deploy, và vòng Kiro tự lặp có thể đốt 5–10 deploy cho một PR. Ngưỡng ~100/24 h là chung cả team | luật deploy Hobby (bối cảnh S240) | §8 Vercel |
| R14 | Chi phí Cognito | "~10 MAU, trong free tier" bỏ sót WAF cho pool ≈ 12–15 USD/tháng, đã có trong ADR 0006 mục Costs | `0006-ecosystem-identity.md:420-445` | §1.5, §8 |
| R15 | Solo | Migration GĐ5 cần bản copy ở Infra + workflow DB Migrate (luồng D8), tức thêm một PR Infra. Schema reference giờ do workflow tự regenerate, không làm tay | `db-schema-reference.md` header; steering `db-schema.md` | §5.4, GĐ5 |
| R16 | Bảo mật | So sánh secret bằng `!=` (không constant-time; P0-5 S241 yêu cầu sửa) | `admin.py:110-114` | GĐ −1, bảng SDLC |
| R17 | Route mapping | Danh sách router của GĐ3 thiếu `admin.py`, `admin_dashboard`, `admin_search`, `admin_trip_page` | `main.py:207-249` | GĐ3 |

### 11.2 Đã kiểm, đúng như bản trước, giữ nguyên

- 17 trang `/admin/*`, `NAV_GROUPS` (Overview · Content · Intelligence · Tenants · Operations + Settings), `also` của Social Content, `PAGE_RULES` (kể cả rule thừa `/admin/pipeline`), `canWriteAdminPath` cho ghi mặc định (`rbac.ts:117-121`), BFF chuyển tiếp `x-admin-role` / `x-admin-user-id` / `X-Admin-Secret`, `matcher` `/admin/:path*`.
- 7 tab Settings (`pipeline`, `brand`, `seo`, `models`, `jev-credit`, `tenant`, `ui-kit`) chọn qua `?tab=`, nên redirect bằng `next.config` với `has` query là làm được (redirect của `next.config` chạy trước middleware).
- Spec smoke đã dẫn (`ui-smoke.spec.ts:55` `settings-models`, `:134` redirect dashboard, `aa752-shell.spec.ts:25`) và `BottomNav` hard-code Overview/Jobs: đều đúng.
- `verify-admin` không check lại `is_active` (`main.py`, docstring "Stateless…24h"): đúng. Vì vậy GĐ4a phải xong trước GĐ5, nếu không thì khoá staff ở GĐ5 tới 24 h sau mới có hiệu lực.
- **ADR 0006:** directory ở CIS admin là writer Cognito duy nhất; reconcile chỉ báo cáo; không có UI tạo mật khẩu (cấm `AdminSetUserPassword`); machine caller không có Cognito client (khớp với việc giữ secret làm machine principal); `@adventure.asia`. Các điểm còn lệch (`staff_app_grant` thay cột role theo app, group `booking-content_creator`) đã được nêu là **cần amendment** (Q3, Q5), không làm ngầm.
- **ADR 0004 O1:** Booking giữ app riêng, đăng nhập bằng tài khoản CIS qua RS256 `aud=booking`; console chỉ link sang, không port.
- **tenant-sees-content-only:** QA/gate/A4/Content Trace ở lại admin (khu CIS Content), không có gì đẩy ra `/portal`. Đã ghi thêm rằng trang Platform không bao giờ được link từ portal (KHÔNG #11).
- Phương án A (không thêm Vercel project, không đổi URL) vẫn là lựa chọn đúng. Phản biện không đổi điểm chấm của §3, chỉ đổi thời gian tới trang staff đầu tiên.

### 11.3 Chưa làm được trong vòng này (để người làm GĐ −1 xác nhận)

- Danh sách 26 route lấy từ quét AST theo heuristic (không thấy `verify_admin_secret`/`Depends`/`admin_secret` trong hàm). 12 route chưa xác nhận bằng 200: `jobs/{id}/llm-calls` trả 404 (không phải 403) với id giả, nghĩa là request đã đi qua mà không bị kiểm auth; 11 route còn lại (`jobs/{id}`, `llm-shadow/report`, `llm-usage/tree`, `dfs-usage`, `dfs-usage/by-country`, 5 route `photos`, `POST segment-research/preview`) được suy ra từ code, không gọi (POST thì cố ý không gọi). Test CI của GĐ −1 là phép kiểm cuối cùng.
- Chưa kiểm job retention nào xoá `acp_shared.audit_log` trước khi bật trigger (§5.5). GĐ5 kiểm.
