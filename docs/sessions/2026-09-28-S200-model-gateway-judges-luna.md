# S200: Model Gateway P0 + P1 lõi, judge chuyển sang GPT-5.6 Luna, Jira ↔ Linear

- **Ngày:** 28/09/2026
- **Tác nhân:** Claude Code (VSCode/WSL)
- **Người duyệt:** Nghiệp
- **Đầu vào:** memory S199 (P1 Model Gateway: AA-657 → AA-658 → AA-659), 4 việc chị Thư giao trên Jira
  hôm nay (KAN-90, PR-7, PR-11, PR-12).

## Trạng thái

- **AA-657 Done**: IAM acc3 gọi được Sonnet 5, Opus 5.5, GPT-5.6 Luna, GPT-6 Astra (sau đó thêm GPT-6 Luna).
- **AA-658 Done**: bảng `shared.llm_model_catalog` + adapter Bedrock Converse.
- **AA-659 In Progress**: đã build, deploy, verify phần lõi (route model + fallback + shadow, gỡ ghim
  GPT-4.1 ở mọi judge). Còn treo quyết định brand_audit → Nghiệp chốt **giữ nguyên, chờ thêm Jev**.
- Judge trên Dev:

| Stage | Model chính | Fallback | Shadow |
|---|---|---|---|
| s1_judge, t10_judge, n7_judge | gpt-5.6-luna | gpt-6-luna → gpt-6-luna-openai | gpt-4.1 100% |
| s1_brand_audit | gpt-4.1 | — | gpt-5.6-luna 100% |

## Thay đổi Codebase

**AA-CIS-App**
- **#455** (`9bc81ef`, AA-658):
  - migration 169 `shared.llm_model_catalog`;
  - `shared/llm_client/catalog.py`;
  - Converse adapter trong `LLMClient` (acc3, không fallback ngầm);
  - giá đọc từ catalog (`pricing.py` chỉ còn là fallback);
  - dropdown admin chỉ cho chọn model stage chạy được, PATCH trả 422 nếu không hợp lệ;
  - ADR 0005.
- **#456** (`2d94fc4`, AA-659):
  - migration 170 (cột `fallback_model_ids` / `shadow_model_id` / `shadow_sample_pct`, bảng
    `shared.llm_shadow_log`, giá đã kiểm) và migration 171 (chuyển judge);
  - route trong `LLMClient` + `shared/llm_client/shadow.py`;
  - `json_schema` trên `LLMRequest`;
  - `brand_fit`, `judge_client.invoke_judge(stage=)`, `brand_audit_node` đều đi qua gateway;
  - ADR 0006.
- **#457** (`3ced35d`, AA-659): `shared/llm_client/schema_check.py`, kiểm mọi output có schema ngay trong gateway.
- CONTEXT.md App: thêm glossary Stage / Model Key / Model Catalog / Stage Route + mục kiến trúc.

**AA-CIS-Infra**
- **#74** (`c9c1a73`, AA-657): 4 model mới vào `AA3-Bedrock-Invoker`. Giữ nguyên tên policy, chỉ đổi Sid
  (đổi tên inline policy sẽ destroy + create, role mất quyền giữa 2 bước).
- **#75** (`4003bc5`): thêm GPT-6 Luna.

**Repo gốc** (commit cùng log này)
- Steering `session-workflow.md`: quy tắc comment Jira + quy tắc 3 tầng đặt ADR.

## Thay đổi Hạ tầng

- **acc3:**
  - `terraform apply` root `accounts/acc3-bedrock` 2 lần, đều 0 add / 1 change / 0 destroy;
  - policy invoker giờ có 21 ARN.
- **acc3:** **chấp nhận agreement GPT-6 Luna** (`create-foundation-model-agreement`). Offer tính giá theo
  lượng dùng, global standard $0.10 / $0.50 per 1M.
- **DB Dev:**
  - migration 169, 170, 171 đã apply;
  - bật `gpt-6-luna` trong catalog;
  - `s1_brand_audit` đổi tay 2 lần (rollback → GPT-4.1 + shadow Luna, `updated_by` ghi rõ).
- **ECS:** taskDef :353 → :354 → :355, cả 3 lần rollout COMPLETED.

## Bằng chứng verify

- **AA-657:**
  - `get-role-policy` → Sid `InvokeApprovedModelsOnly`, 18 ARN (sau #75 là 21);
  - Converse thật từ ECS: sonnet-5 và gpt-5.6-luna, account acc3, `end_turn`.
- **AA-658:**
  - `GET /admin/llm-config` 200, option lấy từ catalog;
  - PATCH judge → sonnet-5 trả 422;
  - `llm_call_log` `adhoc_aa658` đúng giá: sonnet-5 $0.000084, luna $0.000004, haiku $0.000036.
- **AA-659, smoke 9/9:** F8 / brand_fit / brand_audit × GPT-5.6 Luna / GPT-6 Luna (OpenAI) / GPT-4.1,
  đều parse được. Luna rẻ hơn GPT-4.1 khoảng 4–7 lần.
- **AA-659, end-to-end:** gate F8 T10 và brand_fit thật chạy trên `satellite-gpt-5.6-luna` acc3, không
  dùng fallback; shadow GPT-4.1 ghi đủ vào `llm_shadow_log` và `llm_call_log` (`shadow=true`).
- **Brand_audit 12/12 đúng schema** sau #457. Luna chủ yếu trả `manual_check`, số mã lỗi 2–7; GPT-4.1
  trả `flagged` ×3, luôn 2 mã.
- **CloudWatch 30 phút:** 0 lỗi route / skip / ghi shadow / giá không rõ, 0 traceback.
- **Test local:** 2056 test pass, flake8 sạch; CI 5/5 xanh cả 3 PR App.

## Sự cố trong phiên

- **brand_audit âm thầm cho mọi tour "pass" sau migration 171.**
  - **Nguyên nhân:** GPT-5.6 Luna qua forced tool thiếu key `status` (Bedrock không ép schema); `result["status"]`
    gây KeyError và nhánh xử lý lỗi của node trả `pass`.
  - **Xử lý:** rollback `s1_brand_audit` về GPT-4.1 trong vài phút → fix #457 → kiểm lại 12/12.
- **Giá GPT-5.6 Luna ghi sai** ở migration 169: $0.10 / $0.50 là giá của GPT-6 Luna, bị chép nhầm từ S198/S199.
  Sửa thành $0.20 / $1.20 ở migration 170.

## Jira ↔ Linear

- Connector Atlassian đã chạy (site `adventure-asia.atlassian.net`).
- **KAN-90:** đã comment tiến độ bằng tiếng Anh, ngắn gọn, không nêu mã Linear.
- **Map Jira → Linear** (đã ghi cross-ref vào issue Linear): PR-11 (visual map planner) → AA-674/673;
  PR-7 (repo social pipeline của chị Thư) → AA-634; PR-12 (booking) → AA-677.
- **Issue mới:**
  - AA-684: quy ước sở hữu schema + dọn migration;
  - AA-685: 5 chỗ gọi model chưa ghi chi phí + TripPlanner;
  - AA-686: UI sửa route / shadow + báo cáo A/B.
- **AA-664:** thêm yêu cầu xem CloudWatch trên UI admin.

## Quyết định của Nghiệp (grilling thủ công 3 vòng + AA-659)

- Giữ nguyên các Model Key cũ.
- Model Converse không fallback ngầm; chỉ fallback theo route khai báo.
- Dropdown chỉ hiện model stage chạy được.
- **ADR đặt theo 3 tầng** (root / infra / app).
- **Migration giữ theo repo sở hữu schema**, không dồn về Infra hay repo gốc (→ AA-684).
- **Judge:** ưu tiên GPT-5.6 Luna Bedrock, giữ GPT-6 Luna qua OpenAI API, fallback có 5.6 Luna, A/B bằng shadow.
- **brand_audit:** giữ GPT-4.1 làm chính, chờ thêm Jev.

## Còn lại

1. **AA-660:** Jev `decide()` + `decision_log`, chạy shadow cho judge (kể cả brand_audit). Cần chốt trước:
   nơi để key Jev, ngân sách Jev, bộ câu hỏi dùng để chấm.
2. **AA-685, AA-650/651/652** (job runner), **AA-686**, **AA-684**.
3. **Infra:** gỡ biến môi trường `JUDGE_MODEL=gpt41` khỏi task def (không còn tác dụng).
4. **Tồn từ S199:**
   - log `segment_research_ideas_task` (task gợi ý trả 0 ý tưởng);
   - 91 địa điểm Bhutan chưa research;
   - AA-641.
5. **Việc chị Thư:** TripPlanner AA-673/674 (PR-11), AA-Booking AA-677/678 (PR-12).
6. `apps/AA-CIS-App/.claude/CLAUDE.md` LIVE STATE vẫn cũ từ 25/08 (việc của AA-654).

## Lưu ý kỹ thuật

- **Apply root `accounts/acc3-bedrock`:**
  - workflow "Terraform Apply Prod" trên GitHub chỉ apply `accounts/aa365`; acc3 phải apply tay bằng
    `nghiep_aa365`;
  - dùng `plan -out` rồi `apply <file>`.
- **Đổi `name` của `aws_iam_role_policy`** sẽ destroy + create → khoảng trống quyền. Chỉ đổi Sid.
- **Bedrock Converse forced tool không ép schema** → phải kiểm ở client (`schema_check.py`).
- **Thứ tự rollout migration có đổi dữ liệu route:**
  - migration chỉ thêm cột/bảng thì apply **trước** deploy (170);
  - migration đổi dữ liệu thì apply **sau** deploy + smoke (171);
  - SQL rollback nằm ở đầu file 171.
- **Test gate cũ** (`test_aa298_judge.py`, `test_aa372_gates.py`) trỏ route về backend Nova đã mock để chạy offline.
- **CLI:**
  - `gh pr edit` vẫn lỗi (Projects classic) → dùng `gh api -X PATCH .../pulls/N -F body=@file`;
  - `gh pr checks` không có `--json`.
- **Auto mode:** bộ kiểm quyền nhiều lần không trả kết quả (kể cả với `ls`) → thử lại sau vài lượt.
- Script chạy qua ECS exec in log ra stdout, **không vào CloudWatch**.
- **Script tạm:** `.tmp-session/ecsrun.sh` (S3 + ECS exec, `sleep 320 |` giữ stdin, `timeout 300`), đã xoá cuối phiên.
