---
name: aa-linear-issue
description: Tạo, cập nhật và đóng issue Linear cho AA_Ecosys theo chuẩn của Nghiệp — kiểm trùng trước khi tạo, template Problem/Scope/Done-when kiểm chứng được, đúng project và độ ưu tiên, xác minh số issue trước khi ghi, và chỉ đóng khi có bằng chứng. Dùng khi tạo issue, comment, đổi trạng thái, hoặc giao issue cho Claude Code/Kiro.
---

# aa-linear-issue

Team: `AA_Ecosys`. Issue viết bằng **tiếng Anh**; comment trao đổi với Nghiệp có thể tiếng Việt.

## Trước khi tạo

1. **Kiểm trùng:** `list_issues` với `query` là 2–3 từ khoá chính, kể cả Backlog. Có issue gần giống → comment hoặc mở rộng scope issue đó, không tạo mới.
2. **Chọn 1 trong 3 project** (gom lại S231, 12/10/2026; mọi issue phải gắn 1 project; 1 project **không quá 100 issue chưa lưu trữ** (cả mở lẫn đã đóng; Nghiệp chốt S236) — gần ngưỡng thì báo Nghiệp và đề xuất lưu trữ/gộp trước khi tạo thêm):
   - `CIS Core — Pipeline, LLM & Platform` — backend App + Infra: A/T pipeline, rerun, review, LLM gateway, judge, Jev, eval, jobs, CI, bảo mật, auth, docs/skill
   - `CIS Portal — Admin & Tenant UI` — trang admin/portal, UI kit, design system
   - `TripPlanner & AA-Booking` — AA-TripPlanner-Web + AA-Booking (AAA)
   - Workspace Linear gói Free: trần 250 issue chưa lưu trữ; **không nâng gói** (Nghiệp, S245). Ba việc thay cho lưu trữ tay (UI không có nút Archive):
     (1) **1 issue = 1 lát việc giao được** (~1 PR hoặc nhóm PR nhỏ); việc chi tiết nằm trong plan/checklist local (`docs/backlog/tracker/plan.json`, file đợt) — chương trình lớn (CRM, Writing Memory) chỉ vài issue mỗi đợt.
     (2) Cuối phiên chạy `python3 tools/linear/linear_export.py` (xuất mọi issue Done/Canceled kèm comment ra `docs/linear-export/`, commit vào root PR) rồi `--archive` (dry run) → `--archive --apply`.
     (3) **Không xoá issue** để trống chỗ: issue xoá mất hẳn sau 30 ngày cùng comment bằng chứng. Báo số issue chưa lưu trữ theo project cuối phiên.
3. **Ưu tiên:** Urgent = đang hỏng production hoặc mất dữ liệu; High = chặn wave/việc kế tiếp hoặc rủi ro bảo mật; Medium = cải tiến có ích; Low = để sau.

## Template

```markdown
## Problem
Chuyện gì xảy ra, ở đâu, bằng chứng (phiên S<nnn>, PR, số liệu). Không viết "có thể".

## Scope
1. … (cụ thể đến file/bảng/endpoint khi biết)
Out of scope: …

## Done when
- Điều kiện kiểm chứng được trên môi trường thật (curl/query/screenshot), không phải "code merged".

## Related
AA-xxx (vì sao liên quan)
```

Title: `[Area] <việc cần làm> — <chi tiết chính>`, ví dụ `[T11] Idempotent publish — …`.

## Definition of Ready (trước khi giao Kiro/subagent/lane)

Issue chỉ được giao khi đủ các mục dưới (thêm dưới template trên; mẫu đầy đủ: `docs/templates/definition-of-ready.md`, AA-887). Thiếu → bổ sung trước, chưa giao.

- [ ] **Goal** — 1–2 câu kết quả nghiệp vụ.
- [ ] **Scope** ghi repo/schema/file và phần out of scope.
- [ ] **Done when** 3–6 tiêu chí kiểm được trên Dev (không phải "code merged").
- [ ] **Verify** — lệnh curl/trang/query/workflow cụ thể chứng minh live.
- [ ] **Risk class** — none | auth | migration | IAM/secret | delete | cost | LLM; lớp rủi ro → `kiro-reviewer` trên PR.
- [ ] **Dependencies** — issue/PR/migration phải xong trước (`blocks`/`blockedBy`).
- [ ] **Docs impact** — CONTEXT.md | ADR | runbook | contract | ID trong catalog `docs/README.md` | none.
- [ ] **Cost** — 0 USD, hoặc ước tính USD/tháng cho resource AWS mới / chạy trả phí (DM-10.7; LLM: subset + `stage=adhoc_<issue>`).

## Cập nhật

- **Trước khi ghi vào issue nào: `get_issue` và kiểm title khớp nội dung.** Từng gọi nhầm số issue 3 lần trong một phiên (30/07).
- Phát hiện mới trong lúc làm → comment vào issue (ngày + bằng chứng), không sửa lặng lẽ description.
- Việc phát sinh ngoài scope → issue mới + `relatedTo`, không nhồi vào issue hiện tại.
- Dùng `blocks` / `blockedBy` khi thứ tự là bắt buộc (ví dụ AA-729 chặn AA-724).

## Đóng

- PR ghi `Refs AA-xxx`, không auto-close.
- Chỉ chuyển Done sau khi `aa-ship` mục 3 pass, kèm comment "Verified live …".
- Thiếu bằng chứng → In Review, ghi rõ còn thiếu gì.
