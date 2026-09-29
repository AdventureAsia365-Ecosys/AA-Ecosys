# S201: Mọi lời gọi model qua Gateway, job runner bền, T2/T9/A3 thành job, chi phí theo job

- **Ngày:** 28–29/09/2026
- **Tác nhân:** Claude Code (VSCode/WSL)
- **Người duyệt:** Nghiệp
- **Đầu vào:** memory S200 (AA-659 còn In Progress, AA-685 kế tiếp, P1 job runner AA-650/652).

## Trạng thái

| Issue | Kết quả | Trạng thái Linear |
|---|---|---|
| AA-659 | Gỡ env `JUDGE_MODEL` không còn dùng (Infra #76, task def :356) | Done |
| AA-685 | 5 call site chưa log + TripPlanner đi qua Model Gateway, mọi lời gọi đều ghi `llm_call_log` | Done (tự đóng khi merge); **còn đối chiếu chi phí 1 ngày từ 30/09** |
| AA-650 | Job runner bền (Postgres `shared.job`), worker chạy trong API (phương án C, Nghiệp chọn) | **Done**: nhánh trả job khi SIGTERM đã chạy thật trên Dev |
| AA-652 | T2 rewrite, T9 write, A3 atomize chuyển sang job; portal có trạng thái lỗi + Retry | Done: T2/T9 verify live; A3 chạy được, không chặn API sau hotfix |
| PR #466 | Chi phí LLM gắn theo job (`llm_call_log.job_id`) | Verify live (job T2 = $0.042) |
| AA-687, AA-688 | Tạo mới: UI giám sát job; gộp embedding cho bước PAA | Backlog |

- Dev hiện chạy **ECS task def :364**, RDS đang chạy. Nghiệp để Dev chạy liên tục, không cis-stop.
- Migration mới nhất trên Dev: **177**.

## Thay đổi Codebase

### AA-CIS-App
- **#458–#460 (AA-685)**
  - Migration 172: mở rộng CHECK role/provider, seed route `a0_column_map`, `f10_embed`, `tp_compose`, `tp_search_embed`.
  - Migration 173: grant cho role `tripplanner` đọc config gateway và ghi `llm_call_log`; seed `tp_extract`, `tp_component_embed`.
  - `shared/llm_client/embed.py` mới (Cohere Embed v4 qua gateway, có log).
  - `content_embedding.py`, `column_mapper.py`, debate judge đi qua gateway.
  - Xoá `h3_rule_extractor.py` (code chết).
  - Test AST chặn lời gọi model thô ngoài gateway.
  - Trang Settings có nhóm a0, embed, tp.
- **#461 (AA-650)**
  - Migration 174 `shared.job`.
  - `shared/jobs/` gồm `queue.py`, `registry.py`, `worker.py`: claim `SKIP LOCKED`, lease 90 s, heartbeat, reaper, backoff, idempotency, cancel/retry, hook `on_terminal`.
  - `segment_research` là job đầu tiên.
  - Trang admin `/admin/jobs` và API `/admin/job-runner/*`.
- **#462 (AA-652 PR-A)**
  - Migration 175: `tenant_tour_versions.job_id` và trạng thái `failed`.
  - Job `t2_rewrite`, endpoint retry version.
  - Portal CatalogTab có "Queued…", "Writing failed" và nút Retry.
- **#463 (PR-B):** migration 176 `content_piece.job_id`; job `t9_write`.
- **#464 (PR-C):** job `a3_atomize` (export publish và admin re-atomize đều enqueue).
- **#465 (hotfix):**
  - A3 chạy trong thread + event loop riêng.
  - `MAX_RELEASES = 3`: job bị trả về quá 3 lần thì fail, không lặp vô hạn.
- **#466 (chi phí theo job):**
  - Migration 177 `llm_call_log.job_id`, gán qua contextvar `call_log.bind_job`.
  - Chi phí job = phần handler tự báo (DFS) + tổng log của job, tính lúc đọc; API có thêm `llm_cost_usd`.
  - `segment_research` chỉ tự báo phần DFS.

### AA-TripPlanner-Web
- **#50, #51:**
  - `backend/shared/llm_gateway.py`: client gateway mỏng, đọc `llm_role_config`/`llm_model_catalog`, Bedrock acc3 → acc1 → acc2, ghi `llm_call_log` gắn app `tripplanner`.
  - Bỏ model id cứng trong config.

### AA-CIS-Infra
- **#76:** bỏ biến judge_model / `JUDGE_MODEL`.
- **#77:** bỏ `BEDROCK_MODEL_EMBED` và `BEDROCK_MODEL_COMPOSE` ở TripPlanner.

## Thay đổi Hạ tầng
- Terraform apply Infra #76 và #77 (acc2).
- Migration 172–177 apply lên RDS Dev qua ECS exec, trước mỗi lần deploy.
- ECS: :356 → :364 qua các lần deploy trong phiên.

## Bằng chứng verify
- **AA-685:** A0 column map chạy lại được qua acc3; trước đó hỏng âm thầm vì Haiku acc2 bị chặn với tài khoản channel-program. Embedding F10 và TripPlanner đã có dòng log.
- **T2 (job 3039c977):** succeeded sau 35 s, score 10, có live progress, $0.033.
- **T9 (job 386edc8b):** 190 s, piece held → ready, $0.0499.
- **Release khi SIGTERM (AA-650), chạy thật 2 lần:**
  - lần 1: 01:18:39 drain → 01:19:00 `job_released_on_shutdown` → 01:19:01 task mới claim, lần chạy vẫn là 1;
  - lần 2: 02:21:02 → 02:21:03 (`releases=1`).
- **Hotfix A3:** `/health` luôn trả 200 trong 30 phút theo dõi (chậm nhất 2.17 s), không có sự kiện ECS thay task "unhealthy".
- **Chi phí theo job:** job T2 a57d0e1e `cost_usd` = `llm_cost_usd` = $0.042135 (trước đây $0), không có `llm_call_log_write_failed`.

## Sự cố trong phiên
- **API Dev bị treo (29/09, khoảng 00:40–01:02 UTC):**
  - Nguyên nhân: chuỗi A3 chạy trên event loop của API, trong khi `compute_embedding()` có `time.sleep(3.5)` (pacing AA-610).
  - Hậu quả: `/health` lỗi, ECS thay task 2 lần; job bị trả về rồi được nhận lại liên tục.
  - Xử lý: huỷ job tay lúc 01:02, rồi hotfix #465.
  - Lỗi chặn loop đã có từ trước (task nền in-process); chuyển sang job chỉ làm nó lộ ra.

## Còn lại
- **AA-685:** từ 30/09, đối chiếu 1 ngày External Spend với Cost Explorer theo từng account.
- **Job a3_atomize 547d955b** vẫn chạy ở bước ghép câu hỏi PAA: hơn 1.500 lần embed từng câu, mỗi lần chờ 3.5 s → **AA-688**.
- **AA-687:** UI giám sát job. Nghiệp yêu cầu mọi tính năng backend phải quan sát và giám sát được trên UI. Phần trùng đã gộp vào AA-664 (widget Overview) và AA-665 (chi phí theo app/embed).
- **AA-651:** tách worker thành ECS service riêng, khi traffic tăng.
- **Follow-up cũ còn mở:**
  - TripPlanner search dùng `input_type` search_query hay không;
  - `judge_client` còn backend cũ;
  - `segment_research_ideas_task` ra 0 ý tưởng có volume;
  - text ứng viên Debate bị hỏng;
  - 71 place Bhutan còn cũ.

## Lưu ý kỹ thuật
- **Migration có INSERT tên cột mới** (vd 177): apply **trước** deploy. Ghi log là fire-and-forget, nên insert lỗi sẽ mất dòng log mà không có cảnh báo.
- **Deploy Dev mất khoảng 8–10 phút** vì ALB `deregistration_delay` = 300 s. Task cũ vẫn chạy job trong lúc drain; SIGTERM đến sau khoảng 5 phút.
- **Không gọi code sync có `time.sleep` từ async** trong API. Nếu cần, chạy qua `asyncio.to_thread`, như A3 đang làm.
- **Contextvar đi qua được** `create_task`, `asyncio.to_thread` và executor của LangGraph, nhưng **không** qua `loop.run_in_executor` tự viết.
- **Log group đúng là `/ecs/aa-cis-dev`.**
- **ECS exec session có thể đứt giữa chừng** (EOF): kiểm tra trạng thái trước khi chạy lại, tránh tạo job trùng.
- **AA-652 và AA-685 tự Done khi merge PR** (tích hợp GitHub ↔ Linear): kiểm tra lại trạng thái sau khi merge.
