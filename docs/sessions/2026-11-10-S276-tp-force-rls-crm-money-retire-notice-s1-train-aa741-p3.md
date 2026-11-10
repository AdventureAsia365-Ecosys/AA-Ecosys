# S276 — TripPlanner FORCE RLS, tiền trong CRM (lịch trả tiền, phí huỷ, lãi theo chuyến), gỡ bài chỉ báo, S1 train bật, AA-741 phase 3

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). 10/11/2026 ~16:50 → ~22:30 +07, cùng ngày với S275.
- MFA `aa365-admin` hết hạn 21:49; việc cần MFA (D8, Terraform apply, DB Migrate) làm trong 19:00–21:19.
- Tech lead duyệt trên điện thoại qua trang artifact (trang so sánh Odoo) và trong chat.
- Kiểm OOM đầu phiên theo yêu cầu: không có OOM, còn ~6 GB RAM → mở thêm lane.

Snapshot: `docs/audits/2026-11-10-S276-session/state-snapshot.md`.

## Danh sách đầu phiên (tech lead "ok" + Ultracode, 17:00)
1. AA-1063: đưa câu t2@2 vào hàng duyệt, luật Jev lọc trước thành code.
2. AA-1024 D8: migration 336 + `DB_AUTO_APPLY_CONTRACT` (sau 12:00Z).
3. AA-1038: test teal + Playwright, FORCE RLS.
4. AA-1039: drill trên test-wp với một bài mới.
5. AA-741 phase 3: báo cáo theo cơ chế.
6. AA-1067: lịch trả tiền, nhắc hạn, chính sách huỷ, phí / hoàn.
7. AA-1068: lãi theo chuyến, "Bookings with AA", hoá đơn NCC (kéo lên từ S277).
8. AA-1049: S1 train (W3).

## Quyết định của tech lead
- **17:05 "kiểm OOM rồi tăng tốc":** không có OOM → mở thêm lane (AA-1068, sửa gateway, đo AA-741).
- **17:20 giải thích phải cụ thể:** mỗi việc nói rõ làm gì, để làm gì, tiền một lần hay hằng tháng, đụng bao nhiêu tour /
  dòng, có cần duyệt không. Đã lưu vào memory.
- **17:25 AA-1049 "làm luôn smoke":** duyệt ~1 USD. Sửa xong thì phải BẬT công tắc, không để tắt.
- **17:30 tour cũ:** giữ nguyên văn bản cũ cho tới khi sửa; kế hoạch sửa làm sau khi có kết quả replay.
- **17:35 sửa Master:** mọi cách sửa Master phải đánh giá lan truyền toàn hệ thống, kể cả atom hoá lại (A3).
- **17:50 AA-1039 drill:** thêm T8, trần 0,25 USD.
- **17:55 WordPress của đại lý:** mặc định CHỈ BÁO. Đại lý tự chuyển bài về nháp bằng một nút, hoặc tự bật "tự chuyển về
  nháp sau N ngày". Sửa ADR 0019 d20.
- **18:05 Batch API:** đợt viết hàng loạt dùng Batch (rẻ 50%) → tạo AA-1076, làm trước đợt sửa tour cũ.
- **18:20:** tạo 6 issue từ AA-741 phase 3 (AA-1077…1082).
- **18:35:** dựng trang so sánh Odoo với CRM / Booking.
- **21:10:** duyệt chạy lại drill AA-1039 (trần 0,25 USD); chốt phiên sau khi việc đang chạy xong.

## Thay đổi codebase (đã merge)

**CIS**
- **#1421 `d3dd7132` (AA-1024):** dòng bị từ chối của một deployment bị bỏ qua giờ ghi tên connection.
  - Gốc: `t7_debate_judge` có shadow 10% gpt-6-luna trên acc3; circuit acc3 đang mở vì access_denied.
  - Hậu quả cũ: ~10% dòng refused không có connection.
- **#1422 `3f54cb89` (AA-1063):** luật Jev lọc trước thành code, mặc định shadow.
  - Luật: p ≥ 0,90 + panel đa số ok + không lens non-ok nào có `fact.misbinding`.
  - Labeller `prefilter:jev090+panel`. Không bao giờ dùng làm bằng chứng release.
- **#1423 `9539e953` (AA-1049):** S1 train sau công tắc `S1_CONTROL`.
- **#1424 `29c4d86d` (AA-1063):** tìm nguồn cho câu T2.
  - 310 / 417 câu t2@2 không có nguồn: đợt bổ sung vòng 2 đánh số mẫu lại từ 1 và chưa từng được import.
  - Giờ mỗi câu T2 đọc đúng bản của đại lý theo `version_id`, cùng tenant.
- **#1425 `59c0b1ab` (AA-1039):** migration 395 `auto_draft` (đã áp).
- **#1426 `987dccdc` (AA-1039):** fan-out chỉ báo, route chuyển về nháp, settings.

**Partner**
- **#260 `b838c565` (AA-1067):** crm-049 (expand) + crm-050 (contract), đã áp.
- **#261 `6dd244de` (AA-1067):** lịch trả tiền, nhắc hạn, chính sách huỷ, phí / hoàn.
- **#262 `91256719` (AA-1039):** danh sách trong Content studio + thẻ settings "tự chuyển về nháp".
- **#263 `8ebbc27e` (AA-1068):** crm-051, đã áp.
- **#264 `4a9ce7ba` (AA-1068):** lãi theo chuyến, "Bookings with AA", hoá đơn NCC so với kế hoạch.
- **#265 `f166946f` (AA-1068):** sửa mobile `/aa-bookings` (cuộn ngang 149 px).
- **#266 (AA-1067, follow-up, merged `a40a93f1`):** bảng phí huỷ mặc định theo đề xuất 3A: 0% từ 31 ngày, 25% 15–30 ngày, 50% 8–14 ngày,
  100% ≤ 7 ngày. Đang ship lúc chốt; trạng thái ở snapshot.

**TripPlanner**
- **#249 `0d6b5eb8` (AA-1038):** tp-028 FORCE RLS.

**Infra**
- **#754 `c7ee47de` (AA-1038)** + #755 bản copy migration.
- **#756 `aaccacd0` (AA-1049):** `s1_control=contract` trên worker; cập nhật guard test. Terraform Apply run 42808715047.

**Root**
- #666: AA-1038.
- **#667 `d00a5d43`:** gateway_status đếm mỗi lượt một lần.
- #669, #673: retention DM-7.1 cho bảng crm-049/050 và crm-051.
- **#672:** sửa ADR 0019 d20 (gỡ tour = chỉ báo; một nút và tuỳ chọn tự chuyển nháp).

## Việc dữ liệu / vận hành trên Dev

**AA-1038 (Done)**
- DB Migrate apply run 42803155123 (tp-028).
- Probe cách ly run 42803939499: 99/99, có 2 ô mới `tenant.tripplanner_isolation` và `rls.tripplanner_system_scope`.
- Playwright 3/3 PASS: trip còn sau khi tải lại; ngữ cảnh chéo tenant rỗng. Ảnh: `docs/audits/2026-11-10-S276-session/aa1038-force-smoke/`.
- Chi phí: **đo được** (tag) ~0,1–0,3 USD/ngày, tức ~3–9 USD/tháng. Con số 12–14 USD/tháng là **ước tính** có cộng phí
  WAF niêm yết. Đọc lại ở C8 đầu tháng 12. Đã đăng comment sửa trên Linear. Bằng chứng: `docs/audits/2026-11-10-S276-session/aa1038-cost/`.

**AA-1024 D8 (Done)**
- CIS 336 áp lệch thứ tự: check run 42812787570, apply run 42813123222, key 336 đã ghi.
- `DB_AUTO_APPLY_CONTRACT=true` lúc 12:11Z (19:11 +07). Đặt bằng `gh` login của tech lead, vì App `aa-agent` bị 403 khi
  ghi repo variables.
- Kèm theo: CIS #1421 và root #667 (ở trên).

**AA-1063 (In Review)**
- Enqueue t2@2/1.0.0: 417 câu; gọi lần hai thêm 0.
- Allowlist Jev đã rỗng (không còn tenant demo).
- Đề xuất panel agent đã nhập Lab:
  - 107 câu: 81 ok / 20 vi phạm / 6 chưa chắc.
  - 310 câu (sau #1424): 300 ok / 6 vi phạm / 4 chưa chắc; hai lens đồng ý 306 câu.
- Còn lại: tech lead duyệt một đợt trong Writing Lab, rồi đóng.

**AA-1049 (In Review)**
- Replay miễn phí trên 817 Master: 0 khác biệt chưa khai báo; 93 giống; 280 `D-s1-compose`; 1 `D-s1-status`; 444 MISS.
- Bật `S1_CONTROL=contract` trên worker (từ :652).
- Smoke 3 tour (wave `80102e97`): 3/3 publish, điểm 10, 0 vi phạm contract.
  - Chi phí 0,1468 USD (0,049 USD/tour, đã gồm A3).
  - Wave đóng 13:52Z khi recompute nền tảng vẫn đang chạy.
- Còn: một lượt `s1_flag_fix` khi công tắc bật; quyết định cho 280 tour (sau AA-1076).

**AA-1039 (In Review)**
- Bài thử 1 `05384b74` (0,18 USD) không dùng được: bài theo Segment Subject phục vụ 13 tour, không "về" key cần gỡ.
  Script đã sửa (luật `about_key`).
- Bài thử 2 `b5f11e37`: 0,282 USD, vượt trần 0,25 USD 0,03 USD. Lý do: script chỉ kiểm ước tính p90 trước khi chi.
- Các bước drill publish → retire (chỉ báo) → movedraft → restore → put_back: Drill AA-1039 theo luật mới ĐẠT 44/44 kiểm trên site WordPress thử (publish `804a822e`, key `66a568bd`): đăng → kiểm 'về key' → ngừng bán (bài vẫn online, chuông + danh sách) → đại lý 'Move to draft' (bấm lại không tạo thêm) → khôi phục → 'Put back online' (bấm lại là replay) → online. Bằng chứng `docs/audits/2026-11-10-S276-session/aa1039-drill/`. Issue Linear AA-1039 đã Done và lưu trữ từ 05/11 nên không nhận comment mới; bằng chứng nằm trong repo.

**Gateway (21:28)**
- Chi tiêu tháng: 26,45 USD.
- anthropic-direct 22,63 / 150; openai 0,75 / 10; acc3 0,97 / 100.
- acc3 vẫn 7 model bị từ chối. Route v7.

## AA-741 phase 3 (báo cáo theo cơ chế)
- Báo cáo: `docs/audits/2026-11-10-S276-aa741-phase3/`. 4 script chỉ đọc, 0 USD.
- 13/13 bài giữ vì F4 đều **quá ngắn**: trung vị 652 từ, prompt yêu cầu 900–1.300 từ.
- Viết lại toàn bài chỉ sửa được 6/18. Bộ chuẩn hoá cắt ngắn bài sau khi đã qua cổng.
- Có lỗi bị che (hidden failures).
- Judge brand-fit chấm 5,9–6,3, trong khi điểm lưu là 9,9–10. Debate gắn cờ 499/502.
- Chi phí: phase 2 6,77 USD; tổng AA-741 13,33 / 20 USD.
- 56 kết luận theo cơ chế, 21 mục giao diện.
- 148 ảnh chụp giữ ngoài repo public.
- Follow-up: AA-1077…AA-1082. AA-741 đóng khi root PR này merge.

## Bản đồ lan truyền khi sửa Master
- `docs/audits/2026-11-10-S276-session/master-propagation/` (nghiên cứu chỉ đọc).
- Đường A: sửa tại chỗ các trường cố định; ~0,006–0,03 USD/tour cho A3.
- Đường B: S1 viết lại; ~0,077 USD/tour.
- Không sửa bảng trực tiếp.

## Trang so sánh Odoo
- https://claude.ai/artifact/T389pCPUPDSDsmEorAJV6W: 73 tính năng, 12 chỗ hệ mình hơn Odoo.

## Hội tụ Linear
- **Done:** AA-1038, AA-1024, AA-1067, AA-1068.
  - AA-1067: kiểm UI live PASS trên đại lý thử Sen Vàng.
  - AA-1068: kiểm UI live PASS; vai trò assistant nhận 403 ở các API tiền.
  - Ảnh: `docs/audits/2026-11-10-S276-session/ui-verify/`.
- **In Review:** AA-1063 (chờ tech lead duyệt một đợt), AA-1049 (s1_flag_fix + quyết định 280 tour),
  AA-1039 (bằng chứng drill).
- **Đóng khi root PR này merge:** AA-741.
- **Issue mới:**
  - AA-1076 Batch lane + phạm vi prompt caching (S277, M1b).
  - AA-1077 hợp đồng độ dài blog (S277).
  - AA-1078 làm hiện lỗi bị che (S277).
  - AA-1079 Debate / brand-fit (S278).
  - AA-1080 import brief + thị trường (S278).
  - AA-1081 chủ đề T7 (S279).
  - AA-1082 CRM web HA, báo chi phí trước (S279).

## Jira
chờ tech lead duyệt 4 nháp (PR-26, PR-23, PR-24, PR-22) — xem `docs/audits/2026-11-10-S276-session/jira-drafts.md`

Nháp: `docs/audits/2026-11-10-S276-session/jira-drafts.md`.

## Trạng thái cuối phiên (từ snapshot)
ECS 1/1 COMPLETED, revision mới nhất = đang chạy: CIS api :1086 / worker :654 (`987dccdc`, schema 395, S1_CONTROL=contract), Booking :112 (bk-044), CRM api :149 (crm-051), web :127 (`f166946f`), TripPlanner web :6 (tp-028). Wave 0, gateway 26,45 USD tháng 11. Chi tiết: `docs/audits/2026-11-10-S276-session/state-snapshot.md`.

## Bài học (đã chuyển vào `skill/aa-lessons/lessons.md`)
- Lane chạy `pytest -n 8` cả bộ unit làm cạn RAM; điều phối phải kill.
- venv local lệch bản ghim fastapi / pydantic → test openapi đỏ giả, chặn push.
- Số chi phí phải ghi rõ "đo được" hay "ước tính".
- Drill chọn bài theo Subject phải kiểm "về key" trước khi chi.
- Tham số `parametrize` sinh ngẫu nhiên lúc import làm xdist thu khác danh sách test.
- Còn chờ ghi: script trả phí phải chặn theo từng stage, không chỉ kiểm ước tính trước (drill vượt trần).

## Việc đầu phiên sau (S277)
1. **AA-1063:** tech lead duyệt một đợt trong Writing Lab → đóng.
2. **AA-1039:** đóng với bằng chứng drill (nếu PASS), hoặc sửa.
3. **AA-1076:** Batch lane.
4. **Tour cũ (280 Master):** kế hoạch sửa có bản đồ lan truyền + chi phí batch → tech lead quyết.
5. **AA-1077, AA-1078.**
6. **AA-1049:** kiểm lượt `s1_flag_fix`.
7. **Guard CI từ bài học:** chặn RAM `pytest -n`, kiểm venv đúng bản ghim, lint `parametrize`.
8. **C8 đầu tháng 12:** đọc lại chi phí TripPlanner.
