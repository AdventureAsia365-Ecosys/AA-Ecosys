---
id: AUD-S261-aws-bedrock-org-access
title: "Bedrock access in our own AWS Organization under Billing Transfer (S261)"
description: "Bản tư vấn cho tech lead: org riêng + Billing Transfer qua đại lý thì account thành viên phải cấu hình gì để gọi Bedrock theo từng nhà cung cấp model (Anthropic, OpenAI, Amazon, Meta, Mistral, Cohere, DeepSeek...), các bước theo thứ tự và ai làm, câu hỏi cho đại lý, và có cần account AI riêng không."
type: report
status: active
owner: nghiep
audience: [cto, devops, engineer, agent]
applies_to: [ecosystem, aa-cis-infra]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1004, AA-1002, AA-642]
---

# Bedrock trong org riêng của công ty + Billing Transfer qua đại lý (S261)

Bản tư vấn viết cho tech lead (tiếng Việt, theo luật `docs/audits`). Đọc cùng thiết kế org S258
(`../2026-10-29-S258-aws-org-blueprint/README.md`), postmortem acc3
(`../../ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md`) và playbook
`../../ops/playbooks/llm-access-denied.md`.

- Cách làm: 5 hướng nghiên cứu (billing, cơ chế quyền Bedrock, các kiểu bị từ chối, kiến trúc account, hiện trạng nội
  bộ), rồi một vòng kiểm độc lập các ý chính với tài liệu AWS bản hiện hành (đọc ngày 31/10/2026). Phần lớn trang
  Bedrock User Guide không ghi ngày cập nhật, nên ở đây coi bản đọc ngày 31/10/2026 là bản mới nhất.
- Từng ý kèm URL, trích nguyên văn và kết quả kiểm nằm ở `claims.json`. Danh sách câu hỏi gửi đại lý, dán được
  ngay, nằm ở `reseller-questions.md`.
- Không ghi account ID. Tên dùng ở đây: **aa-management** (account quản trị mới), **aa-nonprod** (acc2 hôm nay),
  **aa-ai** (acc3 hôm nay), **aa-prod** (tạo khi go-live). Profile CLI theo S258: `aa-mgmt`, `aa-nonprod`, `aa-ai`
  (hôm nay acc2 = `aa365-admin`, acc3 = `nghiep_aa365`).
- Bản này chỉ đọc tài liệu. Không chạy lệnh ghi nào trên AWS. Các lệnh ở mục 3 là đề xuất để tech lead tự chạy.
- Giọng trung lập: liệt kê lựa chọn, không đẩy hợp đồng nào. Đại lý đang cân nhắc: eCloudvalley, Sun Cloud;
  TrueIDC đang là bên trả tiền cho acc2.

## 1. Trả lời ngắn

- **Billing Transfer giữ nguyên org của mình.** Account quản trị của đại lý trả toàn bộ hoá đơn gộp của org bên
  mình (cả account thành viên, cả mua hàng Marketplace như Claude, GPT). Bên mình vẫn toàn quyền quản trị: IAM, SCP,
  tạo và gỡ account, form Anthropic. Đại lý không gắn được SCP vào account của mình như khi mình là thành viên trong
  org của họ. Đổi lại, bên mình chỉ thấy chi phí "pro forma" theo giá đại lý đặt qua Billing Conductor, mất Cost
  Anomaly Detection, không thấy số dư credit, và phải dựng lại CUR (A-B1, A-B2, A-B15).
- **Mỗi org chỉ có một Billing Transfer ra ngoài, AWS không nâng giới hạn này.** Mọi account trong org (nonprod, ai,
  prod) cùng một bên trả tiền. Muốn account AI có bên trả tiền khác thì nó phải nằm ở org khác hoặc đứng riêng (A-B3).
- **Account thành viên cần gì để gọi Bedrock.** Từ 15/10/2025 không còn trang "Model access" để xin quyền từng
  model ở region thương mại. Model mở theo mặc định, kiểm soát bằng IAM + SCP. Còn lại 4 cửa:
  1. Quyền IAM `bedrock:InvokeModel*` (cộng ARN inference profile và mọi region đích nếu gọi cross-region).
  2. Model bán qua Marketplace (Claude, GPT bản thương mại, Cohere...): lần gọi đầu trong mỗi account, Bedrock tự
     đăng ký Marketplace. Người gọi lần đầu cần `aws-marketplace:Subscribe`, `Unsubscribe`, `ViewSubscriptions`, và
     account cần "phương thức thanh toán hợp lệ cho Marketplace".
  3. Riêng Anthropic: form First Time Use (FTU). Nộp **một lần từ aa-management bằng API**, mọi account thành viên
     thừa hưởng (trừ region opt-in, và không cần cho endpoint bedrock-mantle).
  4. Một cửa riêng ở mức account do AWS quyết ("additional account-level access"). Hai account cùng org có thể khác
     nhau. Thiếu cửa này thì làm đủ 1–3 vẫn bị từ chối; tài liệu AWS bảo liên hệ AWS Sales (acc3 hiện đang đi qua case
     AWS Support). Error 002 của acc3 khớp nhóm này nhất, nhưng đó là suy luận (chuỗi "Error 002" không có trong tài
     liệu AWS), và phải loại trừ trước IAM/SCP, quyền Marketplace, thanh toán, form PENDING (mục 3, bước 9).
- **Khác nhau theo provider.** Claude (Anthropic bán), GPT bản thương mại (OpenAI bán), Cohere (Cohere bán) đi qua
  Marketplace. Việc chúng phụ thuộc bên trả tiền là suy luận của mình (khớp sự cố acc3), AWS chỉ ghi "quyết theo từng
  account". Amazon Nova/Titan, Meta, Mistral, DeepSeek, Qwen, Google, MiniMax, Moonshot, NVIDIA, xAI, Z.AI và OpenAI
  gpt-oss không qua Marketplace (A-B11), không cần form hay quyền Marketplace. Với Claude còn một cửa nữa: đại lý bán lại
  Bedrock phải có **giấy phép bán lại của Anthropic** (resale authority). AWS nói từ 19/11/2025 đại lý "resell AWS
  services using Billing Transfer", nên gần như chắc cửa này áp cho Billing Transfer. Đây là suy luận, phải xin
  đại lý xác nhận bằng văn bản.
- **Có cần account AI riêng không?** AWS không bắt buộc. Gộp Bedrock vào account hạ tầng là mẫu hợp lệ (AWS SRA cho
  AI cho phép gộp). Lý do giữ aa-ai lúc này: một phần quyền Bedrock được quyết theo từng account (đăng ký
  Marketplace, phương thức thanh toán, cửa mức account; còn form Anthropic và SCP thì áp cả org), nên ít account gọi
  Bedrock thì ít chỗ có thể bị chặn; acc3 đã có lịch sử dùng LLM (quota mặc định phụ thuộc tuổi và lịch sử account), và ngoại lệ
  SCP cho định tuyến cross-region gói gọn trong một OU. Khi có prod, nên cho prod một hạn mức (quota) riêng, không
  dùng chung với các đợt chạy dev. Chi phí theo app vẫn tách được khi gộp (mục 5).
- **Điều kiện tiên quyết:** đại lý được chọn phải xác nhận bằng văn bản là giấy phép Anthropic của họ áp cho khách
  Việt Nam theo Billing Transfer. Nếu không có, Claude phải chạy ở một account nằm ngoài org (đứng riêng trả bằng
  thẻ, hoặc org khác), hoặc gọi thẳng API Anthropic (phương án D của S257).
- **Mốc thời gian:** Billing Transfer luôn bắt đầu 00:00 UTC ngày 1 của tháng. Từ hôm nay, sớm nhất là **01/12/2026**,
  lời mời phải được chấp nhận chậm nhất 29/11/2026 23:59:59 UTC (nên làm sớm hơn). Mọi chi phí tháng 11 của org mới
  do aa-management tự trả, nên cần thẻ trên aa-management.

## 2. Mô hình account đề xuất (bản gọn)

```text
                    Org của ĐẠI LÝ (bên ngoài, không quản trị org mình)
                    └── account quản trị của đại lý  = "bill-transfer account"
                              ▲   trả hoá đơn AWS (kể cả Marketplace), xuất hoá đơn VND/VAT cho bên mình
                              │   Billing Transfer (đại lý gửi lời mời, aa-management chấp nhận)
AWS Organization của công ty (all features)        ← bên mình giữ toàn quyền
├── aa-management ...... "bill-source account": chỉ quản trị (Organizations, Identity Center, budget,
│                        org CloudTrail, kích hoạt cost allocation tag, nộp form Anthropic bằng API).
│                        Không chạy ứng dụng. SCP không áp lên account này.
├── OU NonProd   [SCP region + ngoại lệ định tuyến Bedrock]
│   └── aa-nonprod (acc2) ... ECS/RDS/S3 dev+staging; gọi Bedrock qua role trong aa-ai
│                              (Cohere Embed v4 + guardrail đang gọi trực tiếp tại chỗ)
├── OU AI        [SCP region + ngoại lệ định tuyến Bedrock (cả 'unspecified' cho global.*)]
│   └── aa-ai (acc3) ......... chỉ Bedrock: role invoker cho nonprod (và prod khi có)
└── OU Prod      [SCP chặt hơn]  (khi go-live)
    └── aa-prod .............. khách thật; LLM: role riêng hoặc gọi Bedrock tại chỗ (mục 5)
```

Ai trả tiền gì:

| Khoản | Trước ngày bắt đầu Billing Transfer | Sau ngày bắt đầu |
|---|---|---|
| Hạ tầng (ECS, RDS, S3...) của mọi account trong org | aa-management (thẻ của công ty) | Đại lý trả AWS, xuất hoá đơn cho bên mình |
| Bedrock model do AWS bán (Nova, Llama, Mistral, DeepSeek, Qwen, gpt-oss) | aa-management | Đại lý (hoá đơn Bedrock thường) |
| Model bán qua Marketplace (Claude, GPT, Cohere) | aa-management (Marketplace) | Hoá đơn Marketplace chuyển sang account của đại lý, thuế tính theo hồ sơ thuế của đại lý |
| Billing Conductor | — | Gói AWS managed: 0 USD. Gói customer managed: 50 USD/org/tháng từ 01/06/2026. Ai chịu: hỏi đại lý |
| Credit của mình (Lift, Activate) | Trừ vào hoá đơn của mình | Vẫn áp, nhưng trừ vào hoá đơn AWS gửi đại lý; bên mình không thấy số dư nữa. Hợp đồng phải ghi đại lý trả lại phần này |

So với kiểu "account thành viên trong org của đại lý" (acc2 với TrueIDC hôm nay): khi đó đại lý là management, gắn
được SCP (ví dụ chặn `bedrock:InvokeModel`), gỡ account, và có thể chặn bên mình tự rời org (A-B21). Billing Transfer
không chuyển account đi đâu. Rút ra lúc nào cũng được, hiệu lực cuối tháng hiện tại hoặc tháng sau, không hoàn tác
được (A-B20).

## 3. Cấu hình từng bước (theo thứ tự)

Ký hiệu người làm: **[BM]** bên mình (tech lead), **[ĐL]** đại lý, **[AWS]** AWS Support/Sales.
Mọi lệnh viết một dòng, thay `<...>` trước khi chạy. Lệnh `converse` tốn vài token (không đáng kể).

### Bước 0. Chốt đại lý bằng văn bản [BM + ĐL]
Gửi `reseller-questions.md`. Ba câu bắt buộc phải có văn bản (phụ lục hợp đồng) trước khi ký: (1) đây là Billing
Transfer, không phải đưa account vào org của đại lý; (2) giấy phép bán lại Anthropic áp cho khách Việt Nam theo
Billing Transfer; (3) account của đại lý chấp nhận các khoản Marketplace (Claude, GPT, Cohere) và không đặt chính
sách chặn. Hỏi luôn trong case AWS đang mở (Error 002): chuyển acc3 vào org trước hay sau khi AWS gỡ chặn.

Đọc câu trả lời để quyết (số câu theo `reseller-questions.md`):

| Câu trả lời | Quyết định |
|---|---|
| Câu 1 = Không, hoặc câu 2 = Có | Loại đại lý này (không giữ được quyền quản trị org) |
| Câu 3b = Không | Đại lý không bán lại được Bedrock (suy luận từ luật SPP): không dùng đại lý này cho org có account gọi Bedrock |
| Câu 6a = Không (không có giấy phép Anthropic hoặc không có văn bản) | Vẫn dùng được đại lý cho hạ tầng + model AWS bán; Claude chạy ở account ngoài org (đứng riêng trả thẻ, hoặc org khác) hoặc API Anthropic trực tiếp |
| Câu 6a = Có, 6b = Không (chỉ áp cho account trong org đại lý) | Như dòng trên, hoặc chấp nhận kiểu thành viên trong org đại lý (mất quyền SCP/root, không khuyến nghị) |
| Câu 8 = Không, hoặc chặn OpenAI/Cohere | Provider bị chặn phải chạy ngoài org như Claude ở trên |
| Câu 6a, 6b, 8 = Có, có văn bản | Đi tiếp bước 1–11 với một payer cho cả org |

### Bước 1. Tạo aa-management + bật Organizations all features [BM]
Account mới, MFA phần cứng cho root, thẻ thanh toán (cần cho tháng 11), budget. Billing Transfer yêu cầu cả hai org
ở chế độ all features.

- `aws organizations create-organization --feature-set ALL --profile aa-mgmt`
- Kiểm: `aws organizations describe-organization --profile aa-mgmt --query Organization.FeatureSet --output text` → `ALL`

### Bước 2. Đưa aa-ai (acc3) vào org [BM, AWS tư vấn thời điểm]
acc3 đang đứng riêng, nên chỉ cần mời rồi chấp nhận. Đặt vào OU riêng chưa gắn SCP chặn trong 1 tuần đầu (OU
Transitional của S258), rồi mới chuyển sang OU AI.

- `aws organizations invite-account-to-organization --target Id=<AI_ACCOUNT_ID>,Type=ACCOUNT --profile aa-mgmt`
- `aws organizations list-handshakes-for-account --profile aa-ai --region us-east-1`
- `aws organizations accept-handshake --handshake-id <h-...> --profile aa-ai --region us-east-1`

### Bước 3. Đưa aa-nonprod (acc2) từ org TrueIDC sang org mình [BM + ĐL TrueIDC]
Từ 19/11/2025 AWS cho chuyển account thẳng từ org này sang org khác, không phải đứng riêng ở giữa, nên không cần thẻ
riêng cho acc2 lúc chuyển. Điều kiện thực tế: TrueIDC không chặn (họ là management, có thể chặn rời org bằng SCP),
và cần biết ai giữ email root + MFA của acc2.

- Trước khi chuyển: chạy thử Cohere Embed v4 + guardrail, mở sẵn case AWS, chọn lúc ít việc (rủi ro E-1 của S257:
  acc2 có thể bị chặn Bedrock như acc3).
- Mời: `aws organizations invite-account-to-organization --target Id=<NONPROD_ACCOUNT_ID>,Type=ACCOUNT --profile aa-mgmt`
- Chấp nhận từ acc2: `aws organizations accept-handshake --handshake-id <h-...> --profile aa-nonprod --region us-east-1`
- Sau khi chuyển: xoá `OrganizationAccountAccessRole` cũ nếu TrueIDC từng tạo (role này không tự mất).

### Bước 4. Billing Transfer [ĐL gửi, BM chấp nhận]
- [ĐL] Từ account quản trị của họ: Billing and Cost Management > Billing transfers > Inbound billing > Send
  invitation (API `InviteOrganizationToTransferResponsibility`, type BILLING), chọn ngày bắt đầu (ngày 1 của tháng,
  từ tháng sau tới 6 tháng). Bên mình không gửi được lời mời.
- [BM] Trước ngày bắt đầu: tải về CUR, Budgets, dữ liệu hoá đơn (sau đó CUR cũ thành "Unhealthy").
- [BM] Chấp nhận: Billing transfers > Outbound billing > View details > Accept, hoặc
  `aws organizations list-handshakes-for-account --filter HandshakeType=TRANSFER_RESPONSIBILITY --profile aa-mgmt --region us-east-1`
  rồi `aws organizations accept-handshake --handshake-id <h-...> --profile aa-mgmt --region us-east-1`.
- Hạn: chấp nhận ít nhất 24 giờ trước ngày bắt đầu. Với 01/12/2026: chậm nhất 29/11/2026 23:59:59 UTC (tài liệu AWS
  ghi lệch nhau vài giờ, nên làm trước vài ngày).
- [BM] Sau khi bắt đầu: dựng lại CUR (pro forma), hỏi đại lý gói Billing Conductor (giá niêm yết hay giá của họ).

### Bước 5. Form Anthropic (FTU), một lần cho cả org [BM]
Nộp từ aa-management **bằng API**: blog bảo mật AWS (10/2025) nói thừa hưởng chỉ có hiệu lực khi nộp qua API; User
Guide hiện hành không nhắc điều kiện này, nhưng nộp bằng API thì đúng theo cả hai nguồn. Nội dung form: companyName,
companyWebsite, intendedUsers, industryOption, otherIndustryOption, useCases (kiểm lại mẫu trong
`model-access.html` trước khi chạy).

- `aws bedrock put-use-case-for-model-access --form-data fileb://<ftu.json> --profile aa-mgmt --region us-west-1`
- Kiểm ở từng account thành viên (đọc `agreementAvailability.status`; PENDING thì vẫn bị AccessDenied tới khi
  AVAILABLE): `aws bedrock get-foundation-model-availability --model-id <anthropic-model-id> --profile aa-ai --region us-west-1`
- Lấy model-id đúng: `aws bedrock list-foundation-models --by-provider anthropic --profile aa-ai --region us-west-1 --query "modelSummaries[].modelId" --output text`

### Bước 6. SCP [BM]
SCP không áp lên aa-management. Thử ở OU tạm trước khi gắn OU NonProd / AI / Prod. Làm từ aa-management:

- Lấy root: `aws organizations list-roots --profile aa-mgmt --query "Roots[0].Id" --output text`
- Bật SCP: `aws organizations enable-policy-type --root-id <r-...> --policy-type SERVICE_CONTROL_POLICY --profile aa-mgmt`
- Tạo OU (làm cho Transitional, NonProd, AI, Prod): `aws organizations create-organizational-unit --parent-id <r-...> --name AI --profile aa-mgmt`
- Chuyển account vào OU: `aws organizations move-account --account-id <AI_ACCOUNT_ID> --source-parent-id <r-... hoặc ou-...> --destination-parent-id <ou-...> --profile aa-mgmt`
- Tạo SCP: `aws organizations create-policy --name aa-scp-region-bedrock --type SERVICE_CONTROL_POLICY --description "Region guard with Bedrock routing exception" --content file://<scp-ai.json> --profile aa-mgmt`
- Gắn vào OU: `aws organizations attach-policy --policy-id <p-...> --target-id <ou-...> --profile aa-mgmt`

Mẫu cho OU AI (và NonProd nếu nonprod gọi Bedrock tại chỗ):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyOtherRegionsExceptBedrockRouting",
      "Effect": "Deny",
      "NotAction": ["iam:*", "organizations:*", "sts:*", "support:*", "budgets:*", "ce:*", "cur:*",
                    "aws-marketplace:*", "license-manager:*", "sso:*", "account:*", "health:*",
                    "route53:*", "cloudfront:*"],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {"aws:RequestedRegion": ["us-west-1", "us-west-2", "us-east-1"]},
        "Null": {"bedrock:InferenceProfileArn": "true"}
      }
    },
    {
      "Sid": "OptionalDenyProvider",
      "Effect": "Deny",
      "Action": "bedrock:*",
      "Resource": ["arn:aws:bedrock:*::foundation-model/deepseek.*", "arn:aws:bedrock:::foundation-model/deepseek.*"]
    }
  ]
}
```

Cách hoạt động:
- Điều kiện `Null` chỉ miễn chặn cho các lần kiểm foundation-model có mang `bedrock:InferenceProfileArn`. Nhờ vậy
  `us.*` vẫn tới được us-east-2, và `global.*` vẫn qua được lần kiểm có `aws:RequestedRegion = unspecified`. Lần kiểm
  ARN profile ở region nguồn không mang key này, nên us-west-1 vẫn phải nằm trong danh sách cho phép.
- Danh sách `NotAction` là ví dụ: đối chiếu với danh sách dịch vụ toàn cầu trong blueprint S258 (`aa-scp-region`).
- Statement thứ hai là mẫu AWS (DenyDeepseekEverywhere), chỉ thêm khi công ty có chính sách cấm một provider. Chặn
  `aws-marketplace:Subscribe` **không** chặn được lần gọi đầu; muốn chặn model phải Deny `bedrock:*` trên ARN model.

### Bước 7. Role gọi model trong aa-ai [BM]
Trust policy (cho role chạy task của app trong aa-nonprod; giữ ExternalId như pattern satellite hiện tại; cho phép
`sts:TagSession` để ghi tag app vào chi phí):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::<NONPROD_ACCOUNT_ID>:role/<app-task-role>"},
    "Action": ["sts:AssumeRole", "sts:TagSession"],
    "Condition": {"StringEquals": {"sts:ExternalId": "<external-id>"}}
  }]
}
```

Permission policy (ghép từ mẫu trong tài liệu AWS, chưa chạy thử):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SystemInferenceProfilesAndProject",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": [
        "arn:aws:bedrock:us-west-1:<AI_ACCOUNT_ID>:inference-profile/us.anthropic.*",
        "arn:aws:bedrock:us-west-1:<AI_ACCOUNT_ID>:inference-profile/global.anthropic.*",
        "arn:aws:bedrock:us-west-1:<AI_ACCOUNT_ID>:inference-profile/us.openai.*",
        "arn:aws:bedrock:us-west-1:<AI_ACCOUNT_ID>:inference-profile/global.openai.*",
        "arn:aws:bedrock:us-west-1:<AI_ACCOUNT_ID>:inference-profile/us.amazon.*",
        "arn:aws:bedrock:us-west-1:<AI_ACCOUNT_ID>:project/default"
      ]
    },
    {
      "Sid": "FoundationModelsOnlyBehindAProfile",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/*",
        "arn:aws:bedrock:us-east-2::foundation-model/*",
        "arn:aws:bedrock:us-west-1::foundation-model/*",
        "arn:aws:bedrock:us-west-2::foundation-model/*",
        "arn:aws:bedrock:::foundation-model/*"
      ],
      "Condition": {"StringLike": {"bedrock:InferenceProfileArn": "arn:aws:bedrock:us-west-1:<AI_ACCOUNT_ID>:inference-profile/*"}}
    },
    {
      "Sid": "InRegionModels",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": [
        "arn:aws:bedrock:us-west-1::foundation-model/amazon.*",
        "arn:aws:bedrock:us-west-1::foundation-model/cohere.embed-*"
      ]
    },
    {
      "Sid": "OptionalMarketplaceFirstCallViaBedrockOnly",
      "Effect": "Allow",
      "Action": ["aws-marketplace:Subscribe", "aws-marketplace:Unsubscribe", "aws-marketplace:ViewSubscriptions"],
      "Resource": "*",
      "Condition": {"StringEquals": {"aws:CalledViaLast": "bedrock.amazonaws.com"}}
    }
  ]
}
```

Ghi chú:
- Converse/InvokeModel kiểm quyền bằng `bedrock:InvokeModel`; ConverseStream bằng `InvokeModelWithResponseStream`.
- Profile `us.*` gọi từ us-west-1 đi tới us-east-1, us-east-2, us-west-1, us-west-2 (theo model card Claude Sonnet
  5.5). Region đích khác nhau tuỳ model: kiểm bằng
  `aws bedrock get-inference-profile --inference-profile-identifier us.anthropic.<model> --profile aa-ai --region us-west-1`.
- GPT trên bedrock-runtime cần thêm quyền trên `project/default`. Endpoint bedrock-mantle dùng action riêng
  (`bedrock-mantle:CreateInference`), không có cross-region, và chỉ phục vụ GPT-5.5 ở us-east-1/us-east-2.
- Statement Marketplace là tuỳ chọn. Cách gọn hơn là bước 8: admin bật từng model một lần, sau đó role gọi model
  không cần quyền Marketplace.
- Tạo role (trong aa-ai; lâu dài đưa vào Terraform AA-CIS-Infra, không sửa tay):
  `aws iam create-role --role-name <invoker-role> --assume-role-policy-document file://<trust.json> --profile aa-ai`
  rồi `aws iam put-role-policy --role-name <invoker-role> --policy-name bedrock-invoke --policy-document file://<invoke.json> --profile aa-ai`
- Phía gọi (aa-nonprod): role chạy task của app cũng phải được Allow `sts:AssumeRole` + `sts:TagSession` trên
  `arn:aws:iam::<AI_ACCOUNT_ID>:role/<invoker-role>` (thêm vào policy của task role trong Terraform). Thiếu một trong
  hai phía thì AssumeRole bị từ chối.

### Bước 8. Đăng ký Marketplace lần gọi đầu, mỗi account, mỗi model bán qua Marketplace [BM]
Admin của aa-ai (có quyền Marketplace) gọi thử từng model Claude / GPT / Cohere một lần. Việc đăng ký chạy nền tới
15 phút. Nếu lúc đầu thiếu quyền, sau khi cấp quyền có thể bị từ chối thêm khoảng 2 phút.

- `aws bedrock-runtime converse --model-id us.anthropic.<model> --messages '[{"role":"user","content":[{"text":"ping"}]}]' --inference-config '{"maxTokens":16}' --profile aa-ai --region us-west-1 --query "output.message.content[0].text" --output text`
- Kiểm trạng thái: `aws bedrock get-foundation-model-availability --model-id <model-id> --profile aa-ai --region us-west-1`

Cách khác (khi có nhiều account gọi Bedrock): **managed entitlements**. aa-management (hoặc delegated admin) đăng ký
một lần, rồi cấp grant qua AWS License Manager cho account, OU hoặc cả org. Account có grant không cần quyền
Marketplace riêng. License luôn nằm ở us-east-1. Nếu đại lý hoặc provider có private offer: xin họ phát offer cho
**aa-management**, vì giá riêng chỉ áp cho account chấp nhận offer cho tới khi cấp grant.

### Bước 9. Quota [BM; AWS duyệt]
Quota tính theo account, theo region, theo model, và tách theo endpoint (bedrock-runtime và bedrock-mantle khác
nhau). Account mới hoặc ít dùng có thể nhận mức thấp hơn mức mặc định công bố.

- Đọc mức thật của từng account:
  `aws service-quotas list-service-quotas --service-code bedrock --profile aa-ai --region us-west-1 --query "Quotas[?contains(QuotaName,'Sonnet')].[QuotaName,QuotaCode,Value]" --output table`
- Mã quota (L-xxxx) có trong AWS General Reference (ví dụ "Cross-Region model inference tokens per minute for
  Anthropic Claude Sonnet 4.6" = L-15B8E632, Claude Haiku 4.5 = L-58BE175A). Vẫn lấy mã từ lệnh trên cho từng account.
- Xin tăng (bedrock-runtime): xin trên quota "Cross-Region InvokeModel tokens per minute for <model>"; support sẽ đề
  nghị tăng luôn on-demand TPM và "Cross-Model Max Tokens Per Day". RPM (nếu có, Adjustable) xin riêng.
  `aws service-quotas request-service-quota-increase --service-code bedrock --quota-code <L-xxxx> --desired-value <N> --profile aa-ai --region us-west-1`
- AWS ưu tiên account đang dùng gần hết quota; account để không có thể bị từ chối. Model Legacy/Deprecated không được
  tăng. bedrock-mantle: xin qua form "Service limit increase" của AWS Support (ghi endpoint, region, model, quota, giá
  trị, kèm số liệu CloudWatch).
- Tăng quota **không** mở được chặn ở mức account. Gặp chặn kiểu Error 002 thì trước hết loại trừ: Deny trong
  IAM/SCP, model có ở region không, quyền Marketplace, phương thức thanh toán, `agreementAvailability` còn PENDING,
  thiếu quyền `project/default` (GPT); thử luôn một model AWS bán (Nova). Nếu Nova cũng bị từ chối thì mới xin
  "grant this account access" (AWS Sales / case Support), đừng xin "raise TPM".

### Bước 10. Theo dõi chi phí [BM]
- Kích hoạt cost allocation tag (gồm tag IAM principal / session tag và tag của application inference profile) từ
  aa-management. Account thành viên không làm được. Tag chỉ có hiệu lực từ lúc bật, có thể mất tới 24 giờ.
  Lệnh (sau khi tag đã xuất hiện trong dữ liệu billing): `aws ce update-cost-allocation-tags-status --cost-allocation-tags-status TagKey=app,Status=Active --profile aa-mgmt --region us-east-1`
- Tạo CUR 2.0 export mới có chọn "include caller identity" (export cũ không tự có).
- Theo Billing Transfer, tag của bên mình hiện trong CUR của đại lý. Việc lọc theo tag trên Cost Explorer pro forma
  phía mình có chạy không: chưa xác nhận.

### Bước 11. Kiểm tra cuối (mỗi account gọi Bedrock, mỗi route) [BM]
- `aws sts get-caller-identity --profile aa-ai`
- `aws organizations describe-organization --profile aa-ai --query Organization.MasterAccountId --output text` (phải là aa-management)
- Claude: lệnh `converse` ở bước 8 với `us.anthropic.<model>` và `global.anthropic.<model>`
- Nova: `aws bedrock-runtime converse --model-id us.amazon.<nova-model> --messages '[{"role":"user","content":[{"text":"ping"}]}]' --inference-config '{"maxTokens":16}' --profile aa-ai --region us-west-1 --query "output.message.content[0].text" --output text`
- GPT: gọi theo đúng API mà LLM gateway dùng (Responses/Chat qua `us.openai.<model>` + project/default)
- Cohere Embed v4 trên aa-nonprod: smoke test có sẵn của app
- Từ app: chạy probe của gateway (playbook `llm-access-denied.md`) cho mọi route đang bật.

## 4. Bảng theo provider

| Provider | Ai bán / qua Marketplace? | Form | Quyền lần gọi đầu | us-west-1 | Quota | Cần hỏi đại lý |
|---|---|---|---|---|---|---|
| Amazon (Nova, Titan) | AWS; không qua Marketplace | Không | Chỉ `bedrock:InvokeModel*` | Tuỳ model: xem model card (có model chỉ qua `us.*`) | Đọc Service Quotas từng account | Không phụ thuộc giấy phép provider; vẫn có thể dính chặn mức account (acc3 bị chặn cả Nova) |
| Anthropic (Claude) | Anthropic bán, qua Marketplace (có product ID, ví dụ Sonnet 5.5 `prod-pjfguoisodbd6`) | FTU, một lần ở aa-management bằng API | `aws-marketplace:Subscribe/Unsubscribe/ViewSubscriptions` + thanh toán Marketplace hợp lệ | Sonnet 5.5, Haiku 5.5: chỉ `us.*` / `global.*` | Có thể thấp ở account mới (acc2 hôm nay: Sonnet 4.6 10 rpm) | Giấy phép bán lại Anthropic, phạm vi Việt Nam + Billing Transfer, bằng văn bản |
| OpenAI GPT thương mại (GPT-5.4, 5.5, 5.6) | OpenAI bán, qua Marketplace (ví dụ GPT-5.5 `prod-indw4nwkcsyua`) | Không | Như trên + `project/default` | bedrock-runtime: chỉ `us.*` / `global.*`; mantle: GPT-5.5 ở us-east-1/2, GPT-5.6 ở us-east-1/2, us-west-2 | Runtime và mantle tách riêng | Payer chấp nhận khoản Marketplace của OpenAI; Việt Nam có trong "Supported Countries" của OpenAI không (chưa xác nhận) |
| OpenAI gpt-oss (open-weight) | AWS bán; không qua Marketplace | Không | Chỉ `bedrock:InvokeModel*` | Xem model card | Service Quotas | Không |
| Meta (Llama) | AWS bán; không qua Marketplace | Không | Chỉ `bedrock:InvokeModel*` | Xem model card | Service Quotas | Không |
| Mistral | AWS bán (serverless); không qua Marketplace. Riêng Mistral trên "Bedrock Marketplace" bán kiểu khác | Không | Chỉ `bedrock:InvokeModel*` | Xem model card | Service Quotas | Không |
| DeepSeek, Qwen | AWS bán; không qua Marketplace | Không | Chỉ `bedrock:InvokeModel*` | Xem model card | Service Quotas | Không (nếu công ty cấm thì chặn bằng SCP) |
| Cohere (Embed v4) | Cohere bán, qua Marketplace (`prod-ft3cj5gst3spo`), tính phí dưới tên Cohere | Không | Quyền Marketplace + thanh toán hợp lệ | acc2 đang gọi tại chỗ | RPM (embedding tính theo RPM) | Payer chấp nhận khoản Marketplace của Cohere. acc2 đang gọi được dưới TrueIDC, nên (suy luận) ít nhất TrueIDC không chặn Cohere |
| Google, MiniMax, Moonshot, NVIDIA, xAI, Z.AI | Không qua Marketplace, không có product key (A-B11) | Không | Chỉ `bedrock:InvokeModel*` | Xem model card | Service Quotas | Không. Chưa kiểm từng model trong bản này; xem model card trước khi dùng |
| Khác (AI21, Writer, Luma, Stability, TwelveLabs) | Phần lớn qua Marketplace, nhưng phải xem trường "Marketplace product ID" trên từng model card | Không | Theo product ID | Xem model card | Service Quotas | Chỉ hỏi nếu định dùng |

Ghi chú:
- Model không qua Marketplace thì chặn bằng Deny trên ARN model (SCP/IAM), hoặc không cho Allow.
- Model qua Marketplace hiện trên hoá đơn và Cost Explorer dưới tên provider, không dưới "Amazon Bedrock".

## 5. Một account hạ tầng + một account AI: có cần không

| Tiêu chí | Gộp Bedrock vào aa-nonprod (và aa-prod) | Giữ aa-ai riêng (hiện tại) |
|---|---|---|
| AWS có bắt buộc không | Không. SRA cho AI cho phép gộp khi AI dùng khắp tổ chức | Mẫu mặc định của SRA (Application account + Generative AI account) |
| Rủi ro bị chặn quyền model | Mỗi account gọi Bedrock là một chỗ có thể bị chặn riêng (nonprod, prod) | Một chỗ duy nhất để mở khoá và kiểm; sự cố 29/10 chỉ ảnh hưởng LLM, hạ tầng vẫn chạy |
| Quota | Quota của account hạ tầng (acc2 hôm nay rất thấp, xin tăng Cohere từng bị từ chối) | acc3 đã có lịch sử dùng LLM; nhưng dev và prod dùng chung một quota nếu prod cũng gọi qua aa-ai |
| SCP | SCP của workload phải mang ngoại lệ định tuyến cross-region | Ngoại lệ gói trong OU AI, OU NonProd/Prod giữ SCP region chặt |
| Chi phí AWS | Không thêm | Không thêm phí (Organizations, IAM miễn phí; STS miễn phí chưa thấy trang AWS chính thức ghi) |
| Độ phức tạp | Bỏ được code assume-role satellite | Thêm role, ExternalId, cache credential, thêm một chỗ để debug |
| Theo dõi chi phí | Lọc theo service (Bedrock / provider Marketplace) + tag | Tách sẵn theo account |
| Giấy tờ Anthropic | Form một lần ở aa-management, như nhau | Như nhau |
| Bên trả tiền | Cùng một payer cho cả org | Cùng payer nếu ở trong org; muốn payer khác thì phải ra ngoài org |

Khuyến nghị cho quy mô 2–3 người:
- **Bây giờ:** giữ aa-ai riêng, đưa vào org của mình dưới cùng payer Billing Transfer, nếu đại lý xác nhận giấy phép
  Anthropic. Nếu đại lý không có giấy phép Anthropic: giữ aa-ai ngoài org (đứng riêng, thẻ hoặc payer khác) chỉ cho
  Claude, còn các model AWS bán vẫn gọi được trong org.
- **Khi go-live:** đừng để traffic prod dùng chung quota với các đợt chạy dev trong aa-ai. Hai cách: aa-prod tự gọi
  Bedrock (sau khi kiểm từng model trên aa-prod), hoặc tạo aa-prod-ai. Tách theo môi trường là một lựa chọn trong SRA,
  không phải yêu cầu.
- **Khi nào gộp:** khi aa-nonprod (và aa-prod) đã gọi được thật mọi route bằng InvokeModel và quota đủ. Lúc đó bỏ
  code satellite, theo dõi chi phí bằng:
  - IAM principal attribution: Bedrock ghi role gọi cho mỗi request (cả runtime và mantle); một role hoặc session tag
    `app=cis|booking|crm|tp` cho mỗi app, kích hoạt tag ở aa-management, CUR 2.0 bật caller identity.
  - Application inference profile: bọc một model, gắn tag, truyền ARN thay model ID. Chỉ cho InvokeModel/Converse
    trên bedrock-runtime; Responses/Chat Completions dùng Projects (bedrock-mantle) hoặc IAM principal.
  - Mức chi tiết: theo usage type theo ngày, không theo từng request (từng request thì đã có `shared.llm_call_log`).
- Guardrail toàn org không cần account riêng: từ 04/2026 có Bedrock policy trong Organizations áp guardrail từ
  management cho mọi account.

## 6. Rủi ro và bẫy

| Rủi ro | Dấu hiệu | Cách tránh |
|---|---|---|
| Đổi org / đổi payer làm account bị chặn Bedrock (như acc3 ngày 29/10) | Error 002 / AccessDenied cho cả Nova | Mở case AWS trước khi chuyển, chuyển lúc ít việc, smoke test trước và sau, có đường dự phòng (API trực tiếp) |
| Rời org mất thoả thuận org; đăng ký Marketplace có thể phải làm lại | GPT bị từ chối ngay sau khi acc3 rời org | Sau mỗi lần chuyển org, gọi lại từng route, chờ tới 15 phút để tự đăng ký lại |
| Đại lý không có giấy phép Anthropic | Claude bị từ chối trên mọi account trong org | Xin văn bản trước khi ký; phương án dự phòng ở mục 5 |
| Account mới quota thấp | Throttling ngay từ đầu | Đọc quota thật, xin tăng sớm, giữ account có lịch sử |
| SCP chặn region đích của `us.*` (thiếu us-east-2) hoặc `global.*` (thiếu 'unspecified') | AccessDenied chỉ khi đi cross-region | Dùng ngoại lệ `bedrock:InferenceProfileArn` như mẫu mục 3 |
| Chặn Marketplace mà tưởng chặn được model | Model vẫn gọi được | Deny `bedrock:*` trên ARN model |
| Form Anthropic nộp bằng console ở management, member không thừa hưởng | Claude AccessDenied ở member | Nộp bằng API; kiểm `agreementAvailability` ở từng member |
| Credit Lift của acc3 (~250 USD, hết hạn 31/12/2026) khi đổi payer | Không thấy số dư; không chắc trả được cho Marketplace | Hỏi AWS + đại lý; hợp đồng ghi rõ cách trừ credit |
| Mất công cụ chi phí (CAD, CUR cũ, giá AWS) | Không còn cảnh báo bất thường | Budget theo account, tải dữ liệu trước ngày bắt đầu, hỏi đại lý CUR pro forma |
| Hỗ trợ bán lại (Resold Support) | AWS Support không nhận case tài khoản/billing | Hỏi đại lý mô hình hỗ trợ trước khi ký |
| Hợp đồng mẫu lệch cam kết qua chat (eCloudvalley: mẫu ghi kiểu thành viên trong org, giữ root, phí 10 %) | — | Chỉ tin điều khoản trong hợp đồng/phụ lục |
| Tháng 11 chưa có Billing Transfer | Hoá đơn USD gửi aa-management | Thẻ trên aa-management; kế toán biết trước |

## 7. Chưa xác nhận được (cần hỏi đại lý / AWS)

| # | Điều chưa rõ | Hỏi ai |
|---|---|---|
| U1 | Billing Transfer có bị coi là "bán lại" (channel account) trong cửa Anthropic không, và giấy phép Anthropic của đại lý có áp cho khách Việt Nam theo Billing Transfer không. AWS ghi đại lý "resell ... using Billing Transfer" nhưng không trang nào nối thẳng Anthropic với Billing Transfer | Đại lý (văn bản); có thể hỏi aws-reseller-program@anthropic.com |
| U2 | Các "limitations" khi bán lại Anthropic chỉ nằm trong FAQ Partner Central (không công khai) | Đại lý |
| U3 | Chuỗi "Error 002: Access to Bedrock models is not allowed for this account" không có trong tài liệu AWS; cộng đồng mô tả nó là ValidationException, còn tài liệu nói AccessDeniedException. Có phải "additional account-level access" không, có gắn với đổi org/payer không | AWS case đang mở |
| U4 | Org bill-source không có thẻ riêng có qua được kiểm "valid payment method for AWS Marketplace" không | AWS Support / đại lý |
| U5 | Account của đại lý có cần quyền/cho phép riêng cho từng provider Marketplace không, hay chỉ cần trả hoá đơn | Đại lý |
| U6 | Đại lý có chặn gì với Marketplace của khách Billing Transfer không (FAQ chỉ nói họ "may" dùng SCP cho việc ẩn số PO) | Đại lý |
| U7 | Credit Lift có trả cho khoản Marketplace (Claude, GPT) không; còn áp không khi vào org / Billing Transfer | AWS + đại lý |
| U8 | Phí Billing Conductor 50 USD/org/tháng (gói customer managed): đại lý hay bên mình chịu; bên mình thấy giá niêm yết hay giá đại lý | Đại lý |
| U9 | Cost Explorer pro forma phía mình có lọc theo cost allocation tag không | Đại lý / thử sau khi bắt đầu |
| U10 | Quyền mức account và lịch sử quota có giữ khi account chuyển payer / org không | AWS |
| U11 | Việt Nam có trong "Supported Countries" của OpenAI không (trang help.openai.com trả 403 khi đọc) | Đại lý / OpenAI |
| U12 | Đổi payer có làm mất đăng ký Marketplace đã có của account không | AWS |
| U13 | Lỗi "restricted geo-location" khi đăng ký Marketplace dựa vào quốc gia của payer hay của account | AWS |
| U14 | STS AssumeRole miễn phí: chỉ thấy nguồn bên thứ ba | (không chặn quyết định) |
| U15 | Ý kiến nội bộ "quyền model bên thứ ba đi theo payer" (postmortem): khớp với quan sát, nhưng AWS chỉ ghi "quyết theo từng account" | AWS case |

## 8. Nguồn

Trang AWS đọc ngày 31/10/2026; phần lớn không ghi ngày cập nhật, ghi ngày khi trang có.

- Billing Transfer tổng quan (GA 19/11/2025): <https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing.html>
- Billing Transfer quota: <https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing-quotas.html>
- Gửi lời mời: <https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing-send-invitation.html>
- Trả lời lời mời: <https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing-respond-invitation.html>
- Rút Billing Transfer: <https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing-stop-transfer.html>
- Credit theo Billing Transfer: <https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/useconsolidatedbilling-credits.html>
- Cost allocation tag: <https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html>
- Marketplace FAQ cho người mua theo Billing Transfer: <https://docs.aws.amazon.com/marketplace/latest/buyerguide/billing-transfer-faq-for-buyer.html>
- Billing Conductor giá (phí từ 01/06/2026): <https://aws.amazon.com/aws-cost-management/aws-billing-conductor/pricing/>
- Chuyển account thẳng giữa org (19/11/2025): <https://aws.amazon.com/about-aws/whats-new/2025/11/aws-organizations-direct-account-transfers/>
- Rời org (account thành viên): <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_leave-as-member.html>
- Khái niệm Organizations: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html>
- Organizations miễn phí: <https://docs.aws.amazon.com/organizations/latest/userguide/pricing.html>
- Bedrock tự mở model (15/10/2025): <https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-bedrock-automatic-enablement-serverless-foundation-models/>
- Blog bảo mật "Simplified Amazon Bedrock model access" (15/10/2025, sửa 22/10/2025): <https://aws.amazon.com/blogs/security/simplified-amazon-bedrock-model-access/>
- Bedrock model access: <https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html>
- Managed entitlements: <https://docs.aws.amazon.com/bedrock/latest/userguide/managed-entitlements.html>, <https://docs.aws.amazon.com/bedrock/latest/userguide/managed-entitlements-subscribing.html>
- Mã lỗi Bedrock: <https://docs.aws.amazon.com/bedrock/latest/userguide/troubleshooting-api-error-codes.html>
- Quota Bedrock: <https://docs.aws.amazon.com/bedrock/latest/userguide/quotas.html>, <https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-runtime.html>, <https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-mantle.html>, <https://docs.aws.amazon.com/general/latest/gr/bedrock.html>
- Cross-region: <https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html>, <https://docs.aws.amazon.com/bedrock/latest/userguide/geographic-cross-region-inference.html>, <https://docs.aws.amazon.com/bedrock/latest/userguide/global-cross-region-inference.html>
- Model card: Claude Sonnet 5.5 (ra mắt 28/09/2026) <https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-sonnet-5-5.html>, Claude Haiku 5.5 <https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-haiku-5-5.html>, GPT-5.5 (ra mắt 01/06/2026) <https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-55.html>, GPT-5.6 Terra <https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-56-terra.html>, GPT-5.4 <https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-54.html>
- IAM actions Bedrock: <https://docs.aws.amazon.com/service-authorization/latest/reference/list_bedrock.html>
- Resource policy Bedrock: <https://docs.aws.amazon.com/bedrock/latest/userguide/security_iam_service-with-iam.html>
- Chi phí theo app: <https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-application-inference-profiles.html>, <https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-iam-principal-tracking.html>
- Guardrail toàn org (03/04/2026): <https://aws.amazon.com/about-aws/whats-new/2026/04/bedrock-guardrails-cross-account-safeguards>
- Điều khoản model bên thứ ba (Anthropic 18/08/2025, OpenAI 06/2026): <https://aws.amazon.com/legal/bedrock/third-party-models/>
- Bedrock cho đại lý bán lại (14/10/2025): <https://aws.amazon.com/blogs/apn/amazon-bedrock-now-available-for-partner-resale/>
- Danh sách dịch vụ được bán lại SPP (cập nhật 24/09/2026): <https://solution-provider-program-legal-documents.s3-us-west-2.amazonaws.com/Solution+Provider+Program+List+of+Services.pdf>
- Activate credit terms (22/01/2026): <https://aws.amazon.com/activate/terms/>
- AWS Support case: <https://docs.aws.amazon.com/awssupport/latest/user/case-management.html>
- SRA cho Generative AI: <https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture-generative-ai/gen-ai-sra.html>
- Lợi ích nhiều account: <https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/benefits-of-using-multiple-aws-accounts.html>
- Anthropic supported countries (hiệu lực 12/11/2026): <https://www.anthropic.com/supported-countries>
- Nội bộ: postmortem acc3, playbook llm-access-denied, S257 `angle1-aws-partners-vn.md` + `migration-assessment.md`,
  S258 blueprint, log S260.

## Artifact

- `aws-llm-model.html`: <https://claude.ai/artifact/5zccrpwjZ31c2XtiP4HRfu> (private, claude.ai account nghieppham@adventure.asia since S261)
