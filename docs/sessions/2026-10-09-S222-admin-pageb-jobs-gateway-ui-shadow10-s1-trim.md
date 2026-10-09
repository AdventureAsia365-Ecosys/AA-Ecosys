# S222 — Admin PR B + trang Jobs + Gateway UI (shadow 10%) + ẩn distinctiveness + bớt LLM ở S1 (09/10/2026)

**Tác nhân:** Claude Code (VSCode/WSL), chế độ "dùng kiro-cli" · **ECS cuối phiên:** `aa-cis-dev-api:498` / `worker:53` (cùng SHA `f298b05`, rollout COMPLETED, /health 200) · **Migration mới:** không · **Job queue:** sạch · **Kiro credit:** còn ~920/2.000 (dùng ~258 trong phiên, reset 01/11).

## Trạng thái đầu phiên
Khớp memory S221: api `:489` / worker `:44` cùng SHA `4cc4f52`, queue 0, /health 200, Kiro preflight OK (1.131 credit). Không lệch.

## Quyết định của Nghiệp (chỉ điều Nghiệp nói)
- Phiên làm **ít nhất 3–5 issue** (bỏ quy tắc v3 "một issue một phiên"); **mỗi issue phải giới thiệu là gì / làm gì / ai làm / kiểm thế nào** trước khi làm.
- Shadow judge: **giữ 10%**, theo dõi chi phí + chất lượng, **chốt dùng 1 model vào 31/10/2026** (không chạy 2 model lâu dài). Cần **công tắc bật/tắt shadow + chỉnh % mẫu trên UI**.
- **Mọi đường LLM ưu tiên Bedrock**; đổi mặc định judge trong code sang Luna qua Bedrock acc3; **giữ OpenAI làm dự phòng**.
- `n7_judge` và N7 là tàn dư → tạo issue dọn, **phải kiểm kỹ không còn dùng thật** (AA-753).
- Distinctiveness: **ẩn hẳn** ở admin (repo gốc của chị Thư đã bỏ khái niệm); tạo issue gỡ cả phía tenant (AA-754) và **bỏ luôn tab Competitors** để tenant không hiểu nhầm.
- AA-747: đồng ý giao Kiro code + **chạy wave đo ~50 tour (India)**, thử 3 tour trước.

## Kết quả chính
**AA-752 — Done.** **#612** PR B (Kiro 72 credit, 2 vòng): PageHeader kit trên 15 trang, nút thương hiệu (Button kit; `Btn` cũ uỷ quyền), một định dạng ngày "9 Oct 2026", danh sách dạng thẻ < 768px (DataTable kit + Master/Tenants/Jobs), sửa smoke logo flaky (chờ hydrate). Claude sửa tiêu đề thẻ bị cắt. p95 `/admin/search` phía server ≈ 20–40 ms (TTFB 255 ms trừ nền mạng `/health` 221 ms). Smoke production 21 pass / 0 flaky.

**AA-721 — Done.** **#613** trang Jobs trên kit + react-query (Kiro 14 credit, 1 vòng): worker sống theo task revision + "show stopped (19)", bảng Job kinds (concurrency/max_attempts/expected_seconds + đếm theo trạng thái), ghi rõ job chạy ở service `aa-cis-dev-worker`. Smoke production 21 pass.

**AA-686 — Done.** **#614** backend (Kiro 16 credit + reviewer PASS-with-nits; Claude sửa: `null` xoá shadow, giá ≥ 0): PATCH route/shadow, catalog GET/PATCH, báo cáo A/B shadow, audit mọi thay đổi vào `acp_shared.audit_log` (cả PATCH model cũ). **#616** (Claude, phát hiện khi verify live): `s1_judge` chỉ trả điểm → agreement luôn null; suy đạt/trượt từ gate 7.0. **#618** UI (Kiro 20 credit): Settings → LLM Models 3 tab (Stages: chuỗi dự phòng + **công tắc shadow ON/OFF + % 0/10/20/50/100**; Catalog; Shadow A/B), ẩn `n7_judge`.
- **Đổi cấu hình thật qua API (audited):** shadow `s1_judge`/`s1_brand_audit`/`t10_judge` 100% → **10%**; `n7_judge` tắt shadow.
- **Số A/B (s1_judge, 5.135 cặp):** Luna 6 đồng ý đạt/trượt với Luna 5.6 **81,8%**, lệch điểm 0,65; chi phí $0,000775 vs **$0,000440** mỗi lần (Luna 6 rẻ hơn ~43%). GPT-4.1 cũ: 74,3%, lệch 1,95. Ghi AA-714 (due 31/10).

**AA-714 (In Review, due 31/10).** **#617** (Claude): SAFE_DEFAULTS judge = Luna 5.6 (Bedrock acc3) → Luna 6 (Bedrock) → Luna 6 OpenAI → GPT-4.1 (key legacy, chạy được khi DB/catalog sập). 7 ngày qua 100% lời gọi LLM đi Bedrock; 0 lời gọi GPT-4.1.

**AA-749 — Done.** **#615** (Kiro 19 credit): atom platform `distinctiveness = null`, lọc `NOT_SCORED`, lập kế hoạch bỏ qua atom chưa chấm (live: NOT_SCORED 23.864). **#619** (Claude): ẩn hẳn ở Atom Curation (badge, lọc, 4 thẻ KPI).

**AA-747 — In Progress.** **#620** (Kiro 66 credit + reviewer PASS-with-nits; Claude sửa 3 điểm): flag_fix không gửi seo_meta/title cho LLM khi fit tất định đã sửa; nudge tối đa 3/tour (ngày tệ nhất trước); S1 chạy song song prefetch (FE chỉ chờ tạo job; prefetch commit theo lô 5, kiểm lại độ mới mỗi lô; rewrite chờ đúng tour của mình tối đa 5′, không mua 2 lần). `S1_PER_DAY_TARGETS` viết sẵn, **mặc định TẮT**. Chưa đo trên wave.

**Issue mới:** **AA-753** dọn 6 stage N7 + `acp_produce/gates.py` (đã kiểm 3 lớp: code main không import, 0 lời gọi `n7_*` trong `llm_call_log`/`llm_shadow_log` từ trước tới nay, 6 dòng config nằm im). **AA-754** gỡ distinctiveness phía tenant + bỏ tính năng Competitors (không đụng `cross_brand_distinct` của judge).

## Thay đổi hạ tầng / dữ liệu
- Không Terraform, không migration. Ghi DB duy nhất: 4 lần PATCH route qua API (audit_log có before/after).

## Kế hoạch phiên sau (S223)
1. **AA-747 đo wave:** #620 đã deploy (f298b05) → chạy 3 tour India thử → ~50 tour India (so mốc S218 86% / 7,69): flag_fix ≤ 15%, nudge ≤ 3/tour, S1 đầu < 2′. Sau đó A/B `S1_PER_DAY_TARGETS` trên 10 tour.
2. **AA-753** dọn N7 (DRY RUN xoá 6 dòng config). 3. **AA-754** gỡ distinctiveness + Competitors (DRY RUN migration).
4. **AA-695** gộp segment → **AA-741** T-series 4 tenant brand.
5. 31/10: chốt judge (AA-714) — xem 18% ca bất đồng có sát ngưỡng 7.0 không.

## Lưu ý kỹ thuật / BÀI HỌC (đã ghi `skill/aa-lessons/lessons.md` + `kiro-delegate/SKILL.md`)
- Báo cáo mới phải chạy trên dữ liệu thật trước khi báo xong (agreement null của s1_judge).
- Nhiều PR backend: merge nối tiếp, chờ Deploy Dev xong mới update-branch + auto-merge PR sau (`BEHIND` chặn im lặng; `gh api -X PUT .../pulls/<n>/update-branch`).
- SAFE_DEFAULTS phải chạy được khi DB/catalog sập (giữ key legacy cuối chuỗi).
- Kiro song song bằng `git worktree`; `next build` cần `cp -al node_modules` (Turbopack từ chối symlink); brief không dùng `{a,b}` trong Files in scope.
- Ghi cấu hình qua API bị auto-mode chặn — cần Nghiệp cho phép.
