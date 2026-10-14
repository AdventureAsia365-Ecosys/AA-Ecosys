# S235 — 14/10/2026 — Pilot agent team, Booking chạy thật, thiết kế hệ sinh thái, place card sạch

**Tác nhân:** Claude Code (WSL, Ultracode bật một phần) — điều phối + nhiều agent con theo lane (CIS backend, portal, Booking, infra, docs).
**Audit / artifact:** `docs/audits/2026-10-14-S235-ecosystem-team-pilot/` (journal `00-orchestrator-journal.md`, blueprint, ai-first, ai-governance-audit, t2-rerun, r5, card-kinds-audit, booking-e2e, ui-verify…). Blueprint: https://claude.ai/artifact/Hz5bn9ryLDToqiNU7vrHpt

## Trạng thái cuối phiên
- ECS CIS: api :588 / worker :143 cùng SHA `f5f1333` (COMPLETED, /health 200). Booking: service `aa-booking-dev-api` chạy, `/booking/health` + `/health/ready` 200 (bk-002).
- Migration mới nhất: CIS **224**, TripPlanner **tp-009**, Booking **bk-002** (schema reference đã regenerate).
- 5 repo (gốc + CIS + TripPlanner + Infra + Booking) ở main/master; repo AA-Booking clone tại `apps/AA-Booking` (đã gitignore).
- Chi phí LLM phiên ≈ $4,7 (T2 rerun $3,49 + F9 replay $0,13 + r5 $1,06 + thử thẻ AA-808 $0,01).

## Quyết định của Nghiệp
- Pilot agent team theo plan S234 — duyệt; hook chặn agent con push/merge/ghi AWS/MCP.
- Tenant: gỡ trường chất lượng khỏi pool tenant + gỡ chi phí LLM/Jev khỏi /v1/billing; tenant có **khôi phục** sau ngừng hợp tác.
- T2 judge: chọn **B** — mission lấy từ core_idea của tenant.
- ADR 0004 Booking: O1 staff dùng login CIS; O2 sub-domain lumiguides.it.com, review FE trên domain Vercel; O3 bảng `booking.job` riêng; O6 khách để lại tên + email + đồng ý, tạo lead, gộp khi OTP; O7 nội dung ở CIS; O8 TripPlanner là cửa trước; O9 job kind `bk_*`. Chưa tạo prod; prod sau này cũng trên **acc2**.
- ADR 0005 giá: USD chính + EUR/GBP/AUD/SGD; biên mục tiêu theo đề xuất; giữ Redis.
- Toàn bộ blueprint hệ sinh thái + hướng AI-first: duyệt.
- OpenAI chỉ là fallback cuối khi Bedrock sự cố (migration 224); chưa cần ZDR.
- Mọi audit/artifact phải lưu local trong docs/audits.
- Chất lượng: Nghiệp duyệt, Claude Code tự audit (panel agent) rồi báo cáo.
- AA-774 làm phương án (a) — endpoint sửa fact có audit; duyệt áp 54 sửa đổi.
- Thẻ trùng: **điều tra chắc chắn rồi mới gộp — để phiên sau.**
- Jira: duyệt đăng 4 nháp.

## Thay đổi Codebase
- **CIS** #699 AA-794, #700 AA-776, #701 AA-785, #702 AA-797 (vòng đời tenant + restore), #703 AA-798 (chi phí LLM thật, mig 223), #704 AA-792, #705 AA-796 (projection tenant), #706 AA-799 (bảo mật /v1/pipeline), #707, #708 (lens core idea T2), #709 AA-786 (F9 v1.1), #710 CONTEXT, #711 AA-774 (lọc kind fact vào seed), #712 mig 224, #713, #714 AA-773 (offered status), #715 AA-775 (pace), **#716** AA-774 endpoint sửa fact + drawer, **#717** AA-808 (drafter không ghép câu khách du lịch + post-check), **#718** drawer UI, **#719** AA-809 (khớp thẻ sau khi soạn, chống trùng).
- **TripPlanner** #69 (identity), #70 (tp-009 grant cho booking).
- **Booking** repo mới (public, branch protection 5 check), bootstrap + PR #1 bk-002 inquiry intake + worker.
- **Gốc** #58–#63: ADR 0001/0004/0005 Accepted, contracts (`inquiry.submitted.v1.1`), ecosystem-architecture, schema-ownership, guardrail hook bắt lệnh có option prefix (31/31 red-team).

## Thay đổi Hạ tầng
- Infra #95 OIDC trust ghim id bất biến (org/repo), #96 booking.tf (24 resource), #97 repo id, #98 11 alarm + log retention + tag, #99 ALB SG chỉ VPC + WAF CommonRuleSet **count-only** + trust TripPlanner ghim + RDS deletion protection, #100/#101 bản copy migration.
- Secret mật khẩu role booking chỉ nằm trong Secrets Manager.
- Cost allocation tags: acc2 là linked account → payer 033086823579 phải bật (miễn phí). **Nghiệp nhờ chủ payer.**

## Bằng chứng verify
- Booking E2E: trip TripPlanner c14c07ae → TC-000001 + lead + notification staff; job `bk_inquiry_pull`/`bk_inquiry_process` succeeded.
- r5 (20 bài, $1,064) so với r4: sửa nhẹ trở lên 70% (55%), LinkedIn 11/12, blog 3/8 (1/8), điểm 5,96 (5,74), lỗi cứng 2 (4), lật ngược 0/8 (4/8).
- AA-774: audit 2 lens 110 thẻ/732 fact → áp 54/54 sửa đổi trên 37 thẻ, 37 dòng audit; seed Tsaatan không còn câu đường vào.
- AA-808: 31/31 fact lọt bị bắt, 0/22 bắt nhầm, 2/437 nền; thử 5 thẻ mới, 0 câu khách du lịch.
- AA-809: resolver live 5/5 đúng (chỉ đọc).
- UI drawer Facts: 12 ảnh, 0 console error, 0 request ghi.

## Linear
- Done: AA-773, 774, 775, 776, 785, 786, 794, 796, 797, 798, 799, 808, 809.
- In Progress: AA-792 (brand_fit 6,22 → 7,0, chưa ≥7 mọi tenant; chờ đọc giọng).
- Mới: AA-799–809.

## Jira (đã đăng, Nghiệp duyệt)
- PR-12 comment 10465 (Booking chạy thật, luồng đầu, cách tính giá).
- PR-7 comment 10466 (kết quả r5).
- Tạo PR-17 (tenant viết đúng giọng thương hiệu), PR-18 (quản lý tenant) — PR-18 chờ chị Thư xem rồi Done.

## Còn lại (phiên sau)
1. **Thẻ trùng**: điều tra chắc chắn 5 cặp nghi trùng (Paro/Paro Town, Zhongba/Zhongba County, Gyirong/Gyirong County, Lake Manasarovar/eastern shore, Rongbuk/Rongbuk Valley) — xem facts + atom link, rồi mới gộp. File `card-kinds-audit/aa809_duplicate_clusters.json`.
2. AA-792: đọc giọng T2 + AA-801 ổn định judge T2 (shadow gpt-6-luna 10% tới 31/10).
3. AA-789/790: repair làm mồ côi câu mở đầu blog; hashtag/địa danh sai chính tả; giọng Terra.
4. AA-805: TripPlanner gửi chặng sai thứ tự ngày; Booking: màn nhân viên + nhập giá nhà cung cấp.
5. AA-806: sau 1–2 ngày count thì bật WAF enforce; tách role CI.
6. AA-802/803/804/807/800.

## Lưu ý kỹ thuật cho phiên sau
- ECS exec stdout hay bị cắt ("EOF") → in kết quả 1 dòng hoặc ghi S3; **lệnh chạy LLM bị cắt output vẫn có thể đã chạy** — kiểm DB trước khi chạy lại (AA-808 trial chạy 2 lần vì vậy).
- `gh` không có `pr update-branch` → `gh api -X PUT repos/.../pulls/<n>/update-branch` (train.sh đã sửa).
- Bảng audit platform là `acp_shared.audit_log` (không phải `shared.platform_audit_log`).
- Lệnh ghi dữ liệu Dev / Secrets Manager bị auto mode chặn → Nghiệp tắt auto mode rồi chạy.
