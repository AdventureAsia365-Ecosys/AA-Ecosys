# S240 — 16/10/2026 — Alarm RDS, tenant pool đợt 2 (6 cờ bật tự động), template bảng job (X6), dọn Vercel

**Tác nhân:** Claude Code (VS Code, Ultracode). Phiên chính điều phối, khoảng 12 workflow nhiều agent:
build trong worktree → review đối kháng → sửa. Agent con chỉ commit; push, PR, merge, Terraform apply,
DB Migrate, ECS exec, Redis, Vercel và Linear đều do phiên chính làm.
**Audit / bằng chứng:** `docs/audits/2026-10-16-S240-aa859/`, `docs/audits/2026-10-16-S240-aa751/`,
`docs/audits/2026-10-16-S240-vercel/`.

## Trạng thái cuối phiên
- **ECS CIS:** api / worker cùng image (xem dòng "Trạng thái cuối" của memory S240 cho revision cuối).
- **Booking:** `/booking/health/ready` = **bk-013**.
- **Migration áp trong phiên** (DB Migrate check → apply, `shared.job` rảnh):
  - CIS **241** (aa_app_user mất mọi quyền trên 33 quan hệ không RLS; RLS `angle_gate_option`; grant cột `tenant_integrations`);
  - CIS **242** (`shared.job` theo template: CHECK kind/lease/attempts, trigger `updated_at`, index, autovacuum 0,02/50);
  - Booking **bk-013** (`cancel_requested`, `progress`, `cost_usd`, `parent_job_id`, index theo template).
- **Terraform** (luôn plan có target **từ `main` đã merge**, đọc plan rồi mới apply):
  - #155 AA-832 alarm RDS + metric theo role + sửa drift parameter group RDS;
  - #156 trần autoscale api 10 → 7;
  - #160 bỏ lịch Lambda 5 phút, alarm tồn đọng job (CIS + Booking), IAM `AA/Jobs/*`, **bỏ email OK trên 28 alarm**.
- **Cờ tenant pool AA-859 (Redis):** cả 6 cờ `aa859:*` **bật** sau kiểm tự động.
- **Vercel:** xoá 5 project cũ; xoá 342 preview > 7 ngày; bỏ deploy hook trùng (#783). Team chạm trần
  ~100 deployment/24h từ 12:55Z (hồi dần từ 15:08Z, phần lớn từ 00:22Z 17/10).
- **CloudWatch:** xoá log metric filter + alarm cũ `AA296-T3-Fallback-*` (tạo tay, không action, chưa từng bắn).
  Custom metric còn 10 (đúng free tier).
- **`shared.job`:** rỗng lúc kiểm cuối.

## Quyết định của Nghiệp
- Duyệt danh sách đầu phiên ("ok làm đi"): AA-777 đóng theo kết quả r7 + tách follow-up (AA-865).
- **Tắt auto mode nhiều lần** để mình tự merge / apply / DB Migrate / xoá tài nguyên.
- AA-859:
  - `/admin/atoms`: kiểm log 30 ngày rồi xoá nhánh tenant, không cờ (WAF: 0 lượt Bearer / 1.041);
  - bật cờ **tự động** (bật → kiểm A/B + log → sai thì tự tắt), không duyệt tay từng cờ;
  - sizing **A**: tenant pool 2/task + trần autoscale 7;
  - **giữ AA-859 mở** (đợt 3, đợt 4, D5b còn lại).
- AA-751: **làm tiếp**; TripPlanner: `tripplanner.job` làm **cùng AA-861** (phương án A), không tạo bảng rỗng.
- Vercel: đồng ý hết đề xuất; xoá `visionserve-bundle-int8`, `statusboard-ai-*`, `aa-acp-portal`, `cis-agentops`.
- Token GitHub + mật khẩu RDS master bị in vào transcript local (lỗi MFA): **để nguyên, xoay khi lên prod**;
  chỉ cần xoá bản local và không push lên repo.
- Cảnh báo: **CloudWatch, chỉ email khi ALARM** (không email OK); bỏ chuỗi Lambda 5 phút, lấy số liệu
  **trong tiến trình app**; xoá metric `ACP/Pipeline` cũ cho đỡ tốn.

## Thay đổi Codebase
- **CIS:**
  - #771 AA-832 job kind theo role (sau đó gỡ ở #786);
  - #772 mig 241; #773 PR-A disconnect 2 transaction + UUID + timing; #774 pool 2 + cờ + gauge;
  - #775 `/admin/atoms` chỉ staff; #776 W2; #777 W4; #778 W3; #779 W9; #780 W6; #781 W5a; #782 CONTEXT;
  - #783 bỏ deploy hook Vercel trùng;
  - #784 template bảng job + comparator + mig 242; #785 xoá chỗ đọc `acp_runs` + Terraform canary chết;
  - #786 sampler trong tiến trình api (AA/RDS + AA/Jobs/CIS), gỡ endpoint/kind 5 phút.
- **Booking:** #24 bk-013; #25 trả job khi tắt + `cancel_requested` + test template; #26 sampler `AA/Jobs/Booking`.
- **Infra:** #155, #156, #157 (copy 241), #158 (DB Migrate idle check), #159 (copy 242 + bk-013), #160.
- **TripPlanner:** #93 docs chuỗi Cohere.
- **Gốc:** PR cuối phiên (log này, backlog, audits, lessons, data standards C4.1/C2.2, schema-ownership).

## Bằng chứng verify chính
- **AA-832:** `max_connections` 181 → ngưỡng 108; metric 3 role khớp đếm tay; thử SNS ALARM → OK (10:55Z → 11:02Z).
- **AA-859:**
  - P0 trước 241 (aclexplode): `gate_241_ready=true`; sau 241: invariant **0 vi phạm**;
  - disconnect bấm 2 lần live: 200/200 `[true,false]`, event `aa859_integration_disconnect_raced`;
  - 6 cờ: piece_edit 6/6, angle_gate 9/9, unpublish 11/11 (đăng + gỡ thật trên site WP test), integration 9/9,
    t2 reads 8/8 (khớp baseline cờ tắt), t2 write 12/12 (lượt 2, khôi phục trạng thái V bằng 1 UPDATE);
  - 90 phút log: 0 lỗi tenant pool / 42501.
- **AA-751:** DB Migrate **từ chối** apply khi `booking.job` bận (run 38924913602) và khi `shared.job` bận
  (run 38925718483), exit 7; huỷ probe → apply bk-013 + 242 OK; shape 2 bảng khớp template; worker CIS chạy
  job sau 242; `/admin/acp/stuck-runs` 404.

## Còn lại (việc chưa xong)
- AA-859: D5b, đợt 3 (mig 243?: brand identity + publish), đợt 4 (atoms / subject / planning, mig tour_atoms).
- AA-751: deploy gate Booking (B3/B4); thử bắn alarm tồn đọng job (window B); docs R1.
- AA-861 + `tripplanner.job` + Lambda worker.
- Vercel: sửa poller admin CIS (CPU); CI tạo preview theo `frontend/**`; nhóm portal AA-836/863/834.
- 2 alarm Lambda TripPlanner còn `ok_actions` (cố ý loại khỏi apply #160 để không đụng artifact S3 TP).
- Rotate admin secret (từ 17/10). Token GitHub + mật khẩu RDS: khi lên prod.

## Lưu ý kỹ thuật cho phiên sau
- Terraform apply **chỉ từ `main` đã merge**; plan có target có thể kéo theo dependency (parameter group RDS,
  object S3 của TP): đọc kỹ, loại khỏi target nếu không cần.
- `export $(aws configure export-credentials …)` khi MFA hết hạn in toàn bộ env → luôn `C=$(…) || exit 1`.
- Vercel: deployment bị Ignored Build Step huỷ **vẫn tính trần**; `git.deploymentEnabled` lọc theo nhánh, không theo thư mục.
- ECS exec output dài bị cắt → ghi JSON lên S3; zsh không tách `$P` thành nhiều tham số.
- Probe job: đặt `run_after` tương lai để worker không claim mà DB Migrate vẫn tính bận.
