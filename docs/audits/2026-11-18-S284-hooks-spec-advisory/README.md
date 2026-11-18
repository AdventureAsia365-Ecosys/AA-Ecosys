# Tư vấn: hooks đồng bộ code → test → docs, và luồng plan → spec → task (S284, 18/11/2026)

Tác nhân: Claude Code. Bản tư vấn cho tech lead, chưa tạo gì trong repo ngoài file này.
Dựa trên: kiểm kê hooks/CI hiện có (đọc repo, chỉ đọc), tài liệu chính thức của Kiro và Claude Code, một bản thiết kế,
và một bản phản biện độc lập. Mục 9 ghi nguồn.

## 1. Trả lời nhanh

- Hiện có 7 Claude hook ở repo gốc. Tất cả là hook **chặn sai lầm** (lệnh shell nguy hiểm, PII, subagent merge, kit core,
  lane không đúng slot, dừng khi checklist còn việc). **Chưa có hook nào nối code với test, docs hay implementation note.**
- Đồng bộ code ↔ test hôm nay nằm ở pre-push và CI (khá chắc). Đồng bộ code ↔ docs/note chỉ dựa vào kỷ luật và checklist
  trong PR template, nên hay sót.
- Đề xuất A: thêm hook kiểu Kiro, nhưng chỉ chạy **script shell xác định** (0 token), **nhắc** trong lúc code, và chỉ
  **chặn ở push/PR**. Một thư viện `tools/sync/` dùng chung cho Claude hook, Kiro hook, pre-push và CI.
- Đề xuất B: dùng đúng định dạng spec của Kiro (`.kiro/specs/AA-<n>-<slug>/requirements.md`, `design.md`, `tasks.md`),
  mỗi tiêu chí có mã R, mỗi task ghi R nào; `lane.js` nhận `spec` + `tasks` và trả về `trace`. Linear chỉ giữ mã R + đường dẫn spec.
- Kiro hook trên CLI cần kiro-cli **3.x** (máy đang 2.28.0), nên phần Kiro để sau.
- Làm 3 lát nhỏ, lát 1 chạy chế độ **chỉ ghi log** một tuần để đo trước khi bật nhắc/chặn.

## 2. Hiện mình đang có gì

### 2.1 Bảng cơ chế

| Sự kiện | Cơ chế | Chặn hay nhắc | Repo |
|---|---|---|---|
| Agent chạy Bash (subagent) | `subagent-guardrails.sh` | Chặn push/merge/deploy/lệnh phá huỷ | Gốc (áp cho mọi lane qua `$CLAUDE_PROJECT_DIR`) |
| Agent chạy Bash có SQL | `pilot-pii-guard.sh` | Chặn trả cột PII bảng tenant | Gốc |
| Agent chạy Bash | `aa-shell-guard.sh` (PKILL-1, RAM-1, TF-1, SHIP-1…) | Chặn | Gốc |
| Khởi động lane (`lane.js`) | `lane-start-guard.sh` | Chặn khi sai args/slot/worktree | Gốc |
| Subagent gọi MCP ghi | `subagent-mcp-guardrails.sh` | Chặn | Gốc |
| Agent sửa `_kit/core`, `ui/core` | `kit-core-edit-guard.sh` | Chặn | Gốc |
| Agent dừng | `stop-open-work.sh` | Chặn 1 lần nếu checklist còn việc | Gốc |
| `git push` | `.githooks/pre-push` → `scripts/pre-push.sh` | Chặn (bỏ được bằng `--no-verify`) | Cả 6 repo |
| Pre-push CIS | flake8 + unit theo file đổi, stamp integration, `code_health`, gitleaks | Chặn | CIS |
| PR | `pr-title.yml` | Chặn | Cả 6 repo |
| PR | CI: unit/integration/coverage ratchet, Q0 red-on-base, contract, kit consumers | Chặn qua merge queue | CIS, Booking, Partner, TripPlanner |
| PR | `docs-lint.yml` (front-matter, ADR index, link) | Chặn | Gốc, Booking, Partner, TripPlanner, Infra |
| Hằng tuần | Docs freshness | Chỉ báo | Gốc |
| Sau migration | DB Schema Dump → PR `bot/db-schema-reference` tự merge | Tự động | Infra → gốc |

### 2.2 Lỗ hổng

1. Không có PostToolUse, SessionStart hay UserPromptSubmit hook. Không có "sửa file → chạy X".
2. Không pre-push hay CI nào kiểm **implementation note** có mặt, **CONTEXT.md** có cập nhật, hay **docs impact**.
   Chỉ có ô tick trong PR template.
3. **AA-CIS-App không có `docs-lint.yml`** (31 trang đã audit, 5 trang sai).
4. "Docs impact" trong template Linear và quy tắc CONTEXT.md chỉ dựa vào người đọc tự giác.
5. `lane.js` bắt `tests` và `live_steps` nhưng không có trường trace hay docs.
6. Repo có `.kiro/agents`, `settings`, `steering`, **không có `.kiro/hooks`, không có `.kiro/specs`** (TripPlanner còn một
   spec mồ côi `tripplanner-mvp`).

## 3. Kiro làm gì

### 3.1 Agent Hooks

- File JSON trong `.kiro/hooks/*.json` (định dạng `{"version":"v1","hooks":[...]}`), hoặc mảng `hooks` trong file agent.
- Trigger: UserPromptSubmit, Stop, SessionStart, PreToolUse (chặn được), PostToolUse, PostFileCreate/Save/Delete,
  PreTaskExec/PostTaskExec (vòng đời task của spec), PreCompact/PostCompact.
- **Trigger file chỉ chạy khi agent sửa file**, không chạy khi người sửa tay trong editor.
- Hai loại action:
  - `command`: chạy shell, stdout vào ngữ cảnh agent, exit khác 0 trên PreToolUse thì chặn. **Không tốn credit.**
  - `agent`: chèn prompt, mở vòng agent mới, **tốn credit**.
- Hook "Manual" đã cũ; thay bằng steering file `inclusion: manual` gọi như `/<tên>`.
- Không thấy trong docs: mã thoát chi tiết của PreToolUse ngoài "khác 0 là chặn"; mẫu hook có sẵn kiểu security scan.

### 3.2 Specs

- Mỗi spec một thư mục `.kiro/specs/<feature>/` gồm `requirements.md` (hoặc `bugfix.md`), `design.md`, `tasks.md`.
- Ba loại: Feature (Requirements-First hoặc Design-First), Bugfix, Quick Spec (sinh cả 3 file một lần, không cổng duyệt).
- `requirements.md` dùng EARS: "WHEN … THE SYSTEM SHALL …".
- `tasks.md`: task rời, có phụ thuộc, bắt buộc/tuỳ chọn; Kiro tự đổi trạng thái. "Run all tasks" chạy task độc lập song song
  theo đợt, task chạm cùng file không chạy song song.
- **Sync Files** sinh task cho yêu cầu mới/đổi. Spec để trong git, một spec một feature.
- Liên kết task ↔ requirement (`_Requirements: 1.1_`) **không có trong docs chính thức**, chỉ có ở template bên thứ ba.
- Plan mode là chế độ nhẹ riêng (hỏi lại, đọc code, ra kế hoạch), không phải bước trước spec.

### 3.3 Chạy headless qua kiro-cli

| Tính năng | CLI 2.28 (đang cài) | CLI 3.x (V3) |
|---|---|---|
| PreToolUse, PostToolUse, Stop, UserPromptSubmit | Có | Có |
| SessionStart, PostFileSave/Create/Delete, PreTaskExec/PostTaskExec | Không | Có |
| Feature/Bugfix/Quick Spec | Docs nói có trên CLI | Có |
| Correctness (property-based testing) | Chỉ IDE | Chỉ IDE |

Lưu ý: `kiro-run.sh` chạy `cd` vào worktree repo con và symlink `aa-worker.json` vào `~/.kiro/agents/`. Vì vậy file
`.kiro/hooks/` ở repo gốc **sẽ không được nạp** khi Kiro chạy lane; hook phải nằm trong mảng `hooks` của `aa-worker.json`.

## 4. Đề xuất A: hooks đồng bộ code → test → docs

### 4.1 Nguyên tắc

1. Script quyết định, model không quyết định. Không dùng Claude `prompt`/`agent` hook hay Kiro `agent` action (tốn token,
   dễ lặp).
2. Chỉ chặn khi kiểm vừa rẻ vừa chắc. Chỉ chặn ở **push/PR**. Trong lúc code chỉ **nhắc**.
3. Một thư viện `tools/sync/` (Python stdlib), nhiều nơi gọi: Claude hook, Kiro hook, pre-push, CI. Theo mẫu
   `shell_guard_core.py` hiện có.
4. Im khi ổn. Phản hồi tối đa ~1.500 ký tự, mỗi điều chỉ nói một lần cho mỗi `session_id` + `agent_id`.
5. Công tắc `AA_SYNC_HOOKS=off|log|warn|block`, hook nào cũng đọc đầu tiên.

### 4.2 Bảng hook

| Khi nào | Nơi chạy | Làm gì | Chặn/nhắc | Thời gian / token |
|---|---|---|---|---|
| Agent sửa file code | Claude `PostToolUse` (`Edit\|Write\|MultiEdit`, `if: Edit(apps/**)`) | Lint nhanh **đúng file đó** (ruff/eslint một file) + `doc_impact.py`: "trang X ánh xạ tới file này, cập nhật hoặc ghi N/A trong note" | Nhắc (`additionalContext`) | < 1 s, 0 token |
| Lane/subagent xong | Claude `SubagentStop`, gộp vào **một** Stop dispatcher cùng `stop_open_work.py` | `change_guard.py`: code đổi mà chưa đổi test, thiếu `docs/implementation-notes/<ISSUE>[-<lane>].md`; gọi bộ chọn test sẵn có của `pre-push.sh` (thêm chế độ `--select-only`) và báo kết quả | Nhắc, chỉ với agent đã tự ghi file | < 2 s cho phần kiểm; phần test theo pre-push |
| Phiên chính bắt đầu/nén | Claude `SessionStart` (`startup\|resume\|compact`) | In đường dẫn spec đang chạy + task kế tiếp từ `plan.json` | Nhắc | ≤ 800 ký tự |
| `git push` | `scripts/pre-push.sh` mỗi repo | Thêm bước `change_guard` + `trace_check` | Cảnh báo ở fast mode; giống CI ở `--full` | < 3 s |
| PR | Workflow tái sử dụng `sync-guards.yml` ở repo gốc | `notes-present`, `test-cochange`, `spec-trace`; `docs-impact` lấy từ AA-1132 A4 | `spec-trace` chặn khi issue có spec; còn lại WARN + một sticky comment | ~30 s mỗi job, không AWS |
| Kiro lane (khi có 3.x) | Mảng `hooks` trong `aa-worker.json`, đường dẫn tuyệt đối, chỉ `command` | `PostFileSave` → lint + `doc_impact`; `Stop` → `change_guard`; `PreToolUse` shell → `aa_shell_guard.py` | Như Claude | 0 credit |

Miễn trừ (waiver) ghi trong implementation note, không ghi trong chat: `No test needed: <lý do>`,
`No note needed: <lý do>` (chỉ cho chore dưới ~20 dòng). Reviewer thấy được, script đếm được theo repo.

Trạng thái hook ở `.tmp-session/hookstate/<session_id>-<agent_id>.json` (gitignored, không lọt ra repo public).

### 4.3 Chi tiết kỹ thuật bắt buộc (từ phản biện)

- Lane làm việc trong worktree bằng đường dẫn tuyệt đối, `cwd` của hook thường là checkout gốc. Phải suy ra repo và
  worktree từ `tool_input.file_path`; với SubagentStop thì dùng bản ghi các worktree mà `agent_id` đó đã ghi.
- Job CI mới bắt buộc ở CIS/Booking/Partner phải nghe `merge_group` và không dùng `paths:` (theo mẫu `kit-consumers.yml`),
  nếu không merge queue sẽ kẹt.
- Miễn job chặn cho PR bot: `bot/db-schema-reference`, release-please, Dependabot.
- Bước pre-push mới không được ghi file (Partner `--from-hook` từ chối cây bẩn).
- Self-test cho trường hợp worktree và `agent_id`, đặt cạnh các test hook hiện có.

## 5. Đề xuất B: luồng plan → spec → task

### 5.1 Nơi đặt

- Spec ở repo chủ: `.kiro/specs/AA-<n>-<slug>/`. Kiro tìm được bằng `#spec` và Sync Files; Claude đọc như file thường.
- Việc nhiều repo: spec ở `.kiro/specs/` của repo gốc, mỗi task ghi `repo:`.
- Lưu trữ: `.kiro/specs/_archive/`. Chuyển spec mồ côi `tripplanner-mvp` vào đó trước.
- `docs-sync.yml` đưa `.kiro/specs/**` vào bundle `/admin/docs`.
- Repo app là public: spec theo DM-6.10, chạy redaction + gitleaks + lint resource ID trên `.kiro/specs/**`.

### 5.2 Định dạng file

`requirements.md` có front-matter: `id`, `issue`, `status`, `owner_repo`, `kind` (feature/bugfix/quick),
`approved_at`. Thân: một đoạn Problem, rồi các tiêu chí EARS đánh mã, mỗi tiêu chí có cách kiểm:

```text
R1.1 WHEN a tenant job fails 3 times THE SYSTEM SHALL mark it dead and emit job.dead.
     Verify: tests/integration/test_job_dead.py; live GET /admin/job-runner/summary shows dead=1
```

`design.md` chỉ bắt buộc khi đụng migration/schema, auth/quyền, ranh giới mới hoặc nhiều repo: quyết định `D1..` kèm mục
CONTEXT.md sẽ đổi, danh sách docs impact (id theo doc-map của AA-1132 A4), chiến lược test cho từng R.

`tasks.md` dạng checkbox của Kiro:

```text
- [ ] T1 Add dead-letter state to runner — repo: AA-CIS-App — lane: l1
  _Requirements: R1.1, R1.2_
- [x] T2 ...
- [~] T3 ... carried → AA-xxxx (reason)
- [-] T4 ... dropped: <reason>
```

Dòng `_Requirements:` là quy ước bên thứ ba; Kiro bỏ qua không lỗi, `trace_check.py` đọc nó. Quick spec chỉ cần
`requirements.md` + `tasks.md`.

### 5.3 Liên kết Linear (an toàn với gói Free)

- 1 issue = 1 spec = 1 lát giao được.
- Linear giữ Problem + Scope. Done-when = **danh sách mã R + đường dẫn spec**, không chép lại chữ của R (tránh bản sao lệch
  nhau, bài học S283).
- Đổi tiêu chí sau khi bắt đầu: ghi rõ `R1.1 (amended S<n>: …)`, một dòng "Changed" trong note, một comment Linear.
- Khi export issue sang `docs/linear-export/`, đường dẫn spec giữ cho truy vết sống.

### 5.4 `lane.js` dùng spec thế nào

- Thêm args tuỳ chọn `spec` (đường dẫn) và `tasks` (`["T1","T2"]`). Một lane = một nhóm task, thường của một repo.
- `lane-start-guard` chỉ kiểm thêm **khi có `spec`**: status là `approved`/`in-progress`, task tồn tại và chưa tick,
  không lane nào đang giữ cùng task. Lane không có spec chạy như cũ.
- Prompt Implement nhận nguyên văn các task + R của chúng.
- Output thêm `trace: [{task, requirements[], tests[], live_steps[], status}]` và
  `docs_impact: [{page, action, reason}]`.
- Hai lens reviewer mới: **spec** (mỗi R có test hoặc live step, không thêm hành vi ngoài spec) và **docs**. Lens docs chỉ
  ra mức minor/info để không biến "docs impact chỉ cảnh báo" thành cổng chặn.
- Lane tick task trong `tasks.md` của **cùng repo** trong cùng PR. Spec ở repo gốc thì orchestrator tick trong root PR
  cuối phiên (lane ở CIS không sửa được file của repo gốc).

### 5.5 Vòng đời và truy vết

`draft` → `approved` → `in-progress` (lane đầu tiên chạy) → `implemented` (PR cuối merge, mọi task là `[x]`, `[~]` hoặc
`[-]`) → `archived` (cuối phiên, vào `_archive/`).

- **Duyệt spec = duyệt danh sách issue đầu phiên.** Orchestrator đặt `status: approved` lúc đó. Không thêm cổng người riêng
  cho từng spec (giữ luật "decide, don't ask" và self-merge giai đoạn dev).
- Sau `implemented`, spec là **hợp đồng lịch sử**, không phải tài liệu sống. Sự thật hiện tại chỉ ở CONTEXT.md và các khối
  sinh tự động. Việc sau đổi hành vi thì mở spec mới với `supersedes: spec-AA-<n>`.
- Ba lớp, mỗi lớp một loại sự thật: spec = đã thống nhất gì; implementation note = thực tế khác spec ở đâu, vì sao;
  CONTEXT.md = sau đó cái gì đúng.
- Chuỗi truy vết: Linear (R ids + đường dẫn) → `requirements.md` R → `tasks.md` T → `trace` trong output lane và thân PR →
  test/live step → bằng chứng Linear theo aa-ship.

## 6. Lộ trình 3 lát nhỏ (chỉ đề xuất)

| Lát | Nội dung | Công sức | Chứng minh được gì | Thuộc issue |
|---|---|---|---|---|
| 1. Change guard (Claude) | `tools/sync/` (`change_guard.py`, `hookio.py`), Stop dispatcher gộp, `SubagentStop` + `PostToolUse` lint một file, chế độ `--select-only` cho pre-push CIS/Booking, job `notes-present` + `test-cochange` ở mức WARN, công tắc `AA_SYNC_HOOKS`, self-test; **một tuần chế độ `log`** ghi `.tmp-session/hooklog.jsonl` | ~1 lane-ngày | PostToolUse/SubagentStop có chạy trong lane agent không; p50/p95 thời gian hook; số lần nhắc sai; tỉ lệ commit code không có note (hôm nay 25–75 %) có giảm không. Ngưỡng đạt/trượt đặt trước khi chạy | Issue mới (cần anh đồng ý tạo): "Agent change hooks: code↔tests↔notes" |
| 2. Docs impact khắp nơi | `doc-map.yaml` + `doc_impact.py` (AA-1132 A4 đã có phần CI + pre-push), chỉ thêm caller là hook và trường `docs_impact` + lens docs trong `lane.js`; thêm `docs-lint.yml` cho AA-CIS-App | ~1 ngày | Một bản đồ phục vụ hook, pre-push, CI và lane; feedback như nhau | AA-1132 |
| 3. Spec + trace | Mẫu spec (feature, bugfix, quick) trong skill `aa-linear-issue` hoặc skill mới; `trace_check.py`; args `spec`/`tasks` cho `lane.js` + `lane-start-guard`; job `spec-trace`; thử trên 1–2 issue thật của phiên sau | ~1–1,5 ngày | Một issue đi trọn Linear → R → T → test → PR → bằng chứng mà không cần đọc chat | Issue mới (cần anh đồng ý) |

Hoãn: Kiro hooks trong `aa-worker.json`, chờ nâng kiro-cli lên 3.x và thử headless xem `PostFileSave`/`Stop` có chạy không.
Trước đó Kiro vẫn gặp cùng luật ở pre-push và CI.

## 7. Rủi ro và cái giá

- **Nhắc sai.** "Code đổi, test không đổi" là phỏng đoán: refactor, config, style, migration, kit sync đều dính. Vì vậy
  trong phiên chỉ nhắc; chặn chỉ ở PR, và chỉ sau khi đo lát 1.
- **Lane chậm và RAM.** Chạy pytest trên mỗi lần sửa với 3 lane + Kiro sẽ xếp hàng và vượt luật RAM-1 (pytest do hook
  chạy nằm ngoài `aa_shell_guard`). Đã bỏ phần này; chỉ lint một file và gọi bộ chọn có sẵn một lần khi lane xong.
- **Hai Stop hook đụng nhau.** Hook chạy song song, cái nào cũng có thể ăn mất lượt chặn duy nhất. Phải gộp thành một
  dispatcher.
- **Lạm dụng waiver.** Lane có thể ghi "No test needed" cho qua. Cần đếm waiver theo repo trong báo cáo phiên và cho lens
  spec soi lý do.
- **Spec thành bản sao lệch.** Nếu coi spec là tài liệu sống, nó sẽ lệch như các trang S283 đã audit. Đóng băng sau
  `implemented` để tránh.
- **Merge queue kẹt** nếu job bắt buộc mới thiếu `merge_group`; **PR bot kẹt** nếu không miễn trừ.
- **Chi phí:** 0 USD hạ tầng, 0 token (chỉ script shell), ~3–3,5 ngày công cho cả 3 lát. Mỗi job CI thêm ~30 s.
- **Kiro:** hook `agent` tốn credit; ta không dùng. Nâng kiro-cli 3.x có thể đổi hành vi `kiro-run.sh`, cần thử riêng.

## 8. Câu hỏi cần anh quyết

1. **Có tạo 2 issue mới (lát 1 và lát 3) không?** Đề xuất: có, mỗi issue một lát giao được; lát 2 gộp vào AA-1132.
2. **`notes-present` ở CI có được chặn không?** Đề xuất: WARN trong lát 1; chuyển sang chặn chỉ khi số nhắc sai sau một tuần
   dưới ngưỡng đã đặt, và anh đồng ý riêng (khác với quyết định "docs impact chỉ cảnh báo").
3. **Duyệt spec thế nào?** Đề xuất: duyệt danh sách issue đầu phiên là duyệt spec; không có cổng duyệt riêng từng spec.
4. **Dùng spec cho mọi issue hay chỉ một số?** Đề xuất: bắt buộc cho issue có migration/auth/nhiều repo (feature spec); Quick
   spec cho issue thường; chore nhỏ không cần spec.
5. **Nâng kiro-cli lên 3.x khi nào?** Đề xuất: sau lát 2, thử trên một lane không quan trọng; nếu file trigger headless
   không chạy thì giữ Kiro chỉ dựa vào pre-push + CI.

## 9. Nguồn

Repo (đọc 18/11/2026):

- `.claude/settings.json`, `.claude/hooks/*` (7 hook + test), `tools/workflows/lane.js`, `kiro-run.sh`
- `scripts/pre-push.sh` của 6 repo, `.githooks/pre-push`, các workflow CI liệt kê ở mục 2
- `skill/aa-linear-issue/SKILL.md` (template Done-when, Docs impact), `.github/pull_request_template.md`
- `kiro-cli --version` = 2.28.0; `claude --version` = 2.1.303

Kiro (tài liệu chính thức):

- <https://kiro.dev/docs/hooks/>
- <https://kiro.dev/docs/hooks/types/>
- <https://kiro.dev/docs/hooks/actions/>
- <https://kiro.dev/docs/hooks/best-practices/>
- <https://kiro.dev/docs/ide/whats-new-v1/hooks/>
- <https://kiro.dev/docs/cli/v3/hooks-migration/>
- <https://kiro.dev/docs/specs/>
- <https://kiro.dev/docs/specs/feature-specs/>
- <https://kiro.dev/docs/specs/best-practices/>
- <https://kiro.dev/blog/faster-smarter-specs/>

Claude Code (tài liệu chính thức):

- <https://code.claude.com/docs/en/hooks>
- <https://code.claude.com/docs/en/hooks-guide>

### Phụ lục: xử lý các điểm phản biện

Nhận và đã sửa vào bản trên: cwd của lane (1), hook có chạy trong lane agent nên lát 1 chỉ cần xác nhận PostToolUse/
SubagentStop (2), không dựa vào `PostToolBatch` và `asyncRewake` khi chưa kiểm trên 2.1.303, mọi hook có `timeout` (3),
Kiro hook đặt trong `aa-worker.json` và hoãn tới 3.x (4), khoá dedupe theo `session_id` + `agent_id` (5), bỏ chạy test
mỗi lần sửa (6), Stop chỉ nhắc (8), gộp Stop dispatcher (9), không thêm cổng duyệt spec riêng (10), lens docs chỉ
minor/info (11), `ship_merge.py` không kiểm thêm `spec-trace` (12), `doc_impact` chỉ thêm caller hook (13), `merge_group`
(14), miễn PR bot (15), `notes-present` giữ WARN (16), tick task gốc ở root PR (17), Linear chỉ giữ mã R (18), redaction
spec (19), pre-push không ghi file (20), công tắc, self-test, số đo lát 1, đếm waiver.

Bác một phần: điểm 7 (SessionStart giá trị thấp). Vẫn giữ con trỏ spec ở SessionStart cho phiên chính, vì orchestrator nén
ngữ cảnh thường xuyên, hook rẻ (< 800 ký tự, 0 token) và giúp không lạc task sau khi nén. Không kỳ vọng nó tới lane.
