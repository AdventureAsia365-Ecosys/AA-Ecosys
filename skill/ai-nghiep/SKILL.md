---
name: ai-nghiep
description: Cách làm việc với Nghiệp trên chương trình AA_Ecosys (AA-CIS, TripPlanner, AA-Booking/AAA) — luật cứng, phân công công cụ, nguồn sự thật, và bản đồ để biết load skill AA nào khi nào. Dùng cho mọi việc liên quan AA_Ecosys, AWS acc2/acc3, FastAPI, PostgreSQL, Bedrock, Linear/Notion/Jira của AA, hoặc quyết định kiến trúc.
---

# ai-nghiep — làm việc với Nghiệp (AA_Ecosys)

Skill này chỉ giữ những thứ **ổn định**. Trạng thái đang đổi (ECS revision, số tour, issue đang làm) KHÔNG nằm ở đây — đọc nguồn live (mục 4).

## 1. Người và cách làm việc

- Nghiệp: solo AI/DevOps + technical architect tại Adventure Asia. Mid-senior — không giải thích kiến thức cơ bản.
- Ngôn ngữ: tiếng Việt cho trao đổi nội bộ; tiếng Anh cho Linear issue, PR, deliverable chính thức. Xưng tôi/bạn hoặc mình/bạn.
- Trả lời: kết luận trước, giải thích sau. Không filler, không nhắc lại câu hỏi.
- Môi trường local: WSL2 / Ubuntu / Zsh / VSCode. Agent coding: Claude Code và Kiro (cùng đọc `skill/` trong repo).

## 2. Luật cứng

1. **Verify, không assume.** Mọi claim về state (DB, ECS, deploy, issue) phải có lệnh/query/curl chứng minh. "Có thể do…" không phải kết luận.
2. **Root cause trước symptom.** Ưu tiên fix tất định (code, check, constraint) hơn chỉnh prompt.
3. **"Done" = đã verify live** trên domain thật (curl 200 + shape, hoặc screenshot), không phải build pass. Xem `aa-ship`.
4. **Xoá dữ liệu vĩnh viễn** theo quy trình 5 bước DRY RUN (xem `aa-cis-schema` → `references/destructive-ops.md`).
5. **AWS CLI một dòng** (multi-line với `\` treo trên WSL2). Không SSH — dùng ECS Exec/SSM. Không hardcode secret.
6. **Trước khi ghi vào một issue Linear/Jira, `get_issue` xác minh title khớp ngữ cảnh** — không tin số issue nhớ từ đầu phiên.
7. **Comment Jira và tin nhắn cho người ngoài nhóm kỹ thuật: soạn nháp → Nghiệp duyệt → mới đăng.** Xem `aa-jira-update`.
8. **Không tự đánh giá đầu ra của chính mình là bằng chứng.** Judge khác vendor writer; check tất định thắng LLM self-score.

> "Không deploy/merge backend khi `shared.job` còn queued/running" đã thành CI check (deploy workflow có pre-deploy job guard + post-deploy live smoke), không còn là luật phải tự nhớ.

## 3. Phân công công cụ

Chia theo **nơi tài nguyên nằm**, không theo "Chat không được viết code":

| Việc | Ở đâu | Lý do |
|---|---|---|
| Sửa code repo, migration, Terraform, ECS exec, chạy wave | Claude Code / Kiro (local) | Repo, git, STS profile nằm ở máy local |
| Thiết kế, ADR, review, phân tích tài liệu | Claude Chat | Không cần repo |
| Linear / Notion / Jira | Bất kỳ bên nào có connector | Chat và Claude Code đều có MCP |
| Báo cáo dài (>200 dòng, nhiều bảng) | Claude Code tạo thẳng trang Notion từ file | Tránh cắt mất nội dung khi chép qua chat |

Khi Chat giao việc cho Claude Code/Kiro: dùng template ở `references/handoff-prompt.md`.

## 4. Nguồn sự thật (đọc theo thứ tự)

| Cần biết | Nguồn | Ghi chú |
|---|---|---|
| Trạng thái hiện tại, việc đầu phiên | Notion `memory.md` HOT (Program Brain) | Đọc đầu mỗi phiên |
| Kiến trúc content pipeline | `CONTEXT.md` + `docs/adr/` trong AA-CIS-App | Thắng Notion khi lệch |
| Tên bảng/cột DB | `docs/architecture/db-schema-reference.md` (AA-CIS-App) | Regenerate sau mỗi migration |
| Việc đang làm, ưu tiên | Linear team `AA_Ecosys` | |
| Quyết định kiến trúc | ADR Log (Notion) + `docs/adr/` | Format ở `references/adr.md` |
| Yêu cầu nghiệp vụ từ chị Thư (Ms. Thu) | Jira (PR, KAN, CON) | |

Khi hai nguồn lệch nhau: repo > Notion trang canonical > memory > skill. Báo lệch cho Nghiệp, đừng tự chọn im lặng.

## 5. Hệ sinh thái trong 5 dòng

- **AA-CIS-App** — FastAPI + Next.js. Admin tier A0–A4 (ingest → rewrite → QA → Master → atomize/segment/score/route) và tenant tier (T0–T4 rewrite theo brand, Slate → Angle → Write → Gate → Publish).
- **AA-CIS-Infra** — Terraform cho acc2 (ECS api + worker, RDS, S3, Lambda TripPlanner).
- **AA-TripPlanner-Web** — B2C map-first planner, đọc atom/Master từ CIS.
- **AA-Booking (AAA)** — đang bootstrap (AA-678), nhận catalog qua outbox (AA-679).
- Atom, Segment, Score, Route, Hub là platform-wide (một lần cho cả pool Master, scope theo `tour_id`, không per-tenant). Slate/Subject mới là per-tenant.
- Chi tiết: `aa-ecosys-repos`. DB: `aa-cis-schema`.

## 6. Load skill nào khi nào

| Tình huống | Skill |
|---|---|
| Bắt đầu / kết thúc phiên | `aa-session` |
| Chuẩn bị merge, deploy, đánh Done | `aa-ship` |
| Sửa hoặc thêm trang UI | `aa-ui-verify` |
| Tạo, cập nhật, đóng issue Linear | `aa-linear-issue` |
| Báo cáo cho chị Thư trên Jira | `aa-jira-update` |
| Chạy lại pipeline cho một nước | `aa-wave-rerun` |
| Query DB, ECS exec, xoá bảng | `aa-cis-schema` |
| Tìm file/router/page, Terraform, repo nào | `aa-ecosys-repos` |

## 7. References (load khi cần)

- `references/aws.md` — account map, profile, chain Bedrock, start/stop môi trường, CLI rules
- `references/lessons.md` — các nguyên tắc rút ra từ sự cố thật (ngắn, mỗi dòng một nguyên tắc)
- `references/adr.md` — format ADR, khi nào phải viết, các quyết định đã khoá
- `references/stakeholders-english.md` — người liên quan, giọng văn theo người đọc, review tiếng Anh
- `references/handoff-prompt.md` — template giao việc cho Claude Code/Kiro

## Bảo trì skill này

- Thêm điều mới → sửa đúng mục, **không** nối khối "ADDITIONS" ở cuối.
- Điều cũ bị thay → **xoá**, không ghi chú "lỗi thời". Lịch sử ở git.
- Luật nào đã thành CI check → xoá khỏi mục 2.
