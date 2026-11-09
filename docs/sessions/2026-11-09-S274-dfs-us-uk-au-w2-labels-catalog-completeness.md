# S274 — DFS mới (US/UK/AU), nhãn W2 vòng 2, đo và lấp đủ dữ liệu catalogue, ticket Bedrock, vệ sinh CI

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). 09/11 ~10:00 → 10/11 ~07:00 +07.
- Trần tuần Claude chạm khoảng 14:00 (reset 17:00), trần 5 giờ chạm khoảng 23:30 (reset 03:00).
- Máy OOM một lần (exit 137, phải khởi động lại), do bỏ qua ram_gate khi chạy lane có test.
- MFA hết hạn một lần; tech lead làm mới sau khi hết hạn.
- Vài cửa sổ tắt auto mode: apply TF root alert, môi trường GitHub, WordPress.

Snapshot: `docs/audits/2026-11-09-S274-session/state-snapshot.md`.

## Danh sách đầu phiên (duyệt "Đồng ý list đề xuất", Ultracode)
AA-1052 W6 · AA-1048 W2 · AA-1050 W4 · AA-1055 DFS · AA-820 · AA-1049 W3 · root #644 + dependabot · hội tụ In Review · guard bài học.

## Quyết định của tech lead
- **Ticket AWS Bedrock:** theo tư vấn của Hoài (TrueIDC), tạo 2 case riêng: acc3 và acc2, cả hai xin đủ 7 model. Ticket acc3 chỉ nói về acc3. Lưu acc4 (aa-management) vào bản đồ tài khoản (ID nằm trong memory riêng, không đưa vào repo).
- **Bức tranh hệ thống (11 việc):** "Tạo cả 4 và làm trong phiên" → AA-1056 recompute, AA-1057 vòng đời Segment, AA-1058 gắn chi phí, AA-1059 phần sót catalogue.
- **WordPress test:** chạy container phụ trong task ECS Booking admin sẵn có (0 USD) → AA-1060, "tạo và làm luôn".
- **Lấp dữ liệu CIS:** "đồng ý làm luôn". Làm US/UK/AU trước; nhóm thị trường dùng chung (DE/FR/NL) sau; thị trường mới hoàn toàn làm sau cùng. Cuối phiên archive Linear đúng quy trình.
- **DFS:** chạy từng nước, mỗi nước một trần; giảm tiền nhưng phải kiểm chất lượng.
- **MFA:** chỉ làm mới khi đã hết hạn, không ghi đè giữa phiên; "cứ làm bình thường".

## Thay đổi codebase (đã merge)
- **CIS:**
  - #1397, #1212: dependabot.
  - **#1400 (mig 392) + #1401 AA-1052 W6:** dấu thay đổi nguồn, cổng sửa runtime.
  - #1402: test đồng hồ giả.
  - **#1403 AA-1055 PR 1:** phía đọc; Slate dùng MAX demand và ghi lý do trượt.
  - **#1404 AA-1056:** lưới quét recompute, cảnh báo trễ, khoá, dừng.
  - **#1405 AA-1057:** liveness Segment Subject, retarget.
  - **#1406 (mig 393) + #1407 AA-1055 PR 2:** phía mua; Standard queue, bản đồ từ khoá, trần USD, recompute sau research.
  - **#1408 AA-1058:** gắn chi phí trên ledger.
  - **#1409 AA-1059:** catch-up Segment, chẩn đoán phần sót.
  - #1410: giá theo queue, stage cho mọi dòng DFS, báo cáo chất lượng.
  - #1411: research đi qua stage gateway, bỏ tier haiku cũ.
  - #1412: lọc từ khoá trùng tên địa danh, không phải địa điểm, bị lỗi chữ.
  - Chờ deploy lúc viết:
    - #1413: đảo nhỏ ngoài polygon 1:10m.
    - #1414: retarget mặc định apply.
    - #1415: AA-1055 PR 3, guard tỉ lệ địa điểm cũ theo thị trường và phạm vi re-atomize.
- **Infra:**
  - #743: dependabot.
  - #744, #747: copy migration 392, 393.
  - **#745:** root alert giữ đăng nhập / ghi / đọc ngoài console, bỏ đọc ngầm của console; thêm forwarder us-east-2 và us-west-2.
  - **#746:** role apply của CI đọc được inline policy (CI apply hỏng từ S273).
  - **#748, #750 AA-1060:** WordPress test làm container phụ của Booking admin, host test-wp.
- **Booking:** #214 dependabot; **#215:** deploy admin giữ container phụ.
- **TripPlanner** #248, **Partner** #255 / #240: dependabot.
- **Root:**
  - #641: dependabot.
  - **#647 AA-820:** DPA v0.4 và điều khoản Tenant Terms về chính sách AI.
  - **#648:** guard bài học (PIPE-1, đọc merge queue, allow-list action lồng).
  - #644: schema-ref tự sinh.
  - #650: retention place_keyword.
  - #651: secrets register cho container WordPress.
  - **#654:** pin freshness đọc release upstream có IP allow list mà không cần token.

## Việc dữ liệu / vận hành trên Dev (có trả tiền đều theo trần)
- **AA-1055 R1 (Standard queue), so với S273:**
  - US: DFS 1,62 + LLM 0,22 USD.
  - UK: DFS 0,48 USD.
  - AU: DFS 0,48 USD.
  - Tổng DFS 24 giờ 7,16 USD; số này gồm lần R1 đầu lỗi định tuyến LLM (dữ liệu mua lần đó được giữ).
  - Chất lượng: Jev giữ 91–92% từ khoá; panel kiểm 93% đúng; PAA ≥3 đạt 63,6% (bản live 65%).
- **Kết quả:**
  - Dòng ranking có demand: US 22% → 88%, UK 16% → 88%, AU 15% → 88%.
  - Segment qua thanh Blog: US 391 → 1.593, UK 221 → 1.257, AU 190 → 1.060.
  - Slate 9 tenant: 75 → 141.
- **Place cards:** 57 tour, khoảng 0,44 USD. Atom chờ viết card 215 → 0.
- **Bản sao seo_context tháng 10:** 3.092 volume + 442 SERP (0 USD).
- **AA-1057 one-off:** chuyển 6 Route Subject (DRY RUN rồi apply theo id đã ghim).
- **AA-1048 W2 vòng 2:**
  - Panel 321/321 file; import CL-1 1.1.0 (2.604 nhãn) và t2@2 1.0.0 (2.166 nhãn); 0 mâu thuẫn; blog held-out 812 ≥ 784.
  - Đợt phân xử 1 sẵn sàng, chờ 84 mục mở của CL-1 1.0.0.
- **AA-1050 W4:**
  - Replay 24 object, 0,12 USD. Công cụ đánh unsupported cả 24/24; baseline (F9 / kiểm T2) chỉ trùng 1.
  - Bước tiếp: gắn nhãn khoảng 30 ca bất đồng. Công tắc vẫn tắt.
- **AA-1060:** WordPress test sống trên host test-wp. Diễn tập retire → draft → restore PASS, nhưng lộ lỗ hổng: restore không tự đăng lại trang đã chuyển nháp. Lane đang sửa theo review: 1 lỗi chặn + 4 lỗi lớn.
- **Đo completeness 5 lớp** trước / sau: báo cáo `docs/audits/2026-11-09-S274-session/completeness/report.vi.md`.

## Bài học (đã chuyển vào skill/aa-lessons)
Xem `.tmp-session/S274-lessons-pending.md`:
- lane đọc nhầm tin nhắn giữa lượt;
- OOM khi bỏ ram_gate;
- ecsx bị từ chối khi ARGS có dấu cách;
- định nghĩa metric geo sai;
- đảo nhỏ ngoài polygon;
- IP allow list của upstream;
- ecsx bỏ chờ ở 900 giây trong khi script vẫn chạy;
- ước chi worst case cao gấp 7 lần thực tế.

## Đóng phiên (10/11 sáng)
- **Đã deploy và kiểm trên live:**
  - CIS #1413 + #1414 lên `dc4c13e9`, #1415 lên `116179b3`.
  - Deploy của #1415 bị guard chặn một lần do có job geocode xếp hàng; đã chạy lại.
- **AA-1059 Done:**
  - Đưa lại 44 tên → 6 tên được định vị, 7 thành phần tour và 3 card được nối lại toạ độ.
  - 38 tên còn lại là "unknown" thật.
- **AA-1057 Done:** mode apply có hiệu lực. Plan còn 1 Subject `taken` và 3 yêu cầu `no_match`, cả hai đúng thiết kế.
- **AA-1055:**
  - Guard trên data coverage: US / UK / AU 0% địa điểm cũ, DE / FR / NL 99% (trước R2).
  - R2: DE 0,96 USD, FR 0,96 USD, NL — xem snapshot.
  - Còn phải kiểm `reatomized` bằng 1 lần re-atomize thật rồi mới đóng.
- **AA-1056:**
  - Retire → restore tour KR `4f273a8e` (0 phái sinh) lúc 22:59:56 / 22:59:58Z.
  - Hai sự kiện được gộp vào recompute `bbbc63ce` (bắt đầu 23:02:45Z) — kiểm thời điểm xong ở phiên sau.
- **Infra #741** đã merge: plan dev / management chạy lại bằng App.
  - Plan acc3 có 8 thay đổi tag. Lệnh apply bị auto mode chặn → anh chạy.
- **Root:** #654 sửa pins (CI hygiene xanh), #649 tài liệu infra sinh lại.
- **AA-1039 restore-republish:**
  - Review 1: 1 lỗi chặn + 4 lỗi lớn → đã sửa.
  - Review 2: 1 lỗi lớn (claim bị ngắt) + 4 lỗi nhỏ → lane đang sửa.
  - Chưa push. Nhánh nằm trong clone của lane: `.claude/worktrees/agent-aab2ee2027ec9ec08/apps/AA-CIS-App`, branch `fix/aa-1039-restore-republish`.

## Còn dở / phiên sau
- **AA-1039 restore-republish:** review lần 3 vẫn BLOCK (2 lỗi lớn + 6 lỗi nhỏ, mỗi vòng sửa lại mở lỗ mới). Nhánh đã push, không PR. Đề xuất A: tenant bấm "Put back online" một lần, không tự đăng. Chờ anh chọn A/B (`aa1060/restore-republish-followup.md`).
- **AA-1056:** đọc `first_finished_after` của 2 sự kiện 22:59Z, kiểm 2 recompute không chạy chồng, rồi đóng.
- **AA-1055:** sau R2, kiểm guard DE / FR / NL; chạy preview `reatomized` sau 1 lần re-atomize; đóng.
- **AA-1058:** 1 lượt S1 + 1 bài T9 có `prompt_version` / `content_piece_id`.
- **AA-1048:** chờ tech lead xử lý 84 mục → enqueue CL-1 1.1.0 đợt 1.
- **AA-1050:** gắn nhãn khoảng 30 ca bất đồng.
- **Cần anh:** apply tag acc3 (tắt auto mode).
- **Chờ người:**
  - 25 tour chờ duyệt S1;
  - ảnh bìa 730 tour;
  - giá tham chiếu 281 tour;
  - Booking 2/892 bán được (nháp Jira đề xuất).
