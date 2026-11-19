# Gateway AI: một gateway trung tâm hay mỗi app một gateway?

## 1) Trả lời ngắn

**Chưa nên dựng một gateway trung tâm (service HTTP) lúc này.** Nên đi theo hướng **"một gateway logic, chạy trong từng app"**: gom các luật đang bị chép tay vào thư viện chung `aa_llm`, và biến "app × connection" thành dữ liệu (dòng), không còn là cột hay map viết cứng. CRM thiếu cột vì lúc thiết kế coi connection là thuộc tính của cả process, không phải của từng route. Cách sửa tổng quát là lưu `connection_key` theo đúng bộ khoá của registry CIS ở mọi bảng route và ledger, và lưu ngân sách thành dòng `(app, connection_key)`.

## 2) Hiện trạng

- ADR 0009 d1 chốt một gateway logic cho mọi nhà cung cấp trả tiền (`docs/adr/0009-ai-platform-and-provider-gateway.md:130-140`). d13 chốt cách xây: lõi vendored cộng control plane của CIS, và service HTTP chỉ xét lại khi có ≥3 app chạy prod hoặc khi cần key trung tâm (`:414-427`).
- Phần dùng chung thật chỉ là lõi `aa_llm` thuần, khoảng 1,2k dòng (`apps/AA-CIS-App/shared/aa_llm/ports.py:1-13`). Phần dispatch thì mỗi app tự viết:
  - CIS khoảng 19,7k dòng;
  - TripPlanner khoảng 1,7k dòng (`apps/AA-TripPlanner-Web/backend/shared/llm_gateway.py:12-27`);
  - CRM khoảng 3,2k dòng.
- Có hai ledger: `shared.llm_call_log` (CIS và TripPlanner) và `crm.llm_call`. Hai bảng đặt tên cột khác nhau cho cùng một nghĩa: `created_at`/`at`, `tokens_in`/`input_tokens`, `cost_usd`/`cost_usd_est`, `status`/`outcome` (`docs/architecture/db-schema-reference.md:7308`, `:12537`).
- Chỉ CIS gọi được acc1 và Anthropic API. TripPlanner chỉ có Bedrock acc2/acc3, nên `tp_compose` mất nấc đầu (`docs/architecture/ai-use-register.md:227`). CRM chỉ có Nova Lite trên acc2 (`infra/AA-CIS-Infra/modules/environment/crm_llm.tf:1-24`).
- Anomaly breaker chỉ thực thi cho `cis` (`apps/AA-CIS-App/shared/llm_client/anomaly_breaker.py:44-45`). Hard stop theo connection chỉ chặn được CIS (ADR 0009:255-263).
- Các luật bị chép tay và lệch nhau:
  - `pii_patterns.py` chép từ CRM, kèm ghi chú "port it there too" (`apps/AA-CIS-App/shared/llm_client/pii_patterns.py:1-6`);
  - breaker của TripPlanner dùng bản SQL mirror, chạy theo luật cũ (ADR 0009:264-278).
- **Chuyện "CRM không có cột":**
  - `crm.llm_stage_route` không có cột connection. CHECK `provider = 'bedrock'` (`db-schema-reference.md:7388-7408`).
  - `crm.llm_usage_daily` có PK `(day, stage, model)`, không có connection (`:7411`).
  - `crm.llm_call` có `connection_key`, nhưng lưu nhãn riêng của CRM là `bedrock`/`bedrock_role`. Regex của cột cho phép `_`, khác regex registry CIS `^[a-z0-9][a-z0-9-]{1,62}$` (`:12886`).
  - Một map viết cứng `{"bedrock": "acc2"}` nối hai bên. `bedrock_role` không có trong map nên không bị cap nào (`apps/AA-Partner/api/app/llm/connection_cap.py:50-51`).
- API chia ngân sách AA-1113 có cột cứng `cis_share_usd`/`crm_share_usd` (`apps/AA-CIS-App/api/services/llm_connection_split.py:95-97`). TripPlanner bị tính chung vào phần của CIS và không bị chặn. Booking không có phần nào.
- Trong khi đó `shared.llm_app_profile` đã có CHECK app ∈ `cis, tripplanner, crm, booking` (`db-schema-reference.md:12498`). Nghĩa là danh sách app đã nằm sẵn trong dữ liệu.

**Kiểm chéo hai bản đề xuất:**

- Cả hai đều chọn hướng lai. Tôi đồng ý.
- Bản 1 đề xuất backfill `crm.llm_call.connection_key`. Cách này **sai**: bảng là append-only, có trigger `crm.erasable_append_only` (`:7365`). Bản 2 đúng: giữ nguyên dòng cũ, quy đổi tên trong contract view.
- Bản 2 muốn đưa retry, breaker và cả 3 lượt scrub vào kernel ngay. Phạm vi này quá rộng. Nên bắt đầu hẹp như bản 1: cap, anomaly, regex scrub, route plan.
- Con số "~520k dòng" của bản 2 chưa kiểm, tôi bỏ.
- Chi phí service (40–60 USD/tháng mỗi env) chỉ là ước tính, chưa tra giá bằng CLI.

## 3) Các phương án

| Phương án | Cách làm | Lợi | Hại | Công sức / chi phí |
|---|---|---|---|---|
| A. Giữ nguyên, vá từng chỗ | Thêm `bedrock_role` vào map, thêm cột `tp_share_usd`, port tay breaker và scrub sang TripPlanner/CRM | Nhanh, không cần sửa ADR | Mỗi app mới lại thêm cột hoặc map; ba bản luật chép tay sẽ lệch nhau | 6–9 ngày, 0 USD |
| B. Gateway trung tâm (service HTTP) | ECS `aa-ai-gateway` giữ mọi key, một ledger, cap xuyên sản phẩm | Một chỗ đặt luật, cap và key; TripPlanner/CRM có ngay route Anthropic → acc1 | Thêm một điểm chết chung (tier-0): service lỗi là mọi app mất AI; phải sửa ADR 0008a (lời hứa riêng tư với đại lý); thêm một hop trong giới hạn 30 s của Lambda TripPlanner; điều kiện xét lại của d13 chưa đạt | 30–50 ngày, ~40–60 USD/tháng mỗi env (ước tính), nhân đôi khi có prod |
| **C. Lai (khuyến nghị)** | Data plane vẫn chạy trong từng app; `connection_key` và ngân sách thành dòng; `aa_llm` 1.3 thêm module luật thuần; mỗi app có role/key riêng | Lỗi app nào ở app đó; CRM giữ nguyên 0008a; hết lệch luật; thêm app hay connection chỉ là thêm dòng | Không có hard stop nguyên tử xuyên app; ba lớp dispatch vẫn còn; kernel sync vẫn tốn PR bot | 18–25 ngày chia nhỏ, 0 USD |

## 4) Khuyến nghị và lý do

Chọn **C**, vì bốn lý do:

1. **Lỗi không lan sang app khác.** CIS deploy hỏng hoặc scale về 0 thì TripPlanner và CRM vẫn chạy, mỗi app rơi về `degrade_mode` riêng. TripPlanner được thiết kế "không phụ thuộc CIS API" (`llm_gateway.py:8-10`).
2. **Ranh giới PII giữ nguyên.** Scrub F3 của CRM chạy trong process và fail closed. ADR 0008a §5–6 không phải sửa.
3. **Lợi ích lớn nhất của B không cần tới.** Đó là hard cap nguyên tử xuyên sản phẩm, nhưng chính sách prod S283 chỉ yêu cầu cap ở mức alert + failover (ADR 0009:300-315).
4. **Đau thật nằm ở mô hình dữ liệu và luật chép tay**, không ở số lượng process. Sửa đúng chỗ đó thì rẻ hơn và đảo ngược được.

## 5) Lộ trình (không làm gãy Dev)

**Phiên này hoặc phiên sau:**

0. **Docs (root PR):**
   - thêm note vào ADR 0009 d13 về lớp "platform contract";
   - sửa dòng cũ `docs/architecture/ai-gateway.md:319` (CRM giờ là Nova Lite live, không còn stub);
   - ghi lại câu trả lời "vì sao CRM thiếu cột".
1. **CRM expand** (migration crm-NNN):
   - thêm `connection_key` nullable vào `crm.llm_stage_route` và `crm.llm_usage_daily`, rồi đưa nó vào PK (tạo PK mới sau khi đã điền dữ liệu);
   - dòng mới của `crm.llm_call` ghi khoá registry (`acc2`); dòng cũ quy đổi trong view;
   - giữ map `CIS_CONNECTION` làm fallback trong một release.
   - Cho reviewer xem trước khi merge, vì đây là migration.
2. **Split API v2:** trả `shares[]` gồm `{app, connection_key, share_usd, enforced, source}`, lấy danh sách app từ `shared.llm_app_profile`. Giữ hai field cũ trong một release rồi bỏ.

**Các phiên kế tiếp:**

3. **CRM contract:** sau khi đối chiếu tổng tiền khớp thì đặt NOT NULL cộng regex giống registry CIS, nới CHECK `provider`, provider factory chọn theo `connection_key`, rồi xoá map.
4. **Cap view v2 và TripPlanner:** thêm `catalog.v_llm_connection_cap_v2` có cột `app`. Phần ngân sách của TripPlanner nằm trong registry CIS, vì đó vốn là control plane của TripPlanner theo d13. TripPlanner chạy ở chế độ log trước, rồi mới bật thực thi.
5. **`aa_llm` 1.3:** thêm các module thuần `caps`, `anomaly`, `scrub_patterns`, `route_plan`, kèm golden test. CIS dùng trước; TripPlanner và CRM bật dần theo thứ tự log → on. Xoá bản port tay `pii_patterns.py`.
6. **Anomaly breaker theo từng app**, chạy trên ledger của chính app đó.
7. **PII cho `tp_plan_chat`:** thêm dòng registry và scrub, khai `pii_class` theo stage (ADR 0019 d12). Việc này cũng gỡ mâu thuẫn giữa `free_text_scrub.py:7-9` và `ai-use-register.md:227`.

**Để sau:**

8. **TripPlanner lên acc1** (trust riêng, ExternalId riêng) cộng key Anthropic riêng: chờ buổi review acc1 đầu tháng 12.
9. **CRM failover sang acc1/acc3:** chỉ làm khi tiến gần prod.

## 6) Khi nào nên xem lại

- Prod có tenant trả tiền dùng AI trên ≥2 app, **và** chính sách được đổi sang hard stop xuyên sản phẩm.
- Bán gói "AI credit" chung một quota cho CRM, TripPlanner và Content studio.
- Nhà cung cấp bắt buộc dùng một key trung tâm, hoặc 429 dùng chung khiến app này làm đói app kia (>2% call bị throttle mỗi ngày trong một tuần).
- Vẫn còn ≥2 sự cố lệch luật trong một quý sau `aa_llm` 1.3, hoặc có caller không viết bằng Python.
- Có yêu cầu một audit log AI duy nhất (DPA, EU AI Act, lưu prompt), hoặc tổng chi AI vượt khoảng 2–3k USD/tháng.
- Đội có người trực được một service tier-0.

## 7) Quyết định tech lead cần chốt

1. **Giữ mô hình C, hoãn service HTTP?** Đề xuất: Có. Ghi vào note của ADR 0009 d13.
2. **Dùng `connection_key` theo đúng registry CIS ở mọi app, kể cả CRM** (CRM chỉ dùng khoá, không đọc bảng CIS)? Đề xuất: Có. Lời hứa "không grant hai chiều" vẫn giữ nguyên.
3. **Ngân sách thành dòng `(app, connection_key)` thay cho cột cứng?** Đề xuất: Có. Phần của TripPlanner nằm trong registry CIS, phần của CRM vẫn ở setting CRM.
4. **Mở trust acc1 cho role riêng của TripPlanner?** Đề xuất: quyết trong buổi review acc1 đầu tháng 12. Trước đó TripPlanner giữ nguyên route hiện tại.
5. **Kernel `aa_llm` 1.3 bắt đầu với phạm vi hẹp** (cap, anomaly, regex scrub, route plan), không gồm retry/breaker/I-O? Đề xuất: Có, kèm test chặn lõi tự mở kết nối.
6. **Key Anthropic riêng cho từng app** (workspace riêng, có cap trên console)? Đề xuất: Có khi tới bước 8. Đây là thao tác tay trên console, không phát sinh chi phí.
