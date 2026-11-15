# S281 — 15/11/2026 — Đóng Settings và xoá dữ liệu có CRM, 3 tính năng CRM, Academy trọn vòng, đóng diễn tập pilot

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 15/11 ~00:30 → trước 17:00 +07 (tech lead: "đóng trước
17h"). MFA `aa365-admin` hết 09:02 (+07) giữa phiên. Trần LLM trả phí của phiên: 5 USD (giữ như S279/S280). WIP Linear
8/8 lúc mở phiên, nên việc kéo thêm chỉ sang In Progress sau khi đóng AA-1086 / AA-1096 / AA-1106.

## Trạng thái

- **Done (có bằng chứng live), 9 issue:** AA-1096, AA-1106, AA-1086, AA-1105, AA-1093, AA-1089, AA-1012, AA-965, AA-1077.
- **Còn mở:**
  - **AA-1048 (In Progress).** Instrument 2 bước live; pool mới cần sheet bắn lớn hơn (mẫu 150 chỉ ra 11 TP, cần ≥ 20).
    Lượt bắn mẫu 300 (có checkpoint, CIS #1526) đang chạy lúc chốt; lượt có cổng (gated run) để S282.
  - **AA-1051.** Phần $0 xong (CIS 427, 34/36 key enforced). Null run trả phí chờ AA-1048 ghim instrument + tech lead
    yes (trần null 5 USD).
  - **AA-1003 (In Progress).** R5 live (FI-08, BK-03, FI-07). Còn R6, R7.
  - **AA-1090 (In Review).** Duyệt chi phí, code + migration + Terraform phần lớn đã merge; Terraform 2 bước (Infra #863) và
    test sub-domain trên tên miền thử đang chạy lúc chốt.
- Bài học S281 đã vào `skill/aa-lessons/lessons.md` (commit trong root PR này); runbook diễn tập khôi phục TripPlanner cập
  nhật cùng PR (`docs/ops/runbooks/tenant-restore-drill.md`).

## Quyết định của tech lead (trong phiên)

- 00:35 "ok, kéo thêm việc làm tăng tốc lên": duyệt danh sách việc đang chạy và kéo thêm AA-1089, AA-1012, AA-1003 (R5).
- ~01:10 "Ok cả hai": duyệt nội dung YAML catalogue (`docs/catalogue/features.yaml`, `integrations.yaml`, AA-1106) và cho
  agent chạy X2 (diễn tập ngừng bán tour, AA-1086) qua admin route.
- ~02:15 "cứ làm bình thường, việc đợi tôi để sau, kéo thêm việc khác": kéo AA-965, AA-1090 (apply chờ duyệt giá) và lane
  guard công cụ.
- Đặt `cis.t9.blog_extend_material = with_background` cho tenant thử trên Platform › Settings (AA-1077, trước trial 6).
- ~09:15 "duyệt hết": cửa sổ xoá thật AA-1093 cùng các quyết định đang chờ (hai lần duyệt Cognito có fingerprint, setting
  do tech lead đổi), chi phí AA-1090 (~0 USD/tháng theo bản ghi chi phí), publish module F3 của AA Academy.
- Chọn phương án 1: mua một tên miền thử (~3 USD/năm) cho test sub-domain của AA-1090.
- "kéo thêm 1-2 việc, đóng trước 17h": thêm lane l15 (checkpoint/resume `r1_fire`, CIS #1526) và lane l16 (root #808).

## Kết quả theo issue

- **AA-1096 Done** (comment 14/11 23:10Z): gỡ env var của mọi setting đã chuyển sau một release.
  - CIS #1519 + CIS 424, Partner #320 + crm-068, TripPlanner #268 (Deploy Lambdas trên 378eb83), Booking #258 (settings-lint
    rule 7), Infra #850 (bỏ env retention của drill xoá), root #796 (runbook).
  - Live `GET /admin/settings/registry`: CIS 214 setting, TripPlanner 17, 0 `env_override`, 0 giá trị lấy từ env.
- **AA-1106 Done:** Catalogue guard là required check trên root master (ruleset do tech lead tạo bằng gh của mình, App
  `aa-agent` bị 403). Nightly chạy tay bắt drift thật (12 key `cis.learn.*` chưa gắn feature) → root #786; chạy lại xanh.
  Tech lead duyệt YAML.
- **AA-1086 Done:** mọi Done-when đạt.
  - Marker 1b: tenant `pilot-rehearsal-01-marker`, yêu cầu pilot thứ hai bị từ chối `pilot_taken`; REH-01b PASS 3/3 sau
    sửa kịch bản (root #787). 12b End pilot: REH-12b PASS 2/2, slot pilot Dev trống.
  - Teardown: offboard mềm hẹn xoá không trước 14/12/2026 (CRM 12/02/2027); partner Booking `suspended`.
  - REH-08a quay lại v4 PASS 5/5 (take S280 mất theo worktree); 6 video lên thư mục diễn tập trên Drive; README root #788.
  - **X2 PASS cả phần CRM:** trash 18:15Z (trang tour công khai 410, Booking nhận, 1 tenant được báo) → 4 cờ CRM trên 4
    chuyến lúc sync 20:00Z → restore + activate 23:02Z (trang 200) → cờ gỡ lúc sync 01:00:27Z. Tối đa ~2 giờ từ CIS tới
    CRM. README root #806; bằng chứng `docs/audits/2026-11-15-S281-session/verify/aa1086/`.
- **AA-1105 Done:** AA Academy chạy trọn vòng tới chứng chỉ.
  - S4: CIS 421 (#1511) + learning API #1512 (kèm sửa review về chứng chỉ cấp lại). CIS 425 + #1520/#1522 (header giới
    hạn verify theo visitor), root #793 (`learn.http.v1` 1.1).
  - S5: Academy web Partner #317 trên host academy (6 trang 200, 0 lỗi console, 1440/390 sáng/tối); Partner #323 (Objective
    hiện 1 lần); edge check Infra #847 7/7, raw-cf Infra #858 (edge 26/26 PASS).
  - F3 active (root #809, v1.0.0). Learner E2E: F3-01/F3-02 xong, quiz F3 6/6, quiz cuối Fundamentals 100 %, chứng chỉ
    `f9de22c4…`, trang verify công khai 200 VALID trên trình duyệt ẩn danh.
- **AA-1093 Done:** xoá thật lần 2 trên tenant tổng hợp `aa1093-erase-02`, có CRM.
  - Code: CIS #1514 (saga phủ `learn.*`), Partner #315 (crm-066/067; crm-066 đổi sang contract vì bảng mới trong schema
    `crm` phải ENABLE + FORCE RLS, `CREATE OR REPLACE TRIGGER`) + #316 (stage xoá CRM), Infra #844 (công tắc CRM), Infra
    #860 (script đọc lại bằng master), root #789 (dòng retention DM-7.1).
  - R1 (duyệt 03:52Z, fingerprint `bce15fdf`): CIS xoá 55 dòng, Booking redact 2 + ẩn danh 1, TripPlanner 0. R2 CRM (duyệt
    04:46Z, fingerprint `32c1185e`): xoá 36, ẩn danh 1, shred 1 khoá vault. Snapshot RDS trước khi xoá
    `tenant-erase-20261115-erase02`.
  - Đọc lại độc lập E1–E4 PASS (0 dữ liệu cá nhân ở cả 4 app). Công tắc: bật Infra #861, tắt Infra #862 (Terraform Apply +
    Deploy Dev CIS / Booking / Partner); CRM `LIFECYCLE_DRY_RUN` giữ true suốt.
  - Diễn tập khôi phục TripPlanner PASS: `tp_tenant_backup` 42 dòng / 4 bảng, `restore_drill` passed (5/5, 5/5, 29/29, 3/3).
- **AA-1089 Done:** CIS #1510 (mẫu "Booking confirmed" EN/VI, seed + publish; `/v1/trip/<key>` 301 về bản hiện hành),
  Partner #313 + #314 (đầu trang chuyến đi `aa_source`). Live: `import-aa` 200 thêm 6 mẫu; 3 chuyến `web_booking` hiện tour
  AA gốc + ngày khởi hành + link.
- **AA-1012 Done:** Partner #318 (render + ký PAdES-B-B qua `kms:Sign` DIGEST) + #319 (chuỗi chứng thư Dev, khớp khoá KMS).
  Live: PDF 200, pyHanko intact / valid / trusted, phủ ENTIRE_FILE; bản VI (nội dung giả lập) in đủ dấu.
- **AA-965 Done:** Partner #321 (crm-069) + #322 (crm-070). Trial trên đại lý thử: 49 lượt thật (R41 17, R10 17, R40 15),
  33 lượt bị trần tần suất chặn trước khi gọi AI ($0); 0,0072 USD (~0,00015/lượt, scrub chiếm 2/3). R40 chạy qua lead
  tổng hợp `not_sure`. Đã tắt AI lại như cũ.
- **AA-1077 Done:** CIS #1513 (CIS 422, setting extend material) + #1517 (repair co bài, extend có guard nền). Phân tích $0:
  bài 2 trial 5 bị repair cắt dưới sàn, extend từ chối. Trial 6: 2 bài, 0 F4 hold, 1 duyệt, 1 giữ vì F17 (thuộc AA-1048),
  0,275 USD. DW3 đã đạt từ 13/11 (3.364, scope platform); lần đọc 5.8 trước đó sai vì script thiếu `ensure_fresh`.
- **AA-1048 (In Progress):** CIS #1515 (423) + #1518 (instrument 2 bước v5c/v5j, fresh pool, pre-registration, gated runner),
  #1523 (426) + #1524 (bắn R1 trên claim chưa có nhãn), #1526 (checkpoint/resume `r1_fire`). Trial 9 lời gọi 0,027 USD
  (ledger 9/9). Lượt 177 lời gọi đầu bị script timeout cắt ở lời gọi 108 (mất report, ~0,17 USD). Lượt bắn mẫu 150: 177 lời
  gọi, 0,289 USD, bắn 48 → panel 3 lens → import 11 TP / 34 FP (thiếu TP). Bắn mẫu 300 sau #1526: đang chạy lúc chốt.
- **AA-1051:** CIS #1525 + CIS 427 (contract): 34/36 key CIS chuyển `enforced = true`; 2 key chưa có code đọc giữ false.
  Review 2 lens đều duyệt.
- **AA-1003 (In Progress):** root #795 (registry: FI-08 mới, BK-03 + FI-07 `generator: cis` từ 16/11) + CIS #1516
  (`b2b_ops.py`). Chạy thật 3/3 `report_run` thành công.
- **AA-1090 (In Review):** bản ghi thiết kế + chi phí ~0 USD/tháng
  ([`2026-11-15-S281-tp-custom-domain`](../audits/2026-11-15-S281-tp-custom-domain/README.md)), root #802 (contract 1.8,
  ADR 0019 amendment, dòng retention). Merged: CIS #1521 (CIS 428–429), CIS #1527 (code), TripPlanner #269, Infra #854.
  Còn: Infra #863 (Terraform 2 bước) và test sub-domain trên tên miền thử.
- **Không thuộc issue:** root #792 (lane l9: gitleaks resolver, `ship_wave` exit 7 cho migration bị giữ, UAT-1, 4 bài học
  thành guard); root #808 (lane l16: ship chờ deploy theo service bị chạm, chặn merge khi còn ECS exec đang chạy).

## Thay đổi Codebase (PR đã merge, chính)

- **CIS:** #1510, #1511 (421), #1512, #1513 (422), #1514, #1515 (423), #1516, #1517, #1518, #1519 (424), #1520 (425), #1521
  (428–429), #1522, #1523 (426), #1524, #1525 (427), #1526, #1527.
- **Partner:** #313, #314, #315 (crm-066/067), #316, #317, #318, #319, #320 (crm-068), #321 (crm-069), #322 (crm-070), #323.
- **Booking:** #258. **TripPlanner:** #268, #269.
- **Root:** #786, #787, #788, #789, #792, #793, #795, #796, #802, #806, #808, #809; schema dump tự merge #790, #791, #794,
  #797–#801, #803–#805, #807.

## Thay đổi Hạ tầng

- Copy migration theo từng wave (Migration Sync), Infra #843 … #865.
- Infra #844 công tắc xoá CRM; #861 bật / #862 tắt cho cửa sổ AA-1093 (mỗi lần Terraform Apply + Deploy Dev 3 app); #860
  script đọc lại bằng master qua DB Migrate run-script.
- Infra #847 edge check academy, #858 raw-cf; #850 bỏ env retention của drill xoá khỏi Terraform.
- AA-1090: Infra #854 merged; #863 (Terraform 2 bước) chưa xong lúc viết log.
- Root: ruleset Catalogue guard required trên master (tech lead tạo).

## Bằng chứng verify (chọn lọc)

- AA-1086 X2: `docs/audits/2026-11-15-S281-session/verify/aa1086/` + root #806.
- AA-1093: E1–E4 PASS, verify 0/96 (CIS), 0/22 (Booking), 0/8 (TripPlanner), 0/83 (CRM); TP restore 42/42.
- AA-1105: verify chứng chỉ 200 VALID ẩn danh; edge academy 26/26.
- AA-1096: registry CIS 214 / TP 17, 0 env override.
- AA-1012: pyHanko 0.38.0, một chữ ký `PlatformSeal`, `/ETSI.CAdES.detached` SHA-256.
- Comment đóng của từng issue trên Linear có đủ số liệu; file bằng chứng gom trong `docs/audits/2026-11-15-S281-session/`.

## Chi phí trả phí của phiên

| Khoản | USD |
|---|---|
| AA-1077 trial 6 (ledger) | 0,275 |
| AA-1048 trial 9 lời gọi | 0,027 |
| AA-1048 lượt bị timeout cắt (108/177 lời gọi, mất report) | ~0,172 |
| AA-1048 bắn mẫu 150 (177 lời gọi) | 0,289 |
| AA-1048 bắn mẫu 300 (237 lời gọi, bắn 104; pool mới 21 TP / 66 FP mẫu, DRY RUN sạch) | 0,396 |
| AA-965 trial + mở rộng (49 lượt) | 0,0072 |
| **Tổng LLM trả phí của phiên** | **~1,17** |

Dưới trần phiên 5 USD. Ngoài LLM: tên miền thử cho AA-1090 ~3 USD/năm (tech lead chọn phương án 1).

## Jira

**Chờ duyệt.** 4 nháp (PR-22 CIS, PR-26 CRM, PR-27 nền tảng, PR-20 diễn tập pilot) nằm ở `.tmp-session/S281/jira-drafts.md`,
chưa đăng. Đăng sau khi tech lead duyệt, rồi chép bản lưu sang `docs/audits/2026-11-15-S281-session/jira-drafts.md`.
Không nháp PR-23 / PR-24 / PR-25 (không có tính năng mới ở đó). Báo cáo tuần kỳ 5 (10–16/11) dưới PR-20 để S282 soạn đủ tuần.

## Trạng thái kiểm cuối phiên

Theo [`state-snapshot.md`](../audits/2026-11-15-S281-session/state-snapshot.md) (~07:40 UTC):

- ECS: cis-api :1170 / worker :739 cùng dev-6393fd75; booking-api :141 (8019cb88); crm-api :182, crm-web :156 (7e24a4c5); booking-admin :29. Rollout COMPLETED, running = desired.
- Health 200 cả CIS, Booking, CRM, CRM web, academy, TripPlanner; migration CIS 429, bk-058, crm-070, tp-031.
- Bảng job: shared.job và booking.job rảnh; crm.job 2 job định kỳ. Không wave.
- Công tắc xoá dữ liệu tắt hết; domain test AA-1090 còn giữ; RDS snapshot erase02 xoá sau root PR.

## Còn lại (việc cho S282, theo thứ tự)

1. Merge root PR chốt phiên rồi xoá snapshot RDS `tenant-erase-20261115-erase02` (nếu chưa xoá lúc chốt).
2. Jira: tech lead duyệt 4 nháp S281 → đăng → ghi id comment; soạn báo cáo tuần kỳ 5 dưới PR-20.
3. AA-1048: đọc kết quả bắn mẫu 300 → panel → import; đủ ≥ 20 TP và ≥ 25 FP thì chạy lượt có cổng theo pre-registration,
   chưa đủ thì mở rộng sheet bắn.
4. AA-1051: null run trả phí khi AA-1048 ghim instrument và tech lead yes (trần 5 USD).
5. AA-1090: xong Infra #863 + test sub-domain (HTTPS branded, gỡ tên miền rơi về path) → đóng.
6. AA-1003: R6 (`crm.ops.v1`) rồi R7; xem lần tự chạy đầu của BK-03 / FI-07 (thứ Hai 16/11 01:30 UTC).
7. C4.3 tuần W47 (phiên đầu tiên từ 16/11).
8. Follow-up nhỏ: AA-1086 G8 (kịch bản studio / planner khi hết ngân sách AI); AA-1089 (`trip_source` bỏ proposal đã xoá
   mềm, index cho fallback key); AA-1012 ảnh VI live cần đại lý thử locale `vi`; đưa driver trial T9 vào `tools/`.

## Lưu ý kỹ thuật cho phiên sau

- **Lượt trả phí dài phải chạy tiếp được.** `r1_fire` nay ghi checkpoint (CIS #1526). Đặt `ECSX_SCRIPT_TIMEOUT` từ kế hoạch
  (số lời gọi × độ trễ đo ở trial × 1,5), viết dạng tham số sau tên script (`ecsx.sh script.py ECSX_SCRIPT_TIMEOUT=N`), xoá
  report cũ trước mỗi lượt.
- **ECS exec không nằm trong bảng job:** deploy giữa chừng giết lượt chạy. Root #808 chặn merge khi còn ECS exec đang chạy.
- **Script ECS exec đọc setting phải gọi `settings.ensure_fresh(pool)` trước;** không thì chỉ thấy compiled default.
- **ecsx trên CRM / Booking:** dùng `ECSX_SHIP=inline ECSX_READ_CHUNK=600`; mất output sau một lượt ghi thì đọc lại trạng
  thái trước khi chạy lại.
- **Đổi trạng thái tour sinh `recompute` toàn platform (16–52 phút)** chặn Migration Apply: apply migration trước, chạy drill
  vòng đời tour sau. Một lượt catalogue sync phủ ~500/890 tour, nên tour → cờ CRM mất tới ~2 giờ.
- **Partner Migration preflight bước Classify** chạy dưới `bash -e`: mã 14 làm bước chết trước khi in `classify.log`. Bảng mới
  trong schema `crm` thiếu ENABLE + FORCE RLS → file phải là contract và chạy lại được.
- **Số migration của PR mở có thể bị PR khác lấy:** #1525 lấy 427, #1521 đánh lại 428–429 lúc ship.
- **Đổi major version module Academy reset hoàn thành module**: quiz phải đạt ở major hiện hành.
- **Required check mới ở root** cần token gh của tech lead (App `aa-agent` thiếu quyền administration, cố ý theo ADR 0011).


## Bổ sung lúc chốt (sau snapshot)

- AA-1090: test thật trên domain thử phát hiện lỗi SAN rỗng của chứng chỉ edge → CIS #1528 (cf746a02); retry → host
  active 08:06Z, TripPlanner mang tên đại lý trên tên miền riêng (ảnh `verify/aa1090/`); gỡ host → về đường dẫn chung.
- AA-1048: fire 300 xong (0,396 USD, bắn 104), pool 21 TP / 66 FP, DRY RUN sạch.

- Jira đã đăng sau khi tech lead duyệt: PR-22 10657, PR-26 10658, PR-27 10659, PR-20 10660 (`../audits/2026-11-15-S281-session/jira-drafts.md`). Báo cáo tuần kỳ 5 trên PR-20: comment 10661 (`../audits/2026-11-15-S281-session/pr20-period5/README.md`).
