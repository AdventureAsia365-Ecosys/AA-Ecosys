---
name: ai-nghiep
description: Nền tảng làm việc với Nghiệp trên chương trình AA_Ecosys (AA-CIS, TripPlanner, AA-Booking, AA-Partner trên AWS acc2) — luật cứng, phân công công cụ (Chat / Claude Code / Kiro, điều phối / subagent), nguồn sự thật, AWS account và profile, cách viết ADR, giọng văn với người liên quan, template giao việc, và bản đồ load skill AA nào khi nào. Dùng khi bắt đầu một việc AA_Ecosys chưa rõ skill nào, khi cần luật cứng / AWS account / Bedrock satellite / quyết định kiến trúc hay ADR, khi review tiếng Anh hoặc soạn tin Zalo/email cho người ngoài nhóm kỹ thuật hay tin cho đại lý/reseller AWS (comment Jira thuộc aa-jira-update), hoặc khi viết prompt giao việc cho Claude Code/Kiro.
---

# ai-nghiep — làm việc với Nghiệp (AA_Ecosys)

Skill này chỉ giữ những thứ **ổn định**. Trạng thái đang đổi (ECS revision, số tour, migration mới nhất, issue đang làm)
KHÔNG nằm ở đây — đọc nguồn live (mục 4).

## 1. Người và cách làm việc

- Nghiệp: solo AI/DevOps + technical architect tại Adventure Asia. Mid-senior — không giải thích kiến thức cơ bản.
- Ngôn ngữ: trao đổi với Nghiệp tiếng Việt; code, commit, PR, Linear, tài liệu kỹ thuật tiếng Anh. Log phiên, memory
  Notion và audit viết cho Nghiệp (`docs/audits/`) tiếng Việt; guide cho chị Thư và guide theo vai trò song ngữ EN–VI.
  Xưng tôi/bạn hoặc mình/bạn.
- Trả lời: kết luận trước, giải thích sau. Không filler, không nhắc lại câu hỏi.
- Đã duyệt hướng thì làm trọn tới cuối; tự quyết việc nhỏ và báo lại, chỉ dừng khi bị chặn thật (MFA, tiền, quyết
  định chỉ Nghiệp/chị Thư đưa ra). Hỏi thì kèm bối cảnh bằng lời thường + đề xuất trả lời sẵn.
- Môi trường local: WSL2 / Ubuntu / Zsh / VSCode. Agent coding: Claude Code và Kiro (cùng đọc `skill/` trong repo).
  Tài khoản claude.ai hiện tại: `info@adventure.asia` (skill upload lại ở đó).

## 2. Luật cứng

1. **Verify, không assume.** Mọi claim về state (DB, ECS, deploy, issue) phải có lệnh/query/curl chứng minh. "Có thể do…" không phải kết luận.
2. **Root cause trước symptom.** Ưu tiên fix tất định (code, check, constraint) hơn chỉnh prompt.
3. **"Done" = đã verify live** trên domain thật (curl 200 + shape, hoặc screenshot), không phải build pass. Xem `aa-ship`.
4. **Xoá dữ liệu vĩnh viễn** theo quy trình 5 bước DRY RUN (xem `aa-cis-schema` → `references/destructive-ops.md`).
5. **AWS CLI một dòng** (multi-line với `\` treo trên WSL2). Không SSH — dùng ECS Exec/SSM. Không hardcode secret.
6. **Trước khi ghi vào một issue Linear/Jira, `get_issue` xác minh title khớp ngữ cảnh** — không tin số issue nhớ từ đầu phiên.
7. **Comment Jira và tin nhắn cho người ngoài nhóm kỹ thuật: soạn nháp → Nghiệp duyệt → mới đăng.** Xem `aa-jira-update`.
8. **Không tự đánh giá đầu ra của chính mình là bằng chứng.** Judge khác vendor writer; check tất định thắng LLM self-score.
9. **Không tự bật/tắt hạ tầng** (scale ECS, stop/start RDS, NAT). Dev chạy liên tục; chỉ Nghiệp làm hoặc yêu cầu rõ.
10. **Terraform apply chỉ qua workflow** `terraform-apply.yml` của AA-CIS-Infra; migration chỉ qua workflow DB Migrate. Không chạy từ máy cá nhân.

## 3. Phân công công cụ

Chia theo **nơi tài nguyên nằm**, không theo "Chat không được viết code":

| Việc | Ở đâu | Lý do |
|---|---|---|
| Sửa code repo, migration, Terraform, ECS exec, chạy wave | Claude Code / Kiro (local) | Repo, git, STS profile nằm ở máy local |
| Thiết kế, ADR, review, phân tích tài liệu | Claude Chat | Không cần repo |
| Linear / Notion / Jira | Bất kỳ bên nào có connector | Chat và Claude Code đều có MCP |
| Báo cáo dài (>200 dòng, nhiều bảng) | Claude Code tạo thẳng trang Notion / artifact từ file, bản gốc lưu `docs/audits/` | Tránh cắt mất nội dung khi chép qua chat |

Trong Claude Code, **phiên điều phối** và **subagent** khác quyền:

- Điều phối: push / mở PR / merge qua `tools/github/as-app.sh` (GitHub App `aa-agent`), `gh workflow run` (deploy,
  Terraform apply, DB Migrate), ECS exec, kiểm live. Giai đoạn dev: tự merge khi CI xanh, kể cả PR hạ tầng/bảo mật;
  PR rủi ro (auth/quyền, migration, CI/workflow/secret, xoá dữ liệu) cho agent review độc lập trước.
- Subagent: viết code, test, review, chuẩn bị runbook/script. Hook `.claude/hooks/subagent-guardrails.sh` chặn
  push, merge, `gh workflow run`, Terraform apply, ECS exec và lệnh AWS ghi — bước live luôn trả về cho điều phối.

Khi giao việc cho Claude Code/Kiro: dùng template ở `references/handoff-prompt.md`.

## 4. Nguồn sự thật (đọc theo thứ tự)

| Cần biết | Nguồn | Ghi chú |
|---|---|---|
| Trạng thái hiện tại, việc đầu phiên | Notion `memory.md` HOT (Program Brain) + `docs/sessions/` | Đọc đầu mỗi phiên (`aa-session`) |
| Thứ tự việc, milestone | `docs/backlog/README.md` + `docs/backlog/tracker/plan.json` | Slot là thứ tự, không phải cổng |
| Stack, ranh giới, ownership từng app | `CONTEXT.md` của repo đó; cả hệ: `docs/ecosystem-architecture.md` | Đọc trước khi thiết kế/sửa code; thắng Notion khi lệch |
| Tên bảng/cột DB | `docs/architecture/db-schema-reference.md` (repo gốc) | Sinh tự động (DB Schema Dump), không sửa tay |
| Chủ schema / migration | `docs/database/schema-ownership.md` | App không migrate schema app khác |
| Việc đang làm, ưu tiên | Linear team `AA_Ecosys` | |
| Quyết định kiến trúc | `docs/adr/` của repo gốc và từng app | Format ở `references/adr.md` |
| Yêu cầu nghiệp vụ từ chị Thư (Ms. Thu) | Jira (PR, KAN, CON) | |
| Bài học từ sự cố | `aa-lessons/lessons.md` | Đọc mục của vùng code trước khi sửa |

Khi hai nguồn lệch nhau: repo > Notion trang canonical > memory > skill. Báo lệch cho Nghiệp, đừng tự chọn im lặng.

## 5. Hệ sinh thái trong vài dòng

- **AA-CIS-App** — FastAPI api + job worker (`shared.job`) + admin Next.js. Admin tier A0–A4 (ingest → rewrite → QA →
  Master → atomize/segment/score/route) và Content studio API `/v1/*` cho tenant (T-tier: viết lại theo brand,
  Slate → Angle → Write → Gate → Publish). Bản `portal/` đông lạnh đã xoá (AA-979 dọn dẹp, S256).
- **AA-Partner** — CRM cho đại lý đối tác (api chạy cả `crm.job` worker trong process + web, ECS ARM64) và tenant
  portal / Content studio (ECS `aa-crm-dev-portal`, cùng host `portal.` với CRM web; deploy từ repo này).
- **AA-Booking (AAA)** — back office đặt tour (api + `booking.job` worker, staff admin trên Vercel), nhận catalog từ CIS.
- **AA-TripPlanner-Web** — B2C map-first planner (Next.js + 2 Lambda), đọc catalog/atom từ CIS.
- **AA-CIS-Infra** — Terraform acc2 (ECS, RDS, S3, Lambda, API Gateway, Cognito) + workflow DB Migrate / DB Schema Dump.
- Chỉ CIS ghi nội dung; app khác đọc qua view. Atom, Segment, Score, Route, Hub là platform-wide (một lần cho cả
  pool Master, scope theo `tour_id`, không per-tenant). Slate/Subject mới là per-tenant.
- Chi tiết: `aa-ecosys-repos`. DB: `aa-cis-schema`.

## 6. Load skill nào khi nào

| Tình huống | Skill |
|---|---|
| Bắt đầu / kết thúc phiên | `aa-session` |
| Chuẩn bị merge, deploy, Terraform apply, đánh Done | `aa-ship` |
| Sửa hoặc thêm trang UI | `aa-ui-verify` |
| Tạo, cập nhật, đóng issue Linear | `aa-linear-issue` |
| Báo cáo cho chị Thư trên Jira | `aa-jira-update` |
| Chạy lại pipeline cho một nước / wave | `aa-wave-rerun` |
| Query DB, ECS exec, migration, xoá bảng | `aa-cis-schema` |
| Tìm file/router/page, Terraform, repo nào | `aa-ecosys-repos` |
| Phát hiện lỗi do làm sai cách; trước khi sửa một vùng code | `aa-lessons` |

## 7. References (load khi cần)

- `references/aws.md` — account map, profile, runtime acc2, LLM routing, môi trường chạy liên tục, CLI / ECS exec / Terraform
- `references/adr.md` — khi nào viết ADR, đặt ở repo nào, đánh số, format, các quyết định đã khoá
- `references/stakeholders-english.md` — người liên quan, giọng văn theo người đọc, tin cho đại lý/nhà cung cấp (checklist câu hỏi AWS/Bedrock), review tiếng Anh
- `references/handoff-prompt.md` — template giao việc cho Claude Code/Kiro

## Bảo trì skill này

- Thêm điều mới → sửa đúng mục, **không** nối khối "ADDITIONS" ở cuối.
- Điều cũ bị thay → **xoá**, không ghi chú "lỗi thời". Lịch sử ở git.
- Luật nào đã thành CI check → xoá khỏi mục 2.
- Sửa xong → đóng gói lại cho claude.ai (`aa-session`, bước đóng gói skill).
