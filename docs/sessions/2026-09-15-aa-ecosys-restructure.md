# Session Log — AA-Ecosys Restructure

- **Ngày:** 2026-09-15
- **Agent:** Kiro
- **Chủ đề:** Gom multi-repo về AA-Ecosys + đổi tên org GitHub `AdventureAsia365-CIS` → `AdventureAsia365-Ecosys`
- **Trạng thái:** Hoàn tất 14/15 task. Còn Task 14 (gỡ trust org cũ) do người làm sau vài ngày.

> Mục đích file: để phiên Kiro/Claude Code sau nắm được đã làm gì, thay đổi gì về codebase + hạ tầng,
> mà không phải đọc lại toàn bộ hội thoại.

---

## 1. Kết quả tổng thể

Đổi tên **org** GitHub (KHÔNG đổi tên repo). Đổi tên **thư mục local** cho khớp tên repo. Nguyên tắc
chống rủi ro: mở rộng OIDC trust nhận CẢ tên cũ + mới TRƯỚC, đổi tên SAU, gỡ trust cũ sau cùng (G5, chưa làm).

## 2. Thay đổi CODEBASE

### Thư mục local (đã đổi tên)
- `apps/cis` → `apps/AA-CIS-App`
- `apps/tripplanner` → `apps/AA-TripPlanner-Web`
- `infra/AA-CIS-Infra` (giữ nguyên)
- Mỗi repo giữ `.git` riêng (multi-repo). Đường dẫn thật: `~/projects/AA-Ecosys/`.

### Repo GỐC mới
- Tạo `AdventureAsia365-Ecosys/AA-Ecosys` (private) chứa docs cấp hệ + README + `.claude/CLAUDE.md`.
- `.gitignore` gốc loại: `apps/`, `infra/` (repo con độc lập), `skill/` (giữ LOCAL, không push), `docs/AAA/`.
- Nhánh: `master`.

### PR đã MERGE (mọi CI xanh)
| Repo | PR | Nội dung |
|------|----|----|
| AA-TripPlanner-Web | #43 | docs org/path + gitignore docs/AAA/ |
| AA-CIS-Infra | #59 | OIDC widen trust (transitional) |
| AA-TripPlanner-Web | #44 | configure-aws-credentials @v4→@v6 (Node24) |
| AA-CIS-App | #385 | configure-aws-credentials @v4→@v6 (deploy-dev + eval-regression) |
| AA-CIS-Infra | #60 | configure-aws-credentials @v4→@v6 (terraform-plan/apply) |
| AA-TripPlanner-Web | #45 | tạo mới `.claude/CLAUDE.md` |
| AA-CIS-App | #386 | `.claude/CLAUDE.md` +section RESTRUCTURE |
| AA-CIS-Infra | #61 | `.claude/CLAUDE.md` +section RESTRUCTURE |

### Git remote
- Cả 3 repo `origin` đã trỏ `github.com/AdventureAsia365-Ecosys/<repo>` (script `docs/g3-remote-update.sh`).
- Redirect org cũ vẫn hoạt động.

### Tài liệu tạo mới (`docs/`)
- `ecosystem-architecture.md` — sơ đồ toàn hệ, phân vai schema, data contracts, OIDC.
- `tripplanner-to-aaa-handoff.md` — spec bàn giao TripPlanner → AA-Booking (nháp, chờ AAA).
- `inventory-old-refs.md` — kiểm kê refs cũ + kết quả terraform plan.
- `g3-remote-update.sh`, `g5-remove-old-trust.md` — script/hướng dẫn.

### Skill (LOCAL, không push GitHub)
- `aa-ecosys-repos_SKILL.md` — cập nhật 3 repo, org mới, path mới, TripPlanner, OIDC transitional.
- `aa-cis-schema.md` — thêm mục TripPlanner chia sẻ RDS acc2 (schema `tripplanner.*` + `shared.destinations`).
- `ai_nghiep.md` — org mới ở lệnh gh + ghi chú 3 repo.

## 3. Thay đổi HẠ TẦNG (AWS acc2 005097885195, us-west-1)

### OIDC trust — ĐÃ APPLY (terraform apply, 0 add / 4 change / 0 destroy)
- `aws_iam_role.cicd` (aa-cis-dev-role): `sub` nhận cả `repo:AdventureAsia365-CIS/*:*` + `repo:AdventureAsia365-Ecosys/*:*` (+ 1 biến thể wildcard dư sẽ bỏ ở G5).
- `aws_iam_role.tripplanner_app_deploy`: `sub` nhận cả `...-CIS*/AA-TripPlanner-Web*:*` + `...-Ecosys*/...`.
- 2 S3 object (tripplanner zip) chỉ thêm tag (default_tags), vô hại.
- **KHÔNG đụng** RDS/ECS/Lambda code/secret. Không destroy gì.

### Xác minh OIDC subject
- Org OIDC "Subject claim template" TRỐNG + immutable subject OFF → customization là **repo-level**
  (chỉ AA-TripPlanner-Web bật dạng `@id`), KHÔNG org-level.

## 4. Bằng chứng verify (chạy thật, không chỉ tin CI xanh)
- `git ls-remote` org mới OK + redirect org cũ OK.
- GitHub Actions **Deploy Lambdas #30 = SUCCESS** dưới org mới (OIDC assume role thật).
- CI **Terraform Plan (dev) = PASS** trên PR #59.
- Vercel `aa-tripplanner` Connected Git Repo = `AdventureAsia365-Ecosys/AA-TripPlanner-Web`.

## 5. CÒN LẠI — Task 14 (người, hoãn vài ngày)
Gỡ trust org cũ khi deploy ổn định thuần org mới. Theo `docs/g5-remove-old-trust.md`:
- `cicd.tf`: chỉ giữ `repo:AdventureAsia365-Ecosys/*:*` (dạng phẳng).
- `tripplanner.tf`: chỉ giữ `repo:AdventureAsia365-Ecosys*/AA-TripPlanner-Web*:*`.
- `terraform plan` (kỳ vọng chỉ 2 role đổi) → `apply` (MFA) → verify deploy xanh.

## 6. Lưu ý kỹ thuật cho phiên sau
- **terraform apply cần MFA:** TF không tự prompt. Dùng:
  `export $(aws configure export-credentials --profile aa365-admin --format env | xargs) && unset AWS_PROFILE` rồi chạy terraform.
- **AA-CIS-App có branch protection** (5 CI job) → merge PR phải `gh pr merge --auto` (tự merge khi CI xanh).
- Chạy terraform/git luôn từ đường dẫn WSL `/home/nghiep/...` (không dùng path UNC `\\wsl.localhost`).
- 3 nợ TripPlanner ngoài phạm vi restructure (chưa làm): Icon 6+2 (ActivityIcon), hover tên nước → highlight
  (FilterChips onMouseEnter → focusCountry) — chờ tool ghi bật lại.

---

## Bổ sung cuối phiên (16/09/2026) — MCP + session workflow

### MCP đã thiết lập (workspace-level)
- File `.kiro/settings/mcp.json` (gitignored, chứa token Notion) với 2 server:
  - **Notion** (`@notionhq/notion-mcp-server`, token nội bộ) — ✅ Connected. Đã share integration `Kiro MCP`
    cho Program Brain + Program Dashboard (+ trang con kế thừa). Chỉ làm việc trong Program Brain.
  - **Linear** (`mcp-remote https://mcp.linear.app/mcp`, OAuth) — ✅ Connected sau khi:
    - Sửa endpoint `/sse` → `/mcp` (Linear đã gỡ SSE, /sse trả 404).
    - Cài `wslu` (wslview) để WSL mở được trình duyệt OAuth; hoàn tất authorize (scope read+write).
- Verify: Notion đọc memory.md OK; Linear đọc workspace `AA_Ecosys` + team + issues thật OK.

### Session workflow (steering)
- Tạo `.kiro/steering/session-workflow.md` — quy tắc bắt buộc mọi phiên Kiro:
  - "bắt đầu session mới" → đọc memory Notion + log local + Linear → tổng hợp + chờ chốt.
  - Trong khi làm → hỏi trước khi tạo issue Linear; plan/duyệt việc lớn.
  - "dừng session này" → ghi log local + prepend memory Notion (S mới) + đồng bộ Linear + đảm bảo 3 nguồn nhất quán.
- Quyền MCP: Notion đọc/ghi; Linear đọc + cập nhật trạng thái + tạo issue + comment.

### Đối chiếu state (verify chéo)
- Linear backlog chính sạch, issues gần nhất (AA-585/587/583/582/586/584/577/579/524) đều Done — khớp memory S177/S179.
- AA-586 (Done) = nhánh feature repo AA-CIS-App đang đứng. Linear ↔ repo ↔ memory nhất quán.

### Ghi memory Notion
- Đã prepend **S181** vào đầu `Program Brain/memory.md` (phiên restructure, tác nhân Kiro).
