# S253: snapshot lúc tạm dừng chờ reset hạn mức (27/10/2026)

Tác nhân: Claude Code. Đây là bản tạm; lúc chốt phiên phải chụp lại.

- ECS (tất cả COMPLETED, 1/1):
  - aa-cis-dev-api:861, aa-cis-dev-worker:427 (CIS `43a92134`);
  - aa-booking-dev-api:63 (`988e0a66` code S2; main hiện là `740ac714`, chỉ đổi workflow);
  - aa-crm-dev-api:63, aa-crm-dev-web:33, aa-crm-dev-portal:9.
- Migration: CIS 289, Booking bk-027. TripPlanner web `545514a0` (AA-995 Golden Hour live).
- PR còn mở:
  - CIS #1069 (sửa selector smoke, đang merge queue);
  - CIS #1068 (migration 290, ĐANG GIỮ: lỗi quyền schema shared + test interval);
  - các PR release: CIS #1049, Booking #95, TP #155, Partner #64;
  - Infra #411, #412 (cũ).
