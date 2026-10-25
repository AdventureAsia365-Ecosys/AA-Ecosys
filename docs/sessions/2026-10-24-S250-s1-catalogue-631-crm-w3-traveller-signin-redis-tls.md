# S250 — 24–25/10/2026: viết lại S1 tới 631/810 tour, CRM W3 + feed membership, đăng nhập traveller, Redis TLS

**Tác nhân:** Claude Code (Ultracode; workflow + subagent song song, tối đa 3 lane code; VSCode, WSL2; agent điều phối tự
merge/deploy/verify theo luật giai đoạn dev, push/merge bằng GitHub App `aa-agent`). Phiên nối tiếp S249 cùng ngày
(24/10 ~19:00 VN → 25/10 ~13:00 VN). Wave S1 chạy nền suốt phiên bằng driver `.tmp-session/s250/waves.sh`; deploy
backend CIS và DB Migrate chỉ chạy trong khoảng nghỉ giữa wave (cờ `s250/GAP`).

Nguồn số liệu: `docs/audits/2026-10-25-S250-wrap/state-snapshot.md` (kiểm live lúc đóng, ~05:45–06:00 UTC), comment
Linear từng issue (đọc 25/10), checklist sống `.tmp-session/S250-checklist.md`, log wave `.tmp-session/s250/waves.log` +
`sum-cw_*.txt`, `.tmp-session/s249/aa645/realpilot/cw-progress.log`, danh sách PR từ `gh`. Phần chưa kiểm ghi rõ
"chưa verify".

## Trạng thái

- **Linear Done trong phiên (10):** AA-910, AA-941, AA-978, AA-813, AA-943, AA-944, AA-977, AA-874, AA-908, AA-851.
  Ngoài ra AA-938 phương án B xong (Partner #36; issue Linear đã archive từ S249 nên bằng chứng nằm ở AA-Partner
  GitHub #27 + log này).
- **In Progress:** AA-645 (631/810 tour trên writer v2), AA-835 (live, chưa chạy thử LLM trả phí), AA-926 / AA-924 /
  AA-916 / AA-790 (CIS #982/#992 live, pilot T9 trả phí chưa chạy), AA-917 / AA-918 (CIS #998 live lúc đóng, chưa kiểm
  chạy thật), AA-945 (nhận mail chạy thật; kết nối Gmail/M365 cần Nghiệp), AA-853 (lint chứng minh được; báo cáo drift
  chưa chạy trên main — xem cảnh báo #380), AA-979 (P2a xong; còn P2a-4 docs/registers + P2b), AA-820 (kỹ thuật xong,
  chờ chị Thư).
- **PR merged: 82** — CIS 18, Booking 7, TripPlanner 4, Infra 29, AA-Partner 12, root 12 (đếm bằng `gh`, merged từ
  24/10 11:30Z, trừ các PR của S249). CIS #990 đóng không merge (gộp vào #992).
- **Migration áp Dev (DB Migrate):** CIS **275 → 280**; Booking **bk-023, bk-024**; TripPlanner **tp-019**; CRM
  **crm-012 → crm-015**.
- **Release:** CIS 0.9.0 (#984), Booking 0.6.0 (#85), TripPlanner 0.8.0 (#146), AA-Partner 0.4.0 (#38). Còn mở: CIS #999
  (release 0.10.0), root #249 (bot regenerate db-schema-reference).

## Quyết định của Nghiệp (trong phiên)

- Đầu phiên: tự chọn 20 việc từ master plan + tồn S249, chạy liên tục, không hỏi; việc cần duyệt thì duyệt luôn theo
  kế hoạch.
- AA-941: Nghiệp tự mở `/admin/platform/agencies` bằng phiên admin của mình để kiểm drawer (user E2E không nâng quyền được).
- 25/10 05:43Z: **dừng driver wave trước `cw_sri-lanka_3`** (cờ STOP) — 179 tour còn lại để S251.
- 25/10 ~06:00 UTC: **giữ route v2 làm mặc định** (writer v2 + `s1_generate` = sonnet-5-5) cho 179 tour còn lại và cho
  tour mới sau khi xong catalogue; **không trả về haiku** (ghi ở checklist + comment Linear AA-645). Lưu ý: snapshot chụp
  trước quyết định này nên ghi "đang chờ".
- Jira: nháp S249 + S250 **chưa đăng**, chuyển sang S251.

## Thay đổi Codebase

**AA-CIS-App (18):** migration 275 nội dung AA tự soạn (#980), 276 danh bạ membership tenant + feed (#986), 277
`shared.writing_signal` (#988), 278 nội dung supply + view đọc ngược (#989), 279 `shared.countries` ISO 3166-1 +
`country_iso2` + `catalog.v_country` (#995), 280 `shared.writing_rule` (#996); portal /terms tóm tắt AI v0.2 (#981);
Q-1 registry/taxonomy/thresholds + lint (#982); Redis từ env có TLS + AUTH (#983); atomize retry khi parse hỏng (#985,
nguyên nhân dừng wave Thailand); `/catalog/v1/aa-content` + feed `tenant.membership.v1` cho CRM (#987); consumer feed
supply của Booking + job nháp LLM + purge ảnh + API review (#991); severity theo từng finding + guard toàn vẹn sau sửa +
capture writing signal (#992); trang editor nội dung AA (#993) + seed (#994); đóng băng bản portal trong CIS (#997);
writing memory P1 — rule mining, backfill, R0 replay, L0 lexicon (#998); release 0.9.0 (#984).

**AA-Booking (7):** bk-023 outbox stream supply + `entity_media` + `v_supply_*` (#84); upload ảnh NCC + đọc ngược nội
dung CIS + text đã publish trên proposal (#86); bk-024 `customer_identities` (#87); bảng staff vừa 1400 px với dữ liệu
thật (#88); phiên chỉ đọc cho user E2E staff + ghi chú smoke (#89); nhận `inquiry.submitted` v1.4, nối traveller đã
đăng nhập với một khách đã verify (#90); release 0.6.0 (#85).

**AA-TripPlanner-Web (4):** tp-019 tài khoản traveller (#145); token traveller, nhận chuyến guest, API My Trips, hand-off
v1.4 trong Lambda assembly (#147); đăng nhập bằng mã email qua BFF, cookie phiên, trang My Trips (#148); release 0.8.0
(#146).

**AA-CIS-Infra (29):** bucket supply-media (#353); replication group Redis mã hoá + AUTH (#354), chuyển api/worker sang
group mới + đưa `S1_WRITER_V2` vào template (#372), xoá node Redis cũ (#373); alarm cờ tenant-pool (#355); scope M2M
`cis.tenant/read` + route `/tenant/membership` (#358), miễn `crm_membership_pull` khỏi kiểm rảnh DB Migrate (#359); WAF
Cognito + callback TripPlanner thứ hai + traveller E2E (#360, sửa description #367); địa chỉ E2E staff thứ hai cho
Booking (#361); quyền purge ảnh supply + invalidate CDN (#368); sign-up traveller chỉ cho BFF (#374); mail CRM
forward-in — MX `crm-in`, rule SES ingest (#375); route `ANY /me/{proxy+}` (#381); ownership lint (#379); báo cáo
drift hằng đêm (#380); bản copy migration CIS 275–280, bk-023/024, tp-019, crm-012…015 (#356, #357, #362–#366,
#369–#371, #376–#378).

**AA-Partner (12):** scrubber f3-3 giữ điểm đến không giống tên người (#36, AA-938 B); crm-012 + CRM-15 stage engine,
form planning, call slot + web (#37/#40); crm-013 + consumer feed membership (#39/#41); crm-014 + CRM-16 sổ agency-line,
NCC, tỷ giá ngày (#42/#43); chuyển portal tenant vào AA-Partner kèm lịch sử 152 commit (#44) + deploy/smoke/guard (#46);
crm-015 + CRM-17 mail agency (#45/#47); release 0.4.0 (#38).

**AA-Ecosys (root, 12):** hợp đồng R1 — supply v1, catalog.http 1.2, inquiry v1.4 (#237); registers DM-7 + schema
ownership + ERD TripPlanner (#238); go/no-go S251 + bằng chứng AA-941 (#239); điều khoản AI v0.2 (#240); ADR 0006a
A10a (#241); báo cáo replay AA-924 (#245); MIG-5/MIG-6 (#246); register `shared.countries` + `catalog.country.v1`
(#247); register `shared.writing_rule` (#248); bot regenerate (#242, #243, #244).

## Thay đổi Hạ tầng

- **DB Migrate (apply):** CIS 275, 276, 277, 278, 279, 280; bk-023, bk-024; tp-019; crm-012, crm-013, crm-014, crm-015.
  Tất cả áp trong khoảng nghỉ giữa wave (279/280 áp 03:13–03:16Z giữa China 2 và China 3).
- **Terraform (CI apply):** các PR Infra ở trên. Live lúc đóng: Valkey `aa-cis-dev-cache` (TLS required, at-rest, AUTH),
  node Redis cũ **không còn**; route `/me/*` có trên API TripPlanner; WAF `aa-identity-dev-pools` (4 rule) mới.
- **ECS lúc đóng:** CIS api `:819` / worker `:385` cùng `dev-4ce6a3aa` (#998); Booking `:56` `174a194c` (#90); CRM api
  `:41` `88be0b18` (#47), CRM web `:19` `923e2069` (release 0.4.0). Rollout đều COMPLETED.
- **Lambda TripPlanner** browse + assembly cập nhật 25/10 02:30Z (#147). **Vercel:** CIS admin `4ce6a3aa`, TripPlanner
  `49738c6f` (#148), Booking admin `f2eedbdf` (#86), portal giờ deploy từ AA-Partner `a90c1c26` (#46); biến/secret
  portal ở repo CIS đã xoá (không còn 2 nơi deploy).
- **Cố ý để BẬT cho S251:** worker `S1_WRITER_V2=on` (`:385`), route `s1_generate` = sonnet-5-5 (từ 24/10 08:51Z) — nay là
  mặc định theo quyết định Nghiệp. RDS snapshot thủ công `aa-cis-dev-db-pre-s1-*`: 20 bản (hết hạn theo luật 30 ngày
  AA-869).
- **⚠️ Infra #380 xoá ngược nội dung #372–#378 và #381 trên `main`** (squash `af8ac53b`, +1532 / −3616): mất bản copy
  279/280/crm-015, `crm_mail.tf`, `S1_WRITER_V2` + env Redis TLS trong `modules/ecs`, node Redis cũ quay lại
  `modules/elasticache`, mất route `/me/{proxy+}`, mất notes AA-874/AA-908 + runbook mail CRM. **Live chưa bị ảnh hưởng**
  (chưa apply sau 04:17Z), nhưng apply/deploy kế tiếp từ main sẽ phá. Chưa có PR khôi phục lúc đóng.
- **Chi phí thêm/tháng (Dev, giá niêm yết):** Valkey `cache.t3.micro` ≈ $12,9 (thay node cũ, không chạy song song);
  WAF `aa-identity-dev-pools` ≈ $9 (+ $0,60/triệu request). Đối chiếu Cost Explorer ở đợt audit đầu tháng 11.

## Bằng chứng verify (chính)

- **AA-645 / S1 — 13 wave theo nước trong S250** (mỗi wave: Jev 100%, 0 review, 0 ở lại v1, chưa wave nào chạm điều kiện
  dừng trừ Thailand):

  | Wave | Tour | Gate trước→sau | Phủ số liệu | Brand-fit (report) | Chi phí | $/tour | Luỹ kế |
  |---|---|---|---|---|---|---|---|
  | Taiwan | 29 | 8→2 | 0,481→0,598 | 7,79→8,76 | $1,546 | $0,053 | $11,89 |
  | Thailand | 34 | 13→1 | 0,556→0,692 | 7,62→8,29 | $2,748 | $0,081 | $14,64 |
  | Laos | 36 | 11→1 | 0,476→0,629 | 7,67→8,00 | $2,869 | $0,080 | $17,51 |
  | Philippines | 40 | 13→2 | 0,635→0,909 | 7,53→7,60 | $2,462 | $0,062 | $19,97 |
  | Japan 1 | 50 | 20→1 | 0,438→0,627 | 7,80→7,96 | $2,508 | $0,050 | $22,48 |
  | Japan 2 | 22 | 10→2 | 0,502→0,777 | 7,73→7,91 | $1,155 | $0,053 | $23,64 |
  | Nepal 1 | 50 | 16→3 | 0,328→0,833 | 7,90→8,00 | $4,427 | $0,089 | $28,06 |
  | Nepal 2 | 26 | 13→4 | 0,311→0,864 | 7,73→8,89 | $2,482 | $0,095 | $30,55 |
  | China 1 | 50 | 21→2 | 0,326→0,460 | 7,72→8,68 | $3,495 | $0,070 | $34,04 |
  | China 2 | 50 | 21→1 | 0,330→0,493 | 7,76→8,04 | $3,741 | $0,075 | $37,78 |
  | China 3 | 11 | 5→2 | 0,302→0,494 | 8,00→8,82 | $0,933 | $0,085 | $38,71 |
  | Sri Lanka 1 | 50 | 12→0 | 0,368→0,652 | 7,48→6,96 | $3,653 | $0,073 | $42,37 |
  | Sri Lanka 2 | 50 | 25→0 | 0,316→0,652 | 7,64→7,76 | $3,791 | $0,076 | $46,16 |

  - Thailand: dừng vì 1 tour lỗi tách atom (JSON hỏng từ LLM) → chạy lại atomize thành công → đóng theo luật 10% (1/34);
    sửa gốc ở CIS #985.
  - Sri Lanka 1: brand-fit (chỉ báo cáo, rubric khác nhau v1/v2) giảm 7,48→6,96, gate 12→0; không phải cổng.
  - **Tổng 17 wave theo nước (4 wave S249 + 13 wave S250):** 578 tour, 578 publish, 0 review, 0 ở lại v1; gate pages
    226→26; phủ số liệu 0,422→0,675; brand-fit 7,69→7,99. Cộng pilot 3 + wave ≤50 → **631/810 tour trên v2**.
  - Slug 308 cũ→mới đã kiểm từng tour tới Laos (100%); các wave sau chưa kiểm (S251).
- **AA-910:** tự kiểm live bằng user E2E Booking riêng, 100/100 sạch, slack ≥78 px ở 1440; ảnh 150% zoom của Nghiệp là
  nguyên nhân cột bị cắt (`docs/audits/2026-10-24-S250-aa910-live/`).
- **AA-941:** reviewer bị chặn đúng; phiên admin của Nghiệp thấy 3 agency + drawer đủ mục, nút ghi ẩn vì chưa ở nhóm
  `crm-platform-admin` — đúng thiết kế (`docs/audits/2026-10-24-S250-aa941-ui/`).
- **AA-908:** trên `tripplanner.lumiguides.it.com` (Playwright 1440 + 390): chuyến guest → đăng nhập 1 mã email →
  `claimed: 1` → My Trips mở được chuyến → đăng xuất → trình duyệt mới đăng nhập lại vẫn thấy; traveller thứ hai không
  thấy chuyến của người kia; mã sai → 400 `code_invalid`; 0 lỗi console, 0 5xx (`docs/audits/2026-10-25-S250-aa908-live/`).
  Route `/me/*` thiếu được phát hiện nhờ bước kiểm live → #381.
- **AA-977:** seed 28 mục (27 publish, 1 nháp); `/catalog/v1/aa-content` 200 với token M2M `cis.catalog/read`, 403 token
  chỉ tenant, 401 không token. Chưa kiểm trang editor bằng phiên admin.
- **AA-978:** events 200/401/403 đúng scope; consumer CRM (#41) chạy.
- **AA-874:** group Valkey TLS required + at-rest + AUTH; alarm `aa-cis-dev-tenant-flag-read-failed` OK → ALARM 03:59:44Z →
  OK 04:14:44Z (mail cả hai chiều).
- **AA-851:** countries 249; nhóm chưa map 0; `raw_tours` / `destinations` NULL `country_iso2` = 0
  (`docs/audits/2026-10-25-S250-wrap/AA-851-live.md`).
- **AA-945:** 1 mail SES thử → object raw trong bucket ingest → `crm_mail_ingest` lưu 1 → conversation (Unmatched) đọc lại
  qua API; raw xoá sau commit (`AA-945-live.md`). Chưa thử: send-as Gmail/M365/SMTP, threading theo token, import lịch sử.
- **AA-853:** ownership lint chứng minh bằng chạy local trên main; drift report chưa có run trên main (`AA-853-live.md`).
- **AA-938 B:** Scrub corpus run 40102237468: 260 mẫu, 0 rò rỉ, che quá tay 3,98% (< 5%).
- **Health lúc đóng:** CIS `/health` 200 `4ce6a3aa`, `/health/ready` schema 280; Booking 200 `174a194c`, bk-024; CRM api
  200 `88be0b18`, crm-015; CRM web 200 `923e2069`; TripPlanner browse 200.

## Chi phí

- **S1 trong S250:** 13 wave, 498 tour, **$35,81** (~$0,072/tour). Tổng 17 wave theo nước $42,05 ($0,0728/tour); luỹ kế
  chiến dịch (pilot $0,27 + wave ≤50 $3,84 + theo nước) **$46,16 / $120**. 179 tour còn lại ước ~$13.
- Không chạy batch LLM trả phí nào khác (AA-835 thử consumer và pilot T9 của AA-926/924/916/790 chưa chạy; R0 replay
  AA-918 là $0).
- Hạ tầng thêm/tháng: Valkey ≈ $12,9, WAF identity ≈ $9 (mục Thay đổi Hạ tầng).

## Còn lại cho S251 (theo thứ tự)

1. **Khôi phục Infra `main` sau #380** (đảo ngược phần diff `b1d2e924..af8ac53b` nằm ngoài phạm vi AA-853: copy
   279/280/crm-015, `crm_mail.tf`, `S1_WRITER_V2` + env Redis TLS trong `modules/ecs`, `modules/elasticache`, route
   `/me/{proxy+}`, notes/runbook) — **trước mọi `terraform apply` và deploy CIS**. Sau đó `terraform plan` phải sạch so
   với live, chạy lại DB Schema Dump và đọc lại báo cáo drift; xem log 2 lần fail 03:14Z/03:15Z.
2. **AA-645:** Sri Lanka 3 (12) + India 1–4 (167) bằng driver `.tmp-session/s250/waves.sh` (gỡ cờ STOP); kiểm slug 308
   cho các wave từ Philippines trở đi; báo cáo tổng + đóng AA-645. Route v2 giữ nguyên làm mặc định (không khôi phục haiku).
3. Merge root #249 (bot) và CIS #999 (release 0.10.0).
4. **Jira S249 + S250** (`docs/audits/2026-10-25-S250-wrap/jira-drafts.md`): điền ô `[số cuối]` bằng số wave cuối →
   Nghiệp duyệt → đăng.
5. AA-926 / AA-924 / AA-916 / AA-790: pilot T9 trả phí (subset) → đóng.
6. AA-917 / AA-918: kiểm live #998 (rule mining, R0 replay, L0 lexicon) → đóng.
7. AA-835: chạy thử consumer trả phí (subset) + bằng chứng Done-when (create → draft → publish → read-back, rename →
   stale, deactivate → unpublish).
8. AA-945: Nghiệp cài OAuth Gmail / Microsoft 365 (đăng nhập trình duyệt); kiểm send-as, threading, `crm_mail_health`.
9. AA-979: P2a-4 (docs/registers ở root) rồi P2b (CloudFront → Fargate, pool partner, 301 `/trip/*`).
10. AA-853: đóng khi drift report chạy xanh trên main (sau bước 1).
11. AA-820: chị Thư chọn A/B/C + luật sư (đưa qua nháp Jira).
12. AA-908 việc nhỏ: nút đăng xuất ở trạng thái lỗi My Trips; `email_verified` trong phiên đầu sau sign-up.

## Jira

- **Chưa đăng.** Nháp S249 + S250 ở `docs/audits/2026-10-25-S250-wrap/jira-drafts.md` (PR-22, PR-26, PR-25, PR-24, PR-27,
  PR-23), chuyển sang S251 theo ý Nghiệp; cần cập nhật số wave cuối trước khi đưa duyệt.

## Lưu ý kỹ thuật cho phiên sau

- Bài học mới trong `skill/aa-lessons/lessons.md` (S250): job nuốt lỗi LLM theo mục phải raise để retry; user E2E staff bị
  ghim `cis-reviewer`; WAFv2 cấm ngoặc trong description; TF apply chạm `module.ecs` tạo revision template làm deploy CIS
  mất cờ runtime; đọc lại kết quả giải xung đột rebase (flake8); `ps | grep` + kill giết shell gọi (gộp vào bài pkill).
- Comment Linear AA-645 ghi "`S1_WRITER_V2` nay nằm trong Terraform (#372)" — đúng cho #372 nhưng **không còn đúng trên
  main** sau #380 cho tới khi khôi phục.
- Merge CIS khi branch protection strict: `gh pr merge` bị từ chối nếu nhánh BEHIND → `update-branch` rồi chờ CI (gặp ở
  #998).
- Driver wave: `.tmp-session/s250/waves.sh` (bỏ qua wave đã đóng, `RESUME_OPEN` khi wave đang mở), cờ `s250/STOP` để
  dừng trước wave kế, cờ `s250/GAP` để giữ khoảng nghỉ cho deploy/DB Migrate.
- `/booking/health` báo 0.5.0 vì release 0.6.0 chỉ đổi CHANGELOG/manifest (không deploy lại) — không phải lệch.
- DB Schema Dump (Infra) fail 3 lần gần nhất (lần 04:43Z hỏng ở bước "Design ERD drift (report)"; dump + PR vẫn chạy).
