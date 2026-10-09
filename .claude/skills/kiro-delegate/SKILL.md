---
name: kiro-delegate
description: Chế độ "dùng kiro-cli" — Claude Code chọn việc + gác cổng, kiro-cli (Kiro) viết code và tự lặp tới khi CI + UI smoke trên Vercel preview xanh. CHỈ dùng khi Nghiệp mở phiên bằng "bắt đầu session mới, dùng kiro-cli" (hoặc bật rõ giữa phiên). Gồm preflight credit, phân việc Kiro/Claude, brief ngắn trỏ Linear, gác cổng cuối, reviewer chỉ khi rủi ro, fallback về Claude.
---

# kiro-delegate (v3, S221)

Nguyên tắc: **Kiro làm tới khi xanh trên preview, Claude chỉ gác cổng.** Token Claude tốn nhất ở phiên dài và
vòng review/đo tay — v3 cắt cả hai.

## Khi nào bật
- **Chỉ khi Nghiệp nói** "bắt đầu session mới, dùng kiro-cli" (hoặc bảo bật giữa phiên). Không có câu đó → Claude tự viết code, KHÔNG gọi Kiro.
- **Phân việc (Nghiệp chốt S221):**
  - **Kiro:** backend/logic/migration có test đo được; thay đổi cơ học nhiều file; refactor phạm vi rõ; UI theo mockup/issue đã chốt (Kiro tự xem ảnh smoke).
  - **Claude tự làm:** sửa < ~80 dòng, hotfix; CI/workflow, auth/bảo mật; điều tra nguyên nhân gốc; chỉnh thẩm mỹ sau khi Kiro xanh mà lệch thiết kế.
  - Luôn ở Claude: DRY RUN/ghi DB, AWS/Terraform, merge/deploy/verify live, Linear/Jira/Notion, ADR, trao đổi với Nghiệp.

## 0. Preflight (đầu phiên + trước mỗi task)
`bash .claude/skills/kiro-delegate/kiro-preflight.sh` → exit 0 = sẵn sàng (in credit còn lại).
- Exit 3 (credit < 100 hoặc ≥ 95%), 4 (chưa cài/login), 5 (`/usage`/ping lỗi): **báo Nghiệp** + **chuyển về Claude viết code** cho phần còn lại của phiên.
- Login hết hạn: Nghiệp chạy `kiro-cli login --license pro --identity-provider https://noventiq-aws-lab.awsapps.com/start --region us-east-1`.

## 1. Giao việc — brief ngắn (10–20 dòng)
1. Repo đích: `git checkout main && git pull && git checkout -b <feat|fix|chore>/<aa-xxx>-<slug>`.
2. Chép `brief-template.md` → `.tmp-session/kiro/<task-id>/brief.md`. Điền: issue Linear (Scope + Done when = hợp đồng), 1–3 dòng riêng (quyết định của Nghiệp, file:dòng, bẫy), `## Files in scope`, `## Test commands` (kiro_check.py đọc 2 mục này). **Không chép lại nội dung issue.** Phần "Standard rules" giữ nguyên — nó gồm vòng lặp push → CI preview → tự sửa.
3. Chạy nền: `bash .claude/skills/kiro-delegate/kiro-run.sh <task-id> <workdir>` (`run_in_background: true`). Không poll.

## 2. Kiro tự lặp tới khi xanh (không cần Claude)
Kiro: test local xanh → `git push` branch → chờ CI (mỗi ~4′) → `UI smoke (Playwright)` tự chạy trên Vercel preview
(credential nằm ở GitHub secrets, Kiro không cầm secret nào) → đỏ thì `gh run view --log-failed` (smoke in trang lỗi,
body API, phần tử tràn / nền sáng) + `gh run download` xem ảnh → sửa → push, tối đa 3 vòng.
`aa-worker` cấm: push main/master, force-push, `gh pr merge`, `gh workflow run`, `gh secret`, aws/terraform/psql/sudo.

## 3. Claude gác cổng (đọc ít)
Thư mục `.tmp-session/kiro/<task-id>/`: `meta.txt` (exit, credit, `FLAGS: n`), `checks.md`, `result.md`, `transcript.md`, `diff.patch`, `commits.txt`.
1. Đọc `meta.txt` + `result.md` (run id CI cuối) + `gh pr checks`/`gh run list` của branch.
2. UI: xem 2–4 ảnh của trang đã đổi (`gh run download`, crop phần liên quan). Lệch thiết kế nhỏ → Claude sửa trực tiếp; lớn → `feedback-<n>.md` + `kiro-run.sh <task-id> <workdir> <feedback>` (resume đúng session; path tương đối được).
3. **Subagent `kiro-reviewer` chỉ khi rủi ro:** đụng auth/middleware/quyền, migration/schema, CI/workflow/secret, xoá dữ liệu, hoặc `checks.md` có flag không giải thích được. Việc UI/logic thường → bỏ qua.
4. Xanh + ảnh ổn → Claude mở PR ("code written by Kiro (aa-worker), gated by Claude Code"), theo `aa-ship` (merge/deploy/verify live). Ghi `kiro_credits_task` vào implementation notes.

## 4. Giữ token Claude thấp
- **Một issue lớn (hoặc nhóm nhỏ) = một phiên Claude mới**, nối bằng memory + session log + Linear. Phiên dài làm MỌI lượt đắt hơn — đây là khoản tiết kiệm lớn nhất.
- Không đọc transcript/diff nguyên khối; không tự đo/screenshot khi smoke đã xanh trừ bước xem 2–4 ảnh.
- Output khi Claude tự chạy: `-q` + `tail`.

## Bẫy
- Log headless (`run.clean.log`) chỉ có tên lệnh → nguồn sự thật là `transcript.md`/`session.jsonl`.
- `/usage` cũng tạo session; script chọn session có đường dẫn brief.
- Một task = một branch = một thư mục log; không chạy 2 task Kiro cùng repo cùng lúc; không sửa `kiro-run.sh` khi Kiro đang chạy. Dọn `.tmp-session/kiro/<task-id>` sau khi PR merge.
- Smoke chỉ chạy khi có Vercel preview (thay đổi frontend). Backend-only: CI unit/integration là cổng; verify live sau deploy vẫn là việc của Claude.
