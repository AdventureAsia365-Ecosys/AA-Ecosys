# S197: đồng bộ CONTEXT.md 4 repo + báo cáo tuần 15–25/09

- **Ngày:** 25/09/2026
- **Tác nhân:** Claude Code
- **Người duyệt:** Nghiệp

## Trạng thái

**Xong:**
- Đọc toàn bộ log S181–S196 (15–25/09).
- Đồng bộ `CONTEXT.md` của 3 repo + `docs/ecosystem-architecture.md` với code thật. 4 PR đã merge (Nghiệp merge tay).
- Báo cáo tuần 15–25/09 cho buổi họp với chị Thư, trên Notion (Program Brain), cấu trúc theo báo cáo 31/08–10/09.
- Nghiệp thêm rule quyền `gh pr merge` vào `.claude/settings.local.json`.

**Không đụng:** code, hạ tầng, DB, Linear.

## Thay đổi Codebase

Chỉ sửa tài liệu, không đổi code.

| Repo | PR | Commit trên nhánh chính | Nội dung |
|---|---|---|---|
| AA-CIS-App | #449 | `c5b8c6f` | Glossary: Segment/Score/Route/Hub là platform-wide (AA-545), bỏ cảnh báo per-tenant cũ và sửa bảng Ownership. Score 4 chiều (AA-610). Slate có Debate + unmapped market + dedup cross-channel (AA-629/631/632). Gate 3 mức + Piece tenant-safe (AA-613/614). Repo Context thêm: model theo stage, theo dõi chi phí (AA-616), Batch bị chặn, quota gói (AA-640), brand tokens, route admin/portal hiện tại, code đã xoá, migration apply tay |
| AA-TripPlanner-Web | #49 | `b60d14e` | Tên bảng thật, BFF + X-TripPlanner-Key + HTTP API, Cohere gọi thẳng acc2, suggest-next taste+geo, gateway trên map (AA-589/590/591), việc còn treo |
| AA-CIS-Infra | #72 | `a69ed8e` | Role Cost Explorer acc1/acc3 (AA-623), tài nguyên Batch + blocker AWS (AA-606/624), Lambda DFS balance + quy tắc schedule group (AA-627), `stopTimeout` 90s (AA-310), quy tắc `profile` trong backend acc1/acc3 |
| AA-Ecosys | #5 | `b3f6f55` | `ecosystem-architecture.md`: bỏ cảnh báo per-tenant, thêm §4.4 theo dõi chi phí cross-account, trạng thái Batch, epic rerun |

Local 4 repo đã về `main`/`master`, nhánh `docs/context-sync-s197` đã xoá (cả remote).

## Thay đổi Hạ tầng

Không có. Không start/stop NAT/RDS/ECS (hạ tầng chạy suốt tháng 9 để theo dõi chi phí).

## Báo cáo tuần

- Notion: `Program Brain / Weekly Report (Sep 15 – Sep 25) — Cost Control, Content Quality & Tenant Portal`
  (https://app.notion.com/p/3e6b8a41ec5d817184f0de7f37be329b).
- Viết cho chị Thư, bằng tiếng Anh, không kèm mã issue. Các mục: Clean slate, Cost, Social Content Engine, Master Content, Tenant Portal, Trip Planner, Current State, Next Steps.
- Điểm cần chốt trong buổi họp: chạy lại 763 tour bằng Batch (chờ AWS) hay chạy đồng bộ theo từng nước.

## Bằng chứng verify

- 4 PR: CI xanh trước khi merge (App 5 job + Vercel; TripPlanner Backend/Frontend/Vercel; Infra Terraform Plan; repo gốc không có check). Trạng thái `CLEAN`.
- Sau merge: `git log` trên nhánh chính cả 4 repo có commit docs; `CONTEXT.md` nằm trong HEAD.
- Các fact ghi vào CONTEXT đã đối chiếu code: route portal/admin (`ls`), migration 146 (bỏ `tenant_id`, PK `(market, tour_id, segment_id)`), migration mới nhất 167, `stopTimeout = 90`, `profile` trong backend acc1/acc3, các bảng TripPlanner trong `001_tripplanner_schema.sql`.
- Rule quyền: đọc lại `.claude/settings.local.json`, 2 dòng `Bash(gh pr merge:*)` và `PowerShell(wsl -d Ubuntu -- gh pr merge:*)` đúng cú pháp. Chưa thử thật (không có PR mở).

## Còn lại

1. **Chốt cách rerun 763 tour** (AA-599/600/601) sau buổi họp với chị Thư: chờ AWS bật Batch (AA-624) hay chạy đồng bộ theo từng nước.
2. **AA-641:** Nghiệp đọc mô tả rồi chốt.
3. **AA-634 Jev:** chờ API key.
4. **PR #6 (log phiên này, repo gốc):** Nghiệp merge tay.
5. Merge PR: vẫn do Nghiệp làm tay khi chạy auto mode. Có thể gỡ 2 rule `gh pr merge` khỏi `settings.local.json` vì không có tác dụng, hoặc giữ nếu sau này chạy chế độ khác.

## Lưu ý kỹ thuật cho phiên sau

- **Auto mode của Claude Code chặn 2 loại hành động, kể cả khi Nghiệp đã đồng ý trong chat:**
  - `gh pr merge` (lý do "Merge Without Review");
  - agent tự sửa settings quyền (lý do "Self-Modification").
  Đồng ý trong chat không mở khoá được, và rule allow trong settings cũng không (đã thử thật ở PR #6).
  → Merge PR: agent mở PR + báo CI, Nghiệp merge tay.
- **Dán rule vào `/permissions`:** mỗi rule một ô. Dán 2 rule chung một ô thì dấu ngoặc bị escape và rule hỏng.
- **Từ Bash tool (Git Bash) gọi `wsl -- bash /home/...`:** path bị đổi thành `C:/Program Files/Git/home/...`. Dùng PowerShell tool gọi `wsl -d Ubuntu -- bash <file>`.
- **TripPlanner local trước đó đứng ở nhánh `docs/context-md` (PR #47 cũ).** Đã chuyển về `main`.
- **`accounts/aa365/lambda_src/dfs_balance_check.zip` untracked ở repo Infra.** Là artefact build của AA-627, không commit.
