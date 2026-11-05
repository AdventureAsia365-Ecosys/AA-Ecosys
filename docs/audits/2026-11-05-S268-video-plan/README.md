---
title: Kế hoạch video sản phẩm và UAT (S268)
lang: vi
---

# Kế hoạch video sản phẩm và UAT (S268, 05/11/2026)

Bản tư vấn cho tech lead (tiếng Việt theo luật N-7 cho audit tư vấn). Theo dõi trong Linear **AA-855** (tech lead chọn gộp kế hoạch series sản phẩm vào AA-855, 05/11/2026).

Quyết định của tech lead ngày 05/11/2026: không đăng nội dung làm từ dự án lên kênh cá nhân (AA-1021 dừng). Tài liệu này giữ hai mảng: series giới thiệu sản phẩm và video vận hành (UAT, hướng dẫn, hồi quy).

## Series video giới thiệu sản phẩm (PV)

Đề xuất chuỗi video giới thiệu sản phẩm cho toàn hệ sinh thái AA theo mô hình B2B-only (ADR 0019). Có 27 video, chia 4 nhóm khán giả:
- OV, tổng quan cho chủ doanh nghiệp / nhà đầu tư / đại lý tiềm năng: 3 video
- AG, chủ đại lý và nhân viên đại lý: 11 video
- ST, staff và ops nội bộ của AA: 10 video
- TR, khách du lịch dùng planner mang thương hiệu của đại lý: 3 video

Mỗi video gắn với một cổng: milestone R1–R7 hoặc mốc pilot 1 (~S272) và pilot 2 (~S277). Nhờ vậy không quay thứ gì còn nằm trên kế hoạch như thể đã chạy.

Ba điểm cốt lõi:
1. **Video TripPlanner giới thiệu ngày 30/10 đã lỗi thời.** Lời đọc vẫn nói "tư vấn viên của Adventure Asia sẽ biến kế hoạch thành chuyến đi thật" và trang mang thương hiệu AA. Điều này trái với bất biến 1 của ADR 0019, với b8 ("Powered by AA" mặc định tắt) và với d11 (lead chuyển về đại lý). Nên chuyển video sang thư mục lưu trữ và không gửi ra ngoài nữa.
2. **Ưu tiên một "gói onboarding pilot", quay ngay sau khi cổng pilot 1 xanh (S272–S273).** Gói gồm AG-01…AG-07, TR-02 và OV-01 v1. Không quay sớm hơn, vì ba thay đổi giao diện lớn rơi đúng S270–S272: AA-1008 (ShellFrame chung), i18n của studio trong R3, và việc gộp app agency. Quay trước đó gần như chắc chắn phải quay lại.
3. **Dùng lại pipeline aa-uat-video, không dựng công cụ mới.** Mỗi chương của video sản phẩm là một kịch bản Playwright có assert. Kịch bản chạy ở fast mode như regression để tự báo video nào đã lỗi thời. Ghép chương bằng longform.py; khi UI đổi chỉ quay lại đúng chương bị đổi. Chi phí $0 (TTS chạy local).

Những việc cần business owner quyết: chia sẻ video ra ngoài cho đại lý pilot / khách tiềm năng, có nói giá trong video hay không, đăng YouTube hay website (kênh của công ty, không phải tài khoản cá nhân), ghi chú giọng đọc là giọng tổng hợp, và lời cam kết B2B b1 mà counsel chưa duyệt.


### Đề xuất

- **1. Danh mục video theo khán giả: tổng quan (OV) — 3 video.** PV-OV-01 'Nền tảng AA trong 3 phút' (2,5–3 phút, EN + VI). Đi qua Content (sản phẩm nền), CRM và TripPlanner (add-on), Booking (back office B2B), AI gateway, mô hình tenant và feature key.
- v1 quay S273, sau pilot 1. Lúc đó chỉ Content + CRM là live; 'Book with AA' và TripPlanner cho đại lý chỉ hiện trên một slide 'Next', không ghi ngày.
- v2 quay ≥S281, sau R7.

PV-OV-02 'AA làm việc với đại lý thế nào' (90 s, EN + VI). Chỉ có sơ đồ động, không có màn hình: AA chỉ bán cho đại lý; đại lý là controller, AA là processor; hai loại hoá đơn là phí phần mềm và quyết toán tour. Viết kịch bản được ngay vì video giải thích mô hình, không khẳng định tính năng nào. Nhưng chỉ dựng xong sau khi business owner duyệt câu chữ cam kết b1, mà counsel chưa xem.

PV-OV-03 'Tình trạng nền tảng' (4–5 phút, VI, nội bộ cho business owner). Mỗi cổng quay một bản: S272, S277, S280. Video này thay kiểu 'video tiến độ CRM' của S261. Số liệu lấy từ plan.json; số trên Dev ghi rõ là chưa ổn định. _Vì sao:_ Business owner và người ngoài cần hiểu mô hình B2B mới trước khi xem tính năng. Tách phần 'mô hình' (làm sớm được) khỏi phần 'màn hình' (phải chờ cổng) giúp có nội dung sớm mà không trình bày việc đang thiết kế như đã chạy.
- **2. Danh mục: chủ đại lý và nhân viên đại lý (AG) — 11 video, đi kèm gói onboarding pilot.** Tất cả quay EN + VI, mỗi ngôn ngữ một MP4 riêng có phụ đề in cứng (theo Q1 của S261).

- **AG-01 Bắt đầu** (2 phút). Content home, mời thành viên kèm map vai trò (d7), đổi EN/VI. Cổng: R3 đóng (~S272).
- **AG-02 Thương hiệu và giọng văn, T0** (2 phút). Cổng: i18n studio R3 xong.
- **AG-03 Tìm tour trong marketplace AA** (2–3 phút). Chỉ tour live (invariant 3). Chương 'giá from / RRP' chỉ quay sau R4, khi price.from.v1 trả RRP.
- **AG-04 Lên kế hoạch nội dung** (slate, angle, quarter plan; 2 phút).
- **AG-05 Viết và duyệt bài** (2–3 phút). Cho thấy AI notice và dấu ai_generated (AA-1040) và gate d21. AG-04 và AG-05 cần đường LLM. Nếu chưa có thì chỉ quay output có sẵn ở dạng đọc.
- **AG-06 Đăng lên kênh của đại lý** (2 phút). WordPress và Facebook theo BYO, cộng việc tự gỡ bài khi tour ngừng bán (d20). Bị chặn đến khi tech lead tạo site WordPress test mới.
- **AG-07 CRM trọn luồng** (6–8 phút, có chương). Đi lead → pipeline → client 360 → proposal → khách accept trên điện thoại → hoá đơn và đặt cọc → client portal. Quay lại các đoạn của CRM review S262, nhưng trong app đã gộp.
- **AG-08 Book with AA** (quote/hold, 'Bookings with AA', hoá đơn quyết toán). Cổng: R4 (~S274).
- **AG-09 Gói, add-on, ngân sách AI, hoá đơn SaaS**. Cổng: R4.
- **AG-10 Dựng trip planner thương hiệu riêng** (brand token, path, launcher, lead vào CRM hoặc webhook). v0 quay S277; v1 quay sau R7 (S280).
- **AG-11 Dữ liệu và quyền riêng tư cho đại lý** (controller/processor, xuất và xoá, cấp support grant). Cần câu chữ do business owner / counsel duyệt.

Gói onboarding pilot = AG-01…AG-07 cộng TR-02 và OV-01. _Vì sao:_ Đại lý pilot ở mốc 1 cần tự học được sản phẩm. Đây là lý do kinh doanh chính của cả chuỗi, nên các video AG được sắp sau R3, R4, R5 và R7. Tách chương giá ra để khi R4 đổi giá chỉ phải quay lại đúng một chương.
- **3. Danh mục: staff và ops AA (ST) — 10 video nội bộ, giọng VI, UI tiếng Anh.** - **ST-01 Tham quan AA Admin** (Home / Tenants / AA Catalogue / Tenant QA / AI & spend / Writing Lab / Platform; 4 phút). Quay sau AA-1008 ShellFrame (S272).
- **ST-02 Onboard một đại lý mới** (saga tenant_provision, plan, subscription, entitlement, override, trial; 3 phút). R1 đã xong nên làm v0 được ở S269; v1 quay sau ShellFrame.
- **ST-03 Account manager** (giao tenant, tenant scope 403, view-as chỉ đọc 60 phút có banner và ghi log). Cổng: R2 đóng S271, quay S272.
- **ST-04 Tenant QA, gate d21 và fan-out d20**. Quay sau khi AA-1039 đóng (~S274).
- **ST-05 AI & spend** (route control center, thứ tự provider, Route trace, ngân sách tenant, fail-closed). Quay sau khi AA-1042 đóng (S269–S270).
- **ST-06 Writing Lab**. Chờ đường LLM và việc gỡ băng TL-11.
- **ST-07 Booking cho B2B** (agency desk, supply và net rate, hạng đại lý 0/3/6 %, RRP có maker-checker). Sau R4, quay S275.
- **ST-08 Finance** (agency_invoice SaaS và settlement, thanh toán maker-checker, paid-through báo về CIS). Quay S275.
- **ST-09 Vận hành TripPlanner theo tenant** (tenant demo, trần AI cho các stage tp, đường đi của lead). Quay S277.
- **ST-10 Runbook hỗ trợ pilot** (support grant, export và restore một tenant). Quay S272–S273, chỉ trên tenant demo.

Video ST không bao giờ công khai: trên màn hình có chi phí, route AI và account ID (admin hiện account ID lúc chạy). _Vì sao:_ Theo b13, mỗi đại lý có một người phụ trách đích danh, và R2 thêm 6 vai trò staff. Staff mới cần tài liệu đào tạo có hình. Bus factor hiện bằng 1, video giúp chuyển giao kiến thức. Lỗi thời ít hại vì chỉ dùng nội bộ, nên làm v0 sớm được.
- **4. Danh mục: khách du lịch qua planner của đại lý (TR) — 3 video, không có thương hiệu AA.** - **TR-01 Lên kế hoạch chuyến đi trên bản đồ** (90 s, EN; quay cả điện thoại 390 và desktop). Dùng brand token của một 'Demo Agency' tổng hợp; 'Powered by AA' tắt (b8). Chỉ quay sau R7 (S280), vì R7 đổi gần hết UX: ảnh, icon, sắp xếp có undo, chọn ngày, share / PDF / .ics.
- **TR-02 Trang chuyến đi / client portal từ link CRM** (90 s, điện thoại). Hôm nay đã live (M11), quay lại trong app gộp ở S273.
- **TR-03 Gửi kế hoạch cho đại lý** (lead.submitted.v1; 60 s). v0 ở S277, v1 ở S280.

Các video này để đại lý gửi cho khách của họ. Vì vậy thương hiệu phải trung tính hoặc là của đại lý, và lời đọc không nhắc AA. _Vì sao:_ ADR 0019 d10 và d11 định nghĩa traveller là guest của tenant. Video mang thương hiệu AA sẽ trái b8 và trái invariant 1, đúng như lỗi của video 30/10.
- **5. Luật cổng: chỉ quay thứ đã live.** Một video, hoặc một chương, chỉ được quay khi đủ ba điều:
(a) Mọi issue nó cho thấy đã Done theo aa-ship: merge, CI xanh, deploy, verify live.
(b) Kịch bản chạy fast mode PASS trên Dev.
(c) Không có thay đổi UI lớn đã xếp lịch trong 1–2 phiên tới.

Phần chưa có chỉ được nói trên slide 'Coming next' trong video OV, không ghi ngày và không có mã AA-xxx.

Các đợt thay đổi UI đã biết, không quay ngay trước chúng:
- AA-1008 ShellFrame và i18n studio R3 (S270–S272): ảnh hưởng mọi video admin và agency.
- R4 giá / RRP (S274): ảnh hưởng chương giá của AG-03.
- R5 rồi R7 (S277–S280): ảnh hưởng mọi video TripPlanner.
- R8 gộp màn Booking vào CIS: ảnh hưởng ST-07 và ST-08.
AA-911 (S275) không ảnh hưởng, vì phần đăng nhập không lên hình. _Vì sao:_ Luật lane hiện có là không trình bày việc đang thiết kế như đã chạy, và Jira chỉ được nói 'chạy được' khi có bằng chứng live. Video sản phẩm chính là một lời khẳng định như vậy với khán giả bên ngoài.
- **6. Sản xuất: dùng lại pipeline UAT, thêm lớp hoàn thiện cho video sản phẩm.** - **Dữ liệu và kịch bản.** Mỗi chương là một kịch bản trong tools/uat/scenarios/product/. Nên dùng chung kịch bản với UAT khi được: quay một lần, ghép theo hai kiểu.
- **Tenant để quay.** Một tenant 'Demo Agency' riêng, tạo bằng tenant_provision, kind tổng hợp, có brand token. Có prep/cleanup chạy lại được (giống S261). Tuyệt đối không quay tenant pilot: theo d16 đó là PII thật, và hook chặn agent đọc nó.
- **Khung hình.** Video sản phẩm quay viewport 1600×900 (16:9) để lên YouTube hay website không bị viền đen; UAT giữ 1440×900. Đoạn điện thoại 390×844 đặt giữa khung.
- **Thẻ hình.** Thẻ mở, thẻ chương và thẻ kết làm bằng HTML theo kit, chỉ một bộ dùng cho mọi video (theo luật 'consistent, not one-off').
- **Giọng đọc.** EN là Kokoro af_heart, VI là VieNeu 'Thục Đoan'. Không dùng giọng clone của tech lead cho video sản phẩm, vì video sản phẩm thuộc công ty còn giọng là danh tính cá nhân, và như vậy bus factor lại thêm phụ thuộc vào một người.
- **Ghép.** longform.py ghép theo chương, nên chỉ quay lại đúng chương bị đổi.
- **Nhịp.** Mỗi phiên tối đa 2 video hoàn chỉnh, hoặc khoảng 15 đoạn (luật S260). Một Chromium và một model TTS trong RAM tại một thời điểm. _Vì sao:_ Pipeline đã chứng minh chạy được ($0, có kiểm khung hình và khớp tiếng). Gắn video với kịch bản có assert cho phép tự phát hiện video đã lỗi thời thay vì phải nhớ bằng đầu.
- **7. Chính sách quay lại khi UI đổi.** Mỗi PV-id có một manifest gồm: các chương, kịch bản của từng chương, route, component kit dùng tới, và SHA của app lúc quay.

Sau mỗi deploy app, hoặc ít nhất một lần mỗi phiên, chạy `dryrun.cjs --only PV-*` ở fast mode.
- Assert FAIL → video thành **stale** trong catalogue và không được gửi ra ngoài cho tới khi quay lại.
- Đổi nhãn hay điều hướng → quay lại chương bị đổi, tăng v<n> cho cả video.
- Đổi thuần thẩm mỹ (màu, khoảng cách) → không quay lại. Riêng video OV và AG đang dùng bên ngoài thì gom lại, quay một lần ở cổng kế tiếp.

Không ghi đè bản cũ: giữ bản cũ để mốc thời gian trong các phát hiện vẫn đúng. Bản bị thay thì chuyển vào thư mục lưu trữ bằng `rclone moveto` để link vẫn sống. _Vì sao:_ UI đang đổi theo từng milestone R. Có luật rõ thì tránh hai chuyện: quay lại tràn lan, và gửi đại lý một video sai.
- **8. Đặt tên, phiên bản và nơi lưu.** **Tên file:** `PV-<AUD>-<NN>_<slug>_<EN|VI>_<yyyymmdd>_v<n>.mp4`, ví dụ `PV-AG-07_crm-end-to-end_VI_20261118_v1.mp4`. Tiền tố PV tách hẳn khỏi id UAT (TP-xx, CRM-xx).

**Drive (bản gốc):** `01 Video/Giới thiệu sản phẩm/`
- `00 Tổng quan/`
- `01 Đại lý/`
- `02 Nội bộ AA/`
- `03 Khách du lịch/`
- `99 Lưu trữ (đã thay)/`
Trong mỗi nhóm có `<PV-id>_<slug>/v<n>/`, chứa zip và README theo package.py.

**Catalogue:** một trang artifact riêng tư có db (trạng thái: planned / ready / filmed / stale / superseded; cổng; app SHA; link Drive). Link đưa vào draft Jira cuối phiên. Không ghi link Drive hay danh mục vào repo gốc, vì repo gốc đang public.

**Sau này:**
- Nhúng vào trang Help trong app agency khi AA-970 mở lại (sau S280), đúng video theo feature key.
- Website hoặc YouTube unlisted chỉ sau ngày go-live (b18) và khi business owner duyệt, trên kênh của công ty.
- Video ST không bao giờ ra ngoài. _Vì sao:_ Tên có mã khán giả và ngôn ngữ thì lọc và tự động hoá được. Catalogue có trạng thái 'stale' là nơi duy nhất trả lời câu hỏi 'video nào gửi được hôm nay'.
- **9. Lời đọc và repo public.** Kịch bản và caption của UAT nằm trong repo gốc public (ví dụ tools/uat/intro/narration.json). Cho video sản phẩm cần thêm luật:
- Lời đọc nằm trong repo chỉ được mô tả UI.
- Không giá: 299/799/1.499 USD sẽ xem lại sau 3 đại lý (b2).
- Không tên đại lý pilot, không ngày roadmap.
- Không câu cam kết pháp lý (b1, b9) khi chưa duyệt.

Phần lời đọc mang tính thương mại của OV-02 và OV-03 giữ ở thư mục riêng tư (Drive, hoặc work/ đã gitignore), không commit.

Trade-off: mất một phần khả năng tái tạo từ repo, đổi lại không lộ chiến lược trước khi ra thị trường. _Vì sao:_ Repo gốc public tới khi có quyết định khác. Lời đọc thương mại là tài liệu chưa công bố của công ty.
- **10. Các bước tiếp theo theo thứ tự.** 1. **S268:**
   - Chuyển video TripPlanner 30/10 sang `99 Lưu trữ`, kèm ghi chú 'trước B2B, không gửi ra ngoài'.
   - Dựng catalogue riêng tư với 27 PV-id, cổng và trạng thái 'planned'.
   - Đặc tả và tạo tenant 'Demo Agency' tổng hợp.
   - Làm bộ thẻ hình kit, có dòng 'Giọng đọc tổng hợp (TTS)' ở thẻ kết.
   - Viết nháp kịch bản OV-02 để business owner xem.
2. **S269–S270:**
   - Quay v0 nội bộ của ST-02 và ST-05 (sau khi AA-1042 đóng) để thử manifest, quay lại theo chương và khung 1600×900.
   - Viết kịch bản fast mode cho AG-01…AG-07.
   - Xin quyết định có một lượt chạy LLM trả phí nhỏ cho AG-04 và AG-05 hay không.
3. **S271:** chạy toàn bộ PV-AG ở fast mode trên Dev để biết cái gì còn đỏ trước cổng.
4. **S272, khi cổng pilot 1 xanh:** quay AG-01, AG-02, AG-03 (chưa có chương giá), ST-01, ST-03.
5. **S273:**
   - Quay AG-05, AG-06 (nếu đã có site WordPress test), AG-07, TR-02, ST-10, OV-01 v1.
   - Đóng gói 'gói onboarding pilot', thêm vào draft Jira cuối phiên.
   - Chạy AA-855 vòng 1 cùng lúc, dùng chung các đoạn quay.
6. **S274–S275:** ST-04; AG-08, AG-09, ST-07, ST-08; quay lại chương giá của AG-03.
7. **S277:** AG-10 v0, TR-03 v0, ST-09, OV-03 bản pilot 2.
8. **S280 trở đi:** TR-01, AG-10 v1, TR-03 v1, OV-01 v2. Sau go-live và khi business owner duyệt: website / YouTube unlisted. _Vì sao:_ Thứ tự đi theo critical path của ADR 0019 d15, và đặt video nặng nhất (gói pilot) đúng lúc nó tạo ra giá trị.

### Cấu trúc

Cấu trúc thư mục trên Drive và tên file:

```
01 Video/
├── Giới thiệu sản phẩm/
│   ├── 00 Tổng quan/          (PV-OV-*)
│   ├── 01 Đại lý/             (PV-AG-*)
│   ├── 02 Nội bộ AA/          (PV-ST-*, chỉ dùng nội bộ)
│   ├── 03 Khách du lịch/      (PV-TR-*, thương hiệu Demo Agency)
│   └── 99 Lưu trữ (đã thay)/  (bản cũ, gồm video TripPlanner 30/10)
│       mỗi nhóm: <PV-id>_<slug>/v<n>/  → zip (MP4 EN, MP4 VI, MP3, SRT/VTT, README VI+EN)
├── UAT (kiểm thử nghiệm thu)/<round>/<app>/  (AA-855, dùng chung đoạn quay)
```

Tên file: `PV-<OV|AG|ST|TR>-<NN>_<slug>_<EN|VI>_<yyyymmdd>_v<n>.mp4`.

Mỗi PV-id có một manifest: các chương, kịch bản (tools/uat/scenarios/product/), route, component kit, app SHA lúc quay.

Catalogue riêng tư (artifact có db) gồm:
- trạng thái: planned / ready / filmed / stale / superseded
- cổng (R1…R7, P1, P2)
- link Drive
- khán giả và ngôn ngữ

### Lịch

Lịch quay theo phiên và milestone (theo plan.json / backlog §3, ADR 0019 d15):
- S268: không quay. Lưu trữ video TP 30/10; dựng catalogue và tenant 'Demo Agency'; làm thẻ hình kit; viết nháp kịch bản OV-02 để business owner xem.
- S269–S270: v0 nội bộ ST-02 (provision tenant, R1 đã xong) và ST-05 (AI & spend, sau AA-1042). Viết kịch bản fast mode AG-01…07. Chưa quay bản chính thức vì AA-1008 ShellFrame và i18n R3 đang đổi shell.
- S271: chạy toàn bộ PV-AG ở fast mode (kiểm trước cổng). R2 đóng.
- S272, cổng pilot 1 (R1, R3 gộp, R2, AA-969, d16, AA-1040, AA-820): quay AG-01, AG-02, AG-03 (chưa có chương giá), ST-01, ST-03; OV-03 bản pilot 1.
- S273: quay AG-05, AG-06 (cần site WordPress test), AG-07 CRM, TR-02, ST-10, OV-01 v1. Đóng gói 'gói onboarding pilot', thêm vào draft Jira. AA-855 vòng 1 dùng chung đoạn quay.
- S274: ST-04 (Tenant QA, d20/d21, sau khi AA-1039 đóng).
- S275, R4 xong: AG-08 Book with AA, AG-09 gói và hoá đơn, ST-07 Booking B2B, ST-08 Finance; quay lại chương giá / RRP của AG-03.
- S276: dự phòng cho việc quay lại.
- S277, cổng pilot 2 (R5): AG-10 v0, TR-03 v0, ST-09; OV-03 bản pilot 2.
- S278–S279: không quay TripPlanner (R7 đang đổi UX).
- S280, R7 đóng: TR-01, AG-10 v1, TR-03 v1; OV-03 bản R7.
- ≥S281: OV-01 v2 cho toàn hệ sinh thái. Nhúng vào Help của app agency khi AA-970 mở lại. Website / YouTube unlisted sau go-live (b18) và khi business owner duyệt.

Nhịp: tối đa 2 video hoàn chỉnh (~15 đoạn) mỗi phiên, chạy như lane phụ, không lấy năng lực của critical path. Chi phí $0, trừ lượt LLM tuỳ chọn cho AG-04/05.

### Rủi ro

- Quay trước AA-1008 ShellFrame / i18n R3 (S270–S272) thì gần như mọi video admin và agency phải quay lại. Hai phiên S269–S270 chỉ làm v0 nội bộ.
- Lỡ quay tenant pilot (PII thật, d16) hoặc để lộ OTP, token, URL ICS. Luôn dùng tenant 'Demo Agency' tổng hợp, mask, và kiểm từng khung hình trước khi đóng gói.
- Lời đọc thương mại (giá, cam kết b1/b9, tên pilot, ngày roadmap) bị commit vào repo gốc public qua file narration hoặc caption.
- Video OV hoặc AG trình bày Book with AA hay TripPlanner cho đại lý như đã chạy trước R4 / R5. Chỉ được nằm trên slide 'Coming next', không ghi ngày.
- AG-04, AG-05, AG-06 bị chặn bởi bên ngoài: đường LLM (acc3 Error 002; đường tạm có trần 10 USD/tháng) và site WordPress test mới mà tech lead chưa tạo.
- Gửi đại lý một video đã 'stale'. Cần chạy fast mode cho các PV sau mỗi deploy và chặn gửi khi trạng thái là stale.
- Video gắn thương hiệu AA ở phía khách du lịch thì trái b8 và invariant 1 (lặp lại lỗi của video 30/10).
- Giọng tổng hợp mà không ghi chú có thể gây hiểu nhầm. Chuẩn công bố AI (EU AI Act Art. 50) là bối cảnh nên ghi chú ngay từ đầu.
- RAM 8–10 GB trên WSL: quay hoặc TTS song song với build hay pytest của lane khác sẽ làm hỏng phiên quay.
- rclone dùng client_id chung sắp ngừng trong 2026. Cần tạo OAuth client riêng trước đợt upload lớn ở S273.

### Cần tech lead / business owner quyết

1. Video TripPlanner giới thiệu 30/10 (B2C, thương hiệu AA, nói 'tư vấn viên AA') xử lý thế nào? — **Đề xuất:** Chuyển sang 01 Video/Giới thiệu sản phẩm/99 Lưu trữ, ghi 'trước B2B, không gửi ra ngoài'. Bản thay thế là TR-01 + AG-10 sau R7 (S280). (Phương án khác: Lưu trữ, thay sau R7 (đề xuất); Xoá hẳn; Giữ làm tài liệu nội bộ, cắt câu 'tư vấn viên AA')
2. (Business owner) Gói onboarding pilot (AG-01…AG-07, TR-02, OV-01) có được gửi cho đại lý pilot / khách tiềm năng không, và gửi bằng hình thức nào? — **Đề xuất:** Có, sau khi business owner xem bản S273. Gửi link Drive chỉ xem (view-only), không gửi file tải về. Ghi rõ 'môi trường thử, dữ liệu tổng hợp'. (Phương án khác: Gửi link Drive chỉ xem (đề xuất); Chỉ trình chiếu trong buổi họp; Chưa gửi tới go-live)
3. (Business owner) Có nói giá (299/799/1.499 USD, add-on, AI 15/40/80 USD) trong video không? — **Đề xuất:** Không nói giá trong video; chỉ nói 'theo gói'. Giá đi trong báo giá hoặc hợp đồng, vì b2 sẽ xem lại sau 3 đại lý. (Phương án khác: Không nói giá (đề xuất); Có giá trong bản gửi đại lý; Có giá chỉ trong bản OV nội bộ)
5. Ghi chú rằng giọng đọc là giọng tổng hợp (TTS)? — **Đề xuất:** Có. Thêm dòng 'Narration: synthetic voice (TTS)' ở thẻ kết và mô tả mỗi video, đồng bộ với tinh thần AI notice của AA-1040. (Phương án khác: Có ghi chú (đề xuất); Không ghi)
6. Ngôn ngữ của từng nhóm video? — **Đề xuất:** AG và OV có hai bản EN và VI. ST giọng VI, UI tiếng Anh. TR chỉ EN (khách quốc tế của đại lý). Business owner xác nhận ngôn ngữ của đại lý pilot. (Phương án khác: Như đề xuất; Mọi video đều EN + VI; Chỉ EN, phụ đề VI)
7. AG-04 và AG-05 (lên kế hoạch / viết bài bằng AI) cần nội dung do LLM tạo ra. Lấy nội dung đó từ đâu? — **Đề xuất:** Một lượt trả phí nhỏ, khoảng 3 piece, trên đường tạm OpenAI/acc2 (vài cent). Cần có đồng ý riêng và chi phí ghi theo stage trong shared.llm_call_log. Nếu không đồng ý thì chỉ quay output có sẵn. (Phương án khác: Lượt trả phí ~3 piece (đề xuất); Chỉ quay output có sẵn; Hoãn tới khi đường LLM chính trở lại)
9. Catalogue video đặt ở đâu? — **Đề xuất:** Một artifact riêng tư có db (trạng thái, cổng, SHA, link Drive). Không ghi vào repo gốc public. (Phương án khác: Artifact riêng tư (đề xuất); Google Sheet trong Drive; docs/audits trong repo gốc (không khuyến nghị: lộ link Drive))

## UAT, video hướng dẫn, bằng chứng hồi quy (OPS)

Chủ đề 3 (UAT, video kịch bản test, video hướng dẫn, bằng chứng hồi quy): đề xuất chia 5 loại video, tất cả dùng chung một engine là tools/uat (run.sh, dryrun.cjs, build.py, longform.py, package.py, check_sync.py). Gốc của mọi video là một danh mục kịch bản duy nhất: một kịch bản = một user story = một bài test có assert, rồi từ đó sinh ra video UAT, video hướng dẫn, clip phát hành và clip lỗi. Mình không quay lại từ đầu cho từng mục đích.

Hiện trạng đã đọc:
- Kế hoạch S260 có khoảng 60 ID (TP, CIS, PRT, CRM, BK, X, *-PUB).
- Bộ dry run (AA-1009) chạy xanh. Bản CRM review S262 dài 19:53 có 21 chương, kèm bản highlight 8:30, và đã bắt được lỗi thật (CSV export trả 401 khi token hết hạn).
- Smoke trong CI: CIS ui-smoke (smoke-public, @staff, cognito, admin-evidence), Partner smoke-portal và e2e-dev, Booking layout + smoke-public, TripPlanner visual.yml (PNG 1440/390 sáng/tối). Mọi chỗ đều để video off. Partner để trace off vì sợ lộ trang nhập mã.
- AA-855 đang ở Backlog, milestone M-P1, slot S272. Vòng 1 (Content + CRM) khi AA-1036, AA-1008, AA-1035 và đường LLM xanh (~S272–S274). Vòng 2 TripPlanner sau R5 (~S277+). Plan ghi đây là việc trong thời gian pilot, không phải cổng pilot.

Ba điểm lệch phải sửa trước khi quay chính thức:
- R0 (chỉ B2B) làm TP-05, X-01, BK-02 thành lịch sử.
- R3 gộp portal vào web, nên các kịch bản PRT đổi route/host.
- R1, R2, R6 và AA-1040 thêm tính năng mà danh mục chưa có kịch bản (Tenant 360/Plans, vai trò staff và scope, AI notice, gate d21).

Rủi ro lớn nhất cần chặn sớm:
- Tenant pilot thật sẽ nằm trên Dev (d16). Recorder hiện chưa có gì ngăn nó lên hình.
- Trace Playwright (có header, cookie, body) không bao giờ được upload thành artifact trên repo public.
- Link Drive không nên nằm trong index ở repo gốc public.


Mọi đề xuất dưới đây chỉ đọc, chưa sửa repo nào, chi phí $0 nếu giữ TTS local + Drive. Chỉ phương án S3 private là trả phí, cần một lần "có" riêng.

### Đề xuất

- **(a) UAT nghiệm thu chính thức: theo vòng, theo app, mỗi kịch bản có checklist PASS/FAIL và business owner ký trên trang.** Người xem: business owner, tech lead. Không đưa cho đại lý.

Kích hoạt theo tiêu chí vào vòng của AA-855:
- Vòng R1 (Content + CRM + phần CIS mà R1/R2/R6 đụng tới): khi AA-1036 merge xong (kể cả studio tiếng Việt), AA-1008 có visual job, AA-1035 lát 2 có danh tính E2E theo vai trò, và có đường LLM.
- Vòng R1b Booking: sau R4 (~S274–S275), vì R4 đổi Booking sang chỉ B2B.
- Vòng R2 TripPlanner: sau R5 (~S277+), đúng tiêu chí của M-P2.

Cách làm:
- Mỗi kịch bản: run.sh, ra MP4 có 2 track tiếng (EN Kokoro, VI VieNeu) + phụ đề mềm + result.json. Mỗi app: longform.py ra bản dài có chương và bản highlight ≤8 phút. Đây là mẫu của CRM-REVIEW S262, đã chứng minh chạy được.
- Checklist PASS/FAIL lấy thẳng từ result.json. Mỗi kịch bản có thêm cột 'Kết quả mong đợi', viết bằng lời nghiệp vụ, lấy từ header Given/When/Then.
- Business owner ký trên một trang artifact (memory owner-report-one-artifact, artifact-decisions-interactive): mỗi app một tab. Mỗi kịch bản có video highlight, mô tả, verdict tự động và 3 nút Accept / Accept with note / Reject, lưu vào db của artifact.
- Link trang vào nháp Jira cuối phiên (thu-links-via-jira). Tech lead duyệt nháp rồi mới đăng.
- Agent đọc các dòng db để ghi kết quả vào index docs/audits (ghi theo vai trò: 'business owner accepted <ngày>') và comment Linear AA-855.
- Kịch bản Reject: mở hoặc gắn issue (hỏi trước khi tạo, AA-855 vẫn là issue chung). Sửa xong quay lại v<n+1>, chỉ quay kịch bản đó.

Điều kiện quay:
- Chỉ trên Dev, chỉ dữ liệu tổng hợp, không gọi LLM trả phí.
- Tính năng AI phải ghi rõ 'test mode' nếu đúng là test mode (ví dụ CRM AI gateway CRM-33a). _Vì sao:_ Business owner không xem nổi 60 video rời. Highlight + checklist + nút bấm cho bà một quyết định rõ ràng và để lại dấu vết kiểm được. Dùng lại đúng pipeline đã chạy xanh ở S262 nên chi phí $0 và rủi ro thấp.
- **(b) Video hướng dẫn EN+VI kiêm đào tạo, sinh từ chính kịch bản UAT (mode guide).** Người xem theo lộ trình vai trò:
- Đại lý pilot: owner, agent, assistant.
- Staff AA theo 6 vai trò R2: content reviewer, account manager, finance...
- Booking ops.

Khác với UAT:
- Lời đọc dạng chỉ dẫn ('Bấm New trip…'), nhịp chậm hơn, có zoom hoặc highlight vùng bấm.
- Không có tiền tố [FAIL], không có số liệu Dev.
- Bản VI quay với UI tiếng Việt chứ không chỉ thay track tiếng, vì đại lý Việt sẽ dùng UI VI. Việc này cần xong i18n studio của R3.
- Mỗi guide vẫn chạy assert. Guide không chạy được nữa có nghĩa là UI đã đổi và phải quay lại.

Gói tối thiểu trước pilot mốc 1 (~S272), khoảng 8–10 guide, mỗi guide 1–3 phút:
- Đăng nhập + Content home
- Marketplace chọn tour
- Onboarding / brand
- Import khách từ bảng tính (CRM-REV R02)
- Pipeline
- Proposal builder
- Gửi proposal + khách duyệt trên điện thoại
- Hoá đơn đặt cọc
- Vai assistant thấy gì
- Đổi tiếng Việt / dark mode

Nguyên tắc:
- Ghép với trang hướng dẫn bằng chữ trong docs/ theo vai trò. Có `.vi.md`. Gọi bằng vai trò, không gọi tên người. Không hiện AA-xxx trên hình.
- Chưa làm guide cho vùng còn đổi mạnh: TripPlanner trước R5/R7, Booking trước R4. _Vì sao:_ Đại lý pilot sẽ cần tài liệu đào tạo ngay khi được mời. Sinh guide từ kịch bản có assert thì guide tự báo khi lỗi thời, nên không phải rà tay sau mỗi lần UI đổi (R3, R7).
- **(c) Bằng chứng hồi quy tự động: 3 tầng, chỉ quay video khi có lỗi.** Tầng 1, mỗi lần deploy (đã có):
- Các bộ đang chạy: CIS ui-smoke (smoke-public trên preview của PR; @staff sau production deploy), Partner ui-smoke-portal, Booking layout + smoke-public, TripPlanner visual.yml.
- Thêm `video: 'retain-on-failure'` cho các project chạy test trang. Project setup đăng nhập vẫn để off như hiện tại. Mức lộ của video ngang ảnh chụp đang upload, vì artifact CI hiện đã có ảnh trang đã đăng nhập (dữ liệu tổng hợp).
- TUYỆT ĐỐI không bật `trace` cho run đã đăng nhập trên repo public. Trace chứa header, cookie và body phản hồi, mà artifact của repo public thì người ngoài cũng tải được.

Tầng 2, mỗi đầu phiên và cuối phiên:
- Đưa `node tools/uat/dryrun.cjs` (fast, chỉ đọc, chặn ghi, chặn LLM) thành bước chuẩn của aa-session. Kết quả cuối phiên ghi vào state-snapshot.
- Thêm cờ mới `--record-on-fail`: kịch bản FAIL tự chạy lại ở chế độ quay, ra clip loại (e).
- Lý do không dựng lịch nightly lúc này: Dev không có người dùng (dev-no-waiting), phiên diễn ra gần như hằng ngày, và dựng nightly trên ECS/CI cần secret E2E ở repo public hoặc tốn chi phí. Khi có aa-prod (M5) mới dời sang lịch CI.

Tầng 3, phát hiện guide/UAT cần quay lại:
- Lúc quay, lưu một keyframe PNG cho mỗi step (build.py đã trích frame).
- Mỗi dry run chụp lại đúng step đó rồi so bằng odiff hoặc pixelmatch (MIT, local, $0). Vùng số liệu và ngày tháng được che.
- Lệch quá ngưỡng (ví dụ >3 % pixel hoặc heading/nhãn đổi): đánh dấu `stale` trong catalogue.json, đưa vào hàng chờ quay lại.
- Khi AA-1008 có visual job 1440/390 sáng/tối, đối chiếu `screens` của từng kịch bản với các route bị đổi trong job đó để có thêm tín hiệu thứ hai.

Lưu giữ:
- Mỗi kịch bản giữ 3 lần PASS gần nhất (local).
- Mọi FAIL giữ đến khi issue Done + 30 ngày.
- Bản chính thức giữ vĩnh viễn trên Drive. _Vì sao:_ Hiện mọi suite đều để video off, và dry run mới chỉ chạy khi có người nhớ gọi. Làm như trên thì regression thành thói quen ở mỗi phiên với chi phí $0, và tín hiệu 'cần quay lại' tự động thay cho việc rà tay sau R3/R7.
- **(d) Clip phát hành theo milestone: ghép từ bản đã quay, không quay mới.** Kích hoạt: milestone Done. Các mốc: REL-R3 (một app agency), REL-P1 (pilot mốc 1), REL-R4 (Booking chỉ B2B), REL-P2 (TripPlanner đa tenant), REL-R7.

Cách làm:
- `longform.py --highlight` lấy các chunk đã PASS của vòng gần nhất.
- Mở đầu bằng một thẻ 'Có gì mới'. Nội dung lấy từ changelog release-please của các repo (repo nào cũng có release-please.yml), dịch sang lời nghiệp vụ.
- Độ dài 1–3 phút.

Hai bản:
- Nội bộ: có chương 'Chưa làm' như CRM-REVIEW, có ghi 'test mode'.
- Bên ngoài (đại lý): chỉ tính năng đã quay chạy thật, không số liệu Dev, không ID nội bộ.

Theo memory jira-claims-need-live-evidence: chỉ nói 'chạy được' cho đúng kênh đã quay end-to-end. Ví dụ WordPress khác Facebook, và PRT-07b (Meta thật) phải do tech lead quay.

Đây cũng là nguyên liệu rẻ nhất cho series giới thiệu sản phẩm (chủ đề 2). _Vì sao:_ Không tốn thêm phiên quay. Business owner thấy tiến độ theo milestone đúng nhịp plan.json. Nhờ luật bằng chứng, clip không nói quá thực tế.
- **(e) Clip tái hiện lỗi: nội bộ, ngắn, gắn Linear.** Nguồn:
- Step FAIL trong dry run hoặc vòng UAT. run.sh đã giữ lại video FAIL.
- Bug được báo: viết hoặc dùng lại kịch bản, rồi chạy `--repro`.

Chế độ repro: không TTS, chỉ caption, bật trace + console + network log. Tất cả chỉ ở local `tools/uat/work/bugs/`, không upload lên CI public.

Đặt tên: `BUG-<AA-xxxx>_<ID>_<stamp>`.

Đính kèm vào Linear: 1 ảnh frame tại step lỗi + mốc thời gian + đường dẫn Drive `UAT/bugs/` (thư mục hạn chế). Linear gói Free vẫn đính kèm được.

Sửa xong chạy lại đúng kịch bản. Clip PASS v2 là bằng chứng Done, đi cùng aa-ship verify live.

Không đưa vào Jira hay cho business owner, trừ khi tech lead muốn.

Tiền lệ: R15 CSV export trả 401 khi token 30 phút hết hạn (S262). Lỗi này được bắt nhờ quay video và đã có fix bffDownload. _Vì sao:_ Agent sửa lỗi (Claude/Kiro) cần thấy đúng trạng thái lúc lỗi. Trace cho nhiều thông tin nhất, nhưng phải giữ ngoài kênh public.
- **Cập nhật danh mục theo plan hiện tại trước khi quay thêm.** Danh mục S260 lập trước R0 và R3. Cần làm:
- Retire TP-05 (hỏi advisor có đăng ký), X-01, BK-02 (inquiry B2C → trip case). Thay bằng X-05: 'Send to advisor' hiện thông báo demo.
- Chuyển PRT-01…10 sang route và host của app agency sau AA-1036.
- Thêm CIS-15…20, PRT-11…14, X-04, BK-11…12 (đã liệt kê ở phần structure).
- Mở khoá các kịch bản ghi đang bị chặn (CIS-02 approve, CIS-06 đổi limit, CIS-13 facts) bằng danh tính E2E theo vai trò, chỉ trên Dev, của R2. Đây là tiêu chí M-R2 'nhận AA-1010'.
- Khi có vai trò chỉ đọc cho CRM, đưa các kịch bản CRM vào bộ dry run mặc định.
- Mỗi kịch bản ghi `covers` tới tiêu chí milestone. Khi đó trang tracker cho thấy tiêu chí nào đã có video bằng chứng.

Việc chi tiết để trong checklist hoặc plan local. Không tách issue Linear mới (quota Free 250); AA-855 vẫn là một issue. _Vì sao:_ Quay theo danh mục cũ sẽ ra video sai mô hình B2B-only, và phải quay lại ngay khi R3 gộp xong.
- **Chặn tenant pilot (dữ liệu thật) khỏi mọi bản quay.** M-R1 và M-P1 cho phép đúng một tenant pilot thật trên Dev (d16). Vì vậy cần thêm vào lib/dryrun-page.cjs và record.cjs một bước kiểm:
- Trước mỗi kịch bản, đọc tenant/agency đang hiển thị qua API. Nếu kind=real hoặc có dấu pilot thì dừng (exit mã riêng).
- Trang danh sách: lọc hoặc che hàng của tenant pilot, hoặc chỉ quay khi bộ lọc đang ở tenant E2E.
- Job cleanup của kịch bản CRM (cleanup.cjs) phải bỏ qua tenant pilot. Việc này khớp biện pháp d16 'job dọn dẹp/E2E bỏ qua tenant pilot', và cần có test.

Làm trước khi mời tenant pilot, tức là trước ~S272. _Vì sao:_ Hiện recorder dựa vào việc trên Dev chỉ có dữ liệu tổng hợp. Khi có tenant thật, chỉ một bản quay danh sách Tenants hay Clients là đã thành sự cố PII.
- **Giữ repo public sạch: index không có link Drive, CI không có trace.** - Skill aa-uat-video §8 đang cho phép ghi link Drive vào index ở repo gốc. Đề xuất bỏ: link Drive chỉ nằm trong trang artifact cho business owner và Jira. Index public chỉ ghi ID, verdict, độ dài, SHA, mốc lỗi.
- Kiểm lại thư mục Drive `UAT/` đang chia sẻ 'chỉ người được mời', không phải 'ai có link'.
- CI: video retain-on-failure được, trace của run đã đăng nhập thì không.
- Báo cáo đã che ARN và account ID (đã có trong skill), giữ nguyên.

### Cấu trúc

TỔ CHỨC TỔNG THỂ: 3 họ video, tách bạch
2. Giới thiệu sản phẩm (chủ đề 2): Drive `01 Video/Giới thiệu sản phẩm/`.
3. Bằng chứng chất lượng (chủ đề 3, chính là phần này): chia 5 loại (a) đến (e), cùng một engine tools/uat.
Nguồn chảy một chiều: kịch bản → video UAT → highlight hoặc clip phát hành → nguyên liệu cho series sản phẩm. Chiều ngược lại không có, tức là video marketing không bao giờ được dùng làm bằng chứng.

MỘT DANH MỤC DUY NHẤT (đề xuất mới)
File `tools/uat/catalogue.json` ở repo gốc, mỗi kịch bản một dòng:
- id, app, module, story, roles
- kinds: uat | guide | release | regression
- covers: id tiêu chí milestone, ví dụ `M-R3#4`
- screens: route mà kịch bản đi qua
- status: live | after-lane | blocked | retired
- issues: AA-xxx, chỉ dùng nội bộ (package.py đã bỏ id nội bộ khỏi zip)
Bảng §4 của kế hoạch S260 sinh ra từ file này, không sửa tay hai nơi.

CHUẨN ĐẶT ID (giữ nguyên mọi ID đã quay; không đánh số lại)
- Kịch bản: `<APP>-<NN>`. APP gồm:
  - TP: TripPlanner
  - CIS: CIS admin, gồm cả control plane R1 và vai trò R2
  - PRT: module Content trong app agency sau R3, vẫn giữ PRT dù đã gộp app
  - CRM: module CRM
  - BK: Booking admin
  - X: xuyên app
- Trang công khai: `<APP>-PUB-<NN>` (TP-PUB-01, PORTAL-PUB-01 giữ nguyên).
- Biến thể:
  - `.m` = điện thoại 390, ví dụ `CRM-06.m`
  - `@<role>` = cùng story nhưng vai khác, ví dụ `CRM-02@assistant`, `CIS-06@account-manager`
  - chữ cái = tách story, ví dụ PRT-07b (đã có)
- Sửa kịch bản không đổi ID mà tăng `rev` trong file. Video quay lại thì tăng `v<n>`.
- Kịch bản bị R0 làm lỗi thời: status=retired, giữ ID, không tái dùng số. Story mới thì cấp số mới.
- Vòng UAT: `R<k>-<yyyy-mm>`, ví dụ `R1-2026-11`. Vòng nhỏ theo app: `R1b`.
- Đề xuất cấp số cho story mới, theo nhóm:
  - R1 control plane: CIS-15 (Tenant directory + Tenant 360), CIS-16 (Subscription + Plans seed 299/799/1.499), CIS-17 (tenant_provision)
  - R2 vai trò: CIS-18@account-manager (chỉ thấy tenant được giao, 403 tenant khác), CIS-19 (view-as chỉ đọc, có dòng audit)
  - R6 IA admin: CIS-20 (điều hướng mới + redirect URL cũ)
  - Gate d21 / fan-out d20: PRT-11 (gate d21 giữ piece ở Tenant QA › Compliance), PRT-12 (fan-out tour ngừng bán)
  - R3: PRT-13 (một đăng nhập → Content home → chuyển app), PRT-14 (studio tiếng Việt)
  - Xuyên app: X-04 (AI notice + dấu ai_generated trên mọi bề mặt, AA-1040), X-05 (TripPlanner "Send to advisor" trả thông báo demo, thay cho X-01 cũ)
  - R4 Booking: BK-11 (Book with AA: quote/hold từ app agency vào Booking), BK-12 (hoá đơn SaaS + settlement hiện ở Tenant 360)

TÊN FILE
- UAT: `<ID>_<yyyymmdd>_v<n>.mp4` (đã có)
- Long-form: `<APP>-REVIEW_<yyyymmdd>_v<n>` + `_highlight` (đã có)
- Hướng dẫn: `G-<ID>_<en|vi>_<yyyymmdd>_v<n>`, ví dụ `G-CRM-06_vi_20261110_v1`
- Phát hành: `REL-<milestone>_<yyyymmdd>_v<n>`, ví dụ `REL-R3`, `REL-P1`
- Lỗi: `BUG-<AA-xxxx>_<ID>_<yyyymmdd>_<hhmm>`; chưa có issue thì `BUG-<ID>_<stamp>`

THƯ MỤC
Drive AdventureAsia → `01 Video/`:
- `Giới thiệu sản phẩm/`: chủ đề 2, đã có
- `UAT (kiểm thử nghiệm thu)/`: đã có
  - `R1-2026-11/<app>/`: bản chính thức, giữ vĩnh viễn
  - `dry-run/`: đã có, ví dụ CRM-review-20261101
  - `bugs/`: mới, KHÔNG chia sẻ ra ngoài
- `Hướng dẫn sử dụng/<vai trò>/<app>/<en|vi>/`: mới
- `Phát hành/<milestone>/`: mới

Repo gốc (public):
- Lưu: script kịch bản, `catalogue.json`, index `docs/audits/<date>-S<nnn>-uat/<app>.md` (ID, story, verdict, độ dài, step FAIL + mốc thời gian, SHA app).
- Không lưu: link Drive, account ID, video.
- Hướng dẫn bằng chữ: `docs/` theo vai trò, kèm `.vi.md`, front-matter có `video: G-...`.

Local (gitignore): `tools/uat/work/`, `out/`. Clip lỗi và trace chỉ nằm ở đây.

BẢNG 5 LOẠI (ai xem / kích hoạt / độ dài / công cụ / lưu giữ / ký duyệt)
(a) UAT nghiệm thu chính thức
- Ai xem: business owner, tech lead.
- Kích hoạt: đủ tiêu chí vào vòng.
- Độ dài: 60–120 s mỗi kịch bản. Thêm long-form theo app ≤20 phút có chương, và highlight ≤8 phút.
- Công cụ: run.sh, longform.py, package.py.
- Lưu giữ: vĩnh viễn.
- Ký duyệt: business owner bấm trên trang artifact.

(b) Hướng dẫn / đào tạo EN+VI
- Ai xem: nhân viên đại lý pilot (owner, agent, assistant) và staff AA (6 vai trò R2, Booking ops).
- Kích hoạt: UI ổn định sau AA-1008 và trước khi mời đại lý pilot.
- Độ dài: 1–3 phút.
- Công cụ: engine như (a), mode guide.
- Lưu giữ: bản hiện hành + 1 bản trước.
- Ký duyệt: tech lead duyệt nội dung, business owner duyệt việc đưa ra ngoài.

(c) Bằng chứng hồi quy tự động
- Ai xem: tech lead, agent.
- Kích hoạt: mỗi lần deploy (smoke) và mỗi đầu/cuối phiên (dry run).
- Độ dài: không quay video, trừ khi FAIL.
- Lưu giữ: video giữ 3 lần PASS mới nhất mỗi kịch bản, mỗi FAIL giữ đến khi issue Done + 30 ngày. Artifact CI 14 ngày.
- Ký duyệt: không cần.

(d) Clip phát hành theo milestone
- Ai xem: business owner (bản nội bộ), đại lý pilot (bản ngoài, phải được duyệt).
- Kích hoạt: milestone Done.
- Độ dài: 1–3 phút, ghép từ bản quay đã PASS bằng longform --highlight, không quay mới.
- Lưu giữ: vĩnh viễn.

(e) Clip tái hiện lỗi
- Ai xem: tech lead, Claude/Kiro khi sửa.
- Kích hoạt: một step FAIL hoặc bug được báo.
- Độ dài: 10–60 s, chỉ có caption, có trace local.
- Lưu giữ: đến khi issue Done + 30 ngày.
- Liên kết: Linear, kèm 1 ảnh frame. Không đưa vào Jira.

### Lịch

Bám plan.json (đang ở S268):

S268–S269, $0:
- Cập nhật danh mục theo R0/R1/R2/R3/R6/AA-1040, tạo tools/uat/catalogue.json, sửa §4 kế hoạch S260 (root PR).
- Thêm guard tenant pilot vào recorder và cleanup.
- Đưa dry run thành bước đầu/cuối phiên của aa-session.
- Thêm `--record-on-fail`.
- CI: bật video retain-on-failure cho các project test trang (không bật trace khi đã đăng nhập).
- Lúc k6 của AA-969 đang chạy thì không quay (RAM).

S270–S271:
- Khi AA-1008 xong: chụp keyframe gốc cho từng step + cơ chế đánh dấu stale (odiff/pixelmatch).
- Khi AA-1035 lát 2 có danh tính E2E theo vai trò: viết các kịch bản ghi của CIS (CIS-02 approve, CIS-06, CIS-13) và kịch bản từ chối theo vai trò (CIS-18/19).
- Viết và quay gói 8–10 guide EN+VI cho đại lý pilot, cần xong i18n studio của R3.

~S272, pilot mốc 1:
- Cổng mời pilot gồm dry run xanh + guard pilot + gói guide. Bản thân UAT không phải cổng.

S272–S274, AA-855 vòng R1 (Content + CRM + control plane CIS):
- Quay, làm long-form và highlight, trang artifact cho business owner ký, nháp Jira.
- Làm clip REL-R3 / REL-P1.

~S274–S275, vòng R1b Booking sau R4 (BK-11/12 mới, retire BK-02); clip REL-R4.

S277+, vòng R2 TripPlanner sau R5 (tiêu chí của M-P2):
- Viết lại TP-* theo tenant theo path + brand; clip REL-P2.

S277–S280, R7 UX TripPlanner: tín hiệu stale sẽ tự báo các TP guide cần quay lại; khi đó mới làm guide TripPlanner.

M5 prod (từ ≥01/12):
- UAT vẫn chỉ chạy trên Dev với dữ liệu tổng hợp; prod chỉ có smoke chỉ đọc.
- Hồi quy chuyển sang lịch CI, kèm lưu trữ private (cần 'có' riêng về chi phí).

Mỗi phiên quay tối đa ~15 kịch bản, mỗi lúc một Chromium.

### Rủi ro

- Tenant pilot thật trên Dev (d16) có thể lên hình qua danh sách Tenants/Clients hoặc bị job cleanup của kịch bản đụng tới, nếu recorder chưa có guard trước ~S272.
- Repo public: trace Playwright (header, cookie, body) hoặc link Drive 'ai có link' lọt qua artifact CI hay index docs/audits, và không thu hồi được.
- Danh mục lệch plan: R0 làm TP-05/X-01/BK-02 sai mô hình; R3 đổi route PRT; quay trước khi cập nhật thì phải quay lại.
- UI còn đổi lớn (R3 gộp app, AA-1008 ShellFrame, R5/R7 TripPlanner, R4 Booking): làm guide quá sớm sẽ thành khoản bảo trì. Chỉ làm guide cho vùng đã qua visual job.
- Thời gian của business owner: đưa 60 video rời thì sẽ không ai xem. Phải đi theo thứ tự highlight → checklist → video chi tiết.
- Nói quá thực tế: clip phát hành hoặc guide ngầm nói tính năng 'chạy được' trên kênh chưa quay thật (Facebook/Meta, Microsoft 365, AI mới ở test mode).
- Môi trường quay: Vercel chặn IP VPN/datacenter (phải kiểm egress = VN); BotID chặn TripPlanner headless (cần chạy headed trên WSLg); máy WSL 8 GB phải chạy từng thứ một (k6 load test AA-969 đang chạy thì không quay).
- Bảo trì toolchain: client_id dùng chung của rclone sắp bị khai tử năm 2026; các model TTS phải giữ giấy phép cho dùng thương mại.
- Quota Linear Free: không tách mỗi kịch bản thành một issue; AA-855 vẫn là issue duy nhất, chi tiết để ở checklist.

### Cần tech lead / business owner quyết

1. Business owner ký nghiệm thu UAT bằng cách nào? — **Đề xuất:** Bấm Accept / Accept with note / Reject cho từng kịch bản trên trang artifact (lưu db). Tech lead tóm tắt kết quả trong Jira. Agent chép kết quả vào index docs/audits và Linear AA-855. (Phương án khác: Bấm trên trang artifact + tóm tắt Jira (đề xuất); Business owner comment trực tiếp trên Jira; Ký PDF biên bản cuối mỗi vòng)
2. Có chia sẻ video hướng dẫn cho đại lý pilot không, và qua kênh nào? (business owner quyết, vì video mang thương hiệu Adventure Asia ra ngoài) — **Đề xuất:** Có. Trong pilot dùng thư mục Drive chỉ mời đại lý pilot. Sau pilot mới gắn vào trang Help trong app. (Phương án khác: Drive, chỉ mời đại lý pilot (đề xuất); Trang Help trong app (cần chỗ lưu file, có thể tốn vài cent/tháng); Kênh video công ty để chế độ không công khai; Chưa chia sẻ, chỉ dùng nội bộ)
3. Clip phát hành (REL-*) có gửi cho đại lý hoặc người ngoài không? (business owner) — **Đề xuất:** Bản nội bộ cho business owner ở mỗi milestone. Bản ngoài chỉ từ REL-P1 trở đi, và chỉ khi business owner duyệt từng clip. (Phương án khác: Chỉ nội bộ; Nội bộ + bản ngoài khi được duyệt (đề xuất))
4. Vòng UAT R1 có thành cổng mở pilot mốc 1 không? (tech lead + business owner) — **Đề xuất:** Không, giữ như plan.json ('việc trong thời gian pilot'). Cổng pilot chỉ gồm: dry run xanh hoàn toàn, guard tenant pilot trong recorder đã chạy, và gói guide đào tạo đã sẵn. (Phương án khác: Không phải cổng, chỉ cần dry run + guide (đề xuất); Là cổng: phải có R1 ký xong mới mời pilot)
5. Đường LLM tạm (OpenAI API / model acc2 qua gateway) có được tính là 'đường LLM đã trở lại' để vào vòng R1 không? (tech lead) — **Đề xuất:** Có. Video ghi rõ model hoặc đường đang chạy. Lượt trả phí trong lúc quay theo luật hiện có (thử ~3 trước, chi phí ghi vào llm_call_log). (Phương án khác: Có, kèm nhãn (đề xuất); Chờ acc3 trở lại)
6. Lưu bản quay hồi quy và clip lỗi ở đâu? (tech lead; phương án S3 là trả phí mới nên cần 'có' riêng) — **Đề xuất:** Hiện tại: local + Drive `UAT/bugs/` hạn chế, $0. Chỉ khi chuyển hồi quy sang lịch CI (sau khi có aa-prod) mới dùng prefix private trong bucket bronze acc2, lifecycle 30 ngày (~vài cent/tháng). (Phương án khác: Local + Drive (đề xuất); Prefix private trong S3 bronze acc2 + lifecycle (~0,0x USD/tháng))
7. Guide tiếng Việt quay với UI tiếng Việt (quay 2 lần) hay UI tiếng Anh + track tiếng Việt như UAT? (tech lead) — **Đề xuất:** Guide: quay UI tiếng Việt riêng, sau khi i18n studio R3 xong. UAT giữ một lần quay UI tiếng Anh với 2 track tiếng. (Phương án khác: UI VI riêng cho guide (đề xuất); UI EN + track VI cho mọi thứ)
