# VERIFY-LOG — AA-733 skill restructure (S215, 06/10/2026, Kiro)

Mọi mốc `VERIFY` / `SINH LẠI` trong `skill-draft/` đã được giải quyết bằng code/AWS/DB thật, rồi xoá
comment mốc. Kích thước cuối: 9 skill = 56.1 KB (cũ 114 KB); mỗi `SKILL.md` ≤ 90 dòng.

## Bảng mốc đã giải quyết

| Mốc | File | Kết luận | Bằng chứng |
|---|---|---|---|
| toàn file aws | ai-nghiep/references/aws.md | 2 ECS service (api + worker), domain đúng, start/stop chỉ scale api | `aws ecs list-services` → api+worker; `~/.zshrc` cis-start/stop |
| task in-process ngoài AA-723 | aws.md | Không còn — mọi bg task qua `shared.job` | `services/jobs/*_job.py` có s1_rewrite/revalidate/recompute |
| Step Functions còn dùng? | aws.md | State machine `aa-cis-dev-pipeline` còn tồn tại nhưng pipeline KHÔNG gọi (AA-182/AA-311) → xoá khỏi skill | `test_aa311_no_step_functions_call.py`; `aws stepfunctions list-state-machines` |
| cis-stop scale worker? | aws.md | KHÔNG — alias chỉ scale `aa-cis-dev-api`, worker giữ nguyên | đọc `~/.zshrc` cis-start/cis-stop |
| writer model route | aws.md | Đọc route thật `shared.llm_role_config`, không ghi số vào skill | CONTEXT.md Stage Route |
| mô tả atom/segment khớp CONTEXT | ai-nghiep/SKILL.md | Atom/Segment/Score/Route/Hub platform-wide (không per-tenant) | CONTEXT.md (AA-545/AA-526) |
| luật deploy/merge khi job chạy | ai-nghiep/SKILL.md | Đã thành CI check (AA-725 pre-deploy guard + smoke) → chuyển thành ghi chú | PR #574 merged phiên này |
| ADR quy ước + đánh số | ai-nghiep/references/adr.md | 2 cấp repo (root 0001-0003 + AA-CIS-App 0001-0007), số trùng nhau, đếm độc lập | `ls docs/adr/` cả 2 repo |
| danh sách người | stakeholders-english.md | Giữ chị Thư/Leigh/Trang; Mr.Manh/QuanSolution không verify được → câu hỏi mở | — |
| path db-schema-reference | aa-cis-schema/SKILL.md | Ở **repo gốc AA-Ecosys** `docs/architecture/`, KHÔNG trong AA-CIS-App (draft sai) | `find db-schema-reference.md`; steering db-schema.md |
| runner `.tmp-session/` | aa-cis-schema/SKILL.md | Mỗi phiên runner tạm `sNNN_run.sh`, tái dùng/viết mới | pattern dùng phiên này |
| bối cảnh dữ liệu | aa-cis-schema/SKILL.md | Khớp schema ref (atom view, job shared.job, ADR 0002) | db-schema-reference.md |
| ecs-exec runner + script | ecs-exec.md | Giữ bản secretsmanager-trực-tiếp (độc lập app); nêu thêm lựa chọn get_database_url | chạy ECS exec thật phiên này |
| log group worker + Lambda | ecs-exec.md | 1 log group chung `/ecs/aa-cis-dev`; 8 Lambda sống | `aws logs describe-log-groups`, `aws lambda list-functions` |
| score_distinctiveness | gotchas.md | Chưa có; distinctiveness/weight vẫn default chết | `grep score_distinctiveness db-schema-reference.md` = 0 |
| AA-Booking repo tồn tại? | aa-ecosys-repos/SKILL.md + booking.md | CHƯA (local + GitHub đều không có) — đang bootstrap | `ls apps/AA-Booking`, `gh repo view` = not found |
| pipeline khớp CONTEXT/ADR | aa-ecosys-repos/SKILL.md | Khớp; bỏ marker | CONTEXT.md |
| auth | aa-ecosys-repos/SKILL.md | admin x-admin-secret (verify_admin_secret); tenant JWT (_create_jwt/verify_jwt) | api/main.py, api/routers/admin.py |
| path job kind | aa-ecosys-repos/SKILL.md | `services/jobs/*_job.py`, decorator `@job_kind` | `grep @job_kind services/jobs` |
| SINH LẠI cis-app.md | cis-app.md | Sinh router prefix + trang admin/portal + 10 job kind từ repo | grep APIRouter / find page.tsx / @job_kind |
| SINH LẠI pipeline.md | pipeline.md | Điền code chính mỗi stage; Segment platform-wide | ls services/*; CONTEXT.md |
| Infra tf + workflow | infra.md | accounts/aa365 + acc1/acc3-bedrock; terraform-plan/apply.yml | `ls accounts/`, `ls .github/workflows` |
| TripPlanner 2 Lambda | tripplanner.md | browse/handler.py + assembly/handler.py + extraction (offline) | `find backend -name handler.py` |
| accountId chị Thư + mention | aa-jira-update/SKILL.md | `70121:5793bdd5-44b1-4623-97d4-43c35d440869`, html mention node | steering + comment PR-15 đăng phiên này |
| project Linear active | aa-linear-issue/SKILL.md | 6 project chính khớp; thêm luật ≤50 issue/project | list_issues phiên này |
| 5 job CI | aa-ship/SKILL.md | Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check | ci.yml |
| frontend/AGENTS.md | aa-ui-verify/SKILL.md | Tồn tại (Next.js breaking-changes guide) | `head frontend/AGENTS.md` |
| cột/bảng wave | aa-wave-rerun/SKILL.md | Trỏ db-schema-reference, không ghi cứng | nguyên tắc aa-cis-schema |

## Nội dung mới (ngoài scope draft, thêm trong phiên)

- Tạo `AA-Ecosys/docs/architecture/dead-table-registry.md` (21 bảng DROP 27/08, migration 121+122) — chuyển từ skill `aa-cis-schema` cũ, đặt ở **root AA-Ecosys** cạnh db-schema-reference (không phải AA-CIS-App như MIGRATION-PROMPT ghi, vì db-schema-reference cũng ở root). `aa-cis-schema/SKILL.md` đã trỏ tới path này.

## Đã sửa so với draft (draft sai thực tế)

- Draft trỏ `db-schema-reference.md` + dead-table-registry "trong AA-CIS-App" → thực tế ở **repo gốc AA-Ecosys**.
- Draft ADR dùng số `ADR-2026-NNN` → thực tế `NNNN` 4 chữ số, 2 cấp repo, số trùng nhau.
- Draft "S1 rewrite/revalidate/recompute đang chuyển (AA-723)" → đã Done, có job kind thật.

## Câu hỏi đã được Nghiệp quyết (06/10/2026)

1. **Mr. Manh / QuanSolution** — KHÔNG còn liên quan AA. Giữ nguyên 3 người (chị Thư/Leigh/Trang) trong `stakeholders-english.md`.
2. Kích thước 56.1 KB (so với mục tiêu ~55 KB) — **chấp nhận**, không cắt thêm.
3. dead-table-registry.md đặt ở **root AA-Ecosys** (cạnh db-schema-reference) — **xác nhận đúng**.

---

# S251 (25/10/2026, Claude Code) — rà soát toàn bộ trước khi upload sang tài khoản claude.ai mới

Từng skill do một agent rà (đối chiếu path/route/bảng/workflow với `origin/main` các repo, `db-schema-reference.md` dump
25/10, GitHub API, Linear/Jira live), rồi một lượt chéo giữa các skill. Các dòng S215 ở trên là lịch sử; khi lệch, mục
này thắng (ví dụ "5 job CI" → required check theo từng repo; "6 project Linear, ≤50 issue" → 5 project, ~100 issue).

Kích thước: 10 `SKILL.md` 75–149 dòng; cả bộ 218 KB, trong đó `aa-lessons/lessons.md` 84 KB → phần còn lại 134 KB
(origin/master trước phiên: 176 KB / 89 KB). Không file `references/` mồ côi; không marker VERIFY/ADDITIONS.

## Sửa chính theo skill

| Skill | Sửa | Bằng chứng |
|---|---|---|
| aa-session | 5 service ECS (thêm `aa-crm-dev-api`/`-web`), bảng job thêm `crm.job`, health Booking/CRM/CRM web, TripPlanner web `/api/health` (Lambda không có health), repo gốc + 5 con, Linear export dry run trước `--apply`, đọc `plan.json`, cỡ phiên 3–5 / 8–10 | root `.claude/CLAUDE.md` RESOURCES; Partner `api/tests/unit/test_health.py`, `web/app/healthz/route.ts`; curl `tripplanner…/api/health` 200 có `git_sha` (25/10); argparse `tools/linear/linear_export.py` |
| aa-ship | Required check đọc bằng `gh pr checks --required` (CIS/Partner 8, Booking 7, TP 5, Infra/root 0); deploy gate 3 app; auto-merge chỉ CIS/Booking/TP; release-please 4 repo; Terraform plan guard + state lock + template revision; bỏ luật COPY Dockerfile (đã là test) | branch protection API; `deploy-dev.yml` từng repo; `allow_auto_merge`; `terraform-apply.yml`; `test_aa725_dockerfile_copy.py` |
| aa-ui-verify | Smoke qua `workflow_call` (Vercel Git tắt), `alias_only_url`, CRM web, portal ở AA-Partner, user E2E ghim `cis-reviewer` | `vercel-deploy.yml`, `ui-smoke.yml`, `check_vendored_copies.py` |
| aa-cis-schema (+ refs) | Schema `crm` / `crm_owner`, `cis_app` đọc được vài view `booking.v_ops_*`/`v_supply_*`/`tripplanner.v_ops_traffic_daily`, ECS exec chỉ điều phối, gotcha `acp_v2_*` sai → bỏ, `distinctiveness` đã DROP (CIS 208), Lambda còn lại sau AA-750, quarantine DM-3.8/3.9 | grant trong reference; `db/owners.yaml`; `subagent-guardrails.sh`; `208_drop_distinctiveness_competitors.sql`; `accounts/aa365/*.tf` |
| aa-wave-rerun | Wave object `/admin/waves` (AA-727 Done), `a3_atomize` concurrency 1, thang 3 → ≤50 → theo nước, snapshot mỗi wave, báo cáo chi phí | `admin_waves.py`, `services/waves/report.py`, `a3_atomize_job.py` |
| aa-ecosys-repos (+ refs) | AA-Partner (api/web/portal), mọi repo public, bảng job theo app, auth WORKFORCE + M2M, router/page/kind sinh lại, role CI theo việc | GitHub API visibility; Partner `CONTEXT.md`; `staff_identity.py`, `m2m_auth.py`; `cicd_split.tf` |
| aa-lessons | Bảng mục → khi nào đọc; bài học chờ trong `.tmp-session` rồi chuyển cuối phiên; gộp dòng trùng; xoá 10 dòng đã có guard | tên guard trong change list S251 |
| aa-linear-issue | 5 project (thêm Partner CRM, Data Platform), comment Linear tiếng Anh, hỏi trước khi tạo, cờ export/archive thật, `pr-title` chỉ ở Booking/Partner/TP | `list_projects` 25/10; steering language; `tools/linear/README.md` |
| aa-jira-update | Epic PR-20, PR-22…27; không tự tạo issue/đổi trạng thái; nơi lưu nháp `docs/audits/…/jira-drafts.md`; ảnh nhúng 2 pha | JQL `issuetype = Epic` 25/10; `getJiraUser` @thule active |
| ai-nghiep (+ refs) | Booking live + AA-Partner; luật cứng 9–10 (không bật/tắt hạ tầng; Terraform/migration chỉ qua workflow); quyền điều phối vs subagent; format ADR thật; commit không mã issue ở subject | AA-678/AA-725 Done (linear-export); hook; header ADR root 0011/0014 |

## Lượt chéo (cross-skill)

- Tên service ECS, profile (`aa365-admin` mọi lệnh), bảng job (`shared.job` / `booking.job` / `crm.job`), `Refs AA-xxx`
  (không `[AA-xxx]`/`Fixes`/`Closes`, không mã issue trong tiêu đề), luật merge (điều phối tự merge giai đoạn dev,
  subagent bị hook chặn): khớp giữa các skill sau khi sửa.
- Prefix branch thống nhất `feat|fix|chore|docs/aa-xxx-…` (aa-ship, aa-ecosys-repos, handoff-prompt) — khớp tên
  branch thật của PR CIS gần đây (`feat/` chiếm đa số).
- Host health: aa-ship và `aws.md` trỏ thêm bảng repo của `docs/ecosystem-architecture.md` (root `.claude/CLAUDE.md`
  chưa có host AA-Partner/TripPlanner). Curl 25/10: `partner-dev…/crm/health` 200, `/healthz` 200, TripPlanner
  `/api/health` 200.
- Trigger: thu hẹp `aa-ecosys-repos` (không còn bắt "admin/portal/CRM" chung chung; loại trừ aa-ui-verify), `ai-nghiep`
  (Zalo/email; Jira thuộc aa-jira-update), thêm "schema drift / ERD drift" vào `aa-cis-schema`. Thử 9 câu của
  `REVIEW-CHECKLIST.md`: mỗi câu một skill chính (`aa-lessons` chỉ đi kèm khi sửa code).
- DBeaver db `aa_cis_dev`: khớp default `modules/rds/variables.tf` (không root nào ghi đè).
- Lint cục bộ: `check_docs_text.py aws-multiline` 0 lỗi; `resource-ids` 0 cảnh báo trong `skill/`; unit test
  `tools/docs` 30 OK. markdownlint/lychee của Docs lint chỉ quét `docs/**`, không quét `skill/`. Không có gitleaks local
  (CI `secret-scan.yml` chạy trên PR); grep mẫu secret/DSN/key trong `skill/` = 0.

## Câu hỏi mở cho Nghiệp

1. **Kích thước:** phần không tính `lessons.md` tăng từ 89 KB lên 134 KB (tiếng Việt có dấu ~1,3 byte/ký tự). Giữ, hay
   cắt bớt `aa-session` / `aa-ship` / `aa-ui-verify` (các skill lớn nhất)?
2. **Steering lệch skill** (ngoài `skill/`, chưa sửa): `.kiro/steering/session-workflow.md` còn "gốc + 4 con", "5 CI
   job", "đề xuất 5–10 issue", chỉ `shared.job`/`booking.job`; `.kiro/steering/db-schema.md` còn "3 app", thiếu `crm`.
   Steering nói "khi lệch, skill thắng" nhưng nên sửa trong root PR.
3. **Tour cưỡi voi:** memory `elephant-riding-policy` (giữ trong tập, chờ người duyệt) vs memo AA-645 §6 (bỏ khỏi
   `expected_set`). Skill theo memory.
4. **Account ID trong repo public:** `ai-nghiep/references/aws.md` và `ecs-exec.md` ghi account ID + tên bucket; accountId
   Atlassian của chị Thư ở `aa-jira-update`. Giữ (cần cho lệnh/mention) hay tra mỗi lần?
5. **Jira:** mở đầu "@thule Cập nhật …" (skill) vs "@thule Dạ chị," (memory `jira-draft-tone`); luật 7 (không chi phí
   nội bộ chi tiết) vs nháp PR-22 S250 có cột chi phí theo nước; `docs/backlog/jira-map.md` mà memory nhắc không tồn tại.
6. **Underscore env var:** bài học được viết lại theo memory `do-hand-steps-myself` (đặt bằng script/pipe, không chép tên
   từ chat đã render), khác câu trong CLAUDE.md toàn cục ("edit manually in VSCode").
7. **Thiếu ngoài skill:** runbook rollback AA-Partner; dòng Partner trong `deploy-gate-override.md` và bảng deploy của
   `docs/ops/README.md`; `docs/ops/runbooks/preview-staff-sign-in.md` mà `vercel-deploy.yml` (CIS) trỏ tới không tồn tại.
8. **Tracker artifact** `2VSP2stG…` thuộc tài khoản claude.ai cũ: publish từ `info@adventure.asia` có thể bị từ chối →
   trang mới + sửa link trong `docs/backlog/tracker/README.md`.
