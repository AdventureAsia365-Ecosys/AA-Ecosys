# ECS exec + S3 — query DB AA-CIS

RDS trong private subnet → chạy script Python (asyncpg) trong container `api` qua ECS exec, lấy kết quả qua S3. Script có thể import secret trực tiếp (dưới) hoặc dùng app code (`sys.path.insert(0, "/app")` rồi `from shared.secrets import get_database_url`) — cả hai chạy được; bản dưới độc lập app, dùng được cả khi code app đổi.

## Script mẫu (asyncpg, ghi kết quả ra file)

```python
import asyncio, json, boto3, asyncpg
from urllib.parse import urlparse

async def main():
    sm = boto3.client("secretsmanager", region_name="us-west-1")
    dsn = sm.get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"].strip()  # DSN thô
    u = urlparse(dsn)
    conn = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username,
        password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await conn.fetch("SELECT ...")  # luôn schema-qualify
    with open("/tmp/result.json", "w") as f:
        json.dump([dict(r) for r in rows], f, indent=2, default=str)
    await conn.close()
    boto3.client("s3", region_name="us-west-1").upload_file(
        "/tmp/result.json", "aa-cis-bronze-005097885195", "scripts/result.json")

asyncio.run(main())
```

## Chạy (mỗi lệnh một dòng)

```bash
aws s3 cp /tmp/script.py s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1 --expires-in 300)
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s.py && python3 /tmp/s.py && echo DONE'" --profile aa365-admin --region us-west-1
aws s3 cp s3://aa-cis-bronze-005097885195/scripts/result.json /tmp/result.json --profile aa365-admin --region us-west-1
```

## Lưu ý

- `execute-command` có thể treo tới ~120 giây → chạy nền, poll S3. Script > 5 phút → chia nhiều bước.
- zsh không word-split biến chứa nhiều flag → `bash -c` hoặc flag rời.
- Script cần code app → `sys.path.insert(0, "/app")`.
- Dùng task của `aa-cis-dev-api` cho query. Job dài thì chạy trên worker qua `shared.job`, không chạy qua exec.

## Log

- ECS: `/ecs/aa-cis-dev` — một log group chung cho cả api và worker, phân biệt bằng stream prefix. Retention 14 ngày.
- Lambda: `/aws/lambda/aa-cis-dev-<name>` (ingestion, validation, seo, export, content, brand-brief-parser, authorizer, dfs-balance-check).

## DBeaver qua SSM port-forward

```bash
TASK_ID=$(echo $TASK_ARN | cut -d'/' -f3)
RUNTIME_ID=$(aws ecs describe-tasks --cluster aa-cis-dev-cluster --tasks $TASK_ARN --profile aa365-admin --region us-west-1 --query 'tasks[0].containers[0].runtimeId' --output text)
aws ssm start-session --target "ecs:aa-cis-dev-cluster_${TASK_ID}_${RUNTIME_ID}" --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters "{\"host\":[\"<RDS endpoint>\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"15432\"]}" --profile aa365-admin --region us-west-1
```
DBeaver: `localhost:15432`, db `aa_cis_dev`.
