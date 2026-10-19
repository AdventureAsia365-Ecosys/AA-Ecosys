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
- [ ] **Docs:** "Docs impact" của issue đã làm trong cùng PR (CONTEXT.md / ADR / runbook / contract / trang catalog `docs/README.md`), hoặc ghi "N/A". Trang catalog theo `docs/STYLE.md` (front-matter, CLI một dòng, không ID thô); chỉ bump `last_reviewed` khi đã kiểm với hệ thật.
- [ ] **Changelog:** PR `feat`/`fix` người dùng thấy → tiêu đề PR đọc được như một dòng CHANGELOG (release-please lấy từ đây khi AA-891 xong).
- [ ] **LLM:** đổi prompt/model/route → ghi run ID eval chạy tay/dispatch trên golden set AA-729 vào PR (D-23; không có trigger theo PR). `prompt_version` chỉ khi ledger v2 (AA-804) đã có.
- [ ] **Cost:** thêm resource AWS hoặc lượt chạy trả phí → ghi ước tính USD/tháng trong PR body (DM-10.7); resource mới có tag `App` (DM-10.1).

## 2. Guard trước merge backend

- CI (`deploy-dev.yml`) tự chặn deploy khi `shared.job` còn queued/running. Override chỉ Nghiệp, phải ghi lý do
  (`docs/ops/runbooks/deploy-gate-override.md`). Kind có cờ `deploy_gate_exempt` không tính (từ AA-751 không kind nào
  dùng; `ops_rds_role_connections` đã nghỉ, sampler tự huỷ row của nó); `/admin/job-runner/deploy-gate` liệt kê ở `exempt_kinds`.
- Bị chặn → không override để "cho nhanh". Chờ job xong, hoặc hỏi Nghiệp nếu job treo.
- Có wave đang chạy → không merge PR backend/pipeline dù CI cho qua (`aa-wave-rerun`). PR chỉ FE thì được merge.
- Kiểm tay khi cần:

  ```sql
  SELECT kind, status, count(*) FROM shared.job WHERE status IN ('queued','running') GROUP BY 1,2;
  ```

## 3. Sau deploy — verify live

1. **Revision:** api và worker cùng image SHA, rollout COMPLETED.

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker --profile aa365-admin --region us-west-1 --query "services[].{n:serviceName,td:taskDefinition,r:deployments[0].rolloutState}"
   ```

2. **Worker:** log có `job_worker_started` cho đủ mọi kind.
3. **API:** curl **từng endpoint đã đổi** trên domain thật → 200 + đúng shape (field chính, số dòng > 0 khi phải có dữ liệu).
4. **UI:** trang đã đổi → `aa-ui-verify`.
5. **Infra:** `terraform-plan.yml` trên PR đã xem; apply qua `gh workflow run terraform-apply.yml --repo AdventureAsia365-Ecosys/AA-CIS-Infra --ref main`. IAM vừa cấp mà apply lỗi → chạy lại lần 2 (eventual consistency).

## 4. Đánh Done

Chỉ khi mục 3 pass. Comment vào issue theo mẫu:

```text
Verified live <dd/mm>:
- PR: #<n> (merged <sha>), ECS api :<rev> / worker :<rev>
- <endpoint> → 200, <tóm tắt shape/số dòng>
- UI: <trang> — screenshot đính kèm / link
- Docs: <file/ID catalog đã sửa, hoặc N/A> · Cost: <0 USD / ước tính USD/tháng>
- Ghi chú: <giới hạn còn lại, issue tách ra nếu có>
```

Thiếu bằng chứng nào → để In Review và ghi rõ còn thiếu gì.

## 5. Rollback (AA-869)

Deploy hỏng mà circuit breaker ECS không tự lùi → lùi app trước, sửa sau. DB không lùi theo app (migration chỉ tiến).
Các bước đầy đủ (kiểm, verify, rollback từng bước) nay nằm ở runbook — AA-892 chuyển từ đây sang:

- CIS api + worker: `docs/ops/runbooks/rollback-cis.md` (đã diễn tập S241).
- Booking: `docs/ops/runbooks/rollback-booking.md`. Vercel: `docs/ops/runbooks/rollback-vercel.md`.
- Lambda TripPlanner: `docs/ops/runbooks/rollback-tp-lambda.md`. Terraform: `docs/ops/runbooks/rollback-terraform.md`.
- Mục lục + playbook sự cố: `docs/ops/README.md`. Sự cố ảnh hưởng người dùng → `docs/ops/incident-response.md`.
