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
2. **Smoke tự động (AA-732):** mỗi PR có Vercel preview → workflow `UI smoke (Playwright)` tự chạy (`deployment_status`, env `Preview`), mở 7 trang admin chính, fail khi API `/api/` 4xx/5xx, console error, hoặc trang không có dòng/empty state; ảnh desktop/mobile × light/dark nằm trong artifact + comment trên PR. Đọc comment/artifact đó trước. Chạy tay: `gh workflow run ui-smoke.yml [--ref <branch>] -f base_url=<preview URL>`; local: `BASE_URL=https://aa-cis.lumiguides.it.com npx playwright test --project=smoke` với `E2E_ADMIN_USERNAME/PASSWORD` export từ secret (không in). Thêm trang = thêm 1 dòng vào danh sách trong `tests/e2e/smoke/ui-smoke.spec.ts`. Portal chờ tenant test (AA-741, `E2E_TENANT_API_KEY`).
   Smoke chỉ là sàn tối thiểu — trang vừa sửa vẫn kiểm tay các bước dưới.
3. Mở trang bằng browser (Claude in Chrome hoặc Playwright), đăng nhập đúng vai (admin / tenant test).
   Tài khoản admin test: secret `aa-cis/dev/e2e-test-admin` (acc2, JSON username/password; user `e2e-claude-code`).
   Đọc vào biến môi trường lúc chạy, không in hay ghi mật khẩu ra file/log/PR.
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
