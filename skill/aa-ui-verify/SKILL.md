---
name: aa-ui-verify
description: Kiểm tra giao diện trước khi báo xong — admin AA-CIS (frontend/), tenant portal / Content studio (AA-Partner portal/) và CRM web (AA-Partner web/), Next.js với UI kit app/_kit — build, Vercel preview, UI smoke, mở trang bằng browser, screenshot desktop/mobile/light/dark, console và network lỗi, dữ liệu thật, tuân thủ kit. Dùng mỗi khi sửa hoặc thêm trang, component, bảng, drawer, khi rà ảnh toàn portal, hoặc khi Nghiệp báo "UI không hiện / sai". Merge, deploy backend và đánh Done thuộc aa-ship.
---

# aa-ui-verify

Build pass không chứng minh trang chạy. Agent phải **nhìn thấy** trang rồi mới báo xong.
Bài học của vùng này: `aa-lessons/lessons.md` mục "Frontend" (phân trang server, Playwright chờ có trần, tràn ngang
mobile, hydrate trước khi `fill`) — đọc trước khi sửa trang.

## 1. Trước khi viết code

- Đọc `frontend/AGENTS.md` của AA-CIS-App: Next.js 16 có breaking changes — đọc guide trong
  `node_modules/next/dist/docs/` trước khi viết code FE (áp dụng cả `portal/` và `web/` của AA-Partner).
- Trang mới ráp từ kit `app/_kit/` (DataTable, Drawer, Modal, Toast, PageHeader, Tabs, Badge, StatusBadge,
  EmptyState/ErrorState/Skeleton, apiGet/apiSend). Không tự viết lại bảng/modal.
- Kit của `portal/` và `web/` (AA-Partner) là bản copy byte của AA-CIS-App `frontend/app/_kit` (check "Vendored CIS
  copies"): sửa file ở CIS trước, rồi chép sang.
- Fetch dữ liệu bằng react-query. Không fetch trong `useEffect` (React Compiler lỗi `set-state-in-effect`).
- Style: inline style + brand token, **không** Tailwind `className`. Kit prop khác legacy: EmptyState `description`
  (không phải `sub`), Badge `tone` (không phải `color`/`variant`).
- Trang mở bằng **tiếng Anh mặc định**; tiếng Việt chỉ khi người dùng chọn (locale của tenant/agency không tự đổi ngôn ngữ UI).
- Mở rộng trang có sẵn trước khi tạo route mới (ví dụ Tenant 360 là panel inline trong trang Tenants; Kit demo là tab
  trong Settings).
- Làm ADMIN trước, TENANT sau; mỗi issue một PR.

## 2. Build

```
export PATH="$HOME/.nvm/versions/node/v22.22.3/bin:/usr/local/bin:/usr/bin:/bin"
cd frontend && npm run lint && npm run build
```

Node mặc định 18 sẽ fail. tsc trong build bắt lỗi prop mà eslint bỏ sót.

- Tenant portal: code ở **AA-Partner `portal/`** (cùng lệnh, `cd portal`). `portal/` của AA-CIS-App là bản đóng băng,
  không deploy — không sửa.
- CRM web: AA-Partner `web/` → `npm test && npm run build`.
- Máy WSL ít RAM: mỗi lúc chỉ một `next build` / Playwright.

## 3. Kiểm trên preview hoặc Dev

1. Deploy của PR xanh: Vercel không tự build từ Git — `vercel-deploy.yml` (CIS) / `vercel-deploy-portal.yml`
   (Partner) tạo preview cho PR chạm `frontend/**` / `portal/**`; job deploy xanh và deployment READY. CRM web deploy lên ECS
   (`deploy-web-dev.yml`) sau merge, không có preview.
2. **Smoke tự động** (chỉ là sàn tối thiểu, trang vừa sửa vẫn kiểm tay các bước dưới):
   - **Preview riêng của từng PR** (`*.vercel.app`): `vercel-deploy.yml` gọi `ui-smoke.yml` sau khi preview xong,
     **chỉ spec công khai** (project `smoke-public`): Cognito không cho callback wildcard nên preview của PR không có
     đăng nhập staff. Đọc comment/artifact trên PR trước.
   - **Smoke có đăng nhập** (project `smoke`, spec gắn tag `@staff`, ảnh desktop/mobile × light/dark), người dùng Cognito
     E2E, chỉ chạy từ `main`:
     - Production `https://aa-cis.lumiguides.it.com`: job "UI smoke (production, signed in)" tự chạy sau mỗi production
       deploy, vai **reviewer**; trang reviewer không được mở phải chuyển về trang đích (`frontend/lib/rbac.ts` `PAGE_RULES`).
     - Host Preview cố định `https://aa-cis-preview.lumiguides.it.com`: vai **viewer**. Trỏ host vào preview của PR bằng
       dispatch `vercel-deploy.yml` từ `main` với `alias_only_url=<preview url>` (không tạo deployment mới, tự chạy smoke
       có đăng nhập), hoặc label `preview-signin` (tạo thêm một deployment — Vercel Hobby giới hạn số deployment/ngày)
       rồi dispatch `gh workflow run ui-smoke.yml --ref main -f base_url=https://aa-cis-preview.lumiguides.it.com -f staff_session=true`.
   - Local: `BASE_URL=<URL> npx playwright test --project=smoke-public`. Smoke có đăng nhập **không chạy được từ máy
     local** (role đọc hộp thư chỉ tin `refs/heads/main` + environment `e2e`).
   - Thêm trang = thêm 1 dòng vào danh sách trong `tests/e2e/smoke/ui-smoke.spec.ts`.
   - Portal: smoke ở AA-Partner (`e2e/smoke-portal/`, `e2e/playwright.portal.config.ts`), workflow `UI Smoke (portal)`
     tự chạy trên preview của PR đụng `portal/**` (đăng nhập tenant bằng secret `E2E_TENANT_API_KEY`).
3. Mở trang bằng browser (Claude in Chrome hoặc Playwright), đúng vai. **Không còn đăng nhập staff bằng mật khẩu ở bất kỳ
   host CIS nào** (AA-816 S2, root ADR 0006a A12): API từ chối mọi phiên HS256 (`/auth/verify-admin` → 401 "Password
   sessions are switched off"), `/login` chỉ có "Sign in with company email". Agent không đọc được hộp thư
   `@adventure.asia` nên phần có đăng nhập staff đi qua CI.

   | Cần kiểm | Ở đâu, bằng gì |
   |---|---|
   | Trang công khai, layout chung, trang `/login` | PR preview: smoke công khai (tự chạy) hoặc browser không đăng nhập |
   | Trang đọc (viewer xem được) trước merge | Host Preview cố định (dispatch `alias_only_url` hoặc label `preview-signin`) + smoke có đăng nhập |
   | Trang reviewer sau merge | Smoke production có đăng nhập (tự chạy sau deploy) hoặc `e2e-cognito.yml` |
   | Trang chỉ-admin, thao tác ghi admin | User E2E bị pre-token Lambda ghim đúng `cis-reviewer`, không nâng được: sau deploy nhờ **Nghiệp** đăng nhập production và kiểm (hoặc gửi ảnh); báo cáo ghi rõ phần này chưa do agent kiểm |
   | Tenant portal | Key tenant E2E (mục 3b) trên preview hoặc `https://portal.lumiguides.it.com` |
   | CRM web | Phần có đăng nhập: workflow `E2E Dev` (`e2e-dev.yml`, dispatch từ `main`) trên `https://partner-dev.lumiguides.it.com`; trang không đăng nhập mở bằng browser |
   | UI Booking | Agent chưa có tài khoản Booking dùng được: nhờ Nghiệp, ghi rõ "chưa do agent kiểm" |

   Không in hay ghi mã email / token / API key ra file, log hay PR. Rollback đăng nhập mật khẩu (chỉ khi sự cố): runbook
   root `docs/ops/runbooks/legacy-login-flag.md`, mục "Roll back or abort"; cần deploy, không phải bật một công tắc.
4. Với **mỗi trang đã đổi**, ghi lại:
   - Screenshot desktop 1440px và mobile 390px; light + dark.
   - Console: 0 error. Liệt kê warning mới.
   - Network: API của trang 2xx. Có 401/403/500 → đọc response body, đừng đoán (500 thật từng bị tưởng là 401).
   - Dữ liệu: bảng có dòng thật, hoặc đúng empty state. Số đếm khớp với query DB. Dữ liệu > 1 trang → đổi page size,
     sang trang 2, đếm option filter.
   - Mobile 390px: không tràn ngang (`scrollWidth <= clientWidth` của cả trang lẫn khung cuộn chứa bảng).
   - Hành động chính (nút, filter, drawer, bulk) bấm được và có tác dụng; sau thao tác, chờ trạng thái server (đọc lại
     API hoặc phần tử đích), không chờ chữ thông báo tạm.
5. Nút hay panel phụ thuộc trạng thái (ví dụ Live view chỉ hiện với job do trang tự kích) → thử cả trạng thái có và không.

## 3b. Audit ảnh chụp toàn trang — tenant portal (và admin)

Dùng khi cần rà cả portal chứ không chỉ trang vừa sửa.

1. **Chụp:** chạy smoke portal của AA-Partner local (thư mục `e2e/`), trỏ vào production portal
   (`https://portal.lumiguides.it.com`), lần lượt từng tenant brand:
   `BASE_URL=<portal> npx playwright test -c playwright.portal.config.ts --project=portal --workers=1`. Key mỗi tenant đọc
   từ Secrets Manager `aa-cis/dev/e2e-tenant/<tenant>` vào biến `E2E_TENANT_API_KEY` ngay trong lệnh — không in, không ghi file.
2. **Gom ảnh:** sau mỗi tenant, chép PNG từ AA-Partner `e2e/results/smoke-portal/` sang
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
UI verify <trang> — <PR #n>, deploy <xanh / READY>
- Desktop/mobile, light/dark: <ảnh>
- Console: 0 error | Network: <endpoint> 200
- Dữ liệu: <n> dòng, khớp query <…>
- Đã thử: <hành động>
- Còn thiếu / ngoài phạm vi: <…>
```

Không có ảnh hoặc chưa mở được trang → không báo "xong"; nói rõ còn thiếu bước nào. Câu "chạy được" chỉ cho đúng kênh/
vai đã thử thật, có ảnh.
