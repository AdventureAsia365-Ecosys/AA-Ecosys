# S237 — 14→15/10/2026 — Chuỗi lane 5 repo, RLS tenant (229), retention (233), Booking đợt 2, data standards v1.0

**Tác nhân:** Claude Code (VS Code, Ultracode bật) — điều phối + workflow nhiều agent (lập lane, build trong worktree,
review đối kháng, UI verify + phản biện, review kiến trúc dữ liệu, data standards, dịch song ngữ). Subagent chỉ commit;
push / PR / merge / apply / deploy do phiên chính làm.
**Audit / artifact:** `docs/audits/2026-10-14-S237-lane-backlog/` (journal điều phối, lanes, aa712 trial + 6b parity,
aa817 probe trước/sau 229, booking demo, data-architecture review, ui-verify), `docs/architecture/data-standards/` (v1.0),
artifact "AA Data Platform Standards" (song ngữ Anh–Việt, riêng tư): https://claude.ai/artifact/R1YLp4i1QCt3kjnKd6yvvJ

## Trạng thái cuối phiên
- ECS CIS: api :611 / worker :168, cùng `dev-50bd488`, COMPLETED, `/health` 200. Worker có thêm `T3_BACKGROUND_FACTS=on`.
- Booking: task def :14, `/booking/health/ready` → **bk-010**.
- TripPlanner: Lambda pool **1 kết nối/instance**; reserved concurrency browse **15**, assembly **5** (ngân sách 20 kết nối).
- Migration áp trong phiên: CIS **228, 230, 231, 229, 233**; Booking **bk-007 → bk-010**. 232 bỏ trống (D1/D4).
  `db-schema-reference.md` đã regenerate (CIS 233, tp-010, bk-010).
- RDS: Performance Insights bật, `max_allocated_storage` 100, alarm mới; **chờ maintenance window thứ Hai 04:00–05:00 UTC
  (11:00–12:00 giờ VN)**: đổi `db.t3.micro → db.t4g.small` + parameter group `aa-cis-dev-pg15` (reboot 1–2 phút cả 3 app).
- `shared.job` rỗng cuối phiên. Lambda quota acc2 = 1.000 (AWS duyệt sớm 15/10).
- Vercel TripPlanner: target **Preview** đã có `BROWSE_API_URL` / `TRIP_API_URL` / `TRIPPLANNER_API_KEY` /
  `NEXT_PUBLIC_MAPBOX_TOKEN` (trước đây chỉ Production/Development → mọi preview 500).

## Quyết định của Nghiệp
- "Duyệt toàn bộ", toàn quyền chạy mọi lane tới cuối rồi báo cáo chi tiết; chốt D1–D9 (số migration, 229 ENABLE không
  FORCE, AA-819 tách lane, AA-679 đọc live catalog, SES apex, Laos thử, 228 chỉ view, luồng migration D8, quota Linear 100).
- Review kiến trúc dữ liệu: "đồng ý duyệt hết" E1–E11 (ADR 0008/0003a, tách role Booking/TP trước, retention 180/90/30–90 ngày,
  view contract trong `catalog`, t4g.small + PI, giới hạn kết nối trước quota 1.000, `inquiry.submitted` v1.2,
  `booking.customers` là bản gốc, CRM nghiên cứu trước) + yêu cầu bộ tiêu chuẩn kỹ thuật/quản lý dữ liệu/scale + artifact
  (sau đó bản song ngữ).
- Cho quyền cố định `gh pr merge`, `gh workflow run`, `terraform apply` trong `.claude/settings.json` (không commit).
- "Làm luôn": tự thêm env Preview cho Vercel TripPlanner.

## Thay đổi Codebase
- **CIS:** #727 AI notice + field giới hạn publish, #728 mig 228 (view place/graph), #729 mig 230, #730 gate F19 authenticity +
  giới hạn publish/ngày, #731 Facebook connect + unpublish thật + disconnect, #732 sửa im lặng T2 + chỉ báo bản cũ,
  #733 T2 best draft + targeted repair + background facts, #734 mig 231, #735 ledger từng attempt + Label,
  #736 mig 229 (RLS mẫu `TO aa_app_user`), #737 writer panel, #738 đọc piece qua tenant pool (cờ tắt, fail closed),
  #739 mig 233, #740 retention TTL + rollup (mặc định DRY RUN).
- **TripPlanner:** #75 slice 6a (bỏ writer địa điểm), #76 bộ 30 câu search AA-805, #77 AA-812 (ảnh dự phòng, WCAG AA,
  lọc tháng), #78 slice 6b (`PLACES_SOURCE=legacy|cis`, mặc định legacy), #79 pool max 1.
- **Booking:** #6 đóng đợt 1, #7–#8 AA-810 maker-checker (bk-007), #9–#10 AA-822 NCC + hợp đồng (bk-008),
  #11–#12 AA-679 trip plans (bk-009), #13–#14 AA-823 khách sạn/dịch vụ/giá net (bk-010).
- **Infra:** #110 Copy Guard (byte-for-byte), #111/#112/#115–#120 bản copy migration, #113 Route 53 + SES (AA-811),
  #114 permissions boundary (AA-806 bước 4), #121 RDS guardrails (AA-824), #122 dump schema hằng đêm + runner an toàn
  (AA-807 N1/N5), #123 ACM + custom domain có cổng (AA-818), #124 `T3_BACKGROUND_FACTS`, #125 concurrency TP.
- **Gốc:** #71 contract `catalog.graph.v1` / `catalog.tour.v1.1`; PR S237 (data standards v1.0, ADR 0008 + 0003a + index
  `docs/adr/README.md`, `schema-ownership.md` quy tắc 2 → chỉ view + dòng job → 0003a, con trỏ ADR 0001/0003, audits,
  schema reference, lessons, steering quota 100, nháp điều khoản AA-820, log này).

## Thay đổi Hạ tầng / AWS
- Terraform **apply cục bộ có target** (không apply full root từ CI vì drift ẩn): #113 (31 add / 1 change), #114 (13 role
  boundary), #121 (4 add / 4 change / 0 destroy, có guard chặn delete), #124 (task def worker), #125 (browse 15).
  Plan luôn đọc trước khi apply (classifier chặn "blind apply" — tách plan/apply).
- Route 53 zone `lumiguides.it.com` NS: ns-1284.awsdns-32.org, ns-1671.awsdns-16.co.uk, ns-178.awsdns-22.com,
  ns-764.awsdns-31.net — **chưa đổi NS ở Namecheap** → SES DKIM/MAIL FROM còn PENDING, ACM (#123) chưa apply.
- Lambda reserved concurrency: tạm 5/5 lúc quota được duyệt sớm → nay browse 15 / assembly 5 trong Terraform.
- Vercel env Preview (chỉ thêm target, không đọc giá trị).

## Bằng chứng verify
- AA-712: thử 3 tour Laos PASS ($0,024/tour); batch Laos 43/43 → 46/46 build ok ($0,755); 142/573 tên địa điểm còn pending.
  Parity 6b (Laos, legacy vs cis): phủ tốt hơn hẳn (graph 45 vs 4 tour, tour-route 46/46 vs 27) nhưng chậm hơn
  (route ~1 s vs 40 ms, tiles 1 s vs 0,12 s, chi tiết điểm đến 3,6 s vs 0,85 s) → giữ legacy tới khi có L4.
- AA-817: probe sau 229 với `aa_app_user`: GUC lạ/rỗng/master → 0 dòng; tenant đúng → 6/74/8 dòng; facts chỉ dòng platform;
  không còn default ACL; runner (owner) vẫn thấy hết.
- AA-825: view usage dùng range predicate, 16 cột, 2 bảng rollup, index hợp lệ; `/admin/job-runner/retention` 5 kind DRY RUN.
- AA-793: rerun 14 cặp (+3 thử) — escalation **0/14**, **$0,080/version**, 0 lần lưu bản điểm thấp hơn; tổng $1,42 → **Done**.
- AA-819: lượt T9 dẫn về review ($0,131): thân bài không bịa review/rating/trích dẫn; F19 qua (CTA của tenant được miễn theo
  thiết kế). AA-791: ledger từng attempt hiện trên drawer admin (ảnh 1440/390).
- AA-824: burst 40 request tiles song song không cache trên production → 40 × 200 (trước: 503 khi List prefetch 24 trang).
- UI verify (workflow 4 khu vực + phản biện): xem `ui-verify/README.md` — PASS: AA-819 admin + AI notice, quy tắc
  tenant-chỉ-thấy-nội-dung, regression Booking, WCAG AA; nhiều mục NOT VERIFIABLE vì cần thao tác ghi.

## Linear
- Done: AA-793, AA-812 (AA-805 Done trong phiên).
- Comment bằng chứng: 668, 679, 712, 791, 802, 807, 810, 815, 817, 818, 819, 823, 824, 825 (+ 683, 801, 792 đầu phiên).
- Tạo mới: AA-822, AA-823 (Booking đợt 2), project "Data Platform — Schema, Ops & Scale" + AA-824…AA-829.

## Còn lại (phiên sau)
1. **Nghiệp làm tay:** đổi NS Namecheap → Route 53 (sau `dns-parity.md`); xin SES production access; thêm secret GitHub
   `ROOT_REPO_DOCS_TOKEN` cho AA-CIS-Infra (AA-807 N1); Mapbox: cho phép host preview `*.vercel.app`; site WordPress test có
   app password (AA-815); người duyệt thứ hai AA-810; quyết CTA tenant có nhắc review (AA-819); lưu trữ issue Done trên Linear;
   kích hoạt cost tag trong Billing; `.wslconfig` 12 GB + `wsl --shutdown` khi rảnh.
2. Sau khi đổi NS: apply ACM round 1 (#123) → custom domain round 2 → Cognito #105.
3. Thứ Hai: theo dõi reboot RDS (t4g.small + pg_stat_statements) → tính lại connection budget; migration CONNECTION LIMIT (N3).
4. AA-817: bật cờ `aa817:content_piece_reads_pool` có theo dõi; rồi tách role CIS (X1).
5. AA-825: DRY RUN từng kind, đọc số, rồi bật xoá thật; thêm rule lifecycle `archive/` cho bucket bronze.
6. AA-712: tối ưu view catalog (L4) trước khi chuyển `cis`; 142 tên pending.
7. Sửa lỗi UI ghi trong `ui-verify/README.md` (D5 tên quyền Facebook, layout portal 390, cột LABEL, bảng pricing rules…);
   test UI smoke AA-752 "collapse rail" flaky 2 lần.
8. AA-791: bộ 30 piece fault-injection trong CI; AA-819: lỗi 429 lần publish thứ 21 + audit badge TripPlanner.

## Lưu ý kỹ thuật cho phiên sau
- Kết quả ECS exec dài bị cắt im lặng → dùng `.tmp-session/s237/exec_s3out.sh` (wrapper upload stdout lên S3).
- `jobcheck2.py` kiểm cả `shared.job` và `booking.job` trước apply/merge.
- Merge/apply: chạy lệnh đơn, đọc plan trước khi apply (classifier chặn gộp plan+apply và lệnh ghép).
- WSL 7,6 GB: tối đa ~3 agent song song (OOM đã giết phiên 3 lần).
- Lessons mới trong `skill/aa-lessons/lessons.md`: ECS exec cắt output, Vercel Preview thiếu env, concurrency + pool, SET ROLE vs
  session_user, stand-in conftest toàn cục.

## Phần 2 (chiều 15/10) — làm nốt 7 việc sau báo cáo đầu
- **DNS:** Nghiệp đổi NS Namecheap → Route 53. Trước khi đổi đã so 10/10 bản ghi; bảng Namecheap có thêm `acp`, `langfuse` (không cần, bỏ), `www`/`api` (đích chết, xoá khỏi Route 53), 6 CNAME ACM của chứng chỉ acc1 không dùng (đã xoá 4 chứng chỉ). Mail Zoho, api-cis, aa-cis chạy bình thường sau khi đổi. Lưu ý: auto-renew tên miền đang tắt (hết hạn 04/04/2027).
- **AA-818:** chứng chỉ ACM ISSUED; custom domain chạy: `api-booking.`, `api-tripplanner.`, `tripplanner.lumiguides.it.com`. SES đã verified + DKIM; MAIL FROM chờ AWS kiểm; đã xin production access (PENDING).
- **AA-824 Done:** reboot RDS ngay (t4g.small, max_connections 181), migration 234 (pg_stat_statements + giới hạn kết nối theo role), `application_name` cho mọi pool (CIS/Booking/TP).
- **AA-807 N1:** Nghiệp thêm token GitHub → dump schema tự mở root PR #73 (đã merge).
- **Mapbox:** thêm domain mới vào token `tripplanner-frontend`; bản đồ chạy trên domain mới (preview nhánh không có map vì Mapbox không nhận `*`).
- **AA-815 Done:** site WordPress test (TasteWP), vòng đăng → gỡ → bài vào thùng rác → ngắt kết nối; Facebook token giả báo lỗi đúng.
- **AA-819:** cảnh báo khi CTA của tenant nhắc review/số sao + báo admin; Q14 vào bản nháp điều khoản; tin Zalo cho chị Thư Nghiệp giữ để trao đổi sau.
- **Trang /admin/api-docs** (admin-only, đọc spec qua BFF). Review phát hiện và sửa lỗ hổng có sẵn: proxy BFF có thể bị `..%2F` leo ra khỏi tiền tố khi kèm admin secret.
- **Tự đồng bộ key tenant test:** xoay key 4 tenant test → app tự ghi key mới vào `aa-cis/dev/e2e-tenant/<slug>`; đã thử xoay atlas-hearth → đăng nhập 200.
- **AA-810 Done:** duyệt 2 người live (e2e tạo, tự duyệt bị 403, Nghiệp duyệt, báo giá EUR 1.410).
- **Billing:** TrueIDC đã bật 5 cost allocation tag; tài khoản tự tạo được Budgets (số liệu sau ~24 giờ).
- **Quy trình:** thêm bước soạn draft Jira cho Nghiệp duyệt cuối phiên (skill `aa-session` 4b + steering). Draft S237: `docs/audits/2026-10-14-S237-lane-backlog/jira-drafts.md` (PR-17, PR-12, PR-11, PR-14, PR-7) — chưa đăng.
- **Memory:** cách nhắn Zalo cho TrueIDC (`zalo-message-to-trueidc`).
- Trạng thái cuối: ECS CIS api :616 / worker :173 (`dev-02f5592`), Booking :15, TP Lambda pool 1 + concurrency 15/5; CIS migration mới nhất 234.
