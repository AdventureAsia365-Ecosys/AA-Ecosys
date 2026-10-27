# S253 (27/10/2026): lan truyền S1 v2, thẻ địa điểm đạt ngưỡng, Booking vận hành S2+S3, trang chủ TripPlanner, worker dừng mượt, UI kit S1a+S1b

Tác nhân: **Claude Code** (Ultracode; workflow implement → 2 review → fix; tối đa 2 lane nặng). Phiên dài, có một lần dừng chờ
reset hạn mức (~17:35–19:12 giờ VN). Số liệu cuối phiên lấy từ `docs/audits/2026-10-27-S253-session-close/state-snapshot.md`.

## Trạng thái

- Đầu phiên: Nghiệp giao tự chọn 20 việc từ master plan và tồn S252, coi như đã duyệt, chạy liên tục.
- Cuối phiên: Nghiệp duyệt dừng sau khi xong #1–#3 của danh sách tối; #4 (các màn Figma Booking) chưa mở.

## Quyết định của Nghiệp (trong phiên)

- Đầu phiên: chọn 20 việc, chạy liên tục, không tự dừng phiên, báo cáo đầy đủ trước khi dừng.
- "Làm luôn": các bước cần làm tay thì agent tự làm, ví dụ ghi canary trên DB dùng chung.
- Hạn mức gần hết thì canh giờ reset rồi làm tiếp, không chốt phiên. Nghiệp sẽ tự nhắc khi hạn mức sắp hết.
- **Duyệt H6 (AA-994 S1b):** 4 màu theme sáng đổi; chữ trên nút vàng từ trắng sang nâu đậm.
- **Booking phải phủ đủ mọi màn Figma.** Các màn từng "cố ý không dựng" nay phải dựng. Nội dung thuộc CIS thì hiện chỉ xem kèm "Edit in CIS ↗", hoặc gọi API CIS. Hộp thoại xoá cứng chuyển thành vô hiệu hoá. Đã ghi vào memory `booking-figma-full-coverage`.
- **Audit độ khớp Figma (120 PNG so với ảnh live): làm sau cùng**, khi mọi việc khác đã xong.
- Giai đoạn cuối: làm nốt các việc đang dở, không mở việc mới.
- **Jira:** duyệt đăng 6 comment kèm ảnh. Báo cáo tuần kỳ 3 không đăng, vì báo cáo kỳ chỉ làm mỗi tuần một lần (đã ghi memory `platform-report-weekly`).

## Done (kèm bằng chứng)

| Issue | Kết quả | Bằng chứng |
|---|---|---|
| AA-991 | Xoá 10.495 member chết, có snapshot RDS trước khi xoá. Probe độ mới chuyển `ENFORCE=True` (Infra #426, #427). | Probe enforce run 40456962884 xanh. Linear Done. |
| AA-988 | Sửa id segment trùng (CIS #1060); 227 → 0 atom thiếu segment; gỡ 104 member dán nhầm và xếp lại 104/104. | Probe run 40466598280 xanh; chi phí ≈ $0,009. |
| AA-989 | `tour_place` còn 0 dòng trỏ atom chết; dựng 892/892 nguồn. `content_embedding` vào Dead Table Registry. | Linear Done. |
| AA-784 | Thẻ địa điểm vòng 3 (CIS #1065): FK **1/51 = 2,0%**, đạt ≤ 3%; LK, WI và sai nước đều 0; locality/region sai 3/14. | `docs/audits/2026-10-27-S253-aa784-spotcheck-r3/`; Linear Done. |
| AA-951 | crm-022 live; Partner #96 `ae8104f5`; cache AA và mẫu tin nhắn hoạt động. | Linear Done; ảnh trong `aa951-live`. |

## Ship, chưa đóng issue (In Progress, còn slice)

- **AA-682 Booking vận hành.**
  - S2 (check trước chuyến và vòng đời hồ sơ): bk-027 (#106, Infra #434). Code #107 có trigger seed 3 check, board, và job `bk_case_lifecycle` đã go-live: Infra #435 → #438, lần chạy live `af5c3b5d` chuyển 1 hồ sơ, 0 bị chặn.
  - S3 (hoá đơn, lịch thanh toán, thanh toán ghi tay):
    - bk-028 qua #111 và #113. Review độc lập tìm ra blocker: verify được khi bằng chứng đã bị gỡ. Lint X1 của Infra cấm trigger deferred, nên phần kiểm tổng chuyển sang cửa sổ `amending`. Apply qua Infra #442.
    - Code #114 `ac540fc9`.
    - Run-script #443 (dry), #444 (apply), #445 (về dry): `verdict ok` ở mọi bước Done-when.
    - Ảnh `/billing`: `docs/audits/2026-10-27-S253-aa682-s3/`.
  - Còn S4 (hoá đơn nhà cung cấp) và S5 ("Thanh toán của tôi").
- **AA-993 delivery pipeline.**
  - V3: Partner #97.
  - **G1:** CIS #1072 cùng Infra #440 (`JOB_WORKER_GRACE_SECONDS=100`, `JOB_TEST_KINDS` chỉ bật trên Dev). Chứng minh live qua 3 lần deploy:
    - job 300 s được làm xong trong cửa sổ;
    - job 1.800 s `3e31d444` được nhả lúc 14:18:14 (`counted: false`) rồi nhận lại, kết thúc `succeeded` ở attempt 1;
    - `/released` báo 1.
  - **G4 phần 1:** Booking #112, Partner #98; sau SIGTERM process thoát dưới 1 s.
  - Còn: chứng minh G4 bằng job Booking, G2/G3, G5, Phase E.
- **AA-994 UI kit.**
  - S1a #1067 (thay #1066 bị gitleaks bắt nhầm hash).
  - S1b #1071 `51d2a65a`, Nghiệp đã duyệt H6. Smoke production có đăng nhập xanh, lần đầu từ #1056, nhờ #1069 sửa selector. Ảnh: `docs/audits/2026-10-27-S253-aa994-s1b/`.
  - Còn S1c, S2.
- **AA-995 TripPlanner Golden Hour.**
  - Slice 1–4 (#163 `545514a0`).
  - Gộp ảnh trùng ở tầng nội dung: CIS mig 290 (#1068, Infra #439), 2.629 dòng → 1.120 path.
  - Ribbon lấy 40 tour (#164 `3d0840b8`): 25 ảnh, chạy ngang.
  - Còn các trang khác theo giao diện mới, và các follow-up ghi trên Linear.
- **AA-990.** N4 kiểm live: 137 tour bị gắn cờ, 0 tour còn dưới ngưỡng (`docs/audits/2026-10-27-S253-aa990-n4/`). Mig 289 về ngày dạng ranged: Sri Lanka 16/16.
- **AA-979.** Portal chạy trên Fargate; diễn tập rollback 3′28″ / 3′11″; E2E phase 2 đạt 6/6. Lỗi CSP khi đăng xuất đã sửa (Partner #94, Infra #431). Đợt dọn bắt đầu từ 03/11.
- **Khác:**
  - AA-978: lock_source và feed trên console CRM (CIS #1063).
  - AA-816: reconcile còn drift 0.
  - AA-790: test linear-time ổn định lại (#1070).
  - Booking #109: cột Due không xuống dòng.
  - Booking #108: ghim runner smoke sang `ubuntu-24.04`, vì Playwright chưa có chromium cho 26.04.

## Sự cố

1. **#1061 revert ngầm #1059 và #1060.** PR được đẩy qua Git Data API từ một nhánh có base cũ, và bản revert đã deploy lên Dev.
   - Đã khôi phục bằng #1064 và sửa lại dữ liệu.
   - `api_push.py` giờ chặn khi base không phải tổ tiên.
   - Lần dựng nhánh S3 (#114) suýt lặp lại lỗi này với Dockerfile của #112; phép so `merge-base` bắt được trước khi commit.
2. **bk-028 đã merge ở Booking rồi mới bị lint Infra (X1) chặn.** Phải đóng Infra #441 và sửa lại migration (#113). Đã ghi bài học.
3. **MFA hết hạn giữa phiên.** Lần apply 290 đầu tiên thật ra chưa chạy; vòng chờ bám vào run cũ nên báo rc 0. Nghiệp đưa mã MFA, mình chạy lại và kiểm đúng run mới.

## Trạng thái kiểm cuối phiên

Xem `state-snapshot.md`. Tóm tắt:
- ECS: cis api:867 và worker:433 (`960dafda`), booking:66 (`ac540fc9`), crm api:64, web:33, portal:9. Tất cả COMPLETED và là revision mới nhất.
- Schema: CIS 290, Booking bk-028. TripPlanner `3d0840b8`. CIS admin Vercel `51d2a65a`.
- `shared.job`: 1 queued, 0 running; 0 wave mở.

## Chi phí

- LLM có ghi log: thẻ địa điểm vòng 3 $0,045; recompute AA-988 ≈ $0,009; dựng lại 10 thẻ $0,048 và 20 thẻ ≈ $0,10. Tổng 27/10 khoảng $0,20.
- Vercel (hạ tầng): Fluid Active CPU 3h00 / 4h trong kỳ miễn phí, khoảng 69% là admin CIS. Kỳ mới bắt đầu khoảng 28/10. Đã soát: không có chỗ thừa đáng kể.

## Bài học

Đã chuyển hết vào `skill/aa-lessons/lessons.md`:
- output ECS exec; ECS exec treo;
- `pkill` tự giết chính lệnh;
- push 403 của App; nhánh dựng từ base cũ bị revert khi đẩy qua Git Data API;
- probe dùng sai điều kiện đủ tư cách;
- openapi phải sinh bằng đúng bản FastAPI của CI;
- Cognito `fillSettled`;
- runner Playwright trên Ubuntu 26.04;
- gitleaks bắt nhầm hash trong manifest;
- test chọn phần tử theo class của khung trang;
- migration `cis/` không tự `SET ROLE` khi đổi view trong `shared`;
- ảnh trùng phải so theo sha256;
- migration app phải qua lint Infra trước khi merge.

## Jira

Đã đăng 27/10 tối, đều kèm ảnh:

| Issue | Comment | Ảnh |
|---|---|---|
| PR-23 | 10509 | 5 |
| PR-26 | 10510 | 4 |
| PR-25 | 10511 | 6 |
| PR-24 | 10512 | 4 |
| PR-22 | 10513 | 2 |
| PR-27 | 10514 | 3 |

PR-20 kỳ 3: không đăng, theo nhịp báo cáo mỗi tuần. Nháp và kết quả nằm ở `docs/audits/2026-10-27-S253-session-close/jira-drafts.md`.

## Việc cần làm đầu phiên sau (S254, theo thứ tự)

1. **Booking: dựng đủ các màn Figma** theo quyết định của Nghiệp:
   - Destinations / Countries;
   - "Sign-in & security";
   - form nội dung lấy từ CIS kèm "Edit in CIS ↗";
   - hộp thoại vô hiệu hoá.
2. AA-682 S4 (bk-029, hoá đơn nhà cung cấp và chi trả), rồi S5 ("Thanh toán của tôi").
3. AA-994 S1c (eslint-kit), rồi S2a (vendor core vào Partner; sửa check "Vendored CIS copies" đang đỏ).
4. AA-993: chứng minh G4 bằng job Booking chạy qua run-script; G2/G3; G5 (đổi guard); Phase E (cần ADR).
5. Follow-up nhỏ:
   - dedupe theo `path` ở `catalog_http/mapping.py` và `browse/catalog.py`;
   - `fill_destination_covers` dùng id chuẩn;
   - 6 thẻ địa điểm xuyên biên giới;
   - Vercel: đặt region sfo1 và retention cho deployment.
6. Đợt dọn AA-979 từ 03/11. Rà chi phí AWS đầu tháng 11 (memory `infra-cost-audit-nov-2026`).
7. Cuối cùng: audit độ khớp Figma của Booking.
