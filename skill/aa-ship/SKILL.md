---
name: aa-ship
description: Quy trình từ PR tới "Done" cho các repo AA_Ecosys (CIS, Booking, Partner, TripPlanner, Infra, repo gốc) — kiểm trước merge, cách merge (App aa-agent, branch protection), guard deploy khi còn job hoặc wave, Terraform apply, luồng migration, verify live sau deploy và chỉ đánh Done trên Linear khi có bằng chứng. Dùng khi chuẩn bị merge PR, deploy, Terraform apply, DB Migrate, rollback, hoặc định chuyển issue sang Done. Kiểm giao diện chi tiết thuộc aa-ui-verify.
---

# aa-ship

Mục tiêu: "Done" luôn nghĩa là đã chạy đúng trên môi trường thật, có bằng chứng.
Bài học của vùng này: `aa-lessons/lessons.md` mục "Verify và Done" + "Vận hành" — đọc trước khi merge/deploy.

## 0. Ai làm bước nào

- **Agent điều phối** push, mở PR, merge, `gh workflow run` (deploy, DB Migrate, Terraform apply, probe), ECS exec.
- **Subagent** chỉ code, test, commit local. Hook `.claude/hooks/subagent-guardrails.sh` chặn push/merge/`gh workflow run`/
  Terraform apply/`aws ecs execute-command`. Việc live (kiểm DB, verify) subagent giao lại dạng runbook/script kèm mục
  "post-merge steps cho orchestrator" — không lách qua script helper.

## 1. Trước khi mở/merge PR

- [ ] Branch `feat|fix|chore|docs/aa-xxx-<mô tả>` từ `origin/main` mới nhất (repo gốc: `master`).
- [ ] **Worktree luôn tạo bằng đường dẫn TUYỆT ĐỐI**: `/home/nghiep/projects/AA-Ecosys/.tmp-session/wt/<tên>`
  (đường dẫn tương đối với `git -C apps/<repo>` rơi vào trong repo con, không bị gitignore).
- [ ] Commit và PR body ghi **`Refs AA-xxx`**. Không `[AA-xxx]`, không `Fixes`/`Closes`, và tiêu đề PR không có mã
  issue (Linear đọc "fix: AA-xxx …" là câu đóng issue). PR docs/log nhắc issue khác thì ghi tên việc, không ghi mã.
- [ ] **Danh tính GitHub (ADR 0011):** push/PR/merge bằng App `aa-agent`:
  `/home/nghiep/projects/AA-Ecosys/tools/github/as-app.sh --repos <Repo> -- <git -C <worktree> push … | gh pr create … | gh pr merge …>`.
  Cần phiên AWS MFA còn hạn (`aa365-admin`; script đọc key từ Secrets Manager) và `tools/github/apps.env` của repo gốc;
  `git push` cần `gh auth setup-git` một lần. Kiểm `gh pr view <n> --json author` ra `app/aa-agent`. App
  `aa-ecosys-ci-bot` chỉ cho release-please và PR bot của Infra. Hướng dẫn: `docs/security/github-apps.md`.
- [ ] **PR rủi ro → vòng review trước merge** (auth/quyền, migration/RLS, CI/workflow/secret, xoá dữ liệu, middleware
  trên đường request): commit local → subagent review độc lập (chỉ đọc, nhiệm vụ "phá nó") → sửa mọi blocker/should-fix
  → điều phối push, chờ CI, merge.
- [ ] **Required check xanh:** `gh pr checks <n> --required` (danh sách theo branch protection từng repo, không nhớ
  cứng). Infra và repo gốc không có required check → đọc đủ `gh pr checks <n>` (Docs lint, Terraform Plan) trước merge.
  Vercel deploy + UI smoke không phải required → PR frontend kiểm riêng (`aa-ui-verify`).
- [ ] Test xanh local, đỏ CI → so package đã cài (`pip list` local vs CI/image) trước khi sửa code.
- [ ] Khẳng định "check xanh khi khớp / đỏ khi lệch" → chứng minh bằng nhánh thử hoặc draft PR có cài sẵn chỗ lệch rồi
  đóng không merge; không merge thứ sai để thử.
- [ ] **PR có migration — chọn luồng theo loại file (ADR 0017, AA-993; Part A MIG-4):**
  - **File expand** (header `-- migrate: expand`, chỉ thêm: object mới, cột nullable / default không volatile, index
    không unique; không bảng nóng): **một PR app** gồm file + code cần nó + nâng readiness lên key đó. Check "Migration
    preflight" của app phải xanh và ghi `expand`. Sau merge: bot migration-sync của Infra copy + merge PR copy (≤ 10′) →
    Migration Apply (khi `DB_AUTO_APPLY=true`) apply theo đúng thứ tự số + Isolation Probe chặn → DB Schema Dump, PR
    root tự merge khi sạch → Deploy Dev của app qua `schema-gate` (chờ key + job apply/probe của run Migration Apply
    xanh, tối đa `SCHEMA_GATE_TIMEOUT_S`, mặc định 40′) rồi mới roll. `DB_AUTO_APPLY` chưa bật → bot vẫn copy, người
    chạy DB Migrate `check` → `apply` cho file đó **trong cửa sổ của gate**; quá cửa sổ thì `schema-gate` đỏ (không
    deploy) → sau khi apply, **chạy lại Deploy Dev bằng tay** (Actions → Run workflow, hoặc "Re-run all jobs").
  - **File contract / destructive** (không header expand) → **luồng D8**: PR chỉ chứa file migration ở repo chủ merge
    trước → bot copy sang AA-CIS-Infra `db/migrations/<owner>/` (Migration Copy Guard đỏ nếu PR repo chủ chưa vào
    `main`; Migration Apply dừng ở file này, không bao giờ tự apply) → DB Migrate `check` → `apply` (chờ mọi bảng job
    owner rảnh và không wave mở) → merge PR bot `bot/db-schema-reference` (nếu chưa tự merge) → DB Isolation Probe →
    PR code. Preflight từ chối PR vừa thêm file contract vừa nâng readiness lên nó.
  - File đã copy sang Infra là **bất biến**: sửa bằng file mới; số file mới = max trên `main` + 1 (số thấp hơn cố ý →
    nhãn `migration:out-of-order`, không bao giờ tự apply).
  Log DB Migrate ghi login `db_migrator` và `ran as: <owner>` (`cis_owner` / `bk_owner` / `tp_owner` / `crm_owner`);
  `roles/` chạy bằng master. Chủ schema: `docs/database/schema-ownership.md`.
  - Migration đổi bảng/khoá/FK của schema có trang ERD thiết kế `enforce=true`
    (`docs/architecture/erd/design/<schema>.md`, repo gốc) → sửa trang đó trong cùng đợt thay đổi, không thì DB Schema
    Dump đêm đó đỏ bước drift.
  - Booking và AA-Partner deploy ở mọi push vào `main` chạm backend; từ AA-993 M4b Deploy Dev của CIS, Booking,
    Partner có `schema-gate` chặn trước khi roll (key chưa có, hoặc run Migration Apply gần nhất có apply/probe đỏ,
    sau `SCHEMA_GATE_TIMEOUT_S` (mặc định 40′) → đỏ, không deploy; sửa xong thì "Re-run failed jobs" run Infra đó rồi
    chạy lại Deploy Dev). PR code cần file
    contract vẫn chỉ merge sau `apply`; push chỉ đổi `api/migrations/**` (CIS, Partner) / `migrations/` (Booking)
    không deploy.
- [ ] **Cờ fail-closed (thiếu key = BẬT) + migration:** đặt cờ TẮT rõ ràng trước khi deploy code → apply migration →
  BẬT cờ + verify lật cờ.
- [ ] PR frontend → `npm run build` đầy đủ local (Node 22 qua nvm), rồi `aa-ui-verify`.
- [ ] PR xoá bảng/dữ liệu → quy trình DRY RUN (`aa-cis-schema/references/destructive-ops.md`).
- [ ] **Docs:** "Docs impact" của issue làm trong cùng PR (CONTEXT.md / ADR / runbook / contract / trang catalog
  `docs/README.md`), hoặc ghi "N/A". Trang catalog theo `docs/STYLE.md`; chỉ bump `last_reviewed` khi đã kiểm với hệ thật.
- [ ] **Changelog:** PR `feat`/`fix` người dùng thấy → tiêu đề PR đọc được như một dòng CHANGELOG (release-please lấy từ đây).
- [ ] **LLM:** đổi prompt/model/route → điền mục "LLM change" của mẫu PR CIS (id prompt trong sổ đăng ký
  `docs/llm/prompt-register.md`, loại eval); eval chạy tay theo runbook CIS `docs/llm/eval-runbook.md` (R2 trên golden
  set AA-729, `--stage adhoc_aa900`, trần mỗi lần chạy) — run ID + chi phí ghi vào PR (D-23, handbook §5.7).
  `prompt_version` chỉ khi ledger v2 (AA-804) đã có. Đổi route/model → chụp lại bảng route
  (`tools/docs/gen_llm_routes.py`, root `docs/generated/llm-routes.md`).
- [ ] **Cost:** thêm resource AWS hoặc lượt chạy trả phí → ước tính USD/tháng trong PR body (DM-10.7); resource mới có tag `App` (DM-10.1).

### Cách merge

- Squash chỉ sau `git fetch`; gộp commit bằng `git reset --soft $(git merge-base HEAD origin/main)`, không bằng
  `origin/main` trần. Trước mọi merge: `gh pr diff <n> --name-only` — có file bị xoá/đổi ngoài phạm vi PR thì dừng.
- **CIS, Booking, Partner: merge queue (AA-889).** Không `update-branch` nữa: một lệnh mỗi PR,
  `tools/github/mergeq.sh <Repo> <n>` — chờ check của PR, xếp hàng (`gh pr merge --squash --auto` qua `as-app.sh`),
  chờ tới merged, in SHA. Queue chạy lại required check trên commit tạm `gh-readonly-queue/main/*` (PR đi trước +
  `main` mới nhất) rồi tự squash vào `main`. Guard §2 (bảng job, wave) kiểm **trước khi** xếp hàng vì queue merge tự
  động. Rút PR khỏi hàng: `tools/github/mergeq.sh <Repo> <n> --dequeue` (GraphQL `dequeuePullRequest`, hoặc "Remove
  from queue" trên UI). `gh pr merge --disable-auto` chỉ huỷ được khi check của PR còn chạy; PR đã xanh thì đã vào
  thẳng hàng, lệnh đó không rút được. Check không báo → queue loại PR sau `check_response_timeout`; xem
  `gh run list --event merge_group`.
- TripPlanner: `gh pr merge <n> --auto --squash`. AA-CIS-Infra, repo gốc tắt auto-merge → `gh pr merge <n> --squash`
  sau khi check xanh.
- Nhiều PR backend cùng repo: xếp hàng cùng lúc được; queue có thể đẩy cả nhóm trong một push → một Deploy Dev cho cả
  nhóm, verify live (§3) cho từng PR của nhóm theo `git_sha` cuối. Deploy đỏ → tìm PR gây lỗi trong nhóm trước khi xếp
  tiếp.
- Chờ CI: `gh pr checks <n> --watch` (CI ~3–5′), kiểm một lần, không poll dồn.

### Ngoại lệ: PR release (release-please, AA-891)

- PR `chore(main): release x.y.z` ở cả 4 repo app, do `aa-ecosys-ci-bot` mở và tự cập nhật; chỉ đổi `CHANGELOG.md` +
  manifest + file version (CIS `api/version.py`, Booking `backend/pyproject.toml`, Partner `api/pyproject.toml`,
  TripPlanner chỉ manifest).
- **Không có `Refs AA-xxx`** — ngoại lệ duy nhất của luật Refs; không sửa tay title/body. Mỗi dòng CHANGELOG link tới
  commit/PR gốc, PR đó có `Refs`.
- Agent điều phối merge như mọi PR. Commit release **không** kích hoạt deploy; field `version` trên health (`/health`,
  `/booking/health`, `/crm/health`, TripPlanner `/api/health`) báo bản trước tới lần deploy kế; `git_sha` mới là bằng chứng.
- Sau khi tag: release note theo `docs/templates/release-note.md` (chỉ tính năng đã verify live) → draft Jira (`aa-jira-update`).

## 2. Guard trước merge backend, DB Migrate, Terraform apply

- Deploy Dev của 3 app có ECS worker tự chặn (AA-993 G5, C6.3a), nhưng **chỉ** khi: CIS có wave mở
  (`shared.rerun_wave.status = 'open'`) hoặc đang **chạy** một job kind `deploy_blocking` (`data_erasure`,
  `s1_batch_ingest`) — `/admin/job-runner/deploy-gate`; Booking đang chạy job retention (`bk_retention_job`,
  `bk_retention_inbox_redact`) — `/booking/ops/deploy-gate`; Partner đang chạy `crm_dispatch` — `/crm/ci/deploy-gate`
  (CRM web không có worker nên không có guard). "Đang chạy" gồm cả job kind đó **queued đến hạn trong 15 phút**
  (`blocking_due`: preflight chạy trước khi build, task cũ sẽ claim nó trước SIGTERM). Job queued/running loại khác
  **không** chặn nữa: worker drain khi
  SIGTERM, job còn chạy được release và task mới claim lại (G1–G4). Lý do bị chặn nằm ở `blocked_by` trong log
  preflight. Override chỉ Nghiệp, ghi lý do (`docs/ops/runbooks/deploy-gate-override.md`). Bị chặn → chờ job đó xong
  / đóng wave, hoặc hỏi Nghiệp nếu job treo, không tự override.
- **Wave đang chạy** → không merge PR backend/pipeline CIS, không DB Migrate (PR chỉ FE thì được); Deploy Dev CIS tự
  chặn khi wave mở. Booking/Partner không đọc wave CIS (design Q4). Driver wave có cờ tạm dừng trước wave kế: đặt cờ →
  chờ wave đang chạy đóng → deploy → verify → gỡ cờ (`aa-wave-rerun`). DB Migrate `apply` vẫn chờ **mọi** bảng job rảnh
  (C6.3b, không đổi).
- Kiểm tay mọi bảng job một lần: DB Migrate `mode=check` (input `migration` = một file đã apply, ví dụ
  `cis/<NNN>_<tên>.sql`; check chỉ báo cáo) liệt kê từng bảng job owner (`<schema>.job`) busy và wave mở.
- **Terraform:** plan trên PR (`terraform-plan.yml`) phải đọc; apply chỉ qua workflow (`terraform-apply.yml`, từ `main`).
  - Apply không có guard job. Trước apply đụng `aws_ecs_service`, `aws_ecs_task_definition` hoặc `aws_lambda_function`
    → idle gate tay (DB Migrate `check` không bảng nào busy, không wave), dán vào session log. Apply chỉ đổi
    alarm/IAM/secret metadata thì không cần gate. `main` của Infra không được có thay đổi đã merge mà chưa apply.
  - Plan guard (AA-846) từ chối thay đổi secret version / `random_password` / RDS instance; `allow_guarded` +
    `allow_reason` chỉ khi PR chủ ý đổi đúng thứ đó.
  - Plan/apply đỏ "Error acquiring the state lock" là tranh lock giữa các run, không phải lỗi code → chờ run kia xong, chạy lại.
  - Apply chạm task def ECS đăng ký revision mới từ template, và Deploy Dev lần sau chép revision ACTIVE mới nhất →
    sau apply, so tên env của revision mới nhất với revision đang chạy; lệch thì sửa trước lần deploy kế.
  - IAM vừa cấp mà apply lỗi → chạy lại lần 2 (eventual consistency).

## 3. Sau deploy — verify live

1. **Revision:** service đã đổi rollout COMPLETED; CIS api và worker cùng image SHA.

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker aa-booking-dev-api aa-crm-dev-api aa-crm-dev-web --profile aa365-admin --region us-west-1 --query "services[].{n:serviceName,td:taskDefinition,r:deployments[0].rolloutState}"
   ```

2. **Health:** `git_sha` = commit vừa merge và `/health/ready` 200 — CIS `api-cis…/health`, Booking
   `api-booking…/booking/health`, Partner `partner-dev…/crm/health` (CRM web `/healthz`), TripPlanner web
   `tripplanner…/api/health` (host đủ: root `.claude/CLAUDE.md` mục LIVE ENDPOINTS + bảng repo của
   `docs/ecosystem-architecture.md`).
3. **Worker:** CIS log worker có `job_worker_started` đủ mọi kind. Booking và CRM chạy worker trong process api.
4. **API:** curl **từng endpoint đã đổi** trên domain thật → 200 + đúng shape (field chính, số dòng > 0 khi phải có dữ liệu).
5. **UI:** trang đã đổi → `aa-ui-verify`.
6. **Infra:** apply `gh workflow run terraform-apply.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main` xanh;
   plan lại không còn thay đổi ngoài dự kiến.
7. **DB (PR có migration, role, grant, RLS, secret DB hoặc task def DB):** DB Migrate `apply` exit 0 với `ran as: <owner>`;
   PR schema dump đã merge; **DB Isolation Probe** xanh (dán tóm tắt pass / pending / fail), đặc biệt
   `rls.enable_only_has_cis_app_policy`, `rls.force_parity.cis_app`, `sessions.master_break_glass_only`. Đổi
   `DATABASE_URL` / task def → bảng Connections của dump: `cis-api` / `cis-worker` là `cis_app`, `db-migrate` là `db_migrator`.
   Kiểm DB qua ECS exec là việc của điều phối: in dòng ngắn có flush hoặc ghi ra S3 (`aa-cis-schema/references/ecs-exec.md`).
8. **LLM (PR đổi prompt/model/route, AA-900):** sau deploy chạy eval theo runbook CIS `docs/llm/eval-runbook.md`
   (DRY RUN rồi `--enqueue`, job `writing_memory_r2` chạy trên worker — chặn deploy khi đang chạy), đọc kết quả bằng
   `scripts/llm_ops/eval_run_report.py`, rồi comment vào PR: id prompt, run ID, verdict, chi phí log được. Verdict `fail`
   → revert PR.

## 4. Đánh Done

Chỉ khi mục 3 pass và từng gạch "Done when" của issue có bằng chứng. Comment vào issue theo mẫu:

```text
Verified live <dd/mm>:
- PR: #<n> (merged <sha>), ECS <service> :<rev>
- <endpoint> → 200, <tóm tắt shape/số dòng>
- UI: <trang> — screenshot đính kèm / link
- Docs: <file/ID catalog đã sửa, hoặc N/A> · Cost: <0 USD / ước tính USD/tháng>
- Ghi chú: <giới hạn còn lại, issue tách ra nếu có>
```

Thiếu bằng chứng nào → để In Review và ghi rõ còn thiếu gì. Linear có thể tự chuyển Done khi merge/deploy dù chỉ có
`Refs` → sau mỗi merge/apply của issue còn mở, `get_issue` kiểm trạng thái, mở lại nếu đóng nhầm.

## 5. Rollback

Deploy hỏng mà circuit breaker ECS không tự lùi → lùi app trước, sửa sau. DB không lùi theo app (migration chỉ tiến).
**Revert PR app có migration đã copy/apply = chỉ revert code**: giữ nguyên file migration (đã copy = bất biến, ADR
0017); nâng readiness ngược lại trong cùng PR revert; bỏ object thì viết file contract mới theo luồng D8.

- CIS api + worker: `docs/ops/runbooks/rollback-cis.md`.
- Booking: `docs/ops/runbooks/rollback-booking.md`. AA-Partner (`aa-crm-dev-api`, `aa-crm-dev-web`) chưa có runbook
  riêng: cùng cơ chế Deploy Dev (chép revision mới nhất, tag = git SHA) → theo các bước của rollback-booking.
- Vercel (CIS admin, portal, Booking admin, TripPlanner): `docs/ops/runbooks/rollback-vercel.md`.
- Lambda TripPlanner: `docs/ops/runbooks/rollback-tp-lambda.md`. Terraform: `docs/ops/runbooks/rollback-terraform.md`.
- Mục lục + playbook sự cố: `docs/ops/README.md`. Sự cố ảnh hưởng người dùng → `docs/ops/incident-response.md`.
