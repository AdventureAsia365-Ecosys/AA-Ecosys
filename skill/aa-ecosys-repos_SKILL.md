---
name: aa-ecosys-repos
description: AA-Ecosys repository architecture (org AdventureAsia365-Ecosys, 3 repo dưới ~/projects/AA-Ecosys/), folder structure, pipeline flow, domain mapping, frontend page inventory, API endpoints, auth mechanism, known bugs, audit & UAT scope. Dùng skill này bất cứ khi nào làm việc với CIS Admin UI, tenant portal (T-series), TripPlanner, backend pipeline A0-A4/T0-T11, Lambda, Terraform, hoặc cần biết file/router/page nào ở đâu. Trigger khi thấy: AA-Ecosys, AA-CIS-App, AA-CIS-Infra, AA-TripPlanner-Web, AdventureAsia365-Ecosys, pipeline stages, A0-A4, T0-T11, atom, frontend pages, routers, HITL gates, Vercel, Lambda, admin workspace, tenant portal, audit, UAT, CIS domain, login, auth.
---

# AA_Ecosys — Repository Architecture Reference
> Last verified: 27/08/2026 — đợt dọn dẹp lớn nhất từ trước tới giờ (AA-473 xoá hẳn Gate A,
> AA-475 xoá hẳn Atomize/Curation platform-scope, AA-477 xoá hẳn 6 router ACPv1 + 2 Lambda,
> AA-480/481 xoá 6 bảng chết bổ sung + viết FK Reference đầy đủ). Bản 26/08 (S160) đã lỗi thời
> nặng ngay hôm sau — mọi mục ghi "CHƯA re-verify" ở bản đó giờ đã có kết luận rõ ràng, xem §9.
> Note: skill chỉ chứa cấu trúc ổn định. Số liệu vận hành (commit, migration số, task def, PROD
> state) → Notion memory.md, KHÔNG ở đây.

**Linear:** toàn bộ issue active của AA_Ecosys giờ nằm trong 1 project duy nhất "ACPv2 —
Admin/Tenant Split (A/T)" (gộp từ ACP v2 + ACPv2 Phase 2 + AA-CIS, 27/08/2026) — không còn rải
rác qua nhiều project. 3 project cũ (ACP v2, ACPv2 Phase 2, AA-CIS) còn tồn tại trên Linear (chưa
archive vật lý tính tới lúc verify) nhưng 0 issue active còn lại — đã sẵn sàng archive, chỉ chưa
bấm nút.

---

## 0. ⚠️ TÌNH TRẠNG VẬN HÀNH THẬT — đọc trước mọi thứ khác

> **CẬP NHẬT 15/09/2026 (restructure AA-Ecosys):** workspace đã gom về `~/projects/AA-Ecosys/`
> (multi-repo, mỗi repo `.git` riêng). Org GitHub đổi tên `AdventureAsia365-CIS` →
> **`AdventureAsia365-Ecosys`** (redirect tự động; OIDC trust đã mở rộng nhận cả 2 tên, đã apply).
> **Có 3 repo** (không phải 2 như bản 27/08): thêm `AA-TripPlanner-Web` (B2C trip planner, đã
> tồn tại thật, backend rides trong `AA-CIS-Infra/accounts/aa365/tripplanner.tf`). Tên repo GIỮ
> NGUYÊN, chỉ đổi org + đổi tên thư mục local cho khớp tên repo. Xem `docs/ecosystem-architecture.md`.

**Nội dung §1 (repos), §5 (Infra), path bên dưới đã cập nhật theo restructure. Phần nghiệp vụ
(pipeline A0-T11, routers, gates §3/§4/§6/§7/§9) giữ nguyên — không bị ảnh hưởng bởi restructure.**

**`AA-ACP-App` và `AA-ACP-Core` đã ARCHIVE trên GitHub** (26/08/2026, AA-467) **VÀ XOÁ HẲN khỏi
local workspace** — không còn tồn tại nữa. Mọi dependency ngầm (CORS entry, `services/acp/s2/`
dead code, `requirements-acpcore.txt`) đã dọn sạch qua PR #230.

**Khi giao bất kỳ task UI/frontend nào cho Claude Code, LUÔN ghi rõ repo đích là AA-CIS-App**
trong prompt — dù nguy cơ nhầm sang AA-ACP-App giờ đã bằng 0 (thư mục không còn tồn tại), vẫn
giữ thói quen ghi rõ để tránh mọi nhầm lẫn tên gọi (lỗi thật từng xảy ra S136/AA-330 khi repo
đó còn tồn tại).

**Chuỗi ACPv2 T-series (T0-T11) đã BUILD XONG HOÀN TOÀN** (S155-S159, tất cả Done, live-verified
qua HTTP thật). Toàn bộ mô tả "N4-N8 chưa lắp ráp/chỉ preview/0 router wired" trong các bản skill
cũ (trước 31/07) đã **LỖI THỜI HOÀN TOÀN** — xem §8 để biết mapping N-series cũ → T-series mới.

**AA-467/468/472 (S160) đã dọn sạch tàn dư kiến trúc "staff chuẩn bị trước cho tenant":**
- Xoá hẳn: `services/acp/s2/` (ACPv1 S2 dead code), `admin_produce.py`, `/admin/quarter-plan`,
  `/admin/produce`, `admin_marketplace.py`, `/admin/marketplace`, `seed_tenant_atoms()`,
  `assign_tenant_angle()` (PATCH .../angle), `get_tenant_mirror()` (GET .../mirror)
- Tạo tenant mới **KHÔNG còn cách nào seed portfolio/angle thủ công qua API** — tenant luôn bắt
  đầu 0 tour, tự chọn qua T1 (`GET /v1/tours/pool`, toàn bộ Master Content)

**AA-473/475/477/480/481 (27/08/2026) đã dọn tiếp phần "staff gate/curate trước khi tenant thấy"
— chuỗi dọn dẹp lớn nhất từ trước tới giờ, tóm tắt đầy đủ ở §9. Điểm quan trọng nhất cho bất kỳ
ai đọc skill cũ:** mọi mục "CHƯA re-verify, dead traffic theo skill cũ" ở bản 26/08 — 6 router
ACPv1 (`v1_s1.py`, `v1_acp.py`, `v1_acp_gate.py`, `v1_s3.py`, `v1_s4_blog.py`,
`admin_acp_proxy.py`) — giờ **ĐÃ XOÁ HẲN, có kết luận rõ ràng, không còn "cần grep lại xác nhận"
nữa.**

---

## 1. Repos Overview (3 repo, org: AdventureAsia365-Ecosys)

Tất cả nằm dưới org GitHub **`AdventureAsia365-Ecosys`**. Thư mục local gom trong `~/projects/AA-Ecosys/`,
tên thư mục khớp CHÍNH XÁC tên repo.

| Repo | WSL2 Path | Role | Deploy | Trạng thái |
|------|-----------|------|--------|------------|
| **AA-CIS-App** | `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App` | FastAPI backend (CIS core + ACPv2 T-series thật) + CIS Admin frontend + Tenant Portal frontend | ECS Fargate (api) + Vercel (frontend) | ✅ **SỐNG** |
| **AA-TripPlanner-Web** | `/home/nghiep/projects/AA-Ecosys/apps/AA-TripPlanner-Web` | B2C map-first trip planner (Next.js FE + 2 Lambda BE). BE resource nằm trong `AA-CIS-Infra/accounts/aa365/tripplanner.tf` | Vercel (FE) + Lambda (BE) | ✅ Sống |
| **AA-CIS-Infra** | `/home/nghiep/projects/AA-Ecosys/infra/AA-CIS-Infra` | Terraform — ECS, RDS, Lambda, API GW, VPC, NAT, OIDC, Bedrock cross-account | GitHub Actions (aa365) + human/MFA (acc1/acc3) | ✅ Sống |

Sắp có: **`AA-Booking` (AAA)** — B2C, thêm sau. Điểm bàn giao TripPlanner → AAA: xem
`~/projects/AA-Ecosys/docs/tripplanner-to-aaa-handoff.md`.

~~AA-ACP-App~~ / ~~AA-ACP-Core~~ — **ARCHIVE + XOÁ HẲN 26/08/2026 (AA-467)**. Không còn tồn tại
dưới bất kỳ hình thức nào (local lẫn active trên GitHub, chỉ còn read-only archived repo trên
GitHub cho mục đích tham khảo lịch sử nếu thật sự cần).

---

## 2. Domain & Audience Map

| Domain | Repo → path | Audience | Trạng thái |
|--------|------------|----------|-------|
| `aa-cis.lumiguides.it.com` | AA-CIS-App → `frontend/app/(internal)/admin/` | aa_internal admin + content team | ✅ Sống |
| `aa-cis.lumiguides.it.com/portal` | AA-CIS-App → `frontend/app/(tenant)/portal/` | Tenant self-service (T0-T11) | ✅ Sống |
| `api-cis.lumiguides.it.com` | AA-CIS-App → `api/` (ECS) | Backend chung | ✅ Healthy |

~~`acp.lumiguides.it.com`~~ — domain đã gỡ khỏi CORS allow_origins (PR #230), repo phục vụ nó
đã archive + xoá.

---

## 3. AA-CIS-App — Backend Routers

### Entry: `api/main.py`
- asyncpg pool min=2 max=10, Redis ElastiCache
- **KHÔNG còn** import/mount `services/acp/s2/` (xoá PR #230), `admin_produce_router` (PR #231),
  `admin_marketplace_router` (PR #232) — nếu thấy dòng import này trong code là bug/chưa dọn hết
- **KHÔNG còn** import/mount 6 router ACPv1: `v1_s1_router`, `v1_s3_router`, `v1_acp_gate_router`,
  `v1_s4_blog_router`, `v1_acp_router`, `admin_acp_proxy_router` — **xoá hẳn 27/08/2026 (AA-477,
  PR #238)**, không còn tồn tại kể cả reachable-by-URL
- **KHÔNG còn** import/mount `v1_atoms_router` — **xoá hẳn 27/08/2026 (AA-475, PR #236)**, whole
  file, không còn endpoint decompose độc lập nào qua API

### Routers T-series (ACPv2 thật, tenant-facing, JWT-only) — SỐNG, build xong S155-S159

| File | Stage | Route chính | Ghi chú |
|------|-------|-------------|---------|
| `v1_tours.py` | T1-T3 | `/v1/tours/*` | T1 pool browse, T2 rewrite, T3 check |
| `v1_planning.py` | T7 | `/v1/planning/*` | Content planning (kế N4-N6 cũ), quarter-plan tenant self-service |
| `v1_angle_gate.py` | T8 | `/v1/angle-gate/*` hoặc tương đương | 8-goal angle selection cho từng piece (KHÔNG phải cấp tenant) |
| `v1_content_writing.py` | T9+T10-inline | — | Async 202+poll (AA-466, S159), 9 gate F1-F9 |
| `v1_publish.py` | T11 | `/v1/publish-log/*` | Blog-only, tenant self-unpublish |
| `v1_integrations.py` | T11 | `/v1/integrations/wordpress` | WordPress credentials per-tenant |
| `v1_marketplace.py` | — | `/v1/marketplace` | Tenant xem toàn bộ Master Content (thay `marketplace_portfolios` cũ đã xoá) |
| `v1_s1_from_atom.py` | — | — | **ĐÃ BỎ HẲN (AA-306, xác nhận 26/08/2026 S159)** — không phát triển thêm dưới bất kỳ hình thức nào, coi là dead code cần đánh giá dọn riêng nếu còn tồn tại |

⚠️ **T5 (atomize) KHÔNG còn là 1 endpoint `/v1/*` độc lập** — `v1_atoms.py` đã xoá hẳn (AA-475).
Logic atom hoá giờ chạy nội bộ trong `services/acp_produce/tenant_pipeline.py::run_t5_atomize()`,
gọi 4 helper thuần (`SYSTEM_PROMPT`/`build_user_prompt()`/`source_hash()`/`strip_json_fence()`)
từ `services/acp_shared/atom_extraction.py` (module mới, tách ra từ `v1_atoms.py` TRƯỚC khi xoá
file — nếu không tách, xoá file sẽ làm gãy T5 thật). T4→T5 hiện chạy liền 1 mạch (kiến trúc bị
Ms. Thu đánh giá SAI, AA-469 việc 1 sẽ tách trang riêng — chưa build).

### Routers admin (aa_internal, X-Admin-Secret) — sống

| File | Vai trò | Ghi chú |
|------|---------|---------|
| `admin.py` | Tenant CRUD, T0 upload brand | **Gate A ĐÃ XOÁ HẲN (AA-473)** — `create_tenant()` INSERT `is_active=true` thẳng, không còn `approve_gate_a()`/`get_gate_a_status()`, không còn `pending_tenants[]` trong `list_tenants()` |
| `admin_pipeline.py` | core-CIS S0/S1 admin | Sống. **`get_tours_for_atomization()` + `admin_decompose_atoms()` ĐÃ XOÁ (AA-475)** — N0-N2 admin-triggered decompose không còn tồn tại |
| `admin_atoms.py` | Atom list/star/edit (KHÔNG phải decompose) | **KHÔNG bị xoá, chỉ cắt bớt** (AA-475) — `list_atoms`/`atoms_summary`/`patch_atom` giữ nguyên vì T6 (`/portal/t6-atoms`) phụ thuộc; `patch_atoms_bulk`/`preview_slotgrid` đã xoá (chỉ có `/admin/curation`/`/admin/curation/preview` gọi, đã xoá cùng đợt) |
| `admin_a4.py` | A4 Cross-Tenant Oversight | Safety net hậu-kiểm cho T11 auto-publish, by design |
| `admin_settings.py` | Settings | Sống |
| `auth.py` | JWT + API key | Sống |

**ĐÃ XOÁ HẲN (tổng hợp toàn bộ, 26-27/08/2026):**
- S160 (26/08): `admin_produce.py` (PR #231), `admin_marketplace.py` (PR #232),
  `seed_tenant_atoms()`, `assign_tenant_angle()`, `get_tenant_mirror()` (PR #232)
- AA-473 (27/08): `approve_gate_a()`, `get_gate_a_status()`, `GateAApproveRequest` khỏi `admin.py`
- AA-475 (27/08): `v1_atoms.py` (whole file), `get_tours_for_atomization()` +
  `admin_decompose_atoms()` khỏi `admin_pipeline.py`, `patch_atoms_bulk` + `preview_slotgrid`
  khỏi `admin_atoms.py`, `shared/services/atom_decompose_poller.py` (0 caller)
- AA-477 (27/08): 6 router ACPv1 nguyên file (`v1_s1.py`, `v1_s3.py`, `v1_acp_gate.py`,
  `v1_s4_blog.py`, `v1_acp.py`, `admin_acp_proxy.py`) + `services/acp_s4/` + `services/acp_s3/`
  + `services/acp_s4_evaluate/` (source thật của 2 Lambda đã xoá cùng đợt) + file chết trong
  `services/acp_s4_blog/` — **GIỮ TUYỆT ĐỐI** `cms/wordpress.py` + `cms/base.py` (T11 dùng thật)

---

## 4. Frontend — CIS Admin + Tenant Portal

**Domain:** `aa-cis.lumiguides.it.com` | Auth admin: `x-admin-secret` header + cookie | Auth
tenant: JWT cookie

### Admin pages (`frontend/app/admin/`)
```
admin/
├── dashboard/page.tsx
├── upload/page.tsx          ← S0: Excel upload
├── s1-rewrite/page.tsx      ← S1 Rewrite (CIS core)
├── review/page.tsx          ← HITL Review Queue
├── run-health/page.tsx
├── master-content/page.tsx  ← published_tours pool
├── brand/page.tsx
├── tenants/page.tsx         ← Tenant CRUD — KHÔNG còn Gate A wizard step (AA-473, xem dưới)
├── settings/page.tsx
└── a4-oversight/page.tsx    ← A4 Cross-Tenant Oversight — SỐNG, by design safety net
```

**ĐÃ XOÁ HẲN, tổng hợp:**
- S160 (26/08): `admin/quarter-plan/` (+create), `admin/produce/` (PR #231), `admin/marketplace/`
  (PR #232) — thay thế hoàn toàn bởi T-series (quarter-plan→T7, produce→A4 hậu-kiểm,
  marketplace→tenant tự xem qua `v1_marketplace.py`)
- AA-473 (27/08): `admin/tenants/page.tsx`'s Onboarding tab hoàn toàn — `OnboardingTabContent`,
  `GateAStatus`, `StepHeader`, `PendingOnboarding`/`PendingTenant` types, `pendingStepLabel()`,
  `PendingTenantCard`, `PendingOnboardingSection`, cookie helper riêng cho tab này, `"onboarding"`
  khỏi `TABS` — default tab giờ luôn `"tours"`, không còn chọn tab theo trạng thái Gate A
- AA-475 (27/08): `admin/atomize/`, `admin/curation/`, `admin/curation/preview/` (3 page nguyên
  vẹn) + `AdminSidebar.tsx`'s `ATOMS_NAV` entries + `middleware.ts`'s 2 dòng `PROTECTED_ROUTES`
  tương ứng

### Tenant Portal pages (`frontend/app/(tenant)/portal/`)
```
portal/
├── t0-brand/page.tsx
├── t1-rewrite/page.tsx           ← Browse Master Content pool + rewrite + atomize gộp (T1-T5)
├── t4-pool/page.tsx              ← My Catalog — điểm dừng thật
├── t6-atoms/page.tsx             ← Chọn atom theo HIGH/MED/LOW — dùng chung admin_atoms.py backend
├── t7-planning/page.tsx          ← Content Planning (chỉ xem, chưa sửa được — AA-469 sẽ thêm edit)
├── t8-angle-gate/page.tsx        ← Wizard 9 bước liền mạch (Angle Gate → Write Content, T8+T9 gộp UI)
├── t11-publish/page.tsx (+connection/) ← Publish + Manage WordPress connection
├── marketplace/page.tsx          ← GET /v1/marketplace — xem toàn bộ Master Content
├── dashboard/, activity/, api/, billing/, settings/ ← tenant account pages, ngoài phạm vi T-series
```

**Lưu ý quan trọng:** `/portal/marketplace` (tenant-facing, sống) và `/admin/marketplace`
(đã xoá S160) là 2 route HOÀN TOÀN KHÁC NHAU dù tên gần giống — không nhầm lẫn khi grep.

### API calls pattern
- Admin: `x-admin-secret` header, Base URL `api-cis.lumiguides.it.com`
- Tenant: JWT cookie, cùng Base URL, prefix `/v1/*`

---

## 5. AA-CIS-Infra — Terraform

**Nhiều Terraform root song song:**
- `main.tf` (legacy, account 867490540162 / acc1) — module `eventbridge`
- `accounts/aa365/main.tf` (**live thật, app chính**, account 005097885195 / acc2)
- `accounts/aa365/tripplanner.tf` — TripPlanner BE (2 Lambda, API GW HTTP v2, S3 artifacts,
  OIDC deploy role, secret DB+api-key) trong cùng root aa365. App `AA-TripPlanner-Web` owns code.
- `accounts/acc1-bedrock/` — role satellite Bedrock trên acc1 (fallback)
- `accounts/acc3-bedrock/` — role satellite Bedrock trên acc3 (786888028788, CHÍNH), state
  bucket riêng

**OIDC (transitional, 15/09/2026 — org rename):** 2 role trong root aa365 đã mở rộng `sub` để nhận
CẢ `repo:AdventureAsia365-CIS...` VÀ `repo:AdventureAsia365-Ecosys...` (applied: 0 add/4 change/0
destroy). `cicd.tf` (`aa-cis-dev-role`) dùng dạng phẳng `repo:<org>/*:*`; `tripplanner.tf`
(`aa-tripplanner-dev-app-deploy`) dùng dạng `@id` wildcard vì repo AA-TripPlanner-Web bật
"include repo ID in subject" (org KHÔNG bật). Gỡ tên cũ ở G5: xem `docs/g5-remove-old-trust.md`.

⚠️ **Tech debt CI đã gây sự cố THẬT 2 lần (AA-397, AA-399)** — `.github/workflows/terraform-apply.yml`
hard-code `working-directory: accounts/aa365`. Merge PR chạm root mới KHÔNG bao giờ tự apply qua
CI — luôn cần `terraform apply` tay qua MFA. Trước khi đổi resource cross-account IAM, luôn xác
nhận role đích tồn tại thật (`aws iam get-role`) trước khi apply phía gán quyền.

**AA-477 (27/08/2026, PR #35 accounts/aa365):** draft xoá 2 Lambda (`acp-s3-campaign-planner`,
`acp-s4-evaluate`) — Terraform applied THẬT (Nghiệp chạy tay qua MFA), `Apply complete: 8
destroyed` đúng kế hoạch. Cùng đợt dọn `deploy-dev.yml`/`scripts/package_lambdas.sh` (AA-CIS-App)
bỏ 2 tên Lambda này khỏi vòng lặp deploy.

**Còn treo, CHƯA điều tra lại (chưa xác nhận đổi gì kể từ 26/08):** `aa365.tfplan` (root live
thật acc2, chưa xác nhận đã apply hay chưa) + `accounts/acc3-bedrock/*.tfplan` (2 file, liên
quan AA-399) — Nghiệp yêu cầu "sau điều tra thêm", vẫn chưa làm, KHÔNG liên quan đợt dọn 27/08
này nên không tự ý giả định đã xong.

---

## 6. Full Pipeline Flow — A0-A4 + T0-T11 (mapping đầy đủ, thay N-series cũ)

### Core-CIS (S0 → S1, vẫn dùng cho tour KHÔNG qua atom) — A0-A3
```
A0: Excel upload → Lambda ingestion → raw_tours (Bronze, LUÔN thuộc aa_internal theo thiết kế —
    chỉ AA ingest ở A0, tenant chỉ sở hữu dữ liệu TỪ SAU khi rewrite/atomize qua owner_scope)
A1: S1 rewrite (1-lệnh-gọi-duy-nhất kiến trúc, xem services/content_generation/graph.py)
A2: HITL Review Queue (status='hitl')
A3: gold_aa_internal.published_tours (Master Content — nguồn cho T1 pool)
A4: Cross-Tenant Oversight — hậu-kiểm, safety net cho T11 auto-publish (KHÔNG phải gate chặn trước)
```

### ACPv2 T-series — trạng thái THẬT sau S159 + đợt dọn 27/08

| Stage | Route | Trạng thái |
|-------|-------|-----------|
| T0 | `/portal/t0-brand` | Done — brand + đối thủ |
| T1 | `/portal/t1-rewrite` | Done — **1 bug thật**: browse pool chỉ thấy 28/71 tour publish (AA-469 việc 3, chưa điều tra nguyên nhân) |
| T2 | — | Done — rewrite, ẩn |
| T3 | — | Done — check, ẩn |
| T4 | `/portal/t4-pool` | Done — My Catalog, **kiến trúc SAI theo Ms. Thu**: hiện chạy liền T2→T5 (AA-469 việc 1 sẽ tách) |
| T5 | — | Done — atomize, chạy nội bộ trong `tenant_pipeline.py` (KHÔNG còn endpoint API riêng từ AA-475), **cần trang riêng + tenant tự bấm** (AA-469 việc 1, chưa build) |
| T6 | `/portal/t6-atoms` | Done — chọn atom HIGH/MED/LOW, backend = `admin_atoms.py` (3 hàm còn giữ sau AA-475) |
| T7 | `/portal/t7-planning` | Done — Content Planning, **chỉ xem chưa sửa được** (AA-469 việc 2, chưa build) |
| T8 | `/portal/t8-angle-gate` | Done — wizard 9 bước, Angle Gate → Write Content gộp UI |
| T9 | — | Done — async 202+poll (AA-466, S159) |
| T10 | — | Done — 9 gate F1-F9 |
| T11 | `/portal/t11-publish` | Done — blog-only, patch timeout AA-465 vẫn mở bảo vệ `/goal` |

**AA-469 [REDESIGN T-series]** (Backlog, chưa STEP0) — 5 việc lớn từ họp Ms. Thu 26/08: tách
T4/T5, T7 UI edit+lịch sử, fix bug 28/71 tour, xác nhận T8-T11, A4 feedback loop cho mọi bước LLM.

**tour_atoms schema** (`acp_contract.tour_atoms`, migration 079 + ALTER 084/085) — 20 cột. **Từ
27/08/2026 (AA-475), atom CHỈ còn sinh từ T5 (tenant tự rewrite), `owner_scope=<tenant_id>`** —
2551 atom `owner_scope='platform'` (catalog chung cũ, N0-N2) đã DELETE thật khỏi DB cùng ngày,
KHÔNG còn khái niệm "atom platform-scope dùng chung" nữa. Chưa có trường ngày/thứ tự — xem
AA-352.

### Old ACPv1 (S0→S2→S3→S4.2, EventBridge/SFN)
**Đã xoá HOÀN TOÀN 27/08/2026 (AA-477)** — không chỉ `services/acp/s2/` (đã xoá từ S160) mà cả 6
router (`v1_s1.py`/`v1_s3.py`/`v1_acp_gate.py`/`v1_s4_blog.py`/`v1_acp.py`/`admin_acp_proxy.py`)
+ `services/acp_s3/`/`services/acp_s4/`/`services/acp_s4_evaluate/` + 2 Lambda deploy +
**21 bảng DB thật** (migration 121+122, COMMIT 27/08/2026 16:55:09 UTC). Chi tiết đầy đủ + Dead
Table Registry: xem §9 và skill `aa-cis-schema.md`.

---

## 7. HITL Gates

**Gate A/B/C là thuật ngữ ADR/PRD cấp cao, KHÔNG map 1-1 với Gate 1/2/3 ACPv1 cũ (đã archive
cùng AA-ACP-Core).**

- **Gate A** = Tenant onboarding approval — **ĐÃ XOÁ HẲN 27/08/2026 (AA-473)** — tenant
  `is_active=true` ngay khi `create_tenant()` INSERT, không còn approval nào, không còn
  `approve_gate_a()`/`get_gate_a_status()`, không còn `acp_shared.tenant_onboarding` (DB, migration
  120 — draft, CHƯA apply, vẫn còn 2 row sống tính tới 27/08, xem `aa-cis-schema.md`)
- **Gate B** = Quarter Plan approval — **đã chuyển Option A (tenant tự động approved)**, không
  còn staff duyệt tay (T7, theo ADR-2026-038 §0.2)
- **Gate C** = Produce approval cũ — **ĐÃ XOÁ HẲN** (S160, `/admin/produce`), thay bằng A4
  hậu-kiểm

**F1-F9** (T10 Quality Pass) = bộ gate khác hẳn, port từ `aa-marketing-v2`, không liên quan Gate
A/B/C. Gate numbering thật (không có F5, xem memory_user_edits #21 để biết lý do): F1_grounding,
F2_banned_patterns, F3_structural_variance, F4_brief_compliance, F6_route_to_sellable,
F7_faq_dedup, F8_framework, F9_brand_seo_audit.

---

## 8. Việc chưa xác nhận được (ghi rõ để không giả định)

- `aa365.tfplan` + 2 file `acc3-bedrock.tfplan` (AA-CIS-Infra) — chưa điều tra đã apply hay chưa,
  KHÔNG liên quan đợt dọn 27/08
- Live AWS state (task def revision, PROD config thật) — luôn lấy từ Notion memory.md đầu phiên
- Admin page inventory ở §4 và Portal page inventory đã đối chiếu trực tiếp `find` thật 27/08
  (khác bản 26/08 vốn liệt kê `admin/pipeline/s1/page.tsx` — path thật hiện tại là
  `admin/s1-rewrite/page.tsx`; và Portal thật có thêm `dashboard/`, `activity/`, `api/`,
  `billing/`, `settings/` ngoài T-series, chưa từng liệt kê ở bản cũ) — nếu 2 phần này lại lệch ở
  lần audit sau, đối chiếu lại bằng `find frontend/app/admin -name page.tsx` thay vì tin theo
  bảng cây thư mục cũ.
- `admin_atoms.py` sau AA-475 giờ có 2 loại caller khác hẳn nhau dùng chung 3 endpoint
  (`list_atoms`/`atoms_summary`/`patch_atom`) — staff qua x-admin-secret VÀ tenant qua JWT
  (`_resolve_atom_owner_scope`, AA-431). Chưa có UI admin nào gọi lại 3 endpoint này sau khi
  `/admin/curation` xoá — về lý thuyết vẫn reachable qua x-admin-secret trực tiếp nhưng không rõ
  còn ai dùng đường staff nữa, chưa xác nhận, không tự ý xoá tiếp nếu chưa hỏi.

---

## 9. Dọn dẹp ACPv1 hoàn tất 27/08/2026 (AA-473 → AA-475 → AA-477 → AA-480/481)

Chuỗi dọn dẹp lớn nhất từ trước tới giờ, 1 ngày, 3 hạng mục độc lập nhưng cùng nguyên nhân gốc:
mô hình "staff chuẩn bị/gate trước cho tenant" đã bị thay hoàn toàn bởi "tenant tự vận hành qua
T-series" (ADR-2026-038 §0.2), phần code/DB còn sót lại của mô hình cũ giờ mới dọn hết.

1. **AA-473 — Gate A xoá hẳn.** `approve_gate_a()`/`get_gate_a_status()` + Onboarding tab UI +
   `acp_shared.tenant_onboarding` (migration 120, draft, CHƯA apply). Kèm dọn dữ liệu: 12 tenant
   test xoá thật (DB giờ chỉ còn 3 tenant thật: `aa_internal`, `wanderlux-travel`,
   `exploreasia-co`). PR #234.
2. **AA-475 — Atomize/Curation platform-scope xoá hẳn.** `v1_atoms.py` (whole file, tách 4 helper
   thuần sang `atom_extraction.py` trước khi xoá vì T5 phụ thuộc — STEP0 ban đầu bỏ sót phụ thuộc
   này), `admin/atomize`+`admin/curation`(+preview) frontend, `admin_pipeline.py`'s 2 hàm N0-N2,
   `admin_atoms.py`'s 2 hàm chỉ /admin/curation gọi (giữ lại 3 hàm T6 dùng). Kèm dọn dữ liệu: 2551
   atom `owner_scope='platform'` DELETE thật (2629 row tính cả marker/deleted). PR #236.
3. **AA-477 — 6 router ACPv1 + 2 Lambda + cụm bảng DB gốc xoá hẳn.** STEP0 2 lần (lần 1 kết luận
   "0 row/0 caller", Nghiệp bác bỏ, yêu cầu điều tra sâu hơn ở lần 2 — tìm ra `cms/wordpress.py`/
   `base.py` sống thật giữa 1 package phần lớn đã chết, PHẢI giữ lại). PR #238 (code) + PR #35
   (Terraform, 2 Lambda) + migration 121 (15 bảng).
4. **AA-479/480/481 — audit lại từ đầu, không tin số cũ.** Nghiệp yêu cầu dump schema thật từ đầu
   thay vì tin báo cáo STEP0 cũ — tìm thêm 6 bảng chết ngoài phạm vi 121 (migration 122), viết FK
   Reference đầy đủ (81 quan hệ lúc đó).
5. **Migration 121+122 — CHẠY THẬT, COMMIT** 27/08/2026 16:55:09 UTC — 21 bảng DB xoá vật lý. DB
   từ 76→55 bảng, 81→63 FK. Full Dead Table Registry (tên bảng, migration, ngày, lý do, code cũ
   từng dùng) — xem skill `aa-cis-schema.md`, KHÔNG lặp lại ở đây.

**Không lặp lại chi tiết kỹ thuật/bằng chứng ở đây** — xem `docs/claude_audit/AA-473-step0-admin-gate-cleanup.md`,
`AA-475-step0-atomize-curation-teardown.md`, `AA-258-259-acpv1-tables-audit.md`,
`AA-479-schema-audit.md` (AA-CIS-App) và Linear AA-473/475/477/480/481 cho toàn bộ quá trình
điều tra + quyết định.

---

*Lịch sử refresh: 06/07/2026 (full), 30/07/2026, 31/07/2026 (S131 — full re-audit), 26/08/2026
(S160 — sau AA-467/468/472), 27/08/2026 (đợt dọn dẹp lớn nhất — AA-473/475/477/480/481, xem §9).*
