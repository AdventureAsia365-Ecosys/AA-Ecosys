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
- [ ] PR có migration → `docs/architecture/db-schema-reference.md` được regenerate **trong cùng PR**.
- [ ] Thêm thư mục top-level → thêm `COPY` vào Dockerfile và path filter `deploy-dev.yml`.
- [ ] PR frontend → `npm run build` đầy đủ chạy local (Node 22 qua nvm), rồi `aa-ui-verify`.
- [ ] PR xoá bảng/dữ liệu → quy trình DRY RUN (`aa-cis-schema/references/destructive-ops.md`).

## 2. Guard trước merge backend

```sql
SELECT kind, status, count(*) FROM shared.job
WHERE status IN ('queued','running') GROUP BY 1,2;
```
- Không lọc theo `created_at`.
- \> 0 → **không merge PR backend/pipeline**. PR chỉ FE thì được merge.
- Có wave đang chạy → chờ wave xong (`aa-wave-rerun`).
<!-- Khi AA-725 xong: thay mục này bằng "CI tự chặn; override cần lý do" -->

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
