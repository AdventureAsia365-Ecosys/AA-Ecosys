---
name: kiro-delegate
description: Giao việc viết code cho kiro-cli (Kiro là "tay chân", Claude Code điều phối + review + verify). Dùng khi một issue AA đã có phạm vi rõ và phần việc chính là viết/sửa code + test — để token viết code tiêu ở Kiro (free) thay vì Claude. Không dùng cho điều tra nguyên nhân gốc, ghi DB, deploy, Terraform.
---

# kiro-delegate

Claude Code giữ: plan, brief, review, chạy lại test, PR, merge/deploy (aa-ship), verify live, Linear, trao đổi với Nghiệp.
Kiro (`kiro-cli`, agent `aa-worker`) làm: viết code + test trên branch riêng, ghi báo cáo.

## Điều kiện
- `~/.local/bin/kiro-cli whoami` ra tài khoản (chưa login → nhờ Nghiệp chạy `kiro-cli login`).
- Agent: `.kiro/agents/aa-worker.json` (script tự symlink vào `~/.kiro/agents/`). Cấm aws/terraform/merge/deploy/push main/psql.

## Quy trình
1. **Branch trước:** trong repo đích `git checkout main && git pull && git checkout -b <feat|fix>/<issue>-<slug>`. Script từ chối chạy trên main/master.
2. **Brief** `.tmp-session/kiro/<task-id>/brief.md` (tiếng Anh), đủ các mục:
   - Issue + mục tiêu (1–3 câu), **phạm vi và ngoài phạm vi**;
   - repo/branch, file liên quan (đường dẫn thật), CONTEXT.md + mục lessons cần đọc;
   - ràng buộc (không đổi schema nếu không nói, không đụng file X…);
   - **lệnh test phải chạy** (vd `python3 -m pytest -q tests/unit -p no:cacheprovider`, `python3 -m flake8 <files>`);
   - điều kiện xong (đo được); có commit hay không (`Refs AA-xxx`);
   - đường dẫn result: `.tmp-session/kiro/<task-id>/result.md` + các mục bắt buộc (Summary, Files changed, Commands run, Test results, Decisions not in the brief, Open questions / risks).
3. **Chạy nền:** `bash .claude/skills/kiro-delegate/kiro-run.sh <task-id> <workdir>` với `run_in_background: true`. Không poll; chờ thông báo.
4. **Review ĐẦY ĐỦ (không chỉ đọc tóm tắt của Kiro):**
   - `meta.txt` (exit code, result/session/transcript có hay MISSING — MISSING = coi như chưa xong);
   - **`transcript.md` — nguồn chính**: mọi tool call của Kiro + output thật (stdout/stderr/exit status, nội dung file đọc/ghi), dựng từ `session.jsonl` của kiro-cli. Đọc hết, đối chiếu từng lệnh và kết quả. (`run.clean.log` chỉ ghi tên lệnh, không có output — S219 smoke test);
   - `diff.patch` — đọc toàn bộ, so với brief: thừa / thiếu / đụng file ngoài phạm vi;
   - `git_status.txt` (file chưa commit), `commits.txt`;
   - `result.md` chỉ là lời khai — mọi khẳng định phải khớp log + diff. Lệch → ghi vào feedback.
5. **Tự chạy lại test** trong workdir (không tin số trong result.md). Lint đúng như CI.
6. **Chưa đạt:** viết `feedback-<n>.md` cùng thư mục (lỗi cụ thể, file:dòng, việc phải làm), thêm vào brief mục "Round n feedback", chạy lại script (task-id giữ nguyên, log cũ đổi tên `run.<n>.log` trước khi chạy).
7. **Đạt:** Claude mở PR (mô tả do Claude viết), theo `aa-ship` để merge/deploy/verify; ghi Linear. Ghi trong implementation notes / PR: "code written by Kiro (kiro-cli aa-worker), reviewed + verified by Claude Code".

## Giữ cho Claude (không giao Kiro)
Điều tra nguyên nhân gốc qua log/DB; DRY RUN + ghi DB; Terraform/AWS; deploy; verify live; Jira/Linear/Notion; quyết định kiến trúc (ADR).

## Bẫy
- Kiro chạy với `--trust-tools` → chặn bằng `deniedCommands` trong agent, nhưng vẫn phải đọc `run.clean.log` để chắc nó không làm việc ngoài brief.
- `.tmp-session/` bị gitignore — log không lên git; dọn thư mục task sau khi PR merge.
- Một task = một branch = một thư mục log. Không chạy 2 task Kiro cùng repo cùng lúc.
