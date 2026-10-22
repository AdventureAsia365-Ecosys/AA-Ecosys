---
name: aa-session
description: Nghi thức bắt đầu và kết thúc một phiên làm việc AA_Ecosys — đọc memory.md HOT, kiểm job/ECS/STS, chốt danh sách việc; cuối phiên prepend session block (không rotate), cập nhật Linear, soạn draft Jira cho Nghiệp duyệt, để nguyên môi trường. Dùng khi Nghiệp nói bắt đầu phiên, "S2xx", "đầu phiên", "kết thúc phiên", "chốt phiên", "wrap up", hoặc khi một phiên AA bắt đầu mà chưa có bối cảnh.
---

# aa-session

## Bắt đầu phiên

1. **Đọc Notion `memory.md` HOT** (Program Brain). Lấy: phiên gần nhất, "việc cần làm đầu phiên sau", lưu ý kỹ thuật, ECS revision cuối. Không đọc archive trừ khi cần lịch sử cũ.
2. **Kiểm trạng thái thật**, so với memory:
   - STS còn hạn: `aws sts get-caller-identity --profile aa365-admin`
   - Môi trường đang chạy? (`cis-status`). Nếu môi trường đang tắt → **KHÔNG tự `cis-start`**; báo Nghiệp và chờ Nghiệp bật. Agent không bao giờ tự bật/tắt hạ tầng.
   - api và worker cùng image SHA, đúng revision memory ghi
   - `shared.job` có job queued/running không (query không lọc thời gian)
   - Jev canary `credit_ok` và số dư DFS, nếu phiên có chạy pipeline
   - **Chỉ khi Nghiệp nói "dùng kiro-cli"** (Claude Code): chạy `.claude/skills/kiro-delegate/kiro-preflight.sh`, ghi credit Kiro còn lại vào khối trạng thái. Lỗi / credit thấp → báo và làm phiên này bằng Claude như thường (skill `kiro-delegate`).
3. **Đưa danh sách 5–10 issue sẽ làm**, theo thứ tự ưu tiên. Mỗi issue `get_issue` để chắc title đúng.
4. **Báo lệch:** nếu state thật khác memory (revision, job treo, issue đã đóng), nói ngay trước khi làm.
5. **Đọc bài học:** lướt các mục trong `aa-lessons/lessons.md` liên quan tới các issue đã chốt.

Đầu ra: một khối ngắn gồm trạng thái (3–5 dòng), lệch nếu có, danh sách việc.

## Trong phiên

- **Checklist sống (S247):** đầu phiên tạo `.tmp-session/S<nnn>-checklist.md` — issue gom theo nhóm, mỗi dòng
  `[x]` xong / `⏳` đang chạy / `⛔` bị chặn + lý do / `[ ]` chưa làm. Báo Nghiệp mở bằng Markdown Preview
  (Ctrl+Shift+V) trong VSCode. Cập nhật sau mỗi bước xong, không dồn cuối phiên. Lúc chốt phiên nó là nguồn cho log.
- **Bài học chờ (S247):** tìm ra nguyên nhân gốc → ghi ngay 1 dòng (mẫu `aa-lessons`) vào
  `.tmp-session/S<nnn>-lessons-pending.md`; cuối phiên (bước 3) chuyển vào `aa-lessons/lessons.md`. Lý do: không mất
  bài học khi phiên dài hay bị ngắt.
- **Làm xong rồi mới đề xuất chốt phiên:** còn việc làm được (In Progress, phát hiện phụ) thì làm tiếp; chỉ liệt kê
  việc thật sự bị chặn, kèm cái gì chặn (memory `finish-before-closing`, S247).
- **Mọi câu hỏi cho Nghiệp:** bối cảnh bằng lời thường + đề xuất trả lời sẵn; không hỏi trống (memory
  `artifact-decisions-interactive`).
- Mỗi quyết định kiến trúc → đề xuất ADR (`ai-nghiep/references/adr.md`).
- Mỗi issue xong → theo `aa-ship` (verify live rồi mới Done).
- Wave rerun → theo `aa-wave-rerun`, không merge backend giữa wave.

## Kết thúc phiên

Thứ tự bắt buộc (Nghiệp chốt S247, 22/10/2026): **chốt việc → kiểm nguồn thật → Jira duyệt + đăng → mới ghi log /
memory / tracker**. Log ghi sau cùng nên có cả kết quả Jira và số liệu đã kiểm, không chép từ trí nhớ của phiên.

1. **Chốt việc + Linear.** Việc làm được thì làm xong trước (memory `finish-before-closing`). Issue đã verify → Done
   kèm comment bằng chứng; đang dở → In Progress kèm ghi chú còn lại gì và vì sao (bị chặn bởi gì).
2. **Kiểm nguồn thật (snapshot), trước khi viết bất cứ log nào.** Mọi con số trong log / memory / tracker lấy từ
   bước này, không lấy từ đoạn chat trước đó (revision, SHA, migration hay bị lệch khi phiên dài):
   - STS: `aws sts get-caller-identity --profile aa365-admin`.
   - ECS: mỗi service `aa-cis-dev-api`, `aa-cis-dev-worker`, `aa-booking-dev-api` → task definition đang chạy
     (family:revision), image tag, `rolloutState` COMPLETED, desired/running; api và worker CIS cùng SHA.
   - Endpoint: `/health` (git_sha) và `/health/ready` (schema_version) của CIS và Booking; khớp SHA ở trên.
   - Migration mới nhất mỗi owner (`shared.schema_versions` / `/health/ready`, hoặc dòng "Verified" của
     `docs/architecture/db-schema-reference.md`).
   - Lambda TripPlanner: `CodeSha256` / mô tả version của `aa-tripplanner-dev-browse` và `-assembly`; Vercel: commit
     của deployment Production từng project.
   - Bảng job `shared.job` / `booking.job`: queued/running = 0?
   - Mỗi repo (gốc + 4 con): `main`/`master` mới nhất, PR còn mở (của phiên hay bot), CI run cuối của main.
   - Lệch giữa snapshot và điều phiên tưởng (VD revision khác, PR chưa merge, deploy chưa chạy) → xử lý hoặc ghi
     rõ là lệch; không viết log theo điều tưởng.
   Ghi snapshot vào `docs/audits/<date>-S<nnn>-…/state-snapshot.md` (tiếng Việt, chỉ tên/số, không giá trị secret).
3. **Bài học:** lỗi do làm sai cách đã ghi ngay vào `aa-lessons/lessons.md` trong phiên (xem `aa-lessons`); cuối phiên
   rà lại, ghi nốt cái còn thiếu. Lưu ý kỹ thuật lặp lại ≥2 phiên → đưa vào skill phù hợp rồi xoá khỏi memory.
4. **Jira — nháp → Nghiệp duyệt → đăng, TRƯỚC khi ghi log** (S237; thứ tự S247): rà các issue Jira (PR, KAN, CON)
   khớp với việc của phiên (`searchJiraIssuesUsingJql` + đọc comment gần nhất để không lặp lại), rồi **soạn draft**
   cập nhật cho từng issue theo `aa-jira-update` (tiếng Việt, mention @thule, không mã nội bộ, số liệu lấy từ
   snapshot bước 2). Đưa Nghiệp duyệt **một lần** trong chat (memory `batch-drafts-at-session-end`); **không tự
   đăng** khi chưa duyệt. Chỉ báo việc đã ship (memory `jira-report-when-done`). Rà **mọi issue Jira chưa Done**
   (`project in (PR, KAN, CON) AND statusCategory != Done`), không chỉ issue có việc trong phiên: mỗi issue đối chiếu
   commit/PR của phiên theo chủ đề (S237 bỏ sót PR-18). Mỗi câu khẳng định trong draft kèm bằng chứng live + ảnh
   (memory `jira-claims-need-live-evidence`). Nghiệp duyệt → đăng → ghi link comment đã đăng (hoặc "chưa đăng: lý
   do") vào `docs/audits/<date>-S<nnn>-…/jira-drafts.md`.
5. **Rồi mới ghi**, tất cả từ snapshot (bước 2) + kết quả Jira (bước 4):
   - **Log local** `docs/sessions/<yyyy-mm-dd>-S<nnn>-<slug>.md` + index `docs/sessions/README.md` (có mục Jira:
     đã đăng / chờ).
   - **Session block** prepend vào đầu Notion `memory.md` HOT, đúng format:
     ```
     ## S<nnn> (<dd/mm/yyyy>, <Kiro|Claude Code|Claude Chat> — <môi trường>): <tiêu đề ngắn>
     **Quyết định của Nghiệp** — chỉ quyết định Nghiệp nói, không phải đề xuất của agent
     **Kết quả chính** — issue + PR + bằng chứng verify
     **Trạng thái kiểm cuối phiên** — revision/SHA/migration từ snapshot
     **Việc cần làm đầu phiên sau (S<nnn+1>)** — có thứ tự
     **Lưu ý kỹ thuật** — chỉ điều mới, chưa có trong skill
     ```
     **Chỉ prepend.** Agent không cắt, không di chuyển, không xoá session block cũ. Nghiệp tự chuyển phiên cũ sang
     `memory_archive_2026H2` bằng tay (rotate tự động từng gây lỗi).
   - **Backlog sống** `docs/backlog/README.md` + `docs/backlog/tracker/plan.json`, publish lại trang tracker.
6. **Linear export + archive** (`python3 tools/linear/linear_export.py --archive --apply`), root PR gom log / audit /
   backlog → agent tự merge; mọi repo về `main`/`master` cây sạch, dọn worktree và file tạm (S3 scripts, `.tmp-session`).
7. **KHÔNG dừng môi trường.** Hệ thống để chạy liên tục, ổn định. Agent TUYỆT ĐỐI không tự `cis-stop`/`cis-start`/scale
   ECS/stop RDS/stop NAT — mọi bật/tắt hạ tầng chỉ Nghiệp làm, hoặc Nghiệp yêu cầu rõ. Cuối phiên để nguyên môi trường.
8. **Tóm tắt 3 dòng** cho Nghiệp: đã làm / còn lại (và cái gì chặn) / phiên sau bắt đầu từ đâu.
