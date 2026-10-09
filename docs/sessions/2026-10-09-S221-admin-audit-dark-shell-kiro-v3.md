# S221 — Audit UI admin + dark theme + khung admin mới + kiro-delegate v3 (09/10/2026)

**Tác nhân:** Claude Code (VSCode/WSL), chế độ "dùng kiro-cli" · **ECS cuối phiên:** `aa-cis-dev-api:489` / `worker:44` (cùng SHA `4cc4f52`, rollout đang chạy lúc ghi log — #610 chỉ đổi frontend, image backend giống #611 `:488`) · **Migration mới:** không · **Job queue:** sạch (deploy-gate active 0) · **Kiro credit:** còn 1.131/2.000 (reset 01/11).

## Trạng thái đầu phiên
Lệch nhỏ so với memory S220: ECS đang `:482`/`:37` (SHA `646a651`, do #603 tự deploy-on-push), memory ghi `:481`/`:36`. Vô hại. Queue 0, /health 200, Kiro preflight OK.

## Quyết định của Nghiệp (chỉ điều Nghiệp nói)
- Chốt danh sách S221 theo đề xuất (AA-601 trước).
- **Dashboard cũ: bỏ hẳn** (AA-722). **Dark theme admin: làm luôn trong AA-601.**
- Nút Regenerate phải **có chữ** (icon nhỏ khó nhận biết) — trả lại trong AA-728.
- Theme switch phải dễ thấy (chuyển lên header sidebar, rồi topbar).
- Thiết kế lại khung admin chuyên nghiệp như trang thương mại, giữ bản sắc adventure.asia: sidebar ẩn/thu gọn, logo → Overview; **không nhãn DEV**; ⌘K phải dùng được thật; điện thoại dễ dùng. Tạo issue **AA-752**. Cập nhật design system "AA-CIS Design System" theo token thật.
- **Kiro: đồng ý chia việc** (Kiro = backend/logic/cơ học; Claude = UI cần mắt, sửa nhỏ, CI/bảo mật) + **quy trình v3** (Kiro tự lặp tới khi CI + UI smoke trên preview xanh, Claude gác cổng, reviewer chỉ khi rủi ro, mỗi issue lớn một phiên mới). Cho phép Kiro chạy smoke trên preview (thực hiện qua CI, Kiro không cầm credential).

## Kết quả chính
**AA-601 — Done (verify production).** Audit 16 trang trên Dev: mọi trang tải được, API 2xx, 0 lỗi console, dữ liệu thật (Overview 37 chờ duyệt = Review Queue; 880 Master khớp mọi trang). Lỗi thật + sửa:
- **#605**: smoke phủ 16 trang + tín hiệu "ready" từng trang + kiểm tràn ngang 390px; sidebar off-canvas < 768px; Jev "Acted on = NaN" (stage chỉ có trong rollup cache → `acted: null`) → backend zero-fill + FE guard (live: `s1_judge_tiebreak` acted 0); Review Queue nút bị cắt ở 1440 là **Approve**. Kiro 3 vòng + Claude tự đo trên preview (thủ phạm: `<select>` tên tour tự rộng theo option dài nhất qua ancestor min-content → `width: 100%`).
- **#606** dark theme: token `A`/`K` → CSS variables (light = giá trị cũ), theo hệ điều hành; portal + login giữ sáng; ~95 màu trắng cứng; smoke chặn mảng sáng lớn ở dark. Kiro 3 vòng (reviewer bắt login bị tối + giá trị legacy đổi).
- **#607** theme switch lên header sidebar (footer bị khuất trên laptop).
- Smoke production 17 pass / 3 skip (portal, chưa có tenant test).

**AA-722 — Done.** **#608** bỏ `/admin/dashboard` (đọc `shared.pipeline_runs` lỗi thời), redirect theo vai trò (admin → Overview, reviewer/content → Review Queue vì Overview admin-only); Master Content bỏ panel Pipeline Runs, thêm Score distribution (27 + 557 + 296 = 880). Kiro 1 vòng 12,7 credit. Endpoint giờ không FE nào gọi: `/admin/metrics`, `/admin/metrics/seo`, `/admin/metrics/spot-workers` (giữ, dọn sau).

**AA-728 — Done (verify dữ liệu thật).** **#609** `failure_class` + `retryable` + `hint` mỗi dòng Review Queue; Regenerate (có chữ) chỉ ở dòng thử lại được; Actions 2 hàng; bulk bỏ qua dòng không thử lại được. Live 37 dòng: needs_human 26 (cả **23 tour cưỡi voi**), low_quality 7, hard 3, raw_insufficient 1. Kiro 2 vòng 9 credit; Claude bắt regex `\b5\d\d\b` bắt nhầm số.

**AA-752 — In Progress (PR A ship).** Thiết kế: canvas https://claude.ai/artifact/Hsr5SaBRNS7AxgRdoDhBAx (A mở rộng sáng, B thu gọn tối, C điện thoại thanh dưới đáy). **#611** `GET /admin/search` (tách riêng để backend lên trước UI) — verify live ("kerala" 8 tour, "wander" tenant, "a3_" 5 job, không secret 403). **#610** khung `AdminShell` từ `app/admin/layout.tsx` (kit Sidebar/Topbar/CommandPalette/BottomNav), logo → Overview, thu gọn 68px nhớ trạng thái, ⌘K thật, deep link `?tour=`/`?tenant=`, thanh dưới đáy điện thoại, không nhãn môi trường. Smoke production 20 pass / 1 flaky / 3 skip. **Task đầu tiên chạy v3**: Kiro tự lặp 2 lần trên preview (topbar làm tràn 390px mọi trang; flake reload) tới khi xanh, Claude chỉ gác cổng.

**Design system "AA-CIS Design System" v2** (https://claude.ai/artifact/FEWjBR5UfmvHFSesjL6nR3): bản 19/09 đã cũ (cam/đỏ, Fraunces/IBM Plex) → token thật light + dark, một accent vàng, đỏ chỉ cho lỗi, Fahkwang + Poppins; vẽ lại Btn/Badge/Card/ProgressBar/cover; bỏ mockup Dashboard. T10Review/T8AngleGate còn màu cam cũ → vẽ lại khi làm portal.

**Linear:** Done AA-601, AA-722, AA-728; In Progress AA-752 (mới, comment còn lại PR B).

**Skill / tooling (root PR):** `kiro-delegate` v3 (SKILL + brief-template: brief 10–20 dòng trỏ Linear, Kiro push → CI preview → tự sửa ≤ 3 vòng, Claude gác cổng, reviewer chỉ khi rủi ro, mỗi issue lớn một phiên); `kiro-run.sh` nhận path feedback tương đối; `.claude/CLAUDE.md` cập nhật; bài học tràn ngang mobile.

## Đánh giá Kiro (chốt S221, 8 task S220–S221)
| Task | Vòng | Credit | Ghi chú |
|---|---|---|---|
| aa601a responsive/smoke | 3 + Claude | 49,8 | Kiro đoán sai nguyên nhân tràn 2 lần |
| aa601b dark | 3 | 93,6 | reviewer + ảnh bắt lỗi |
| aa722 | 1 | 12,7 | sạch |
| aa728 | 2 | 9,0 | sạch, Claude bắt regex |
| aa752a shell (v3) | 2 (tự lặp) | 84,2 | xanh trên preview không cần Claude đo |
Kết luận: điểm nghẽn là Kiro không nhìn thấy app chạy → v3 cho Kiro đọc CI/ảnh smoke qua `gh` (không credential). ACP (hướng B) không đáng xây. Tiết kiệm token lớn nhất: phiên ngắn.

## Kế hoạch phiên sau (S222, phiên mới)
1. **AA-752 PR B** (Kiro, v3): PageHeader + nút thương hiệu 15 trang; một định dạng ngày "9 Oct 2026"; danh sách dạng thẻ trên điện thoại; sửa smoke flaky logo; đo p95 `/admin/search` phía server; implementation notes.
2. **AA-721** trang Jobs trên khung mới. 3. **AA-686** Gateway UI.
4. Nhóm B (Kiro): AA-695 → AA-747 → AA-749. 5. Nhóm C: AA-741.

## Lưu ý kỹ thuật / BÀI HỌC
- Tràn ngang mobile: đo phần tử gây tràn rồi mới sửa (đã ghi `skill/aa-lessons/lessons.md`); smoke giờ tự in phần tử gây tràn.
- Preview Vercel gọi **backend Dev** → UI cần endpoint mới thì tách PR backend, merge/deploy trước (#611 trước #610).
- Ảnh smoke chụp lúc chart đang animate có thể trông như thiếu dữ liệu — kiểm API trước khi kết luận.
- `docs/architecture/db-schema-reference.md` ghi migration 205, thực tế đã có 206 (S219) → regenerate khi có migration kế.
- Design system artifact khác code → repo thắng; đã đồng bộ v2.
