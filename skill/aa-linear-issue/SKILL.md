---
name: aa-linear-issue
description: Tạo, cập nhật và đóng issue Linear cho AA_Ecosys theo chuẩn của Nghiệp — hỏi trước khi tạo, kiểm trùng, template Problem/Scope/Done-when kiểm chứng được, đúng project và độ ưu tiên, xác minh số issue trước khi ghi, giữ quota gói Free (export + archive), và chỉ đóng khi có bằng chứng. Dùng khi tạo issue, comment, đổi trạng thái, giao issue cho Claude Code/Kiro, hoặc dọn/archive issue Linear.
---

# aa-linear-issue

Team: `AA_Ecosys` (key `AA`). Issue (title, description) và comment viết bằng **tiếng Anh**
(`.kiro/steering/language-convention.md`); trao đổi về issue với Nghiệp trong chat thì tiếng Việt.

## Trước khi tạo

1. **Hỏi Nghiệp trước khi tạo issue mới** (steering `session-workflow.md`). Đưa sẵn title + Problem/Scope đề xuất
   bằng lời dễ hiểu để Nghiệp chỉ cần đồng ý; nhiều issue thì gom một lần.
2. **Kiểm trùng:** `list_issues` với `query` là 2–3 từ khoá chính, kể cả Backlog. Có issue gần giống → comment hoặc mở
   rộng scope issue đó, không tạo mới.
3. **Chọn project** — mọi issue gắn đúng 1 project. Danh sách hiện có đọc bằng `list_projects` (team `AA_Ecosys`);
   chia việc theo phạm vi:
   - `CIS Core — Pipeline, LLM & Platform` — backend CIS: A/T pipeline, rerun/wave, review, LLM gateway, judge, Jev, eval, job runner CIS, CI, docs/skill
   - `CIS Portal — Admin & Tenant UI` — UI admin CIS, UI kit, design system
   - `TripPlanner & AA-Booking` — AA-TripPlanner-Web + AA-Booking
   - `Partner CRM — AA-Partner` — app AA-Partner (CRM api + web) và các lane đi kèm, kể cả việc chuyển portal tenant sang AA-Partner
   - `Data Platform — Schema, Ops & Scale` — RDS dùng chung, migration safety, drift, retention, FinOps/cost, bảo mật tài khoản, ops
4. **Ưu tiên:** Urgent = đang hỏng production hoặc mất dữ liệu; High = chặn wave/việc kế tiếp hoặc rủi ro bảo mật;
   Medium = cải tiến có ích; Low = để sau.

## Quota (Linear gói Free, không nâng gói — S245)

Trần 250 issue chưa lưu trữ cho cả workspace; mỗi project giữ dưới ~100 issue chưa lưu trữ (gần ngưỡng → báo Nghiệp).
UI không có nút Archive, nên:

1. **1 issue = 1 lát việc giao được** (~1 PR hoặc nhóm PR nhỏ). Việc chi tiết nằm trong plan/checklist local
   (`docs/backlog/tracker/plan.json`, file đợt). Chương trình lớn (CRM, Writing Memory) chỉ vài issue mỗi đợt.
2. **Cuối phiên: export rồi archive** bằng `tools/linear/linear_export.py` (cách dùng + các cờ `--archive`, `--apply`,
   `--only`, `--rescue-trash`, `--rescue-open-archived`: `tools/linear/README.md`). Export vào `docs/linear-export/`,
   commit trong root PR cùng phiên (script chỉ archive issue có file export khớp `updatedAt`); luôn đọc dry run trước `--apply`.
3. **Không xoá issue** để trống chỗ: issue xoá mất hẳn sau 30 ngày cùng comment bằng chứng.
4. **Không gắn issue kế hoạch làm sub-issue của một issue sẽ đóng sớm** — archive cha là archive luôn mọi con đang mở;
   dùng `relatedTo` (bài học trong `skill/aa-lessons/lessons.md`, mục Vận hành).

## Template

```markdown
## Problem
What happens, where, evidence (session S<nnn>, PR, numbers). No "might".

## Scope
1. … (down to file/table/endpoint when known)
Out of scope: …

## Done when
- Checkable on the real environment (curl/query/screenshot), not "code merged".

## Related
AA-xxx (why related) · Jira: <key> when the issue serves a Jira request
```

Title: `[Area] <việc cần làm> — <chi tiết chính>`, ví dụ `[Admin] Apps page — health, version, links`,
`[CRM W3] CRM-16 Agency-line ledger + suppliers`. Không ghi mã Jira trong title.

**Liên kết Jira:** issue làm cho một yêu cầu Jira (PR, KAN, CON) ghi `Jira: <key>` ở mục Related. Chiều ngược lại
không có: comment Jira không bao giờ chứa mã Linear (`aa-jira-update`).

## Definition of Ready (trước khi giao Kiro/subagent/lane)

Issue chỉ được giao khi đủ các mục dưới (thêm vào template trên; mẫu đầy đủ + checklist: `docs/templates/definition-of-ready.md`).
Thiếu → bổ sung trước, chưa giao.

- [ ] **Goal** — 1–2 câu kết quả nghiệp vụ.
- [ ] **Scope** ghi repo/schema/file và phần out of scope.
- [ ] **Done when** 3–6 tiêu chí kiểm được trên Dev (không phải "code merged").
- [ ] **Verify** — lệnh curl/trang/query/workflow cụ thể chứng minh live. Bước cần ECS exec / DB live là việc của
      agent điều phối (hook chặn subagent); subagent chỉ chuẩn bị runbook/script.
- [ ] **Risk class** — none | auth | migration | IAM/secret | delete | cost | LLM; lớp rủi ro → `kiro-reviewer` trên PR.
- [ ] **Dependencies** — issue/PR/migration phải xong trước (`blocks`/`blockedBy`).
- [ ] **Docs impact** — CONTEXT.md | ADR | runbook | contract | ERD thiết kế | ID trong catalog `docs/README.md` | none.
- [ ] **Cost** — 0 USD, hoặc ước tính USD/tháng cho resource AWS mới / chạy trả phí (DM-10.7; LLM: subset + `stage=adhoc_<issue>`).

## Cập nhật

- **Trước khi ghi vào issue nào: `get_issue` và kiểm title khớp nội dung.** Từng gọi nhầm số issue 3 lần trong một phiên.
- Phát hiện mới trong lúc làm → comment vào issue (ngày + bằng chứng), không sửa lặng lẽ description.
- Việc phát sinh ngoài scope → issue mới (hỏi Nghiệp) + `relatedTo`, không nhồi vào issue hiện tại.
- Dùng `blocks` / `blockedBy` khi thứ tự là bắt buộc (ví dụ migration phải apply trước code đọc cột mới).
- **In Progress không được đọng:** issue đã đạt Done-when → đóng có bằng chứng; phần còn lại nhỏ → làm xong; bị chặn →
  ghi rõ cái gì chặn và trả về Backlog/Todo nếu không ai làm (memory `in-progress-must-converge`).

## Đóng

- Commit/PR ghi `Refs AA-xxx` trong thân. Tiêu đề PR không chứa mã issue (kể cả dạng `fix: AA-123 …` — Linear đọc
  thành câu đóng issue). Thân PR chỉ nhắc mã của issue mà PR thật sự làm. CI `pr-title` đã chặn `[AA-xxx]` trong tiêu đề
  và từ khoá đóng issue trong thân ở AA-Booking, AA-Partner, AA-TripPlanner-Web; repo gốc, AA-CIS-App, AA-CIS-Infra
  chưa có guard nên tự kiểm.
- Linear vẫn có thể tự chuyển Done khi merge/deploy/DB Migrate dù chỉ có `Refs`: sau mỗi merge/apply/deploy của issue
  còn mở, `get_issue` kiểm status và mở lại nếu bị đóng nhầm (bài học trong `lessons.md`, mục Verify và "Done").
- Chỉ chuyển Done khi `aa-ship` (verify live + Đánh Done) pass, kèm comment "Verified live …" có bằng chứng.
- Thiếu bằng chứng → In Review, ghi rõ còn thiếu gì.
