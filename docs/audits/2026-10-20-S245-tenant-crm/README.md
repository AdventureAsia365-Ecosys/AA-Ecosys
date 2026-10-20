# Thiết kế CRM cho đại lý (tenant) — sản phẩm hoàn chỉnh (AA-821 / PR-19)

Ngày 20/10/2026, phiên S245, tác nhân: Claude Code. Chỉ đọc và viết tài liệu: không đổi Linear, Jira, Notion, GitHub
hay AWS. Quyết định đầu vào của Nghiệp (S245): **không làm MVP**, thiết kế sản phẩm hoàn chỉnh theo spec của chị Thư
([partner-crm-spec.md](../../research/partner-crm-spec.md), Jira PR-19) để xây thẳng một mạch.

Tài liệu gốc trong `research/` (tiếng Anh, giữ nguyên như workflow trả về):
[01 nền tảng](research/01-platform-fit.md) · [02 yêu cầu](research/02-requirements.md) ·
[03 benchmark](research/03-market-benchmark.md) · [04 chi phí, tuân thủ, bảo mật](research/04-economics-compliance-security.md) ·
[options.json](research/options.json) · [judges.json](research/judges.json) · [ADR nháp](research/adr-draft.md).

## 1. Tóm tắt

1. Khuyến nghị: xây CRM thành **app thứ tư `AA-CRM`** (repo, ECS service, REST API, schema `crm` riêng), giao diện cho đại lý chạy **bên trong portal** (`/portal/crm`, Vercel multi-zone) nên đại lý chỉ thấy một portal, một lần đăng nhập.
2. Phủ đủ 23 module (F1–F5, 1–18) và cả 3 điểm khác biệt của spec: hàng AA thật trong CRM (qua Booking B2B API), proposal khách tự chọn (qua TripPlanner `/builder`), riêng tư theo kiến trúc (khoá KMS riêng mỗi đại lý, profile ẩn danh, scrubber, audit log).
3. Công sức: **khoảng 16 phiên agent (dải 14–16,5), ~114 issue, 9 đợt W0–W8**, ở nhịp 8–10 issue/phiên (agent team): 114 ÷ 8–10 ≈ 12–15 phiên làm, cộng 1–2,5 phiên dự phòng; bảng §9 cộng từ dưới lên ≈ 16,3. Ở nhịp hiện tại 3–5 issue/phiên thì là 23–38 phiên.
4. Lịch thực tế bị quyết định bởi việc **ngoài code**: xác minh Google (CASA), Meta/WhatsApp, insurer duyệt waiver, luật sư (DPA, PDPL Việt Nam, có thể cần giấy phép VN), và môi trường prod (AA-880), vì dữ liệu khách thật không được lên Dev (C7.1a). Phải khởi động tất cả từ W0.
5. Chi phí tăng thêm: Dev ~$70–83/tháng; prod ~$500–925 / $1,6–2,0k / $4,7–5,2k mỗi tháng ở 10 / 50 / 200 đại lý, chưa kể prod nền ($150–300) và phí luật sư (chưa có báo giá).
6. Cần Nghiệp trả lời **20 quyết định** ở §15 (có/không hoặc a/b/c) cộng một ngày go-live prod, và hỏi chị Thư 10 câu, trong đó quan trọng nhất là mô hình giá cho đại lý và câu chữ cam kết F1.

## 2. Yêu cầu của chị Thư (trích nguyên văn)

| # | Nguyên văn | Ngày / kênh | Nguồn |
|---|---|---|---|
| T1 | "Chị đang suy nghĩ build 1 cái CRM, quản lý khách hàng cho tenant." | 14/10/2026 (S236) | AA-821; log S236 |
| T2 | "CRM cho travel agencies (tenant) dùng với khách hàng của họ, Không phải AA quản lý tenant." | 18/10/2026, Jira | PR-19 |
| T3 | Đính kèm spec (link Drive) làm tài liệu yêu cầu | 18/10/2026 | PR-19 → [partner-crm-spec.md](../../research/partner-crm-spec.md) |
| T4 | (Nghiệp chép lại, không có nguyên văn) CRM nằm **trong** tenant portal, cho tenant quản lý khách B2C; không bán riêng ngoài portal | 19/10/2026, Zalo 11:07 | comment AA-821 |
| T5 | "Cái CRM em cứ lơ đi cái 40 tuần đi" | 19/10/2026, Zalo 11:21 | comment AA-821; log S243 |

Spec (trích): mục đích "*a CRM given to AA partner travel agencies to manage their own customers (B2C): inquiry →
proposal → booking → payment → trip → follow-up*"; ba điểm khác biệt "*Live AA supply inside the CRM*",
"*Traveler-configurable proposals*", "*Privacy by architecture*"; định vị "*free for partners*"; nguyên tắc "*Traveler
data belongs to the agency*", "*AI drafts, humans send*", "*Every task must be faster than the agency's current Gmail +
WhatsApp + spreadsheet routine*", "*Privacy foundation ships before any feature that stores or reads traveler data*".
Pipeline 7 bước Inquiry → Qualifying → Proposal → Booked → Pre-departure → Travelling → Completed (+ Lost). Thu thập
dữ liệu theo 3 giai đoạn. 23 module, 7 tích hợp (§9), một track không phải code (luật, DPA, thoả thuận không lôi kéo
khách, insurer, WhatsApp).

Cách hiểu S245: T5 bỏ **kế hoạch 40 tuần / 2–3 dev**, không bỏ phạm vi. Nghiệp chốt làm đủ phạm vi. Câu hỏi Q1 trong
[02](research/02-requirements.md) (bỏ lịch hay bỏ cả phạm vi) coi như đã trả lời; nên xác nhận lại với chị Thư một câu (§15, H1).

## 3. Hiện trạng nền tảng: cái gì tái dùng được

| Cần | Đã có | Dùng thế nào |
|---|---|---|
| Vỏ portal + UI kit | App `portal/` (Vercel `aa-cis-portal`), BFF tenant, kit `DataTable`/`Drawer`/`savedViews` (AA-885) | Zone `/portal/crm/*` trong host portal; kit chép byte-copy có guard |
| Danh tính tenant | Hôm nay: 1 API key chung mỗi tenant, chưa có người dùng riêng | **Chưa đủ.** Cần AA-813 (Cognito EXTERNAL, `shared.tenant_members`, lời mời) — điều kiện cứng |
| Cách ly DB | Mẫu RLS CIS 229/241, pool fail-closed AA-544, probe aa817; X1 xong (runtime CIS = `cis_app`) | Dùng **mẫu**, không dùng role: CRM có `crm_owner`/`crm_app` riêng, FORCE RLS từ `crm-001` |
| Audit log | `acp_shared.audit_log` hash-chain (CIS 248) | Chép thiết kế sang `crm.access_event`, đổi khoá advisory theo tenant |
| Job runner | Mẫu bảng job ADR 0003a (`shared.job`, `booking.job`) | `crm.job` với kind `crm_*` |
| State machine | Booking `trip_case_status_transitions` + trigger (bk-003) | Chép mẫu cho pipeline 7 bước |
| Inbox idempotent | `booking.inbox_events UNIQUE(source, contract, idempotency_key)` + xoá PII 90 ngày | Chép mẫu cho webhook Stripe/Twilio/Meta/Graph và sự kiện Booking |
| Lead → khách | `bk_inquiry_process` | **Chỉ chép mẫu.** DM-6.8/KEY-6 cấm CRM đọc/ghi `booking.customers`, `tripplanner.customers` |
| Catalog tour | `catalog.v_tour*`, `v_destination`, `catalog.v_graph_node` / `catalog.v_graph_edge` (hợp đồng `docs/contracts/catalog.graph.v1.json`); khoá mềm `(source_system, source_id)` | Proposal tham chiếu tour bằng khoá mềm |
| Nội dung tenant đã đăng | `acp_shared.content_piece`, `publish_log`; `tenant_brand_rules.default_cta` | Gắn nguồn lead (attribution) + CTA trỏ form của tenant |
| Giá B2B | ADR 0005 quyết định 9 (bảng giá net B2B, kênh `b2b` đã có trong `pricing_rules`); AA-681 Done | Booking B2B API mới (giá, availability, hold) — **chưa có endpoint, chưa có mô hình availability** |
| Kết nối kênh | `shared.tenant_integrations` + connect/test/disconnect WP/FB | Chép UX cho mailbox, WhatsApp |
| Webhook cho tenant | Portal ghi "Coming soon", không có router | Chưa có |
| Gác AI | Model Gateway + `shared.llm_call_log`; DM-6.4; AA-820 | Ràng buộc cho module 14 |

**Lead của tenant hôm nay đi đâu:** không vào nền tảng. CTA là chữ trơn; trang trip white-label `/trip/[tourId]` của
CIS có CTA cứng `mailto:admin@adventureasia.com` — khách đến từ kênh của tenant sẽ email cho **AA**, ngược hướng
controller (và domain có thể sai). Chi tiết: [01 §3](research/01-platform-fit.md).

## 4. Benchmark thị trường

| Công cụ | Mạnh | Yếu (so với spec) | API/webhook nhận lead | GDPR/vùng dữ liệu | Giá 2026 (nguồn) |
|---|---|---|---|---|---|
| Tourwriter | Itinerary → booking NCC → hoá đơn | CRM cơ bản; không white-label cho đại lý con | REST, cài qua support; webhook không rõ | Không công bố | $99–249/user/tháng + ~$1.199 setup (bên thứ ba) |
| Travefy | CRM mới (07/2025), form, automation, proposal, hoá đơn, hoa hồng | API là sản phẩm trả phí riêng | API $2.500/năm; $1.000/tháng cho 1.000 itinerary | Không công bố | $39–59/user/tháng (chính hãng) |
| TravelJoy | Form, hoá đơn, thanh toán, proposal, client app | Team và NCC yếu; không có API công khai | Chỉ Zapier (Premium, beta) | Không công bố | $19–39/tháng (chính hãng) |
| Lemax | Costing tour nhiều ngày, cổng B2B cho đối tác | Thiếu CRM đầy đủ (review) | SOAP | Không công bố | Không công bố (~$10k/user/năm, chưa kiểm) |
| Kaptio | Trên Salesforce, itinerary builder, multi-currency | Cho doanh nghiệp lớn, cần admin Salesforce | Theo Salesforce | Theo Hyperforce | ~€200/user/tháng (Capterra) |
| Tourplan NX | Back office DMC | CRM không rõ | hostConnect/accountConnect | Không công bố | $250–1.000/tháng (lệch nhau) |
| Rezdy / Bókun | Đặt tour ngày, phân phối OTA | Không phải CRM | Webhook ở gói cao | Không công bố | $49–499/tháng + % booking (chính hãng) |
| HubSpot | Pipeline, form, tracking; GDPR mode | Không hiểu tour/pax; sequence ở gói Pro | REST mọi gói; webhook theo app | Chọn vùng EU/AU/US | $7 và $20/seat (chính hãng, không ghi kỳ thanh toán); $15 năm / $20 tháng (bên thứ ba) |
| Zoho CRM / Bigin | Web-to-lead, cadence, quote ở Pro | Không hiểu tour | REST; webhook chỉ chiều ra | Chọn vùng theo domain | $14–52/seat; Bigin $7–18 (bên thứ ba) |
| Pipedrive | Pipeline-first | Không free; không hiểu tour | Webhook mọi gói | EU/AU/US, bị gán | $14–79/seat (bên thứ ba) |
| Salesforce | Đầy đủ; Partner Community | Đắt; PRM cần Enterprise | API thêm phí ở gói thấp | Hyperforce chọn vùng | $25–550/user/tháng (bên thứ ba) |

Nguồn + URL: [research/03 §Sources](research/03-market-benchmark.md) (truy cập 20/10/2026). "Chính hãng" = trang giá
của vendor; "bên thứ ba" = danh bạ/blog, thường lệch nhau.

Rút ra: công cụ du lịch mạnh itinerary/báo giá nhưng yếu CRM và im lặng về GDPR; CRM phổ thông có API và GDPR nhưng
không hiểu tour. **Không ai cung cấp sẵn nội dung itinerary** — đại lý phải tự gõ. Đó là lợi thế riêng của AA: lead đến
đã kèm tour/ngày/pax, proposal dựng từ tour master theo giọng thương hiệu tenant, giá chỉ báo từ giá net thật, và miễn phí
cho đối tác. 8 "table stakes" ở [03 §3](research/03-market-benchmark.md) được dùng làm tiêu chí nghiệm thu demo W3/W5.

## 5. Ba phương án kiến trúc cho sản phẩm hoàn chỉnh

Cả ba đều theo cùng spec; chỉ khác nơi đặt và mức tự xây. Chi phí là phần CRM **tăng thêm** mỗi tháng trên prod (USD),
chưa gồm prod nền ($150–300) và phí luật sư.

| | A. App thứ tư `AA-CRM` | B. Module trong AA-CIS-App | C. Tích hợp CRM sẵn có (HubSpot/Zoho/Pipedrive) |
|---|---|---|---|
| Nơi đặt | Repo + ECS service + REST API `api-crm` + schema `crm` riêng; UI đại lý là zone trong host portal; app khách riêng | Route trong process API CIS, job trên worker CIS, trang trong `portal/`; schema `crm` riêng, pool DB thứ hai | AA chỉ thu lead + đẩy sang CRM của đại lý; schema `crm` mỏng (integration_link, outbox, consent) |
| Tái dùng | Mẫu RLS/job/inbox/audit, portal host + kit, catalog, Booking pricing, TP map | Cao nhất: thêm CI, deploy, ECS, API GW của CIS | Intake + attribution; còn lại là của vendor |
| Chi phí/tháng ở 10 / 50 / 200 đại lý | $500–925 / $1,6–2,0k / $4,7–5,2k (Dev +$70–83) | $480–900 / $1,55–1,95k / $4,6–5,1k (Dev +$50–63) | AA $30–60 / $40–80 / $60–120; nếu AA trả seat cho đại lý: $450–700 / $2,3–3,5k / $9–14k |
| Số phiên tới hoàn chỉnh | ~16 (dải 14–16,5) | ~13–15 | ~3–4 (nhưng **không** phải sản phẩm trong spec) |
| Rủi ro chính | Thêm một bộ hạ tầng để vận hành; hợp đồng chéo repo (builder, B2B) có thể lệch | Phát hành CRM bị chặn khi CIS chạy wave (DM-11.4); task role CIS phải đọc secret `crm_app`; giải mã PII chung process với pipeline nội dung; migration CIS đang đóng băng tới X1 S22 | Không có proposal trên hàng AA, không riêng tư theo kiến trúc, không ops release, không insights; đại lý dùng Gmail + bảng tính thì không có CRM để đẩy vào |
| Tuân thủ | Tốt nhất: phụ lục kỹ thuật DPA sạch (role, khoá, audit tách khỏi AA) | Như A trên giấy, nhưng câu chuyện cách ly yếu hơn | AA tiếp xúc ít nhất (chỉ lead đang truyền), DPA ngắn; dữ liệu khách nằm ở vendor của đại lý |

Nguồn số liệu chi phí: [04 §3](research/04-economics-compliance-security.md); seat của C từ [03 §2](research/03-market-benchmark.md).
Chi tiết từng phương án: [options.json](research/options.json). Phương án A là bản workflow trả về; B và C được dựng ở bước
viết tài liệu từ các note research (output của các lane phương án khác không tới bước này).

## 6. Điểm giám khảo

Thang 1–5, trọng số cộng lại 100. **Lưu ý:** output panel giám khảo của workflow không tới bước viết tài liệu; điểm dưới
đây do tác nhân viết bản này chấm trên cùng dữ liệu research — coi là tham khảo, không phải panel độc lập
([judges.json](research/judges.json)).

| Tiêu chí (trọng số) | A | B | C |
|---|---|---|---|
| Phủ spec F1–F5, 1–18 và 3 điểm khác biệt (25) | 5 | 5 | 1 |
| Cách ly + tư thế processor + DPA (25) | 5 | 3 | 4 |
| Tái dùng, khớp luật/ADR hiện có (15) | 3 | 5 | 4 |
| Chi phí AA hằng tháng (10) | 3 | 3 | 4 |
| Công sức tới hoàn chỉnh (15) | 2 | 3 | 5 |
| Rủi ro vận hành (10) | 4 | 2 | 4 |
| **Tổng /100** | **79** | **74** | **68** |

## 7. Khuyến nghị

**Chọn A — `AA-CRM` là app thứ tư**, ghép thêm:

- **Từ B:** UI đại lý chạy trong host portal (multi-zone `/portal/crm`), dùng lại kit portal bằng byte-copy guard; giữ
  đúng key space `crm-NNN` và mục `owners.yaml` như ADR 0008 §8 đã định nên không phải đánh số lại.
- **Từ C:** module xuất `crm.integration_link` + outbox sang HubSpot/Zoho/Pipedrive (W7) cho đại lý đã có CRM riêng;
  đường thu lead + attribution (W3) dùng được ngay cả khi đại lý chưa dùng phần còn lại.
- **Từ benchmark:** 8 table stakes là tiêu chí nghiệm thu demo với đại lý pilot ở W3 và W5.

Lý do chọn A thay vì B: sản phẩm bán bằng lời hứa riêng tư; A giữ intake công khai, 6 nguồn webhook, giải mã KMS và
scrubber **ngoài** process/task role của CIS, có guard deploy riêng (`crm.job`) nên không bị wave nội dung CIS chặn, và
cho DPA một phụ lục kỹ thuật sạch. Giá phải trả: thêm khoảng 1 phiên dựng khung và ~$20/tháng trên Dev. Thay đổi so với
luật đã viết (ADR 0008 §8 "CIS module", DM-6.8 "không app AA nào đọc `crm.*`") cần ADR mới — bản nháp:
[research/adr-draft.md](research/adr-draft.md) (Proposed).

## 8. Kiến trúc chi tiết (phương án A)

### 8.1 Sơ đồ khối

```mermaid
flowchart LR
  subgraph Users["Người dùng"]
    AG["Đại lý: owner / agent / assistant"]
    TR["Khách của đại lý (không có tài khoản)"]
    AAOPS["AA ops / sales (Booking admin)"]
    AAMGT["AA management (CIS admin)"]
  end
  subgraph Vercel["Vercel"]
    PORTAL["portal host: CIS portal + zone /portal/crm (aa-crm-agent)"]
    CLIENT["clients host (aa-crm-client): form, proposal, client portal"]
    BUILDER["TripPlanner /builder"]
  end
  subgraph ACC2["AWS acc2 — ECS cluster dùng chung"]
    CRMAPI["aa-crm-dev-api + crm.job worker + Presidio sidecar"]
    CISAPI["aa-cis-dev-api"]
    BKAPI["aa-booking-dev-api (B2B API mới)"]
    KMS["KMS: 1 khoá mỗi đại lý (hoặc BYOK)"]
    S3["S3 aa-crm-docs (SSE-KMS)"]
    SES["SES inbound/outbound"]
    subgraph RDS["RDS dùng chung"]
      CRMDB["schema crm (crm_app, FORCE RLS)"]
      CAT["catalog.v_tenant_member, v_tour*, v_tenant_content_piece"]
      BKDB["booking.b2b_request, departure, b2b_traveller"]
    end
  end
  subgraph EXT["Bên ngoài"]
    COG["Cognito EXTERNAL (cis-portal)"]
    BED["Bedrock acc3, us. profile, ZDR none"]
    STRIPE["Stripe Connect Standard / cổng VN"]
    MSG["Meta WhatsApp Cloud API / Twilio SMS"]
    MAIL["Gmail / Microsoft Graph"]
    ESIGN["E-sign"]
  end
  AG --> PORTAL --> CRMAPI
  AG --> COG
  TR --> CLIENT --> CRMAPI
  AG --> BUILDER -->|builder token, crm.builder.v1| CRMAPI
  CRMAPI --> CRMDB
  CRMAPI -->|đọc view hợp đồng| CAT
  CRMAPI -->|IAM, giá/availability/hold| BKAPI --> BKDB
  BKDB -->|booking.v_b2b_status_outbox| CRMAPI
  CRMDB -->|crm.v_ops_release_outbox (đồng ý)| BKAPI
  AAOPS --> BKAPI
  CRMDB -->|crm.v_aa_insights_k10| CISAPI --> AAMGT
  CRMAPI --> KMS
  CRMAPI --> S3
  CRMAPI --> SES
  CRMAPI -->|scrub trước khi gọi| BED
  CRMAPI <--> STRIPE
  CRMAPI <--> MSG
  CRMAPI <--> MAIL
  CRMAPI <--> ESIGN
```

### 8.2 Mô hình dữ liệu (schema `crm`, chủ AA-CRM)

Mọi bảng tenant có `tenant_id NOT NULL`, FORCE RLS từ `crm-001`, mẫu NULLIF `TO crm_app` + WITH CHECK; không FK sang
schema khác; tour qua khoá mềm `(source_system, source_id)`; mọi cột PII có `COMMENT 'pii:<class>'` (thêm lớp
`pii:gov_id`, `pii:special`). Danh sách đầy đủ cột: [options.json](research/options.json) → `options[0].data_model`.

| Nhóm | Bảng chính |
|---|---|
| F4 tenancy | `tenant_settings` (key_mode, tiền tệ, ngôn ngữ, retention theo lớp), `member` (owner/agent/assistant, margin_visible), `support_grant`, `api_key` (chỉ hash) |
| F1 vault | `tenant_key` (ARN CMK hoặc BYOK, DEK/HMAC key đã bọc), `traveller` (các cột `_enc` AES-256-GCM + blind index email/phone/tên), `traveller_sensitive`, `document` (S3 SSE-KMS) |
| F2 ẩn danh | `profile` (`traveller_token` ngẫu nhiên, band, flag, sở thích — không có `traveller_id`); view `v_ai_trip_context`, `v_insight_facts` |
| Consent | `consent_event` append-only (contact, marketing, health_data, ops_release_to_aa, ai_processing, whatsapp_optin) |
| Pipeline | `trip`, `trip_stage_transition` + trigger, `trip_stage_history`, `trip_traveller`, `intake_submission`, `form_link` |
| Proposal | `proposal`, `proposal_day`, `option_block`, `option` (aa_ref hoặc supplier, requires/excludes, hold), `selection`, `proposal_link`, `builder_session` |
| Tiền + giao hàng | `supplier`, `booking_line`, `booking_line_cost` (RLS ẩn với assistant), `invoice`, `invoice_line`, `payment_schedule`, `payment`, `payment_account`, `commission_claim`, `signature_request` |
| Liên lạc | `channel_account`, `conversation`, `message` (`body_enc`), `message_template`, `saved_reply`, `internal_note` |
| Tự động + AI | `workflow_template`, `workflow_rule`, `task`, `ai_draft` (không lưu bản đồ placeholder) |
| Báo cáo / insights / xuất | `report_daily`, `insight_fact`, view `v_aa_insights_k10`, `export_job`, `erasure_request` |
| F5 audit | `access_event` (phân vùng theo tháng, chuỗi hash theo tenant) |
| Nền | `job`, `outbox` + view `v_ops_release_outbox`, `inbox_events`, `integration_link` |

Ngoài `crm`: **CIS** thêm `shared.tenant_members`, `shared.tenant_invitations` (AA-813), `catalog.v_tenant_member`,
`catalog.v_tenant`, `catalog.v_tenant_content_piece`, cấu hình route LLM `crm_*`. **Booking** thêm `b2b_request`,
`departure`/`allotment`, `b2b_traveller` (TTL 90 ngày), `v_b2b_status_outbox`. **TripPlanner** không thêm bảng (route
`/builder` chỉ là UI). **Infra** thêm mục `owners.yaml`, file roles `rl-`, Lambda cấp khoá KMS, bucket tài liệu, WAF.

### 8.3 F1–F5: riêng tư theo kiến trúc

| Module | Cách làm | Ai bị chặn, bằng gì |
|---|---|---|
| F1 Kho danh tính | Mã hoá từng trường AES-256-GCM ở tầng ứng dụng, DEK bọc bằng **khoá KMS riêng mỗi đại lý** (encryption context `tenant_id`), blind index HMAC để tìm chính xác, crypto-shred khi đại lý rời đi; tuỳ chọn BYOK (khoá trong AWS của đại lý) | Master DB chỉ thấy ciphertext; key policy chỉ cho task role CRM; CloudTrail báo động mọi Decrypt từ principal khác |
| F2 Profile ẩn danh | `traveller_token` ngẫu nhiên; liên kết danh tính↔token chỉ nằm ở `traveller.profile_token` | Role `crm_ai_reader`/`crm_insights` không có grant trên bảng vault — **DB chặn**, không dựa vào review code |
| F3 Scrubber | 3 lượt: thay giá trị danh tính đã biết của chính chuyến đi → Presidio (sidecar trong VPC, recognizer VN/hộ chiếu) → cổng regex còn sót, lỗi thì chặn; placeholder chỉ khôi phục trong phản hồi cho đại lý | Không có PII định danh trong prompt hay `llm_call_log`; bộ corpus EN/VI trong CI phải 0 rò |
| F4 Tenancy | Membership CIS (AA-813) là ranh giới; role CRM owner/agent/assistant; RLS biên lợi nhuận | Probe cách ly: `cis_app`, `booking`, `tripplanner` nhận 42501 trên `crm.*` (trừ 2 view hợp đồng) |
| F5 Audit | `access_event` ghi **trong cùng transaction** với mỗi lần đọc vault — ghi lỗi thì đọc lỗi; trang audit cho đại lý tự kiểm chuỗi hash + số Decrypt KMS | Đại lý tự thấy ai/cái gì đọc trường nào, vì sao |

**Câu chữ phải sửa:** spec F1 "*No access outside the agency, AA included*" không đúng khi khoá nằm trong account AA. Nói
đúng là "**chỉ runtime CRM dùng được khoá, mọi lần dùng đều ghi log; đại lý thu hồi được nếu dùng BYOK**". Cần chị Thư
đồng ý (§15, H3).

### 8.4 Tích hợp theo spec §9

| Spec §9 | Thiết kế | Hợp đồng |
|---|---|---|
| AA inventory API | Booking B2B API mới (giá net B2B + FX, availability theo departure/allotment, hold có hạn, yêu cầu đặt) gọi bằng IAM SigV4; trạng thái về qua `booking.v_b2b_status_outbox`. Tour tailor-made = "on request" | ADR 0005a, OpenAPI, `booking.b2b_status.v1` |
| Visual itinerary builder | TripPlanner `/builder` (bản đồ Mapbox, route planner, gợi ý trên `catalog.v_graph_node` / `catalog.v_graph_edge`, hợp đồng `catalog.graph.v1`) — chỉ UI; dữ liệu nằm ở `crm.*` | `crm.builder.v1`, builder token ký bằng KMS, khoá chỉnh sửa đồng thời |
| Stripe | Connect **Standard**: đại lý là merchant of record, AA trả $0; Checkout pay link; webhook ký + idempotent; hoàn tiền (refund) và đa tiền tệ theo spec §9. **Stripe không hỗ trợ Việt Nam** → cổng VN (OnePay/2C2P/9Pay, cần báo giá) hoặc ghi nhận thủ công | — |
| Gmail / Outlook | Outlook qua Graph; Gmail đồng bộ hai chiều cần scope restricted → CASA hằng năm; đường dự phòng `gmail.send` + chuyển tiếp vào SES inbound (không CASA) | — |
| Twilio / 360dialog | WhatsApp Embedded Signup: mỗi đại lý sở hữu WABA, trả Meta trực tiếp; Cloud API trực tiếp (Tech Provider) hoặc Twilio làm BSP; tránh 360dialog ($49/số/tháng, [research/04 §2.4](research/04-economics-compliance-security.md) → docs.360dialog.com/docs/pricing, truy cập 20/10/2026). SMS qua Twilio. Messenger và Instagram (spec §7 `Conversation.channel`) qua Meta Graph API, dùng chung xác minh Meta với WhatsApp (D19) | — |
| E-sign | BoldSign ($30/tháng gồm 40 phong bì, sau đó $0,75/phong bì; có vùng AU/EU — [research/04 §2.5](research/04-economics-compliance-security.md) → boldsign.com/pricing, truy cập 20/10/2026) — đổi sang Documenso Platform khi > ~30 đại lý | — |
| LLM | Bedrock acc3 qua gateway, profile `us.`, model cho phép retention `none` (không Fable 5/5.1), SCP ép ZDR; loại OpenAI và Jev khỏi route CRM | ADR 0009 (đã giữ số, AA-804) |

### 8.5 Luồng chính (tóm tắt)

Đại lý được mời (AA-813) → vào `/portal/crm` lần đầu thì tạo `tenant_settings` + cấp khoá KMS → khách điền form (nhúng,
link CTA thay `mailto`, có attribution) → lead lên board → agent mở trip, gửi form Stage 2 → dựng proposal trong
`/builder`, giá qua Booking B2B → khách chọn/đổi/chấp nhận không cần đăng nhập → đặt hold ở Booking → thanh toán cọc
(Stripe/cổng VN) → Booked, mở Stage 3 (hộ chiếu, e-sign waiver) → "Release to AA ops" có đồng ý → Booking giữ bản sao,
xoá sau 90 ngày và báo lại → báo cáo, insights k≥10, xuất/xoá. Chi tiết từng bước:
[options.json](research/options.json) → `options[0].flows`.

## 9. Bảng phủ spec

Số phiên là ước lượng từ dưới lên ở nhịp 8–10 issue/phiên. Module F1–9: theo lane phương án; 10–18 và các hạng mục
chung: ước lượng ở bước viết tài liệu (phần đó của lane bị cắt).

| Module | Xây ở đâu | Tái dùng | Phiên |
|---|---|---|---|
| F1 Kho danh tính | AA-CRM (vault, `traveller`, `tenant_key`, `document`) + Infra (Lambda cấp khoá KMS, bucket SSE-KMS, báo động Decrypt) | Mẫu envelope KMS; quy tắc prefix secret DM-8.6 | 0,6 |
| F2 Profile ẩn danh | AA-CRM (`profile`, view) + Infra (role NOLOGIN trong file `rl-`) | Mô hình role X1, `SET LOCAL ROLE` của DB Migrate | 0,25 |
| F3 Scrubber | AA-CRM (sidecar Presidio, `scrub()`/`restore()`, corpus CI) | Quy ước `llm_call_log`; DM-6.4 | 0,5 |
| F4 Tenancy | AA-CIS-App (AA-813, `v_tenant_member`) + AA-CRM (role, RLS biên lợi nhuận, support grant) + Infra (owners.yaml, role, connection limit) | ADR 0006 QĐ3, pool fail-closed AA-544, RLS 229/241, probe aa817 | 1,25 (gồm AA-813 ~0,75) |
| F5 Audit | AA-CRM (`access_event`, verifier, trang audit, archive Parquet) | Thiết kế CIS 248 | 0,4 |
| 1 Form intake | AA-CRM (API công khai, script nhúng, form host) + CIS (view attribution, sửa CTA `/trip`) + Infra (WAF) | Inbox idempotent Booking; `default_cta`; `content_piece`/`publish_log` | 0,5 |
| 2 Pipeline | AA-CRM (bảng chuyển trạng thái + trigger, board, panel Traveller info, cổng 80%) | Mẫu bk-003; kit portal | 0,6 |
| 3 Proposal tương tác | TripPlanner (`/builder`) + AA-CRM (builder API, mô hình option, trang chọn cho khách) + Booking (B2B API, departure/allotment) | Bản đồ + route planner TP, `catalog.graph.v1`; engine giá Booking, `fx_rates` | 1,6 |
| 4 Proposal dạng chữ | AA-CRM (render cùng version ra email/WhatsApp) | Dữ liệu module 3 | 0,2 |
| 5 Inbox email | AA-CRM (Graph, Gmail sau CASA, SES inbound) + Infra (SES rule set) | SES đã dùng; UX `tenant_integrations`; `safe_http` (AA-875) | 0,8 |
| 6 Sổ booking | AA-CRM (`booking_line`, `booking_line_cost`) + Booking (`v_b2b_status_outbox`) | Quy tắc outbox → pull → inbox | 0,4 |
| 7 Hoá đơn + thanh toán | AA-CRM (Stripe Connect, adapter cổng VN, thủ công, nhắc) | Ý tưởng `deposit_pct`, FX Booking; chưa có cổng thanh toán nào trong hệ | 0,8 |
| 8 AA ops release | AA-CRM (outbox có đồng ý, UI) + Booking (pull, `b2b_traveller`, TTL 90 ngày, sự kiện đã xoá) | Mẫu outbox TP→Booking; job xoá 90 ngày của Booking | 0,5 |
| 9 Inbox WhatsApp/SMS/Messenger/IG | AA-CRM (Embedded Signup, Cloud API/Twilio, template, cửa sổ 24h, hàng đợi số lạ; Messenger + Instagram qua Meta Graph API) | Mẫu inbox webhook; blind index số điện thoại | 0,8 |
| 10 Tự động hoá | AA-CRM (rule theo stage, nhắc khi im lặng, T-21, tự gửi Stage 2, mẫu task) | `crm.job` (ADR 0003a) | 0,5 |
| 11 Client portal | AA-CRM client app (một link: proposal, Stage 3, tài liệu, hoá đơn, itinerary) | Link ký có hạn (DM-6.9) | 0,4 |
| 12 Hợp đồng + waiver | AA-CRM (tích hợp e-sign, lưu PDF đã ký) | `crm.document`, inbox webhook | 0,3 |
| 13 Hoa hồng | AA-CRM (dự kiến vs đã nhận, cờ quá hạn) | `booking_line_cost` | 0,2 |
| 14 AI agent | AA-CRM (nháp trả lời/proposal/follow-up, UI duyệt, tỉ lệ sửa) + CIS (cấu hình route `crm_*` trên gateway) | Model Gateway, `llm_call_log`, AA-820 | 0,8 |
| 15 Danh bạ NCC | AA-CRM (`supplier`; AA là mặc định) | Mô hình option module 3 | 0,3 |
| 16 Báo cáo đại lý | AA-CRM (`report_daily`, trang báo cáo) | Kit DataTable/csv | 0,4 |
| 17 AA insights | AA-CRM (rollup k≥10, view) + CIS (trang admin) | Luật "tenant chỉ thấy nội dung" (QA ở admin) | 0,3 |
| 18 Mang dữ liệu đi | AA-CRM (xuất CSV/JSON, xoá khách có DRY RUN, offboarding + crypto-shred, runbook) | Quy trình DRY RUN `destructive-ops` | 0,5 |
| Chung: ADR, hợp đồng, spec gap 1–7 | Repo gốc | ADR 0008, `docs/contracts/` | 1,0 |
| Chung: khung repo + hạ tầng app | AA-CRM + Infra | Mẫu Booking (ADR 0004/0004b) | 0,5 |
| Chung: onboarding/import | AA-CRM | CSV kit | 0,3 |
| Chung: NFR theo spec gap 6 (i18n EN/VI, tiền tệ, múi giờ, mobile, SLO hiệu năng + uptime kèm alarm, event tracking) | AA-CRM + Infra | FX Booking; alarm CloudWatch sẵn có | 0,6 |
| Chung: prod, review bảo mật, pilot | Infra + AA-CRM + gốc | AA-880, AA-855 | 1,0 |
| **Tổng** | | | **≈16,3** |

## 10. Kế hoạch xây theo đợt (toàn bộ module, không cắt)

| Đợt | Phạm vi | Phiên | Thoát đợt khi |
|---|---|---|---|
| W0 Quyết định, hợp đồng, khởi động việc ngoài | ADR 0010/0011/0005a/0006b + ADR Infra KMS; sửa DM-6.1/6.8; 4 hợp đồng JSON; spec gap 1–7; mở **mọi** quy trình bên ngoài (bảng dưới) | 1 | ADR được duyệt; mỗi việc ngoài có ticket, người phụ trách, ngày |
| W1 Điều kiện nền + khung app | AA-813; X2 phủ `crm`; owners.yaml + role; repo AA-CRM + CI; ECS/REST API/SG/secret; `crm-001`; probe; 2 project Vercel | 1,5 | `/crm/health/ready` 200 trên Dev; probe 0 dòng chéo tenant; người không có membership bị từ chối |
| W2 Nền riêng tư F1–F5 | Lambda KMS + báo động; vault; F2; consent; scrubber + corpus; audit; RLS biên lợi nhuận; lint `pii:`; TTL | 1,5 | Master chỉ thấy ciphertext; `crm_ai_reader` nhận 42501 trên vault; corpus 0 rò; shred khoá test → không giải mã được |
| W3 Bán một chuyến (1–4 + onboarding) | Intake + WAF + attribution + sửa CTA; board; Stage 2; import CSV; Booking B2B API + availability + hold; TP `/builder`; trang proposal cho khách; proposal dạng chữ | 2,5 | Một ngày làm việc trên Dev bằng dữ liệu giả: lead → proposal từ tour AA, giá qua B2B, khách đổi + chấp nhận, hold hiện ở Booking admin |
| W4 Inbox email (5) | Outlook; SES inbound + `gmail.send`; Gmail hai chiều sau cờ; threading; ghi chú | 1 | Outlook + chuyển tiếp chạy với mailbox test; Gmail chỉ bật khi có thư LOA của Google |
| W5 Thu tiền + giao (6, 7, 8, 12, 13) | Sổ booking; hoá đơn; Stripe Connect (pay link, hoàn tiền, đa tiền tệ); cổng VN/thủ công; ops release + xoá 90 ngày; e-sign; hoa hồng | 1,5 | Cọc test Stripe → Booked; waiver đã ký được lưu; ops release tới Booking, xoá có báo lại |
| W6 Tự động (9, 10, 14) | WhatsApp + SMS + Messenger/IG; workflow; lớp AI qua scrubber + Bedrock ZDR | 1,7 | WhatsApp chạy trên WABA test (sau Meta); nháp AI không có danh tính trong log/prompt; không gửi khi chưa duyệt |
| W7 Trải nghiệm + quy mô (11, 15–18) + NFR | Client portal; NCC; báo cáo; insights k≥10 + trang admin CIS; xuất/xoá/offboarding; trang dữ liệu công khai; xuất sang HubSpot/Zoho; i18n, tiền tệ, múi giờ, mobile; SLO hiệu năng/uptime + alarm; event tracking | 1,6 | Xuất → xoá → kiểm đúng ngay lần đầu; insights không có nhóm n<10; client portal chạy trên điện thoại |
| W8 Prod, review bảo mật, pilot | Phần CRM của AA-880; probe prod; pen test/review độc lập; hồ sơ CASA; review quyền; DPA ký; 3–5 đại lý; video UAT; nộp TIA VN nếu luật sư xác nhận | 1–1,5 | Đại lý pilot chạy prod với dữ liệu thật dưới DPA đã ký; không có PII thật trên Dev |
| Dự phòng | Tích hợp chéo repo, sửa sau verify | 1–2,5 | — |
| **Tổng** | | **≈14,3–16,3** | |

Phụ thuộc theo thứ tự: W1 cần AA-813 + X2; W2 trước mọi dữ liệu khách; W3 cần Booking B2B + hợp đồng builder; W6 (AI)
cần F3, F5, 5 và 9; module 17 chỉ có ý nghĩa sau 3–6 tháng dữ liệu pilot.

**Đổi so với spec — thời điểm pilot:** spec đặt pilot 3–5 đại lý ở cuối Phase 2 (tuần 22), trước phần tự động hoá. Bản
này dời pilot xuống W8, sau mọi module, vì pilot dùng dữ liệu khách thật nên cần prod (AA-880, C7.1a cấm PII thật trên
Dev), DPA đã ký và review bảo mật — các việc đó gom ở W8. Đại lý pilot vẫn thấy sản phẩm sớm qua demo trên dữ liệu giả ở
W3 và W5. Nếu muốn pilot sớm như spec: kéo phần prod + DPA + review bảo mật của W8 lên ngay sau W5, rồi chạy W6–W7 khi
pilot đang chạy (cần Nghiệp chọn khi đặt ngày go-live, D13).

### Phụ thuộc bên ngoài có thời gian chờ — khởi động ngay W0, chạy song song

| Việc | Thời gian chờ | Chi phí | Chặn cái gì nếu trễ |
|---|---|---|---|
| Google: xác minh thương hiệu + scope restricted + CASA | Vài tuần (+2–3 ngày brand); **làm lại mỗi 12 tháng** | $675–5.400/năm (bên thứ ba) | Chỉ Gmail hai chiều (W4); đường chuyển tiếp chạy trước |
| Microsoft publisher verification | Ngày → tuần (chưa rõ) | ~$0 (chưa kiểm) | Outlook ở tenant M365 chặn user consent |
| Meta: xác minh doanh nghiệp + Tech Provider + duyệt template WhatsApp | 2–4 tuần | $0 phí Meta (chưa kiểm) | WhatsApp (W6) |
| Insurer duyệt waiver ký điện tử | Chưa rõ | Chưa rõ | Tiêu chí "insurer chấp nhận" của module 12 |
| Luật sư: DPA, SCC Module 2 (+ flow-down Module 3) / UK Addendum, PDPL VN (DPIA, TIA, **có thể cần Giấy chứng nhận đủ điều kiện + pháp nhân VN**), APP 8 Úc, thoả thuận đối tác chống lôi kéo khách | Chưa rõ; TIA VN nộp trong 60 ngày từ lần chuyển đầu | Chưa có báo giá | Pilot với dữ liệu thật; đại lý VN có thể phải chờ |
| Stripe Connect platform profile | Vài ngày | $0 | Thanh toán AU/EU (W5) |
| Cổng thanh toán VN (OnePay / 2C2P / 9Pay) | Chưa rõ | Chưa có báo giá | Thanh toán online cho đại lý VN; tạm ghi nhận thủ công |
| Vendor e-sign: DPA + vùng dữ liệu | Vài ngày | $30/tháng gồm 40 phong bì, sau đó $0,75/phong bì (BoldSign) | W5 |
| Vercel Pro (D-18) | Ngay | $20/seat/tháng | Đại lý dùng portal (Hobby cấm thương mại) |
| Môi trường prod (AA-880 / ADR 0012) | Vài phiên | ~$150–300/tháng | Toàn bộ pilot (C7.1a) |
| Tuyển 3–5 đại lý pilot + phỏng vấn | Theo chị Thư | — | Phản hồi sản phẩm từ demo W3 |

Nguồn + URL: [research/04 §2, §3.4](research/04-economics-compliance-security.md) (BoldSign → boldsign.com/pricing; CASA,
Meta, Stripe, Vercel theo nguồn ghi trong note), [research/03 §Sources](research/03-market-benchmark.md); truy cập 20/10/2026.

## 11. Issue Linear đề xuất theo đợt (CHƯA tạo — chờ Nghiệp duyệt D16)

114 issue, tên tiếng Anh như sẽ tạo trên Linear. `[root]` repo gốc, `[CRM]` AA-CRM, `[CIS]`, `[BK]` Booking, `[TP]`, `[Infra]`.
Issue đã có: AA-813, AA-880, AA-886, AA-855, AA-873/875/876/877 — cập nhật mô tả thay vì tạo trùng. AA-848 (X2) đã
**Done** trên Linear (đọc 20/10/2026), nên phần phủ `crm` (W1 #4) là issue mới.

**W0 (9)**
1. [root] ADR 0010 AA-CRM app and integration
2. [root] ADR 0011 tenant traveller data protection (keys, vault/profile, scrubber, audit, crypto-shred, F1 wording)
3. [root] ADR 0005a Booking B2B channel: price, availability/hold, requests, ops release
4. [root] ADR 0006b CRM roles (owner/agent/assistant) and traveller signed links
5. [Infra] ADR: per-agency KMS key provisioner
6. [root] Data standards amendment: pii:gov_id, pii:special, DM-6.8 contract exceptions, X1 wording fix
7. [root] Contracts crm.ops_release.v1, booking.b2b_status.v1, crm.insights.v1, crm.builder.v1 + Booking B2B OpenAPI
8. [root] CRM spec gaps 1–7: G/W/T stories (module 3 first), edge cases, day-in-the-life, mockups, event plan, NFRs
9. [root] External-process tracker: Google/CASA, Microsoft, Meta, Stripe Connect, VN gateway, e-sign, insurer, counsel (incl. the partner agreement with a no-poaching clause, spec non-code track phase 1), Vercel Pro, pilot agencies

**W1 (13)**
1. [CIS] AA-813 rescope + build: Cognito invitations, shared.tenant_members, shared.tenant_invitations (existing issue)
2. [CIS] catalog.v_tenant_member and catalog.v_tenant views + grants to crm_app
3. [CIS] Tenant user sign-in on cis-portal + re-run the N7 probe (007b default ACL already gone in the 20/10 dump)
4. [Infra] Extend the X2 guard (AA-848, Done) to cover the crm schema (new issue)
5. [Infra] owners.yaml crm entry + runner, copy-guard and probe mirrors
6. [Infra] rl- roles: crm_owner, crm_app (limit 10), crm_ai_reader, crm_insights, crm_staff + C2.2 budget offset
7. [CRM] Repo bootstrap: FastAPI + asyncpg, CONTEXT.md, CI (tests, migration lint, PG15 replay, copy guard)
8. [Infra] ECR, ECS service + task def, per-app SG, REST API api-crm, ALB /crm/*, OIDC deploy role, App=crm tags, budget, alarms
9. [CRM] crm-001: schema, tenant_settings, member, support_grant, api_key, crm.job, retention rows
10. [CRM] Auth middleware: JWKS + v_tenant_member + crm.member role, fail closed
11. [Infra] Isolation probe: crm cells (own/foreign/forged/empty GUC; other app roles get 42501)
12. [CRM] Vercel projects aa-crm-agent (portal multi-zone) and aa-crm-client + UI kit byte-copy guard
13. [CIS] Portal rewrites + navigation entry for /portal/crm

**W2 (13)**
1. [Infra] KMS key-provisioner Lambda + key policy template + Decrypt alarm (extends AA-873)
2. [CRM] tenant_key lifecycle: provision, rotate, BYOK validate, shred
3. [CRM] Vault library: AES-256-GCM + AAD, DEK cache, HMAC blind indexes, re-encrypt job
4. [CRM] traveller, traveller_sensitive, trip_traveller (F1)
5. [Infra] S3 docs bucket with per-tenant SSE-KMS + crm.document
6. [CRM] F2 profile + v_ai_trip_context + v_insight_facts + role grants
7. [CRM] Append-only consent ledger crm.consent_event
8. [CRM] F3 Presidio sidecar + scrub()/restore() + residual gate
9. [CRM] F3 EN/VI synthetic leak corpus in CI (0-leak gate)
10. [CRM] F5 access_event: monthly partitions, per-tenant hash chain, verifier
11. [CRM] Agency audit page: events, chain verify, KMS Decrypt counts
12. [CRM] Margin RLS (app.crm_margin), CRM roles, support-grant flow
13. [CRM] pii: lint for crm migrations + TTL jobs with DRY RUN first run

**W3 (22)**
1. [CRM] Public intake API (form_key, Idempotency-Key, bot check, honeypot)
2. [Infra] WAF rate limits on api-crm public routes (extends AA-876)
3. [CRM] Embed script + hosted Stage 1 form
4. [CRM] Tenant server-to-server lead API (crm.api_key)
5. [CIS] catalog.v_tenant_content_piece attribution view
6. [CIS] /trip/[tourId] CTA points to the tenant form (replace the hardcoded mailto)
7. [CRM] trip + stage transition table + trigger + history
8. [CRM] Pipeline board UI
9. [CRM] Trip view, Traveller-info panel, 80% completeness gate + override log
10. [CRM] Stage 2 form links + auto-send rule
11. [CRM] Repeat-traveller match and prefill by blind index
12. [CRM] CSV import/export + first-run onboarding wizard + team invites
13. [BK] B2B price list + quote endpoint (pricing_rules b2b + FX), IAM auth
14. [BK] departure / allotment availability model
15. [BK] b2b_request + holds with expiry + staff admin view
16. [BK] booking.v_b2b_status_outbox (booking.b2b_status.v1)
17. [CRM] Booking B2B client + crm_b2b_status_pull + inbox_events
18. [CRM] Builder API crm.builder.v1 + KMS-signed builder token + edit lock
19. [TP] /builder route on the builder token (map + route planner)
20. [CRM] Proposal model: proposal, day, option_block, option, selection, link
21. [CRM] Client interactive proposal page: keep/swap/request, dependency rules, live price, unavailable options
22. [CRM] Text proposal renderer (email / WhatsApp short form)

**W4 (8)**
1. [CRM] channel_account, conversation, message (encrypted bodies)
2. [CRM] Outlook Graph connect + change notifications + sync
3. [Infra] SES inbound rule set + per-agency forwarding address
4. [CRM] SES-inbound forwarding ingest + gmail.send sending
5. [CRM] Gmail restricted-scope two-way sync behind a flag (watch + crm_mail_sync)
6. [CRM] Threading to traveller/trip + unified inbox UI
7. [CRM] Saved replies + internal notes
8. [CRM] Attachments to crm.document through safe_http (AA-875)

**W5 (13)**
1. [CRM] Bookings ledger UI: AA lines from status events + manual lines
2. [CRM] Invoice + payment schedule from the accepted proposal
3. [CRM] Stripe Connect Standard onboarding + payment_account
4. [CRM] Stripe Checkout pay links + signed idempotent webhook → stage booked + refunds + multi-currency (spec §9)
5. [CRM] VN payment gateway adapter + manual payment recording
6. [CRM] Payment reminders (crm_payment_reminder)
7. [CRM] Ops release UI + consent check + crm.v_ops_release_outbox
8. [BK] bk_crm_ops_release_pull + booking.b2b_traveller (pii tags, retention row)
9. [BK] bk_b2b_traveller_purge 90 days after return + purge event + early purge on erasure
10. [CRM] Purge confirmation display + outbox redaction after 90 days
11. [CRM] E-sign integration (terms + waiver), signed PDF to crm.document
12. [CRM] Stage 3 unlock + pre_departure transition rules
13. [CRM] Commission expected vs received + overdue flags

**W6 (13)**
1. [CRM] WhatsApp Embedded Signup + per-agency WABA connect
2. [CRM] WhatsApp inbound webhook (signature), phone match, unmatched queue
3. [CRM] Template sync + approval status + 24-hour window enforcement
4. [CRM] SMS via Twilio
5. [CRM] Workflow engine: stage rules, idle nudges, task templates
6. [CRM] T-21 Stage 3 nudge + Stage 2 auto-send rule set
7. [CIS] Gateway: crm_* stages on Bedrock acc3 us. profile, ZDR none + SCP, no OpenAI/Jev
8. [CRM] AI draft service: crm_ai_reader context + scrub + gateway + restore
9. [CRM] AI draft approval UI + edit-ratio metric + send only on human action
10. [CRM] AI proposal and follow-up drafts
11. [CRM] AA-820 AI disclosure on traveller-facing surfaces
12. [CRM] Leak audit of AI drafts on synthetic threads
13. [CRM] Facebook Messenger + Instagram inbox via the Meta Graph API (spec §7 channels; webhook signature, unmatched queue)

**W7 (14)**
1. [CRM] Client portal (proposal, Stage 3, documents, invoices, itinerary)
2. [CRM] Supplier directory (AA default + agency suppliers, mixed trips)
3. [CRM] Agency reports (conversion by stage, margin, lead source, option picks)
4. [CRM] Insights rollup k≥10 + complementary suppression + v_aa_insights_k10
5. [CIS] Admin page: CRM insights (k≥10) + CRM health counts
6. [CRM] Full export (CSV/JSON zip, 7-day presigned link)
7. [CRM] Traveller erasure (DRY RUN, F1 delete, redaction, Booking early purge, verified_at)
8. [CRM] Tenant offboarding: export, hard delete, ScheduleKeyDeletion + runbook
9. [CRM] integration_link export to HubSpot / Zoho / Pipedrive
10. [CRM] i18n EN/VI + time zones + currencies AUD/USD/VND/EUR via Booking FX
11. [CRM] Mobile-first pass on agent and client apps
12. [CRM] Event tracking + metrics dashboard for every spec success metric
13. [root] Public plain-language data page for agencies
14. [Infra] Performance and uptime SLOs for api-crm and both UIs + CloudWatch alarms (spec gap 6)

**W8 (9)**
1. [Infra] CRM slice of the AA-880 prod blueprint (RDS, KMS, WAF, Vercel prod, Sentry without PII)
2. [Infra] Prod isolation probe + X2 on prod
3. [CRM] Independent security review / pen test + fixes
4. [CRM] CASA evidence pack + Google Letter of Assessment
5. [root] Access review incl. crm_* roles and KMS key policies (DM-8.10)
6. [root] DPA + terms + partner agreement (no-poaching clause) + sub-processor annex signed per pilot agency (extends AA-886)
7. [CRM] Pilot onboarding of 3–5 agencies (runbook + support)
8. [root] CRM part of the UAT videos (AA-855)
9. [root] VN DPIA / TIA filing (if counsel confirms)

Hạn mức Linear: 114 issue vượt một project (≤100 chưa lưu trữ) → cần project mới "AA-CRM" (hoặc hai, theo đợt); tạo
issue theo từng đợt khi bắt đầu đợt đó.

## 12. Điều kiện tiên quyết

1. **AA-813** (Backlog): viết lại theo ADR 0006 Phase 3 rồi xây — ranh giới F4, không có dữ liệu CRM nào trước nó.
2. **AA-848 X2** (Done trên Linear, đọc 20/10/2026): mở rộng X2 phủ schema `crm` (FORCE, NULLIF, không PUBLIC, `rolconnlimit`) bằng issue mới W1 #4.
3. **N7 / AA-817** (Done): phần default ACL 007b tới `aa_app_user` **đã kiểm trong dump 20/10** (`db-schema-reference.md` mục Default privileges không còn dòng nào tới `aa_app_user`). Còn mở: probe lại không runtime role nào có `pg_read_all_data`/BYPASSRLS.
4. **Ngân sách kết nối** (AA-824 Done): thêm dòng `crm_app` vào C2.2 kèm bù trừ (ví dụ hạ `booking` từ mức live 15 xuống mục tiêu C2.2 là 10, hoặc bù ở role khác), nếu không thì t4g.medium (~+$31/tháng Dev). Tổng LOGIN limit live (dump 20/10): 155 = `aa_app_user` 15 + `booking` 15 + `cis_app` 90 + `db_migrator` 5 + `tripplanner` 30, trên `max_connections` 181 (`03-scaling.md:125`).
5. **AA-880 + ADR 0012** (Backlog): điều kiện cứng của pilot; Nghiệp đặt ngày go-live.
6. **AA-886** (In Progress): mở rộng cho DPA CRM, phụ lục sub-processor, SCC, điều khoản xoá 90 ngày.
7. **AA-681** (Done): đủ cổng "Booking báo giá được" của ADR 0005 QĐ9; vẫn phải xây B2B API + availability/hold.
8. **AA-873, AA-875, AA-876, AA-877** (Backlog): xong trước khi intake công khai, link proposal và webhook lên (W3/W5).
9. **ADR 0009** (đã giữ số, AA-804): ghi luật route AI cho CRM (`us.`, ZDR qua SCP, không Fable 5/5.1, không OpenAI/Jev).
10. **Vercel Pro (D-18)** trước khi đại lý đầu tiên dùng portal.
11. **Thứ tự với M1:** backlog đang ghi AA-821 "After M1"; quyết định S245 đổi điều này — xác nhận phần M1 không nằm trên đường CRM chạy song song (D3).
12. **Linear + backlog:** project mới + cập nhật Done-when của AA-821 theo quyết định "sản phẩm hoàn chỉnh"; sửa luôn dòng AA-821 ở `docs/backlog/README.md:123` (đang ghi "research + phased MVP plan … After M1", trái với quyết định không MVP và với D3).

## 13. Chi phí

**Một lần:** CASA $675–5.400 (rồi lặp mỗi năm); xác minh Microsoft, Meta, Stripe ~$0; pen test chưa có báo giá; luật
sư VN + AU/EU chưa có báo giá (DPA, SCC, DPIA/TIA, ý kiến về giấy phép VN, thoả thuận đối tác); đại diện EU Art. 27 nếu
cần: chưa rõ.

**Hằng tháng — Dev (tăng thêm):** ~$70–83 (task API ~$21, sidecar Presidio ~$39–49, KMS ~$5, secret ~$1,6, log/alarm ~$3–5, S3 + API Gateway < $1).

**Hằng tháng — prod (phần CRM tăng thêm):**

| | 10 đại lý | 50 đại lý | 200 đại lý |
|---|---|---|---|
| Biến đổi (~$18,7/đại lý: WhatsApp qua Twilio ~5, SMS ~3, LLM Sonnet ~8,4, KMS 1–3, SES ~0,3) | ~187 | ~935 | ~3.740 |
| E-sign | 75 (BoldSign) | 250 (Documenso) | 250 |
| Compute | 111 | 222 | 395 |
| RDS tăng thêm | ~0 | +63 | +188 (+ lưu trữ) |
| Vercel Pro | 40–60 | 60 | 60–100 |
| CASA chia tháng | 56–450 | 56–450 | 56–450 |
| Bảo mật nền / WAF | 25–40 | 25–40 | 25–40 |
| **Tổng** | **≈ $500–925** | **≈ $1,6k–2,0k** | **≈ $4,7k–5,2k** (~$24–26/đại lý) |

Nguồn + URL: [research/04 §3](research/04-economics-compliance-security.md) (giá AWS us-west-1 và trang giá vendor, truy cập
20/10/2026).

Chưa gồm: prod nền ~$150–300/tháng; phí đại lý tự trả (Stripe, Meta nếu đại lý sở hữu WABA); luật sư. Đòn bẩy: Haiku
thay Sonnet −$8/đại lý; WABA của đại lý trên Cloud API trực tiếp −$3–5/đại lý; đường Gmail chuyển tiếp tránh CASA. Nếu
"miễn phí cho đối tác", AA gánh ~$4,7–5,2k/tháng ở 200 đại lý. Nếu đại lý tự trả WhatsApp và SMS (Stripe chưa bao giờ là
chi phí của AA: Connect Standard $0), phần AA còn lại là LLM 1.680 + KMS 200–600 + SES 60 + compute 395 + RDS 188 + Vercel
60–100 + WAF 25–40 ≈ **$2,6–3,1k**; cộng e-sign 250 và CASA 56–450 mà AA vẫn gánh thì ≈ **$2,9–3,8k**. (Con số ~$2,5k ở
[research/04 §3.3](research/04-economics-compliance-security.md) thấp hơn thực tế; dùng số ở đây.) Mọi dịch
vụ AWS mới (KMS, SES inbound, Lambda, WAF) cần Nghiệp duyệt báo giá này (DM-10.7); gắn tag `App=crm`.

## 14. Tuân thủ + DPA

- **Vai trò:** đại lý là controller, AA là processor cho `crm.*` (DM-6.8). Với bản sao ops release (module 8), Booking là
  controller hay processor theo chỉ dẫn — luật sư quyết, DPA phải ghi rõ cùng điều khoản xoá 90 ngày + xác nhận đã xoá.
- **GDPR (đại lý EU/UK):** điều khoản Art. 28; chuyển dữ liệu ra ngoài EU gồm ba chặng: SCC Module 2 cho đại lý (EU) →
  AA (lưu ở Mỹ); flow-down Module 3 / điều khoản tương đương cho chuyển tiếp sang sub-processor (AWS và các bên khác theo
  DPF hoặc SCC riêng của họ); và việc nhân viên AA truy cập từ Việt Nam (nước chưa có quyết định đầy đủ). Ai là exporter /
  importer còn tuỳ pháp nhân của AA ở nước nào (H5, chưa biết) — luật sư chốt sau H5. UK: IDTA/Addendum. Bằng chứng Art. 32
  (mã hoá, RLS, audit, review quyền); đồng ý rõ ràng Art. 9 cho cờ sức khoẻ/vận động/ăn uống; yêu cầu chủ thể qua module
  18; runbook hỗ trợ khi rò rỉ; danh sách sub-processor có báo trước khi đổi. Hỏi luật sư: đại diện Art. 27, sổ Art. 30(2).
- **PDPL Việt Nam** (Luật 91/2025/QH15 + Nghị định 356/2025, hiệu lực 01/01/2026): hợp đồng xử lý có nội dung bắt buộc;
  DPIA cho cả processor; **TIA nộp trong 60 ngày** từ lần chuyển dữ liệu ra nước ngoài đầu tiên (us-west-1); AA
  **không** được hưởng ân hạn doanh nghiệp nhỏ, trước hết vì AA là bên **cung cấp dịch vụ xử lý dữ liệu cá nhân** (theo
  các bản tóm tắt thứ cấp của Điều 38), và thêm vì CRM giữ dữ liệu nhạy cảm (sức khoẻ, tài chính; ảnh giấy tờ có phải dữ
  liệu nhạy cảm theo Nghị định 356 hay không: luật sư xác nhận); cấm ô đồng ý tick sẵn;
  **có thể phải có Giấy chứng nhận đủ điều kiện và pháp nhân VN** cho dịch vụ "cung cấp hệ thống xử lý dữ liệu cá nhân
  cho bên kiểm soát". Phải có ý kiến luật sư trước khi đại lý VN nào lưu dữ liệu. Chưa có ở đâu theo dõi việc này.
- **Privacy Act Úc:** viết DPA đạt phép thử APP 8 "use, not disclosure" cho cloud nước ngoài (giới hạn mục đích, ràng
  buộc nhà thầu phụ, đại lý giữ quyền kiểm soát); các APP (kể cả APP 8, APP 11) + NDB chỉ áp cho đại lý là APP entity (doanh thu > A$3M,
  hoặc thuộc ngoại lệ như kinh doanh thông tin cá nhân hay tự chọn tham gia); bản thân AA cũng có thể là APP entity —
  luật sư xác nhận; "AI nháp, người gửi" có lẽ
  nằm ngoài nghĩa vụ minh bạch quyết định tự động (từ 10/12/2026) — cần kiểm.
- **DPA mẫu phải có trước đại lý đầu tiên** (DM-6.8, mở rộng AA-886): điều khoản processor cho VN/GDPR/AU; phụ lục SCC (Module 2 + flow-down
  Module 3) + UK; xoá 90 ngày cho ops; tổng hợp k≥10; phụ lục kỹ thuật (khoá KMS, RLS, audit, câu chữ F1 đã sửa); phụ lục
  sub-processor: AWS acc2 qua TrueIDC, Bedrock acc3 qua eCloudvalley, Vercel, Twilio/Meta, vendor e-sign, Sentry (không
  PII); Stripe/Google/Microsoft là hợp đồng riêng của đại lý (luật sư xác nhận); OpenAI và Jev bị loại khỏi CRM.
- **Luật nền tảng phải bám:** DM-6.1, 6.3, 6.4, 6.5, 6.6, 6.8, 6.9, DM-7.1/7.2, DM-8.4, DM-8.9, C7.1a; điều khoản AI cho
  tenant (`docs/legal/tenant-terms-ai-clause-draft.md`) mở rộng cho CRM; chính sách Limited Use của Google (nhân viên AA
  không đọc mail đồng bộ nếu không có đồng ý từng thread).

## 15. Quyết định cần Nghiệp

Trả lời theo số, ví dụ "D1 a, D2 có, …". Khuyến nghị in đậm.

| # | Quyết định | Lựa chọn | Khuyến nghị |
|---|---|---|---|
| D1 | Kiến trúc | a) App thứ tư AA-CRM · b) module trong CIS · c) tích hợp CRM sẵn có | **a** |
| D2 | Sửa ADR 0008 §8 + DM-6.8 qua ADR 0010: câu "it is a CIS module" của ADR 0008 §8 đổi theo D1 = a, và DM-6.8 thêm 2 ngoại lệ view hợp đồng (ops release → `booking`, insights k≥10 → `cis_app`) | có / không | **có** |
| D3 | Thứ tự với M1 | a) CRM thành một lane riêng chạy song song từ S246 (W0 ngay; W1 khi AA-813 xong) · b) chờ M1 đóng hẳn như backlog ghi | **a** |
| D4 | Nhịp làm | a) agent team (điều phối + 2–3 lane) ~8–10 issue/phiên → 12–15 phiên + 1–2,5 dự phòng ≈ 14–16,5 · b) giữ 3–5 issue/phiên → 23–38 phiên | **a** |
| D5 | Khởi động mọi việc ngoài ngay ở W0 (Google/CASA, Microsoft, Meta, Stripe, insurer, brief luật sư) | có / không | **có** |
| D6 | Gmail | a) đồng bộ hai chiều (scope restricted, CASA $675–5.400/năm), xây đường chuyển tiếp trước làm dự phòng · b) chỉ `gmail.send` + chuyển tiếp SES, không CASA | **a** |
| D7 | Khoá F1 | a) 1 khoá KMS mỗi đại lý (+ BYOK tuỳ chọn), $1–3/đại lý/tháng · b) 1 khoá chung + DEK mỗi đại lý (~$1/tháng tổng, xoá kém sạch vì backup PITR) | **a** |
| D8 | Sửa câu F1 trong spec/DPA thành "chỉ runtime CRM dùng được, mọi lần đều ghi log; thu hồi được với BYOK" — cùng một quyết định với H3, **chỉ chốt sau H3** (chị Thư đồng ý) | có / không | **có** |
| D9 | WhatsApp | a) Embedded Signup, đại lý sở hữu WABA, Cloud API trực tiếp (Tech Provider) · b) Twilio làm BSP · c) 360dialog | **a** (b làm dự phòng) |
| D10 | Thanh toán đại lý VN | a) tích hợp cổng VN sau khi có báo giá, trong lúc chờ ghi nhận thủ công · b) chỉ ghi nhận thủ công | **a** |
| D11 | E-sign | a) BoldSign · b) Documenso Platform | **a** (xem lại ở ~30 đại lý) |
| D12 | Route AI của CRM chỉ Bedrock acc3 `us.`, model cho phép ZDR (không Fable 5/5.1), SCP ép `none`, loại OpenAI + Jev | có / không | **có** |
| D13 | Prod (AA-880 / ADR 0012, ~$150–300/tháng) là điều kiện cứng của pilot | có / không | **có** |
| D13-ngày | Ngày go-live prod (cũng quyết định pilot đi theo W8 hay sớm hơn, xem §10) | Nghiệp điền ngày | — |
| D14 | Mua Vercel Pro (D-18) trước khi đại lý đầu tiên vào portal | có / không | **có** |
| D15 | Gửi brief cho luật sư VN + AU/EU để lấy báo giá | có / không | **có** |
| D16 | Tạo project Linear "AA-CRM" và tạo issue theo từng đợt (114 issue ở §11), cập nhật Done-when AA-821 và dòng AA-821 ở `docs/backlog/README.md:123` | có / không | **có** |
| D17 | Repo AA-CRM | a) public như Booking (không ghi ID/inventory, có branch protection miễn phí) · b) private | **a** |
| D18 | Mở ngay một issue nhỏ (CIS) sửa CTA `mailto:admin@adventureasia.com` cứng trên `/trip/[tourId]` (lead của tenant đang chảy về AA) | có / không | **có** |
| D19 | Messenger + Instagram (spec §7 `Conversation.channel`) | a) làm ở W6 qua Meta Graph API (W6 #13) · b) hoãn — đây là cắt phạm vi spec, phải ghi rõ | **a** |
| D20 | Ngôn ngữ giao diện (spec gap 6 chưa chốt) | a) EN/VI cho app đại lý và app khách, khung i18n sẵn để thêm ngôn ngữ · b) thêm ngay ngôn ngữ cho đại lý/khách EU (ví dụ DE, FR) | **a**, xem lại sau H4 |

### Câu hỏi cho chị Thư

1. **H1.** "Lơ đi cái 40 tuần" là bỏ lịch, còn phạm vi vẫn đủ 23 module như spec — chị xác nhận giúp em đúng không?
2. **H2.** Mô hình giá cho đại lý: miễn phí / theo seat / gắn với hoa hồng khi bán hàng AA? (Ở 200 đại lý AA gánh ~$5k/tháng nếu miễn phí hoàn toàn.)
3. **H3.** Chị đồng ý sửa câu "AA cũng không truy cập được" thành "chỉ hệ thống CRM dùng được khoá, mọi lần đều ghi log, đại lý tự thu hồi được nếu dùng khoá riêng"?
4. **H4.** 3–5 đại lý pilot là ai, ở nước nào (Úc / EU / VN)? Mình phỏng vấn họ được từ đầu không?
5. **H5.** Pháp nhân ký hợp đồng của AA ở nước nào? Chị có luật sư VN và AU/EU để em gửi brief (PDPL, có thể cần giấy phép VN)?
6. **H6.** Bảo hiểm nào sẽ duyệt waiver trekking ký điện tử, ai liên hệ?
7. **H7.** Khách VN của đại lý có cần Zalo không (spec ghi WhatsApp/SMS/Messenger/IG, không có Zalo)?
8. **H8.** Tour AA nào có ngày khởi hành cố định + chỗ (allotment) để hiển thị "còn chỗ" thật; ai giữ số liệu đó luôn đúng?
9. **H9.** Bảng giá net B2B (ADR 0005, biên 15%) có dùng nguyên cho CRM không?
10. **H10.** Ai soạn nội dung điều khoản đặt tour và waiver mẫu cho đại lý?

## 16. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Lời hứa F1 quá tay (khoá nằm trong account AA) | Cao | Sửa câu chữ (D8), key policy chỉ task role CRM + encryption context, báo động Decrypt, BYOK |
| Pháp lý VN (Nghị định 356): có thể cần giấy phép + pháp nhân VN; DPIA/TIA | Cao | Brief luật sư từ W0 (D15); đại lý VN có thể phải chờ — trượt phạm vi do bên ngoài |
| Lịch: 114 issue; ở nhịp 3–5 issue/phiên là 23–38 phiên, cạnh tranh với CIS-first | Cao | D4 (agent team), CRM là lane riêng |
| Rủi ro sản phẩm: chưa phỏng vấn đại lý nào; Dev có ~4 tenant thử | Cao | Tuyển pilot ở W0, demo W3 trên dữ liệu giả, table stakes làm tiêu chí |
| Việc ngoài trễ (CASA, Meta, insurer, luật sư, cổng VN) | TB | Code đằng sau cờ; chỉ Gmail hai chiều, WhatsApp và pilot bị chặn |
| Booking chưa có mô hình availability | TB | Departure/allotment trong W3; tour tailor-made "on request"; cần kỷ luật vận hành (H8) |
| Ngân sách kết nối RDS sát trần (~126/135 + 10) | TB | Bù trừ trong C2.2 hoặc t4g.medium |
| Khối lượng audit (~10 triệu dòng/tháng ở 200 đại lý) | TB | Phân vùng tháng, chuỗi theo tenant, 90 ngày nóng rồi Parquet S3 |
| Tìm kiếm trên dữ liệu mã hoá chỉ khớp chính xác | TB | Blind index; kiểm với pilot xem có chậm hơn Gmail không |
| Scrubber tiếng Việt chưa rõ chất lượng | TB | Lượt thay thế tất định trước, recognizer riêng, corpus CI đo "0 rò" |
| Bedrock `global.` có thể đi vòng thế giới; Fable 5/5.1 bắt buộc lưu 30 ngày | TB | Ghim `us.` + model cho phép ZDR + SCP (D12); kiểm acc3 (eCloudvalley) cho phép SCP |
| Stripe không có VN → hai adapter thanh toán | TB | D10 |
| Chi phí WhatsApp trôi (từ 01/10/2026 tính phí service vượt 1.000; nhắc khách có thể là marketing) | TB | WABA của đại lý (D9) |
| Hai bề mặt chéo repo (TP builder, portal zone) lệch hợp đồng | TB | OpenAPI + consumer test, guard byte-copy |
| Pool Cognito EXTERNAL dùng chung | TB | Membership là ranh giới; probe + X2 bắt buộc |
| Backup PITR giữ hàng đã xoá 7–14 ngày | Thấp | Crypto-shred khi offboarding; ghi rõ trong DPA |

## 17. Ghi chú nguồn và chỗ lệch

- Nguồn chính: 4 note research trong `research/`, phương án A từ lane phương án (bị cắt sau module 9 của bảng phủ —
  phần 10–18 ở §9 do bước viết tài liệu ước lượng), spec, ADR 0005/0006/0008, data standards DM-6/7/8, C7.1a.
- **Lệch giữa các lane:** AA-848 (lane 1: Backlog, slot S250; lane phương án: In Progress) — đã kiểm Linear 20/10/2026:
  **Done**, cả hai lane đều sai; đã sửa ở §11/§12; AA-824 N3 (lane 1: chưa
  kiểm; lane phương án: Done); ngân sách kết nối (lane 1: tổng LOGIN limit 155 → 165 trên 181; lane phương án: worst
  case C2.2 ~126 trên trần 135). Kiểm lại live khi bắt đầu W1.
- **Lệch tài liệu đã thấy** (sửa ở W0, issue 6): `docs/ecosystem-architecture.md:340` còn ghi staff Cognito của Booking
  "chưa bắt đầu"; DM-6.8/KEY-6/SEC-12 còn ghi `aa_cis_admin` runtime đọc được `crm.*` (X1 đã xong); CIS `CONTEXT.md:1621`
  ghi T11 chỉ blog nhưng code đăng cả Facebook.
- Giá vendor phần lớn từ nguồn bên thứ ba (ghi rõ trong research) — phải lấy báo giá trước khi chốt ngân sách.
