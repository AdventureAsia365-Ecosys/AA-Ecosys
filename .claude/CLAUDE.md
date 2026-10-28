# AA-Ecosys Workspace — Claude Code Context
# Updated: 19/10/2026 (S243, AA-889: Booking live, ACP repos, endpoints, merge rule per S241 D-13; X1 S18/S19 DB access)

## WORKSPACE STRUCTURE
~/projects/AA-Ecosys/            (repo gốc, PUBLIC tạm thời từ 22/10/2026 — ADR 0014 amendment, default branch master)
├── apps/
│   ├── AA-CIS-App/          → FastAPI api (gồm Content studio API `/v1/*`) + job worker (ECS), admin (Vercel); `portal/` là bản copy đóng băng, không deploy (AA-979) — public repo
│   ├── AA-Booking/          → Booking back office: FastAPI + asyncpg + booking.job worker (ECS, cùng cluster CIS), staff admin (Vercel) — public repo, live từ S235
│   ├── AA-TripPlanner-Web/  → B2C map-first trip planner (Next.js FE + 2 Lambda) — public repo
│   └── AA-Partner/          → CRM cho đại lý đối tác: api (chạy cả crm.job worker trong process) + web (ECS ARM64, cùng cluster CIS), tenant portal / Content studio (Vercel `aa-cis-portal`, từ AA-979) — public repo
├── infra/
│   └── AA-CIS-Infra/        → Terraform ECS/RDS/Lambda/API GW/Cognito, DB Migrate, DB Schema Dump (see infra/AA-CIS-Infra/.claude/CLAUDE.md)
├── docs/                    → tài liệu cấp hệ; điểm vào theo vai trò + catalog: docs/README.md; trang cũ: docs/archive/
└── skill/

# Org GitHub: AdventureAsia365-Ecosys (đổi tên từ AdventureAsia365-CIS).
# AA-ACP-App: ĐÃ XOÁ hẳn (S241, AA-867). AA-ACP-Core: archived, private, giữ nguyên (S241) — cả hai không còn trong workspace.
# Repo app public → KHÔNG ghi account ID, ARN, SG/VPC ID, inventory, báo cáo bảo mật vào repo app (DM-6.10, D-25); để ở repo gốc / Infra.

## AWS — CIS ACCOUNT (account map, confirmed live via sts get-caller-identity, AA-517 02/09/2026; acc1 gỡ khỏi hệ sinh thái AA-998 28/10/2026)

| Vai trò | Account | Region | Profile |
|---|---|---|---|
| **Acc2 — hạ tầng chính** (RDS/ECS/S3/Lambda thật, DUY NHẤT chứa hạ tầng) | 005097885195 | us-west-1 | `aa365-admin` |
| **Acc3 — LLM satellite** (Bedrock chat models; DUY NHẤT ngoài acc2 dùng cho LLM) | 786888028788 | us-west-1 | `nghiep_aa365` |
| Acc1 — tài khoản CÁ NHÂN của Nghiệp, **ĐÃ GỠ khỏi hệ sinh thái** (AA-998, S255) | 867490540162 | — | `pqnghiep-admin` (chỉ việc cá nhân) |

LLM chỉ chạy trên **acc3** (Bedrock satellite) + các model Bedrock native acc2 đang dùng hôm nay (vd. Cohere Embed v4).
Không còn fallback chéo account: acc3 lỗi → fallback model cùng acc3 / job retry (Nghiệp chấp nhận, AA-998).
KHÔNG tạo resource, deploy, ghi secret hay route LLM vào acc1; không thêm lại acc1 vào code/Terraform/catalog.

Always verify: aws sts get-caller-identity --profile aa365-admin

**`default` CLI profile = acc2** since AA-517 (02/09/2026) — trước đó `default` trỏ acc1 bằng
static key, là nguyên nhân gốc của 2 lần ghi nhầm Secrets Manager (22/05, 25/08/2026). Đã đổi
`default` để assume cùng role với `aa365-admin` (dùng chung STS cache 8h). Key acc1 cũ đổi tên
`[acc1-legacy-default]` trong `~/.aws/credentials`; không dùng cho việc hệ sinh thái (AA-998: access key tĩnh đã Inactive).

History: account 1 (867490540162) — compute/network hạ tầng CŨ đã xoá 09/07/2026
(AA-271, acc1-destroy-v3.tfplan); sau đó giữ làm Bedrock satellite FALLBACK (ADR-2026-022 amended, AA-296,
role AA-Bedrock-Invoker, root Terraform `accounts/acc1-bedrock` từ S235). AA-517 (02/09/2026): dọn 1 RDS
snapshot lạc + 20 Secrets Manager secrets lạc trên acc1 (nguyên nhân: `default` profile từng trỏ acc1).
**AA-998 (S255, 28/10/2026): acc1 gỡ khỏi hệ sinh thái** — code CIS/TripPlanner/Infra bỏ mọi đường gọi acc1,
root `accounts/acc1-bedrock` đã destroy cùng bucket state, tài nguyên sót đã xoá (kiểm kê lại 28/10: 0 role/bucket/Lambda/secret us-west-1; thư mục root còn trong Infra, chờ xoá); quyết định: ADR 0001a (`docs/adr/0001a-retire-acc1-llm-on-acc3-only.md`).

## LIVE ENDPOINTS (Dev, kiểm 19/10/2026)
CIS API:       <https://api-cis.lumiguides.it.com>      (API Gateway REST → VPC link → ALB → ECS; `/health` 200)
CIS frontend:  <https://aa-cis.lumiguides.it.com>       (Vercel)
Booking API:   <https://api-booking.lumiguides.it.com>  (REST API riêng, cùng VPC link; `/booking/health` 200)
Booking admin: Vercel project `aa-booking-admin`
Staff sign-in: Cognito WORKFORCE, managed login <https://staff-auth.lumiguides.it.com> (ADR 0006/0006a)
ID của API Gateway / pool / SG: KHÔNG chép vào đây (đổi được) — tra bằng lệnh 1 dòng hoặc Terraform output.

## RESOURCES
ECS cluster: aa-cis-dev-cluster | services: aa-cis-dev-api, aa-cis-dev-worker, aa-booking-dev-api, aa-crm-dev-api, aa-crm-dev-web
ECR: aa-cis-dev-api (tag `dev-<git sha>`, AA-869), aa-booking-dev-api (tag = git SHA) — cả hai IMMUTABLE; không dùng `:latest`
RDS: aa-cis-dev-db (PostgreSQL 15, db.t4g.small) | DSN secrets: aa-cis/dev/rds (master — từ X1 S18/S19, 19/10/2026: KHÔNG còn là login runtime CIS, task role CIS bị Deny đọc secret này), mỗi app một secret riêng — danh sách: docs/security/secrets-register.md (AA-878)
DB từ ECS exec: script dùng `DATABASE_URL` của container (= `cis_app`: schema CIS kể cả bảng RLS, không `booking.*`/`tripplanner.*`, không DDL); việc cần master → DB Migrate `mode=run-script` (docs/ops/runbooks/ecs-exec-s3-mediated.md)
S3 scripts bucket: aa-cis-bronze-005097885195

## ACTIVE WORK
Bốn app trên acc2: AA-CIS-App, AA-TripPlanner-Web, AA-Booking, AA-Partner.
Kiến trúc & lộ trình: docs/ecosystem-architecture.md, docs/adr/ (0001–0008), data standards docs/architecture/data-standards/,
backlog sống docs/backlog/README.md.
Trạng thái phiên: memory Notion (Program Brain/memory.md) + docs/sessions/. Không ghi số ECS/issue cứng ở đây.

## Git Rules — NON-NEGOTIABLE
- ADR-2026-023 (trunk-based): không có `develop`. Branch feature/fix → PR → CI bắt buộc → squash merge thẳng vào
  `main` (repo gốc: `master`). Bắt đầu: tạo branch/worktree từ `origin/main` mới nhất, không sửa trên checkout chính.
- **Quyền merge theo giai đoạn (S241 D-13, data standards DM-11.5 — v1.1, Nghiệp duyệt S243 (N-1)):**
  - **Giai đoạn dev (bây giờ):** phiên agent điều phối TỰ merge PR của mình khi CI xanh — kể cả PR bảo mật/hạ tầng —
    rồi deploy, verify live, báo cáo (memory `dev-phase-self-merge`). Subagent KHÔNG merge (hook
    `.claude/hooks/subagent-guardrails.sh` chặn). Thay đổi rủi ro (auth/quyền, migration/schema, CI/workflow/secret,
    xoá dữ liệu) → cho agent review trước (`kiro-reviewer` theo `kiro-delegate`, hoặc subagent review độc lập).
  - **Từ prod đầu tiên hoặc tenant trả tiền đầu tiên:** Nghiệp duyệt trước khi merge mọi PR Terraform/IAM, migration DB,
    auth/bảo mật, xoá dữ liệu. PR app khác: agent merge khi CI xanh.
- Agent điều phối push / mở PR / merge bằng GitHub App `aa-agent` qua `tools/github/as-app.sh` (ADR 0011, S247; cách
  gọi: `skill/aa-ship` §1). Subagent vẫn không push, không merge (hook chặn lệnh, không phụ thuộc danh tính).
- Không merge/deploy backend khi bảng job còn job hoặc đang có wave (DM-11.4); "Done" theo `skill/aa-ship/SKILL.md`.
## KIRO STEERING RULES — BẮT BUỘC (import, added 24/09/2026)
Nguồn sự thật duy nhất là `.kiro/steering/` (dùng chung Kiro + Claude Code) — import trực tiếp để
không lệch nhau; sửa quy tắc thì sửa file steering, KHÔNG chép lại vào đây.

@../.kiro/steering/session-workflow.md
@../.kiro/steering/language-convention.md
@../.kiro/steering/db-schema.md

### Chế độ "dùng kiro-cli" (Nghiệp chốt 09/10/2026, S219)
- Chỉ bật khi Nghiệp mở phiên bằng **"bắt đầu session mới, dùng kiro-cli"** (hoặc bảo bật rõ giữa phiên). Không có câu đó → Claude tự viết code như thường, không gọi Kiro.
- Bật thì: chạy preflight (`.claude/skills/kiro-delegate/kiro-preflight.sh`) ngay đầu phiên và trước mỗi task; báo credit Kiro trong khối trạng thái đầu phiên. Preflight lỗi / credit thấp → **báo Nghiệp** và **chuyển về Claude viết code** cho phần còn lại của phiên.
- Quy trình chi tiết (v3, S221 — phân việc Kiro/Claude, brief ngắn trỏ Linear, Kiro tự lặp tới khi CI + UI smoke trên preview xanh, Claude gác cổng, reviewer chỉ khi rủi ro; S222: mỗi phiên 3–5 issue): skill `kiro-delegate`.

### Điều chỉnh khi chạy trong Claude Code (thay phần đặc thù Kiro)
- Notion/Linear: dùng connector **claude.ai Notion / claude.ai Linear** (không phải `.kiro/settings/mcp.json`).
  Nếu connector không có trong phiên → nói rõ với Nghiệp, không tự đoán state.
- `control_bash_process` / `get_process_output` (Kiro) → Bash `run_in_background` / Monitor; vẫn giữ quy tắc
  "chờ 1 khoảng dài, kiểm 1 lần" khi chờ CI/deploy.
- File scratch: dùng `.tmp-session/` trong workspace hoặc scratchpad của Claude Code — không ghi ra `~/`.
- Git từ PowerShell/UNC path báo "dubious ownership" → chạy git qua WSL (`wsl -- bash script.sh`).
- Session log ghi rõ **Tác nhân: Claude Code**.
