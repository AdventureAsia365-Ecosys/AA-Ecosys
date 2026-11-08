# S273 — W2 sinh bài held-out, kiểm toán + thiết kế lại DFS, bức tranh hệ thống, vệ sinh CI/CD (ADR 0021)

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). 08/11 ~17:00 → 09/11 ~07:00 +07. Đổi tài khoản Claude 2 lần
(lần cuối ~00:30 09/11), MFA làm mới 1 lần (19:10), vài cửa sổ tắt auto mode (secret GitHub, xoá role, org settings).
Snapshot: `docs/audits/2026-11-08-S273-session/state-snapshot.md`.

## Trạng thái
- Danh sách đầu phiên (duyệt "đồng ý list đề xuất", bật Ultracode): AA-1038 R5, AA-1048 W2, AA-1047 W1, AA-1049 W3,
  AA-911, AA-820, AA-1040, Jira + PR-20.
- Kéo thêm ("ok list thêm"): C4.3 W46, AA-1053, AA-1050 W4, AA-1004, AA-1052 W6, AA-1051 W5, nháp PR-20.
- Phát sinh theo yêu cầu: CI/CD hygiene + GitOps (ADR 0021), đổi role admin 12 h, kiểm toán DataForSEO, thiết kế
  dữ liệu SEO mới, bức tranh toàn hệ thống (recompute, bật/tắt tour, chi phí).

## Quyết định của tech lead
- Trang quyết định 21:32: guard T9 stable_keys theo job cho tenant audit; SEO builder giữ tắt tới khi sửa; T2 linear
  sửa lỗi đếm ngày rồi thử lại ≤0,5 USD; W2 đợt 1 ≈2,9 USD, phân xử T9 held-out trước; trần đợt 1 = **5 USD** ("A").
- Role admin: đổi sang `nghiep-admin-12h` (Terraform), xoá role tay cũ (anh chạy lệnh).
- GitHub: repo giữ public, siết bảo mật cấp org miễn phí (ADR 0021); allow-list Actions + 2 action lồng; budget 0 USD.
- "thêm T2" (23:05): cho thêm T2 held-out để có nguồn blog (dừng ở 14 theo đề xuất sau khi thấy gốc là thiếu demand).
- Bấm chọn 23:2x: research nhu cầu tenant audit (~1,7 USD), tạo issue toàn hệ thống (**AA-1055**), thử SEO builder
  ~0,3 USD, T2 linear bật theo job cho tenant audit.
- Bấm chọn 01:xx: **duyệt thiết kế DFS mới (hướng A) nhưng chưa code đêm nay**; thử Standard queue ~0,1 USD; R0 + R1
  (US/UK/AU) sau khi PR 1 + PR 2 live, R2 sau khi xem số R1; thử DE/FR/NL 0,27 USD; giữ ngưỡng Blog 1.000 tới sau R2.

## Thay đổi Codebase (đã merge, live trên Dev)
- **CIS:** #1381, #1382 (nhập nhãn claim + split plan), #1383 (trial flags W3), #1384/#1385 (integration + replay),
  #1386, **#1387 AA-1053** (một chỗ retry token budget + một luật effort), #1388 (cache spaCy), **#1390 AA-1052**
  (lineage + change control + dọn code chết), #1391 (cache hygiene), #1392 (ghim SHA), **#1394** (một bộ đọc số ngày
  T2), #1395 (đợt phân xử), #1396 (SEO builder meta ngắn), **#1398 mig 391 + #1399 AA-1050 shadow** (công tắc tắt
  mặc định, mọi class chỉ warn). Live `70f4d80e`, schema 391.
- **Partner:** #248 crm-047 + #249 (lead TripPlanner chỉ cho đại lý bật add-on), #250 docs X-AI DOCX, CI #251/#252/#254.
- **TripPlanner:** #236/#240/#241/#243 (web trên ECS sau CloudFront, gỡ Vercel), **#244 tp-027** (thu hồi quyền booking
  đọc outbox inquiry), CI #245–#247.
- **Booking:** #209 kit, CI #211–#213.
- **Infra:** #721/#722/#725–#728 (TripPlanner ECS + WAF + DNS), #730/#733/#742 (copy migration), #731/#732 (guard
  contract copy + isolation probe), **#734 AA-1004** (role OrganizationAccountAccess + OU Transitional), #736/#738
  (role admin 12 h), #739 (hook rò GIT_DIR), #740 (WL6), CI #735/#737.
- **Root:** #628 DPA Annex 2 v0.4, #629/#633 (retire inquiry), #634 secrets register, **#637/#638 ADR 0021**, #639/#640
  (guard CI hygiene, ghim SHA), **#642** (CI hygiene lớp 3 + 4, WL7 artifact retention), #643/#645 (retention), #636.

## Kết quả chính
- **AA-1053 Done**: lô T9 của W2: 23 request, 0 cắt, 0 retry; route-test t9_write 2 rung đúng effort.
- **AA-1052**: lineage live (7/7 bản T2 mới đủ 4 trường) — chuyển lại In Progress vì còn fan-out + chặn sửa runtime;
  lane l21 xong → CIS #1400 (mig 392) + #1401 đã mở, mỗi PR còn 1 check đỏ.
- **AA-1050**: shadow live (công tắc `CLAIM_SHADOW` tắt mặc định), chờ nhãn W2 để đo.
- **AA-1048 W2 đợt 1**: T2 14/14, T9 blog 14/14 trên tenant audit, **2,58/5 USD**. Chưa đóng băng / panel vòng 2.
- **AA-1049**: T2 linear thử lại ĐẠT (10/10, contract khớp, 0,064 USD); SEO builder thử 2 bài (0,126 USD): sửa được meta
  ngắn, bài 2 bị giữ vì F13_leak + FAQ_COUNT (không do builder).
- **AA-1004**: Infra #734 merge; apply management 3 mục (OU Transitional, SCP 1, `aa-org-member-access`), plan lại sạch;
  phía acc2 chờ check 1.4 / trả lời bên bán lại.
- **CI/CD (ADR 0021)**: cache + sha256 + tải có xác thực (spaCy, lychee, Syft); dọn ~13,8 GB cache; ghim SHA mọi repo;
  workflow CI hygiene hằng ngày (lớp 3) + kiểm pin hằng tuần (lớp 4); WL7.
- **Bảo mật**: tp-027 apply, DB Isolation Probe xanh; nightly CIS xanh (issue #1379 tự đóng).
- **DataForSEO**: kiểm toán (`dfs-cost-audit/report.vi.md`): 71,49 USD từ 19/09, 49 USD riêng 25/09 (kích hoạt sai chỗ ×
  task chở 4,5 từ khoá × 3 nước × không trần). Tenant viết blog hôm nay KHÔNG chạy DFS. Research tenant audit 0,55 USD
  + recompute: chủ đề đủ chuẩn Blog **4 → 31**. Thiết kế mới (`design.vi.md`): một người mua, 1 SERP/địa điểm; 6 thị
  trường lần đầu ≈23 USD (DFS ≈21,5) so với ≈90 USD cách cũ; hằng tháng ≈2,9 USD.
- **Bức tranh hệ thống** (`system-picture/`, trang https://claude.ai/artifact/4FA5xGDt1WvG9Hmjxud6sk): 917 tour sống → 892
  Master → 883 ranking → 699 route; 28 tour có T2; 405 bài T9, 254 duyệt, 6 từng đăng, 1 đang đăng; recompute 116/118
  ổn nhưng research không gọi nó và cặp bật/tắt 05/11 chờ ~74 giờ; GAP 1/GAP 2 lan truyền.
- **C4.3 W46**: không lỡ mục tiêu; `pg_stat_statements` dealloc 2.056 → 9.122 (max 10.000).

## Chi phí trả phí trong phiên
W2 2,58 USD; research 0,547 USD (DFS 0,508); T2 linear 0,064; SEO builder 0,126; route-test 0,0003; S1/W3 thử đầu phiên
≈0,42 (0,213 S1 + 0,207 W3). Tổng ≈3,7 USD.

## Việc cần làm đầu phiên sau (S274)
1. Chuỗi 392: xem check đỏ CIS #1400/#1401 → apply cis/392 (`--allow-out-of-order` khi 336 còn chờ) → ship #1401 →
   kiểm fan-out trên 1 tour → AA-1052.
2. W2: đóng băng held-out (addendum 1.3.0) → export → panel vòng 2 (CL-1 rồi t2@2) → import → xếp đợt phân xử T9.
3. Thử Standard queue DFS (~0,1 USD, đã duyệt); rồi AA-1055 PR 1 (T2 + Slate phía đọc) theo `design.vi.md`.
4. Root #644 (bot schema-ref, check cancel) + dependabot PR các repo (review, không tự merge).
5. Tech lead: gắn label/env `ci-hygiene` + key App + Actions: Read (root #642 live steps); tick "Require SHA pin" ở org.
6. ≥10/11 12:00Z: apply cis/336 (AA-1024).

## Lưu ý kỹ thuật
- Chừng nào cis/336 còn hẹn giờ, mọi migration CIS mới apply bằng `dbmig.sh … --allow-out-of-order`.
- Research DFS không tự recompute: sau mỗi lượt phải enqueue `recompute` scope platform (giới hạn `segment_ids`).
- Bài học đã chuyển vào `skill/aa-lessons/lessons.md` (Vận hành + Dữ liệu).
