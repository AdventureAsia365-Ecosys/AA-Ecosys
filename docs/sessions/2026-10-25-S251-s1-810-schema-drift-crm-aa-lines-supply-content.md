# S251 — 25/10/2026: viết lại S1 xong 810/810, schema drift sạch, CRM AA lines + vòng đời, nội dung supply, cảnh báo bảo mật

**Tác nhân:** Claude Code (Ultracode; workflow + subagent; VSCode, WSL2; agent điều phối tự merge/deploy/verify theo
luật giai đoạn dev, push/merge bằng GitHub App `aa-agent`). Đổi tài khoản claude.ai giữa phiên (tài khoản cũ hết hạn
mức). Phiên dài, Nghiệp chốt "phiên này dài lắm rồi" → đóng, phần còn lại sang S252.

Nguồn số liệu: `docs/audits/2026-10-25-S251-wrap/state-snapshot.md` (kiểm live ~16:30 UTC), `.tmp-session/s251/SESSION-FACTS.md`,
checklist sống `.tmp-session/S251-checklist.md`, bài học chờ `.tmp-session/S251-lessons-pending.md`, log bằng chứng
AA-991 `.tmp-session/s251/aa991/out-rewrite.log`. Phần chưa kiểm ghi rõ "chưa verify". Không đếm lại tổng số PR merge
trong phiên (không có trong nguồn).

## Trạng thái

- **Linear Done trong phiên (8):** AA-645, AA-853, AA-825, AA-926, AA-946, AA-761, AA-947, AA-835.
- **Issue mới:** AA-988…AA-991 (lan truyền S1 v2 toàn hệ + probe tự đồng bộ), tạo theo yêu cầu của Nghiệp.
- **In Progress (Linear):** AA-790, AA-991, AA-990, AA-669, AA-916 / AA-917 / AA-918 / AA-924, AA-945, AA-979. Đang dở
  nhưng không In Progress: AA-919 (Linear vẫn Backlog; thiết kế + critic xong), follow-up của AA-908 / AA-978 (hai issue
  đã Done S250). Chi tiết ở mục "Đang dở".
- **Migration áp Dev (DB Migrate):** CIS **281** (AA-853), **282** (AA-835); CRM **crm-016** (AA-946), **crm-018** (AA-978).
- **Release PR còn mở:** CIS #1009 (0.11.0), Booking #92 (0.7.0), Partner #52 (0.5.0), TripPlanner #153 (0.8.2).

## Quyết định của Nghiệp (trong phiên)

- Đầu phiên: tự chọn 20 việc từ master plan + tồn S250, chạy liên tục, không hỏi; việc cần duyệt theo kế hoạch coi như đã duyệt.
- Đóng gói lại các skill zip cho tài khoản claude.ai mới vào `skill/dist/` (thay bản cũ); cuối phiên Nghiệp tự upload
  `aa-session.zip`.
- Link chính của trang tracker master plan: artifact `Q4LvqJyX…` (thuộc tài khoản hiện tại).
- Nghiệp tự xoay mật khẩu DataForSEO (lưu ở kho secret cục bộ) → agent cập nhật secret + kiểm.
- Sửa cảnh báo gitleaks/secret ở mọi repo một lần; cuối phiên: "gắn nhãn `secret-scan-baseline-reviewed` cho CIS #1010
  … làm luôn".
- Sau khi xong S1: tạo issue cho lan truyền toàn hệ + kiểm tự đồng bộ (→ AA-988…991).
- Lưu key tenant test vào kho secret cục bộ `secret_manager/tenant-test-keys`.
- Jira: bản rút gọn được duyệt "duyệt đăng" (đăng cả 7). Ảnh AA-835 do Nghiệp tự chụp.
- Đóng phiên: "phiên này dài lắm rồi" → wrap up, việc còn lại sang phiên sau.

## Done (kèm bằng chứng)

- **AA-645 — viết lại S1 writer v2:** **810/810 tour trên v2**, luỹ kế **$59,34 / $120**; slug 308 kiểm toàn bộ (đúng
  hết); 39 tour cưỡi voi giữ nguyên; 54 tour golden giữ nguyên. Done 10:33Z (`ALL_WAVES_DONE` 09:55Z).
- **AA-853 — schema drift:** 281 áp (DB Migrate run 40186864048); Schema Dump run 40191477074 "Drift verdict: clean"
  (0 open, 343 file replay, 0 failed); root #252/#254/#255/#261 merged.
- **AA-825 — Booking retention:** Booking #91 (task def :58) + Infra #386; DRY RUN 17/5 → live 17 job archive rồi xoá,
  5 inbox redact; object archive trên S3.
- **AA-926 — Q-1 taxonomy / gate registry / thresholds:** Done 12:51Z.
- **AA-946 — CRM-18 vòng đời thin:** crm-016, Partner #49/#50; E2E lifecycle-thin PASS (run 40190930352, chạy lại
  40202260808).
- **AA-761 — trang Account của portal:** CIS #1002 + Partner #51; UI verify portal PASS (Billing / Activity /
  Integrations / Members, 2 tenant, 1440/390, light/dark).
- **AA-947 — CRM-19 AA lines:** Partner #55/#56/#61; setup Booking (partner sen-vang + gợi ý giá); E2E Dev run
  40202260808 xanh 5/5 + 1 skip (aa-lines: quote, cảnh báo from-price, read-only 403, hold, assistant 403
  `role_forbidden`, Lost + Undo giữ hold, Lost nhả hold).
- **AA-835 — nội dung supply:** chạy live phát hiện lỗi (key cũ `sonnet` bỏ qua `json_schema` → 3/3 nháp "reply is not
  JSON", $0,011) → CIS #1016 `55e24026` (gateway giữ schema trên key cũ, `UnusableReply` / `RouteUnusableReply` có kiểu,
  kiểm trùng gặp reply hỏng = unsure) + mig 282 (route `supply_content_writer` → sonnet-5-5) Infra #395, DB Migrate apply
  40204566298. Rồi S1–S12: publish → Booking đọc ngược + text trong proposal; replay duplicate:4 UNCHANGED; rights on →
  photos1 → publish; rights off → purge (CDN 403, S3 404); deactivate → unpublished; ảnh do Nghiệp chụp (drawer Booking
  desktop + mobile, trang CIS). **Khoảng trống nêu rõ:** 409 `photo_rights` live chưa chạy sạch (probe chạy trước khi CIS
  kéo sự kiện; có unit test). Writer 6 lời gọi, $0,025. Hotel `HTL-000003` để active + published v3 (dữ liệu tổng hợp).

## Ngoài kế hoạch (Nghiệp yêu cầu trong phiên) — xong

- Rà 10 skill, đóng gói lại 10 zip (root #257; #259 thêm guard packager: description không có `<` / `>`).
- **Cảnh báo bảo mật:** 96 cảnh báo "Google API key" là chính các key mẫu của gitleaks trong `.gitleaks.toml`; viết lại
  regex không chứa key thật (Partner #57, Booking #93, Infra #393, TP #151, root #260) → 80/96 đóng; Nghiệp gắn nhãn
  `secret-scan-baseline-reviewed` → CIS #1010 MERGED `520199cd` (gộp main, gỡ + gắn lại nhãn cho lượt gitleaks theo sự
  kiện labeled) → 16 cảnh báo CIS đóng (false positive) → **96/96 đóng, 0 mở ở cả 6 repo** (kiểm `gh api` sau merge).
  Comment Jira PR-27 đã đăng con số 80/96 trước đó; không tự sửa comment (cần duyệt) — đưa 96/96 vào báo cáo tuần sau. CodeQL: CIS #1011 (5 ReDoS + 1 stack-trace) + TP #152 merged; CIS code-scanning mở = 0.
- DataForSEO: secret cập nhật, `/admin/dfs-balance/check` 200, issue Sentry resolve.
- Tạo AA-988…AA-991.
- Key tenant test lưu `secret_manager/tenant-test-keys` (4/4 đăng nhập 200).
- Ngân sách AWS acc3: $201,69 / $250 (tháng 10), dự báo $215–225.
- Partner main đỏ (test console giả định tenant mới nằm trong 200 dòng đầu) → keyset cursor (#62); Partner #60 sửa helper
  E2E (không gọi `res.json` trên 202 không đọc).

## Đang dở (còn gì + cái gì chặn)

- **AA-790 — T9 writer AI-tells:** vòng 1 CIS #1015 `e5c82e9d` live (`writer_prompt_version` 3c078692); re-panel trả phí
  20 bài $0,878; panel mù 4 góc (40 bài, trước vs sau): AI-tells 4,15 → 5,12 (**thanh 5,5 chưa đạt**), brand voice
  6,70 → 7,12 tổng (Trail Pulse 6,0, WildKind 6,75 **chưa đạt**), source fidelity 7,58 → 7,12 (LinkedIn 8,92 → 7,08 —
  hồi quy: rule AUDIENCE bịa chi tiết chuyến thăm), reader value 6,88 → 7,20. Vòng 2 = CIS PR **#1017** (nhánh
  `feat/aa-790-writer-round2`, `7d8e3785`, prompt 751b0a34; census $0 lỗi sửa được 8 → 0; 1062 unit test) **còn mở** →
  còn: review độc lập → merge → deploy → re-panel (~$0,9) → panel mù.
- **AA-919 — writing memory eval / release gate:** thiết kế + critic ở `.tmp-session/s251/aa919/{plan,critic}.md`; critic
  tìm 4 lỗi chặn ở WM-18/20 (replay tự so với chính nó, drill trả phí, fixture AA-729 trong repo gốc public với tenant pack
  tổng hợp, đường duyệt AI_ADMIN). Build WM-17 (mig 283) mất 2 lần (hết hạn mức tài khoản, rồi WSL khởi động lại) →
  phiên sau, mỗi lần một agent viết code.
- **AA-991 — probe độ tươi:** Infra #394 `464414aa`; DB Freshness Probe hằng đêm 05:13 UTC, chế độ report; run đầu
  40200002656 GREEN (read_as `cis_app`, errors 0, stale=6: `orphan_segments` 8469 aged, `geo_tour_place_stale` 1473
  aged, `place_card_links_missing` 2223 aged, `seo_context_expired_active_tours` 75,
  `angle_gate_requests_on_inactive_atoms` 11, `tours_with_place_atoms_but_no_segment` 3); thử alarm `enforce=true` run
  40200215229 RED đúng kỳ vọng.
  **Bằng chứng tự đồng bộ — rewrite tour A `8a759395` (Laos) qua promote** (POST promote 200 lúc 15:47:29Z):
  poll 1 (15:50:42Z) 3/8 layer theo, còn job `recompute` queued; poll 2 (15:53:55Z) 5/8 (atoms, ranking, routes theo
  trong 3–6 phút), không còn job mở; **poll cuối đọc được = poll 11 lúc 16:23:05Z: 5/8 layer theo, không job mở, còn chờ
  `segments`, `tour_place`, `place_cards`** (poll 2 → 11 không đổi) — tiến trình vẫn đang chạy lúc kiểm (16:24Z, giới
  hạn 5400 s; kết quả cuối chưa có). Ba layer này không nằm trong chuỗi tự động → bằng chứng cho AA-988/989. Chưa chạy bằng chứng pause/restore tour B `7df4db05`.
- **AA-990 — reader dựng chuyến:** phát hiện + sửa 409 `atom_replaced` (CIS #1013) live.
- **AA-669 — portal My Content:** Partner #59 merged (sửa layout); còn chụp lại ảnh.
- **AA-916 / AA-917 / AA-918 / AA-924:** làm một phần — còn ảnh UI / khoảng trống dữ liệu (WM-13 cần ≥3 cụm, không ép).
- **AA-945 — mail CRM:** card live OK; còn đọc `crm_mail_health` sau 19:00Z; OAuth client cần Nghiệp.
- **AA-979:** P2a-4 xong (root #253, CIS #1000, Partner #48); P2b chưa bắt đầu.
- **AA-908 follow-ups:** TP #149 merged; bằng chứng `email_verified` cần địa chỉ traveller E2E thứ ba (rule SES ở Infra).
- **AA-978 follow-ups:** crm-018 áp, alarm áp, tab Members đã ship.

## Sự cố

- **Tài khoản claude.ai cũ hết hạn mức phiên** giữa workflow → mất 2 workflow (AA-790 vòng 2 và AA-919 WM-17 phải chạy lại).
- **WSL VM khởi động lại** (~22:45 giờ máy, uptime 0) — gần như chắc do hết RAM: 3 workflow viết code song song trên máy
  8 GB (AA-790 vòng 2, AA-919 WM-17, AA-835 UI smoke). Cả ba run mất; việc đã merge/deploy không ảnh hưởng. Luật mới: mỗi
  lúc chỉ một agent viết code (workflow chỉ đọc chạy kèm được).

## Trạng thái kiểm cuối phiên (snapshot ~16:30Z)

- STS acc2.
- ECS: `aa-cis-dev-api:829` + `aa-cis-dev-worker:395` image `dev-55e24026` COMPLETED; `aa-booking-dev-api:58`
  `8d00c76d`; `aa-crm-dev-api:48` + `aa-crm-dev-web:22` `e83aef55`; tất cả 1/1.
- CIS `/health` git 55e24026, `/health/ready` schema 282 (required 280). Booking `/booking/health` 8d00c76d, ready
  bk-024 (Booking main `76259f79` là commit chỉ đổi cấu hình gitleaks, không deploy).
- Lambda TripPlanner browse/assembly CodeSha256 `rFXJi1TS…`, LastModified 25/10 11:40Z.
- Job: `shared.job` trống; `booking.job` queued 1 (theo lịch); `crm.job` chưa kiểm.
- Repo: root master (sau #261); CIS main `55e24026` lúc snapshot (mở #1017, #1009; #1010 merged sau đó `520199cd`); Booking main `76259f79` (mở #92);
  Partner main `b26d4a11` (mở #52); TP main `f024a396` (mở #153); Infra main `7f7b226d` (không PR mở).
- Chi tiết: `docs/audits/2026-10-25-S251-wrap/state-snapshot.md`.

## Chi phí

- S1 toàn chiến dịch: **$59,34 / $120** (810/810 tour).
- AA-790: re-panel 20 bài $0,878. AA-835: lần lỗi $0,011 + 6 lời gọi writer $0,025.
- AWS acc3 tháng 10: $201,69 / $250, dự báo $215–225.

## Jira (đã đăng, Nghiệp duyệt)

- PR-22 comment `c10503`; PR-27 `c10504`; PR-26 `c10505` (4 ảnh); PR-25 `c10506` (5 ảnh); PR-24 `c10507` (3 ảnh);
  PR-23 `c10508` (4 ảnh); story mới **PR-28** "Báo cáo nền tảng kỳ 2 (20–26/10/2026)".
- Nháp: `docs/audits/2026-10-25-S251-wrap/jira-drafts-final.md` (bản rút gọn đã đăng), `jira-drafts.md` (bản dài + bảng
  bằng chứng).

## Việc cần làm đầu phiên sau (S252, theo thứ tự)

1. **AA-790:** review độc lập #1017 → merge → deploy → re-panel (≤$2) → panel mù so với các thanh.
2. **AA-919:** WM-17 (mig 283, importer, guard không có text tenant) theo các sửa của critic; sửa plan WM-18/20 (replay so
   với dump trước refactor; drill $0; fixture ra khỏi repo gốc public; duyệt qua UI tối thiểu hoặc CLI + ghi chú ADR).
3. **AA-991:** bằng chứng pause/restore tour B; rồi sửa AA-988/989 (segments, tour_place, place_cards chưa nằm trong chuỗi
   tự động); sau đó bật ENFORCE.
4. Release PR (CIS 0.11.0, Booking 0.7.0, Partner 0.5.0, TP 0.8.2) khi không có proof/wave nào đang chạy.
5. AA-945 `crm_mail_health`; AA-908 `email_verified`; AA-979 P2b; AA-669 chụp lại ảnh; AA-916/917/918/924 bằng chứng còn lại.

## Lưu ý kỹ thuật cho phiên sau

Toàn bộ bài học chờ ở `.tmp-session/S251-lessons-pending.md` (chuyển vào `skill/aa-lessons/lessons.md`). Điểm chính:

- Máy WSL 8 GB: tối đa **một** workflow viết code mỗi lúc.
- Hook guardrail subagent chỉ khớp dòng lệnh → ECS exec gọi qua script helper lọt qua; việc verify live (ECS exec) là của
  điều phối, subagent chỉ soạn runbook.
- Trang ERD thiết kế `enforce=true` phải đổi cùng PR với migration đổi bảng của nó (tp-019 làm Schema Dump đỏ).
- Không dán nguyên file rule mặc định có key mẫu vào repo public (96 cảnh báo); App `aa-agent` không đổi được trạng thái
  cảnh báo secret scanning (403) và gắn nhãn bằng `gh pr edit --add-label` có thể hỏng âm thầm trên AA-CIS-App → dùng REST
  `issues/<n>/labels` rồi đọc lại.
- Stage có `json_schema` phải route tới key catalog; key cũ (`haiku`/`sonnet`/`gpt-4.1`) bỏ qua schema (lỗi AA-835).
- Sau khi xoay credential vendor: cập nhật secret trước deploy kế tiếp hoặc ép deployment mới (task đọc secret lúc start).
- Merge loop: `mergeStateStatus` là BLOCKED (không phải BEHIND) khi check cuối đỏ → dùng `compare/main...head` behind_by.
- Đổi file kit vendored CIS (`frontend/app/_kit/*`) → ship bản copy Partner ngay sau, nếu không Partner main đỏ.
- Playwright: `fullPage` trên admin chỉ chụp viewport (vùng cuộn là `<main>`); không gọi `response.json()` trên response
  trang không đọc; trang not-found có API 404 cần `expectApiFailure`.
- Feed supply Booking → CIS có độ trễ: chờ ~60 s trước khi pull trong script bằng chứng.
