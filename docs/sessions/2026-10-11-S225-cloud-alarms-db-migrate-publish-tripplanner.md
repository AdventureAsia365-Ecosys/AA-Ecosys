# S225 — Cloud session: alarm log-write-failed, workflow DB Migrate, publish idempotent, TripPlanner harness, wave, docs, staff auth, agent role, outbox inquiry, ERD AAA v2, gỡ 7 Lambda (11/10/2026)

**Tác nhân:** Claude Code (cloud session — KHÔNG có AWS/MFA, KHÔNG local/WSL; mọi thay đổi hạ tầng/DB đi qua GitHub workflow)
**ECS sau phiên:** api + worker chạy build của App `08e5654` (Deploy Dev cuối sau App #650 xanh; số revision không đọc được từ cloud — kiểm `aws ecs describe-services`)
**Migration mới đã áp Dev (workflow DB Migrate):** 215, 216, 217, 218 (CIS) + tp-007, tp-008 (TripPlanner)
**Terraform Apply Prod trong phiên:** #82, #83, #86, #88 (lỗi 2 role), #89 (chạy 2 lần, lần 2 xoá xong 2 role — hoàn tất phần gỡ AA-750)
**Queue:** sạch lúc deploy (guard Deploy Dev cho qua)

## Trạng thái đầu phiên
Cloud container không có aws CLI, key trong env bị STS từ chối → không kiểm được STS/ECS/`shared.job` trực tiếp. `/health` 200; 4 repo trên main khớp S224 (App `d537930`); 0 PR mở.

## Quyết định của Nghiệp
- Chốt 10 issue làm được từ cloud.
- **Migration làm qua repo Infra**: Nghiệp duyệt PR → Claude merge → trigger DB Migrate / Terraform Apply Prod và theo dõi; **không đụng local/WSL**. Infra PR chỉ merge sau câu "Duyệt #N".
- AA-726: chưa cần publish WordPress thành công — chỉ note lại → **Done**.
- Việc cloud không làm được: note cho local/WSL (mục "Việc cần kiểm từ local/WSL").
- AA-730: "làm luôn".
- AA-676: outbox đặt trong schema `tripplanner`, AA-Booking đọc qua view — "làm luôn".
- AA-750: gỡ **cả 7** Lambda (kể cả brand-brief-parser + xoá endpoint chết) — "làm luôn"; đồng ý apply từ cloud **không chờ** bước WSL (90 ngày invocations + snapshot code).
- Không ghi log vội — ghi tổng hợp 1 lần khi đóng phiên.

## PR trong phiên (tất cả đã merge, trừ root #44 squash khi đóng phiên)

| Repo | PR | Commit | Issue | Nội dung |
|---|---|---|---|---|
| AA-CIS-Infra | #82 | `512f31f` | AA-756, AA-726, AA-731 | 4 alarm log-write-failed; workflow DB Migrate; SQL 215, 216 |
| AA-CIS-Infra | #83 | `9d85593` | AA-727, AA-684 | SQL 217; probe gọi `/admin/waves/check`; DB Migrate prefix `tp-`/`bk-`; tp-007; xoá `modules/rds/migrations` |
| AA-CIS-Infra | #84 | `a76844e` | AA-654 | README đầy đủ (plan No changes) |
| AA-CIS-Infra | #85 | `376f66f` | AA-656 | SQL 218 |
| AA-CIS-Infra | #86 | `7010740` | AA-730 | role `aa-cis-dev-agent-session` |
| AA-CIS-Infra | #87 | `bc9551e` | AA-676 | SQL tp-008 |
| AA-CIS-Infra | #88 | `06ca893` | AA-750 | gỡ 7 Lambda + Step Functions + SQS + authorizer |
| AA-CIS-Infra | #89 | `3195a7a` | AA-750 | CI role thêm `iam:ListInstanceProfilesForRole`; notes AA-750 |
| AA-CIS-App | #646 | `eda8fc4` | AA-726 | publish idempotent |
| AA-CIS-App | #647 | `4a844be` | AA-727 | `shared.rerun_wave` + `/admin/waves` |
| AA-CIS-App | #648 | `df89241` | AA-654 | README, `.claude/CLAUDE.md` ngắn, CONTEXT contracts |
| AA-CIS-App | #649 | `24ad4a0` | AA-656 | JWT cho mọi role staff, ma trận RBAC |
| AA-CIS-App | #650 | `08e5654` | AA-750 | xoá endpoint brand-brief + job deploy-lambdas |
| AA-TripPlanner-Web | #65 | `beb1fed` | AA-731 | send idempotent, narration grounding, view active atoms, op orphans |
| AA-TripPlanner-Web | #66 | `ee8e3e6` | AA-684 | migration đăng ký `tp-NNN` |
| AA-TripPlanner-Web | #67 | `8366317` | AA-654 | README, CONTEXT contracts |
| AA-TripPlanner-Web | #68 | `5738a2b` | AA-676 | outbox `inquiry.submitted` + consent |
| AA-Ecosys (root) | #43 | `307d1d3` | AA-684, AA-654 | schema-ownership, ADR 0001 qđ 6, README gốc, ecosystem-architecture, handoff |
| AA-Ecosys (root) | #44 | squash khi đóng phiên | AA-677, AA-676 | ERD AAA v2, contract JSON, log S225 |

## Kết quả theo issue

### AA-756 — In Progress (phần alarm xong)
- Infra #82: 4 metric filter + 4 alarm `*_log_write_failed` (llm_call_log, decision_log, llm_shadow_log, dfs_call_log) → SNS `aa-cis-dev-acp-alerts`. Apply **8 added / 0 changed / 0 destroyed**.
- Còn: kiểm tay ~30 quyết định Jev sau ngưỡng v2; đọc số liệu `a1_promise_unsupported` (cần DB/WSL).

### Workflow DB Migrate (hạ tầng chung, Infra #82/#83)
- `.github/workflows/db-migrate.yml` + `db/run_migration.py` + `db/README.md`: chỉ chạy từ main, input `migration=<owner>/NNN_*.sql`, `mode=check|apply`; one-off Fargate task từ task def api (cùng subnet/SG, `DATABASE_URL` của task), SQL qua presigned S3, kiểm sha256, fail nếu version không vào `shared.schema_versions`. Key `NNN` (cis), `tp-NNN` (tripplanner), `bk-NNN` (booking).
- Đã áp: 215 (05:28Z), 216 (05:31Z), 217 (06:10Z), tp-007 (06:13Z), 218 (07:02Z), tp-008 (07:53Z).

### AA-726 — Done
- App #646: `publish_log.idempotency_key` + trạng thái `requested` + unique index (mig 215). Ghi `requested` trước khi gọi WordPress/Facebook; cùng revision đã đăng → replay; đang chạy → 409; thử lại sau mất response → tìm bài trên remote trước (WP theo slug revision, FB theo message).
- Unit 2552 passed, integration Postgres thật 6/6. Chưa publish WordPress thật (Nghiệp: không cần).

### AA-731 — In Progress
- TripPlanner #65 (Deploy Lambdas xanh): Send-to-advisor idempotent (advisory lock + event `sent`, không migration); narration grounding (số bịa → thay bằng tên component); extraction đọc `acp_contract.v_active_tour_atoms` (grant mig 216); op `orphans`. 152 test pass.
- Còn: kiểm live trên Lambda (WSL mục 2).

### AA-727 — In Progress (chờ wave thật)
- App #647: `shared.rerun_wave` (mig 217) + `/admin/waves` — tạo wave (tour_ids hoặc 1 nước), danh sách, đóng; báo cáo 4 cột + trạng thái từng tour + loại lỗi + Jev coverage + chi phí; `/check` → wave thiếu thì 1 chuông. Unit 2561, integration 2/2.
- Infra #83: Lambda probe gọi `/admin/waves/check` hằng ngày.
- Done-when: wave Laos phải **tạo wave trước** khi chạy, rồi so với đếm tay.

### AA-684 — In Progress
- Root #43: `docs/database/schema-ownership.md`, ADR 0001 quyết định 6, steering db-schema.
- Infra #83: xoá `modules/rds/migrations` (9 file cũ); DB Migrate nhận prefix owner.
- TripPlanner #66: `tp-007` đăng ký `tp-001…006` theo đối tượng có thật.
- Còn: Nghiệp xác nhận `shared.destinations` thuộc CIS; WSL mục 4.

### AA-654 — In Progress (docs xong)
- App #648: README viết lại, `.claude/CLAUDE.md` 518 → ~90 dòng (bỏ LIVE STATE), CONTEXT bảng contracts.
- TripPlanner #67: README, CONTEXT contracts, sửa câu cũ "ghi shared.destinations".
- Infra #84: README (plan No changes).
- Root #43: README gốc tiếng Anh; `ecosystem-architecture.md` + `tripplanner-to-aaa-handoff.md` cập nhật (worker, DB Migrate, schema ownership, AA-Booking acc2, alarm, waves, outbox ADR 0001).
- Còn: kiểm sâu README với thực tế (WSL mục 7).

### AA-656 — In Progress (ship + verify live xong, còn bước WSL)
- Infra #85 → mig 218 (`shared.admin_role` thêm `content`). App #649 → Deploy Dev xanh 07:09Z.
- Role `content` đăng nhập bằng JWT thật qua `shared.admin_users` (bỏ login `CONTENT_PASSWORD` không token). Middleware kiểm **role trong JWT đã verify**, không đọc cookie `cis_role` (lỗ cũ: reviewer tự đặt `cis_role=admin` là vào trang admin).
- Ma trận RBAC duy nhất `frontend/lib/rbac.ts` (trang + proxy + menu); mọi BFF proxy verify (401 sai token / 403 sai role); proxy tenant + playground verify JWT tenant. CONTEXT "Staff roles and permissions" (+ ánh xạ role AA-Booking). `scripts/create_staff_user.py` (getpass + bcrypt).
- Test: unit 2568; UI smoke preview 32 passed (10 test cookie giả mới). Live: cookie giả → 307 /login mọi trang, proxy → 401.

### AA-730 — In Progress (apply xong, còn kiểm từ WSL)
- Infra #86 → apply OK: role `aa-cis-dev-agent-session` (`accounts/aa365/agent_session.tf`), trust account root + MFA, 8h. Allow: ECS describe/list + `ExecuteCommand` cluster dev, SSM port-forward qua task, S3 `bronze/scripts/*`, logs/cloudwatch/rds/scheduler/events/apigateway đọc, `lambda:InvokeFunction` (`aa-cis-dev-*`, `aa-tripplanner-dev-*`). Deny tường minh: IAM ghi + `sts:AssumeRole`, đọc config Lambda, RDS delete/modify/stop/start, EC2 stop/start, `ecs:UpdateService/RunTask/StopTask`, autoscaling, secret value, `kms:Decrypt`, tfstate.
- `cicd.tf` `AgentSessionRoleTagging` (iam:TagRole do default_tags). Hướng dẫn `docs/agent-session-role.md` (Infra).
- Còn: tạo profile WSL `aa365-agent` + chạy test Done-when (WSL mục 9).

### AA-676 — In Progress (code + migration xong, chờ verify luồng thật)
- Infra #87 → tp-008 (07:53Z): bảng `tripplanner.outbox` + view `tripplanner.v_inquiry_outbox` (AA-Booking đọc qua view).
- TripPlanner #68: `backend/assembly/handoff.py` (build payload `inquiry.submitted` v1 có legs + customer + consent) ghi outbox **trong cùng transaction** với Send-to-advisor; idempotency key `<trip_id>:<handoff_id>`; checkbox consent ở frontend; test; CONTEXT; notes AA-676.
- Root #44: contract `docs/contracts/inquiry.submitted.v1.json` (JSON Schema); spec bàn giao ghi đã chốt chỗ đặt outbox.

### AA-677 — In Progress (bản nháp, chờ chị Thư / anh Mạnh)
- Root #44: `docs/AAA/erd-v2/booking.dbml` (34 bảng, 13 enum, schema `booking.*` trên acc2, UUID PK) + `README.md`: các quyết định (golden record theo ADR 0002, lineage catalog, multi-tour/multi-country, đóng gap P0/P1 bàn giao, pricing theo mùa/pax band, tách customer/staff, `inbox_events` phía consumer outbox), bảng ánh xạ v1 → v2, **đề xuất trả lời 6 câu hỏi nghiệp vụ (TO CONFIRM)**.

### AA-750 — In Progress (gỡ xong, còn verify sâu)
- App #650 (Deploy Dev xanh): xoá `POST /admin/tenants/{id}/brand-brief` (gọi tên Lambda/bucket acc1 cũ — vốn đã hỏng), `services/acp_brand_brief_parser` + test, `scripts/package_lambdas.sh`, `scripts/install_phase4.sh`, job deploy-lambdas trong `deploy-dev.yml`, bước CI "Audit Lambda requirements". Live: endpoint → 404 (route đối chứng 403).
- Infra #88 → Apply Prod run 38125730946: đã xoá 7 Lambda (ingestion, seo, validation, content, export, authorizer, brand-brief-parser) + log group, Step Functions `aa-cis-dev-pipeline`, 6 SQS + DLQ + alarm DLQ, authorizer API GW + permission, widget dashboard; API GW redeploy. Lỗi duy nhất: không xoá được 2 role rỗng (`aa-cis-dev-lambda-exec`, `aa-cis-dev-sfn-exec`) vì CI role thiếu `iam:ListInstanceProfilesForRole`.
- Infra #89 → thêm quyền đó + cập nhật notes AA-750 → Apply Prod run 38126366515 vẫn lỗi y hệt (race: Terraform xoá role **song song** với lúc sửa `cicd_inline`, quyền mới chưa có hiệu lực); chạy lại run 38126489066 → **Apply complete: 0 added, 0 changed, 2 destroyed** (2 role đã xoá). Live sau apply: `/health` 200, `/admin/tenants` 403, `/v1/` 403 khi không có credential.
- Live sau #88: `/health` 200; `/admin` 403, `/v1` 401 khi không có credential (`/docs`, `/openapi.json` 403 là có từ trước).
- **Lệch quy trình (Nghiệp đồng ý):** KHÔNG chạy kiểm 90 ngày invocations và KHÔNG snapshot code về `scripts/restore/` trước khi apply. Khôi phục được từ git: App trước `08e5654`, Infra trước `06ca893`. Metric CloudWatch còn 15 tháng → kiểm bù được.

## Việc cần kiểm từ local/WSL (cloud không làm được)
1. **AA-726** — `SELECT status, count(*) FROM acp_shared.publish_log GROUP BY 1;` không có `requested` treo > 2 phút. Khi có site WordPress thật: publish 1 piece → 1 bài + dòng `published` có `idempotency_key`; publish lại → `replayed: true`, vẫn 1 bài.
2. **AA-731** — invoke `aa-tripplanner-dev-assembly` `{"extraction": {"op": "orphans"}}` → xem `orphan_components` (dọn bằng `prune {"include_components": true}` nếu > 0). Chạy `{"op": "components", "tour_ids": ["<1 tour>"]}` để chắc role `tripplanner` đọc được `v_active_tour_atoms` qua RLS. Send-to-advisor 2 lần trên preview → 1 email (LoggingSender), 1 event `sent`.
3. **AA-756** — alarm `aa-cis-dev-*-log-write-failed` ở OK/INSUFFICIENT_DATA; email SNS `aa-cis-dev-acp-alerts` đã confirm. Kiểm tay ~30 quyết định Jev sau ngưỡng v2; đọc `a1_promise_unsupported`.
4. **AA-684** — `SELECT version FROM shared.schema_versions WHERE version LIKE 'tp-%' ORDER BY 1;` → mong tp-001…tp-008.
5. **AA-727** — sau lần chạy probe đầu tiên: log Lambda `aa-cis-dev-dfs-balance-check` có `/admin/waves/check` 200. Wave Laos: tạo wave trước khi chạy.
6. **Schema reference** — regenerate `docs/architecture/db-schema-reference.md` cho mig 215 (cột `publish_log`), 217 (`shared.rerun_wave`), 218 (enum `admin_role` có `content`), tp-008 (`tripplanner.outbox`, view `v_inquiry_outbox`).
7. **AA-654** — đối chiếu README mới với thực tế: biến môi trường App/TripPlanner khớp task def ECS / Lambda config / Vercel; lệnh setup/test chạy được local. Đọc lại `.claude/CLAUDE.md` cũ (git `df89241^`) xem có quy tắc còn hiệu lực bị rơi.
8. **AA-656** — (a) `python scripts/create_staff_user.py <tên> content` trong container api (ECS exec), đăng nhập role content → Review Queue có dữ liệu, trang chỉ-admin đẩy về /admin/review; (b) đăng nhập reviewer, sửa cookie `cis_role=admin` → /admin/tenants vẫn đẩy về /admin/review; (c) xoá biến `CONTENT_PASSWORD` trên Vercel. Xong → Done.
9. **AA-730** — thêm `[profile aa365-agent]` vào `~/.aws/config` (role_arn `arn:aws:iam::005097885195:role/aa-cis-dev-agent-session`, cùng source_profile + mfa_serial với `aa365-admin`, 8h). Kiểm: `sts get-caller-identity` ra assumed-role agent-session; `aws iam create-user` và `aws rds delete-db-snapshot` → AccessDenied; `ecs list-tasks` + `s3 ls bronze/scripts/` chạy; 1 script ECS exec end-to-end. Sau đó Kiro/Claude WSL dùng `AWS_PROFILE=aa365-agent`.
10. **AA-676** — gửi 1 trip qua Send-to-advisor (preview/live) rồi: `SELECT idempotency_key, payload->'customer'->>'consent' FROM tripplanner.v_inquiry_outbox ORDER BY id DESC LIMIT 3;` → 1 dòng/lần gửi, consent đúng checkbox; gửi lại cùng trip → không thêm dòng. Validate `payload` với `docs/contracts/inquiry.submitted.v1.json`.
11. **AA-750** — (a) kiểm bù: `aws cloudwatch get-metric-statistics` Invocations 90 ngày cho 7 function = 0; `aws stepfunctions list-executions` không có gì gần; (b) `aws lambda list-functions` chỉ còn `aa-cis-dev-dfs-balance-check` + ops probe + `aa-tripplanner-dev-*`; `aws iam get-role --role-name aa-cis-dev-lambda-exec` (và `aa-cis-dev-sfn-exec`) → NoSuchEntity; (c) S0 upload 1 file + 1 lần S1 rewrite chạy được; đăng nhập admin 200. Xong → Done.
12. **AA-677** — chị Thư / anh Mạnh trả lời 6 câu hỏi trong `docs/AAA/erd-v2/README.md`, rồi chốt ERD v2 trước khi tạo repo AA-Booking.

## Issue còn lại chưa làm được từ cloud
AA-712 (chuyển place pipeline sang CIS — lớn, cần chạy ECS/LLM), AA-670 (cần tài khoản tenant test), AA-729 (cần người gán nhãn), AA-697 (sau rerun), AA-678/679/680/681 (cần repo AA-Booking), các issue Jev/pipeline (cần chạy ECS/LLM).

## Việc đầu phiên S226
1. Chạy các mục WSL ở trên theo thứ tự ưu tiên: 9 (AA-730 → để các mục sau dùng profile agent), 11 (AA-750), 6 (schema reference), 10 (AA-676), 8 (AA-656), rồi 1–5, 7.
2. Đóng issue khi verify xong: AA-750, AA-656, AA-730, AA-676.
3. AA-677: gửi 6 câu hỏi cho chị Thư / anh Mạnh (qua Jira, nháp → Nghiệp duyệt).

## Lưu ý kỹ thuật
- Auto-mode Claude Code chặn lệnh Bash soạn/đọc Terraform IAM ("Permission Grant") kể cả khi Nghiệp đã cho làm; tool Write/Edit thì được.
- Xoá IAM role qua Terraform cần `iam:ListInstanceProfilesForRole` (DeleteRole gọi trước) — CI role đã có từ #89. Thêm quyền cho CI role cùng lúc với thao tác cần quyền đó → apply đầu thường lỗi vì 2 việc chạy song song; chạy lại apply là xong (hoặc tách 2 PR).
- Branch phiên trên remote còn commit đã squash-merge → `git push --force-with-lease=<branch>:<sha remote>` khi bắt đầu việc mới trên cùng branch.
- Mỗi repo chỉ 1 branch phiên → mỗi repo 1 PR một lúc; gộp việc Infra vào 1 PR để Nghiệp duyệt một lần.
- `gh` trong cloud: GraphQL bị chặn (dùng `gh api` REST; draft → ready qua MCP `update_pull_request`); tải log run bị 403 → đọc log job qua MCP `get_job_logs`.
- Registry Terraform bị chặn trong container → `terraform validate` chỉ chạy ở CI plan.
- Lint App CI: `flake8 api/ services/ shared/` max 120 — sửa docstring dễ vượt dòng.
