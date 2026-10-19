# S244 — Kế hoạch tổng thể AA_Ecosys (audit toàn bộ issue đang mở)

Ngày 19/10/2026, phiên S244, tác nhân: Claude Code. Chỉ đọc: không đổi Linear, Jira, Notion, GitHub hay AWS.
Bảng chi tiết từng issue: [issues.md](issues.md). Bản đề xuất thay §3/§3a/§4 của backlog sống: [backlog-proposal.md](backlog-proposal.md).

Nguồn: 4 lane audit theo project Linear (đọc đủ mô tả và comment của mọi issue mở), một vòng verify độc lập cho các đề xuất đổi trạng thái, một lane rà khoảng trống cam kết (ADR, data standards, baseline bảo mật, CONTEXT.md, lessons, Jira), một lane lộ trình. Kiểm chéo bằng git và gh ở chế độ chỉ đọc.

## 1. Tóm tắt

1. Đang mở **84 issue**: 17 In Progress và 67 Backlog. Không có issue nào ở Todo, In Review hay Triage.
2. Khối nền tảng (Q10) đã xong khoảng 80%. Còn lại X1 S20–S23, cutover AA-816, gỡ ngoại lệ E2E (ADR 0006a A10) và gỡ cầu nối Booking (AA-680). Hai mục cuối không có trong ghi chú S243.
3. Công việc nội dung CIS đã đứng yên từ 16/10 (S240), trong khi mỗi phiên tạo issue nhanh hơn đóng: khoảng 80 tạo so với 60 đóng trong S238–S243.
4. Đường găng là chuỗi **X1 S21 → S22**. Trước S22, view `catalog.*` bị đóng băng; từ lúc chép 245 sang Infra cho tới S22, migration CIS cũng bị đóng băng. Vì vậy AA-847, AA-851, AA-850, AA-859 và A10 đều phải chờ.
5. Rủi ro lớn nhất:
   - X1 S21 chuyển chủ sở hữu toàn bộ object CIS trên RDS dùng chung.
   - Terraform apply toàn root đang chạy mà chưa có guard (AA-846).
   - Dump dữ liệu thật vẫn nằm trên laptop, không mã hoá (AA-829).
   - TripPlanner thu PII nhưng chưa có trang /privacy (AA-886).
   - Hạn AA-820 là 11/11.
6. Quá nhiều việc dở: 17 issue In Progress, trong đó 7 issue tài liệu/CI cùng được mở ngày 19/10.
7. Có 4 issue Done giả (đóng tự động khi merge PR) cần mở lại: AA-825, AA-805, AA-665, AA-669. Có 2 issue nên chuyển Done thành Canceled: AA-675, AA-689.
8. Riêng AA-902: kiểm lại bằng gh lúc ~12:00Z, cả 4 PR đã merge: CIS #854 (11:49:56Z), Booking #45 (11:44:15Z), TP #105 (11:42:55Z), Infra #221 (11:37:46Z); Deploy Dev của CIS trên `1d16adf` thành công. Còn verify live, copy guard mig 153/240, và 2 file test TripPlanner còn ID nên chưa sạch. AA-903 (CIS #855, Booking #46, TP #106) và AA-816 #856 cũng đã merge.
9. Đề xuất: S244–S246 đóng hẳn khối nền tảng. Từ S247, mỗi phiên dành 2–3 issue cho nội dung CIS và 1–2 issue cho bảo mật/nền tảng.
10. Hạn mức Linear: CIS Core đang 96/100, nên issue mới cho nội dung CIS chưa thể tạo vào project đó.

### Issue mở theo project

| Project | In Progress | Backlog | Tổng mở | Chưa lưu trữ / 100 |
|---|---|---|---|---|
| Data Platform — Schema, Ops & Scale (P-AA-16) | 13 | 26 | 39 | 55 |
| CIS Core — Pipeline, LLM & Platform (P-AA-15) | 1 | 27 | 28 | 96 |
| CIS Portal — Admin & Tenant UI | 1 | 6 | 7 | 41 |
| TripPlanner & AA-Booking | 2 | 8 | 10 | 34 |
| **Tổng** | **17** | **67** | **84** | |

Data Platform có khoảng 20 issue SDLC, CI, docs, bảo mật và FinOps (AA-866…AA-903), tức gần một nửa project, đã lệch khỏi mục đích ban đầu của nó (ADR 0008).

## 2. Mốc và đường găng

| Mốc | Hoàn thành khi | Issue | Ước lượng | Thứ tự |
|---|---|---|---|---|
| **M1 — Đóng khối nền tảng** | (1) X1 S20–S23 xong, probe xanh và không còn ô pending. AA-860 và AA-852 Done có bằng chứng S18/S22. (2) Cutover AA-816: tắt legacy login ở Production, đã thử break-glass qua managed login, đã xoay `ADMIN_SECRET`, E2E xanh. (3) Đã gỡ ngoại lệ A10. (4) Đã gỡ cầu nối CIS→Booking và có bằng chứng live rằng user không thuộc nhóm `booking-*` bị từ chối. | AA-860, AA-852, AA-816, AA-680 (nửa staff), AA-703 (pha 0–2) | 2,5 phiên (S244–S246), cộng 1 phiên dự phòng nếu S21 vướng | 1 |
| **M1b — SDLC/docs "Now"** | AA-902 quét 0 hit trên main của 3 repo public và CI đỏ khi thử cài ID. AA-903 và AA-904 đã merge. Docs lint chặn ở mọi repo; repo chỉ cho squash; CONTEXT.md có front-matter; có `alarms.md` sinh tự động; có GitHub App, rồi tới release-please. Báo cáo cost tháng 10 (sau 01/11). | AA-902, 903, 904, 887, 888, 889, 890, 893, 895, 896, 878, 901, 891, 846 | Rải trong S244–S252; AA-896 làm ở phiên đầu tiên từ 01/11 | Song song với M1 và M2 |
| **M2a — Chất lượng nội dung CIS** | Có golden set (AA-729) và baseline. Đã gọn bộ gate T10 (AA-787, 789, 790). Có từ vựng thương hiệu tenant (AA-800). Đã xử lý LinkedIn/FAQ (AA-780, 779) và tỉ lệ F9 (AA-865). Đã chạy G7 48 tour và viết báo cáo G8 (AA-741). Mỗi thay đổi có số trước/sau đo trên golden set (D-23). | AA-729, 787, 789, 790, 800, 780, 779, 865, 741, 783 | 4 phiên (S247–S250) | 2, chỉ bắt đầu khi M1 xong |
| **M2b — Địa điểm, ảnh, Jev** | L4 read model và lật `PLACES_SOURCE=cis` (AA-847). CloudFront và đồng bộ ảnh hằng ngày (AA-844, đã hứa chị Thư trên PR-11). Một lượt chạy place gộp (AA-712, 905, 784). Vòng nhãn Jev (AA-845, 803). | AA-847, 844, 712, 905, 784, 845, 803 | 3 phiên (S248–S252, xen với M2a) | 2, chỉ làm sau X1 S22 |
| **M3 — Booking wave 3** | Phạm vi AA-682: supplier bookings, trip checks, invoices + lịch thanh toán, supplier bills. Hiện **chưa có Done-when**, cần viết trước. | AA-682, AA-835 | 3–5 phiên | Chưa xếp lịch. Chờ quyết định thuế và cách đánh dấu thanh toán. |
| **M4 — UAT video** | Mỗi kịch bản có một video (1440/390) ở 4 bề mặt. Có báo cáo pass/fail. Nghiệp ký duyệt. Kịch bản đăng nhập bằng Cognito, vì password login sẽ bị tắt. | AA-855, AA-906, AA-837 | 1–2 phiên | Sau M2a và trước tenant trả tiền đầu tiên, khi Nghiệp ra hiệu |
| **M5 — Tenant trả tiền đầu tiên, rồi prod** | Hoàn tất Tenant horizon (handbook §9.2) và AA-813 (tenant đăng nhập bằng Cognito, chưa có trong §9.2). Có gói pháp lý (AA-886, AA-820) và lớp bảo mật (AA-874, 876, 875, 873, 848, 859). Prod thì cần thêm ngày go-live và AA-880. | ~26 issue (xem issues.md) | 8–12 phiên, cộng 2–3 phiên cho blueprint prod | 3 |

**Đường găng (thứ tự cứng):**

1. **X1 S20** (S244): sinh mật khẩu `db_migrator` (đã duyệt), chạy `set-password`, rồi probe.
2. **X1 S21** (S245):
   - Chạy lại plan Infra #220 (lần trước vướng lock), chạy script kiểm kê, merge root #110/#111 (file rollback).
   - Merge CIS #853 (mig 245) và bản chép sang Infra. Từ đây bắt đầu đóng băng migration CIS.
   - Apply qua DB Migrate khi `shared.job` và `booking.job` rảnh.
3. **X1 S22** (S246): đặt secret cho task def migrator (bước tay H6). Sau đó DB Migrate, Schema Dump và probe đăng nhập bằng `db_migrator`, chạy probe 246. **Từ đây hết đóng băng**.
4. Sau S22, cùng phiên S246: gỡ A10 bằng một migration CIS mới, rồi tới S23 close-out. Nửa staff của AA-680 và cầu nối Booking làm sau cutover (S246).
5. Từ đây mở khoá AA-847 → AA-712 → AA-851; AA-859 wave 3–4; AA-850.
6. Cutover AA-816 chạy song song với bước 2–3, nhưng không deploy CIS trong cửa sổ S21.

**Mốc lịch cứng:**

- ≥01/11: audit cost, AA-896, AA-838.
- ~02/11: Jira PR-20 kỳ 2.
- ≤11/11: AA-820 (AUP Anthropic có hiệu lực 12/11). Nên có quyết định của chị Thư khoảng 01/11.
- 18/11: hết hạn khôi phục 4 secret đã xoá.
- 30/11: hết hạn ignore pip-audit cho langchain và langgraph, đồng thời hết hạn allowlist CIS của AA-902. Nếu chưa xử lý, CI sẽ đỏ từ 01/12.
- 31/12: hết hạn ignore chromadb.

## 3. Kế hoạch theo phiên

Quy ước đề xuất (Nghiệp có thể bỏ): mỗi phiên làm **3–5 issue chính**. Riêng các issue XS chỉ còn bước đóng (đã có bằng chứng, ≤30 phút) được ghi ở dòng "đóng kèm" và không tính vào hạn mức này.

Ngày dự kiến giả định nhịp khoảng 1 phiên/ngày như S238–S243. Đây chỉ là giả định, không phải cam kết.

Cổng chất lượng chung áp cho mọi issue:

- Có code backend → Done theo `aa-ship`: merge, CI xanh, rollout COMPLETED, verify endpoint live.
- PR rủi ro (auth/quyền, migration/schema, CI/workflow/secret, xoá dữ liệu) → review độc lập trước khi merge.
- Sửa UI → `aa-ui-verify` ở 1440/390, light/dark.
- Chạy có trả phí → báo giá trước, thử 3 mẫu, tối đa khoảng 50 tour.
- Tên issue không đưa vào title hay body PR dưới dạng tự đóng.

### S244 — phần còn lại hôm nay (khối nền tảng + AA-902)

| Issue | Việc | Cổng chất lượng |
|---|---|---|
| AA-902 | (1) CIS #854 và Booking #45 đã merge (gh, ~12:00Z), Deploy Dev CIS `1d16adf` thành công; kiểm Booking deploy cũng xong. (2) Kiểm copy guard: #854 sửa chuỗi trong `COMMENT ON COLUMN` của mig 153, nên file không còn khớp bản đã apply; mig 240 cần chép lại byte-for-byte sang Infra. (3) Verify live api + worker (bên dưới). (4) Booking: retention DRY RUN. (5) Mở PR TP bỏ 2 hit còn lại trong `backend/tests/test_embed_satellite_fallthrough.py` và `backend/tests/test_llm_gateway.py`. | Live verify CIS: upload URL/ingest bucket, photos sync, retention archive, Bedrock Batch `s3BucketOwner`, nhãn `/admin/llm-usage` theo `account_key`. Booking: retention DRY RUN. TP: `/api/browse` và một lượt search có embed. Chưa Done trước S245. |
| AA-903 | CIS #855, Booking #46, TP #106 đã merge (11:31–11:32Z). Còn gắn link run Dependabot. | Mỗi repo có 1 link run Dependabot bỏ qua "Vercel deploy" mà các check khác vẫn xanh. Đóng Booking #39. |
| AA-816 | CIS #856 đã merge (11:41:30Z) và nằm trong Deploy Dev `1d16adf`; chạy `e2e-cognito.yml`. Chuẩn bị cutover theo root #112. | E2E xanh. Nghiệp xác nhận N-A…N-F, đặc biệt N-B và N-D. |
| AA-860 | Hoàn tất S20: đặt mật khẩu `db_migrator`, rồi probe. | Probe xanh và có link run. |
| AA-904 | Smoke 4 luồng trên preview (bản đồ Mapbox, search, /plan, gửi cho advisor bằng contact test), merge #107, verify prod. | Có ảnh chụp desktop/390, `npm audit` trên main = 0. |

**Đóng kèm:** AA-852 → Done, sau khi comment chuyển việc revoke grant 179/180 sang AA-847 và bỏ relation cũ với AA-826. Các đổi trạng thái ở §4 nếu Nghiệp đồng ý.
**Cuối phiên (Jira, gom một lần):** nháp AA-820 cho chị Thư, kèm bản draft điều khoản và mốc quyết định ~01/11.

### S245 (~20/10) — X1 S21 + cutover S1

| Issue | Việc | Cổng chất lượng |
|---|---|---|
| AA-860 | X1 S21: chốt thiết kế (policy `cis_owner` hoặc NO FORCE trên 8 bảng FORCE, view owner-rights), rồi mig 245 qua DB Migrate. | Review độc lập (migration và ownership). Chỉ apply khi bảng job rảnh. Probe xanh, 0 ô pending. Kiểm người đọc TP/catalog không bị trả về 0 dòng. Nghiệp duyệt Done-when (1) mới (x1-plan.md, ~dòng 70–76). |
| AA-816 | Stage S1: tắt `LEGACY_ADMIN_LOGIN_ENABLED` ở Production qua Vercel API, nếu Nghiệp cho phép đúng như đã nói. Thử break-glass qua managed login. Xoá `password_hash` legacy (script có review). Xoay `ADMIN_SECRET` ở 5 nơi. Chuyển secret `E2E_ADMIN_*` sang tài khoản viewer. Tắt `e2e-claude-code-2`. Bước E của root #112 (C9: check admin-secret theo principal + secret Preview chỉ quyền viewer) là một PR auth của CIS, cũng thuộc AA-816. **Xung đột lịch:** bước F (xoay `ADMIN_SECRET`) chạy `force-new-deployment` cho api + worker, và C9 cần deploy CIS, trong khi đường găng cấm deploy CIS trong cửa sổ S21. Làm E/F trước khi chép 245 sang Infra, hoặc sau khi apply 245 xong và probe xanh, không làm xen giữa. | Review (auth). `/api/auth/login` trả 404 trên Production. CI UI smoke trên Preview vẫn xanh: phải kiểm kỹ vì N-F tắt tài khoản password. Health của staff báo sẵn sàng. |
| AA-902 | Đóng: chạy lại regex trên main của 3 repo và đính kèm output. Mở PR thử cài account ID để thấy check đỏ. Cập nhật `docs/security/baseline.md`. Ghi quyết định về viết lại lịch sử git (đề xuất: không). Ghi quyết định về pool/client ID Cognito (đề xuất: coi là public theo OIDC và ghi ngoại lệ). Kiểm Infra #221 đã chuyển ID satellite cho task def CIS chưa; nếu chưa, lên PR trước 30/11. | 0 hit, ngoại trừ allowlist có hạn. Có link run đỏ. |
| AA-846 | Guard trong `terraform-apply.yml`: từ chối plan đụng `aws_secretsmanager_secret_version`, `random_password` hoặc `aws_db_instance`. Pin chính xác `required_version`. Đọc từng diff ẩn. | Review (CI/workflow). Một run bị từ chối đúng. Một lần apply toàn root với 0 thay đổi ở các resource trên. |
| AA-865 | Gộp retry r5–r7 (n≥60, $0), phân loại, khoảng tin cậy 95%. | Báo cáo trong `docs/audits`. Chỉ sửa code nếu tỉ lệ >8% (≤$1,5). |

**Đóng kèm:** AA-895 (baseline trỏ AA-902), AA-889 (khi CIS #854 đã merge và quét sạch).

### S246 (~21/10) — X1 S22–S23, đóng M1

| Issue | Việc | Cổng chất lượng |
|---|---|---|
| AA-860 | S22: secret cho task def migrator (H6, tay + MFA), DB Migrate / Dump / probe chạy dưới `db_migrator`, probe 246. Sau đó S23 close-out: docs, C2.2, skills, CONTEXT.md, lessons. Thử đường rollback một lần. | Probe 246 xanh, Schema Dump có PR bot, run DB Migrate ghi `ran as`. Done. |
| AA-816 | Gỡ A10: migration CIS mới (chỉ làm được sau S22), revert Infra #215, gỡ scope của CIS #849, tắt user và row. Bỏ `scripts/create_staff_user.py`. Sửa Done-when trong mô tả. | Review (migration + auth). E2E vẫn xanh. Done. |
| AA-680 | Nửa staff: lấy bằng chứng live user WORKFORCE không thuộc nhóm `booking-*` bị từ chối, gỡ cầu nối (`/auth/booking-token`, key JWT). Tách nửa khách hàng sang issue mới (nếu Nghiệp duyệt). | Review (auth). Log từ chối. Đăng nhập staff Booking vẫn chạy. |
| AA-886 | Trang `/privacy` và `/terms` (đánh dấu nháp) trên TripPlanner và portal, gắn link ở footer và form PII. Truy vấn kiểm việc lưu consent (DM-6.5). | UI verify, có link trên form gửi advisor. |
| AA-800 | Tách 3 lớp từ cấm, từ vựng chữ ký của tenant, quy tắc 1 của writer theo tenant. | Unit test giữ nguyên prompt vàng A1. Kiểm live A&H T2+T9 <$1 (cần duyệt). |

**Đóng kèm:** ghi AA-703 pha 1–2 xong. AA-887: front-matter cho 4 file CONTEXT.md, ghép vào PR kế tiếp của từng repo.

### S247 (~22/10) — bắt đầu M2a

| Issue | Việc | Cổng chất lượng |
|---|---|---|
| AA-729 | Chọn ~100 mẫu phân tầng, gắn nhãn (quyết định sẵn có + agent panel), báo giá, thử 3 mẫu, rồi chạy baseline. | Nghiệp duyệt bộ mẫu và chi phí. Mọi lời gọi qua `LLMClient`, stage `adhoc_aa729`. Báo cáo baseline. |
| AA-787 | Bỏ F8, F3, F5 và (nếu Nghiệp xác nhận lại) `promises_an_option`; gộp F7→F16, F15_voice_warn→F15, F2 thành một gate lexicon. | Số trước/sau trên golden set. UI verify tab Content Quality. CI xanh. |
| AA-845 | Điều tra 402 (~48k lần trong 14 ngày, rơi về rule mà không báo) và chọn nguồn nhãn. | Báo cáo đếm theo ngày so với lần nạp tiền. Alarm bắn thử. |
| AA-878 | Drift check về diff = 0. Xác nhận 2 orphan GitHub. Ghi quyết định smoke dùng admin. | PR có output diff = 0. Nghiệp revoke PAT/Mapbox. |
| AA-805 | Mở lại và chạy 4 kiểm tra còn thiếu: 429, `llm_spend_daily`, cache narration, join tour inactive (~$0,02). | Comment bằng chứng, đóng tay. Dùng trip có ít nhất 1 ngày không phải master. |

**Đóng kèm:** AA-890 (`gh api` cho 5 repo; danh sách DRY RUN nhánh đã merge của CIS, giữ lại nhánh còn PR mở).

### S248 (~23/10)

| Issue | Việc | Cổng chất lượng |
|---|---|---|
| AA-847 | L4 read model (materialize/tune `catalog.v_destination`), chạy parity tới ≤1,5x legacy hoặc <200 ms. Thêm vào scope: revoke 179/180, attribution Geoapify, property test của AA-674. | Review (migration catalog). Có số parity. |
| AA-780 | Thêm 6 câu sáo, cảnh báo broetry, kiểm tên địa danh trong hashtag. Viết lại Done-when theo checkpoint kế tiếp. | Unit test từ ví dụ r5. Nghiệp duyệt giọng Trail Pulse. |
| AA-779 | Đưa PAA vào `write_faq`, kiểm thực thể chính trong câu trả lời. Viết lại Done-when. | Unit test từ r4/r5. Đo ở checkpoint 8 blog. |
| AA-875 | Client `safe_http`, đưa mọi lời gọi ra URL do tenant cung cấp qua nó. | Review (bảo mật). 4xx live với địa chỉ nội bộ, site WP test vẫn publish được. |
| AA-888 | Job kiểm link và regex ID ở Infra và app repos. Một PR thử bị đỏ. | Có link run đỏ. |

### S249 (~24/10)

| Issue | Việc | Cổng chất lượng |
|---|---|---|
| AA-847 | Báo cáo hợp lệ nội dung (tab `/admin/places`), sửa HCM Trail và Kuang Si, lật flag. | Quan sát ngắn bằng burst test, không chờ 7 ngày (cần Nghiệp chốt). Verify live trên TP. |
| AA-790 | Gate giọng tenant cùng kiểm toàn vẹn sau repair (orphan thuộc issue này). | Nghiệp chọn LLM judge hay rubric. Pilot 20 mẩu, panel 4 góc. |
| AA-876 | Rate limit login (legacy, tenant), CORS, header, chặn Booking docs. WAF chỉ làm sau khi có báo giá. | Review (bảo mật). Test 429 live. |
| AA-844 | CloudFront + OAC + cert + DNS. Resolve host ở tầng app để khỏi phải sửa view. Lịch photo_sync hằng ngày. | Báo giá trước (vài USD/tháng). 2 lần chạy liên tiếp theo lịch. |
| AA-877 | Tag `pii:<class>` qua bk/tp migrations. | DB Migrate apply, regenerate reference. |

### S250 (~25/10) — đóng M2a

| Issue | Việc | Cổng chất lượng |
|---|---|---|
| AA-741 | G7: 12 tour × 4 tenant, rồi báo cáo G8. Loại các dòng test (`s237`, nhãn "ZZ S239"). | Duyệt chi phí ~$10–20. Báo cáo trong `docs/audits`. |
| AA-789 | Chỉ phần lexical recall: F15, F18, F13 paraphrase, F13_leak. | Unit test. Không bắn mới trên LinkedIn đã sạch theo panel. |
| AA-874 | Redis AUTH/TLS/at-rest, chuyển CIS api/worker sang trong giờ vắng, alarm cho flag. | Duyệt báo giá. Thử email ALARM→OK. Xác nhận Booking không dùng Redis. |
| AA-848 | Guard RLS trên DB replay: luật a–e, grant PUBLIC, allowlist (gồm bộ policy parity `USING(true)` của `cis_app`). | Mỗi luật có một run đỏ. |
| (mới) pip-audit | Bump langchain/langgraph, bỏ chromadb, chạy regression 3 tour. | Phải xong trước 30/11. Cần Nghiệp duyệt tạo issue. |

### S251 (~26/10)

- AA-893: sinh `alarms.md` và kiểm link. Bước 2 cần một OIDC role chỉ đọc, phải review IAM.
- AA-901: Nghiệp tạo GitHub App, agent mint token và mở một PR thử.
- AA-859: viết lại kế hoạch sau S22 (đánh số lại migration), làm D5b và wave 3.
- AA-825: mở lại, override Dev chạy thật một lần cho các kind retention của Booking, hoặc Nghiệp bỏ dòng Done-when đó.
- AA-783: chỉ làm phân tích nếu Nghiệp đã gắn nhãn.
- **Đóng kèm:** AA-888, nếu run theo lịch ngày 26/10 đã ra (kiểm nó có thật sự ghi `docs/generated/freshness.md` không).

### S252 (~27/10)

- AA-891: release-please, sau AA-901.
- Một lượt chạy place gộp: AA-712 + AA-905 + AA-784 (quốc gia thử). Điều kiện trước: viết lại `suggestions.py` sang HNSW (ADR 0007). Có báo giá.
- AA-803: dùng chung đợt gắn nhãn với AA-845.

(AA-712 + AA-905 + AA-784 là 3 issue, nên S252 đã đủ 5. AA-849 và AA-879 chuyển sang S253.)

### S253 (~28/10)

- AA-849: một run đỏ, đặt thành required check.
- AA-879: CI parity.
- AA-839: chỉ sửa chữ "GDPR" trên endpoint offboard (phần còn lại vẫn đỗ tới trước prod).
- N3 (nếu Nghiệp duyệt tạo): kiểm token guest cho các GET của TripPlanner.

### Phiên đầu tiên từ 01/11

- AA-896: báo cáo tháng 10 có đơn giá, cộng cả acc3 và credit.
- AA-838: capacity review đầu tiên, gộp access review của AA-878.
- AA-665: Cost Operations.
- Nháp Jira PR-20 kỳ 2.
- Kiểm AA-820.

### Sau S253

- AA-906 → AA-837 (cùng file trên TP).
- AA-855 UAT, khi Nghiệp ra hiệu.
- AA-821 nghiên cứu CRM.
- **Thứ tự bảo mật M5 (các mục "trước tenant trả tiền / trước prod"), mỗi phiên 1–2 mục, xen với phần còn lại:**
  1. AA-813: rescope theo ADR 0006 pha 3, rồi build (trước tenant trả tiền đầu tiên; Jira PR-14, PR-18).
  2. N2 (nếu duyệt tạo): nửa khách hàng của AA-680, Cognito EXTERNAL cho traveller (ADR 0006 pha 4).
  3. AA-873: GuardDuty, Access Analyzer, S3 BPA, CloudTrail (sau AA-846, từng mục có báo giá).
  4. AA-871: JSON log + Sentry cho Booking và TP, cộng dòng uptime Booking.
  5. AA-839: runbook xoá dữ liệu + DRY RUN (trước prod).
  6. AA-804: ADR nền tảng AI (0009) + ledger v2 + AI Use Register, quyết định PII DM-6.4 (trước prod).
  7. AA-861: redaction PII outbox TP (chưa có dòng nào quá 90 ngày trước ~01/2027).
  8. AA-880 khi có ngày go-live (cần AA-864 quyết trước).
- Phần còn lại của M5: AA-850, AA-851, AA-853, AA-826, AA-898, AA-814, AA-899 (sau AA-891), AA-894 (sau AA-893).
- M2a "để sau": AA-900 (sau AA-729), AA-795 (Nghiệp: còn cần không), AA-788 (sau AA-787), AA-765.
- M3 khi đã có quyết định thuế và thanh toán.

## 4. Đề xuất đổi trạng thái Linear (chỉ các đề xuất đã qua verify)

| Issue | Từ → Sang | Bằng chứng | Điều kiện |
|---|---|---|---|
| AA-852 | In Progress → **Done** | Cả 3 dòng Done-when đều có bằng chứng: `booking` 36/36 object thuộc `bk_owner`, `tripplanner` 17/17 thuộc `tp_owner` (db-schema-reference.md, Verified 19/10 06:00Z). Infra run 39191152573 có `aa-cis-dev-db-migrate:26` và "ran as: bk_owner"; run 39191437849 có "ran as: tp_owner". Probe 39 pass / 0 fail. | Trước khi đóng, comment chuyển việc revoke grant 179/180 sang AA-847 và bỏ relation cũ "blocked by AA-826". Scope dòng 3 (role `tripplanner` nằm trong migration, grant không guard) mới có một phần: rl-001 `ALTER ROLE tripplanner` không guard, tp-013 khai lại default privileges, nhưng không migration nào `CREATE ROLE tripplanner`. Ghi rõ điều này trong comment đóng. |
| AA-829 | Backlog → **In Progress** | Drill PITR S241 đạt (~22 phút, 148/148 bảng), `docs/audits/2026-10-17-S241-restore-drill/`; `restore-rds-pitr.md` có `last_tested: 2026-10-17`. | Còn: rehearsal cho 1 schema, CNAME, dump. |
| AA-849 | Backlog → **In Progress** | TP #96 (7e8ec2b) thêm job "Migrations (lint, PG 15 replay)", replay tp-001…015; TP #106 run 39241604810 đạt. | Còn: một run đỏ và đặt thành required check. |
| AA-846 | Backlog → **In Progress** | Infra #218 (pin TF 1.15.5 trên CI), #155 (`apply_method`), #211 (xoá .bak), CloudTrail dùng `local.shared_tags`. | Còn: guard apply, diff ẩn, pin `required_version`. |
| AA-826 | Backlog → **In Progress** | Infra #163 (eef43c0b): `db/owners.yaml`, `test_owners_registry.py`, `roles/` rl-001. | Nghiệp duyệt Done-when mới, vì thiết kế đã chốt là dùng hằng số mirror có guard, không phải "không cần sửa code". |
| AA-825 | Done → **In Progress** (mở lại) | Done-when bổ sung ở S238 (15/10) yêu cầu chạy thật một lần cho Booking. Comment đóng (16/10) chỉ có DRY RUN với 0 ứng viên. Lịch EventBridge vẫn chỉ ở DRY RUN. | Hoặc Nghiệp bỏ dòng Done-when đó trong một comment. |
| AA-805 | Done → **In Progress** (mở lại) | TP #76 merge 23:45:47Z, Done tự động lúc 23:45:49Z. `aa805-evidence.md`: "must not be set to Done yet". 4 dòng còn mở. Burst S239 ghi 0 lần HTTP 429, nên dòng 429 chưa hề được chứng minh. | Chạy xong 4 kiểm tra rồi đóng tay. |
| AA-665 | Done → **Todo** (mở lại) | Đóng tự động bởi CIS #475. Comment của Nghiệp 05:21:56Z: "the rest … is still open". `page.tsx:664` vẫn là "External Spend", có 4 tab, bảng `<table>` thô. | Todo chứ không phải In Progress, cho tới khi có người làm. |
| AA-669 | Done → **Todo** (mở lại) | Đóng tự động bởi CIS #556, không có comment. `ReviewList.tsx` thiếu place/topic, words, published-at, lọc theo ngày, duplicate/regenerate, các saved view có sẵn. | Hoặc Nghiệp chấp nhận phần đã giao và đóng kèm comment rescope. |
| AA-675 | Done → **Canceled** | Chỉ 56/121 tour, job theo wave chưa bao giờ xây (comment AA-731 S225). Phạm vi chuyển sang AA-712/AA-905 (ADR 0002). | Comment đóng trỏ sang AA-712 và AA-905. |
| AA-689 | Done → **Canceled** | Done-when pha A không đạt. Epic bị đóng 20 phút sau comment "Parked". | Comment ánh xạ: A → AA-812 + property test; B sign-in → AA-680/AA-703 pha 4; B "My itineraries/share/PDF" → chưa có chủ (hỏi Nghiệp); C → AA-708/AA-712; D → AA-704. |
| AA-680 | Giữ In Progress, **tách** | Nửa staff đã live (Booking #34/#35/#36, Infra #199). Nửa khách hàng chưa bắt đầu. | Nghiệp duyệt tạo issue mới cho nửa khách hàng. Viết Done-when riêng cho nửa staff. |
| AA-674 | Giữ Done, thêm comment sửa | Property test 20 bộ pin ngẫu nhiên chưa có (`test_coverage.py` chỉ có 7 case viết tay). | Đưa property test vào scope AA-847. |
| AA-902 | Không đổi | Đã mở lại đúng lúc 10:00:40Z, đang In Progress. | — |

**Đề xuất bị verify bác (giữ nguyên):**

- AA-895 Done: baseline chưa trỏ tới AA-902. Đóng ở S245.
- AA-859 về Backlog: wave 2 đã live, và rào cản thật là đánh số migration/S21 chứ không phải đóng băng view. Giữ In Progress kèm comment.
- AA-868, AA-870, AA-892, AA-707, AA-763, AA-843, AA-719, AA-726, AA-885, AA-883, AA-662, AA-681, AA-676: giữ Done. Một số issue chỉ cần thêm comment bằng chứng.
- AA-842 Done: Nghiệp đã quyết ở S238 giữ làm placeholder.
- AA-790 tách, AA-780/AA-788 gộp: dữ liệu r5 bác, mục tiêu gộp cũng sai.
- AA-781/AA-628 Canceled: chỉ huỷ khi Nghiệp quyết.
- AA-813, AA-682 tách: chỉ rescope hoặc viết Done-when.
- AA-710 Done: chưa ánh xạ gap, chưa trả lời KAN-20.

## 5. Khoảng trống cam kết chưa có issue

| Cam kết | Tình trạng | Đề xuất |
|---|---|---|
| AA-820: điều khoản AI phải xong trước 12/11 | Chưa có Jira nào đưa bản draft cho chị Thư | Nháp Jira cuối S244 và thêm dòng §1 "~01/11 quyết định luật sư" |
| AA-902: pool/client ID Cognito | Scanner không bắt. Còn trong CIS `CONTEXT.md`, `identity_config.py`, test e2e, impl notes; Booking `identity_config.py`, `cognito.ts` | Nghiệp chọn: coi là public và ghi ngoại lệ SEC-06/D-25, hoặc chuyển ra config |
| PR-11: CloudFront + đồng bộ ảnh hằng ngày (hứa 01/10) | AA-844 không có trong backlog | Đưa vào §3 (S249) và báo chị Thư mốc mới |
| ADR 0006a: gỡ hẳn legacy login 30 ngày sau cutover | Không issue nào nhận | Dòng §1 "+30 ngày" và một scope line trên AA-703. Cập nhật bảng trạng thái ADR 0006a. |
| pip-audit hết hạn 30/11 và 31/12 | Không có issue | Tạo issue mới (N1) |
| ADR 0007: attribution Geoapify; HNSW trong `suggestions.py` | Không có trong Done-when nào | Thêm scope line vào AA-847, AA-784, AA-905 |
| TripPlanner: GET của guest chưa kiểm token (`CONTEXT.md:157`) | Không có issue | Tạo issue mới (N3) |
| Baseline: role apply quá rộng (inline policy 9.559/10.240 ký tự) | AA-806 đã Done | Thêm scope line vào AA-846 |
| Jira PR-14: tenant đăng nhập, Google/Facebook | AA-813 đỗ, chưa có ngày | Rescope AA-813 theo ADR 0006 pha 3. Dòng §2 về xác minh app Facebook. Báo chị Thư rằng Google cho staff đã bỏ theo quyết định. |
| Jira PR-12: wave 3 Booking | AA-682 xếp hàng 23, ưu tiên Low | Viết Done-when, báo chị Thư thứ tự thật |
| Jira PR-17: phản hồi về giọng | Không có issue theo dõi | Dòng §2. Khi chị Thư trả lời, chuyển vào AA-800 |
| Jira PR-18: quản lý tenant (tạm ngưng/ngừng/khôi phục, tenant chỉ thấy nội dung) | Comment 10486 (19/10) hứa còn: tenant đăng nhập bằng mã email, và "chế độ xem hỗ trợ" cho nhân viên. Mã email → AA-813. Chế độ xem hỗ trợ: không tìm thấy issue nào. Xoá dữ liệu tenant ngừng hợp tác → AA-839 | Báo cáo PR-18 khi AA-813 xong. Hỏi Nghiệp có cần issue cho chế độ xem hỗ trợ không |
| Jira PR-7: social media pipeline (tenant viết bài) | Báo lần cuối 16/10 (10480). Không có slot báo cáo tiếp | Báo một lần sau khi M2a đóng (S250: AA-787/790/800/780/779 + G8 của AA-741) |
| Jira PR-13: Jev decision layer | Không có trong kế hoạch | Gắn với AA-845 (S247) và AA-803 (S252); báo sau S252 |
| Jira PR-9 (content upload update), PR-21 (báo cáo kỳ 1) | PR-9: chưa ánh xạ được sang issue Linear nào (unknown). PR-21: đã đăng 19/10 | PR-9: Nghiệp xác nhận còn việc hay đề xuất đóng. PR-21: đề xuất đóng cùng lúc nháp PR-20 kỳ 2 (~02/11) |
| Data standards, mục mở #8/#9 | Không có chủ | #9 vào AA-838, #8 vào AA-839/AA-861 |
| Lessons có thể thành guard: smoke 390 px `scrollWidth <= innerWidth` | Chưa có | Chore nhỏ. Xoá các dòng 41/81/116/145 vì guard đã có |
| Drift tài liệu | Backlog §4 (AA-807 đã Done; AA-835/837/838/839 ghi "Approve creating"); `ecosystem-architecture.md` §4.6 + domain portal; handbook §9 còn trạng thái cũ; heading ADR 0004a; Booking `CONTEXT.md:438`; TP CONTEXT có 2 dòng cũ | Sửa trong một root PR. Riêng app thì làm qua AA-889. |

**Đề xuất tạo issue mới (hỏi Nghiệp trước, không tự tạo):**

- **N1** [CIS] Bump langchain/langgraph và bỏ chromadb trước 30/11 (S). Đặt ở Data Platform cho tới khi CIS Core có chỗ.
- **N2** [Identity] Nửa khách hàng tách từ AA-680: Cognito EXTERNAL cho traveller, liên kết guest TP, My Trips (XL, đỗ tới ADR 0006 pha 4). Project TripPlanner & AA-Booking.
- **N3** [TripPlanner] Kiểm token guest cho các GET đọc trip, suggestions, coverage, activities (S).
- **N4** [Booking] UI ở 1440 (bảng cuộn ngang, cột FX bị xuống dòng, scrollbar 1 px) và audit row cho room type/rate và cho V1 bị superseded (S).
- Có điều kiện, nếu Nghiệp muốn:
  - Main pool hiểu GUC, tức RLS thật trên pool admin (~69 file), theo quyết định của AA-860.
  - "My itineraries/share/PDF" (phần còn lại của AA-689).
  - Bulk publish qua `shared.job` (scope 4 của AA-726).

**Chỉ thêm scope line, không tạo issue:**

- 179/180 revoke và property test → AA-847.
- Booking uptime → AA-871.
- Phần còn lại của AA-892 (`deploy.md` từng app, playbook SES, chuyển draft sang active) → AA-888.
- Follow-up của AA-799 → AA-765, sau khi kiểm AA-882.

## 6. Việc chờ Nghiệp và chị Thư (xếp theo mức chặn đường găng)

1. **Chặn M1, cần ngay:**
   - Xác nhận N-A…N-F của AA-816, nhất là N-B (xoá hash break-glass) và N-D (để phiên cũ tự hết hạn trong 24h).
   - Cho phép agent sửa biến có dấu gạch dưới qua Vercel/GitHub (`LEGACY_ADMIN_LOGIN_ENABLED`, `E2E_ADMIN_*`), nếu không thì Nghiệp tự sửa.
   - Duyệt Done-when (1) mới của AA-860.
   - Secret task def H6 cho S22 (tay + MFA).
   - Đăng ký TOTP break-glass vào app.
2. **Chặn đóng AA-902:** quyết định viết lại lịch sử git (đề xuất: không) và pool ID Cognito có coi là public hay không.
3. **Chặn M2a:**
   - Xác nhận lại việc bỏ `promises_an_option` (AA-787).
   - Chọn loại gate (AA-790).
   - Duyệt bộ mẫu và chi phí golden set (AA-729).
   - Duyệt khoản <$1 cho AA-800 và ~$10–20 cho G7.
   - 2–3 giờ gắn nhãn cho AA-783.
   - Chọn nguồn nhãn cho AA-845.
   - Xem trường giọng Trail Pulse (AA-780).
4. **Bảo mật, không chặn đường găng nhưng rủi ro cao:**
   - Xoá hoặc mã hoá dump 2026-09-16 (AA-829). Treo từ S238.
   - Revoke PAT và token Mapbox.
   - Duyệt báo giá AA-874, AA-876 (WAF), AA-873, AA-844.
5. **Quyết định cấu trúc:**
   - Tách issue cho AA-680.
   - Rescope AA-813.
   - AA-864: có còn muốn dời account không (CLAUDE.md S235 nói prod ở acc2). Cần quyết trước AA-880.
   - Tạo GitHub App (AA-901 → AA-891).
   - Tách project "Platform engineering / SDLC" ra khỏi Data Platform.
6. **Việc tay chưa có trong §2:** sửa `~/.claude/CLAUDE.md` (bỏ handoff.md, bỏ nhắc dừng ECS, bỏ số task-def/CI; ghi luật merge theo giai đoạn), bật tag `Environment` ở payer, chính sách payer U-10(c).
7. **Chị Thư:**
   - AA-820, cần trước ~01/11.
   - Câu chữ AA-886.
   - Kế hoạch CRM (AA-821).
   - Thuế, % đặt cọc, lịch thanh toán (AA-682).
   - Margin seed (AA-810).
   - Quyền dùng ảnh (AA-708; ảnh đã public).
   - Phản hồi giọng PR-17.
   - Gộp Marketplace với Browse Tours (AA-671).
   - Duyệt đóng các Jira đã xong: PR-1, PR-6, PR-10, PR-15, PR-16, KAN-90 (agent nháp, Nghiệp duyệt).

## 7. Gộp, huỷ, đỗ và hạn mức

- **Huỷ (đã verify):** AA-675, AA-689 (Done → Canceled).
- **Đỗ, giữ Backlog:** AA-842 (quyết định S238), AA-781, AA-628, AA-782, AA-704, AA-697, AA-655, AA-671, AA-710, AA-839, AA-881 (trigger 05/2027), AA-880 (chờ ngày go-live).
  - AA-781 và AA-628 chỉ huỷ khi Nghiệp quyết, ví dụ vì hạn mức.
- **Làm rõ phạm vi để khỏi làm hai lần:**
  - Orphan sau repair thuộc AA-790; chủ thể câu FAQ thuộc AA-779; AA-789 chỉ giữ phần lexical.
  - AA-803 và AA-845 dùng một đợt gắn nhãn.
  - AA-712, AA-905, AA-784 chạy chung một lượt place.
  - Access review chỉ làm một lần trong AA-838, AA-878 trỏ sang.
  - AA-889 dòng 3 và AA-888 "job chặn ID" được AA-902 giao luôn.
  - AA-837 làm sau hoặc gộp vào AA-906 vì sửa cùng file.
- **Đảo ưu tiên:**
  - AA-901 (Medium) chặn AA-891 (High). Đề xuất nâng AA-901 lên High, hạ AA-891 xuống Medium.
  - AA-875, AA-876 là phát hiện P0 nhưng đang Medium. Đề xuất nâng lên High.
  - Các đề xuất ưu tiên chưa qua verify; Nghiệp chốt.
- **Done-when cần sửa:**
  - AA-860 (1); AA-826 ("no code edit").
  - AA-887: chỉ có 4 file CONTEXT.md, không phải 5.
  - AA-780 ("r5"), AA-779 ("r6"); AA-729 dòng 3 (AA-724).
  - AA-804: đổi "ADR 0006" thành 0009.
  - AA-837: light-only hay cả dark?
  - AA-847: watch 7 ngày mâu thuẫn với luật "dev không chờ".
  - AA-898: thêm N-3 (owner-only) và K-15.
  - AA-816 và AA-858: mô tả còn cũ.
  - AA-861: tiêu đề còn chữ "blocked".
  - AA-682 và AA-671: chưa có Done-when.
- **Hạn mức:**
  - CIS Core 96/100, khoảng 60 issue Done trước 16/10. Issue mới cho nội dung CIS (N1, follow-up gate) phải đặt project khác cho tới khi có chỗ.
  - Data Platform 55/100, Portal 41/100, TP & Booking 34/100.
- **Giới hạn WIP:** đề xuất tối đa ~8 issue In Progress. Sau S247, số In Progress phải giảm từ 17 xuống ≤10 nhờ các bước đóng kèm.
- **Phòng Done giả:** Linear tự đóng issue khi PR có ID trong title/body/nhánh (AA-902 qua root #109, AA-805, AA-665, AA-669, AA-662, AA-707, AA-719). Không để ID trong title PR, và kiểm thiết lập GitHub integration của Linear.

## 8. Giới hạn của audit

- **Chưa kiểm được:**
  - AWS live (profile cần MFA): các check hằng ngày ở §1 (reconcile 06:15 UTC, Lambda snapshot 22:00 UTC) và trạng thái SES production.
  - Secret repo GitHub (hook chặn `gh secret`): 2 orphan của AA-878 và `AWS_DEPLOY_ROLE_ARN` của TP.
  - Memory Notion.
- **Dữ liệu AA-902 lệch theo thời điểm:** lane audit ghi TP #105 còn draft và chưa có PR Infra. Lượt verify sau đó ghi TP #105 merge lúc 11:42:55Z và Infra #221 merge lúc 11:37:46Z. Lượt critic (~12:00Z) xác nhận thêm CIS #854/#855/#856 và Booking #45/#46 đã merge. Infra #221 có sửa `modules/ecs/main.tf` và `variables.tf` (biến satellite cho api/worker), nhưng chưa kiểm Terraform apply đã chạy cho nó chưa.
- **Done cũ:** trong 68 Done của CIS Core, các issue đóng trước 14/10 chỉ được kiểm mẫu.
