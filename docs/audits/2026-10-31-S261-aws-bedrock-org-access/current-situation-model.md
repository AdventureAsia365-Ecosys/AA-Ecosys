---
id: OPS-08-s261-aws-model-current-situation
title: "Mô hình AWS cho tình huống hiện tại (acc4 quản lý, acc2 còn ở TrueIDC, acc3 bị Error 002)"
description: "Bản tư vấn cho tech lead: mô hình account (quản lý / hạ tầng / AI hôm nay, thêm aa-prod khi go-live theo ADR 0018), hai tầng hỏng của Bedrock, thứ tự đưa account vào org, có nên dồn về 1 account không, và cấu hình để gọi model ổn định khi lên prod."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1004, AA-1002, AA-642, docs/adr/0018-lean-aws-account-model.md, docs/adr/0001a-retire-acc1-llm-on-acc3-only.md, docs/ops/runbooks/llm-anthropic-api-key.md, docs/audits/2026-10-31-S261-aws-bedrock-org-access/README.md, docs/audits/2026-10-29-S258-aws-org-blueprint/README.md]
---

# Mô hình AWS cho tình huống hiện tại (S261, 31/10/2026)

Tình huống thật, do tech lead xác nhận ngày 31/10:

- **acc4** là account quản lý của org AA, **đã dựng ở S259** (Infra #513/#514/#515, ADR 0018 Proposed): org (all features), 3 OU, 3 SCP, org trail, budget, Identity Center us-west-1, CI OIDC; role bootstrap đã xoá (truy cập qua Identity Center). Org chưa có member nào. Form Anthropic trên acc4: chưa kiểm (xem `acc4-anthropic-form.md`).
- **acc2** (hạ tầng Dev) vẫn là member trong org của TrueIDC. Hợp đồng chưa cho rời, nên acc2 giữ nguyên chạy hạ tầng.
  Khi tách được thì chuyển sang org AA.
- **acc3** (AI) đã rời org eCloudvalley ngày 29/10 và đang đứng riêng. Mọi model Bedrock đều bị chặn với lỗi
  "Error 002", kể cả Amazon Nova, ở us-west-1 và us-east-1 (E-E1). Lúc acc3 còn trong org eCloudvalley thì gọi được.
  Đã mở case AWS (gói Basic), hẹn trả lời khoảng 04–06/11. Đối chứng S260: một account đứng riêng khác, ngoài hệ sinh
  thái, gọi Bedrock bình thường, nên lệnh chặn nằm ở riêng acc3.
- **Dev hiện không có đường LLM nào:** acc3 Error 002, OpenAI API trực tiếp hết credit (429), connection
  `anthropic-direct` chưa có secret (key cũ đã thu hồi). Chỉ Cohere Embed v4 trên acc2 chạy.
- Kế hoạch của tech lead: đưa acc3 vào org AA trước, làm account `aa-ai`.

Mã khẳng định (ví dụ C-C1) trỏ tới `claims.json` cùng thư mục, trong đó có URL và trích dẫn nguồn AWS. Mã U (ví dụ U1)
là các điểm chưa xác nhận ở README §7.

## 1. Mô hình đích: 3 account hôm nay, thêm aa-prod khi go-live (ADR 0018)

Bản này theo **ADR 0018** (Proposed S259, bản gọn tech lead chọn ở S258): prod nằm ở account riêng `aa-prod`, không ở
acc2. Bản trước của file này đặt prod trên acc2 theo ADR 0012; ADR 0018 thay quyết định đó khi được chấp nhận.

```text
Org AA (all features)                                   Bên trả hoá đơn AWS
├── acc4  aa-management  chỉ quản trị: org, SCP,         ── Billing Transfer ──▶ đại lý có giấy Anthropic
│         Identity Center, budget, form Anthropic        (SỚM NHẤT 01/12/2026, có thể muộn hơn;
│         (không chạy app, không gọi model)              tới lúc đó acc4 tự trả bằng thẻ)
├── acc3  aa-ai        chỉ Bedrock chat. Một role invoker cho mỗi môi trường
│                      (dev, đợt viết lại catalog, batch; role prod-only khi có prod)
├── acc2  aa-nonprod   hạ tầng Dev (+ staging khi bật). Vào org khi TrueIDC cho rời
└── aa-prod            tạo khi có ngày go-live (ADR 0018 §1, §3). Gọi model qua role prod-only của aa-ai

Account mới vào org đứng thẳng dưới root (chưa SCP của mình) 1 tuần rồi mới vào OU NonProd / Prod (ADR 0018 §4).
Ngoài org, giai đoạn chuyển tiếp: acc2 ở org TrueIDC, gọi Claude/GPT qua role của acc3;
Cohere Embed v4 và guardrail gọi tại chỗ trên acc2 (đang chạy dưới TrueIDC).
Ngoài AWS: Anthropic API trực tiếp (connection `anthropic-direct`), tuỳ chọn thêm OpenAI API.
```

### Ba đường gọi model

| Đường | Dùng cho | Quota | Hỏng riêng khi (tầng account) |
|---|---|---|---|
| 1. Bedrock trong acc3 (assume role) | dev, batch; prod qua role prod-only (mặc định theo ADR 0018 §3 và ADR 0001a) | quota của acc3, dev và prod **dùng chung** nên phải có trần theo môi trường trong gateway | acc3 bị chặn mức account (như 29/10), quota acc3 cạn, đăng ký Marketplace của acc3 lỗi |
| 2. Bedrock tại chỗ trong aa-prod (tuỳ chọn, làm sau) | prod, chỉ khi aa-prod đã gọi thật mọi route và quota đã được "làm ấm" | quota riêng của aa-prod; account mới có thể thấp hơn mặc định (C-C9, D-D5) | như trên, cho aa-prod. Phải sửa ADR 0001a (hiện chỉ cho chat model trên account LLM) |
| 3. Anthropic API trực tiếp (key, ngoài AWS) | dev **ngay bây giờ** (mục 3 bước 0); prod cho các stage được phép `vendor_direct` | theo tier của tổ chức Anthropic (tier tăng theo mức đã nạp và đã chi) | key hoặc credit hết, Anthropic sự cố |

LLM gateway (AA-1002) được **thiết kế** cho mọi app và mọi đường: registry connection (Bedrock nhiều account, Anthropic
API, OpenAI), circuit breaker, fallback và budget theo connection, đổi route bằng màn admin, không sửa code. **Code** hôm
nay: CIS dùng đầy đủ. TripPlanner đọc chung bảng route/catalog nhưng gọi model qua client mỏng riêng (chỉ acc3/acc2).
CRM có gateway riêng (scrub PII, budget), lệnh gọi model vẫn là stub chờ CRM-33a (AA-964). Đưa TripPlanner và CRM lên
core dùng chung là lát **S8** của AA-642 (đã có trong kế hoạch, không cần LLM để code). Dù vậy, fallback sang đường 3 **không tự xảy ra**: migration 311 cho mọi stage CIS
trừ judge/validate `allowed_scopes = {aws_only}`, và `deployment_plan` không bao giờ rơi từ dòng `aws_only` sang dòng
`vendor_direct`. Các dòng Anthropic API do migration 306 tạo sẵn sẽ không được dùng cho writer, tenant hay các stage
prod khác cho tới khi có quyết định data scope (mục 4).

### Sửa lại (31/10/2026, kiểm Cost Explorer + CloudTrail của acc3)

Câu "acc3 chưa từng tự trả tiền" **sai**. Dòng thời gian thật:

| Giờ VN | Sự kiện | Nguồn |
|---|---|---|
| 10–17/08/2026 | acc3 đứng độc lập, **tự trả**, gọi Claude Sonnet 4.6 + Haiku 4.5 bình thường (18,49 USD gồm thuế) | Cost Explorer acc3 |
| 17/08 15:40 | acc3 chấp nhận lời mời vào org eCloudvalley | CloudTrail `AcceptHandshake` INVITE ACCEPTED |
| 25/09, 06/10 | root của acc3 thử `LeaveOrganization`, bị SCP của eCloudvalley từ chối | CloudTrail AccessDenied |
| 29/10 13:50 | eCloudvalley đưa acc3 ra khỏi org | CloudTrail |
| 29/10 → 31/10 | đứng độc lập lại: Error 002 với mọi model, kể cả Nova | probe 31/10 |

Hệ quả: "đứng độc lập thì không được Bedrock" và "không có lịch sử thanh toán riêng" đều bị loại. Giả thuyết còn lại
(chỉ case AWS xác nhận được): (1) hoá đơn tháng 8 của acc3 chưa thanh toán xong (kiểm Billing › Payments); (2) lần rời
org do bên quản lý thực hiện để lại trạng thái cần AWS xét tay cho Bedrock ở mức account; (3) account mang dấu chương
trình đại lý sau thời gian ở org eCloudvalley. Chi tiết này nên đưa vào case khi tech lead nhắc lại case (không tự nhắn).

### Hai tầng hỏng: vì sao hai đường Bedrock không độc lập

- **Tầng account** (tính riêng từng account): cổng "additional account-level access" (C-C1), quota, đăng ký Marketplace
  của account đó. Tách account chỉ che được tầng này.
- **Tầng org / payer** (chung cho mọi account trong org AA): payer (acc4 tới khi Billing Transfer chạy, sau đó là đại
  lý), Billing Transfer bị rút, giấy bán lại Anthropic của đại lý không áp hoặc hết hạn (U1, rủi ro lớn nhất chưa xác
  nhận), đại lý trễ thanh toán, form Anthropic nộp ở acc4, SCP sai. Cộng thêm hai điểm chung khác: region nguồn
  us-west-1 và vòng đời model (model chuyển Legacy không xin tăng quota được, EOL thì mất, C-C10).
- **Sự cố 29/10 bắt đầu đúng ở tầng org / payer** (acc3 rời org, E-E1). Việc quyền model bên thứ ba đi theo payer là
  giả thuyết nội bộ (E-E3, U15), AWS chỉ ghi "theo từng account". Dù nguyên nhân nào, một lần đổi payer hoặc org là
  thứ đã kích hoạt sự cố.
- **Chỉ đường 3 độc lập với tầng org / payer.** Vì vậy độ ổn định của prod dựa vào đường 3 được bật sẵn, có tiền, được
  probe hằng ngày, không dựa vào số account.

### Các lần đổi payer / org đã lên kế hoạch

| Thay đổi | Khi | Ảnh hưởng |
|---|---|---|
| acc3: đứng riêng → org AA (payer acc4) | sau khi có trả lời case (mục 3 bước 3) | đường 1 |
| Billing Transfer: acc4 → đại lý | sớm nhất 00:00 UTC 01/12 (07:00 giờ VN) | mọi account trong org cùng lúc |
| acc2: org TrueIDC → org AA | khi hợp đồng cho | Cohere Embed v4, guardrail CRM, đường acc2 → acc3 |
| aa-prod được tạo | khi có ngày go-live | đường 2 (nếu dùng) |

Luật: **làm xong mọi thay đổi payer / org trước go-live prod**, không xếp thay đổi nào sát ngày go-live; mỗi lần đổi
thì không chạy wave, probe mọi connection trước và ngay sau, đọc lại Service Quotas.

### Theo từng app: gọi gì, hỏng gì

| App | Gọi account nào hôm nay | Fallback hiện có | acc3 bị chặn | acc2 bị chặn Bedrock |
|---|---|---|---|---|
| AA-CIS-App (writer, judge, validate, T-stage tenant) | chat: acc3; embed: Cohere trên acc2 | registry + breaker + fallback cấu hình (AA-1002); `vendor_direct` chỉ cho judge/validate | mọi stage `aws_only` dừng; judge/validate sang OpenAI nếu có credit | embed dừng |
| AA-TripPlanner-Web (tp_compose, tp_search_embed) | gateway riêng `backend/shared/llm_gateway.py`, `SUPPORTED_ACCOUNTS = ("acc3", "acc2")` cố định | chỉ chuyển model / account trong hai account đó; không registry, không Anthropic API | compose dừng | Cohere embed rơi sang dòng acc3 (cũng đang chặn) |
| AA-Partner (AI trả lời CRM) | chat qua Bedrock; pass 3 của bộ lọc PII là Bedrock Guardrail ở acc2 | fail-closed | AI CRM dừng | **mọi** lệnh AI CRM bị từ chối `scrub_failed`, dù model chạy đường nào |
| AA-Booking | chưa thấy code gọi Bedrock | — | — | — |

Việc code phải xong trước prod:

- TripPlanner: chuyển gateway sang registry dùng chung của CIS (chính code ghi là bản fork tạm), để dùng được account
  prod và `anthropic-direct`.
- Thêm account prod vào mọi gateway (CIS, TripPlanner, Partner).
- CRM: quyết định hành vi guardrail khi acc2 hỏng: guardrail thứ hai ở account hoặc region khác, hoặc giáng cấp rõ ràng
  sang "trả lời tay" kèm cảnh báo.

## 2. Có nên dồn hết về 1 account (hạ tầng dev + prod + AI)?

**Bây giờ thì không làm được.** Trên acc2 dưới TrueIDC, Claude và GPT đều bị từ chối; nguyên nhân chưa xác nhận
(thiếu giấy bán lại Anthropic là một cách giải thích, E-E4, E-E12, nhưng không giải thích được GPT vì chỉ Anthropic cần
giấy riêng, E-E9). Còn dồn về acc3 thì phải dời toàn bộ hạ tầng (RDS, ECS, Cognito, DNS), quá lớn.

**Lý lẽ mạnh nhất cho 1 account** (sau khi acc2 vào org AA với payer có giấy Anthropic):

1. Mọi lưu lượng thật dồn về một chỗ nên lịch sử dùng lớn nhanh; AWS ưu tiên tăng quota cho account đang dùng gần hết
   quota (C-C10). Chia lưu lượng ra nhiều account làm yếu từng đơn xin.
2. Một bộ đăng ký Marketplace, một ngoại lệ SCP, một chỗ để kiểm.
3. Bỏ hẳn một lớp lỗi: STS AssumeRole, trust policy / ExternalId lệch, cache credential hết hạn.
4. Sự kiện chính làm gãy Claude (đổi payer / org) là chung cho cả hai thiết kế (mục 1).
5. Tranh chấp dev / prod xử lý được trong một account bằng limiter `rpm_limit` / `max_concurrency` theo connection đã
   có trong gateway, cộng batch inference của Bedrock hoặc chạy viết lại catalog ngoài giờ cao điểm.

**Lý lẽ chống:**

- "Một account cho dev + prod + AI" đảo ngược quyết định tách prod của ADR 0018. Đó là quyết định bảo mật (người và
  quyền của dev không chạm được dữ liệu khách thật), không phải quyết định về LLM.
- Một account duy nhất tự làm account quản lý thì SCP không áp lên nó, nghĩa là prod chạy không có rào SCP. Tách acc4
  ra là **thực hành tốt AWS khuyến nghị** (account quản lý chỉ để billing và quản trị), không phải điều kiện kỹ thuật
  của Billing Transfer: một account đơn lẻ vẫn có thể tự lập org và làm bill-source.

| | 1 account (dev + prod + AI) | Mô hình đề xuất (aa-ai + aa-nonprod + aa-prod) |
|---|---|---|
| Hỏng tầng org / payer | mất mọi model Bedrock, còn đường 3 | **như nhau**: mất mọi model Bedrock, còn đường 3 |
| Hỏng tầng account | dev và prod cùng mất Bedrock | mất một account; prod còn đường khác nếu đã dựng đường 2 |
| Quota | lịch sử dồn một chỗ; dev tranh với prod, phải có limiter | quota chia ra; prod qua aa-ai vẫn tranh với dev, cũng phải có limiter |
| Độ phức tạp | không có role assume | giữ role invoker theo môi trường; code CIS đã có |
| Cách ly prod | không (trái ADR 0018) | có |
| Chi phí AWS | như nhau | như nhau. Organizations và IAM miễn phí (D-D12); STS thực tế không tính phí nhưng chưa thấy trang AWS chính thức ghi (U14) |
| Giấy tờ / hợp đồng | như nhau (một org, một Billing Transfer) | như nhau |

**Kết luận:** số account là yếu tố bậc hai với độ ổn định LLM. Những thứ quyết định:

1. Payer có giấy Anthropic **bằng văn bản**.
2. Đường ngoài AWS (Anthropic API) luôn ấm, cho các stage được phép dùng.
3. Quota dư trên đúng account mà prod gọi.
4. Mỗi route prod có hai họ model (và hai region nguồn).
5. Cảnh báo tức thời khi circuit mở.

Khuyến nghị: giữ aa-ai (acc3) cho dev và batch ngay bây giờ; prod ở aa-prod theo ADR 0018, gọi model qua role prod-only
của aa-ai có trần theo môi trường, `anthropic-direct` ấm phía sau; chỉ cho aa-prod tự gọi Bedrock tại chỗ khi đã kiểm
từng model trên aa-prod và đã làm ấm quota (kèm sửa ADR 0001a). Không gộp prod vào account dev, không dời hạ tầng vào
acc3.

### Phương án thêm: acc3 đứng riêng, ngoài org

Giữ acc3 đứng riêng, AWS là payer trực tiếp, trả bằng thẻ công ty. README §1 và §5 đã nêu đây là đường lui khi đại lý
không có giấy Anthropic (A-B3: account AI muốn payer khác thì phải ở ngoài org hoặc ở org khác).

- **Được:** không phụ thuộc giấy Anthropic của đại lý (U1); tránh hai lần đổi payer trong tháng 11 và 12.
- **Mất:** hoá đơn USD, không có hoá đơn VAT Việt Nam; acc3 không nằm dưới SCP của org; và đứng riêng không chắc chữa
  được Error 002 (E-E18: acc3 đang bị chặn đúng lúc đứng riêng).
- **Quyết định ở mục 3 bước 3** gắn với hai thứ: trả lời của case AWS và trả lời văn bản của đại lý cho câu 6a/6b. Chưa
  đủ cả hai thì chưa đưa acc3 vào org.

## 3. Thứ tự làm, theo tình huống hiện tại

0. **Ngay bây giờ, ngoài AWS, chạy song song với mọi bước sau.**
   - **0a. Cho Dev có đường LLM.** Tech lead tạo key Anthropic API mới (key cũ đã thu hồi), đặt giới hạn chi hằng tháng
     trong Anthropic Console, nạp credit. Chi phí: trả theo dùng, cộng khoảng 0,40 USD/tháng cho secret; số credit
     nạp do tech lead chốt trước khi mua. Lưu secret `aa-llm/dev/anthropic-direct`, bật connection và chạy
     `tools/llm/aa1002_anthropic_probe.py` theo runbook `docs/ops/runbooks/llm-anthropic-api-key.md`.
     Lưu ý data scope: với `allowed_scopes` hiện tại (migration 311) chỉ judge/validate dùng được key này. Muốn writer và
     các stage khác trên Dev chạy qua nó thì phải nới `allowed_scopes` cho từng stage trên Dev (Dev chỉ có dữ liệu thử,
     C7.1a). Đó là quyết định riêng, phải ghi lại; prod chọn lại từ đầu (mục 4). Bước này không phụ thuộc gì khác và gỡ
     áp lực thời gian khỏi case AWS.
   - **0b. Hỏi đại lý ngay.** Business owner gửi các câu ★ trong `reseller-questions.md` và đòi trả lời bằng văn bản.
     Thêm ba câu: hạn mức nhận Billing Transfer ("Inbound billing transfers", mặc định 0, chỉ account quản lý của đại lý
     xin nâng, AWS duyệt theo hồ sơ khách) đã được nâng chưa; chuỗi chuyển hoá đơn có đúng một cấp không (giới hạn mặc
     định độ dài chuỗi là 1; nếu đại lý lại chuyển tiếp lên nhà phân phối thì phải xin trước); đã đăng ký account nhận
     hoá đơn trong Partner Central chưa. Đây là việc chờ lâu nhất, nên làm đầu tiên.
1. **acc4, phần tay của tech lead** (kiểm, làm nốt phần chưa có; một phần đã chuẩn bị ở AA-1004):
   - Xác minh email root (AWS bắt buộc trước khi gửi lời mời member); email root là alias theo vai trò trên domain công
     ty, không phải email cá nhân; MFA phần cứng cho root.
   - Alternate contacts (billing, operations, security).
   - Thẻ + địa chỉ thanh toán Việt Nam + thông tin thuế mà AWS Marketplace chấp nhận (U4, U13): thẻ này trả Claude
     từ lúc acc3 vào org tới khi Billing Transfer chạy.
   - Danh tính admin qua IAM Identity Center để không dùng root hằng ngày; budget alarm trên acc4; profile CLI
     `aa-mgmt` có MFA.
   - Sau đó: bật Organizations (all features), tạo OU theo ADR 0018 (`NonProd`, `Prod`, `Suspended`), chưa gắn SCP chặn
     region. Nộp form Anthropic từ acc4 **bằng API** **trước khi** acc3 vào. Hướng dẫn hiện tại của AWS ghi form ở root
     account được các account trong org thừa hưởng (A-B9). API là cách an toàn vì thoả cả điều kiện cũ của blog 2025
     (B-B3). Hướng dẫn không nói rõ account vào org sau khi nộp form có thừa hưởng không, nên sau khi acc3 vào phải
     kiểm `agreementAvailability` trên acc3 và gọi thật.
2. **Đọc quota hiện tại của acc3 ngay** (rời org có thể làm quota đổi; AWS ghi "the account's quota limits may change"
   khi rời org). Ghi lại để so sau mỗi lần đổi:

   ```bash
   aws service-quotas list-service-quotas --service-code bedrock --region us-west-1 --profile nghiep_aa365 --query "Quotas[?contains(QuotaName,'Sonnet') || contains(QuotaName,'Haiku')].[QuotaName,Value]" --output table
   ```

3. **acc3: chờ case, có hạn chót, và không nằm trên đường găng.** Tạo org, OU, form Anthropic và nhận lời mời Billing
   Transfer đều làm được khi org chưa có member nào.
   - Error 002 **không có trong tài liệu AWS** (U3). Nhiều khả năng là chặn mức account (suy luận: acc3 bị từ chối cả
     Amazon Nova, model AWS tự bán, không qua Marketplace; cổng AWS mô tả trong tài liệu chỉ áp cho "some models").
     Chỉ case đang mở xác nhận được nguyên nhân và cách gỡ. Các thread re:Post nối Error 002 với account ít lịch sử
     hoá đơn hoặc bị gắn cờ lúc tạo, nhưng đó chỉ là nguồn cộng đồng.
   - Hỏi thẳng trong case: "Chúng tôi định đưa account này vào org của một account quản lý mới tạo. Nên làm trước hay
     sau khi các bạn gỡ chặn? Quyền Bedrock và quota có giữ nguyên khi đổi payer không? Payer là account quản lý mới, ít
     lịch sử thanh toán, có ảnh hưởng tới các kiểm Bedrock / Marketplace (kể cả kiểm 'valid payment method for AWS
     Marketplace purchases') trên acc3 không? Có nên để acc3 đứng riêng tới khi Billing Transfer sẵn sàng không?"
   - Hạn chót: nếu tới khoảng **07/11** AWS chưa trả lời thì nhắc lại trong case. Nâng gói Support của acc3 một tháng để
     được trả lời nhanh hơn là tuỳ chọn có phí: báo giá tháng (trang AWS Support plans) cho tech lead trước, chỉ làm khi
     tech lead đồng ý.
   - Trước khi vào org: xuất Cost Explorer và hoá đơn của acc3, ghi số dư credit Lift (U7). Từ ngày vào, thẻ của acc3
     thôi được dùng, thẻ acc4 trả; hoá đơn của giai đoạn làm member nằm ở account quản lý.
   - Vào org khi đã có trả lời case **và** trả lời văn bản của đại lý cho 6a/6b. Đại lý không xác nhận được thì giữ acc3
     đứng riêng trả thẻ (mục 2, phương án thêm).
   - Khi vào: chọn khung giờ không có wave; để acc3 đứng thẳng dưới root 1 tuần; gọi thử từng route ngay; đọc lại quota
     (bước 2); gãy thì mở lại case ngay, ghi rõ mốc thời gian.
4. **Từ lúc acc3 vào org tới khi Billing Transfer chạy:** acc4 trả bằng thẻ. Model qua Marketplace (Claude, GPT,
   Cohere) tính vào thẻ của acc4. Credit Lift của acc3 có áp cho khoản Marketplace hay không thì chưa xác nhận (U7).
5. **Billing Transfer:** 01/12/2026 là ngày **sớm nhất có thể**, không phải ngày chắc chắn.
   - Điều kiện phía đại lý, phải xong trước khi đại lý gửi lời mời: giấy Anthropic áp cho khách Việt Nam theo Billing
     Transfer (văn bản), hạn mức nhận > 0 đã duyệt, chuỗi một cấp (hoặc hai cấp đã duyệt), đăng ký Partner Central.
   - acc4 chấp nhận chậm nhất 29/11/2026, tức trước 00:00 UTC 30/11 (trước ngày bắt đầu ít nhất 24 giờ, C-C17).
   - Không có văn bản xác nhận tới khoảng 25/11 thì bỏ tháng 12, nhắm 01/01/2027. Cái giá: thêm một tháng trả bằng thẻ
     acc4; không có gì gãy. Không ép ký cho kịp ngày.
   - Ngay sau 00:00 UTC ngày bắt đầu (07:00 giờ VN): probe mọi connection, đọc lại quota.
6. **acc2:** giữ ở TrueIDC tới khi hợp đồng cho rời; trong lúc đó gọi Claude/GPT qua acc3 (đường 1) và
   `anthropic-direct`, Cohere và guardrail vẫn tại chỗ. Khi rời: **chuyển thẳng** từ org TrueIDC sang org AA (AWS cho
   chuyển account giữa hai org từ 19/11/2025, README bước 3), không đứng riêng ở giữa nên không cần thẻ cho acc2. Điều
   kiện: TrueIDC không chặn việc rời, đổi email root sang email công ty trước, xuất Cost Explorer và hoá đơn trước, smoke
   Cohere Embed v4 + guardrail trước và sau, đọc quota acc2 trước và sau.
7. **aa-prod, khi có ngày go-live:** tạo sớm (vài tuần trước go-live), dựng role prod-only trong aa-ai, đặt trần theo
   môi trường. Nếu muốn có đường 2: chạy lưu lượng Claude thật nhỏ trên aa-prod để đăng ký Marketplace và tạo lịch sử,
   đọc quota, rồi mới xin tăng; sửa ADR 0001a.
8. **Kiểm tra sau mỗi lần đổi payer hoặc org** (và sau mỗi sự kiện hoá đơn: đổi thẻ, tranh chấp hoá đơn với đại lý):
   mỗi connection gọi một lệnh nhỏ qua `tools/llm/llm_connections_probe.py` (có ghi `shared.llm_call_log`), **kể cả các
   model fallback**, không chỉ model chính. Không tin `GetFoundationModelAvailability` một mình. Đăng ký Marketplace mới
   cần tới 15 phút (B-B4).

## 4. Cấu hình để gọi model ổn định khi lên prod

### Hai kịch bản go-live

- **A. aa-prod đã ở org AA, payer có giấy Anthropic, đã kiểm từng model:** prod gọi qua role prod-only của aa-ai
  (đường 1), có thể thêm đường 2 tại chỗ khi đã làm ấm; `anthropic-direct` phía sau.
- **B. Chưa gọi được Claude trong org (đại lý chưa xác nhận, hoặc acc2 còn ở TrueIDC cũng không sao):** prod chạy trên
  acc3 + Anthropic API. Quota acc3 phải tính đủ cho prod; wave dev bị giới hạn hoặc tạm dừng trên acc3; đường 3 là
  fallback bắt buộc, phải ấm. Việc acc2 còn ở TrueIDC không đổi gì với đường gọi LLM của prod.

| Lớp | Việc phải có | Ai làm | Khi nào |
|---|---|---|---|
| Hợp đồng | Đại lý xác nhận bằng văn bản: giấy Anthropic + OpenAI áp cho Billing Transfer ở Việt Nam, chấp nhận khoản Marketplace, không đặt SCP hay giữ root, hạn mức nhận Billing Transfer > 0, chuỗi một cấp, Partner Central | Business owner | Bắt đầu ngay (bước 0b) |
| Payer | Billing Transfer → đại lý (org vẫn của mình), không làm member trong org đại lý. Tài liệu AWS về rời org chỉ ghi: các thoả thuận org chấp nhận thay member (AWS Artifact) thôi áp, mất lịch sử Cost Explorer, quota có thể đổi. Việc mất quyền Marketplace / Bedrock khi đổi org là **giả thuyết nội bộ** từ sự cố 29/10 (E-E3, U12, U15), không phải luật AWS | acc4 | Sớm nhất 01/12 |
| Form + Marketplace | Form Anthropic ở acc4 (bằng API). Kiểm `agreementAvailability` và gọi thật trên từng account sau khi vào org. Lần gọi đầu ở mỗi account gọi model cần quyền `aws-marketplace:Subscribe/ViewSubscriptions/Unsubscribe` | tech lead | Một lần mỗi account |
| SCP | Chặn region nhưng chừa region của profile `us.*` / `global.*` (và `unspecified` cho global), chừa cả region nguồn thứ hai. Thử ở một OU trước | tech lead | Trước khi gắn SCP region |
| Model id + region | Gọi qua inference profile `us.*` / `global.*` (Claude 5.5 và GPT chỉ chạy qua profile). Profile trải suy luận ra nhiều region nhưng endpoint runtime và quota vẫn ở region nguồn us-west-1: thêm một dòng deployment thứ hai cho mỗi model prod với region nguồn khác (ví dụ us-west-2 hoặc us-east-1, kiểm SCP cho phép). Region thứ hai chỉ che sự cố region, không che chặn mức account (acc3 bị chặn ở cả hai region) | gateway config | Lúc dựng prod |
| Họ model + vòng đời | Mỗi route prod có fallback là phiên bản hoặc họ model khác, không chỉ cùng họ. Model chuyển Legacy thì không xin tăng quota được, EOL thì mất (C-C10): theo dõi ngày vòng đời Bedrock của model prod trong rà soát hằng tháng | tech lead + gateway | Lúc dựng prod, rồi hằng tháng |
| Quota prod | Đọc Service Quotas thật của account prod gọi (aa-ai, và aa-prod nếu có đường 2), không dựa vào lịch sử cũ. Xin tăng quota cross-region TPM/RPM cho đúng model prod dùng. Quota account mới **có thể** thấp hơn mặc định (C-C9); AWS ưu tiên account đang dùng gần hết quota (C-C10). Mốc 4–6 tuần trước go-live là đệm của mình, không phải cam kết của AWS | tech lead | Khi có ngày go-live |
| Tách dev / prod | Trần `rpm_limit` / `max_concurrency` theo môi trường trên các dòng connection acc3. Tự dừng wave khi có circuit của deployment prod đang mở. Mỗi môi trường có budget riêng | gateway config | Lúc dựng prod |
| Data scope | Chọn và ghi lại `allowed_scopes` cho từng stage prod ngay bây giờ. Stage nào giữ `aws_only` thì **không có fallback ngoài AWS**, phải nói rõ. Mở `vendor_direct` là quyết định quản trị dữ liệu: nội dung ra khỏi AWS, có nội dung tenant, áp DPA của Anthropic | tech lead | Trước khi dựng prod |
| Fallback | Thứ tự connection mỗi route: aa-ai (role prod-only) → [Bedrock tại chỗ aa-prod, nếu đã có] → Anthropic API (chỉ stage cho phép `vendor_direct`). Tuỳ chọn thêm OpenAI API key nếu route GPT quan trọng. Circuit breaker cho lỗi access / throttle đã có | gateway config (AA-1002 / AA-642) | Lúc dựng prod |
| Anthropic API ấm | Key dự phòng "nguội" nguy hiểm: tier của Anthropic phụ thuộc mức nạp và chi, key không dùng thì nằm ở tier thấp và bị throttle đúng lúc cần. Giữ ấm bằng một phần nhỏ lưu lượng thật hoặc probe hằng ngày; nạp trước credit + auto-reload; so giới hạn tier với đỉnh prod; budget tháng trên connection; báo động khi key hoặc credit hết | tech lead | Từ bước 0a |
| Gateway các app | TripPlanner chuyển sang registry chung; thêm account prod vào mọi gateway; chốt hành vi guardrail CRM (mục 1) | dev | Trước go-live |
| Giám sát | Probe mỗi connection mỗi ngày (thẻ availability + digest OPS-12) chưa đủ nhanh cho prod. Thêm cảnh báo **tức thời** khi một circuit mở trong `shared.llm_provider_health` (`llm_access_denied` hoặc throttled trên stage prod; breaker mở ngay với access denied, sau 3 lần liên tiếp với throttle). Kiểm hoá đơn Marketplace hằng tháng | một phần đã có | Lúc dựng prod |
| ADR | Sửa ADR 0001a nếu dùng đường 2 (Bedrock tại chỗ ở aa-prod) hoặc fallback chéo account | tech lead | Trước khi bật đường 2 |
| Không cần | Provisioned Throughput (đắt, chỉ cần khi traffic lớn và đều), account riêng cho log/security ở giai đoạn này | — | Khi gặp trigger |

## 5. Còn chưa chắc (phải hỏi)

- Hỏi AWS (trong case đang mở): Error 002 có liên quan tới việc acc3 rời org không? Vào org AA trước hay sau khi gỡ chặn?
  Quyền Bedrock và quota có giữ khi đổi payer không (U10)? Payer là account quản lý mới, ít lịch sử thanh toán, có ảnh
  hưởng các kiểm Bedrock / Marketplace trên acc3 không? Có nên để acc3 đứng riêng tới khi Billing Transfer sẵn sàng?
- Hỏi đại lý: các câu ★ trong `reseller-questions.md`. Quan trọng nhất: giấy Anthropic áp cho Billing Transfer ở Việt
  Nam (6a, 6b), chấp nhận khoản Marketplace (8), cộng ba câu mới ở bước 0b (hạn mức nhận, độ dài chuỗi, Partner Central).
- Hỏi TrueIDC: điều kiện để acc2 rời org, có chặn chuyển thẳng sang org khác không, ai giữ email root (câu 3–4 của
  blueprint S258 mục 5).
- Tự kiểm: tier và giới hạn tốc độ của tổ chức Anthropic sau khi nạp credit, so với đỉnh dự kiến của prod.
