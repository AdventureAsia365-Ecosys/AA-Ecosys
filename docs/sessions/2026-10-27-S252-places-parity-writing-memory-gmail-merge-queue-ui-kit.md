# S252 — 25/10 → 27/10/2026: parity địa điểm TripPlanner, release 0 Writing memory, Gmail CRM, merge queue + CI, một UI kit

**Tác nhân:** Claude Code (Ultracode; workflow + subagent; VSCode, WSL2; agent điều phối tự merge/deploy/verify theo
luật giai đoạn dev, push/merge bằng GitHub App `aa-agent`). Phiên chạy liên tục từ 25/10, qua nửa đêm sang 27/10.
VM WSL khởi động lại giữa phiên (hết RAM) — xem mục Sự cố.

Nguồn số liệu: `docs/audits/2026-10-27-S252-session-close/state-snapshot.md` (kiểm live ~05:10Z 27/10),
`.tmp-session/S252-facts.md`, checklist sống `.tmp-session/S252-checklist.md`. Số liệu nào không có trong các nguồn này
thì không ghi; phần chưa kiểm ghi rõ "chưa verify". Không đếm tổng số PR merge trong phiên (không có trong nguồn).

## Trạng thái

- **Linear Done trong phiên (10):** AA-916, AA-917, AA-918, AA-924, AA-669, AA-949, AA-950, AA-992, AA-908, AA-905
  (AA-905 đóng 27/10 kèm bằng chứng coverage).
- **Issue mới:** AA-993 (DevOps: delivery pipeline + tốc độ CI), AA-994 (một design system / UI kit cho 5 frontend),
  AA-995 (trang khách TripPlanner thân thiện, có chuyển động).
- **Đang dở:** AA-790, AA-991, AA-988, AA-989, AA-990, AA-919, AA-784, AA-945, AA-682, AA-979, AA-993 (In Review),
  AA-994, AA-995. Chưa đụng: AA-861, AA-816. Chi tiết ở mục "Đang dở".
- **Migration áp Dev:** CIS từ 282 (đầu phiên) lên **288** (checklist ghi: 284 WM-17, 286 route place card, 287 WM-18/20,
  288 FK `raw_tours.country` → `shared.countries`); Booking **bk-025**, **bk-026**; TripPlanner **tp-020**;
  CRM **crm-020**, **crm-021**.
- **Jira:** không soạn, không đăng trong S252 — gom sang S253 (xem mục Jira).

## Quyết định của Nghiệp (trong phiên)

- Đầu phiên: chọn ~20 việc từ master plan + tồn S251, chạy liên tục; việc cần duyệt theo kế hoạch coi như đã duyệt;
  báo cáo đầy đủ trước khi dừng; bật Ultracode.
- Ảnh bằng chứng do agent tự chụp (Playwright + user E2E), không nhờ Nghiệp.
- AA-993: gộp thành một issue DevOps cho delivery pipeline + tốc độ CI; duyệt Q6 (desired 0 = đỏ, không tự scale),
  Q7 (migration dạng expand tự apply ở dev, không người duyệt; prod thì Nghiệp duyệt), Q16 (Infra về private →
  `DB_AUTO_APPLY=false`) và 14 câu còn lại theo đề xuất.
- AA-919: "duyệt release 0" của Writing memory.
- Ngân sách acc3 ($250, cảnh báo) chỉ là cảnh báo — làm trọn việc Dev trả phí.
- N2 Kilimanjaro: nước của tour = dòng Excel nguồn (INDIA.xlsx → India); địa điểm giữ ISO country của chính nó; không
  có danh sách AA viết tay.
- Writing memory có tab Guide; không làm tiếng Việt riêng từng trang — nếu cần thì một công tắc VI cho toàn admin;
  "mọi thứ đồng bộ và chuyên nghiệp".
- AA-994 duyệt: một design system / UI kit cho cả 5 frontend (ADR 0016).
- AA-995 yêu cầu: trang khách TripPlanner thân thiện, chỉn chu, có chuyển động (như banner ngang của adventure.asia).
- Jira: phiên đã qua 27/10 nên mọi draft Jira gom sang S253, đưa duyệt một lần ở đó.
- 27/10: "làm dứt điểm việc hiện tại rồi chuẩn bị dừng phiên" → dừng AA-994 S1a, AA-790 r7, build AA-995, chuyển S253.
- Repo gốc giữ public tới tháng 11; ID trong repo được chấp nhận, không làm sạch.

## Done (kèm bằng chứng)

- **AA-916 / AA-917 / AA-918 / AA-924 — Writing memory:** WM-07 20/20 (100%) (AA-916); AA-917 ngoại lệ WM-13; AA-918
  ngoại lệ 1 candidate; AA-924 (26/10) nhãn retired + drawer severity live, replay 0 khác biệt.
- **AA-669 — portal My Content:** đo live 2 tenant × 4 chế độ, D1/D2 hết.
- **AA-949 — E2E Dev CRM:** run 40266164840 6 pass / 1 skip; runner ghim `ubuntu-24.04` (CIS #1028, Partner #69).
- **AA-950 — CRM-21b proposal + accept + hold:** review approve sau 5 vòng fix; Booking #97 (bk-api:59), root #270,
  Partner #77 (mig crm-021, apply run 40296875160), Infra #413, Partner #78 (`8c255bee`, API + web); sửa test E2E
  (cookie path) #82.
- **AA-992 — trang Data coverage:** TP #156, Booking #94, Partner #75, root #269, Infra #410, CIS #1031 (allow-list) +
  #1032 (API + UI); tp-020 + bk-025 apply. Live 38/39 nguồn ok, `tp_layers` timeout (view 6,1 s) → CIS #1034 tách nguồn,
  per-tour 1,55 s. Ảnh 1440/390 light/dark, 0 lỗi console/API.
- **AA-908 — traveller sign-up:** Infra #396 + apply; sign-up traveller-3 → `email_verified` true ngay phiên đầu.
- **AA-905 — build địa điểm:** 8 lô xong, **$4,31**; đóng 27/10 kèm bằng chứng coverage.

## Ship trong đoạn cuối (27/10)

- **AA-990 ISO country:** CIS #1052 + Infra #424 + migration **288** (áp 04:12Z, run 40448250177) — live, ready schema 288.
- **AA-990 N3 ngày:** CIS #1057 (parser "Day N" có ngoặc + `final_day_guard`); 3 Master hỏng ngày đã viết lại; quét lại
  3 → 1 tour còn thiếu ngày (Sri Lanka: heading dạng khoảng "Day 12-15" vẫn còn).
- **AA-990 tab Merges:** CIS #1058 sửa crash Places → Merges, verify trên ảnh production
  `docs/audits/2026-10-26-S252-aa990-parity/shots/places-merges-fixed-1440.png`.
- **AA-993 H1:** CIS #1053 pytest-xdist; #1051 + 5 PR pre-push hook khác.
- **Writing memory UI:** CIS #1054 tab Guide (kit `GuidePanel`), #1055 Guide toàn chiều rộng, #1056 mọi trang admin dùng
  kit `AdminMain`.
- **AA-994 S0:** root #277 ADR 0016 + `kit-sync.sh` + hook `kit-core-edit-guard`. Root #278/#279 (docs bot) merged.
- **Infra #425:** `PLACE_PIPELINE_AUTO=on` + xoá 3 schedule chết + chỉ số probe (TF apply 40450724466, deploy 04:57Z).
- **AA-784 spot check mù 20 thẻ:** FK 3,6% (trượt ngưỡng ≤3% đúng một dữ kiện), identity/leak đạt, region/locality sai
  7/20 → sửa hệ thống ở S253. Báo cáo `docs/audits/2026-10-26-S252-place-card-model-eval/spot-check/README.md`.
- **AA-991 probe enforce:** thử đỏ đúng; `orphan_segments` 3 → 0, `place_card_links_missing` 330 → 32; còn đỏ: 8 angle
  request, 10.495 dòng member chết, 9 tour không có segment.
- **AA-988 đo lại:** 99,1% segment coverage với các loại trừ có lý do; 228 chưa có lý do; hub là standalone theo thiết kế.

## Đã làm sớm hơn trong phiên (chi tiết: checklist)

- **AA-790 — T9 writer AI-tells:** r3 #1024 (bất biến sự thật: 0 regression), r4 #1027, r5 FAMILY_RULE, r6 BRAND TEXTURE
  #1035 live (mean tốt nhất). Brand voice còn dưới mức r3 ở vài nhánh → r7 sang S253.
- **AA-979 phase 1 xong:** root #267, Infra #407/#408 (+ TF apply), CIS #1029, Partner #70–#73 + fix gate #76; crm-020
  apply (run 40271770824); smoke Fargate 59/59 (run 40276705589). Phase 2 (re-enrol + MFA + cutover) chưa làm.
- **AA-945 — mail CRM:** Gmail send-as live (Infra #415, OAuth project `aa-crm-mail`, "Send a test" → Sent ✓); Partner
  #86 Message-ID → R2 pass live; UI import lịch sử. Còn M365.
- **AA-682 S1 live:** Booking #100 (coverage 89,3 → 93,5%), deploy, health bk-026.
- **AA-919 WM-17/18/20:** WM-17 #1021 + Infra #399 (mig 284, golden set 1.1.0 import + verify); WM-18/20 CIS #1039 +
  Infra #416 (mig 287); replay pre/post 0 byte khác ở mọi writer; release 0 active cho 4 writer, memory on, drill pass.
- **AA-990 F1/F2/F3:** geocode stall #1050, pool 500 #1048; mục 6: 75 SEO "hết hạn" (cột trace 7 ngày lệch luật reuse
  180 ngày) → chỉnh `expires_at`, còn 0 ($0).
- **AA-784 dựng thẻ:** route `gpt-6-luna` × Haiku 4.5 (CIS #1030 + Infra #409, mig 286); dựng xong 892 tour **$12,65**.
- **AA-993:** merge queue 3 repo (CIS #1041, Partner #87, Booking #101), post-deploy verify 4 app, CI speed PR-1,
  pre-push hook 6 repo.
- **Dọn tồn:** CIS #1010 merged có nhãn; 0 cảnh báo secret mở ở 6 repo; main CIS đỏ do test bom hẹn giờ → #1023;
  AA-835 409 `photo_rights` live sạch; seed AA-973 GIỮ (fixture E2E); audit lan truyền CIS + TripPlanner
  (`docs/audits/2026-10-26-S252-propagation-audit/`).

## Đang dở (còn gì + cái gì chặn)

- **AA-991 / AA-988 / AA-989:** cần cửa sổ dọn dữ liệu theo quy trình destructive (10.495 dòng member chết + trỏ lại
  angle request) → probe enforce xanh → bật `ENFORCE` (hiện `False` trong `db/freshness_gate.py`).
- **AA-784:** sửa hệ thống region/locality rồi dựng lại 11 thẻ + kiểm 20 thẻ mới.
- **AA-990:** heading dạng khoảng ở writer v2 (Sri Lanka), N4, ảnh portal, N1.
- **AA-994:** S1a dừng giữa chừng → S1b (trang quyết định giá trị token) → S1c; H1 branch protection do Nghiệp.
- **AA-995:** build hướng "Golden Hour" + immersive grafts — dừng, sang S253.
- **AA-790:** round 7.
- **AA-993 (In Review):** còn Phase C (drain êm), E (migration trong PR app), V3, H2, đo lại CI.
- **AA-919:** tab Releases. **AA-945:** M365. **AA-682:** S2+. **AA-979:** phase 2. **AA-861, AA-816:** chưa đụng.
- **82 tour published vẫn writer v1** — chưa rõ vì sao wave bỏ qua.

## Sự cố

- **VM WSL khởi động lại giữa phiên** (hết RAM) khi nhiều lane code + workflow + Playwright + driver chạy cùng lúc; mọi
  tiến trình nền phía máy mất, job trên ECS không mất. Luật mới trong `skill/aa-lessons/lessons.md`.
- **Vercel 403 "Code 21":** máy đang chạy VPN (datacenter M247, NL). Nghiệp tắt VPN; IP về FPT Hà Nội.

## Trạng thái kiểm cuối phiên (snapshot ~05:10Z 27/10)

- ECS (cluster `aa-cis-dev-cluster`), tất cả 1/1 COMPLETED, revision đang chạy = revision mới nhất:
  `aa-cis-dev-api:855` + `aa-cis-dev-worker:421` image `dev-d1409c6d`; `aa-booking-dev-api:62` `759732a4`;
  `aa-crm-dev-api:61` `78d0abf4`; `aa-crm-dev-web:30` `7bd2bb08`. Env mới `PLACE_PIPELINE_AUTO=on` trên api:855 +
  worker:421.
- Endpoint: CIS 0.11.0 `d1409c6d`, ready schema **288** (required 287); Booking 0.7.0 `759732a4`, ready `bk-026`;
  CRM api 0.5.0 `78d0abf4`, ready `crm-021`; CRM web 0.5.0 `7bd2bb08`; TripPlanner web 0.8.2 `f61a7485`.
- Migration mới nhất: CIS 288 · Booking bk-026 · CRM crm-021 · TripPlanner tp-020.
- Vercel production: aa-cis-frontend `d1409c6d` (#1058); aa-booking-admin `e5d36dbe`; aa-tripplanner `f61a7485`
  (main TP `4b089499`, #162 chỉ đổi hook/CI); aa-cis-portal không deploy mới trong 12 giờ cuối.
- EventBridge Scheduler `aa-cis-dev-acp`: còn 5 schedule; 3 schedule chết đã xoá.
- Job: `shared.job` 0 running, 1 queued hẹn giờ (`run_after` > 1 giờ, không chặn deploy); `shared.rerun_wave` còn 1
  dòng chưa ở trạng thái đóng (không có wave chạy) — S253 xem lại.
- Repo: chỉ còn PR bot (release-please, dependabot): CIS #1049; Booking #96, #95; TP #157, #155; Partner #64; Infra
  #412, #411. Root: PR chốt phiên S252.
- Probe độ tươi enforce: **đỏ** (`tours_with_place_atoms_but_no_segment` 9, `angle_gate_requests_on_inactive_atoms` 8,
  `dead_member_rows` 10.495).
- **Cố ý để BẬT:** `PLACE_PIPELINE_AUTO=on` (≈ $0,006–0,019 mỗi nguồn); Writing memory release 0 active cho 4 writer,
  memory on; route place card `gpt-6-luna` × Haiku 4.5; writer S1 v2 + `s1_generate` = sonnet-5-5.
- Chi tiết: `docs/audits/2026-10-27-S252-session-close/state-snapshot.md`.

## Chi phí

- LLM từ 25/10 00:00Z (`shared.llm_call_log`): **$54,93**.
- Trong đó các mục đã ghi: AA-905 build địa điểm $4,31; AA-784 dựng thẻ 892 tour $12,65.

## Bài học

Đã chuyển vào `skill/aa-lessons/lessons.md` (commit "docs: S252 lessons into the lesson log"). Điểm chính: giới hạn tải
WSL (tối đa 2 lane nặng, một workflow viết code mỗi lúc); job `succeeded` chưa phải việc xong (đọc bộ đếm `result`);
không quét lớn vào site Vercel từ máy agent; panel mù nhiều vòng chấm lại mọi nhánh trong một lượt; bất biến "không xoá
token sự thật" cho `ai_tells`; ngày cố định gần hiện tại trong test/fake là bom hẹn giờ; ghim `ubuntu-24.04` cho job
Playwright; không đưa account ID thật vào test repo app public.

## Jira

Không soạn và không đăng trong S252 — Nghiệp quyết định 27/10: phiên qua ngày nên mọi draft gom sang S253, duyệt một
lần ở đó. Danh sách việc cần có trong draft: `docs/audits/2026-10-27-S252-session-close/jira-drafts.md`.

## Việc cần làm đầu phiên sau (S253, theo thứ tự)

1. **Jira** (dồn từ S252): soạn draft, Nghiệp duyệt một lần, đăng.
2. **Cửa sổ dọn dữ liệu** (quy trình destructive): AA-991/988 10.495 dòng member chết + trỏ lại 8 angle request; rồi
   probe enforce xanh → bật `ENFORCE` (AA-991 Done), đóng AA-988/989 kèm số liệu.
3. **AA-784 sửa hệ thống:** region = cấp hành chính thứ nhất hoặc null, locality của park/núi = null, checker không tin
   trạng thái thì hiện tại; dựng lại 11 thẻ; kiểm 20 thẻ mới.
4. **AA-990 phần còn lại:** heading dạng khoảng (Sri Lanka) trong writer v2, N4, ảnh portal, N1 → đóng.
5. **AA-994** S1a → S1b (trang quyết định giá trị token) → S1c; H1 branch protection do Nghiệp.
6. **AA-995** build "Golden Hour" + immersive grafts (chụp màn hình từ GitHub Actions).
7. **AA-790** round 7.
8. **AA-993** phần còn lại (Phase C, E, V3, H2, đo lại CI).
9. AA-919 tab Releases; AA-945 M365; AA-682 S2+; AA-979 phase 2; AA-861; AA-816.
10. **82 tour published còn writer v1:** tìm vì sao wave bỏ qua; viết lại (trả phí, subset trước).
