---
name: aa-ship
description: Quy trình từ PR tới "Done" cho các repo AA_Ecosys — kiểm trước merge, guard deploy khi còn job, verify live sau deploy (api + worker + UI), và chỉ đánh Done trên Linear khi có bằng chứng. Dùng khi chuẩn bị merge PR, deploy, Terraform apply, hoặc định chuyển issue sang Done.
---

# aa-ship

Mục tiêu: "Done" luôn nghĩa là đã chạy đúng trên môi trường thật, có bằng chứng.

## 1. Trước khi mở/merge PR

- [ ] Branch `feature|fix|chore/aa-xxx-<mô tả>` từ `main`; PR vào `main`.
- [ ] Commit và PR body ghi **`Refs AA-xxx`**. Không dùng `[AA-xxx]` hay `Fixes AA-xxx` — chúng tự đóng issue khi merge.
- [ ] CI xanh — 5 job required: Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check (Vercel không nằm trong 5 job, kiểm riêng cho FE).
- [ ] PR có migration → sau khi migration apply, regenerate `docs/architecture/db-schema-reference.md` ở repo gốc AA-Ecosys (PR riêng, cùng ngày, link chéo hai PR).
- [ ] Thêm thư mục top-level → thêm `COPY` vào Dockerfile và path filter `deploy-dev.yml`.
- [ ] PR frontend → `npm run build` đầy đủ chạy local (Node 22 qua nvm), rồi `aa-ui-verify`.
- [ ] PR xoá bảng/dữ liệu → quy trình DRY RUN (`aa-cis-schema/references/destructive-ops.md`).

## 2. Guard trước merge backend

- CI (`deploy-dev.yml`) tự chặn deploy khi `shared.job` còn queued/running. Override chỉ Nghiệp, phải ghi lý do.
  Kind có cờ `deploy_gate_exempt` (hiện chỉ `ops_rds_role_connections`, chạy mỗi 5 phút, AA-832) không tính; `/admin/job-runner/deploy-gate` liệt kê ở `exempt_kinds`.
- Bị chặn → không override để "cho nhanh". Chờ job xong, hoặc hỏi Nghiệp nếu job treo.
- Có wave đang chạy → không merge PR backend/pipeline dù CI cho qua (`aa-wave-rerun`). PR chỉ FE thì được merge.
- Kiểm tay khi cần:
  ```sql
  SELECT kind, status, count(*) FROM shared.job WHERE status IN ('queued','running')
     AND kind <> 'ops_rds_role_connections' GROUP BY 1,2;   -- kind 5 phút, deploy-gate bỏ qua
  ```

## 3. Sau deploy — verify live

1. **Revision:** api và worker cùng image SHA, rollout COMPLETED.
   ```
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker --profile aa365-admin --region us-west-1 --query "services[].{n:serviceName,td:taskDefinition,r:deployments[0].rolloutState}"
   ```
2. **Worker:** log có `job_worker_started` cho đủ mọi kind.
3. **API:** curl **từng endpoint đã đổi** trên domain thật → 200 + đúng shape (field chính, số dòng > 0 khi phải có dữ liệu).
4. **UI:** trang đã đổi → `aa-ui-verify`.
5. **Infra:** `terraform-plan.yml` trên PR đã xem; apply qua `gh workflow run terraform-apply.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main`. IAM vừa cấp mà apply lỗi → chạy lại lần 2 (eventual consistency).

## 4. Đánh Done

Chỉ khi mục 3 pass. Comment vào issue theo mẫu:

```
Verified live <dd/mm>:
- PR: #<n> (merged <sha>), ECS api :<rev> / worker :<rev>
- <endpoint> → 200, <tóm tắt shape/số dòng>
- UI: <trang> — screenshot đính kèm / link
- Ghi chú: <giới hạn còn lại, issue tách ra nếu có>
```

Thiếu bằng chứng nào → để In Review và ghi rõ còn thiếu gì.

## 5. Rollback (AA-869)

Deploy hỏng mà circuit breaker ECS không tự lùi (task vẫn healthy nhưng app sai) → lùi app trước, sửa sau.
DB không lùi theo app: migration chỉ tiến (lùi = migration mới); app cũ phải chạy được trên schema mới.

**ECS (CIS api/worker, Booking):** trỏ service về revision task-def trước. ECR CIS và Booking là
IMMUTABLE, giữ 30 image `dev-*` gần nhất (CIS), nên revision trong khoảng đó còn image.
```
aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api --profile aa365-admin --region us-west-1 --query "services[0].taskDefinition" --output text
aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --task-definition aa-cis-dev-api:<rev-1> --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text
aws ecs wait services-stable --cluster aa-cis-dev-cluster --services aa-cis-dev-api --profile aa365-admin --region us-west-1
```
- Worker: cùng lệnh với `aa-cis-dev-worker` / `aa-cis-dev-worker:<rev-1>`; api và worker phải về **cùng SHA**.
- Kiểm: rollout COMPLETED, image của task = `dev-<sha cũ>`, `/health` 200.
- Lùi xong: revert PR lỗi trên `main` (deploy bình thường đưa service lên revision mới). Không "roll forward"
  bằng tay sang revision lỗi.
- `shared.job` đang chạy: rollback cũng restart container, nên vẫn hỏi deploy-gate trước; sự cố SEV1 thì
  Nghiệp quyết.

**Vercel (CIS admin/portal, TripPlanner, Booking FE):** deploy do CI tạo (S241). Dashboard → project →
Deployments → bản production trước → **Instant Rollback** (Hobby: chỉ về bản production ngay trước). Sau
rollback, Vercel tắt tự gán domain production cho deploy mới: khi bản sửa đã lên, vào bản đó → **Promote**
(hoặc `vercel promote <url> --token …`), không thì domain vẫn đứng ở bản cũ.

**Lambda TripPlanner:** revert PR lỗi trên `main`, `deploy-lambdas.yml` tự deploy lại. Không dispatch từ nhánh
khác: role deploy chỉ tin `sub` = `…:ref:refs/heads/main`, nên AWS từ chối.

Sự cố ảnh hưởng người dùng → `docs/ops/incident-response.md`.
