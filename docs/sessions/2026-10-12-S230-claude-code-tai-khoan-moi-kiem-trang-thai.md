# S230 (12/10/2026, Claude Code — WSL/VSCode) — tài khoản Claude mới: đọc bối cảnh, kiểm trạng thái, dừng vì MCP

**Bối cảnh:** Nghiệp chuyển sang tài khoản Claude mới, yêu cầu đọc toàn bộ skill / state / repo /
Notion / Linear để chắc agent nắm dự án. Phiên dừng sớm theo yêu cầu Nghiệp vì Notion + Linear +
Atlassian không kết nối được trong phiên này — để phiên sau mở lại với đủ công cụ.

## Trạng thái (đã verify trong phiên)
- 4 repo (gốc + App + TripPlanner + Infra) ở main/master, cây sạch, đã pull. HEAD App `16ceff9` (#660).
- STS acc2 còn hạn. ECS api `:533` / worker `:88`, cùng image `dev-16ceff9…`, rollout COMPLETED.
  RDS `available`. `/health` 200.
- DB: `shared.job` 0 queued/running (24h qua chỉ succeeded: s1_rewrite 12, revalidate 6,
  a3_atomize 6, recompute 3). Migration mới nhất `tp-008`, `218`. Tenant: 4 brand
  (atlas-hearth, terra-family, trail-pulse, wildkind-travel) + `aa_internal` active; 3 cũ offboard.
  892 Master active.
- UI (Playwright, login e2e): `/admin/tenants` 5 tenant khớp DB; `/admin/jobs` 0 queued, cost 30
  ngày $91.82, 4 failed; TripPlanner home tải bình thường. 0 console error.
- **Không lệch** so với log S229.

## Quyết định của Nghiệp
- Dừng phiên, không làm thêm, để phiên sau load đủ công cụ (MCP) rồi mới làm.
- Remote Control bị tổ chức chặn ("disabled by your organization's policy") → nhắn chị Thư bật
  (đã soạn nháp Zalo cho Nghiệp; chưa biết đã gửi chưa).

## Kết quả chính
- Không có thay đổi codebase, hạ tầng, dữ liệu. Không PR.
- G1 mới ở bước khảo sát (chưa sửa file nào) — ghi lại hướng làm ở dưới để phiên sau dùng ngay.

## MCP / công cụ — tình trạng
- GitHub (`gh` CLI, tài khoản `pqnghiep1354`, scope repo/workflow) và AWS: dùng bình thường.
- Trong phiên này: Notion "not connected"; Linear / Atlassian / Canva 404 "Server not found".
  Nhưng `claude mcp list` chạy process mới báo cả 4 **Connected** → phiên này giữ registry
  connector cũ (trước khi đổi tài khoản). Cách sửa: mở phiên mới (`claude --continue`), nếu vẫn lỗi
  thì `/mcp` → Reconnect, hoặc ngắt/kết nối lại ở claude.ai → Settings → Connectors.
- Nghiệp đã tự sửa MCP GitHub + Vercel.

## Chưa làm được (do MCP) — phiên sau làm đầu tiên
1. **Prepend session block S230 vào Notion `memory.md` HOT** (khối dưới đây).
2. Đọc memory HOT, đối chiếu với log S229/S230; `get_issue` các issue liên quan (AA-741, AA-668,
   AA-756, AA-759–762, AA-703) để chắc title/trạng thái.

## Việc cần làm đầu phiên sau (S231)
1. Kiểm MCP Notion + Linear hoạt động; làm 2 việc ở mục trên.
2. **G1** (backend, $0) — gắn tenant_id vào gateway. Hướng đã khảo sát:
   - `shared/llm_client/call_log.py`: thêm `_current_tenant_id` ContextVar + `bind_tenant()`
     cạnh `_current_job_id`/`bind_job`; `record_call`/`record_call_with_pool` dùng
     `tenant_id or current_tenant_id()`.
   - `shared/jobs/worker.py:152` đang `bind_job(job.id)` quanh `create_task(handler)` → bind thêm
     tenant từ `job.payload["tenant_id"]` (`shared.job` KHÔNG có cột tenant_id; payload T2/T9/
     s1_rewrite/s1_seo_prefetch có `tenant_id`). Lưu ý `aa_internal` cho job A-series.
   - `shared/llm_client/decide.py:_write_logs` (Jev decision_log) cũng nên lấy tenant từ ContextVar
     khi caller không truyền.
   - Bỏ `tenant_id=None` ở: `brand_audit_node.py:345`, `flag_fix_node.py:260,366`, `graph.py:151`,
     `grounding.py:410`, `judge_node.py:156`, `source_facts.py:260`, `quality_gates.py:523` (đọc
     comment 507/570 trước — có lý do cũ). `api/middleware/rate_limit.py:186` và
     `acp_angle_gate/generate.py:97` kiểm riêng.
   - Đường request HTTP (T7/T8 chạy trong request): bind tenant ở dependency xác thực tenant —
     chú ý dependency `def` (sync) chạy trong threadpool nên set ContextVar không lan sang endpoint.
   - Test: 1 T2 + 1 T9 ghi tenant trên mọi dòng `llm_call_log` (integration test Postgres thật).
3. Hỏi Nghiệp: số goal (8 trong code hay 10); T2 có viết cho nhiều thị trường không.
4. G2 (Nghiệp bấm) → G3 pilot, theo `docs/architecture/t-series-audit-and-plan.md` §7.

## Khối memory HOT để prepend (phiên sau dán vào Notion)
```
## S230 (12/10/2026, Claude Code — WSL/VSCode): tài khoản Claude mới — đọc bối cảnh, kiểm trạng thái, dừng vì MCP
**Quyết định của Nghiệp** — Dừng phiên sớm để phiên sau có đủ MCP. Remote Control bị org chặn → nhờ chị Thư bật.
**Kết quả chính** — Không đổi code/hạ tầng. Verify: 4 repo sạch main; ECS api :533 / worker :88 cùng SHA 16ceff9; RDS available; shared.job 0 treo; 4 tenant brand + aa_internal; 892 Master. Không lệch so với S229. G1 mới khảo sát (hướng ghi trong log local S230).
**Việc cần làm đầu phiên sau (S231)** — 1) kiểm MCP Notion/Linear; 2) G1 tenant_id qua ContextVar trong call_log + bind ở worker từ payload; 3) hỏi số goal 8/10 + T2 đa thị trường; 4) G2 → G3 pilot.
**Lưu ý kỹ thuật** — Đổi tài khoản Claude giữa phiên: phiên cũ giữ registry connector cũ (Linear/Atlassian 404, Notion not connected) dù `claude mcp list` báo Connected → mở phiên mới.
```

## Lưu ý kỹ thuật
- Playwright: dùng `apps/AA-CIS-App/node_modules/playwright` (frontend không có). Nút login CIS
  không phải `type=submit` → selector `button:has-text('Log in')`/fallback `button`.
- Bắt đầu phiên đã đoán nhầm cột `shared.tenants.status` (không tồn tại — có `is_active`,
  `cancelled_at`); quy tắc "đọc db-schema-reference trước" đã có trong steering, không thêm bài học.
- Môi trường để nguyên đang chạy (không stop ECS/RDS).
