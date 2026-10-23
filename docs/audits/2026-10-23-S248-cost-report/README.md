---
id: FIN-02-2026-10-prelim
title: Cost report August, September and October 2026 (October month to date)
description: Program AWS spend was 208 USD in August, 187 USD in September and is forecast at about 404 USD in October, driven by LLM waves on acc3 (+164 USD) and new always-on services on acc2 (+53 USD); refresh after 01/11.
type: report
status: draft
owner: nghiep
audience: [owner, engineer, cto, cio, pm]
applies_to: [ecosystem]
last_reviewed: 2026-10-23
related: [FIN-01, FIN-02, OPS-08, AA-896, AA-838, AA-884, AA-624]
---

# Báo cáo chi phí tháng 8, 9, 10/2026 (tháng 10 tính tới 22/10)

- Phiên: S248, 23/10/2026. Tác nhân: Claude Code (lane `aa896-finops`). Chế độ: **chỉ đọc** AWS.
- Nguồn: Cost Explorer của từng account (acc2 `aa365-admin`, acc3 `nghiep_aa365`, acc1 `pqnghiep-admin`), số
  Unblended, đọc 23/10 khoảng 07:40 UTC. Dữ liệu thô trong [`data/`](data/), lệnh lấy trong
  [`scripts/fetch_ce.sh`](scripts/fetch_ce.sh). Không có account ID trong các file này.
- Thêm (chỉ đọc): `aws budgets describe-budgets`, `aws ce get-anomaly-*`, `ecs describe-services` /
  `describe-task-definition`, `rds describe-db-instances`, `secretsmanager list-secrets` (chỉ đếm), log CI của
  Terraform Apply.
- Bổ sung cùng ngày (lane tiếp theo): số lượt gọi và token theo model từ CloudWatch `AWS/Bedrock` của acc3 và acc1
  (`get-metric-data`, 48 metric × 2 account ≈ 0,001 USD), lệnh trong
  [`scripts/fetch_cw_bedrock.sh`](scripts/fetch_cw_bedrock.sh), bảng tính bằng
  [`scripts/bedrock_units.py`](scripts/bedrock_units.py) (chỉ đọc file local). Dùng cho mục 5 và mục 6.
- **Chi phí của chính báo cáo này:** 18 request Cost Explorer × 0,01 USD = **khoảng 0,18 USD** (acc2 6, acc3 8, acc1 4;
  gồm cả các lệnh đọc anomaly monitor/subscription, tính phòng xa như request có phí).
- **Tháng 10 chưa chốt.** Số tháng 10 là 01–22/10 + dự báo của AWS cho cả tháng. Bước **làm lại sau 01/11** ở
  [mục 9](#9-làm-lại-sau-0111-bắt-buộc).

## 1. Tóm tắt cho chị Thư (VI, bản nháp — chốt sau 01/11)

1. Chi phí AWS cả chương trình: tháng 8 khoảng 208 USD, tháng 9 khoảng 187 USD, tháng 10 dự kiến khoảng 400 USD.
2. Phần tăng chính (khoảng 165 USD) là tiền gọi AI để viết lại và chấm toàn bộ tour của 14 nước trong 10 ngày đầu tháng 10; phần này giảm khi không chạy lại cả loạt.
3. Phần hạ tầng (máy chủ, cơ sở dữ liệu) tăng khoảng 50 USD/tháng vì có thêm hệ thống đặt tour (Booking), máy chạy việc nền riêng và cơ sở dữ liệu lớn hơn; đây là mức nền mới, khoảng 190 USD/tháng.
4. Hạn mức cảnh báo 250 USD/tháng cho hạ tầng vẫn còn dư; tài khoản AI trước đây chưa có hạn mức, nay đề xuất thêm hạn mức 250 USD/tháng và email cảnh báo.
5. Chưa cần chị quyết gì; có vài cách tiết kiệm nhỏ (mục 7) sẽ trình anh Nghiệp duyệt từng cái.

## 2. Tổng theo account (USD, Unblended)

| Account | Tháng 8 | Tháng 9 | Tháng 10 (01–22) | Tháng 10 dự báo cả tháng | Tháng 9 → 10 (dự báo) |
|---|---:|---:|---:|---:|---:|
| acc2 — hạ tầng (TrueIDC) | 140,22 | 134,96 | 126,57 | **187,75** | +52,79 (+39 %) |
| acc3 — LLM chính (eCloudvalley) | 22,40 | 51,43 | 138,61 | **215,74** | +164,31 (+319 %) |
| acc1 — LLM dự phòng (cá nhân) | 45,15 | 0,97 | 0,11 | ~0,15 | ≈ 0 |
| **Cộng** | **207,77** | **187,36** | **265,29** | **~403,6** | **+216 (+115 %)** |

Theo ngày (để so tháng lẻ ngày): acc2 4,52 → 4,50 → **5,75 USD/ngày** (riêng 16–22/10: **6,24**); acc3 0,72 →
1,71 → **6,30 USD/ngày**. Dự báo cả tháng là `get-cost-forecast` của AWS (file `data/*-forecast-oct.json`).

- **Tax:** acc3 có 1,68 USD thuế tháng 8, acc1 4,11 USD tháng 8; acc2 không có dòng thuế (TrueIDC tính ở hoá đơn).
- **Credit:** acc1 có credit nhỏ (−0,81 tháng 9, −0,46 tháng 10). **acc3 không có dòng Credit nào trong Cost
  Explorer tháng 8–10** dù đã nhận AWS Lift tier 1 (250 USD) — xem [phát hiện F1](#8-phát-hiện-và-việc-cần-làm).

## 3. acc2 theo `App` tag (tag có hiệu lực từ 15–16/10)

Tháng 8, 9 và nửa đầu tháng 10 toàn bộ là "untagged" (tag không gán ngược). Số đáng tin là **16–22/10 (7 ngày)**:

| App | 16–22/10 | USD/ngày | ≈ USD/tháng | Tỷ lệ | Dịch vụ chính |
|---|---:|---:|---:|---:|---|
| shared | 19,35 | 2,76 | 84 | 44 % | ELB 7,48 · RDS 7,17 · WAF 1,88 · EC2-Other 1,62 |
| cis | 13,33 | 1,90 | 58 | 30 % | ECS 9,11 · ElastiCache 3,28 · Secrets 0,43 · ECR 0,20 |
| untagged | 8,50 | 1,21 | 37 | 19 % | CloudWatch 3,78 · VPC (IPv4 public) 2,22 · Secrets 1,54 · ECS 0,63 |
| booking | 2,22 | 0,32 | 10 | 5 % | ECS 2,11 · Secrets 0,08 |
| tripplanner | 0,26 | 0,04 | 1 | 1 % | Secrets 0,21 (Lambda + API ~0) |
| identity / platform | 0,07 | 0,01 | 0 | 0 % | Secrets, RDS (giá trị tag ngoài danh sách DM-10.1) |
| crm | 0,00 | 0 | 0 | 0 % | `aa-crm-dev-spike` desired 0 |
| **Cộng** | **43,73** | **6,25** | **190** | | |

Budget per-App đọc live 23/10 (actual tháng 10): shared **20,84 / 50**, cis 14,20 / 150, booking 2,35 / 25,
tripplanner 0,29 / 25; account 126,57 / 250 (AWS forecast 197,26). Với nhịp 84 USD/tháng, **budget `shared` 50 USD
sẽ báo vượt mỗi tháng từ tháng 11** — đã chuẩn bị chỉnh (mục 8, F3).

## 4. acc2 theo dịch vụ và các bước nhảy

| Dịch vụ | Tháng 8 | Tháng 9 | 10 (01–22) | USD/ngày T9 → T10 | Thay đổi |
|---|---:|---:|---:|---|---:|
| Elastic Load Balancing | 37,61 | 36,41 | 25,85 | 1,214 → 1,175 | −3 % |
| Elastic Container Service | 21,54 | 21,13 | 31,85 | 0,704 → **1,448** | **+106 %** |
| RDS | 20,82 | 20,39 | 18,02 | 0,680 → 0,819 | +21 % |
| ElastiCache | 16,37 | 15,84 | 11,20 | 0,528 → 0,509 | −4 % |
| VPC (IPv4 public) | 11,17 | 10,81 | 7,63 | 0,360 → 0,347 | −4 % |
| CloudWatch | 6,92 | 7,86 | 9,37 | 0,262 → 0,426 | **+62 %** |
| WAF | 9,37 | 9,46 | 6,54 | 0,315 → 0,297 | −6 % |
| Secrets Manager | 3,61 | 4,42 | 5,62 | 0,147 → 0,255 | **+73 %** |
| EC2-Other (EBS, truyền dữ liệu) | 3,21 | 3,44 | 4,25 | 0,115 → 0,193 | +69 % |
| EC2 Compute (NAT t4g.nano) | 3,72 | 3,98 | 2,82 | 0,133 → 0,128 | −3 % |
| API Gateway | 0,12 | 0,38 | 1,82 | 0,013 → 0,083 | +547 % |
| S3, ECR, Route 53, SES, Cost Explorer | 0,65 | 0,78 | 1,49 | 0,026 → 0,068 | |
| Bedrock trên acc2 (Nova Pro, Palmyra, Cohere) | 5,61 | 0,02 | 0,10 | | chuyển sang acc3 |

Giải thích từng bước nhảy (theo usage type trong `data/acc2-usage-type.json`, đối chiếu log phiên):

- **Tháng 8 → 9 (−5 USD):** Bedrock trên acc2 (Nova Pro 4,52, Palmyra 0,58, Marketplace 0,51 ≈ 5,6 USD) về 0 khi
  mọi lời gọi LLM chuyển sang satellite acc3 (AA-296/AA-397). Các dịch vụ còn lại gần như phẳng.
- **ECS +106 % (≈ +23 USD/tháng):** Fargate vCPU 0,56 → 1,09 USD/ngày, GB 0,12 → 0,24. Nguyên nhân: service
  `aa-cis-dev-worker` chạy 24/7 từ 05/10 (0,5 vCPU / 1 GB, AA-651), `aa-booking-dev-api` từ 14/10 (0,25 / 0,5),
  autoscaling api 1→7 và worker 1→3 trong các wave, task chạy ngắn (DB Migrate, DB Schema Dump hằng đêm, isolation
  probe) và task chồng nhau khi deploy (nhiều deploy/ngày từ S235). Tất cả trên Fargate Spot, x86.
- **RDS +21 % (mức nền mới ≈ +10 USD/tháng):** `db.t3.micro` → `db.t4g.small` khoảng 15/10 (t3.micro chỉ còn 14,3
  ngày phí trong tháng 10; t4g.small ≈ 0,88 USD/ngày). Backup tính phí 0,012 → 0,039 USD/ngày. RDS sau đổi ≈ 30
  USD/tháng (trước ≈ 20).
- **CloudWatch +62 % (≈ +5 USD/tháng):** alarm tăng gấp đôi (AlarmMonitorUsage 0,056 → 0,099 USD/ngày: alarm RDS,
  identity, Booking, TripPlanner S240–S243), custom metric 0,075 → 0,149 USD/ngày, vended logs tăng. Dashboard
  basic ≈ 2,4 USD/tháng (phẳng).
- **Secrets Manager +73 % (≈ +3 USD/tháng):** nay 34 secret × 0,40 USD ≈ 13,6 USD/tháng (Booking, identity, CRM,
  E2E). 20/34 secret chưa có tag `App`.
- **Truyền dữ liệu (≈ +9 USD/tháng, chưa rõ nguồn):** DataTransfer-Regional (giữa AZ) 0,036 → 0,213 USD/ngày,
  DataTransfer-Out 0,002 → 0,069, DataProcessing 0,003 → 0,029. Ứng viên: lưu lượng giữa AZ ECS ↔ RDS/Redis/NAT,
  trang SSR TripPlanner (892 trang tour từ S236), Booking. Cần soi thêm (F5).
- **API Gateway (+2 USD/tháng):** REST API Booking (từ 14/10), lưu lượng TripPlanner và probe/smoke.
- **Phẳng:** 2 load balancer (ALB + NLB cho VPC link) ≈ 36 USD/tháng, ElastiCache `cache.t3.micro` ≈ 16, 3 IPv4
  public ≈ 11, WAF ≈ 9,5, NAT `t4g.nano` ≈ 3,6.

## 5. acc3 (LLM chính) và acc1 (LLM dự phòng)

| Model (acc3) | Tháng 8 | Tháng 9 | 10 (01–22) |
|---|---:|---:|---:|
| Claude Haiku 4.5 | 2,49 | 18,27 | **86,45** |
| Claude Sonnet 4.6 | 18,23 | 33,05 | 37,41 |
| OpenAI GPT-5.6 Luna | — | 0,05 | 10,73 |
| OpenAI GPT-6 Luna | — | — | 3,40 |
| Claude Sonnet 5 / Haiku 5.5 (thử) | — | — | 0,44 |
| Cost Explorer API | — | 0,06 | 0,18 |
| Tax | 1,68 | — | — |
| **Cộng** | **22,40** | **51,43** | **138,61** |

- **Tháng 8 → 9 (+29 USD):** rewrite S1 + review chuyển hẳn sang acc3; hai đợt lớn 17/09 (24,79 USD) và 25/09 (11,94).
- **Tháng 9 → 10 (+164 USD dự báo):** khớp với log phiên (tương quan theo ngày, chưa tách theo stage — xem mục 9):
  - 01–08/10: chạy lại toàn bộ 14 nước (Korea/Taiwan 01, Mongolia 02, China 121 tour 03, Bhutan/Thailand 05, Laos 06,
    Nepal 07; xong 08/10 kèm audit A-series v4). Ngày đắt nhất 08/10: **34,30 USD** (Haiku 28,94).
  - 09–10/10: regenerate tour rớt + wave India ×2 + A/B (10/10: 22,84 USD).
  - Haiku 4.5 chiếm 62 % tháng 10 (judge/review/atomize S1 theo wave); GPT-5.6 Luna mới (place card AA-772,
    judge/brand audit AA-714), GPT-6 Luna (atomize, S224).
  - **Haiku 4.5 tăng 4,7 lần (18,27 → 86,45 USD) = số lượt gọi × 2,2 và giá mỗi lượt × 2,2** (CloudWatch, mục 6):
    9.688 → 21.104 lượt (01–22/10); token vào mỗi lượt 716 → 1.729 (prompt dài hơn: chấm/atomize đọc cả bài S1),
    token ra 234 → 480. Giá theo token gần như không đổi (1,99 → 1,85 USD / 1M token). Nghĩa là phần tăng là do
    **khối lượng và độ dài prompt**, không phải đổi model hay giá.
  - Sonnet 4.6 gần như đứng yên về số lượt (1.644 → 1.638) và giá mỗi lượt (~20–23 USD / 1.000 lượt); chỉ chiếm 4 %
    số lượt nhưng 27 % tiền LLM tháng 10.
  - 12–20/10: pilot tenant T-series (T2/T9 Sonnet 4.6), golden set baseline 20/10. Từ 17/10 nhịp thấp: 0–8 USD/ngày.
- **acc1:** tháng 8 = 45,15 USD, gồm Sonnet 4.6 27,84 (trước khi acc3 thành primary), **Secrets Manager 8,09 + RDS
  0,41 là tài nguyên lạc** do `default` profile từng trỏ acc1 (đã dọn ở AA-517, 02/09). Từ tháng 9 chỉ còn fallback:
  < 1 USD/tháng.
- Chi phí API ngoài AWS (OpenAI trực tiếp, Jev, DataForSEO, geocoder) **không có trong Cost Explorer**; lấy từ ledger
  DB ở bước mục 9.

## 6. Đơn giá (unit cost)

### 6a. Theo model — tính được ngay (CloudWatch × Cost Explorer)

Tử số: tiền Cost Explorer của dòng dịch vụ model (Unblended). Mẫu số: `Invocations` (lượt gọi thành công),
`InputTokenCount`, `OutputTokenCount` của CloudWatch `AWS/Bedrock` (us-west-1), cộng theo ngày UTC; tháng 10 = 01–22.
Đối chiếu: số token × giá niêm yết khớp Cost Explorer trong ±2 % (Haiku 4.5 tháng 10: 36,48M vào × 1 + 10,13M ra × 5
= 87,1 USD so với 86,45; Sonnet 4.6: 4,12M × 3 + 1,71M × 15 = 38,0 so với 37,41).

| Account | Model | Tháng | Lượt OK | Lỗi phía client | Token vào / lượt | Token ra / lượt | USD (CE) | USD / 1.000 lượt | USD / 1M token |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| acc3 | Claude Haiku 4.5 | 8 | 397 | 2 | 1.881 | 880 | 2,49 | 6,26 | 2,27 |
| acc3 | Claude Haiku 4.5 | 9 | 9.688 | 0 | 716 | 234 | 18,27 | 1,89 | 1,99 |
| acc3 | Claude Haiku 4.5 | 10 (01–22) | 21.104 | 0 | 1.729 | 480 | 86,45 | **4,10** | 1,85 |
| acc3 | Claude Sonnet 4.6 | 8 | 984 | 0 | 2.501 | 800 | 18,23 | 18,53 | 5,61 |
| acc3 | Claude Sonnet 4.6 | 9 | 1.644 | 0 | 1.487 | 1.043 | 33,05 | 20,10 | 7,95 |
| acc3 | Claude Sonnet 4.6 | 10 (01–22) | 1.638 | 0 | 2.512 | 1.044 | 37,41 | **22,84** | 6,42 |
| acc3 | OpenAI GPT-5.6 Luna | 10 (01–22) | 11.827 | 0 | 83 | 560 | 10,73 | **0,91** | 1,41 |
| acc3 | OpenAI GPT-6 Luna | 10 (01–22) | 7.090 | 0 | 69 | 666 | 3,40 | **0,48** | 0,65 |
| acc3 | Claude Sonnet 5 (thử) | 10 (01–22) | 102 | **90** | 551 | 308 | 0,43 | 4,18 | 4,87 |
| acc3 | Cohere Embed v4 (thử) | 10 (01–22) | 525 | **56** | 13 | 0 | ~0 | — | — |
| acc1 | Claude Haiku 4.5 | 8 | 1.024 | 0 | 1.270 | 665 | 4,71 | 4,60 | 2,38 |
| acc1 | Claude Sonnet 4.6 | 8 | 840 | 0 | 2.487 | 1.712 | 27,84 | 33,14 | 7,89 |
| acc1 | Claude Sonnet 4.6 | 9 / 10 | 16 / 16 | 1 / 0 | — | — | 0,05 / 0,10 | — | — |

Đọc nhanh:

- Một lượt Sonnet 4.6 đắt **~5,6 lần** một lượt Haiku 4.5 tháng 10 và **~25–47 lần** một lượt GPT-5.6/6 Luna.
  Các lượt GPT Luna rất ngắn ở đầu vào (69–83 token) và dài ở đầu ra (560–666): đúng kiểu sinh place card / atom.
- Giá **mỗi token** của từng model ổn định giữa các tháng; giá **mỗi lượt** thay đổi theo độ dài prompt. Muốn hạ tiền
  LLM thì nhắm vào số lượt (chạy lại theo tập con, DM-10.6) và độ dài prompt (cache, cắt ngữ cảnh), không phải đổi giá.
- acc1 tháng 8: Sonnet 4.6 mỗi lượt đắt hơn acc3 (33 so với 19 USD / 1.000 lượt) vì đầu ra dài gấp đôi (1.712 token)
  — khi đó acc1 còn chạy writer S1 trước khi acc3 thành primary.
- Haiku 5.5, Sonnet 5.5 (thử, < 30 lượt) không có dòng tiền riêng đáng kể nên bỏ khỏi bảng (số đầy đủ:
  `python3 -I scripts/bedrock_units.py data`).

### 6b. Theo sản phẩm — ước lượng, chốt sau 01/11

- **USD LLM / tour trong catalog, tháng 10 (ước lượng trần):** 138,43 USD LLM acc3 (01–22/10, trừ phí Cost Explorer)
  ÷ ~892 tour trong `gold_aa_internal.published_tours` (`reltuples`, dump 22/10) ≈ **0,16 USD / tour**; khoảng
  **24 lượt Haiku + 2 lượt Sonnet + 21 lượt GPT Luna cho mỗi tour**. Đây là trần vì tháng 10 = chạy lại cả 14 nước
  cộng pilot tenant T-series và A/B; mẫu số là cả catalog chứ chưa phải số tour publish/republish trong tháng.
- Thêm phần hạ tầng `cis` acc2 (≈ 58 USD/tháng, nhịp từ 16/10) thì **≈ 0,22 USD / tour / tháng** khi chạy lại toàn bộ.
- Các ô dưới đây vẫn cần DB (theo stage, theo tháng). Mẫu số và LLM theo stage đọc qua ECS exec, mà hook chặn ECS exec
  với subagent; script chỉ-đọc đã sẵn: [`scripts/aa896_units.py`](scripts/aa896_units.py) (LLM theo
  app/account/provider/stage/model/ngày, DataForSEO, geocoder, Jev `decision_log`, `published_tours` theo
  `published_at`, `acp_shared.content_piece` theo kênh).

| Đơn vị | Tử số | Mẫu số | T9 | T10 |
|---|---|---|---:|---:|
| USD / tour publish | cis acc2 (≈ 58 USD/tháng từ 16/10) + LLM stage `s1_*`/`a*` | `published_tours` có `published_at` trong tháng | | |
| USD LLM / tour publish | LLM stage `s1_*`, `a1_*`–`a3_*` | như trên | | |
| USD / content piece | LLM stage `t*_` | `acp_shared.content_piece` trong tháng (~293 bản ghi tổng, dump 22/10) | | |
| USD / trip plan | tripplanner (≈ 1 USD/tháng) + `tp_*` | không đọc được bằng `cis_app` (schema `tripplanner`) | | |
| USD / booking | booking (≈ 10 USD/tháng) | 0 booking thật ở Dev | — | — |

## 7. Cách tiết kiệm (đề xuất, chưa làm gì — mỗi mục cần anh duyệt, DM-10.7)

| # | Cách | Ước tính | Đánh đổi |
|---|---|---:|---|
| S1 | **Bedrock Batch inference** cho wave rerun (giảm 50 % giá token) | ~50 USD mỗi lần rerun cả catalog (lần tháng 10 ≈ 100 USD) | Đang bị AWS chặn entitlement trên acc3 (AA-624); batch chậm (giờ, không phút) |
| S2 | Giữ luật chạy trả phí theo tập con (DM-10.6) + prompt caching cho system prompt dài (Sonnet/Haiku) | tuỳ stage; đo bằng `llm_call_log` | Cần kiểm client đã bật cache chưa |
| S3 | Fargate **ARM64 (Graviton)** cho cis api/worker và booking | ~20 % phần ECS ≈ 5–6 USD/tháng | CI build image multi-arch; thử worker trước |
| S4 | ALB internet-facing → **internal** (API vào qua API GW + NLB; CRM qua CloudFront VPC origin vốn dùng ALB internal) | ≈ 7 USD/tháng (2 IPv4 public) | Phải kiểm lại lý do AA-585 để ALB internet-facing trước |
| S5 | ElastiCache `cache.t3.micro` → `cache.t4g.micro` | ≈ 2–3 USD/tháng | Thay node = cache trống vài phút |
| S6 | Xoá dashboard CloudWatch không dùng (3 dashboard đầu miễn phí) | ≈ 2 USD/tháng | Không |
| S7 | Secrets: xoá `booking-jwt-signing-key` khi bỏ bridge; secret tĩnh không xoay → SSM Parameter Store SecureString (miễn phí) | 0,40–5 USD/tháng | Mất rotation tự động của Secrets Manager |
| S8 | REST API + NLB → HTTP API nối thẳng ALB | ≈ 18 USD/tháng (bỏ NLB) | **Không khuyến nghị bây giờ**: mất WAF trên API Gateway và các tính năng REST |

## 8. Phát hiện và việc cần làm

| # | Phát hiện | Việc | Trạng thái |
|---|---|---|---|
| F1 | acc3 không có dòng Credit nào tháng 8–10; Lift tier 1 (250 USD) không hiện trong Cost Explorer | Anh Nghiệp mở Billing → Credits trên acc3 (hoặc hoá đơn eCloudvalley) để xem credit đã áp chưa và còn bao nhiêu. Với nhịp ~216 USD/tháng, 250 USD chỉ đủ khoảng 1 tháng | Chờ anh (cần console) |
| F2 | acc3 **không có budget**; anomaly chỉ có subscription mặc định (≥ 100 USD **và** ≥ 40 %, email hằng ngày) | Infra `feat/aa896-cost-anomaly-detection`: budget 250 USD/tháng (không tính credit) + email anomaly hằng ngày ≥ 10 USD (`accounts/acc3-bedrock/cost_guard.tf`, plan 2 add) | Code xong, chờ merge + apply local |
| F3 | Budget `shared` 50 USD sẽ báo vượt mỗi tháng (nhịp ≈ 84); `cis` 150 không bao giờ báo (nhịp ≈ 58) | Cùng nhánh Infra: cis 150 → 90, shared 50 → 100 (tổng account 250 giữ nguyên) | Code xong, chờ merge + CI apply |
| F4 | 19 % chi phí acc2 từ 16/10 là untagged: CloudWatch, IPv4 public, 20/34 secret, một phần ECS (task chạy ngắn) | Gắn `App` cho secret và alarm còn thiếu; task chạy ngắn của Infra mang tag qua `propagateTags`/`tags` khi run-task | Đề xuất (issue con của AA-828 nếu anh đồng ý) |
| F5 | Truyền dữ liệu giữa AZ + ra Internet tăng ≈ 9 USD/tháng, chưa rõ nguồn | Soi CE theo `USAGE_TYPE` + `RESOURCE_ID` (cần opt-in resource-level, 14 ngày) hoặc VPC Flow Logs ngắn hạn | Đề xuất |
| F6 | Giá trị tag `identity`, `platform` nằm ngoài danh sách DM-10.1 (cis, booking, tripplanner, crm, shared) | Gộp `identity` → `shared` hoặc thêm vào DM-10.1; tiền chỉ vài cent | Đề xuất |
| F7 | Cost Anomaly Detection acc2 **đã live** từ 19/10 (Terraform Apply run 39199328963: import monitor + tạo subscription IMMEDIATE ≥ 5 USD → topic alerts). Chưa có alert nào được ghi nhận | Không cần làm thêm | Xong |
| F8 | acc1 có 2 budget tạo tay (180 và 150 USD), chi < 1 USD/tháng | Không cần làm thêm | Xong |
| F9 | Model đang thử trên acc3 có tỉ lệ lỗi phía client cao trong tháng 10: Sonnet 5 90/192 lượt (47 %), Sonnet 5.5 6/16, Haiku 5.5 7/26, Cohere Embed v4 56/581 (10 %). Tiền gần 0, nhưng là dấu hiệu cấu hình/quyền model hoặc tham số request sai | Khi bật một model mới qua `shared.llm_model_catalog`, kiểm `InvocationClientErrors` trên CloudWatch cùng lúc với `llm_call_log`; đưa vào bước thử ~3 lượt (DM-10.6) | Đề xuất |
| F10 | Sonnet 4.6 = 4 % số lượt nhưng 27 % tiền LLM tháng 10 (22,84 USD / 1.000 lượt, gấp ~5,6 lần Haiku) | Khi có `llm_call_log` theo stage (mục 9): liệt kê stage nào dùng Sonnet; chỉ đổi model sau A/B chất lượng + duyệt (S245 systematic quality) | Đề xuất |

## 9. Làm lại sau 01/11 (bắt buộc)

Tháng 10 ở trên là **01–22/10 + dự báo**. Phiên đầu tiên từ **03/11** (Cost Explorer còn sửa số ~48 giờ sau cuối tháng):

1. `bash scripts/fetch_ce.sh 2026-11-01 data-final` (từ thư mục này; 11 request ≈ 0,11 USD; MFA cho `aa365-admin`).
2. `bash scripts/fetch_cw_bedrock.sh 2026-11-01 data-final` rồi `python3 -I scripts/bedrock_units.py data-final`
   (≈ 0,001 USD) để thay bảng 6a; thêm model ID mới vào script nếu `list-metrics` thấy model mới.
3. Orchestrator chạy `scripts/aa896_units.py` qua ECS exec S3-mediated (sửa ngày cuối `2026-10-23` → `2026-11-01`),
   tải `scripts/aa896_result.json` từ bucket bronze, xoá 2 object `scripts/aa896_*` trên S3.
4. Thay số tháng 10 ở mục 2–5 bằng số chốt, điền mục 6b, tính lại F3 bằng nhịp cả tháng 10 theo `App`.
5. Đối chiếu tổng tiền và số lượt LLM của `llm_call_log` với Cost Explorer và CloudWatch acc3 (bảng 6a); S195 từng
   thấy log thiếu ~20 % so với bill.
6. Viết báo cáo tháng 10 chuẩn theo [`docs/ops/cost/README.md`](../../ops/cost/README.md) (C8 capacity + cost),
   chốt 5 dòng cho chị Thư ở mục 1, rồi đổi `status` của file này thành `superseded`.
