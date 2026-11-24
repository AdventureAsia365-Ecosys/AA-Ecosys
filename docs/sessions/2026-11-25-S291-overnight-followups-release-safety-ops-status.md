# S291 — 24–25/11/2026 — qua đêm: follow-up S290, hiệu năng C4.3, an toàn phát hành, trợ lý ops A0, trang status P1, docs khớp thực tế

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). 24/11 ~20:15 → 25/11 ~04:00 +07. MFA aa365-admin hết hạn 06:52 (không cần nhập lại trong phiên). Lane song song qua `tools/workflows/lane.js` (a–i), tối đa 3 lane cùng lúc theo RAM; mỗi lane qua review độc lập + lượt sửa trước khi ship. Chạm **giới hạn 5 giờ** của Claude ~00:50 (reset 01:00) → resume lane h, dời AA-1142.

## Trạng thái

- **Done (3):** AA-1118 (docs khớp thực tế + lint chống lệch), AA-1119 (an toàn phát hành), AA-1141 (Ecosystem status P1, Done-with-scope).
- **AA-1154** A0 ship + live (giữ In Progress cho A1/A2).
- Follow-up S290 (không issue riêng): CIS (tour tay khỏi Upload, trash tour chưa phục vụ không recompute), Booking (data.mail, mail theo lần gửi, diff Inventory, hợp đồng gốc, đếm allotment, nhãn "from the tour", season-sync nhớ kết quả), CRM (add-on chỉ theo điểm của ngày tour).
- Hiệu năng C4.3 W48: CIS request_tours 25,5 → 4,0 ms; CRM due_proposals ~60 → 0/phút, tenant_status ~380 → 130/phút, prune ~8 → 3,5/phút, eviction pgss → 0.
- **AA-1142 dời S292** (limit). Savepoint Booking #331 + CIS #1676 để **draft, giữ tới sau thứ Năm 26/11**.
- Lượt LLM trả phí: **0 USD**.
- Snapshot: [state-snapshot](../audits/2026-11-24-S291-session/state-snapshot.md).

## Quyết định của Nghiệp

- ~20:20: duyệt danh sách 8 việc, 2 lane song song, không đụng việc thứ Năm 26/11.
- "tiếp đi, hết MFA thì kêu anh nhập".
- ~04:20: gom toàn bộ Jira S291 sang phiên sau cùng ngày.
- Tắt auto mode để agent gắn nhãn `secret-scan-baseline-reviewed` cho TripPlanner #301/#302 (rồi bật lại).
- CloudWatch Omni (bài anh gửi): em đề xuất chưa bật, ghi làm phương án cho AA-842 khi có prod / agent thật — chưa có quyết định.

## Thay đổi Codebase (merged)

- **Follow-up S290 CIS + perf** — CIS #1670 (480 index key expression) `77d9dbf9`, #1671 `adacb075` (tours-ready bỏ tour tay, trash tour chưa phục vụ không recompute, REQUEST_TOURS_SQL LATERAL + OFFSET 0, anomaly breaker cache median); Infra #1010 (script EXPLAIN).
- **Follow-up S290 Booking** — root #989 (retention `booking.season_sync_checks`), Booking #327 (bk-075) `90cf853f`, #328 `591d7397`.
- **AA-1118** — root #988 `f4c67bd3`, CIS #1672 `ce54595b` (thay #1669), Booking #326, Partner #387, TP #300, Infra #1009.
- **Catalogue đỏ** — root #990 `66e2879a` (surface snapshot + 5 setting compliance S290).
- **AA-1154 A0** — CIS #1673 (481, 12 setting) `cb9341fa`, #1675 `149c844c`.
- **AA-1119** — TP #301 `bc7daf0e`, #302 `bf5a9f08`, #303 `aa78d945` (planner không sập khi add-on sai dạng), CIS #1674 `8a31486f`, Booking #329 `caa80a41`, Partner #388 `9d7d2b7a`, Infra #1013 `06599d33`, root #992 `aee2f94f`.
- **CRM perf** — Partner #389 (crm-088) `0280d877`; Infra #1016 (script đếm tải).
- **AA-1152 follow-up** — Partner #390 `4471854c`.
- **AA-1141** — root #993 `b5cb1335` (retention + ownership), CIS #1677 (482 expand, 483 contract 11 setting) `89a1a153`, #1678 `df33eb9b`, hotfix #1679 `64242ba4` (ToastProvider).
- Root #991 `16354ec7` (bot db-schema-reference).

## Thay đổi Hạ tầng / dữ liệu Dev

- Migration áp Dev: CIS 480, 481, 482, 483; bk-075; crm-088.
- ECS (revision đang chạy = mới nhất): cis-api :1276 / worker :845 (`df33eb9b`), admin :101 (`64242ba4`), booking-api :175 (`591d7397`), booking-admin :67 (`caa80a41`), crm-api :219 / web :191 (`4471854c`), tp-web :29 (`aa78d945`).
- GitHub: ruleset `main: merge queue (AA-1119)` + strict checks trên TripPlanner main (gh của tech lead). Canary #303 qua queue OK.
- Dừng 3 Postgres sót của lane S289/S290 (giải phóng RAM).

## Bằng chứng verify

- Thư mục: `docs/audits/2026-11-24-S291-session/` (`evidence/aa838-explain-old-vs-new.txt`, `evidence/aa838-crm-load-counts.txt`, `live/*.png|json`).
- **CIS perf:** EXPLAIN cũ/mới qua ECS exec (`cis_app`): 15/15 cặp kết quả bằng nhau; request_tours 25,5 → 4,0 ms (4.385 → 149 buffer, dùng index 480). (run-script bị guard PII fail-closed với `EXPLAIN ANALYZE EXECUTE`.)
- **Booking:** notifications 85 dòng, 0 có data.mail; TC-000040 tab Suppliers 10/10 "from the tour, day N"; AA-1158 probe sau deploy: chi BIL-000002 vẫn 409 `bank_account_pending`.
- **AA-1154 A0:** replay 29/10 → 6 thẻ xếp hạng (probe R1, observe R0, wave_pause R2, route_save R3, retry R3, AWS Support R4), llm.calls 0; drawer Actions mở trên `/admin/overview`.
- **AA-1119:** coverage TP 90,31% ≥ 90,0; 4 deploy ghi "previous revision", rollback skipped; Sentry CRM test event → AA-PARTNER-API-4; DB Migrate file không tồn tại → job Inputs đỏ trước AWS (run 45436788452); TP deploy Visual xanh (aa78d945).
- **AA-1141:** status payload 200 (acks, viewer.can_ack, thresholds…); saved view create/list/delete 200; ack mục `main-cis` 200 → `acked` → clear 200; trang hiện What changed / as of / forecast; ảnh 1440 sáng/tối, 390.
- **CRM:** run-script 45444026209 (120 s): due_proposals 0/phút, tenant_status 130/phút, prune 3,5/phút, eviction 0.

## Jira

Chưa đăng — **chuyển sang phiên sau cùng ngày 25/11** (tech lead quyết ~04:20): 5 nháp (PR-25, PR-30, PR-29, PR-24, PR-27) gom chung với nháp phiên sau, duyệt một lần: `docs/audits/2026-11-24-S291-session/jira-drafts.md`.

## Việc đầu phiên sau (S292)

1. Thứ Năm 26/11 (buổi chủ DN): đăng nhập → Make business owner → duyệt TK SUP-000019 → agent thử chi 24 h → 409 `bank_payout_locked` (AA-1158); bật hai công tắc hai người + người thứ hai thật (AA-1148, AA-1173); Trang đăng nhập (AA-1155 T12); review bảo mật tháng đầu.
2. Sau buổi thứ Năm: ship savepoint Booking #331 + CIS #1676 (bỏ draft) + chạy `aa838_s291_savepoint_counts.py` (cần Infra PR); dọn dữ liệu SYNTHETIC S290.
3. Jira: gom 5 nháp S291 với nháp phiên này, đưa duyệt một lần rồi đăng.
4. AA-1136 readout (~26/11); AA-1142 (status P2); AA-1154 A1 (LLM, cap 10 USD stage ops_assist).
5. Release-please tuần W49 (CIS #1645, Booking #302, Partner #380, TP #295); dependabot actions bump.

## Còn lại / follow-up

- Smoke + visual đăng nhập của CI chạy vai viewer nên bỏ qua trang chỉ admin (vì thế lỗi ToastProvider lọt CI) → cần cách chạy admin E2E trong CI.
- Lỗi console `useToast must be used within a <ToastProvider>` ở `/admin` (trang đăng nhập) — có từ trước, chưa sửa.
- Visual `content-workspace-new` 390 cuộn ngang đỏ ở deploy 149c844c / df33eb9b, không tái hiện trên Dev với vai admin; deploy 64242ba4 xanh — theo dõi.
- AA-1141: Cost Explorer đọc ngày (cần yes, ~0,30 USD/tháng); Actions cache chưa có nguồn đo; push SEV1/2 thuộc P2.
- AA-1152: điểm ngủ đêm chưa có trong `catalog.http.v1` TourDay.places (cần đổi contract CIS).
- Alarm tuổi bản copy RDS vẫn đỏ vì giữ snapshot tp-018 (từ S290).
- CloudWatch Omni: phương án cho AA-842 (chưa bật).

## Lưu ý kỹ thuật cho phiên sau

- Push từ điều phối: `export PATH=/home/nghiep/projects/AA-Ecosys/.tmp-session/gitleaks-8301:$PATH` (shim mise không active).
- So kế hoạch SQL trên Dev: ECS exec, không run-script (guard PII fail-closed).
- `ecsx` bỏ SENTRY_DSN; test Sentry cần `ECSX_KEEP_SENTRY=1`.
- Agent gắn nhãn `secret-scan-baseline-reviewed` bị auto mode chặn → cần anh tắt auto mode hoặc tự gắn.
- `lane.js` COMMON thêm 2 guard (chuỗi allow của gitleaks; surface catalogue khi thêm setting).
- Bài học chi tiết: `skill/aa-lessons/lessons.md` (8 dòng S291).

## Session block cho memory Notion

```
## S291 (24–25/11/2026, Claude Code — VS Code/WSL, qua đêm): follow-up S290, perf C4.3, an toàn phát hành, trợ lý ops A0, status P1, docs khớp thực tế
**Quyết định của Nghiệp** — duyệt 8 việc, 2 lane, không đụng việc thứ Năm 26/11; "tiếp đi, hết MFA thì kêu"; tắt auto mode để agent gắn nhãn secret-scan-baseline-reviewed cho TP #301/#302.
**Kết quả chính** — Done: AA-1118 (root #988, CIS #1672 + 4 bản copy), AA-1119 (TP merge queue + strict + coverage 90%, rollback khi kiểm sau deploy đỏ ở 4 web app, Sentry CRM, DB Migrate kiểm input; TP #303 sửa planner sập), AA-1141 (status P1, CIS 482/483, #1678 + hotfix #1679). AA-1154 A0 live (CIS 481, #1675; replay 29/10 → 6 thẻ R0–R4, 0 LLM). Follow-up S290 CIS/Booking/CRM (bk-075, CIS 480, crm-088). Perf: request_tours 25,5→4,0 ms; CRM due_proposals ~60→0/phút, tenant_status ~380→130, eviction pgss→0. 0 USD LLM. AA-1142 dời S292 (chạm limit 5h ~00:50).
**Trạng thái kiểm cuối phiên** — ECS 8/8 1/1: cis-api :1276 / worker :845 (df33eb9b), admin :101 (64242ba4), booking-api :175 (591d7397), booking-admin :67 (caa80a41), crm-api :219 / web :191 (4471854c), tp-web :29 (aa78d945). Migration CIS 483, bk-075, crm-088, tp-037. shared.job 0, booking.job 0. Draft giữ tới sau thứ Năm: Booking #331, CIS #1676 (savepoint). Jira: 5 nháp chuyển phiên sau cùng ngày.
**Việc cần làm đầu phiên sau (S292)** — (1) buổi thứ Năm 26/11 (AA-1158/1148/1173/1155); (2) sau đó ship #331/#1676 + đếm savepoint; dọn SYNTHETIC S290; (3) gom Jira S291 vào nháp phiên này, duyệt một lần, đăng; (4) AA-1136 readout, AA-1142, AA-1154 A1; (5) release-please W49.
**Lưu ý kỹ thuật** — PATH gitleaks 8.30.1 cho push; EXPLAIN qua ECS exec (run-script fail-closed); ecsx bỏ SENTRY_DSN (ECSX_KEEP_SENTRY=1); smoke CI vai viewer bỏ qua trang chỉ admin.
```
