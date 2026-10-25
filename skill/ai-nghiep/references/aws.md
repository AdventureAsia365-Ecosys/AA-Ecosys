# AWS — AA_Ecosys

## Account map

| Vai trò | Account | Region | Profile |
|---|---|---|---|
| App chính: ECS, RDS, S3, Lambda, API Gateway, Cognito, mọi DB query | 005097885195 (acc2) | us-west-1 | `aa365-admin` (MFA, chỉ Nghiệp) |
| Bedrock satellite chính | 786888028788 (acc3) | us-west-1 | `nghiep_aa365` |
| Bedrock satellite fallback | 867490540162 (acc1) | us-west-1 | `pqnghiep-admin` |

- Cả bốn app (CIS, TripPlanner, Booking, Partner) chạy trên acc2; prod sau này cũng ở acc2, không account mới.
- Các account AAA cũ của Quanskill (ap-southeast-1) không thuộc hệ sinh thái — không deploy ở đó.
- acc1 vẫn ACTIVE, giữ có chủ đích làm Bedrock satellite (role `AA-Bedrock-Invoker`); không tạo compute mới ở đó.
- Profile `default` = acc2 (cùng role với `aa365-admin`). Trước khi tạo tài nguyên: `aws sts get-caller-identity --profile <profile>`.
- Bucket script/runner: `aa-cis-bronze-005097885195`.
- Repo gốc và Infra đang public (ADR 0014 amendment): không ghi ARN, SG/VPC ID, inventory hay giá trị secret vào repo
  app; tên secret thì xem `docs/security/secrets-register.md`.

## Runtime trên acc2

- ECS cluster `aa-cis-dev-cluster`, 5 service:
  - `aa-cis-dev-api` (container `api`, uvicorn) và `aa-cis-dev-worker` (job runner `shared.job`, `python -m worker`) —
    cùng một image, mỗi deploy đăng ký task-def mới cho cả hai. `JOB_WORKER_IN_API` mặc định tắt; đọc giá trị thật
    trong task-def, đừng suy từ code.
  - `aa-booking-dev-api` — API Booking, worker `booking.job` chạy trong process.
  - `aa-crm-dev-api` (worker `crm.job` trong process) và `aa-crm-dev-web` — AA-Partner, Fargate ARM64.
- RDS `aa-cis-dev-db` dùng chung, mỗi app một schema và một DSN secret riêng. Secret `aa-cis/dev/rds` là master —
  task role CIS bị Deny đọc; api + worker dùng `DATABASE_URL` (`aa-cis/dev/rds-cis-app`, role `cis_app`: schema CIS,
  không `booking.*`/`tripplanner.*`, không DDL). Việc cần master → DB Migrate `mode=run-script` với script đã review
  trên main. RDS ở subnet riêng, CI không query thẳng được. Pattern: `aa-cis-schema/references/ecs-exec.md`.
- Domain và endpoint live: mục "LIVE ENDPOINTS" của root `.claude/CLAUDE.md`; host AA-Partner (`partner-dev.`,
  `portal.`) và TripPlanner trong bảng repo của `docs/ecosystem-architecture.md` (ID API Gateway / pool / SG không chép vào
  skill — tra bằng lệnh một dòng hoặc Terraform output).

## LLM routing

Gateway định tuyến theo stage (`shared.llm_role_config`): acc3-first, fallback acc1, rồi model ngoài (OpenAI API).
Vendor rule: stage **writer** chạy Anthropic, stage **judge** chạy vendor khác (không tự chấm văn của hãng mình);
stage **validate** (trích xuất / kiểm mà judge không chấm) được dùng bất kỳ model nào trong catalog (CIS ADR 0008).
Đọc route thật trong DB, không ghi model vào skill (đổi theo A/B). Script adhoc gọi LLM phải qua `LLMClient` và ghi
`shared.llm_call_log` (steering `session-workflow.md`).

## Môi trường — CHẠY LIÊN TỤC

- **Hệ thống Dev chạy liên tục. Agent TUYỆT ĐỐI KHÔNG tự bật/tắt hạ tầng:** không `cis-start`/`cis-stop`, không
  `aws ecs update-service --desired-count`, không `rds stop/start-db-instance`, không `ec2 start/stop-instances`.
  Muốn bật/tắt → hỏi Nghiệp, chỉ làm khi Nghiệp yêu cầu rõ. Cuối phiên không nhắc lệnh tắt.
- Kiểm trạng thái chỉ bằng lệnh đọc (`aws ecs describe-services …`, `cis-status` = trạng thái NAT instance).
- STS hết hạn sau 8h → Nghiệp chạy `aws sts get-caller-identity --profile aa365-admin` và nhập MFA.
- Terraform/boto3 cần credential trong env: dùng mẫu `env-no-export` trong steering `session-workflow.md`
  (không `export $(…)` trần — lệnh rỗng thì in toàn bộ env, lộ token).

## CLI rules

- Một dòng, luôn ghi `--profile` và `--region`.
- zsh không word-split biến chứa nhiều flag → dùng `bash -c` hoặc flag rời.
- **ECS exec** (chỉ phiên điều phối; hook chặn subagent):
  - Lệnh > ~100s dễ timeout → chạy nền, ghi kết quả ra S3, poll.
  - Output dài / JSON một dòng lớn làm rớt phiên SSM (`Cannot perform start session: EOF`) và bị cắt im lặng → in dòng
    ngắn, flush, LIMIT nhỏ; container CIS: ghi file rồi upload lên bucket bronze và tải về. Task role CRM không ghi được
    bucket bronze → probe CRM chỉ in vài dòng ngắn.
- **Terraform:** apply chỉ qua workflow `terraform-apply.yml` (workflow_dispatch, `--ref main`) của AA-CIS-Infra; plan
  guard (AA-846) từ chối thay đổi loại tài nguyên được bảo vệ trừ khi đặt `allow_guarded` + `allow_reason`. Plan của
  nhiều PR chạy cùng lúc có thể fail "Error acquiring the state lock" — chạy lại, không phải lỗi code. Apply chạm task
  definition ECS đăng ký một revision mẫu mà deploy kế tiếp sẽ chép → sau apply đó, so tên env giữa revision mới nhất
  và revision đang chạy. Chi tiết và cách sửa: `aa-lessons/lessons.md` (mục Vận hành).
