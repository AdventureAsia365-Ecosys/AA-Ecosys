# Bộ skill AA_Ecosys — bản tái cấu trúc (nháp 06/10/2026)

Issue: AA-733. Nguồn phân tích: tài liệu "Harness Engineering → AA-CIS", mục 8.3.

## Vì sao

3 skill cũ cộng lại 114 KB. Trong đó có 8 khối "ADDITIONS" nối đuôi và 83 chỗ ghi "lỗi thời/SAI/cũ". Một số nội dung đã sai so với thực tế: atom per-tenant, Step Functions, account AAA đã đóng. Agent đọc phải cả phần đúng lẫn phần sai, rồi tự đoán cái nào còn hiệu lực.

## Nguyên tắc của bộ mới

1. Mỗi `SKILL.md` ≲ 150 dòng. Chi tiết nằm trong `references/`, chỉ load khi cần (progressive disclosure).
2. Điều cũ bị thay thì **xoá**, không chú thích "lỗi thời". Lịch sử nằm ở git và Notion archive.
3. Skill không chứa số đang đổi (revision, số tour, issue đang làm). Những số đó đọc từ memory.md HOT hoặc verify live.
4. Không chép thứ đã có nguồn trong repo (schema → `db-schema-reference.md`, kiến trúc → `CONTEXT.md`); skill chỉ trỏ tới.
5. Luật nào đã thành CI check thì xoá khỏi skill.
6. Một nguồn duy nhất: thư mục `skill/` trong repo → đồng bộ sang Kiro steering và upload lên Claude.

## Bản đồ cũ → mới

| Cũ | Mới |
|---|---|
| `ai-nghiep` §1, §2, §12 | `ai-nghiep/SKILL.md` §1–3 |
| `ai-nghiep` §3 Session ritual | `aa-session` |
| `ai-nghiep` §4 AWS | `ai-nghiep/references/aws.md` |
| `ai-nghiep` §5 CI/CD, git | `aa-ship`, `ai-nghiep/references/handoff-prompt.md` |
| `ai-nghiep` §6 FastAPI, frontend notes | `aa-lessons/lessons.md`, `aa-ui-verify` |
| `ai-nghiep` §7 schema rules | AAA → `aa-ecosys-repos/references/booking.md`; CIS → `aa-cis-schema` |
| `ai-nghiep` §8 pipeline Step Functions | **xoá** (thay bằng `aa-ecosys-repos/references/pipeline.md`) |
| `ai-nghiep` §9–10 ADR, techstack | `ai-nghiep/references/adr.md` |
| `ai-nghiep` §11, §14 người, tiếng Anh | `ai-nghiep/references/stakeholders-english.md` |
| `ai-nghiep` §13 memory sources | `ai-nghiep/SKILL.md` §4 + `aa-session` |
| `ai-nghiep` 8 khối ADDITIONS | nguyên tắc → `lessons.md`; chi tiết sự cố → xoá |
| `ai-nghiep` cert alignment, sprint phrase log | **xoá** (cần thì chuyển sang skill học tập riêng) |
| `aa-cis-schema` bảng cột, FK, overview | **xoá** → trỏ `db-schema-reference.md` |
| `aa-cis-schema` ECS exec, gotchas, phương pháp | `aa-cis-schema/references/*` |
| `aa-cis-schema` Dead Table Registry | Chuyển vào `docs/architecture/dead-table-registry.md` ở repo gốc AA-Ecosys |
| `aa-ecosys-repos` §1–5 | `aa-ecosys-repos/SKILL.md` + `references/cis-app.md`, `infra.md` |
| `aa-ecosys-repos` §6–7 pipeline, gates | `references/pipeline.md` |
| `aa-ecosys-repos` §8–9 chưa xác nhận, dọn dẹp 27/08 | **xoá** (lịch sử) |
| — | Mới: `aa-ship`, `aa-ui-verify`, `aa-linear-issue`, `aa-jira-update`, `aa-wave-rerun` |

## Cấu trúc

```
ai-nghiep/        SKILL.md + references/{aws, adr, stakeholders-english, handoff-prompt}.md
aa-lessons/       SKILL.md + lessons.md (sổ bài học — ghi ngay khi gặp lỗi do làm sai cách)
aa-session/       SKILL.md
aa-ship/          SKILL.md
aa-ui-verify/     SKILL.md
aa-linear-issue/  SKILL.md
aa-jira-update/   SKILL.md
aa-wave-rerun/    SKILL.md
aa-cis-schema/    SKILL.md + references/{ecs-exec, gotchas, destructive-ops}.md
aa-ecosys-repos/  SKILL.md + references/{cis-app, pipeline, infra, tripplanner, booking}.md
```

## Bước tiếp

1. Đưa thư mục này vào `skill/` của repo, kèm `MIGRATION-PROMPT.md` cho Claude Code hoặc Kiro.
2. Agent xử lý mọi mốc `<!-- VERIFY ... -->` và `<!-- SINH LẠI ... -->` dựa trên code thật.
3. Upload lại cho Claude Chat review theo `REVIEW-CHECKLIST.md`.
4. Upload lên Claude (Settings → Skills), đồng bộ sang Kiro steering, xoá bản cũ.
