# S261 (31/10/2026): dọn In Progress, vá quyền IAM, cổng AI v2, CRM 7 module chốt, AA-997 luật aa997.4, video review CRM phiên A

Tác nhân: **Claude Code** (VSCode/WSL, Ultracode; lane code trong worktree → reviewer độc lập → sửa; tối đa 3 lane nặng
vì RAM 9 GB). 31/10 ~08:10 → ~18:10 +07 (01:10Z → ~11:10Z). Số liệu cuối phiên:
`docs/audits/2026-10-31-S261-close/state-snapshot.md` (kiểm ~10:59–11:05Z; chỗ không kiểm ghi "chưa kiểm").
Sự cố môi trường: 15:05 +07 WSL khởi động lại (hết RAM, extension VSCode `cloudcode_cli` giữ ~3,4–3,8 GB), mất 2 tác
vụ nền (lần gọi lại acc4, workflow video), chạy lại sau đó có chốt RAM.

## Quyết định của tech lead (chỉ lời / quyết định của tech lead)

- Mở phiên: "việc nào cần tôi duyệt thì duyệt cho làm luôn theo kế hoạch" → trang quyết định §6 của triage S260 coi
  như đã duyệt (câu chữ Done-with-scope, follow-up, `hide_flagged` theo đề xuất, CRM12 theo đề xuất).
- ~04:10Z: **duyệt kế hoạch video review CRM** (Q1–Q8); **duyệt tạm hai giọng** (EN Kokoro `af_heart`, VI VieNeu nữ
  miền Nam), chờ nghe mẫu R01/R03; phụ đề và giọng phải đổi được (MP4 chủ 2 audio + 2 phụ đề mềm, bản Drive không in
  cứng phụ đề); agent tự xếp lịch phiên.
- ~04:30Z: duyệt mô hình tổ chức AWS + kế hoạch dung lượng / quota LLM (phần tech lead T1–T14); phần business owner
  B1–B7 chờ chị Thư.
- AA-967: chọn **(a)** — diễn tập xoá thật trên Dev.
- ~13:40 +07: đường LLM Dev qua API Anthropic: **dựng sẵn, chưa thêm key**; **bằng chứng quota cho case AWS: chưa gửi,
  chờ vài ngày** (đã chat trực tiếp 30/10), không nhắc; **TL-7 (rule env `prod` của Infra): chưa làm**, không nhắc;
  **mật khẩu DataForSEO đã xoay từ S251 (25/10)**, không bao giờ nhắc lại; **GitHub không tốn tiền → repo gốc +
  Infra giữ public** (huỷ kế hoạch về private 01/11).
- ~14:35 +07: **acc3 giữ độc lập, chưa cần vào org AA vội** (comment AA-1004).
- ~17:20 +07: **duyệt cả 3 đề xuất thiết kế cổng AI v2** (một cổng cho mọi nguồn trả phí; đường dự phòng ấm bắt buộc;
  acc2 chạy chat cho chấm/kiểm, writer giữ Claude). Lưu ý của tech lead: API ngoài = **cả Anthropic và OpenAI**; yêu
  cầu đánh giá UI cần làm lại thế nào, ảnh hưởng, và tạo ít issue nhất.
- ~18:00 +07: **duyệt thiết kế cổng AI v2** (root #397 merged; phần đã duyệt của ADR 0009 = Accepted). Luật mới:
  **không nói trạng thái theo trí nhớ — kiểm live** (memory `verify-live-before-claiming`).
- Artifact S261 nằm dưới tài khoản claude.ai `nghieppham@adventure.asia` (memory `claude-account-nghieppham`).
- Cuối phiên: "vậy dừng phiên đi … lưu ý nháp jira lưu sang cho phiên tiếp theo ngay sau đây cùng ngày làm việc luôn".

## Kết quả theo issue

| Issue | Kết quả | PR / bằng chứng |
|---|---|---|
| Dọn In Progress (đợt 1) | 31 → 12 In Progress: Done-with-scope AA-880, AA-919, AA-1002, AA-816, AA-703; AA-642 viết lại thành issue giao được (Todo); nhóm bị chặn về Backlog/Todo kèm blocker + trigger; tạo follow-up AA-1005…AA-1010 | Linear comment từng issue; `docs/audits/2026-10-30-S260-inprogress-triage/` |
| AA-923 | **Done**: WM-34 retired; WM-32 hai nhãn; WM-33 diễn tập xoá tenant tổng hợp (DRY RUN 15/2 → snapshot → xoá thật, tenant khác SHA không đổi → dọn seed + xoá snapshot) | `S261-evidence/AA-923/`, retention-log |
| AA-921 | Kiểm live xong (mark, refresh, pin/unpin, cách ly 9 owner 0 rò rỉ, ảnh 1440 light/dark) → Backlog (phần còn lại cần LLM) | `S261-evidence/AA-921/` |
| AA-788 | Replay 349/349 (300 replay, 0 lỗi): giữ thêm tối đa 5 (1,7 %, đều F12_scope) → Backlog, chờ 19/11 + LLM | `S261-evidence/AA-788/` |
| AA-997 | CIS #1193 (luật aa997.4 day-guard) deploy api :940 / worker :506; trial 50 dòng ($0, 0 lỗi); 5 điểm regressed trả về; chuỗi `b0190743` 75 dòng rồi dừng credit ngày → `dc260ef8` chạy lại ~00:12Z 01/11 (còn 1.024 dòng). **In Progress** | `docs/audits/2026-10-31-S261-aa997-report/` (số chốt điền sau 01/11) |
| AA-990 | **Done-with-scope** (Booking/CRM/portal đọc đúng S1 v2); 3 lỗi Booking → AA-1013 | `S261-evidence/AA-990/` |
| AA-945 | **Done-with-scope** (saved reply, ghi chú, nháp); M365 + SMTP + lịch → AA-1011 | `S261-evidence/AA-945/` |
| AA-955 | **Done-with-scope** (mã hết hạn 422, re-accept 409 → 200, waiver + từ chối niêm phong); PAdES → AA-1012 | `S261-evidence/AA-955/` |
| AA-961 | **Done**: sự cố bật → gỡ live qua run-script (banner, task `aa_incident`, panel Travelling) | Infra #544/#545/#546; `S261-evidence/AA-961/` |
| AA-967 | **Done**: xoá thật một khách tổng hợp (receipt `subject_gone`, 404, DRY RUN lại 404, export huỷ); cờ `LIFECYCLE_DRY_RUN` tắt tạm (rev 91) rồi bật lại (rev 93) | Infra #547 → #548; retention-log; `S261-evidence/AA-967/` |
| AA-952 | Lát 4 (claim, gia hạn giữ chỗ một lần, giữ lại khi cọc trễ, nhắc quá hạn) + F1/F2 (ô thanh toán chờ chấp nhận lại điều khoản); live 15 mục đạt; Migration Apply từng từ chối crm-028 (bảng chưa ANALYZE) → Infra #538. **In Progress**, còn 2 mốc giờ | Partner #143, #148; Infra #536, #538; `S261-evidence/AA-952/` |
| AA-953 | **Done**: portal theo từng người (live 13 mục; review 4 major bảo mật đã sửa) | Partner #145, Infra #539; `S261-evidence/AA-953/` |
| AA-962 | **Done**: onboarding + import (coverage 89,10 → 91,51 %) | Partner #146, Infra #540; e2e Dev 41172484182; `S261-evidence/AA-962/` |
| AA-966 | **Done**: báo cáo + insight (insight đếm trip một lần qua view crm-031) | Partner #144, root #391, Infra #537; `S261-evidence/AA-966/` |
| E2E CRM | CRM-18 đỏ do 429 (limiter ẩn danh dùng chung) → limiter riêng cho phiên portal; spec CRM-18/21b theo hành vi mới | Partner #149, #147; e2e 41177723455 (9 passed, 1 skipped) |
| Partner #150 | Không giao thư cho địa chỉ `.invalid` | Deploy Dev 10:52Z |
| AA-994 | **Done-with-scope**; phần còn lại → AA-1006 (CIS kit S6b), AA-1007, AA-1008 | Linear |
| AA-873 | Vá chuỗi đọc secret IAM (F1/F2 của review kiến trúc): apply cục bộ 2 đợt có target, simulate Deny đạt, CIS ready 200 không restart. Rút gọn ghi chú nhạy cảm ở Infra. Chi tiết trong Linear AA-873. **In Progress** (GuardDuty vẫn tắt; TL-7 chưa làm) | Infra #541, #543 |
| AA-1002 | Done-with-scope (đầu phiên); sau đó dựng đường Anthropic Dev **không key**: 2 stage `vendor_direct`, budget 150 USD/tháng, connection tắt | Infra #549, #550; root #395 (runbook) |
| AA-1004 | Mô hình AWS + Bedrock theo account; form Anthropic: acc4 đã nộp bằng API (profile `aa-mgmt`); acc4 gọi được Nova + Cohere embed; Claude "account being verified"; acc3: hoá đơn tháng 8 đã trả, case chờ AWS gỡ (~05–06/11) | Infra #542; `docs/audits/2026-10-31-S261-aws-bedrock-org-access/` |
| AA-804 (cổng AI v2) | Thiết kế v2 duyệt; root ADR 0009 (phần đã duyệt Accepted); tạo AA-1017 (sổ nguồn v2, hạn 28/11), AA-1018 (độ tin cậy, hạn 05/12); cập nhật AA-642 (lát S0 0 USD), AA-900, AA-1016, AA-820, AA-964 | root #397; `docs/audits/2026-10-31-S261-ai-gateway-design-v2/` |
| Capacity LLM | Kế hoạch 5 tầng quota, B2C/B2B/B2B2C, giám sát; tạo AA-1015, AA-1016 | `docs/audits/2026-10-31-S261-llm-capacity-plan/` |
| Review kiến trúc 9 vai | 3,2/5; F1/F2 đã vá (Infra #541) và rút khỏi bản public; TL-x / BO-x chờ quyết | `docs/audits/2026-10-31-S261-architecture-review/` |
| Repo private | Báo cáo rủi ro phút CI (~26.000 phút/tháng, gấp 13 lần Free) → tech lead giữ public, mục huỷ | `docs/audits/2026-10-31-S261-private-repos-risk/` |
| AA-1014 (video review CRM) | Phiên A xong: 21 đoạn + prep/cleanup PASS fast trên Dev; mẫu R01/R03 EN + VI ở `.tmp-session/S261/video-samples/` (đã lên Drive: chưa kiểm). **In Progress**, hạn 10/11 | root #396; worktree `.tmp-session/wt/s261-video-a` giữ cho Session B |
| Ứng viên writer Bedrock | Mẫu 16 model (không chạy pipeline) | `docs/audits/2026-10-31-S261-bedrock-writer-candidates/` |

Issue tạo trong phiên: AA-1005…AA-1010 (follow-up triage), AA-1011, AA-1012, AA-1013 (follow-up CRM/Booking), AA-1014
(video), AA-1015, AA-1016 (capacity), AA-1017, AA-1018 (cổng AI v2). Issue Done trong phiên (Linear, đọc lại cuối
phiên): AA-1002, AA-880, AA-919, AA-816, AA-703, AA-994, AA-923, AA-990, AA-945, AA-955, AA-961, AA-967, AA-953,
AA-962, AA-966.

## Trạng thái live cuối phiên (từ snapshot)

- ECS (đều COMPLETED, 1/1, rev đang chạy = rev mới nhất): cis-api :940 + cis-worker :506 cùng `dev-1b6e9448`;
  booking-api :90 (`636df62c`); crm-api :94 (`bc5f9280`); crm-web :66 (`ba225e4b`).
- Migration: CIS 317 (required 315), bk-035, crm-031 (ready endpoint); tp-022 chỉ theo dòng Verified, live chưa kiểm.
- Health: CIS, Booking, CRM api/web (portal), TripPlanner đều 200; `crm.lumiguides.it.com/healthz` 000.
- Lambda TP browse/assembly cùng CodeSha256 (30/10 12:27–28Z).
- Vercel: CIS `041ba9a2` (head CIS không đổi `frontend/`), TripPlanner `02dd9f1c`, Booking `636df62c`; portal chưa kiểm.
- `shared.job`: 1 queued (place_relocate `dc260ef8`, cố ý), 0 running, 0 wave; `booking.job` / `crm.job` chưa kiểm.
- CI đỏ: root Secret Scan full history (từ 02:48Z, gitleaks `aws-access-token` trong `tools/docs/test_docs_reader.py`,
  commit `97a3c2b8` #302, có thể là giá trị giả — chưa kiểm); Infra DB Freshness Probe 4 đêm (111 link
  `place_card_links_missing`).
- PR mở: root #374, #328; CIS #1179; Booking #161; TP #196; Partner #133 (release bot / chờ).
- Để BẬT: đường Anthropic Dev (không key), CRM `LIFECYCLE_DRY_RUN=true`, chuỗi AA-997 `dc260ef8`, worktree video.
- LLM: chi phí LLM trong phiên chưa kiểm từ `llm_call_log`; không chạy việc LLM trả phí (acc3 vẫn chờ AWS).

## Jira

**Chuyển S262** (cùng ngày): chưa soạn, chưa đăng, theo lệnh tech lead. Danh sách việc cần báo:
`docs/audits/2026-10-31-S261-close/jira-drafts.md`.

## Việc cần làm đầu phiên sau (S262, cùng ngày)

1. **Nháp Jira** (S258…S261 còn tồn + S261): soạn một lần từ `jira-drafts.md`, đưa tech lead duyệt một lần, rồi đăng.
2. **AA-952**: kiểm nhắc nợ ≥ 18:10Z 31/10 và link hết hạn ≥ 04:35Z 02/11 (spec `.tmp-session/S261/aa952`) → Done-with-scope.
3. **AA-997**: sau chuỗi `dc260ef8` (~00:12Z 01/11) → audit cuối → điền chỗ trống của báo cáo
   `docs/audits/2026-10-31-S261-aa997-report/` → quyết TL-25 (`hide_flagged`) → đóng.
4. **Một trang quyết định bấm chọn** cho các mục TL còn mở của review kiến trúc (memory `artifact-decisions-interactive`).
5. **AA-642 lát S0** (sửa lỗi 0 USD theo cổng AI v2).
6. **AA-1014 Session B** trước 10/11 (prep lại dữ liệu ≥ 1 giờ trước R10).
7. **AA-896** (hạn 01/11) và **AA-922** (hạn 02/11).
8. **AA-994 follow-up UI kit** (AA-1006 CIS S6b, rồi AA-1007, AA-1008).

Kèm theo khi rảnh: xem lại CI Secret Scan đỏ của repo gốc và DB Freshness Probe đỏ của Infra (snapshot mục "Cần biết
trước"); C4.3 W45 từ 02/11; AA-1003 bằng chứng report_run (≥ 03/11).
9. AA-1014: tech lead nghe mẫu R01/R03 (giọng duyệt tạm; mẫu đã lên Drive, rclone check 0 khác biệt, 10 file).
10. AA-997: khôi phục 6 dòng regressed cũ từ relocate.prev (kèm lúc đóng).
11. Root Secret Scan (full history) đỏ từ 02:48Z: 2 báo nhầm đã ghim trong root PR chốt S261 (khoá giả AKIA…ABCDEF trong test, question_key Jev) → kiểm xanh lại.
12. Infra DB Freshness Probe đỏ 4 đêm (place_card_links_missing 111) → điều tra.
13. db-schema-reference cũ (crm-027, live crm-031) → chạy DB Schema Dump publish=true; host crm.lumiguides.it.com/healthz trả 000 → kiểm DNS/host.
14. acc4 (kiểm 09:40Z): Claude 4.x chạy, Claude 5 "not available for this account" — chỉ ghi nhận, không có việc.

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- Không nói trạng thái theo trí nhớ: kiểm live hoặc ghi "chưa kiểm" (3 lần nói sai trong phiên).
- Giải thích sự cố tài khoản phải đọc Cost Explorer + CloudTrail trước (acc3 từng tự trả tháng 8).
- Trước khi tư vấn hạ tầng, đọc log 3 phiên gần nhất + snapshot (acc4 đã dựng từ S259).
- Trước khi đề xuất model/gateway, đối chiếu thiết kế đã duyệt và issue đang mở.
- Brief lane có dòng AUTHORIZATION; subagent soạn payload Linear, điều phối áp bằng script.
- Merge train: "giữ cả hai bên" chỉ an toàn cho dòng danh sách; chạy tsc/eslint/vitest sau rebase có xung đột.
- DB Migrate: bảng chưa ANALYZE bị expand guard từ chối (đã sửa Infra #538); apply-pending không nhảy khoảng trống số →
  merge theo thứ tự số migration.
- Limiter portal có phiên phải tách khỏi limiter ẩn danh.
- Geocode: khớp tên trong bán kính chưa đủ, phải có bằng chứng của chính ngày đó (aa997.4).
- Lặp lại (gộp vào dòng cũ): zsh không tách từ; WSL hết RAM với lane TTS + Chromium; gitleaks bắt khoá map `_key` trong HCL.
