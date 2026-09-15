# Inventory — tham chiếu tên cũ (org / repo / path) trong AA-Ecosys

**Mục đích:** Kiểm kê mọi tham chiếu tới tên org cũ `AdventureAsia365-CIS`, tên repo,
và đường dẫn local cũ, để biết chính xác chỗ nào **PHẢI sửa**, chỗ nào **GIỮ nguyên**
(URL lịch sử bất biến) khi đổi tên org GitHub `AdventureAsia365-CIS` → `AdventureAsia365-Ecosys`.

**Quyết định đã chốt (07/09/2026 trong phiên restructure):**
- CHỈ đổi tên **org**. KHÔNG đổi tên repo nào (`AA-CIS-App`, `AA-TripPlanner-Web`, `AA-CIS-Infra` giữ nguyên).
- Đã đổi tên **thư mục local** cho khớp tên repo: `apps/AA-CIS-App`, `apps/AA-TripPlanner-Web`, `infra/AA-CIS-Infra`.

**Cách đọc bảng:**
- **Loại A — PHẢI sửa (cấu hình bắt buộc):** ảnh hưởng vận hành (OIDC trust). Sửa ở G2.
- **Loại B — NÊN sửa (docs mô tả hiện trạng):** cập nhật cho khớp org/thư mục mới. Sửa ở G3/G9.
- **Loại C — GIỮ nguyên (URL lịch sử / lệnh đã cho phép):** URL PR/run đã xảy ra, hoặc allow-list lệnh cũ. KHÔNG sửa (làm sai lệch lịch sử).

---

## 1. `AdventureAsia365-CIS` (tên org cũ)

| # | File | Dòng | Nội dung | Loại | Ghi chú |
|---|------|------|----------|------|---------|
| 1 | `infra/AA-CIS-Infra/accounts/aa365/cicd.tf` | 25 | `sub = "repo:AdventureAsia365-CIS/*:*"` | **A** | OIDC role `aa-cis-dev-role`. G2: thêm `AdventureAsia365-Ecosys/*` (additive). |
| 2 | `infra/AA-CIS-Infra/accounts/aa365/tripplanner.tf` | 477 | `sub = "repo:AdventureAsia365-CIS*/AA-TripPlanner-Web*:*"` | **A** | OIDC role `aa-tripplanner-dev-app-deploy`. G2: thêm biến thể `-Ecosys*`. |
| 3 | `infra/AA-CIS-Infra/accounts/aa365/tripplanner.tf` | 472–476 | Comment mô tả sub `repo:AdventureAsia365-CIS@<orgid>/...` | **B** | Cập nhật comment giải thích 2-org transitional khi sửa ở G2. |
| 4 | `apps/AA-TripPlanner-Web/docs/vercel-setup.md` | 11 | `github.com/AdventureAsia365-CIS/AA-TripPlanner-Web` | **B** | Đổi org → `AdventureAsia365-Ecosys`. |
| 5 | `infra/AA-CIS-Infra/docs/implementation-notes/AA-TripPlanner-backend.md` | 49 | `repo:AdventureAsia365-CIS/AA-TripPlanner-Web:*` | **B** | Mô tả role hiện tại → cập nhật org. |
| 6 | `skill/ai_nghiep.md` | 789 | `gh workflow run ... --repo AdventureAsia365-CIS/AA-CIS-Infra` | **B** | Lệnh vận hành thực tế → đổi org để lệnh chạy đúng sau rename. |
| 7 | `infra/AA-CIS-Infra/docs/implementation-notes/AA-397.md` | 209, 213, 216, 251 | URL PR #24 / run #31559123177 / comment PR | **C** | **GIỮ** — URL lịch sử (redirect tự động của GitHub vẫn hoạt động). |

---

## 2. Tên repo (`AA-CIS-App` / `AA-CIS-Infra` / `AA-TripPlanner-Web`)

Vì **không đổi tên repo**, các tham chiếu tên repo trong docs/comment về nguyên tắc **không cần sửa**.
Chỉ liệt kê để xác nhận không có chỗ nào giả định tên khác. Không có mục Loại A ở đây.

| # | File | Ghi chú | Loại |
|---|------|---------|------|
| 8 | Nhiều docs trong `apps/AA-TripPlanner-Web/docs/*`, `infra/.../docs/*` | Tham chiếu `AA-CIS-Infra`, `AA-TripPlanner-Web`, `AA-CIS-App` — đúng, giữ nguyên | **C** |
| 9 | `apps/AA-TripPlanner-Web/.kiro/steering/structure.md` (dòng 8) | Cây thư mục mở đầu `AA-TripPlanner-Web/` — đúng tên repo | **C** |
| 10 | `apps/AA-TripPlanner-Web/README.md`, `migrations/001_*.sql` header | Tiêu đề mang tên repo — đúng | **C** |

---

## 3. Đường dẫn local cũ (`~/projects/aa-cis/...`, `~/projects/AA-TripPlanner-Web`)

Đây là **ngoài phạm vi rename org**, nhưng sau khi đổi tên thư mục các path này càng lệch.
Vị trí thực tế hiện tại: `~/projects/AA-Ecosys/{apps/AA-CIS-App, apps/AA-TripPlanner-Web, infra/AA-CIS-Infra}`.

| # | File | Nội dung | Loại | Ghi chú |
|---|------|----------|------|---------|
| 11 | `.claude/CLAUDE.md` (gốc) | `~/projects/aa-cis/` + cây `AA-CIS-App/`, `AA-CIS-Infra/` | **B** | Cập nhật mô tả cấu trúc workspace sang `~/projects/AA-Ecosys/`. |
| 12 | `.claude/settings.local.json` (gốc + mỗi repo) | Nhiều lệnh `git -C /home/nghiep/projects/aa-cis/...` trong allow-list | **C** | **GIỮ** — allow-list lệnh đã chạy, không phải cấu hình sống; sửa không có tác dụng vận hành. |
| 13 | `infra/AA-CIS-Infra/main.tf.bak` / `main.tf.bak2` | `lambda_zip_dir = "/home/nghiep/projects/aa-cis/AA-CIS-Infra/dist/lambdas"` | **C** | **GIỮ** — file `.bak` (backup, không được Terraform đọc). |
| 14 | `apps/AA-TripPlanner-Web/docs/e2e-uat-guide.md` (dòng 5) | `/home/nghiep/projects/AA-TripPlanner-Web` | **B** | Cập nhật path hướng dẫn chạy local sang vị trí mới. |

---

## 4. Tóm tắt hành động

- **G2 (Loại A):** sửa 2 file `.tf` — OIDC trust (mục #1, #2) + comment (#3). Additive, không xoá pattern cũ.
- **G3/G9 (Loại B):** cập nhật docs mô tả hiện trạng org/path — mục #4, #5, #6, #11, #14. (#3 làm chung với G2.)
- **GIỮ nguyên (Loại C):** URL lịch sử (#7), tham chiếu tên repo đúng (#8–10), allow-list & file `.bak` (#12, #13).

**Lưu ý:** OIDC ở `cicd.tf` là org-wide (`.../*`), KHÔNG pin tên repo → việc không đổi tên repo không phát sinh thay đổi OIDC nào ngoài phần đổi tên org.


---

## 5. Kết quả `terraform plan` G2 (15/09/2026, aa365 root)

`Plan: 0 to add, 4 to change, 0 to destroy` — an toàn, không destroy, không đụng RDS/ECS/Lambda code/secret.

| Resource | Thay đổi | Nguồn |
|----------|----------|-------|
| `aws_iam_role.cicd` | `sub` string → list: giữ `repo:AdventureAsia365-CIS/*:*`, thêm `repo:AdventureAsia365-Ecosys/*:*` + `repo:AdventureAsia365-Ecosys*/*:*` | Thay đổi G2 (mình) |
| `aws_iam_role.tripplanner_app_deploy` | `sub` string → list: giữ `...-CIS*/AA-TripPlanner-Web*:*`, thêm `...-Ecosys*/...` | Thay đổi G2 (mình) |
| `aws_s3_object.tripplanner_assembly_zip` | chỉ thêm `tags_all` (default_tags) — KHÔNG đụng etag/source/code | Drift có sẵn, lành tính |
| `aws_s3_object.tripplanner_browse_zip` | chỉ thêm `tags_all` (default_tags) — KHÔNG đụng etag/source/code | Drift có sẵn, lành tính |

→ Sẵn sàng `terraform apply` (Task 6). 2 S3 tag-only là drift phụ, không liên quan đổi tên org.
