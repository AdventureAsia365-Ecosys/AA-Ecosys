---
name: aa-session
description: Nghi thức bắt đầu và kết thúc một phiên làm việc AA_Ecosys — đầu phiên đọc memory HOT + backlog sống + master plan, kiểm STS/ECS/bảng job, đề xuất danh sách issue theo slot; trong phiên giữ checklist sống và bài học chờ; cuối phiên chụp snapshot trạng thái live, soạn draft Jira cho Nghiệp duyệt, rồi mới ghi log/memory/tracker, đóng gói skill đã đổi, để nguyên môi trường. Dùng khi Nghiệp nói "bắt đầu session mới", "dừng session này", "đầu phiên", "kết thúc/chốt phiên", "wrap up", nêu số phiên (ví dụ S251), hoặc khi một phiên AA bắt đầu mà chưa có bối cảnh.
---

# aa-session

Thứ tự ưu tiên khi nguồn lệch: repo > Notion trang canonical > memory > skill. Lệch thì báo Nghiệp, không im lặng chọn.

## Bắt đầu phiên

1. **Đọc trạng thái đã ghi:** Notion `memory.md` HOT (Program Brain — chỉ workspace `AA_Ecosys`), log local mới nhất
   `docs/sessions/`, backlog sống `docs/backlog/README.md` (mục "Time-gated checks", "Waiting on Nghiệp") và master
   plan `docs/backlog/tracker/plan.json`. Không đọc archive trừ khi cần lịch sử cũ; không audit lại toàn Linear
   (chỉ khi backlog cũ hơn ~2 tuần).
   - Connector Notion/Linear/Jira lỗi (404, "not connected") mà `claude mcp list` báo Connected → registry của phiên đã
     cũ (hay gặp sau khi đổi tài khoản claude.ai): báo Nghiệp mở lại phiên, không debug. Không có Notion thì đọc HOT
     block từ log local.
2. **Kiểm trạng thái thật**, so với memory (lệnh AWS một dòng, `--profile aa365-admin --region us-west-1`):
   - STS còn hạn: `aws sts get-caller-identity --profile aa365-admin` (hết hạn → Nghiệp nhập MFA).
   - ECS cluster `aa-cis-dev-cluster`, 5 service `aa-cis-dev-api`, `aa-cis-dev-worker`, `aa-booking-dev-api`,
     `aa-crm-dev-api`, `aa-crm-dev-web`: running = desired, rollout COMPLETED; api và worker CIS cùng image SHA.
     Service nào đang tắt → **không tự bật**; báo Nghiệp (agent không bao giờ tự bật/tắt hạ tầng).
   - Bảng job `shared.job`, `booking.job`, `crm.job`: queued/running (query không lọc thời gian). Truy vấn qua ECS exec
     chỉ phiên điều phối làm được (hook chặn subagent).
   - Jev canary `credit_ok` và số dư DFS, nếu phiên có chạy pipeline.
   - **Chỉ khi Nghiệp nói "dùng kiro-cli"**: chạy `.claude/skills/kiro-delegate/kiro-preflight.sh`, ghi credit Kiro vào
     khối trạng thái. Lỗi / credit thấp → báo và làm phiên này bằng Claude (skill `kiro-delegate`).
3. **Đề xuất danh sách issue** theo master plan: trước hết issue có `session` = phiên này, rồi slot kế, rồi theo thứ tự
   milestone; mỗi dòng ghi slot (S-số + milestone); bỏ qua hay kéo lên sớm thì nói vì sao. Slot là **thứ tự, không
   phải cổng**: việc đủ điều kiện kỹ thuật thì kéo lên làm. Chỉ phụ thuộc thật mới chặn (migration phải áp trước, bảng
   job bận, MFA, tiền, quyết định chỉ Nghiệp/chị Thư đưa ra). Không tự đặt trần "≤ N việc mỗi lane".
   - Cỡ phiên: 3–5 issue; Ultracode bật → 8–10 issue chạy liên tục bằng lane song song.
   - Liệt kê mọi issue **In Progress**: đủ Done-when → đóng ngay kèm bằng chứng (`aa-ship`); còn ít → làm xong trong
     phiên; bị chặn → ghi rõ cái gì chặn. Ưu tiên làm xong việc dở trước việc mới.
   - Mỗi issue `get_issue` để chắc title đúng.
4. **Báo lệch:** state thật khác memory (revision, job treo, issue đã đóng, PR mở) → nói ngay trước khi làm.
5. **Đọc bài học:** mục liên quan trong `aa-lessons/lessons.md`, và `.tmp-session/S<nnn-1>-lessons-pending.md` nếu
   phiên trước chưa chuyển hết.
6. **Rà soát định kỳ (AA-838, data standards C4.3 / C8 / DM-8.10)** — đến hạn thì đưa vào danh sách việc của phiên:
   - **Tuần (C4.3):** phiên đầu mỗi tuần ISO, và sau mỗi wave: `pg_stat_statements` top 20 theo role (tổng + mean),
     slow log > 500 ms, lock wait, PI top SQL. Ghi 1 đoạn trong log phiên ("C4.3 tuần W<nn>"); hạn = log phiên gần nhất
     có dòng đó cách ≥ 7 ngày. Mục tiêu C1.2 trượt 2 tuần liên tiếp → báo Nghiệp (C1.2a).
   - **Tháng (C8):** phiên đầu mỗi tháng: rà soát dung lượng + chi phí (9 mục C8b, danh sách quyết định C8c), lưu
     `docs/audits/<date>-S<nnn>-capacity-review/` qua root PR. Hạn = folder `*capacity*` mới nhất trong `docs/audits/`
     thuộc tháng trước. Cách làm + script: folder đầu tiên `docs/audits/2026-10-28-S255-aa838-capacity/`.
   - **Quý (DM-8.10):** phiên đầu mỗi quý: rà soát quyền (role, grant, default ACL, IAM đọc secret DB, user Cognito
     `aa-workforce`), lưu `docs/audits/<date>-S<nnn>-access-review/`. Hạn = folder `*access-review*` mới nhất thuộc quý trước.
   - Không bao giờ chạy `pg_stat_statements_reset()` trừ ngay sau một rà soát tháng đã lưu snapshot top 50 (C4.3a).

Đầu ra: một khối ngắn gồm trạng thái (3–5 dòng), lệch nếu có, danh sách việc kèm slot.

## Trong phiên

- **Checklist sống:** đầu phiên tạo `.tmp-session/S<nnn>-checklist.md` — issue gom theo nhóm, mỗi dòng `[x]` xong /
  `⏳` đang chạy / `⛔` bị chặn + lý do / `[ ]` chưa làm, cộng mục "Ràng buộc" và "Quyết định của Nghiệp". Báo
  Nghiệp mở bằng Markdown Preview (Ctrl+Shift+V). Cập nhật sau mỗi bước xong; lúc chốt phiên nó là nguồn cho log.
- **Bài học chờ:** tìm ra nguyên nhân gốc → ghi ngay 1 dòng (mẫu `aa-lessons`) vào `.tmp-session/S<nnn>-lessons-pending.md`.
- **Mỗi issue khi bắt đầu:** 3–6 dòng tiếng Việt cho Nghiệp — vấn đề / làm gì / ai làm / kiểm thế nào. Việc rộng
  (audit, migration nhiều file, nghiên cứu nhiều nguồn) mà Ultracode đang tắt → một dòng gợi ý bật.
- **Điều phối và subagent:** subagent không push, merge, `gh workflow run`, Terraform apply, DB Migrate, ECS exec
  (hook `.claude/hooks/subagent-guardrails.sh`; hook chỉ đọc dòng lệnh nên brief phải nói rõ, kể cả khi gọi qua
  script helper). Brief lane kết thúc bằng mục "bước live cho điều phối"; lane "verify live" chỉ chuẩn bị runbook/
  script, điều phối chạy. Mỗi lane một thư mục scratch riêng; script dùng lâu hơn một lượt để trong
  `.tmp-session/S<nnn>/`, không để trong scratchpad. Số lane theo RAM (`free -h`, chừa ≥ ~2 GB).
- **Push / PR / merge** chỉ điều phối, qua `tools/github/as-app.sh` (GitHub App `aa-agent`), theo `aa-ship`.
- **Bước auto mode chặn** (đổi quyền IAM/Cognito, ghi secret…) → gom vào một cửa sổ, báo trước bước nào cần, xong thì
  báo ngay "bật lại auto mode được rồi".
- **Câu hỏi cho Nghiệp:** bối cảnh bằng lời thường + đề xuất trả lời sẵn; nhiều câu → một trang quyết định bấm chọn.
  Câu hỏi mở không phải lý do dừng: làm theo đề xuất, báo để Nghiệp đảo nếu muốn. Chỉ dừng vì chặn thật.
- **Dev không chờ:** không treo việc sau "đợi N ngày / cửa sổ đếm"; tự tạo traffic/bằng chứng ngay rồi đóng.
- **Audit/báo cáo/artifact** sinh ra trong phiên → lưu ngay vào `docs/audits/<yyyy-mm-dd>-S<nnn>-<slug>/` (kèm link
  artifact) để vào root PR cuối phiên.
- Quyết định kiến trúc → đề xuất ADR (`ai-nghiep/references/adr.md`). Issue xong → `aa-ship` (verify live rồi mới Done).
- Wave đang chạy → `aa-wave-rerun`; deploy backend CIS / DB Migrate chỉ trong khoảng nghỉ giữa wave.
- **Làm xong rồi mới nói tới chốt phiên:** còn việc tự làm được (In Progress, phát hiện phụ, bước kiểm live) thì làm
  tiếp, không liệt kê lại thành lời nhắc. Chốt phiên chỉ khi Nghiệp nói "dừng session này" hoặc mọi việc còn lại
  đều bị chặn thật (kèm cái gì chặn). Không chốt khi task Kiro của phiên còn chạy: chờ, gác cổng, mở PR rồi mới ghi log.

## Kết thúc phiên

Thứ tự bắt buộc: **chốt việc → kiểm nguồn thật → bài học → Jira duyệt + đăng → mới ghi log / memory / tracker**.
Log ghi sau cùng nên có cả kết quả Jira và số liệu đã kiểm, không chép từ trí nhớ của phiên.

1. **Chốt việc + Linear.** Issue đã verify → Done kèm comment bằng chứng; đang dở → In Progress kèm còn lại gì và cái gì
   chặn.
2. **Kiểm nguồn thật (snapshot), trước khi viết bất cứ log nào.** Mọi con số trong log / memory / tracker lấy từ bước
   này (revision, SHA, migration hay lệch khi phiên dài):
   - STS acc2.
   - ECS: mỗi service trong 5 service ở trên → task definition đang chạy (family:revision), image tag, rollout,
     running/desired; api và worker CIS cùng SHA. Revision mới nhất của mỗi family phải là revision đang chạy — một
     Terraform apply chạm ECS để lại revision mẫu mà deploy kế tiếp sẽ chép (xem `aa-lessons`, mục Vận hành).
   - Endpoint: CIS `/health` + `/health/ready`; Booking `/booking/health` + `/booking/health/ready`; CRM api
     `/crm/health` + `/crm/health/ready`; CRM web `/healthz`; git_sha khớp ECS. TripPlanner: web `/api/health` (Vercel,
     có `git_sha`); hai Lambda không có health → gọi một route browse (`/api/browse?resource=countries`) và đọc
     `CodeSha256` của `aa-tripplanner-dev-browse` / `-assembly`. Host: bảng repo của `docs/ecosystem-architecture.md`.
   - Migration mới nhất mỗi owner (CIS, `bk-`, `tp-`, `crm-`): `/health/ready` hoặc dòng "Verified" của
     `docs/architecture/db-schema-reference.md`.
   - Vercel: commit của deployment Production từng project (CIS admin, Booking admin, TripPlanner, portal — portal
     deploy từ AA-Partner).
   - Bảng job `shared.job` / `booking.job` / `crm.job` và wave: còn job / wave mở / cờ nào đang giữ?
   - Mỗi repo (gốc + 5 con: CIS, Booking, TripPlanner, Partner, Infra): head nhánh mặc định, PR còn mở, CI run cuối;
     soát commit lạ xoá nhiều file trên main (squash từ base cũ có thể revert âm thầm).
   - Ghi rõ thứ **cố ý để BẬT** cho phiên sau (cờ/route của wave đang dở).
   - Lệch giữa snapshot và điều phiên tưởng → xử lý hoặc ghi rõ là lệch; không viết log theo điều tưởng.
   Ghi vào `docs/audits/<date>-S<nnn>-<slug>/state-snapshot.md` (tiếng Việt, chỉ tên/số, không account ID, ARN hay
   giá trị secret).
3. **Bài học:** chuyển `.tmp-session/S<nnn>-lessons-pending.md` vào `aa-lessons/lessons.md` (đúng mục, tiếng Việt), rà
   cái còn thiếu. Lưu ý kỹ thuật lặp lại ≥ 2 phiên → đưa vào skill phù hợp rồi xoá khỏi memory.
4. **Jira — nháp → Nghiệp duyệt → đăng, TRƯỚC khi ghi log** (`aa-jira-update`): rà **mọi issue Jira chưa Done**
   (`project in (PR, KAN, CON) AND statusCategory != Done`), đối chiếu commit/PR của phiên theo chủ đề, đọc comment
   gần nhất để không lặp. Soạn draft (số liệu từ snapshot; mỗi khẳng định có bằng chứng live + ảnh; chỉ báo việc đã
   ship). Dán **nguyên văn mọi draft** trong tin nhắn cuối phiên, đưa duyệt **một lần**; **không tự đăng** khi chưa
   duyệt. Đăng xong ghi link comment (hoặc "chưa đăng: lý do") vào `docs/audits/<date>-S<nnn>-<slug>/jira-drafts.md`.
   Ngoại lệ: tách phiên trong **cùng ngày** → draft gom sang phiên sau, ghi rõ trong log.
5. **Rồi mới ghi**, tất cả từ snapshot (bước 2) + kết quả Jira (bước 4):
   - **Log local** `docs/sessions/<yyyy-mm-dd>-S<nnn>-<slug>.md` (ghi rõ tác nhân) + index `docs/sessions/README.md`
     (có mục Jira: đã đăng / chờ).
   - **Session block** prepend vào đầu Notion `memory.md` HOT, đúng format:
     ```
     ## S<nnn> (<dd/mm/yyyy>, <Kiro|Claude Code|Claude Chat> — <môi trường>): <tiêu đề ngắn>
     **Quyết định của Nghiệp** — chỉ quyết định Nghiệp nói, không phải đề xuất của agent
     **Kết quả chính** — issue + PR + bằng chứng verify
     **Trạng thái kiểm cuối phiên** — revision/SHA/migration từ snapshot
     **Việc cần làm đầu phiên sau (S<nnn+1>)** — có thứ tự
     **Lưu ý kỹ thuật** — chỉ điều mới, chưa có trong skill
     ```
     **Chỉ prepend.** Agent không cắt, không di chuyển, không xoá session block cũ; Nghiệp tự chuyển phiên cũ sang
     archive bằng tay. Không có connector Notion → để block trong log local cho phiên sau dán.
   - **Backlog sống** `docs/backlog/README.md` + `docs/backlog/tracker/plan.json`, publish lại trang tracker theo
     `docs/backlog/tracker/README.md` (link nằm ở đó). Artifact thuộc tài khoản claude.ai đã publish nó: sau khi đổi
     tài khoản, `read` trước; bị từ chối ghi → publish trang mới dưới tài khoản hiện tại và cập nhật link trong README.
6. **Skill đổi trong phiên → đóng gói cho claude.ai:** `tools/skills/package_skills.sh --changed <commit đầu phiên>` →
   `skill/dist/<tên>.zip` (mỗi zip một skill); báo Nghiệp danh sách zip cần upload (`skill/README.md`).
7. **Linear export + archive:** `python3 tools/linear/linear_export.py --archive` (dry run) rồi thêm `--apply`. Root PR
   gom log / audit / backlog / lessons → chờ Docs lint xanh → điều phối tự merge. Mọi repo (gốc + 5 con) về
   `main`/`master` cây sạch; dọn worktree và file tạm (S3 scripts, `.tmp-session` của phiên).
8. **KHÔNG dừng môi trường.** Agent không tự `cis-stop`/`cis-start`, scale ECS, stop RDS/NAT — chỉ Nghiệp làm hoặc yêu
   cầu rõ. Tách phiên cùng ngày khi wave đang dở → giữ nguyên cờ/route wave, ghi trong handoff cái gì đang BẬT và wave
   kế tiếp; chỉ trả cờ khi chuỗi wave xong hoặc gặp điều kiện dừng.
9. **Tóm tắt 3 dòng** cho Nghiệp: đã làm / còn lại (và cái gì chặn) / phiên sau bắt đầu từ đâu.
