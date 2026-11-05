# S269 (05/11/2026): bảo vệ pilot + load test, R3 đóng, R2 đóng lát, key Anthropic + 13 model, R4 hoá đơn đại lý + bậc giá + G1–G6

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree qua `tools/workflows/lane.js` → reviewer độc lập → lượt sửa; PR
bảo mật/quyền thêm vòng review đối kháng; điều phối merge/deploy/DB Migrate/Terraform/kiểm live).
05/11 ~09:30 → ~18:00 +07 (02:30Z → 11:00Z). Đổi tài khoản Claude 1 lần (chạm hạn mức 5 giờ 2 lần: 11:00 và ~16:00, lane resume).
Số liệu cuối phiên lấy từ snapshot `docs/audits/2026-11-05-S269-close/state-snapshot.md`.

Môi trường: 3 cửa sổ tắt auto mode (nâng owner AA-1036; cắm key Anthropic; sync user E2E + Terraform Apply ×2). Hook PII mới (root #548)
chạy ngay trong phiên, chặn đúng nhiều lệnh của chính điều phối.

## Quyết định của Nghiệp (tech lead)

- **~09:35:** "ok làm đi" — danh sách 9 issue S269.
- **~11:05:** gửi key API Anthropic (được tài trợ) → cắm vào gateway; **~11:15** "tạm thời bật ưu tiên dùng từ api anthropic-direct", kiểm mọi họ model.
- **~11:20:** thư mục `secret_manager` đã chuyển ra ngoài repo (`/home/nghiep/projects/secret_manager`), **dùng phải hỏi**; đầu phiên phải báo
  trạng thái LLM gateway; **cắm mọi model còn lại vào catalog làm dự phòng**.
- **~14:55:** master plan phải cập nhật đúng link tracker (đã publish v45 + tab Phiên).
- **~15:40:** **làm hết G1–G6** (benchmark Asian Trails); xong việc #1–5 thì chốt; **AA-741 sang S270**; **nháp Jira gom sang S270**; tăng tốc.
- Hỏi về Terratest: chỉ để biết, **không tạo issue**.

## Kết quả theo issue

Done: **AA-969**, **AA-1036**.

| Issue | Trạng thái | Kết quả | PR / bằng chứng |
|---|---|---|---|
| AA-969 CRM-37a | **Done** | Load test 50 đại lý `lt-*`: 6.482 req, 0 lỗi, calm p95 238/238/288 ms, refused 0 %. d16: hook PII agent + guard run-script, job dọn bỏ qua pilot, crm-044 `is_pilot`, backup đêm, diễn tập khôi phục (southern-cross 24/24, sen-vang 5.206/5.206). **Lỗi thật bắt được**: export mở `message_delivery`/`ops_release` sai DEK → sửa + guard AST + cảnh báo backup pilot | root #548; Infra #678; Partner #222, #223, #224, #230; CIS #1314; Booking #182; `docs/audits/2026-11-05-S269-aa969-loadtest/` |
| AA-1036 R3 | **Done** | User mời thật 7/7; request add-on → staff duyệt 15/15 → tenant 4/4; owner CRM-only có trang Add-ons trong CRM (`tenant.addons.v1`, scope M2M `cis.tenant/addons`); suppressions Partner `{}` | root #547; CIS #1313; Partner #221; Infra #677; ảnh `docs/audits/2026-11-05-S269-live-verify/` |
| AA-1035 R2 | In Review | Relay phạm vi staff CRM (fail-closed, kiểm danh tính), Tenant QA theo sổ, bỏ alias reviewer (375), crm-045 giữ địa chỉ mời; 2 vòng review đối kháng | CIS #1315, #1316; Partner #226, #227; root #549; Infra #679 (apply) |
| AA-1008 kit | In Review | ShellFrame 3 app, visual job (self-test 8/8, sau deploy xanh), suppressions `{}` ở 3 repo; còn H3 (tech lead) | CIS #1317; Partner #228, #229; Booking #184, #185; TP #225 |
| AA-1037 R4 | In Review | Lõi hoá đơn đại lý (bk-041/042, CIS 377, tick công nợ) + G1/G2/G4/G5/G6 (bk-044, `booking.b2b.v1` 1.3) | root #556, #560; Infra #684; Booking #186, #187, #189, #191; CIS #1320, #1321 |
| AA-1030 bậc giá | In Review | Bậc Standard/Silver/Gold 0/3/6 %, rate card, maker-checker (bk-043), markup bán lẻ CRM (crm-046), G3 bảng giá theo đại lý (`booking.b2b.v1` 1.4) | root #558, #564; Booking #188, #190, #192; Partner #231, #232 |
| AA-1042 gateway | In Review | Key Anthropic cắm (AA-1026), ưu tiên API (route v6), CIS 376: +9 model API, 13/13 probe ok | CIS #1318, #1319; root #552 |
| AA-820 DPA | In Progress | Gói DPA v0.2 + 4 phụ lục + bộ điều khoản pilot (C1–C12 cần luật sư) | root #546 |
| AA-710 benchmark | In Progress | Ghi chú Asian Trails (18 nguồn); G1–G6 đã làm; nháp KAN-20 gom S270 | root #545 |
| AA-855 | Backlog | Linear sửa từ In Progress về Backlog (lệch) | — |

## Còn mở và vì sao

- **AA-1035:** chưa có user E2E customer_success để kiểm live "chỉ thấy tenant được giao".
- **AA-1008:** H3 — đặt kit + visual thành check bắt buộc (tech lead đăng nhập GitHub).
- **AA-1037:** luồng hoá đơn live đầy đủ (2 staff maker-checker), fixture layout-mock trang billing, tab Billing Tenant 360, lát bỏ B2C.
- **AA-1030:** kiểm live 2 đối tác khác bậc + ảnh; nút tải bảng giá trong CRM (chờ quyết định vai trò được xem giá AA).
- **AA-741:** sang S270 (tech lead).
- **Follow-up:** tenant E2E có cả tài khoản CIS lẫn owner CRM-only; image CIS chưa `apt-get upgrade` (Trivy sẽ đỏ như Partner/Booking).

## Chi phí phiên

LLM: probe/kiểm ~0,006 USD (Anthropic API) + ~0,0002 khác; 0 lượt pipeline trả phí. Secret mới ~0,40 USD/tháng.

## Trạng thái kiểm cuối phiên

Chi tiết: `docs/audits/2026-11-05-S269-close/state-snapshot.md`.

- ECS (mỗi family chạy revision mới nhất, 1/1 COMPLETED): cis-api :1016 + worker :582 `dev-4aed550d`; booking :104 `f81ecac6`; crm-api :136 + crm-web :110 `15c7de1c`.
- Migration: CIS **377**; Booking **bk-044**; CRM **crm-046**; TripPlanner không đổi.
- Bảng job: `shared.job` 0, `booking.job` 0, `crm.job` 3 job định kỳ. Không wave.
- Gateway: `anthropic-direct` ON, route v6 ưu tiên API; acc3 5.x vẫn bị từ chối.

## Jira

Chưa đăng — tech lead gom nháp S268 + S269 (kèm KAN-20) sang S270.

## Việc cần làm đầu phiên sau (S270), theo thứ tự

1. Jira: một lượt duyệt cho nháp S268 + S269 + KAN-20 (`docs/research/2026-11-05-asian-trails-b2b-benchmark/kan-20-jira-comment-DRAFT.md`); PR-20 kỳ 4 từ thứ Hai 09/11.
2. AA-741 phase 0 (tech lead dời sang S270).
3. Kiểm live AA-1037 (nháp hoá đơn, thanh toán maker-checker, trạng thái công nợ tới CIS, credit stop) và AA-1030 (2 đối tác khác bậc) → đóng.
4. AA-1035: tạo user E2E customer_success, kiểm live phạm vi → đóng.
5. AA-1008 H3 (tech lead), rồi đóng.
6. **≥10/11 ~12:00Z:** áp 336, bật lại `DB_AUTO_APPLY_CONTRACT` → đóng AA-1024; C4.3 W46 từ 09/11.

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- ecsx CRM/Booking mất lần chạy lúc khởi động (không `.out`); đếm bảng CRM có RLS bằng `crm_app` trần ra 0 giả.
- Guard load test không dựa một dòng sampler (job định kỳ 15′); zsh `\<`; boto3 MFA getpass.
- Contract migration Dev phải check → apply tay khi auto-apply contract tắt; cache catalog LLM ~5′ sau migration.
- Hook PII chặn ghi + chạy cùng lệnh và `cd` + đường dẫn tương đối.
