# AA-Booking (AAA)

Trạng thái: live Dev từ S235 (`apps/AA-Booking`, `https://api-booking.lumiguides.it.com/booking/health`). Account AAA cũ ở ap-southeast-1 không thuộc hệ sinh thái; mọi thứ chạy trên acc2. Nguồn sự thật: `apps/AA-Booking/CONTEXT.md`; vài dòng thiết kế dưới đây là từ lúc bootstrap (AA-677/678/679).

- Repo `AA-Booking` (dự kiến): `backend/` (FastAPI, asyncpg, cùng pattern CIS) + `frontend/` (Next.js; staff admin + customer app).
- ECS service `aa-booking-dev-api` trên `aa-cis-dev-cluster`. Schema `booking` thuộc NOLOGIN `bk_owner` (bk-014, X1); app đăng nhập role `booking` (DML trong `booking`, đọc `catalog.*`), không DDL. Migration `bk-NNN` chạy qua DB Migrate bằng `bk_owner`.
- Catalog: CIS ghi outbox `catalog.tour.published|updated|trashed` → job AA-Booking upsert theo `external_ref` (AA-679). AAA không ghi bảng CIS; CIS không ghi dữ liệu thương mại.
- Quy tắc schema (ERD v2, AA-677): `trip_plans` = template, `trip_case` = hồ sơ khách — không gộp. Itinerary của version là bảng quan hệ, không JSONB. Ảnh lưu `s3_bucket` + `s3_key`, CDN URL sinh lúc trả response.
- Nền từ ngày đầu (comment AA-678, AA-682): state machine trip case trong DB; idempotency key cho mọi side effect; payment không do agent thực hiện; CI guard AA-725 + Playwright AA-732.
