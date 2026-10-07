# AWS — AA_Ecosys

## Account map

| Vai trò | Account | Region | Profile |
|---|---|---|---|
| App chính: ECS, RDS, S3, Lambda TripPlanner, mọi DB query | 005097885195 (acc2) | us-west-1 | `aa365-admin` (MFA, chỉ Nghiệp) |
| Bedrock satellite chính | 786888028788 (acc3) | us-west-1 | `nghiep_aa365` |
| Bedrock satellite fallback | 867490540162 (acc1) | us-west-1 | `pqnghiep-admin` |

- Account AAA cũ (ap-southeast-1) đã đóng. AA-Booking chạy trên acc2.
- acc1 không tạo compute mới; chỉ giữ làm satellite.
- Bucket script/runner: `aa-cis-bronze-005097885195`.

## Runtime trên acc2

- ECS cluster `aa-cis-dev-cluster`; hai service dùng chung một image: `aa-cis-dev-api` (container `api`, uvicorn) và `aa-cis-dev-worker` (job runner, chạy `python -m worker`). Mỗi deploy đăng ký task-def mới cho cả hai.
- Job nền chạy qua `shared.job` + worker service. Env `JOB_WORKER_IN_API` quyết định api có chạy thêm worker loop hay không; đọc giá trị thật trong task-def api, đừng suy từ default trong code.
- RDS `aa-cis-dev-db`, DB `aa_cis_dev`; secret `aa-cis/dev/rds` là DSN thô (không phải JSON). RDS nằm trong subnet riêng — CI không query thẳng được, phải qua ECS exec.
- Domain: API `api-cis.lumiguides.it.com`, frontend `aa-cis.lumiguides.it.com`.

## LLM routing

Gateway định tuyến theo stage (`shared.llm_role_config`): acc3-first, fallback acc1, rồi model ngoài (OpenAI API). Writer chạy model Anthropic; judge và brand audit chạy GPT (vendor khác writer có chủ ý). Đọc route thật trong DB, không ghi số/model vào skill (đang đổi theo A/B).

## Start / stop môi trường

- `cis-start` (NAT → RDS → ECS api scale 1), `cis-stop` (ECS api scale 0 → RDS → NAT), `cis-status`. NAT instance cần ~60–90 giây mới có outbound.
- Cả hai alias chỉ scale service `aa-cis-dev-api`, KHÔNG đụng `aa-cis-dev-worker` — worker giữ nguyên desired count khi dừng/khởi động môi trường bằng alias.
- STS hết hạn sau 8h → `eval "$(aws configure export-credentials --profile aa365-admin --format env)"` + MFA (chỉ Nghiệp).

## CLI rules

- Một dòng, luôn ghi `--profile` và `--region`.
- ECS exec: lệnh > ~100s dễ timeout → chạy nền, ghi kết quả ra S3, poll. Pattern ở `aa-cis-schema/references/ecs-exec.md`.
- zsh không word-split biến chứa nhiều flag → dùng `bash -c` hoặc flag rời.
- Terraform apply chỉ qua workflow repo Infra (`gh workflow run ... --ref main`), không chạy tay.
