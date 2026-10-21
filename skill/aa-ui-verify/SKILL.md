---
name: aa-ui-verify
description: Kiểm tra UI admin/portal AA-CIS (Next.js, UI kit app/_kit) trước khi báo xong — build, Vercel preview, mở trang bằng browser, screenshot desktop/mobile/light/dark, console và network lỗi, dữ liệu thật, và tuân thủ kit. Dùng mỗi khi sửa hoặc thêm trang, component, bảng, drawer, hoặc khi Nghiệp báo "UI không hiện / sai".
---

# aa-ui-verify

Build pass không chứng minh trang chạy. Agent phải **nhìn thấy** trang rồi mới báo xong.

## 1. Trước khi viết code

- Đọc `frontend/AGENTS.md` (Next.js bản mới có breaking changes — đọc guide trong `node_modules/next/dist/docs/` trước khi viết code FE).
- Trang mới ráp từ kit `app/_kit/` (DataTable, Drawer, Modal, Toast, PageHeader, Tabs, Badge, StatusBadge, Empty/Error/Skeleton, apiGet/apiSend). Không tự viết lại bảng/modal.
- Fetch dữ liệu bằng react-query. Không fetch trong `useEffect` (React Compiler lỗi `set-state-in-effect`).
- Style: inline style + brand token, **không** Tailwind `className`. Kit prop khác legacy: EmptyState `description` (không phải `sub`), Badge `tone` (không phải `color`/`variant`).
- Mở rộng trang có sẵn trước khi tạo route mới. Ví dụ: Tenant 360 là panel inline trong trang Tenants, không phải `/admin/tenants/[id]`. Kit demo là tab trong Settings, không phải mục nav riêng.
- Làm ADMIN trước, TENANT sau; mỗi issue một PR.

## 2. Build

```
export PATH="$HOME/.nvm/versions/node/v22.22.3/bin:/usr/local/bin:/usr/bin:/bin"
cd frontend && npm run lint && npm run build
```
Node mặc định 18 sẽ fail. tsc trong build bắt lỗi prop mà eslint bỏ sót.

## 3. Kiểm trên preview hoặc Dev

1. Vercel deployment của PR = **READY/SUCCESS**.
2. **Smoke tự động (AA-732):** mỗi PR có Vercel preview → workflow `UI smoke (Playwright)` tự chạy (`deployment_status`, env `Preview`), mở 7 trang admin chính, fail khi API `/api/` 4xx/5xx, console error, hoặc trang không có dòng/empty state; ảnh desktop/mobile × light/dark nằm trong artifact + comment trên PR. Đọc comment/artifact đó trước. Từ S244 (AA-878 N1) smoke đăng nhập bằng tài khoản **viewer** (`e2e-claude-code-viewer`, GitHub `E2E_ADMIN_*`), log ghi "logged in with staff role: viewer"; spec chỉ dành cho admin tự skip (59 passed / 7 skipped là bình thường). Chạy tay: `gh workflow run ui-smoke.yml [--ref <branch>] -f base_url=<preview URL>`; local: `BASE_URL=<preview URL> npx playwright test --project=smoke` với `E2E_ADMIN_USERNAME/PASSWORD` export từ secret `aa-cis/dev/e2e-test-viewer` (không in). **Không** chạy smoke với `base_url` = production `https://aa-cis.lumiguides.it.com`: production không còn form mật khẩu, `smoke-setup` fail "HTTP 404". Thêm trang = thêm 1 dòng vào danh sách trong `tests/e2e/smoke/ui-smoke.spec.ts`. Portal chờ tenant test (AA-741, `E2E_TENANT_API_KEY`).
   Smoke chỉ là sàn tối thiểu — trang vừa sửa vẫn kiểm tay các bước dưới.
3. Mở trang bằng browser (Claude in Chrome hoặc Playwright), đăng nhập đúng vai (admin / tenant test). Đăng nhập staff
   đã đổi từ AA-816 S1 (19/10/2026, S244):
   - **Production** (`aa-cis.lumiguides.it.com`): **không còn đăng nhập bằng mật khẩu**; trang `/login` chỉ có
     "Sign in with company email" (Cognito, mã gửi qua email). `POST /api/auth/login` → 404. Agent không đọc được
     hộp thư `@adventure.asia`, nên không tự đăng nhập admin trên production được.
   - **PR preview**: form mật khẩu legacy vẫn còn (cờ Preview giữ bật đến S2), nhưng BFF của preview giữ **Preview
     credential** (`aa-cis/dev/admin-secret-preview`, AA-816 C9) nên mọi phiên trên preview chỉ có **quyền viewer**,
     kể cả khi đăng nhập bằng tài khoản admin. Ghi admin (lưu, duyệt, chạy job) và trang chỉ-admin trả 403 trên preview
     — đó là thiết kế, không phải lỗi của PR.
   - Cách kiểm theo loại trang:
     | Cần kiểm | Ở đâu, bằng gì |
     |---|---|
     | Trang đọc (viewer xem được) | PR preview, tài khoản viewer: secret `aa-cis/dev/e2e-test-viewer` (user `e2e-claude-code-viewer`) |
     | Trang reviewer trên production sau merge | workflow `e2e-cognito.yml` (người dùng Cognito E2E, vai reviewer, hộp thư E2E theo ngoại lệ A10) — chỉ trang reviewer |
     | Trang chỉ-admin, thao tác ghi admin | Sau merge + deploy: nhờ **Nghiệp** đăng nhập production bằng mã email và kiểm (hoặc gửi ảnh); ghi rõ trong báo cáo là phần này chưa do agent kiểm |
     | Trang admin CIS trên preview, quyền thật (Cognito) | Host Preview cố định `aa-cis-preview.lumiguides.it.com` (AA-911): gắn nhãn `preview-signin` cho PR hoặc dispatch `alias_only_url` từ main, rồi **Nghiệp** đăng nhập bằng mã email (agent không đọc được hộp thư). Runbook `docs/ops/runbooks/preview-staff-sign-in.md` |
     | UI Booking | **Agent không đăng nhập được** (AA-911: bridge CIS đã gỡ; user Cognito E2E không được có nhóm `booking-*`, ADR 0006a A10). Nghiệp đăng nhập trên `booking-preview.lumiguides.it.com` (preview) hoặc production và gửi ảnh; ghi rõ trong báo cáo phần này chưa do agent kiểm |
   - Đọc mật khẩu từ secret vào biến môi trường lúc chạy, không in hay ghi ra file/log/PR. Đổi mật khẩu một tài
     khoản test legacy chỉ còn qua DB Migrate `run-script` có review (script `create_staff_user.py` đã bỏ ở CIS #858).
4. Với **mỗi trang đã đổi**, ghi lại:
   - Screenshot desktop 1440px và mobile 390px; light + dark.
   - Console: 0 error. Liệt kê warning mới.
   - Network: API của trang 2xx. Có 401/403/500 → đọc response body, đừng đoán (S212: 500 thật bị tưởng là 401).
   - Dữ liệu: bảng có dòng thật, hoặc đúng empty state. Số đếm khớp với query DB.
   - Hành động chính (nút, filter, drawer, bulk) bấm được và có tác dụng.
5. Nút hay panel phụ thuộc trạng thái (ví dụ Live view chỉ hiện với job do trang tự kích) → thử cả trạng thái có và không.

## 4. Báo cáo

```
UI verify <trang> — <PR #n>, Vercel <READY>
- Desktop/mobile, light/dark: <ảnh>
- Console: 0 error | Network: <endpoint> 200
- Dữ liệu: <n> dòng, khớp query <…>
- Đã thử: <hành động>
- Còn thiếu / ngoài phạm vi: <…>
```

Không có ảnh hoặc chưa mở được trang → không báo "xong"; nói rõ còn thiếu bước nào.
