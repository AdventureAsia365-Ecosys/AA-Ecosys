# S293: 25/11/2026: trợ lý ops A2, trang Eval runs, kit dự án 1.1–1.3, External checks từ worker, tenant read + rollup

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). Khoảng 12:20 → 17:30 +07. Lane song song qua `tools/workflows/lane.js` (a–h). Tới ~13:10 tài khoản cũ chạm giới hạn 5 giờ; sau khi đổi tài khoản, lane resume bằng `resumeFromRunId`. MFA hết hạn lúc 18:44.

## Trạng thái

- **Done:** AA-1178, AA-1179 (mới), AA-1180 (mới).
- **Đã ship, còn bước của người:**
  - AA-1154 A2: tech lead bấm "I ran this" một thẻ.
  - AA-1169: tech lead đọc tay 12 mẫu.
  - AA-1103: kit v1.3.0 đã đủ; còn duyệt khoá L8.
- **Chờ thứ Năm:** AA-1166 (duyệt ISMS), AA-1157, AA-1158, AA-1155, AA-1148, AA-1173.
- LLM trả phí: **0 USD**.
- Snapshot: [state-snapshot](../audits/2026-11-25-S293-session/state-snapshot.md).

## Quyết định của Nghiệp

- ~12:35: duyệt cả 10 việc, kể cả tạo AA-1179. Deploy CIS rồi smoke lại, dừng deploy sau 22:00.
- ~15:00: "ok duyệt hết, làm tiếp, tăng tốc". Tạo AA-1180. Nháp Jira được duyệt, nhưng auto mode chặn đăng vì nháp chưa hiện nguyên văn → chờ tech lead xem bản nguyên văn rồi đăng.

## Thay đổi Codebase (merged)

- **AA-1178:** không có code mới; kiểm live dưới tải.
- **AA-1179:**
  - CIS #1694 `814c8024`: baseline anomaly-breaker cộng theo ngày UTC trên khoảng `created_at` (không sort, không temp).
  - Infra #1027 `f91fd30a`: 2 run-script chỉ đọc.
  - `REQUEST_TOURS_SQL` đã được viết lại từ S291.
- **AA-1169:** CIS #1695 `933529de` (Writing Lab › Eval runs + 3 GET chỉ đọc), root #1009.
- **AA-1154 A2:** root #1011, CIS #1696 `b4470f06` (490–491), CIS #1697 `8468884a`.
- **AA-1142 follow-up:** root #1013, CIS #1698 `ba334e05` (492–493), CIS #1699 `deeb3e2e`.
- **AA-1180:** CIS #1700 `c497ca97` (494), CIS #1701 `7886cb4c`. CIS #1702 chỉ sửa test.
- **AA-1103:**
  - project-template #1 `a6e3c8c4` (v1.1.0), #2 `408580c7` (v1.2.0), #3 `cd2fb6af` (v1.3.0);
  - root #1010, #1012 (bộ ship nhận repo `project-template`), #1015, #1016.
- **Khác:** Infra #1026 `f96ebd3d` (thay Dependabot #977); root #1014 (bot schema).

## Thay đổi Hạ tầng / dữ liệu Dev

- Migration CIS áp: 490, 491, 492, 493, 494.
- ECS cuối phiên: cis-api :1295 / worker :864 (7886cb4c), admin :106 (deeb3e2e); app khác không đổi.
- Rollup: chạy lại thủ công 17/11–25/11 (0 USD).
- Job nền kiểm AA-1178: `writing_memory_r0` baseline (0 USD).

## Bằng chứng verify

Thư mục `docs/audits/2026-11-25-S293-session/` (`evidence/`, `live/`).

- **AA-1178:** trong lúc job nền chạy 21′, 4 lượt `ops_status_sample` vẫn đúng nhịp (chờ ≤ 11 s), 0 queued.
- **AA-1179:** parity 136 request / 10 tenant lệch 0; baseline 30 case lệch 0; buffer giảm 150–194×; p95 60,3 ms; temp 0.
- **AA-1180:** rollup check ok=True; Jev 0,06664078 = 0,06664078; spec AA-1042/1045 pass.
- **AA-1142 follow-up:** worker chạy 3 lượt (08:54/09:04/09:19Z), mỗi lượt 8/8 host ok.
- **AA-1154 A2:** bảng `ops_assist_run` có (0 dòng), 3 setting có, sampler xanh sau deploy.
- **AA-1169:** trang Eval runs ở 1440/390, sáng/tối (danh sách lượt chạy, không có văn bản tenant).
- **AA-1103:** smoke từng tag (v1.1.0 có hook test pass; v1.2.0, v1.3.0 render đủ phần).
- **Smoke thứ Năm:** 4/4 đạt sau deploy cuối (ảnh `live/thu-smoke-*`).
- **Lỗi đã biết, không phải mới:**
  - Visual (deployed host) đỏ: Content workspace "new" cuộn ngang ở 390 px, có sẵn từ trước.
  - `/admin` gốc đẩy về `/login`: có từ trước.

## Jira

Chưa đăng. Tech lead nói "duyệt hết" nhưng auto mode chặn vì nháp chưa hiện nguyên văn. 9 nháp (S291 J1–J5, S292 J6–J9): `docs/audits/2026-11-25-S293-session/jira-drafts.md`. Đã dán nguyên văn ở tin nhắn cuối phiên; đăng sau khi tech lead xem.

## Việc đầu phiên sau (S294)

1. Thứ Năm 26/11: AA-1158, AA-1148, AA-1173, AA-1155, duyệt ISMS AA-1166, AA-1157.
2. Jira: đăng 9 nháp sau khi tech lead xem (hoặc tắt auto mode).
3. Tech lead:
   - AA-1154: bấm "I ran this" một thẻ;
   - AA-1169: đọc 12 mẫu;
   - AA-1103: duyệt khoá L8.
4. Sau thứ Năm:
   - savepoint Booking #331 + CIS #1676, release W49, CIS #1586, kit sync, Infra #935, AA-1111;
   - sửa `/admin` → trang landing;
   - Content workspace 390 cuộn ngang.
5. ≥ 28/11: AA-1061 / Booking #200. ≥ 30/11: C4.3 W49. ≥ 01/12: các việc theo tháng (C8, cap openai-direct về 10 USD, đối soát hoá đơn).

## Lưu ý kỹ thuật cho phiên sau

- Push app: `AA_GITLEAKS=<workspace>/.tmp-session/gitleaks-8301/gitleaks`, vì shim mise làm pre-push hỏng.
- Không ECS exec trong lúc ship CIS (guard).
- `project-template` giờ đã ship qua `ship_merge` / `ship_wave` được, nhưng PR body không có dòng `Refs AA-` (denylist).
- Bài học chi tiết: `skill/aa-lessons/lessons.md` (5 dòng S293).

## Session block cho memory Notion

```
## S293 (25/11/2026, Claude Code — VS Code/WSL, Ultracode): trợ lý ops A2, Eval runs, kit 1.1–1.3, External checks từ worker, tenant read + rollup
**Quyết định của Nghiệp** — duyệt 10 việc không đụng thứ Năm (tạo AA-1179); deploy CIS + smoke lại, dừng sau 22:00; ~15:00 "duyệt hết, tăng tốc", tạo AA-1180; nháp Jira duyệt nhưng auto mode chặn đăng.
**Kết quả chính** — Done AA-1178 (làn monitor đúng nhịp dưới tải), AA-1179 (parity 0, buffer 150–194×, p95 60 ms), AA-1180 (rollup 8 số lẻ, check ok=True). AA-1154 A2 live (490–491), AA-1169 trang Eval runs live, AA-1103 kit v1.1.0/v1.2.0/v1.3.0 (đủ 9 hàng), External checks chạy từ worker CIS (492–493; GitHub cron 0 lượt). Smoke thứ Năm 4/4. LLM 0 USD.
**Trạng thái kiểm cuối phiên** — cis-api :1295 / worker :864 (7886cb4c), admin :106 (deeb3e2e), booking-api :175, booking-admin :69, crm-api :220, crm-web :191, tp-web :29. Migration CIS 494, bk/crm/tp không đổi. shared.job 0. Bật: blog_claim_rule, hook warn, external checks worker.
**Việc cần làm đầu phiên sau (S294)** — (1) buổi thứ Năm + duyệt ISMS + AA-1157; (2) đăng 9 nháp Jira sau khi xem; (3) tech lead: AA-1154 bấm thẻ, AA-1169 đọc 12 mẫu, AA-1103 duyệt L8; (4) sau thứ Năm: savepoint, release W49, PR giữ lại, /admin → landing.
**Lưu ý kỹ thuật** — AA_GITLEAKS khi push app (shim mise); GitHub cron không tin được cho việc < 1 h → làn monitor CIS; PR Dependabot không có secret → tạo lại nhánh; project-template ship qua ship_merge, body không Refs.
```
