---
name: kiro-delegate
description: Chế độ "dùng kiro-cli" — Claude Code điều phối, kiro-cli (Kiro) viết code. CHỈ dùng khi Nghiệp mở phiên bằng "bắt đầu session mới, dùng kiro-cli" (hoặc bật rõ giữa phiên). Gồm preflight kiểm credit Kiro, brief, chạy headless, kiểm tra cơ học, review bằng subagent kiro-reviewer, fallback về Claude khi Kiro hết credit/lỗi.
---

# kiro-delegate

## Khi nào bật
- **Chỉ khi Nghiệp nói** "bắt đầu session mới, dùng kiro-cli" (hoặc bảo bật giữa phiên). Không có câu đó → Claude tự viết code như thường, KHÔNG gọi Kiro.
- Bật rồi thì mọi phần **viết/sửa code + test** đi qua Kiro. Claude giữ: điều tra nguyên nhân gốc, DRY RUN/ghi DB, AWS/Terraform, deploy, verify live, Linear/Jira/Notion, ADR, trao đổi với Nghiệp.

## 0. Preflight (đầu phiên + trước mỗi task)
`bash .claude/skills/kiro-delegate/kiro-preflight.sh` → exit 0 = sẵn sàng (in credit còn lại).
- Exit 3 (credit thấp: còn < 100 hoặc đã dùng ≥ 95%), 4 (chưa cài/chưa login), 5 (`/usage` hoặc ping lỗi, rate limit):
  **báo Nghiệp ngay** (trạng thái + credit + ngày reset) và **chuyển về Claude viết code như bình thường** cho phần còn lại của phiên. Không thử lại vòng vo.
- Login hết hạn: Nghiệp chạy trong terminal WSL `kiro-cli login --license pro --identity-provider https://noventiq-aws-lab.awsapps.com/start --region us-east-1`.

## 1. Giao việc (một task = một issue trọn vẹn, không chia vụn)
1. Repo đích: `git checkout main && git pull && git checkout -b <feat|fix|chore>/<aa-xxx>-<slug>` (script từ chối main/master).
2. Brief: chép `brief-template.md` → `.tmp-session/kiro/<task-id>/brief.md`, chỉ điền phần riêng. Bắt buộc có `## Files in scope` và `## Test commands` dạng ``- `...` `` (kiro_check.py đọc 2 mục này). Yêu cầu Kiro tự lặp sửa → test + lint xanh rồi mới báo.
3. Chạy nền: `bash .claude/skills/kiro-delegate/kiro-run.sh <task-id> <workdir>` (`run_in_background: true`). Không poll.

## 2. Review (đọc đầy đủ — trên model rẻ)
Khi script xong, thư mục `.tmp-session/kiro/<task-id>/` có: `meta.txt` (exit code, credit task tiêu, dòng `FLAGS: n`), `checks.md` (kiểm tra cơ học toàn bộ session), `transcript.md` (mọi lệnh + output thật; đọc/ghi file chỉ ghi đường dẫn), `session.jsonl` (bản gốc đầy đủ), `diff.patch`, `commits.txt`, `git_status.txt`, `result.md` (lời khai của Kiro).
1. Gọi subagent **`kiro-reviewer`** (Sonnet) với đường dẫn thư mục task. Nó đọc HẾT brief/checks/transcript/diff/result, tự chạy lại test, trả VERDICT ≤ 40 dòng.
2. Phiên chính chỉ đọc: `meta.txt` + VERDICT + các hunk reviewer chỉ ra (đọc từ `diff.patch` hoặc file trong repo). Không đọc lại transcript/diff toàn bộ trừ khi VERDICT ≠ PASS mà lý do chưa rõ.
3. `NEEDS_CHANGES` → viết `feedback-<n>.md` (file:dòng, việc phải làm), đổi tên log cũ (`run.<n>.log`, `transcript.<n>.md`, `checks.<n>.md`; giữ `meta.txt`), chạy `kiro-run.sh <task-id> <workdir> <feedback-n.md>` — script **resume đúng session Kiro vòng trước** (`--resume-id`, đọc `session=` trong meta.txt) nên Kiro nhớ ngữ cảnh, không đọc lại từ đầu; resume không khởi động được thì tự chạy session mới (meta ghi `resumed=yes|no`). Tối đa 3 vòng; quá thì Claude tự làm nốt và ghi lý do.
4. `PASS` → Claude mở PR (mô tả do Claude viết, ghi "code written by Kiro (aa-worker), reviewed by kiro-reviewer + Claude Code"), rồi theo `aa-ship` (merge/deploy/verify live). Ghi `kiro_credits_task` vào implementation notes.

## 3. Giữ token Claude thấp
- Một brief = một issue trọn (gom việc), Kiro tự lặp tới khi xanh — ít vòng review.
- Phiên chính không đọc transcript/diff nguyên khối; để `kiro-reviewer` đọc.
- Mỗi giai đoạn/issue lớn là một phiên Claude mới (nối tiếp bằng memory + session log) — context dài làm mọi lượt đắt hơn.
- Output test khi Claude tự chạy: `-q` + `tail`.

## Bẫy
- Log headless (`run.clean.log`) chỉ ghi tên lệnh, KHÔNG có output → nguồn sự thật là `session.jsonl`/`transcript.md` (S219 smoke test).
- `/usage` cũng tạo session; script chọn session có chứa đường dẫn brief, không lấy "mới nhất".
- `--trust-tools` + `deniedCommands` chặn aws/terraform/psql/sudo/merge/workflow/secret/push main; `checks.md` vẫn báo nếu Kiro thử.
- Một task = một branch = một thư mục log; không chạy 2 task Kiro cùng repo cùng lúc. Dọn `.tmp-session/kiro/<task-id>` sau khi PR merge.
