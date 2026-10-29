# S257 (29/10/2026): Facts Entry, job TripPlanner + xoá PII outbox, bot đồng bộ migration và UI kit, ADR 0012 Accepted, geocode v2

Tác nhân: **Claude Code** (Ultracode; nhiều lane song song + workflow). 29/10 10:16 → ~14:45 +07
(MFA acc2 hết hạn ~16:35 +07). Chạm hạn mức 5 giờ ~11:50, reset 12:10, các lane chết được chạy lại bằng workflow resume.
Số liệu cuối lấy từ `docs/audits/2026-10-29-S257-session-close/state-snapshot.md` (chụp 14:45 +07).

## Quyết định của tech lead (trong phiên)

- Đầu phiên: agent tự chọn 20 việc, **coi như đã duyệt**; việc cần duyệt thì **duyệt theo kế hoạch**; chạy liên tục,
  không tự dừng. Theo duyệt kế hoạch đó: chấp nhận ADR 0012 (AA-880), duyệt pilot sơ đồ AA-697, xoá EFS
  `aa-cis-dev-efs` sau DRY RUN, lần chạy thật đầu tiên của job xoá PII outbox TripPlanner (AA-861, `max_rows` 10).
- 12:10: "tiếp tục" sau khi hạn mức reset.
- ~13:10: tech lead **tắt auto mode** cho cửa sổ apply EFS local ("Đã tắt").
- **GuardDuty: "Chưa dùng"** — vẫn tắt (AA-873).

- **~14:49: acc3 hết gói $250 của eCloudvalley** (tech lead chuyển tin nhắn nhà cung cấp): từ 29/10 chi phí acc3 tính vào thẻ của công ty; "sử dụng cân nhắc, xem còn nhiều nội dung cần Bedrock không". Kiểm Billing → Credits của acc3 (tech lead, console): AWS Lift credit $250 (01/09 → 31/12/2026) còn **$249,94**, bill acc3 trừ vào đó trước rồi mới tới thẻ (model bán qua Marketplace như OpenAI-on-Bedrock có thể không được credit trả). Lệnh `freetier get-account-plan-state` chỉ báo credit Free Plan ($0), không dùng làm số dư credit. Tech lead chọn hướng 1 (bật lại OpenAI trên Bedrock): agent tạo agreement Marketplace cho gpt-5.6-luna (gpt-6-luna đã có); gọi thử vẫn AccessDenied sau 6 phút → cần kiểm phương thức thanh toán của acc3 / chờ Marketplace kích hoạt. Agent đã đổi luật: mỗi lượt chạy trả phí phải nêu USD + lý do trước, không chạy thử "để xem". Chọn hướng cho các stage judge đang dùng luna (bật lại model OpenAI trên Bedrock cho acc3 hay chuyển sang Claude Haiku) là việc chờ tech lead.

## Done / ship (kèm bằng chứng)

| Việc | Kết quả |
|---|---|
| **AA-814 Done** | Facts Entry: mig 302 CIS #1138 `bd8df505` (Infra copy #495 do **bot migration-sync mở và merge**, DB Migrate check 40827525440 / apply 40827788951 `ran as: cis_owner`, schema dump #325 tự merge) + CIS #1141 `d8fce643` (API + thứ tự ưu tiên trong writer + trang Facts admin; review độc lập fix_then_ship → đã sửa) + Partner #120 `767b686b` (trang Facts trong Content studio) + root #324 (cờ `aa814:facts_pool`). Live (api :912 / worker :478 `070dd7ba`): tenant tạo fact 201 `fact_5e51d64df5`, PATCH 200, `expected_updated_at` cũ 409, id lạ 404, `tenant_id` trong body 422; RLS: tenant khác 0 / Atlas & Hearth 1; seed T9 kế tiếp trích `[Fact id=fact_5e51d64df5]`; ảnh portal 1440 + 390; fact thử đã xoá. $0. `docs/audits/2026-10-29-S257-aa814-live/`, `ui-evidence/portal-facts-*` |
| **AA-861 Done** | TripPlanner #183 `35e294b7` (tp-021: `tripplanner.job` theo template + `outbox.redacted_at`) → Infra copy #496 **bot mở và merge** → DB Migrate check 40828291999 / apply 40828480157 (`ran as: tp_owner`) → ERD root #323 `2f991c17` → schema dump #326 tự merge. Infra #497 `c2aa8f58` (CI apply 40828964167: 12 add, 1 change): Lambda `aa-tripplanner-dev-jobs` + lịch `-daily` ENABLED + 2 alarm. TripPlanner #185 `a694a88a` (Deploy Lambdas 40829525622, verify sau deploy). DRY RUN 90 ngày: 0 dòng; DRY RUN override 3 ngày: 7 dòng có liên hệ; **chạy thật** `d0cb7915`: redacted 0, `remaining_with_contact = 0`; relay Booking `bk_inquiry_pull` vẫn chạy (122 succeeded / 3 giờ) |
| **AA-697 Done** | Pilot sơ đồ chuẩn AWS được duyệt theo kế hoạch phiên; ghi ở `docs/architecture/diagrams/README.md`, catalog ARCH-01, roadmap handbook — root #320 `daf49f7a`. README sơ đồ giữ `status: draft` tới khi tech lead tự đọc trang |
| AA-880 (In Progress) | **ADR 0012 "Environment model" Accepted** (root #320 `daf49f7a`): data standards **v1.8** (C7.2b/c/d), handbook + guide vai trò + runbook DB Migrate. Còn: blueprint L9 (Terraform plan prod + chi phí) khi có ngày go-live |
| **EFS** (theo sau AA-697) | Infra #492 `e67b7bcb` (bỏ module, access point, SG) + apply local trong cửa sổ tắt auto mode: 6 destroyed, `describe-file-systems` = 0 |
| **ecsx local mode** (bảng 0z) | Root #318 `45e67328`: chạy script trong container Booking / CRM không cần S3 (task role Booking không ghi S3); smoke Booking đạt |
| AA-993 (In Progress) | **M3** Infra #493 `9a069a99` (migration-sync + migration-apply, expand auto-apply mặc định tắt; review độc lập: 1 blocker "apply vượt khoảng trống" + 5 lỗi nhỏ đã sửa; 939 test db). Chứng minh: bot `aa-ecosys-ci-bot` mở và merge Infra #495, #496, #498; **M1** schema dump tự merge #325, #326, #329. **M4b** schema-gate + Migration preflight: CIS #1145 `b1d209e6`, Booking #146 `541d3035`, Partner #121 `03918c0b` (Schema gate Partner xanh). ⚠️ Cron `*/10` của `migration-sync.yml` **chưa chạy lần nào theo lịch** trong ~2 giờ sau merge (6 run đều `workflow_dispatch`); copy #495 / #496 / #498 chỉ được bot mở + merge sau khi dispatch tay → Done-when "không bước tay" **chưa đạt**. Còn (dời S258): proof bk-034 + `DB_AUTO_APPLY`, M5 (root #328 cố ý để mở), đo lead time ≥ 5 PR |
| AA-998 (In Progress) | Infra #491 `8c2b028c` (bỏ tham chiếu acc1-bedrock cũ) + bằng chứng grep 6 repo root #319 `5e812439` (`docs/audits/2026-10-29-S257-aa998-acc1-grep/`: 0 đường code/config sống). Done-when 1, 2, 3, 5 đạt; còn Cost Explorer acc1 tháng 11 (đầu tháng 12) |
| AA-994 (In Progress) | **S3s** bot đồng bộ kit: CIS #1133 `715582fd` + root #321 `b6aca97f`; dry run `kit-sync.yml` 40823853268 đạt; **PR đồng bộ thật đầu tiên** (sau S4a) Partner #119, Booking #144, TripPlanner #184 (đã merge). **S4a** CIS #1137 `fc224ff6` (đưa layout/filter/menu/confirm/format của Booking vào kit core); **S4b** Booking #145 `216cb5e6` (frontend Booking dùng kit core vendored, merge 14:18 +07). CIS #1142 `652b255f` (Kit consumers strict cho Booking) đã merge. Còn: S5a/S5b TripPlanner, phase 6, H3 |
| Viewer cta-check (bảng 0w) | Live bằng user studio đổi tạm sang viewer (audit `tenant.member_role_changed` + feed): viewer gọi `POST /v1/content-writing/cta-check` → 200, lệnh ghi → 403; trả lại owner. `docs/audits/2026-10-29-S257-viewer-cta/` |
| Theo sau AA-671 | Partner #117 `fac5ea8e` (icon chip giá không còn co thành dấu `·`, các mức giá một dòng; ảnh live PASS `ui-evidence/portal-tours-*`). CIS #1131 `978ea46c` (ảnh bìa dự phòng theo điểm đến chính) → **+0 tour** vì 0/3.232 `place_photo` có `destination_id` → job khớp ảnh ↔ điểm đến: mig 303 CIS #1143 `b683b241` + copy Infra #498 (bot) merged; code CIS #1144 `2e8e10a3` **merged + live** (api :913 / worker :479): dry run `photo_destination_match` `6e8b5043` khớp 1.593 (exact 1.079 / name_in_label 495 / core 19; weak 137; ambiguous 120; no_match 779) → apply `69659af9` ghi 1.593, 283 điểm đến có ảnh, open_after 1.036 → pool ảnh bìa phủ **162 → 302 / 892** tour |
| C4.3 tuần W44 + TripPlanner perf | Xem đoạn C4.3 bên dưới; TripPlanner #181 `7118a92d` (đọc địa điểm nhanh, ảnh trang điểm đến cùng origin), probe chỉ đọc Infra #494. Lighthouse mobile production: `/destinations` LCP 3,38 → **2,46 s** (perf 97); `/destinations/bhutan` 3,95 s (không đổi, chưa đạt); trang chủ 1,62 s, trang tour 1,54 s (`lighthouse-prod-after-s257.json`). TP #187 `84df8e0f` (test HNSW so khoảng cách, hết đỏ ngẫu nhiên). `docs/audits/2026-10-29-S257-aa995-tp-perf/` |
| Test chập chờn feed CIS | CIS #1130 `e886d865`: nguyên nhân thật là `ORDER BY` theo alias text của cột xid8 (`'10' < '9'`), không phải thiếu tie-breaker như S256 đoán; guard unit + integration txid 7…1000 |
| AA-919 (In Progress) | CIS #1132 `eba2ab7f` (kappa theo stratum, sửa script diag, harness so model judge). So model `21ca49c6` (stage `adhoc_aa919`, **$0,665**): gpt-5.6-luna **0,562** (tốt nhất, rẻ nhất), gpt-6-astra 0,435, gpt-6-luna 0,054; chưa model nào ≥ 0,6 → `judge_counts` vẫn false. Thiếu cặp Facebook (cần 3 đạt + 3 trượt). `docs/audits/2026-10-29-S257-aa919-judge-compare/` |
| AA-790 (In Progress) | Vòng 10 (cờ `T9_READER_CHECKLIST_MODE`, CIS #1135 `d085620e`, mặc định tắt): A/B ≈ **$0,99** + panel mù 40 mục — reader_value **−0,25** (ngưỡng ≥ −0,15) → **FAIL**, cờ tắt, vòng 6 giữ live. Đề xuất: dừng vòng prompt trên harness này; mẫu cố định ≥ 20 bài + hiệu chuẩn judge trước. `docs/audits/2026-10-29-S257-aa790-r10-panel/` |
| AA-789 (In Progress) | CIS #1140 `0c4dd6a6` (rev 4: chỉ giữ pattern chính xác; 3 vòng verifier 13 → 8 → 10 FP, verifier thứ tư **0 FP**; 194 unit test). Đề xuất đóng Done-with-scope (phần regex đã hết), chờ tech lead |
| AA-900 (In Progress) | CIS #1136 `22d1b704` (prompt register, runbook eval, nhãn `adhoc_aa900`) + root #322 `63fa7e77` (bảng route LLM sinh từ route thật, catalog APP-06). R2 eval `228447e7` (job `462f72ee`, stage `adhoc_aa900`): lượt **không hợp lệ** (~$0,107) vì luna trên acc3 trả AccessDenied sau khi acc3 rời Organization (Sự cố 9), cần chạy lại. Guard test "nhãn không bao giờ đổi route / account" ở nhánh CIS `fix/aa-900-adhoc-label-account` (`7fbbbc6e`, chưa push) |
| AA-997 (In Progress) | Audit giữa chừng (chỉ đọc, $0): chuỗi relocate 1.621 / 3.842 dòng; độ đúng mẫu 600 dòng **75,4 → 77,7 %**, dự phóng khi xong ≈ **79,5 %** (không tới 90 % bằng chuỗi này). v2 CIS #1139 `070dd7ba` (luật chặt `aa997.2`, biến thể truy vấn, recheck, ẩn/hiện — **mặc định tắt**). **P4 FAIL**: luật chặt từ chối 34/251 = 13,5 % dòng đúng (ngưỡng ≤ 2 %) → `aa997.2` giữ tắt, không apply. `recheck_14`: route 13/16, xác nhận hết 1/16. `docs/audits/2026-10-29-S257-aa997-interim/` |
| AA-842 (Backlog, báo cáo xong) | Báo cáo OTel gen_ai (648 dòng) `docs/audits/2026-10-29-S257-aa842-otel/` + Notion: chưa có tracing LLM; 41 call site qua một gateway; đề xuất phương án B (span gen_ai mỗi lệnh logic + span con mỗi attempt, X-Ray Transaction Search < ~$2/tháng Dev). Spike chờ tech lead duyệt; trạng thái giữ theo Done-when |
| Bot / release | Release TripPlanner 0.12.0 (#182 `14280c1b`), Partner 0.9.1 (#118 `04756799`). Lúc chụp 14:45 còn mở: CIS #1134 (0.16.0), Booking #147 (0.12.0), TripPlanner #186 (0.13.0), Partner #122 (0.10.0), root bot #327 (infra docs) — **cả 5 merge lúc chốt** (release chỉ đổi version); root #328 (AA-993 M5) cố ý để mở |

### C4.3 tuần W44

Probe 29/10 (`docs/audits/2026-10-29-S257-c43-w44/`): `pg_stat_statements` 9.438 statement, `stats_reset` 07/10; lock
chờ 0, deadlock 0, cache hit 99,07 %. Lần "trượt" của TripPlanner browse (đọc địa điểm 25 tour 2,5 s) **là cùng số cũ**
cộng dồn (calls 4.140 → 4.141) — đo lại trực tiếp (probe Infra #494, run 40822241134): Seq Scan `tour_atoms` trong view
`tour_destinations`, trong đó JIT chiếm `jit_ms` 3.042–3.364 mỗi lần (nguyên nhân chính). TripPlanner #181 sửa đường đọc:
25 tour **2,5 s → 0,31 s** (Dev).

## Sự cố

1. **Hạn mức 5 giờ** chạm ~11:50 → nhiều lane chết cùng lúc; 12:10 reset, chạy lại bằng workflow resume (giữ lane đã xong).
2. **Push giữa lúc rebase còn xung đột** (CIS #1144): chỉ commit đầu lên GitHub; phát hiện và đẩy lại.
3. **Test HNSW TripPlanner đỏ ngẫu nhiên** trên push main sau TP #181 → chặn Deploy Lambdas; sửa TP #187.
4. **Kit consumers**: bước kiểm toàn vẹn đặt trước `npm ci` → "eslint: not found" che lỗi thật (CIS #1133, sửa trong PR).
5. **Fallback ảnh bìa CIS #1131 +0** vì dữ liệu nguồn rỗng (0 ảnh có `destination_id`) → thêm job khớp ảnh (mig 303, CIS #1144).
6. **Cron `migration-sync` không chạy theo lịch** ~2 giờ sau merge (AA-993 M3) → chưa bật `DB_AUTO_APPLY`. Lượt Migration Apply
   đầu cảnh báo artifact schema dump trên main đã hết hạn (lượt dump đêm sẽ phục hồi).
7. **AA-900 R2 `462f72ee` không hợp lệ** (~$0,107), phải chạy lại.
8. AA-997: job chuỗi `aa997.1` còn xếp hàng (30/10 00:13Z) có thể từ chối khi đổi phiên bản luật — kiểm đầu phiên sau.
9. **acc3 rời AWS Organization lúc 06:50 UTC** (CloudTrail: `organizations.amazonaws.com` xoá `AWSServiceRoleForOrganizations`;
   `describe-organization` → không còn là thành viên). Ngay sau đó model OpenAI-on-Bedrock trên acc3 (gpt-5.6-luna, gpt-6-luna)
   trả AccessDenied "not available for this account"; Claude trên acc3 vẫn chạy. Mọi stage judge route sang luna (t2_judge,
   t10_judge, s1_judge, writing_memory_eval, …) có rủi ro; lối cuối OpenAI API hết credit (429). R2 AA-900 `228447e7` không hợp
   lệ vì lý do này ($0,107). Probe nhỏ gpt-6-luna sau đó không ra kết quả (chưa kiểm được). Chờ tech lead: hỏi reseller
   (eCloudvalley / TrueIDC) vì sao acc3 rời org (billing, credit AWS Lift) và quyết nạp credit OpenAI. Guard test nhãn ↛ route /
   account ở nhánh CIS `fix/aa-900-adhoc-label-account` (`7fbbbc6e`, chưa push — điều phối có thể push).

## Chi phí

- LLM (khoảng, chưa đối chiếu `shared.llm_call_log` lúc soạn): AA-919 so model judge $0,665 + AA-790 vòng 10 ≈ $0,99 +
  AA-900 R2 lượt không hợp lệ $0,107 + probe luna ≈ $0 → **khoảng $1,77**. AA-814, AA-861, AA-997 P4 và audit giữa chừng: $0.
- AWS mới/tháng: Lambda jobs TripPlanner + 2 alarm ≈ **$0,20**; EFS `aa-cis-dev-efs` đã xoá (≈ $0 tiết kiệm, bớt 2 mount
  target / ENI). GuardDuty vẫn tắt (0).

## Trạng thái kiểm cuối phiên

Xem `docs/audits/2026-10-29-S257-session-close/state-snapshot.md` (14:45 +07; STS acc2 OK):

- ECS: CIS api :913 / worker :479 cùng dev-`2e8e10a3` (CIS #1144); Booking api :86 `216cb5e6`; CRM api :77 `03918c0b`; CRM web :49 `04756799` (portal 0.9.1); cả 5 COMPLETED 1/1, revision mới nhất = revision đang chạy.
- `/health/ready`: CIS ok, schema 303, git `2e8e10a3`; Booking ok `bk-033`; portal `/healthz` ok `04756799` (0.9.1); TripPlanner `/api/health` ok `d98ebef7` (báo 0.11.1; commit release 0.12.0 / 0.13.0 không deploy lại); Lambda browse / assembly / jobs deploy 07:04 UTC, cùng CodeSha256 `2W+JYzCH…`.
- Migration mới nhất: CIS 303 (302, 303 áp hôm nay), Booking bk-033, TripPlanner tp-021 (áp hôm nay), CRM crm-023; `DB_AUTO_APPLY` chưa đặt.
- Vercel: TripPlanner production `d98ebef7`; CIS admin / Booking admin không đọc lại trong snapshot.
- RDS `aa-cis-dev-db`: không đọc riêng (mọi `/health/ready` ok); EFS: 0 file system.
- Bảng job: `shared.job` chỉ 1 `place_relocate` queued (`run_after` 30/10 00:13 UTC, chuỗi AA-997, có chủ đích); 0 wave mở; `booking.job` / `crm.job` / `tripplanner.job` không chụp.

PR còn mở sau khi chốt: chỉ root #328 (AA-993 M5, cố ý để mở tới proof auto-apply bk-034). Release CIS #1134, Booking #147,
TripPlanner #186, Partner #122 và root bot #327 (mở lúc chụp 14:45) merge lúc chốt; CIS #1144 `2e8e10a3`, #1142 `652b255f` đã merge trước giờ chụp.
Đã merge trong phiên (từ 10:00 +07): CIS 15 PR (#1130…#1145) + release #1134, Booking 3 (#144–#146) + release #147, TripPlanner 6 (#181–#185,
#187) + release #186, Partner 5 (#117–#121) + release #122, Infra 8 (#491–#498), root 10 (#318–#326, #329) + bot #327.

Issue đóng trong Linear hôm nay: AA-697, AA-814, AA-861. Đóng sổ Linear: export 3 issue (AA-697, AA-814, AA-861) ra `docs/linear-export/` rồi archive qua API.
Tracker HTML: publish lại cùng URL cuối phiên. Skill đóng gói: aa-cis-schema, aa-ecosys-repos, aa-lessons, aa-ship (`skill/dist/`).

## Jira

Nháp ở `docs/audits/2026-10-29-S257-session-close/jira-drafts.md`. Chưa đăng: nháp chờ tech lead duyệt (`docs/audits/2026-10-29-S257-session-close/jira-drafts.md`) — duyệt trong tin nhắn cuối phiên.

## Việc cần làm đầu phiên sau (S258, theo thứ tự)

1. Jira S257 nếu chưa đăng (nháp chờ tech lead duyệt (`docs/audits/2026-10-29-S257-session-close/jira-drafts.md`)).
2. **acc3 / judge luna**: theo dõi trả lời của reseller (tech lead hỏi) về việc acc3 rời Organization; khi luna chạy lại → probe
   gpt-6-luna / gpt-5.6-luna; tới lúc đó coi mọi stage judge trên luna là không tin được (đừng chạy eval trả tiền dựa trên luna);
   push + merge guard test `fix/aa-900-adhoc-label-account` nếu chưa. (Release CIS #1134, Booking #147, TP #186, Partner #122,
   root #327 đã merge lúc chốt S257.)
3. Theo sau AA-671: CIS #1144 xong (ảnh bìa 162 → 302 / 892); xem nhóm weak 137 / ambiguous 120 / no_match 779 và 590 tour
   còn thiếu ảnh bìa. CIS #1142 đã merge.
4. AA-993: kiểm cron `migration-sync` có chạy theo lịch (actor bot / throttle) → proof Booking bk-034 với `DB_AUTO_APPLY`
   → M5 (root #328) → đo lead time ≥ 5 PR.
5. AA-997: kiểm job chuỗi `aa997.1` đang xếp; chỉnh luật off_route / bán kính route trên mẫu P4 (offline, $0); cân nhắc LLM
   phân xử dòng `llm_point`; rồi AA-990 `recheck_14`.
6. AA-919: gán thêm cặp hiệu chuẩn theo stratum (thiếu Facebook 3 đạt + 3 trượt), chạy lại so model trên tập lớn hơn
   trước khi đổi route `writing_memory_eval` (ứng viên gpt-5.6-luna).
7. AA-790: không thêm vòng prompt trên harness 8 bài; mẫu cố định ≥ 20 bài + hiệu chuẩn judge (đề xuất, tech lead chốt).
8. AA-900: chạy lại R2 eval (lượt `228447e7` / job `462f72ee` không hợp lệ) — chỉ sau khi judge luna trên acc3 chạy lại.
9. AA-994: S5a/S5b (token TripPlanner), phase 6; H3 (login tech lead).
10. Follow-up: LCP `/destinations/bhutan` 3,95 s; AA-814 theo sau (T2 chưa nối facts, nhãn `Source:` chưa vào kiểm nhãn rò
    rỉ, tạo/sửa fact platform trên admin chưa thử live).
11. Phiên đầu ≥ 01/11: audit chi phí tháng 8/9/10 (AA-896); C4.3 tuần W45; 04/11 secret acc1 cuối hết hạn xoá.
12. Chờ tech lead: hỏi reseller (eCloudvalley / TrueIDC) vì sao acc3 rời Organization (billing, credit AWS Lift) + quyết nạp
    credit OpenAI; GuardDuty (đang "chưa dùng"), H3 Kit provenance, spike OTel (AA-842), đóng AA-789 Done-with-scope.
