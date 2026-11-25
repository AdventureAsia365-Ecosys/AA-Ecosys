# S292 — 25/11/2026 — Status P2, trợ lý ops A1, T9 first-pass yield, làn job giám sát, dọn snapshot RDS

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). ~06:30 → ~12:15 +07. Lane song song qua `tools/workflows/lane.js` (a–i) + agent nền; tối đa 3 lane nặng theo RAM. MFA nhập lại ~06:55 (hết hạn 18:44). Máy OOM một lần ~11:50 (WSL khởi động lại; đã tắt 3 phiên Claude cũ trước đó, sau OOM chạy tuần tự).

## Trạng thái

- **Done:** AA-1142 (Status P2, Done-with-scope).
- **In Review:** AA-1136 (hook warn bật, chờ đo M7 sau 1 tuần warn), AA-1178 (mới: làn job giám sát, còn kiểm lúc có job nền dài).
- **In Progress:** AA-1154 (A1 xong, còn A2), AA-1169 (đo lại đạt mọi chỉ tiêu máy, còn đọc tay 10 blog), AA-1166 (bộ ISMS xong, chờ chủ DN duyệt thứ Năm).
- **Chờ người:** AA-1157 (view-as cần danh tính chủ DN → thứ Năm).
- Follow-up S291 đã làm: smoke vai admin trong CI (CIS #1682), AA-1152 điểm ngủ đêm (contract catalog.http.v1 1.4).
- Lượt LLM trả phí: **~1,42 USD** (AA-1169 w5-t9-r2) + 0,00085 USD (một Analyse AA-1154).
- Snapshot: [state-snapshot](../audits/2026-11-25-S292-session/state-snapshot.md).

## Quyết định của Nghiệp

- ~06:45: duyệt A + B (10 việc), không đụng việc thứ Năm 26/11; ban đầu nhóm B deploy trước 22:00 rồi đóng băng, sau đó (~08:20) "làm bình thường, tăng tốc, đừng quá để tâm mốc 22:00".
- ~08:50: duyệt (1) đo lại AA-1169 trả phí ≤ 5 USD, (2) AA-1136 bật warn, (3) tắt opus-4-5 (anh tự bấm 09:10; công tắc `cis.t9.blog_claim_rule` anh bật 09:08).
- ~09:50: 2 check trang status là nhiễu → sửa; 3 snapshot để nguyên theo luật; **nháp Jira gom tiếp sang phiên sau cùng ngày**.
- ~10:00: snapshot tp-018 kiểm thấy không cần → xoá hẳn; ~10:05: xoá luôn pre-s253 để alarm không đỏ ngày thứ Năm.
- ~10:15: đồng ý tạo AA-1178 và sửa luôn vụ job giám sát bị chặn sau job nền dài.
- ~11:30: tắt 3 phiên Claude cũ (PID 1723675, 3689029, 3719134).

## Thay đổi Codebase (merged)

- **Guard đỏ:** Infra #1019 `2191213c` (sidecar WordPress test sang digest 25/11: 88 lỗi đã có bản vá; role không sai) + TF apply + deploy Booking admin; root #997 (catalogue S291). Secret Scan full history không cần sửa (commit cũ đã pin).
- **Dependabot:** root #958, Partner #383, TP #293.
- **AA-1136:** root #996 (note tên phiên được tính, M5 22 % → ~10 %), root #1003 (warn; SubagentStop vẫn im lặng).
- **AA-1152 follow-up:** root #998 (catalog.http.v1 1.4), CIS #1680 `0f74f04c`, Partner #391 `1f7c0136`.
- **Smoke admin CI:** CIS #1682 `339a966a` (71 route; sửa escape CodeQL).
- **AA-1169:** CIS #1681 (CIS 484, đổi từ 490 vì preflight), #1684 `c3ca5ca0`, #1688 `4a0ba652` (đăng ký w5-t9-r2); root #999.
- **AA-1142:** root #1002 (External checks workflow, TLS ≥ 1.2), CIS #1685 (485/486), #1687 `97f6c0b4`; root #1007 `50c053ee` (cron lệch phút).
- **AA-1154 A1:** CIS #1686 (487; sửa test replay 304/306/226 + 3 test liệt kê stage), root #1004, CIS #1689 `ed236b6d`.
- **Status nhiễu:** CIS #1690 (488), #1692 `f3dbedb1`, root #1005.
- **AA-1178:** CIS #1691 (489), #1693 `794eea54`, root #1006.
- Root #1001 (bot db-schema-reference).

## Thay đổi Hạ tầng / dữ liệu Dev

- Migration áp Dev: CIS 484, 485, 486, 487, 488, 489.
- ECS cuối phiên: cis-api :1288 / worker :857 (794eea54), admin :103 (ed236b6d), booking-admin :69, crm-api :220; còn lại không đổi.
- Terraform Apply Dev 45514445901 (task def Booking admin, sidecar test-wp).
- S3 private `isms/` (bucket bronze): 12 tài liệu ISMS/AIMS-lite (AA-1166).
- RDS: xoá snapshot `db-migrate-tp-018-…` và `aa-cis-dev-db-pre-s253-aa991-cleanup` (tech lead duyệt, DRY RUN từng bản); Lambda expiry xoá `db-migrate-281-…`; copy age 28,9 ngày.
- Setting: `cis.t9.blog_claim_rule` = On (tech lead), catalog `opus-4-5` Off (tech lead).

## Bằng chứng verify

Thư mục `docs/audits/2026-11-25-S292-session/` (`evidence/`, `live/`).

- **AA-1142:** status 200, 14 section, SLO 4 app, External 8/8; burn drill 300×503 → `slo-fast-cis` 38,5×; 12 ảnh.
- **AA-1169:** first-pass trên S285: B 0,083 (route_timing 21/42 cờ); w5-t9-r2: **yield 0,417**, lỗi/blog 1,58 vs 5,0 non_inferior, 1 request/blog, 0,055 USD/blog, 0 hard stop, 1,42 USD.
- **AA-1154 A1:** Analyse `errors-cis`: 2 thẻ, haiku-5-5 Anthropic API 0,00085 USD, ledger ops_assist/writer/rank_explain; UI changes 200, `?window=45` 422, 0 POST từ phiên read-only; 6 ảnh.
- **AA-1152:** CIS 50 tour/428 ngày đều có `overnight_destination_id` (154 đêm không phải điểm dừng); CRM sync 02:00Z 200/200 tour mới có trường.
- **AA-1178:** 7 kind làn monitor, cap 1/2 từ setting, `ops_status_sample` 12 lần/giờ (chờ ≤ 18 s).
- **Smoke thứ Năm (read-only, sau deploy cuối 794eea54):** 4/4 đạt — CIS sign-in (lỗi ToastProvider S291 không còn), Content workspace (390 không cuộn ngang), Compliance readiness 5 tab, Booking SUP-000019 TK ngân hàng SYNTHETIC "Waiting for approval" + banner chi bị tạm dừng; 7 ảnh `live/thu-smoke-*`. Lưu ý cho buổi họp: Content workspace chỉ có 1 tour SYNTHETIC đã xoá; dữ liệu test còn mã issue ("SYNTHETIC S290 AA-1149…", "(AA-1158)"); Compliance hiện điểm đỏ (Dev, không phải chứng nhận); chuông 25, Review Queue 73, Booking 25 trip check quá hạn.
- **AA-1136:** M1–M4 đạt (2.839 sự kiện, 0 lỗi, p95 ≤ 233 ms), M5 22 % → ~10 % sau sửa, M6 nền theo repo.

## Jira

Chưa đăng — **gom sang phiên sau cùng ngày 25/11** (tech lead quyết ~09:50): 5 nháp S291 (`docs/audits/2026-11-24-S291-session/jira-drafts.md`) + nháp S292 soạn ở phiên sau từ log này.

## Việc đầu phiên sau (S293)

1. Thứ Năm 26/11 (buổi chủ DN): AA-1158, AA-1148, AA-1173, AA-1155 + **duyệt bộ ISMS AA-1166** (policy, scope, roles, tiêu chí rủi ro, chấp nhận R-01/R-03, rủi ro AI) + AA-1157 H0–H6.
2. Jira: soạn nháp S292, gom với 5 nháp S291, duyệt một lần rồi đăng.
3. Sau thứ Năm: savepoint Booking #331 + CIS #1676, release W49, CIS #1586, kit sync, Infra #935, AA-1111.
4. AA-1169: đọc tay 10 blog (cần UI cho output eval: route `/admin/quality/lineage` chưa có trang); AA-1178: kiểm làn monitor khi có job nền dài; AA-1154 A2 + 4 follow-up A1.
5. Kiểm External checks chạy theo lịch mới (7/22/37/52) và mục `external-feed` hết.

## Còn lại / follow-up

- AA-1154 A1 follow-up: biên nhận `pii_scrub` không vào dòng ledger của trợ lý; viewer không thấy AI part đã cache; 503/treo 1 lần lúc deploy; vài lỗi hiển thị.
- AA-1142: lỗi máy chủ theo đại lý chưa đo; text mục cảnh báo mới chỉ tiếng Anh.
- Infra #977 dependabot chờ rebase.

## Lưu ý kỹ thuật cho phiên sau

- Preflight migration CIS đòi số liền kề: lane song song đổi số lúc ship (484 → 489 trong phiên).
- Migration thêm dòng `spend_budget` provider `llm` làm đỏ test replay 304/306/226 (CHECK cũ): fixture phải cất dòng `llm` trước khi replay.
- PR body: mã AA-n chỉ ở dòng `Refs` (check PR title).
- Không chạy ECS exec song song với ship CIS (guard exec chặn merge).
- Bài học chi tiết: `skill/aa-lessons/lessons.md` (8 dòng S292).

## Session block cho memory Notion

```
## S292 (25/11/2026, Claude Code — VS Code/WSL, Ultracode): Status P2, trợ lý ops A1, T9 yield, làn job giám sát, dọn snapshot RDS
**Quyết định của Nghiệp** — duyệt 10 việc không đụng thứ Năm; "tăng tốc, đừng quá để tâm 22:00"; duyệt đo lại AA-1169 ≤ 5 USD, bật hook warn, tắt opus-4-5 (tự bấm), bật cis.t9.blog_claim_rule (tự bấm); 2 check nhiễu → sửa; xoá snapshot tp-018 + pre-s253; tạo + sửa AA-1178; Jira gom sang phiên sau cùng ngày; tắt 3 phiên Claude cũ.
**Kết quả chính** — Done AA-1142 (Status P2: SLO/burn, sự cố, External checks 0 USD, theo đại lý; burn drill bắt slo-fast-cis). AA-1169 đo lại: yield 0,417 (từ 0,083), 1,42 USD, còn đọc tay 10. AA-1154 A1 live (Analyse 0,00085 USD). AA-1178 làn job giám sát (CIS 489). AA-1136 warn bật. AA-1166 bộ ISMS lên S3 private. AA-1152 contract 1.4 live CIS + CRM. Smoke admin CI. Guard đỏ + dependabot. 2 check nhiễu sửa (488). External checks cron lệch phút.
**Trạng thái kiểm cuối phiên** — ECS 8/8: cis-api :1288 / worker :857 (794eea54), admin :103 (ed236b6d), booking-api :175, booking-admin :69, crm-api :220 (1f7c0136), crm-web :191, tp-web :29. Migration CIS 489, bk-075, crm-088, tp-037. shared.job 0. RDS snapshot cũ nhất 28/10. Bật: cis.t9.blog_claim_rule On, hook warn.
**Việc cần làm đầu phiên sau (S293)** — (1) Jira S291 + S292 duyệt một lần; (2) buổi thứ Năm + duyệt ISMS + AA-1157; (3) sau thứ Năm: savepoint, release W49, PR giữ lại; (4) AA-1169 đọc tay, AA-1178 kiểm có tải, AA-1154 A2.
**Lưu ý kỹ thuật** — số migration CIS liền kề khi nhiều lane; dòng spend_budget 'llm' cần fixture replay 304/306/226; mã AA chỉ ở dòng Refs; không ECS exec song song ship CIS.
```
