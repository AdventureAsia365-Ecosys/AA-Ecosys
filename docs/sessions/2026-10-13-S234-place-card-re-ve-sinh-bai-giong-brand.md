# S234 (13/10/2026, Claude Code — WSL/VSCode, Ultracode): place card rẻ 8×, vệ sinh bài T9, giọng brand, sửa câu admin, 4 vòng đo n=20

**Tác nhân:** Claude Code (Ultracode: workflow nhiều agent cho tìm hiểu / code / review / panel). **Bối cảnh:** tiếp S233
(checkpoint n=20: 30% sửa nhẹ, chưa đạt thương mại).

## Trạng thái đầu phiên
4 repo sạch main/master; ECS api `:555` / worker `:110` (`dev-3d833d6`), NAT running, RDS available, `/health` 200,
`shared.job` 0 queued/running. Không lệch S233.

## Quyết định của Nghiệp
- Duyệt danh sách S234 (AA-772 → AA-768 → AA-771 → F9 v2 → AA-769 → đo lại n=20); bật **Ultracode**.
- "Làm đầy đủ tới khi xong, đạt chất lượng, báo cáo rõ ràng kèm tư vấn kỹ thuật + nghiệp vụ, rồi mới hỏi dừng phiên";
  tối ưu kỹ thuật + giảm chi phí mọi việc.
- Hỏi "hệ thống chẳng phải đã lọc atom chung chung/hậu cần rồi?" → có, nhưng ở chỗ khác (`is_logistics_atom` chỉ lúc
  atomize; `atom_ranking.excluded_reason` chỉ Slate đọc); đường place card chỉ lọc `is_empty_marker` + place rỗng.
- Hỏi **"chưa thử Luna à"** → A/B thêm 2 nhánh Luna → chuyển soạn thẻ sang gpt-5.6-luna (migration 222).
- Duyệt merge Infra #93; tắt auto mode để merge/deploy liên tục; nhập MFA khi STS hết hạn.
- Yêu cầu báo cáo luôn ghi **chạy bằng gì** (job worker hay ECS exec) và **cách chấm**.

## Thay đổi Codebase
**AA-CIS-App** (merged, CI 9/9 xanh, deploy Dev):
- #687 AA-772: place card — lọc bằng luật trước LLM (`names_somewhere` của ranking + your/our + danh từ hậu cần), gom theo
  (place, nước), alias + tên lõi trước khi soạn, cache âm `place_card_miss`, key = tên lõi | nước (NFKD), T9 chỉ đọc
  thẻ, job build trần 40 địa danh, API/UI tìm + gộp thẻ trùng có audit; sửa ghi `tokens_in` Converse (cộng cache read/write).
- #692 AA-772: soạn thẻ **gpt-5.6-luna**, kiểm **Haiku** (cả hai `validate`, khác hãng), DRAFT_MAX_TOKENS 1500.
- #694 AA-772: seed giữ 1 giá trị/fact giữa các thẻ, thứ tự ngày, keyword phải có căn cứ trong seed (gỡ "meditation retreat").
- #688 AA-768: `hygiene.py` (scope, lọt chữ, social proof, câu lặp, hashtag), F12_scope/F13_hygiene, seed route theo ngày.
- #690 AA-771: `channel_spec` LinkedIn theo brand, sanitizer brief T8 (cả angle cũ), F14/F15.
- #689 + #693 AA-769: nút Cut/Rewrite/Edit trong drawer (Haiku `t9_repair`, audit log), `regenerate-angles`; sửa
  hydration #418 link sâu + panel trùng không tick sẵn.
- #691 AA-768: `claim_rules.py` (F9 v2, chưa nối gate).
- #695/#696/#697/#698 AA-768 (vòng 2–4): F16_faq (≥3 cặp; regen FAQ từ fact chưa dùng), F13_leak, tên chuyến theo phạm
  vi, toàn vẹn repair, F13_repeat, F17_trip_fact (optional, giờ giấc, nơi ngoài phạm vi, cảnh báo gia đình, moment
  mỏng, nơi chỉ có trong nền), F18_rarity, date authority, CTA nguyên văn, final-pass `text_integrity.py`, title
  không trùng, SEO fit chỉ cho blog.
**AA-CIS-Infra:** #93 migration 221 (`place_card_miss`, `place_card_alias`, `atom_place_card.miss_reason`, stage
`t9_repair` haiku / `t10_claims` luna), #94 migration 222 (đổi route thẻ).
**Root:** log này, `docs/audits/2026-10-13-S234-t-series-rounds/` (panel 4 vòng, replay F9 v2, A/B model thẻ),
`db-schema-reference.md` (dump live sau 222), lessons (3 bài).

## Hạ tầng / dữ liệu
- Migration 221 apply 06:09Z, 222 apply qua DB Migrate (check → apply), kiểm DB đủ đối tượng.
- ECS cuối phiên: api `:568` / worker `:123`, image `dev-20a2387` (cùng SHA). 1 lần deploy song song bị guard SHA
  chặn đúng → rerun.
- Place card: tour Nepal mới 40 lời gọi → 37 thẻ ($0,082); Laos force 14 → 13 + 3 alias. Tổng 122 thẻ.
- DRY RUN gộp thẻ trùng: 8 nhóm trùng thật / 11 thẻ thừa + 1 thẻ mồ côi — **chờ Nghiệp duyệt** (chưa xoá gì).
- Dữ liệu test: 80 bài T9 (4 vòng × 20) trên 4 tenant test; 2 request blog clone qua `regenerate-angles`.

## Chạy bằng gì
- Viết bài đo: script local → public tenant API → job `t9_write` trên **worker** (`JOB_WORKER_IN_API=false`).
- T8 + build thẻ: admin endpoint (gọi từ container api) → job trên **worker**.
- A/B model thẻ, replay F9 v2, chứng minh FAQ: script adhoc **chạy thẳng trong task api** (ECS exec + nohup), stage `adhoc_*`.
- Kiểm DB/verify: S3 + ECS exec vào api. Migration: DB Migrate (one-off ECS task). Deploy: Deploy Dev.
- Panel chấm: agent Claude Code local (4 góc nhìn độc lập + fidelity + đếm lỗi cứng bằng code repo) — không qua gateway.

## Bằng chứng verify
| | S233 | r1 | r2 | r3 | r4 |
|---|---|---|---|---|---|
| Sửa nhẹ | 30% | 55% | 50% | **60%** | 55% |
| LinkedIn / blog sửa nhẹ | 6/12 · 0/8 | 11/12 · 0/8 | 10/12 · 0/8 | 10/12 · 2/8 | 10/12 · 1/8 |
| Điểm tổng | 5,33 | 5,52 | 5,57 | 5,64 | **5,74** |
| Lỗi cứng (cùng script) | 70 | 11 | 10 | 8 | **4 (đều trong bài held)** |
| Gate duyệt đúng | 42% | 59% | 80% | 77% | 73% |
- UI verify Playwright (desktop/mobile, sáng/tối): drawer Cut/Rewrite, nhãn F12–F15, panel thẻ trùng; preview #693 hết #418.
- Live: suggest → apply rewrite trên piece 18b85893, `admin_edits` có audit.
- Replay F9 v2 ($0,40): bắt đúng 71–75% (hiện tại 65–77%), gỡ oan 72% (54–57%), ổn định 38/38, rẻ hơn 55% — chưa đạt 90%, không nối.
- Chi phí LLM phiên **$5,75**: 80 bài ≈ $4,24; adhoc $1,32 (≈ $0,37 phí do replay bị deploy ngắt); thẻ $0,12; T8 $0,08.

## Linear
- **AA-769 Done.** AA-768, AA-771, AA-772 In Progress (đã comment bằng chứng + phần còn lại). AA-763 vẫn chờ job S1.

## Phần cuối phiên (sau báo cáo)
- **Gộp thẻ trùng** (Nghiệp duyệt): snapshot S3 → 8 nhóm / 11 thẻ gộp qua endpoint merge (audit) + xoá 1 thẻ mồ côi
  (transaction, audit) → verify độc lập: thẻ 122 → 110, atom có thẻ 146 → 146, alias 361 → 371, còn 0 nhóm trùng.
- **Jev trục T tắt hẳn** (Nghiệp duyệt): 9 câu hỏi T → `off` qua admin API; `jev_tenant_allowlist` 4 → 0 (backup S3).
  A-series giữ enforce (~72k phán quyết/14 ngày). Rủi ro: ~48k lỗi 402 trên A-series/14 ngày.
- **Báo cáo chi tiết** (`docs/audits/2026-10-13-S234-t-series-rounds/08`–`11`): cách T9 viết bài + 26 gate, thống kê
  lỗi/retry từ DB (F9 47→15 bài, sửa câu cứu 49%, 20% retry làm hỏng thêm, judge F9 gắn cờ lại câu không đổi ở 10/15
  bài bị hoàn tác), so sánh repo chị Thư, audit Jev, kế hoạch issue + prompt dán sẵn, thiết kế đội agent.
- **Linear:** tạo AA-773…AA-784 (issue con của AA-768/771/772/729) theo kế hoạch 09; comment AA-756 (Jev).
- **Quy trình:** định dạng commit `Refs AA-xxx` (sửa `~/.claude/CLAUDE.md`); hook `.claude/hooks/subagent-guardrails.sh`
  chặn agent con push/merge/deploy (khoá theo `agent_id`, verify live); orchestrator được `gh pr merge` khi auto mode;
  nới "CIS trước" cho chế độ nhiều làn.

## Việc phiên sau (S235)
**S235 = thử nghiệm đội agent nhiều làn** — kế hoạch: `docs/audits/2026-10-13-S234-t-series-rounds/11-next-session-team-pilot.md`
(làn A CIS backend AA-776/773/774/775/778/780 + đo r5; làn B portal; làn C **Booking từ đầu** sau review tài liệu; làn D docs;
agent kiến trúc sư hệ sinh thái review trước và trước merge).

### Danh sách cũ (đã chuyển thành issue AA-773…AA-784)
1. Nghiệp duyệt gộp 8 nhóm thẻ trùng + xoá thẻ mồ côi (DRY RUN có sẵn) → chạy theo destructive-ops.
2. Writer blog: cờ `optional` đi từ seed tới writer + kiểm sau viết; chặn hứa hẹn nhịp/độ khó không có trong seed; FAQ
   answer phải chứa chủ thể câu hỏi.
3. LinkedIn: sàn 120 từ (chặn), giọng Trail Pulse (energetic/social), danh sách câu sáo mở rộng (S235 cân nhắc
   viết lại 1 câu mở bằng model khác thay vì thêm gate).
4. Hiệu chỉnh panel AI bằng người thật (10 bài) trước khi chốt ngưỡng thương mại.
5. F9 v2: phân loại claim (place_background/opinion bị lọt) rồi replay lại; chỉ nối khi ≥90%.

## Lưu ý kỹ thuật
- Script adhoc chạy lâu → one-off ECS task, không `nohup` trong task api khi còn PR chờ merge (deploy ngắt).
- Soạn/kiểm khác hãng → cả hai stage `validate`; admin PATCH không đổi được hãng → migration.
- FAQ: luật "lặp thân bài" phải so theo câu + thứ tự, không túi từ (bài bám seed luôn dùng từ của seed).
