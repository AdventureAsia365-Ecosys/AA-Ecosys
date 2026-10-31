---
id: OPS-08-s261-llm-capacity-plan
title: "Kế hoạch quota và năng lực LLM cho prod (S261)"
description: "Bản tư vấn cho tech lead: quota LLM prod xin ở đâu, 5 tầng giới hạn (AWS, connection, app, tenant, người dùng cuối), luồng B2C/B2B/B2B2C, giám sát, ổn định và scale, thêm app mới, bộ issue + mốc ngày, và việc cần tech lead / business owner duyệt."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1002, AA-642, AA-964, AA-1004, AA-880]
---

# Kế hoạch quota và năng lực LLM cho prod (S261, 31/10/2026)

Bản tư vấn viết cho tech lead (tiếng Việt, theo luật `docs/audits`). Đọc cùng:

- `../2026-10-31-S261-aws-bedrock-org-access/current-situation-model.md`: mô hình account đã chốt. Hôm nay có 3 account:
  acc4 `aa-management`, acc3 `aa-ai` (Bedrock), acc2 `aa-nonprod` (vẫn ở org của TrueIDC). `aa-prod` được tạo lúc
  go-live theo ADR 0018. Billing Transfer sang đại lý sớm nhất từ 01/12. Anthropic API trực tiếp là đường ngoài AWS.
  acc3 đang bị Error 002, case AWS đang mở.
- `../2026-10-31-S261-aws-bedrock-org-access/README.md`: các bước cấu hình org, SCP, role và quota (bước 9).
- `../2026-10-29-S258-aws-org-blueprint/README.md`: kế hoạch các lát của LLM gateway (S0–S11).

Cách làm: có 4 hướng nghiên cứu. Hai hướng đọc tài liệu AWS và Anthropic bản hiện hành (đọc ngày 31/10/2026; trang
Bedrock User Guide không ghi ngày cập nhật). Hai hướng đọc code ở các commit sau: CIS `1b6e9448`, TripPlanner `02dd9f1`,
Partner `df5ac86`, cộng cây làm việc của Infra.

- Không ghi account ID.
- Số liệu có ghi "(minh hoạ)" là giả định để tính thử, không phải số đo.
- Ý có ghi **(suy luận)** là kết luận của bản này, nguồn không nói thẳng.
- Bản này chỉ đọc. Không chạy lệnh ghi nào trên AWS hay DB.
- Rà phản biện 31/10 (cùng ngày): đối chiếu lại từng câu với trang AWS / Anthropic và code; sửa các câu nói mạnh hơn
  nguồn; chuyển các việc quá cỡ đội 2–3 người sang bảng "làm khi có trigger" (mục 5.8).

## 1. Trả lời ngắn

- **Quota prod xin ở đâu.** Ở **account gọi model**, theo từng region nguồn, từng model và từng loại profile
  (`us.` / `global.`). Theo ADR 0018, prod gọi qua role prod-only của `aa-ai`, nên
  quota prod chính là quota của `aa-ai` (acc3), **dùng chung với dev và wave**. Nếu sau này bật đường Bedrock tại chỗ
  trong `aa-prod` thì xin thêm quota cho `aa-prod`.
  - **Embedding là ngoại lệ phải chốt.** Model embedding bị chặn theo **RPM**, không theo TPM. Hôm nay TP search gọi
    Cohere Embed v4 **trên acc2** (`aa-nonprod`, 20 RPM theo TP `CONTEXT.md`), có dòng dự phòng trên acc3. Prod không
    được dựa vào account non-prod, nên trước go-live phải chọn: embed prod qua `aa-ai` (role prod-only) hay Bedrock tại
    chỗ trong `aa-prod`, rồi xin RPM trên đúng account đó **(suy luận** từ ADR 0012 d7 + ADR 0018 §3).
  - Tài liệu AWS không nói tới quota Bedrock cấp org: quota tính theo account × region. Ở cấp org chỉ có hai thứ liên
    quan: template tự xin quota cho account **mới tạo trong org** (tối đa 10 quota, org phải bật "all features"; không
    đổi quota của account đã có), và form Anthropic (FTU) nộp ở account quản trị thì account thành viên thừa hưởng.
  - Quota khác quyền truy cập. AWS ghi: tăng quota không cấp thêm quyền dùng model. Error 002 của acc3 là lỗi chặn ở mức
    account (case AWS), không phải vượt quota, nên xin quota không gỡ được **(suy luận)**.
  - Đại lý chỉ trả hoá đơn. Tài liệu AWS không ghi đại lý có quyền nâng quota Bedrock. Họ có thể giúp leo thang qua
    kênh partner hay không thì phải hỏi bằng văn bản (câu 15, 17, 18 của `reseller-questions.md` đã có sẵn).
- **Cách xin.** Service Quotas, mục "Cross-Region InvokeModel tokens per minute for {model}" (và quota Global nếu
  dùng `global.`). Sonnet 5.5 ở us-west-1 **không có In-Region**, chỉ có `us.` / `global.` (model card), nên quota
  on-demand một region không áp cho nó. Kèm số đo CloudWatch. AWS ghi: ưu tiên khách **có lưu lượng đang tiêu quota
  hiện có**, đơn có thể bị từ chối nếu không đạt điều kiện này. Nên phải chạy lưu lượng thật trước rồi mới xin. Tài
  liệu không nêu thời hạn xử lý. Mốc 4–6 tuần trước go-live là đệm của mình.
- **Theo app / tenant / khách.** AWS không có khái niệm quota theo app, tenant, đại lý hay khách B2C. Mọi phân chia đều
  phải nằm **trong gateway** (connection, budget, limiter). AWS chỉ giúp **gán chi phí**. Cách rẻ nhất cho đội 2–3
  người: mỗi app một role invoker trên `aa-ai` (đã là mẫu, ví dụ role CRM), AWS tự ghi danh tính người gọi vào hoá đơn
  (IAM principal attribution), cộng tag `App` đã kích hoạt. Chi phí theo tenant lấy từ sổ của gateway
  (`llm_call_log`, `crm.llm_call`), không lấy từ AWS. Request metadata chỉ nằm trong invocation log, không lên Cost
  Explorer, nên chưa cần (mục 4.2).
- **Đi qua gateway hay không.** Có. Mọi app, mọi lần gọi đều đi qua một core gateway dùng chung (lát S8, epic AA-642).
  Hôm nay mới CIS đi đủ đường. TripPlanner có client mỏng riêng, không có limiter, breaker hay budget connection. CRM
  có gateway riêng, lệnh gọi model còn là stub. Chưa xong S8 thì mọi trần trong gateway chỉ giữ được phần CIS.
- **B2C (TripPlanner).** Hiện chỉ có trần chung 5 USD/ngày và throttle theo route **dùng chung cho mọi khách**. Chưa
  có giới hạn theo IP, phiên hay người dùng. Một script có thể ăn hết trần trong ngày. Phải thêm limiter theo
  phiên/IP + bot check trước go-live.
- **B2B tenant Content studio.** Có quota số bài viết lại theo gói, nhưng **không chặn cứng** (giai đoạn trial, vượt
  quota thì tính phí). Không có trần USD AI theo tenant. Nên thêm trần USD/tháng theo tenant, theo mẫu
  `ai_budget_usd` của CRM.
- **B2B đại lý (CRM).** Đã có trần USD/tháng theo đại lý (mặc định 2 USD, fail closed) và cờ `ai_enabled` (mặc
  định tắt). Lệnh gọi của một đại lý đã chạy **lần lượt từng lệnh** (khoá advisory giữ tới khi ghi log), nên một đại
  lý không chiếm được nhiều slot cùng lúc. Còn thiếu: trần số lệnh/phút theo đại lý (chống vòng lặp tự động), cảnh báo
  75/90 %, luật chống prompt injection, và giá thật theo gói.
- **B2B2C (khách của đại lý).** Hôm nay khách của đại lý **không gọi LLM trực tiếp**: portal, form và trang trip chỉ
  hiển thị nội dung đã viết sẵn. Giữ nguyên như vậy tới khi có thiết kế riêng. Nếu sau này có trợ lý cho khách thì nó
  chạy trong budget của đại lý, có trần con theo từng khách, qua scrub, và báo rõ là AI.
- **Giám sát.** Đã có: `shared.llm_call_log`, thẻ availability, digest OPS-12, đối soát chi phí hằng đêm, AWS Budgets,
  trang chi phí theo app (đã cộng chi phí AI của CRM qua `crm.ops.v1`, AA-936). Còn thiếu: cảnh báo tức thời khi
  circuit mở, 3 alarm CloudWatch (throttle, lỗi client không lọc dimension, lỗi server) trên `aa-ai`, % budget theo
  tenant, và đưa CRM vào thẻ availability + digest. Lưu lượng HTTP thường (API Gateway, ALB, CloudFront) không thuộc
  bản này; ở đây chỉ bàn lưu lượng LLM. Ngưỡng ở mục 4.
- **Thêm app mới.** App mới không có account AWS riêng và không có client model riêng. Nó dùng core gateway sau S8,
  có connection + budget + stage + data scope riêng, khai báo đường giáng cấp (khi AI không chạy) và SLO trước lần gọi
  prod đầu tiên. Checklist ở mục 6.
- **Có nên theo dõi bằng issue / checklist / deadline không.** Có, nhưng ít issue (Linear Free). Tái dùng AA-1002,
  AA-642, AA-964, AA-1004, AA-880, AA-896. Chỉ đề xuất 2 issue mới, chờ tech lead đồng ý mới tạo. Checklist có mốc ngày
  ở mục 7. Việc chưa tới lúc làm thì không tạo issue, chỉ ghi trigger ở mục 5.8. Không dùng AA-1006: đó là issue UI
  kit của CIS, không liên quan.
- **Phải làm gì ngay (≤ 2 tuần).**
  - Đọc và ghi lại quota hiện tại của acc3.
  - Bật đường Anthropic API cho Dev (AA-1004 bước 0a).
  - Điền `monthly_budget_usd` + `rpm_limit` / `max_concurrency` cho các connection.
  - Cảnh báo tức thời khi circuit mở.
  - Business owner hỏi đại lý bằng văn bản. Hạn AA-820 là 11/11.
- **Cỡ đội.** Với 2–3 dev, việc trước go-live gói trong: điền số, một lát S12 nhỏ, S8, hai issue mới (TP limiter,
  budget tenant), load test, đơn quota. Limiter chung qua Redis, invocation logging, region nguồn thứ hai, chia công
  bằng giữa tenant, Reserved tier: chỉ làm khi có trigger (mục 5.8).

## 2. Quota theo 5 tầng

Mỗi lệnh gọi phải qua **cả 5 tầng**. Tầng trên là trần cứng của AWS. Các tầng dưới là trần do mình đặt, để không tầng
nào ăn hết phần của tầng khác.

| Tầng | Ai đặt / ai xin | Cơ chế | Đã có trong code / hạ tầng | Thiếu |
|---|---|---|---|---|
| 1. AWS account × region × model | Tech lead xin trên account gọi model (`aa-ai`; thêm `aa-prod` nếu bật đường 2). AWS duyệt | Service Quotas: TPM on-demand, TPM cross-Region, RPM (chỉ một số model; embedding tính theo RPM), TPM Global, "Cross-Model Max Tokens Per Day" | Không có code nào đọc quota. AWS Budgets trên acc3 (250 USD, chỉ cảnh báo) | Ghi lại quota thật. Tính nhu cầu. Đơn xin có số đo. Alarm throttle |
| 2. Connection trong gateway | Tech lead, qua tab Connections (PATCH admin) | `rpm_limit`, `max_concurrency`, `monthly_budget_usd` + `llm_connection_cost_policy` (cảnh báo 80 %, chặn 100 %), breaker | Có schema, limiter, breaker và budget (S4, S10) | **Các dòng seed (migration 304) để NULL**, nên chưa có tác dụng (chưa kiểm số live). Limiter chạy theo từng task, chỉ đếm request, không đếm token. Đường legacy `haiku`/`sonnet` không qua limiter |
| 3. App / môi trường | Tech lead | Một hoặc nhiều dòng connection theo app × môi trường × lane. Trần ngày của TP | TP: `TP_DAILY_SPEND_CAP_USD` 5 USD/ngày cho stage online. CIS: `shared.spend_budget` theo job kind (không gồm S1/T2/T8/T9/A3) | Không có dòng tách dev / prod hay batch / interactive. Không có trần theo app cho CIS và CRM. TP và CRM không đọc connection |
| 4. Tenant / đại lý | Giá: business owner. Số kỹ thuật mặc định: tech lead | CRM: `crm.tenant_settings.ai_budget_usd`. CIS: quota bài viết lại theo gói + RPM HTTP `/v1/*` theo tenant | CRM: có, fail closed, model còn stub. CIS: chỉ gán chi phí (`v_tenant_monthly_usage`), không chặn | Trần USD AI theo tenant cho Content studio. Trần tốc độ theo đại lý. Cảnh báo 75/90 % của CRM. Chia công bằng giữa các tenant trong hàng job |
| 5. Người dùng cuối | Tech lead (số), business owner (lượt miễn phí có phải tính năng bán hàng không) | Limiter theo IP / phiên khách / user đã đăng nhập ở BFF. Bot check | TP: throttle theo route (narrate 2 rps, search 10 rps), dùng chung cho mọi khách. Cache narration và embedding. CRM: limiter theo IP trên route công khai (không phải LLM) | **Không có giới hạn LLM theo người dùng ở đâu cả** |

### 2.1 Tầng 1: AWS account × region × model

**Đơn vị quota.** Quota tính theo account × region nguồn × model × endpoint × loại profile.

- Trên `bedrock-runtime`, mọi API (InvokeModel, Converse, Responses, Chat Completions) **dùng chung một quota** cho
  mỗi model.
- Profile `global.` có quota riêng, xem và xin ở region nguồn.
- Endpoint `bedrock-mantle` có quota input/output TPM riêng và xin qua case Support, không qua Service Quotas. Hôm nay
  gateway gọi runtime. Nếu sau này dùng mantle thì phải xin riêng.

- Model embedding (Cohere Embed v4 của TP) bị chặn theo **RPM**, không theo TPM. Tính nhu cầu embedding bằng
  request/phút.

**Mặc định có thể thấp hơn bảng công bố.** AWS ghi quota mặc định của một account có thể được điều chỉnh theo yếu tố
vùng, tuổi account, lịch sử dùng, lịch sử thanh toán, dấu hiệu gian lận, nên có thể thấp hơn bảng công bố. Phải đọc
giá trị thật trong Service Quotas. Đổi payer (vào org, Billing Transfer) có thể làm quota đổi **(suy luận** từ "lịch
sử thanh toán" + U10 trong bản S261). Sau mỗi lần đổi phải đọc lại.

**Quota bị tiêu thế nào.** Đây là chỗ hay tính sai.

- Lúc bắt đầu một request, AWS giữ chỗ `input + max_tokens`. Lúc kết thúc, AWS tính lại thành
  `input + cache_write + output × hệ số burndown`. Cache read không tính.
- Hệ số burndown của output: Opus 5.5, Sonnet 5, Opus 5, Fable 5.1 là 10x; Claude 4.8 là 15x; Claude ≤ 4.7 (gồm
  Sonnet 4.6 của TP compose) là 5x.
- **Sonnet 5.5 và Haiku 5.5 không có trên trang này**, model card Sonnet 5.5 cũng không ghi. Hỏi AWS Support hoặc
  đo bằng CloudWatch trước khi tính. Bảng minh hoạ bên dưới giả định 10x.
- Hệ quả: `max_tokens` đặt rộng làm giảm số lệnh chạy song song, dù output thật ngắn. Ví dụ của AWS (model 5x): input
  3.000 + cache write 1.000 + `max_tokens` 32.000 giữ 36.000, nhưng chỉ tính 9.000.

Công thức tính nhu cầu cho từng route, áp cho giờ cao điểm (công thức của bản này, dựng từ cách tính của AWS; hệ số
đệm 1,5 là lựa chọn của mình):

```text
TPM giữ chỗ ≈ request/phút × (input + max_tokens)
TPM tính thật ≈ request/phút × (input không cache + cache_write + output × burndown)
Quota cần xin ≈ max(TPM giữ chỗ, TPM tính thật) × 1,5 (đệm)
```

Ví dụ (minh hoạ, giả định burndown 10x): CRM có 50 đại lý, giờ cao điểm 10 bản nháp/phút, input 3.000 token,
`max_tokens` 800, output thật 400.

- Giữ chỗ ≈ 10 × 3.800 = 38.000 TPM.
- Tính thật ≈ 10 × (3.000 + 4.000) = 70.000 TPM.
- Riêng CRM cần khoảng 105.000 TPM. Phải cộng thêm TP compose, tenant T-stage và wave dev nếu chung account.

**Ai xin, xin thế nào.**

1. Tech lead đọc quota bằng lệnh một dòng:

   ```bash
   aws service-quotas list-service-quotas --service-code bedrock --region us-west-1 --profile nghiep_aa365 --query "Quotas[?contains(QuotaName,'Sonnet') || contains(QuotaName,'Haiku') || contains(QuotaName,'Cross-Model')].[QuotaName,Value,QuotaCode]" --output table
   ```

2. Chạy lưu lượng giống prod trên **đúng model và profile** prod sẽ dùng (load test ở mục 5.6).
3. Xin tăng quota "Cross-Region InvokeModel tokens per minute for {model}". Theo AWS, sau đơn này Support sẽ liên hệ
   và cho chọn nâng luôn TPM on-demand và "Cross-Model Max Tokens Per Day". Lệnh một dòng (cần quyền
   `ServiceQuotasFullAccess` hoặc `iam:CreateServiceLinkedRole`):

   ```bash
   aws service-quotas request-service-quota-increase --service-code bedrock --quota-code <QUOTA_CODE> --desired-value <TPM> --region us-west-1 --profile nghiep_aa365
   ```

4. Trong đơn ghi (danh sách AWS gợi ý cho case Support): endpoint, region, model hoặc profile ID, mã HTTP + loại
   lỗi, request ID và giờ UTC, token/phút, request/phút, concurrency, và lịch tăng tải. Đính kèm ảnh CloudWatch
   `InvocationThrottles` + token count. `EstimatedTPMQuotaUsage` chỉ là ước lượng, AWS dặn không dùng nó một mình.
5. Launch lớn hoặc quan trọng: AWS khuyên liên hệ account team. Mình chưa có account team riêng; hỏi đại lý (câu 17).

**Đại lý giúp gì.** Tài liệu AWS không ghi đại lý có quyền nâng quota. `reseller-questions.md` đã có các câu 15
(Billing Transfer có làm mất quyền Bedrock / đăng ký Marketplace không), 17 (hỗ trợ xin tăng quota, mất bao lâu) và 18
(account mới quota thấp). Chỉ cần đánh dấu ★ cho câu 17 để đòi trả lời bằng văn bản.

**Mất bao lâu.** Tài liệu không nêu thời hạn.

- Trang quota Bedrock ghi rõ đơn tăng quota Bedrock **không được duyệt tự động**. (Trang Service Quotas chung nói đơn
  nhỏ thường tự duyệt, nhưng với Bedrock thì theo trang Bedrock.) Support có thể duyệt, duyệt một phần hoặc từ chối.
- Đơn quota không được hỗ trợ ưu tiên, kể cả khi có gói Support.
- Model đã sang Legacy / Deprecated thì không được tăng quota. Chọn model prod còn đời dài (Sonnet 5.5: EOL không sớm
  hơn 28/09/2027 theo model card).

**Khi nào cần Provisioned Throughput hoặc service tier.** Hôm nay **chưa cần, và phần lớn không dùng được**.

- Provisioned Throughput: bảng model hỗ trợ chỉ có Claude 3 Haiku / Sonnet (ở ap-south-1) trong họ Claude, không có
  model Claude hiện hành và không có region us-west-1.
- Service tier Priority / Flex / Reserved: model card Sonnet 5.5 chỉ đánh dấu Standard (đã đọc). Haiku 5.5 và Sonnet 5:
  chưa đọc model card, kiểm trước khi dùng. Reserved cần tối thiểu 100.000 input TPM + 10.000 output TPM, kỳ hạn 1
  hoặc 3 tháng, liên hệ account team; quota on-demand dùng chung cho Priority / Standard / Flex.
- Batch inference (bảng giá AWS: rẻ hơn 50 % so với on-demand): danh sách hỗ trợ có Haiku 4.5, Sonnet 4.6, Opus 5,
  **không có Sonnet 5.5 / Haiku 5.5 / Sonnet 5**. Prompt cache không dùng được với batch.
- Trigger để xem lại các lựa chọn này ở mục 5.7.

### 2.2 Tầng 2: connection trong gateway

Code CIS (AA-1002 S4, S10) đã có:

- `max_concurrency` (1–1000), `rpm_limit` (1–100000) và `monthly_budget_usd` trên `shared.llm_provider_connection`.
- Limiter: semaphore + cửa sổ trượt 60 giây. Chờ tối đa 30 giây rồi trả `LimiterSaturated` (lỗi `throttled`) và
  chuyển sang deployment kế tiếp.
- Breaker dùng chung giữa các task (`shared.llm_provider_health`).
- Budget tháng: tính từ `llm_call_log`, cảnh báo 80 %, chặn 100 %, job kết thúc `stopped_budget`.

Bốn lỗ hổng phải vá trước prod:

1. **Limiter chạy trong từng process.** Mỗi task ECS giữ phần riêng của nó, nên trần thật bằng trần trên dòng × số
   task. Muốn khớp với quota AWS thì làm một trong hai cách:
   - (a) chia trần trên dòng cho số task tối đa, và ghi rõ trên tab Connections; hoặc
   - (b) dùng token bucket chung trong DB / Redis (đã có Redis cho rate limit `/v1/*`).

   Đề xuất: làm (a) ngay, vì không cần code; khi mỗi service chỉ chạy 1–2 task (kiểm desired count) thì sai số nhỏ. (b) chỉ làm khi có
   trigger (mục 5.8): một service chạy > 2 task, hoặc vẫn có 429 dù trần đã chia.
2. **Limiter chỉ đếm request, không đếm token.** AWS ghi: limiter chỉ đếm RPM không chống được thay đổi kích thước
   request. Thêm trần TPM theo dòng, tính `input + max_tokens` lúc giữ chỗ (trong process, cùng cách (a)). Trước khi có
   code: đặt `max_tokens` đúng theo stage (mục 5.4) là cách rẻ nhất.
3. **Đường legacy `haiku`/`sonnet` không qua limiter và breaker** (`_legacy_chain` chỉ kiểm budget connection). Đây là
   đường mặc định khi `LLM_LEGACY_ALIASES` tắt (mặc định tắt). Đường Anthropic vendor của lát S2 và `openai_chat`
   direct cũng gọi thẳng, không qua `breaker.guarded`. Bật `LLM_LEGACY_ALIASES` sau một lần kiểm live, hoặc bọc các
   đường đó vào `breaker.guarded`.
4. **Chưa thấy dòng nào có số** (seed để NULL; docstring `connection_budget.py` ghi "the seed rows have no budget";
   chưa kiểm live). Đọc tab Connections, rồi điền số ngay, kể cả trên Dev, để thấy hành vi.

### 2.3 Tầng 3: app và môi trường

- **Dev và prod.** Quota `aa-ai` dùng chung. ADR 0012 d7 đã quy định: wave dev trả phí phải nhường prod. Cách làm cụ
  thể:
  - Mỗi môi trường có dòng connection riêng: role dev và role prod-only, cùng account `aa-ai`.
  - Tổng trần của các dòng dev ≤ 30 % quota account từ lúc có prod.
  - Wave tự dừng khi một circuit prod mở.
- **Batch và interactive.** Bước tối thiểu: dòng connection riêng cho wave (bulk) với trần thấp, cộng cờ "bulk
  paused". Lane đầy đủ và claim theo độ ưu tiên (mục 5.1) chỉ làm khi có trigger.
- **Theo app.** Sau S8, mỗi app có ít nhất một dòng connection, ví dụ `cis-prod-interactive`, `cis-prod-bulk`,
  `tp-prod`, `crm-prod` (tên minh hoạ). Trên từng dòng có budget tháng. Trần ngày 5 USD của TP chuyển thành budget của
  dòng `tp-prod`, kèm trần ngày.

### 2.4 Tầng 4: tenant và đại lý

- **CRM.** Đã có. Thứ tự: scrub → budget `ai_budget_usd` → `ai_enabled` → gọi model → ghi `crm.llm_call`. Mọi kết quả
  khác "ok" đều trả `manual_reply_needed`. Còn thiếu:
  - cảnh báo 75/90 % (đã hoãn sang CRM-33a, AA-964);
  - trần số lệnh/phút theo đại lý. Không cần trần song song: khoá advisory theo đại lý giữ từ lúc kiểm budget tới khi
    ghi log (`app/llm/gateway.py`, "calls of one agency are serialised"), nên mỗi đại lý đã chỉ có 1 lệnh chạy cùng
    lúc. Chú ý ngược lại: nếu CRM-33a có màn hình người dùng ngồi chờ nhiều nháp cùng lúc thì việc xếp hàng này làm
    chậm; đo trước khi nới;
  - giá trị mặc định cho prod (2 USD là số thử).
- **Content studio (CIS T-stage).** Chưa có trần USD theo tenant. Đề xuất `tenant_ai_budget_usd`, suy ra từ giá gói:
  - mục tiêu báo cáo K-LLM-TENANT ≤ 30 % giá gói;
  - cảnh báo khi đạt 100 % phần AI của gói;
  - từ 150 %, job mới chờ staff duyệt (không chặn cứng ngay).

  Đếm cả bài T9 vào quota gói. Trần số job T2/T9 đang chạy theo tenant (để một tenant không chiếm hết slot của kind;
  claim hôm nay là FIFO theo `run_after, created_at`, `shared/jobs/queue.py`) chỉ làm khi có trigger: từ 3 tenant trả
  tiền chạy cùng lúc, hoặc có tenant phàn nàn job chờ.

### 2.5 Tầng 5: người dùng cuối

- **B2C TripPlanner.** Limiter ở BFF hoặc Vercel Firewall:
  - Mỗi phiên khách 10 narration/giờ, mỗi IP 30 search/phút (minh hoạ; chỉnh theo log Dev).
  - Bot check (Vercel BotID hoặc Turnstile) trước narration đầu tiên.
  - Khách đã đăng nhập được hạn mức cao hơn.
  - Tách trần ngày giữa search và narration để hai bên không ăn phần của nhau.
- **B2B2C.** Không có lệnh gọi trực tiếp (mục 3). Khi có trợ lý cho khách: trần con theo khách, nằm trong budget của
  đại lý.
- **Nhân viên đại lý trong CRM.** Tuỳ chọn. Chỉ làm khi một đại lý có nhiều người dùng AI.

## 3. Luồng theo loại khách

| Loại khách | App / màn hình | Stage LLM | Ai bấm | Đi đường nào hôm nay → đích | Ai trả | Giới hạn hôm nay | Dữ liệu được ra khỏi AWS |
|---|---|---|---|---|---|---|---|
| **B2C** khách ẩn danh / đã đăng nhập | TripPlanner `/browse/search`, `/trip/{id}/narrate` | `tp_search_embed` (Cohere Embed v4, acc2; khi bị throttle thì sang acc3), `tp_compose` (Claude Sonnet 4.6 qua acc3) | Khách | Client mỏng TP → Bedrock trực tiếp. **Đích: core gateway (S8)** | AA | Trần chung 5 USD/ngày, throttle route 2 rps / 10 rps, cache. Đăng nhập không thêm hay bớt gì | **Không.** `aws_only` cho tới khi có rà soát DPA + trang privacy |
| **B2B** tenant Content studio | Portal (AA-Partner `portal/`) → CIS `/v1/*` → job | T2 rewrite / judge / flag-fix / brand, T3, T5, T7, T8, T9, T10 | Người dùng tenant | Job `t2_rewrite` / `t9_write` → gateway CIS → acc3 | AA trả trước, thu lại qua giá gói + phí vượt quota | Quota bài viết lại (không chặn), RPM HTTP theo gói, cap 4 job mỗi kind (dùng chung mọi tenant) | Writer: không. Judge T: được dùng OpenAI direct làm đường cuối (từ S235). Mở rộng cần sửa terms + DPA (AA-820) |
| **B2B** đại lý CRM | AA-Partner `app/llm/gateway.py` | CRM-33a: nháp trả lời / follow-up / đề xuất. CRM-33b: đọc xác nhận NCC, ghi chú → phương án, giọng văn | Nhân viên đại lý | Gateway CRM (stub). **Đích: core gateway (S8)** + role `AA3-Bedrock-Invoker-CRM` | AA, trong trần của từng đại lý (ADR 0010 d9). Đại lý không dùng key riêng | Scrub fail closed, 2 USD/tháng, `ai_enabled` mặc định tắt. Chưa có trần tốc độ | **Không bao giờ.** Chỉ Bedrock, không OpenAI, không Jev (ADR 0008a). Chỉ gửi văn bản đã scrub |
| **B2B2C** khách của đại lý | Portal `/c/t`, form `/c/f/{key}`, trang trip white-label | **Không có** | — | Đọc nội dung T2 đã viết sẵn | — | Giới hạn theo IP, quota form, honeypot | — (gián tiếp: tin nhắn khách gửi đi vào CRM, rồi đại lý dùng AI trên đó, qua scrub) |
| **Nội bộ AA** | Admin CIS, wave, job | A0, S1 generate / judge / flag-fix, A3, F10 embed, segment, eval, adhoc | Staff, wave | Gateway CIS → acc3 (+ Cohere acc2). Batch S1 qua `bedrock_batch.py` | AA | `spend_budget` theo kind (không gồm S1/T*), wave không có trần USD trong code, breaker + limiter (chưa đặt số) | Judge / validate được dùng `vendor_direct`. Nội dung catalog AA, không PII |
| AA-Booking | — | Không có hôm nay | — | — | — | Luật: không dùng AI cho tư vấn bảo hiểm / tài chính; chat với khách phải báo rõ là AI | — |

Ba luật chung:

1. **Ai trả:** AA trả mọi lệnh gọi. Tenant không thấy chi phí (`/v1/billing` không có `llm_cost_usd`). Khoản này thu
   lại qua giá gói, không bán lại theo token.
2. **Dữ liệu khách ra khỏi AWS:** chỉ khi stage có `vendor_direct` **và** terms + DPA cho phép. Hôm nay mới judge /
   validate của nội dung AA và judge T. Anthropic API trực tiếp (`anthropic-direct`) cũng là `vendor_direct`.
   Nghĩa là: route khách (TP, CRM, writer tenant) **không có fallback ngoài AWS** cho tới khi có quyết định data scope.
   Phải ghi điều này vào SLO của các route đó.
3. **Global CRIS** (`global.`, rẻ hơn khoảng 10 %, xử lý ở mọi region trên thế giới): chỉ dùng cho stage không có PII
   (catalog AA, wave), và chỉ sau khi tech lead đồng ý. CRM và TP giữ `us.`.

## 4. Giám sát

### 4.1 Đã có

| Thứ | Thấy gì | Không thấy |
|---|---|---|
| `shared.llm_call_log` | Mỗi lệnh gọi có tính tiền: tenant, stage, model, connection, fallback, cost, cache. App lấy từ `quality_signal->>'app'` | CRM (log ở `crm.llm_call` riêng). CIS không log lệnh lỗi; TP có log |
| Trang chi phí theo app (`api/services/platform_cost.py`, `cost_by_app`) | Chi phí AWS theo tag `App` + chi phí AI theo app; dòng CRM cộng chi phí AI qua `crm.ops.v1` `/llm/usage` (AA-936) | % budget, quota |
| Thẻ availability `/admin/llm-availability` | Trạng thái blocked / degraded / ok theo provider × account, breaker theo deployment | CRM. Lỗi của TP |
| Tab Connections + `/cost-ops/forecast` + `/spend/daily` | Chi phí và dự báo cuối tháng theo connection | % quota AWS |
| Digest OPS-12 (07:30 ICT) | Route blocked / degraded / unknown. `K-LLM-FALLBACK-24H` ≥ 5 % báo đỏ. `K-LLM-COST-DAY` > 2× trung vị 14 ngày và > 1 USD | TP không có probe, chi phí CRM |
| Đối soát chi phí hằng đêm (S10) | `llm_call_log` so với Cost Explorer (Bedrock) | Anthropic / OpenAI: `not_configured` cho tới khi có Admin key |
| AWS Budgets | acc3 250 USD (80/100 % thực tế, 100 % dự báo) + anomaly. Org 300 USD | Chỉ cảnh báo, không chặn |
| Alarm CloudWatch acc2 | Lỗi ghi `llm_call_log` / `shadow_log` / `decision_log` | Throttle, circuit, quota |

### 4.2 Cần thêm, theo thứ tự

1. **Cảnh báo tức thời khi circuit mở** trên deployment prod (từ `shared.llm_provider_health`), gửi chuông admin +
   email. Không chờ digest.
2. **3 alarm CloudWatch trên account gọi model** (`aa-ai`, namespace `AWS/Bedrock`), **không lọc dimension** (AWS
   ghi: request lỗi trước khi xác định model thì không có dimension `ModelId`, lọc theo `ModelId` sẽ đếm thiếu):
   - `InvocationThrottles`;
   - `InvocationClientErrors` (AWS ghi: request bị từ chối vì vượt service quota được đếm ở đây, không đếm là
     throttle);
   - `InvocationServerErrors`.

   `EstimatedTPMQuotaUsage` và `LegacyModelInvocations`: xem trên dashboard, không cần alarm lúc đầu (AWS dặn
   `EstimatedTPMQuotaUsage` chỉ là ước lượng, không dùng một mình).
3. **Kích hoạt cost allocation tag `App` sớm**, vì AWS ghi kích hoạt **không có hiệu lực ngược** và cần tới 24 giờ
   mới hiện. Cộng một role invoker cho mỗi app × môi trường trên `aa-ai` (IAM principal attribution, AWS tự ghi, không
   cần code) là đủ chi phí theo app trên hoá đơn. Chi phí theo tenant đã có trong sổ gateway.
4. **Invocation logging + request metadata: khi có trigger** (mục 5.8). Lý do chưa bật:
   - request metadata chỉ được ghi vào invocation log (AWS ghi: không thành cost allocation tag, không lên Cost
     Explorer / CUR), mà `llm_call_log` đã có tenant / stage / app / chi phí;
   - invocation log chứa **toàn bộ** prompt / output của mọi lệnh gọi trong account × region (nội dung tenant, văn bản
     CRM đã scrub), giữ tới khi xoá cấu hình. Thêm một kho dữ liệu nhạy cảm phải quản lý quyền và retention.
   Khi bật: retention ngắn (ví dụ 30 ngày), quyền đọc hẹp, metadata không có PII (mã tenant đã hash).
5. **CRM vào cùng sổ:** chi phí CRM đã lên trang chi phí theo app. Còn thiếu: thẻ availability và digest đọc lỗi /
   độ trễ của CRM qua `crm.ops.v1`, hoặc sau S8 CRM ghi `shared.llm_call_log` với `app='crm'`.
6. **Bảng theo tenant** trên trang observability của CIS: % budget tenant (khi có MỚI 2), số 429, tỉ lệ fallback.
   p95 độ trễ và cache hit theo stage: khi có trigger.
7. **Đối soát Anthropic:** đặt tên secret Admin key chỉ đọc để reconcile không còn `not_configured` (chỉ khi đường
   Anthropic API đã chạy).

### 4.3 Ngưỡng đề xuất

Đây là số khởi điểm. Chỉnh sau 2 tuần chạy thật.

| Tín hiệu | Cảnh báo | Báo khẩn (prod) |
|---|---|---|
| Circuit mở trên deployment prod | — | Ngay lập tức |
| `InvocationThrottles` (prod, stage interactive) | > 0 trong 5 phút | ≥ 10 trong 5 phút |
| `InvocationClientErrors` (không lọc dimension) | > 0 lỗi vượt quota trong 15 phút | ≥ 10 trong 15 phút |
| `EstimatedTPMQuotaUsage` / quota (chỉ xem dashboard, ước lượng) | ≥ 60 % đỉnh tuần → chuẩn bị đơn quota | — |
| `InvocationServerErrors` / Invocations | ≥ 2 % trong 15 phút | ≥ 5 % trong 15 phút |
| `LimiterSaturated` trên lane interactive | > 0 trong 15 phút | ≥ 1 % số lệnh trong 1 giờ |
| Budget connection | 80 % (mặc định đã có) | 100 % = chặn (mặc định đã có) |
| Đại lý CRM | 75 % / 90 % | 100 % = AI tắt (đã có) |
| Tenant Content studio | 100 % phần AI của gói | 150 % → chờ staff duyệt |
| Trần ngày TP | 80 % | Chạm trần (hôm nay chỉ giáng cấp, không có cảnh báo) |
| Fallback 24 giờ | ≥ 5 % (đã có) | ≥ 20 % |
| Chi phí ngày | > 2× trung vị 14 ngày (đã có) | > 4× hoặc > AWS Budget ngày |
| Anthropic API: mức dùng so với giới hạn tier | 70 % | 90 % hoặc lỗi spend cap |
| Cache hit theo stage có prompt cố định dài | < 50 % (chỉ để xem) | — |

## 5. Ổn định và scale

### 5.1 Tách lane batch và interactive

Đây là đòn bẩy lớn nhất. Mỗi stage gắn một lane trên `llm_role_config`:

- **interactive:** TP compose / search, nháp CRM, các thao tác Content studio mà người dùng ngồi chờ. `max_tokens`
  nhỏ, timeout ngắn, fallback ngắn.
- **async:** T-stage của tenant, intake CRM. Chạy qua bảng job (`shared.job`, `crm.job`). Bảng job chính là hàng đợi
  mà AWS Well-Architected khuyên đặt giữa app và model. **Không thêm SQS / Kafka.**
- **bulk:** wave viết lại catalog, atomize, eval. Dùng batch khi model hỗ trợ, chạy ngoài giờ cao điểm.

Làm ngay (nhỏ): dòng connection riêng cho bulk, cờ "bulk paused", wave tự dừng khi có circuit prod mở. Bản S258 đã
định "wave pace theo limiter", nhưng hôm nay pace còn làm tay. Khi có trigger (mục 5.8): gắn lane trên
`llm_role_config`, job claim theo độ ưu tiên (interactive / async trước bulk), chia công bằng giữa các tenant, dừng
wave theo p95 interactive.

### 5.2 Fallback hai họ model, hai region nguồn

- Mỗi route prod có fallback sang **model khác** (ví dụ Sonnet → Haiku, hoặc sang GPT với stage được phép).
  Chuỗi dài tối đa 2–3 deployment. Tổng số lần thử cả chuỗi ≤ 6, không phải 6 lần mỗi deployment, để tránh "retry
  surge" (AWS lấy 6 lần thử làm ví dụ ngân sách retry cho một thao tác; áp cho cả chuỗi là lựa chọn của bản này).
- Profile `us.` gọi từ us-west-1 đã được AWS định tuyến sang us-east-1 / us-east-2 / us-west-1 / us-west-2 (model card
  Sonnet 5.5), nên dung lượng đã trải nhiều region. **Region nguồn thứ hai** (us-west-2 hoặc us-east-1, nhớ chừa trong
  SCP) chỉ thêm một khoản quota riêng: làm khi có trigger (503 / 529 lặp lại, hoặc quota us-west-1 không được nâng).
  Nó không cứu được khi cả account bị chặn (như 29/10). Chỉ đường ngoài AWS mới cứu được trường hợp đó.
- Phân loại lỗi:

  | Lỗi | Nghĩa | Gateway làm gì |
  |---|---|---|
  | 429 `ThrottlingException` | Vượt quota | Lùi lại, sang deployment kế |
  | 503 | Hết capacity, không phải vượt quota | Sang region hoặc model khác |
  | 529 | Quá tải tạm thời | Theo `Retry-After` |
  | 429 Anthropic spend cap (`error.details.error_code` = `enforced_spend_limit_reached`, không có `retry-after`) | Hết trần chi của tier tháng này; mở lại 00:00 UTC ngày 1 tháng sau, hoặc khi lên tier cao hơn | Phân loại `quota_exhausted`, **không retry**, báo tech lead xin nâng tier |
  | 400 Anthropic `invalid_request_error`, message "You have reached your specified (workspace) API usage limits" | Chạm spend limit tự đặt (org hoặc workspace) | Như dòng trên, nhưng tự nâng được trong Console |

  Hai dòng cuối cần thêm vào `errors.classify`. Dòng 400 dễ bị coi nhầm là lỗi request.

### 5.3 Giữ Anthropic API luôn ấm

**Sửa lại bản S261.** Theo tài liệu hiện hành, Anthropic xếp tier tự động theo lịch sử dùng và tình trạng tài khoản.
Tổ chức mới hoặc ít lịch sử **có thể** bắt đầu ở tier **Evaluation**, thấp hơn mức chuẩn, và tự tăng khi có lịch sử.
Bản S261 ghi tier tăng theo "mức nạp và chi"; câu đó cần sửa. Kết luận không đổi: key không dùng thì nằm ở tier thấp.

- Tier Start có trần chi 500 USD/tháng. Chạm trần thì nhận 429 tới 00:00 UTC ngày 1 tháng sau, trừ khi xin lên tier
  cao hơn sớm (nút "Request tier increase" trong Console).
- "Acceleration limit" có thể trả 429 khi lưu lượng tăng đột ngột, nên phải tăng dần.
- Cách giữ ấm: probe hằng ngày + một phần nhỏ lưu lượng thật của stage được phép.
- Workspace: tạo 2 workspace (dev, prod), mỗi cái có spend limit riêng (workspace mặc định **không đặt được** spend
  limit). Chỉ CIS dùng đường này: CRM không bao giờ dùng Anthropic API (ADR 0008a, chỉ Bedrock), TP giữ `aws_only`
  tới khi data scope cho phép. Workspace theo app chỉ cần khi có app thứ hai được phép dùng.
- Đặt spend limit trong Console thấp hơn trần tier.
- Priority Tier của Anthropic không còn bán cam kết mới, và không hỗ trợ Sonnet 5.5 / Haiku 5.5 / Opus 5.5 / Sonnet 5 /
  Opus 5.

### 5.4 Prompt caching và `max_tokens`

- Cache read không trừ vào quota Bedrock, và với phần lớn model Claude cũng không tính vào ITPM của Anthropic. Ví dụ
  trong tài liệu Anthropic: cache hit 80 % cho thông lượng input hiệu dụng gấp 5 lần.
- Đã dùng cache 5 phút (S6). Thêm TTL 1 giờ cho prompt của wave và cho system prompt CRM theo đại lý. Wave có khoảng
  nghỉ > 5 phút giữa các tour cùng template sẽ mất cache 5 phút.
- Batch không dùng được cache.
- Đặt `max_tokens` theo từng stage bằng p99 output đo từ `llm_call_log` cộng biên. Đây là nguyên nhân throttle ẩn
  thường gặp nhất.

### 5.5 Batch cho wave

- Đã có `bedrock_batch.py` (AA-606) và kế hoạch S7 (Anthropic Message Batches + interface chung).
- Writer S1 mặc định là Sonnet 5.5. Bedrock batch **không hỗ trợ** model này, nên khoản giảm 50 % chỉ có khi:
  - dùng Anthropic Message Batches. Đây là `vendor_direct`, nên phải có quyết định data scope cho nội dung catalog AA.
    Nội dung AA không có PII, rủi ro thấp; hoặc
  - đổi stage sang model hỗ trợ batch.
- Kiểm lại model card trước mỗi wave lớn.

### 5.6 Load test trước go-live

Load test là thứ để ra con số và lịch sử dùng làm bằng chứng cho đơn quota. Làm theo quy trình ramp của AWS, trên
account và model prod:

1. Bắt đầu từ tải nhỏ đại diện. Mỗi bước chỉ tăng một chiều và giữ một lúc.
2. Ghi 429 / 503 / 529, p95, token, độ sâu hàng đợi.
3. Dừng ở mức ổn định cuối cùng.

Giới hạn chi phí: prompt ngắn, `max_tokens` thật, tổng vài USD qua chính budget của gateway (luật paid runs: thử
khoảng 3 lệnh, rồi ≤ 50). Làm **6 tuần trước go-live**, xin quota ngay sau đó. Ramp key Anthropic theo cùng cách.

### 5.7 SLO và trigger mở rộng

SLO đề xuất. Tech lead duyệt. Đo từ `llm_call_log` + log app. Câu trả lời fallback tính là thành công.

| Tính năng | SLO |
|---|---|
| TP compose (B2C) | 99,5 % request có trả lời (AI hoặc bản giáng cấp) trong 30 ngày. p95 thời gian ra token đầu < 5 giây |
| Nháp CRM (B2B) | 99 % trả nháp hoặc báo rõ "trả lời tay" trong 30 giây. 0 lệnh có văn bản chưa scrub (bất biến cứng) |
| T-stage tenant | 95 % job xong trong N phút (N do tech lead chốt theo đo Dev). Chi phí nằm trong budget tenant |
| Wave catalog | Xong trong 24 giờ, USD/tour trong trần |

Chính sách error budget: một SLO interactive tiêu > 50 % budget lỗi trong một tuần thì đóng băng wave và việc đổi model
tới khi hồi phục.

Trigger mở rộng (đo được, không đoán):

| Trigger | Hành động |
|---|---|
| p95 token/phút của lane interactive > ~60 % quota trong 1 tuần, hoặc có 429 trên stage interactive prod | Xin quota với số đo. Giảm `max_tokens`. Tăng cache hit |
| 503 / 529 lặp lại trên interactive | Thêm region nguồn thứ hai hoặc `global.` (nếu data scope cho phép). Thử Priority tier khi model card có |
| Wave vẫn chen prod dù đã có limiter, hoặc có tenant trả tiền có SLA | Bật đường 2: Bedrock tại chỗ ở `aa-prod` sau khi đã làm ấm quota (sửa ADR 0001a) |
| Interactive bền ≥ 100.000 input TPM + 10.000 output TPM, cần 99,5 % | Hỏi account team về Reserved tier (1 hoặc 3 tháng). Không dùng Provisioned Throughput |
| Chi LLM tháng lớn và phần lớn là bulk | Chuyển bulk sang batch / Flex. Chọn lại model theo stage |

### 5.8 Làm khi có trigger (cỡ đội 2–3 người)

Các việc dưới đây đúng về kỹ thuật nhưng quá cỡ đội lúc này. Không tạo issue; khi trigger xảy ra thì thêm vào issue
có sẵn (cột cuối).

| Việc | Trigger | Gắn vào |
|---|---|---|
| Limiter chung giữa các task (Redis / DB token bucket) | Một service chạy > 2 task, hoặc vẫn có 429 dù trần đã chia theo số task | AA-1002 |
| Lane trên `llm_role_config` + job claim theo độ ưu tiên | Wave làm p95 của TP / CRM / Content studio vượt SLO dù đã có cờ "bulk paused" | AA-1002 |
| Chia công bằng job giữa tenant (trần T2/T9 song song theo tenant) | ≥ 3 tenant trả tiền chạy cùng lúc, hoặc có tenant phàn nàn job chờ | MỚI 2 |
| Invocation logging + request metadata trên `aa-ai` | Cần điều tra sự cố mà `llm_call_log` không đủ, hoặc cần đối soát per-request với CUR | AA-896 |
| Region nguồn thứ hai | 503 / 529 lặp lại trên interactive, hoặc quota us-west-1 không được nâng | AA-1002 |
| Alarm `EstimatedTPMQuotaUsage` / `LegacyModelInvocations`, bảng p95 + cache hit theo stage | Đã có prod và 2 tuần số thật | AA-896 |
| Workspace Anthropic theo app | Có app thứ hai ngoài CIS được phép `vendor_direct` | AA-1004 |
| Hạn mức AI theo nhân viên đại lý trong CRM | Một đại lý có nhiều người dùng AI và phàn nàn chia phần | AA-964 |

Ngoài bảng trên, các việc sau **không làm** (ghi để không ai làm sớm):

- Provisioned Throughput, Reserved tier: chưa tới trigger ở mục 5.7, và không áp cho Claude 5.5 hôm nay.
- Hạ tầng app / DB active-active nhiều region. Chỉ thêm region nguồn thứ hai cho đường LLM.
- Message broker mới (SQS, Kafka). Bảng job đã là hàng đợi.
- Gateway bên thứ ba (LiteLLM, Kong AI), self-host model. Việc cần làm là gom về core (S8), không phải thay.
- Cache ngữ nghĩa output LLM cho B2C: rủi ro sai thông tin tour. Phục vụ nội dung viết sẵn thay vào.
- Account AWS / Anthropic riêng cho từng tenant. Dùng budget, workspace và dòng connection.
- Gọi song song hai model cho một request: tốn gấp đôi.
- Account AI riêng cho prod: chỉ khi có trigger ở bảng trên.

## 6. Thêm app mới vào hệ sinh thái

Checklist rút từ ADR 0008 (bước 9–11), ngoại lệ CRM (ADR 0008a), mẫu TP và kế hoạch S8. Mỗi bước có người duyệt là
tech lead, trừ khi ghi khác.

1. **Cổng quyết định (ADR 0008 d2).** AI là tính năng của AA (AA trả, gateway AA) hay khách tự mang key? Mặc định:
   tính năng của AA, như ADR 0010 d9. Viết ADR con hoặc design doc.
2. **Gateway.** Vendor core `aa_llm` (sau S8). Không gọi boto3 hay SDK vendor trực tiếp. Đăng ký mọi call site (guard
   kiểu `test_aa927_llm_call_site_registry`). Trước S8 chỉ có hai lựa chọn: fork kiểu TP (phải deploy mới đổi được
   route) hoặc gateway riêng kiểu CRM. Cả hai đều phải chuyển về core sau.
3. **Stage + route + data scope.** Đăng ký tiền tố `<app>_*` trong `shared.llm_role_config` bằng migration CIS:
   - `allowed_scopes` đặt trong seed (cột chỉ đổi bằng migration);
   - lane (interactive / async / bulk);
   - `max_tokens` theo đo.

   Phân loại stage online (khách dùng, có trần) và offline (backfill, có budget) như `ONLINE_STAGES` của TP.
4. **Sổ log.** Ghi `shared.llm_call_log` với `quality_signal.app = '<app>'` (ghi chéo schema duy nhất được phép, ADR
   0008 d5), hoặc sổ riêng cùng hợp đồng cột, mở qua ops contract (mẫu CRM). Không lưu prompt khi có thể có PII.
5. **DB role.** `<app>_app` có SELECT trên cấu hình gateway và INSERT trên log, không hơn (mẫu TP, migration CIS 173).
   ADR 0009 sẽ thay bằng hợp đồng HTTP / snapshot.
6. **Account / role AWS.** Không tạo account mới. Một role invoker cho mỗi môi trường trên `aa-ai` (mẫu
   `AA3-Bedrock-Invoker-CRM`; prod dùng role prod-only theo ADR 0012 / 0018), trust chỉ task role của app. Một dòng
   connection riêng cho app × môi trường, có `rpm_limit`, `max_concurrency`, `monthly_budget_usd`. Embedding giữ cùng
   model với không gian vector.
7. **Budget.**
   - Budget connection.
   - Trần ngày cho stage khách dùng.
   - Budget theo tenant nếu là B2B.
   - Limiter theo user / IP nếu là trang công khai.
   - Tag `App=<app>` + cảnh báo budget (ADR 0008 bước 11). Role invoker riêng của app cũng là cách AWS tách chi phí
     theo app trên hoá đơn (IAM principal attribution).
   - Workspace Anthropic riêng nếu dùng `vendor_direct`.
8. **Riêng tư.**
   - Tag `pii:<class>`.
   - Scrubber nếu văn bản tự do của khách đi vào prompt (mẫu F3 của CRM).
   - Nhãn AI trên văn bản AI hiển thị cho khách (AA-819).
   - Báo rõ là AI ở đầu mỗi phiên chat với khách (AA-820, Anthropic AUP từ 12/11/2026).
9. **Đường giáng cấp.** Mỗi tính năng LLM có bản không-AI: văn bản AA, tìm theo từ khoá, `manual_reply_needed`.
   Không có spinner chờ mãi.
10. **Giám sát.** Chi phí hiện trên trang External Spend / cost-ops theo app và theo tenant (K-LLM-APP, K-LLM-TENANT).
    Alarm (mục 4.3). Sentry không có PII. Mỗi lệnh gọi một dòng log kết quả, không kèm văn bản.
11. **Quota.** Cộng nhu cầu TPM của app (RPM nếu là embedding) vào bảng tính tầng 1 (mục 2.1). Nếu tổng vượt ~60 %
    quota hiện có thì xin tăng **trước** khi bật. Nhớ AWS chỉ ưu tiên đơn có lưu lượng thật, nên chạy thử bước 12
    trước rồi mới xin.
12. **Review + chạy thử.** Chạy thử khoảng 3 lệnh, rồi ≤ 50. Chạy isolation probe. Subagent review độc lập (vì có
    IAM / quyền). Khai SLO. Có app có khách trả tiền thì business owner xác nhận phần giá.

## 7. Theo dõi việc

### 7.1 Bộ issue Linear đề xuất

Theo quota Linear Free: mỗi issue là một lát giao được, việc chi tiết để ở checklist local. Tái dùng issue sẵn có
trước. Chỉ đề xuất **2 issue mới**, chờ tech lead đồng ý mới tạo (luật `aa-linear-issue`).

| Issue | Project | Thêm nội dung gì | Phụ thuộc | Hạn đề xuất |
|---|---|---|---|---|
| **AA-1004** (có sẵn) Lean AWS model | Infra / Platform | (a) Đọc + ghi quota acc3 hôm nay (cả RPM Cohere embed) và sau mỗi lần đổi payer / org. (b) Bật Anthropic API Dev (bước 0a): workspace dev + prod, spend limit, auto-reload. (c) Đánh ★ câu 17 trong `reseller-questions.md`. (d) Kích hoạt cost allocation tag `App` + role invoker theo app. (e) Chốt đường embedding cho prod (mục 1) | Case AWS Error 002; key Anthropic do tech lead tạo | (a)(b)(c) ≤ 07/11; (d) ≤ 29/11; (e) ≤ G − 8 tuần |
| **AA-1002** (có sẵn) gateway, thêm **S12 "capacity controls" (bản nhỏ)** | CIS | Trần TPM giữ chỗ theo dòng (trong process). Dòng connection dev / prod / bulk. Bọc đường legacy + vendor direct vào breaker (hoặc bật `LLM_LEGACY_ALIASES`). Phân loại 429 spend cap và 400 spend limit của Anthropic. Cờ "LLM off" theo app + cờ "bulk paused". Wave tự dừng khi circuit prod mở. Cảnh báo tức thời circuit mở. `max_tokens` theo p99. (Redis bucket, lane + claim ưu tiên: khi có trigger, mục 5.8) | S4, S10 (đã có) | Số trên connection: ≤ 07/11 (không cần code). S12 code: ≤ 30/11 |
| **AA-642** (có sẵn) epic Model Gateway / **lát S8** | CIS + TP + Partner | Core `aa_llm`. TP bỏ `SUPPORTED_ACCOUNTS`, đọc registry, vào breaker / limiter / budget. CRM thay stub bằng adapter của core, giữ thứ tự scrub → budget → ai_enabled. CRM ghi chung sổ hoặc qua ops contract. Viết ADR 0009 trước S8 | ADR 0009; S12 nên xong trước | ADR 0009 ≤ 15/11; S8 ≤ 13/12, hoặc go-live − 6 tuần, lấy mốc sớm hơn |
| **AA-964** (có sẵn) CRM-33a | Partner | Cảnh báo 75/90 %. Trần lệnh/phút theo đại lý (song song đã là 1 nhờ khoá advisory). Luật prompt injection (văn bản đến là dữ liệu, model không có tool). Chốt hành vi guardrail khi acc2 hỏng. Mặc định `ai_budget_usd` cho prod | Đường LLM (acc3 hoặc Anthropic API cho Dev nếu data scope cho phép); S8 | Theo slot S264 trong backlog |
| **AA-880** (có sẵn) prod blueprint | Infra / Platform | Thêm: bảng tính TPM prod (mục 2.1), load test ramp, đơn quota, SLO, runbook "chi phí tăng vọt / cạn quota / provider chặn", trigger mở rộng | Ngày go-live; S8; S12 | Go-live − 6 tuần: load test + đơn quota. Go-live − 2 tuần: kiểm cuối |
| **AA-896** (có sẵn) FinOps | Platform | 3 alarm CloudWatch Bedrock trên `aa-ai` (mục 4.2). % budget theo tenant khi có MỚI 2 (chi phí theo app đã có). Đối soát Anthropic bằng Admin key khi đường đó chạy | AA-1004 (d) | ≤ 30/11 |
| **MỚI 1** "TripPlanner: per-session / IP AI limits + bot check" | TripPlanner | Limiter ở BFF hoặc Vercel Firewall cho `/narrate`, `/search`. BotID / Turnstile. Hạn mức cho khách đăng nhập. Tách trần ngày search / narration. Cảnh báo khi chạm trần | Không (làm được trước S8) | ≤ go-live − 4 tuần |
| **MỚI 2** "Content studio: per-tenant AI budget" | CIS | `tenant_ai_budget_usd` (cảnh báo 100 %, chờ duyệt từ 150 %). Đếm bài T9 vào quota gói. (Trần job song song theo tenant: khi có trigger) | Giá gói do business owner chốt (mục 8) | Trước tenant trả tiền đầu tiên, hoặc go-live − 4 tuần |

Không tạo issue riêng cho: số trên connection (thao tác admin, ghi vào AA-1002), giám sát (AA-896), load test (AA-880).

### 7.2 Checklist có mốc ngày

Hôm nay là 31/10/2026. Ngày go-live chưa có (AA-880), nên các mốc sau go-live tính lùi từ ngày đó (G).

- [ ] **≤ 03/11** Đọc quota acc3 (lệnh mục 2.1), lưu vào `docs/audits/<ngày>-S<nnn>-…`. Tạo key Anthropic Dev +
  spend limit + workspace Dev (AA-1004 bước 0a).
- [ ] **≤ 05/11** Điền `rpm_limit` / `max_concurrency` / `monthly_budget_usd` cho mọi connection Dev, chia theo số
  task. Ghi số lên tab Connections.
- [ ] **≤ 07/11** Business owner gửi đại lý các câu ★ (gồm câu 17 về quota, đánh ★ thêm). Nếu AWS chưa trả lời case
  Error 002 thì nhắc lại trong case.
- [ ] **≤ 11/11** AA-820: chốt câu AI trong terms tenant. Câu này quyết định `vendor_direct` cho nội dung tenant.
- [ ] **12/11** Anthropic AUP có hiệu lực: chat với khách phải báo rõ là AI (TP, CRM sau này).
- [ ] **≤ 15/11** ADR 0009 (AI platform, hợp đồng core gateway, sổ log thứ hai của CRM) ở trạng thái Proposed.
- [ ] **≤ 15/11** Cảnh báo tức thời circuit mở (S12, phần nhỏ nhất).
- [ ] **≤ 25/11** Có văn bản của đại lý, hoặc dời Billing Transfer sang 01/01/2027.
- [ ] **≤ 29/11** acc4 chấp nhận Billing Transfer (nếu đi tháng 12). Kích hoạt cost tag `App` + 3 alarm Bedrock trên
  `aa-ai`. S12 (bản nhỏ) merge.
- [ ] **01/12, 07:00 giờ VN** Probe mọi connection, đọc lại quota (nếu Billing Transfer chạy).
- [ ] **≤ 13/12** S8 (TP + CRM vào core), nếu go-live sau tháng 1.
- [ ] **G − 8 tuần** Tạo `aa-prod` + role prod-only trên `aa-ai`. Chốt đường embedding prod (không dùng acc2
  non-prod). Chốt data scope từng stage prod. Chốt SLO.
- [ ] **G − 6 tuần** Load test ramp trên đúng model / profile / account prod. Gửi đơn quota kèm số đo.
- [ ] **G − 4 tuần** Xong MỚI 1 + MỚI 2. Anthropic API prod ấm (probe hằng ngày + lưu lượng thật nhỏ). Không đổi
  payer / org nào sau mốc này.
- [ ] **G − 2 tuần** Kiểm cuối: quota đã duyệt ≥ 1,5 × đỉnh đo. Fallback sang model thứ hai + đường Anthropic API
  (stage được phép) đã probe. Runbook đã chạy thử một lần trên Dev.
- [ ] **G + 2 tuần** Chỉnh ngưỡng (mục 4.3) theo số thật. Rà bảng trigger mục 5.8. Rà quota hằng tháng cùng rà soát chi
  phí.

### 7.3 Lịch

| Giai đoạn | Mục tiêu |
|---|---|
| Tuần này → 07/11 | Có số: quota thật, trần connection, đường Dev qua Anthropic API, câu hỏi đã gửi đại lý |
| 08/11 → 29/11 | Có hàng rào: S12 (bản nhỏ), cảnh báo tức thời, 3 alarm, cost tag, ADR 0009, Billing Transfer (nếu đủ văn bản) |
| Tháng 12 | Có một gateway: S8, CRM-33a, MỚI 1, MỚI 2 |
| G − 8 → G | Có bằng chứng: `aa-prod`, load test, đơn quota, SLO, runbook, đóng băng thay đổi payer / org |

## 8. Cần duyệt

### 8.1 Tech lead duyệt

| # | Việc | Bối cảnh | Đề xuất | Chi phí |
|---|---|---|---|---|
| T1 | Số trên connection | Các dòng đang NULL nên limiter và budget chưa có tác dụng | Dev: `max_concurrency` = 4 ÷ số task, `rpm_limit` 60, budget 50 USD/tháng (minh hoạ, chỉnh theo log). Prod: đặt sau load test | 0 |
| T2 | Tách dòng connection dev / prod / bulk + cờ "bulk paused" | Quota `aa-ai` dùng chung, wave có thể chiếm slot của tenant / TP | Làm trong S12. Dòng dev ≤ 30 % quota từ lúc có prod. Lane đầy đủ: khi có trigger | Công dev ~1–2 ngày (ước tính) |
| T3 | Limiter: chia trần theo số task + giữ chỗ TPM trong process | Limiter hiện tại chỉ giữ trần trong từng task và chỉ đếm request | Làm ngay phần chia trần (không code); TPM trong S12. Redis bucket chung: khi có trigger (mục 5.8) | 0 hạ tầng mới |
| T4 | SLO + chính sách error budget | Chưa có SLO cho tính năng LLM | Bảng mục 5.7 | 0 |
| T5 | Data scope từng stage prod | Stage `aws_only` không có fallback ngoài AWS | Catalog AA: cho `vendor_direct`. Tenant / TP / CRM: giữ `aws_only` tới khi terms + DPA cho phép (T5 đi cùng B3) | 0 |
| T6 | Global CRIS cho stage không PII | Rẻ hơn ~10 %, quota riêng, xử lý ở mọi region | Cho wave / catalog AA. Không cho CRM / TP | Giảm chi phí |
| T7 | Invocation logging trên `aa-ai` | Log chứa prompt / output đầy đủ của mọi lệnh gọi; request metadata chỉ có giá trị khi log bật; `llm_call_log` đã có tenant / stage / chi phí | **Chưa bật**, chỉ khi có trigger (mục 5.8). Khi bật: retention 30 ngày, quyền đọc hẹp | 0 hôm nay. Khi bật: phí nạp + lưu CloudWatch Logs (kiểm bảng giá us-west-1 trước) |
| T8 | 3 alarm CloudWatch Bedrock (throttle, client error, server error, không lọc dimension) | Chưa có cảnh báo throttle / vượt quota | Bật theo mục 4.2 | Phí alarm CloudWatch chuẩn, vài USD/năm cho 3 alarm (kiểm bảng giá) |
| T9 | Key + credit Anthropic API (Dev, sau đó prod) | Đường ngoài AWS duy nhất, phải ấm; chỉ cho stage `vendor_direct` (không bao giờ CRM) | Workspace dev + prod (workspace mặc định không đặt được spend limit), spend limit thấp hơn trần tier, auto-reload | Trả theo dùng + ~0,40 USD/tháng/secret. Số credit nạp do tech lead chốt |
| T14 | Đường embedding cho prod | TP search embed hôm nay chạy trên acc2 (non-prod, 20 RPM) | Chốt `aa-ai` (role prod-only) hay `aa-prod`, xin RPM trên account đó trước G − 6 tuần | 0 (trả theo dùng) |
| T10 | Load test trước go-live | Cần số đo cho đơn quota | Theo mục 5.6, tổng ≤ vài USD | Vài USD |
| T11 | Tạo 2 issue mới (MỚI 1, MỚI 2) + thêm S12 vào AA-1002 | Linear Free | Như mục 7.1 | 0 |
| T12 | ADR 0009 trước S8 | Chưa có ranh giới hợp đồng cho core | Viết Proposed ≤ 15/11 | 0 |
| T13 | Mặc định kỹ thuật cho TP: hạn mức theo phiên / IP, bot check | Một script có thể ăn hết trần ngày | Số minh hoạ ở mục 2.5, chỉnh theo log Dev | BotID / Turnstile có bản miễn phí (kiểm trước khi bật) |

### 8.2 Business owner duyệt

Chỉ các việc về giá, điều khoản, hợp đồng và ngày go-live. Kiến trúc là việc của tech lead.

| # | Việc | Bối cảnh | Đề xuất | Chi phí |
|---|---|---|---|---|
| B1 | Ngân sách AI của đại lý CRM trong gói bán | Hiện mặc định 2 USD/tháng là số thử. Ước tính 50 đại lý khoảng 67–75 USD/tháng | Giữ 2 USD (AI tắt mặc định) tới khi có bảng giá. Khi có gói trả phí: mỗi gói một mức AI, đồng hồ hiện cho đại lý | Theo mức chọn |
| B2 | Phần AI trong gói Content studio + xử lý vượt | Vượt quota hiện được phép và tính phí. Chưa có trần USD AI | Mỗi gói có phần AI (mục tiêu ≤ 30 % giá gói). Vượt 150 % thì chờ staff duyệt, không cắt ngay | 0 (bảo vệ biên lợi nhuận) |
| B3 | Câu AI trong terms tenant và chính sách riêng tư (AA-820, hạn 11/11) | Quyết định nội dung khách có được đi qua Anthropic API trực tiếp khi AWS lỗi hay không | Ghi "qua AWS hoặc trực tiếp từ nhà cung cấp model (Anthropic, OpenAI)". Có cần luật sư không là quyết định của business owner | Phí luật sư nếu cần |
| B4 | Hỏi đại lý bằng văn bản | Quota, Billing Transfer, giấy Anthropic | Gửi các câu ★ của `reseller-questions.md` (câu 17 về quota đánh ★ thêm) trước 07/11 | 0 |
| B5 | Ngày go-live | Mọi mốc G − n tuần tính từ ngày này | Chọn ngày cách thời điểm chọn ít nhất 8 tuần | — |
| B6 | Trần chi LLM prod hằng tháng (tổng) | Để đặt AWS Budget + spend limit Anthropic | Tech lead đề xuất số sau load test, business owner chốt | Theo mức chọn |
| B7 | Khách B2C đăng nhập có thêm lượt AI không (khuyến khích đăng ký) | Hiện khách đăng nhập và khách ẩn danh như nhau | Có: đăng nhập được gấp đôi hạn mức | Nhỏ, nằm trong trần ngày |

## 9. Nguồn

Tài liệu AWS (đọc ngày 31/10/2026):

- Quota runtime, cách xin, ưu tiên khách có lưu lượng đang tiêu quota, không tăng cho model Legacy:
  <https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-runtime.html>
- Mặc định quota theo account, embedding tính theo RPM, "Quota increases aren't granted automatically":
  <https://docs.aws.amazon.com/bedrock/latest/userguide/quotas.html>
- Gán chi phí qua IAM principal: <https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-iam-principal-tracking.html>
- Quota mantle: <https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-mantle.html>
- Token burndown: <https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-token-burndown.html>
- Global cross-Region: <https://docs.aws.amazon.com/bedrock/latest/userguide/global-cross-region-inference.html>
- Cross-Region inference: <https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html>
- Service tiers: <https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html>
- Provisioned Throughput: <https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html>,
  <https://docs.aws.amazon.com/bedrock/latest/userguide/prov-thru-supported.html>
- Batch: <https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html>,
  <https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-supported.html>
- Prompt caching: <https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html>
- Metric CloudWatch: <https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-runtime-metrics.html>
- Invocation logging: <https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html>
- Gán chi phí: <https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-best-practices.html>,
  <https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-application-inference-profiles.html>,
  <https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-request-metadata.html>
- Scale throughput, mã lỗi, ramp: <https://docs.aws.amazon.com/bedrock/latest/userguide/scaling-throughput-best-practices.html>
- Model access theo account: <https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html>
- Model card Sonnet 5.5: <https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-sonnet-5-5.html>
- Service Quotas: <https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html>,
  <https://docs.aws.amazon.com/servicequotas/latest/userguide/organization-templates.html>
- Billing Transfer (19/11/2025): <https://aws.amazon.com/about-aws/whats-new/2025/11/aws-channel-partner-billing-transfer/>
- Managed entitlements (30/06/2026): <https://aws.amazon.com/blogs/machine-learning/simplify-multi-account-access-to-amazon-bedrock-models-with-managed-entitlements/>
- Bảng giá Bedrock: <https://aws.amazon.com/bedrock/pricing/>
- Well-Architected GenAI Lens: <https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/genrel01-bp01.html>,
  <https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/genrel03-bp01.html>

Tài liệu Anthropic (đọc ngày 31/10/2026):

- Rate limit, tier, spend cap, acceleration limit: <https://platform.claude.com/docs/en/api/rate-limits>
- Service tiers: <https://platform.claude.com/docs/en/api/service-tiers>
- Prompt caching: <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>
- Message Batches: <https://platform.claude.com/docs/en/build-with-claude/batch-processing>

Code (đường dẫn tính từ repo gốc):

- CIS gateway:
  - `apps/AA-CIS-App/shared/llm_client/breaker.py:30-33, 113, 462-536` (limiter theo process);
  - `client.py:49-54, 833-930, 1103-1124, 1166-1175` (đường đi qua / không qua limiter);
  - `connection_budget.py:11-21`;
  - `shared/cost_guard.py:323-400`;
  - `api/migrations/304_llm_connection_deployment.sql:169-170, 282-306`;
  - `shared/jobs/queue.py:80-112` (claim FIFO);
  - `services/jobs/*_job.py` (cap theo kind);
  - `api/routers/v1_tours.py:321-336` (quota tenant không chặn);
  - `api/middleware/rate_limit.py`;
  - `services/reports/digest.py`;
  - `services/llm_cost/reconcile.py`;
  - `api/services/platform_cost.py:242-302`;
  - `shared/llm_client/bedrock_batch.py`.
- TripPlanner:
  - `apps/AA-TripPlanner-Web/backend/shared/llm_gateway.py:33-36, 176, 528-591`;
  - `backend/config.py:122`;
  - `backend/browse/search.py:73-140`;
  - `CONTEXT.md:603-663`.
- CIS chi phí theo app, dòng CRM qua `crm.ops.v1`: `apps/AA-CIS-App/api/services/platform_cost.py:242-305`.
- Partner CRM:
  - `apps/AA-Partner/api/app/llm/gateway.py:1-31, 52-72, 170-178` (khoá advisory theo đại lý, dòng 12-14);
  - `api/migrations/005_crm_intake_pipeline.sql:105, 112`;
  - `api/app/ratelimit.py`;
  - `CONTEXT.md:549-560`.
- Infra:
  - `infra/AA-CIS-Infra/accounts/aa365/tripplanner.tf:541-562`;
  - `tripplanner_variables.tf:24-78`;
  - `accounts/acc3-bedrock/cost_guard.tf`;
  - `accounts/management/budgets.tf`;
  - `accounts/aa365/observability.tf:133-143, 505-557`.

Tài liệu nội bộ:

- ADR:
  - `docs/adr/0008-new-app-integration-and-data-platform-rules.md:102-111`;
  - `docs/adr/0008a-crm-separate-app-exceptions.md:107-125`;
  - `docs/adr/0010-aa-partner-app.md:174-175`;
  - `docs/adr/0012-environment-model.md:119, 146-150`;
  - `docs/adr/0018-lean-aws-account-model.md:71`.
- Audit:
  - `docs/audits/2026-10-21-S246-crm-design-v3/design-v3.md:289, 607, 1312-1340`;
  - `docs/audits/2026-10-29-S258-aws-org-blueprint/README.md` (các lát gateway S0–S11);
  - `docs/audits/2026-10-29-S258-report-catalog/catalog.md` (FI-03, K-LLM-TENANT);
  - `docs/audits/2026-10-31-S261-aws-bedrock-org-access/` (README, `current-situation-model.md`,
    `reseller-questions.md`).
- `docs/backlog/README.md` (hàng AA-1002, AA-1004, AA-880, AA-964, AA-820, AA-896).

## Artifact

- `org-accounts.html`: <https://claude.ai/artifact/TXwm33B2PZ8xx67q6H8aHv> (private, claude.ai account nghieppham@adventure.asia since S261)
- `llm-gateway.html`: <https://claude.ai/artifact/3Sx24UxNAHj7NnqR2gsPpf> (private, claude.ai account nghieppham@adventure.asia since S261)
