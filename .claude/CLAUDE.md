# AA-Ecosys Workspace — Claude Code Context
# Updated: 15/09/2026 (restructure: gom AA-Ecosys, đổi tên org → AdventureAsia365-Ecosys)

## WORKSPACE STRUCTURE
~/projects/AA-Ecosys/
├── apps/
│   ├── AA-CIS-App/          → FastAPI backend + LangGraph pipeline (see apps/AA-CIS-App/.claude/CLAUDE.md)
│   └── AA-TripPlanner-Web/  → B2C map-first trip planner (Next.js FE + 2 Lambda)
├── infra/
│   └── AA-CIS-Infra/        → Terraform ECS/RDS/Lambda/API GW (see infra/AA-CIS-Infra/.claude/CLAUDE.md)
├── docs/                    → tài liệu cấp hệ (ecosystem-architecture, handoff AAA, inventory)
└── skill/

# Org GitHub: AdventureAsia365-Ecosys (đổi tên từ AdventureAsia365-CIS).
# AA-ACP-App / AA-ACP-Core: ĐÃ ARCHIVE + XOÁ (26/08/2026, AA-467) — không còn trong workspace.
# Sắp có: AA-Booking (AAA) — xem docs/tripplanner-to-aaa-handoff.md.

## AWS — CIS ACCOUNT (3-account map, confirmed live via sts get-caller-identity, AA-517 02/09/2026)

| Vai trò | Account | Region | Profile |
|---|---|---|---|
| **Acc2 — hạ tầng chính** (RDS/ECS/S3/Lambda thật, DUY NHẤT chứa hạ tầng) | 005097885195 | us-west-1 | `aa365-admin` |
| Acc1 — LLM satellite FALLBACK (AA-296) | 867490540162 | us-west-1 | `pqnghiep-admin` |
| Acc3 — LLM satellite CHÍNH | 786888028788 | us-west-1 | `nghiep_aa365` |

Always verify: aws sts get-caller-identity --profile aa365-admin

**`default` CLI profile = acc2** since AA-517 (02/09/2026) — trước đó `default` trỏ acc1 bằng
static key, là nguyên nhân gốc của 2 lần ghi nhầm Secrets Manager (22/05, 25/08/2026). Đã đổi
`default` để assume cùng role với `aa365-admin` (dùng chung STS cache 8h). Key acc1 cũ vẫn giữ,
đổi tên `[acc1-legacy-default]` trong `~/.aws/credentials`, không xoá.

History: account 1 (867490540162) — compute/network hạ tầng CŨ đã xoá 09/07/2026
(AA-271, acc1-destroy-v3.tfplan), NHƯNG account vẫn ACTIVE, giữ lại có chủ đích
(ADR-2026-022, amended) để chạy Bedrock cross-account satellite pattern (role
AA-Bedrock-Invoker, dùng bởi AA-296 — xem shared/llm_client/bedrock_satellite.py
trong AA-CIS-App). KHÔNG coi account này là "đã đóng" khi audit/plan hạ tầng mới.
TODO/tech debt: AA-Bedrock-Invoker hiện tạo TAY, KHÔNG nằm trong Terraform state
— cần import hoặc tái tạo qua IaC khi có thời gian.
AA-517 (02/09/2026): dọn 1 RDS snapshot lạc + 20 Secrets Manager secrets lạc trên acc1 (nguyên
nhân: `default` profile từng trỏ acc1) — xem memory `project_aa517_acc1_orphan_cleanup`.

## LIVE ENDPOINTS
API:      https://api-cis.lumiguides.it.com  (API GW 4ylo382khg → ECS — corrected 22/08/2026,
          AA-432; `owq9as3wjl` was stale/no longer exists, confirmed via AWS CLI)
Frontend: https://aa-cis.lumiguides.it.com   (Vercel)

## RESOURCES
ECS cluster: aa-cis-dev-cluster | service: aa-cis-dev-api
RDS: aa-cis-dev-db (PostgreSQL 15) | secret: aa-cis/dev/rds
S3 scripts bucket: aa-cis-bronze-005097885195

## ACTIVE PROJECT — ACP
Linear project: ACP | Active sprint: M2 | Session: 22 (closed)
AA-45: Done ✅ | ECS api:151 | AWS: STOPPED
P0: AA-89 (B2B self-approval, migration 021)
HIGH: AA-90 (S1 trigger page), AA-43 (S2 LangGraph)
PENDING INFRA: Lambda aa-cis-dev-acp-s3-campaign-planner + migration 031 (Session 23)

## Git Rules — NON-NEGOTIABLE
- ADR-2026-023 (trunk-based, effective 09/07/2026): `develop` branch REMOVED in all 3 repos
  (AA-CIS-App, AA-ACP-App, AA-CIS-Infra). Work on a feature/fix branch → PR → CI required → merge
  straight to `main` (human-only, via PR review).
- DO NOT merge to main yourself — human does that manually after CI green
- Before starting: git checkout main && git pull origin main
## KIRO STEERING RULES — BẮT BUỘC (import, added 24/09/2026)
Nguồn sự thật duy nhất là `.kiro/steering/` (dùng chung Kiro + Claude Code) — import trực tiếp để
không lệch nhau; sửa quy tắc thì sửa file steering, KHÔNG chép lại vào đây.

@../.kiro/steering/session-workflow.md
@../.kiro/steering/language-convention.md

### Điều chỉnh khi chạy trong Claude Code (thay phần đặc thù Kiro)
- Notion/Linear: dùng connector **claude.ai Notion / claude.ai Linear** (không phải `.kiro/settings/mcp.json`).
  Nếu connector không có trong phiên → nói rõ với Nghiệp, không tự đoán state.
- `control_bash_process` / `get_process_output` (Kiro) → Bash `run_in_background` / Monitor; vẫn giữ quy tắc
  "chờ 1 khoảng dài, kiểm 1 lần" khi chờ CI/deploy.
- File scratch: dùng `.tmp-session/` trong workspace hoặc scratchpad của Claude Code — không ghi ra `~/`.
- Git từ PowerShell/UNC path báo "dubious ownership" → chạy git qua WSL (`wsl -- bash script.sh`).
- Session log ghi rõ **Tác nhân: Claude Code**.
