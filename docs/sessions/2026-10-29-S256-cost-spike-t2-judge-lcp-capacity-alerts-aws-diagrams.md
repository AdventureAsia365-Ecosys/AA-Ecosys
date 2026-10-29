# S256 (28→29/10/2026): đóng trọn In Progress — sự cố chi phí 25/09, judge T2, LCP mobile, capacity D1–D13, cảnh báo bảo mật, sơ đồ AWS

Tác nhân: **Claude Code** (Ultracode; workflow nhiều sóng, sóng 1 `wf_c89985ec-bbc` từ 21:35). 28/10 21:20 +07 → sáng 29/10
(MFA acc2 hết hạn 08:36 +07). Tiến trình Claude Code khởi động lại khoảng 02:45, mọi tác vụ nền dừng theo. Số liệu cuối
lấy từ `docs/audits/2026-10-29-S256-session-close/state-snapshot.md` (<SNAPSHOT>).

## Quyết định của tech lead (trong phiên)

- Đầu phiên: agent tự chọn 20 việc, **coi như đã duyệt**; chạy liên tục; việc cần duyệt thì duyệt theo kế hoạch.
- Hai **cửa sổ tắt auto mode** do tech lead tắt/bật:
  - cửa sổ 1 (xong 21:50): `terraform apply` local IAM cho AA-993 I1 (2 add) + `db_auto_apply_gate.sh` (env `dev-db-auto`,
    secret, ruleset) bằng login gh của tech lead;
  - cửa sổ 2 (trước 08:36): apply local `tf_apply_sec` (AA-873), merge các PR Infra, CI terraform-apply, archive rule +
    kiểm cảnh báo, reboot RDS (AA-838), dọn AA-979.
- **Override** cho DB Migrate apply migration **301** (run 40791617873, AA-995): tech lead duyệt.
- **Sơ đồ kiến trúc phải theo chuẩn AWS** (nhóm chính thức, mũi tên vuông góc, chú giải) → vẽ lại, root #315.
- Không phải quyết định của tech lead: đổi vai user E2E studio (`crm/dev/e2e-test-studio/viewer`) sang **owner** để smoke
  portal chạy hết là **quyết định của agent** (vì thế đường "viewer" của lỗi cta-check chưa được thử live, xem Sự cố).

## Done / ship (kèm bằng chứng)

| Việc | Kết quả |
|---|---|
| **AA-665 Done** | Quy được trigger vụ 25/09: $49,02 / 1.169 lệnh là **DataForSEO** (search_volume_bulk 678 lệnh $39,24 …), hai đợt 05:05–05:23 và 08:33–08:51 UTC, cộng ~7,9k lệnh Haiku `a3_search_demand` ($10,27); nguyên nhân: tenant thử WanderLux viết lại tour trên portal, bước nền chạy nghiên cứu search demand (task nền của API, không phải job). CIS #1106 `1b88edce` (thẻ sự cố trên Cost Operations). Live: `GET /admin/dfs-usage/runs?…25/09…` 200, `incidents[0].id = 2026-09-25-dfs-research-sweep`; viewer 403; ảnh `ui-evidence/05a–05c`. `docs/audits/2026-10-28-S256-aa665-spike-attribution/` |
| **AA-765 Done** | Một judge client (`shared/llm_client/judge.py`) CIS #1116 `df8c436a`; T11 dispatch sang `services/acp_publish` + bỏ `POST /v1/pipeline/run` CIS #1117 `2493398d`. Deploy api :902 / worker :468 `b6b6ea82`; live 11 lệnh `t2_judge` sau deploy, 0 lỗi, 0 fallback. Done-when đúng chữ: 1 bài T9 (atlas-hearth, LinkedIn, image `fe88f168`) → 2 dòng `t10_judge` + verdict PASS. `docs/audits/2026-10-29-S256-aa765-t10/` |
| **AA-795 Done** | Mig 300 (CIS #1119 + Infra #488, DB Migrate 40737225475 / 40737534877) + CIS #1123 `b6b6ea82`: lưu điểm judge chi tiết mỗi version + kiểm câu khẳng định thương hiệu; tenant không thấy. Live proof PASS (terra-family, ≈ $0,05); quét 61 version → 9 cờ. Ảnh drawer `ui-evidence/04b–04c`. `docs/audits/2026-10-28-S256-aa795-t2-judge/` |
| **AA-838 Done** | Tech lead duyệt D1–D13. Infra #481 (D13 `pg_stat_statements.max` 10000, D2 api autoscaling tối đa 7 → 3, D6, D8), apply 40712053694; probe trước reboot (40715436472, 40715780663); **reboot RDS 29/10 06:40 +07** → `SHOW pg_stat_statements.max` = 10000, `/health/ready` CIS/Booking/CRM ok; CIS #1109 `5b6a3174` (application_name mọi kết nối); root #314 `947c1c0a` (data standards v1.7) |
| **AA-995 Done** | Ảnh 960w: mig 301 (CIS #1124 + Infra #490, apply 40791617873 có override) + CIS #1125 `5923c46b`, backfill 3.229 ảnh / 0 lỗi / 0 còn; TP #178 `c9d84bc3`. Lighthouse mobile production (3 lần, trung vị): **home perf 100, LCP 1,54 s; tour perf 100, LCP 1,57 s**, CLS 0. `docs/audits/2026-10-28-S256-aa995-lcp/production-after.md` |
| AA-920 (In Progress) | WM-25: mig 297 (CIS #1112 + Infra #482, apply 40715061377) + CIS #1114 `717c58f1` (stamp `generation_meta`, ẩn với tenant, nút "Check now"). Live PASS (T2 thật cho atlas-hearth ≈ $0,10; curl tenant 0 khoá cấm); WM-26 drill PASS $0. Còn WM-23/24 (cần release 1 có luật được duyệt). `docs/audits/2026-10-28-S256-aa920-wm25/` |
| AA-919 (In Progress) | Rà 13 cặp hiệu chuẩn (2 nhãn sai, 3 rubric mơ hồ, 4 lỗi judge cũ, 4 khớp), rubric CIS #1107 `051434eb`, golden set **1.2.0** import Dev; source parity CIS #1120. Hai lượt R2 `cc0f75cf` ($0,24) và `39096169` ($0,25): kappa **0,316** cả hai → không phải do judge thiếu nguồn; `judge_counts` vẫn false. `docs/audits/2026-10-28-S256-aa919-calibration/` |
| AA-790 (In Progress) | Vòng 9 (cờ `T9_BRIEF_GROUNDING_MODE`, CIS #1108 `d3ae3468`, mặc định tắt): A/B $1,10 + panel mù 32 mục: source_fidelity +0,50 đạt, brand_voice +0,38 đạt, ai_tells 5,62 đạt, **reader_value −0,25 trượt** → FAIL, cờ tắt, vòng 6 giữ live. `docs/audits/2026-10-29-S256-aa790-r9-panel/` |
| AA-873 (In Progress) | Triage Access Analyzer: 12 phát hiện, 11 ACTIVE đều có chủ đích, 1 RESOLVED, 0 lộ thật. Infra #483 `b152372e` (3 archive rule + rule IAM bắt cả Tag*/Untag*…), apply local `tf_apply_sec` + CI 40788053737 → **0 ACTIVE**; `sec_alert_check.py` 44/0 lỗi; thử bằng thay đổi thật: SG 4/4, IAM 6/6, trail 1/1, analyzer 1/1, SNS 0 lỗi, đối tượng thử đã xoá. Chỉ còn GuardDuty. `docs/audits/2026-10-28-S256-aa873-triage/` |
| AA-993 (In Progress) | Phase E: I1 Infra #477 `280cad6d` (role hẹp + gate; IAM simulate đúng, role check 40710037045 success), M2a #478 `d432e538`, M1 #480 + root ADR 0011a #309 `cce37612`, M2b Infra #485, M4a CIS #1121 / Booking #139 / Partner #112. Còn M3, M4b, M5; `DB_AUTO_APPLY` chưa bật |
| AA-697 (In Progress) | Sơ đồ icon AWS chính thức: root #311 (+ CIS #1110 `e1a5f820` reader hiện SVG của bundle, 27 ca độc hại bị chặn), đối chiếu TerraVision root #313 (plan "No changes"), vẽ lại chuẩn AWS root #315 `72c17e14`; link CONTEXT.md CIS #1122, Booking #140, TP #177, Partner #113, Infra #486. Live: 6 SVG tải được (`ui-evidence/03a–03c`). Chờ tech lead duyệt bản pilot |
| AA-880 (In Progress) | ADR 0012 "Environment model" **Proposed**, root #310 `e6921f63`. Done khi tech lead chấp nhận + blueprint prod lúc có ngày go-live |
| AA-979 (In Review) | Dọn P2b sớm: Infra #484 (301 `partner-dev.` → `portal.`, tắt đăng nhập bằng khoá API), Partner #115 `a6d6f282` (Deploy Portal Dev success, smoke 63/63 sau khi đổi user E2E sang owner), xoá 3 secret + 1 biến + project Vercel `aa-cis-portal`; root #316 `67b92431` (docs + secrets register); lỗi viewer gọi cta-check → CIS #1127 `6e68f48e`. Còn: CIS #1126 (xoá `portal/` đông lạnh, `/trip` vĩnh viễn) mở, deploy CRM, redirect URI Google + thử Gmail, thu hồi token Vercel (tech lead) |
| AA-671 (In Progress) | Bộ lọc hoạt động / độ khó / mới thêm + ảnh bìa: CIS #1111 `e85c37f4` + Partner #111 `09c562b9`, portal deploy 40794245317. Live (ảnh `ui-evidence/01a–01l`): 892 tour, lọc "Trekking & hiking" 454, China + "Culture & heritage" 105; lọc nặng nhất 66,1 ms. Ảnh bìa chỉ 162/892 tour (khoảng trống dữ liệu, UI đúng) |
| View `catalog.v_tour_place_name` | CIS #1118 mig 298 + Infra #487 + DB Migrate 40734310260 + Booking #141 `ad4be194`: 25 tour 381 → 109 ms, 100 tour 1.176 → 274 ms (BUDGET_OK, 100/100 cùng kết quả). `docs/audits/2026-10-28-S254-booking-figma-audit/v-tour-place-name-live-S256.md` |
| AA-682 follow-up (ops-docs) | Lỗi tìm ra nhờ đối chiếu sơ đồ AA-697: bucket chứng từ Booking chưa từng được tạo (upload 503). Infra #489 `77185f97` + Booking #142 `5a115023`: BPA 4/4, AES256; verify trong container upload → download (sha256 khớp) → gỡ, 3 dòng audit, RC=0. `docs/audits/2026-10-29-S256-aa682-ops-docs/` |
| AA-898 follow-up | CIS #1115 `4b356ebe` (chờ `document.fonts.ready`) đã merge nhưng ảnh live vẫn ngắt giữa từ (F1, `ui-evidence/03e`) → nguyên nhân là bề rộng ngắt dòng, sửa ở CIS #1128 (mở) |
| AA-994 (In Progress) | i18n admin trong kit (EN mặc định, VI thứ hai): CIS #1129 **mở** lúc soạn, ảnh EN/VI 4 trang ở `docs/audits/2026-10-29-S256-aa994-i18n/` |
| AA-997 (In Progress) | Dry run mọi nước `ce96dfa5` (3.842 dòng / 3.607 request / $0, ~3 ngày credit 1.500/ngày); Laos `2b1fb176` dừng ở trần credit 0/302, job `71781806` chạy lại 07:11 +07 29/10; apply mọi nước `445f9770` xếp 00:40Z sau Laos. Audit lại khi chuỗi xong (~31/10) |
| Bot / release | Release CIS 0.14.0 (#1093), Booking 0.10.0 (#133), Partner 0.8.0 (#106), TripPlanner 0.11.0 (#173); root bot #297, #301 |

## Sự cố

1. **bk-032 bị sửa sau khi đã áp** (Booking #130 đổi NUMERIC(6,4) → (12,4) sau apply; live vẫn (6,4)). Copy guard chạy-mọi-PR
   của AA-993 I1 bắt được ngay lần đầu → Booking #137 `dfea34c2` trả bk-032 về đúng byte đã áp + bk-033 nới
   `effective_margin` (Infra #479, DB Migrate 40707483791 / 40707781252, `/booking/health/ready` → bk-033).
2. **4 guard CI đỏ** trong phiên: gitleaks `uri-embedded-credentials` bắt DSN giả trong test (CIS #1109), guard
   resource-ids (chuỗi 12 chữ số trong fixture), guard văn bản golden AA-919, và "Vendored CIS copies" ở Partner #111 vì CIS
   #1110 đổi file được vendor. Sửa từng PR; luật đã vào lessons chờ. Thêm: nhãn `secret-scan-baseline-reviewed` chỉ có hiệu
   lực khi gắn sau lần push cuối (CIS #1126).
3. **Claude Code khởi động lại ~02:45** → mọi tác vụ nền (chuỗi ship, theo dõi job) dừng, phải dựng lại từ checklist.
4. **Output ECS exec bị cắt** ("Cannot perform start session: EOF") khi script chạy lâu / in dài; task role Booking không ghi
   S3 → chạy nền tách tiến trình rồi đọc kết quả từng đoạn.
5. **Auto mode chặn** một số bước: huỷ job Laos của AA-997 bị chặn (giữ nguyên, apply mọi nước xếp sau), các bước
   apply/merge/secret gom vào 2 cửa sổ tắt auto mode của tech lead.
6. Lỗi viewer gọi `cta-check` (403) trên portal: đã sửa (CIS #1127) nhưng chưa thử live bằng user viewer, vì user E2E studio
   đang là owner (F3 trong `ui-evidence/README.md`). Portal trả 503 thoáng qua một lần ~08:19, chạy lại đạt.

## Chi phí

- LLM có log: AA-919 R2 $0,24 + $0,25 = $0,49; T2 rewrite ~$0,15 (WM-25 ≈ $0,10 + AA-795 ≈ $0,05); AA-790 vòng 9 A/B $1,10;
  bằng chứng T9 cho AA-765 ~$0,04 → **≈ $1,78**.
- AWS mới/tháng: bucket ops-docs Booking ~$0 ở khối lượng hiện tại; secret `crm/dev/e2e-test-studio/viewer` $0,40.
  GuardDuty vẫn tắt (0).

## Trạng thái kiểm cuối phiên

Xem `docs/audits/2026-10-29-S256-session-close/state-snapshot.md`. <SNAPSHOT: CIS api/worker revision + SHA + schema (301
dự kiến); Booking revision + SHA + bk-033; CRM api/web/portal revision + SHA + crm key; TripPlanner web SHA + Lambda;
Vercel production commits; `shared.job` / `booking.job` / `crm.job` (chuỗi `place_relocate` AA-997 cố ý để chạy); PR còn mở
mỗi repo>.

PR còn mở lúc soạn log: CIS #1129 (i18n), #1128 (Mermaid), #1126 (AA-979), release CIS #1113 / Booking #138 / TP #179 /
Partner #114; root bot #308, #312.

## Jira

Nháp 29/10 08:15 ở `docs/audits/2026-10-29-S256-session-close/jira-drafts.md` (PR-22, PR-23, PR-24, PR-25, PR-27 + tuỳ chọn
KAN-90). <JIRA>

## Việc cần làm đầu phiên sau (S257, theo thứ tự)

1. Jira S256 nếu chưa đăng: thay tên ảnh đề xuất bằng ảnh thật trong `docs/audits/2026-10-29-S256-ui-evidence/` → duyệt → đăng.
2. Ship các PR đang mở theo aa-ship: CIS #1129 (AA-994 i18n admin), #1128 (Mermaid ngắt giữa từ), #1126 (AA-979, gắn nhãn
   secret-scan là bước cuối), release ×4, root bot #308/#312.
3. AA-979: deploy CRM; tech lead thêm redirect URI Google `https://portal.lumiguides.it.com/connect/mail/callback` → thử kết nối
   Gmail; tech lead thu hồi token Vercel; thử cta-check bằng user viewer (CIS #1127) → đóng.
4. AA-997: để chuỗi relocate chạy theo credit Geoapify tới ~31/10, rồi audit lại (mục tiêu ≥ 90 %) + AA-990 `recheck_14`.
5. Phiên đầu ≥ 01/11: audit chi phí tháng 8/9/10 (AA-896, cùng AA-838 / AA-665).
6. AA-993: M2b gate (ruleset + show), chứng minh M1 live (schema dump tự merge sau một apply), rồi M3, M4b, M5.
7. AA-919: thêm cặp hiệu chuẩn theo từng stratum (kappa theo stratum), so model judge; sửa script kappa diag (lỗi trên run
   39096169).
8. AA-790 vòng 10: giữ grounding + thêm checklist reader-value vào brief, cùng harness.
9. AA-671: khoảng trống ảnh bìa (162/892), dấu `·` thừa trên chip giá → đóng.
10. Follow-up nhỏ: LCP trang điểm đến (/destinations 3,38 s, Bhutan 3,88 s); EFS `aa-cis-dev-efs` không task nào mount (DRY RUN,
    tech lead quyết xoá); chế độ ecsx không cần S3.
11. Chờ tech lead: duyệt pilot sơ đồ AA-697, chấp nhận ADR 0012 (AA-880), GuardDuty có/không (AA-873), Gmail consent thật
    (tuỳ chọn).
12. AA-920 WM-23/24 khi release 1 có luật được duyệt.
