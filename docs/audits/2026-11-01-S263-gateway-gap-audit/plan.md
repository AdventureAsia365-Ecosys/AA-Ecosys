# Kế hoạch hoàn thiện AI gateway v2 (S263)

Nguồn: kết quả rà 59 gap đã xác nhận (PC, RW, TP, INFRA, CRM, X, CIS, OPS), đối chiếu ADR 0009 / 0008a, audit S261 và S262, cùng code trên main: CIS 0982cbd9, TP c845b62, Partner d395b7a, Infra 1370c7b. Phiên này chỉ đọc, chưa chạy AWS, DB hay LLM.

Tình trạng hôm nay: acc3 vẫn báo Error 002, chưa có khoá Anthropic, kết nối OpenAI chưa có trần. Vì vậy mọi Done-when bên dưới chọn cách kiểm live được ngay ở 0 USD: dòng refused 0 USD trong ledger, provider stub, admin API, ảnh chụp Preview, truy vấn catalog. Phần nào cần LLM thật thì ghi rõ "phần live chờ LLM".

Quy tắc Done chung (aa-ship): merge, CI xanh, deploy **rollout COMPLETED**, rồi kiểm live như cột Done-when. Mọi PR có migration, grant, auth hoặc xoá dữ liệu phải qua agent review trước khi merge.

---

## 1. Gap đã xác nhận, nhóm theo lát giao được

Một lát tương đương một PR hoặc một nhóm PR nhỏ. Cột "Issue" ghi issue đã có, hoặc mã issue mới đề xuất N1…N9 (xem §3, mục T-20).

### A. Lõi gateway CIS (`shared/llm_client`, `role_config`, `invariant`)

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when (kiểm live) |
|---|---|---|---|---|---|---|
| **A1** Stage kill switch + declared degrade mode | CIS-2, OPS-11 (phần stage), CIS-4 | AA-CIS-App (migration + client + admin toggle + invariant) | M | $0 | N1 | Tắt stage `t9_write` trên Dev rồi gọi một lần: `llm_call_log` có dòng `status=refused`, cost 0, không có attempt tới provider. `/admin/llm-availability` hiện `t2_generate`, `t9_write`, `tp_compose` là "declared degrade", không còn là breach. Bật lại thì route chạy như cũ. |
| **A2** Khoá `model_tier` + tạo stage cho segment research | CIS-7, RW-11 (phần 4) | AA-CIS-App (migration thêm stage rows `segment_research*`, đổi request model ở `v1_pipeline`/`admin_pipeline`, `s1_batch.py:265`) | M | $0 | N1 | Chạy query "measure first" `GROUP BY` model_tier trên `llm_call_log`. POST có `model_tier` vào `/v1` hoặc admin rewrite thì nhận 422. Job segment research trên Dev ghi dòng ledger có `stage=segment_research*` (refused 0 USD cũng tính). |
| **A3** Dispatch: route deadline, retry do gateway giữ, gỡ path cũ | RW-11 (phần 1–3) | AA-CIS-App (+ `tools/llm-core` nếu chạm core) | L | $0 | N1 | `SELECT count(*) WHERE route_deadline_s IS NULL` trên `llm_role_config` bằng 0. Adapter Anthropic/OpenAI có `max_retries=0`, botocore `max_attempts=1`, chain dừng ở tối đa 6 attempt (unit test). Ledger không còn `legacy_chain`, `s2_vendor_deployment`, `catalog_fallback_*` sau deploy. |
| **A4** Luật writer/judge theo family, kiểm lúc gọi | RW-08 | AA-CIS-App (judge, client, eval_judge, regression, admin) | S–M | $0 | N1 | Ngay bây giờ: lý do từ chối trong admin là tiếng Anh (PATCH judge cùng vendor trả 422 kèm text EN). Sau khi chấp nhận d12: eval runner từ chối cặp judge/writer cùng family (unit test + một PATCH thử trên Dev). |
| **A5** Chặn route theo `served_roles` | RW-09 (phần CIS) | AA-CIS-App (`vendor_route.deployment_plan`) | M | $0 | N1 | Một deployment acc2 có `served_roles` không gồm writer thì bị loại khỏi plan của stage writer (unit test + `/admin/llm-availability`). Việc drop `account_route` để sau, đi cùng E3 và F2 qua contract view. |
| **A6** Invariant khi lưu route + báo cáo hằng đêm | RW-10 | AA-CIS-App (`patch_llm_route`, job digest) | S–M | $0 | N1 | Trên Dev, PATCH một route phá invariant thì nhận 200 kèm `warnings[]`. Digest đêm có dòng invariant. Chế độ chặn cho prod để tới go-live. |
| **A7** Budget tập trung: app daily, stage/job kind, eval, ad-hoc | CIS-1, OPS-07 | AA-CIS-App (migration mở rộng `spend_budget_scope_check`, pre-call check trong `LLMClient`, coverage tính theo call site) | M–L | $0 | N2 | Đặt cap `stage:t9_write` = 0.01 USD trên Dev rồi gọi: nhận `BudgetExceeded` và dòng refused 0 USD. Tab Budgets hiện coverage theo call site. Số tiền cap chờ tech lead (T-8). |
| **A8** Tenant budget fail closed + `hard_stop` mặc định bật | CIS-3 | AA-CIS-App (`tenant_budget.py`, default migration) | S | $0 | N2 | Unit test: DB đọc được nhưng counter lỗi thì từ chối. Seed một dòng Dev cho tenant E2E: T-stage vượt cap thì dừng chờ duyệt (refused row). |
| **A9** Ledger cho embedding | OPS-02 | AA-CIS-App (`embed.py`, `EmbedResponse`, 2 caller) | S | $0 | N1 | Tắt tạm deployment `cohere-embed-v4` acc2 trên Dev rồi gọi embed: có dòng `status=error/refused`, 0 USD, có `connection_key`, `latency_ms`, `attempt_no`. Bật lại thì dòng ok cũng có đủ ba trường này. |
| **A10** CIS chạy trên core `shared/aa_llm` | PC-4, CIS-8 | AA-CIS-App (+ `tools/llm-core` MANIFEST, resync copy ở TP/Partner) | M | $0 | N1 | Bước 0: đưa outcome `truncated`/`failed_outcome` vào `aa_llm`. Sau đó `git grep "from shared.aa_llm"` thấy trong `shared/llm_client`. Parity test đổi thành identity test. Sau deploy, một dòng ledger mới có shape giống trước (so cột). |

### B. Provider ngoài LLM (Jev, DataForSEO, Geoapify) và cảnh báo

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **B1** `enabled` thật cho typesafe/dataforseo/geoapify + ghi `access_state`/`last_probe_at` + Jev `connection_key` | PC-7 | AA-CIS-App (`decide.py` 2 call site, `dataforseo_client`, `geocoder`, PATCH allowlist) | S–M | $0 | N3 | Tắt Jev trong Providers: lần decide sau có dòng refused 0 USD với `account` khác NULL. Bật lại ok. `access_state` đổi theo. |
| **B2** Probe embedding + Geoapify | PC-6 | AA-CIS-App (`llm_probe_job`) | S | ≈$0 (<0.01 USD/tháng, Geoapify nằm trong free credit) | N3 | Chạy probe job một lần trên Dev: có dòng `adhoc_conn_test` cho `cohere-embed-v4@acc2`/`@acc3` và một dòng Geoapify. `last_probe_at` có giá trị. |
| **B3** Circuit chung, dùng được giữa các task, cho provider ngoài LLM | PC-8 | AA-CIS-App (migration health theo provider hoặc `model_key` nullable, Jev ngắt cả khi outage/5xx, circuit cho DFS và Geoapify, bell + e-mail) | M | $0 | N3 | Ép Jev trả 5xx bằng base_url giả trên Dev: circuit mở cho cả hai task api/worker, có bell `*_circuit_open` và một dòng trong hàng e-mail. Trả lại base_url thì circuit đóng. |
| **B4** E-mail cảnh báo DFS low balance và reconcile mismatch + digest có số dư | OPS-09 | AA-CIS-App (`ops_alerts`, `digest.py` dùng lại `money_sources.balances()`) | S | $0 | N3 | Hạ ngưỡng DFS trên Dev rồi chạy balance check: có bell và job e-mail. Digest có mục Jev/DFS/Geoapify, reconcile, tenant budget. |
| **B5** Sổ top-up chung + `topups_minus_spend` cho anthropic/openai | OPS-08 | AA-CIS-App (migration top-up chung, cảnh báo low credit) | S | $0 | N3 | Nhập số dư OpenAI mở đầu (T-2), đặt ngưỡng cao hơn số dư: có bell low-credit. Providers hiện số dư ước tính cho OpenAI. |

### C. Trang AI providers (admin)

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **C1** Thêm p50/p95, tỉ lệ lỗi cho mọi connection; dòng Guardrails, CRM LLM, Mapbox (static); UI toggle cho B1; sửa `guide.ts` và `guide.vi.ts` | PC-9, OPS-10 | AA-CIS-App (`ai_gateway.py`, `ProvidersTab.tsx`, token CRM passthrough) | S–M | $0 | N3 | API `/admin/ai-gateway/providers` trả `latency_p50/p95` và `error_pct`. Ảnh chụp Preview ở desktop, mobile, light và dark (aa-ui-verify) có các dòng Guardrails, CRM, Mapbox. Console không có lỗi. |

### D. Ledger, vận hành, quản trị route

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **D1** Seed `prompt_version` (32 dòng) + CI gate | OPS-03 | AA-CIS-App (+ bản copy migration ở Infra) | S | $0 | N1 | `SELECT count(*) FROM shared.prompt_version` bằng 32. Dòng ledger mới của một stage có trong manifest (refused cũng được) có `prompt_version` khác NULL. CI fail khi bump manifest mà thiếu migration. |
| **D2** Model lifecycle thành dữ liệu | OPS-04 | AA-CIS-App + AA-CIS-Infra (IAM `bedrock:ListFoundationModels` trên acc3 và aa365) | S–M | $0 (cần apply có MFA) | N1 | Job sync đêm điền `lifecycle_status` và `eol_date`. Digest có cảnh báo EOL 90 ngày. Mọi model đang route có trạng thái khác NULL. |
| **D3** Chốt contract ledger: sửa ADR §8 theo cách đọc federated + làm phần nhỏ | OPS-01 (phương án b + phần nhỏ) | root ADR 0009 + DM-10.4 + AA-CIS-App (`geocode_call` thêm status/latency/app/stage; Jev `role='decide'`) | S–M | $0 | N1 | Sau migration, dòng geocode mới có đủ các cột trên. Dòng Jev mới có `role='decide'`. Tab Calls hiện đúng outcome. |
| **D4** Kill switch cho Batch + dòng trigger T-BATCH | PC-5, OPS-12 | AA-CIS-App (`/admin/s1-batch/submit` trả 503) + root backlog §1 / `plan.json` | XS | $0 | N1 | `curl -X POST …/admin/s1-batch/submit` trả 503 kèm lý do. Backlog và `plan.json` có dòng T-BATCH (chi batch hơn 100 USD/tháng hoặc chạy lại cả catalog). |
| **D5** Embedding space registry (phần miễn phí) | OPS-13 | AA-CIS-App (migration registry, tham chiếu space trên 5 bảng vector) | M | $0 (thử re-embed <1 USD tách riêng) | N1 | Mọi cột vector đều trỏ tới space `cohere-embed-v4/1536/…`. Có runbook re-embed với shadow column. |
| **D6** Đối soát hoá đơn ≤5 % | OPS-06 | AA-CIS-App | M | trả phí nhỏ (snapshot Cost Explorer khoảng 0.3–0.6 USD/tháng) | AA-804 (đã có) | Snapshot Cost Explorer tự chạy hằng ngày. Có báo cáo tháng theo account và provider với kết luận ≤5 %. Totals của `crm.llm_call` được gộp vào phép so. |
| **D7** Đổi route phải có bằng chứng | OPS-05 (+ bậc rollback của RW-07) | AA-CIS-App (cả 2 PATCH: model và route; tra `prompt_eval_runs`; break-glass có lý do + alert) | S | $0 | N4 | PATCH writer/judge thiếu run id: nhận 422. Có run id hợp lệ: 200 và audit_log lưu run id. Dùng break-glass: 200 kèm bell. |
| **D8** Gỡ route chết | CIS-10 | AA-CIS-App (migration) + TP (bảng Route) | S | $0 | N1 | Retire `s1_atom_writer`, `tp_extract`, `tp_component_embed`. `t10_claims` chuyển sang trạng thái disabled/planned. Sinh lại `llm-routes.md` và register thì không còn ba stage kia. |

### E. TripPlanner trên registry dùng chung

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **E1** Coi `truncated` là lỗi + route deadline | TP-3 (phần truncation và deadline) | AA-TripPlanner-Web (`llm_gateway.generate_text`) | S | $0 | N5 | Unit test: `stop_reason=max_tokens` thì failover hoặc raise, không trả text. Live: deploy Lambda, request `tp_compose` trả narration ở chế độ degrade, có dòng ledger, không crash. Phần live với LLM thật chờ LLM. |
| **E2** `prompt_version`, `prompt_hash`, `request_id` trên ledger TP + CI gate | TP-4 | TP + dòng registry `tp_*` phía CIS (sau D1) | S | $0 | N5 | Dòng `app=tripplanner` mới có `prompt_hash` khác NULL. CI fail khi prompt đổi mà không bump. |
| **E3** Dispatch theo deployment + breaker theo connection + `pricing.quote` + data scope | PC-2, RW-13, TP-2, TP-3 (phần breaker) | TP + migration CIS append cột vào view v1 (connection kind/account không bí mật, trạng thái health/circuit; gộp params cho E4) | M–L | $0 | N5 | Khi circuit acc3 mở trên Dev (đang có thật vì Error 002), request TP bỏ qua acc3 ngay, ledger không có attempt acc3 sau ngưỡng, `pricing_mode` lấy từ core. Không còn `SUPPORTED_ACCOUNTS`. |
| **E4** TP áp params stage × model | TP-5 | TP (+ dùng chung migration view của E3) | M | $0 | N5 | Đặt một dòng `stage_model_params` cho `tp_compose` trên Dev: request body (stub client test + log) mang temperature/effort đúng thứ tự ưu tiên. Ưu tiên thấp vì hiện chưa có dòng params nào. |
| **E5** Gỡ fallback bảng + CIS REVOKE + drop `tripplanner.llm_spend_daily` | TP-1 | TP, rồi CIS (revoke), rồi `tp-NNN` drop (DRY RUN) + bản copy Infra | M | $0 | N5 | Làm theo thứ tự: (1) xác nhận live TP đọc view; (2) PR TP fail closed; (3) migration revoke; (4) drop. Done khi grant `shared.llm_role_config` và `llm_model_catalog` không còn cho role TP (xem db-schema-reference) và TP vẫn chạy degrade bình thường. |

### F. CRM (AA-Partner) trên core

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **F1** CRM gateway dùng `aa_llm`: errors.classify, pricing.quote (giá lấy qua contract view), ledger status, family key, budget.decide | PC-3, CRM-1 | AA-Partner (+ migration contract `crm-NNN` cho CHECK) | M | $0 | N6 | Draft stub trên Dev: `crm.llm_call` có `family='anthropic'`, outcome theo class chung. Stub cắt ngắn ghi `status=truncated`, không ghi `ok`. |
| **F2** Stage profile trong schema `crm` + route nhiều attempt + kill switch theo stage | CRM-2, RW-14 | AA-Partner (migration `crm-NNN` + loader + gateway) | M | $0 | N6 | Tắt profile `crm_draft`: endpoint draft trả refused và có dòng 0 USD. Bật lại thì stub draft ghi route theo profile. |
| **F3** UI draft trong trip workspace + `crm.ai_draft` (R39) + kiểm entitlement `ai_assist` | CRM-4 | AA-Partner | M | $0 (stub) | N6 / AA-980 | Bấm "Draft" trên Preview CRM: hiện panel, tạo dòng `ai_draft`. Tenant không có `ai_assist` nhận 403. Có ảnh chụp aa-ui-verify. |
| **F4** Chạy Bedrock thật cho CRM | CRM-3 | AA-CIS-Infra + AA-Partner | M | trả phí nhỏ (~0.001 USD/draft) | N6 | Chờ acc3 hết lỗi và T-12. Một draft Haiku thật đi qua guardrail, dòng ledger có giá theo catalog. |

### G. CI guard chống gọi vòng gateway (4 repo)

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **G1** Mở rộng guard CIS: `messages.create`, `responses.create`, `embeddings.create`, `create_model_invocation_job`, `apply_guardrail`, host vendor qua httpx, quét thêm `scripts/`; xoá 6 script acc1 cũ | PC-11, X-1, OPS-14 | AA-CIS-App | S–M | $0 | N7 | CI xanh với guard mới. `git grep` theo số tài khoản acc1 trong repo không còn kết quả. |
| **G2** Guard cho TP, CRM, Booking + một dòng trong Booking CONTEXT (d13) | X-1, OPS-14 | TP, Partner, Booking (mỗi repo 1 test) | S | $0 | N7 | Ba PR CI xanh. Một commit thử có `converse()` ngoài adapter thì guard làm CI fail (ghi trong PR). |

### H. App profile + capacity S12

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **H1** App profile: AI on/off, `bulk_paused`, budget mặc định, degrade mode; TP đọc cap từ profile, có cap cho stage offline; tín hiệu TP và CRM đổ vào bell/e-mail của CIS | RW-12 (app), X-2, OPS-11 (app) | CIS (bảng + admin), TP, Partner (cùng shape) | L (chia a: CIS, b: TP, c: CRM) | $0 | N2 | Tắt AI cho app `tripplanner` trong admin: TP trả degrade, có dòng refused. Tín hiệu `llm_spend_alert` của TP sinh bell + e-mail. |
| **H2** Capacity S12: TPM limiter, các line dev/prod/bulk, tự pause wave khi circuit prod mở, backpressure khi claim job | RW-12 (S12) | AA-CIS-App (+ `booking.job`/`crm.job` nếu áp dụng) | L | $0 | N2 (hạn ≤30/11) | Test tích hợp: mở circuit thì wave đang chạy chuyển sang paused và job claim bị hoãn. Trên Dev, ép TPM thấp thì request thứ N+1 chờ chứ không lỗi. |

### I. Warm path, model mới, data scope (phần lớn chờ tech lead)

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **I1** Bật warm path Anthropic API | PC-1, RW-01 | Console (tech lead) + CIS data/config + root runbook | S | trả phí: top-up 50 USD một lần, trần 150 USD/tháng; probe <0.001 USD | AA-1004 (BO-2) | Secret `aa-llm/dev/anthropic-direct` có key. Connection enabled, `monthly_budget_usd=150`, cost policy hard stop. `aa1002_anthropic_probe.py` trả ok, có dòng ledger. Runbook bỏ nhãn UNTESTED. |
| **I1b** Sửa các dòng runbook đã cũ (S5/S10 đã ship, 50 USD đã duyệt) | RW-01 | root `docs/ops/runbooks/llm-anthropic-api-key.md` | XS | $0 | AA-1004 | PR docs merge xong. Làm được ngay, không chờ key. |
| **I2** Migration scope: A-series writer được `vendor_direct` | RW-02, CIS-5 (scope) | CIS (migration) + root (register, ghi chú ngoại lệ Dev cho T-stage trong ADR 0009) | S | $0 | N4 | Chờ T-3. DB build từ migration có `{aws_only, vendor_direct}` cho 5 stage writer A-series. T/TP giữ `aws_only` ngoài Dev. Register khớp với Dev. |
| **I3** Trần OpenAI + chuyển key sang secret | RW-04, OPS-08 (cap) | CIS (PATCH) + Infra (secret, gỡ env khỏi task def) | S | ~0.40 USD/tháng (secret); trần là mức tối đa | AA-1018 | `monthly_budget_usd=10` và alert 80 % trên `openai-direct`. Task def không còn `OPENAI_API_KEY`. Probe ok qua secret. |
| **I4** Failover drill hằng tháng + canary chéo path | RW-05 | CIS (job/script + schedule) + Infra (schedule) | M | build $0; ~0.25 USD/lần drill, canary ~0.40 USD | N4 | Build và test với fake ngay được. Lần đầu chạy chân judge sau I3, chân writer sau I1: báo cáo chi phí, cả hai chân xong trong route deadline. |
| **I5** S11: stage dùng key cũ (21 stage) | RW-03, CIS-6 | CIS (+ TP cho `tp_compose`, `tp_extract`) | L | trả phí (~13 USD thử, TL-12) | N4 | Chờ LLM và T-4. Mỗi stage writer chuyển xong thì có kết quả A/B và yes của tech lead. Stage validate chuyển sau khi qua ladder. |
| **I6** Route fallback judge/validate sang acc2 | RW-06 | CIS | M | trả phí nhỏ (smoke <0.10 USD/model) | AA-900 | Chạy được trên acc2, không bị khoá vì acc3. Qua contract smoke và A/B thì PATCH route và báo cáo. Judge cần 40 nhãn (TL-10). |
| **I7** Qualification harness: candidate arm trong R2, smoke 3 call, cost/tour + p95, targeted shadow, rollback, UI ladder | RW-07 | CIS | M–L | build $0 | AA-900 | Chạy harness với provider giả ra báo cáo đủ các bar. Tab Models có ladder. |
| **I8** Data scope d10: maker, geography, tenant fail closed | CIS-9 | CIS (+ TP đọc view) | M | $0 | N4 | Tenant stage gọi thiếu tenant thì bị refused. Stage có maker không nằm trong allowlist thì bị chặn (unit test + dòng refused trên Dev). |
| **I9** Invoker role riêng cho từng app (TP, CRM) | INFRA-1 | AA-CIS-Infra (2 root) + config TP/Partner | S–M | $0 (apply có MFA) | AA-1004 (sub-task) | Plan và apply xong. Role `AA3-Bedrock-Invoker-TripPlanner`/`-CRM` có tag App. AssumeRole kiểm được ngay. InvokeModel chờ acc3. |

### J. Tài liệu và governance (repo gốc)

| Lát | Gap gộp | Repo | Cỡ | Chi phí | Issue | Done-when |
|---|---|---|---|---|---|---|
| **J1** Trang as-built cho gateway + sửa §4.3/§4.4 ecosystem-architecture + làm mới snapshot route | OPS-15 | root (+ Infra nếu gắn snapshot vào DB Schema Dump) | M | $0 | AA-1020 (phiên này) | Trang `docs/architecture/ai-gateway.md` qua lint front-matter. `llm-routes.md` có family và deployment, đề ngày mới. |
| **J2** AI Use Register v1 (gỡ dòng cũ, thêm `crm_scrub` và Batch, script CI kiểm stage ↔ register) + sửa DM-10.4/DM-11.1 + trỏ ADR ở CIS | OPS-16 | root + AA-CIS-App (ADR 0005–0008, 0012) | S | $0 | N8 | Script `tools/` xanh trên root PR. Register đổi sang `status: active` sau T-18. |
| **J3** Dòng kiểm lại failure domain + mục runbook | RW-15, OPS-17 | root backlog §1 + Done-when của AA-1004 + playbook | XS | $0 | AA-1004 | Backlog có dòng với trigger "AA-1004 org invite / đổi payer". Runbook có bước probe trước/sau và xét lại `failure_domain`. |

---

## 2. Thứ tự làm ngay trong phiên này (các lát $0)

Nguyên tắc chia lane theo file sở hữu:

- **Số migration CIS do một lane giữ** và cấp trước: 325 D1, 326 A1, 327 D8, 328 A2, 329 view append cho E3/E4. Gom các migration đã merge để apply DB Migrate một lần trong cửa sổ bảng job rảnh. Acc3 đang khoá nên nhiều khả năng các bảng job đều rảnh, nhưng phải kiểm `shared.job`, `booking.job`, `crm.job` trước khi apply.
- Ba file nhiều lát cùng chạm phải đi theo thứ tự:
  - `admin_llm_ops.py`: B1 → B4 → A4/A6/D7.
  - `admin_pipeline.py`: D4 → A2.
  - `ProvidersTab.tsx`: chỉ lane C. Phải phối hợp với **AA-1006** (chuyển admin lên kit): làm C1 trước khi AA-1006 tới `admin/ai-gateway`, hoặc AA-1006 bỏ qua thư mục đó cho tới khi C1 merge.
- Partner: lane F chỉ chạm `app/llm/` và `crm-NNN` riêng. Phải giữ số `crm-NNN` trước với lane AA-958/959/960.

### Wave 1 (bắt đầu ngay, chạy song song)

| Lane | Thứ tự | File chính | Ghi chú |
|---|---|---|---|
| **L1 Lõi CIS + migration** | D1 (325) → A1 (326) → A9 → A8 | `prompt_registry`, `role_config`, `client.py` (cổng trước attempt), `invariant.py`, `embed.py`, `tenant_budget.py` | A1 và D1 là PR migration nên cần agent review. A8 cần tech lead đồng ý seed Dev (T-9). Trong lúc chờ thì làm phần fail closed. |
| **L2 Provider ngoài LLM** | D4 → B1 (backend) → B4 → B2 | `admin_pipeline.py` (1 hunk), `decide.py`, `dataforseo_client.py`, `geocoder.py`, `ops_alerts.py`, `digest.py`, `llm_probe_job.py` | Làm D4 trước nhất (XS, đóng đường Batch không có guard). B2 tốn <0.01 USD/tháng, đã nằm trong khoản probe được duyệt. |
| **L3 Trang Providers** | C1 (gồm toggle cho B1, sau khi B1 merge) | `ai_gateway.py`, `ai_gateway_calls.py`, `ProvidersTab.tsx`, `guide*.ts` | Phối hợp AA-1006. Ảnh chụp theo aa-ui-verify. |
| **L4 TripPlanner** | E1 → E2 (sau D1 apply) | `backend/shared/llm_gateway.py`, `assembly/agent.py` | Mọi lát TP đều sửa `llm_gateway.py` nên phải đi tuần tự. |
| **L5 CRM gateway** | F1 → F2 | `api/app/llm/*`, `crm-NNN` | Tách khỏi lane CRM-28/29 (channels, workflow). |
| **L6 CI guard** | G1 (CIS) ∥ G2 (TP, Partner, Booking) | chỉ test + xoá script acc1 | Nhanh, ít đụng file. Nếu guard bắt được call cũ thì đưa vào ALLOWED kèm lý do, không sửa trong lane này. |
| **L7 Tài liệu** (gộp với lane AA-1020) | I1b → J3 → J2 → J1 | root `docs/` | Dòng T-BATCH của D4 đi trong cùng root PR. |

### Wave 2 (khi Wave 1 merge xong, cùng phiên nếu còn thời gian)

1. L1: A2 (328, cần L2 đã merge D4) → A6 → A4 (phần lý do tiếng Anh).
2. L4: migration view 329 do L1 cấp số → E3.
3. L2: B5 (sổ top-up) → B3 (circuit ngoài LLM, migration).
4. L1 hoặc L2: D8 (327, cần L4 sửa bảng Route TP sau E3).
5. A10 bước 0: đưa outcome `truncated` vào `tools/llm-core` rồi bump MANIFEST. Chỉ làm khi L4 và L5 đã merge để bot resync không đụng nhánh đang mở.

### Để phiên sau (lớn, hoặc cần tech lead / MFA trước)

A3, A5, A7, A10 (toàn bộ), H1, H2, D2 (IAM có MFA), D3 (sau T-14), D5, D7 (sau T-19), E4, E5, F3, I4 (build), I7, I8.

---

## 3. Việc cần tech lead

Mỗi mục có đề xuất trả lời sẵn và chi phí. Gom thành một trang quyết định để bấm chọn.

| # | Việc | Loại | Đề xuất trả lời | Chi phí |
|---|---|---|---|---|
| T-1 | Bật Anthropic API: đăng nhập Console, tạo workspace Dev có spend limit, tạo key, mua top-up, đặt trần org (BO-2 / AA-1004) | Console + chi tiền | **Đồng ý.** Top-up 50 USD (đã duyệt theo ADR 0009), trần connection 150 USD/tháng, hard stop 100 %. Agent ghi secret, bật connection, chạy probe. Bật xong chưa route writer sang API ngay; ưu tiên route là quyết định riêng ở T-3. | 50 USD một lần; probe <0.001 USD |
| T-2 | Trần OpenAI + số dư hiện tại | Quyết định | **10 USD/tháng, alert 80 %.** Cho số dư OpenAI hiện tại để ghi làm top-up mở đầu (B5). Chuyển key sang secret `aa-llm/dev/openai-direct`. | ~0.40 USD/tháng (secret) |
| T-3 | Mở `vendor_direct` cho A-series writer bằng migration (`s1_generate`, `s1_flag_fix`, `s1_itinerary_nudge`, `a0_column_map`, `supply_content_writer`) | Quyết định | **Đồng ý.** T-stage và `tp_*` giữ `aws_only` ngoài Dev cho tới AA-820. Ghi ngoại lệ T-stage trên Dev (dữ liệu synthetic) vào ADR 0009 và register. | $0 |
| T-4 | Hướng S11 cho 21 stage dùng key cũ | Quyết định + chi tiền | **Phương án (b): chuyển sang `haiku-5-5`/`sonnet-5-5`.** Phương án này phủ được cả `tp_compose`/`tp_extract`, còn (a) không phủ. Chạy thử khi LLM có lại. Mỗi stage writer cần yes riêng; stage validate thì agent tự chuyển sau ladder. | ~13 USD (TL-12) |
| T-5 | Chấp nhận ADR 0009 decision 12 (ladder + bar) | Quyết định | **Chấp nhận nội dung decision** để làm I7, D7, A4. 40 nhãn hiệu chuẩn vẫn hoãn theo TL-10 nhưng dùng chung với AA-900. | $0 (40 nhãn ≈ 2 giờ của tech lead, sau) |
| T-6 | Chấp nhận ADR 0009 decision 10 (data scope) | Quyết định | **Chấp nhận cơ chế ngay** (tenant fail closed, luật tenant chung). Danh sách maker và geography chờ AA-820. Mặc định tạm: giữ maker hiện có, không dùng profile `global.` cho tenant và TP. | $0 |
| T-7 | Bedrock Batch | Quyết định | **Kill switch 503** cho tới trigger T-BATCH (XS, khớp TL-13). Không làm guard trước submit lúc này. | $0 |
| T-8 | Số tiền budget: cap CIS app daily, cap theo job kind (per-run/per-day), eval/ad-hoc theo tháng, TP mirror | Quyết định | **Quy tắc đề xuất:** cap = p95 chi/ngày 30 ngày gần nhất × 1.5, lấy từ `llm_call_log`. Agent tính ra số cụ thể (đọc DB, $0) rồi đưa duyệt. Mốc đối chiếu S249: 0.0768 USD/tour. | $0 (cap là mức tối đa) |
| T-9 | Tenant AI budget | Quyết định | **Seed Dev mặc định 5 USD/tháng mỗi tenant, `hard_stop` bật.** Giá theo gói lấy từ business owner sau. | $0 |
| T-10 | CRM đọc catalog/registry CIS qua contract view; CRM spend tính vào budget connection | Quyết định | **Đồng ý cả hai:** dùng contract view (đúng ADR 0008a). Budget connection cộng `crm.llm_usage_daily` qua `crm.ops.v1`. Fallback CRM chỉ dùng Bedrock cho text đã scrub. | $0 |
| T-11 | Cho `tp_compose` dùng `vendor_direct` | Quyết định | **Chưa.** Giữ `aws_only` + degrade cho tới AA-820 và bước PII của TP (ADR 0009). | $0 |
| T-12 | Draft CRM trả phí đầu tiên + apply env/IAM | Chi tiền | **Đồng ý khi acc3 hết Error 002.** Giới hạn ≤20 draft thử. | ~0.001 USD/draft + ~0.0001 USD guardrail |
| T-13 | Dòng Mapbox chỉ static (free-tier + link) | Quyết định | **Đồng ý.** | $0 |
| T-14 | Contract ledger (OPS-01) | Quyết định | **Phương án (b) + phần nhỏ:** sửa ADR §8 và DM-10.4 theo cách đọc federated; thêm status/latency/app/stage cho `geocode_call`; Jev `role='decide'`. | $0 |
| T-15 | Thử re-embed một bảng trước khi AA-1004 đổi billing/org acc2 | Chi tiền | **Đồng ý, làm trước 01/12** trên bảng nhỏ nhất (`question_embedding`). Registry làm trước, $0. | <1 USD |
| T-16 | Đối soát hoá đơn: key usage read-only Anthropic/OpenAI, snapshot Cost Explorer theo lịch, CIS đọc `crm.llm_call` | Console + chi tiền | **Đồng ý cả ba.** Key tạo trên console (trình duyệt), lưu dưới `aa-llm/`. | ~0.3–0.6 USD/tháng |
| T-17 | Apply Terraform có MFA (invoker role theo app; IAM ListFoundationModels) | Thao tác | Gom thành **một cửa sổ tắt auto mode**: acc3-bedrock root + aa365 root. | $0 |
| T-18 | Duyệt AI Use Register từ draft sang active | Duyệt | Duyệt sau khi J2 merge. | $0 |
| T-19 | Luật "đổi route writer/judge phải có run id" + break-glass | Quyết định | **Đồng ý, kèm break-glass** (lý do bắt buộc, chỉ admin, có alert) vì hiện chưa chạy eval được. | $0 |
| T-20 | Tạo issue Linear mới (gói Free) | Duyệt | **8 issue:** N1 hardening lõi CIS, N2 app profile + budget + S12, N3 provider ngoài LLM + trang Providers, N4 warm path + route governance, N5 TP trên registry, N6 CRM trên core, N7 CI guard, N8 register/docs. Phần còn lại vào AA-1004, AA-900, AA-1018, AA-804, AA-1020. | $0 |
| T-21 | Degrade mode của từng app (wording sản phẩm) | Quyết định | CIS: `queue_retry`. TP: narration cơ bản. CRM: `manual_reply_needed`. Booking: không có AI. | $0 |
| T-22 | Quyết định billing AA-1004 (payer/org của acc2) | Quyết định | Đã có trong AA-1004. Kiểm lại failure domain gắn với lúc thực hiện, không phải cố định ngày 01/12 (J3). | $0 |

---

## 4. Gap bị bác và chỗ đã sửa

Không gap nào bị bác hoàn toàn: cả 59 đều đúng. Các phần sai hoặc phóng đại đã sửa trong bảng trên:

- **PC-1 / RW-01 / CIS-5** trùng nhau và đã có chủ là AA-1004 (BO-2), không nên tính vào danh sách "16 mục chưa có issue".
- **PC-2**: TP **có** đọc `v_llm_gateway_config_v1`, chỉ bỏ qua `deployments` và `allowed_scopes`.
- **RW-13**: các hằng model không quyết định route; route vẫn lấy từ view. View đã có `deployments`.
- **PC-3**: CIS **thấy** chi CRM (tab Calls, platform_cost). Thứ còn thiếu là enforce theo connection. CRM đã có cap riêng cho từng agency.
- **PC-5**: điểm "auth x_admin_secret cũ" sai, vì route đã qua staff middleware. Bỏ điểm đó.
- **PC-8**: Jev **có** bell + e-mail khi hết credit (402). Gap còn lại là breaker theo process và không ngắt khi outage.
- **CIS-7**: `seed_align/adjudicate.py` không tồn tại. `segment_research` không có stage nào chứ không chỉ hard-code. Thêm `s1_batch.py:265`. `services/eval/regression.py` là ngữ cảnh eval, được phép.
- **CIS-10**: "probe scope" bị phóng đại vì probe chạy theo connection. `t10_claims` chỉ disable, không retire.
- **RW-12**: S12 không phải "chưa làm gì": phân loại 429/402 Anthropic và alert circuit đã ship.
- **RW-15 / OPS-17**: nửa "probe trước/sau" đã có probe hằng ngày lo. Chưa cần migration trước. Trigger là AA-1004, không phải ngày 01/12 cố định. Cỡ thật là XS, $0.
- **OPS-04**: mốc "khoảng 13/11 mất model Legacy" chưa kiểm được. Coi là rủi ro, không phải sự thật.
- **OPS-08**: "không cảnh báo nào kích được" là quá mức, vì probe vẫn bắt được `QUOTA_EXHAUSTED`. Cái thiếu là cảnh báo trước khi hết tiền.
- **OPS-13**: đã có fallback `cohere-embed-v4-acc3` cùng space. Điểm yếu là một model/vendor duy nhất, không phải một account.
- **RW-06 / RW-07 / INFRA-1**: gộp vào AA-900 / AA-1004, không tạo issue mới.
- **Mâu thuẫn chưa kiểm**: RW-15 nói `LLM_DAILY_PROBE` đang ON (Infra #574), OPS-04 nói OFF trên Dev. Lane L2 cần kiểm live task def và env trước khi viết B2.