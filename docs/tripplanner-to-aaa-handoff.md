# Spec (nháp) — Bàn giao TripPlanner → AA-Booking (AAA)

> **Trạng thái:** spec nháp G0, **CHƯA code**. Chờ repo/sản phẩm **AA-Booking (AAA)** hình thành.
> **[FACT]** = đã xác minh từ code TripPlanner hiện có; **[TODO-AAA]** = phụ thuộc phía AAA, chưa chốt;
> **[CẦN XÁC NHẬN]** = giả định cần Nghiệp duyệt.
> Nguồn AAA: `apps/AA-TripPlanner-Web/docs/AAA/` — `Adventure Asia PRD and Technical Spec Doc [Final].pdf`,
> `AA ERD.pdf`, `AAA_Quanskill_Handover_Review.docx`, `figma_AAA/` (screens). Các file này là binary,
> spec dưới đây tham chiếu chúng làm nguồn nhưng chưa trích nội dung chi tiết.

## 1. Bối cảnh & mục tiêu

- **TripPlanner** [FACT]: web B2C map-first. Khách vô danh (guest) duyệt điểm đến, ghim component
  (place + activity), ráp itinerary theo ngày, rồi **"Send to advisor"** + đăng ký thông tin liên hệ.
  Kết thúc luồng TripPlanner là một **draft trip + customer record**, KHÔNG phải booking hoàn chỉnh.
- **AA-Booking (AAA)** [TODO-AAA]: hệ quản trị Adventure Asia (admin: activity/hotel/supplier/trip,
  audit log — theo `figma_AAA/`) nơi advisor **nhận draft**, tư vấn, chốt và quản lý booking.
- **Điểm bàn giao:** draft trip do khách tạo ở TripPlanner → advisor xử lý ở AAA. Đây là ranh giới spec này mô tả.

## 2. Trạng thái hiện tại của điểm bàn giao (phía TripPlanner) [FACT]

Nguồn: `apps/AA-TripPlanner-Web/docs/architecture-overview.md`, `backend/assembly/{registration,notify,events}.py`.

- `send-to-advisor` là một route trong Lambda B (Assembly), cùng nhóm add/remove/reorder/narrate.
- `registration.py`: dedupe khách theo **phone/email** + gán (claim) session cho customer.
- `notify.py`: thông báo advisor hiện là **stub ghi log** — email thật (SES + domain verified) **deferred**.
- Dữ liệu draft nằm ở schema `tripplanner`: `trip_events` (append-only), `trip_drafts` (projection),
  `customers`, `sessions`, `itinerary_components`.

→ **Kết luận:** phía TripPlanner đã có "đầu ra" (draft + customer) nhưng **chưa có kênh bàn giao thật** sang AAA.
Hiện chỉ dừng ở log stub. Đây chính là phần spec này cần định nghĩa.

## 3. Interface bàn giao dự kiến

### 3.1 Phương án tích hợp [CẦN XÁC NHẬN — chọn 1]

| PA | Mô tả | Ưu | Nhược |
|----|-------|-----|-------|
| **A. Push webhook** | TripPlanner gọi API AAA khi khách Send-to-advisor | Realtime; đơn giản phía đọc | Cần AAA expose endpoint + auth; retry/idempotency |
| **B. Shared DB read** | AAA đọc trực tiếp `tripplanner.trip_drafts`/`customers` (cùng RDS acc2) | Không cần API mới; tận dụng RDS chung | Ghép chặt schema 2 hệ; ranh giới sở hữu mờ |
| **C. Event/queue** | TripPlanner phát event (SNS/SQS/EventBridge) → AAA tiêu thụ | Lỏng ghép, retry sẵn | Hạ tầng thêm; phức tạp hơn cho MVP |

> Khuyến nghị nháp: **PA A (webhook)** cho MVP — rõ ranh giới sở hữu, khớp với việc `notify.py` vốn đã là
> điểm "báo cho advisor". PA B chỉ nên là fallback tạm vì làm mờ ranh giới app/app. **[CẦN XÁC NHẬN]**

### 3.2 Payload bàn giao dự kiến (draft → AAA) [TODO-AAA]

Dựa trên dữ liệu TripPlanner đang có (schema `tripplanner`), payload tối thiểu:

```jsonc
{
  "source": "tripplanner",
  "draft_id": "uuid",              // trip_drafts
  "created_at": "iso8601",
  "customer": {                    // từ customers (dedupe phone/email)
    "name": "string",
    "phone": "string|null",
    "email": "string|null",
    "consent": true                // [CẦN XÁC NHẬN] cơ chế đồng ý liên hệ
  },
  "itinerary": {
    "days": [
      {
        "day": 1,
        "components": [
          {
            "component_id": "uuid",       // tripplanner.itinerary_components
            "place": "string",
            "activity": "string",
            "country": "string",
            "lat": 0.0, "lng": 0.0,       // [FACT] geocoded, có thể sai số nhỏ
            "source_tour_atom": "uuid|null" // trace về acp_contract.tour_atoms
          }
        ]
      }
    ],
    "narration": "string|null"      // bản AI compose/renarrate (nếu có)
  }
}
```

### 3.3 Ánh xạ dữ liệu TripPlanner ↔ AAA [TODO-AAA]

| TripPlanner | AAA (dự kiến, theo `AA ERD.pdf`) | Ghi chú |
|-------------|----------------------------------|---------|
| `customers` | Customer/Lead entity của AAA | Dedupe phone/email — cần thống nhất khoá định danh |
| `trip_drafts` | Draft booking / enquiry | Trạng thái khởi tạo trong pipeline booking của AAA |
| `itinerary_components` | Activity/Destination của AAA | **[CẦN XÁC NHẬN]** component TripPlanner (từ tour atom) có map 1-1 với "Activity" trong AAA không |
| `shared.destinations` | Destination golden record | Ứng viên bản ghi vàng dùng chung — xem architecture-overview §4 |

## 4. Ranh giới sở hữu [CẦN XÁC NHẬN]

- **TripPlanner sở hữu:** guest session, draft, customer capture, narration. KHÔNG quản lý booking/thanh toán.
- **AAA sở hữu:** advisor workflow, booking lifecycle, supplier/hotel/activity master, audit log.
- **Dùng chung:** RDS acc2 (schema tách biệt), có thể `shared.destinations` làm golden record.
- **Nguyên tắc:** giữ đúng "app owns code, infra owns resources" — nếu thêm hạ tầng cho kênh bàn giao
  (webhook endpoint, queue), Terraform nằm ở `AA-CIS-Infra` (hoặc root mới cho AAA khi có).

## 5. Bảo mật / auth điểm bàn giao [TODO-AAA]

- TripPlanner hiện dùng **edge shared-secret** (`X-TripPlanner-Key`) giữa BFF và Lambda [FACT].
- Kênh bàn giao TripPlanner → AAA cần cơ chế auth riêng: **[CẦN XÁC NHẬN]** shared secret / OIDC service-to-service / signed webhook.
- Xử lý PII (phone/email khách) qua ranh giới 2 hệ cần tuân thủ đồng ý liên hệ (consent) — **[CẦN XÁC NHẬN]**.

## 6. Open items (chờ AA-Booking)

- [ ] **[TODO-AAA]** Chốt phương án tích hợp (A/B/C ở §3.1).
- [ ] **[TODO-AAA]** AAA expose endpoint nhận draft (nếu PA A) + schema xác nhận.
- [ ] **[TODO-AAA]** Ánh xạ entity chi tiết dựa trên `AA ERD.pdf` (đọc ERD khi bắt đầu AAA).
- [ ] **[TODO-AAA]** Thay `notify.py` stub bằng kênh bàn giao thật.
- [ ] **[CẦN XÁC NHẬN]** Cơ chế consent + xử lý PII qua ranh giới.
- [ ] **[TODO-AAA]** Repo `AA-Booking` được tạo dưới org `AdventureAsia365-Ecosys`, thêm vào bảng kiến trúc.
- [ ] **[CẦN XÁC NHẬN]** Idempotency/retry cho bàn giao (một draft không tạo trùng lead ở AAA).

## 7. Không thuộc phạm vi spec này

- Booking lifecycle, thanh toán, supplier management (thuộc AAA).
- Auto-refresh extraction khi có tour mới (đã tracked riêng trong TripPlanner deferred list).
- Chi tiết UI advisor phía AAA (xem `figma_AAA/`).

## 8. Nguồn tham chiếu

- `apps/AA-TripPlanner-Web/docs/architecture-overview.md` — kiến trúc TripPlanner (§2/§3/§4).
- `apps/AA-TripPlanner-Web/backend/assembly/{registration,notify,events}.py` — code điểm bàn giao hiện tại.
- `apps/AA-TripPlanner-Web/docs/AAA/*` — PRD, ERD, Handover Review, Figma screens của AAA.
- `docs/ecosystem-architecture.md` — kiến trúc tổng hệ AA-Ecosys.
