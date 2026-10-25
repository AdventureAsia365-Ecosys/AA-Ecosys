# ECS exec + S3 — query DB từ container

RDS trong private subnet → chạy script Python (asyncpg) trong container qua ECS exec, lấy kết quả qua S3. Bản chuẩn là
runbook `docs/ops/runbooks/ecs-exec-s3-mediated.md` ở repo gốc (tiếng Anh, có bước verify + dọn file S3); file này là
bản tóm tắt nhanh — khi lệch, runbook thắng và file này được sửa theo.

**Chỉ phiên điều phối chạy ECS exec.** Hook `.claude/hooks/subagent-guardrails.sh` chặn subagent gọi
`aws ecs execute-command` (và `run-task`, `update-service`…). Subagent soạn script + lệnh, trả về cho điều phối; đừng
lách qua script trung gian (`bash run.sh`) — hook chỉ đọc dòng lệnh, nhưng luật thì vẫn áp.

## Ai đăng nhập DB, được làm gì

- Container CIS (`aa-cis-dev-api`, `aa-cis-dev-worker`): `DATABASE_URL` = **`cis_app`** (secret `aa-cis/dev/rds-cis-app`):
  đọc/ghi mọi bảng CIS (kể cả bảng RLS), không DDL, không ghi `shared.schema_versions`. `booking.*` / `tripplanner.*`
  chỉ vài view hợp đồng (`booking.v_ops_*`, `booking.v_supply_*`, `tripplanner.v_ops_traffic_daily`); bảng gốc → 42501.
  Không có quyền gì trên `crm`.
- Task role CIS bị **Deny** `GetSecretValue` trên `aa-cis/dev/rds` (master), `aa-cis/dev/db-migrator`, `booking/*`,
  `tripplanner/*` → không lấy DSN master trong script.
- Container CRM (`aa-crm-dev-api`): login `crm_app`, chỉ schema `crm`, đọc dữ liệu tenant qua `app.tenancy.tenant_tx()`
  (RLS theo `app.tenant_id`). Task role CRM **không ghi được bucket bronze** → không có đường S3 cho output.
- Việc cần master (bảng `booking.*` / `tripplanner.*` / `crm.*` ngoài quyền trên, role, `catalog.*`, sửa liên chủ sở
  hữu) → **DB Migrate `mode=run-script`** với file `db/scripts/<name>.py` đã review trong AA-CIS-Infra
  (`db/scripts/README.md`; `READ_ONLY = True` cho script chỉ đọc). Đổi cấu trúc DB là migration của repo chủ.

## Script mẫu (asyncpg, kết quả ra S3)

```python
import asyncio, json, os, boto3, asyncpg

async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")  # cis_app; không đọc secret master
    rows = await conn.fetch("SELECT ...")  # luôn schema-qualify
    with open("/tmp/result.json", "w") as f:
        json.dump([dict(r) for r in rows], f, indent=2, default=str)
    await conn.close()
    boto3.client("s3", region_name="us-west-1").upload_file(
        "/tmp/result.json", "aa-cis-bronze-005097885195", "scripts/result.json")

asyncio.run(main())
```

Script cần code app → `sys.path.insert(0, "/app")` (có `shared.secrets.get_database_url`).

## Chạy (mỗi lệnh một dòng)

```bash
aws s3 cp /tmp/script.py s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1 --expires-in 300)
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s.py && python3 /tmp/s.py && echo DONE'" --profile aa365-admin --region us-west-1
aws s3 cp s3://aa-cis-bronze-005097885195/scripts/result.json /tmp/result.json --profile aa365-admin --region us-west-1
```

(File tạm trên máy: dùng `.tmp-session/` trong workspace thay cho `/tmp` như runbook.)

## Lưu ý

- `--command` không qua shell: `;`, `&&`, pipe phải nằm trong `sh -c '…'`.
- **Không đọc kết quả qua terminal SSM.** Output dài (JSON một dòng vài KB, nhiều dòng liền) làm phiên đóng sớm
  (`Cannot perform start session: EOF`) và mất dữ liệu im lặng. Container CIS: ghi file → upload S3 → tải về, kiểm
  `wc -c` / `json.loads` trước khi đọc. Container CRM (không có S3): in dòng ngắn, mỗi dòng một sự kiện, `flush=True`,
  `LIMIT` nhỏ, cuối script `sleep` ngắn.
- `execute-command` có thể treo tới ~120 giây → chạy nền, poll S3. Script > 5 phút không chạy qua exec (deploy thay task
  là chết giữa chừng; exec nền cũng tự ngắt) → one-off ECS task, job trên worker, hoặc chạy sau khi mọi PR backend đã merge.
- zsh không word-split biến chứa nhiều flag → `bash -c` hoặc flag rời.
- Dùng task của `aa-cis-dev-api` cho query. Việc dài thì enqueue job vào `shared.job` (chạy trên worker).

## Log

- ECS CIS: `/ecs/aa-cis-dev` — một log group cho api và worker, phân biệt bằng stream prefix (retention 30 ngày);
  nhật ký phiên exec `/ecs/aa-cis-dev/exec-sessions` (365 ngày). Booking: `/ecs/aa-booking-dev`; CRM: `/ecs/aa-crm-dev`.
- Lambda còn lại trên acc2: `aa-cis-dev-dfs-balance-check` (kiêm ops probe gọi `/admin/waves/check`),
  `aa-cis-dev-rds-snapshot-expiry`, `aa-identity-dev-*` (Cognito trigger), `aa-tripplanner-dev-browse` / `-assembly`.
  Các Lambda pipeline CIS cũ đã gỡ (AA-750). Log group: `/aws/lambda/<tên>`.

## DBeaver qua SSM port-forward

```bash
TASK_ID=$(echo $TASK_ARN | cut -d'/' -f3)
RUNTIME_ID=$(aws ecs describe-tasks --cluster aa-cis-dev-cluster --tasks $TASK_ARN --profile aa365-admin --region us-west-1 --query 'tasks[0].containers[0].runtimeId' --output text)
aws ssm start-session --target "ecs:aa-cis-dev-cluster_${TASK_ID}_${RUNTIME_ID}" --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters "{\"host\":[\"<RDS endpoint>\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"15432\"]}" --profile aa365-admin --region us-west-1
```

DBeaver: `localhost:15432`, db `aa_cis_dev`.
