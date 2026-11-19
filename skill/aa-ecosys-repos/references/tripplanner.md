# AA-TripPlanner-Web

Nguồn sự thật: `apps/AA-TripPlanner-Web/CONTEXT.md`; yêu cầu sản phẩm: Notion "AA_TripPlanner_AI — PRD Canonical v0.3
(Map-First)".

- `frontend/` Next.js standalone trên ECS `aa-tripplanner-dev-web` sau CloudFront (`deploy-web-dev.yml`; Vercel đã bỏ ở
  AA-1038, S272) + BFF same-origin `/api/*` (giữ API key, gửi header `X-TripPlanner-Key`); `backend/` hai
  Lambda sau API Gateway HTTP: `browse/handler.py` (đọc, stateless, cache được; gọi model duy nhất là embedding cho
  search) và `assembly/handler.py` (mọi thay đổi trip + gọi Claude qua Bedrock satellite). Endpoint đọc mới đặt ở
  browse, mọi thứ ghi trip hoặc gọi text model đặt ở assembly.
- Dữ liệu: schema `tripplanner` (key `tp-NNN`; sessions, customers, trip_events, trip_drafts, outbox, narration_cache,
  llm_spend_daily, component_id_map, traveller_accounts) + Model Gateway (`shared.llm_role_config`,
  `llm_model_catalog`, `llm_call_log`). Mọi thứ khác của CIS **chỉ đọc qua view `catalog.*`** (`v_tour`,
  `v_tour_component`, `v_tour_stop`, `v_destination`, `v_tour_retired`…). Pipeline địa danh (extract, geocode, tour
  graph) là của CIS (ADR 0007, schema `geo`); repo này không ghi dữ liệu địa danh — test
  `backend/tests/test_extraction_ops.py` chặn SQL chạm object ngoài danh sách cho phép.
- Đơn vị khách pin: component của catalog (destination + activity + thời lượng), không phải nguyên tour; id component
  từ trước lần flip AA-847 ánh xạ qua `tripplanner.component_id_map`.
- "Send to advisor" là cổng người duy nhất; bắt đăng ký trước khi bàn giao bằng env `REQUIRE_REGISTRATION_BEFORE_HANDOFF`.
  Khách đăng nhập bằng email code (Cognito EXTERNAL), trang `/sign-in`, `/trips`.
- Bàn giao sang AA-Booking: outbox `tripplanner.outbox` → view `tripplanner.v_inquiry_outbox` → Booking
  `bk_inquiry_pull`; hợp đồng `docs/contracts/inquiry.submitted.v1*.json`. TripPlanner không gửi email; email staff
  do Booking gửi.
- Lead của đại lý (`lead.submitted.v1`): CRM / webhook / email theo lead route CIS. Assembly Lambda còn phục vụ M2M
  `/trip/m2m/v1` cho CRM của AA-Partner: kéo lead (scope `tripplanner.leads/deliver`) và, từ 1.1 (AA-1139), module
  TripPlanner của app đại lý `.../tenants/{id}/planner/*` (`assembly/planner_admin.py`: danh sách lead + trạng thái
  giao, usage AI session trong tháng, xoay khoá ký webhook có version ở tp-035; scope `tripplanner.leads/manage`).
  Hai trang dùng: CRM (Settings › Add-ons › Trip planner) và Content studio (Account › Trip planner) cho đại lý
  KHÔNG có CRM add-on (không có CRM agency; CRM API hỏi CIS `tenant.membership.v1` membership studio, actor
  `studio-member:<id>`); cài đặt site (lead route, theme, locale) của studio đi thẳng CIS `/v1/account/tripplanner`.
- Tài nguyên AWS (Lambda, API Gateway, OIDC deploy role, trust Bedrock) ở AA-CIS-Infra `accounts/aa365/tripplanner.tf`.
