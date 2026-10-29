---
id: OPS-AWS-ORG-blueprint-s258
title: "AWS organization, governance, environments and IaC blueprint (S258)"
description: "Bản thiết kế tổ chức và quản trị AWS cho hệ sinh thái: tài khoản quản trị + thành viên, OU, SCP, Identity Center, thanh toán, dev/staging/prod, tổ chức lại Terraform, profile CLI, LLM gateway nhiều nguồn, lộ trình, kiểm thử, chi phí, vận hành, rủi ro, quyết định."
type: report
status: active
owner: nghiep
audience: [cto, devops, engineer, agent]
applies_to: [ecosystem, aa-cis-infra]
last_reviewed: 2026-10-29
review_every_days: 30
related: [AA-1002, AA-880, AA-864, AA-642, AA-900, AA-998]
---

# Thiết kế tổ chức và quản trị AWS (S258, AA-1002)

Bản tư vấn kiến trúc viết cho tech lead (tiếng Việt, theo luật docs/audits). Nguồn: 3 nghiên cứu (repo cũ
AdventureAsia365/AA-Project-Infra, kiểm kê AA-CIS-Infra, chuẩn AWS/Terraform hiện hành) → thiết kế → phản biện độc lập
(28 chỉnh sửa đã áp). Trang đọc (artifact riêng tư, kèm email/câu hỏi cho chủ doanh nghiệp và bảng so
sánh đại lý): <https://claude.ai/artifact/6XpQ8YUU7w7HsZ9AoGfnRb>. Điều khoản hợp đồng của đại lý không ghi ở đây.

Mọi chi phí là ước tính theo giá niêm yết us-west-1; số Dev hiện tại chưa ổn định.

## 0. Bản gọn cho startup (khuyến nghị)

Quyết định của tech lead (S258, 29/10): đội 2–3 lập trình viên nên dùng 2 môi trường (dev+staging chung, prod riêng) và 3–4 tài khoản; phần 1–14 bên dưới là đích xa khi công ty lớn.

Đội 2–3 lập trình viên: chỉ 2 môi trường (dev+staging chung, prod riêng) và 3–4 tài khoản. Công ty vẫn giữ tài khoản quản trị và quyền gốc; mọi thứ dựng bằng Terraform nên khi lớn lên chỉ cần thêm tài khoản theo điều kiện ở bảng cuối, không phải làm lại.

```text
AWS Organization của công ty
├── aa-management ...... (mới, anh vừa tạo) chỉ quản trị: Organizations, Identity Center, billing, budget, org CloudTrail
├── OU NonProd
│   └── aa-nonprod ..... (đã có 005097885195, tài khoản hạ tầng hôm nay) dev + staging dùng chung
├── OU Prod
│   └── aa-prod ........ (tạo khi có ngày go-live) khách thật
└── aa-ai .............. (đã có 786888028788) chỉ Bedrock; vào org nếu mô hình thanh toán cho phép;
                         gộp vào nonprod/prod khi 2 tài khoản đó gọi được Bedrock
```

### So với bản đầy đủ

| Mục | Bản đầy đủ (9 tài khoản) | Bản gọn (khuyến nghị) | Vì sao đủ |
|---|---|---|---|
| Số tài khoản | 9 | 3 ngay (management, nonprod, ai) + prod khi go-live | Ít tài khoản thì 2–3 người quản lý được; ranh giới quan trọng nhất (prod tách khỏi thử nghiệm) vẫn giữ |
| Môi trường | dev / staging / prod, 3 tài khoản | dev + staging chung tài khoản nonprod; prod riêng | Staging chỉ bật khi cần (trước release, UAT), không tốn tiền chạy liên tục |
| Log, security, backup, shared | 4 tài khoản riêng | Nằm trong management (log CloudTrail) và prod (backup); thêm tài khoản khi chạm điều kiện | Chưa có yêu cầu kiểm toán hay khách doanh nghiệp đòi tách |
| OU | 7 OU | 2 OU (NonProd, Prod) + Suspended | Đủ để gắn SCP khác nhau cho prod |
| SCP | ~9 | 3 | Các chặn quan trọng nhất; thêm khi cần |
| Nhóm quyền | 6 nhóm, 8 permission set | 3 nhóm, 3 permission set | Đúng số người |
| Thời gian kỹ sư | ~30+ ngày công | ~5–8 ngày công (prod tính riêng khi go-live) | Dùng lại Terraform hiện có, không tái cấu trúc lớn |

### Tài khoản

| Tài khoản | ID | Chứa gì | Ai vào | Chi phí/tháng (ước tính) | Khi nào |
|---|---|---|---|---|---|
| aa-management | (anh vừa tạo — cần ghi ID) | Organizations, IAM Identity Center, billing + budget, org CloudTrail + bucket log, không chạy ứng dụng | Tech lead (Admin), chủ doanh nghiệp (Billing, chỉ xem) | 0–3 USD | Ngay (ngày 1) |
| aa-nonprod | 005097885195 | Toàn bộ dev hiện tại + staging bật khi cần (cùng RDS, database riêng `aa_stg`; ECS service stg để 0 task khi không dùng) | Tech lead, lập trình viên (toàn quyền), agent/CI (role riêng) | Như hôm nay ~255–265; staging bật vài ngày/tháng +20–60 | Đã có; vào org khi xong mô hình thanh toán |
| aa-prod | (mới) | Khách thật: VPC, RDS Multi-AZ, ECS 2 task, CloudFront/WAF, Cognito prod, backup + bản sao sang us-west-2 | Tech lead (Admin 1 giờ), lập trình viên (chỉ đọc), CI qua GitHub environment có người duyệt; không agent | 280–410 có tiết kiệm / 410–580 giá niêm yết | Khi chị chốt ngày go-live; dựng 3–5 ngày bằng cùng module |
| aa-ai | 786888028788 | Chỉ Bedrock, role invoker cho nonprod và prod | Tech lead, lập trình viên | Theo lượng gọi | Đã có; giữ tới khi nonprod/prod tự gọi được Bedrock |

### Hai môi trường

| Tiêu chí | dev + staging (tài khoản nonprod) | prod (tài khoản prod) |
|---|---|---|
| Dữ liệu | Dữ liệu mẫu, tour thật của công ty; staging dùng bản sao có ẩn danh khi cần | Dữ liệu thật của khách và đại lý |
| Quy mô | 1 task mỗi dịch vụ; RDS db.t4g.small một AZ; staging tắt khi không dùng | 2 task mỗi dịch vụ khách dùng; RDS Multi-AZ; tự scale theo tải |
| Sao lưu | 7 ngày tự động | 14 ngày, khôi phục theo thời điểm, bản sao sang us-west-2; diễn tập khôi phục mỗi quý |
| Deploy | Merge vào main → tự deploy dev; staging deploy bằng tay khi cần thử release | Cùng bản build (image) đã chạy ở dev/staging, bấm duyệt trong GitHub environment `production` |
| Tên miền | *.lumiguides.it.com (hôm nay), stg-*.lumiguides.it.com | Tên miền chính thức của công ty |
| Đăng nhập | Cognito dev (E2E, thử) | Cognito prod riêng, bắt MFA |
| AI | Qua LLM gateway, mọi đường bật thử được | Qua LLM gateway, chỉ đường đã duyệt, có trần chi |

### Quản trị tối thiểu

| Hạng mục | Cấu hình | Ghi chú |
|---|---|---|
| Identity Center — Admin | Tech lead; mọi tài khoản; phiên 1 giờ ở prod | Không dùng IAM user / khoá cố định |
| Identity Center — Developer | 2–3 lập trình viên; toàn quyền nonprod, chỉ đọc prod | Thêm người = thêm vào nhóm |
| Identity Center — Billing | Chủ doanh nghiệp; xem chi phí, hoá đơn | Không quyền kỹ thuật |
| CI / agent | GitHub OIDC role theo tài khoản; agent chỉ có role nonprod | Prod: chỉ CI có người duyệt |
| SCP 1 | Cấm rời tổ chức, cấm đóng tài khoản (AWS tự gắn nếu tạo org bằng console sau 10/07/2026) | Mọi tài khoản thành viên |
| SCP 2 | Cấm tắt CloudTrail / đổi cấu hình billing ở tài khoản thành viên | Mọi tài khoản thành viên |
| SCP 3 | Chỉ cho vùng us-west-1, us-west-2, us-east-1 (+ ngoại lệ dịch vụ toàn cầu và định tuyến AI chéo vùng) | Gắn OU NonProd, Prod |
| Break-glass | Root của management có khoá MFA phần cứng (2 khoá: dùng + cất két); root tài khoản thành viên xoá tập trung | Chỉ dùng khi Identity Center hỏng |
| Ngân sách | Budget mỗi tài khoản + tổng, cảnh báo theo dự báo; Cost Anomaly Detection ở management | Miễn phí |

### Terraform: thay đổi tối thiểu

| Bước | Làm gì | Công |
|---|---|---|
| 1 | Giữ repo AA-CIS-Infra; root `accounts/aa365` thành root của nonprod (đổi tên dần, không dời state ngay) | 0 |
| 2 | Thêm root `accounts/management` (Organizations, OU, SCP, Identity Center, budget, org CloudTrail) | 1–2 ngày |
| 3 | Tách phần môi trường trong `accounts/aa365` thành `modules/environment` (VPC, RDS, ECS, edge) bằng `moved` block, plan không đổi gì | 2–3 ngày (làm dần) |
| 4 | Khi go-live: root `accounts/prod` gọi cùng `modules/environment` với biến prod; state bucket riêng | 3–5 ngày |
| 5 | CI: plan khi mở PR theo root bị đổi, apply khi merge; prod qua GitHub environment có người duyệt; job drift hằng đêm (đang làm) | 1 ngày |
| 6 | Bỏ account ID viết cứng trong module (đọc từ data source / biến) | 0,5 ngày |

### Profile CLI

| Profile | Tài khoản | Quyền | Thay cho |
|---|---|---|---|
| aa-mgmt | aa-management | Admin | (mới) |
| aa-nonprod | aa-nonprod | Admin / Developer | aa365-admin, default, aa365-admin-session, aa365-admin-toolkit |
| aa-prod | aa-prod | ReadOnly; Admin khi cần | (mới) |
| aa-ai | aa-ai | Developer | nghiep_aa365 |
| (gỡ) | — | — | aa-dev/stg/prod(-admin) cũ của Quanskill, pqnghiep-admin, acc1-legacy-default |

### Lộ trình gọn

| Bước | Khi nào | Công | Phụ thuộc |
|---|---|---|---|
| Bật Organizations + Identity Center + budget ở aa-management, tạo 3 nhóm | Ngày 1 (2–3 giờ) | 0,5 ngày | Có ID tài khoản quản trị |
| Root Terraform `accounts/management` | Tuần 1 | 1–2 ngày | — |
| Mời aa-ai vào org (sau khi hỏi AWS về credit Lift và Bedrock) | Khi chốt mô hình thanh toán AI | 0,5 ngày | Quyết định của chị Thư |
| Mời aa-nonprod vào org (rời tổ chức TrueIDC / Billing Transfer) | Khi TrueIDC hoặc đại lý mới xác nhận | 1 ngày + thời gian giấy tờ | Trả lời của đại lý |
| Staging bật-khi-cần trong nonprod | Trước release lớn đầu tiên | 1–2 ngày | — |
| Tạo aa-prod + dựng bằng module | 3–4 tuần trước go-live | 3–5 ngày | Ngày go-live, duyệt chi phí |

### Khi nào mới mở rộng (điều kiện)

| Thêm gì | Khi nào |
|---|---|
| Tài khoản log-archive + security riêng | Có khách doanh nghiệp / kiểm toán đòi, hoặc > 5 kỹ sư |
| Tài khoản staging riêng | Staging phải bật liên tục hoặc khách UAT trên staging |
| Tài khoản backup riêng | Dữ liệu prod có giá trị lớn / yêu cầu chống xoá |
| Tài khoản shared-services | Nhiều tài khoản cùng cần ECR/DNS chung |
| Tách tài khoản theo app | Một app có đội riêng hoặc chi phí/quyền cần tách hẳn |
| Dịch vụ bảo mật trả phí (GuardDuty, Security Hub, Config) | Trước go-live hoặc khi có dữ liệu nhạy cảm; chờ duyệt riêng từng mục |


## 1. Tổng quan: hôm nay → mục tiêu

Hôm nay mọi app chạy trên 1 account infra (005097885195). Account này là thành viên org của nhà bán TrueIDC. Account AI (786888028788) đứng riêng và đang bị AWS khoá Bedrock (Error 002). Công ty chưa có AWS Organization của mình. Mục tiêu là lấy account quản trị vừa tạo (aa-management) làm gốc Organization của công ty. dev / staging / prod nằm ở 3 account riêng, cạnh các account nền (log, security, backup, shared-services, shared-ai). Quản trị bằng Identity Center + SCP; IaC là Terraform tách theo stack, mỗi account một bucket state. Account AI nằm ở đâu và có vào org hay không phụ thuộc mô hình thanh toán (mục 5).

```text
AWS Organization của công ty  (management = aa-management, account vừa tạo)
Root   [FullAWSAccess, aa-scp-root (DenyMemberRoot)]  [AI services opt-out]
├── aa-management ............ không thuộc OU; không chạy workload; SCP không áp lên account này
├── OU Security               [aa-scp-baseline, aa-scp-region]
│   ├── aa-log-archive ....... (mới) org CloudTrail, log S3/ALB/Config, Data Exports
│   ├── aa-security .......... (mới) delegated admin: Access Analyzer, GuardDuty/Security Hub/Config (khi được duyệt)
│   └── aa-backup ............ (mới, phase 6) vault nhận bản copy backup prod, vault lock
├── OU Infrastructure         [aa-scp-baseline, aa-scp-region-ai]
│   ├── aa-shared-services ... (mới) ECR trung tâm, artifact Lambda, DNS dùng chung
│   └── aa-shared-ai ......... (đã có: 786888028788) Bedrock — CHỈ vào org nếu mô hình thanh toán cho phép (mục 5)
├── OU Workloads              [aa-scp-baseline, aa-scp-region, aa-scp-workloads]
│   ├── OU NonProd            [aa-scp-nonprod-cost]
│   │   ├── aa-dev ........... (đã có: 005097885195) môi trường dev hiện tại
│   │   └── aa-staging ....... (mới)
│   └── OU Prod               [aa-scp-prod]
│       └── aa-prod .......... (mới)
├── OU Sandbox                [aa-scp-baseline, aa-scp-region, aa-scp-nonprod-cost] để trống
├── OU Policy-Staging ........ thử SCP mới trước khi gắn rộng
├── OU Transitional .......... [chỉ FullAWSAccess + aa-scp-root] chỗ đỗ tạm cho account vừa gia nhập (rời org được)
└── OU Suspended ............. [aa-scp-denyall] account chờ đóng (90 ngày)
(FullAWSAccess gắn ở MỌI OU — không ghi lặp trong cây)
```

### Bức tranh mục tiêu theo lớp

| Lớp | Hôm nay | Mục tiêu | Vì sao |
|---|---|---|---|
| Sở hữu account | Không có org riêng. Account infra thuộc org o-cnvpmom3os của TrueIDC (management 033086823579, feature set ALL, nên nhà bán áp được SCP). Account AI rời org eCloudvalley ngày 29/10, đứng riêng và bị Error 002 | Org của công ty, management = aa-management (account mới). Mọi account là member, trừ account AI nếu chọn Billing Transfer cho TrueIDC (mục 5) | Công ty tự giữ SCP, Identity Center, quyền mở/đóng account. Bên thứ ba không còn vào được bằng OrganizationAccountAccessRole |
| Môi trường | Chỉ có Dev. ADR 0012 (29/10) đặt prod chung account infra, không có staging | dev / staging / prod, mỗi môi trường một account | Ranh giới cứng bằng account thay cho tag/boundary. Staging dùng để diễn tập release, migration, UAT |
| Danh tính | Nhiều profile làm tay (role + MFA, STS 8h). Có IAM user nền aa365-nghiep-base. Profile Quanskill cũ và acc1 vẫn còn trong config | IAM Identity Center: nhóm → permission set → account; một sso-session duy nhất. Break-glass ngoài Identity Center | Đăng nhập một lần, MFA tập trung, thu hồi quyền ở một chỗ, không còn access key dài hạn |
| Chính sách (guardrail) | Không có SCP của công ty. Cách ly chỉ dựa vào tag, boundary, key policy trong account | SCP gộp thành vài tài liệu (≤5 SCP mỗi đích), RCP (data perimeter có miễn trừ OIDC), tag policy, backup policy, AI opt-out | Guardrail đặt ngoài account nên không gỡ được từ bên trong |
| Log / kiểm toán | Trail aa-cis-dev-trail trong account infra (multi-region, KMS, Object Lock GOVERNANCE 365 ngày) | Org trail đổ vào aa-log-archive; member không sửa hay xoá được | Bằng chứng nằm ngoài account bị kiểm |
| Backup | RDS automated 7 ngày trong cùng account | Prod: AWS Backup copy sang region us-west-2 VÀ sang account aa-backup (vault lock) | Chống mất dữ liệu khi account prod bị chiếm quyền |
| IaC | 1 root accounts/aa365 chứa toàn bộ (785 resource theo kế hoạch trước, chưa đếm lại) trong 1 state. Root acc3-bedrock apply tay bằng profile cá nhân, không có khoá state | live/<account>/<region>/<stack>, mỗi stack một state, mỗi account một bucket state, module có version, CI plan/apply theo stack | Thu nhỏ blast radius. Promote dev → staging → prod bằng version module |
| CI/CD | OIDC chỉ có ở account infra. GitHub environment 'prod' thực ra apply Dev. Có sẵn environment dev/staging/prod nhưng không có reviewer. ECR nằm trong account infra | Mỗi account một OIDC provider + role. Environment dev/staging/prod/org; prod/org có reviewer. ECR trung tâm, replicate sang prod, promote bằng digest | Tên đúng nghĩa, cổng duyệt thật, cùng một image chạy ở mọi môi trường |
| Thanh toán | TrueIDC xuất hoá đơn cho account infra. Account AI trả bằng Lift credit (còn 249.94 USD, hết hạn 31/12) rồi tới thẻ | Chọn theo bảng kịch bản mục 5; quyết định ở phase 0 | Giữ hợp đồng đã ký mà vẫn giữ quyền quản trị, và không làm gãy Claude |
| AI / LLM | AWS từ chối mọi model Bedrock trên account AI (Error 002, khoá cấp account). Account infra không gọi được Claude vì TrueIDC không có giấy Anthropic | Một account AI đã chạy được (aa-shared-ai) cho cả 3 môi trường, song song đường API trực tiếp (phương án D của S257) | Không phụ thuộc một account hay một reseller |

_Nguồn: docs/adr/0012-environment-model.md; infra/AA-CIS-Infra/accounts/aa365/versions.tf, security_cloudtrail.tf, security_guardduty.tf; accounts/acc3-bedrock/versions.tf; docs/audits/2026-10-29-S257-llm-access-options/; https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html_

### Học gì từ repo cũ AdventureAsia365/AA-Project-Infra

| Điểm | Repo cũ làm | Học / không học | Lý do |
|---|---|---|---|
| Mỗi môi trường một account | DEV/STG/PROD = 3 account ở ap-southeast-1 | Học (dùng account mới ở us-west-1; 3 account Quanskill không thuộc hệ sinh thái) | Đúng khuyến nghị của AWS |
| Identity Center + MFA | Có, MFA bắt buộc | Học | Thay profile làm tay |
| GitHub Actions OIDC, không access key | Có | Học, nhưng mỗi account một OIDC provider | Đã làm ở acc2 |
| SCP khoá region | Có (theo docs/architecture.md) | Học, kèm ngoại lệ cho Bedrock global inference | — |
| IaC | KHÔNG có Terraform thật: scripts/terraform/modules chỉ có .gitkeep; hạ tầng dựng bằng console, lưu bằng ảnh chụp | Không học | Không tái tạo hay kiểm drift được |
| Branch theo môi trường | develop → staging → main | Không học | Trái trunk-based ADR-2026-023; promote bằng SHA/digest |
| Deploy | EC2 + SSM Run Command | Không học | Hệ sinh thái dùng ECS Fargate + Lambda |

_Nguồn: gh api repos/AdventureAsia365/AA-Project-Infra (README.md, docs/architecture.md, cây thư mục), đọc 29/10/2026._

## 2. Thiết kế AWS Organization

aa-management chỉ làm việc quản trị: Organizations, Identity Center, billing, policy. Workload đặt ở account khác, vì SCP không áp lên management account. Hai account có sẵn giữ nguyên ID, chỉ đổi vai trò. Có thêm 6 account mới, tạo dần theo phase. Mỗi account tự giữ bucket state Terraform của mình.

### aa-management: cái gì được đặt, cái gì không

| Hạng mục | Ở aa-management? | Ghi chú |
|---|---|---|
| Organizations, OU, SCP/RCP/tag/backup/AI opt-out policy | Có | Terraform stack live/management/global/10-organization |
| Trusted access cho dịch vụ | Có | Bật: CloudTrail, IAM (centralized root access), Identity Center, Account Management (alternate contact), Backup, Access Analyzer, (sau) GuardDuty/Security Hub/Config |
| IAM Identity Center (user, group, permission set) | Có (phase 1) | Có thể delegate sang aa-security ở phase 7. Delegated admin không quản được permission set đã gán cho chính management |
| Billing, Cost Explorer, org budget, cost allocation tag, Data Exports | Có | Chủ doanh nghiệp xem qua permission set AA-Billing. Data Exports đổ vào S3 ở aa-log-archive để app đọc chi phí mà không phải vào management |
| Tạo org CloudTrail | Có | Bucket đích ở aa-log-archive |
| Terraform state của các stack management | Có (bucket riêng) | Mỗi account một bucket; không phụ thuộc account khác |
| Root user | Chỉ dùng cho break-glass | 2 khoá FIDO2, email nhóm, không access key |
| 1 IAM user break-glass | Có (ngoại lệ duy nhất) | FIDO2, không access key, EventBridge cảnh báo khi đăng nhập. Dùng khi Identity Center hỏng |
| Workload (ECS, RDS, Lambda, S3 dữ liệu app) | KHÔNG | SCP không chặn được principal trong management |
| Bedrock / LLM, ECR, DNS app, secret app | KHÔNG | Thuộc shared-ai / shared-services / account môi trường |
| Role cho workload assume vào (vd đọc Cost Explorer) | KHÔNG | Workload không được có đường vào management |
| CI deploy app | KHÔNG | Chỉ có role CI plan/apply của stack org, qua environment 'org' có reviewer |

_Nguồn: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html ; https://docs.aws.amazon.com/organizations/latest/userguide/orgs_integrate_services_list.html_

### Cây OU

| OU | Mục đích | SCP gắn trực tiếp (ngoài FullAWSAccess) | Account |
|---|---|---|---|
| Root | — | aa-scp-root (DenyMemberRoot) | — |
| Security | Log, bảo mật, backup (giữ tên tương thích Control Tower) | aa-scp-baseline, aa-scp-region | aa-log-archive, aa-security, aa-backup |
| Infrastructure | Dịch vụ dùng chung | aa-scp-baseline, aa-scp-region-ai (thêm region Bedrock + 'unspecified') | aa-shared-services, aa-shared-ai (nếu ở trong org) |
| Workloads | Cha của NonProd/Prod | aa-scp-baseline, aa-scp-region, aa-scp-workloads | — |
| Workloads/NonProd | dev, staging | aa-scp-nonprod-cost | aa-dev, aa-staging |
| Workloads/Prod | Khách hàng thật | aa-scp-prod | aa-prod |
| Sandbox | Thử ngắn hạn, không nối prod | aa-scp-baseline, aa-scp-region, aa-scp-nonprod-cost | (trống) |
| Policy-Staging | Thử SCP/RCP mới | Bản nháp đang thử | aa-staging gắn tạm khi còn trống (phase 1 → 5) |
| Transitional | Account vừa gia nhập, chờ kiểm; còn rời org được | Không gắn thêm | Account AI/infra trong 1–2 tuần đầu |
| Suspended | Account chờ đóng | aa-scp-denyall | (trống) |

_Mỗi đích gắn trực tiếp tối đa 5 SCP, tính cả FullAWSAccess; mỗi SCP tối đa 5.120 ký tự. SCP kế thừa không tính vào giới hạn của đích con. FullAWSAccess phải gắn ở mọi tầng. Nguồn: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html_

### Danh mục account

| Tên account | Email root (quy ước) | Mục đích | OU | Region | Ai truy cập | Chi phí/tháng (ước tính, list us-west-1) | Trạng thái |
|---|---|---|---|---|---|---|---|
| aa-management | Email đã dùng khi tạo (CẦN GHI LẠI; nên là hộp thư nhóm aws+management@adventure.asia) | Organizations, Identity Center, billing, policy | Root | us-west-1 (Identity Center); billing là global | Tech lead (Admin 1h), chủ doanh nghiệp (Billing), break-glass | 0–5 USD | Đã tạo (chưa ghi ID) |
| aa-log-archive | aws+log-archive@adventure.asia | Bucket org CloudTrail, log ALB/S3/Config, Data Exports | Security | us-west-1 | Tech lead ReadOnly, auditor; CI apply | 1–8 USD | Tạo ở phase 1 |
| aa-security | aws+security@adventure.asia | Delegated admin của Access Analyzer (miễn phí), GuardDuty/Security Hub/Config (trả phí, chờ duyệt) | Security | us-west-1 | Tech lead, auditor | 0 USD khi chỉ dùng dịch vụ miễn phí | Tạo ở phase 1 |
| aa-backup | aws+backup@adventure.asia | Vault nhận bản copy backup prod (vault lock compliance) | Security | us-west-1 | Chỉ break-glass + CI apply | 1–5 USD (DB khoảng 3.4 GB) | Tạo ở phase 6 |
| aa-shared-services | aws+shared@adventure.asia | ECR trung tâm, artifact Lambda, DNS dùng chung | Infrastructure | us-west-1 (+ us-east-1 cho ACM) | Tech lead Admin, engineer ReadOnly, CI role | 5–20 USD | Tạo ở phase 1 |
| aa-shared-ai | (email root hiện có; kiểm, đổi sang aws+ai@adventure.asia) | Bedrock (chat model). Invoker role riêng cho dev/staging/prod | Infrastructure, hoặc đứng ngoài org (mục 5) | us-west-1 + region của global/CRIS inference | Tech lead, engineer (PlatformEngineer) | Tính theo lượng gọi (shared.llm_call_log) | Đã có: 786888028788 (đang Error 002) |
| aa-dev | (email root hiện có, CHƯA RÕ ai giữ; nếu TrueIDC tạo account thì có thể do họ giữ) | Môi trường dev hiện tại: 4 app, RDS, ECS, API GW, Cognito | Workloads/NonProd | us-west-1 | Engineer DevAdmin, agent (role riêng) | 140–200 USD (thực tế: 08/2026 140.22; 09/2026 134.96; 1–28/10 185.77) | Đã có: 005097885195 |
| aa-staging | aws+staging@adventure.asia | Release candidate, diễn tập migration, UAT, load test | Workloads/NonProd | us-west-1 | Engineer PlatformEngineer, tech lead | 15–30 USD khi đã huỷ / 90–130 USD dừng tạm / 150–200 USD bật liên tục | Tạo trống ở phase 1, dựng ở phase 5 |
| aa-prod | aws+prod@adventure.asia | Khách hàng thật | Workloads/Prod | us-west-1 (+ us-west-2 bản sao backup, us-east-1 ACM) | ReadOnly mặc định; ProdOperator/Admin 1h; không có agent | 410–580 USD list; 290–410 USD khi dùng đòn bẩy | Tạo ở phase 6 khi có ngày go-live |

_Email dùng plus-addressing trên một hộp thư nhóm (aws@) mà cả tech lead và chủ doanh nghiệp đều đọc được; cần kiểm mail server có hỗ trợ không. Mỗi email chỉ dùng cho một account, và email của account đã đóng không dùng lại được. Account trống gần như không tốn tiền, trừ khi bật dịch vụ tự động (Config/GuardDuty) cho toàn org._

### Account có sẵn: vai trò mới

| Account | ID | Vai trò mới | Lý do | Lưu ý |
|---|---|---|---|---|
| Infra (acc2) | 005097885195 | aa-dev (Workloads/NonProd) | Đang chứa toàn bộ Dev. Giữ nguyên ID nên không phải dời dữ liệu, DNS hay Cognito | Giữ bucket state aa-cis-tfstate-005097885195. Gỡ trail riêng khi org trail chạy (bucket cũ giữ tới hết Object Lock 365 ngày). Zone lumiguides.it.com ở lại đây. Kiểm Cohere Embed v4 trước/sau khi đổi payer |
| AI (acc3) | 786888028788 | aa-shared-ai | Một chỗ quản quota, quyền model và chi phí LLM cho cả 3 môi trường. Account mới tạo cũng có thể dính Error 002, nên giữ account cũ khi nó chạy lại được | Vào org hay không tuỳ mục 5. Khi prod gửi PII qua LLM, cân nhắc tách aa-prod-ai (mục 14) |
| Cá nhân (acc1) | 867490540162 | Không dùng | Đã gỡ khỏi hệ sinh thái (AA-998) | Ngoài phạm vi |
| Quanskill dev/stg/prod | 710590321660 / 593110023608 / 007050358335 | Không dùng | Dự án cũ, ap-southeast-1 | Gỡ profile aa-dev/aa-stg/aa-prod để không trùng tên |

### Lịch tạo account mới

| Account | Phase | Điều kiện tạo | Cách tạo |
|---|---|---|---|
| aa-log-archive | 1 | Org đã bật all features | Terraform aws_organizations_account trong stack 10-organization |
| aa-security | 1 | Như trên | Như trên |
| aa-shared-services | 1 | Như trên | Như trên |
| aa-staging | 1 (tạo trống) → 5 (dựng) | Dùng sớm làm account thử SCP | Như trên |
| aa-prod | 6 | Đã chốt ngày go-live, đã duyệt chi phí; xin tăng quota ngay khi tạo | Như trên |
| aa-backup | 6 | Trước khi bật backup policy cho prod | Như trên |
| Sandbox (vd aa-sandbox-<tên>) | Khi cần | Có thử nghiệm cụ thể, có budget, có ngày đóng | Như trên; xong thì chuyển vào Suspended |

_Khi đã bật centralized root access, account do Organizations tạo không có root credential, và có sẵn OrganizationAccountAccessRole. Đóng account có giới hạn số lượng theo tỷ lệ số member trong 30 ngày, nên phải lên kế hoạch. Account sau khi đóng có 90 ngày post-closure._

## 3. Đưa account có sẵn vào org của công ty

Phải chốt mô hình thanh toán (mục 5) trước, vì nó quyết định account AI có vào org hay không. Việc sửa Error 002 trên account AI làm ngay khi nó còn đứng riêng, độc lập với org. Account infra làm sau, vì phải rời org của TrueIDC (tuỳ hợp đồng, nên làm sát ngày 1 của tháng). Workload đang chạy không dừng khi đổi org. Phần dễ hỏng là billing, credit, quyền model Bedrock và email root.

### Điều kiện trước khi mời

| Điều kiện | Account AI 786888028788 | Account infra 005097885195 | Cách kiểm | Người làm |
|---|---|---|---|---|
| Email root thuộc công ty, nhận được mail | Kiểm; đổi sang aws+ai@ nếu là email cá nhân | CHƯA RÕ, NGHIÊM TRỌNG: nếu TrueIDC tạo account thì email root có thể do họ giữ. Phải đổi sang email công ty TRƯỚC khi rời org | Account settings (root) hoặc hỏi TrueIDC | Tech lead + chủ doanh nghiệp |
| Root MFA (FIDO2) | Bật | Bật (nếu đã bật centralized root access thì phải khôi phục mật khẩu root qua email) | IAM → Security credentials | Tech lead |
| Phương thức thanh toán độc lập | Gắn thẻ (cần cho Error 002 và Marketplace) | Thẻ công ty cho khoảng đứng riêng sau khi rời org TrueIDC | Billing → Payment preferences | Chủ doanh nghiệp |
| Nhà bán đồng ý | Không cần | Cần TrueIDC đồng ý gỡ khỏi org (hoặc chuyển sang Billing Transfer); hỏi thời hạn báo trước | Email chính thức (mục 5) | Chủ doanh nghiệp |
| Xuất dữ liệu chi phí | Cost Explorer, hoá đơn, trạng thái credit | Cost Explorer 13 tháng, hoá đơn VAT, cấu hình budget | Tải CSV, lưu vào thư mục audit | Tech lead |
| Liệt kê Marketplace / model đang dùng | Model Anthropic, OpenAI | Cohere Embed v4 | Console Marketplace; shared.llm_role_config | Tech lead |
| Liệt kê role tin account ngoài, RAM share | — | Role tin payer 033086823579 (chưa kiểm); RAM share từ org TrueIDC. Terraform không có PrincipalOrgID / o-cnvpmom3os (đã grep) | iam list-roles + trust policy; ram get-resource-shares | Tech lead |
| Không có wave LLM hay deploy đang chạy | Có | Có | Bảng job rảnh (shared.job, booking.job, crm.job) | Tech lead |

### Các bước (làm tuần tự)

| # | Bước | Account | Người làm | Rủi ro | Rollback |
|---|---|---|---|---|---|
| 0 | Chốt mô hình thanh toán (mục 5) sau khi TrueIDC trả lời | — | Chủ doanh nghiệp | Chọn B1 thì account AI phải đứng ngoài org | — |
| 1 | Sửa Error 002 khi account AI còn đứng riêng: gắn thẻ, nộp lại form FTU của Anthropic, giữ case Support (Basic hỗ trợ được case account/billing). Hỏi thêm: Lift credit có trả cho model bán qua Marketplace không, và có còn khi vào org không | AI | Tech lead | AWS chưa gỡ khoá; credit 249.94 USD hết hạn 31/12 | Chạy LLM qua API trực tiếp (S257 phương án D) |
| 2 | Kiểm bằng lệnh gọi model thật, KHÔNG tin GetFoundationModelAvailability. Mỗi route một lệnh gọi nhỏ qua LLMClient (ghi shared.llm_call_log, stage adhoc) | AI | Engineer | Tốn vài cent | — |
| 3 | aa-management bật Organizations (all features), trusted access, OU (phase 1) | — | Tech lead | Thấp | Chưa có member nên xoá được |
| 4 | (Chỉ khi mục 5 cho phép AI vào org) Gửi lời mời invite-account-to-organization | AI | Tech lead | Thấp | Huỷ handshake |
| 5 | Chấp nhận lời mời trong account AI; account vào OU Transitional (không có SCP chặn rời org) | AI | Tech lead | Billing đổi sang payer mới ngay; quyền Claude phụ thuộc payer | LeaveOrganization (cần phương thức thanh toán độc lập) |
| 6 | Tạo OrganizationAccountAccessRole tin aa-management (account được mời không tự có role này); gán Identity Center | AI | Tech lead | Thấp | Xoá role |
| 7 | Gọi thử lại từng route. Lỗi thì nộp lại FTU / Marketplace subscribe; có thể bị AccessDenied khoảng 15 phút | AI | Engineer | Bedrock gãy lại sau khi đổi payer | Rời org (OU Transitional) + API trực tiếp |
| 8 | Sau 1 tuần ổn: chuyển sang OU Infrastructure | AI | Tech lead | SCP region làm hỏng global inference | Chuyển lại Transitional |
| 9 | Gửi TrueIDC bộ câu hỏi ở mục 5 | Infra | Chủ doanh nghiệp | Điều khoản hợp đồng | — |
| 10 | Đổi email root sang email công ty; đặt thẻ công ty và thông tin thuế (tên công ty, địa chỉ VN, mã số thuế) | Infra | Chủ doanh nghiệp + TrueIDC | Mất quyền vào root nếu email không thuộc công ty | — |
| 11 | Xuất Cost Explorer, hoá đơn, budget; chụp trust policy các role tin payer; danh sách RAM share | Infra | Tech lead | Mất lịch sử nếu quên | — |
| 12 | Gọi thử Cohere Embed v4 (chụp kết quả làm mốc so sánh) | Infra | Engineer | — | — |
| 13 | TrueIDC gỡ account khỏi org o-cnvpmom3os (hoặc account tự LeaveOrganization nếu SCP cho phép), sát ngày 1 của tháng | Infra | TrueIDC + tech lead | Vài ngày bị tính tiền thẳng qua thẻ; SCP của TrueIDC hết hiệu lực | Xin TrueIDC mời lại |
| 14 | Chấp nhận lời mời của aa-management NGAY trong ngày; vào OU Transitional | Infra | Tech lead | Thấp | Như bước 5 |
| 15 | Xoá role tin 033086823579; tạo OrganizationAccountAccessRole tin aa-management (Terraform, apply local có MFA) | Infra | Tech lead | Nhà bán mất quyền vào, đúng ý định | Tạo lại role cũ nếu hợp đồng yêu cầu |
| 16 | Smoke: /health và /health/ready của CIS/Booking/CRM, ECS steady, DB Migrate mode=check, CI deploy dev, terraform plan 0 thay đổi, budget còn chạy, Cohere Embed gọi được | Infra | Engineer | Embedding bị khoá (Error 002) | Chuyển embedding sang aa-shared-ai hoặc API trực tiếp; case Support |
| 17 | Sau 1–2 tuần: chuyển sang OU Workloads/NonProd, đổi tên hiển thị thành aa-dev | Infra | Tech lead | SCP chặn một thao tác Dev đang dùng | Chuyển lại Transitional |
| 18 | (Nếu chọn Billing Transfer) Bên bill-transfer gửi lời mời transfer tới aa-management; chấp nhận theo hạn AWS quy định (kiểm lại mốc thời gian trong tài liệu) | Cả org | Bên bill-transfer + chủ doanh nghiệp | Mất CUR/anomaly ở phía công ty; chỉ còn số pro-forma | Một trong hai bên rút lời mời |

_Nguồn: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing.html ; https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html ; docs/audits/2026-10-29-S257-llm-access-options/angle2-alternatives.md (Error 002)_

### Cái gì bị ảnh hưởng khi đổi org

| Hạng mục | Ảnh hưởng | Chuẩn bị / xử lý |
|---|---|---|
| Lịch sử Cost Explorer | Management mới chỉ thấy số liệu từ ngày account gia nhập. Dữ liệu trong org TrueIDC không đi theo | Xuất CSV 13 tháng và hoá đơn trước khi rời |
| Cost Anomaly Detection | Hiện có monitor dịch vụ trong acc2 và acc3. Monitor theo tag App chỉ tạo được ở management. Theo Billing Transfer, phía bill-source có thể mất anomaly (cần kiểm) | Mô hình A: tạo monitor theo tag ở aa-management. Mô hình B: budget theo account + hỏi bên bill-transfer |
| Budget trong account | Vẫn chạy | Thêm budget cấp org ở aa-management |
| Bedrock Anthropic (AI) và Cohere Embed v4 (infra) | Quyền Claude phụ thuộc payer có giấy Anthropic. Có thể phải nộp lại form FTU hoặc subscribe lại. Rời TrueIDC có thể làm AWS khoá AI trên acc2 (S257) | Làm ngoài giờ wave; gọi thử trước/sau; giữ đường API trực tiếp làm fallback |
| Lift credit (AI, 249.94 USD, hết hạn 31/12) | Credit gắn với account đã redeem; trong org thì áp theo cài đặt credit sharing. Theo Billing Transfer, bên bill-source không thấy credit. Có thể không trả được cho model Marketplace | Hỏi AWS Support (bước 1) |
| Marketplace subscription | Vẫn còn, nhưng phí chuyển sang payer mới | Liệt kê trước khi đổi |
| Service quota (Bedrock TPM, Fargate vCPU, SES) | Gắn với account, không đổi | Kiểm lại sau khi chuyển |
| SES production access | Gắn với account, không đổi | — |
| SCP của TrueIDC | Hết hiệu lực khi rời | SCP của công ty thay vào, gắn dần từ OU Transitional |
| Hoá đơn VAT Việt Nam | AWS trực tiếp không xuất hoá đơn VAT/e-invoice (S257 angle2 #1) | Kế toán xác nhận hoá đơn nước ngoài + kê khai FCT; hoặc giữ Billing Transfer |
| Trang chi phí theo app của CIS | Đang đọc Cost Explorer qua role AA3-CostExplorer-Reader (acc3) | Giữ reader theo từng account hoặc dùng Data Exports; không cho workload vào management |
| Workload đang chạy, DNS, chứng chỉ | Không bị ảnh hưởng (ID account giữ nguyên) | — |
| Reserved Instance / Savings Plan | Không có (0) | — |
| Terraform | Không đổi | Chỉ thêm provider/role mới |

## 4. Quản trị: danh tính, policy, ngân sách, kiểm toán

Người dùng vào AWS qua Identity Center theo ma trận nhóm × account. Break-glass nằm ngoài Identity Center. CI và agent dùng IAM role OIDC hoặc role riêng, không dùng user. Guardrail gồm vài SCP gộp, RCP có miễn trừ, tag/backup policy. Dịch vụ bảo mật trả phí chờ duyệt.

### Nhóm Identity Center

| Nhóm | Thành viên | Mục đích |
|---|---|---|
| aa-admins | Tech lead (1–2 người) | Quản trị org, hạ tầng, sự cố prod |
| aa-engineers | Kỹ sư | Làm dev/staging; prod chỉ đọc |
| aa-business-owner | Chủ doanh nghiệp | Xem chi phí, hoá đơn, đọc tổng quan |
| aa-auditors | Kiểm toán viên bên ngoài | Gán có thời hạn, chỉ SecurityAudit |
| aa-breakglass-sso | 1 user khẩn cấp (FIDO2 riêng) | Khi nhóm/IdP bị cấu hình sai. KHÔNG thay được break-glass ngoài Identity Center |
| (không phải user) CI, agent | GitHub Actions OIDC; agent lập trình | IAM role trong từng account (bảng ma trận) |

### Permission set

| Tên (không đổi tên được sau khi tạo) | Chính sách | Session | Dùng ở |
|---|---|---|---|
| AA-Admin | AdministratorAccess | 1h | management, security, shared-services, shared-ai, staging, prod (sự cố) |
| AA-DevAdmin | AdministratorAccess | 8h | aa-dev, sandbox |
| AA-PlatformEngineer | PowerUserAccess + IAM giới hạn (tạo role phải gắn boundary aa-workload-boundary; iam:PassRole chỉ cho role aa-*) | 4h | dev, staging, shared-ai |
| AA-ProdOperator | Tự viết: ECS update-service/describe, logs, CloudWatch, RDS describe/reboot. Không GetSecretValue, không đọc S3 dữ liệu, không ECS exec/Session Manager (ADR 0012 d4.4) | 1h | prod |
| AA-ReadOnly | ViewOnlyAccess + đọc cấu hình; chặn GetSecretValue và s3:GetObject trên bucket dữ liệu | 8h | Mọi account |
| AA-Billing | Billing + AWSBillingReadOnlyAccess + Cost Explorer | 4h | management |
| AA-SecurityAudit | SecurityAudit + ViewOnlyAccess | 4h | Mọi account |
| AA-BreakGlass | AdministratorAccess | 1h | Mọi account (chỉ nhóm aa-breakglass-sso) |

_Tên permission set không đổi được sau khi tạo, nên phải đặt đúng ngay lần đầu. Nguồn: https://docs.aws.amazon.com/singlesignon/latest/userguide/permissionsetsconcept.html_

### Ma trận quyền (nhóm × account)

| Nhóm / tác nhân | aa-management | aa-log-archive | aa-security | aa-backup | aa-shared-services | aa-shared-ai | aa-dev | aa-staging | aa-prod |
|---|---|---|---|---|---|---|---|---|---|
| aa-admins | AA-Admin | AA-ReadOnly | AA-Admin | AA-ReadOnly | AA-Admin | AA-Admin | AA-DevAdmin | AA-Admin + AA-PlatformEngineer | AA-ReadOnly + AA-ProdOperator + AA-Admin (1h, ghi lý do) |
| aa-engineers | — | — | — | — | AA-ReadOnly | AA-PlatformEngineer | AA-DevAdmin | AA-PlatformEngineer | AA-ReadOnly |
| aa-business-owner | AA-Billing + AA-ReadOnly | — | — | — | — | — | AA-ReadOnly | AA-ReadOnly | AA-ReadOnly |
| aa-auditors | AA-SecurityAudit | AA-SecurityAudit | AA-SecurityAudit | AA-SecurityAudit | AA-SecurityAudit | AA-SecurityAudit | AA-SecurityAudit | AA-SecurityAudit | AA-SecurityAudit |
| aa-breakglass-sso | AA-BreakGlass | AA-BreakGlass | AA-BreakGlass | AA-BreakGlass | AA-BreakGlass | AA-BreakGlass | AA-BreakGlass | AA-BreakGlass | AA-BreakGlass |
| CI Infra (OIDC) | plan/apply (environment org, reviewer) | plan/apply | plan/apply | plan/apply | plan/apply | plan/apply | plan/apply (environment dev) | plan/apply (environment staging) | plan/apply (environment prod, có reviewer; plan cũng cần duyệt) |
| CI app (OIDC) | — | — | — | — | ECR push (chỉ từ main) | — | app-deploy (dev) | app-deploy (staging) | app-deploy (prod, có reviewer) |
| Agent lập trình | — | — | — | — | ECR read | invoke (role dev) | aa-agent-dev (least privilege) | — (không) | — (không bao giờ) |

### MFA và break-glass

| Hạng mục | Thiết lập | Kiểm |
|---|---|---|
| MFA của Identity Center | Bắt buộc ở mọi lần đăng nhập; admin dùng passkey/FIDO2 | Đăng nhập không MFA phải bị chặn |
| Root aa-management | 2 khoá FIDO2 (tech lead giữ 1, chủ doanh nghiệp giữ 1 trong két), mật khẩu trong vault công ty, email nhóm | Diễn tập 6 tháng/lần |
| IAM user break-glass ở aa-management | FIDO2, không access key; assume OrganizationAccountAccessRole vào member; EventBridge cảnh báo khi đăng nhập | Diễn tập 6 tháng/lần; dùng được khi Identity Center hỏng |
| Root của account member | Xoá credential bằng centralized root access; tác vụ root chạy qua sts:AssumeRoot từ management | iam list-organizations-features; kiểm từng account |
| Khi Identity Center hỏng | IAM user break-glass hoặc root aa-management → OrganizationAccountAccessRole | Ghi vào runbook break-glass |
| Alternate contacts (billing/operations/security) | Hộp thư theo vai trò, đặt từ management (trusted access Account Management) | Xem trong Account settings |

_Nguồn: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html ; https://docs.aws.amazon.com/singlesignon/latest/userguide/emergency-access.html_

### SCP (gộp thành tài liệu để giữ ≤5 SCP mỗi đích)

| Tài liệu SCP | Nội dung | Gắn vào | Ngoại lệ | Phase |
|---|---|---|---|---|
| FullAWSAccess (AWS managed) | Cho phép nền; bắt buộc ở mọi tầng | Root + mọi OU | — | 1 |
| aa-scp-root | DenyMemberRoot: chặn mọi hành động khi principal là root của member | Root | Thử với tác vụ sts:AssumeRoot ở Policy-Staging trước | 1 |
| aa-scp-baseline | DenyLeaveOrg + CloseAccount; ProtectSecurityBaseline (không tắt/xoá CloudTrail, Config, GuardDuty, Access Analyzer, S3 account PAB); ProtectOrgRoles (OrganizationAccountAccessRole, AWSReservedSSO_*, aa-ci-*); DenyIAMUserKeys (CreateUser/CreateAccessKey) | Security, Infrastructure, Workloads, Sandbox (KHÔNG gắn Transitional/Suspended) | Role aa-ci-infra-apply của stack baseline; IAM user path /smtp/ cho SES SMTP; aa-dev được miễn DenyIAMUserKeys (theo aws:PrincipalAccount) cho tới khi gỡ IAM user cũ | 1 (DenyLeave) → 3 (đủ) |
| aa-scp-region | Chặn region khác us-west-1, us-east-1 (ACM cho CloudFront/Cognito), us-west-2 (bản sao backup); NotAction cho dịch vụ global (iam, sts, organizations, cloudfront, route53, budgets, ce, support, sso...) | Security, Workloads, Sandbox | — | 3 |
| aa-scp-region-ai | Như aa-scp-region, thêm us-east-2 và 'unspecified' cho bedrock:* (global / cross-Region inference) | Infrastructure | — | 2–3 |
| aa-scp-workloads | RequireEncryption (RDS/EBS/S3) + IMDSv2 | Workloads | — | 5 |
| aa-scp-nonprod-cost | Chặn instance lớn hơn xlarge, dịch vụ không dùng (SageMaker, Redshift...), mua RI/SP | NonProd, Sandbox | — | 5 |
| aa-scp-prod | ProtectProdData: chặn chia sẻ snapshot RDS ra ngoài org, S3 ACL public, xoá backup vault/recovery point | Prod | — | 6 |
| aa-scp-denyall | Chặn mọi thứ | Suspended | — | 1 |

_Danh sách NotAction và cách ghi 'unspecified' cho Bedrock phải đối chiếu với https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples_general.html và trang cross-Region inference của Bedrock trước khi viết. SCP không áp lên management và service-linked role. Mọi SCP thử ở OU Policy-Staging trước._

### RCP (resource control policy)

| Tên | Tác dụng | Gắn vào | Ngoại lệ bắt buộc | Phase |
|---|---|---|---|---|
| DataPerimeter-S3-KMS-Secrets-STS | Chặn principal ngoài org (aws:PrincipalOrgID) truy cập S3, KMS, Secrets Manager, STS | Workloads/Prod, sau đó NonProd | aws:PrincipalIsAWSService (CloudFront OAC, log delivery); sts:AssumeRoleWithWebIdentity (GitHub OIDC, Cognito identity pool); account AI nếu nó đứng ngoài org (bucket bronze cho Bedrock batch). URL presign do principal trong org ký vẫn chạy | 7 |

_RCP không áp lên tài nguyên của management và service-linked role. Vercel gọi API Gateway qua HTTPS nên không bị ảnh hưởng. Nguồn: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html_

### Tag policy và tag bắt buộc

| Tag | Giá trị cho phép | Cách bắt có tag | Cost allocation tag |
|---|---|---|---|
| Project | aa-ecosys | Terraform default_tags + lint CI | Có |
| Environment | dev, staging, prod, shared | default_tags (biến có validation) + checkov | Có |
| App | cis, booking, tripplanner, crm, shared, ai, platform | Biến của module app | Có |
| Owner | Hộp thư theo vai trò (vd platform@) | Biến | Không |
| CostCenter | engineering, ... | Biến | Có |
| ManagedBy | terraform, manual | default_tags | Không |
| Stack | Tên stack Terraform (vd 30-data) | default_tags | Không |
| DataClass | public, internal, confidential, pii | Biến của module data (RDS, S3, Secrets) | Không |

_Tag policy chỉ chuẩn hoá giá trị: enforced_for chặn giá trị sai chứ không bắt phải có tag. Muốn bắt có tag ở mức API thì thêm SCP với aws:RequestTag cho vài loại resource. Cost allocation tag kích hoạt ở payer; nếu dùng Billing Transfer thì phải hỏi còn kích hoạt được không._

### Backup policy (Organizations) và AI opt-out

| Phạm vi | Tài nguyên | Lịch | Giữ | Bản sao | Vault lock | Phase |
|---|---|---|---|---|---|---|
| prod | RDS (mã hoá bằng CMK), S3 dữ liệu quan trọng | Hằng ngày + hằng tháng | 35 ngày / 12 tháng | us-west-2 (region) + aa-backup (account) | Compliance mode ở aa-backup sau 30 ngày thử | 6 |
| staging | RDS | Hằng tuần | 7 ngày | Không | Không | 5 |
| dev | RDS automated backup 7 ngày (như hiện tại) | — | — | Không | Không | — |
| Root | AI services opt-out policy | — | — | — | — | 1 |

_Muốn copy chéo account thì phải bật trusted access của AWS Backup và cross-account management ở management. Snapshot RDS mã hoá bằng AWS managed key không copy chéo account được, nên prod phải dùng CMK và key policy chia cho aa-backup._

### Budget

| Phạm vi | Ngưỡng/tháng (đề xuất) | Cảnh báo | Người nhận |
|---|---|---|---|
| Cả org (aa-management) | Dev hiện tại: 300 USD → khi go-live: 1.000 USD | 50/80/100% thực tế + 100% dự báo | Chủ doanh nghiệp + tech lead |
| aa-management | 10 USD | 100% | Tech lead |
| aa-log-archive | 15 USD | 80/100% | Tech lead |
| aa-security | 15 USD (150 nếu bật dịch vụ trả phí) | 80/100% | Tech lead |
| aa-backup | 10 USD | 80/100% | Tech lead |
| aa-shared-services | 30 USD | 80/100% | Tech lead |
| aa-shared-ai | Theo trần LLM được duyệt (vd 300 USD) | 50/80/100% + theo ngày | Tech lead + chủ doanh nghiệp |
| aa-dev | 250 USD | 80/100% + dự báo | Tech lead |
| aa-staging | 150 USD | 80/100% | Tech lead |
| aa-prod | 650 USD | 80/100% + dự báo | Tech lead + chủ doanh nghiệp |

_Budget thường miễn phí; budget có action thì 2 cái đầu miễn phí, sau đó 0,10 USD/ngày mỗi cái. Nguồn: https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/_

### Delegated admin và dịch vụ bảo mật

| Dịch vụ | Account admin | Trả phí? | Ước tính/tháng | Trạng thái |
|---|---|---|---|---|
| IAM Access Analyzer (external access) | aa-security | Miễn phí | 0 | Bật ở phase 3 |
| IAM Access Analyzer (unused access) | aa-security | Có (khoảng 0.20 USD/role/tháng) | 5–15 USD | Chờ duyệt |
| GuardDuty | aa-security | Có | 20–60 USD cả org (5–15/account workload) | Chờ duyệt (tạm hoãn vì chi phí, var.guardduty_enabled=false); đề xuất bật cho prod lúc go-live |
| Security Hub CSPM | aa-security | Có (0.0010 USD/check) + BẮT BUỘC có Config | 20–50 USD + chi phí Config | Chờ duyệt |
| AWS Config (+ aggregator) | aa-security | Có (liên tục 0.003 USD/CI; định kỳ 0.012 USD/CI; 0.001 USD/rule eval) | 10–30 USD nếu chỉ prod và ghi định kỳ | Chờ duyệt |
| CloudTrail org trail | aa-management tạo, bucket ở aa-log-archive | Bản management event đầu tiên miễn phí; bản thứ hai 2 USD/100k event | Chỉ trả S3 + KMS: 1–3 USD | Phase 3 |
| AWS Backup (cross-account, cross-region) | aa-backup | Trả theo storage + copy | 1–5 USD | Phase 6 |
| Identity Center, Organizations | management | Miễn phí | 0 | Phase 1 |
| Prowler (OSS, chạy trong CI) | — | Miễn phí | 0 | Phase 6 thay Security Hub nếu chưa duyệt |

_Số tiền là ước tính theo giá list, chưa phải báo giá. Nguồn: https://aws.amazon.com/cloudtrail/pricing/ ; https://aws.amazon.com/config/pricing/ ; https://aws.amazon.com/security-hub/pricing/_

### Org CloudTrail

| Thuộc tính | Giá trị |
|---|---|
| Trail | aa-org-trail, multi-region, management event, bật log file validation |
| Đích | s3://aa-log-archive-cloudtrail-<log-archive-id> (KMS CMK ở aa-log-archive; Object Lock: compliance cho prod, governance cho nonprod) |
| Data event / Lake | Không bật (tốn phí) |
| Trail cũ aa-cis-dev-trail | Xoá trail sau khi org trail chạy 7 ngày (tránh trả tiền bản thứ hai). Bucket cũ có Object Lock GOVERNANCE 365 ngày: giữ tới hết hạn, lifecycle rồi xoá |
| Giữ log | 90 ngày ở S3 Standard → Glacier Instant Retrieval → xoá sau 1 năm (prod: 3 năm) |

### Rà soát quyền

| Việc | Tần suất | Người làm | Bằng chứng |
|---|---|---|---|
| Rà nhóm × permission set × account | Hằng quý | Tech lead; chủ doanh nghiệp ký | Bảng xuất từ Identity Center lưu trong docs/ops |
| Rà các lần dùng AA-Admin/AA-ProdOperator ở prod và đăng nhập break-glass | Hằng tháng | Tech lead | Truy vấn CloudTrail |
| Thu hồi quyền khi người nghỉ hoặc đổi vai trò | Ngay trong ngày | Tech lead | Ticket + log |
| Rà trust policy OIDC/CI role | Hằng quý | Tech lead | Báo cáo iam-roles.md sinh từ state |
| Diễn tập break-glass | 6 tháng | Tech lead + chủ doanh nghiệp | Biên bản diễn tập |

## 5. Mô hình thanh toán

Trong mọi mô hình, công ty đều tự giữ aa-management và org của mình; chỉ đường hoá đơn thay đổi. Một org chỉ có MỘT bên bill-transfer. Claude trên Bedrock chỉ chạy khi payer có giấy bán lại của Anthropic, mà TrueIDC chưa thấy có. Vì vậy chuyển cả org sang Billing Transfer cho TrueIDC có thể chặn Claude trên mọi account. Khuyến nghị: hỏi TrueIDC cả hai điều (Billing Transfer và giấy Anthropic), rồi chọn theo bảng kịch bản. Không ép ký hợp đồng mới.

### So sánh mô hình

| Tiêu chí | A. AWS trực tiếp (thẻ trên aa-management) | B1. Billing Transfer cho TrueIDC | B2. Billing Transfer cho reseller có giấy Anthropic | C. Reseller consolidated (như hôm nay) | D. Hybrid tạm thời |
|---|---|---|---|---|---|
| Ai giữ management account | Công ty | Công ty | Công ty | TrueIDC | Công ty (account mới); TrueIDC (infra) |
| SCP / quản trị | Công ty | Công ty | Công ty | TrueIDC | Tách đôi |
| Hoá đơn / VAT VN | Hoá đơn AWS bằng USD; AWS không xuất hoá đơn VAT/e-invoice | TrueIDC xuất hoá đơn như hiện tại | Reseller xuất (chưa kiểm VND/VAT) | TrueIDC | 2 nguồn hoá đơn |
| Claude trên Bedrock | Được (nếu đã gỡ Error 002) | Có thể bị chặn trên MỌI account (chưa kiểm) → AI đứng ngoài org hoặc dùng API trực tiếp | Được (theo giấy của reseller; chưa kiểm VN) | Bị chặn trên account infra | AI theo account |
| Credit (Lift...) | Thấy và chia được | Bên bill-source không thấy credit | Như B1 | TrueIDC xử lý | Tuỳ account |
| Cost Explorer / anomaly | Đầy đủ | Chỉ số pro-forma, có thể không có anomaly/CUR (cần kiểm) | Như B1 | Hạn chế (member) | Tách đôi |
| Rời bỏ | Tự quyết | Một trong hai bên rút lời mời (kiểm mốc hiệu lực) | Như B1 | Phụ thuộc TrueIDC | — |
| Hợp đồng | Không cần | Giữ hợp đồng đã ký | HỢP ĐỒNG MỚI (chỉ là đường lùi) | Hiện tại | Giữ |
| Chi phí thêm | 0 | Có thể có phí Billing Conductor (hỏi) | Như B1 | Phí hiện tại | 0 |

_Nguồn: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing.html ; docs/audits/2026-10-29-S257-llm-access-options/llm-vendor-recommendation.vi.md (giấy Anthropic, SPP list 24/09/2026); angle2-alternatives.md (AWS không xuất VAT)._

### Cấu trúc khuyến nghị theo từng tình huống

| Tình huống (TrueIDC trả lời) | Mô hình | Account infra và staging/prod | Account AI |
|---|---|---|---|
| Hỗ trợ Billing Transfer VÀ có giấy Anthropic | B1 đầy đủ | Vào org công ty; toàn bộ hoá đơn qua TrueIDC | Vào org (OU Infrastructure) |
| Hỗ trợ Billing Transfer, KHÔNG có giấy Anthropic | B1 + AI đứng ngoài | Vào org công ty; hoá đơn qua TrueIDC | Đứng ngoài org, trả bằng thẻ; quản qua role cross-account. Song song API trực tiếp |
| Không hỗ trợ Billing Transfer nhưng cho rời org; kế toán chấp nhận hoá đơn USD | A | Vào org công ty, trả bằng thẻ | Vào org |
| Chưa cho rời (ràng buộc hợp đồng) | D | Ở lại org TrueIDC tới hết điều khoản; staging/prod dựng ở org công ty, trả bằng thẻ | Vào org công ty |
| Kế toán bắt buộc hoá đơn VAT và TrueIDC không có giấy Anthropic | B2 (đường lùi) | Cần quyết định của chủ doanh nghiệp | — |

### Câu hỏi gửi TrueIDC (chủ doanh nghiệp gửi)

| # | Câu hỏi | Vì sao cần |
|---|---|---|
| 1 | Bên bạn có hỗ trợ AWS Billing Transfer (bên bạn là bill-transfer, công ty là bill-source) không? Có dùng Billing Conductor không, ai trả phí? | Giữ hợp đồng và hoá đơn VAT, công ty vẫn giữ quyền quản trị |
| 2 | Bên bạn có giấy bán lại Anthropic (Claude trên Bedrock) cho khách Việt Nam không? Theo Billing Transfer thì account của công ty có gọi được Claude và model OpenAI không? | Quyết định account AI vào org hay đứng ngoài |
| 3 | Điều kiện để account 005097885195 rời org của bên bạn: báo trước bao lâu, có phí không, làm vào ngày nào? | Lập lịch phase 3 |
| 4 | Ai đang giữ email root và MFA root của account 005097885195? Account này do bên bạn tạo (vend) phải không? | Nếu email thuộc TrueIDC, công ty sẽ mất quyền root khi rời org |
| 5 | Org của bên bạn đang áp SCP / Private Marketplace nào lên account của công ty (Bedrock, Marketplace, LeaveOrganization)? | Nguyên nhân LLM bị chặn; có tự rời org được không |
| 6 | Trong account có role nào tin account của bên bạn (OrganizationAccountAccessRole...) hoặc RAM share nào không? | Dọn quyền truy cập của bên thứ ba |
| 7 | Bên bạn có cảnh báo chi phí bất thường thay cho Cost Anomaly Detection không? | Không mất cảnh báo chi phí |
| 8 | Có xuất được dữ liệu chi phí lịch sử (CUR) của account trước khi chuyển không? | Giữ lịch sử |

## 6. Môi trường dev / staging / prod

Ba môi trường dùng chung một bộ module Terraform, chỉ khác kích thước, dữ liệu và cổng duyệt. Một image (cùng digest) được đẩy dần dev → staging → prod. Frontend Vercel phải build lại cho từng môi trường, vì biến môi trường được nhúng lúc build. Staging mặc định 'huỷ khi rảnh' để tiết kiệm.

### So sánh môi trường

| Thuộc tính | dev | staging | prod |
|---|---|---|---|
| Account / OU | aa-dev (005097885195) / NonProd | aa-staging (mới) / NonProd | aa-prod (mới) / Prod |
| Mục đích | Phát triển, PR preview, chạy wave nội dung | Release candidate, diễn tập migration, UAT, load test | Khách hàng thật |
| Dữ liệu | Một phần nội dung + dữ liệu tổng hợp; không có PII thật | Nội dung copy qua job allow-list (không PII); khách hàng là dữ liệu tổng hợp | Dữ liệu thật; PII không rời prod (ADR 0012 d9) |
| Nơi lưu dữ liệu cá nhân | — | — | us-west-1 (Mỹ): cần hồ sơ đánh giá chuyển dữ liệu ra nước ngoài theo luật VN (chưa kiểm chi tiết, chủ doanh nghiệp quyết với tư vấn pháp lý) |
| RDS | db.t4g.small single-AZ (như hiện tại) | db.t4g.small single-AZ; huỷ hoặc dừng khi không dùng (RDS tự bật lại sau 7 ngày) | db.t4g.medium Multi-AZ, gp3 tự tăng, mã hoá CMK |
| ECS | 1 task/service | 1 task/service | ≥2 task cho service phục vụ người dùng; worker 1 |
| NAT | NAT instance t4g.nano | NAT instance t4g.nano | NAT gateway (1 lúc đầu, 2 khi cần) |
| HA | Không | Không | RDS Multi-AZ, ECS ≥2 AZ, ALB 2 AZ |
| Backup / DR | RDS automated 7 ngày | Automated 3–7 ngày + snapshot trước khi huỷ | PITR 14 ngày; AWS Backup hằng ngày, copy sang us-west-2 và aa-backup; RPO ≤15 phút (mất instance) / ≤24h (mất region); RTO ≤1h / ≤4h |
| Truy cập của người | Engineer: AA-DevAdmin | Engineer: AA-PlatformEngineer | AA-ReadOnly mặc định; AA-ProdOperator/AA-Admin 1h; không ECS exec |
| Agent | Có (role aa-agent-dev) | Không | Không bao giờ |
| Kích hoạt deploy | Tự động khi merge main | workflow_dispatch với SHA đã xanh ở dev | workflow_dispatch + environment prod có required reviewer (tech lead) + allow-list người kích hoạt |
| Migration DB | Expand tự áp (ADR 0017) | DB Migrate apply, environment=staging (tay) | DB Migrate prod (tay), không bao giờ tự áp |
| SES | Identity lumiguides.it.com | Sandbox (chỉ gửi tới địa chỉ đã verify) | Identity tên miền prod; xin production access mới |
| Quota cần xin trước | — | Fargate vCPU | Lambda concurrency (account mới có thể chỉ có 10), Fargate vCPU, SES, Bedrock (ở shared-ai) |
| Log CloudWatch | 14 ngày | 14 ngày | 90 ngày |
| Chi phí/tháng (ước tính) | 140–200 USD | 15–30 (đã huỷ) / 90–130 (dừng tạm) / 150–200 (bật liên tục) | 410–580 list / 290–410 khi dùng đòn bẩy |

_Mục tiêu prod lấy từ ADR 0012 quyết định 10, cộng thêm phần nền của một account riêng. Dev tháng 10 (Cost Explorer 1–28/10): ECS 47.7, ALB 34.2, RDS 26.8, CloudWatch 16.4, ElastiCache 14.5, WAF 10.1, VPC 10.1, Secrets 9.7 (51 secret) USD. ALB, WAF, secret và IPv4 không dừng khi đặt desired=0._

### Quy ước tên miền

| Dịch vụ | dev (giữ nguyên) | staging | prod |
|---|---|---|---|
| CIS API | api-cis.lumiguides.it.com | api-cis.stg.lumiguides.it.com | api-cis.<prod-domain> |
| Booking API | api-booking.lumiguides.it.com | api-booking.stg.lumiguides.it.com | api-booking.<prod-domain> |
| CIS admin (Vercel) | aa-cis.lumiguides.it.com | aa-cis.stg.lumiguides.it.com | aa-cis.<prod-domain> |
| Staff sign-in (Cognito) | staff-auth.lumiguides.it.com | staff-auth.stg.lumiguides.it.com (cần bản ghi A cho stg.lumiguides.it.com) | staff-auth.<prod-domain> (cần bản ghi A cho domain cha) |
| Partner / CRM | partner-dev..., partner-auth..., portal... | partner.stg..., partner-auth.stg..., portal.stg... | partner., partner-auth., portal.<prod-domain> |
| Ảnh CDN | img.lumiguides.it.com | img.stg.lumiguides.it.com | img.<prod-domain> |
| DB private | db.dev.internal | db.staging.internal | db.prod.internal |
| Zone Route 53 | lumiguides.it.com ở aa-dev (tên miền đăng ký ở Namecheap; không dời) | stg.lumiguides.it.com ở aa-staging; NS uỷ quyền đặt trong zone ở aa-dev (chấp nhận được với nonprod) | Sub-zone <prod-domain> ở aa-prod, uỷ quyền thẳng từ nơi đang quản DNS của tên miền công ty; KHÔNG đi qua aa-dev |

_<prod-domain> do chủ doanh nghiệp chọn (mục 14). Alias của CloudFront, custom domain của Cognito và API Gateway không dùng chung giữa account được, nên staging/prod dùng tên mới; không dời tên dev. ACM cho CloudFront/Cognito phải ở us-east-1 trong từng account. User pool không dời account được, nên người dùng phải đăng ký lại ở mỗi môi trường._

### Luồng promote

| Bước | Ở đâu | Hành động | Cổng |
|---|---|---|---|
| 1 | PR (repo app) | Test, build image (chưa push) | CI xanh |
| 2 | Merge main | Build MỘT lần, push ECR ở aa-shared-services, tag = git SHA (IMMUTABLE), ghi digest | — |
| 3 | dev | Deploy bằng digest; smoke /health, /health/ready | Tự động |
| 4 | staging | workflow_dispatch(SHA): tra digest, kiểm SHA đã xanh ở dev; chạy DB Migrate staging nếu có migration; deploy; E2E | Tech lead hoặc engineer kích hoạt |
| 5 | prod | Cùng digest (ECR registry replication sang aa-prod, prod pull từ registry của chính nó); migration expand-first; ECS circuit breaker tự rollback; smoke; revision của task definition là con trỏ release | Environment prod: required reviewer; bật 'prevent self-review' khi có từ 2 người |
| 6 | Vercel (Next.js) | Build lại từ đúng commit SHA với biến của từng môi trường (biến public nhúng lúc build) | Như bước 4–5 |
| 7 | Lambda (TripPlanner) | Zip đặt tên theo SHA trong bucket artifact ở aa-shared-services; copy sang account đích; promote cùng SHA | Như bước 4–5 |

### Staging phải giống prod ở đâu

| Hạng mục | Giống prod | Được khác |
|---|---|---|
| Module Terraform | Cùng version module (ref git tag) | tfvars: kích thước, số task |
| Topology | VPC, ALB, API GW + VPC link, Cognito 4 pool, WAF, private zone | Single-AZ, NAT instance |
| Postgres | Cùng major version, cùng parameter group, cùng role/grant | Instance class |
| IAM | Cùng role, boundary, SCP (thử SCP prod ở staging trước) | Ai được truy cập |
| Secret | Cùng tên <app>/<env>/..., cùng cấu trúc | Giá trị |
| Job runner | Cùng kind, cùng cấu hình | Lịch chạy (tắt cron nặng) |
| Backup | Có backup để diễn tập restore | Không copy sang region/account khác |
| Dữ liệu | Cùng schema, đủ khối lượng để load test | Không có PII thật |

### Vercel, Cognito, Route 53 theo môi trường

| Thành phần | dev | staging | prod |
|---|---|---|---|
| Vercel | Project hiện có (gói Hobby; production branch → API dev); preview cho từng PR | Project riêng '<app>-staging' trong team Pro (Pro tính theo seat, không theo project); bật Deployment Protection | Project prod riêng cho mỗi app (ADR 0012 d7), team Pro |
| Cognito | Pool workforce/external/partner/m2m hiện có | 4 pool riêng, domain *.stg | 4 pool riêng, domain prod; ID pool/client lấy từ config, không ghi cứng trong code app |
| Route 53 | lumiguides.it.com | stg.lumiguides.it.com | <prod-domain> |
| ACM | us-west-1 (API GW) + us-east-1 (CloudFront/Cognito) | Như dev, trong aa-staging | Như dev, trong aa-prod |

## 7. Tổ chức lại repo Terraform (AA-CIS-Infra)

Tách root accounts/aa365 (1 state) thành các stack mỏng dưới live/<account>/<region>/<stack>, mỗi stack một state. Mỗi account có bucket state riêng: aa-dev giữ bucket hiện có, prod có bucket riêng như ADR 0012 quyết định 5. Module dùng chung có version để promote. CI vào thẳng role Terraform của account đích qua OIDC (không chain role). allowed_account_ids lấy từ tfvars. Giữ nguyên đường DB Migrate.

```text
AA-CIS-Infra/
├── README.md · CONTEXT.md · CODEOWNERS
├── stacks.yaml                  # danh mục stack: path, account, env, depends_on, GitHub environment
├── .pre-commit-config.yaml · .tflint.hcl · .trivyignore   # Terraform pin 1.15.5 trong required_version + workflow
├── config/
│   └── accounts.yaml            # tên → account ID → OU → email (không có secret)
├── modules/                     # không có provider/backend; tag chung modules-vX.Y.Z
│   ├── account-baseline/        # bucket state + KMS, OIDC provider, role Terraform, boundary, S3 PAB, EBS encryption, budget
│   ├── network/                 # VPC, subnet, NAT instance|gateway, endpoint, <env>.internal
│   ├── data-rds/  cache/
│   ├── platform/                # ECS cluster, ALB, VPC link, API GW + custom domain, WAF
│   ├── identity-cognito/  edge-cdn/  dns-zone/  observability/  secrets/
│   ├── ecs-service/             # 1 service: task def, SG, log group, alarm, autoscaling
│   ├── app-cis/  app-booking/  app-crm/  app-tripplanner/
│   └── org/  identity-center/  security-tooling/  log-archive/  backup-vault/
├── live/
│   ├── management/{_backend.hcl, global/{00-baseline,10-organization,20-identity-center,30-billing}}/
│   ├── log-archive/{_backend.hcl, us-west-1/{00-baseline,20-log-buckets}}/
│   ├── security/{_backend.hcl, us-west-1/{00-baseline,20-security-tooling}}/
│   ├── backup/{_backend.hcl, us-west-1/{00-baseline,20-backup-vault}}/
│   ├── shared-services/{_backend.hcl, us-west-1/{00-baseline,20-ecr,30-dns,40-artifacts}}/
│   ├── shared-ai/{_backend.hcl, us-west-1/{00-baseline,20-bedrock}}/
│   ├── dev/
│   │   ├── _backend.hcl         # bucket aa-cis-tfstate-005097885195 (giữ)
│   │   └── us-west-1/{00-baseline,20-network,30-data,40-platform,50-app-cis,51-app-booking,52-app-crm,53-app-tripplanner,60-observability}/
│   ├── staging/   (cấu trúc giống dev, bucket riêng)
│   └── prod/      (cấu trúc giống dev, bucket riêng)
│       mỗi stack: backend.tf · providers.tf · main.tf · variables.tf · outputs.tf · terraform.tfvars (account_id) · README.md
├── policies/{scp,rcp,tag,backup}/*.json
├── db/                          # GIỮ NGUYÊN: migrations/<owner>/, schema_dump.py, script DB Migrate
├── scripts/{tf.sh,state-split/}
├── .github/workflows/{tf-lint,tf-plan,tf-apply,tf-drift,db-migrate,...}.yml
└── docs/{adr,runbooks,generated}/
```

### Stack theo account

| Account | Stack | Nội dung | Phụ thuộc | Ai apply |
|---|---|---|---|---|
| mọi account | 00-baseline | Bucket state + KMS của chính account; OIDC provider; role aa-terraform-plan/apply; boundary; S3 PAB; EBS encryption mặc định; budget account | — (bootstrap local bằng OrganizationAccountAccessRole + MFA, rồi init -migrate-state vào chính bucket đó) | Lần đầu local; sau đó CI |
| management | 10-organization | Organization, OU, account, SCP/RCP/tag/backup/AI opt-out (đọc policies/*.json), trusted access, delegated admin | 00 | CI environment org (có reviewer) |
| management | 20-identity-center | Group, permission set, assignment theo ma trận | 10 | CI environment org |
| management | 30-billing | Budget cấp org, cost allocation tag, Data Exports | 10 | CI environment org |
| log-archive | 20-log-buckets | Bucket trail/ALB/Config/Data Exports + KMS + Object Lock | 10-organization | CI |
| security | 20-security-tooling | Access Analyzer; GuardDuty/Security Hub/Config (count = 0 cho tới khi duyệt) | 10-organization | CI |
| backup | 20-backup-vault | Vault, vault lock, key policy cho copy chéo account | 10-organization | CI (prod environment) |
| shared-services | 20-ecr, 30-dns, 40-artifacts | ECR (pull policy theo aws:PrincipalOrgID + replication sang aa-prod); zone dùng chung; bucket artifact Lambda | 00 | CI |
| shared-ai | 20-bedrock | Invoker role cho từng môi trường, batch role, cost reader, anomaly (dời từ accounts/acc3-bedrock) | 00 | CI (bỏ profile ghi cứng) |
| dev / staging / prod | 20-network | VPC, subnet, NAT, endpoint, private zone <env>.internal | 00 | CI |
| dev / staging / prod | 30-data | RDS, parameter group, CNAME db.<env>.internal, Redis (tuỳ môi trường) | 20 | CI; prod có reviewer |
| dev / staging / prod | 40-platform | ECS cluster aa-<env>-cluster, ALB, VPC link, API GW, Cognito, WAF, edge/CDN, bản ghi DNS | 20, 30 | CI |
| dev / staging / prod | 50-app-cis, 51-app-booking, 52-app-crm, 53-app-tripplanner | Service ECS / Lambda, bucket, secret (chỉ khai báo), alarm, role runtime và role deploy của từng app | 40 | CI |
| dev / staging / prod | 60-observability | SNS, dashboard, alarm chung, budget theo App | 40 | CI |

_Tổng 43 root: management 4, log-archive 2, security 2, backup 2, shared-services 4, shared-ai 2, mỗi môi trường 9 × 3. Giữa các stack cùng account, thông tin truyền qua SSM Parameter /aa/<env>/<stack>/<key> (stack sinh ra thì ghi, stack dùng thì đọc bằng data source). Giá trị xuyên account (URL ECR, ARN invoker role) lấy từ config/accounts.yaml. Không dùng terraform_remote_state xuyên account._

### Bố trí state

| Thuộc tính | Giá trị |
|---|---|
| Bucket theo account | aa-tfstate-<account-id>-usw1 trong chính account đó (management, log-archive, security, backup, shared-services, staging, prod) |
| aa-dev | Giữ bucket hiện có aa-cis-tfstate-005097885195; chỉ thêm key mới cho từng stack |
| aa-shared-ai | Giữ bucket aa-cis-tfstate-acc3-bedrock-786888028788; THÊM use_lockfile (hiện không có khoá), bỏ profile = nghiep_aa365 |
| Key | <account>/<region>/<stack>/terraform.tfstate, vd prod/us-west-1/30-data/terraform.tfstate |
| Lock | use_lockfile = true (S3 native, GA từ 1.11; repo đang pin 1.15.5) |
| Mã hoá | SSE-KMS bằng key của chính account (key policy chỉ cho role Terraform của account đó + break-glass); bật bucket key |
| Versioning / lifecycle | Bật versioning; giữ bản noncurrent 90 ngày |
| Quyền | Role plan: đọc state + ghi/xoá *.tflock; role apply: đọc/ghi; agent chỉ có quyền ở aa-dev; bucket chỉ cho TLS; Block Public Access; Object Ownership = BucketOwnerEnforced |
| Bootstrap | 00-baseline apply bằng state local qua OrganizationAccountAccessRole + MFA, rồi terraform init -migrate-state vào chính bucket đó |

_Mỗi account một bucket nên không có cross-account trên đường state: đúng ADR 0012 quyết định 5 (prod có bucket riêng) và thu nhỏ blast radius. Nguồn: https://developer.hashicorp.com/terraform/language/backend/s3_

### Mẫu provider và backend

| File | Mẫu | Ghi chú |
|---|---|---|
| backend.tf | terraform { backend "s3" {} } — cấu hình partial: terraform init -backend-config=../../_backend.hcl -backend-config="key=prod/us-west-1/30-data/terraform.tfstate" | _backend.hcl của từng account: bucket, region = "us-west-1", use_lockfile = true, encrypt = true, kms_key_id = "<ARN>". Không cần assume_role vì bucket cùng account. Nếu buộc phải assume chéo thì viết dạng thuộc tính: assume_role = { role_arn = "..." } |
| terraform.tfvars | account_id = "<id hằng số của account này>" | Không truyền account_id từ CLI/biến môi trường |
| providers.tf | provider "aws" { region = var.region; allowed_account_ids = [var.account_id]; default_tags { tags = local.tags } } — CI không cần assume_role; local thêm assume_role { role_arn = "arn:aws:iam::${var.account_id}:role/aa-terraform-${var.mode}" } | allowed_account_ids làm plan fail khi credential trỏ sai account (đã từng ghi nhầm 2 lần) |
| providers.tf (alias) | provider "aws" { alias = "us_east_1"; region = "us-east-1"; allowed_account_ids = [var.account_id] } | Chỉ cho ACM của CloudFront/Cognito |
| Chuỗi credential CI | OIDC (AssumeRoleWithWebIdentity) → aa-terraform-<plan\|apply> của account đích, max session 2h | Không chain role (role chaining bị giới hạn 1h, dễ hết hạn khi apply RDS lâu) |
| Chuỗi credential local | aws sso login → profile aae-<env>-admin → (tuỳ) assume aa-terraform-* | Chỉ dùng cho bootstrap và sự cố |
| versions.tf | required_version = "1.15.5" (pin chính xác, AA-846); aws ~> 6.69 | Đổi version thì sửa mọi stack và workflow trong cùng PR |

### Version module và promote

| Hạng mục | Quy ước |
|---|---|
| Dev | source = "../../../../modules/<tên>" (luôn lấy bản mới nhất) |
| Staging / prod | source = "git::https://github.com/AdventureAsia365-Ecosys/AA-CIS-Infra.git//modules/<tên>?ref=modules-v1.4.0" |
| Tag | Một tag chung cho cả bộ module, modules-vMAJOR.MINOR.PATCH (đơn giản hơn tag riêng từng module khi chỉ có 1 người); CHANGELOG; thay đổi phá vỡ thì tăng major |
| Promote | PR tăng ref ở live/staging → apply → kiểm → PR tăng ref ở live/prod |
| Kiểm trong CI | Cấm đường dẫn tương đối trong live/staging và live/prod (lint) |
| Khi repo thành private | CI cần token GitHub App để đọc module qua git |

### Quy ước đặt tên

| Đối tượng | Quy ước | Ví dụ |
|---|---|---|
| Account | aa-<vai trò> | aa-prod, aa-shared-ai |
| Resource chung của môi trường | aa-<env>-<loại> | aa-prod-cluster, aa-prod-db, aa-prod-vpc |
| Resource của app | aa-<app>-<env>-<loại> | aa-booking-staging-api |
| IAM role runtime | aa-<app>-<env>-<mục đích> | aa-crm-prod-task |
| Role CI | aa-ci-<repo ngắn>-<plan\|apply\|deploy>; Terraform: aa-terraform-<plan\|apply> | aa-ci-booking-deploy |
| Secret | <app>/<env>/<tên> | booking/prod/database-url |
| SSM Parameter | /aa/<env>/<stack>/<key> | /aa/prod/20-network/vpc_id |
| S3 | aa-<app>-<env>-<mục đích>-<account-id> | aa-cis-prod-bronze-<id> |
| Log group | /aa/<env>/<app>/<component> | /aa/prod/cis/api |
| KMS alias | alias/aa-<env>-<mục đích> | alias/aa-prod-crm-data |
| Private zone | <env>.internal | db.prod.internal |
| GitHub environment | dev, staging, prod, org (+ prod-plan, org-plan có reviewer) | — |

### Tag mặc định (default_tags)

| Tag | Giá trị | Nguồn |
|---|---|---|
| Project | aa-ecosys | locals |
| Environment | dev / staging / prod / shared | var.environment (có validation) |
| App | cis / booking / tripplanner / crm / shared / ai / platform | Biến của module app |
| Account | Tên account | config/accounts.yaml theo account_id; không viết literal |
| Stack | Tên stack | var.stack |
| ManagedBy | terraform | locals |
| Owner, CostCenter, DataClass | Theo tag policy | Biến |

### CI

| Workflow | Trigger | Role / GitHub environment | Cổng |
|---|---|---|---|
| tf-lint.yml | PR | Không cần AWS | fmt, validate, tflint, trivy config, checkov (kể cả kiểm tag), terraform-docs sạch |
| tf-plan.yml | PR | dev/staging/shared: aa-terraform-plan (read-only; trust pull_request của repo). prod/org: environment prod-plan/org-plan có reviewer | Đọc stacks.yaml tìm stack bị ảnh hưởng (kể cả qua module) → matrix plan → comment TÓM TẮT vào PR; plan_guard.py chặn destroy dữ liệu; KHÔNG upload file plan làm artifact (repo public) |
| tf-apply.yml | Push main | dev: environment dev (tự động); staging: environment staging; prod/org: có required reviewer, chỉ từ main | Plan lại trong job apply, so tóm tắt với plan đã duyệt (số add/change/destroy + địa chỉ resource), lệch thì dừng |
| tf-drift.yml | Hằng đêm | Role plan | plan -detailed-exitcode; có drift thì tạo issue hoặc gửi cảnh báo |
| db-migrate.yml (giữ) | Dispatch | Thêm input environment: dev \| staging \| prod; bucket và role lấy từ biến của GitHub environment | Prod chỉ chạy tay |
| Workflow app (repo app) | Merge main / dispatch | aa-ci-<app>-deploy trong từng account; ECR push ở shared | Như mục 6 |

_Repo Infra đang public (kiểm 29/10), nên artifact và log CI ai đăng nhập GitHub cũng xem được. Environment dev, dev-db-auto, prod, staging đã tồn tại nhưng chỉ dev-db-auto có rule (branch_policy). Bật required reviewer ngay khi repo còn public (miễn phí); khi repo chuyển private cần GitHub Team (4 USD/user/tháng) để giữ cổng. Trust OIDC: sub = repo:<org>/<repo>:environment:<env> + điều kiện ref; cân nhắc tuỳ biến sub theo repository_id vì tên org đã đổi một lần._

### Công cụ

| Công cụ | Chạy ở | Mục đích | Fail khi |
|---|---|---|---|
| terraform fmt / validate | pre-commit + CI | Định dạng, cú pháp | Có diff hoặc lỗi |
| tflint (+ ruleset aws) | pre-commit + CI | Lỗi thường gặp, tên, biến không dùng | Có lỗi |
| trivy config hoặc checkov | CI | Cấu hình không an toàn, thiếu tag bắt buộc | Có mức HIGH chưa được miễn có lý do |
| terraform-docs | pre-commit | README cho module và stack | README lệch |
| gitleaks (đã có) | CI | Secret lọt vào repo | Có phát hiện |
| plan_guard.py (đã có) | CI | Chặn destroy RDS/S3/KMS/Object Lock | Có destroy |
| required_version | Mọi stack | Khoá Terraform 1.15.5, provider ~> 6.69 | Lệch version |

### Plain Terraform hay Terragrunt

| Tiêu chí | Plain Terraform + partial backend + stacks.yaml | Terragrunt | Kết luận |
|---|---|---|---|
| Số công cụ | 1 | 2 (thêm HCL của Terragrunt) | Plain |
| Lặp backend/provider | Có, nhưng nhỏ (một _backend.hcl mỗi account + wrapper scripts/tf.sh) | Không | Terragrunt hơn |
| Phụ thuộc giữa stack | Thứ tự trong stacks.yaml + SSM | Có dependency block | Terragrunt hơn |
| Độ phức tạp CI | Matrix đơn giản | run-all, cache, cần hiểu thêm | Plain |
| Đội 1 tech lead + agent, 43 root (27 root là 3 bản giống nhau) | Đủ dùng nếu có scripts/tf.sh và stacks.yaml | Giảm lặp rõ khi số root lớn | Plain lúc này |
| Lock-in / license | Terraform BSL; chuyển OpenTofu dễ | Như trên | Hoà |

_Quyết định: dùng plain Terraform 1.15.5. Xem lại khi số root vượt khoảng 60, khi phụ thuộc chéo gây lỗi thứ tự từ 2 lần trở lên, hoặc khi thêm region thứ hai._

### Kế hoạch chuyển từ root hiện tại

| Bước | Việc | Cách | Cổng / kiểm | Rollback |
|---|---|---|---|---|
| M0 | Đóng băng apply Infra; sao lưu state | Ghi serial và version id của dev/terraform.tfstate; tag repo pre-reorg | State tải lại được | Khôi phục version cũ của state |
| M1 | Đổi environment GitHub 'prod' (thực chất là Dev) thành 'dev' (ADR 0012 d6) | Thêm subject environment:dev vào trust aa-cis-infra-tf-apply (apply local có MFA) → đổi terraform-apply.yml và db-migrate.yml sang environment: dev → gỡ subject cũ → bật reviewer cho prod/staging | Apply dev chạy được | Trả lại subject cũ |
| M2 | Gom resource vào module ngay trong root cũ | moved block (chỉ dùng được trong cùng state) | Plan 0 thay đổi | Revert PR |
| M3 | Viết SSM Parameter cho các output mà stack mới cần đọc | Root cũ ghi /aa/dev/<stack>/<key> | Plan chỉ thêm SSM | Revert PR |
| M4 | Tách state từng stack, theo thứ tự rủi ro thấp → cao: 60-observability → 53-tripplanner → 52-crm → 51-booking → 50-cis → 40-platform → 30-data → 20-network → 00-baseline | Root mới: import block (ID sinh bằng script từ terraform show -json). Loại không import được (tls_private_key, null_resource...): state pull → terraform state mv -state=old.tfstate -state-out=new.tfstate → state push. Root cũ: đổi các tham chiếu tới resource đã dời sang data source/SSM, rồi removed { lifecycle { destroy = false } } | Cả hai plan đều 0 thay đổi hạ tầng; RDS bật deletion_protection + prevent_destroy | Bỏ removed ở root cũ, xoá state stack mới |
| M5 | CI chuyển sang matrix theo stacks.yaml; DB Migrate tham số hoá bucket và environment | Biến của GitHub environment | DB Migrate mode=check xanh sau từng bước | Workflow cũ giữ song song 2 tuần |
| M6 | Bỏ ID account và literal 'dev' ghi cứng | account_id trong tfvars + config/accounts.yaml; modules/ecs bỏ ARN cứng; boundary theo account thay mẫu aa-*-dev-* | grep 005097885195 trong .tf = 0 (trừ tfvars/config) | Revert PR |
| M7 | Dời accounts/acc3-bedrock sang live/shared-ai/us-west-1/20-bedrock (làm được từ phase 2) | Giữ bucket cũ; thêm use_lockfile; bỏ profile; đổi key bằng terraform init -migrate-state; tạo role CI trong account AI | Plan 0 thay đổi | State cũ vẫn còn trong bucket (có versioning) |
| M8 | Dọn dẹp | Xoá accounts/aa365 (đã rỗng), thư mục local acc1-bedrock và envs/dev; sửa Infra CONTEXT.md | Drift job xanh 7 đêm | — |

_Mỗi bước M4 đóng băng tối đa 1 ngày. Vẫn deploy app (đổi image) được, trừ stack của chính app đang tách. Không chạy DB Migrate apply trong lúc tách 30-data. Phải chờ bảng job rảnh (DM-11.4)._

## 8. Quy ước AWS CLI profile

Thay các profile làm tay bằng một khối sso-session 'aa' và profile đặt tên aae-<account>-<vai trò>. Tiền tố 'aae' (AA Ecosys) để không trùng các profile aa-dev/aa-stg/aa-prod của Quanskill cũ. Profile default chỉ có quyền đọc ở dev để tránh ghi nhầm account. Break-glass dùng profile riêng, ngoài SSO.

```text
# ~/.aws/config — mẫu, không có secret. Thay <...> bằng giá trị thật.
[sso-session aa]
sso_start_url = https://<d-xxxxxxxxxx>.awsapps.com/start
sso_region = us-west-1
sso_registration_scopes = sso:account:access

[default]
sso_session = aa
sso_account_id = 005097885195
sso_role_name = AA-ReadOnly
region = us-west-1

[profile aae-dev-admin]
sso_session = aa
sso_account_id = 005097885195
sso_role_name = AA-DevAdmin
region = us-west-1

[profile aae-staging-engineer]
sso_session = aa
sso_account_id = <staging-account-id>
sso_role_name = AA-PlatformEngineer
region = us-west-1

[profile aae-prod-readonly]
sso_session = aa
sso_account_id = <prod-account-id>
sso_role_name = AA-ReadOnly
region = us-west-1

[profile aae-prod-operator]
sso_session = aa
sso_account_id = <prod-account-id>
sso_role_name = AA-ProdOperator
region = us-west-1

[profile aae-ai-engineer]
sso_session = aa
sso_account_id = 786888028788
sso_role_name = AA-PlatformEngineer
region = us-west-1

[profile aae-mgmt-billing]
sso_session = aa
sso_account_id = <management-account-id>
sso_role_name = AA-Billing
region = us-east-1

[profile aae-dev-agent]
role_arn = arn:aws:iam::005097885195:role/aa-agent-dev
source_profile = aae-dev-admin
duration_seconds = 3600
region = us-west-1

# Dùng:  aws sso login --sso-session aa
#        aws sts get-caller-identity --profile aae-dev-admin
```

### Profile mới

| Profile | Account | Permission set / role | Dùng cho |
|---|---|---|---|
| (sso-session aa) | — | — | aws sso login --sso-session aa: đăng nhập một lần cho mọi profile |
| default | aa-dev | AA-ReadOnly | Lệnh không ghi --profile sẽ chạy với quyền chỉ đọc |
| aae-mgmt-admin | aa-management | AA-Admin (1h) | Org, Identity Center |
| aae-mgmt-billing | aa-management | AA-Billing | Chủ doanh nghiệp xem chi phí |
| aae-log-readonly | aa-log-archive | AA-ReadOnly | Tra log |
| aae-security-audit | aa-security | AA-SecurityAudit | Rà soát |
| aae-shared-admin | aa-shared-services | AA-Admin | ECR, DNS |
| aae-ai-engineer | aa-shared-ai | AA-PlatformEngineer (nếu AI ở trong org); nếu đứng ngoài org thì dùng IAM role cross-account | Bedrock (thay nghiep_aa365) |
| aae-dev-admin | aa-dev | AA-DevAdmin (8h) | Việc dev hằng ngày (thay aa365-admin) |
| aae-dev-readonly | aa-dev | AA-ReadOnly | Kiểm trạng thái |
| aae-staging-engineer | aa-staging | AA-PlatformEngineer | Staging |
| aae-prod-readonly | aa-prod | AA-ReadOnly | Xem prod |
| aae-prod-operator | aa-prod | AA-ProdOperator (1h) | Scale, xem log (không ECS exec) |
| aae-prod-admin | aa-prod | AA-Admin (1h) | Sự cố; ghi lý do |
| aae-dev-agent | aa-dev | IAM role aa-agent-dev (role_arn, source_profile = aae-dev-admin) | Agent lập trình; role chaining tối đa 1h |
| aae-breakglass | aa-management | IAM user break-glass + MFA (không lưu key trên máy) | Chỉ khi Identity Center hỏng; cấu hình tạm rồi xoá |

### Profile cần gỡ

| Profile cũ | Hiện trỏ tới | Thay bằng | Khi nào gỡ |
|---|---|---|---|
| default (role admin acc2, AA-517) | Admin acc2 | default = aae-dev-readonly | Cuối phase 1 |
| aa365-admin, aa365-admin-session | Admin acc2 qua role + MFA | aae-dev-admin | Sau phase 3 + 2 tuần chạy song song |
| aa365-admin-toolkit | Công cụ cũ | Không thay | Phase 1 |
| aa365-agent | Role agent acc2 | aae-dev-agent | Phase 3 |
| aa365-nghiep-base | IAM user nền (access key + MFA) | Xoá access key, xoá IAM user | Khi Identity Center chạy ổn (phase 3 + 2 tuần); sau đó gỡ miễn trừ DenyIAMUserKeys cho aa-dev |
| nghiep_aa365 | Account AI | aae-ai-engineer | Phase 2 |
| pqnghiep-admin, acc1-legacy-default | Account cá nhân (acc1) | Gỡ khỏi config hệ sinh thái | Ngay |
| aa-dev, aa-stg, aa-prod (+ -admin) | Quanskill cũ (ap-southeast-1) | Gỡ | Ngay, trước khi tạo aae-* |

_Chưa đọc ~/.aws/config (đúng quy định không đọc credential), nên chưa xác minh role ARN của từng profile cũ. Khi đổi profile phải sửa đồng thời: CLAUDE.md toàn cục (mục AWS ACCOUNTS, mẫu S3 ECS exec), CLAUDE.md của workspace, các skill (ai-nghiep, aa-ship, aa-cis-schema), runbook, và lệnh mẫu kiểu C=$(aws configure export-credentials --profile aa365-admin ...) trong steering._

### MFA và thời hạn session

| Hạng mục | Giá trị |
|---|---|
| MFA | Identity Center bắt MFA khi đăng nhập; admin dùng FIDO2/passkey |
| Token SSO | Tự làm mới, cache trong ~/.aws/sso/cache; PKCE là mặc định ở CLI v2 bản mới (máy không có trình duyệt dùng --use-device-code) |
| Session | Theo permission set: 1h (Admin/ProdOperator/BreakGlass), 4h (PlatformEngineer/Billing/Audit), 8h (DevAdmin/ReadOnly) |
| Script / terraform local | Dùng --profile hoặc AWS_PROFILE; provider có allowed_account_ids; không export credential trần |
| CI | Chỉ OIDC; không có access key |

## 9. Lộ trình theo phase

Thứ tự: duyệt thiết kế và chốt thanh toán → management + Identity Center → sửa và (nếu được) đưa account AI vào org → đưa account infra vào org → sắp xếp lại Terraform → dựng staging → dựng prod và go-live → vận hành. Phase 0–4 gần như không tốn tiền AWS; chi phí tăng từ phase 5. Tính cả thời gian chờ TrueIDC, AWS Support và mốc đầu tháng thì cả lộ trình mất khoảng 3–4 tháng lịch.

### Các phase

| Phase | Bước chính | Người làm | Thời gian (ngày công) | Chi phí AWS thêm/tháng | Tiêu chí xong | Rollback |
|---|---|---|---|---|---|---|
| 0. Duyệt thiết kế + thanh toán | ADR 0018 thay quyết định 1, 2, 5 của ADR 0012; sửa ADR 0001 (đoạn 'No new AWS account is created') và ADR 0001a; gửi câu hỏi cho TrueIDC; chốt mô hình thanh toán (mục 5); kế toán xác nhận chuyện hoá đơn | Tech lead; chủ doanh nghiệp duyệt | 2 | 0 | ADR được chấp nhận; mô hình thanh toán đã chốt | Giữ ADR 0012 |
| 1. Management + Identity Center | Root MFA (2 FIDO2), IAM user break-glass, alternate contacts, bật Organizations (all features) + trusted access, OU, FullAWSAccess + aa-scp-root + aa-scp-denyall + AI opt-out, tạo log-archive/security/shared-services/staging (trống), Identity Center, budget org, 00-baseline mỗi account, CI environment org | Tech lead | 4–5 | 0–5 USD | Đăng nhập SSO vào mọi account mới; ma trận quyền đạt; budget gửi được mail thử; diễn tập break-glass đạt | Đóng account trống; tắt Identity Center |
| 2. Account AI | Sửa Error 002 khi account còn đứng riêng (thẻ, FTU, case Support); vào org chỉ khi mục 5 cho phép; M7 | Tech lead | 1–2 (+ chờ AWS) | 0 (Bedrock tính theo dùng) | Mọi route LLM gọi model thật được; chi phí vào llm_call_log | Rời org (OU Transitional); API trực tiếp |
| 3. Account infra vào org | Bước 9–18 ở mục 3; org trail; gỡ trail riêng; Access Analyzer org; aa-scp-baseline/region | Chủ doanh nghiệp + tech lead | 1–2 (+ chờ tới ngày 1 của tháng) | 0 (thêm S3/KMS log 1–3 USD) | Smoke xanh (kể cả Cohere Embed); plan 0 thay đổi; org trail có log | Xin TrueIDC mời lại |
| 4. Sắp xếp lại Terraform (chỉ dev) | M0–M8 ở mục 7; ECR trung tâm; workflow app dùng role và biến theo environment; đưa Cognito ID ra config | Tech lead + engineer/agent | 12–18 | 0–5 USD (ECR) | Mọi stack plan 0 thay đổi; drift xanh 7 đêm; không còn ID ghi cứng | Từng bước có rollback riêng |
| 5. Dựng staging | Apply live/staging từ đầu; seed secret theo secrets-register; job scrub dữ liệu; Vercel project staging; DB Migrate staging; E2E; thử 'huỷ rồi dựng lại' | Tech lead + engineer | 6–8 | 15–30 (đã huỷ) / 90–130 (dừng tạm) / 150–200 (bật liên tục) | Đạt các mục kiểm của phase 5 (mục 10) | Destroy stack staging |
| 6. Prod + go-live | Tạo aa-prod + aa-backup; xin quota; apply live/prod; Vercel Pro + project prod; tên miền prod; SES production access; backup policy (region + account); diễn tập DR; bật dịch vụ bảo mật được duyệt; tiêu chí go-live (ADR 0012 d11); hồ sơ dữ liệu cá nhân | Tech lead; chủ doanh nghiệp duyệt chi phí, ngày, pháp lý | 13–16 | 410–580 USD list (290–410 có đòn bẩy) + bảo mật 0–110 | Đạt các mục kiểm của phase 6; báo cáo chi phí 7 ngày đầu | Chưa go-live thì destroy được; sau go-live thì rollback bằng release |
| 7. Vận hành | Bảng ở mục 12; RCP; delegate Identity Center sang aa-security (tuỳ chọn) | Tech lead + engineer | 2–4/tháng | Theo mục 11 | Các nhịp rà soát chạy đúng hạn | — |

### ADR và tài liệu cần viết/sửa

| Tài liệu | Việc | Phase |
|---|---|---|
| docs/adr/0018-multi-account-organization.md (số kế tiếp, đã kiểm trong docs/adr/README.md) | Mô hình org, OU, account, thanh toán; thay quyết định 1, 2, 5 của ADR 0012 (giữ 3, 4, 6–11 và áp theo account); ADR 0012 d12 đã có trigger 'AA-864 consolidate' | 0 |
| docs/adr/0012-environment-model.md | Đánh dấu 'Superseded in part by 0018' | 0 |
| docs/adr/0001-ecosystem-target-architecture.md | Sửa đoạn 'No new AWS account is created' (dòng 87) | 0 |
| docs/adr/0001a-retire-acc1-llm-on-acc3-only.md | Mô hình 2 account → org nhiều account; vị trí account AI | 0 |
| Data standards C7.2c, C7.2d; handbook D-17, §6.1, §9.3 + bản .vi.md | Layout prod, cổng prod, thêm staging | 0 |
| infra/AA-CIS-Infra/CONTEXT.md (dòng 423: 'a new environment gets its own accounts/<name>/ root'), README.md | Root mới, stack, quy trình | 4 |
| Infra docs/adr (ADR riêng của Infra) | Layout live/, state theo account, bootstrap, version module | 4 |
| docs/ops/runbooks/* | Thêm cột account/môi trường; runbook mới: account-join, account-create, identity-center-access, scp-change, state-split, prod-release, dr-cross-region-restore, break-glass-iam | 1–6 |
| docs/security/secrets-register.md | Thêm cột môi trường/account | 5 |
| CLAUDE.md (toàn cục + workspace), steering, skill ai-nghiep / aa-ship / aa-cis-schema | Bảng account, profile, mẫu ECS exec | 3–4 |

## 10. Kế hoạch kiểm thử theo phase

Phase nào cũng chỉ xong khi có bằng chứng chạy thật: lệnh và kết quả lưu trong docs/ops/drills hoặc thư mục audit. SCP luôn thử ở OU Policy-Staging trước khi gắn rộng. Bedrock chỉ tính là đạt khi gọi model thật thành công.

### Kiểm thử

| Phase | Kiểm gì | Cách | Đạt khi |
|---|---|---|---|
| 1 | SCP DenyLeave / DenyAll | Gắn aa-scp-baseline cho Policy-Staging; từ aa-staging gọi organizations leave-organization. Đưa account thử vào Suspended rồi gọi một lệnh bất kỳ | AccessDenied |
| 1 | Giới hạn SCP | Đếm số SCP gắn trực tiếp mỗi đích, kích thước từng file JSON (script trong CI) | ≤5 mỗi đích; ≤5.120 ký tự mỗi file |
| 1 | Ma trận quyền | Script đọc ma trận (yaml) → đăng nhập bằng user thử của từng nhóm → chạy danh sách lệnh được phép/bị cấm ở từng account | Khớp ma trận 100% |
| 1 | Break-glass | Đăng nhập root aa-management bằng khoá thứ hai; IAM user break-glass assume OrganizationAccountAccessRole vào 1 member | Vào được; cảnh báo tới trong 5 phút |
| 1 | Budget | Hạ ngưỡng tạm thời | Mail tới hộp thư nhóm |
| 2 | Bedrock | Mỗi route một lệnh gọi nhỏ qua LLMClient (stage adhoc); KHÔNG dựa vào GetFoundationModelAvailability | Hết Error 002; chi phí được ghi |
| 2–3 | SCP region | Ở account thử: ec2 describe-vpcs --region ap-southeast-1 (phải bị chặn); us-west-1 OK; iam list-roles OK; ACM us-east-1 OK; Bedrock global inference OK ở shared-ai | Đúng kỳ vọng từng lệnh |
| 3 | Account infra sau khi chuyển | /health và /health/ready các API; ECS steady; DB Migrate mode=check; CI deploy dev; terraform plan; gọi Cohere Embed | Tất cả xanh; plan 0 thay đổi |
| 3 | Org trail | Tạo event ở member; tìm trong bucket log-archive; principal không có quyền bypass thử xoá object | Có log trong 15 phút; không xoá được |
| 3 | RCP / OIDC (khi bật RCP ở phase 7) | Chạy workflow CI dùng OIDC; CloudFront OAC đọc S3 | Vẫn chạy |
| 4 | Tách state | Plan từng stack sau mỗi bước; drift job | 0 thay đổi; drift xanh 7 đêm |
| 4 | Chặn ghi nhầm account | (a) Đặt account_id sai trong tfvars của một stack thử → plan; (b) dùng credential dev chạy plan stack prod | (a) lỗi allowed_account_ids; (b) AccessDenied ở AssumeRole/state |
| 4 | Không lộ secret qua CI | Kiểm workflow: không upload *.tfplan; comment PR chỉ có tóm tắt | Không có artifact plan |
| 5 | Dựng lại từ đầu | Apply live/staging từ trống; destroy; apply lại | Lên đủ, không cần sửa tay |
| 5 | Migration từ 0 | DB Migrate apply toàn bộ owner trên staging | Đủ migration, schema dump khớp dev |
| 5 | Không có PII | Quét email/số điện thoại/tên thật trên dữ liệu staging sau scrub | 0 kết quả (trừ địa chỉ thử) |
| 5 | E2E | Bộ Playwright chạy trên tên miền stg | Xanh |
| 5 | Restore drill | RDS PITR trên staging → instance mới → app trỏ sang | RTO ghi lại ≤1h |
| 5 | Load test | k6 với tải mục tiêu do chủ doanh nghiệp ước (vd 5× tải dự kiến) | p95 < 500 ms, lỗi < 0.5%, autoscaling chạy |
| 6 | Baseline bảo mật | Prowler (OSS) hoặc Security Hub nếu được duyệt; checkov | Không còn mức HIGH chưa xử lý; S3 public = 0; SG 0.0.0.0/0 chỉ ở ALB 443; IMDSv2; mã hoá CMK |
| 6 | DR | Restore từ bản sao us-west-2 VÀ từ vault ở aa-backup; reboot RDS có failover | RTO region ≤4h; failover AZ khoảng 3 phút trở xuống |
| 6 | Rollback release | Deploy lại revision task definition trước đó | ≤10 phút, smoke xanh |
| 6 | Cảnh báo | Gây alarm thử ở prod | Tới đúng người theo bảng routing |
| 6 | Quota | Service Quotas của aa-prod: Lambda concurrency, Fargate vCPU, SES | Đạt mức đã xin |
| 6 | Chi phí | So chi phí 7 ngày thực tế với ước tính | Lệch trong ±20%; vượt thì phải giải thích |
| 7 | Định kỳ | DR hằng quý, rà quyền hằng quý, chi phí hằng tháng, break-glass 6 tháng | Biên bản đúng hạn |

## 11. Chi phí

Governance cơ bản (Organizations, Identity Center, bản org trail đầu tiên) miễn phí. Chi phí tăng chủ yếu từ prod, sau đó tới staging. Staging rẻ nhất khi huỷ lúc rảnh, vì ALB, WAF, secret và IPv4 không dừng được. Dịch vụ bảo mật trả phí chờ duyệt riêng từng mục. Mọi số là ước tính theo giá list us-west-1, chưa phải báo giá; số Dev biến động theo wave LLM.

### Chi phí tháng theo account và phase (USD, ước tính)

| Account | Hôm nay | Sau phase 1–4 | + staging (phase 5, dừng tạm) | + prod (phase 6) |
|---|---|---|---|---|
| aa-dev (005097885195) | 140–200 (08: 140.22; 09: 134.96; 1–28/10: 185.77) | 140–200 | 140–200 | 140–200 |
| aa-management | — | 0–5 | 0–5 | 0–5 |
| aa-log-archive | — | 1–5 | 1–5 | 2–8 |
| aa-security (chỉ dịch vụ miễn phí) | — | 0 | 0 | 0 |
| aa-backup | — | — | — | 1–5 |
| aa-shared-services | — | 5–15 | 5–15 | 5–20 |
| aa-shared-ai | Theo dùng (Lift credit 249.94 hết hạn 31/12; có thể không trả cho model Marketplace) | Theo dùng | Theo dùng | Theo dùng |
| aa-staging | — | 0 | 90–130 (huỷ khi rảnh: 15–30; bật liên tục: 150–200) | Như cột trước |
| aa-prod | — | — | — | 410–580 list / 290–410 có đòn bẩy |
| Tổng (chưa tính LLM và dịch vụ bảo mật trả phí) | 140–200 | 146–225 | 236–355 | 648–948 (list) / 528–778 (có đòn bẩy) |

_Prod lấy từ ADR 0012 (Price List API 28/10/2026): RDS db.t4g.medium Multi-AZ khoảng 125 USD; 2 NAT gateway khoảng 70; ALB khoảng 25; task Fargate 0.5 vCPU/1 GB khoảng 21 USD/tháng; cộng 10–30 USD phần nền của account riêng (KMS, WAF, secret, IPv4, log). Đòn bẩy: 1 NAT, Fargate ARM, worker 1 task, RDS reserved 1 năm. Staging dừng tạm vẫn tốn: ALB (dev tháng 10: 34), WAF (10), secret (dev 51 secret ≈ 20), IPv4/VPC (10), lưu trữ RDS._

### Dịch vụ governance

| Dịch vụ | Miễn phí / trả phí | Ước tính/tháng | Trạng thái |
|---|---|---|---|
| AWS Organizations, SCP/RCP/tag/backup policy | Miễn phí | 0 | Dùng |
| IAM Identity Center | Miễn phí | 0 | Dùng |
| CloudTrail org trail (management event, bản đầu) | Miễn phí; chỉ trả S3 + KMS. Bản thứ hai 2 USD/100k event | 1–3 | Dùng; gỡ trail riêng của acc2 để tránh bản thứ hai |
| IAM Access Analyzer external | Miễn phí | 0 | Dùng |
| AWS Budgets | Budget thường miễn phí; budget có action: 2 cái đầu miễn phí, sau đó 0,10 USD/ngày mỗi cái | 0 | Dùng (không dùng action) |
| AWS Config (chỉ prod, ghi định kỳ) | Trả phí: 0,012 USD/CI định kỳ (0,003 liên tục) + 0,001 USD/rule eval | 10–30 | Chờ duyệt |
| GuardDuty | Trả phí | 20–60 (cả org) | Chờ duyệt |
| Security Hub CSPM | Trả phí + cần Config | 20–50 + Config | Chờ duyệt |
| Control Tower | Bản thân không thu phí, nhưng bật Config/CloudTrail ở mọi account được quản | 30–100+ (dev có nhiều ECS churn nên Config tăng) | Không khuyến nghị lúc này |
| Billing Conductor (nếu Billing Transfer) | Trả phí (chưa kiểm giá; thường do bên bill-transfer trả) | Hỏi TrueIDC/AWS | Hỏi |
| GitHub Team (nếu Infra/gốc thành private) | Trả phí | 4 USD/user | Quyết định ở mục 14 |
| Vercel Pro (staging + prod) | Trả phí | 20 USD/seat | Phase 5–6 |
| Khoá FIDO2 (2–4 cái) | Một lần | 50–150 USD một lần | Phase 1 |

_Nguồn: https://aws.amazon.com/controltower/pricing/ ; https://aws.amazon.com/config/pricing/ ; https://aws.amazon.com/cloudtrail/pricing/ ; https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/_

### Công kỹ sư một lần

| Phase | Ngày công | Ghi chú |
|---|---|---|
| 0 | 2 | ADR + sửa tài liệu + câu hỏi TrueIDC |
| 1 | 4–5 | Phần lớn là Terraform org/Identity Center/baseline |
| 2 | 1–2 | Cộng thời gian chờ AWS Support |
| 3 | 1–2 | Cộng thời gian chờ TrueIDC / ngày 1 của tháng |
| 4 | 12–18 | Phần lớn nhất: tách root accounts/aa365 |
| 5 | 6–8 | Seed secret, job scrub, E2E |
| 6 | 13–16 | Cùng việc go-live của app; thêm aa-backup |
| Tổng | 39–53 | Khoảng 3–4 tháng lịch tính cả thời gian chờ. Vận hành sau đó 2–4 ngày/tháng |

## 12. Vận hành

Mỗi việc vận hành có nhịp cố định, có vai trò chịu trách nhiệm và để lại bằng chứng. Runbook hiện có được thêm cột account/môi trường; thêm vài runbook mới cho mô hình nhiều account.

### Việc vận hành

| Việc | Nhịp | Vai trò chịu trách nhiệm | Công cụ / runbook | Bằng chứng |
|---|---|---|---|---|
| Release dev | Mỗi lần merge | Engineer | CI app | Run CI + smoke |
| Release staging | Theo đợt (hằng tuần); dựng staging trước nếu đang huỷ | Tech lead | workflow_dispatch(SHA) | Run + E2E |
| Release prod | Theo lịch, có cửa sổ | Tech lead duyệt | Environment prod + runbook prod-release | Phiếu duyệt GitHub + smoke |
| Thay đổi hạ tầng | Mỗi PR | Tech lead; thay đổi rủi ro có review độc lập | tf-plan/apply | Tóm tắt plan trong PR |
| Cảnh báo / trực | Liên tục | Engineer trực | prod: SNS → email nhóm + kênh chat + điện thoại (SEV1); staging/dev: email trong giờ làm việc | Bảng routing alarm |
| Sự cố / postmortem | Mỗi SEV1–2 | Tech lead | docs/ops/incident-response.md | Postmortem trong 5 ngày làm việc |
| Rà chi phí | Hằng tháng | Chủ doanh nghiệp + tech lead | Budget, Cost Explorer / Data Exports, llm_call_log | Báo cáo tháng |
| Rà quyền | Hằng quý | Tech lead; chủ doanh nghiệp ký | Xuất Identity Center | Biên bản |
| Diễn tập backup/DR | prod hằng quý; staging hằng tháng (tuỳ) | Tech lead | restore-rds-pitr, dr-cross-region-restore (cả restore từ aa-backup) | RTO ghi lại |
| Diễn tập break-glass | 6 tháng | Tech lead + chủ doanh nghiệp | break-glass | Biên bản |
| Drift Terraform | Hằng đêm | Engineer trực | tf-drift.yml | Issue/cảnh báo |
| Nâng Postgres 15 → 16/17 | Một lần trong 2027 (PG 15 hết hỗ trợ cộng đồng 11/2027) | Tech lead | RDS Blue/Green, diễn tập trên staging trước | Biên bản nâng cấp |
| Patch image, dependency | Dependabot hằng tuần; build lại base image hằng tháng | Engineer | CI | PR |
| Nâng Terraform/provider | Hằng tháng, dev → staging → prod | Engineer | tf-plan | PR |
| Gia hạn chứng chỉ | Tự động (ACM, DNS validation); alarm 30 ngày trước hạn | Engineer trực | ACM | Alarm |
| Xoay secret | RDS master: lúc go-live rồi hằng năm; DSN app: 90 ngày (rotation khi được); GitHub App key: hằng năm | Tech lead | secret-rotation | secrets-register |
| Vòng đời account | Khi cần | Tech lead | PR vào stack 10-organization; đóng: Suspended 90 ngày (chú ý giới hạn số account đóng mỗi 30 ngày) | PR |
| Rà runbook và tài liệu | 6 tháng | Người sở hữu ghi ở front-matter | docs lint | Ngày review |

### Runbook

| Runbook | Đã có? | Việc cần làm |
|---|---|---|
| break-glass | Có | Thêm root aa-management, IAM user break-glass, nhóm aa-breakglass-sso |
| db-migrate | Có | Thêm environment staging/prod |
| rollback-booking / cis / terraform / tp-lambda / vercel | Có | Thêm cột môi trường |
| restore-rds-pitr, restore-schema | Có | Thêm prod/staging |
| secret-rotation | Có | Thêm theo môi trường |
| ecs-exec-s3-mediated | Có | Profile mới, bucket theo account; ghi rõ không dùng cho prod |
| deploy-gate-override, incident-response | Có | Thêm prod |
| account-join (mời account có sẵn) | Mới | Theo mục 3 |
| account-create | Mới | PR vào 10-organization + 00-baseline của account mới |
| identity-center-access (cấp/thu quyền) | Mới | Ma trận ở mục 4 |
| scp-change | Mới | Policy-Staging → OU; kiểm giới hạn 5 SCP |
| state-split | Mới | Theo M4 |
| prod-release | Mới | Theo luồng promote |
| dr-cross-region-restore | Mới | Restore ở us-west-2 và từ aa-backup |
| staging-up-down | Mới | Dựng/huỷ staging, giữ snapshot |

## 13. Rủi ro và cách giảm

Rủi ro lớn nhất: quyền Claude/Bedrock phụ thuộc payer và Error 002; email root của acc2; việc tách state Terraform; và lộ state/plan trên repo public. Mỗi rủi ro có cách giảm và dấu hiệu nhận biết.

### Rủi ro

| Rủi ro | Khả năng | Ảnh hưởng | Giảm thiểu | Dấu hiệu / kiểm |
|---|---|---|---|---|
| Billing Transfer cho TrueIDC chặn Claude trên mọi account của org (TrueIDC không có giấy Anthropic) | Cao nếu chọn B1 mà AI ở trong org | Cao (pipeline nội dung dừng) | Hỏi TrueIDC câu 2; với B1 thì để AI đứng ngoài org; giữ đường API trực tiếp | Câu trả lời của TrueIDC; gọi thử |
| Error 002 không gỡ được trên account AI | Trung bình | Cao | Case Support; thẻ + FTU; API trực tiếp song song (S257 D) | Phản hồi của AWS |
| Account mới tạo cũng dính Error 002 | Trung bình | Trung bình | LLM chỉ chạy ở aa-shared-ai; không cần Bedrock ở staging/prod | — |
| acc2 bị khoá AI (Cohere Embed v4) sau khi rời TrueIDC | Trung bình | Trung bình (tìm kiếm ngữ nghĩa, lọc CRM) | Gọi thử trước/sau; chuyển embedding sang aa-shared-ai hoặc API trực tiếp | Smoke bước 16 |
| Email root acc2 do TrueIDC giữ | Không rõ | Rất cao (mất quyền root sau khi rời) | Đổi email root trước khi rời (câu hỏi 4) | Account settings |
| Mất lịch sử Cost Explorer | Cao | Thấp–trung bình | Xuất 13 tháng và hoá đơn trước khi rời | File đã lưu |
| Mất Lift credit 249.94 USD | Trung bình | Thấp | Hỏi AWS Support; dùng trước; chọn thời điểm chuyển | Trang Credits |
| Downtime khi chuyển org | Thấp | Trung bình | Resource không dừng; SCP gắn dần từ OU Transitional; thử ở Policy-Staging | Smoke sau chuyển |
| TrueIDC không cho rời org hoặc có điều khoản | Trung bình | Trung bình | Mô hình hybrid D; không ép hợp đồng | Trả lời của TrueIDC |
| Kế toán không chấp nhận hoá đơn USD không có VAT (mô hình A) | Không rõ | Trung bình | Hỏi kế toán ở phase 0; B1/D giữ hoá đơn TrueIDC | Ý kiến kế toán |
| Billing Transfer làm mất anomaly, chỉ còn pro-forma, phát sinh phí Billing Conductor | Cao nếu chọn B | Thấp | Budget theo account; hỏi bên bill-transfer về cảnh báo | — |
| Tên miền duy nhất (Cognito, API GW, CloudFront) trùng giữa account | Cao nếu dời | Cao | Không dời tên dev; staging/prod dùng tên mới; tạo bản ghi A cho domain cha | Plan báo lỗi trùng |
| Tách state sai làm xoá resource | Thấp | Rất cao | import/removed block, state mv cho loại không import được, plan 0 thay đổi, deletion_protection, prevent_destroy, version state | plan_guard |
| State hoặc plan lộ secret trên repo public | Trung bình | Cao | Không upload plan; plan prod/org cần reviewer; role plan chỉ ở account tương ứng; xoay secret trước go-live | Rà workflow |
| Ghi nhầm account (đã xảy ra 2 lần) | Trung bình | Cao | allowed_account_ids với account_id trong tfvars; default chỉ đọc; profile ghi rõ account | Test ở phase 4 |
| Mất quyền vào management | Thấp | Rất cao | 2 FIDO2, IAM user break-glass, email nhóm, diễn tập | Diễn tập 6 tháng |
| Identity Center hỏng hoặc region us-west-1 có sự cố | Thấp | Cao | Break-glass ngoài Identity Center | Diễn tập |
| Vượt giới hạn 5 SCP mỗi đích khi thêm policy | Trung bình | Thấp | Gộp policy; kiểm trong CI | Script đếm |
| RCP chặn GitHub OIDC / CloudFront / Bedrock batch | Trung bình | Cao | Miễn trừ AssumeRoleWithWebIdentity, PrincipalIsAWSService, account AI ngoài org; thử ở Policy-Staging | Test phase 7 |
| Mất cổng duyệt prod khi repo thành private trên GitHub Free | Cao (kế hoạch private từ 11/2026) | Cao | GitHub Team hoặc giữ Infra public | Rules của environment |
| Chi phí tăng ngoài dự kiến | Trung bình | Trung bình | Budget từng account; staging huỷ khi rảnh; dịch vụ trả phí chờ duyệt | Báo cáo tháng |
| shared-services sự cố ảnh hưởng mọi môi trường (ECR, artifact) | Thấp | Cao | Replication ECR sang aa-prod; state không còn ở shared; IAM chặt | — |
| Quota thấp ở account mới (Lambda concurrency, Fargate vCPU, SES sandbox) | Cao | Trung bình | Xin tăng quota ngay khi tạo account, ít nhất 2 tuần trước go-live | Service Quotas |
| ID ghi cứng (account, Cognito pool/client) làm staging hỏng | Cao | Trung bình | M6 + chuyển sang config trước phase 5 | grep = 0 |
| Dữ liệu cá nhân người VN lưu ở Mỹ chưa có hồ sơ theo luật VN | Không rõ | Cao (pháp lý) | Chủ doanh nghiệp hỏi tư vấn pháp lý trước go-live (chưa kiểm chi tiết) | Hồ sơ đã nộp/lưu |
| SCP region chặn Bedrock global inference hoặc dịch vụ global | Trung bình | Cao | Đối chiếu NotAction với trang AWS; 'unspecified' cho bedrock; thử ở Policy-Staging | Test phase 2–3 |

## 14. Việc cần chủ doanh nghiệp và tech lead quyết

Mỗi quyết định có phương án, khuyến nghị, ảnh hưởng chi phí và hạn. Quyết định về thanh toán, tên miền, kế toán và pháp lý thuộc về chủ doanh nghiệp; phần kỹ thuật thuộc về tech lead. Cuối mục có danh sách những gì công ty cần cung cấp (để gửi qua email) và bộ câu hỏi chi tiết.

### Quyết định

| Quyết định | Người quyết | Phương án | Khuyến nghị | Ảnh hưởng chi phí | Hạn |
|---|---|---|---|---|---|
| Chuyển sang mô hình nhiều account (thay một phần ADR 0012) | Tech lead + chủ doanh nghiệp | A. Giữ ADR 0012 (prod chung account infra); B. Org công ty + dev/staging/prod | B | Governance +10–30 USD/tháng; prod +10–30 USD/tháng phần nền; staging theo dòng dưới | Phase 0 |
| Mô hình thanh toán | Chủ doanh nghiệp | A trực tiếp / B1 Billing Transfer TrueIDC / D hybrid / B2 reseller khác (đường lùi) | Chọn theo bảng kịch bản ở mục 5 sau khi TrueIDC trả lời; không ký hợp đồng mới trừ khi buộc phải | Có thể có phí Billing Conductor | Phase 0 (trước khi AI vào org) |
| Hoá đơn AWS bằng USD không có VAT có dùng được không | Chủ doanh nghiệp + kế toán | Được (kê khai FCT) / Không | Hỏi kế toán; câu trả lời quyết định A có khả thi không | 0 | Phase 0 |
| Email root | Chủ doanh nghiệp | Hộp nhóm aws@adventure.asia + plus-addressing / info+aws-<tên>@adventure.asia | Hộp nhóm có 2 người đọc | 0 | Đầu phase 1 |
| Người giữ khoá break-glass | Chủ doanh nghiệp + tech lead | 1 người / 2 người | 2 người (tech lead + chủ doanh nghiệp) | 50–150 USD một lần | Phase 1 |
| Region của Identity Center | Tech lead | us-west-1 / us-west-2 | us-west-1 (cùng region workload). Đổi region sau này rất tốn công (trước đây phải xoá rồi tạo lại; kiểm tài liệu hiện hành) | 0 | Phase 1 |
| Control Tower | Tech lead | Dùng / Organizations + Terraform | Organizations + Terraform; giữ tên OU/account tương thích để bật sau | Tiết kiệm 30–100+ USD/tháng | Phase 1 |
| Staging | Chủ doanh nghiệp | Không có / huỷ khi rảnh / dừng tạm / bật liên tục | Huỷ khi rảnh | 15–30 / 90–130 / 150–200 USD/tháng | Phase 5 |
| Tên miền prod | Chủ doanh nghiệp | Sub-domain của tên miền công ty / thương hiệu mới | Sub-domain của tên miền công ty, uỷ quyền sang Route 53 ở aa-prod | Route 53 0.5 USD/zone | Đầu phase 6 |
| Dữ liệu cá nhân lưu ở Mỹ (us-west-1) | Chủ doanh nghiệp (tư vấn pháp lý) | Giữ us-west-1 + làm hồ sơ / chọn region khác cho prod | Giữ us-west-1, làm hồ sơ theo tư vấn (chưa kiểm chi tiết luật) | Tuỳ tư vấn | Trước phase 6 |
| Dịch vụ bảo mật trả phí | Chủ doanh nghiệp | Tắt hết / chỉ prod / toàn org | Tắt tới go-live; khi go-live bật GuardDuty + Security Hub (kèm Config) cho prod | 0 / khoảng 30–70 / 60–140 USD/tháng | Phase 6 |
| Repo private và GitHub Team | Chủ doanh nghiệp | Giữ Infra public / private + Team | Nếu private thì mua Team để giữ cổng duyệt prod | 4 USD/user/tháng | 11/2026 |
| Account AI vào org hay đứng ngoài | Tech lead (theo mô hình thanh toán) | Vào org / đứng ngoài + role cross-account | Theo bảng kịch bản ở mục 5 | Có thể mất tối đa 249.94 USD credit | Phase 2 |
| Một account AI chung hay mỗi môi trường một account | Tech lead | Chung / tách aa-prod-ai | Chung lúc này (account mới có thể dính Error 002); xem lại khi prod gửi PII qua LLM | 0 | Phase 6 |
| ECR trung tâm hay mỗi account một ECR | Tech lead | Trung tâm / riêng / trung tâm + replication | Trung tâm ở shared-services + replication sang aa-prod | 0–2 USD | Phase 4 |
| Terraform thuần hay Terragrunt | Tech lead | Thuần / Terragrunt | Thuần (xem lại khi > 60 root) | 0 | Phase 4 |

### Những gì cần công ty cung cấp hoặc chuẩn bị (gửi qua email)

| # | Hạng mục | Ai cung cấp | Khi nào |
|---|---|---|---|
| 1 | ID và email root của account quản trị vừa tạo (aa-management); xác nhận ai giữ MFA root | Tech lead + chủ doanh nghiệp | Ngay |
| 2 | Xác nhận email root và người giữ MFA root của account infra 005097885195 (có thể do TrueIDC giữ) và account AI 786888028788 | Chủ doanh nghiệp (hỏi TrueIDC) | Ngay |
| 3 | Tạo hộp thư nhóm aws@ (hoặc xác nhận dùng plus-addressing) làm email root cho các account mới | Chủ doanh nghiệp / quản trị mail | Phase 1 |
| 4 | Thẻ thanh toán công ty + thông tin thuế (tên, địa chỉ, mã số thuế) cho aa-management, account AI và khoảng thời gian account infra đứng riêng | Chủ doanh nghiệp | Phase 0–3 |
| 5 | Gửi TrueIDC 8 câu hỏi ở mục 5 và chuyển lại câu trả lời | Chủ doanh nghiệp | Phase 0 |
| 6 | Ý kiến kế toán: hoá đơn AWS bằng USD không có VAT (kê khai FCT) có dùng được không | Chủ doanh nghiệp / kế toán | Phase 0 |
| 7 | Giữ 1 khoá FIDO2 break-glass và cất mật khẩu root trong vault | Chủ doanh nghiệp | Phase 1 |
| 8 | Chọn tên miền prod và cho biết ai quản DNS của tên miền công ty | Chủ doanh nghiệp | Trước phase 6 |
| 9 | Ngày go-live dự kiến và tải dự kiến (số người dùng, đơn/ngày) để làm load test | Chủ doanh nghiệp | Trước phase 5 |
| 10 | Trần chi phí tháng cho từng môi trường và cho LLM | Chủ doanh nghiệp | Phase 0 |
| 11 | Danh sách người được truy cập (nhóm Identity Center) và kiểm toán viên (nếu có) | Chủ doanh nghiệp + tech lead | Phase 1 |
| 12 | Tư vấn pháp lý về lưu dữ liệu cá nhân khách hàng ở Mỹ | Chủ doanh nghiệp | Trước phase 6 |
| 13 | Duyệt riêng từng dịch vụ trả phí (GuardDuty, Security Hub, Config, Vercel Pro, GitHub Team) | Chủ doanh nghiệp | Khi tới phase tương ứng |

### Bộ câu hỏi cho chủ doanh nghiệp (trả lời theo từng mục)

| # | Câu hỏi | Lựa chọn đề xuất | Ảnh hưởng nếu chưa trả lời |
|---|---|---|---|
| 1 | Đồng ý chuyển sang mô hình nhiều account (dev/staging/prod riêng) thay cho prod chung account infra? | Đồng ý / Chưa | Không dựng được staging/prod theo thiết kế này |
| 2 | Ưu tiên giữ hoá đơn qua TrueIDC hay chấp nhận AWS tính tiền thẳng bằng thẻ? | TrueIDC (B1/D) / AWS trực tiếp (A) | Chưa đưa được account vào org |
| 3 | Nếu TrueIDC không bán được Claude: chấp nhận account AI tự trả bằng thẻ, đứng ngoài org? | Có / Không | LLM tiếp tục chỉ chạy qua API trực tiếp |
| 4 | Email nào làm email root cho các account? | aws@adventure.asia / khác | Chưa tạo được account mới |
| 5 | Ai giữ khoá break-glass thứ hai? | Chủ doanh nghiệp / người khác | Chỉ một người vào được root |
| 6 | Staging: huỷ khi rảnh, dừng tạm hay bật liên tục? | Huỷ khi rảnh / Dừng tạm / Liên tục | Chưa chốt được chi phí phase 5 |
| 7 | Tên miền prod là gì? | sub-domain của tên miền công ty / thương hiệu mới | Chưa xin được chứng chỉ, SES |
| 8 | Ngày go-live dự kiến và tải dự kiến? | Ngày + số người dùng | Chưa lên lịch phase 5–6 |
| 9 | Trần chi phí tháng (từng môi trường, LLM)? | Số USD | Budget dùng số đề xuất ở mục 4 |
| 10 | Bật dịch vụ bảo mật trả phí lúc go-live? | Có (chỉ prod) / Không | Prod chỉ có Prowler OSS + Access Analyzer |
| 11 | Infra/gốc có chuyển private từ 11/2026 không, có mua GitHub Team không? | Giữ public / Private + Team | Mất cổng duyệt prod nếu private mà không có Team |

## AI / LLM Gateway: sẵn sàng mọi đường truy cập, cắm là chạy

Gateway của CIS (`apps/AA-CIS-App/shared/llm_client`) đã có những phần khó nhất: model catalog trong DB, route theo stage (primary, fallback, shadow), cost log cho từng call. Nhánh S258 `feat/aa900-llm-availability` thêm phân loại lỗi (`access_denied` / `quota_exhausted` / `throttled`), `LLMAccessDenied` và thẻ LLM availability.

Chỗ còn thiếu nằm ở 'đường vào':
- Account Bedrock bị hard-code: `_SATELLITE_ACCOUNTS={'acc3'}`, `SERVING_ACCOUNTS=('acc3','acc2')`, CHECK `account_route='acc3'`.
- Key legacy `haiku`/`sonnet` (18 stage dùng làm primary) đi qua `_legacy_chain` với inference profile hằng số, hoàn toàn nằm ngoài catalog.
- OpenAI key được inject qua task definition.
- `model_key` gộp model với đường gọi.
- Chưa có api_style cho Anthropic API.

Từ 29/10 acc3 trả 'Error 002' cho mọi model. Hôm nay chỉ còn 7 stage có đường `gpt-6-luna-openai` (6 judge + `a3_place_dedupe`); writer Claude không còn đường nào.

Đề xuất: tách gateway thành 3 lớp dữ liệu.
- **Connection**: kind, account/region/role hoặc endpoint, tên secret, timeout, retry, hạn mức.
- **Deployment**: logical model × connection, gồm wire id, giá, priority.
- **Logical model**: tên model mà route dùng, kèm `capabilities`.

Khi đó thêm một đường mới thuộc kind đã có chỉ cần: tạo secret, thêm dòng connection, bấm Test, bật. Khoảng 30 phút, không deploy, **nhưng chỉ cho CIS**: TripPlanner và CRM cần S8. Thời gian chờ để tier/hạn mức của vendor tăng không tính vào 30 phút này. Chỉ khi có định dạng API mới hoặc một khả năng model chưa có cờ trong `capabilities` mới phải viết code. Các kind `bedrock`, `anthropic`, `openai` (gồm Azure/compatible), `mock`, cộng `typesafe` có sẵn cho Jev, phủ mọi đường đã biết.

Các phần giữ nguyên: fallback tự động có liệt kê trong route, cost log `shared.llm_call_log` (chỉ thêm cột nullable), route theo stage.

Ký hiệu: [M] = đo/đọc trong repo; [V] = kiểm trên tài liệu chính thức (audit S257 hoặc trang giá Anthropic ngày 29/10); [U] = chưa kiểm.

```text
apps/AA-CIS-App/shared/llm_client/   (mục tiêu; tách core `aa_llm` ở S8)
├── client.py                 route engine: logical model -> deployments -> adapter (dispatch theo api_style + kind)
├── connections.py            NEW registry + secret resolver (chỉ `aa-llm/`, base_url allowlist, TTL 15', đọc lại khi 401)
├── deployments.py            NEW logical model -> deployment list; alias legacy `haiku`/`sonnet`/`gpt-6-luna-openai`
├── breaker.py                NEW breaker + limiter (max_concurrency/rpm) + shared.llm_provider_health
├── errors.py                 AA-900 (+ spend-limit/billing Anthropic, 529 overloaded)
├── adapters/
│   ├── bedrock_converse.py   (từ client._call_bedrock_converse; + cachePoint; session theo connection)
│   ├── bedrock_invoke.py     (legacy anthropic_native, giữ trong giai đoạn chuyển)
│   ├── anthropic_messages.py NEW stream; output_config.format; effort; không forced tool / temperature
│   ├── openai_chat.py        (từ client._call_openai; cached_tokens; client theo connection)
│   └── mock.py               NEW
├── batch/  base.py · anthropic.py NEW · bedrock.py · openai.py NEW
├── embed.py                  (bỏ _acc2_client/account_for hard-code -> deployments)
├── pricing.py                calc_cost(deployment, usage): cache 5m/1h, batch, bậc >100K, geo
├── catalog.py · role_config.py · call_log.py (+ cache cols) · decide.py
api/migrations/ (CIS owner; copy ở AA-CIS-Infra db/migrations/cis/):
304 connection + deployment + CHECK provider/api_style/spend_budget · 305 alias legacy + role_config FK · 306 health · 307 allowed_scopes (backfill) · 308 cache cols log + rollup
```

### 1. Hiện trạng (code thật, 29/10/2026) và mục tiêu

| Hạng mục | Hiện trạng [M] | Mục tiêu | Slice |
|---|---|---|---|
| Đường vào LLM | Chỉ Bedrock acc3 (Error 002 với mọi model từ 29/10). OpenAI API là fallback cuối của 7 stage (`gpt-6-luna-openai`). Chưa có api_style cho Anthropic API (CHECK api_style không có giá trị này) | Mỗi đường là một dòng `shared.llm_provider_connection`, bật/tắt trong admin; nhiều đường cho cùng một model | S1, S2, S3 |
| Key legacy `haiku`/`sonnet` | `_call_key` → `_legacy_chain` → `_call_bedrock_satellite`/`invoke_claude` với `BEDROCK_SONNET`/`BEDROCK_HAIKU` cố định trên acc3. Không đi qua catalog. Dòng catalog `haiku`/`sonnet` (`anthropic_native`) chỉ dùng để lấy giá | Thêm dòng logical `sonnet-4-6`/`haiku-4-5` (Converse + Anthropic API). Key legacy thành alias, được trải ra deployment như mọi model khác | S3 |
| Account Bedrock | Hard-code `bedrock_satellite._SATELLITE_ACCOUNTS`, role `AA3-Bedrock-Invoker`, ExternalId `aa296-satellite-bedrock-acc3`, region us-west-1. `embed.py` có `_acc2_client` riêng. CHECK `llm_role_config.account_route IN (NULL,'acc3')` | Account, region, role ARN, ExternalId, kiểu auth nằm trong connection. Session STS cache theo (connection_key, role_arn, external_id, region) | S1, S3 |
| Credential | `OPENAI_API_KEY` inject qua task def (`modules/ecs/main.tf` dòng 600/824). Task role đã có `GetSecretValue` trên `*` (có Deny cho rds/db-migrator/booking/tripplanner). `shared/secrets.py` cache TTL 1 giờ | Gateway đọc secret `aa-llm/<env>/<connection_key>` lúc runtime (TTL 15 phút, đọc lại khi gặp 401, fail closed). Code + CHECK ép tiền tố `aa-llm/` và allowlist `base_url` theo kind, để một dòng sửa qua admin không lấy được secret khác | S1 |
| Catalog | `model_key` = model + đường. `bedrock_profile_ids` keyed theo account (TripPlanner SELECT cột này). CHECK provider ∈ {bedrock, openai, typesafe}; api_style ∈ {anthropic_native, converse, openai_chat, embed, decide}. Khả năng model chỉ có `supports_temperature`, `max_output_tokens` | Catalog = logical model, thêm `capabilities jsonb` (forced_tool, structured_output, thinking_mode, default_effort, prefill). Bảng mới `llm_model_deployment`. `bedrock_profile_ids` được ghi song song tới khi TP chuyển (S8) | S1, S3 |
| Routing | Route = danh sách `model_key`; mỗi model 1 account (`CatalogModel.account_for`). Dispatch theo `api_style` | Trải logical model ra các deployment đang bật (priority, bỏ deployment có circuit mở), rồi mới tới model kế tiếp | S3 |
| Chính sách | S235 hard-code (`_OPENAI_LAST_RESORT_ONLY`, `openai_platform_allowed`). Hôm nay 3 judge T-series (`t2_judge`, `t7_debate_judge`, `t10_judge`) đã có fallback OpenAI trực tiếp | `data_scope` của connection, `allowed_scopes` của stage, backfill từ route hiện tại (không đổi hành vi). Quyết định T-series ghi rõ ở bảng 11 | S5 |
| Phân loại lỗi | AA-900: `errors.classify`, `LLMAccessDenied` | Giữ nguyên. Thêm: lỗi spend limit / billing của Anthropic → quota; 529 overloaded → throttled. Breaker theo deployment | S0, S2, S4 |
| Timeout / retry | Bedrock acc2: read_timeout 300 giây, 2 attempt. OpenAI: mặc định SDK (600 giây, 2 retry), một attempt có thể chặn tới khoảng 30 phút | `timeout_s`, `max_retries` (0–1 cho 429) theo connection; tôn trọng `retry-after`; trần thời gian cho cả route | S2, S4 |
| Rate limit | Không có giới hạn đồng thời theo đường | `max_concurrency` / `rpm_limit` theo connection (token bucket trong process + đọc bảng health); wave pace theo đó | S4 |
| Health | Thẻ availability đọc `llm_call_log` + lỗi `shared.job` | `shared.llm_provider_health` + nút 'Test connection' | S4 |
| Cost log | `_normalize_model_provider` đoán provider theo chuỗi. `_call_openai` không đọc `cached_tokens` và ghi `account=None`. `calc_cost` theo chuỗi model; model lạ bị tính giá Sonnet. Chưa có cột cache. `tokens_in` của Converse = tổng prompt | Adapter truyền `provider`/`account=connection_key` tường minh. `calc_cost(deployment, usage)` gồm cache 5m/1h, batch, bậc dài Haiku 5.5, geo. Thêm cột cache vào log + rollup. `tokens_in` = tổng prompt trên mọi đường | S1, S6 |
| Ngân sách | `cost_guard.PROVIDERS` và CHECK `spend_budget_provider_check` = dfs/bedrock/openai/jev/geocoder | Thêm `anthropic`, `azure_openai`; budget theo connection | S1, S10 |
| Batch | `bedrock_batch.py` (Haiku v1, ≥100 record, chưa từng chạy live) | Interface chung; Anthropic Message Batches; giá batch ghi đúng vào log | S7 |
| Đa app | CIS: library. TP: fork, đọc `bedrock_profile_ids`/`account_route`, `SUPPORTED_ACCOUNTS=('acc3','acc2')`, env Lambda `BEDROCK_ACCT_PRIMARY`. CRM: gateway riêng. Booking: không gọi LLM | Library `aa_llm` vendored; TP/CRM chỉ được 'cắm không deploy' sau S8 | S8 |
| Prompt caching | Legacy `anthropic_native` có `cache_control`. Converse không gửi `cachePoint` (Luna tự cache) | Converse Claude có `cachePoint`; Anthropic API có `cache_control` (TTL 1 giờ = write 2x) | S6 |
| Admin UI | Settings › LLM models: Catalog, Routes, Shadow, Jev credit, availability (AA-900) | Tab Connections: thêm / Test / bật-tắt / priority / budget / hạn mức, ghi audit_log; chỉ admin staff | S4 |

### 2. Schema mục tiêu (CIS owner, `api/migrations/` từ 304)

| Bảng | Cột chính | Vai trò | Tương thích ngược |
|---|---|---|---|
| `shared.llm_provider_connection` (mới) | `connection_key` PK; `kind` CHECK (bedrock, anthropic, openai, azure_openai, mock); `auth_mode` (assume_role, task_role, bedrock_api_key, api_key); `account_id`, `region`, `role_arn`, `external_id`; `secret_name` CHECK (NULL hoặc `LIKE 'aa-llm/%'`); `base_url` (code chỉ nhận host trong allowlist của kind); `data_scope` (aws_only, vendor_direct); `timeout_s`, `max_retries`, `max_concurrency`, `rpm_limit`; `enabled` (mặc định false); `monthly_budget_usd`; `notes`, `updated_by` | Đường vào: credential chỉ là tên secret; giới hạn kết nối | Seed `acc3` (enabled), `acc2` (embed), `openai-direct` (secret `aa-cis/dev/openai-key` theo trạng thái hiện tại; ngoại lệ tiền tố được ghi rõ, hoặc copy sang `aa-llm/dev/openai-direct`), `anthropic-direct` (tắt) |
| `shared.llm_model_catalog` (đã có) | Thêm `family`, `capabilities jsonb`. Mở rộng CHECK `provider` (+anthropic, azure_openai, mock) và CHECK `api_style` (+`anthropic_messages`, giữ chỗ `openai_responses`). `bedrock_profile_ids` vẫn được ghi (TP đang SELECT) | Logical model: vendor, giá list, khả năng | Mọi key hiện có vẫn chạy. Thêm `sonnet-4-6`, `haiku-4-5` (Converse). `haiku`/`sonnet`/`gpt-6-luna-openai` thành alias |
| `shared.llm_model_deployment` (mới, tạo ngay ở S1) | `model_key` FK, `connection_key` FK, `wire_id`, `priority`, `enabled`, `price_*_override` (gồm `price_cache_write_1h`), `batch_capable`, `request_defaults jsonb` (effort, output_dimension cho embed) | Model × đường | Backfill từ `bedrock_profile_ids`, các dòng `openai`, và profile hằng số của key legacy |
| `shared.llm_role_config` (đã có) | Bỏ CHECK `account_route='acc3'`, thay bằng FK tuỳ chọn tới connection. Thêm `allowed_scopes text[]` (backfill: 7 stage đang có `gpt-6-luna-openai` → {aws_only, vendor_direct}; còn lại {aws_only}) | Route theo stage + chính sách dữ liệu | Hành vi giữ nguyên sau migration. TP chỉ hiểu `acc3`/`acc2` (giá trị khác bị bỏ qua, không lỗi) |
| `shared.llm_provider_health` (mới) | `connection_key`, `model_key`, `last_ok_at`, `last_error_at`, `last_error_class`, `consecutive_failures`, `circuit_open_until` | Breaker dùng chung giữa các task | Bảng rỗng thì không ảnh hưởng gì |
| `shared.llm_call_log` + `shared.llm_call_daily` | Log: thêm `cache_read_tokens`, `cache_write_tokens`, `pricing_mode` (sync/batch) nullable. Rollup: thêm tổng cache. `account` = `connection_key` | Cost ledger | Cột nullable. Sửa `record_call*`/`_INSERT_SQL`/`billed_record`; INSERT của TP vẫn hợp lệ (cột NULL) |

### 3. Các kind provider: credential, bật/tắt, health, cost log

| Kind / biến thể | Cấu hình trong connection | Credential (Secrets Manager, acc2) | Cách bật | Health / lỗi | Cost log (`provider` / `account`) | Code hôm nay [M] |
|---|---|---|---|---|---|---|
| `bedrock` · assume_role (acc3, account LLM trong Org mới) | `account_id`, `region`, `role_arn`, `external_id`. Inference profile ở deployment (`global.` / `us.` / regional; regional/geo +10% so với global [V]) | Không có secret (STS) | Connection + deployment `enabled`. Điều kiện: đã nộp form FTU của Anthropic; lần invoke đầu tự subscribe Marketplace, nên principal cần `aws-marketplace:Subscribe/ViewSubscriptions` hoặc admin gọi trước [U]; SCP không chặn marketplace hay các region đích của profile [U] | Breaker theo `errors.classify`. Test bằng 1 call thật (`GetFoundationModelAvailability` có thể báo sai [S257]) | `bedrock-satellite` / `<connection_key>` | Có, chỉ acc3, hard-code |
| `bedrock` · bedrock_api_key (account của reseller/đối tác) | `region`, wire id | `aa-llm/dev/bedrock-<conn>` [U: key dài hạn gắn với IAM user của account cấp key; AWS khuyên dùng key ngắn hạn] | Như trên | Như trên | `bedrock-satellite` / `<connection_key>` | Chưa có |
| `bedrock` · task_role (acc2 native) | `region` | Không cần | Như trên | Như trên | `bedrock-native` / `acc2` | Có, chỉ embed Cohere (`embed._acc2_client`, 1 attempt) |
| `anthropic` · direct | `base_url` (allowlist `api.anthropic.com`), workspace, `timeout_s`, `max_retries`, hạn mức | `aa-llm/dev/anthropic-direct` | Connection + deployment `enabled`. Spend limit đặt ở workspace. Tier Start: 1.000 RPM / 2M ITPM / 400K OTPM, mỗi họ model một bucket [V audit] | Spend limit → quota; 429 → throttled (theo `retry-after`); 529 overloaded → throttled. KHÔNG bật `fallbacks` phía server (đổi model ngầm) | `anthropic` / `anthropic-direct`; `tokens_in` = input + cache read + cache write | Chưa có (api_style `anthropic_messages`, SDK `anthropic` chưa có trong requirements) |
| `anthropic` · Claude Platform on AWS / Foundry / Vertex | `base_url` / resource / project + region | `aa-llm/dev/anthropic-<variant>` (Vertex dùng ADC/SA của GCP) | Như trên | Như trên | `anthropic` / `<connection_key>` | Chung adapter, chỉ khác hàm tạo client (`AnthropicFoundry`, `AnthropicVertex`) |
| `openai` · direct | `base_url` (allowlist `api.openai.com`), `timeout_s`, `max_retries` | `aa-llm/dev/openai-direct` | Connection + deployment; `data_scope=vendor_direct` | `insufficient_quota` → quota; rate 429 → throttled | `openai` / `openai-direct`; đọc `prompt_tokens_details.cached_tokens` | `_call_openai` (Chat Completions, không stream, client tạo một lần từ env, mặc định SDK 600 giây / 2 retry, không đọc cached_tokens, account=None) |
| `azure_openai` (tuỳ chọn) | endpoint, `api_version`; deployment name = wire id | `aa-llm/dev/azure-openai-<name>` | Như trên | Như trên | `azure_openai` / `<connection_key>` | Chưa có (~0,5 ngày) |
| `openai` · compatible (chỉ khẩn cấp) | `base_url` (phải nằm trong allowlist) | `aa-llm/dev/<name>` | Chỉ cho stage có `vendor_direct` | Mức hỗ trợ strict json_schema khác nhau → dễ ra billed_unusable | `openai` / `<connection_key>` | Chung adapter |
| `mock` | Không có | Không có | Chỉ env dev/test | — | `mock` (cost 0) | CRM `StubProvider`; CIS `services/golden_set/llm_guard.py` |
| `typesafe` (Jev) | Như hiện nay | `aa-cis/dev/typesafe` | Như hiện nay | Breaker trong process (`decide.jev_breaker_open`, 15 phút): mẫu máy trạng thái; trạng thái dùng chung đặt ở bảng health | `typesafe` | Có |

### 4. Logical model và wire id theo từng đường

| Logical model | Bedrock (acc3, account LLM mới) | Anthropic API | OpenAI API / Azure | Giá list in/out USD/MTok (first-party) [V 29/10] | Stage đang dùng [M] | Ghi chú |
|---|---|---|---|---|---|---|
| `sonnet-5-5` | `global.anthropic.claude-sonnet-5-5` | `claude-sonnet-5-5` | — | 2 / 10; cache read 0,10 (0,05x); write 2,50 (5m) / 4 (1h) | `s1_generate`, `supply_content_writer` | Catalog Bedrock ghi cache read 0,2; giá Bedrock là giá đối tác, phải đối chiếu trang giá AWS. Không cho forced tool_choice, không cho temperature khác mặc định; effort mặc định `high` |
| `haiku-5-5` | `global.anthropic.claude-haiku-5-5` | `claude-haiku-5-5` | — | 0,10 / 0,50 (≤100K); 0,50 / 2,50 (>100K) | — | Effort mặc định `medium`; thinking adaptive bật mặc định. Tokenizer mới (+~30% token) |
| `opus-5-5` | `global.anthropic.claude-opus-5-5` | `claude-opus-5-5` | — | 4 / 20; cache read 0,20 | — | Không tắt được thinking; effort mặc định `medium` |
| `sonnet-5` | `global.anthropic.claude-sonnet-5` | `claude-sonnet-5` | — | 2 / 10 | — | Có trong catalog, bảng cũ bỏ sót |
| `sonnet-4-6` (alias của `sonnet` legacy) | `global.anthropic.claude-sonnet-4-6` | `claude-sonnet-4-6` | — | 3 / 15 | 12 stage (gồm `t2_generate`, `t9_write`, `tp_compose`, `tp_extract`) | Dòng Converse mới; key legacy trỏ vào đây ở S3 |
| `haiku-4-5` (alias của `haiku` legacy) | `global.anthropic.claude-haiku-4-5-20251001-v1:0` | `claude-haiku-4-5` | — | 1 / 5 | 13 stage | Cache tối thiểu 4.096 token [V]; context 200K |
| `gpt-6-luna` | `global.openai.gpt-6-luna` | — | OpenAI: wire của `gpt-6-luna-openai` / Azure: deployment | 0,1 / 0,5 (cache read 0,01) | validate + fallback judge | [U] model trên Bedrock và trên OpenAI API có giống hệt nhau không; kiểm bằng golden label trước khi coi là 'cùng model' |
| `gpt-5.6-luna` | `global.openai.gpt-5.6-luna` | — | [U] | 0,2 / 1,2 | Primary của mọi judge | — |
| `gpt-6-astra` | `global.openai.gpt-6-astra` | — | [U] | 10 / 50 | — | — |
| `cohere-embed-v4` | acc2 `us.cohere.embed-v4:0`; acc3 (`cohere-embed-v4-acc3`) | — | — | 0,12 / 0 | 4 stage embed | Gộp thành 2 deployment, cùng `output_dimension` (cột `vector(1536)`) và `input_type`. Không bao giờ fallback sang model embed khác |

### 5. Chính sách route và fallback theo nhóm stage

| Nhóm stage | Stage (hôm nay) | Thứ tự mục tiêu | Không bao giờ | Lý do |
|---|---|---|---|---|
| Writer chính | `s1_generate`, `supply_content_writer`, `t2_generate`, `t9_write`, `t8_angle_gen`, `s1_atom_writer` | Model của stage trên mọi đường theo priority (Bedrock → anthropic-direct) → model dự phòng cùng vendor đã liệt kê trong route | Vendor không phải Anthropic | Giữ văn phong: cùng model + cùng effort trên mọi đường (`request_defaults`) |
| Writer nhẹ / sửa | `s1_flag_fix`, `*_itinerary_nudge`, `t9_repair`, `a0_column_map` | `haiku-4-5` mọi đường → (sau eval R2) `haiku-5-5` | Như trên | Rẻ |
| Judge | `s1_judge`, `t2_judge`, `t7_debate_judge`, `t10_judge`, `writing_memory_*`, `*_brand_audit` | `gpt-5.6-luna` mọi đường → `gpt-6-luna` mọi đường (gồm openai-direct như hôm nay) | Anthropic | Tách vendor giữa writer và judge |
| Validate / extract | `s1_source_facts`, `a3_*` (gồm `a3_place_dedupe` đang có openai-direct), `t10_claims`, `t9_faq_*` | `gpt-6-luna` mọi đường → `haiku-4-5`/`haiku-5-5` mọi đường | — | ADR 0008 |
| Embed | `a3_place_embed`, `f10_embed`, `tp_*_embed` | `cohere-embed-v4` @acc2 → @acc3 | Model embed khác | Phải cùng vector space |
| Tenant-facing (T2, T7–T10) | Writer T-series chỉ `aws_only`. Judge T-series HÔM NAY đã có fallback openai-direct (S235) | Giữ đúng như hôm nay sau migration 307 (backfill). Mở rộng writer T-series sang vendor_direct chỉ khi duyệt (bảng 11) | Thêm vendor_direct mới mà chưa có quyết định | Terms tenant (`apps/AA-Partner/portal/app/terms/page.tsx:54-55`) chỉ ghi 'including Anthropic's Claude through AWS', không loại trừ đường khác; nên viết rõ hơn |
| TripPlanner | `tp_compose`, `tp_extract` | Như writer chính, `aws_only` tới khi review DPA. Chỉ chạy được trên đường mới sau S8 | `vendor_direct` khi chưa duyệt | PII ngẫu nhiên; fork TP chỉ biết acc3/acc2 |
| CRM | AA-964 | Bedrock qua role riêng của CRM, sau PII scrub | OpenAI, Jev, key do agency tự mang | ADR 0008a |
| Luật chung | Mọi route | (1) cùng model, đường khác theo priority; (2) bỏ deployment đang mở circuit; (3) model kế tiếp trong route; (4) hết đường → `LLMAccessDenied` hoặc lỗi thường. Trần thời gian cho cả route; không retry ẩn trong SDK khi gặp 429 | Fallback ngầm (kể cả `fallbacks` phía server của Claude API) | Mỗi fallback để lại `fallback_used`, `llm_route_used`, `account=connection_key` |

### 6. Hỗ trợ batch theo từng đường

| Đường | API batch | Giảm giá | Giới hạn / điều kiện | Lưu dữ liệu | Code hôm nay | Dùng cho |
|---|---|---|---|---|---|---|
| Bedrock (account của mình) | `CreateModelInvocationJob`, manifest S3 | ~50% với model hỗ trợ [U] | ≥100 record mỗi job Claude, service role + S3, bật theo account; [U] có hỗ trợ profile `global.` không | Bucket S3 của mình | `bedrock_batch.py` (chưa chạy live) | Wave lớn |
| Anthropic Message Batches | 1 HTTPS call | -50%, cộng dồn với caching [V] | ≤100k request / 256 MB, hết hạn 24 giờ, kết quả không theo thứ tự (khớp `custom_id`), mỗi batch trong 1 workspace; hàng chờ batch có rate limit riêng [V] | 29 ngày, không đủ điều kiện ZDR [V] | Chưa có | S1 rewrite, re-atomize, eval R2 |
| OpenAI Batch API | JSONL, cửa sổ 24 giờ | -50% [U] | Theo tier | [U] | Chưa có | Judge/validate hàng loạt |
| Azure OpenAI Global Batch | JSONL | ~-50% [U] | Theo deployment | [U] | Chưa có | Tuỳ chọn |
| Azure Foundry Claude | Không có Message Batches [V] | — | — | — | — | Chỉ call đồng bộ |
| Vertex Claude | Batch predictions [U] | [U] | [U] | [U] | — | Tuỳ chọn |

### 7. Dữ liệu, privacy, hợp đồng theo từng đường

| Đường | Dữ liệu ra khỏi AWS? | Training / lưu trữ | Hợp đồng / thanh toán | Hoá đơn VN | Việc cần làm trước khi bật |
|---|---|---|---|---|---|
| Bedrock trên account của mình, AWS tính tiền thẳng | Không (profile `global.` có thể chạy ở bất kỳ region thương mại nào của AWS) | Bedrock không dùng prompt để train | AWS Customer Agreement; thẻ USD; với Claude, payer không phải reseller hoặc là reseller có giấy phép Anthropic | Không có VAT điện tử VN [V audit] | Gỡ Error 002, nộp FTU, kiểm Marketplace/SCP, test bằng call thật |
| Bedrock qua reseller | Không | Như trên | Reseller phải là Anthropic Authorized Reseller cho VN (xin xác nhận bằng văn bản) | Có thể [U] | 6 câu hỏi cho reseller (S257) |
| Anthropic API | Có, sang Anthropic | Không train. Mặc định không lưu, trừ Covered Models (Fable/Mythos, 30 ngày), nội dung bị gắn cờ (≤2 năm) và batch (29 ngày) [V audit]. `inference_geo:"us"` x1,1 giá [V] | Commercial Terms + DPA; credit hết hạn sau 1 năm; Stripe USD; FCT gross-up; báo trước 30 ngày khi chấm dứt [V] | Không [U] | Quyết định S235 cho Claude, MST, auto-reload, spend limit cho workspace, giới hạn đồng thời theo tier |
| OpenAI API | Có, sang OpenAI | Không train dữ liệu API theo mặc định [U]; lưu ~30 ngày để giám sát lạm dụng [U] | Credit trả trước hoặc hoá đơn tháng [U] | Không [U] | Đang dùng làm fallback cuối cho 7 stage (S235) |
| Azure (Microsoft) | Có, sang Microsoft | Theo điều khoản Azure | Claude không mua qua CSP được [V]; GPT mua qua CSP được | Có thể (CSP VN) [U] | Chỉ khi cần thêm đường dự phòng cho GPT |
| OpenRouter / aggregator | Có, qua thêm một bên trung gian | Tuỳ upstream | Credit, phí ~5,5% [U] | Không | Chỉ khẩn cấp, `vendor_direct`, không dùng cho dữ liệu tenant |

### 8. Cắm một đường mới: checklist (mục tiêu ≤30 phút, không deploy app CIS)

| # | Bước | Ai | Thời gian | Bằng chứng |
|---|---|---|---|---|
| 0 | Điều kiện có một lần: đã merge S1–S4 (gồm alias key legacy ở S3) và apply S1-infra. S1-infra = thêm quyền AssumeRole cho `AA-LLM-Invoker` ở `accounts/aa365/bedrock_satellite_assume.tf`: statement riêng cho ARN acc3 + pattern `arn:aws:iam::*:role/AA-LLM-Invoker` kèm `aws:ResourceOrgID` cho Org mới. Không cần thêm GetSecretValue (đã có trên `*`) | Agent + tech lead (MFA) | Một lần | PR Infra, `terraform apply` |
| A1 | Đường API: tạo org/workspace + key, đặt spend limit + cảnh báo 50/75/90%, ghi lại tier/hạn mức hiện tại | Business owner + tech lead | 10 phút | Console vendor |
| A2 | Lệnh 1 dòng `aws secretsmanager create-secret --name aa-llm/dev/anthropic-direct --secret-string file://k.json --profile aa365-admin --region us-west-1`, rồi ghi vào `docs/security/secrets-register.md` | Tech lead / agent | 3 phút | ARN secret |
| A3 | Admin › Connections › Thêm: kind, `secret_name` (bắt buộc tiền tố `aa-llm/`), `base_url` (trong allowlist), `data_scope`, budget, `max_concurrency` theo tier | Tech lead (admin staff) | 3 phút | Dòng `acp_shared.audit_log` |
| A4 | Test connection: 1 call nhỏ mỗi deployment (stage `adhoc_conn_test`, role `validate`, < $0,001, ghi `llm_call_log`) | Tech lead | 2 phút | Thẻ health xanh |
| A5 | Bật deployment (đã seed giá + `capabilities`), đặt priority | Tech lead | 5 phút | Bảng route hiện đường mới |
| A6 | Theo dõi 15 phút: `llm_route_used`, `account=<connection_key>`, cost khớp giá | Agent | 15 phút | `llm_call_log` |
| B1 | Bedrock trên account mới: payer bán được Claude, FTU, subscribe Marketplace (lần invoke đầu, principal có quyền marketplace), SCP cho phép | Business owner | Ngoài khung 30 phút | Call thật thành công |
| B2 | Apply module `llm-invoker`: trust tới task role acc2 + ExternalId; invoke trên `inference-profile/*` của account đó, `arn:aws:bedrock:*::foundation-model/*` và `arn:aws:bedrock:::foundation-model/*` | Tech lead (MFA) | 10 phút | `terraform apply` |
| B3 | Thêm connection → Test → bật deployment | Tech lead | 10 phút | Như A4–A6 |
| C | Kind API mới, hoặc model mới cần khả năng chưa có cờ trong `capabilities` (vd. Responses-only): phải viết code | Agent | 1–2 ngày | PR + test hợp đồng |
| D | TripPlanner / CRM dùng đường mới: chỉ sau S8 (trước đó phải deploy app) | Agent | — | — |

_Đánh đổi ở B2: invoker cho phép mọi model trong account; việc chặn model chưa duyệt dựa vào catalog `enabled` + Budgets + SCP. Gateway không bao giờ gọi wire id nằm ngoài catalog. Rủi ro ngược lại nằm ở connection sửa được qua admin, nên code ép tiền tố secret, allowlist base_url và chỉ admin staff được sửa (có audit). '≤30 phút' là thời gian nối dây; thông lượng do tier của vendor quyết định._

### 9. Dùng chung cho nhiều app qua một gateway library

| App | Hôm nay [M] | Mục tiêu | Control plane | Ledger | Ràng buộc |
|---|---|---|---|---|---|
| CIS | `shared/llm_client` (3 seam `generate` / `decide` / `embed`) | Core `aa_llm` + control plane CIS | `shared.llm_*` | `shared.llm_call_log` | — |
| TripPlanner | Fork `backend/shared/llm_gateway.py`: SELECT `llm_role_config`/`llm_model_catalog` (đọc `bedrock_profile_ids`, `account_route`), `SUPPORTED_ACCOUNTS=('acc3','acc2')`, env `BEDROCK_ACCT_PRIMARY` | Vendor `aa_llm`; đọc config qua hợp đồng CIS (snapshot/endpoint) thay cho SELECT | CIS (đọc) | INSERT `shared.llm_call_log` (`quality_signal.app='tripplanner'`) | Tới S8: CIS phải ghi song song `bedrock_profile_ids`, không đổi tên/xoá cột TP đang đọc; kích thước package Lambda |
| CRM (AA-Partner) | Gateway riêng: scrub → budget → `ai_enabled` → call → `crm.llm_call` | Adapter `aa_llm` sau `Provider` Protocol | `crm.*` (ADR 0008a) | `crm.llm_call` | Chỉ Bedrock |
| Booking | Không gọi LLM | Khi cần: vendor library | — | — | — |
| Lựa chọn kiến trúc | (a) library vendored · (b) gateway service HTTP · (c) proxy có sẵn (LiteLLM…) | Chọn (a) bây giờ; (b) khi ≥3 app gọi thật hoặc cần key tập trung | — | — | (a) không thêm hop, $0. Ghi vào ADR 0009 |

### 10. Tối ưu chi phí

| Đòn bẩy | Áp dụng ở đâu | Ước lượng tiết kiệm | Điều kiện | Trạng thái |
|---|---|---|---|---|
| Chuyển key legacy sang model 5.5 | 13 stage `haiku` (4.5 $1/$5 → 5.5 $0,10/$0,50); 12 stage `sonnet` (4.6 $3/$15 → 5.5 $2/$10) | Tính cả tokenizer mới (+~30% token [V]): haiku ≈ -87%, sonnet ≈ -13% cho cùng văn bản; thinking adaptive mặc định làm tăng output, phải đo | Eval R2 đạt cho từng stage; đặt effort tường minh | Chưa. Đòn bẩy lớn nhất là nhóm haiku |
| Prompt caching | Converse Claude (`cachePoint`), Anthropic API (`cache_control`) | Cache read 0,1x (0,05x trên Sonnet/Opus 5.5) [V]; write 1,25x (5m) / 2x (1h) | Prefix ≥ ngưỡng của model (512 / 1.024 / 4.096) [V] | Converse chưa gửi `cachePoint` |
| Batch | Wave S1 / atomize / eval | -50%; ~$25 cho một lần viết lại 810 tour [M audit] | Batch S1 đọc được writer v2; log `pricing_mode=batch` | Chưa có |
| Model rẻ cho judge | `gpt-6-luna` thay `gpt-5.6-luna` làm primary judge | ~50–60% chi phí judge | Hiệu chuẩn lại với golden label | Validate đã dùng |
| Effort | `output_config.effort` / Converse additional fields | Giảm token thinking ở stage nhẹ | Eval; cùng giá trị trên mọi đường | Chưa |
| Circuit breaker | Mọi route | Bỏ các lần thử chắc chắn hỏng (AA-843: ~2.400 lần/tuần) | S4 | Một phần |
| Cache kết quả | Judge/validate có input không đổi (`request_sha256`) | Không trả tiền lại cho call trùng | Chỉ stage xác định | Chưa |
| Ngân sách | Theo tenant / connection / workspace vendor | Chặn chi phí đột biến | S10 | Một phần |
| Shadow chỉ khi A/B | `shadow_sample_pct` | — | 0% ngoài đợt A/B | Đang áp dụng |
| Sửa cost parity | `_call_openai` đọc `cached_tokens`; `calc_cost` theo deployment (cache 1h, batch, bậc >100K, geo); model lạ phải fail/cảnh báo thay vì lấy giá Sonnet | Log khớp hoá đơn | S6 | Chưa |
| Đối soát chi phí | Usage & Cost API (Admin key) / OpenAI usage / CE | Phát hiện log lệch | Admin key là secret quyền cao: workspace riêng, chỉ đọc | Chưa |

### 11. Quyết định cần tech lead / business owner duyệt

| Quyết định | Đề xuất | Hệ quả nếu không duyệt |
|---|---|---|
| Sửa S235 ('chỉ Bedrock') cho Claude | Cho phép `vendor_direct` (Anthropic) làm đường dự phòng cho writer/validate | Writer Claude không còn đường nào khi Bedrock bị chặn |
| T-series và vendor_direct | Ghi nhận rằng judge T-series đã dùng OpenAI API làm fallback từ S235. Quyết định có mở thêm cho writer T-series không | Migration 307 backfill giữ nguyên hiện trạng; writer T-series chỉ `aws_only` |
| Sửa terms tenant | Ghi rõ: 'through Amazon Web Services or directly from the model vendor (Anthropic, OpenAI)' | Câu hiện tại chỉ nêu Claude qua AWS; mâu thuẫn với fallback OpenAI đang có |
| Thanh toán vendor | Credit trả trước + auto-reload, thẻ công ty, MST, hỏi kế toán về FCT | Hết credit thì đường đó down (route vẫn fallback) |
| Account LLM trong Org mới | Member account `llm` do payer của mình tính tiền; acc3 là đường thứ hai | Tiếp tục phụ thuộc case Error 002 |
| IAM invoker wildcard theo model | Đồng ý (governance qua catalog + Budgets + SCP) | Mỗi model mới cần một PR IAM |
| Giữ tắt `fallbacks` phía server của Claude API | Đồng ý (ADR 0005 §4) | Đổi model ngầm, cost ghi sai model |
### Các lát xây LLM gateway (theo thứ tự)

| Lát | Repo | File | Migration | Test | Công | Rủi ro |
|---|---|---|---|---|---|---|
| S0: Merge nhánh AA-900 (`feat/aa900-llm-availability`) | AA-CIS-App | shared/llm_client/errors.py, client.py, shared/jobs/worker.py, api/services/llm_availability.py, frontend/app/admin/settings/LlmAvailabilityCard.tsx | Không | tests/unit/test_aa900_llm_access_denied.py, test_aa900_llm_availability.py, integration test_aa900_llm_availability_sql.py | 0,5 ngày | Thấp-trung bình: đổi cách worker retry |
| S1: Connection registry + bảng deployment (schema + backfill) + mở CHECK, mọi đường mới ở trạng thái tắt, không đổi hành vi | AA-CIS-App (+ bản copy ở AA-CIS-Infra db/migrations/cis) | api/migrations/304_llm_connection_deployment.sql; shared/llm_client/connections.py (resolver qua shared/secrets._fetch_secret_sdk, ép tiền tố `aa-llm/`, allowlist base_url theo kind, fail closed); deployments.py (chỉ đọc); call_log: provider/account truyền tường minh; shared/cost_guard.py PROVIDERS += anthropic, azure_openai; admin_llm_ops.py GET /admin/llm-connections (chỉ đọc) | Có (304): `llm_provider_connection` (CHECK kind, secret_name `aa-llm/%`), `llm_model_deployment` (backfill từ `bedrock_profile_ids`, các dòng openai, profile hằng số của key legacy), `capabilities jsonb`; CHECK provider += anthropic, azure_openai, mock; CHECK api_style += anthropic_messages, openai_responses; `spend_budget_provider_check` += anthropic, azure_openai; grant cis_app. Giữ `bedrock_profile_ids` (TP SELECT) | Unit: resolver từ chối secret ngoài `aa-llm/` và base_url ngoài allowlist; integration SQL: CHECK, backfill khớp snapshot llm-routes; regenerate docs/generated/llm-routes.md | 2 ngày | Thấp: chỉ thêm, chưa có code đọc deployment trên đường chạy |
| S1-infra: Quyền AssumeRole cho invoker theo Org + module llm-invoker (không cấp thêm quyền đọc secret) | AA-CIS-Infra | accounts/aa365/bedrock_satellite_assume.tf (giữ statement ARN acc3; thêm `arn:aws:iam::*:role/AA-LLM-Invoker` với `aws:ResourceOrgID` của Org mới); modules/llm-invoker/ (role + trust ExternalId; invoke `inference-profile/*`, `arn:aws:bedrock:*::foundation-model/*`, `arn:aws:bedrock:::foundation-model/*`; tuỳ chọn quyền marketplace subscribe) | Không | terraform plan chỉ có thêm; `iam simulate-principal-policy` cho AssumeRole | 0,5–1 ngày | Trung bình (IAM): subagent review độc lập; apply cần MFA |
| S2: Adapter Anthropic Messages (direct; Platform on AWS / Foundry / Vertex qua factory) | AA-CIS-App | shared/llm_client/adapters/anthropic_messages.py (stream, output_config.format thay forced tool, effort từ request_defaults, không temperature, tokens_in = input + cache, ghi response.model, không bật `fallbacks`); client dispatch theo `api_style=='anthropic_messages'`; requirements.txt pin `anthropic` (và pin `openai`); errors.py: spend-limit/billing → quota, 529 → throttled, tôn trọng retry-after; timeout/max_retries theo connection; services/golden_set/llm_guard.py ENTRY_POINTS | Không (deployment đã có từ S1) | Unit với client giả: stream delta, structured output, mapping usage/cache (cộng vào tokens_in), refusal, 429/529/spend-limit → classify, không gửi temperature/forced tool cho Sonnet/Opus 5.5; contract test bằng key thật ≤ $0,01 (stage adhoc) | 2,5–3 ngày | Trung bình: thêm một bên xử lý dữ liệu; vẫn tắt tới khi có connection + key; refusal tính tiền |
| S3: Route trải deployment + alias key legacy + bỏ hard-code account (gồm embed) | AA-CIS-App | api/migrations/305_llm_legacy_alias_role_fk.sql; deployments.py; client._call_route/_call_key (key legacy → logical `sonnet-4-6`/`haiku-4-5` qua Converse/Anthropic; giữ `_legacy_chain` sau cờ để rollback); bedrock_satellite.py (session theo connection, khoá cache gồm role_arn/external_id/region); catalog.SERVING_ACCOUNTS → registry; embed.py (bỏ `_acc2_client`/`account_for`, giữ output_dimension/input_type); admin route editor hiện các đường | Có (305): dòng catalog `sonnet-4-6`/`haiku-4-5` (Converse, giá, capabilities); alias `haiku`/`sonnet`/`gpt-6-luna-openai`; thay CHECK `account_route='acc3'` bằng FK tới connection (dữ liệu hiện tại vẫn hợp lệ). Vẫn ghi song song `bedrock_profile_ids` cho TP | Unit: thứ tự trải (cùng model trước), bỏ deployment tắt/đang mở circuit, alias cho kết quả gọi y hệt, embed giữ dimension; integration: snapshot llm-routes; test vendor rule; 3 tour live cho stage legacy writer | 3,5 ngày | Cao (lõi route; structured output S251 của key legacy chuyển từ schema trong prompt sang tool/output_config): review độc lập, shadow 1 stage validate trước, cờ rollback |
| S4: Breaker + limiter + bảng health + tab Connections | AA-CIS-App | shared/llm_client/breaker.py (máy trạng thái theo mẫu Jev, trạng thái trong DB; limiter max_concurrency/rpm); api/migrations/306_llm_provider_health.sql; admin_llm_ops.py (POST test-connection, PATCH connection chỉ admin staff, audit_log); api/services/llm_availability.py theo connection; frontend/app/admin/settings/ConnectionsTab.tsx (kit, EN mặc định) | Có (306): `shared.llm_provider_health` | Unit: chuyển trạng thái theo class, limiter; PATCH từ chối secret/base_url sai; test-connection ghi `llm_call_log` (stage `adhoc_conn_test`, role validate); UI smoke + screenshot (aa-ui-verify) | 3 ngày | Trung bình: breaker mở nhầm → half-open 1 request, thời gian mở ngắn; PATCH connection là bề mặt nhạy cảm (secret/base_url) |
| S5: Chính sách thành dữ liệu (`data_scope` / `allowed_scopes`), không đổi hành vi | AA-CIS-App (+ ADR 0009 ở repo gốc) | admin_llm_ops.py (`_OPENAI_LAST_RESORT_ONLY` → kiểm theo scope); client.openai_platform_allowed → kiểm theo scope; role_config.py; client._call_route lọc theo scope; docs/adr/0009-model-gateway-connections.md | Có (307): `llm_role_config.allowed_scopes text[]`; backfill {aws_only, vendor_direct} cho 7 stage đang có `gpt-6-luna-openai` (gồm t2/t7/t10 judge, a3_place_dedupe), {aws_only} cho các stage còn lại | Viết lại tests/unit/test_s235_openai_last_resort.py theo scope; snapshot: route hiệu lực trước và sau migration giống hệt | 1,5 ngày | Trung bình (chính sách): tech lead duyệt trước khi mở thêm vendor_direct |
| S6: Cost parity + prompt caching | AA-CIS-App | pricing.calc_cost(deployment, usage) (cache 5m/1h, batch, bậc Haiku 5.5 >100K, inference_geo, giá override; model lạ → cảnh báo + đánh dấu, không âm thầm lấy giá Sonnet); adapters/openai_chat đọc `cached_tokens`, ghi account; adapters/bedrock_converse gửi `cachePoint` khi ≥ ngưỡng; call_log + services/retention/rollups.py thêm cột cache | Có (308): `llm_call_log.cache_read_tokens`, `cache_write_tokens`, `pricing_mode` (nullable); `llm_call_daily` thêm tổng cache | Unit: bảng giá theo từng trường hợp; integration: rollup có cache; 3 tour thử đo cache hit và so cost với console vendor | 2 ngày | Thấp-trung bình: output không đổi; phải đối chiếu với hoá đơn |
| S7: Interface batch + Anthropic Message Batches + S1 batch đọc được writer v2 | AA-CIS-App | shared/llm_client/batch/{base,anthropic,bedrock,openai}.py; services/content_generation/s1_batch_v2.py; job kind submit/poll/ingest (không giữ lease deploy-blocking 24 giờ, ingest có checkpoint, khớp theo custom_id); registry call site (test_aa927 HELPER_NAMES) | Có thể: `shared.llm_batch` + dòng retention | Unit: kết quả không theo thứ tự, item errored/expired không tính tiền; ingest idempotent; báo cáo chi phí wave với `pricing_mode=batch` | 4 ngày | Cao: ngữ nghĩa job, ingest trùng; thang wave 3 → ≤50 → 1 nước |
| S8: Tách core `aa_llm`, vendor vào TripPlanner + CRM | AA-CIS-App + AA-TripPlanner-Web + AA-Partner | CIS: packages/aa_llm/ + script sync; TP: thay backend/shared/llm_gateway.py, đọc config qua hợp đồng CIS, bỏ `SUPPORTED_ACCOUNTS`/env account; CRM: adapter sau `Provider` Protocol, giữ thứ tự scrub → budget → ai_enabled | Không ở CIS; sau khi TP chuyển xong mới ngừng ghi `bedrock_profile_ids` | Bộ test hợp đồng chung cho 3 repo; TP smoke `tp_compose` live; test thứ tự gateway CRM | 3–4 ngày | Trung bình: package Lambda TP, ranh giới ADR 0008a |
| S9: Azure OpenAI / OpenAI-compatible + OpenAI key chuyển sang secret runtime | AA-CIS-App | adapters/openai_chat.py: factory client theo connection (OpenAI / AzureOpenAI / base_url trong allowlist), timeout/max_retries theo connection; bỏ client tạo một lần ở `LLMClient.__init__` | Không | Unit: chọn client theo kind; key từ resolver; env `OPENAI_API_KEY` chỉ còn là fallback | 0,5–1 ngày | Thấp |
| S10: Budget theo connection + đối soát chi phí nightly | AA-CIS-App | shared/cost_guard.py; job kind `llm_cost_reconcile` (Anthropic Usage & Cost API qua Admin key chỉ đọc, OpenAI usage, CE) so với llm_call_log; dòng trên Cost Ops | Có thể: bảng reconcile + retention | Unit tính lệch; integration SQL | 1,5 ngày | Thấp-trung bình (Admin key là secret quyền cao) |
| S11: Chuyển stage key legacy sang model 5.5, có eval chặn | AA-CIS-App | Đổi route bằng dữ liệu; eval R2 theo nhóm stage (đo cả token tăng do tokenizer/thinking); đặt effort trong `request_defaults`; cập nhật SAFE_DEFAULTS | Không | Eval R2 (AA-919) đạt ngưỡng; ghi run ID và $/tour | 1 ngày + eval trả phí (≤50 tour mỗi nhóm) | Trung bình: chất lượng văn bản; rollback bằng một lần sửa route |

## Phụ lục: chỉnh sửa của phản biện

### Quy hoạch tổ chức

- [Nghiêm trọng — thanh toán/LLM] Mục 5 khuyến nghị Billing Transfer cho TrueIDC cho cả org mà bỏ qua kết luận của audit S257 (docs/audits/2026-10-29-S257-llm-access-options/llm-vendor-recommendation.vi.md, angle1-aws-partners-vn.md). Ở đó ghi: Claude trên Bedrock chỉ chạy khi payer (reseller) có giấy bán lại của Anthropic, và không thấy dấu hiệu TrueIDC có giấy này. Một org chỉ có một bên bill-transfer, nên nếu chuyển cả org sang TrueIDC thì Claude có thể bị chặn trên MỌI account, kể cả aa-shared-ai (điểm này chưa kiểm với Billing Transfer). Đã viết lại mục 5 thành bảng kịch bản. Nếu đi B1 (Billing Transfer cho TrueIDC), account AI phải đứng ngoài org và tự trả bằng thẻ, hoặc LLM chạy qua API trực tiếp (phương án D của S257). Reseller khác có giấy Anthropic chỉ là đường lùi, không đề xuất hợp đồng mới.
- [Nghiêm trọng — thứ tự phase] Bản cũ đưa account AI vào org ở phase 2, trước khi chốt thanh toán (hạn 'trước phase 3'). Nếu đưa AI vào org trả thẻ rồi sau đó chuyển sang Billing Transfer với TrueIDC thì Claude lại gãy. Đã dời quyết định thanh toán lên phase 0. AI chỉ vào org khi mô hình cho phép (A hoặc D có AI trong org).
- [Nghiêm trọng — Bedrock] Error 002 là khoá ở cấp account phía AWS. Nó chặn mọi họ model, kể cả Amazon Nova và Cohere, và không do org gây ra (S257 angle2-alternatives.md §Error 002, re:Post). GetFoundationModelAvailability vẫn báo AUTHORIZED trên account bị khoá. Vì vậy vào org KHÔNG phải cách sửa. Cách sửa ngay trên account đứng riêng: gắn thẻ, nộp lại form FTU của Anthropic, giữ case Support. Chỉ tin khi một lệnh gọi model thật chạy được. Thêm hai rủi ro: account mới do Organizations tạo cũng có thể dính Error 002 (re:Post: account tạo cùng đợt), và acc2 có thể bị khoá AI (Cohere Embed v4) khi rời TrueIDC (S257 migration-summary.vi.md).
- [SCP] Không thể gắn DenyLeaveOrg ở Root mà vẫn chừa ngoại lệ cho OU Transitional, vì SCP gắn ở Root áp xuống mọi OU. Đã chuyển nó vào tài liệu aa-scp-baseline, gắn ở từng OU trừ Transitional và Suspended.
- [SCP] Mỗi đích (root/OU/account) gắn trực tiếp được tối đa 5 SCP, tính cả FullAWSAccess; mỗi policy dài tối đa 5.120 ký tự. Bản cũ gắn trực tiếp 7 SCP cho Prod. Đã gộp lại thành vài tài liệu và gắn theo tầng. Ghi rõ FullAWSAccess phải được gắn ở mọi tầng, vì quyền allow phải có ở từng cấp.
- [RCP] Nếu RCP trên STS bắt aws:PrincipalOrgID thì sẽ chặn sts:AssumeRoleWithWebIdentity của GitHub OIDC (principal federated, không thuộc org) và của Cognito identity pool. Cần miễn trừ các trường hợp này, cùng aws:PrincipalIsAWSService và account AI nếu nó đứng ngoài org (bucket bronze dùng cho Bedrock batch, accounts/acc3-bedrock/batch.tf).
- [Tag policy] Tag policy chỉ chuẩn hoá giá trị. enforced_for chặn giá trị sai, KHÔNG bắt phải có tag. Việc bắt có tag làm bằng default_tags + lint CI (checkov), và tuỳ chọn thêm SCP aws:RequestTag cho vài loại resource.
- [Break-glass] User aa-breakglass nằm trong Identity Center thì vô dụng khi chính Identity Center hoặc region của nó gặp sự cố. Break-glass thật gồm: root aa-management (2 FIDO2) và 1 IAM user break-glass trong aa-management (FIDO2, không access key, có cảnh báo; SCP không áp lên management). Nhóm Identity Center aa-breakglass chỉ dùng khi cấu hình IdP/nhóm bị sai.
- [Mâu thuẫn ADR 0012] Bản cũ cho AA-ProdOperator dùng 'SSM Session Manager' ở prod, trái ADR 0012 quyết định 4.4 (ECS exec tắt ở prod; muốn bật phải qua thay đổi Terraform break-glass do người làm). Đã bỏ quyền đó.
- [State Terraform] Bản cũ để state prod trong bucket chung ở shared-services. Cách này trái ADR 0012 quyết định 5 (prod có bucket riêng, chỉ role prod ghi) và nới rộng blast radius. Đã đổi sang mỗi account một bucket state. aa-dev giữ bucket có sẵn aa-cis-tfstate-005097885195 (không phải migrate bucket). Root acc3 giữ bucket aa-cis-tfstate-acc3-bedrock-786888028788 nhưng hiện KHÔNG có khoá (thiếu use_lockfile) và còn ghi cứng profile nghiep_aa365 (accounts/acc3-bedrock/versions.tf); phải sửa cả hai.
- [Terraform] Trong file -backend-config, assume_role của backend s3 viết dạng thuộc tính `assume_role = { role_arn = "..." }`, không phải block. Chuỗi OIDC → role A → assume role B là role chaining nên bị giới hạn 1h, và có thể hết hạn giữa chừng khi apply RDS lâu. Đã đổi: OIDC vào thẳng role Terraform của account đích (session 2h), backend đọc bucket state cùng account nên không assume chéo.
- [Terraform] Bài test 'plan stack prod bằng credential dev' sẽ fail ở AssumeRole (AccessDenied), không phải ở allowed_account_ids. allowed_account_ids chỉ có tác dụng khi account_id là hằng số trong terraform.tfvars của từng stack (không truyền từ CLI). Đã sửa kỳ vọng test.
- [Terraform] Bản cũ ghi 'khoảng 36 root', nhưng đếm thực tế ra 42, vượt chính ngưỡng 'xem lại Terragrunt khi > 40'. Bản sửa có 43 root (thêm aa-backup). Đã đặt lại ngưỡng và lý do.
- [Tách state] Import block không import được một số loại resource (tls_private_key, null_resource...). Với những loại đó phải dùng terraform state pull → state mv -state/-state-out → state push. Resource còn trong root cũ mà tham chiếu resource đã dời đi thì phải đổi sang data source/SSM TRƯỚC khi đặt removed. Đã thêm vào M4.
- [CI — repo public] AA-CIS-Infra đang public (gh api: visibility=public). Plan file lưu làm artifact thì ai đăng nhập GitHub cũng tải được, mà plan chứa giá trị nhạy cảm dạng rõ. Role plan tin pull_request thì bất kỳ người mở PR nào cũng sửa được workflow để đọc state. Đã bỏ việc lưu artifact plan (apply sẽ plan lại và so tóm tắt). Plan của prod/org chạy trong environment có reviewer.
- [Sự thật repo] Infra đã có các GitHub environment dev, dev-db-auto, prod, staging, đều không có reviewer (chỉ dev-db-auto có branch_policy). terraform-apply.yml và db-migrate.yml vẫn dùng `environment: prod` để apply Dev. Repo đang public nên bật required reviewer được ngay, miễn phí. Terraform pin đúng 1.15.5, provider aws ~> 6.69 (AA-846). GuardDuty nằm sau cờ var.guardduty_enabled (mặc định false). Trail aa-cis-dev-trail có bucket Object Lock GOVERNANCE 365 ngày: xoá trail được, nhưng bucket phải giữ tới hết hạn retention.
- [Chi phí] AWS Budgets: budget thường miễn phí; budget có action thì 2 cái đầu miễn phí, sau đó 0,10 USD/ngày mỗi cái (bản cũ ghi 0,02). AWS Config ghi định kỳ tốn 0,012 USD/CI, ghi liên tục 0,003 USD/CI. Security Hub CSPM bắt buộc phải có Config, nên ước tính phải cộng thêm Config.
- [Chi phí staging] Dev hiện có 51 secret (khoảng 20 USD/tháng). Tháng 10 có ALB 34, WAF 10, VPC/IPv4 công khai 10, ElastiCache 14.5 USD (Cost Explorer 1–28/10). Những thứ này không dừng khi đặt ECS desired=0, còn RDS đã stop sẽ tự bật lại sau 7 ngày. Vì vậy con số 'on-demand 60–90' quá lạc quan; thực tế khoảng 90–130. Đã thêm phương án staging 'huỷ khi rảnh' (destroy stack 40–60, giữ snapshot): khoảng 15–30 USD/tháng khi rảnh.
- [Chi phí prod] Số 400–550 của ADR 0012 tính cho prod dùng chung account với dev. Khi prod nằm ở account riêng thì phải cộng phần nền của account: KMS, WAF, secret, IPv4, log. Đã cộng thêm 10–30 USD/tháng.
- [Vercel] Dev hiện dùng gói Hobby (ADR 0012). Custom environment cần gói Pro và có giới hạn số lượng theo gói (cần kiểm). Đã đổi staging thành project riêng '<app>-staging' trong team Pro; Pro tính theo seat, không theo project.
- [Cognito/DNS] Custom domain của Cognito yêu cầu domain cha phải có bản ghi A, nên stg.lumiguides.it.com và <prod-domain> cần một bản ghi A. ACM cho Cognito/CloudFront phải nằm ở us-east-1 trong chính account đó. User pool không dời account được, nên người dùng phải đăng ký lại. Zone staging được uỷ quyền từ aa-dev, nên admin dev (kể cả agent) sửa được NS của staging: chấp nhận được với nonprod. Prod KHÔNG được phụ thuộc aa-dev.
- [Thiếu] Đã bổ sung: (1) backup sang account khác (aa-backup có vault lock; RDS phải mã hoá bằng CMK thì mới copy chéo account được); (2) chuyển dữ liệu cá nhân ra nước ngoài (us-west-1) theo luật VN: hồ sơ đánh giá tác động, chưa kiểm chi tiết, việc pháp lý do chủ doanh nghiệp quyết; (3) email root của acc2 có thể do TrueIDC giữ nếu account do họ tạo; (4) RAM share và điều kiện org trong resource policy (đã grep: không có PrincipalOrgID hay o-cnvpmom3os trong Terraform); (5) quota account mới (Lambda concurrency có thể chỉ 10, Fargate, SES sandbox); (6) danh sách trusted access cần bật; (7) giới hạn đóng account; (8) OIDC sub dựa trên tên repo (org đã đổi tên 1 lần), cân nhắc dùng repository_id; (9) Lift credit có thể không trả được cho model bên thứ ba bán qua Marketplace.
- [Học từ repo cũ] AdventureAsia365/AA-Project-Infra thực ra KHÔNG có Terraform: scripts/terraform/modules chỉ có .gitkeep, hạ tầng dựng tay bằng console và lưu bằng ảnh chụp. Repo đó dùng branch theo môi trường (develop/staging/main), trái trunk-based ADR-2026-023. Bài học 'AA-DevOps thiếu iam:PassRole' không tìm thấy trong repo nên đã bỏ phần quy nguồn. Việc tên permission set không đổi được thì vẫn đúng. Đã thêm bảng 'học gì / không học gì'.
- [ECR] ECR trung tâm khiến prod phụ thuộc shared-services khi pull image. ADR 0012 quyết định 7 chọn copy theo digest. Đã giữ ECR trung tâm (build một lần) và thêm registry replication sang aa-prod, để prod pull từ registry của chính nó.
- [Tài liệu cần sửa] Bổ sung vào danh sách: ADR 0001a (mô hình 2 account), Infra CONTEXT.md dòng 423 ('a new environment gets its own accounts/<name>/ root'), data standards C7.2c/C7.2d, handbook D-17. Số ADR kế tiếp đã xác minh là 0018 (docs/adr/README.md).
- [Cost Explorer] Trang chi phí theo app của CIS đang assume AA3-CostExplorer-Reader trên acc3 (accounts/acc3-bedrock/cost_explorer_reader.tf). Sau khi có org, KHÔNG nên cho workload assume vào management. Giữ reader theo từng account, hoặc dùng Data Exports đổ vào S3 ở aa-log-archive.
- [Không chắc chắn, đã ghi rõ] Một số điểm chưa kiểm nên để dạng câu hỏi: thời điểm Billing Transfer có hiệu lực, phí Billing Conductor, việc bên bill-source còn có Cost Anomaly Detection và kích hoạt được cost allocation tag hay không, khả năng đổi region của Identity Center (trước đây phải xoá rồi tạo lại), giới hạn custom environment của Vercel Pro.
- [Hình thức] Nội dung đã ở dạng bảng và tiếng Việt, đạt yêu cầu. Mục 14 thêm bảng câu hỏi cho chủ doanh nghiệp để trả lời yêu cầu 'chuẩn bị hết câu hỏi' (kế toán: hoá đơn USD của AWS không có VAT; pháp lý: dữ liệu ra nước ngoài; ID và email của account management mới).

### LLM gateway

- [Code, sai đường dẫn] Migration CIS nằm ở `apps/AA-CIS-App/api/migrations/NNN_*.sql`, không có `db/migrations/` trong AA-CIS-App. Bản copy y hệt nằm ở `infra/AA-CIS-Infra/db/migrations/cis/`. Số tiếp theo là 304 (schema reference ghi CIS mới nhất là 303, verified 2026-10-29). Phải kiểm lại số lúc mở PR vì các nhánh S258 có thể đã dùng 304.
- [Code, dispatch] `_call_catalog_model` rẽ nhánh theo `api_style` (`openai_chat` / `converse`), không theo `provider`. Nó raise với `anthropic_native`. CHECK `llm_model_catalog_api_style_check` hiện chỉ cho `anthropic_native, converse, openai_chat, embed, decide`. Vì vậy S1/S2 phải thêm một api_style mới (`anthropic_messages`) vào CHECK và dispatch theo api_style + kind của connection. Các dòng catalog Anthropic API mà audit S257 đề xuất với `api_style=anthropic_native` sẽ không gọi được.
- [Code, thiếu sót lớn] Các key legacy `haiku`/`sonnet` (18 stage dùng làm primary, 21 stage có dùng; trong đó có `t2_generate`, `t9_write`, `t8_angle_gen`, `s1_atom_writer`, `tp_compose`, `tp_extract`) đi qua `_legacy_chain` → `_call_bedrock_satellite` → `invoke_claude`, với inference profile hằng số `BEDROCK_SONNET`/`BEDROCK_HAIKU` trên acc3. Chúng không bao giờ đi qua catalog/Converse. Thiết kế connection/deployment như cũ không mở thêm đường nào cho các stage này. Phải thêm dòng catalog Converse `sonnet-4-6`/`haiku-4-5` và cho key legacy làm alias của chúng (cùng model nên không cần eval chất lượng, nhưng đổi hành vi structured output S251: từ schema chỉ nằm trong prompt sang forced tool / output_config). Việc này phải xong trước khi nói 'cắm là chạy'.
- [Code] Không chỉ judge còn đường `gpt-6-luna-openai`. Stage validate `a3_place_dedupe` cũng có (tổng 7 stage: `s1_judge`, `t2_judge`, `t7_debate_judge`, `t10_judge`, `writing_memory_eval`, `writing_memory_mine`, `a3_place_dedupe`). Catalog có 14 dòng, gồm cả `sonnet-5` mà bảng 4 bỏ sót.
- [Chính sách / migration] Hôm nay `t2_judge`, `t7_debate_judge` và `t10_judge` (thuộc T-series, tenant-facing) đã có fallback sang OpenAI API trực tiếp. Điều này mâu thuẫn với dòng 'T2, T7–T10 chỉ aws_only'. Nếu migration 307 đặt mặc định `allowed_scopes={aws_only}` cho mọi stage thì 7 stage trên sẽ âm thầm mất fallback OpenAI. Migration phải backfill `allowed_scopes` từ route hiện tại, và quyết định cho T-series phải ghi rõ. Trích dẫn terms cũng sai repo: đúng là `apps/AA-Partner/portal/app/terms/page.tsx:54-55`, và câu chữ là 'models from third-party providers, including Anthropic's Claude through Amazon Web Services' (liệt kê không loại trừ), không phải 'chỉ qua AWS'.
- [Infra, sai] Task role ECS đã có `secretsmanager:GetSecretValue` trên `Resource="*"` (`modules/ecs/main.tf` khoảng dòng 258), kèm Deny cho rds/db-migrator/booking/tripplanner. S1-infra không cần cấp thêm quyền đọc. Rủi ro thật ở chiều ngược lại: khi `secret_name` và `base_url` sửa được qua admin/DB, một dòng connection có thể khiến gateway đọc secret khác (typesafe, dataforseo, token social) rồi gửi nó làm API key tới một `base_url` tuỳ ý. Bắt buộc: CHECK + code ép `secret_name LIKE 'aa-llm/%'`, allowlist `base_url` theo kind (hằng số trong code), chỉ admin staff mới được PATCH, ghi audit_log.
- [Infra, sai chỗ] Quyền `sts:AssumeRole` của acc2 nằm ở `infra/AA-CIS-Infra/accounts/aa365/bedrock_satellite_assume.tf` (chỉ ARN role acc3), không nằm trong `modules/ecs/main.tf`. Nếu dùng `aws:ResourceOrgID` cho pattern `role/AA-LLM-Invoker` thì acc3 bị loại, vì acc3 không thuộc Org mới. Phải giữ statement riêng cho ARN acc3.
- [IAM Bedrock] Policy wildcard cho invoker ở account mới phải bao cả 3 dạng ARN đang dùng trên acc3: `arn:aws:bedrock:<region>:<acct>:inference-profile/*`, `arn:aws:bedrock:*::foundation-model/*` (profile địa lý `us.` route sang region khác) và `arn:aws:bedrock:::foundation-model/*` (profile `global.`). Thêm hai điều cần kiểm [U]: (a) lần invoke đầu một model Marketplace (Anthropic, OpenAI) tự subscribe, nên principal cần `aws-marketplace:Subscribe/ViewSubscriptions`, hoặc admin gọi trước một lần; (b) SCP của Org mới không được chặn `aws-marketplace:*` hay các region mà inference profile cross-region route tới.
- [Cost parity] `_call_openai` bỏ qua `usage.prompt_tokens_details.cached_tokens`, nên tính giá đầy đủ cho phần prompt đã cache (dù catalog `gpt-6-luna-openai` có cache read 0,01). Nó cũng ghi `account=None`. Đường OpenAI hôm nay đã lệch so với hoá đơn.
- [Cost parity] `pricing.calc_cost` tra giá theo chuỗi model. Model lạ bị tính theo giá Sonnet mà không báo lỗi (`llm_price_unknown_model`). Giá override theo deployment sẽ không bao giờ được áp nếu `calc_cost` không nhận deployment. Hiện chưa mô hình hoá: bậc giá Haiku 5.5 khi prompt >100K ($0,50/$2,50), cache write 1 giờ = 2x (catalog chỉ có một cột cache write, fallback cố định 1.25x), batch -50%, `inference_geo:"us"` 1.1x, Bedrock regional +10% so với global (đã kiểm trên trang giá Anthropic hôm nay).
- [Cost parity] Quy ước `tokens_in` khác nhau: đường Converse ghi tổng prompt (uncached + cache read + cache write); `usage.input_tokens` của Anthropic API không gồm cache. Adapter mới phải cộng lại giống Converse. Thêm cột cache vào `llm_call_log` nghĩa là sửa `record_call*`/`_INSERT_SQL`/`billed_record` và INSERT của TripPlanner, cộng thêm cột ở `llm_call_daily` (rollup). Đây là thay đổi API ghi log dạng additive, không phải 'không đổi gì'.
- [Ước lượng tiết kiệm sai] Trang giá Anthropic (kiểm 29/10) ghi model 4.7 trở lên dùng tokenizer mới, ra khoảng +30% token cho cùng văn bản. Vì vậy Sonnet 4.6→5.5 chỉ rẻ hơn khoảng 13% cho cùng văn bản (2×1,3 so với 3), không phải 33%. Haiku 4.5→5.5 rẻ hơn khoảng 87%, không phải 90%. Model 5.5 bật adaptive thinking mặc định, và thinking tính tiền như output. Phải đo trong eval R2. Giá cache read Sonnet 5.5 $0,10 (0,05x) là đúng theo trang live; bản cache cũ của skill ghi 0,20 là đã lỗi thời.
- [Khác biệt provider] Sonnet 5.5 và Opus 5.5 trả 400 với `tool_choice` cưỡng bức (`any`/`tool`) và với temperature khác mặc định. API version 2026-10-21 từ chối temperature/top_p/top_k trên mọi model. Effort mặc định: Sonnet 5.5 `high`, Haiku 5.5 và Opus 5.5 `medium`. Adapter Anthropic phải dùng `output_config.format` (structured outputs), không dùng forced tool như Converse. Catalog chỉ có `supports_temperature`/`max_output_tokens`, nên cần cột `capabilities jsonb` (forced_tool, structured_output, thinking/effort mặc định, prefill). Nếu không, model mới trên kind cũ vẫn cần code. Effort phải đặt tường minh theo stage trên mọi đường thì fallback 'cùng model, khác đường' mới giữ được văn phong.
- [Refusal] Không bật `fallbacks` phía server của Claude API: nó đổi model ngầm (vi phạm ADR 0005 §4) và cost bị ghi sai model. Ghi `response.model` thật vào log. `stop_reason=refusal` vẫn tính tiền và phải ghi `billed_unusable`.
- [Timeout/retry] Client OpenAI dùng mặc định của SDK (timeout 600 giây, max_retries 2), SDK Anthropic cũng vậy. Một attempt có thể kéo tới khoảng 30 phút trước khi route chuyển sang model kế tiếp. Retry 429 nội bộ trong SDK che throttle khỏi breaker. Cần `timeout_s`/`max_retries` theo connection (0–1 cho 429), tôn trọng `retry-after`, và xếp 529 `overloaded_error` vào throttled.
- [Rate limit] Org Anthropic mới bắt đầu ở tier Start (audit S257 [V]: 1.000 RPM / 2M ITPM / 400K OTPM). Sonnet 5.5 và Sonnet 4.x có bucket riêng. Cần giới hạn đồng thời (concurrency/RPM) theo connection, nếu không wave sẽ chạm trần. Mốc '≤30 phút' chỉ là thời gian nối dây, không phải thông lượng.
- [Mục tiêu ≤30 phút] Mục tiêu này chỉ đúng cho CIS. TripPlanner đọc `bedrock_profile_ids`/`account_route` qua SELECT, dùng `SUPPORTED_ACCOUNTS=('acc3','acc2')` và env Lambda `BEDROCK_ACCT_PRIMARY`. CRM có gateway riêng. Tới khi S8 xong, TP và CRM vẫn cần deploy. `bedrock_profile_ids` phải được ghi song song (dual-write) và vẫn là nguồn sự thật cho tới khi TP chuyển xong; không đổi tên hay xoá cột mà TP đang SELECT.
- [Embed] `embed.py` cũng dùng `account_for` + `_acc2_client` hard-code, nên S3 phải sửa cả file này. Cột vector là `vector(1536)` (migration 041, 124). Mọi deployment Cohere phải dùng cùng `output_dimension` và cùng `input_type`, và phải kiểm region của account mới có `cohere.embed-v4`.
- [Thứ tự slice] Seed các key `anthropic-*` ở S1 tạo lại đúng kiểu gộp model × đường mà S3 muốn bỏ. Nên tạo bảng `llm_model_deployment` ngay trong migration S1 (schema + backfill) và cho adapter S2 dispatch theo deployment, khỏi phải dựng alias về sau.
- [Cache phiên] Cache session STS đang khoá theo tên account. Khi một connection sửa được `role_arn`/`external_id`/`region`, khoá cache phải gồm các giá trị đó. Secret cache trong `shared/secrets.py` có TTL 1 giờ; resolver mới cần invalidate và đọc lại một lần khi gặp 401.
- [OpenAI] Adapter hiện tại dùng Chat Completions. Model OpenAI mới có thể chỉ chạy trên Responses API, hoặc chỉ có tính năng ở đó (reasoning effort, encrypted reasoning). Nên giữ sẵn api_style `openai_responses`. Endpoint OpenAI-compatible (OpenRouter) khác nhau ở mức hỗ trợ strict json_schema, dẫn tới các dòng billed_unusable. `requirements.txt` chỉ có `openai>=1.16.2` (không pin) và chưa có `anthropic`.
- [Breaker mẫu] `decide.jev_breaker_open` là breaker trong process (biến module + `time.monotonic`), không dùng chung giữa các task. Chỉ dùng nó làm mẫu cho máy trạng thái; trạng thái dùng chung phải nằm ở `llm_provider_health`.
