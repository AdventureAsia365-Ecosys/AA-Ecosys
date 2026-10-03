# S209 — Chạy lại toàn bộ Trung Quốc, DB schema reference, AA-713 Done, bug UI (AA-717/718/719), Jev hết credit (AA-720) (03/10/2026)

**Tác nhân:** Kiro (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:432` COMPLETED · **Migration mới nhất:** CIS 203 (không có migration mới)

## Trạng thái
- **China chạy lại xong toàn bộ:** pilot 3 + wave 1 (30) + wave 2 (30) + wave 3 (58) = 121/121 tour thô active đã S1.
  118 tự đạt lên Master, 3 rớt review queue (Heaven Lake 8.0 manual_check, Pandas and Old Beijing 6.0, Tibet Encompassed 6.0)
  → Nghiệp bấm Regenerate cho cả 8 pending (China/Korea/Taiwan) → **tất cả pass, review queue 0 pending**.
- **Master Content: 207 tour active** (DB thật). UI Master Content chỉ hiện 200 vì bug `LIMIT 200` (AA-718).
- **AA-713 Done** (verify live cycle deactivate→reactivate). **AA-717 Done** (fix REASONS, PR #547).
- **DB schema reference live** (root PR #23): hết cảnh dò cột mỗi phiên.
- **Jev (TypeSafe) hết credit trong ngày 03/10** → 402 `billing_error`. Pipeline fail open (stage dùng luật cũ) nên vẫn chạy,
  nhưng lớp Jev không hoạt động một phần đợt China. Nghiệp đã nhắn chị Thư nạp. → AA-720.
- **Jira đã đăng (03/10):** PR-15 (10452, 3 bảng: tour/nước, atom/segment/route/hub, chi phí ngày — đã bỏ phần Jev theo Nghiệp),
  KAN-90 (10453, nguyên nhân gốc DFS spike = tenant rewrite chạy platform-wide, đã sửa từ AA-646), PR-16 (10454, judge Luna ổn định).

## Số liệu tổng (đến hết 03/10/2026)
| Nước | Tour Master | Điểm TB | Atom active |
|---|---|---|---|
| China | 121 | 7.76 | 3.054 |
| Taiwan | 36 | 7.81 | 504 |
| South Korea | 30 | 7.57 | 1.116 |
| Mongolia | 17 | 7.88 | 334 |
| Bhutan | 3 | 7.67 | 110 |
| **Tổng** | **207** | ~7.8 | **5.118** |

- Quality 7×60 / 8×139 / 9×8 — tất cả ≥7. Brand audit fixed 194 / pass 13, 0 fail.
- Hạ nguồn: segment 3.528, segment member 5.611, route live 92, hub 382, atom_ranking 28.932, atom_embedding 1.960 view (lazy, đúng thiết kế).
- Chi phí 03/10: LLM ~$9,44 (Bedrock satellite $8,87; typesafe $0,57 — phần lớn lỗi 402; embed ~$0,001), DFS prefetch $1,13 (4 job).
  Judge shadow gpt-6-luna 808 calls 0 lỗi. Jobs: a3_atomize 129 succeeded, s1_seo_prefetch 4 succeeded, 0 failed.
- Wave: pilot S1 48–93s; W1 30 tour (39/101/179s, prefetch $0,315); W2 30 (24/119/261s, $0,320); W3 58 (26/93/231s, $0,422).

## Thay đổi Codebase
| Repo | PR | Nội dung |
|---|---|---|
| AA-Ecosys (root) | #23 merged (dee9550) | `docs/architecture/db-schema-reference.md` (dump live: 12 schema, 100 bảng/view, 95 FK, 13 enum, mig 203) + steering `.kiro/steering/db-schema.md` + import vào `.claude/CLAUDE.md` |
| AA-CIS-App | #547 merged (7d9bf9b) | **AA-717** Review Queue: cột REASONS fallback parse `failure_summary` (codes + LOW_QUALITY / BRAND_MANUAL_CHECK / BRAND_FLAGGED) khi `failures[]` rỗng. FE-only (`frontend/app/admin/review/page.tsx`). Merge sau khi job queue sạch. |
| AA-Ecosys (root) | PR log phiên này | log S209 + index |
- Root PR #22 (S208) phát hiện đã merged sẵn đầu phiên.
- `skill/aa-cis-schema.md` thêm note trỏ file reference — nhưng `skill/` bị gitignore nên chỉ local.

## Thay đổi Hạ tầng / dữ liệu (Dev)
- Không đổi Terraform/IAM. Deploy Dev 1 lần (#547) → ECS :431 → **:432** COMPLETED.
- Dữ liệu: 121 tour China lên Master + atom hoá (129 job a3_atomize). Không đổi route LLM.
- Test chuỗi lan truyền trên tour "1-Day Highlights of Xi'an" (deactivate/activate master + trash/restore raw) — **đã khôi phục sạch về baseline** (active/active, 4 atom, 24 ranking).

## Bằng chứng verify
- AA-713 live: deactivate → view_atoms 4→0, ranking 24→0; phần còn lại nguyên (other_view 2622, other_ranking 15090); reactivate → 4/24.
- Raw trash (gap): `source_status=trashed` nhưng master vẫn active, atom vẫn 4/24, chỉ có notification `tour.source.trashed` target [admin, content] → AA-716.
- Count 207: DB active 207, không trùng/ghost/deleted; UI 200 do `ORDER BY published_at DESC LIMIT 200` (admin.py ~l.508) + `Total Tours = tours.length` (master-content page.tsx ~l.1098).
- #547: CI 5/5 + Vercel pass; Deploy Dev success; ECS :432 rollout COMPLETED, 1 deployment, running=desired=1.
- Probe TypeSafe (03/10 15:35 UTC, key hiện tại): `GET /v1/models` 200; `POST /v1/systemone` **402** `{"detail":{"error_type":"billing_error",...}}`; `/v1/balance|credits|usage|account|billing` đều 404. OpenAPI chính thức chỉ có 2 endpoint → **không có API đọc số dư**.

## Linear
- **Done:** AA-713, AA-717.
- **Mới:** AA-716 (High, chuỗi raw trash → master inactive → drop atom → cảnh báo tenant), AA-717 (Done), AA-718 (Master Content 6 bug: Pipeline Runs=20 treo, LLM cost all-time, run kẹt INGESTING, LIMIT 200 mất tour + đếm sai, Avg Quality không theo filter, header/footer không sticky + redesign), AA-719 (Review Queue bulk regenerate + regenerate không đóng băng màn hình), AA-720 (Jev credit: cảnh báo 402 billing_error + circuit breaker + canary hằng ngày).
- **Cập nhật:** AA-705 (reconfirm SEO dashboard nghèo), AA-651 Low→**High**, AA-686 Medium→**High**.
- Design note admin UI (Master Content / Review Queue / SEO-DFS) là artifact phiên này, tóm trong AA-718/719/705.

## Thứ tự ưu tiên các phiên tới (Nghiệp duyệt S209)
1. Dứt điểm rerun — các nước còn lại qua AA-653 (Thái Lan → Lào → Nepal → Sri Lanka → Ấn Độ → Bhutan [chờ chị Thư 2 NCC]).
2. AA-651 (worker ECS job runner) + AA-662 (UI kit) — 2 nền tảng mở khoá nhiều việc.
3. AA-718 + AA-719 + AA-705 (UI có bug thật + design note).
4. AA-686 → AA-644 (route UI + A/B report → quyết t10_judge).
5. AA-716 (chuỗi ngưng tour).
6. Khởi động AAA (AA-678 / AA-677).
- **AA-720** (High) làm sớm, nhỏ — đặt cạnh bước 2. **t10_judge A/B** cần tenant content thật.

## Còn lại
- Chị Thư nạp credit TypeSafe → phiên sau kiểm Jev chạy lại (Jev Decisions page: zone không còn `error`).
- Đợt China có một phần chạy không có Jev (402) — cân nhắc cần chạy lại phần A3 Jev cho China khi có credit không (chưa quyết).
- AA-720 / AA-716 / AA-718 / AA-719 / AA-686 / AA-651 / AA-662 theo thứ tự trên.

## Lưu ý kỹ thuật cho phiên sau
- **Báo cáo wave phải tách:** S1 job ok ≠ tour lên Master. Ghi rõ published / rớt review queue (tên + lý do) / atomized. (Nghiệp nhắc S209.)
- **Sau mỗi wave: báo cáo đầy đủ → chờ Nghiệp duyệt → mới chạy wave tiếp.**
- **Merge PR App chỉ khi `shared.job` không còn queued/running** (kiểm `status IN ('queued','running')` KHÔNG lọc theo created_at — lần này query lọc 40 phút đã báo nhầm là sạch).
- `a3_atomize` cap = **1/1** toàn hệ (dù 2 worker × 4 slot) → 20–30 job xếp hàng ~1 giờ. Worker job runner vẫn chạy chung tiến trình API (AA-651).
- **Jev thất bại âm thầm**: `decide.py` fail open; `llm_call_log` vẫn ghi cost provider `typesafe` cho cả lần lỗi → đừng dùng số call/cost làm bằng chứng Jev chạy tốt. Xem `shared.decision_log.zone` (`error`) hoặc trang Jev Decisions.
- `atom_embedding` lazy by-design (chỉ embed atom vào shortlist PAA landing, batch 96/call trong a3_atomize; ranking fallback claim-by-name). Không cần backfill.
- ECS exec: lệnh > ~100s bị tool timeout 120s → để T≤110/T2≤95 hoặc chạy nền; script > 5 phút bị cắt session → chia step ngắn orchestrate từ local (`s209_prop_orchestrate.sh`). `nohup ... &` trong exec không sống sót. Agent exec đôi khi "isn't running" → thử lại sau vài phút.
- Script chạy trong container mà import code app phải `sys.path.insert(0, "/app")`.
- zsh: biến chứa nhiều flag (`$P`) không word-split → chạy qua `bash -c`.
- Jira qua connector: `contentFormat: html` + `<span data-type="mention" data-user-id="70121:5793bdd5-...">@thule</span>`; bảng HTML render tốt. cloudId `78f9a2ea-f228-4ff6-b37d-7079434d2cef`.
- Runner phiên: `.tmp-session/s209_run.sh <script.py> <s3-key>`; wave `s208_wave.mjs` (COUNTRY/OFFSET/LIMIT/CONC/PREFETCH); regenerate schema reference: `s209_schema_dump.py` + `s209_gen_schema_md.py`.
