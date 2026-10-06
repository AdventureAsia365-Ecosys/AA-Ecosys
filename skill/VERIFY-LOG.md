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

## Câu hỏi cần Nghiệp quyết

1. **Mr. Manh / QuanSolution** còn liên quan AA không? Nếu có, thêm vào `stakeholders-english.md`; nếu không, giữ nguyên 3 người.
2. Kích thước cuối 56.1 KB — nhỉnh hơn mục tiêu ~55 KB khoảng 1 KB. Chấp nhận, hay cần cắt thêm (ứng viên: gộp bớt reference `aa-ecosys-repos`)?
3. dead-table-registry.md đặt ở root AA-Ecosys (không phải AA-CIS-App) — xác nhận hướng này đúng (nhất quán với db-schema-reference).
