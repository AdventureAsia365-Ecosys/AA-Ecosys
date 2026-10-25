# AA-Booking (AAA)

Live trên Dev (`https://api-booking.lumiguides.it.com/booking/health`). Mọi thứ chạy trên acc2; các account AAA (Quanskill) ở
ap-southeast-1 không thuộc hệ sinh thái. Nguồn sự thật: `apps/AA-Booking/CONTEXT.md` + root ADR 0004 / 0004a / 0005a.

- Layout: `backend/` (FastAPI, asyncpg SQL thuần, `app/` theo miền, `app/jobs/` = runner `booking.job`), `frontend/`
  (staff admin Next.js, Vercel `aa-booking-admin`), `migrations/` (key `bk-NNN`, nằm ngoài deploy paths). Customer app
  chưa làm.
- Runtime: ECS `aa-booking-dev-api` trên `aa-cis-dev-cluster`; worker `booking.job` (kind `bk_*`) chạy trong process
  API. Tài nguyên AWS ở AA-CIS-Infra `accounts/aa365/booking.tf` ("app sở hữu code, Infra sở hữu tài nguyên").
- DB: schema `booking` thuộc NOLOGIN `bk_owner`; app đăng nhập role `booking` (DML trong `booking`, đọc view được grant),
  không DDL. Migration chạy qua DB Migrate bằng `bk_owner`.
- Đọc từ app khác chỉ qua view được grant: TripPlanner `tripplanner.v_inquiry_outbox` (outbox → job `bk_inquiry_pull`
  → `booking.inbox_events`, hợp đồng `docs/contracts/inquiry.submitted.v1*.json`); catalog CIS **đọc live** lúc
  request (`catalog.v_tour`, `v_tour_day`, `v_tour_photo`, `v_destination`, `v_supply_content`; không copy), tombstone
  `catalog.v_tour_retired` + `catalog.v_tour_lifecycle_outbox` (job `bk_tour_lifecycle_pull`). Không đọc bảng pipeline
  CIS, không ghi nội dung (ADR 0002).
- Cho CIS đọc: view tổng hợp `booking.v_ops_*` và facts supply (`v_supply_*`) grant cho `cis_app`; ngoài ra không grant gì.
- Staff: Cognito WORKFORCE (client `booking-staff` + `breakglass`, quyền theo nhóm `booking-*` cấp trong CIS →
  Platform → Staff); hồ sơ mỏng `booking.staff_users`, không đọc danh bạ staff của CIS.
- B2B cho AA-Partner: `/booking/b2b/v1` chỉ nhận token M2M `aa-m2m-<env>` + `X-AA-Tenant-Id` kiểm theo
  `booking.b2b_partners`; giá ra ngoài là `b2b_price`, giá net nhà cung cấp không rời Booking.
- Quy tắc schema (ERD v2, `docs/AAA/erd-v2/`): `booking.trip_plans` = template, `booking.trip_cases` = hồ sơ khách — không gộp.
  Itinerary của version là bảng quan hệ (`trip_case_version_itinerary`), không JSONB. Ảnh lưu `s3_bucket` + `s3_key`, CDN URL sinh lúc trả response.
- Nền bất biến: state machine trip case trong DB; idempotency key cho mọi side effect; **payment không do agent thực
  hiện**.
