# S297 — RDS tự quản mật khẩu, xoay key, chỉ USD, tự rollback API, vá NAT

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 28/11 ~08:55 → ~17:30 +07.
**Snapshot cuối phiên:** [state-snapshot.md](../audits/2026-11-28-S297-session/state-snapshot.md) · **Jira:** [jira-drafts.md](../audits/2026-11-28-S297-session/jira-drafts.md) · **Ảnh UI:** [ui/evidence.md](../audits/2026-11-28-S297-session/ui/evidence.md)

## Trạng thái

- Nghiệp "ok, làm hết 10 việc" (~09:05). 10 lane (lane.js) + 1 lane phát sinh (vá NAT); 3 lane chạy lại review/fix sau khi hết limit 5 giờ và đổi tài khoản Claude.
- **Đóng 3 issue:** AA-1155 (Done-with-scope), AA-1193 (Done), AA-1191 (Done-with-scope).
- **In Review (phần còn lại là bước của người hoặc ngày):** AA-1182, AA-1183, AA-1184, AA-1185, AA-1110, AA-1117, AA-1054.
- **Chờ số migration:** AA-1187 bước 2 (bk-077 cần bk-076 của chuỗi AA-1061).

## Thay đổi Codebase

| Repo | PR | Nội dung |
|---|---|---|
| AA-Ecosys (root) | #1056 / #1057 / #1058 / #1059 / #1060 / #1061 / #1062 / #1063 / #1064 / #1065 | Cổng go-live 2 ngày; gói liên tục; runbook rollback tự động; lịch ops; runbook key ceremony; kiểm hạn xoay secret; sổ secret S297; runbook ngày pilot; schema reference (CIS 498); hợp đồng + DRY RUN USD |
| AA-CIS-App | #1725 / #1726 / #1727 / #1728 / #1729 / #1730 / #1731 | Tự rollback api+worker; tab Calendar; env ci-bot; CIS 495–496 rào pilot + code; CIS 497–498 tiền tệ + code USD |
| AA-Booking | #342 / #343 / #344 / #345 / #347 | Tự rollback; env ci-bot; rào pilot; USD; ô tổng billing ẩn tiền tệ tắt |
| AA-Partner | #409 / #410 / #411 | Tự rollback; env ci-bot; USD (kèm sửa 3 test integration) |
| AA-TripPlanner-Web | #309 | env ci-bot |
| AA-CIS-Infra | #1055 / #1056 / #1057 / #1058 / #1059 / #1060 / #1061 / #1066 | Swap + timeout vá NAT; kênh Slack (tắt); SNS cho role deploy; RDS tự quản master + công cụ xoay client secret; quyền metadata cho kiểm xoay; ci-bot; script tắt danh tính E2E; DRY RUN VND |

## Thay đổi Hạ tầng

- **Cửa sổ tắt auto mode (~12:00–13:00):** apply bootstrap local (`tf_apply_sec` + 3 policy SNS); CI Terraform Apply run 46110618114 (2 add, 3 change); swap NAT 1 GB + vá (79 gói, 0 lỗi); nhãn root #1059; dismiss 2 cảnh báo CodeQL báo nhầm; RDS: apply 1 (`manage_master_user_password`), apply 2 (xoay 180 ngày), kiểm qua DB Migrate run-script, xoá `TF_VAR_DB_PASSWORD`, lên lịch xoá `aa-cis/dev/rds` (khôi phục được tới 05/12).
- Key CI bot: tech lead tạo key App mới (quyền Secrets + Environments đọc); `setup` 6 env `ci-bot`; 5 PR workflow merge; `cleanup` xoá 6 bản cũ.
- Migration: CIS 495–496 (rào pilot), 497–498 (tiền tệ) qua wave (contract apply).
- Drill tự rollback trên Dev: Booking (:183), CRM (:230), CIS (:1310/:879) → sau đó deploy lại main CIS (:1312/:881) để revision mới nhất = đang chạy.

## Bằng chứng verify

- AA-1182: DB Migrate run 46113574430 `managed_secret status=active`, `legacy_master=refused`; run 46113801136 `legacy_master=absent`; `describe-secret` → `True 180`.
- AA-1183: run 46116536462 (168 dòng); `plan` sau cleanup: 6 bản cũ `gone`; lịch ops check OK (0 overdue) sau sổ secret.
- AA-1185: patch state Install 05:21:59Z, 79/0/0; CIS + Booking ready 200 trước và sau.
- AA-1193: 3 drill, `ROLLED BACK` + health trả commit cũ; issue deploy-smoke-red mở rồi đóng (Booking #346, Partner #412, CIS #1732).
- AA-1191: 27 ảnh UI (CIS, Booking, Partner), 0 lỗi console; DRY RUN: CIS 7 gói còn giá VND, Booking 1 hoá đơn nháp VND, CRM 1 đại lý thử 4 proposal VND — không quy đổi.
- AA-1184: drill OC-999 hiện đỏ trên tab Calendar (ảnh 01-*); Ops calendar run 46130888902 OK.
- AA-1054: CIS `/health/ready` schema 496→498; post-deploy verify Booking + CIS xanh khi công tắc tắt.

## Quyết định của Nghiệp

- "ok, làm hết 10 việc".
- Comment Jira bỏ nhãn "Claude": đăng bằng token API của Nghiệp (`secret_manager/Jira/jira-token`, tạo 28/11).
- Tự làm bước tay: App ci-bot (quyền + key mới), revoke 3 PAT, token Vercel, xoá key acc1 trên IAM; "em xoá đi" (profile acc1 local — auto mode chặn, còn lại cho Nghiệp).
- DMARC: "làm cho tôi" — agent không có quyền Cloudflare, để lại hướng dẫn. Kênh Slack: "chưa cần".

## Jira

(điền sau khi Nghiệp duyệt và đăng — xem jira-drafts.md)

## Còn lại

- ≥ 28/11 23:50Z: AA-1061 DRY RUN bk-076 → Nghiệp duyệt pins → chuỗi; rồi ship AA-1187 (bk-077, gói NCC).
- 29/11: AA-873 số đếm ~05:00Z, 4 lịch tự tắt 09:17–09:32Z, dọn role. CN 29/11 21:00Z: lượt vá NAT theo lịch đầu tiên có swap.
- Tay Nghiệp: xoá key App cũ; xoá khối `[acc1-legacy-default]`; TXT DMARC trên Cloudflare; import `.ics`; tabletop với chủ DN (AA-1110); hạn mức vendor LLM + ngày ceremony (AA-1182).
- Follow-up: rotation_check / register_check nhận tiền tố `rds!db-`; CRM (A10c) chưa đọc rào pilot; mô tả platform `crm.ai_budget_usd_monthly` có mã issue; dòng setting list hiện "Allowed —".

## Lưu ý kỹ thuật cho phiên sau

- Hai lane cùng owner migration → giao `migStart` riêng; drill CIS chạy cuối, sau mọi deploy; PR RDS merge sau CI apply, apply -target 2 lượt (lessons.md).
- App aa-agent không có quyền code scanning: dismiss cảnh báo CodeQL bằng gh của tech lead.
- `ship_merge.py` rớt khỏi merge queue mà mọi check xanh → xem run CI của merge_group (`gh run list --event merge_group`).
