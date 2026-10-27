# AA-979 P2b phase 2: cutover of `portal.` to Fargate (S253, 27/10/2026)

Agent: Claude Code. Runbook: `docs/audits/2026-10-26-S252-aa979-p2b/RUNBOOK.md` §2–§4.

## Kết quả

`portal.lumiguides.it.com` giờ trỏ vào CloudFront `crm_agency`: Fargate chạy Content studio, CRM web và CRM api trên cùng một host.
Bản Vercel `aa-cis-portal` trả 301 sang `portal.…`. Đại lý đăng nhập một lần (partner pool + MFA) là vào cả CRM lẫn studio.

| Bước | Bằng chứng |
|---|---|
| §2.2 curl qua distribution (trước cutover) | `/tenant-login` 200 + HSTS/X-Frame-Options/CSP, `via … cloudfront`; `/portal/dashboard` 307 `/auth/refresh`; `/crm/health` 200; `/healthz` web; tên distribution trần 403 |
| §2.2 `crm_edge_live_check.py --agency-cf-domain` | 8/8 PASS |
| §2.3 UI Smoke (portal) `target=fargate`, ghim host | run 40459724302: 59 passed |
| §2.4 đăng nhập partner + MFA qua distribution | Playwright, user E2E chủ agency: CRM home tải được; user không có studio → `/portal-access/none` |
| §4.1 cutover (Infra #428) | plan 0 thêm / 1 sửa (CNAME `crm_agency[0]`) / 0 xoá; apply 40461647714; `dig` → distribution; Vercel `/x` → 301 `portal./x` |
| §4.1 smoke sau cutover | run 40461936316: 59 passed |
| §4.2 diễn tập rollback | T0 07:04:26Z (DNS về Vercel, Infra #429) → T1 07:07:54Z smoke Vercel xanh (run 40464957900): **3′28″**; T2 07:12:05Z (DNS về Fargate, Infra #430) → T3 07:15:16Z smoke Fargate xanh (run 40465695825): **3′11″** |
| §2.4b/§2.7/§3/§6a mời lại + studio (A10b-1, tự động) | `phase2.spec.ts` chế độ `a10b`, vai viewer, tenant tổng hợp Atlas & Hearth: (a) A10b mời → CRM 202, mail tới; (b) nhận lời + MFA; (c, d) studio trên `portal.` bằng đăng nhập partner, không API key; (e) quyền viewer giữ trên mọi kiểu header Bearer; E check khớp phiên API key; đăng xuất studio kết thúc phiên CRM → `/signed-out`. Ảnh: `shots/`, bản ghi chạy: `phase2-run.json` |

## Chuẩn bị dữ liệu cho luồng A10b (Dev, tenant tổng hợp)

- `shared.tenants.is_canary = TRUE` cho Atlas & Hearth (tenant E2E). CIS chỉ cho A10b mời trên tenant tổng hợp.
- Agency CRM tổng hợp cùng id, tạo bằng chính `console.create_agency` của CRM (ticket `AA-979`, Dev chỉ cho synthetic).
  Điều kiện 3 của `check_e2e_invitation`.
- Reset tài khoản partner của user mời (`crm_dev_identity.py invitee-reset --invitee studio-viewer`, dry run rồi apply).
- Lần thử đầu (trước khi có agency CRM) để lại một membership `invited` thừa trên Atlas & Hearth (`ab4e98e4…`), vô hại.

## Lỗi thật tìm ra và đã sửa

1. **Đăng xuất studio bị CSP chặn** (người dùng thật trên `portal.` sẽ gặp).
   - Nguyên nhân: CSP lúc build của studio là `form-action 'self'`. Web trả 303 sang trang logout của managed login, và trình duyệt áp `form-action` cho cả bước redirect đó, nên không có gì xảy ra. Phiên Cognito vẫn mở, lần vào `/portal/*` sau đó sẽ tự đăng nhập lại.
   - Sửa: CSP đặt lúc chạy trong `portal/proxy.ts` (`portal/lib/csp.ts`), thêm origin của managed login; host-source kiểm chặt (chặn `*`, `;`, dấu nháy). AA-Partner #94, AA-CIS-Infra #431 (`CRM_SIGN_OUT_FORM_ORIGIN`).
   - Review độc lập tìm ra 2 điểm cần sửa (guard Python, origin quá lỏng), đều đã sửa. Live: `form-action 'self' https://partner-auth.lumiguides.it.com`.
2. **Harness E2E bị race** khi điền form managed login (giá trị điền lúc hydrate bị mất, rồi chờ 15′). Thêm helper `fillSettled` (AA-Partner #94).

## Còn lại (theo runbook)

- §4.3 slice `/trip` (PR riêng), §4.4 gỡ cầu nối EXTERNAL `cis-portal` trên `/crm/v1`.
- §4.5 dọn dẹp ≥ 7 ngày sau cutover (**từ 03/11/2026**): `PORTAL_API_KEY_SIGNIN=false`, xoá project Vercel và các biến `VERCEL_PORTAL_*`, xoá bản `portal/` đông lạnh trong CIS, 301 `partner-dev.` → `portal.`, chuyển origin mail OAuth.
