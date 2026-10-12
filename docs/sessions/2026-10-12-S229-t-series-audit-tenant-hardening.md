# S229 (12/10/2026, Kiro — WSL/VSCode) — khởi động audit T-series + hardening tenant + dọn hub

**Bối cảnh:** tiếp sau S228. Nghiệp làm việc kiểu phản biện từng bước, yêu cầu kiểm thật từ code/DB
chứ không đoán, và chốt "làm trọn việc rồi báo một lần".

## Trạng thái
- 4 repo về main/master cây sạch. ECS api `:533` / worker `:88`, SHA `16ceff9` (sau 6 PR App).
  Các commit docs sau đó không deploy.
- `shared.job` sạch, 0 wave. STS còn hạn.

## Quyết định của Nghiệp
- Làm việc 1 (dọn hub mồ côi) rồi tập trung trục T-series; audit kỹ + redesign UI chuyên nghiệp.
- Đồng ý toàn bộ đề xuất: sửa lỗi trước audit → pilot → tách layer → chạy đủ → báo cáo → UI.
- Thứ tự AA-703 (login passwordless): sau audit, cùng AA-672b, có ADR identity + SES trước.
- Tenant cũ: offboard (soft-delete), không xoá cứng.
- Quy đổi thị trường: Europe → UK/DE/FR/NL, North America → US/CA.
- DFS: khẳng định đúng thiết kế gốc — admin mua sẵn, tenant chỉ đọc để sinh topic/goal/angle/viết;
  tenant KHÔNG bao giờ chạy DFS. Cần làm rõ hệ thống phản ứng ra sao với thị trường lạ.
- Ghi tất cả điều tra + artifact vào `docs/audits`, rồi dừng phiên.

## Kết quả chính
- **Việc 1 — dọn hub mồ côi (Refs AA-758):** DRY RUN → xoá 387 hub không route nào tham chiếu
  (mọi version). Bảng hub 446 → 59; 21 hub sống nguyên. Snapshot S3
  `snapshots/s229_orphan_hubs_unref.json`. `/admin/overview` hub_count=21.
- **6 PR App (merged, CI xanh, deploy Dev):**
  - **#655** T-series pre-audit hardening: Jev fail-closed khi stage T thiếu tenant_id; A1-3
    `judge_units` nhận sai kiểu từ #631 (nuốt lỗi, mã bữa ăn bắn sai); T2 nuốt lỗi brand →
    raise + ghi `job.result.brand_loaded/seo_source`; trigger_rewrite kiểm active-Master +
    1 pending/tenant/tour + trừ quota sau cùng trong 1 tx; retry flip pending trước re-queue;
    endpoint tenant từ chối JWT staff (403).
  - **#656** revalidate chấm edit đối chiếu nguồn thật (trước chỉ truyền name/country/duration →
    so với nguồn rỗng; lỗi từ AA-234).
  - **#657** mỗi version revalidate được nhiều lần (idempotency key vĩnh viễn → chỉ chạy 1 lần).
  - **#658** offboard tenant chưa bao giờ chạy (`AmbiguousParameterError` `$1`) + offboard gỡ
    allow-list Jev; integration test trên Postgres thật.
  - **#659** T0 brand intake: upload .docx → parse điền form (parser cũ gộp Should Not vào Should);
    bỏ cắt ngầm 300 ký tự → 422 báo rõ; thị trường form → `tenant_seo_config` (trước không ai đọc,
    mọi tenant viết cho US).
  - **#660** upload/parse brand = base64 JSON (API Gateway không có binaryMediaTypes làm hỏng
    multipart: .docx 15.191 byte → 25.187 byte; mọi file brand cũ đều hỏng).
- **Tenant phase 0:** offboard 3 tenant cũ; tạo 4 tenant brand (atlas-hearth, terra-family,
  trail-pulse, wildkind-travel) nạp qua luồng T0 thật; key chỉ ở Secrets Manager; đều vào
  allow-list Jev.
- **Điều tra sâu (artifact + 2 tài liệu):**
  - Lớp đặt job/worker của T-series + cách gọi LLM: mọi call qua gateway, không hard-code model,
    0 DFS tenant; nhưng chi phí tenant ghi thiếu (tenant_id=None nhiều stage) và T7/T8 chạy LLM
    trong request HTTP (lệch ADR 0003).
  - Logic T2 (viết lại Master theo brand + keyword thị trường tenant) và T7–T11 (viết từ atom nền
    tảng; tour tenant chỉ dùng để chọn candidate); DFS end-to-end; cô lập tenant; phản ứng với
    thị trường lạ.
- **Lỗi lộ ra & đã sửa (ngoài kế hoạch):** A1-3 judge_units (#655), revalidate nguồn rỗng (#656),
  revalidate 1-lần (#657), offboard $1 (#658), API Gateway hỏng multipart (#660).

## Lệch đã xử trong phiên
- `docs/` trong App repo bị gitignore → tài liệu kiến trúc + audit đặt ở ROOT repo (đúng chỗ
  `db-schema-reference.md`), push master theo lệ root.
- "$0.03–0.06/bài" là số từ 7 bài social thử — rút lại, chờ đo thật ở pilot.
- Số goal: code có 8, không phải 10 Nghiệp nhớ → open question, đối chiếu Bảng 1 chị Thư ở audit T8.
- Key Atlas bị Nghiệp rotate tay lúc thử đăng nhập → mình mint lại + lưu Secrets Manager.

## Bằng chứng verify
- CI xanh 9/9 mỗi PR; deploy Dev COMPLETED cùng SHA (api/worker). 2615→2629 unit test pass.
- Integration test offboard + brand-markets chạy trên Postgres local (fail khi bỏ fix).
- DFS: `search_demand` US 1.602 / UK 1.484 / AU 1.214 vs DE/FR/NL 96 (1–3/09). 0 DFS tenant từ 29/09.
- LLM log: s1_judge 3/8.393 có tenant, s1_brand_audit 0/37, t10_judge 0/23, f10_embed 0/2.861.

## Còn lại / phiên sau (S230) — bắt đầu từ G1
1. **G1** (backend, $0): gắn tenant_id vào gateway (ContextVar như job_id), bỏ tenant_id=None ở 9
   call site. PHẢI xong trước pilot.
2. Hỏi Nghiệp: số goal (8/10); T2 có nên viết cho nhiều thị trường không.
3. **G2** (Nghiệp bấm): segment_research cho DE/FR/NL (budget $5/run; Kiro báo ước tính trước).
4. **G3**: pilot 3 tour × 4 tenant + 1 luồng slate→angle→blog→social/tenant; đo chi phí thật
   (tách blog/social), độ trễ T7/T8, thu nhãn ground-truth.
- Backlog đầy đủ G1–G15 + sơ đồ phụ thuộc: `docs/architecture/t-series-audit-and-plan.md` §7.
- Log kickoff chi tiết: `docs/audits/2026-10-12-S229-t-series-audit-start.md`.

## Lưu ý kỹ thuật
- `docs/` App repo gitignore — tài liệu kiến trúc/audit đặt ở root.
- Upload file qua API: dùng base64 JSON, API Gateway REST không có binaryMediaTypes.
- Trang quản lý tenant = panel inline trong `/admin/tenants` (AA-666), không phải trang riêng.
- T2 prefetch (`resolve_buyer_market` số ít) cố ý 1 thị trường cho Master — không phải bug; dữ
  liệu per-market cho tenant đến từ `segment_research` (nhận list thị trường).
