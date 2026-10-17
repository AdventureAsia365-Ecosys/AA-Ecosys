# S241: Đánh giá SDLC/ADLC: repo, GitHub org, môi trường, CI/CD, API, vận hành

- **Ngày:** 17/10/2026 (S241). **Bản sửa 2** sau 2 vòng phản biện (xem §9).
- **Tác nhân:** Claude Code (workflow 6 lĩnh vực chạy song song, 1 bước tổng hợp, 2 phản biện, 1 bước sửa).
- **Phạm vi:** org `AdventureAsia365-Ecosys` (AA-CIS-App, AA-Booking, AA-TripPlanner-Web, AA-CIS-Infra, root AA-Ecosys), AWS acc2 `005097885195` (us-west-1), 3 project Vercel, quy trình agent (Claude Code, Kiro).
- **Cách làm:** chỉ đọc. Dùng `gh api` (GET), `aws describe/list/get` (profile `aa365-admin`) và đọc file. Không thay đổi gì trên GitHub, AWS, Vercel hay Linear. Không in giá trị secret, chỉ in tên và metadata.
- **Phân biệt:** **[QS]** là quan sát trực tiếp (kèm file:line, trường API hoặc lệnh). **[SL]** là suy luận.
- **Báo cáo gốc theo lĩnh vực** (tiếng Anh, đủ bằng chứng) nằm trong [`areas/`](areas/). §8.3 liệt kê mâu thuẫn giữa các báo cáo lĩnh vực đã tự kiểm lại. §8.4 là phụ lục lệnh một dòng.

---

## 1. Tóm tắt

**Phạm vi đánh giá:** acc2 "Dev" là **hệ thống lưu PII thật của khách** (`booking.customers`, CRM, tenant thật qua Jira). Với questionnaire của khách B2B, môi trường đang giữ dữ liệu khách chính là môi trường production, dù tên là Dev. Báo cáo này ưu tiên theo nguyên tắc đó, không theo câu "để khi có prod".

Nền móng kỹ thuật **tốt hơn mức thường gặp ở team 1 người**:
- CI dùng OIDC, không có AWS key tĩnh trong CI (nhưng trust hiện quá rộng, xem P0-1; máy dev vẫn có key tĩnh, xem P0-3);
- pipeline Booking đạt chuẩn tham chiếu;
- có deploy-gate theo job và migration guard;
- Definition of Done dựa trên bằng chứng live;
- có ADR và data-standards.

**Lớp quản trị lại gần như chỉ là quy ước, chưa được cưỡng chế.** Cụ thể:
- Một nhánh bất kỳ có thể chạy `terraform apply` với role gần admin trên acc2, vì environment `prod` của Infra không có rule nào.
- Agent AI chạy bằng quyền admin của Nghiệp và tự merge, không có review được ghi nhận (0/951 PR).
- Cô lập tenant **fail-open**: mất cờ Redis là route `/v1` quay về pool BYPASSRLS, trong khi Redis không có AUTH/TLS.
- Runtime CIS đọc được PII của Booking/CRM; 3 service dùng chung 1 security group.
- Có đường sửa dữ liệu không review, không log (ECS exec chạy script với user master).
- Lỗi production không ai thấy: Sentry tắt, CIS API không có alarm 5xx. Backup chưa từng thử khôi phục.

Mức hiện tại khoảng **1,5/4** so với chuẩn (NIST SSDF, OpenSSF Scorecard, OWASP API/LLM, DORA).

**Chia P0 làm hai:**
- **P0-A, làm ngay** (khoảng 3–4 ngày công, **0 USD**): những gì đang hở hôm nay và đóng được bằng thay đổi XS–S.
- **P0-B, trước tenant trả tiền đầu tiên** (khoảng 15–20 ngày công): cô lập tenant, tách quyền DB, biên API, khôi phục/rollback, đường truy cập dữ liệu, hồ sơ pháp lý. Có nhiều việc cỡ M.

**Chi phí tăng thêm** đến hết P1: khoảng **35–55 USD/tháng** (phương án GitHub A hoặc C), hoặc **70–90 USD/tháng** (phương án B, Enterprise). Chi tiết ở §6.

**5 việc quan trọng nhất:**
1. **Đóng đường "nhánh bất kỳ → quyền admin AWS"** (P0-1): branch policy `main` cho env CIS, `if: github.ref == 'refs/heads/main'` cho terraform-apply, thêm điều kiện IAM `token.actions.githubusercontent.com:ref` vào trust các role apply/migrate/deploy. Làm được trên gói Free.
2. **Revoke token GitHub đã lộ ngay** (P0-2). Mật khẩu RDS master xoay theo đúng thứ tự (xoay tay → AA-817 X1 → RDS-managed), xem P0-9.
3. **Thu hẹp quyền agent** (P0-3): agent dùng `aa365-agent`, các lệnh nguy hiểm sang `ask`/`deny`, chặn agent đọc `~/.aws/**`. Sau đó (P1-1) là danh tính GitHub App cho agent, rồi mới đến ruleset theo tầng rủi ro.
4. **Cô lập tenant và dữ liệu** (P0-8, P0-9): cờ RLS mặc định bật trong code, Redis có AUTH/TLS, runtime CIS không đọc được PII Booking/CRM, SG riêng cho từng app.
5. **Thấy được lỗi và khôi phục được** (P0-6, P0-11): Sentry, alarm 5xx CIS, uptime check, diễn tập PITR (AA-829), ECR immutable và rollback bằng task-def revision trước.

---

## 2. Bảng điểm hiện trạng

Thang điểm:
- 0: không có;
- 1: làm tự phát, phụ thuộc quy ước;
- 2: có công cụ nhưng chưa cưỡng chế hoặc chưa đều giữa các repo;
- 3: cưỡng chế được và đo được;
- 4: tự động hoá và cải tiến liên tục.

| Lĩnh vực | Điểm | Bằng chứng ngắn |
|---|---|---|
| GitHub org & repo governance | **1** | Org `plan=free`, `two_factor_requirement_enabled=false`. Root `master` không được bảo vệ. Infra trả 403 khi đọc protection ("Upgrade to GitHub Pro"). Trên các repo app: `required_pull_request_reviews=null`, `enforce_admins=false`. Secret scanning và push protection `disabled` trên 4 repo public và repo archived public `AA-ACP-App`. Dependabot alerts tắt trên Infra (403). Không có CODEOWNERS, SECURITY.md hay dependabot.yml. |
| CI/CD & phát hành | **2** | Điểm cộng: OIDC tách role theo job, Booking dùng tag ECR immutable, deploy-gate fail-closed, circuit breaker, smoke kiểm SHA. Điểm trừ: CIS `pip-audit … \|\| true` (ci.yml:51), Trivy `exit-code: 0`, deploy-dev CIS không có `concurrency`, ECR CIS MUTABLE, chỉ giữ 10 image. Không có rollback, provenance, tag hay release. |
| Môi trường, secret, IAM, mạng, DR | **1,5** | Điểm cộng: permission boundary và OIDC subject bất biến. Điểm trừ: env `prod` của Infra trống rule nhưng role tf-apply có RDS/SecretsManager/ECS/VPC/S3/Lambda FullAccess (cicd.tf:22-32). 27 secret `RotationEnabled=None`. Credential đã lộ chưa xoay (S240). Redis `AuthTokenEnabled=false`, `TransitEncryptionEnabled=false`. 3 ECS service chung SG `sg-038383acb15660582`, cũng là nguồn ingress duy nhất của SG RDS và Redis. ECS Exec bật trên cả 3 service, cluster `configuration=null` (không log phiên). CloudTrail single-region, không KMS, bucket không versioning. Không có GuardDuty (`list-detectors` trả `[]`). acc2 thuộc org có management account bên thứ ba `033086823579`. Chưa từng diễn tập restore. |
| Quản lý API | **1,5** | Điểm cộng: Booking dùng RS256, JWKS và ma trận quyền; contract sự kiện có version. Điểm trừ: RBAC staff của CIS chỉ có ở BFF (`rbac.ts:117-121` mặc định cho phép). Cô lập tenant fail-open (`aa544_tenant_pool.py:146-158`). WAF không gắn vào API GW. CIS stage throttle `-1`. Frontend CIS và TripPlanner không gửi CSP/X-Frame-Options/nosniff/Referrer-Policy. 11/258 route có `response_model`. |
| Chất lượng, quan sát, vận hành | **1,5** | Điểm cộng: khoảng 4,3k unit test và 440 integration test cho CIS; Booking coverage 90%; 47 alarm. Điểm trừ: secret Sentry DSN không tồn tại nên Sentry tắt. CIS API không có alarm 5xx. SNS chỉ gửi email. Log dạng text, giữ 14 ngày. Không có quy trình sự cố. UI smoke chỉ chạy 1/100 lần. |
| ADLC (cách dùng agent AI) | **1,5** | Điểm cộng: skills, lessons log, DoD và hook guardrail cho subagent. Điểm trừ: agent dùng role `nghiep-admin-8h-session`, tự merge, không có review được ghi nhận. `~/.aws/credentials` có 5 profile key tĩnh và `~/.aws/cli/cache` có 11 phiên STS, agent đọc được. Hook chỉ áp cho subagent và dựa trên deny-list. Eval regression chạy lần cuối 01/08. |

---

## 3. Điểm mạnh nên giữ

1. **Không có AWS key tĩnh trong CI.** OIDC tách theo repo và job, trust gắn với ID repo bất biến (`cicd_split.tf:40-50`). Role plan dùng ReadOnly, role apply tách riêng, có permission boundary (`aa-workload-boundary`, DenyIamWrites…). Phạm vi trust hiện quá rộng (P0-1). Máy dev vẫn còn key tĩnh (P0-3).
2. **Pipeline AA-Booking là mẫu chuẩn** để nhân rộng:
   - tag ECR immutable;
   - `git_sha` được bake vào image và smoke kiểm lại;
   - deploy-gate xác thực bằng OIDC, fail-closed, có unit test;
   - có `concurrency`;
   - `pip-audit` chặn build;
   - gitleaks quét toàn bộ lịch sử;
   - coverage tối thiểu 90%;
   - integration test fail khi có test bị skip;
   - frontend có security header (`AA-Booking/frontend/next.config.ts:10`).
3. **An toàn migration vượt mức team nhỏ:**
   - copy-guard kiểm byte-identical;
   - lint CONCURRENTLY và các lệnh phá huỷ;
   - lock/statement timeout;
   - tự snapshot RDS trước migration phá huỷ;
   - kiểm idle `shared.job`;
   - sinh lại `db-schema-reference.md`.
4. **Deploy an toàn:** có guard job trước deploy, smoke JSON shape sau deploy, kiểm api và worker cùng SHA, circuit breaker rollback trên cả 3 ECS service.
5. **Definition of Done dựa trên bằng chứng live** (`skill/aa-ship`), lessons log chuyển thành CI guard, implementation notes (417 ở CIS), ADR có index và quy ước amendment, data-standards v1.0 (PII class, RPO/RTO, retention).
6. **Quản trị LLM trong sản phẩm:**
   - một gateway duy nhất, có test cưỡng chế (`test_aa685_no_raw_model_calls.py`);
   - `llm_role_config` có audit và shadow;
   - ledger chi phí `llm_call_log`;
   - TripPlanner có trần chi tiêu theo ngày.
7. **Contract giữa các app** (docs/contracts) có version. Bản copy giống từng byte và được pin hash trong test.
8. **Tốc độ:** CI p50 khoảng 2,7 phút, deploy 1–6 phút, merge lên Dev khoảng 10 phút. Throughput thuộc nhóm "elite" theo DORA (trên Dev). Mọi đề xuất dưới đây đều cố **giữ tốc độ này**: không thêm cú bấm tay cho PR rủi ro thấp.

---

## 4. Khoảng trống theo ưu tiên

- **P0-A:** đang hở hôm nay, rẻ, làm ngay (tuần này).
- **P0-B:** phải xong **trước khi ký tenant trả tiền đầu tiên**.
- **P1:** trong 90 ngày, giới hạn ở những việc giảm rủi ro thật.
- **P2:** có điều kiện kích hoạt (first prod, contributor thứ hai, tenant tích hợp API, bật thanh toán…).

Công sức: XS dưới nửa ngày; S 1–2 ngày; M 3–5 ngày; L trên 1 tuần (1 người cộng agent).

### P0-A (làm ngay, khoảng 3–4 ngày công, 0 USD)

#### P0-1. Bất kỳ nhánh nào cũng có thể assume role deploy/tf-apply (đường ngắn nhất tới quyền admin acc2)

**Bằng chứng [QS]:**
- `gh api repos/.../AA-CIS-Infra/environments`: `prod` có `protection_rules=0`, `deployment_branch_policy=null`, `can_admins_bypass=true`. Các env `dev` và `staging` cũng vậy.
- Trust của role `aa-cis-infra-tf-apply` là `…:environment:prod` (`accounts/aa365/cicd_split.tf:515-519`). Comment ở dòng 515-517 ghi rằng "main only" dựa vào branch rule **và required reviewer** của environment, nhưng cả hai đều không tồn tại (và required reviewer không dùng được trên repo private ở gói Free/Team, xem P1-1).
- `terraform-apply.yml` (Infra `a6605ce` = `origin/main`): `workflow_dispatch` (dòng 4), `environment: prod` (dòng 18), `-auto-approve` (dòng 77-78), không kiểm `github.ref`.
- Grant set của role apply gồm `AmazonRDSFullAccess`, `SecretsManagerReadWrite`, `AmazonECS_FullAccess`, `AmazonVPCFullAccess`, `AmazonS3FullAccess`, `AWSLambda_FullAccess`… (`cicd.tf:22-32`).
- AA-CIS-App env `dev`: rule 0, branch policy `null`. Role deploy trust `environment:dev` (`cicd_split.tf:311-317`).
- Secret cấp repo (không scope env) trên AA-CIS-App: `ADMIN_SECRET`, `E2E_ADMIN_USERNAME`, `E2E_ADMIN_PASSWORD`, `VERCEL_AUTOMATION_BYPASS_SECRET`, `VERCEL_TOKEN`, `VERCEL_DEPLOY_HOOK`, `ACPCORE_READ_TOKEN` (`gh api …/actions/secrets`). Env `dev` chỉ có `AWS_ROLE_ARN`. `ADMIN_SECRET` chỉ được dùng trong `deploy-dev.yml`.
- `VERCEL_TOKEN` dùng cho **cả preview lẫn production** trong cùng một job (`vercel-deploy.yml:59-132` trên remote 3 repo FE), vì Git integration của Vercel đã tắt để tránh trần khoảng 100 deployment/ngày của Hobby (`vercel-deploy.yml:3-7`).
- Lịch sử: CIS Deploy Dev đã chạy thành công từ nhánh `pqnghiep1354/aa-519-…` (03/09). DB Migrate dùng cùng env `prod` nhưng có `if:` main.

**Rủi ro:** người, agent, token bị đánh cắp hoặc một GitHub App có quyền `contents/workflows: write` (vercel, linear-code, claude) có thể push một nhánh có workflow sửa đổi, rồi dispatch để có quyền gần admin trên acc2, hoặc đọc `ADMIN_SECRET` (god-key, giả được mọi role qua `x-admin-role`, `admin.py:119-124`). acc2 chứa PII thật của cả 3 app.

**Chuẩn:** NIST SSDF PO.5/PS.1; SLSA Build L2–L3; OpenSSF Scorecard Dangerous-Workflow/Branch-Protection; CIS GitHub Benchmark 1.1/1.4.

**Đề xuất (làm được trên gói Free):**
1. AA-CIS-App env `dev` và `prod`: "Selected branches: main" (copy cấu hình env `dev` của Booking). Lệnh ở §8.4. Không đặt required reviewer cho `dev` (129 deploy/tuần).
2. Thêm `if: github.ref == 'refs/heads/main'` cho job apply trong `terraform-apply.yml`.
3. Trust IAM: thêm `StringEquals "token.actions.githubusercontent.com:ref" = "refs/heads/main"` (và tuỳ chọn `StringLike …:job_workflow_ref = AdventureAsia365-Ecosys/AA-CIS-Infra/.github/workflows/terraform-apply.yml@refs/heads/main`) vào role tf-apply, db-migrate và deploy CIS. AWS IAM có tài liệu cho các key này (mục "Available keys for AWS OIDC federation", tab GitHub, liệt kê `ref`, `job_workflow_ref`, `environment`, `repository_id`…). Cách này **không đổi template `sub`**, nên không có rủi ro tự khoá role. Thứ tự an toàn: thử trên một role nháp trước (dispatch từ nhánh khác main phải bị `AccessDenied`), sau đó apply từ main (run trên main thoả điều kiện mới). Nếu thử thất bại, dùng phương án dự phòng: bỏ `environment: prod` khỏi job apply và trust `${local.oidc_sub_cis_infra}:ref:refs/heads/main`.
4. Chuyển `ADMIN_SECRET` vào env `dev` (main-only) của AA-CIS-App, sau đó xoay `ADMIN_SECRET`.
5. Sửa comment `cicd_split.tf:515-517` cho đúng sự thật.
6. **Rủi ro chấp nhận có ghi lại:** `E2E_ADMIN_*` và `VERCEL_AUTOMATION_BYPASS_SECRET` phải ở mức repo, vì UI smoke chạy trên preview của mọi PR (`ui-smoke.yml:5-7, 36-38`). `VERCEL_TOKEN` cũng vậy chừng nào preview còn deploy bằng token. Biện pháp bù ở P1-2 (tài khoản E2E chỉ đọc) và P0-13 (khi lên Vercel Pro, bật lại Git integration cho preview, token chỉ còn ở env production main-only).

**Công sức:** S. **Tự động hoá:** có (Terraform cộng `gh api`; thao tác settings do Nghiệp chạy).

#### P0-2. Token GitHub đã lộ vẫn còn hiệu lực

**Bằng chứng [QS]:** `docs/sessions/2026-10-16-S240-rds-alarm-…md:37`: "Token GitHub + mật khẩu RDS master bị in vào transcript local …: **để nguyên, xoay khi lên prod**".

**Đề xuất này mở lại quyết định S240, lý do:** lộ qua transcript local, không phải leak public, nên mức khẩn cấp của **mật khẩu RDS** thấp hơn (RDS nằm trong VPC private, phải qua SG). Riêng **token GitHub thì dùng được từ bất kỳ đâu trên Internet** (scope `repo, workflow`): push vào repo đang deploy qua OIDC, đọc Infra. Vì vậy token tách ra làm ngay. Phần RDS chuyển sang P0-9 với thứ tự không làm gãy runtime.

**Đề xuất:**
1. Revoke token ngay (GitHub → Settings → Developer settings), cấp lại token fine-grained.
2. Xoá bản transcript có giá trị lộ. Ghi một bản ghi sự cố ngắn trong `docs/incidents/`.

**Công sức:** XS. **Tự động hoá:** không (thao tác tay).

#### P0-3. Agent AI chạy bằng quyền admin của người

**Bằng chứng [QS]:**
- `sts get-caller-identity` trả về `assumed-role/nghiep-admin-8h-session`.
- `~/.aws/config` **đã có `[profile aa365-agent]`** (dòng 79) nhưng không được dùng. `--profile aa365-admin` có trong `~/.claude/CLAUDE.md`, `.claude/CLAUDE.md`, `.kiro/steering/session-workflow.md`, `skill/ai-nghiep/references/aws.md`, `skill/aa-ship/SKILL.md`, `skill/aa-session/SKILL.md`, `skill/aa-cis-schema/SKILL.md`, `skill/aa-cis-schema/references/ecs-exec.md` (`grep -rln aa365-admin`).
- Role agent cho ECS exec (`agent_session.tf:67`) nhưng **Deny tường minh** đọc giá trị secret, start/stop/scale (`agent_session.tf:14-17, 159`).
- `~/.aws/credentials` có 5 profile key tĩnh (chỉ đọc tên): `acc1-legacy-default`, `aa365-nghiep-base`, `nghiep_aa365`, `aa365-admin-session`, `aa365-admin-toolkit`. `~/.aws/cli/cache` có 11 phiên STS, gồm phiên admin 8h có MFA mà `default` dùng chung.
- `gh auth status`: scope `repo, workflow, gist, read:org` trên 2 tài khoản.
- Working copy chưa commit của `.claude/settings.json` (153 dòng, bản commit 29 dòng) cho phép `terraform apply:*`, `aws iam *`, `gh workflow run:*`, ghi secret và sửa env Vercel.
- Hook guardrail thoát 0 khi không có `agent_id` (`subagent-guardrails.sh:11`), nên phiên chính không được kiểm.
- `.claude/settings.local.json` (gitignored) có 3 rule chứa chuỗi giống mật khẩu (không in giá trị).

**Rủi ro:** "lethal trifecta". Agent đọc nội dung không tin cậy (Jira, web, file nhà cung cấp, text tenant) trong khi giữ quyền ghi secret, IAM, Terraform và merge. Chỉ đặt `AWS_PROFILE` thì **không phải ranh giới**: agent vẫn truyền được `--profile aa365-admin` hoặc đọc cache. Đã từng có 2 lần ghi nhầm account (AA-517).

**Chuẩn:** OWASP Agentic Top 10 2026 ASI02/ASI03; OWASP LLM06 Excessive Agency; NIST SSDF PO.5; tài liệu bảo mật Claude Code.

**Đề xuất:**
1. **Sửa tài liệu điều khiển agent:** trong 8 file kể trên, lệnh dành cho agent đổi `--profile aa365-admin` thành `--profile aa365-agent`. Ghi rõ `aa365-admin` chỉ cho Nghiệp. Bỏ `AWS_PROFILE` trong `env` nếu tài liệu đã truyền `--profile` tường minh.
2. **`.claude/settings.json` (bản commit):**
   - `ask`: `Bash(terraform apply:*)`, `Bash(aws iam:*)`, `Bash(aws secretsmanager put-secret-value:*)`, `Bash(aws secretsmanager get-secret-value:*)`, `Bash(gh workflow run:*)`, `Bash(gh pr merge:*)`, `Bash(vercel env:*)`, `Bash(aws ecs update-service:*)`.
   - `deny`: `Read(~/.aws/**)`, `Read(~/.config/gh/**)`, `Bash(cat ~/.aws/*)`, và một rule chặn `--profile aa365-admin` (cú pháp wildcard cần thử trên bản Claude Code đang dùng [SL]).
   - Bản allow cá nhân để trong `settings.local.json`. Xoá 3 rule có mật khẩu literal.
   - Kiro có cấu hình trust riêng: áp danh sách tương đương.
3. **Terraform PR (Nghiệp apply):** cho role agent đọc đúng 1 secret `aa-cis/dev/e2e-test-admin`. Phải **thu hẹp Deny ở `agent_session.tf:159`** bằng `NotResource` cho ARN đó, vì Deny tường minh thắng mọi Allow.
4. **Luồng giữ lại cho Nghiệp** (agent dừng lại và nhờ): `terraform apply` cục bộ, ghi hoặc xoay secret, `aws iam`, scale/stop ECS, dispatch DB Migrate `apply`, merge PR chạm đường dẫn nhạy cảm.
5. Kiểm tra đầu phiên: cảnh báo nếu identity của agent là role admin.
6. Sau (P2): IAM Identity Center hoặc aws-vault để không còn key tĩnh trên đĩa; vô hiệu hoá `[acc1-legacy-default]` sau khi kiểm last-used; chạy agent dưới OS user hoặc devcontainer chỉ có profile `aa365-agent`.

**Công sức:** S (khoảng 2 ngày, gồm Terraform PR và sửa 8 file). **Tự động hoá:** có.

#### P0-4. Tính năng bảo mật GitHub miễn phí đang tắt, 2FA không bắt buộc

**Bằng chứng [QS]:**
- AA-CIS-App, AA-Booking, AA-TripPlanner-Web, AA-Ecosys (public): `secret_scanning`, `push_protection`, `dependabot_security_updates` đều `disabled`. CodeQL default setup `not-configured`. Private vulnerability reporting tắt.
- `AA-ACP-App` (archived, **public**): secret scanning `disabled`; lịch sử public chưa từng được quét.
- AA-CIS-Infra (private): `GET …/dependabot/alerts` trả 403 "Dependabot alerts are disabled". Infra chứa provider Terraform và workflow có role mạnh nhất.
- Org: `two_factor_requirement_enabled=false`, `members_can_create_public_repositories=true`.

**Đề xuất (0 USD, lệnh ở §8.4, Nghiệp chạy vì là thao tác ghi):**
1. 4 repo public: bật secret scanning, push protection, validity checks, Dependabot alerts và security updates, CodeQL default setup, private vulnerability reporting.
2. Infra: bật Dependabot alerts và security updates, thêm `dependabot.yml` cho `terraform` và `github-actions` (miễn phí trên repo private).
3. `AA-ACP-App`: chạy gitleaks/trufflehog toàn bộ lịch sử, xoay những gì tìm thấy, rồi xoá hoặc chuyển private.
4. Org: Require 2FA (UI: Org Settings → Authentication security), tắt quyền tạo repo public cho member.
5. Ruleset tối thiểu trên nhánh mặc định của 4 repo public (miễn phí): **chỉ** chặn force-push và xoá nhánh, chưa bắt PR hay approval (để không chặn luồng agent hiện tại; xem P1-1).

**Công sức:** XS. **Tự động hoá:** có.

#### P0-5. Backend không kiểm role cho các route ghi admin nhạy cảm

**Bằng chứng [QS]:**
- `frontend/lib/rbac.ts:66-72`: `API_RULES.admin = ALL_STAFF`. `canWriteAdminPath` trả `true` khi không có rule nào khớp (`:117-121`).
- Backend chỉ kiểm secret, không kiểm role, ở `PATCH /admin/llm-config/{stage}` (`admin_llm_ops.py:206-213`), `PUT /admin/budgets/...` (`admin_budgets.py:57-60`), cancel/retry/retention của job-runner (`admin_job_runner.py:169-215`).
- Backend tin `x-admin-role`/`x-admin-user-id` từ bất kỳ ai giữ `ADMIN_SECRET` (`admin.py:119-124`). So sánh secret bằng `!=`/`==` (`admin.py:113`, `auth.py:216-218`, `v1_social.py`, `v1_rules.py`, `v1_tours.py:685`); chỉ `v1_pipeline.py:51` dùng `hmac.compare_digest`.

**Rủi ro:** tài khoản reviewer hoặc content đổi được model LLM, gỡ ngân sách, huỷ job (OWASP API5 BFLA).

**Đề xuất:**
1. Dependency kiểm role phía server cho 3 nhóm route trên (chỉ `admin`/`owner`).
2. Một verifier chung dùng `hmac.compare_digest`, thay mọi chỗ so sánh secret.
3. Phần còn lại (role cho mọi router `/admin`, test route-policy, verify JWT staff) ở P1-3.

**Công sức:** S. **Tự động hoá:** có.

#### P0-6. Lỗi production không ai thấy

**Bằng chứng [QS]:**
- `api/core/sentry.py` đọc `aa-cis/dev/sentry-dsn-api`, nhưng `describe-secret` trả ResourceNotFoundException. Log ghi "Sentry DSN not found — error tracking disabled".
- Không có alarm 5XXError hoặc Latency cho API GW `4ylo382khg` (Booking thì có). Không có uptime check bên ngoài. SNS chỉ có email.

**Đề xuất (phần P0-A):**
1. Tạo secret DSN (Sentry free) cho CIS, `release = git SHA`.
2. Terraform: alarm 5XXError-rate và IntegrationLatency p95 cho CIS API GW.
3. Một uptime check miễn phí (Better Stack hoặc UptimeRobot) cho CIS `/health` và Booking `/booking/health/ready`, đẩy về điện thoại.

Sentry cho Booking/TripPlanner, OKActions, test guard thiếu DSN để ở P1-6.

**Công sức:** S. **Tự động hoá:** có.

#### P0-7. Cổng CI "luôn xanh" và deploy CIS chạy chồng

**Bằng chứng [QS]:**
- `AA-CIS-App/.github/workflows/ci.yml:51`: `pip-audit -r requirements.txt --ignore-vuln PYSEC-2024-56 || true`, nằm trong check **bắt buộc** "Security Audit". 0 Dependabot alert cộng pip-audit luôn qua nghĩa là không có bằng chứng quản lý lỗ hổng.
- `deploy-dev.yml` của CIS **không có `concurrency`** (kiểm trên remote `main`). 40/550 lượt chạy chồng thời gian. Run 38744146079 fail ở bước "same SHA".
- Guard của CIS fail-open khi thiếu `ADMIN_SECRET` (deploy-dev.yml:48-51).

**Đề xuất:**
1. Bỏ `|| true`, thay bằng danh sách `--ignore-vuln` có ngày hết hạn (giống Booking).
2. Thêm `concurrency: {group: deploy-dev-cis, cancel-in-progress: false}`. Guard chuyển fail-closed.
3. **Giữ** `--desired-count 1` trong `deploy_family.sh` (`deploy-dev.yml:147-148`) và thêm comment lý do: deploy phải đánh thức được service đã scale về 0, nếu không task-def được đăng ký nhưng không có task chạy và smoke sẽ timeout. Nếu sau này cần scale > 1, đổi thành "đọc `desiredCount` hiện tại qua `describe-services`, đặt `max(current, 1)`".

Trivy chặn, bỏ `frontend/**` khỏi path filter, ratchet coverage ở P1-4.

**Công sức:** XS–S. **Tự động hoá:** có.

### P0-B (trước tenant trả tiền đầu tiên, khoảng 15–20 ngày công)

#### P0-8. Cô lập tenant fail-open và phụ thuộc Redis không xác thực

**Bằng chứng [QS]:**
- `apps/AA-CIS-App/api/core/aa544_tenant_pool.py:146-158`: "Any Redis error or unset key means \"off\" (the admin pool…)". Pool admin là `aa_cis_admin` có BYPASSRLS (`:25-28`). Rollback là `redis-cli DEL <flag>` (`:30-32`). Mọi cờ "Default off (admin pool)" (`:59`). Lỗi đọc được log ở mức ERROR (`aa817_tenant_flag_read_failed`) nhưng không có alarm.
- `aws elasticache describe-cache-clusters`: `aa-cis-dev-redis` `cache.t3.micro`, `SnapshotRetentionLimit=0`, `AuthTokenEnabled=false`, `TransitEncryptionEnabled=false`, `AtRestEncryptionEnabled=false`. SG Redis cho ingress từ `sg-038383acb15660582`, SG chung của CIS api, worker và Booking api.
- Khoảng 14/63 route `/v1` dùng pool RLS; phần còn lại lọc `tenant_id` bằng tay trên pool BYPASSRLS. `_validate_wp_url` không resolve DNS và vẫn theo redirect (`v1_integrations.py:61-86, 340`).

**Rủi ro [SL]:** Redis reboot, thay node, bảo trì, hoặc một lệnh ghi Redis bất kỳ từ SG chung (kể cả từ container Booking) sẽ âm thầm đưa mọi route `/v1` đã chuyển về pool BYPASSRLS, không cần deploy, không có alarm. Rò rỉ dữ liệu chéo tenant là câu hỏi đầu tiên trong mọi questionnaire B2B (SOC 2 CC6.1, OWASP API1). SSRF qua URL WordPress do tenant nhập (API7).

**Đề xuất:**
1. Đảo mặc định trong code: thiếu cờ nghĩa là dùng pool tenant. Muốn quay về admin pool phải deploy hoặc đổi SSM Parameter (có IAM, có CloudTrail), không phải Redis. Giữ hành vi "Redis lỗi không gây 503" bằng cách đọc cờ từ cấu hình đã nạp lúc khởi động.
2. Redis: bật AUTH và TLS (`transit_encryption_enabled`, `auth_token` từ Secrets Manager). At-rest encryption cần tạo cluster mới, cùng loại node nên chi phí gần như không đổi.
3. Alarm trên metric filter `aa817_tenant_flag_read_failed` và trên `used_tenant_pool=false` cho route tenant.
4. Test CI route-policy cộng test 2 tenant cho mọi route `/v1`. Hoàn thành các wave AA-859.
5. Client `safe_http` dùng chung: resolve DNS và chặn IP private, `allow_redirects=False`, giới hạn size và timeout.

**Chuẩn:** OWASP API1/API7; SOC 2 CC6.1. **Công sức:** M. **Tự động hoá:** có.

#### P0-9. Runtime CIS đọc được PII của Booking/CRM, các app không tách mạng; mật khẩu RDS master đã lộ

**Bằng chứng [QS]:**
- `data-standards/02-data-management.md:214` (DM-6.8): "aa_cis_admin can still read crm.* through pg_read_all_data; the isolation is partial". DM-8.9: `aa_cis_admin` (master) là runtime CIS.
- `aws ecs describe-services`: 3 service dùng chung `sg-038383acb15660582`. SG RDS `sg-055c18ce0bd00b5e3` và SG Redis chỉ cho ingress từ SG đó.
- `aa-cis/dev/rds` là chuỗi DSN thuần, LastChangedDate 07/07/2026, RDS `MasterUserSecret=null`. Consumer: runtime CIS, `api/core/aa544_tenant_pool.py`, `services/acp_produce/sweeper_lambda.py`, skill ECS exec, các script verify.
- Pipeline CIS đưa text không tin cậy của tenant và nhà cung cấp vào LLM trong khi kết nối bằng role SELECT được `booking.customers`.

**Thứ tự (sai thứ tự sẽ làm gãy runtime):** secret do RDS quản lý là JSON `{username,password}` và tự xoay (mặc định 7 ngày). Bật nó trước khi runtime CIS rời master user thì runtime gãy ở mỗi lần xoay.
1. **Xoay tay một lần:** đổi master password qua RDS Console (không dán mật khẩu vào shell hay transcript). Cập nhật DSN trong `aa-cis/dev/rds` bằng Console. ⚠️ Có biến dấu gạch dưới: Nghiệp sửa tay. Sau đó force-new-deployment api và worker (lệnh ở §8.4), làm mới Lambda dùng DSN.
2. **AA-817 X1:** role runtime CIS riêng, không BYPASSRLS, không `pg_read_all_data`, REVOKE trên schema `booking`, `crm`, `tripplanner`.
3. **SG riêng cho từng app**, SG RDS và Redis liệt kê ingress theo từng app.
4. Test "isolation probe" trong CI: role CIS `SELECT booking.customers` phải lỗi.
5. Chỉ sau đó mới bật `manage_master_user_password = true` và bỏ `TF_VAR_DB_PASSWORD` khỏi GitHub.

**Chuẩn:** NIST SP 800-53 AC-6/IA-5; SOC 2 CC6.1. **Công sức:** S (bước 1) cộng M (bước 2–5). **Tự động hoá:** một phần.

#### P0-10. Biên API: login không giới hạn, không WAF/throttle, lộ docs, thiếu security header

**Bằng chứng [QS]:**
- JWT HS256, một `JWT_SECRET` dùng chung cho staff và tenant, không có `iss`/`aud`, sống 24h (`auth.py:38-39, 85`). `/auth/admin-login` không có lockout hay rate-limit.
- WAF chỉ gắn vào ALB (`list-resources-for-web-acl --resource-type API_GATEWAY` trả `[]`). Stage `dev` của CIS throttle `-1`. `waf_protect_rest_api_stages` mặc định `false` (`variables.tf:188-191`).
- Lưu lượng thật của `aa-cis-dev-api` stage `dev` (`get-metric-statistics Count`): đỉnh 186 request/phút trong 24h qua (khoảng 3 rps trung bình), p99 101/phút; đỉnh 1249 request/10 phút trong 14 ngày.
- `https://api-booking.lumiguides.it.com/booking/openapi.json` trả 200 (110.749 byte) công khai; `https://api-cis.lumiguides.it.com/booking/openapi.json` trả 403.
- `curl -sI https://aa-cis.lumiguides.it.com/login`: có HSTS, **không có** CSP, X-Frame-Options/frame-ancestors, X-Content-Type-Options, Referrer-Policy. Không có cấu hình header nào trong `next.config` của CIS và TripPlanner (`AA-TripPlanner-Web/frontend/next.config.mjs`); chỉ Booking có.
- CORS cho localhost kèm credentials trên môi trường đã deploy (`main.py:144-155`).

**Rủi ro:** dò mật khẩu staff (không MFA, không throttle). Flood vào RDS chung ảnh hưởng cả 3 app (API4). Bản đồ endpoint Booking bị lộ (API8/9). Trang login admin và portal tenant bị frame được (clickjacking), XSS không có CSP chặn.

**Đề xuất:**
1. Rate-limit theo IP cộng backoff tăng dần theo user (không khoá cứng theo user, vì ai cũng khoá được tài khoản staff khi biết username) cho `/auth/admin-login` và `/auth/tenant-login`.
2. Cấp `apigateway:SetWebACL` cho role apply, đặt `waf_protect_rest_api_stages=true`. Throttle stage CIS **50 rps / burst 100**: hơn 10 lần đỉnh đo được theo phút, đủ chỗ cho UI smoke, Playwright, Lambda TripPlanner và worker. Method `/auth/*` khoảng 5 rps / burst 10. Đo lại theo giây trước khi siết hơn.
3. Khoá `/booking/docs` và `/booking/openapi.json` trên `api-booking.lumiguides.it.com` theo pattern AA-577.
4. CORS rỗng ở môi trường đã deploy.
5. Security header qua `headers()` trong `next.config` cho CIS và TripPlanner (CSP có `frame-ancestors 'none'`, `nosniff`, Referrer-Policy chặt, HSTS mọi route), lấy Booking làm mẫu.

Phần còn lại (Cognito, tách key staff/tenant, bỏ god-key) ở P1-3 và ADR 0006 Phase 1.

**Chuẩn:** OWASP API Top 10 2023 API2/API4/API8/API9; OWASP ASVS V3/V14; NIST SP 800-63B. **Công sức:** M. **Tự động hoá:** có.

#### P0-11. Chưa chứng minh được khả năng khôi phục (DB) và rollback (app)

**Bằng chứng [QS]:**
- RDS `MultiAZ=false`, PITR 7 ngày. `backup list-backup-plans` trả `[]`. `03-scaling.md:336` ghi "Restore drill | never". AA-829 để "later".
- `docs/backups/2026-09-16` có 11 MB dump dữ liệu thật trên laptop (vi phạm DM-6.10). 4 snapshot RDS thủ công không có hạn (ví dụ `aa-cis-dev-db-g0-audit-20260916`).
- ECR `aa-cis-dev-api` MUTABLE, vẫn push `:latest`. Lifecycle "Keep last 10 images", trong khi CIS deploy khoảng 129 lần/tuần, nên task-def cũ hơn khoảng 1 ngày trỏ tới image đã bị xoá.
- `aa-ship` không có runbook rollback. Không có quy trình sự cố.

**Đề xuất:**
1. Diễn tập PITR: restore ra instance tạm, smoke query từng schema, ghi RTO vào `docs/audits/`, xoá instance tạm. Lặp lại mỗi quý.
2. Chuyển dump lên S3 prefix private SSE-KMS rồi xoá bản local. Đặt hạn cho snapshot thủ công.
3. ECR CIS: bỏ push `:latest` trong workflow **trước**, rồi chuyển IMMUTABLE qua Terraform. Lifecycle giữ 30 image `dev-*`, untagged hết hạn sau 7 ngày.
4. Rollback = **trỏ service về task-def revision trước** (một lệnh, ở §8.4), ghi vào `aa-ship`. `rollback.yml` là tuỳ chọn (P2).
5. Ghi cách dùng Vercel instant rollback.
6. Một trang `docs/ops/incident-response.md`: SEV1–3, ai được báo (gồm chị Thư và tenant), 15 phút đầu (rollback), mẫu thông báo. SLA trong P0-13 dựa vào trang này.

**Chuẩn:** NIST SP 800-34 CP-9/CP-10; AWS Well-Architected REL 9; DORA time-to-restore. **Công sức:** S–M. **Tự động hoá:** có.

#### P0-12. Đường truy cập dữ liệu production không review, không log; bên thứ ba quản trị account

**Bằng chứng [QS]:**
- ECS Exec bật trên `aa-cis-dev-api`, `aa-cis-dev-worker`, `aa-booking-dev-api` (`enableExecuteCommand=true`). Cluster `configuration=null`: không log phiên exec.
- Parameter group `aa-cis-dev-pg15`: `shared_preload_libraries=pg_stat_statements` (không có pgaudit), `log_connections` và `log_statement` để mặc định.
- Pattern "S3-mediated ECS exec" trong CLAUDE.md toàn cục tải script presign rồi chạy trong container với credential master, bỏ qua PR, CI và mọi cổng ở P0-1. Agent dùng hằng ngày; role agent có `ecs:ExecuteCommand` (`agent_session.tf:67`).
- `aws organizations describe-organization`: acc2 là member của org có management account `033086823579` (không thuộc 3 account AA), `FeatureSet=ALL`. Theo memory `acc2-bedrock-claude-gpt-blocked.md` đây là reseller TrueIDC (SCP đang chặn Bedrock LLM). **Chưa kiểm được** role `OrganizationAccountAccessRole` trong acc2 vì hook subagent chặn lệnh `aws iam`.

**Rủi ro:** questionnaire sẽ hỏi "truy cập dữ liệu production được kiểm soát và ghi log thế nào?" và "bên thứ ba nào có quyền đặc quyền trên hạ tầng?" (SOC 2 CC6.1/CC6.8/CC8.1). Biện pháp bù cho "prod trên acc2" ở §5.2 không áp dụng cho principal từ management account.

**Đề xuất:**
1. Bật ngay `executeCommandConfiguration` có logging (CloudWatch và/hoặc S3, KMS) trên cluster qua Terraform.
2. Load `pgaudit` (role-level `ddl,write`) và bật `log_connections` (cần reboot ngắn).
3. Nghiệp kiểm (chỉ đọc) có role nào trong acc2 trust `033086823579` không (lệnh ở §8.4). Xin TrueIDC chính sách truy cập và SCP bằng văn bản. Ghi TrueIDC vào danh sách sub-processor/vendor đặc quyền (P0-13) và secrets register.
4. Sau (P2): thay script ad-hoc bằng job kind đã review trong `shared.job` hoặc workflow "run-script" chỉ chạy script đã commit trên main; ECS exec thành break-glass.

**Công sức:** S. **Tự động hoá:** một phần.

#### P0-13. Hồ sơ pháp lý và thương mại tối thiểu (đề xuất nhẹ nhàng gửi chị Thư, không gây áp lực)

**Bằng chứng [QS]:**
- `docs/legal/` chỉ có `tenant-terms-ai-clause-draft.md` ("DRAFT … NOT APPROVED", AA-820, gắn với AUP của Anthropic hiệu lực 12/11/2026).
- DM-6.8: "A DPA template is required before the first tenant". DM-6.7 (`02-data-management.md:213`): xoá dữ liệu khách du lịch trải qua booking, tripplanner, jsonb audit, Cognito, S3, trạng thái "to build (L3); Runbook until then". Không có quy trình truy cập/xuất dữ liệu (DSAR).
- TripPlanner không có route privacy, terms hay cookie, trong khi vẫn thu tên, email, số điện thoại.
- Không có SLA, kênh support hay status page. PII khách Việt Nam lưu ở us-west-1 và gửi tới sub-processor Mỹ (OpenAI, Anthropic/Bedrock, Vercel).
- Vercel Hobby giới hạn ở mục đích phi thương mại.

**Rủi ro:** không ký được hợp đồng với tenant. Thu PII khi chưa có privacy notice. Nghị định 13/2023 Điều 25 và Luật BVDLCN 2025 yêu cầu hồ sơ đánh giá tác động chuyển dữ liệu ra nước ngoài [SL: luật sư xác nhận khả năng áp dụng].

**Đề xuất:** gói đề xuất cho chị Thư (chị và luật sư quyết):
- privacy policy và cookie notice;
- mẫu DPA kèm danh sách sub-processor (AWS, TrueIDC, Bedrock/Anthropic, OpenAI, Jev, Vercel, Mapbox, SES, Sentry);
- RoPA (sổ đăng ký hoạt động xử lý dữ liệu);
- runbook DSAR/xoá dữ liệu (theo DM-6.7);
- hồ sơ đánh giá tác động chuyển dữ liệu ra nước ngoài;
- SLA gọn (ví dụ 99,5%/tháng, thời gian phản hồi) dựa trên quy trình sự cố ở P0-11;
- `support@` dẫn vào Linear intake;
- chốt AA-820 trước 11/11; metadata `ai_generated` trong payload gửi tenant.

Phần kỹ thuật: trang `/privacy`, `/terms` trên TripPlanner và portal. Nâng **Vercel Pro** trước ngày thu tiền; khi đó bật lại Git integration cho preview (trần deployment cao hơn) để `VERCEL_TOKEN` chỉ còn ở env production main-only (đóng nốt phần P0-1).

**Chuẩn:** GDPR Art. 13/15/17/28/30; Nghị định 13/2023/NĐ-CP [SL: cần luật sư]; EU AI Act Art. 50; SOC 2 CC2.3. **Công sức:** M (phần lớn là thời gian người duyệt). **Tự động hoá:** không.

### P1 (90 ngày; 8 việc, khoảng 25–32 ngày công)

| # | Vấn đề (bằng chứng chính) | Đề xuất | Chuẩn | Công sức | Tự động |
|---|---|---|---|---|---|
| P1-1 | Không có cổng merge được ghi nhận: 0/951 PR có review (khoảng 16 PR/ngày, trung vị 6 phút). Root `master` không bảo vệ, 53/142 commit push thẳng. Agent push bằng `pqnghiep1354`, mà GitHub **không cho tác giả tự approve PR của mình**. Quy tắc tự mâu thuẫn (`.claude/CLAUDE.md` "DO NOT merge"; Booking "Agents never merge"; memory `agent-team-pilot.md` cho orchestrator merge). GitHub App (vercel `administration/workflows:write`, claude, linear-code) cài trên mọi repo. Chưa có quyết định visibility/gói GitHub | **Thứ tự bắt buộc:** (1) GitHub App "aa-agent" làm danh tính commit/PR của agent (token hết hạn sau 1h, cần credential helper cho cả Claude Code và Kiro). (2) ADR 0011 chọn phương án visibility × gói (§5.1). (3) ADR 0010 "Change authority". (4) Ruleset theo tầng rủi ro: CODEOWNERS cho `.github/workflows/**`, `db/migrations/**`, `accounts/**`, `.claude/**`, `.kiro/**`, `skill/**`, `CLAUDE.md`, module auth/RBAC; PR chạm các đường dẫn đó cần Nghiệp approve; còn lại auto-merge khi required checks xanh kèm AI review không chặn. Chưa bật "approval of most recent push" cho đến khi App identity chạy ổn. (5) Mỗi App chỉ cài vào repo cần dùng. Viết lại `autoMode.environment` trong `~/.claude/settings.json` (vẫn mô tả org cũ) | SSDF PW.7; Scorecard Code-Review/Branch-Protection; SOC 2 CC8.1 | M | có |
| P1-2 | Vệ sinh secret: 27 secret không rotation; `ADMIN_SECRET` ở 6 nơi (gồm env Lambda plaintext, `dfs_balance.tf:161`); `ACPCORE_READ_TOKEN`, `VERCEL_DEPLOY_HOOK` mồ côi; `ROOT_REPO_DOCS_TOKEN` là PAT; E2E admin là tài khoản staff đầy đủ | `docs/security/secrets-register.md` (tên, owner, consumer, ngày xoay, gồm vendor TrueIDC). Xoá secret mồ côi. PAT → App token. Lambda đọc secret theo ARN. Tài khoản E2E chuyển sang role staff chỉ đọc, không thấy PII; sau đó thay `ADMIN_SECRET` trong Vercel Preview bằng credential quyền thấp | SSDF PS.1; CIS Controls 5.3 | S | có |
| P1-3 | RBAC staff chỉ ở BFF (phần còn lại sau P0-5); JWT HS256 chung staff/tenant | `require_staff(roles=…)` ở cấp `APIRouter` cho mọi router `/admin`. Test CI duyệt `app.routes`, fail khi route `/admin` không phải GET thiếu policy. Backend verify JWT staff (Bearer), thôi tin header. Tách key staff/tenant (`iss`/`aud` hoặc RS256). TTL staff 8h. Đích: ADR 0006 Phase 1 (Cognito có MFA), bỏ `X-Admin-Secret` | OWASP API5; RFC 8725 | M | có |
| P1-4 | Cổng CI còn thiếu: CIS không có `tsc` hay `next build`; Trivy `exit-code: 0`; `deploy-lambdas.yml` TripPlanner không phụ thuộc CI, không smoke; không kiểm header bảo mật; coverage CIS 30% | Bắt buộc `tsc --noEmit` và `next build`. Trivy `exit-code: 1`, `ignore-unfixed`, `.trivyignore` có hạn. TripPlanner deploy Lambda sau CI kèm smoke curl, thêm job security của Booking. Check header trên preview (tuỳ chọn ZAP baseline). Bỏ `frontend/**` khỏi path filter deploy ECS. Coverage CIS ratchet +5%/tháng | Scorecard CI-Tests; SSDF PW.7/RV.1 | S–M | có |
| P1-5 | Không có eval gate cho prompt và model: `eval-regression.yml` chỉ dispatch tay, lần cuối 01/08; 85 commit đụng prompt từ đó; baseline thiếu thì `regression.py:139-142` trả False | Golden set 20–30 mẫu cho T2, T9 cộng bộ prompt-injection. Job PR bắt buộc theo path filter, trần ≤ 1 USD/lần qua `LLMClient` (`stage=adhoc_eval`). Fail khi thiếu baseline. PATCH `llm-config` kèm eval run ID | NIST SP 800-218A; OWASP LLM01/09 | M | có |
| P1-6 | Log text, không request ID; Sentry chưa có ở Booking/TripPlanner; alarm không có OKActions | structlog JSON và middleware request ID (gắn `tenant_id`, `job_id`) ở 3 app. Sentry cho Booking và TripPlanner. OKActions. Test guard: fail nếu không có DSN khi `ENVIRONMENT != test` | ASVS V7; Google SRE | S–M | có |
| P1-7 | Phát hiện và audit trail yếu: không GuardDuty, Access Analyzer, S3 BPA cấp account; CloudTrail single-region, không KMS, không CloudWatch, bucket không versioning hay Object Lock; log giữ 14 ngày, flow log 7 ngày; không có audit log thống nhất cho thao tác staff/tenant CIS | GuardDuty với feature giới hạn (§6), IAM Access Analyzer, S3 BPA cấp account. CloudTrail multi-region kèm KMS, gửi CloudWatch với metric filter (root login, thay đổi IAM/SG/trail, đọc Secrets Manager). Bucket trail versioning cộng Object Lock governance 365 ngày, lifecycle sang Glacier. Log bảo mật giữ ≥ 365 ngày (trên S3). Schema audit event append-only (actor, tenant, action, hash before/after) cho ghi `/admin` và `/v1` | CIS AWS Foundations 3.x/4.x; SOC 2 CC7.2/CC7.3 | S–M | có |
| P1-8 | Chưa có năng lực quyền chủ thể dữ liệu (DM-6.7 "to build") | Script xoá theo DM-6.7 chạy qua DRY RUN, có query xác minh. Endpoint export cho staff (DSAR). Chính sách hết hạn cho snapshot thủ công | GDPR Art. 15/17; Nghị định 13 | M | có |

### P2 (có điều kiện kích hoạt)

| # | Việc | Kích hoạt khi |
|---|---|---|
| P2-1 | ADR 0012 "Environment model": `dev` và `prod` trên acc2, đổi tên env Infra `prod` thành `dev-apply`, xoá env thừa, tham số hoá Terraform (`stacks/platform`), thống nhất C7.2c với CONTEXT.md của Infra; kèm điểm xem xét quyền management account | Bắt đầu dựng prod |
| P2-2 | Luồng Terraform: plan comment trên PR, apply gắn với hash của plan, `fmt`/`validate`/tflint/trivy config, drift hằng đêm, lock cho acc1/acc3, xoá `.bak`/`.tfplan` | Trước prod, hoặc sau sự cố drift tiếp theo |
| P2-3 | Build once, deploy theo digest; `attest-build-provenance`/`attest-sbom`; `vercel build --prebuilt`; pin SHA mọi action, allowlist action | First prod. Attestation chỉ khả thi trên repo public (phương án A) hoặc Enterprise (B) |
| P2-4 | OpenAPI: `response_model` cho `/v1`, commit `openapi.json`, `oasdiff breaking`; problem+json và `request_id` **chỉ trên bề mặt `/v1` ngoài và `docs/contracts`**; access log API GW, tắt `execute-api` | Tenant đầu tiên tích hợp bằng API |
| P2-5 | Public API v1: `shared.tenant_api_keys` (scope, hết hạn, ≥ 2 key active), X-API-Key, rate-limit theo key, usage plan. Ngay khi rảnh: gỡ `/v1/webhooks` khỏi Playground | Quyết định bán gói API |
| P2-6 | `Idempotency-Key` cho POST tốn tiền hoặc không đảo ngược được | Trước khi bật thanh toán |
| P2-7 | release-please, GitHub Deployment, CHANGELOG, release note cho tenant; đo DORA từ đó | First prod |
| P2-8 | Org `.github`: reusable workflow (Booking làm mẫu), PR/issue template, SECURITY.md, CONTRIBUTING | Contributor thứ hai, hoặc lần lệch pipeline thứ ba |
| P2-9 | SLO người dùng và alarm burn-rate, dashboard mỗi app, k6 | First prod |
| P2-10 | Migration: bot mở PR copy sang Infra, `required_schema_version` preflight | Sự cố "app deploy trước migration" tiếp theo |
| P2-11 | ECS exec thành break-glass, workflow "run-script" chỉ chạy script trên main | Sau P0-12, khi có prod |
| P2-12 | Pentest bên thứ ba (một lần, không phải chi phí tháng) | Trước deal enterprise đầu tiên |
| P2-13 | Không còn key tĩnh trên máy dev (IAM Identity Center hoặc aws-vault), agent chạy trong devcontainer/OS user riêng | Sau P0-3, trong 6 tháng |
| P2-14 | DR cho prod: Multi-AZ, PITR 14 ngày, AWS Backup cross-region; mạng prod (NAT GW, ALB internal, xoá default VPC); Security Hub FSBP và Config | Khi dựng prod |
| P2-15 | `rollback.yml`, Lambda alias `live` (ADR 0006:233) | First prod |
| P2-16 | Provenance code AI (trailer `AI-Agent:`), telemetry agent (OTel, session name riêng), tracing (AA-842 B), SLSA L3, harden-runner | Sau P1-6 |
| P2-17 | Dọn nhánh (CIS-App 702 nhánh, 209 đã merge), `delete_branch_on_merge`, squash-only; tự sinh trạng thái phiên/backlog | Bất kỳ lúc nào (XS) |

---

## 5. Mô hình đích cho 1 người cùng agent AI

Nguyên tắc: **agent làm nhanh, cổng do máy cưỡng chế, người chỉ bấm ở chỗ rủi ro cao** (PR chạm đường dẫn nhạy cảm, apply hạ tầng, promote prod). Mọi điểm đều có bản ghi trong GitHub. Không dựa vào việc agent "đọc và tuân thủ văn bản".

### 5.1 Repo, gói GitHub và ruleset

**Ma trận visibility × gói** (theo trang "Deployments and environments" của GitHub, đọc 17/10/2026 [QS]: trên Free/Pro/Team, required reviewer và wait timer **chỉ có cho repo public**; branch policy của env có cho repo private từ Pro/Team; `can_admins_bypass=false` chỉ cho repo public. Attestation trên repo private cần Enterprise Cloud; push protection trên repo private cần GHAS Secret Protection [SL: theo tài liệu GitHub mình biết, kiểm lại trước khi quyết]):

| | A. Team, root + Infra private, app public | B. Enterprise, tất cả private | C. Team, tất cả private |
|---|---|---|---|
| Chi phí GitHub | ~8 USD (2 seat) | ~42 USD (2 × ~21) | ~8 USD |
| Env reviewer, wait timer | Có trên repo app; Infra thì không | Có ở mọi repo | Không có |
| Cổng apply Infra | Ruleset PR + IAM `ref` + env branch policy | Env reviewer + các lớp kia | Ruleset PR + IAM `ref` + env branch policy |
| CodeQL, push protection | Miễn phí trên repo app; root/Infra dùng gitleaks pre-commit + CI | Cần GHAS nếu muốn (không đề xuất) | gitleaks pre-commit + CI, Semgrep OSS |
| Attestation | Có trên repo app | Có | Không |
| Lộ IP | Mã app public, cần LICENSE proprietary | Không | Không |
| Việc phải làm | Chuyển giá, audit, screenshot ra khỏi root public **trước** khi private hoá root | — | Như A cộng thêm 3 repo app |

**Khuyến nghị [SL]:** **A** ngay bây giờ (rẻ nhất mà vẫn giữ tính năng miễn phí cho repo app). Xem lại sang **B** khi khách enterprise đòi mã nguồn private hoặc có contributor thứ hai. Đây là quyết định kinh doanh (IP) của Nghiệp và chị Thư, ghi trong ADR 0011. Lý do public ở S235 (`docs/sessions/2026-10-14-S235-…md:29`, "public, branch protection 5 check") vẫn đúng cho repo app; với root và Infra thì không, vì root chứa giá và audit, còn Infra trả protection bằng Team.

- **Trunk-based** (giữ ADR-2026-023): nhánh ngắn hạn, squash-only, `delete_branch_on_merge`, linear history.
- **Ruleset theo tầng rủi ro** (sau khi có App identity):
  - mọi PR: required checks dùng tên chuẩn (`lint`, `security`, `unit`, `integration`, `build`, cộng `ui-smoke` và `eval` theo path), chặn force-push và xoá; auto-merge khi xanh;
  - PR chạm đường dẫn trong CODEOWNERS: cần Nghiệp approve [SL: thử `required_approving_review_count=0` cộng `require_code_owner_review=true` trên một repo trước];
  - bypass chỉ cho tài khoản break-glass `adventure365`.
- **Danh tính:** `pqnghiep1354` là owner, 2FA bằng passkey; `adventure365` là break-glass; **GitHub App "aa-agent"** là tác giả PR của agent, không có quyền admin hay secrets.

### 5.2 Môi trường và luồng promote

```
feature branch ──PR──► CI (lint, security, unit, integration, build)
                         │ auto-merge khi xanh; Nghiệp approve nếu chạm đường dẫn nhạy cảm
                         ▼
                 main ──► dev (acc2, env "dev", main-only) ── smoke + UI smoke + eval subset
                         │ tag vX.Y.Z
                         ▼
                 prod (acc2, env "prod", main/tag-only;
                       reviewer + wait timer nếu repo public hoặc Enterprise,
                       nếu không: IAM ref + ruleset PR là cổng)
                         └─ cùng image, cùng Vercel deployment được promote; smoke prod
```

- **Không dựng staging thường trực lúc này.** Khi có prod, Dev đóng vai pre-prod. Preview Vercel theo PR đáp ứng nhu cầu review UI.
- **Prod trên acc2** (quyết định đã chốt ở ADR 0001 và CLAUDE.md). Chuẩn AWS (Well-Architected SEC01) khuyến nghị tách account. Mình **giữ quyết định**, ghi trong ADR 0012 các biện pháp bù:
  - role và trust OIDC riêng cho prod (`environment:prod` cộng điều kiện `ref`);
  - KMS CMK riêng cho prod;
  - permission boundary và tag `env=prod` (ABAC) chặn role Dev đụng vào tài nguyên prod;
  - DB instance riêng cho prod, SG riêng cho từng app;
  - state Terraform key riêng;
  - role agent không có quyền gì trên tài nguyên `env=prod`.
  
  **Giới hạn:** các biện pháp này không áp dụng cho principal từ management account của TrueIDC (P0-12). ADR 0012 phải ghi điểm xem xét "ai sở hữu/kiểm soát account" trước khi dựng prod.

### 5.3 CI/CD chuẩn

- **Deploy:** `concurrency` theo service, guard fail-closed, smoke theo contract, circuit breaker kèm alarm, rollback bằng task-def revision trước (P0-11).
- **Supply chain:** Dependabot (pip, npm, docker, github-actions, terraform) gom PR hằng tuần, tự merge patch/minor khi xanh; pip-audit/npm audit/Trivy chặn build với ignore có hạn; export kết quả hằng tháng làm bằng chứng. CodeQL trên repo public, gitleaks pre-commit cộng CI trên repo private.
- **Build once theo digest, attestation, reusable workflow:** P2 (kích hoạt khi first prod hoặc contributor thứ hai).

### 5.4 Quản lý secret

- **Nguồn sự thật:** AWS Secrets Manager (runtime) và GitHub env secret (chỉ những gì CI cần). Không lưu secret trong env Lambda hay TF state.
- **Register** `docs/security/secrets-register.md` (tên, owner, consumer, ngày xoay). Xoay 90 ngày, và **xoay ngay khi nghi lộ** (theo thứ tự an toàn như P0-9), coi đó là sự cố có bản ghi.
- **Danh tính máy:** OIDC (AWS), GitHub App token (cross-repo), Vercel token chỉ ở env production. Không dùng PAT cá nhân trong CI.
- Agent không đọc được secret runtime, không đọc `~/.aws/**`, chỉ đọc secret e2e đã allowlist.

### 5.5 Quản lý API

- **Bây giờ:** kiểm role ở backend, cô lập tenant fail-closed, rate-limit login, WAF và throttle, security header, khoá docs.
- **Khi tenant tích hợp API:** OpenAPI cho `/v1` (`response_model`, `oasdiff breaking`), problem+json và `request_id` cho `/v1`, Deprecation/Sunset header, idempotency key trước thanh toán. HTTP contract giữa các app nằm trong `docs/contracts`.
- **AuthN/AuthZ đích:** Cognito (ADR 0006) với JWT bất đối xứng (`iss`, `aud`, `kid`); deny-by-default có test liệt kê route; API key nhiều key mỗi tenant; bỏ god-key `X-Admin-Secret`.
- **Inventory** một bảng trong `ecosystem-architecture.md`: domain, API, owner, auth, consumer.

### 5.6 Quan sát và SLO

Sentry cho 3 app; log JSON có request ID; alarm 5xx/latency cho mỗi API; uptime ngoài; alarm đẩy về điện thoại kèm OK; audit trail giữ 365 ngày. SLO burn-rate và dashboard khi có prod.

### 5.7 Phát hành và hỗ trợ khách hàng

- Trước tenant đầu tiên: quy trình sự cố một trang, SLA gọn, `support@` dẫn vào Linear, status page free.
- Khi có prod: release-please, CHANGELOG, release note cho tenant.

### 5.8 ADLC: cổng review, phạm vi quyền agent, eval

| Lớp | Agent được làm | Chỉ người (hoặc CI có cổng) |
|---|---|---|
| Code | branch, commit, mở PR (bằng App "aa-agent"), chạy test, đọc log; auto-merge PR rủi ro thấp khi xanh | approve và merge PR chạm đường dẫn nhạy cảm |
| AWS | `aa365-agent`: describe/list/get, đọc log, đọc secret e2e đã allowlist; ECS exec Dev **chỉ khi đã bật log phiên** (P0-12) | IAM, Terraform apply, DB Migrate apply, ghi secret, scale/stop, xoá tài nguyên |
| GitHub settings | GET | ruleset, environment, secret |
| Vercel | đọc deployment/log | env var, promote prod |
| LLM/prompt | sửa prompt trong PR | đổi model route (kèm eval run ID) |

- **Cưỡng chế bằng IAM, token, permission deny và sandbox**, không chỉ bằng regex hook. Hook là lớp bổ sung, áp cho cả phiên chính.
- **Eval-driven:** PR đụng prompt, model hoặc route phải qua eval có trần chi phí.
- **Rà soát:** mỗi quý xem lại permission, cấu hình agent và App install (một mục trong backlog time-gated).

---

## 6. Lộ trình

Tiêu đề issue Linear bằng tiếng Anh. Theo quy tắc, **hỏi Nghiệp trước khi tạo issue**; danh sách dưới đây là đề xuất.

### Giai đoạn 0a (tuần này, khoảng 3–4 ngày công, 0 USD): P0-A

| Issue đề xuất | Map | Công sức |
|---|---|---|
| Restrict CIS deploy environments to main, add ref guard and IAM ref condition to apply/migrate/deploy roles, env-scope ADMIN_SECRET | P0-1 | S |
| Revoke the exposed GitHub token and record the incident | P0-2 | XS |
| Run agent sessions on aa365-agent; ask/deny list; block agent reads of ~/.aws | P0-3 | S |
| Enable free GitHub security features, org 2FA, Infra Dependabot; scan AA-ACP-App history | P0-4 | XS |
| Server-side role check on llm-config, budgets, job-runner writes; constant-time secret compare | P0-5 | S |
| Create Sentry DSN, CIS API 5xx/latency alarms, one external uptime check | P0-6 | S |
| Make pip-audit blocking; add concurrency and fail-closed guard to CIS deploy | P0-7 | XS–S |

### Giai đoạn 0b (trước tenant trả tiền đầu tiên, khoảng 15–20 ngày công, 4–6 tuần part-time song song với Booking B4): P0-B

| Issue đề xuất | Map | Công sức |
|---|---|---|
| Make tenant RLS pool the default; Redis AUTH/TLS; alarm on flag-read failure; two-tenant route tests; safe_http | P0-8 | M |
| Rotate RDS master manually, ship AA-817 X1 runtime role, per-app security groups, isolation probe; then RDS-managed secret | P0-9 | S+M |
| Login rate limiting, WAF and measured throttles on CIS stage, gate Booking docs, CORS, security headers | P0-10 | M |
| AA-829 PITR drill, dumps to encrypted S3, immutable CIS ECR, task-def rollback runbook, incident one-pager | P0-11 | S–M |
| ECS Exec session logging, pgaudit, log_connections; verify management-account access to acc2 | P0-12 | S |
| Legal readiness packet for Ms. Thư (privacy, DPA, RoPA, DSAR, transfer assessment, SLA) and Vercel Pro | P0-13 | M |

### Giai đoạn 1 (đến hết 90 ngày): P1-1 … P1-8

- Agent GitHub App identity, then risk-tiered rulesets, CODEOWNERS, ADR 0010 and ADR 0011 *(P1-1)*
- Secrets register, env-scoped secrets, read-only E2E account *(P1-2)*
- Server-side staff RBAC for all /admin routers with a route-policy test *(P1-3)*
- Required FE typecheck/build, blocking Trivy, TripPlanner Lambda deploy after CI *(P1-4)*
- Cost-capped eval gate for T2/T9 prompt and model changes *(P1-5)*
- JSON logging with request IDs; Sentry for Booking and TripPlanner *(P1-6)*
- GuardDuty (limited features), Access Analyzer, hardened multi-region CloudTrail, 365-day security logs *(P1-7)*
- DM-6.7 erasure script under DRY RUN, staff export, snapshot expiry *(P1-8)*

### Chi phí tăng thêm ước tính mỗi tháng

Toàn bộ là **[SL]**: giá công khai mình biết, cần kiểm lại trang giá trước khi bật (theo quy tắc "Cost before new AWS services").

| Hạng mục | Giai đoạn | USD/tháng | Ghi chú |
|---|---|---|---|
| Tính năng bảo mật GitHub trên repo public, Sentry free, uptime free | 0a | 0 | |
| WAF gắn thêm REST stage (dùng lại web ACL) | 0b | ~0–2 | Chỉ phí request |
| Restore drill (instance tạm vài giờ, mỗi quý) | 0b | <1 | |
| ECR giữ 30 image | 0b | ~1–3 | |
| Log phiên ECS exec, pgaudit và log_connections (CloudWatch) | 0b | ~1–5 | Phụ thuộc lượng ghi |
| Redis mới có TLS/AUTH/at-rest, cùng `cache.t3.micro` | 0b | ~0 | Thay thế, không thêm node |
| **Vercel Pro (1 member)** | 0b | ~20 + usage | Hobby là phi thương mại |
| GitHub: phương án A hoặc C (Team, 2 seat) | 1 | ~8 | Phương án B (Enterprise): ~42 |
| GuardDuty, chỉ foundational (CloudTrail, VPC flow, DNS) cộng RDS login | 1 | ~1–5 | Tắt `RUNTIME_MONITORING`, `EBS_MALWARE_PROTECTION`, `LAMBDA_NETWORK_LOGS`, `S3_DATA_EVENTS` lúc đầu; xác nhận bằng ước tính trong 30 ngày dùng thử (lệnh ở §8.4) trước khi giữ |
| CloudTrail multi-region, KMS key, bucket versioning/Object Lock | 1 | ~1–3 | |
| Giữ log bảo mật 365 ngày (S3/Glacier), log app 30–90 ngày | 1 | ~2–8 | |
| **Tổng đến hết P1, phương án A hoặc C** | | **~35–55** | Cộng phí usage Vercel |
| **Tổng đến hết P1, phương án B** | | **~70–90** | |
| Pentest bên thứ ba | P2 | một lần | Không phải phí tháng; báo giá riêng |
| Prod trên acc2 (RDS Multi-AZ, ECS prod, NAT GW mỗi AZ, AWS Backup cross-region) | khi dựng prod | ~150–300 | Ước rất thô; tính riêng trong ADR 0012 |

GuardDuty bằng Terraform: `aws_guardduty_detector` cộng một `aws_guardduty_detector_feature` cho mỗi feature trên với `status = "DISABLED"`, và `RDS_LOGIN_EVENTS` ở `ENABLED`.

---

## 7. Những gì KHÔNG nên làm lúc này

1. **Không dựng staging thường trực, multi-region hay active-active.** Dev, PR preview và promote cùng image là đủ cho đến khi có prod và khách lớn.
2. **Không mua GHAS cho repo private.** Dùng gitleaks (pre-commit và CI) và Semgrep OSS.
3. **Không làm Infra thành public.** Team (8 USD) cộng IAM `ref` rẻ hơn rủi ro.
4. **Không chạy Kubernetes, service mesh, Backstage hay developer portal tự host.**
5. **Không bật Security Hub hay AWS Config lúc này** (chi phí và nhiễu). GuardDuty giới hạn feature, Access Analyzer và audit trail vẫn làm ở P1, vì Dev đang giữ PII thật.
6. **Không làm audit SOC 2 hay ISO thật lúc này.** Chỉ chuẩn bị bằng chứng (approval trên PR nhạy cảm, change log, register, postmortem).
7. **Không bắt bấm duyệt tay mọi PR.** Khoảng 16 PR/ngày; chỉ PR chạm đường dẫn nhạy cảm cần người, còn lại auto-merge khi xanh kèm AI review.
8. **Không bật canary hay CodeDeploy cho ECS ngay.** Circuit breaker, alarm và rollback bằng task-def revision là đủ.
9. **Không dùng Pact broker.** `oasdiff` và JSON Schema trong `docs/contracts` là đủ khi cần.
10. **Không viết lại toàn bộ auth trước ADR 0006 Phase 1.** Chỉ vá (P0-5, P0-10), rồi đi thẳng sang Cognito.
11. **Không chạy eval trên toàn catalog.** Golden set 20–30 mẫu có trần chi phí.
12. **Không tách AWS account cho prod ngay** (đi ngược quyết định đã chốt). Áp biện pháp bù ở §5.2, ghi điểm xem xét lại (gồm quyền management account) trong ADR.
13. **Không bật `manage_master_user_password` trước AA-817 X1** (P0-9).
14. **Không khoá cứng tài khoản theo username** khi làm rate-limit login (P0-10).

---

## 8. Phụ lục

### 8.1 Chuẩn tham chiếu

| Chuẩn | Link |
|---|---|
| NIST SSDF SP 800-218 v1.1, SP 800-218A (AI) | https://csrc.nist.gov/projects/ssdf, https://csrc.nist.gov/pubs/sp/800/218/a/final |
| SLSA v1.x | https://slsa.dev/spec/ |
| OpenSSF Scorecard checks | https://github.com/ossf/scorecard/blob/main/docs/checks.md |
| OWASP ASVS 5.0 | https://owasp.org/www-project-application-security-verification-standard/ |
| OWASP API Security Top 10 2023 | https://owasp.org/API-Security/editions/2023/en/0x11-t10/ |
| OWASP Top 10 for LLM Apps 2025 | https://genai.owasp.org/llm-top-10/ |
| OWASP Top 10 for Agentic Applications 2026 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ |
| DORA metrics | https://dora.dev/guides/dora-metrics/ |
| GitHub deployments and environments (gói và tính năng) | https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments |
| GitHub artifact attestations | https://docs.github.com/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds |
| AWS IAM condition keys cho OIDC (tab GitHub: `ref`, `job_workflow_ref`…) | https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html |
| Claude Code security | https://code.claude.com/docs/en/security |
| CIS AWS Foundations / CIS GitHub Benchmark | https://www.cisecurity.org/benchmark/amazon_web_services |
| AWS Well-Architected (Security, Reliability) | https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html |
| RFC 9457 Problem Details; RFC 8594 Sunset | https://www.rfc-editor.org/rfc/rfc9457, https://www.rfc-editor.org/rfc/rfc8594 |
| EU AI Act Art. 50 | https://artificialintelligenceact.eu/article/50/ |
| Google SRE workbook (SLO) | https://sre.google/workbook/implementing-slos/ |

### 8.2 Bằng chứng chi tiết theo lĩnh vực

Báo cáo gốc (tiếng Anh, chưa cập nhật theo §9; khi lệch, README này thắng):

- [`areas/github-governance.md`](areas/github-governance.md): GitHub org và quản trị repo
- [`areas/cicd.md`](areas/cicd.md): CI/CD và luồng phát hành, kèm số liệu DORA ước tính
- [`areas/environments-secrets-iam.md`](areas/environments-secrets-iam.md): môi trường, secret, IAM, mạng, DR, residency
- [`areas/api.md`](areas/api.md): quản lý API, đối chiếu OWASP API Top 10 2023
- [`areas/quality-observability-delivery.md`](areas/quality-observability-delivery.md): test, cổng chất lượng, quan sát, sự cố, giao hàng
- [`areas/adlc-standards.md`](areas/adlc-standards.md): ADLC và baseline chuẩn bên ngoài

### 8.3 Mâu thuẫn giữa các báo cáo lĩnh vực và kết quả tự kiểm (17/10/2026)

| # | Mâu thuẫn | Kiểm bằng | Kết luận |
|---|---|---|---|
| 1 | ADLC nói `.claude/settings.json` **đã commit** cho phép `aws iam *`, `terraform apply:*`…; GitHub area nói bản commit chỉ có `gh pr merge:*` | `git show HEAD:.claude/settings.json` | Bản commit có **29 dòng, chỉ `Bash(gh pr merge:*)`**. Các allow rộng nằm trong **working copy chưa commit** (153 dòng). GitHub area đúng. |
| 2 | CI/CD nói CIS có "204 Dependabot alerts"; GitHub area nói 0 | `gh api repos/.../AA-CIS-App/dependabot/alerts` (mọi state, paginate) | **0 alert** (alerts đang bật trên repo public, trả `[]` chứ không 403). Con số 204 không tái hiện được. `pip-audit` (AA-177) từng tìm ra 5 lỗ hổng, nên dựa vào `pip-audit` chặn build. |
| 3 | Env area liệt kê "plan as required PR check" ở Infra là điểm mạnh | `gh api` protection Infra → 403 | **Không thể bắt buộc** (Infra không có protection). Plan chỉ mang tính tham khảo. |
| 4 | CLAUDE.md dự án ghi các repo ACP "ĐÃ ARCHIVE + XOÁ"; các area ghi xoá 26/08 | `gh api orgs/.../repos` | **Vẫn tồn tại ở trạng thái archived**: `AA-ACP-App` (public, secret scanning tắt), `AA-ACP-Core` (private). Cần sửa CLAUDE.md và xử lý theo P0-4. |
| 5 | Có hay không role/profile riêng cho agent | `grep '^\[profile' ~/.aws/config` | `[profile aa365-agent]` **đã có** (dòng 79) nhưng phiên agent vẫn dùng `aa365-admin`. Thiếu là cấu hình, tài liệu và ranh giới đọc file, không phải thiếu hạ tầng. |
| 6 | Vị trí `settings.local.json` có mật khẩu literal | `ls` hai vị trí | File nằm ở **`/home/nghiep/projects/AA-Ecosys/.claude/settings.local.json`** (gitignored). Có 3 chuỗi dạng `pass…=`; giá trị không được in. |
| 7 | Env area đề xuất account AWS riêng cho prod; ADR 0001 và CLAUDE.md đã chốt prod trên acc2 | ADR 0001:79-80, CLAUDE.md | **Giữ quyết định đã chốt**, kèm biện pháp bù (§5.2) và giới hạn về management account (P0-12). |
| 8 | API area đề xuất "ADR 0009" cho HTTP conventions | `docs/adr/README.md:21` | 0009 đã giữ chỗ cho AI platform (AA-804). ADR mới đánh số từ 0010 (Change authority), 0011 (Repo visibility), 0012 (Environment model), 0013 (HTTP API conventions, P2). |
| 9 | Số dòng `terraform-apply.yml` | `grep -n` trên Infra `a6605ce` | `workflow_dispatch` dòng 4, `environment: prod` dòng 18, `terraform apply … -auto-approve` dòng 77-78, **không có** `github.ref`. |
| 10 | Deploy CIS có `concurrency` hay không | `gh api …/contents/.github/workflows/deploy-dev.yml` | **Không có** trên remote `main`. |
| 11 | Root master: 8/50 commit push thẳng và 53/142 | — | Khác khoảng thời gian, không mâu thuẫn. |
| 12 | Grant set của role tf-apply | `accounts/aa365/cicd.tf:22-32` | Xác nhận (giới hạn bởi boundary DenyIamWrites). |
| 13 | Trạng thái env | `gh api …/environments` | CIS `dev` 0 rule/null; CIS `prod` có `protected_branches`; CIS `Preview` 0 rule/null; Infra `dev`/`prod`/`staging` 0 rule/null; Booking `dev` có custom policy; `can_admins_bypass=true` ở mọi env. |
| 14 | Checkout local AA-CIS-App không có `vercel-deploy.yml` | `ls .github/workflows` local so với `gh api …/contents` | Checkout local cũ hơn remote; bằng chứng về Vercel lấy từ remote `main`. |

### 8.4 Lệnh một dòng (đều là thao tác ghi: **Nghiệp chạy tay**, agent không chạy)

Thay `<repo>` lần lượt bằng `AA-CIS-App`, `AA-Booking`, `AA-TripPlanner-Web`, `AA-Ecosys`.

```bash
# P0-4: secret scanning + push protection (repo public)
gh api -X PATCH repos/AdventureAsia365-Ecosys/<repo> -f 'security_and_analysis[secret_scanning][status]=enabled' -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'
# P0-4: Dependabot alerts + security updates (gồm cả AA-CIS-Infra)
gh api -X PUT repos/AdventureAsia365-Ecosys/<repo>/vulnerability-alerts
gh api -X PUT repos/AdventureAsia365-Ecosys/<repo>/automated-security-fixes
# P0-4: CodeQL default setup + private vulnerability reporting (repo public)
gh api -X PATCH repos/AdventureAsia365-Ecosys/<repo>/code-scanning/default-setup -f state=configured
gh api -X PUT repos/AdventureAsia365-Ecosys/<repo>/private-vulnerability-reporting
# P0-4: không cho member tạo repo public (Require 2FA: UI Org Settings → Authentication security)
gh api -X PATCH orgs/AdventureAsia365-Ecosys -F members_can_create_public_repositories=false
# P0-1: env dev của CIS chỉ cho main (lặp lại cho prod; kiểm lại cấu hình sau khi PUT)
echo '{"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}' | gh api -X PUT repos/AdventureAsia365-Ecosys/AA-CIS-App/environments/dev --input -
gh api -X POST repos/AdventureAsia365-Ecosys/AA-CIS-App/environments/dev/deployment-branch-policies -f name=main -f type=branch
# P0-9: sau khi đổi mật khẩu master và DSN trong Console, khởi động lại api và worker
aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --force-new-deployment --profile aa365-admin --region us-west-1
aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-worker --force-new-deployment --profile aa365-admin --region us-west-1
# P0-11: rollback về task-def revision trước (thay <family>:<rev>; image của revision đó phải còn trong ECR)
aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --task-definition <family>:<rev> --profile aa365-admin --region us-west-1
# P0-11: chỉ sau khi workflow thôi push :latest (nên làm qua Terraform để không drift)
aws ecr put-image-tag-mutability --repository-name aa-cis-dev-api --image-tag-mutability IMMUTABLE --profile aa365-admin --region us-west-1
# P0-12: kiểm (chỉ đọc) role mà management account có thể assume
aws iam get-role --role-name OrganizationAccountAccessRole --profile aa365-admin --region us-west-1 --query 'Role.AssumeRolePolicyDocument'
# P0-10: đo lại lưu lượng (chỉ đọc; period 60 thì tối đa 1 ngày mỗi lần gọi)
aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --metric-name Count --dimensions Name=ApiName,Value=aa-cis-dev-api Name=Stage,Value=dev --period 60 --statistics Sum --start-time <ISO-1d> --end-time <ISO-now> --profile aa365-admin --region us-west-1
# P1-7: ước tính chi phí GuardDuty trong thời gian dùng thử (chỉ đọc)
aws guardduty get-usage-statistics --detector-id <id> --usage-statistic-type SUM_BY_FEATURES --usage-criteria '{"Features":["CLOUD_TRAIL","DNS_LOGS","FLOW_LOGS","RDS_LOGIN_EVENTS"]}' --profile aa365-admin --region us-west-1
```

---

## 9. Phản biện đã xử lý

Hai vòng phản biện, 24 điểm (12 mỗi vòng), đánh số 1–24 theo thứ tự nhận. Điểm 14 (vòng 2: "Team không có env reviewer cho repo private") trùng điểm 1 nên gộp vào đó. Mình tự kiểm lại các dữ kiện bị tranh luận trước khi sửa.

### 9.1 Chấp nhận và đã sửa

| # | Phản biện | Kiểm lại | Đã sửa |
|---|---|---|---|
| 1, 14 | Team không cho required reviewer/wait timer trên repo private; attestation private cần Enterprise; push protection private cần GHAS | Trang GitHub "Deployments and environments" [QS]: "If you are on a GitHub Free, GitHub Pro, or GitHub Team plan, required reviewers are only available for public repositories" (wait timer, admin-bypass cũng vậy) | Thêm ma trận visibility × gói ba phương án A/B/C vào §5.1 (cho ADR 0011, Nghiệp chọn). Sửa §5.2, P1-1, bảng chi phí. Ghi rõ comment `cicd_split.tf:515-517` giả định reviewer không tồn tại. Attestation chuyển sang P2-3 với điều kiện. Ghi rõ đây là đảo lại lựa chọn public của S235 và vì sao chỉ đảo cho root/Infra |
| 2 | Ruleset "1 CODEOWNERS approval" không chạy được với 1 người; App identity phải có trước; 16 PR/ngày | Agent push bằng `pqnghiep1354`, GitHub không cho tác giả tự approve | P1-1: App identity trước, rồi ruleset theo tầng rủi ro (chỉ đường dẫn nhạy cảm cần duyệt); tắt "approval of most recent push" đến khi App chạy ổn; đánh giá lại M. §7 #7 sửa |
| 3 | P0 quá to, trộn "đang hở" với "trước prod"; 1–2 tuần không thực tế | Đếm lại: 10 mục, 3 M | Tách P0-A (7 mục, khoảng 3–4 ngày công) và P0-B (6 mục, khoảng 15–20 ngày công, 4–6 tuần part-time). Team, ADR 0010/0011, visibility chuyển sang P1-1; `rollback.yml`, Lambda alias sang P2-15. §1 bỏ câu "đóng phần lớn bằng XS–S" |
| 4 | Bật RDS-managed secret trước AA-817 X1 làm gãy runtime; lấn quyết định S240 không nói | `aa-cis/dev/rds` là DSN thuần; consumer liệt kê ở P0-9 | P0-2 chỉ còn revoke token GitHub và nói rõ đang mở lại quyết định S240, kèm lý do. Phần RDS sang P0-9 theo thứ tự xoay tay → X1 → managed. Đánh giá S cộng M. §7 #13 |
| 6 | Token Vercel "preview riêng" không tách được; bỏ `ADMIN_SECRET` khỏi Preview làm gãy UI smoke và vòng lặp Kiro | `skill/aa-ui-verify/SKILL.md:30`, `.claude/skills/kiro-delegate/SKILL.md:29`; `vercel-deploy.yml` dùng 1 token cho cả preview và production | Bỏ đề xuất token preview riêng và bỏ ngay `ADMIN_SECRET` khỏi Preview. Ghi rủi ro chấp nhận. Biện pháp bù: tài khoản E2E chỉ đọc (P1-2); khi có Vercel Pro, bật lại Git integration cho preview để token chỉ còn ở env production main-only (P0-13). Ghi chú thêm: Git integration bị tắt vì trần deployment của Hobby (`vercel-deploy.yml:3-7`) |
| 7 | Chi phí mâu thuẫn (§1 8–40, §6 35–55); GuardDuty không nêu feature | — | Một khoảng thống nhất: 35–55 (A/C), 70–90 (B). GuardDuty chỉ foundational cộng RDS login, liệt kê feature tắt, có lệnh kiểm usage trong thời gian dùng thử |
| 8 | P1 quá nhiều, nhiều việc kiểu enterprise | 18 mục, khoảng 11 M và 1 L | P1 còn 8 mục (khoảng 25–32 ngày công). release-please, reusable workflow, attestation, build-by-digest, burn-rate SLO, migration bot, oasdiff/problem+json (chỉ cho `/v1` khi tenant tích hợp) chuyển P2 kèm điều kiện kích hoạt |
| 9 | Đặt `AWS_PROFILE` vô tác dụng khi lệnh truyền `--profile aa365-admin`; Deny secret xung đột luồng e2e; công sức không thống nhất | `grep -rln aa365-admin` ra 8 file; `agent_session.tf:159` Deny tường minh `GetSecretValue` | P0-3 liệt kê 8 file cần sửa, danh sách `ask`/`deny` cụ thể, Terraform PR phải thu hẹp Deny bằng `NotResource` (Allow thôi là không đủ), các luồng giữ cho Nghiệp. Một mức công sức: S |
| 10 | "Bỏ ép desired-count" không có lý do và làm smoke timeout | `deploy-dev.yml:147-148` | P0-7: giữ dòng đó, thêm comment; phương án `max(current,1)` khi cần |
| 11 | Số throttle và lockout chưa đo; khoá theo user gây DoS | Đo CloudWatch [QS]: đỉnh 186 req/phút (24h), 1249 req/10 phút (14 ngày) | Ghi số đo vào P0-10; giữ 50 rps/burst 100 (hơn 10 lần đỉnh theo phút), `/auth/*` chặt hơn. Đổi sang rate-limit theo IP cộng backoff theo user. §7 #14 |
| 12 | Việc XS thiếu lệnh cụ thể | — | Thêm §8.4, lệnh một dòng, ghi rõ Nghiệp chạy tay |
| 13 | Cô lập tenant fail-open, Redis không AUTH, phải là P0 | `aa544_tenant_pool.py:146-158`; `describe-cache-clusters` [QS] | Thêm P0-8 (trước tenant đầu tiên), cập nhật §2 |
| 15 | AA-817 bị xếp thấp; app không tách mạng | DM-6.8 dòng 214; 3 service chung `sg-038383acb15660582`, nguồn ingress duy nhất của SG RDS/Redis [QS] | Đưa vào P0-9 cùng SG riêng và isolation probe |
| 16 | Đường truy cập dữ liệu production không log | `enableExecuteCommand=true` ×3, cluster `configuration=null`, không pgaudit, `log_connections` mặc định [QS] | Thêm P0-12; sửa dòng AWS trong bảng §5.8 (ECS exec chỉ khi đã bật log); P2-11 |
| 17 | Thiếu DSAR, RoPA, đánh giá chuyển dữ liệu ra nước ngoài; snapshot thủ công không hạn | DM-6.7 dòng 213; 4 snapshot thủ công [QS] | P0-13 thêm RoPA, DSAR runbook, hồ sơ chuyển dữ liệu; P1-8 phần kỹ thuật; P0-11 hạn snapshot |
| 18 | Audit trail ngắn hạn, sửa được | `IsMultiRegionTrail=false`, `KmsKeyId=null`, không CloudWatch; bucket không versioning [QS] | P1-7 mở rộng (Object Lock, giữ 365 ngày, audit event schema) |
| 19 | Bên thứ ba kiểm soát acc2 | `describe-organization`: management `033086823579`, `FeatureSet=ALL` [QS]. Không kiểm được role (hook chặn `aws iam`) | P0-12 bước 3, lệnh ở §8.4; TrueIDC vào danh sách sub-processor; giới hạn ghi ở §5.2 và §7 #12 |
| 20 | Agent đọc được key tĩnh và cache STS | 5 section trong `~/.aws/credentials`, 11 file cache [QS, chỉ đếm tên] | P0-3: deny đọc `~/.aws/**`, `~/.config/gh/**`; P2-13 SSO/aws-vault, devcontainer. §1 và §3 sửa câu "không có AWS key tĩnh" thành "trong CI" |
| 21 | Secret god-key và E2E ở mức repo trên repo public | `gh api …/actions/secrets` [QS] | P0-1 bước 4: chuyển `ADMIN_SECRET` vào env `dev` main-only rồi xoay. E2E: xem điểm bác bỏ một phần ở §9.2 |
| 22 | Frontend thiếu security header; thiếu pentest | `curl -sI …/login` [QS] | P0-10 bước 5, check trên preview ở P1-4, pentest ở P2-12 |
| 23 | Khung "Dev = prod" chưa nhất quán; OIDC được khen quá; thiếu hostname Booking OpenAPI | `api-booking…/booking/openapi.json` 200 (110.749 byte), `api-cis…/booking/openapi.json` 403 [QS] | Thêm câu phạm vi ở §1; sửa điểm mạnh OIDC; ghi đúng host ở P0-10 |
| 24 | Dependabot tắt ở Infra; `AA-ACP-App` chưa quét; pip-audit luôn qua | 403 trên Infra; `security_and_analysis` của AA-ACP-App [QS] | P0-4 bước 2–3; P0-7 nêu thiếu bằng chứng quản lý lỗ hổng; §5.3 thêm export định kỳ |

### 9.2 Bác bỏ hoặc chấp nhận một phần

| Phản biện | Lý do |
|---|---|
| (5) "AWS STS chỉ hỗ trợ `aud`, `sub` (và `amr`) cho OIDC; điều kiện `job_workflow_ref` có thể không làm được; phải đổi template `sub`, có nguy cơ tự khoá" | **Bác bỏ phần dữ kiện.** Tài liệu IAM của AWS (mục "Available keys for AWS OIDC federation", tab GitHub) [QS] liệt kê `token.actions.githubusercontent.com:ref`, `:job_workflow_ref`, `:environment`, `:repository_id`, `:actor_id`… làm condition key. Vì vậy **không cần đổi template `sub`**, không có rủi ro tự khoá do đổi sub. **Chấp nhận phần quy trình:** P0-1 dùng điều kiện `ref` (đơn giản hơn `job_workflow_ref`), thử trên role nháp trước, và giữ phương án dự phòng "bỏ `environment` ở job apply, trust `…:ref:refs/heads/main`" của phản biện |
| (22) "Không có HSTS trên `/login`, chỉ có trên `/`" | **Sai một phần.** `curl -sI https://aa-cis.lumiguides.it.com/login` trả `strict-transport-security: max-age=63072000` [QS]. Phần còn lại (thiếu CSP, X-Frame-Options, nosniff, Referrer-Policy) đúng và đã đưa vào P0-10 |
| (21) "Chuyển E2E creds và Vercel bypass secret vào env main-only" | **Chấp nhận cho `ADMIN_SECRET`, bác bỏ cho E2E/bypass.** `ui-smoke.yml` chạy theo `deployment_status` trên preview của mọi PR (`ui-smoke.yml:5-7`) và đọc 3 secret đó (`:36-38`). Env main-only sẽ làm gãy UI smoke, cổng mà P1-4 và vòng lặp Kiro dựa vào. Thay bằng: tài khoản E2E chỉ đọc, không thấy PII (P1-2), ghi là rủi ro chấp nhận ở P0-1 |
| (3) "Ước tính Giai đoạn 0 là 3–4 tuần part-time" | **Chấp nhận một phần.** P0-A khoảng 1 tuần. P0-B sau khi thêm các mục của vòng phản biện 2 (P0-8, P0-9, P0-12) khoảng 15–20 ngày công, tức 4–6 tuần part-time. Mốc chặn là ngày ký tenant đầu tiên, không phải số tuần |
| (15) "Mọi app một SG riêng" ngay | Chấp nhận, nhưng đặt trong P0-B (trước tenant) chứ không P0-A, vì cần Terraform và deploy lại 3 service |
| (16) "Tắt ECS Exec mặc định ngay" | **Chấp nhận một phần.** Tắt ngay sẽ làm gãy luồng hằng ngày (skill `aa-cis-schema`, verify). Bật log phiên ngay (P0-12), chuyển sang break-glass ở P2-11 khi đã có workflow thay thế |
