# S288 — 23/11/2026 — quy tắc duyệt Booking, view-as, tách booking nhà cung cấp, guard dữ kiện T9, nghĩa vụ luật, bậc số khách, owner E2E

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). 23/11 ~06:30 → ~23:00 +07, phiên dài cả ngày. Đổi tài khoản claude.ai 3 lần
(hạn mức 5 giờ, hạn mức tuần; workflow resume bằng `resumeFromRunId`, không mất việc). Auto mode tắt 1 cửa sổ (đăng PR-20).
MFA hết hạn 1 lần (Nghiệp nhập lại).

## Trạng thái

- Hội tụ đầu phiên: AA-1161 Done (GitHub sau GC: root 113 MB, Infra 6 MB); PR-20 kỳ 6 đã đăng (comment 10687);
  release-please tuần 48 + dependabot 9/9 merged và deploy.
- 5 issue mới đã merge + deploy + kiểm live phần agent làm được, chuyển **In Review** (chờ bước của tech lead / chủ DN):
  AA-1157, AA-1158 (phần 1), AA-1149, AA-1172, AA-1174.
- 2 issue tạo trong phiên (Nghiệp yêu cầu): **AA-1175** bậc số khách chỉnh được trong Pricing › Policy (bk-066), **AA-1176**
  tài khoản owner E2E chỉ trên Dev cho agent (CIS 473). Cả hai merged + deploy + kiểm live.
- AA-1155 T12: info@adventure.asia đã được tạo với vai trò Content và gửi lời mời (bằng owner E2E). Người ops chưa có tài khoản.
- Lỗi mới tìm ra khi kiểm live bằng owner E2E: **F1** banner view-as của CIS không hiện (cookie hiển thị mã hoá hai lần) →
  sửa ở CIS #1651 trong phiên.
- Snapshot: [state-snapshot](../audits/2026-11-23-S288-session/state-snapshot.md).

## Quyết định của Nghiệp (23/11)

- Duyệt cả danh sách 9 việc, bật Ultracode.
- Tắt auto mode để đăng PR-20.
- Chạy thêm lượt bẫy AA-1172 (thứ 2), xong thì tech lead tự quyết bật guard (guard vẫn TẮT).
- AA-1174 D1: giữ các trang pháp lý ở draft (readiness tự cập nhật khi trang được thông qua).
- Làm luôn AA-1175 (bậc số khách) trong phiên; tạo AA-1176 owner E2E để agent tự làm view-as, Refresh, mời info@.
- info@adventure.asia làm Content (T12).
- Chị Thư dùng mail thu@ (ghi trong repo là t***@adventure.asia); chuẩn bị sẵn mọi thứ, chỉ còn bước xác thực sáng 24/11.
- Runbook chủ DN + hệ thống giá: bản đầy đủ trong `/admin/docs` + bản ngắn artifact cho cả team.

## Thay đổi Codebase (merged)

- **AA-1157 view-as** — CIS #1639 (mig 470), #1640 `7a6a8ef3`; Booking #301 `703a3f73`; root #945. Sửa sau kiểm live:
  CIS #1651 (cookie hiển thị không mã hoá hai lần; test ba dạng).
- **AA-1158 phần 1 quy tắc duyệt** — Booking #299 (bk-064) `cf13013d`, #300 `19f2fcf1` (gỡ xung đột custom_roles với view-as,
  tách hàm `current_staff`); root #947. Phần 2 (B2B giảm giá/phí huỷ, chặn DB cho billing_entity/supplier) → S289, ghi Linear.
- **AA-1149 booking nhà cung cấp theo thành phần + "Can operate"** — Booking #303 (bk-065), #304 `bd8ed457`; root #950.
- **AA-1172 guard dữ kiện T9** — CIS #1643 (mig 472), #1644 `4dbdfafc`; setting `cis.llm.fact_instruction_guard` mặc định TẮT,
  giới hạn còn lại ghi trong `services/ai_safety/fact_guard.py` (Known limits).
- **AA-1174 nghĩa vụ luật** — CIS #1641 (mig 471), #1642; Partner #379 `3d20ef12`; root #946. Sửa sau kiểm live: CIS #1646
  (trang Compliance crash do thiếu ToastProvider; thêm vào admin evidence spec).
- **AA-1175 bậc số khách** — Booking #306 (bk-066), #307 `79a8b389`, #308; root #954, #955. Tham số `price_pax_bands` v2
  (1, 2, 3, 4, 5–7, 8–10, 11+) hiệu lực từ 23/11, đổi cần người thứ hai.
- **AA-1176 owner E2E Dev** — CIS #1648 (mig 473), #1649 `8019c841`; Partner #381 `6dce1f2c`; Infra #978 (identity),
  #981/#982 (run-script ghi một lần rồi trả về READ_ONLY). ADR 0006a A10h.
- **CI đỏ cả chiều** — CIS #1650 `495a715b`: ghim `sentry-sdk[fastapi]==2.75.0`, `redis[asyncio]==8.1.0`; test view-as bỏ NOW cố định.
- **Docs** — root #953 runbook chủ DN + hệ thống giá (`docs/guides/business-owner-onboarding-and-pricing.md` + `.vi.md`).

## Thay đổi Hạ tầng / dữ liệu Dev

- Migration áp Dev: CIS 470, 471, 472, 473; Booking bk-064, bk-065, bk-066.
- Nạp register tuân thủ v2 (DRY RUN → apply): 61 control, 465 mapping, 14 luật, 60 nghĩa vụ, 29 dòng ma trận.
- Cognito WORKFORCE: user owner E2E (`cis-admin` + `booking-admin`), dòng staff `is_owner` qua Infra run-script.
- Ghi bởi owner E2E (23/11 tối): preset Business owner cho dòng staff t***@adventure.asia (không gửi mời; marker chủ DN bị
  từ chối đúng thiết kế A10h); tenant "Test Agency - Business Owner" (starter, crm.core, ngân sách AI 2 USD/tháng; **agency CRM
  chưa tạo** vì owner E2E không có crm-platform-admin); staff info@ vai trò Content + lời mời; 1 lần Refresh evidence; 2 phiên
  view-as (bắt đầu + kết thúc).

## Bằng chứng verify

- Thư mục: `docs/audits/2026-11-23-S288-session/live/` (aa-1157, aa-1158, aa-1149, aa-1174, aa-1172, e2e-owner).
- AA-1172 lượt bẫy: lượt 1 0,8601 USD, lượt 2 0,5414 USD, tổng **1,4015 USD** (stage `adhoc_aa1172`). Guard bật 13/14 qua,
  6/6 bẫy dữ kiện; guard tắt 2 bẫy dữ kiện lọt → guard có tác dụng đo được.
- Owner E2E (evidence.md): Booking view-as đủ (banner, 403 `view_as_read_only`, Back); CIS view-as đúng phía server nhưng không
  banner (F1); Refresh: 17 kết quả, `cis_db` + `crm_ops` có lần kiểm 22:01.
- Ảnh chứa username đã che; 10 file cũ trong repo gốc có địa chỉ đầy đủ của chủ DN đã che thành t***.

## Jira

- PR-20 kỳ 6: đã đăng (10687).
- PR-25 (Booking), PR-27 (nền tảng), PR-31 (trả lời "Price system"): nháp ở `docs/audits/2026-11-23-S288-session/jira-drafts.md`,
  chờ Nghiệp duyệt.

## Việc đầu phiên sau (S289, sáng 24/11 cùng tech lead + chị Thư)

1. Dòng staff của chị Thư: Resend invite (A3) → đăng nhập lần đầu (A4) → **Make business owner** (A5, tech lead) → Booking (A6)
   → TOTP (A7).
2. Test agency: Tenants › CRM agencies › Create agency cho "Test Agency - Business Owner" (tech lead), rồi Invite first owner (B3).
3. Kiểm chủ DN tự duyệt (AA-1158) và kịch bản bán tour giả lập (AA-1149) bằng phiên chủ DN.
4. Tech lead quyết bật guard AA-1172.
5. AA-1158 phần 2.

## Còn lại

- AA-1157/1158/1149/1172/1174/1175/1176: In Review, chờ bước của người.
- Ghim nốt 14 dòng `>=` trong `requirements.txt` CIS (ứng viên lint).
- Booking #200 (bk-045 cũ, chờ ≥ 28/11), Infra #935 (WAF geo, sau MFA admin).

## Lưu ý kỹ thuật cho phiên sau

- Owner E2E: mail mã nằm ở S3 `inbound-admin/` (chỉ role admin MFA đọc); không bao giờ đặt marker chủ DN; gỡ theo A10h.
- Hai bản lane trình duyệt chạy cùng danh tính ghi chồng nhau: kiểm agent đang chạy trước khi relaunch.
- Next `res.cookies.set` tự encode; không `encodeURIComponent` trước (bài học Frontend).
- Sửa body PR bằng token App không chạy lại check PR title → push commit rỗng.
