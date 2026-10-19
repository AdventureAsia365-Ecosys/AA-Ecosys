---
id: GUIDE-03
title: Glossary
description: Delivery, operations, data and AA-Ecosys terms with their Vietnamese equivalent and where each shows up in our system.
type: reference
status: active
owner: nghiep
audience: [owner, engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 180
related: [CAT-00, TPL-02]
---

# Glossary

Terms used across AA-Ecosys docs, with the Vietnamese term (VI) for readers who prefer it. Built from the S243
SDLC guide §8 and extended with program terms. Use the English term in technical docs and keep it the same
everywhere ([STYLE](STYLE.md#voice-and-structure)). Add a term in the same PR that first uses it.

## Process and delivery

| Term | Tiếng Việt | Meaning | In AA-Ecosys |
|---|---|---|---|
| SDLC | Vòng đời phát triển phần mềm | The life of software from idea to retirement. | Plan, build, verify, release, operate, retire. |
| ADLC | Vòng đời phát triển có agent | Our name for the SDLC plus control of AI agents and the life cycle of LLM features. | Kiro or a subagent writes code, Claude Code gates; writer/judge prompts have evals. |
| Trunk-based development | Phát triển trên một nhánh chính | Short branches merged often into one always-deployable branch. | `main` in the app and Infra repos, `master` in root (ADR-2026-023). |
| Pull request (PR) | Yêu cầu gộp code | A proposed change where review and CI run. | Squash merge, body carries `Refs AA-xxx`. |
| CI (continuous integration) | Tích hợp liên tục | Build and test every change automatically. | CIS `ci.yml`: Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check. |
| CD (continuous delivery / deployment) | Triển khai liên tục | Ship a change that passed CI to an environment automatically. | `deploy-dev.yml` (CIS), `deploy-lambdas.yml` (TripPlanner). |
| Required checks / branch protection | Kiểm tra bắt buộc / bảo vệ nhánh | Checks that must be green before a merge. | Five required jobs on AA-CIS-App; private repos on GitHub Free have none. |
| Deploy gate | Cổng chặn deploy | CI step that blocks a backend deploy while background jobs run. | `shared.job` queued/running blocks CIS deploy; override is Nghiệp's call. |
| Definition of Ready (DoR) | Điều kiện sẵn sàng | What an issue needs before work starts. | [`templates/definition-of-ready.md`](templates/definition-of-ready.md). |
| Definition of Done (DoD) | Điều kiện hoàn thành | What must be true to call work done. | `skill/aa-ship`: merged, CI green, rollout COMPLETED, verified live. |
| Kanban | Kanban | Pull work from one ordered queue with a work-in-progress limit, no sprints. | The live backlog plus sessions of 3 to 5 issues. |
| Change record | Hồ sơ thay đổi | The written trace of a change, its risk and its rollback. | The PR itself; risky classes get `kiro-reviewer`. |
| DORA metrics | Chỉ số DORA | Deploy frequency, lead time, recovery time, change-fail rate, rework rate. | Later (U-47, at first prod). |

## Versions and releases

| Term | Tiếng Việt | Meaning | In AA-Ecosys |
|---|---|---|---|
| Conventional Commits | Chuẩn commit quy ước | Commit subject format `type(scope)!: subject`. | `fix: excel price mapping`, body `Refs AA-26`. |
| SemVer | Đánh version ngữ nghĩa | `MAJOR.MINOR.PATCH` by compatibility. | Planned app versions (AA-891). |
| CalVer | Đánh version theo ngày | Version by date. | Optional for Infra. |
| Git tag | Nhãn git | A fixed label on one commit. | None yet; first tags with AA-891. |
| GitHub Release | Bản phát hành GitHub | A page for a tag with notes and artifacts. | Created by release-please (AA-891). |
| CHANGELOG | Nhật ký thay đổi | Human-readable list of changes per version. | `CHANGELOG.md` per repo (AA-891). |
| Release note | Ghi chú phát hành | Business summary of a release. | Jira draft for Ms. Thư, [template](templates/release-note.md). |
| release-please | release-please | Bot that opens a release PR with the version bump and changelog and tags on merge. | AA-891 (U-47, pulled early). |
| Immutable image tag | Tag image bất biến | An image tag that cannot be overwritten. | ECR `dev-<sha>`, IMMUTABLE, last 30 kept (CIS). |
| Task definition revision | Bản task definition | A numbered ECS run configuration. | Rollback points the service at the previous revision (`skill/aa-ship` §5). |
| Rolling deploy | Triển khai cuốn chiếu | Replace tasks gradually. | ECS default for CIS and Booking. |
| Circuit breaker (ECS) | Cầu dao tự lùi | ECS stops and rolls back a deploy whose tasks do not become healthy. | Enabled on the ECS services in Terraform. |
| Blue/green, canary | Xanh/lục, canary | Switch traffic between two stacks / shift a percentage gradually. | Not needed yet. |
| Rollback / roll-forward | Lùi bản / sửa tiến | Return to the previous version / ship a fix. | `skill/aa-ship` §5; rollback runbooks (OPS-02). |
| Build once, deploy many | Build một lần, chạy nhiều nơi | One artifact, same digest in every environment; only config differs. | `dev-<sha>` image, later promoted to prod. |
| Feature flag | Cờ tính năng | Switch a feature without a deploy. | Register in `docs/ops/feature-flags.md` (OPS-06); tenant-pool flags are a security control. |
| Deploy vs release | Triển khai và phát hành | Code running vs users seeing it. | Turn a flag on for one tenant first. |
| Expand / contract | Mở rộng / thu hẹp | Change a schema or API in three steps so old and new run together. | Migrations and contract versions. |
| Breaking change | Thay đổi phá tương thích | A change that breaks existing clients. | Removing a response field; caught by oasdiff (AA-899). |
| OpenAPI | OpenAPI | Machine-readable REST API spec. | `/booking/openapi.json`; export for CIS and Booking in AA-899. |
| Deprecation / Sunset header | Header báo ngừng | HTTP headers that announce an API is going away and when. | RFC 9745 / RFC 8594; with ADR 0013 (U-44). |

## Documentation

| Term | Tiếng Việt | Meaning | In AA-Ecosys |
|---|---|---|---|
| Docs-as-code | Tài liệu như code | Docs in the repo, changed in the same PR, checked by CI. | This catalog; lint in AA-888. |
| Diátaxis | Diátaxis | Four doc types: tutorial, how-to, reference, explanation. | The `type` field of the [front-matter](templates/frontmatter.schema.json). |
| Doc catalog | Danh mục tài liệu | The list of every maintained doc, owner and cadence. | [`docs/README.md`](README.md). |
| Front-matter | Phần đầu trang | YAML block at the top of a page with its metadata. | Required: id, title, type, status, owner, last_reviewed. |
| Runbook / playbook | Sổ tay vận hành / kịch bản xử lý | Exact steps for one task / strategy for one kind of incident. | `docs/ops/runbooks/`, `docs/ops/playbooks/`. |
| ADR | Bản ghi quyết định kiến trúc | Context, decision and consequences of an architecture choice. | `docs/adr/` (root), app and Infra repos. |
| CONTEXT.md | CONTEXT.md | Per-repo page on stack, boundaries and ownership; read before designing. | CIS, Booking, TripPlanner, Infra. |
| C4 model | Mô hình C4 | Architecture diagrams at four zoom levels; we use L1 context and L2 containers. | `ecosystem-architecture.md`. |
| llms.txt | llms.txt | A Markdown index that tells AI agents what to read. | [`docs/llms.txt`](llms.txt). |
| Freshness | Độ tươi tài liệu | Whether `last_reviewed` is inside `review_every_days`. | Weekly report with AA-888. |
| Postmortem (blameless) | Phân tích sau sự cố | Incident analysis without blame, ending in action items. | [`templates/postmortem.md`](templates/postmortem.md); lesson line in `lessons.md`. |

## Infrastructure and operations

| Term | Tiếng Việt | Meaning | In AA-Ecosys |
|---|---|---|---|
| acc1 / acc2 / acc3 | Tài khoản 1 / 2 / 3 | The three AWS accounts. | acc2 = all infrastructure; acc3 = main LLM satellite; acc1 = LLM fallback. Map: [onboarding](onboarding.md#account-map). |
| Infrastructure as Code (IaC) | Hạ tầng dạng code | Infrastructure declared in code. | Terraform in AA-CIS-Infra. |
| Terraform state / lock file | Trạng thái / file khoá Terraform | Record of real resources / pinned provider versions. | Remote state on S3; `.terraform.lock.hcl`. |
| Terraform drift | Lệch hạ tầng | Real infrastructure differs from code or state. | Apply only from `main` through `terraform-apply.yml`. |
| OIDC (CI to AWS) | Đăng nhập liên kết OIDC | CI gets short-lived AWS credentials without static keys. | Trust limited to `refs/heads/main` (AA-866). |
| ECS exec, S3-mediated | ECS exec qua S3 | Run a script inside the CIS container: upload to S3, presign, curl it in, run with python3. | The standard way to reach the private RDS (D-07); sessions are logged. |
| Break-glass | Lối khẩn cấp | An emergency credential or switch used only when normal access fails. | Cognito `breakglass` user with TOTP; RDS master (DM-8.9). Runbook OPS-10. |
| Observability | Khả năng quan sát | Understanding the system through logs, metrics and traces. | CloudWatch, Sentry (CIS), admin pages. |
| Log retention | Thời gian giữ log | How long logs are kept. | Security logs (flow, WAF, ECS exec, PostgreSQL) 365 days, app logs 30 days (D-09, AA-872). |
| SLI / SLO / SLA / error budget | Chỉ số / mục tiêu / cam kết / ngân sách lỗi | Measure / target / contract / allowed failure share. | SLOs with first prod (AA-880, U-49). |
| RPO / RTO | Mất dữ liệu tối đa / thời gian dừng tối đa | Acceptable data loss / downtime. | Targets in DM-9.6; Dev restore drill took about 22 minutes (S241). |
| PITR | Khôi phục theo thời điểm | Restore a database to any moment in its retention window. | Dev RDS keeps 7 days; prod will keep 14 (C7.2b). |
| Restore drill | Diễn tập khôi phục | Practice restore with a recorded RTO. | Dev: when the procedure changes and once before prod; quarterly in prod (DM-9.3). |
| FinOps / unit cost | Quản trị chi phí / chi phí đơn vị | Managing cloud spend / cost per business unit. | USD LLM per published tour; monthly review (FIN-02). |
| Cost allocation tag | Tag phân bổ chi phí | A tag Cost Explorer can split spend by. | `App` and `Environment` (DM-10.1); Nghiệp activates them in Billing. |
| Ledger | Sổ ghi chi phí | A table that records every paid call with its cost. | `shared.llm_call_log`, `shared.decision_log`, `shared.dfs_call_log` (DM-10.4). |
| SBOM | Danh mục thành phần phần mềm | List of every library and version in an artifact. | syft in CIS CI (AA-177). |
| SLSA / provenance | SLSA / nguồn gốc build | Supply-chain trust levels / proof of who built what from which commit. | Later (U-43, first prod). |

## Data

| Term | Tiếng Việt | Meaning | In AA-Ecosys |
|---|---|---|---|
| Migration | Migration (thay đổi cấu trúc DB) | A numbered SQL file that changes the schema. | Keys `NNN` (CIS), `tp-NNN`, `bk-NNN`; applied by Infra DB Migrate. |
| Forward-only | Chỉ tiến | Never roll a schema back; undo with a new migration. | DB Migrate rule; the old app must run on the new schema. |
| Idempotent | Chạy lại không đổi kết quả | Running twice has the same effect as once. | `ON CONFLICT DO NOTHING` in `schema_versions`. |
| Schema owner | Chủ schema | The only repo that writes migrations and rows for a schema. | [`schema-ownership.md`](database/schema-ownership.md); registry `db/owners.yaml` in Infra. |
| Kernel schema | Schema lõi dùng chung | `shared`: tenants, destinations, countries, LLM gateway, `schema_versions` only. | DM-1.5; app tables go to the owner's schema. |
| Contract (event / API / view) | Hợp đồng dữ liệu | Versioned interface between apps. | `docs/contracts/`, `catalog.*` views (ADR 0008). |
| RLS | Bảo mật mức dòng | PostgreSQL row-level security that filters rows per tenant. | Tenant pool and isolation probe (AA-817, U-16). |
| Tenant pool | Pool kết nối theo tenant | DB connection pool whose role is bound by RLS. | Fail-closed globally (D-12). |
| Dead Table Registry | Danh sách bảng chết | Tables kept but no longer written, with their removal plan. | ARCH-09 (AA-850). |
| PII | Dữ liệu cá nhân | Data that identifies a person. | Dev holds test data only (D-01); `pii:` column tags (AA-877). |

## LLM operations

| Term | Tiếng Việt | Meaning | In AA-Ecosys |
|---|---|---|---|
| LLMOps | Vận hành LLM | Versioning prompts and models, evals, quality and cost monitoring. | APP-06 (AA-900, narrowed). |
| Model Gateway | Cổng gọi model | The single seam for paid model calls. | `LLMClient.generate()` writes `shared.llm_call_log`. |
| Writer / judge / validate | Người viết / người chấm / kiểm | The three LLM roles in the pipeline. | `role` in `shared.llm_call_log`. |
| Eval / golden set | Đánh giá / bộ mẫu chuẩn | A fixed sample to score LLM quality before changing a prompt or model. | About 100 samples (AA-729); runs by hand or dispatch (D-23). |
| Shadow run | Chạy song song | Run a new model or route next to the live one without serving its output. | `shared.llm_shadow_log`. |
| Jev | Jev | The external decision service that gives verdicts on content. | `decide()` writes `shared.decision_log`. |
| Atom | Atom | A reusable piece of tour content produced by the A-series pipeline. | Read through `acp_contract.v_active_tour_atoms`. |
| A-series / T-series | Chuỗi A / chuỗi T | Admin pipeline stages A0-A4 / tenant stages T0-T11. | CIS CONTEXT.md. |

## Program and governance

| Term | Tiếng Việt | Meaning | In AA-Ecosys |
|---|---|---|---|
| Dev phase | Giai đoạn Dev | Today: only a Dev environment, no real users, test data only. | Agents merge after green CI (D-13; DM-11.5 text update pending v1.1). |
| Prod | Môi trường prod | The future production environment. | Separate RDS instance on acc2 (ADR 0001, C7.2a, D-17); dated at go-live (AA-880). |
| Data standards | Chuẩn dữ liệu | Binding DM-x (Part B) and C-x (Part C) rules for the shared RDS. | `docs/architecture/data-standards/` v1.0; v1.1 pending (N-1). |
| U-xx / D-xx | Mục lộ trình / quyết định | S241 roadmap items / Nghiệp's recorded decisions. | `docs/audits/2026-10-17-S241-sdlc-review/unified-roadmap.md`, `docs/sessions/2026-10-17-S241-decisions.md`. |
| Session (S<nnn>) | Phiên làm việc | One numbered working session with a log. | `docs/sessions/`, Notion memory. |
| CODEOWNERS | CODEOWNERS | GitHub file that assigns required reviewers by path. | Later, needs a separate agent identity (U-25). |
| NIST SSDF (SP 800-218) | Khung phát triển an toàn NIST | Secure software development practices in four groups. | Reading checklist, later. |
| Workforce pool | Pool nhân viên | The Cognito user pool for staff sign-in. | CIS staff sign in with an e-mail code (ADR 0006a). |
