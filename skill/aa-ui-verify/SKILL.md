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
2. **Smoke tự động (AA-732; chia đôi từ AA-816 S247):**
   - **Preview riêng của từng PR** (`*.vercel.app`): workflow `UI smoke (Playwright)` tự chạy (`deployment_status`,
     env `Preview`) nhưng **chỉ spec công khai** (project `smoke-public`, không đăng nhập): Cognito không cho
     callback wildcard nên preview của PR không có đăng nhập staff. Đọc comment/artifact trên PR trước.
   - **Smoke có đăng nhập** (project `smoke`, spec gắn tag `@staff`, 7 trang admin chính, ảnh desktop/mobile ×
     light/dark): đăng nhập bằng **người dùng Cognito E2E** (hộp thư E2E theo ngoại lệ A10), chỉ chạy từ `main`:
     - Production: tự chạy sau mỗi production deploy ("UI smoke (production, signed in)"), vai **reviewer**; trang
       reviewer không được mở phải chuyển về trang đích (`frontend/lib/rbac.ts` `PAGE_RULES`).
     - Host Preview cố định `https://aa-cis-preview.lumiguides.it.com`: vai **viewer** (setup fail nếu khác viewer).
       Trỏ host vào preview của PR bằng label `preview-signin`, rồi dispatch smoke từ `main`.
     - Chạy tay (agent điều phối): `gh workflow run ui-smoke.yml --ref main -f base_url=<một trong hai host> -f staff_session=true`.
   - Local: `BASE_URL=<URL> npx playwright test --project=smoke-public`. Smoke có đăng nhập **không chạy được từ máy
     local** (role đọc hộp thư chỉ tin `refs/heads/main` + environment `e2e`).
   Thêm trang = thêm 1 dòng vào danh sách trong `tests/e2e/smoke/ui-smoke.spec.ts`. Portal chờ tenant test (AA-741,
   `E2E_TENANT_API_KEY`). Smoke chỉ là sàn tối thiểu: trang vừa sửa vẫn kiểm tay các bước dưới.
3. Mở trang bằng browser (Claude in Chrome hoặc Playwright), đăng nhập đúng vai (admin / tenant test). **Không còn
   đăng nhập staff bằng mật khẩu ở bất kỳ host CIS nào** từ AA-816 S2 (22/10/2026, S247; root ADR 0006a A12): API
   từ chối mọi phiên HS256 (`/auth/verify-admin` → 401 "Password sessions are switched off"), BFF `/api/auth/login`
   → 404, `/login` chỉ có "Sign in with company email". Tài khoản legacy `e2e-claude-code`, `e2e-claude-code-2` đã
   tắt. Agent không đọc được hộp thư `@adventure.asia` nên không tự đăng nhập tay được; phần có đăng nhập đi qua CI.
   - Cách kiểm theo loại trang:
     | Cần kiểm | Ở đâu, bằng gì |
     |---|---|
     | Trang công khai, layout chung, trang `/login` | PR preview: smoke công khai (tự chạy) hoặc browser không đăng nhập |
     | Trang đọc (viewer xem được) trước merge | Label `preview-signin` trên PR + dispatch smoke có đăng nhập trên host Preview cố định (vai viewer) |
     | Trang reviewer sau merge | Smoke production có đăng nhập (tự chạy sau deploy) hoặc `e2e-cognito.yml` |
     | Trang chỉ-admin, thao tác ghi admin | Sau merge + deploy: nhờ **Nghiệp** đăng nhập production bằng mã email và kiểm (hoặc gửi ảnh); ghi rõ trong báo cáo là phần này chưa do agent kiểm |
     | UI Booking | Agent chưa có tài khoản Booking dùng được (`e2e-claude-code` đã tắt S247; người dùng Cognito E2E chưa có vai Booking): nhờ Nghiệp, ghi rõ "chưa do agent kiểm" |
   - Không in hay ghi mã email / token ra file, log hay PR. Rollback đăng nhập mật khẩu (chỉ khi sự cố): runbook root
     `docs/ops/runbooks/legacy-login-flag.md`, mục Roll back; cần deploy, không phải bật một công tắc.
4. Với **mỗi trang đã đổi**, ghi lại:
   - Screenshot desktop 1440px và mobile 390px; light + dark.
   - Console: 0 error. Liệt kê warning mới.
   - Network: API của trang 2xx. Có 401/403/500 → đọc response body, đừng đoán (S212: 500 thật bị tưởng là 401).
   - Dữ liệu: bảng có dòng thật, hoặc đúng empty state. Số đếm khớp với query DB.
   - Hành động chính (nút, filter, drawer, bulk) bấm được và có tác dụng.
5. Nút hay panel phụ thuộc trạng thái (ví dụ Live view chỉ hiện với job do trang tự kích) → thử cả trạng thái có và không.

## 3b. Audit ảnh chụp toàn trang — tenant portal (và admin) (S247)

Dùng khi cần rà cả portal chứ không chỉ trang vừa sửa (S247 AA-760).

1. **Chụp:** chạy smoke có sẵn local, trỏ vào production portal (`https://portal.lumiguides.it.com`), lần lượt từng
   tenant brand: `BASE_URL=<portal> npx playwright test --project=smoke-portal --workers=1`. Key mỗi tenant đọc từ
   Secrets Manager `aa-cis/dev/e2e-tenant/<tenant>` vào biến `E2E_TENANT_API_KEY` ngay trong lệnh — không in, không
   ghi file.
2. **Gom ảnh:** sau mỗi tenant, chép PNG từ `tests/e2e/results/smoke-portal/` sang
   `.tmp-session/<issue>-shots/<tenant>/` (lần chạy sau ghi đè thư mục kết quả).
3. **Review:** agent review mở **từng ảnh** theo nhóm trang và điền checklist: trạng thái (loading/lỗi), empty state,
   nhãn/copy, layout desktop + phone, dark mode, dữ liệu thật, **lộ thông tin nội bộ** (tenant chỉ thấy nội dung —
   memory `tenant-sees-content-only`: không gate/held/flag/QA).
4. **Sửa:** một agent sửa gom mọi phát hiện; rồi **một agent verify độc lập** chụp lại và kiểm.

Bẫy khi chụp:

- Chờ dữ liệu xong mới chụp: không còn phần tử `[aria-busy="true"]`.
- Shell portal cuộn bên trong `main[data-pshell=main]`, không cuộn `body` → full-page chỉ ra khung nhìn; đặt kích
  thước viewport theo chiều cao nội dung của `main` trước khi chụp.
- Login smoke: điền key lặp lại tới khi input (đã hydrate) giữ được giá trị (`auth.setup.ts`); điền trước hydrate bị
  React reset im lặng.

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
