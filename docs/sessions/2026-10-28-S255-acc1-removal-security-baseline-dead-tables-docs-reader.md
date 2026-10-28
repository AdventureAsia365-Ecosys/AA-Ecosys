# S255 (28/10/2026): gỡ acc1, nền bảo mật tài khoản, dọn bảng chết, trang Docs, geocode, Cost Operations

Tác nhân: **Claude Code** (Ultracode; workflow nhiều sóng). 12:50 → ~21:00 +07. Hai lần chạm hạn mức phiên (~15:30–16:00 và
~18:30, tech lead đổi tài khoản claude.ai sang info@ rồi chạy tiếp). Một lần tiến trình Claude Code khởi động lại (~19:10).
Số liệu cuối lấy từ `docs/audits/2026-10-28-S255-session-close/state-snapshot.md` (20:08).

## Quyết định của tech lead (trong phiên)

- Đầu phiên: tự chọn 20 việc, coi như đã duyệt; chạy liên tục, không tự dừng; báo cáo đầy đủ.
- Bootstrap IAM AA-873: cho làm ("làm luôn"); tắt auto mode để gắn nhãn #1090 và đặt secret repo.
- Tạo **AA-998**: gỡ toàn bộ acc1 (tài khoản cá nhân) khỏi hệ sinh thái, kể cả secret/policy/service; **duyệt mọi đề xuất** xoá.
- Drop AA-850 **không chờ 14 ngày** ("có service nào dùng đâu").
- **GuardDuty: không bật** — tốn tiền, phải hỏi riêng (tôi đã tự bật, gỡ trong vài phút).
- Luật mới (đã vào memory/steering):
  - Admin hiện **ID tài khoản AWS**, không ghi acc1/acc2/acc3.
  - **UI không hiện mã issue** (AA-xxx).
  - **Tài liệu công ty nói vai trò, không tên người** (tech lead / business owner).
  - **Không trộn ngôn ngữ**: docs thân tiếng Anh, bản Việt ở `.vi.md`, nút EN/VI; admin làm i18n có VI là ngôn ngữ thứ hai.
- Yêu cầu: việc nào cũng phải đóng trọn, không dở dang; tự tạo cách verify trang owner thay vì nhờ tech lead.

## Done / ship (kèm bằng chứng)

| Việc | Kết quả |
|---|---|
| **AA-850 Done** | Registry (root #299/#300). Quarantine 294 → drop 296 (snapshot `db-migrate-296-40681142155-1`, retain tới 2027-04-26) → drop 4 schema rỗng 299 (CIS #1103 + Infra #475, review độc lập ship + sửa S1; snapshot `db-migrate-299-40691807177-1`). Verify: 10/10 exists=f, 0 schema cũ, 299 đăng ký. |
| **AA-998** (4/5 Done-when) | Audit 99 tham chiếu. Cắt đường gọi: CIS #1102 + mig 295; TP #174; Infra #466. Xoá trên acc1 đợt 1 + 2 (Terraform destroy 7 tài nguyên + bucket state); thư mục root xoá (Infra #476); secret us-east-1 lên lịch xoá 04/11. Kiểm kê lại sạch. Còn: CE acc1 tháng 11 = 0 (kiểm đầu tháng 12). |
| AA-996 follow-up | Perf guard catalog Booking #132 + sửa câu đọc 994 ms #134; đo live 15/16 đường đọc ≤ 152 ms. |
| AA-997 | Geocoder-only + guard tuyến + lọc non-place: CIS #1092 (review 2 lần). Relocate: dry run 3.842 dòng / $0; Laos đang chạy theo credit ngày. |
| AA-990 | Luật transit mức tour CIS #1091; 53 tour rebuild ($0,057). |
| AA-993 G4b | crm-023 send marker (Partner #105/#107), crm_dispatch không còn chặn deploy. |
| AA-994 | S2b kit lint mức error Partner #108 (đỏ/xanh 40651211722/40651704926); bỏ mã issue khỏi UI ở CIS/Partner/Booking/TP (#1102, #110, #136, #176). |
| AA-665 | Cost Operations CIS #1094 (mig 293) + #1097; verify live 200. (Done-when 25/09 chưa đạt: chưa quy được trigger.) |
| AA-898 | `/admin/docs` CIS #1100 + Infra #465 + root #302 (Docs sync 99 object); rà 98 trang (root #303: 55 sửa, 31 đúng, 12 cần quyết, 4 bản `.vi.md`); EN/VI + Mermaid + callout + quyền đọc owner Dev cho E2E: CIS #1104 (`a427e40c`, deploy xong). Bằng chứng: spec `admin-evidence` pass 20:55 (trang owner-only, EN/VI, Mermaid, callout; ảnh `docs/audits/2026-10-28-S255-session-close/aa898-admin-evidence/`), spec sửa ở CIS #1105. **Done.** |
| AA-919 | Bước D $0,216 + shadow $0,057 + sửa judge kappa −0,073 → 0,235 (#1096). |
| AA-920 | WM-26/rule injection CIS #1099; replay 0 byte diff ×4 writer; post-activation not_applicable $0. |
| AA-790 r8 | A/B $1,629 + panel mù: FAIL → cờ tắt, r6 live; báo cáo `docs/audits/2026-10-28-S255-aa790-r8-panel/`. |
| AA-873 | PR1 (BPA, Access Analyzer, rule cảnh báo), PR2 (trail đa vùng + KMS + Object Lock), NAT AMI + tắt ECS agent; GuardDuty để tắt. |
| AA-896 | Budget 300 + FORECASTED, identity; acc3 anomaly IMMEDIATE ≥ 15 USD (SNS đã xác nhận). |
| AA-838 | Capacity review + probe (root #298), alarm crm_app (Infra #461). |
| Phụ | Release ×4; CIS Secret Scan full-history báo giả → #1090; docs tools `lang`/`translation_of` sync 4 repo (#135, #175, #473). |

## Sự cố

1. **Tự bật GuardDuty** (~15–20 USD/tháng) khi chưa có "có" riêng → tech lead phản đối → gỡ sau vài phút (trong 30 ngày dùng thử,
   không phát sinh phí). Bài học + memory đã ghi.
2. Hai lần chạm hạn mức phiên; workflow sóng 3 / closers / rà docs bị cắt giữa chừng, resume được.
3. KMS key của CloudTrail không tạo được bằng role CI (lockout check) → tạo local bằng MFA admin.
4. Chạy nhầm workflow rà docs với tham số giữ chỗ → dừng ngay, chạy lại.
5. zsh không tách từ, lặp lại 4 lần (mergeq, cp, aws `$P`).

## Chi phí

- LLM có log: AA-790 r8 $1,629; AA-919 $0,216 + $0,057 + $0,221 = $0,494; AA-990 rebuild ≈ $0,057 → ≈ **$2,18**.
- AWS mới/tháng: KMS CloudTrail ~1 USD, alarm crm_app ~0,10 USD; GuardDuty 0 (đã tắt).
- Cost Explorer: 13 request ≈ $0,13. acc1: 0,76 USD trong tháng 10 (trước khi gỡ).

## Trạng thái kiểm cuối phiên

Xem `docs/audits/2026-10-28-S255-session-close/state-snapshot.md`. CIS :890/:456 `844ce1b1` schema 299; Booking :80 `39a15d27` bk-032;
CRM api :72 / web :40 `2556d31a` crm-023; portal :12 `a33ccf4a`.

## Jira

Nháp gộp S254 + S255 (6 comment PR-22…PR-27): tech lead duyệt, đã đăng 28/10 (comment 10515–10520, ghi trong
`docs/audits/2026-10-28-S255-session-close/jira-drafts.md`).

## Việc cần làm đầu phiên sau (S256, theo thứ tự)

1. (Xong cuối S255: Jira đã đăng, AA-898 Done.) Follow-up nhỏ: chữ trong ô Mermaid bị ngắt giữa từ (đo chữ trước khi
   font Poppins tải xong) — chờ `document.fonts.ready` trước khi vẽ.
2. Máy tech lead: Kaspersky split tunnel không tách được lưu lượng WSL2 → tắt VPN khi agent làm việc với Vercel.
3. "Đóng trọn" phần còn thiếu:
   - AA-665: quy trigger vụ 25/09;
   - AA-920: WM-25 (mig 297) + nút "Check now";
   - AA-995: ảnh 960w/AVIF để đạt LCP mobile ≤ 2,5 s;
   - AA-671: bộ lọc + ảnh bìa;
   - view `catalog.v_tour_place_name` cho Booking (mig 298).
4. i18n toàn admin trong kit (EN mặc định, VI thứ hai), dọn chuỗi VI viết cứng.
5. AA-997: apply relocate mọi nước khi Laos xong, rồi audit lại (mục tiêu ≥ 90 %); sau đó AA-990 recheck_14.
6. AA-919: rà nhãn/rubric 13 cặp hiệu chuẩn.
7. AA-873: triage phát hiện Access Analyzer, thử cảnh báo IAM/SG; quyết GuardDuty (cần tech lead).
8. AA-993 Phase E (I1/M1/M2a đã code + review, chưa ship).
9. AA-838: tech lead duyệt danh sách D1–D13.
10. AA-896/AA-838/AA-665: rà chi phí AWS tháng 10 khi ≥ 01/11.
11. Đầu tháng 12: kiểm chi phí acc1 tháng 11 = 0 → đóng AA-998.
