---
name: ai_nghiep
description: Personalization skill for working with Nghiep on the AA_Ecosys program. Trigger on any question related to AA-CIS, AAA, ACP, AWS, CI/CD, FastAPI, PostgreSQL, LangGraph, Bedrock, or architecture decisions within AA_Ecosys. Applies working style rules, AWS patterns, session rituals, techstack decision framework, English review format, and ADR tracking automatically — without being asked.
---

# ai_nghiep.md — Claude Skill: Làm việc với Nghiep (AA_Ecosys)

> **Mục đích**: File này là "bộ nhớ cá nhân hóa" để Claude hiểu cách làm việc,
> tác phong, nguyên tắc kỹ thuật, và các rule cứng của Nghiep. Đây là skill
> được inject vào context — Claude đọc file này và áp dụng tự động, không cần
> Nghiep nhắc lại.
>
> **Trigger**: Bất kỳ câu hỏi nào liên quan đến AA-CIS, AAA, ACP, AWS, CI/CD,
> FastAPI, PostgreSQL, LangGraph, hoặc các quyết định kiến trúc trong AA_Ecosys.

---

## 1. Personality & Working Style

### Tác phong cơ bản
- **Môi trường**: WSL2 / Ubuntu 24 / Zsh (Oh My Zsh) / VSCode
- **Ngôn ngữ**: Vietnamese cho casual / internal work. English cho formal deliverables (Leigh, Ms. Thu)
- **Xưng hô**: Tôi/bạn — không dùng mày/tao. Giữ respectful, không formal quá mức.
- **Level**: Mid-Senior DevOps/AI Engineer — **không patronize**, không giải thích basics không cần thiết
- **Phong cách nhận câu trả lời**: Lead with answer → explain sau nếu cần. Không filler, không recap lại câu hỏi.

### Cách đưa ra quyết định
- **Root cause > symptom**: Luôn fix nguyên nhân, không patch bề mặt
- **Verify trước, assume sau**: Không assume state — verify bằng CLI/query thực tế
- **Document quyết định**: Mọi major tech decision → ghi ADR ngay trong session
- **Audit data trước UI**: UI on bad data = wasted time → audit pipeline correctness trước khi build thêm UI
- **Cost discipline**: Track cost per decision. Luôn stop ECS (desired=0) + RDS sau session

### Phản ứng với lỗi / unexpected output
- Không chấp nhận "có thể do..." mà không verify
- Muốn biết **chính xác** lỗi gì, ở đâu, tại sao
- Sau khi fix xong: hỏi "còn gì có thể vỡ không?"
- Prefer post-processing cho deterministic fixes > prompt-only solutions

---

## 2. Claude Chat vs Claude Code — Phân công công việc (RULE CỨNG)

### Nguyên tắc
| Loại task | Làm ở đâu | Ví dụ |
|---|---|---|
| Code, scripts, file edits | **Claude Code** | Migration SQL, Python scripts, AWS CLI, Terraform, CI YAML |
| Design, architecture | **Claude Chat** | Thiết kế schema, chọn stack, ADR, review plan |
| Notion / Linear updates | **Claude Chat** | Update memory.md, tạo issues, sync PRD |
| Formal deliverables | **Claude Chat** | DOCX reports, SKILL.md update, handoff.md |
| DB queries via ECS Exec | **Claude Code** | S3-mediated script, asyncpg queries |

```
❌ KHÔNG BAO GIỜ: Viết code/script trong Claude Chat
✅ THAY VÀO ĐÓ: Mô tả task đủ context → user chuyển sang Claude Code
```

### Format Claude Code task prompt — 1 code block duy nhất để dễ copy

```
## Task cho Claude Code: [tên task]

Mục tiêu: [làm gì, output là gì]

Repo: [AA-CIS-App | AA-CIS-Infra]  (AA-ACP-App/AA-ACP-Core đã archive+xoá hẳn 26/08/2026, AA-467 — không còn tồn tại)
Branch hiện tại: [branch]
Tạo branch mới: [yes: feature/aa-XX-desc | no]
Merge vào: main (trunk-based từ 09/07/2026 — AA-CIS-App/AA-CIS-Infra không còn develop)

Files cần đọc trước:
- [path]: [vai trò]

Context:
- [thông tin kỹ thuật, constraints, gotchas]

Steps:
1. [bước cụ thể]
2. [bước cụ thể]

Verify: [câu lệnh/query kiểm tra kết quả]

Sau khi done:
- git commit -m "feat/fix/chore: desc [AA-XX]" && git push
- Paste verify result về Claude Chat
- Linear: [AA-XX] → [status]
```

---

## 3. Session Ritual (Claude tự động — không cần nhắc)

### Session Start
1. Fetch Notion **memory.md HOT** (page `358b8a41-ec5d-807e-96c3-d66d620789e8`) → prod-state + 3 session gần nhất. **KHÔNG đọc archive** (`🗄️ memory_archive_2026H1`) trừ khi cần truy lịch sử cũ (S77→S39).
2. Confirm sprint + P0 task đang active
3. Nếu task cần AWS: `cis-start` (NAT → RDS → ECS) + `aws sts get-caller-identity` verify trước khi thao tác
4. Flag nếu state thực tế khác memory.md HOT

### Trong session
- Suggest commit format: `fix: description [LINEAR-ID]` hoặc `feat: ...`, `chore: ...`
- Update Linear issue status sau mỗi task done — **không cần user nhắc**
- Mỗi architectural decision → propose ADR ngay
- CLI output: luôn confirm từng bước trước khi tiếp tục bước tiếp theo

### Session End (Claude nhắc nếu user quên)
1. Stop AWS: `cis-stop` (ECS desired=0 → RDS stop → NAT)
2. Prepend session block mới vào memory.md HOT (`insert_content`, `position:{type:'start'}`)
3. **ROTATION** — sau khi prepend, đẩy block cũ nhất ngoài cửa sổ **3-session-gần-nhất** xuống `🗄️ memory_archive_2026H1` (cắt khỏi HOT, append vào archive). Giữ HOT *bounded* — không phình lại.
4. Update Linear issues (Done / In Progress)
5. Summary 3 dòng: đã làm gì / còn gì / session sau bắt đầu từ đâu
6. Nếu có quyết định kiến trúc mới → update ADR Log (page `358b8a41-ec5d-819d-8d1a-f5a314177bb9`)

---

## 4. AWS Patterns & Rules

### Account Map (luôn verify trước khi tạo resource) — SỬA 12/08 (S139, AA-397/398/399), mục 30/07 bên dưới cũng lỗi thời theo

🔴 **acc3 (786888028788) giờ là Bedrock satellite CHÍNH — thay acc1.** acc1 lùi xuống
**fallback** (dùng khi acc3 lỗi/hết fund $250), KHÔNG bị xoá khỏi routing. Áp dụng cho
CẢ interactive call (S1/N7/ACP) lẫn Bedrock Batch. Đừng copy lệnh cũ ghi acc1 làm satellite
chính — đã lỗi thời từ 12/08/2026.

Ứng dụng chính (ECS `aa-cis-dev-cluster`, RDS `aa-cis-dev-db`, S3 bronze/silver/gold,
mọi query DB) **vẫn ở acc2 `005097885195` / profile `aa365-admin`** — không đổi, không
liên quan thay đổi satellite.

```bash
aws sts get-caller-identity --profile aa365-admin   # acc2 — app chính, ECS/RDS/S3, hầu hết việc hàng ngày
aws sts get-caller-identity --profile nghiep_aa365   # acc3 — Bedrock satellite CHÍNH (mới)
aws sts get-caller-identity --profile pqnghiep-admin  # acc1 — Bedrock satellite FALLBACK (khi acc3 lỗi/hết fund)
```

| Project | Account | Region | Profile | Vai trò |
|---|---|---|---|---|
| CIS/ACP app (ECS/RDS/S3) | 005097885195 (acc2) | us-west-1 | aa365-admin | Chính, dùng hàng ngày |
| CIS/ACP Bedrock satellite CHÍNH | 786888028788 (acc3) | us-west-1 | nghiep_aa365 | LLM call ưu tiên (interactive + Batch), fund $250, real cost |
| CIS/ACP Bedrock satellite FALLBACK | 867490540162 (acc1) | us-west-1 | pqnghiep-admin | LLM call khi acc3 lỗi/hết fund, real cost |
| AAA DEV | 710590321660 | ap-southeast-1 | aa-dev-admin | |
| AAA STG | 593110023608 | ap-southeast-1 | aa-stg-admin | |
| AAA PROD | 007050358335 | ap-southeast-1 | aa-prod-admin | |

**Chain routing thật (`shared/llm_client/client.py`, sau AA-399):**
`T1 (acc2 native Sonnet) → T1.5a (acc3 satellite Sonnet) → T1.5b (acc1 satellite Sonnet)
→ T2 (acc2 native Haiku) → T2.5a (acc3 satellite Haiku) → T2.5b (acc1 satellite Haiku)
→ T3 (GPT-4.1 last resort)`. Field theo dõi: `LLMResponse.satellite_account: str|None`
(giá trị `"acc1"`/`"acc3"`/`None` — **đã đổi từ `satellite_used: bool` cũ**, migration 100
trên `silver_aa_internal.generated_content`, cột `satellite_used` cũ giữ song song
backward-compat, đừng xoá).

**IAM chain (2 role riêng biệt trên acc3, xác nhận qua AA-397/399):**
- `AA3-Bedrock-Invoker` — interactive satellite (mirror `AA-Bedrock-Invoker` acc1)
- `aa3-bedrock-batch-inference-role` — Batch inference (mirror `aa-bedrock-batch-inference-role` acc1)
Cả 2 đều trust `arn:aws:iam::005097885195:role/aa-cis-dev-ecs-task-role` (acc2 ECS task
role assume vào, KHÔNG phải ngược lại), ExternalId riêng cho acc3
(`aa296-satellite-bedrock-acc3`, khác acc1's `aa296-satellite-bedrock`).
Policy acc2 cho phép assume cả 2 role (acc1 + acc3) song song, nằm trong
`aa-cis-dev-ecs-assume-bedrock-invoker` (KHÔNG PHẢI `aa-cis-dev-ecs-task-policy` —
2 policy khác nhau, dễ nhầm tên, xem AA-398 nếu cần đối chiếu lại).

⚠️ **Bedrock model access trên acc3 gate theo TỪNG REGION riêng, dù cùng account** —
Marketplace subscription là account-level nhưng model access UI (đã bị AWS RETIRE, giờ
auto-enable khi invoke lần đầu) vẫn yêu cầu invoke thành công riêng mỗi region. us-west-1
(region code thật dùng) và us-east-1 (Playground mặc định) KHÔNG dùng chung 1 lần trigger.
Nếu thêm model/account Bedrock mới sau này, luôn test invoke thật đúng region sẽ dùng
trong code, đừng tin Playground pass ở region khác.

⚠️ Bucket S3 đúng cho scripts/query trên acc2: `aa-cis-bronze-005097885195`
(KHÔNG phải `aa-cis-bronze-867490540162` — mọi lệnh mẫu bên dưới dùng bucket cũ, SỬA TRƯỚC KHI CHẠY).

### Account Map cũ (lỗi thời, giữ lại để đối chiếu lịch sử, KHÔNG dùng để copy lệnh)
```bash
# Kiểm tra account trước mọi thứ
aws sts get-caller-identity --profile <profile>
```

| Project | Account | Region | Profile |
|---|---|---|---|
| AA-CIS (SAI — xem mục sửa 30/07 ở trên) | 867490540162 | us-west-1 | pqnghiep-admin |
| AAA DEV | 710590321660 | ap-southeast-1 | aa-dev-admin |
| AAA STG | 593110023608 | ap-southeast-1 | aa-stg-admin |
| AAA PROD | 007050358335 | ap-southeast-1 | aa-prod-admin |

### CLI Rules — CRITICAL
```
❌ NEVER: Multi-line AWS CLI với backslash trong WSL2 → HANGS
✅ ALWAYS: Single-line AWS CLI commands

❌ NEVER: SSH vào EC2/ECS
✅ ALWAYS: SSM Session Manager hoặc ECS Exec

❌ NEVER: Hardcode secrets trong code/Terraform
✅ ALWAYS: AWS Secrets Manager — retrieve at runtime

❌ NEVER: Public subnet cho RDS
✅ ALWAYS: Private subnet, access via ECS Exec
```

### ECS DB Query Pattern (Canonical — S3-mediated)
```bash
# Không có psql trong container — dùng python3 + asyncpg/psycopg2
# Không thể upload trực tiếp từ container — dùng boto3 → S3
# Dùng acc2 (aa365-admin) cho MỌI DB query/ECS exec — đây là account chạy app thật,
# KHÔNG phải acc1/acc3 (2 account đó CHỈ dùng cho Bedrock satellite, không có ECS/RDS gì).

# Step 1: Viết script local với boto3 upload result
# Step 2: Upload script lên S3
aws s3 cp /tmp/script.py s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1

# Step 3: Presign URL
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1 --expires-in 300)

# Step 4: Get task ARN
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)

# Step 5: Execute in container
aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s.py && python3 /tmp/s.py'" --profile aa365-admin --region us-west-1
```

### AWS Service Selection Rules
| Cần gì | Dùng gì | Không dùng |
|---|---|---|
| Job orchestration | Step Functions | SQS trực tiếp (P1 single tenant) |
| Notification fanout | EventBridge (ACP) | SNS (đã remove) |
| Secrets | Secrets Manager | Env vars plaintext, Parameter Store |
| Container serving | ECS Fargate | EC2 trực tiếp |
| LLM calls trong ECS | AWS Bedrock | Anthropic API trực tiếp |
| DB trong private subnet | ECS Exec + python3 | psql local, RDS Query Editor |
| Frontend deploy | Vercel (Phase 1) | EC2/S3 static (unnecessary complexity) |
| Rate limiting API | API Gateway Usage Plans | Custom middleware (duplication) |
| Monitoring | CloudWatch + Langfuse | Chỉ dùng 1 trong 2 |

---

## 5. CI/CD & Git Patterns

### Git Branch Discipline — Claude PHẢI hỏi đầu mỗi task code

Trước khi giao bất kỳ task code nào cho Claude Code, Claude Chat PHẢI confirm đủ 4 thông tin này:

```
1. Repo:    AA-CIS-App | AA-CIS-Infra | AAA-*  (AA-ACP-App/AA-ACP-Core archive+xoá hẳn 26/08/2026, AA-467)
2. Nhánh hiện tại: (vd: main, feature/aa-45-s3-planner)
3. Tạo nhánh mới không? → Feature branch nếu task > 1 commit
4. Merge target: main (duy nhất, kể từ 09/07/2026 — xem ADR-2026-023)
```

**⚠️ AA-CIS-App, AA-CIS-Infra KHÔNG còn nhánh `develop`** (xóa 09/07/2026,
ADR-2026-023, trunk-based CI/CD). Các repo AAA-* chưa migrate — verify
branch model thật của repo đó trước khi giả định (`git branch -r` hoặc hỏi trực tiếp),
đừng áp trunk-based cho repo chưa xác nhận. (AA-ACP-App/AA-ACP-Core không còn tồn tại,
không cần verify branch model của chúng nữa.)

**Branch naming convention:**
```
feature/aa-XX-short-description   # feature mới
fix/aa-XX-short-description        # bug fix
chore/terraform-description        # infra only
```

**Merge rules (không được skip, cho AA-CIS-App/AA-CIS-Infra):**
```
✅ feature/* → PR → main → CI required check xanh → merge (human-only, không qua develop)
✅ hotfix/* → PR → main trực tiếp
✅ Infra (AA-CIS-Infra): chore/* → PR → main → terraform-plan.yml (auto trên PR) → merge
   → apply KHÔNG tự chạy sau merge (workflow_dispatch only) → tự tay
     `gh workflow run terraform-apply.yml --ref main` khi sẵn sàng
```

**Claude Chat tự động append vào mỗi Claude Code task prompt:**
```
Git context:
- Repo: [tên repo]
- Current branch: [branch]
- Tạo branch mới: [yes/no — tên branch nếu yes]
- Merge vào: [target branch]
- Sau khi done: git add . && git commit -m "feat/fix/chore: desc [AA-XX]" && git push
```

---

### GitHub Actions — AA-CIS
```
Pipeline bắt buộc (gate mọi merge):
Lint → Unit Tests → Integration Tests → Docker Build

Track: CI run + task def → **KHÔNG hard-code trong skill** (sẽ stale). Luôn đọc PROD STATE trong memory.md HOT, hoặc verify live: `aws ecs describe-services` + `describe-task-definition`.
```

### Commit Format
```
feat: add endpoint description [AA-XX]
fix: resolve bug description [AA-XX]
chore: terraform/infra change [AA-XX]
docs: update README [AA-XX]
refactor: restructure without behavior change [AA-XX]
```

### Vercel Deploy (Phase 1 — manual)
```bash
# Vercel Hobby không support private org repos → manual deploy
vercel --prod

# Pull env: BẮT BUỘC thêm flag
vercel env pull --environment=production
```

### Terraform Rules
```
- Always: terraform plan trước apply
- S3 tag values: không dùng (), +, . — dùng dashes/plain text
- S3 bucket policy AllowCISServicesOnly với Principal: { AWS: [] } → MalformedPolicy
- RDS Query Editor: KHÔNG support standard PostgreSQL, chỉ Aurora Serverless
```

---

## 6. FastAPI Patterns (AA-CIS)

```python
# Route order CRITICAL — specific trước generic
# ✅ Đúng:
@app.get("/v1/tours/{id}/full")   # trước
@app.get("/v1/tours/{id}")        # sau

# ❌ Sai — {id} capture hết, /full không bao giờ hit

# UUID safe casting
import uuid
def safe_uuid(val) -> uuid.UUID | None:
    try: return uuid.UUID(str(val))
    except: return None

# Decimal safe casting cho JSON response
from decimal import Decimal
def safe_decimal(val) -> float | None:
    try: return float(Decimal(str(val)))
    except: return None
```

---

## 7. Database Schema Rules (AA_Ecosys — Non-negotiable)

### AAA Schema (PRD v4)
```
trip_plans     = TEMPLATES ONLY
trip_case      = CUSTOMER CONTAINER
→ KHÔNG BAO GIỜ merge hai bảng này

OTP-only auth → KHÔNG có password field trong users table

trip_case_version_itinerary = RELATIONAL TABLE (không phải JSONB)

Version status = boolean flags:
  is_sent_to_customer BOOLEAN
  is_approved BOOLEAN
  (KHÔNG dùng enum)

Image storage:
  s3_bucket VARCHAR
  s3_key VARCHAR
  → Generate cdn_url tại API response time (không store cdn_url)

Image migration → S3 + CloudFront TRƯỚC DB migration
(old server local filesystem at risk)
```

### AA-CIS Schema (Medallion)
```
shared.*                 → Cross-tenant: tenants, users, api_keys
silver_aa_internal.*     → Raw + pipeline state: raw_tours, pipeline_runs, generated_content
gold_aa_internal.*       → Published: published_tours, seo_contexts, content_exports

RLS enabled: 6 tables
Tenant schemas: dynamic via shared.create_tenant_schemas(slug)
```

### Env Var / Underscore Rule
```
❌ PROBLEM: Claude markdown rendering corrupts underscores trong code blocks
  NEXT_PUBLIC_API_URL → rendered thành [process.env.NEXT](url)

✅ SOLUTION: Nếu phát hiện vấn đề này → direct user mở file trong VSCode
  KHÔNG attempt fix bằng sed/heredoc/inline Python (corruption propagates)
```

---

## 8. LangGraph / AI Pipeline Patterns

### AA-CIS Pipeline (Step Functions)
```
S3 trigger (raw-inbox/) → Ingestion Lambda → Step Functions
  → SEO Lambda
  → Validation Lambda (currently bypassed — tech debt)
  → Content Lambda (calls /v1/pipeline/run-tour via ECS)
  → Export Lambda
```

### Bedrock Rules
```python
# Dùng Bedrock trong ECS pipeline (không phải Anthropic SDK)
import boto3

bedrock = boto3.client("bedrock-runtime", region_name="us-west-1")

response = bedrock.invoke_model(
    modelId="anthropic.claude-sonnet-4-5",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    })
)

# Cost tracking: log input_tokens + output_tokens mỗi call
```

⚠️ **Code trên minh hoạ Bedrock native (T1/T2, acc2 gọi trực tiếp).** Với satellite
call (T1.5/T2.5, real cost, acc3 chính/acc1 fallback) — KHÔNG tự viết `boto3.client`
tay như trên, dùng `shared/llm_client/bedrock_satellite.py`'s `invoke_claude(prompt,
model="sonnet"|"haiku", account="acc3"|"acc1")` (đã có AssumeRole + cache theo account
sẵn, xem chi tiết ở mục Account Map §4). `account` mặc định `"acc1"` nếu không truyền —
các call site mới nên truyền rõ `account="acc3"` trừ khi có lý do dùng acc1 (VD: Batch
control-plane client `v1_atoms.py`, khác `invoke_claude()`, đọc kỹ trước khi đổi
account cho path đó — role acc3 có thể chưa có đúng IAM permissions cho loại call này).

### Langfuse (Observability)
```
Version: v2.95.11, self-hosted trên ECS (aa-cis-dev-langfuse:1)
SDK: langfuse<3.0.0 (pinned — v3 breaking changes)
DB: langfuse schema trên existing RDS PostgreSQL 15
```

---

## 9. Techstack Decision Framework

Khi Nghiep hỏi "dùng A hay B", Claude nên trả lời theo framework này:

```
1. Alignment với existing stack? (add complexity không?)
2. Phase phù hợp chưa? (P1 simple, P2 scale)
3. Cost implication? (estimate số thực)
4. Reversibility? (dễ thay đổi sau không?)
5. Trong AA_Ecosys đã dùng chưa? (tái sử dụng > reinvent)
```

### Đã locked (không re-debate)
| Decision | Lý do | ADR |
|---|---|---|
| Bedrock > Anthropic API trực tiếp | Cost, no vendor lock, IAM native | ADR-2026-001 |
| Step Functions > SQS (P1) | Simpler for single tenant, visual debugging | ADR-2026-002 |
| ECS Fargate > EC2 | No infra management, serverless-like | Locked |
| PostgreSQL > DynamoDB | Relational data model, RLS multi-tenant | Locked |
| LangGraph > custom orchestration | Stateful agents, built-in retry | Locked |
| Claude Code > Codex (primary) | Native MCP HTTP, better multi-file reasoning | ADR-2026-005 |

---

## 10. Learning Integration Rules

### ADR Trigger — Claude đề xuất ngay khi
- Chọn service A thay vì B (e.g., dùng EventBridge thay vì polling)
- Thay đổi kiến trúc (e.g., migrate từ direct invoke sang SQS worker)
- Quyết định schema (e.g., JSONB vs relational table)
- Security pattern change (e.g., từ env var sang Secrets Manager)

### ADR Format (15 phút, lưu Notion AA_Learning/ADR Log)
```markdown
## ADR-2026-NNN: [Title]
**Date**: YYYY-MM-DD
**Status**: Accepted

**Context**: Tại sao cần quyết định này?

**Decision**: Chúng ta quyết định làm gì?

**Consequences**:
- ✅ Benefits
- ⚠️ Trade-offs / Risks

**Alternatives considered**:
- Option A (lý do không chọn)
- Option B (lý do không chọn)
```

### Cert Alignment (Claude track ngầm)
| Khi làm task | Mention domain cert liên quan |
|---|---|
| Lambda / API GW / SQS | DVA-C02: Development with AWS Services |
| IAM / Secrets / WAF | DVA-C02: Security |
| Multi-account / Organizations | SAP-C02: Design for Organizational Complexity |
| EventBridge / Step Functions | SAP-C02: Design for New Solutions |
| SageMaker / Bedrock / RAG | MLS-C01: Modeling + ML Implementation |

---

## 11. Stakeholder Context

| Name | Role | Communication style |
|---|---|---|
| Ms. Thu | Tech Lead + approval authority | Formal English / Vietnamese, DOCX deliverables |
| Leigh | Commercial Lead | English, business-focused, metrics-first |
| Mr. Manh | QuanSolution backend | Technical, tập trung ERD + schema |
| Trang | Internal content | Vietnamese, workflow-focused |

**Deliverable format rules:**
- Ms. Thu / Leigh → DOCX (formal)
- Internal tech → Markdown
- Architecture diagrams → FigJam flowchart (không dùng erDiagram)

---

## 12. Output Format Preferences

| Context | Format |
|---|---|
| CLI commands | Code block, single-line, với profile/region explicit |
| Terraform | HCL, modular, với comments giải thích |
| Python | Type hints, async-first (FastAPI patterns) |
| SQL | Named CTEs, readable formatting |
| Bash scripts | Error handling (`set -e`), output to `/tmp/` |
| Architecture explanation | Markdown table + sequence nếu cần |
| Formal report | DOCX via docx skill |

### Claude không làm
- Không suggest multi-line AWS CLI (hangs WSL2)
- Không suggest SSH (dùng SSM/ECS Exec)
- Không suggest hardcode secrets
- Không tự assume state — verify trước
- Không tiếp tục bước tiếp theo khi chưa có confirm output từ bước trước

---

## 13. Program Memory Sources (theo thứ tự ưu tiên)

**Kiến trúc memory (tách theo change-rate — tránh đọc thừa token):**
- **memory.md HOT** (`358b8a41-ec5d-807e-96c3-d66d620789e8`) — prod-state + 3 session gần nhất. Fetch mỗi session. Bounded ~3k token nhờ rotation.
- **🗄️ memory_archive_2026H1** (child page) — session log cũ (S77→S39). Fetch ON-DEMAND, không đọc lúc start.
- **Skills** (`ai-nghiep` / `aa-cis-schema` / `aa-ecosys-repos`) = reference layer ổn định (infra, AWS accounts, stakeholders, schema, ECS patterns). **KHÔNG nhét mutable state** (task def, CI#) vào skill — nó stale.
- **ADR Log** (`358b8a41-ec5d-819d-8d1a-f5a314177bb9`) — quyết định kiến trúc.

**Ưu tiên đọc:**
1. **memory.md HOT** — single source of truth cho state hiện tại (fetch đầu session)
2. **Linear issues** — Current sprint state
3. **Claude Project memory** (userMemories) — Long-term patterns
4. **handoff.md** trong repo — Code-Chat bridge (Claude Code writes, Chat reads)
5. **GitHub commit messages** — Ground truth cho code state

### 13.1 Maintenance Cadence (lịch update tài liệu — Claude tự nhắc khi tới hạn)
| Tài liệu | Cadence | Trigger |
|---|---|---|
| memory.md HOT | Mỗi session-end | Prepend block + ROTATION (đẩy block thứ 4 xuống archive) |
| `aa-cis-schema` skill | Mỗi **Monday** / sau migration mới | `SELECT version FROM shared.schema_versions ORDER BY version DESC` để verify |
| CIS + ACP CBT (Notion) | Mỗi **tháng**, hoặc khi 1 epic lớn đóng | Bump minor version (v0.x), append session-stamped §, sửa claim kiến trúc stale tại chỗ |
| `ai-nghiep` + `aa-ecosys-repos` skill | Mỗi **tháng** / khi đổi stack-pattern-ADR | Re-export SKILL.md → re-upload (Settings → Skills) |
| ADR Log (Notion) | Khi có quyết định kiến trúc | Format `ADR-2026-NNN` (xem §ADR) |

**Nguyên tắc anti-stale:** tài liệu reference (skill) KHÔNG chứa số biến động (task def, CI#, tour count) — số đó chỉ ở memory.md HOT hoặc verify live. **ADR numbering canonical = `ADR-2026-NNN`** (bare `ADR-NNN` cũ = prepend `2026-`). **Source of truth = Notion** (MD/DOCX project files là export, có thể lệch — Notion thắng khi conflict).

---

## 14. English Integration Rules (Active từ 18/05/2026)

### Khi nào Claude áp dụng
Bất kỳ khi nào Nghiep viết English text trong AA_Ecosys context — email, PR description,
Linear issue, Loom script, DOCX deliverable — hoặc khi Claude tạo English deliverable.

### Review Format (3 tầng — luôn theo thứ tự này)
```
❌ Original  : "We have done the deploy and now the system was working."
✅ Suggested : "The deployment is complete and the system is now running."
💡 Why       : (1) "have done the deploy" → dùng noun phrase "deployment is complete"
               (2) Tense inconsistency: "was working" → "is now running" (present state)
               (3) Over-translation từ tiếng Việt: "đã làm xong" → natural English dùng state
```

### Audience Tone Rules
| Audience | Tone | Avoid |
|---|---|---|
| Leigh | Direct, metric-first, confident | Hedging ("maybe", "I think") |
| Ms. Thu | Formal, structured, clear headers | Contractions (don't → do not) |
| Technical peer | Concise, jargon OK, no padding | Over-explanation of basics |
| Loom async | Conversational, short sentences | Long complex clauses |

### Sprint Phrase Extraction (tự động)
Cuối mỗi sprint có English output → Claude extract 5 key phrases và kèm:
- Phrase + example sentence trong context AA_Ecosys
- When to use (scenario)
- Update vào Notion Sprint Phrase Log (page 364b8a41-ec5d-81ca-8013-c15301a4b699)

### Technical Term Rule
Khi giải thích AWS / AI / tech term bằng tiếng Việt → luôn kèm:
```
Term: **idempotency**
Nghĩa: Gọi cùng 1 operation nhiều lần cho cùng 1 kết quả — không có side effect phụ.
Example: "SQS message processing must be idempotent to handle duplicate deliveries."
Dùng khi: Viết docs cho SQS consumer, Lambda, hoặc API endpoint design.
```

### Common Error Patterns (Nghiep-specific — cập nhật khi phát hiện)
| Pattern | Wrong | Correct |
|---|---|---|
| Article | "deploy to ECS cluster" | "deploy to **the** ECS cluster" |
| Tense mix | "We deployed X and now it is running Y" | Chọn 1 tense, giữ nhất quán |
| Over-translation | "We have done the fix" | "The fix is in place" / "We fixed it" |
| Preposition | "depend of", "consist of the" | "depend **on**", "consist **of**" |
| Passive overuse | "It was decided by us that..." | "We decided to..." |

*File này được tạo bởi Claude ngày 18/05/2026.*
*Update khi: thay đổi stack, add new pattern, ADR mới, hoặc khi Nghiep nói "update ai_nghiep.md".*
*Lưu tại: Google Drive → AA_Ecosys/ và Claude Skills (Settings > Customize > Skills)*

## ADDITIONS FOR ai-nghiep.md (04/06/2026)

### Section 3 — Session Ritual UPDATE

#### Session Start (updated)
1. Fetch Notion **memory.md HOT** (prod-state + 3 session gần nhất; KHÔNG đọc archive trừ khi cần lịch sử)
2. Confirm sprint + P0 task đang active
3. Start AWS resources — dùng alias `cis-start`:
   ```bash
   cis-start  # starts NAT Instance + RDS + ECS (in order)
   ```
   Chờ ~90 giây cho NAT Instance boot + iptables ready trước khi ECS cần outbound

#### Session End (updated)
1. Stop AWS: dùng alias `cis-stop` (stops ECS → RDS → NAT Instance)
   ```bash
   cis-stop  # stops ECS desired=0 + RDS + NAT Instance
   ```
2. Prepend session block mới vào memory.md HOT + **ROTATION**: đẩy block thứ 4 (ngoài cửa sổ 3-gần-nhất) xuống `🗄️ memory_archive_2026H1`
3. Update Linear issues (Done / In Progress)
4. Summary 3 dòng: đã làm gì / còn gì / session sau bắt đầu từ đâu

### Section 4 — AWS Patterns UPDATE

#### NAT Instance (thay NAT Gateway từ 05/06/2026)
```
NAT Instance: i-04ebd090e97184f45 (t4g.nano, us-west-1a)
EIP: 50.18.72.86 (cố định — keep attached để tránh recreate)
Cost: ~$3-5/mo (vs $42-67/mo NAT GW)
Interface: ens5 (NOT eth0) — AL2023 ARM64 naming
iptables: MASQUERADE on ens5 — saved in /etc/sysconfig/iptables
Terraform: modules/vpc/main.tf (AA-CIS-Infra, PR #1 merged)
```

Stop/Start pattern:
```bash
cis-start   # NAT + RDS + ECS
cis-stop    # ECS + RDS + NAT
cis-status  # check NAT instance state
```

⚠️ EIP cost khi stopped: $0.005/hr × stopped hours (~$3.65/mo nếu stop 30 ngày)
→ Acceptable. Không release EIP để tránh phức tạp khi restart.

⚠️ NAT Instance boot time: ~60-90 giây sau start trước khi iptables ready
→ cis-start đã include sleep, nhưng nếu ECS pull image fail → chờ thêm 30s

#### AWS Service Selection Rules (updated row)
| Outbound internet từ private subnet | NAT Instance (t4g.nano) | NAT Gateway ($67/mo) |

### Section 13 — Schema Update Rule (NEW)

```
STANDING RULE: Update aa-cis-schema skill mỗi thứ 2 (sau weekend dev)
hoặc sau bất kỳ tuần nào có migration mới.

Lệnh dump:
1. Ensure ECS running (cis-start)
2. Upload dump script:
   TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile pqnghiep-admin --region us-west-1 --query 'taskArns[0]' --output text)
3. Run dump_schema2.py via S3-mediated ECS exec
4. Download result + update /mnt/skills/user/aa-cis-schema/SKILL.md

Last updated: 04/06/2026 (47 tables, 653 columns, migrations 001-067)
```

### Section 9 — Techstack Decision Framework UPDATE

#### Đã locked (thêm mới)
| NAT Instance > NAT Gateway (dev) | Cost $3/mo vs $67/mo, stop/start per session | ADR-2026-011 |


## ADDITIONS FOR ai-nghiep.md (05/06/2026)

### Section 4 — AWS State (updated 05/06/2026)
ECS task def / main commit / Deploy Prod # → **KHÔNG hard-code** (stale). Đọc PROD STATE trong memory.md HOT hoặc verify live.
Migrations: theo dõi trong aa-cis-schema skill (xem mục Migrations); HOT memory note migration mới nhất mỗi session.

### Section 4 — DB Gotchas (NEW — verified 05/06/2026)
- `acp_silver_s3.content_calendars` — plural, NOT `content_calendar`
- `acp_run_context` là nguồn chính cho S2/S3 data (JSONB inline):
  s2_keyword_clusters, s2_visibility_report, s3_content_calendar, s3_ads_plan
  KHÔNG fetch từ separate table rows — fetch từ acp_run_context
- `acp_shared.acp_runs` KHÔNG có s2_status/s3_status — chỉ có s4_blog_status, s4_social_status, status
- `acp_silver_s2.visibility_reports` table tồn tại nhưng data nằm trong acp_run_context.s2_visibility_report

### Section 5 — AA-170 Done (05/06/2026)
CIS Admin UI S2→S4.2 hoàn chỉnh — 4 pages live tại aa-cis.lumiguides.it.com:
- /admin/pipeline/s2 — confidence gauge + keyword clusters + Gate 1 HITL
- /admin/pipeline/s3 — 12-week calendar + ads campaigns + Gate 2 (tabs)
- /admin/pipeline/s4-blog — draft cards + HITL actions (msthy_approved/flagged_human)
- /admin/pipeline/s4-social — empty state + channel filters + batch grid
PRs #26 + #27 | main `46f2c4b` | Deploy Prod #88

### Section 4 — Tooling (NEW)
Vercel Plugin cài ngày 05/06 trong Claude Code (scope: user):
- 26 skills auto-injected (nextjs, deployments-cicd, env-vars, vercel-api, ...)
- Slash commands: /vercel-plugin:deploy, /vercel-plugin:status, /vercel-plugin:env
- Restart Claude Code để load plugin

## ADDITIONS (17/06/2026) — S1 pipeline lineage + 5 findings + 2-model architecture

### Pipeline lineage (KHÔNG lẫn — MỘT dòng phát triển, không phải nhánh tách biệt)
- aa_batch_rewrite_v5.py (Ms. Thư) = LOGIC GỐC. Single-brand Adventure Asia, output JSONL.
  2-model: Claude Sonnet draft (EDITORIAL_KEYS) → GPT-4.1 finalize (schema+SEO+QA, FINAL_KEYS).
- CIS S1 (admin + AA internal) = phát triển TỪ v5. Thêm multi-brand (tenant_brand_rules,
  brand_identity_id, _build_brand_diff_block), ghi DB qua ECS. NHƯNG rút gọn còn SINGLE-LLM.
- ACP = mở rộng tiếp từ CIS cho B2B multi-tenant.
- /admin/run-tour → _execute_run_tour CHÍNH LÀ S1 của CIS. KHÔNG phải nhánh khác.
- Field contract gốc v5 = 7 fields: NAME, SUBTITLE, SUMMARY, HIGHLIGHTS, ITINERARIES,
  SEO_TITLE, SEO_META. KHÔNG có DESCRIPTION. aa_description trong DB = tàn dư, luôn rỗng vì
  không có src_description nguồn → KHÔNG phải bug, đừng đào lại.

### S1 graph thật (services/content_generation/graph.py) — verified S65
- generate_node (Bedrock haiku/sonnet) = LLM call DUY NHẤT. System = SYSTEM_PROMPT +
  brand_system_prompt + _build_brand_diff_block(state).
- validate_node = deterministic regex (length, itinerary format, seo_title ≤60). KHÔNG LLM.
- brand_audit_node = self-score Bedrock chấm chính nó → 9.6 vô dụng (không bắt generic).
- Loop: generate → validate → should_retry(quality_score) → brand_audit → flag_fix → END.
- _rewrite_tour (v1_pipeline.py) build initial_state, merge brand_rules (gồm AA-202 fields:
  core_idea/customer_segment/customer_mindset/voice_examples/good_examples) vào state.
- LLMClient (shared/llm_client/client.py) ĐÃ hỗ trợ 3 tier: haiku | sonnet | gpt-4.1.
  gpt-4.1 wired sẵn (_call_openai), OPENAI_API_KEY env. Không cần xây client mới.

### 5 findings của Ms. Thư (4-tenant S1 run) = backlog chất lượng S1
S1 sinh master content → gate toàn bộ downstream (S2→S4.2). Fix S1 TRƯỚC mọi thứ.
Decision Ms. Thư: S1 dùng DataForSEO cho keyword sourcing (không để LLM đoán), align với S2 SERP.
1. Brand differentiation yếu — cùng trip × 4 brand ra gần giống nhau. [= AA-206]
2. Keywords yếu — derive 4 nguồn: trip location, tenant country (US/UK/AUS), people-also-ask,
   suggestion keywords → DataForSEO. [= AA-197/AA-203]
3. Meal + activity time — BỎ mô tả bữa ăn + giờ giấc trong day content (thuộc trip planning sau).
4. Day-by-day titles vô dụng — phải chứa địa danh/hoạt động chính + đọc cuốn hút. [= AA-196 F4]
5. Meta + title bị cắt giữa từ — viết gọn trong limit (title ≤60, meta 80-160) không hard-truncate. [= AA-204]

### ADR-2026-014 — S1 Two-Model Generate–Judge (giải finding #1 = AA-206 + AA-207)
- Phân vai cứng: Bedrock VIẾT, GPT-4.1 CHẤM. GPT chỉ score brand-fit + feedback, KHÔNG sửa content.
- Bedrock sửa theo feedback qua retry loop (feedback field + should_retry có sẵn).
- Thêm node llm_judge (gpt-4.1 tier) sau validate; thay self-score brand_audit bằng judge.
- Tăng cường _build_brand_diff_block: CONTRAST phủ cả itineraries + day-titles + negative contrast
  (hiện chỉ phủ summary+highlights → root cause differentiation yếu).
- Lý do 2-model: single-model self-eval = blind spot + bias. Cross-provider judge bắt generic
  mà model viết không tự thấy.

### Diagnostic lesson (S65 — tự nhắc để không lặp)
- ĐỌC CODE THẬT trước khi giả thuyết. S65 mất nhiều lượt vì giả thuyết "GPT-4.1 finalize làm phẳng
  brand" — code bác bỏ: S1 chỉ 1 LLM call, không có finalize node. Verify graph/code trước mọi claim.
- ECS exec streaming chết với generate dài (SSM EOF). Để KÍCH S1 run: curl /admin/run-tour qua
  api-cis.lumiguides.it.com (chấp nhận gateway timeout — generate vẫn chạy server-side tới xong),
  rồi đọc kết quả từ generated_content qua ECS exec read-only (nhanh, không EOF).
- API base CIS = api-cis.lumiguides.it.com (KHÁC frontend aa-cis.lumiguides.it.com). Health 401, admin POST cần x-admin-secret (aa-cis/dev/admin-secret).

## ADDITIONS (09/07/2026) — Trunk-based CI/CD (ADR-2026-023), thay thế toàn bộ mô tả develop→main cũ

**Nhánh `develop` đã bị xóa hoàn toàn ở AA-CIS-App + AA-CIS-Infra kể từ 09/07/2026** (lúc đó
chỉ có 2 repo; nay có thêm `AA-TripPlanner-Web` cũng dùng trunk-based, deploy qua Vercel Git
Integration + `deploy-lambdas.yml`). Tất cả dưới org `AdventureAsia365-Ecosys`. `main` là default
branch duy nhất. Mọi mô tả CICD pipeline cũ trong
skill này ("feature branch từ develop → CI green → merge develop → Deploy Dev green →
merge main") ĐÃ LỖI THỜI — quy trình mới:

```
feature/aa-XXX-desc (từ main) → PR → main
  ↳ CI required check (AA-CIS-App: 5 job Lint/Security/Unit/Integration/Docker)
  ↳ merge → app repo tự động deploy (push:[main] + paths-filter, workflow_dispatch
     dự phòng) — Infra KHÔNG tự apply
```

**Lưu ý 26/08/2026 (AA-467):** AA-ACP-App + AA-ACP-Core đã ARCHIVE trên GitHub + XOÁ HẲN
khỏi local workspace — không còn là repo đang hoạt động, mọi mô tả CI/CD/branch của 2 repo
này trong skill (nếu còn sót ở đâu) chỉ mang tính lịch sử, không áp dụng cho task nào nữa.

**Infra khác biệt quan trọng:** `terraform-apply.yml` (AA-CIS-Infra) đã đổi từ
`push:[develop]` sang **`workflow_dispatch` là trigger DUY NHẤT** — merge PR vào main
KHÔNG bao giờ tự chạy apply. Phải tự tay chạy sau khi merge và đã xem lại
`terraform-plan.yml` (chạy tự động trên PR):
```bash
gh workflow run terraform-apply.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main
```
Luôn chỉ định `--ref main` — workflow_dispatch không tự lấy code mới nhất theo push.
Lý do dùng workflow_dispatch thay vì GitHub Environment required-reviewers: AA-CIS-Infra
là private repo trên GitHub Free — required-reviewers cho environment chỉ khả dụng ở
Enterprise Cloud cho private repo (đã verify qua doc GitHub 09/07/2026). Environment
`prod` (lowercase, có sẵn) được tái sử dụng, không tạo `production` mới.

**KHÔNG còn bước "đảo main→develop"** (`git fetch origin && git checkout develop &&
git reset --hard origin/develop`) — bước này đã bị xóa khỏi quy trình vì không còn
nhánh develop để đảo.

**Lý do migration (tóm tắt, đầy đủ xem ADR-2026-023 trong Notion ADR Log):** CIS/ACP chỉ
có 1 environment AWS thật (account 2, AA365) — khác AAA có 3 account DEV/STG/PROD tách
biệt. Buffer "develop ngấm vài ngày" không được dùng trong thực hành (PR fail luôn fix
ngay cùng session), nên giữ 2 nhánh chỉ tạo ma sát thủ tục (fast-forward develop→main)
mà không mang lại an toàn thật. Trigger tái đánh giá: khi CIS/ACP có tenant B2B thật đầu
tiên onboard hoặc traffic ngoài core team — lúc đó cần tách STG/PROD thật và model này
cần review lại.

**Chưa làm (carryover):** Terraform backend state key trên AA-CIS-Infra vẫn là literal
`dev/terraform.tfstate` dù environment đã đổi tên thành `prod` — lệch tên gọi, không phải
lỗi chức năng, nhưng đổi cần state migration thật (`terraform state mv` hoặc tương đương)
nên để riêng, không gộp vào lúc đổi trigger.

## ADDITIONS (30/07/2026) — Phiên rà soát brand_audit_node + atom pipeline, 8 lỗi "đánh Done nhưng chưa persist thật"

**Bối cảnh:** Xuất phát từ Ms. Thư báo tour dài bị nén trên script v6 ngoài repo. Đối chiếu
v6 vs S1 production, rồi mở rộng rà soát toàn bộ `brand_audit_node` theo nguyên tắc ADR-2026-037
(mọi thứ đánh Done phải có đường đọc ra thật). Tìm được 8 lỗi cùng họ, xem đủ ở comment Linear
AA-329/AA-341/AA-347 và AA-342 (rà soát ngược, đang gom). KHÔNG liệt kê chi tiết ở đây — chỉ
ghi các NGUYÊN TẮC rút ra, có giá trị lâu dài hơn từng bug cụ thể.

### Nguyên tắc mới — "audit tồn tại không có nghĩa audit đúng"
Trước 30/07, mặc định tin các phép kiểm tất định trong `brand_audit_node` đo đúng điều tên
chúng nói. SAI. Ví dụ điển hình: `ITIN_MEAL_INVENTED` chỉ dò từ khoá breakfast/lunch/dinner
trong OUTPUT, không hề đối chiếu SOURCE — báo động phần lớn là giả. `ITINERARY_DAY_TITLE_GENERIC`
chết theo cấu tạo (0/0 fire toàn hệ thống) vì `validate_node` chuẩn hoá dấu gạch ngang TRƯỚC
khi phép kiểm này chạy tới. **Quy tắc mới: mọi phép kiểm mang tên hàm ý "bịa/invented/fabricated"
PHẢI được xác nhận có đối chiếu source thật trước khi tin số liệu nó báo ra.**

### Nguyên tắc mới — "atom hoá không có nghĩa atom không bịa"
Kiểm tay atom vừa decompose (Sonnet 4.6): 1/2 mẫu có chi tiết KHÔNG có trong nguồn ("canyon
landscape"). Giả định "nhánh atom miễn nhiễm bịa đặt theo cấu tạo" CHƯA được chứng minh —
n=2, cần đo thêm ở AA-339. Atom cần grounding check riêng, không tự động tin.

### Con số quan trọng nhất phiên này — quét 58 tour đã xuất bản
**39/58 tour** (sau vá) có ít nhất 1 số/mốc thời gian bịa không có trong nguồn — đã UNPUBLISH
ngày 30/07 (cơ chế: `PATCH /admin/master/{tour_id}/deactivate`, admin.py:1071, null hoá field
qua `v_trip_registry` mà giữ nguyên raw source). Phép kiểm dùng: `find_novel_numeric_claims()`
(services/acp_shared/grounding.py) — đã có sẵn, đã chứng minh trên dữ liệu thật ở ADR-2026-033,
chỉ cần VÁ (bỏ sót số thứ tự dạng "11th") và MỞ RỘNG phạm vi so sánh (toàn văn source, không
chỉ atom có citation), không cần viết phép kiểm mới. **Bài học: trước khi viết validator mới,
tìm xem đã có cái tương tự ở nhánh khác chưa — S1-from-atom đã có, S1 cũ thì không.**

### Bug thao tác của chính Claude Chat — tự sửa
3 lần liên tiếp trong phiên 30/07, Claude Chat gọi SAI số Linear issue khi giao việc cho
Claude Code (dùng "AA-341" cho nội dung không liên quan gì tới issue AA-341 thật). Claude
Code tự phát hiện trước khi post (so title thực tế), không post nhầm. **Quy tắc mới bắt buộc:
mọi lần Claude Chat giao `issueId` trong prompt cho Claude Code, PHẢI tự `get_issue` xác minh
title khớp bối cảnh trước khi ghi bất cứ gì vào issue đó — không tin số issue nhớ được từ
đầu phiên.**

### Hướng chiến lược đã chốt
Chuyển trọng tâm từ "vá S1 cũ" sang "đẩy nhanh nhánh atom" (AA-306/S1-from-atom) — dựa trên
AA-346: thí nghiệm sửa prompt để chống nén itinerary theo ngày KHÔNG có tác dụng đáng kể trên
Haiku (nhiễu giữa 2 lần chạy cùng prompt LỚN HƠN hiệu ứng của việc thêm chỉ dẫn). Câu hỏi mở
chưa đo: Sonnet có khác Haiku không (đưa vào AA-339 cùng với grounding check).

## ADDITIONS (01/08/2026) — Báo cáo dài từ Claude Code: tạo thẳng trên Notion, không dán qua chat

**Bối cảnh:** Before/after benchmark AA-353 (S132) tạo ra báo cáo 924 dòng (`README.md`,
77 bảng dữ liệu). Lần đầu, Claude Chat đọc file qua `view` rồi gõ lại vào Notion — bị cắt
mất ~1/3 nội dung giữa file (giới hạn hiển thị 1 lần đọc của `view`), không phát hiện ra
cho tới khi Nghiep hỏi lại. Lần hai, xác nhận Claude Code có sẵn Notion MCP
(`mcp__claude_ai_Notion__*`) — để nó tự đọc file từ đĩa (không giới hạn như `view`) và tự
gọi `notion-create-pages`, kết quả đủ 77/77 bảng, verify được bằng đếm số bảng 2 bên.

**Quy tắc mới, áp dụng từ giờ:** Khi Claude Code hoàn thành báo cáo/thí nghiệm dài (đặc
biệt >200-300 dòng hoặc nhiều bảng dữ liệu), **giao cho Claude Code tự tạo page Notion
trực tiếp** từ file kết quả trên đĩa (dùng Notion MCP nó đã có sẵn), thay vì dán nội dung
qua chat để Claude Chat gõ lại. Claude Chat sau đó `notion-fetch` từ chính page đó để đọc
đủ chi tiết khi cần phân tích/trả lời câu hỏi — tránh mất thông tin qua vòng tóm tắt
trung gian. Lưu ý kỹ thuật Claude Code đã xử lý: Notion không nhận cú pháp bảng markdown
`| a | b |` — phải chuyển sang khối `<table><tr><td>` XML, và escape ký tự `<` đứng trước
số (VD `<70%`) để tránh bị hiểu nhầm thành mở tag.

## ADDITIONS (27/08/2026) — Đợt dọn dẹp ACPv1 lớn nhất, quy trình DRY RUN bắt buộc cho mọi DROP TABLE

Tóm tắt: 1 phiên dọn dẹp gộp Gate A + Atomize/Curation + cụm 21 bảng ACPv1 + gộp 3 project Linear
về 1. Rút ra nguyên tắc mới có giá trị lâu dài:

1. **STEP0 không dừng ở "0 caller/0 row"** — phải hỏi đúng câu "tenant/A-T-series đã có đường tự
   làm việc này chưa" thay vì "có ai đang dùng không". Sai lầm đã xảy ra 1 lần ở AA-473 STEP0 lần
   1 (kết luận nhầm giữ nguyên Atomize/Curation vì nghĩ nó là "catalog dùng chung", thực ra là mô
   hình đã bị bỏ hoàn toàn).
2. **FK-graph-first qua pg_constraint là điều kiện CẦN, không ĐỦ** — cột không có FK constraint
   DB (VD run_id/tenant_id trần) vẫn có thể liên hệ thật ở tầng ứng dụng, luôn bổ sung quét "0
   row + 0 caller code" độc lập (bài học AA-479, acp_cms_publish_queue).
3. **Cùng thư mục/package KHÔNG cùng số phận** — luôn xóa từng FILE, verify import chain riêng,
   không xóa cả thư mục theo bản năng (bài học AA-477, cms/wordpress.py sống trong khi
   publisher.py cùng thư mục đã chết).
4. **Trước khi DROP TABLE — DRY RUN → xác nhận số liệu khớp → SAVEPOINT verify trong transaction
   → COMMIT thật → verify độc lập qua information_schema (không tin lại transaction cũ)** — quy
   trình 5 bước này giờ là chuẩn bắt buộc cho mọi thao tác xóa dữ liệu vĩnh viễn.
5. **CI replay migration thật bắt được lỗi mà grep tĩnh không thấy** — test integration insert
   vào bảng sắp DROP sẽ fail thật trên CI (postgres container thật), không phải flaky. Luôn grep
   tên bảng sắp DROP trong tests/integration/ trước khi coi migration là "chỉ ảnh hưởng DB".
6. **Sau đợt dọn DB lớn — LUÔN quay lại update skill 2 lần**: 1 lần trước khi apply (audit +
   go-ahead), 1 lần SAU khi apply thật (số liệu mới + Dead Table Registry để truy vết sau này).
   Không coi 1 lần update là đủ.

Giữ ngắn gọn, không lặp lại chi tiết kỹ thuật đã có ở aa-cis-schema.md và aa-ecosys-repos.md —
chỉ ghi nguyên tắc làm việc rút ra.
