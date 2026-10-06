# AA-Booking (AAA)

Trạng thái: bootstrap (AA-678) — repo CHƯA tồn tại. Account AAA cũ ở ap-southeast-1 đã đóng; mọi thứ chạy trên acc2. Nội dung dưới là thiết kế dự kiến (AA-677/678/679), verify lại khi repo có thật.

- Repo `AA-Booking` (dự kiến): `backend/` (FastAPI, asyncpg, cùng pattern CIS) + `frontend/` (Next.js; staff admin + customer app).
- ECS service `aa-booking-dev-api` trên `aa-cis-dev-cluster`. DB role chỉ ghi schema `booking`, đọc `shared.*` và catalog views.
- Catalog: CIS ghi outbox `catalog.tour.published|updated|trashed` → job AA-Booking upsert theo `external_ref` (AA-679). AAA không ghi bảng CIS; CIS không ghi dữ liệu thương mại.
- Quy tắc schema (ERD v2, AA-677): `trip_plans` = template, `trip_case` = hồ sơ khách — không gộp. Itinerary của version là bảng quan hệ, không JSONB. Ảnh lưu `s3_bucket` + `s3_key`, CDN URL sinh lúc trả response.
- Nền từ ngày đầu (comment AA-678, AA-682): state machine trip case trong DB; idempotency key cho mọi side effect; payment không do agent thực hiện; CI guard AA-725 + Playwright AA-732.
