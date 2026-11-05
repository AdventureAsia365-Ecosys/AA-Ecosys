# S268 (04–05/11/2026): route control + trace, R2 lát 2, R3 add-on + studio tiếng Việt, usage explorer, R6, CRM hardening

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree qua `tools/workflows/lane.js` → reviewer độc lập →
lượt sửa; PR quyền/bảo mật thêm vòng review đối kháng; điều phối merge/deploy/DB Migrate/Terraform/kiểm live).
04/11 ~20:45 → 05/11 ~09:15 +07 (13:45Z → 02:15Z). Nối tiếp S267 cùng ngày.
Số liệu cuối phiên lấy từ snapshot `docs/audits/2026-11-05-S268-close/state-snapshot.md`.

Môi trường: MFA hết hạn 1 lần (Nghiệp nhập lại); 1 cửa sổ tắt auto mode (Terraform Apply Infra #675); auto mode chặn gộp DB
Migrate `check` + `apply` trong một lệnh nên luôn tách hai bước.

## Quyết định của Nghiệp (tech lead)

- **~20:45:** "ok" danh sách S268, Ultracode bật.
- **~20:50:** duyệt áp CIS 369 (DROP `shared.tenants.api_key_hash`) sau DRY RUN `ready=true`.
- **~23:40:** "làm hết việc thì kéo issue về làm tiếp nếu còn usage" → kéo AA-969, AA-1039, rồi follow-up AA-1035, phần còn lại AA-1036.
- **05/11 ~02:00:** duyệt alarm SLO CRM (~0,30 USD/tháng, Infra #675) + load test; tab Cards AA-1039 chọn **A** (route
  `/admin/places/cards`, quyền giữ nguyên).
- **AA-1021:** làm Ep3 (gateway) và Ep2, duyệt đưa Ep1/Ep3 lên Drive, làm trang danh mục video và post kit — rồi **dừng hẳn**:
  không đăng nội dung làm từ dự án lên kênh cá nhân, không repo cá nhân ("quá rủi ro"). AA-1021 → Canceled.
- **Kế hoạch video:** giữ #2 (series giới thiệu sản phẩm) và #3 (UAT, hướng dẫn, hồi quy), **gộp vào AA-855** (không tạo issue mới).
- **Jira:** gom nháp sang S269, rút gọn.

## Kết quả theo issue

Done: không có (Done-when còn thiếu ảnh admin hoặc bước live). Canceled: **AA-1021**.

| Issue | Trạng thái | Kết quả | PR / bằng chứng |
|---|---|---|---|
| AA-1042 Route control | In Review | Chỉnh route trên admin (thứ tự provider, chế độ thứ tự trong DB, preset, xem trước, version + hoàn tác, tắt gpt-4.1), Route trace, cảnh báo (`llm_route_watch`), đánh dấu nội dung do model dự phòng viết, preview tính probe; live 14/15 + 11/11 | CIS #1300 (370), #1301 (371), #1302, #1307; root #532, #534 |
| AA-1035 R2 lát 2 | In Review | Xem như đối tác chỉ đọc (gắn role lúc bắt đầu `srl`), Assignments, đọc Lab có log, chuông theo scope; 2 vòng review (3 major sửa) + minor #1308; live 20/20 | CIS #1303, #1308; root #540 (ADR 0006a A10b-2) |
| AA-1036 R3 | In Review | 369 DROP áp (snapshot `db-migrate-369-41850160705-1`); studio EN/VI; Request add-on thật (374) + banner AI tạm dừng; smoke portal 67/67 | CIS #1298, #1310, #1312; Partner #215, #216, #217, #219, #220; root #529, #541 |
| AA-1029 R4 | In Review | Portal Marketplace hiện "From $235" (bk-040 cấp quyền cho cis_app); ảnh smoke | root #530; Booking #181; CIS #1299; Infra #668; Partner #214 |
| AA-1045 Usage explorer | In Review | Rollup theo giờ (372, đổi sang contract #1305), explorer API + trang; rollup = ledger, API 14/14 | root #537; CIS #1304, #1305, #1306; Infra #672, #673 |
| AA-1039 R6 | In Progress | Route theo `pii_class` (373) + sửa review (decide không gửi pii cho vendor), Tenant 360 route, Catalogue settings, Place cards (A), Lab Releases/Metrics; live 4/4 | CIS #1309, #1311 |
| AA-969 CRM-37a | In Review | Review bảo mật 3 vòng (16 lỗi sửa: body budget, fair scheduler, fair claim, hook, Sentry), alarm SLO + 4 query apply, harness load test; live 413/401/403 | Partner #218; Infra #675; root #539 |
| AA-855 UAT | Backlog | Gộp kế hoạch video sản phẩm + vận hành | `docs/audits/2026-11-05-S268-video-plan/` |
| AA-1021 Video kiến trúc | **Canceled** | Ep1–Ep3 lên Drive (nội bộ); guard corpus | root #543 |

## Còn mở và vì sao

- **AA-969:** load test chưa chạy — seed 50 đại lý `lt-*` chết giữa chừng (không output); identity `lt agent` + secret đã có, k6 đã cài.
- **Ảnh trang admin** (Route control, Trace, Assignments, Xem như đối tác, Usage explorer, Place cards): user E2E smoke là role content → tech lead mở xem.
- **AA-1036:** vòng tenant gửi yêu cầu add-on → staff duyệt chưa chạy thật; user mời thật.
- **AA-1042:** "primary back" chờ acc3 mở model chính; 2 route chết hết khi áp 336 (≥10/11 ~12:00Z).
- **AA-1039 / AA-1040:** cần site WordPress test mới.
- **CRM web chạy 1 task Spot:** Spot interruption làm smoke đỏ giả — đề xuất 2 task / on-demand khi có pilot.

## Chi phí phiên

LLM: kiểm trace AA-1042 0,00025 USD (+ một lượt mất output ~0,0003 USD); 0 lượt pipeline trả phí. Alarm CRM mới ~0,30 USD/tháng.
Video: $0 (TTS local).

## Trạng thái kiểm cuối phiên

Chi tiết: `docs/audits/2026-11-05-S268-close/state-snapshot.md` (05/11 ~02:05Z).

- ECS (mỗi family chạy đúng revision mới nhất, 1/1 COMPLETED): cis-api :1011 + worker :577 `dev-25142dae`; booking :98;
  crm-api :130 + crm-web :106 `0ce28cec`.
- Health: CIS **374**; Booking **bk-040**; CRM **crm-043**; TripPlanner không đổi (Lambda `dsDF/qUp…`, tp-024).
- Bảng job: `shared.job` 0, `booking.job` 0, `crm.job` 2 job định kỳ. Không wave.
- PR còn mở: chỉ bot (dependabot, release-please, root #542/#538 sinh docs).

## Jira

Chưa đăng: nháp (bản rút gọn + bản dài) ở `docs/audits/2026-11-05-S268-close/jira-drafts.md`, tech lead gom sang S269.

## Việc cần làm đầu phiên sau (S269), theo thứ tự

1. **AA-969 load test:** chạy lại seed (`python -m app.seed --apply --load-test 50 --load-test-sub <sub của lt agent>`, trước
   tiên không `--travellers`, script in tiến độ từng bước), lấy 50 tenant_id, chạy `loadtest/crm_loadtest.py precheck` rồi `run`.
2. Jira: đăng bản rút gọn S268 cùng nháp S269 sau một lần duyệt; PR-20 kỳ 4 từ thứ Hai 09/11.
3. AA-1036: chạy vòng tenant gửi yêu cầu add-on → staff duyệt trên Dev; user mời thật.
4. Theo slot S269: AA-1035 phần còn lại (relay crm.ops scope, Tenant QA book riêng), AA-1040, AA-969 5 biện pháp d16.
5. **≥ 10/11 ~12:00Z:** áp 336, bật lại `DB_AUTO_APPLY_CONTRACT` → đóng AA-1024; C4.3 W46 từ 09/11.

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- zsh: `?` trong URL và `set -- $x`; `pkill -f` giết chính lệnh chứa mẫu.
- ecsx: script dài ghi `> file`, in tiến độ từng bước; pipe qua `tail` mất output khi bị đẩy xuống nền.
- Migration Apply dừng sau file CIS cố ý treo (336) → áp tay `check` → đọc → `apply`.
- Bảng `tenant_id` RLS tắt có chủ đích → contract, không expand.
- Smoke tìm theo `aa_name`; lane song song cùng file generated → merge main + sinh lại bằng venv pin.
- Corpus gate video phải ngang origin (đã thành guard #543); CRM web 1 task Spot → 503 giả khi bị thu hồi.
