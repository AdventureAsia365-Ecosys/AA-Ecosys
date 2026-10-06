# Prompt cho Claude Code / Kiro — hoàn thiện bộ skill AA (AA-733)

Copy nguyên khối dưới đây:

```
## Task: Hoàn thiện bộ skill AA tái cấu trúc — Refs AA-733

Mục tiêu: Bộ skill nháp trong `skill-draft/` (9 skill) phải khớp code và cách làm việc thật hiện tại. Output là `skill-draft/` đã sửa, kèm `skill-draft/VERIFY-LOG.md`.

Repo: AA-CIS-App (đặt bộ nháp ở `skill-draft/` cạnh `skill/` hiện có)
Branch: chore/aa-733-skill-restructure từ main → PR → main

Đọc trước:
- skill-draft/README.md — nguyên tắc + bản đồ cũ→mới
- skill/*.md — bản skill hiện tại trong repo (có thể MỚI hơn bản trên Claude)
- .kiro/steering/* — steering Kiro hiện tại
- docs/CONTEXT.md, docs/adr/*, docs/architecture/db-schema-reference.md
- Notion memory.md HOT (Program Brain) — 3 phiên gần nhất

Luật:
- Không thêm lại nội dung cũ chỉ vì nó có trong skill cũ. Mỗi dòng giữ lại phải đúng với code/AWS hiện tại.
- Điều đã bị thay → xoá. Không ghi "lỗi thời", "cũ", "SAI".
- Không chép bảng schema; trỏ tới db-schema-reference.md.
- Không ghi số đang đổi (revision ECS, số tour, migration mới nhất).
- SKILL.md ≤ ~150 dòng; tổng toàn bộ ≤ ~55 KB (bản cũ 114 KB; tiếng Việt có dấu tốn byte).
- Giữ nguyên frontmatter `name`. Được sửa `description` cho đúng trigger.
- Tiếng Việt, câu ngắn. Lệnh AWS một dòng, có --profile/--region.

Các bước:
1. Liệt kê mọi mốc `VERIFY` và `SINH LẠI` (grep "VERIFY\|SINH LẠI" skill-draft -r).
2. Với mỗi mốc: kiểm bằng code (git grep, find), AWS (describe, read-only) hoặc DB (ECS exec read-only). Sửa nội dung cho đúng, rồi xoá comment mốc.
3. Sinh lại references/cis-app.md (router, page, job kind) và references/pipeline.md (stage → code → bảng) từ repo.
4. So skill/*.md và .kiro/steering/* với bộ nháp. Điều gì có trong bản hiện tại, còn đúng, còn giá trị lâu dài mà bộ nháp chưa có → thêm vào đúng chỗ (thường là lessons.md hoặc gotchas.md). Ghi vào VERIFY-LOG.
5. Kiểm description của 9 skill: mỗi cái nêu rõ khi nào dùng, không chồng chéo nhau.
6. Chuyển "Dead Table Registry" từ skill aa-cis-schema cũ (bản trên Claude hoặc skill/aa-cis-schema.md) sang docs/architecture/dead-table-registry.md — nguyên văn bảng, thêm dòng đầu nêu nguồn và ngày.
7. Đo: wc -l */SKILL.md, du -sh skill-draft. Ghi vào VERIFY-LOG.

VERIFY-LOG.md gồm:
- Bảng: mốc | file | kết luận | bằng chứng (lệnh/kết quả rút gọn)
- Nội dung đã thêm từ skill/ hoặc steering hiện tại (và vì sao)
- Nội dung đã xoá mà bộ nháp có (và vì sao)
- Câu hỏi cần Nghiệp quyết (không tự quyết)

Verify:
- grep -rn "VERIFY\|SINH LẠI\|lỗi thời\|SAI\b" skill-draft → chỉ còn trong VERIFY-LOG.md
- wc -l skill-draft/*/SKILL.md → mỗi file ≤ ~150

Kết thúc:
- Commit "chore: restructure AA skills draft (Refs AA-733)", mở PR, chưa merge.
- Nén skill-draft/ thành zip để Nghiệp upload lại cho Claude Chat review.
```
