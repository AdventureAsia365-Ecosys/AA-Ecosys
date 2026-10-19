> Superseded on 2026-10-19 (S243) by docs/engineering-handbook.md — kept for history.

# Hướng dẫn SDLC/ADLC cho AA-Ecosys: tài liệu, phiên bản, phát hành, vận hành, chi phí

> S243 · 19/10/2026 · Tác nhân: Claude Code · Đối tượng: Nghiệp (1 kỹ sư + AI agents, giai đoạn Dev, hướng tới prod)
>
> Câu hỏi gốc: *"Có 1 việc cần bạn tư vấn cho tôi là documentation cho toàn bộ hệ sinh thái, trong quá trình viết code,
> quản lý phiên bản docs và phiên bản code cũng như cách quản lý phiên bản khi deploy, hay update tính năng như thế nào
> cho chuẩn SDLC/ADLC, từ hạ tầng, BE, FE đến vận hành, chi phí,.... Vì tôi vừa làm vừa học nên cần bạn tư vấn các quy
> trình chuẩn để làm tốt nhất, kèm giải thích một số thuật ngữ hay cách làm."*
>
> Cách đọc: §1 là bản 1 trang. §2–§6 là quy trình chuẩn áp vào hệ mình. §7 là lộ trình việc cụ thể. §8 là từ điển thuật ngữ.
> Mọi nhận định về hiện trạng dẫn tới file thật (đọc-only, không sửa gì). Chỗ nào chưa chắc ghi **[cần kiểm]**.
>
> Tài liệu liên quan: bản review SDLC đầy đủ S241 `docs/audits/2026-10-17-S241-sdlc-review/README.md` (+ `unified-roadmap.md`,
> `areas/*.md`). Bản này **không thay** S241 — nó trả lời câu hỏi "làm thế nào cho chuẩn" và trỏ về các mục U-xx của S241.
>
> Mức áp dụng dùng xuyên suốt: **[CẦN NGAY]** làm bây giờ · **[BẢN NHẸ]** làm phiên bản nhỏ · **[CHƯA CẦN]** bỏ qua tới khi có team/prod thật.
>
> Ký hiệu **Lxx** (vd L66) = **số dòng** trong `skill/aa-lessons/lessons.md` tại 19/10/2026 — sẽ trôi khi file đổi; tìm theo nội dung
> đã tóm tắt cạnh đó. Bản này viết tiếng Việt vì là tư vấn cho Nghiệp (như S241); mọi file **mới** nó đề xuất (glossary, runbook,
> PR template, mẫu DoR, CHANGELOG) viết **tiếng Anh** theo `.kiro/steering/language-convention.md`.

---

## 1. Tóm tắt — mô hình vận hành đề xuất trong một khung nhìn

- **Mô hình làm việc = Kanban + DevOps + trunk-based.** Luồng issue nhỏ liên tục (Linear → `docs/backlog/README.md`),
  nhánh ngắn → PR → CI → merge thẳng `main` (đã có, ADR-2026-023). Không cần Scrum/sprint.
- **ADLC của mình = SDLC + kiểm soát agent + vòng đời tính năng LLM.** Agent (Claude Code, Kiro) viết code; Nghiệp viết
  đề bài (DoR), gác cổng (review/CI/verify) và giữ quyền (merge/deploy/IAM). Tính năng LLM có thêm eval, version prompt/model, cost.
- **Mỗi sự thật chỉ có 1 chỗ ở (single source of truth).** Code + docs + ADR trong git là chuẩn; Linear = trạng thái việc;
  Notion memory = con trỏ ngắn giữa các phiên; Jira = tiếng nói với chị Thư. Ngừng chép cùng 1 thông tin vào nhiều nơi (§3.3).
- **Docs-as-code: docs đổi trong cùng PR với code.** PR template có ô "Docs/ADR/CONTEXT/runbook/CHANGELOG cập nhật hoặc N/A".
  Thứ gì sinh được thì để CI sinh (schema dump đã có; thêm OpenAPI).
- **Một "phiên bản" phải truy được từ đầu đến cuối:** commit (Conventional Commits) → image `dev-<sha>` (immutable) →
  ECS task-def → `/health` trả `git_sha` + `version` → git tag `vX.Y.Z` + CHANGELOG + GitHub Release → release note cho chị Thư.
  Hiện mắt xích **tag/CHANGELOG** và **`/health` của CIS** còn thiếu — đây là lỗ hổng số 1.
- **Deploy ≠ release.** Deploy = code đã chạy trên môi trường; release = người dùng thấy tính năng. Tách bằng feature flag +
  expand/contract cho DB và API, để update tính năng không phải "big bang".
- **Done = merge + CI xanh + deploy COMPLETED + verify live + Linear có bằng chứng** (`skill/aa-ship/SKILL.md`, đã rất tốt) —
  đề xuất thêm ô **docs/changelog** (§5.5). Bổ sung **Definition of Ready** để brief cho agent rõ ràng trước khi code.
- **Vận hành & chi phí tối thiểu nhưng có kỷ luật:** alarm → runbook, postmortem không đổ lỗi → `lessons.md`, RPO/RTO + diễn tập
  restore theo quý, tag `App` + Budgets + **Cost Anomaly Detection (miễn phí, chưa có)** + review chi phí hàng tháng có unit cost.

---

## 2. Bản đồ vòng đời (SDLC + ADLC) cho đội 1 người + agents

### 2.1 Định nghĩa ngắn

- **SDLC** (Software Development Life Cycle — vòng đời phát triển phần mềm): ý tưởng → yêu cầu → thiết kế → code → test →
  phát hành/deploy → vận hành/giám sát → bảo trì → khai tử.
- **ADLC** — thuật ngữ **chưa chuẩn hoá**, mỗi nguồn hiểu một kiểu. Có 2 nghĩa và hệ mình dùng cả hai:
  - (a) **Agentic SDLC**: xây phần mềm bằng AI coding agent. SDLC vẫn vậy, nhưng việc của người chuyển sang viết spec, cung cấp
    context (CLAUDE.md, CONTEXT.md, skill), gác cổng và kiểm soát quyền.
  - (b) **AI/LLM feature lifecycle** (LLMOps): dữ liệu → prompt/model → eval → deploy → giám sát → cải tiến. Áp cho writer/judge,
    Jev, atoms, T-series.
  - Đề xuất ghi vào glossary dự án: **"ADLC (AA) = SDLC + kiểm soát agent (a) + vòng đời tính năng LLM (b)"**, không chạy theo
    framework của một vendor nào.

### 2.2 Bảng giai đoạn — ai làm, artifact gì, file nào

| # | Giai đoạn | Việc chính | Ai | Artifact chuẩn | Ở đâu hiện nay |
|---|---|---|---|---|---|
| 1 | Ý tưởng / yêu cầu | Nhận yêu cầu (chị Thư, Jira PR-xx, phát hiện từ audit) | Nghiệp | Issue Linear (goal, acceptance criteria) | Linear team AA_Ecosys; Jira cho phía khách |
| 2 | Backlog / ưu tiên | Sắp thứ tự, ghi time-gated checks | Nghiệp + Claude | Backlog sống | `docs/backlog/README.md` |
| 3 | **Ready (DoR)** | Issue đủ: mục tiêu, phạm vi, tiêu chí nghiệm thu, cách verify, rủi ro | Claude soạn, Nghiệp chốt | Mô tả issue theo mẫu DoR (§5.6) | Chưa có mẫu — **thiếu** |
| 4 | Thiết kế | Quyết định kiến trúc, ranh giới, contract | Claude đề xuất, Nghiệp chốt | ADR, CONTEXT.md, contract JSON | `docs/adr/`, `apps/*/docs/adr/`, `apps/*/CONTEXT.md`, `docs/contracts/` |
| 5 | Build | Code trên nhánh `feat/aa-xxx-slug`, worktree cho việc song song | Kiro / Claude subagent | Commit Conventional, implementation note | `docs/implementation-notes/<ISSUE>.md`; hook `.claude/hooks/subagent-guardrails.sh` |
| 6 | Review / test | CI (lint, unit, integration, docker build, CodeQL, pip-audit), review rủi ro | CI + Claude gác + `kiro-reviewer` khi rủi ro | PR có mô tả rủi ro + rollback | `.github/workflows/ci.yml` mỗi repo; `.claude/agents/kiro-reviewer.md` |
| 7 | Release / deploy | Merge → build image → deploy Dev; migration riêng qua DB Migrate | Claude (dev-phase self-merge) | Image `dev-<sha>`, task-def revision, (thiếu) tag + CHANGELOG | `deploy-dev.yml`, `infra/AA-CIS-Infra/.github/workflows/db-migrate.yml` |
| 8 | Verify | Rollout COMPLETED, api/worker cùng SHA, curl endpoint, UI check | Claude | Comment "Verified live" trên Linear | `skill/aa-ship/SKILL.md` §3–§4, `skill/aa-ui-verify/` |
| 9 | Vận hành | Alarm, Sentry, sự cố, backup, secrets | Nghiệp + Claude | Runbook, playbook, incident note | `docs/ops/incident-response.md`, `infra/AA-CIS-Infra/accounts/aa365/observability*.tf` |
| 10 | Học | Postmortem → nguyên tắc → guard CI | Claude ghi, Nghiệp duyệt | Lesson, test guard | `skill/aa-lessons/lessons.md` |
| 11 | Chi phí | Budget, LLM ledger, review tháng | Claude báo, Nghiệp quyết | Báo cáo chi phí tháng | Budgets trong `observability.tf`; `shared.llm_call_log` |
| 12 | Báo cáo khách | Release note dạng nghiệp vụ | Claude nháp, Nghiệp duyệt | Jira comment | `docs/sessions/*-jira-drafts.md`, `skill/aa-jira-update/` |

### 2.3 Vai trò của từng tác nhân (ADLC phần a)

| Tác nhân | Được làm | Không được làm | Cơ chế đảm bảo |
|---|---|---|---|
| Nghiệp | Chốt DoR, ADR, chi tiêu, quyết định prod; override deploy-gate | — | — |
| Claude Code (phiên chính) | Chọn việc, gác cổng, merge/deploy ở Dev (memory `dev-phase-self-merge`), Terraform, DB Migrate, Linear | Đụng prod (khi có), tự đăng Jira | Quy tắc trong steering/skill; **chưa có** quyền tách riêng (chạy bằng role admin của Nghiệp — S241 P0-3) |
| Subagent / Kiro | Code, test, commit trên nhánh | Push, merge, apply, ECS/RDS/IAM write, secret | `.claude/hooks/subagent-guardrails.sh` (deny-list regex) |
| CI | Cổng chất lượng bắt buộc | — | Required checks: CIS 5, Booking 5, TripPlanner 2 (`gh api …/protection`, 19/10); **Infra + root không có** (GitHub Free, repo private) |

Điểm cần biết khi "vừa làm vừa học": theo DORA 2025, AI **khuếch đại** quy trình sẵn có — quy trình tốt thì nhanh hơn, quy trình
lỏng thì lỗi nhiều hơn. Vì vậy đầu tư vào DoR, CI và verify có lợi gấp đôi khi agent viết phần lớn code.

---

## 3. Documentation — hệ thống tài liệu

### 3.1 Diátaxis: 4 loại tài liệu, đừng trộn

**Diátaxis** là cách phân loại tài liệu theo *nhu cầu người đọc*. Một trang chỉ nên thuộc một loại.

| Loại | Người đọc cần | Đặc điểm | File hiện có ánh xạ vào |
|---|---|---|---|
| **Tutorial** (học bằng làm) | Người mới bắt đầu | Dẫn từng bước, có kết quả chắc chắn | Repo README phần setup; `apps/AA-TripPlanner-Web/docs/e2e-uat-guide.md` — **gần như chưa có** cho onboarding hệ sinh thái |
| **How-to** (làm 1 việc) | Người đã biết, cần làm việc X | Các bước + lệnh copy-paste + verify + rollback | Runbook: `docs/ops/incident-response.md`, `docs/db-access-ssm-tunnel.md`, CIS `docs/CIS_Runbook_v1.md`, CIS `docs/runbooks/clean-rerun.md`, Infra `db/README.md`; skill `skill/aa-ship/`, `skill/aa-wave-rerun/` |
| **Reference** (tra cứu) | Cần sự thật chính xác | Khô, đầy đủ, nên **sinh tự động** | `docs/architecture/db-schema-reference.md` (sinh bởi CI), `docs/contracts/*.json`, OpenAPI (`/booking/openapi.json`; CIS sau admin secret), `infra/AA-CIS-Infra/db/owners.yaml` |
| **Explanation** (tại sao) | Hiểu bối cảnh, lý do | Kiến trúc, quyết định, đánh đổi | `docs/ecosystem-architecture.md`, `docs/adr/*`, `apps/*/CONTEXT.md`, `docs/architecture/data-standards/` |

Ngoài 4 loại trên, hệ mình có thêm **tài liệu quá trình** (không phải tài liệu sản phẩm): session log, backlog, audit,
implementation notes, lessons. Chúng là *nhật ký*, không phải *sự thật hiện hành* — đọc để biết lịch sử, không dùng làm nguồn chuẩn.

### 3.2 Bố cục thư mục đề xuất (nhẹ, không dời file ồ ạt)

Không cần chuyển hết file. Chỉ áp quy tắc cho file **mới**, và thêm **index** để tìm được file cũ:

```
AA-Ecosys/docs/
  ecosystem-architecture.md        # explanation (cấp hệ) — thêm sơ đồ C4 L1–L2 bằng Mermaid
  adr/                             # explanation — quyết định ≥2 repo (đã có)
  contracts/                       # reference — event/read-model, có version (đã có)
  architecture/db-schema-reference.md  # reference — SINH TỰ ĐỘNG (đã có)
  architecture/data-standards/     # explanation + rules (đã có, v1.0)
  ops/README.md                    # MỚI: index mọi runbook/playbook của cả hệ (trỏ sang repo con)
  ops/runbooks/                    # how-to dùng chung (dời dần docs/*.md, *.sh rời rạc vào đây)
  glossary.md                      # MỚI: thuật ngữ dự án (lấy từ §8 bản này)
  sessions/ backlog/ audits/ research/ implementation-notes/   # tài liệu quá trình (giữ nguyên)

apps/<repo>/
  README.md                        # tutorial ngắn: chạy, test, deploy
  CONTEXT.md                       # explanation: stack, ranh giới, ownership (đã có)
  CHANGELOG.md                     # MỚI: sinh bởi release-please
  docs/adr/                        # quyết định 1 app (TripPlanner chưa có)
  docs/runbooks/                   # how-to riêng app
  docs/implementation-notes/       # quá trình (đã có)

infra/AA-CIS-Infra/
  CONTEXT.md, README.md, CHANGELOG.md (mới)
  docs/adr/                        # MỚI: quyết định chỉ hạ tầng (quy tắc đã yêu cầu nhưng thư mục chưa có)
```

### 3.3 Ma trận nguồn sự thật — sự thật nào ở đâu

Quy tắc ưu tiên hiện tại trong `.kiro/steering/session-workflow.md`: **repo > Notion canonical > memory > skill**. Bảng dưới
cụ thể hoá cho từng loại sự thật. Cột "Nơi khác" chỉ được **trỏ link**, không chép nội dung.

| Sự thật | Chủ (canonical) | Nơi khác chỉ trỏ link | Ghi chú |
|---|---|---|---|
| Stack, ranh giới, ownership 1 app | `apps/<repo>/CONTEXT.md` | CLAUDE.md của repo, skill | Steering bắt buộc đọc trước khi thiết kế |
| Quyết định kiến trúc | ADR (`docs/adr/` hoặc repo con) | ecosystem-architecture, CONTEXT.md | ADR đã chấp nhận thì không sửa, chỉ supersede/amend (`0006a` là mẫu đúng) |
| Tên bảng/cột | `docs/architecture/db-schema-reference.md` (sinh) | skill `aa-cis-schema` (chỉ giải thích) | Đã đúng: steering ghi "khi lệch, file dump thắng" |
| Schema nào thuộc repo nào | `infra/AA-CIS-Infra/db/owners.yaml` | `docs/database/schema-ownership.md` | Đề xuất: coi `owners.yaml` là gốc, md chỉ diễn giải (đã có test `db/tests/test_owners_registry.py`) |
| Hình dạng API | OpenAPI sinh từ code | README, frontend | Hiện yếu: ~11/258 route CIS có `response_model` (S241) |
| Event/read-model giữa app | `docs/contracts/*.vN.M.json` | code các app (pin hash trong test) | Tốt nhất hệ hiện nay |
| Hạ tầng thật | Terraform trong `infra/AA-CIS-Infra` + state S3 | CONTEXT.md Infra | Lesson L66: apply từ worktree làm `main` lệch hạ tầng thật |
| Phiên bản đang chạy | `/health` của từng service + (sau này) GitHub Deployments | session log | Hiện chỉ Booking trả `git_sha` |
| Trạng thái việc | Linear | backlog (thứ tự), session log (diễn biến) | Notion memory chỉ nên giữ con trỏ "đang ở đâu" |
| Thứ tự ưu tiên | `docs/backlog/README.md` | Notion memory | — |
| Diễn biến phiên | `docs/sessions/` | Notion memory HOT (tóm tắt + link) | — |
| Tiến độ với khách | Jira (chị Thư) | — | Nháp trong `docs/sessions/*-jira-drafts.md`, duyệt trước khi đăng |
| Quy trình làm việc | `skill/*/SKILL.md` | steering (bản tóm), CLAUDE.md (import) | Steering ghi "khi lệch, skill thắng" |
| Quy tắc agent | `.kiro/steering/*.md` | `.claude/CLAUDE.md` (import bằng `@`) | Đúng hướng: "sửa steering, không chép" |
| Bài học | `skill/aa-lessons/lessons.md` | — | Kiểm được bằng test thì thành guard rồi xoá dòng |
| Chi phí thật | AWS Cost Explorer / Budgets | báo cáo tháng | LLM: `shared.llm_call_log` |
| Danh sách secrets | **chưa có** (secrets register, AA-878) | — | — |

**Những chỗ đang chép trùng / lỗi thời nên dọn** (từ inventory, chưa sửa gì):

| Chỗ | Lệch | Đề xuất |
|---|---|---|
| `~/.claude/CLAUDE.md` (toàn cục, không nằm trong git) | Vẫn bảo đọc/ghi `handoff.md`, ghi task-def/CI run/commit hash vào CLAUDE.md repo, nhắc stop ECS/RDS, số ADR kiểu `ADR-2026-0xx` | Rút gọn chỉ còn quy tắc thật sự toàn cục (WSL CLI 1 dòng, account map, env var gạch dưới); phần quy trình trỏ sang steering/skill. Nghiệp sửa tay vì file ngoài git |
| `.claude/CLAUDE.md` (root) | "Sắp có AA-Booking" (đã live), Git Rules còn nhắc AA-ACP-App (đã xoá), "DO NOT merge to main yourself" (mâu thuẫn `dev-phase-self-merge`, S241 D-13) | Sửa trong 1 root PR; ghi rõ quy tắc merge theo giai đoạn (Dev: agent tự merge; prod: cần người duyệt) |
| `.kiro/steering/db-schema.md` | Thiếu Booking; vẫn hướng dẫn regenerate tay bằng `.tmp-session/s209_*.py` trong khi `db-schema-dump.yml` của Infra đã tự làm | Sửa theo thực tế: CI tự sinh, tay chỉ là fallback |
| `infra/AA-CIS-Infra/.claude/CLAUDE.md` | Banner "RESTRUCTURE 15/09/2026" đã thành lịch sử | Chuyển lịch sử vào CONTEXT.md/ADR, CLAUDE.md giữ ngắn |
| `apps/AA-CIS-App/handoff.md` | Cập nhật lần cuối 23/08/2026 | Thêm dòng đầu "ARCHIVED — xem docs/sessions" hoặc xoá |
| Trạng thái phiên ở 4 nơi | Notion HOT, sessions, backlog, Linear | Mỗi nơi giữ đúng vai trò ở bảng trên; Notion HOT chỉ tóm tắt + link |

### 3.4 Docs-as-code — quy tắc vận hành

**Docs-as-code** = tài liệu là file Markdown trong cùng repo với code, review trong cùng PR, version bằng git, kiểm bằng CI.

Quy tắc đề xuất (thêm vào `skill/aa-ship/SKILL.md` §1 và PR template):

1. **Docs đổi cùng PR với code** mà nó mô tả. PR template mỗi repo (hiện **chưa có `.github/pull_request_template.md`**, S241) gồm:
   ```
   ## What / Why
   Refs AA-xxx
   ## Risk & rollback
   - Risk: low | medium | high (auth / migration / IAM / cost / delete)
   - Rollback: <how>
   ## Docs
   - [ ] CONTEXT.md updated (boundary/stack/ownership changed) or N/A
   - [ ] ADR added/amended (decision reversible only by touching ≥1 repo) or N/A
   - [ ] Runbook updated (ops procedure changed) or N/A
   - [ ] Contract version bumped (docs/contracts) or N/A
   - [ ] Implementation note docs/implementation-notes/AA-xxx.md
   ```
2. **Trigger bắt buộc cập nhật** — dễ nhớ:

   | Khi thay đổi… | Thì cập nhật… |
   |---|---|
   | Ranh giới app, stack, ai sở hữu dữ liệu | CONTEXT.md của repo (+ `ecosystem-architecture.md` nếu cấp hệ) |
   | Quyết định khó đảo ngược / ảnh hưởng ≥2 repo | ADR mới hoặc amendment `NNNNa` |
   | Migration đổi cấu trúc | Không làm tay: `db-schema-dump.yml` tự mở PR root; chỉ cần merge PR bot |
   | Endpoint public / shape response | OpenAPI (sinh) + CHANGELOG mục Changed/Deprecated |
   | Event giữa app | File contract mới `vN.M+1` (minor) hoặc `vN+1` (major + dual-write) theo `docs/contracts/README.md` |
   | Quy trình vận hành (lệnh, bước) | Runbook trong `docs/ops/runbooks/` hoặc repo con + index `docs/ops/README.md` |
   | Thêm/xoá AWS resource có tiền | Ghi chi phí tháng ước tính trong PR (memory `cost-advice-new-aws-services`) |
   | Đổi prompt/model/route LLM | Ghi version prompt + run ID eval trong PR (§4.8) |

3. **Tài liệu sinh tự động thì không sửa tay**: đặt dòng đầu `<!-- GENERATED by <workflow> — do not edit -->`. Đã có mẫu tốt là
   `db-schema-reference.md` (có `schema-fingerprint` + header "Verified …"). Nên thêm: OpenAPI export mỗi app (§4.4).
4. **Freshness (độ tươi)** [BẢN NHẸ]: runbook và reference viết tay có front-matter:
   ```
   ---
   owner: nghiep
   last-reviewed: 2026-10-19
   applies-to: aa-cis-api >= v0.4.0
   ---
   ```
   Một script nhỏ (hoặc chỉ là checklist đầu tháng) liệt kê file `last-reviewed` > 90 ngày. Đây cũng là cách bắt CLAUDE.md lỗi thời.
5. **Kiểm tra CI cho docs** [BẢN NHẸ]: link check (markdown-link-check/lychee) cho `docs/`, lint trạng thái ADR (mỗi ADR có
   `Status:` hợp lệ và có trong `docs/adr/README.md`). Không cần site tài liệu riêng (Docusaurus/MkDocs) — [CHƯA CẦN].
6. **Không lưu binary trong git**: `.docx/.xlsx/.csv/.zip/.webm` → Google Drive (memory `gdrive-adventureasia-folder`) hoặc S3, git
   chỉ giữ link. Root đã làm (`docs/calib/*.xlsx|csv`, `*.webm` gitignored).
7. **CIS `docs/` đang bị gitignore toàn bộ** (`apps/AA-CIS-App/.gitignore:43`). Hệ quả: ~64 implementation note, `investigations/`,
   `architecture/` chỉ tồn tại trên 1 laptop; note mới phải `git add -f` nên dễ sót. Đề xuất: đổi thành ignore theo đuôi binary
   (`docs/**/*.docx`, `*.xlsx`, `*.csv`, `*.zip`) và track toàn bộ `.md`; rà một lượt file local trước khi add (có thể chứa dữ liệu thật).
8. **Xung đột ở file note dùng chung** (lesson L18: nhiều PR cùng append `AA-816.md` → DIRTY merge): mỗi PR song song viết
   một mục riêng hoặc file riêng `AA-816-<slug>.md`.

### 3.5 Version của tài liệu

- **Tài liệu trong git đi theo version của code**: khi tag `v0.4.0`, docs tại tag đó chính là docs của bản đó. Không cần cơ chế riêng.
- **Tài liệu cấp hệ (root repo)** không có release; version bằng ngày + PR. Riêng loại có "người dùng phụ thuộc" thì ghi version
  ngay trong file như mẫu đang có: `data-standards` "Version 1.0 · S237" + bảng thay đổi; contract `vN.M`; `owners.yaml version: 1`.
- **ADR**: không đánh version; trạng thái `Proposed → Accepted → Superseded by NNNN / Amended by NNNNa`. Đừng sửa nội dung ADR đã
  Accepted — viết amendment (hệ mình đã làm đúng với 0003a/0004a/0004b/0006a).
- **CONTEXT.md**: thêm dòng `applies-to` hoặc ghi "valid as of vX.Y.Z" khi có release.

### 3.6 Cụ thể theo từng lớp

| Lớp | Explanation (tại sao) | Reference (tra cứu) | How-to (runbook) | Sinh tự động? |
|---|---|---|---|---|
| **Hạ tầng** | `infra/AA-CIS-Infra/CONTEXT.md`, ADR hạ tầng (cần tạo `infra/AA-CIS-Infra/docs/adr/`), `infra/AA-CIS-Infra/docs/ci-role-split.md` | Terraform outputs; danh sách resource theo `App` tag; `owners.yaml` | apply, bootstrap MFA, rollback ECS, restore RDS, rotate secret | `terraform-docs` cho module [BẢN NHẸ]; plan trong PR (đã có) |
| **Backend** (CIS, Booking, TP Lambda) | CONTEXT.md, ADR app | OpenAPI, env var list, job kinds | deploy, deploy-gate override, ECS exec S3-mediated, wave rerun | OpenAPI export trong CI [CẦN NGAY trước prod] |
| **Frontend** (Next.js trên Vercel) | CONTEXT.md phần FE | danh sách route/page, env var `NEXT_PUBLIC_*` (sửa tay trong VSCode) | Vercel Instant Rollback/Promote, preview bypass | Không cần |
| **Data / DB** | `docs/architecture/data-standards/`, ADR 0002 (chỉ CIS ghi content), 0008 (quy tắc data platform), 0003/0003a (job tables) | `db-schema-reference.md`, `schema-ownership.md`, contracts | migration flow (Infra `db/README.md`), DRY RUN xoá dữ liệu (`skill/aa-cis-schema/references/destructive-ops.md`) | Có (schema dump nightly + sau migrate) |
| **Vận hành** | `docs/ops/incident-response.md` (SEV, quy trình) | danh sách alarm → runbook | playbook theo loại sự cố (5xx spike, queue stuck, LLM cost spike, Cognito lỗi) | Bảng alarm có thể sinh từ Terraform [BẢN NHẸ] |
| **Chi phí** | quy tắc chi tiêu (memory → nên đưa vào 1 file `docs/ops/finops.md`) | budget, unit cost theo tháng | quy trình review chi phí tháng | Có thể sinh số liệu từ Cost Explorer [BẢN NHẸ] |
| **AI/LLM** | ADR **CIS** 0005 (model catalog, `apps/AA-CIS-App/docs/adr/0005-model-catalog-and-converse-adapter.md`) + CIS 0006 (route/fallback/shadow); ADR hệ 0009 (AI platform, đang reserved — lưu ý ADR hệ 0005 là pricing, khác số) | `shared.llm_model_catalog`, `shared.llm_role_config`, danh sách prompt + version | đổi route model, chạy eval, script adhoc có ghi cost | Bảng route có thể export từ DB [BẢN NHẸ] |

---

## 4. Versioning — quản lý phiên bản

### 4.1 Hiện trạng ngắn

| Thứ | Có version? | Bằng chứng |
|---|---|---|
| Git tag / GitHub Release | **Không** ở cả 5 repo | `git tag -l` rỗng, `gh release list` rỗng |
| CHANGELOG | **Không** | S241 xếp U-47, trigger "first prod" |
| `version` trong `package.json`/FastAPI | Có nhưng **không bao giờ bump** | CIS FastAPI `version="0.3.0"` (`api/main.py:152`), `/health` trả cứng `0.3.0` (`api/main.py:519-520`) |
| Image container | Có, immutable theo SHA | CIS `dev-${sha}` (`deploy-dev.yml:86`), Booking `${GITHUB_SHA}`; ECR IMMUTABLE |
| SHA lộ ra lúc chạy | Chỉ Booking | `/booking/health` trả `git_sha` (`routers/health.py:21`), smoke so khớp (`deploy-dev.yml:201`); CIS có `APP_GIT_SHA` trong image nhưng chỉ dùng cho Sentry release |
| DB migration | Có, theo owner | `shared.schema_versions`, khoá `NNN`/`tp-NNN`/`bk-NNN`/`rl-NNN` |
| Contract giữa app | Có, rõ ràng | `docs/contracts/*.vN.M.json` + quy tắc minor/major |
| Terraform | Pin core + provider + lockfile | `accounts/*/versions.tf`, `.terraform.lock.hcl` |
| Prompt LLM | **Không có version ID** gắn vào mỗi call | — |

### 4.2 Code: trunk + tag + release

- **Giữ trunk-based** (ADR-2026-023). Nhánh sống ≤ 1–2 ngày.
- **Thêm tag theo SemVer cho mỗi app**, tạo bởi **release-please**:
  - **SemVer** (`MAJOR.MINOR.PATCH`): MAJOR = phá tương thích, MINOR = thêm tính năng tương thích, PATCH = sửa lỗi.
    `0.y.z` = chưa ổn định, được phép phá.
  - **CalVer** (version theo ngày, vd `2026.10.19`) hợp với app deploy liên tục không có người dùng ngoài phụ thuộc. Nhưng
    release-please và Conventional Commits đã làm sẵn cho SemVer, và hệ mình đã có số `0.x` trong code → **chọn SemVer cho tất cả**,
    đơn giản nhất.

| Repo | Scheme | Bắt đầu từ | Lên `1.0.0` khi |
|---|---|---|---|
| AA-CIS-App | SemVer, release-please | `v0.4.0` (nối tiếp 0.3.0 hiện có) | Prod đầu tiên, API `/v1` có OpenAPI ổn định |
| AA-Booking | SemVer | `v0.2.0` | Prod + đối tác B2B dùng API |
| AA-TripPlanner-Web | SemVer | `v0.4.0` (nối frontend 0.3.0) | Prod công khai |
| AA-CIS-Infra | **Tuỳ chọn** [BẢN NHẸ]: chỉ tag ngày `infra-2026.10.19` khi apply lớn, hoặc release-please nếu muốn CHANGELOG | `v0.1.0` | Có env prod tách biệt |
| AA-Ecosys (root) | Không release; docs version bằng PR | — | — |

**release-please làm gì** (giải thích cho người mới): mỗi lần merge commit `feat:`/`fix:` vào `main`, bot mở/cập nhật 1 PR tên
"chore(main): release 0.4.0" chứa CHANGELOG mới và bump version trong `package.json`/`pyproject`. Khi Nghiệp (hoặc agent) merge PR
đó, bot tạo git tag `v0.4.0` + GitHub Release. Không merge thì nó cứ gom dần — mình chọn **lúc nào** cắt release.

- Nhịp cắt release đề xuất ở Dev: **gom theo tuần hoặc theo mốc báo chị Thư**, không cần mỗi merge một release.
- Cấu hình: `release-please-config.json` + `.release-please-manifest.json` (manifest mode), workflow
  `googleapis/release-please-action` (pin version cụ thể). Monorepo con trong CIS (backend + frontend) có thể khai báo 2 package
  hoặc 1 package chung — đề xuất **1 package/repo** cho đơn giản.
- **Bẫy cấu hình release-please cần biết trước** (kiểm lại trong docs release-please khi cài):
  - Mặc định, commit phá tương thích (`feat!:`) khi đang `0.x` sẽ nhảy thẳng lên **`1.0.0`**. Muốn giữ `0.x` thì bật
    `"bump-minor-pre-major": true` (và tuỳ chọn `"bump-patch-for-minor-pre-major": true`) trong `release-please-config.json`.
  - PR do bot tạo bằng `GITHUB_TOKEN` mặc định **không kích hoạt workflow `pull_request`** → required checks ở CIS/Booking/TP không
    chạy → release PR không merge được. Cần token của GitHub App (hoặc PAT fine-grained) cho action, hoặc cho phép bỏ qua check
    với PR chỉ đổi CHANGELOG/manifest.
  - CIS ghi version cứng **2 chỗ** trong `api/main.py` (FastAPI `version=` và chuỗi trong `/health`) → đưa về 1 hằng số, đánh dấu
    `# x-release-please-version` và khai `extra-files` để bot bump; hoặc đọc từ `pyproject.toml`.
  - Merge release PR = 1 push vào `main` → kích hoạt `deploy-dev.yml` (và deploy-gate). Thêm `paths-ignore: [CHANGELOG.md,
    .release-please-manifest.json]` hoặc chấp nhận 1 lần deploy thừa.
  - Release PR do bot tạo không có `Refs AA-xxx` — ghi ngoại lệ này vào `skill/aa-ship/SKILL.md` §1.
- Lưu ý: S241 xếp U-47 vào "first prod". Bản này đề xuất **kéo phần nhẹ (release-please + CHANGELOG + tag) lên sớm** vì gần như
  miễn phí và giải quyết lỗ hổng "không biết bản nào đang chạy". Phần GitHub Deployments + DORA để lại U-47. Nghiệp quyết.

### 4.3 Commit: Conventional Commits — giữ nguyên

Định dạng hiện tại (`~/.claude/CLAUDE.md`, `skill/aa-ship/SKILL.md` §1) **hợp lệ** với Conventional Commits 1.0:

```
feat: add tour availability filter

Refs AA-901
```

- Bổ sung 3 điều để release-please hiểu đúng:
  - `feat!:` hoặc footer `BREAKING CHANGE: <mô tả>` khi phá tương thích → bump MAJOR (khi còn `0.x` chỉ bump MINOR **nếu** bật
    `bump-minor-pre-major`, xem §4.2).
  - Thêm type `perf`, `test`, `ci`, `build` khi phù hợp. CHANGELOG mặc định của release-please hiện `feat`, `fix`, `perf`, `revert`;
    ẩn `docs`, `chore`, `refactor`, `test`, `ci`, `build`, `style`.
  - Scope tuỳ chọn: `feat(booking-api): ...`, `fix(fe): ...`.
  - Quy tắc commit hiện tại (`~/.claude/CLAUDE.md`: `feat|fix|chore|refactor|docs: description`) chưa có các type/scope/`!` này →
    nếu áp dụng, sửa cùng lúc `skill/aa-ship/SKILL.md` §1 và ghi chú cho Nghiệp sửa tay file toàn cục, để agent không "sửa lại" commit đúng.
- Chi tiết kỹ thuật: theo đặc tả CC, footer có dạng `Token: value` hoặc `Token #value`; `Refs AA-901` (không có `:`) được coi là
  thân commit, không phải footer chuẩn. Không sao — Linear vẫn nhận, release-please bỏ qua. **Không đổi** thói quen này.
- Độ tuân thủ 50 commit gần nhất: CIS 50/50, Infra 50/50, TripPlanner 42/50, Booking 37/50. Vì squash-merge, **tiêu đề PR = commit
  message** → nên có check nhỏ `amannn/action-semantic-pull-request` (lint tiêu đề PR) ở Booking và TripPlanner. [BẢN NHẸ]

### 4.4 CHANGELOG và release notes

| | CHANGELOG | Release note |
|---|---|---|
| Cho ai | Kỹ sư, agent | Chị Thư, tenant, người dùng |
| Ngôn ngữ | Tiếng Anh, kỹ thuật | Nghiệp vụ; Jira comment theo `skill/aa-jira-update/` |
| Nguồn | release-please sinh từ commit, sửa tay nếu cần | Viết tay từ CHANGELOG, chỉ tính năng đã ship + verify live (memory `jira-report-when-done`) |
| Format | Keep a Changelog: `Added / Changed / Deprecated / Removed / Fixed / Security`, mục `Unreleased` trên cùng | 3–6 dòng, không mã Linear nội bộ |
| Ở đâu | `CHANGELOG.md` mỗi repo + GitHub Release | Jira; nháp ở `docs/sessions/*-jira-drafts.md` |

### 4.5 API versioning

- **Major trong URL** (`/v1/...`) — các router public của CIS đã có prefix `/v1`; còn `/admin/*` (CIS) và `/booking/*` (Booking)
  **chưa có version** → chốt trước khi đối tác B2B gọi Booking (vd `/booking/v1/...`). Trong cùng major chỉ thay đổi **cộng thêm** (thêm field, thêm endpoint).
  Bỏ/đổi tên field, đổi kiểu, đổi nghĩa = major mới (`/v2`) hoặc expand/contract.
- **OpenAPI là hợp đồng**: CI xuất `openapi.json` (FastAPI sinh sẵn), commit vào repo hoặc đính vào GitHub Release; PR chạy
  **oasdiff** so với `main` để chặn breaking change không khai báo. Điều kiện cần: thêm `response_model` cho các route public
  (hiện ~11/258 ở CIS — S241).
- **Quy trình deprecate**: thông báo → header `Deprecation` (RFC 9745) + `Sunset: <ngày>` (RFC 8594) + `Link: rel="deprecation"`
  trỏ docs → giữ cửa sổ chuyển đổi → gỡ. Ghi mục `Deprecated` trong CHANGELOG.
- **Event contract** đã có quy tắc riêng tốt (`docs/contracts/README.md`: minor cộng thêm, major dual-write). Giữ nguyên.

### 4.6 DB schema versioning

Hệ mình đã có nền rất tốt; chỉ cần nắm nguyên tắc để update tính năng an toàn:

- Migration **đánh số, forward-only, idempotent, chạy bằng CI** (`db-migrate.yml`), không chạy từ máy cá nhân. Không sửa
  migration đã apply — thêm file mới. Lesson L134: sửa cả comment trong file migration CIS cũng làm vỡ Copy Guard.
- **Expand/contract (parallel change)** — cách đổi schema không downtime khi 3 app dùng chung 1 RDS. Martin Fowler định nghĩa
  **3 pha: expand → migrate → contract**; dưới đây tách pha migrate thành 2 bước (ghi đôi rồi chuyển đọc) cho dễ làm:
  1. **Expand**: thêm cột/bảng mới (nullable, không ràng buộc phá). PR migration-only, merge + apply trước (S237 D8).
  2. **Migrate code**: deploy code ghi cả cũ và mới; backfill dữ liệu.
  3. **Switch reads**: đọc từ cấu trúc mới; theo dõi.
  4. **Contract**: ở release sau, xoá cột/bảng cũ (`-- migrate: destructive` → snapshot RDS tự động trước).
  - Nhờ vậy code bản N và N+1 đều chạy được trên cùng schema → rollback app luôn an toàn (aa-ship §5: "old app must run on new schema").
- Đề xuất nhỏ: app khi khởi động kiểm `required_schema_version` (S241 U-50) — fail sớm nếu deploy app trước migration.

### 4.7 Hạ tầng (Terraform)

| Nguyên tắc | Hiện trạng | Việc |
|---|---|---|
| Pin core `required_version`, provider `~>`, commit lockfile | Có | Giữ |
| Pin engine (RDS 15.17, ElastiCache 7.1) | Có | Ghi vào CHANGELOG Infra mỗi lần nâng |
| Module dùng `?ref=vX.Y.Z` | Module local, không cần | [CHƯA CẦN] tới khi chia sẻ module |
| State remote + lock + bucket versioning | S3 `aa-cis-tfstate-005097885195` + DynamoDB `aa-cis-tfstate-lock-005097885195` (`accounts/aa365/versions.tf`); S243 đã cấp quyền IAM trước cho `use_lockfile` (`cicd_split.tf`), backend chưa đổi | [cần kiểm] versioning bật trên bucket state |
| Plan trong PR, apply từ CI trên `main` | Plan PR có; `terraform-apply.yml` dispatch-only, `if: github.ref == 'refs/heads/main'`, GitHub environment tên `prod` | Giữ; đổi tên environment `prod` (ví dụ `dev-apply`) vì nó apply **dev** state (S241 D-16 / P2-1) |
| Không apply từ worktree/nhánh | Lesson L66 (apply từ worktree trước merge làm `main` chậm hơn hạ tầng thật) | Ghi vào runbook apply |
| Dọn file thừa | `main.tf.bak`, `main.tf.bak2`, thư mục rỗng `envs/dev` ở gốc Infra | Xoá trong 1 PR `chore` |
| **Change log cho infra** | Không có | release-please ở Infra + PR mô tả "resource đổi gì, chi phí bao nhiêu, rollback thế nào" + đính plan |

### 4.8 Image / artifact

- **Đúng chuẩn rồi**: tag theo SHA, ECR IMMUTABLE, không còn `:latest` (AA-725/AA-869), task-def trỏ SHA → rollback = deploy lại revision cũ.
- Bổ sung khi có tag release: thêm tag phụ `v0.4.0` cho cùng digest (không build lại). Với ECR immutable, tag mới trên digest cũ là hợp lệ.
- **SBOM** (danh sách thư viện trong image): CIS đã sinh bằng syft — đính vào GitHub Release. Trivy hiện **report-only**
  (`ci.yml:202`) → chuyển sang chặn với mức CRITICAL trước prod.
- **Provenance attestation** (`actions/attest-build-provenance`) ~ SLSA Build L2, chi phí thấp — [BẢN NHẸ], trước prod.
- **Frontend (Vercel)**: mỗi deployment Vercel đã gắn commit SHA. Để biết FE nào đang chạy, hiển thị SHA ngắn + version ở footer
  trang admin (Vercel cấp sẵn biến hệ thống chứa commit SHA lúc build — tên có dấu gạch dưới, **sửa tay trong VSCode**). Version FE
  đi theo version của repo (release-please bump `package.json`).

### 4.9 Prompt và model LLM

- **Model**: luôn pin model ID chính xác, không "latest" — đã có `shared.llm_model_catalog` (ADR 0005) + `shared.llm_role_config`
  có audit + shadow (`shared.llm_shadow_log`).
- **Prompt**: hiện chưa có version ID gắn vào từng call. Đề xuất [CẦN NGAY trước khi đổi prompt lớn]:
  - Prompt nằm trong git; mỗi prompt có id + version (vd `writer.tour_summary@3`) hoặc dùng hash nội dung (8 ký tự).
  - Ghi `prompt_version` vào `shared.llm_call_log` (cần 1 migration expand — cột nullable).
  - Đổi prompt/model/route = PR có **run ID eval** (golden set AA-729) so với baseline. `eval-regression.yml` hiện chỉ chạy tay,
    lần cuối 01/08/2026.
- Lợi ích: khi chất lượng tụt hoặc chi phí nhảy, truy được "prompt bản nào, model nào, từ ngày nào".

### 4.10 Một "version" chảy từ commit tới release note như thế nào

```
1. PR "feat: add tour availability filter"  (Refs AA-901)  → squash merge vào main
        │  commit 3f9c2e1
2. CI build image ECR:  aa-cis-api:dev-3f9c2e1   (immutable, APP_GIT_SHA=3f9c2e1)
        │
3. deploy-dev.yml đăng ký task-def aa-cis-dev-api:686 → ECS rolling, circuit breaker
        │  smoke: GET /health → {"version":"0.4.0-dev","git_sha":"3f9c2e1"}  phải khớp SHA  ← CIS cần thêm (copy Booking)
4. Verify live (aa-ship §3) → comment "Verified live" trên Linear AA-901
        │
5. release-please đã gom commit vào PR "chore(main): release 0.4.0"
   merge → tag v0.4.0 + CHANGELOG.md + GitHub Release (+ SBOM)   ← thiếu hiện nay
        │  (tuỳ chọn) gắn thêm tag image v0.4.0 cho digest dev-3f9c2e1
6. Sentry release = 3f9c2e1 / v0.4.0  → lỗi mới gắn đúng bản
        │
7. Release note nghiệp vụ → nháp Jira → Nghiệp duyệt → đăng cho chị Thư
```

Kết quả: hỏi "lỗi này xuất hiện từ bản nào?" hay "tenant đang dùng tính năng gì?" đều trả lời được bằng 1 tra cứu.

**Bảng "cái gì đang chạy ở đâu"** [BẢN NHẸ]: một script/trang admin gom `/health` của CIS api/worker, Booking, TP Lambda (tag
Lambda version/alias), Vercel deployment hiện hành → 1 bảng `service | git_sha | version | deployed_at`. Lesson L61 (worker chạy
task-def cũ) sẽ bị bắt ngay.

> Lưu ý thao tác: các tên biến môi trường có dấu gạch dưới (vd `APP_GIT_SHA`, `NEXT_PUBLIC_*`) khi áp dụng thì **sửa tay trong VSCode**,
> không sinh script tự động (quy tắc `~/.claude/CLAUDE.md`).

---

## 5. Phát hành và cập nhật tính năng

### 5.1 Môi trường — khi nào thêm staging/prod

| Môi trường | Mục đích | Hiện trạng | Khi nào thêm |
|---|---|---|---|
| Local | Dev, unit test | Có | — |
| PR preview (ephemeral) | Xem FE trước merge | Vercel preview + SSO bypass, `ui-smoke.yml` (3 lần gần nhất bị skipped) | Có; sửa để smoke chạy thật |
| **Dev** (acc2) | Tích hợp, được phép vỡ | Có — nhưng **đang chứa PII thật của tenant/khách** (S241), thực chất là "prod mềm" | — |
| Staging | Giống prod, verify trước release | Không | Khi có prod. Có thể scale-to-zero để rẻ; hoặc bỏ qua staging và dùng prod + flag |
| Prod | Người dùng thật | Không (trên acc2, không tách account — `~/.claude/CLAUDE.md`) | Có ngày go-live → ADR 0012 / U-40 trước |

Nguyên tắc **build once, deploy many**: cùng một image digest đi qua dev → (staging) → prod; cấu hình khác nhau nằm ở env/secrets
(12-factor), **không build lại theo môi trường**. Hệ đã sẵn sàng vì tag theo SHA + ECR immutable.

### 5.2 Deploy ≠ Release: feature flags

- **Deploy**: code đã chạy trên môi trường. **Release**: người dùng thấy tính năng. Flag tách 2 việc này: merge + deploy "tối"
  (flag off), bật cho 1 tenant thử, rồi bật hết; có sự cố thì tắt flag thay vì rollback.
- Hệ mình đang có flag ad hoc: `LEGACY_ADMIN_LOGIN_ENABLED` (cutover Cognito), cờ tenant pool fail-closed (D-12, #792),
  kill switch theo job kind (`docs/ops/incident-response.md`), route LLM trong DB (`shared.llm_role_config`).
- Đề xuất [BẢN NHẸ]:
  - 1 bảng `shared.feature_flag(key, owner_app, type, enabled, tenant_allowlist, created_at, remove_by)` hoặc giữ env var cho
    cờ vận hành. Không mua LaunchDarkly — [CHƯA CẦN]. FE có thể dùng Vercel Flags nếu cần.
  - 4 loại cờ: **release** (tạm, phải gỡ), **ops/kill-switch** (lâu dài), **experiment**, **permission**.
  - Mỗi cờ release có `remove_by` + issue Linear để gỡ — tránh "flag debt".
  - Danh sách cờ đang sống nằm ở 1 chỗ (bảng hoặc `docs/ops/feature-flags.md`).

### 5.3 Thay đổi phá tương thích — quy trình mẫu

Ví dụ: thêm `availability` vào tour catalog cho TripPlanner, đổi dần tên field `price` → `price_from`.

| Bước | Repo | Việc | Release |
|---|---|---|---|
| 1 | CIS | Migration expand: thêm cột nullable (PR migration-only) → copy sang Infra → DB Migrate check/apply | — |
| 2 | root | `catalog.tour.v1.2.json` (minor: thêm field), test pin hash cập nhật | — |
| 3 | CIS | Code ghi cột mới + trả cả `price` và `price_from`; backfill qua `shared.job` | CIS v0.5.0 (`feat`) |
| 4 | TripPlanner | Đọc field mới sau flag `tp_show_availability` | TP v0.5.0 |
| 5 | — | Bật flag cho 1 tenant → verify → bật hết | (release cho người dùng) |
| 6 | CIS | Đánh dấu `price` deprecated (CHANGELOG `Deprecated`, header Deprecation nếu là REST) | CIS v0.5.1 |
| 7 | CIS | Sau cửa sổ chuyển đổi: migration contract xoá cột cũ (`-- migrate: destructive`) + contract `v2` nếu bỏ field | CIS v0.6.0 / `v1.0` sau prod |

Thứ tự vàng: **DB trước, producer sau, consumer cuối; gỡ cái cũ sau cùng.**

### 5.4 Rollout và rollback

| Thành phần | Rollout hiện có | Rollback | Ghi chú |
|---|---|---|---|
| ECS (CIS api/worker, Booking) | Rolling + circuit breaker + `stopTimeout=90`; deploy-gate chặn khi `shared.job` còn job | `update-service` về task-def trước, api + worker cùng SHA, rồi revert PR trên `main` (aa-ship §5) | Blue/green/canary cho ECS — [CHƯA CẦN] |
| Vercel FE | CI tạo deployment, prod khi merge `frontend/**` | Instant Rollback (Hobby: chỉ về bản prod liền trước) → Promote | Muốn rollback xa hơn: redeploy commit cũ |
| TP Lambda | `deploy-lambdas.yml` path-filtered, **không `needs` CI, không smoke** | Revert trên `main` | Thêm `needs: ci` + smoke + alias `live` (S241 U-54) |
| DB | Forward-only | Không rollback schema; roll-forward bằng migration mới; restore PITR là đường cuối | Lý do bắt buộc expand/contract |
| Terraform | Plan PR → apply dispatch | Revert PR + apply lại; resource có dữ liệu thì snapshot trước | Ghi chi phí + rollback trong PR |

**Rollback trước, điều tra sau**: trong sự cố, ưu tiên quay về bản tốt đã biết (nhanh nhất). Chỉ **roll-forward** (ship bản sửa)
khi rollback không an toàn (vd đã chạy migration không đảo ngược). Đề xuất gom phần rollback từ `skill/aa-ship/SKILL.md` §5 thành
1 runbook ngắn mỗi app trong `docs/ops/runbooks/rollback-<app>.md`.

### 5.5 Definition of Done — giữ aa-ship, thêm 2 dòng

DoD hiện tại (`skill/aa-ship/SKILL.md`) đã tốt hơn mức trung bình: merge + CI xanh + deploy rollout COMPLETED + api/worker cùng SHA
+ `job_worker_started` + curl endpoint đổi + UI check + plan Terraform đã review + comment "Verified live". Thêm:

- [ ] Docs checklist trong PR đã tick (CONTEXT/ADR/runbook/contract/N/A).
- [ ] Nếu là `feat`/`fix` hướng người dùng: dòng CHANGELOG đúng (release-please tự lấy từ tiêu đề PR — kiểm tiêu đề có nghĩa).
- [ ] Nếu đụng LLM: run ID eval + `prompt_version`.
- [ ] Nếu thêm AWS resource: ước tính chi phí tháng.

### 5.6 Definition of Ready — mẫu mới cho issue (quan trọng khi agent code)

Mẫu viết tiếng Anh (issue Linear là tiếng Anh theo language-convention):

```
## Goal            — 1–2 sentences, business outcome
## Scope           — in / out (which repo, which schema)
## Acceptance      — 3–6 testable criteria (endpoint X returns field Y; UI shows Z)
## Verify          — how to prove it live (curl, screen, query)
## Risk class      — none | auth | migration | IAM/secret | delete | cost | LLM
## Dependencies    — issues/PRs/migrations that must land first
## Docs impact     — CONTEXT / ADR / runbook / contract / none
```

Issue chưa đủ các mục trên → chưa giao cho Kiro/subagent. Mẫu này đặt vào `skill/aa-linear-issue/SKILL.md`.

### 5.7 Change management nhẹ (thay cho CAB)

- **PR = change record**: mô tả, rủi ro, rollback, issue liên kết. **CI = cổng duyệt tự động**.
- Thay đổi rủi ro (auth, thanh toán, IAM, DB destructive, hạ tầng tốn tiền) → bắt buộc `kiro-reviewer` hoặc review của Nghiệp,
  dù đang ở dev-phase self-merge. Ghi nhãn `risk:high` trên PR.
- Repo private (Infra, root) không có branch protection vì GitHub Free (API trả 403). Lựa chọn:
  (a) nâng GitHub Team (~4 USD/người/tháng [cần kiểm giá hiện hành]) để có ruleset + required checks;
  (b) giữ như hiện tại, bù bằng `if: ref == main` + OIDC trust `refs/heads/main` (AA-866). Quyết khi lên prod.
- **CODEOWNERS** cho đường nhạy cảm (`.github/workflows/**`, `**/migrations/**`, `accounts/**`, `.claude/**`, `skill/**`) —
  [BẢN NHẸ]; có tác dụng khi bật required review lúc prod. **Bẫy với đội 1 người**: GitHub không cho tác giả PR tự approve PR của
  mình. Hiện agent mở PR bằng tài khoản GitHub của Nghiệp, nên bật required review sẽ khoá luôn PR của chính Nghiệp. Muốn dùng thật thì
  agent phải có danh tính riêng (GitHub App/bot user, P7) để Nghiệp đứng vai người duyệt.

---

## 6. Vận hành và chi phí

### 6.1 Observability (khả năng quan sát)

Ba tín hiệu: **logs** (sự kiện), **metrics** (con số theo thời gian), **traces** (đường đi của 1 request qua nhiều service).

| | Hiện có | Nên thêm | Mức |
|---|---|---|---|
| Logs | CloudWatch text, giữ 14 ngày (flow log 7), chưa có request ID | JSON có `request_id`, `tenant_id`, `git_sha`; truyền `X-Request-ID` giữa FE → CIS → Booking | [BẢN NHẸ] trước prod |
| Metrics / alarm | ~36 khối `aws_cloudwatch_metric_alarm` ở aa365 root (`observability*.tf`, `identity.tf`, `ses.tf`, `rds_snapshot_expiry.tf`: CIS 5xx/p95, ECS, Booking, TP Lambda, RDS, jobs, SES, Cognito…) → SNS e-mail | Mỗi alarm có `runbook_url` trong description; kênh thứ 2 ngoài e-mail (Slack/điện thoại) khi prod | [CẦN NGAY] phần runbook link |
| Errors | Sentry cho CIS backend + frontend | Booking, TripPlanner (AA-871); bật Sentry release = SHA | [CẦN NGAY trước prod] |
| Uptime | 1 monitor Sentry free cho CIS `/health` + ops-probe Lambda hằng ngày | Health check cho Booking/TP (CloudWatch Synthetics có phí — báo giá trước) | [BẢN NHẸ] |
| Traces | Không | OpenTelemetry — [CHƯA CẦN] (S238: chỉ làm khi job chậm không giải thích được) |
| LLM | `shared.llm_call_log` (cost, account, fallback, job_id) | `prompt_version`, latency p95 theo stage | [CẦN NGAY] khi đổi prompt |

Nhớ 2 bộ chỉ số: **RED** cho service (Rate, Errors, Duration) và **USE** cho tài nguyên (Utilization, Saturation, Errors).
Alarm theo **triệu chứng người dùng cảm nhận** (5xx, health fail, queue kẹt, vượt budget), không theo nguyên nhân (CPU 70%).

### 6.2 SLO bản nhẹ

- **SLI**: con số đo được (vd % request không 5xx). **SLO**: mục tiêu cho SLI (vd 99.5% trong 30 ngày). **SLA**: cam kết hợp đồng
  có phạt — không áp ở Dev. **Error budget** = 1 − SLO: còn budget thì ship tính năng, hết thì ưu tiên ổn định.
- Đề xuất khi có người dùng thật: mỗi API public 2 SLO — availability 99.5%/30 ngày và p95 latency (CIS < 1s, Booking < 800ms
  [số gợi ý, chốt theo đo thực tế]). Chính sách error budget chính thức — [CHƯA CẦN] ở Dev.
- Memory `dev-no-waiting`: Dev không có traffic thật → đừng đặt watch chờ thời gian; SLO chỉ có nghĩa khi có prod.

### 6.3 Sự cố, runbook, postmortem

- Quy trình sự cố đã có: `docs/ops/incident-response.md` (SEV1–3, 15 phút đầu, thông báo tenant, write-up trong Linear).
- Bốn bước khi có sự cố: **phát hiện → giảm thiểu (rollback/tắt flag) → khắc phục → review**.
- **Runbook** = các bước chính xác cho 1 việc (rollback ECS, restore RDS, ECS exec S3-mediated). **Playbook** = chiến lược cho 1 loại
  sự cố (5xx tăng vọt, chi phí LLM tăng vọt). Mỗi runbook: trigger, điều kiện trước, lệnh copy-paste (AWS CLI **1 dòng**), cách verify, cách rollback.
- Top runbook nên có trong `docs/ops/README.md` (index): rollback ECS/Vercel/Lambda · restore RDS PITR (đã diễn tập S241, ~22 phút) ·
  restore 1 schema (AA-829 còn mở) · override deploy-gate · rotate secret · ECS exec S3-mediated · DB Migrate destructive · cost spike LLM ·
  Cognito/login lỗi (legacy flag) · SES bounce.
- **Postmortem không đổ lỗi** (blameless): timeline, nguyên nhân gốc, gì tốt/gì tệ, action item. Thói quen `lessons.md` đã đúng tinh thần
  này — chỉ cần thêm 1 mẫu ngắn trong `docs/ops/postmortem-template.md` cho sự cố SEV1–2.

### 6.4 Backup và DR

- **RPO** (Recovery Point Objective): mất tối đa bao nhiêu dữ liệu chấp nhận được. **RTO** (Recovery Time Objective): ngừng tối đa bao lâu.
- Hiện có: RDS PITR 7 ngày, `deletion_protection`, final snapshot, single-AZ; diễn tập PITR đầy đủ đạt (~22 phút, AA-829); Lambda hết hạn
  snapshot thủ công; snapshot tự động trước migration destructive. Mục tiêu prod đã ghi ở `data-standards/02-data-management.md` DM-9.3/DM-9.6.
- Còn thiếu: restore 1 schema, DSN qua CNAME (AA-829), Multi-AZ + backup cross-region (khi prod, U-40), **nhịp diễn tập theo quý**.
- Quy tắc nhớ: **backup chưa từng restore thử = chưa có backup.**

### 6.5 Nhịp bảo mật (security cadence)

| Nhịp | Việc | Hiện trạng |
|---|---|---|
| Mỗi PR | CodeQL, secret scanning + push protection (3 repo public), pip-audit chặn (CIS), gitleaks (Infra) | Có; Trivy CIS chỉ report |
| Hằng tuần | Merge PR Dependabot gom nhóm | `dependabot.yml` chỉ CIS + Infra → thêm Booking, TripPlanner |
| Hằng tháng | Rà danh sách secret sắp hết hạn/không dùng; rà cảnh báo CodeQL/Dependabot còn mở | Chưa có secrets register (AA-878) |
| Hằng quý | Access review: IAM role, GitHub collaborator/app, quyền agent, MCP connector; diễn tập restore | Chưa có (S241 đề xuất; AA-838 parked) |
| Trước prod | Rotate GitHub OAuth token bị lộ + RDS master password; GuardDuty, Access Analyzer, S3 public block, CloudTrail (AA-873); Redis AUTH/TLS (AA-874); agent dùng role riêng ít quyền | Đã lên backlog §1 |

### 6.6 FinOps — chi phí

FinOps có 3 pha: **Inform** (thấy tiền đi đâu) → **Optimize** (cắt chỗ phí) → **Operate** (thành thói quen).

| Việc | Hiện trạng | Đề xuất |
|---|---|---|
| Tag phân bổ chi phí | Tag `App` (cis, booking, tripplanner, shared) kích hoạt 15/10/2026 | Thêm `Env` (dev/prod) qua Terraform `default_tags` trước khi có prod; rà resource chưa tag |
| Budget | Tổng 250 USD (80%/100% actual), per-App (80% actual, 100% forecast) | Thêm budget cho acc1/acc3 (LLM satellite) nếu chưa có [cần kiểm] |
| **Cost Anomaly Detection** | **Không có** | Thêm monitor theo service + theo tag `App` (dịch vụ miễn phí) — [CẦN NGAY] |
| LLM ledger | `shared.llm_call_log` + `test_aa685_no_raw_model_calls.py` + quy tắc `stage="adhoc_<issue>"` + cap DFS/TP | Giữ; thêm `prompt_version` |
| Review tháng | Kế hoạch audit đầu tháng 11 (memory `infra-cost-audit-nov-2026`) | Biến thành nhịp tháng: 1 file `docs/ops/cost/2026-11.md` — tổng theo App, top 5 service, so tháng trước, giải thích chênh > 20% |
| **Unit cost** | Chưa có | USD / tour published, USD LLM / tour, USD / trip plan, USD / booking — số hữu ích nhất cho quyết định sản phẩm |
| Trước khi thêm dịch vụ | Quy tắc memory: báo giá tháng trước khi apply | Đưa vào PR template (§3.4) |

---

## 7. Đang làm tốt vs khoảng trống — lộ trình ưu tiên

### 7.1 Đang làm tốt (giữ và nhân rộng)

| Thực hành | Bằng chứng |
|---|---|
| Trunk-based, PR + required checks ở 3 repo app | ADR-2026-023; `gh api` branch protection CIS/Booking/TP |
| DoD có verify live | `skill/aa-ship/SKILL.md` §1–§5 |
| ADR theo phạm vi, amendment thay vì sửa | `docs/adr/0001…0008`, `0003a/0004a/0004b/0006a`, `skill/ai-nghiep/references/adr.md` |
| Contract event có version + quy tắc major/minor | `docs/contracts/README.md`, `*.v1.1.json`, `*.v1.2.json` |
| Tài liệu reference sinh tự động | `docs/architecture/db-schema-reference.md` ← `db-schema-dump.yml` |
| Migration theo owner, copy guard, apply qua CI, snapshot trước destructive | `infra/AA-CIS-Infra/db/README.md`, `migration-copy-guard.yml`, `db-migrate.yml` |
| Image immutable theo SHA, không `:latest` | `deploy-dev.yml:86`, ECR IMMUTABLE (AA-725/AA-869) |
| Booking pipeline mẫu: smoke so `git_sha` | `apps/AA-Booking/.../routers/health.py:21`, `deploy-dev.yml:201` |
| Deploy-gate fail-closed khi có job | CIS `/admin/job-runner/deploy-gate` (AA-868) |
| LLM cost ledger + test cấm gọi model trực tiếp | `shared.llm_call_log`, `test_aa685_no_raw_model_calls.py` |
| Lesson log → guard CI | `skill/aa-lessons/lessons.md` |
| Hook chặn subagent làm việc nguy hiểm | `.claude/hooks/subagent-guardrails.sh` |
| Đã diễn tập PITR thật | `docs/audits/2026-10-17-S241-restore-drill/` |

### 7.2 Lộ trình

**Now — 2 tuần tới, rẻ, mỗi việc ≤ 1 PR** (đánh số để dễ chọn vào phiên 3–5 issue):

| # | Việc | Repo | Cỡ | Liên quan S241 |
|---|---|---|---|---|
| N1 | CIS `/health` trả `version` + `git_sha` từ `APP_GIT_SHA`; smoke trong `deploy-dev.yml` so khớp SHA (copy mẫu Booking) | CIS | XS | — |
| N2 | release-please (manifest mode, `bump-minor-pre-major`, token GitHub App — xem bẫy §4.2) + `CHANGELOG.md` + tag đầu tiên cho CIS, Booking, TripPlanner (Infra tuỳ chọn) | 3 repo | S | kéo sớm 1 phần U-47 |
| N3 | PR template có mục Risk/Rollback/Docs checklist; lint tiêu đề PR (semantic PR) ở Booking + TP | 4 repo | XS | — |
| N4 | Dọn lệch lớp chỉ dẫn agent: root `.claude/CLAUDE.md`, `.kiro/steering/db-schema.md`, Infra CLAUDE.md; ghi chú cho Nghiệp sửa tay `~/.claude/CLAUDE.md` | root, Infra | S | — |
| N5 | CIS `.gitignore`: bỏ ignore `docs/`, chỉ ignore binary; rà và add các note/investigation local | CIS | S | — |
| N6 | `docs/ops/README.md` (index runbook toàn hệ) + `rollback-<app>.md` tách từ aa-ship §5 | root | S | — |
| N7 | Cost Anomaly Detection (monitor service + tag `App`) qua Terraform, gửi cùng SNS e-mail | Infra | XS | — |
| N8 | `delete_branch_on_merge=true` ở CIS/Booking/Infra/root (TP đã bật) + dọn nhánh đã merge (~730 nhánh remote CIS); tắt merge commit để squash-only (cả 5 repo đang cho phép) | 4 repo | XS | U-11 |
| N9 | Tạo `infra/AA-CIS-Infra/docs/adr/README.md` và `apps/AA-TripPlanner-Web/docs/adr/README.md` (rỗng, có mẫu) | Infra, TP | XS | — |
| N10 | `docs/glossary.md` (tiếng Anh, dịch từ §8) + mẫu DoR vào `skill/aa-linear-issue/SKILL.md` | root | XS | — |
| N11 | Xoá `main.tf.bak`, `main.tf.bak2`, thư mục rỗng `envs/dev` ở Infra | Infra | XS | — |

**Before prod — khi có ngày go-live** (nhiều việc đã nằm trong U-40):

| # | Việc | Ghi chú |
|---|---|---|
| P1 | ADR 0012 mô hình môi trường + layout Terraform (D-16/D-17); build once, promote cùng digest | U-40 |
| P2 | OpenAPI export trong CI + `response_model` cho route public + oasdiff chặn breaking | — |
| P3 | Eval gate: golden set AA-729 + `eval-regression.yml` chạy trên PR đụng prompt/LLM; cột `prompt_version` trong `llm_call_log` | — |
| P4 | Sentry cho Booking + TripPlanner (AA-871), Sentry release = SHA | — |
| P5 | TP Lambda deploy `needs: ci` + smoke + alias `live` | U-54 |
| P6 | Trivy chặn CRITICAL, nâng coverage CIS (30% → mục tiêu dần), `tsc`/`next build` gate cho CIS FE | — |
| P7 | Bảo mật: rotate token + RDS master, secrets register (AA-878), AA-873/874/876, agent role ít quyền + GitHub App cho agent | S241 P0-3/P1-1 |
| P8 | Cổng merge cho prod: required review cho đường nhạy cảm (CODEOWNERS), quyết GitHub Team cho repo private | — |
| P9 | DR: restore 1 schema, DSN CNAME, Multi-AZ, backup cross-region, diễn tập theo quý | AA-829, U-40 |
| P10 | 2 SLO/API public; alarm có runbook link; kênh cảnh báo thứ 2 | — |
| P11 | Logs JSON + request ID xuyên app; GitHub Deployments + bảng "what runs where" | U-47 |
| P12 | Tag `Env`, budget prod riêng, release note cho tenant | U-47 |

**Later — khi team lớn hoặc có traffic thật:**

- Số DORA hằng tháng (deploy frequency, lead time, change fail rate, recovery time, rework rate) đếm từ GitHub API.
- Unit cost hằng tháng thành dashboard admin.
- Sơ đồ C4 L1–L2 trong `ecosystem-architecture.md` (Mermaid).
- Provenance attestation (~SLSA L2), SBOM đính release.
- Well-Architected self-review 1 lần/năm/app (dùng thêm Generative AI Lens cho phần LLM).
- NIST SSDF, NIST AI RMF, OWASP LLM Top 10 2025 dùng làm checklist đọc.
- OpenTelemetry tracing (khi job chậm không giải thích được).

**[CHƯA CẦN] — bỏ qua có chủ đích:** Scrum ceremonies, CAB, chứng nhận ISO/IEC 42001, chương trình OWASP SAMM đầy đủ, SLSA L3,
canary/blue-green cho ECS, site tài liệu nhiều version, lịch trực paging, nền tảng DORA/flag trả phí, arc42 đầy đủ, chính sách
error budget chính thức ở Dev.

---

## 8. Thuật ngữ

| # | Thuật ngữ | Giải thích ngắn | Ví dụ trong hệ mình |
|---|---|---|---|
| 1 | SDLC | Vòng đời phát triển phần mềm từ ý tưởng tới khai tử | §2.2 |
| 2 | ADLC | (dự án) SDLC + kiểm soát agent + vòng đời tính năng LLM | Kiro viết code, Claude gác; writer/judge có eval |
| 3 | Trunk-based development | Mọi người merge nhánh ngắn vào 1 nhánh chính luôn deploy được | ADR-2026-023, `main` |
| 4 | Pull Request (PR) | Đề nghị gộp code, nơi review + chạy CI | Squash-merge có `Refs AA-xxx` |
| 5 | CI (Continuous Integration) | Tự động build/test mỗi thay đổi | `ci.yml`: lint, unit, integration, docker build |
| 6 | CD (Continuous Delivery/Deployment) | Tự động đưa bản đã qua CI lên môi trường | `deploy-dev.yml` |
| 7 | Required checks / branch protection | Cổng bắt buộc xanh trước khi merge | 5 check ở CIS/Booking |
| 8 | Conventional Commits | Chuẩn tiêu đề commit `type(scope)!: subject` | `fix: excel price mapping` |
| 9 | SemVer | Version `MAJOR.MINOR.PATCH` theo mức tương thích | CIS `v0.4.0` (đề xuất) |
| 10 | CalVer | Version theo ngày | `infra-2026.10.19` (tuỳ chọn) |
| 11 | Git tag | Nhãn cố định trỏ vào 1 commit | `v0.4.0` (chưa có) |
| 12 | GitHub Release | Trang phát hành gắn tag, notes, artifact | Sinh bởi release-please |
| 13 | CHANGELOG | Nhật ký thay đổi cho người đọc, theo version | `CHANGELOG.md` (chưa có) |
| 14 | Release note | Tóm tắt thay đổi theo ngôn ngữ nghiệp vụ | Jira comment cho chị Thư |
| 15 | release-please | Bot mở "release PR" bump version + changelog, tag khi merge | Đề xuất N2 |
| 16 | Immutable image tag | Tag image không ghi đè được | `dev-<sha>`, ECR IMMUTABLE |
| 17 | Task definition revision | Phiên bản cấu hình chạy container trên ECS | `aa-cis-dev-api:685` |
| 18 | Rolling deploy | Thay task dần dần | ECS mặc định |
| 19 | Circuit breaker (ECS) | Tự dừng + quay lại khi deploy mới không khoẻ | Đã bật |
| 20 | Blue/green, canary | Hai môi trường đổi traffic / chuyển % traffic dần | [CHƯA CẦN] |
| 21 | Rollback / roll-forward | Quay về bản cũ / ship bản sửa | aa-ship §5 |
| 22 | Feature flag | Công tắc bật/tắt tính năng không cần deploy | `LEGACY_ADMIN_LOGIN_ENABLED` |
| 23 | Deploy vs release | Code chạy vs người dùng thấy | Bật flag cho 1 tenant trước |
| 24 | Expand/contract (parallel change) | Đổi schema/API theo 3 pha expand → migrate → contract để bản cũ và mới cùng chạy | §4.6, §5.3 |
| 25 | Migration | File SQL đánh số đổi cấu trúc DB | `api/migrations/247_*.sql`, `bk-015` |
| 26 | Forward-only | Không rollback schema, chỉ thêm migration mới | Quy tắc DB Migrate |
| 27 | Idempotent | Chạy lại nhiều lần không đổi kết quả | `ON CONFLICT DO NOTHING` trong `schema_versions` |
| 28 | Contract (event/API) | Hợp đồng dữ liệu giữa các app | `inquiry.submitted.v1.2.json` |
| 29 | OpenAPI | Đặc tả máy đọc được của REST API | `/booking/openapi.json` |
| 30 | Breaking change | Thay đổi làm client cũ hỏng | Bỏ field `price` |
| 31 | Deprecation / Sunset header | Báo trước API sắp bỏ + ngày gỡ | RFC 9745 / RFC 8594 |
| 32 | ADR | Bản ghi quyết định kiến trúc: bối cảnh, quyết định, hệ quả | `docs/adr/0006-ecosystem-identity.md` |
| 33 | Docs-as-code | Tài liệu là code: cùng repo, cùng PR, có CI | §3.4 |
| 34 | Diátaxis | Chia tài liệu: tutorial / how-to / reference / explanation | §3.1 |
| 35 | Runbook / playbook | Bước cụ thể cho 1 việc / chiến lược cho 1 loại sự cố | `docs/ops/incident-response.md` |
| 36 | DoR / DoD | Điều kiện để bắt đầu / để coi là xong | Mẫu §5.6 / `skill/aa-ship` |
| 37 | Infrastructure as Code (IaC) | Hạ tầng khai báo bằng code | Terraform `infra/AA-CIS-Infra` |
| 38 | Terraform state / lockfile | Ghi nhớ hạ tầng thật / khoá version provider | S3 `aa-cis-tfstate-…`, `.terraform.lock.hcl` |
| 39 | OIDC (CI → AWS) | CI lấy quyền AWS tạm thời, không cần key tĩnh | Role `aa-cis-dev-app-deploy` |
| 40 | Observability | Hiểu hệ thống qua logs / metrics / traces | CloudWatch + Sentry |
| 41 | SLI / SLO / SLA / error budget | Số đo / mục tiêu / cam kết hợp đồng / phần lỗi được phép | §6.2 |
| 42 | RPO / RTO | Mất dữ liệu tối đa / ngừng tối đa chấp nhận | PITR 7 ngày; drill ~22 phút |
| 43 | Postmortem (blameless) | Phân tích sự cố không đổ lỗi, ra action item | Lesson log |
| 44 | DORA metrics | 5 chỉ số giao hàng: tần suất deploy, lead time, recovery time, change fail rate, rework rate | Later |
| 45 | FinOps / unit cost | Quản trị chi phí cloud / chi phí trên 1 đơn vị nghiệp vụ | USD LLM / tour |
| 46 | Cost allocation tag | Tag để Cost Explorer chia tiền theo app | Tag `App` |
| 47 | Eval / golden set | Bộ mẫu chuẩn để chấm chất lượng LLM trước khi đổi prompt/model | AA-729, `eval-regression.yml` |
| 48 | Shadow run | Chạy song song model/route mới, không trả kết quả cho người dùng | `shared.llm_shadow_log` |
| 49 | SBOM | Danh sách mọi thư viện + version trong artifact | syft trong CI CIS |
| 50 | SLSA / provenance | Mức tin cậy chuỗi build / chứng nhận "ai build cái gì từ commit nào" | Later |
| 51 | Kanban | Kéo việc liên tục từ 1 hàng đợi có thứ tự, giới hạn việc dở dang (WIP), không chia sprint | Backlog sống + phiên 3–5 issue |
| 52 | Build once, deploy many | Build 1 artifact, đưa cùng digest qua mọi môi trường; khác nhau chỉ ở config (12-factor) | `dev-<sha>` → prod sau này |
| 53 | PITR | Point-In-Time Recovery: khôi phục DB về 1 thời điểm bất kỳ trong cửa sổ lưu | RDS PITR 7 ngày, drill AA-829 |
| 54 | CODEOWNERS | File GitHub gán người duyệt bắt buộc theo đường dẫn | §5.7 (cần danh tính agent riêng) |
| 55 | Terraform drift | Hạ tầng thật lệch khỏi code/state (do sửa tay hoặc apply từ nhánh) | Lesson L66 |
| 56 | NIST SSDF (SP 800-218) | Bộ thực hành phát triển phần mềm an toàn của NIST (4 nhóm: chuẩn bị tổ chức, bảo vệ phần mềm, tạo phần mềm an toàn, xử lý lỗ hổng) | Checklist đọc, Later |
| 57 | LLMOps | Vận hành tính năng LLM: version prompt/model, eval, giám sát chất lượng + chi phí | ADLC phần (b), §4.9 |

---

## 9. Đọc thêm (nguồn gốc)

**Quy trình & DevOps**
- Trunk-based development — https://trunkbaseddevelopment.com/
- DORA metrics — https://dora.dev/guides/dora-metrics/ · nghiên cứu: https://dora.dev/research/
- Google SRE Book + Workbook (miễn phí) — https://sre.google/books/
- 12-Factor App — https://12factor.net/
- Feature toggles (Martin Fowler) — https://martinfowler.com/articles/feature-toggles.html · OpenFeature — https://openfeature.dev/
- Parallel change / expand-contract — https://martinfowler.com/bliki/ParallelChange.html

**Tài liệu**
- Docs-as-code (Write the Docs) — https://www.writethedocs.org/guide/docs-as-code/
- Diátaxis — https://diataxis.fr/
- ADR (Nygard) — https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions · MADR — https://adr.github.io/madr/
- C4 model — https://c4model.com/ · arc42 — https://arc42.org/overview
- AGENTS.md — https://agents.md/

**Phiên bản & phát hành**
- SemVer — https://semver.org/ · CalVer — https://calver.org/
- Conventional Commits — https://www.conventionalcommits.org/en/v1.0.0/
- Keep a Changelog — https://keepachangelog.com/en/1.1.0/
- release-please — https://github.com/googleapis/release-please
- GitHub Releases — https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- OpenAPI — https://spec.openapis.org/oas/latest.html · oasdiff — https://github.com/oasdiff/oasdiff
- RFC 9745 (Deprecation header) — https://www.rfc-editor.org/rfc/rfc9745 · RFC 8594 (Sunset) — https://www.rfc-editor.org/rfc/rfc8594
- Terraform version constraints — https://developer.hashicorp.com/terraform/language/expressions/version-constraints · lockfile — https://developer.hashicorp.com/terraform/language/files/dependency-lock
- ECR tag immutability — https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
- ECS deployment types / circuit breaker — https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-types.html · https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html

**Bảo mật & AI**
- NIST SSDF SP 800-218 — https://csrc.nist.gov/pubs/sp/800/218/final (bản v1.2 đang draft: https://csrc.nist.gov/pubs/sp/800/218/r1/ipd)
- OWASP SAMM — https://owaspsamm.org/model/ · OWASP Top 10 for LLM Apps 2025 — https://genai.owasp.org/llm-top-10/
- SLSA — https://slsa.dev/ [cần kiểm version hiện hành trên trang] · SBOM: https://cyclonedx.org/ , https://spdx.dev/
- NIST AI RMF — https://www.nist.gov/itl/ai-risk-management-framework · GenAI Profile NIST AI 600-1 — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

**Vận hành & chi phí**
- OpenTelemetry signals — https://opentelemetry.io/docs/concepts/signals/ · 4 golden signals — https://sre.google/sre-book/monitoring-distributed-systems/
- AWS DR options — https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html
- FinOps framework — https://www.finops.org/framework/
- AWS cost allocation tags — https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html
- AWS Cost Anomaly Detection — https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html
- AWS Well-Architected — https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html · Generative AI Lens — https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html

---

*Phương pháp: tổng hợp từ 3 báo cáo trinh sát đọc-only ngày 19/10/2026 (tài liệu & version; giao hàng/vận hành/chi phí; chuẩn
ngành) + bản review S241. Không có thay đổi nào với repo, AWS, Linear, Notion hay Jira khi viết bản này. Các mục **[cần kiểm]**
chưa được xác minh trực tiếp.*
