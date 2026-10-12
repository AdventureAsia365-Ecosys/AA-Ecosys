# S231 (12/10/2026, Claude Code — WSL/Kiro) — G1 tenant_id + G2 DE/FR/NL + pilot T-series (AA-741)

**Tác nhân:** Claude Code. **Bối cảnh:** tiếp S230 (dừng sớm vì mất MCP). Phiên này Notion + Linear
kết nối lại. Nghiệp duyệt đề xuất G1 → G2 → G3 (→ G4), chốt "dùng 8 goal", giao "làm tất cả
tới khi xong, chưa có issue thì tạo mới, cuối phiên báo cáo tổng kết".

## Trạng thái đầu phiên
- 4 repo sạch ở main/master, khớp GitHub. ECS api `:533` / worker `:88` cùng SHA `16ceff9`,
  RDS available, `/health` 200, `shared.job` 0 queued/running. **Không lệch** S229/S230.
- Dán bù session block S230 vào Notion memory HOT (S230 không có MCP).

## Quyết định của Nghiệp
- Số goal: **8** (đúng như code `goals.py`).
- Đồng ý danh sách S231; "làm tất cả tới khi xong", việc chưa có issue thì tạo issue mới.
- Sửa MCP GitHub "làm luôn, tôi duyệt tay" (sửa `~/.zshrc`).
- (Câu hỏi T2 đa thị trường: Nghiệp chưa hiểu → đã giải thích a/b/c, khuyến nghị giữ (a) 1
  thị trường tới khi có số G7; chưa chốt.)

## Thay đổi Codebase (AA-CIS-App — tất cả merged, CI xanh, deploy Dev)
- **#661 G1** — `call_log.bind_tenant` (ContextVar như job_id); worker bind tenant từ payload
  (`tenant_id` hoặc T9 `context.tenant_id`; aa_internal KHÔNG bind → dòng A-series giữ NULL);
  `record_call*` + `decide()` fallback về tenant đã bind; bỏ `tenant_id=None` ở 8 call site.
  15 unit + integration Postgres thật qua Worker thật (fail khi bỏ fix).
- **#662** — uvicorn `--timeout-keep-alive 105` (> ALB idle 100s): 502 ngẫu nhiên khi ALB tái dùng
  kết nối uvicorn đã đóng (pilot 1/12; metric ALB 502 = 39 ngày 07/10).
- **#663** — lời gọi shadow (thread thường, cố ý không kế thừa contextvars) mang theo job_id +
  tenant của lời gọi chính (pilot: 29 dòng s1_judge shadow thiếu tenant).
- **#664** — T2 keyword thị trường tenant khớp theo **địa danh atom** (trước chỉ theo chữ trong
  TÊN tour → 12/12 rơi về keyword admin US). Kèm sửa conftest: tạo role `aa_app_user` (thiếu →
  migration 203 `v_active_tour_atoms` chưa bao giờ áp trong integration test).
- Root: báo cáo `docs/audits/2026-10-12-S231-t-series-pilot.md`; 2 lesson mới.

## Thay đổi Hạ tầng / dữ liệu
- ECS cuối phiên: api `:536` / worker `:91`, image `dev-c6fc020`. Deploy #663 lần đầu bị
  guard chặn (đúng — còn job T9), gộp vào deploy #664.
- **G2**: segment_research DE/FR/NL cho 73 place của 3 tour pilot — DE/FR/NL 26 → 99 place,
  keyword 96 → 263/nước, **$0,70**.
- **Pilot G3** trên 4 tenant brand (dữ liệu test, giữ lại để G7 dùng): 12+1 version T2, 5
  angle_gate_request + 9 content_piece (đều held), subject slate cho atlas/terra/trail/wildkind.
- Không có migration.

## Bằng chứng verify
- G1 live: 12 job T2 → **359/359** dòng `llm_call_log` có tenant; 5 job T9 → mọi dòng có tenant.
- #664 live (code đã deploy, ECS exec): `tenant_market_seo` trả keyword thị trường tenant cho
  9/9 tổ hợp (trước 0/12). 1 T2 xác minh sau deploy (terra-family × Bhutan): `seo_source = tenant_market`, market UK, điểm 7 (`ai_generated`), $0,31, 0 dòng thiếu tenant.
- #662: 30/30 request keep-alive 200 (qua API GW — phụ); bằng chứng chính = metric ALB 502 tuần tới.

## Kết quả pilot (chi tiết: `docs/audits/2026-10-12-S231-t-series-pilot.md`)
- T2: $0,38/tour (95% `t2_generate`, ~7 lần generate/tour), 281s/job; 5/12 đạt 7.
- T7 slate: `GET /v1/slate` chạy propose + Debate MỖI lần tải, 2'48"–4'+ → **504 cả 4 tenant**;
  Debate gắn cờ 49–54/60 ứng viên.
- T8 angle: 15–19s trong request. T9: blog ≈ $0,14/bài, LinkedIn ≈ $0,057/bài (gồm T8).
- **5/5 bài held** — writer bịa số liệu (F1_grounding) + F9 manual_check.
- Tổng chi pilot ≈ $5,8 (+ $0,38 T2 xác minh).

## Linear
- Tạo AA-763 (G4 stage key T), AA-764 (G5 T7/T8 sang worker), AA-765 (G6), AA-766 (G9 Tenant 360).
- **Workspace Linear hết hạn mức issue gói free** → các phát hiện 502 / shadow / T9 held ghi
  thành comment AA-741.
- AA-741 vẫn In Progress (G1–G3 xong; G4+ còn).

## Còn lại / phiên sau (S232)
1. **T9 bịa số liệu (5/5 held)** — áp luật writer A/B (S223) cho T9: chỉ số liệu có trong seed;
   đo lại 5 bài. Đây là chặn lớn nhất trước khi tenant nhận được bài.
2. **AA-764 (G5)** — T7/T8 sang worker; `GET /v1/slate` chỉ đọc, không propose lại (504 + tốn tiền mỗi lần tải).
3. AA-763 (G4) stage key T-series; Debate cờ 82–90% → calib (AA-696/699).
4. G7 chạy đủ 48 sau khi 1–3 xong; dùng tenant-market keyword (#664).
5. Linear hết hạn mức issue — Nghiệp quyết: nâng gói / dọn issue cũ.
6. Kiểm metric ALB `HTTPCode_ELB_502_Count` = 0 cả tuần (đóng phần #662).

## Lưu ý kỹ thuật
- Claude Code chạy dưới kiro-server: env lấy từ `~/.zshrc` MỘT lần lúc server khởi động → sửa rc
  (token MCP GitHub) cần tắt hẳn Kiro + `pkill -f kiro-server`. Đã sửa dòng `npm bin -g` (npm 9+
  bỏ) đang chèn chữ lỗi vào PATH.
- Remote Control: policy tải mới 13:53 vẫn `allow_remote_control: false` → chị Thư kiểm lại Admin Console.
- Phiên STS 8h hết giữa phiên → Nghiệp nhập MFA lại.
- `GET /v1/slate` là thao tác TỐN TIỀN (propose + Debate) — script đo đừng gọi lặp; lấy subject từ DB.
- T9 write cần CTA (cố ý: không tự bịa CTA) — script pilot phải gửi `cta`.
