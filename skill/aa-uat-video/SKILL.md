---
name: aa-uat-video
description: Quay video UAT và video giới thiệu sản phẩm AA_Ecosys (Playwright + phụ đề + giọng đọc TTS miễn phí chạy local) — kịch bản có assert từng bước, kiểm khung hình và khớp tiếng, đóng gói zip mỗi video, upload Google Drive bằng rclone, index + báo cáo. Dùng khi Nghiệp nói UAT, quay video, video giới thiệu, giọng đọc / lồng tiếng, nhân bản giọng, hoặc AA-855. Screenshot và kiểm một trang sau khi sửa UI thuộc aa-ui-verify.
---

# aa-uat-video

Mục tiêu: **một kịch bản = một user story = một video = một regression test.** Video là bằng chứng cho người đọc
nghiệp vụ; kịch bản đồng thời là bài test chạy lại được.

Công cụ: `tools/uat/` ở repo gốc (mỗi file có header ghi cách gọi). Cài một lần: `bash tools/uat/setup.sh`.
Kế hoạch đầy đủ (danh mục kịch bản theo app, bảng giọng đã thử, nơi lưu, audit thiết kế tổng thể):
`docs/audits/2026-10-30-S260-uat-video-plan/README.md` (§2.1, §3, §4).

## 1. Khi nào quay

- Quyết định S260: từ S261 kịch bản chạy như **dry run nội bộ** và regression; video giữ nội bộ.
- **Vòng chính thức** (Drive `UAT (kiểm thử nghiệm thu)/<round>/` + trang cho chủ doanh nghiệp) chỉ quay khi đủ tiêu
  chí vào vòng trong kế hoạch §6 (UI ổn định sau AA-994, có lại đường LLM, quyền ghi UAT Dev cho E2E CIS admin đã merge).
- Vòng sau chỉ **quay lại tính năng mới hoặc đã đổi**; bản cũ giữ nguyên, tăng `v<n>`.
- Check theo từng issue vẫn là `aa-ship` (verify live) + `aa-ui-verify` (ảnh); không biến mỗi issue thành một UAT.

## 2. Trước khi quay

1. **Egress = VN.** `curl -s ipinfo.io/country` phải ra `VN`; khác thì DỪNG và nhờ Nghiệp tắt VPN (Vercel chặn IP
   VPN/datacenter). `run.sh` tự kiểm và thoát mã 3. Triệu chứng + nguyên nhân: `aa-lessons` mục Vận hành (dòng
   Vercel 403 Code 21).
2. **RAM:** một Chromium và một model TTS trong RAM tại một thời điểm (`tts.py` giải phóng Kokoro rồi mới nạp VieNeu).
3. **Dữ liệu:** chỉ dữ liệu tổng hợp trên Dev (tenant, đại lý, khách, staff E2E). Mọi form thật để nguyên chưa gửi,
   mọi tin nhắn thật để nguyên chưa gửi; luồng cần gửi chạy trên đối tượng E2E. Không gọi LLM trả tiền khi quay.
4. **Che bí mật:** `scenario.mask = [selector]` làm mờ API key, webhook secret… trước khi quay.
5. **Đăng nhập không lên hình:** đăng nhập một lần trong context không quay, lưu `storageState`, truyền qua
   `UAT_STORAGE_STATE`. Danh tính và cách đăng nhập E2E: `aa-ui-verify` §3 (bảng) + §3a — dùng đúng bảng đó.
   Luồng cần UI bên thứ ba thật (Meta, hộp thư) → Nghiệp quay bằng Claude trên trình duyệt desktop.

## 3. Viết kịch bản

File `tools/uat/scenarios/<app>/<id>.cjs` (mẫu: `tripplanner/tp-pub-01.cjs`, `partner-portal/portal-pub-01.cjs`):
`id`, `title`, `baseURL` (ghi đè bằng `UAT_BASE_URL`), `viewport` (1440 × 900; 390 × 844 cho trang dùng trên điện
thoại), header Given/When/Then, danh sách `steps`.

- Mỗi step có `caption: { en, vi }` (vừa là phụ đề vừa là lời đọc) và `run()` **làm hành động và assert** kết quả
  (heading, URL, số dòng, badge trạng thái).
- Assert sai → step FAIL, dừng chạy, **video vẫn giữ** làm bằng chứng lỗi; phụ đề step đó có `[FAIL]`.
- **Fast mode** cho CI / regression: `node tools/uat/record.cjs <scenario> --fast` (không video, không giữ nhịp,
  chỉ `result.json`).
- Id theo danh mục **`tools/uat/catalogue.json`** (AA-855: một dòng mỗi kịch bản — app, module, story, roles, kinds,
  covers, screens, status live / after-lane / blocked / retired, round, identity, writes, paid; kiểm bằng
  `node tools/uat/lib/catalogue.cjs` và `node --test tools/uat/tests/*.test.cjs`). Kịch bản mới = thêm dòng catalogue
  cùng PR; id retired giữ nguyên, không tái dùng số. Kịch bản đọc thêm vào `scenarios/dryrun.cjs`; kịch bản ghi / trả
  phí dùng `rw()` của `lib/uat-page.cjs` (allowWrites hẹp, `after()` trả lại giá trị cũ) và không vào dry run.
- **Chặn tenant pilot** (AA-855, `lib/pilot-guard.cjs`, fail closed): trước mỗi kịch bản đã đăng nhập, record.cjs đọc
  tenant / agency qua API của app (`/api/tenant/me`, `/bff/me`) trong một context không quay; ngoài allow-list tổng
  hợp hoặc có dấu pilot → exit 5 `pilot_guard`, không video. Phạm vi CRM chỉ khớp theo id (agency tự đặt
  `display_name`); Content khớp được theo tên bịa khi chưa ghim id. Id tenant không công khai được để trong
  `tools/uat/work/uat-allowlist.json` (gitignore). Mọi trang staff có tên tenant (CIS-01/04/06/12) dùng `allowRows`
  (che hàng ngoài allow-list) + `h.assertRowsFiltered()`; trang mới có tên tenant cũng phải thêm.

## 4. Giọng đọc

- **Tiếng Anh:** Kokoro `af_heart` (nữ) — Nghiệp đã duyệt.
- **Tiếng Việt:** VieNeu-TTS v3 Turbo, giọng miền Nam **"Thục Đoan"** (đã chọn). Đổi bằng `UAT_VI_VOICE`
  (vd. `Adam` = nam miền Nam, hoặc file giọng clone `own-voice/work/voice_w<k>.npz`).
- **Giọng của chính người đọc:** chỉ khi người đó đồng ý (ghi rõ trong báo cáo phiên), mẫu ≤ 8 s; hướng dẫn thu và
  script: `tools/uat/own-voice/README.vi.md` + `clone.py`.
- **Giọng riêng của tech lead (đã đồng ý, S279):** `own-voice/work/voice_nghiep_v1.npz` (gitignored) — dấu giọng trung bình 12 clip
  giọng thật, giọng miền Nam; file mang luôn thông số đọc (temperature 0,6, top_k 20, chậm 8 %) và `lib/vi_vieneu.py` dùng đúng
  thông số đó: `UAT_VI_VOICE=$PWD/tools/uat/own-voice/work/voice_nghiep_v1.npz bash tools/uat/run.sh <kịch bản>`. Fine-tune LoRA
  trên audio lớp học (nén, vang) cho kết quả kém hơn zero-shot; chỉ fine-tune khi có 15–30 phút thu sạch.
- **Chỉ TTS miễn phí chạy local.** Giọng chưa đủ hay → thử model mã nguồn mở khác. Piper `vi_VN-vais1000` (giọng Bắc)
  đã bị loại. Dịch vụ TTS trả tiền nằm ngoài phạm vi (luật dịch vụ trả tiền: `aa-lessons/lessons.md` mục Cách làm việc).
- **Luật giấy phép:** code, trọng số và giọng preset đều phải cho phép dùng thương mại. Danh sách đã loại (NC / CPML /
  không rõ) và cách kiểm một model mới: `references/voices-licences.md` — đọc trước khi thêm giọng.

## 5. Chạy, build và kiểm

```bash
bash tools/uat/run.sh scenarios/<app>/<id>.cjs
# captions -> tts.py (EN + VI, durations.json) -> record (mỗi step giữ >= độ dài lời đọc) -> build.py -> check_sync.py
# exit 0 PASS | 2 có step FAIL (video vẫn giữ) | 3 egress không phải VN
```

`build.py`: ffmpeg H.264, phụ đề tiếng Anh burn vào hình, hai track audio EN (mặc định) + VI, sidecar
`.en/.vi.srt` + `.vtt`, `.result.json`. Video giới thiệu TripPlanner: `bash tools/uat/intro/run_intro.sh en|vi`
(một MP4 mỗi ngôn ngữ, kịch bản cảnh ở `intro/narration.json`).

Kiểm xong khi cả ba đạt:

1. **Khung hình:** mở từng ảnh `work/<id>/frames/*.png` (một ảnh mỗi 20 s) — thấy con trỏ, phụ đề đọc được, không có
   trang Security Checkpoint / trang lỗi.
2. **Khớp tiếng:** `check_sync.py` báo có tiếng ở mọi điểm bắt đầu cue, cho cả hai track. `run.sh` kiểm track EN;
   track VI chạy thêm: `tools/uat/venv/bin/python -I tools/uat/check_sync.py <mp4> <stem>.vi.srt --track 1`.
3. **Kết quả:** `result.json` có PASS/FAIL từng step; báo cáo ghi đúng step FAIL + mốc thời gian.

Agent không tự nghe được: độ tự nhiên của giọng là Nghiệp quyết.

### 5a. Chạy thử (dry run) cả bộ — AA-1009

```bash
node tools/uat/dryrun.cjs --list                 # bộ kịch bản công khai / chỉ đọc (manifest scenarios/dryrun.cjs)
node tools/uat/dryrun.cjs                         # cả bộ, fast mode, một bảng kết quả + git SHA từng app
node tools/uat/dryrun.cjs --app booking --stop-on-fail   # lọc: --only <id,..> / --app / --identity (AND)
node tools/uat/dryrun.cjs --identity crm --include-writable   # kịch bản CRM (chủ đại lý GHI ĐƯỢC): chỉ khi gọi rõ
node tools/uat/dryrun.cjs --record TP-02          # quay một video từ harness (đăng nhập danh tính rồi run.sh)
node --test tools/uat/tests/dryrun.test.cjs       # unit test logic runner (không cần trình duyệt)
# exit 0 tất cả PASS | 2 có FAIL / BLOCKED / CRASH | 3 egress không phải VN | 4 thiếu RAM
```

- Mỗi danh tính (`public`, `studio`, `crm`, `cis-admin`, `booking`) đăng nhập **một lần** ngoài kịch bản
  (`lib/signin.cjs`), lưu `storageState` chmod 600 trong `work/` (gitignore), dùng lại khi app còn nhận. `cis-admin` /
  `booking` cần phiên MFA admin còn hạn (đọc mã e-mail từ hộp thư e2e). Đăng nhập lỗi → kịch bản của danh tính đó
  **BLOCKED** kèm lý do, phần còn lại vẫn chạy.
- Kịch bản dry run viết bằng `ro()` của `lib/dryrun-page.cjs` (`readOnly`, `identity`, `check()` = tiêu đề + dữ liệu
  hoặc empty state + không API 5xx/401/403). Runner luôn bật chặn ghi: request không phải GET bị huỷ và kịch bản FAIL
  (beacon telemetry và keep-alive phiên staff `POST /api/auth/refresh` chỉ được liệt kê); `page.request` /
  `context.request` ghi bị từ chối (tính là ghi), WebSocket bị đóng; đường gọi model trả tiền (TripPlanner search /
  narrate) bị chặn hẳn. Runner từ chối kịch bản có danh tính đăng nhập mà không `readOnly`, có `allowWrites` hoặc
  `prepare()`.
- Danh tính `crm` (chủ đại lý review) **ghi được** (CRM chưa có vai trò chỉ đọc): mặc định bỏ qua, báo cáo ghi "Not run";
  chạy bằng `--include-writable`. Phiên lưu riêng `work/dryrun/.state-crm.json`, không dùng chung với bộ CRM review.
- Lỗi AWS chỉ ghi mã lỗi (`AccessDenied`, `ExpiredToken`); báo cáo che ARN và số account 12 chữ số trước khi chép vào
  repo gốc (public).
- Kết quả `tools/uat/work/dryrun/<stamp>/results.{md,json,tsv}` → chép `results.md` vào
  `docs/audits/<date>-S<nnn>-uat-dry-run/` trong root PR.

### 5b. Kịch bản GHI / trả phí (write set) — AA-855 W-01..W-04

```bash
node tools/uat/dryrun.cjs --only W-01,W-02 --preview   # chỉ phần đọc (các bước trước bước ghi đầu tiên), $0
node tools/uat/dryrun.cjs --record W-01 --allow-paid   # quay 1 kịch bản trả phí (LLM ~0,1–0,2 USD), tenant audit
UAT_STUDIO_TENANT=audit-terra-family node tools/uat/dryrun.cjs --record W-02 --allow-paid   # đổi tenant audit
node tools/uat/dryrun.cjs --record W-04 --include-writable   # W-04 chỉ đọc (xuất file), $0, nằm trong bộ dry run
```

- `scenarios/write-set.cjs` liệt kê kịch bản ghi (W-01..W-03, PRT-02, PRT-06, DRILL-01): không bao giờ chạy trong cả
  bộ hay qua `--app` / `--identity`; chỉ gọi theo id. Kịch bản trả phí bị từ chối nếu thiếu `--allow-paid` (cờ này kéo theo
  `--include-writable`). Catalogue đánh `paid` khớp với kịch bản (test `checkWriteSet`).
- Diễn tập pilot, phần CRM (AA-1086): REH-02b-agency-setup → REH-06 … REH-10 trong write set, danh tính
  `crm-rehearsal` (chủ) / `crm-rehearsal-agent` (tư vấn) ghim vào `pilot-rehearsal-01`; REH-10b chỉ đọc, danh tính
  `crm-staff`. Thiết lập đại lý + thứ tự + bàn giao: `tools/uat/scenarios/crm/REHEARSAL.md`. Bước nào khiến CRM gửi
  mail cho khách phải gọi `R.checkTraveller()` trước (địa chỉ bịa: `*.invalid` hoặc miền hộp thư E2E).
- `allowWrites` ghi được cả phương thức: `'POST ^https://…/bff/x$'`, `'PUT|PATCH ^…'` (`lib/net-guard.cjs`
  `parseAllow`); nguồn không có tiền tố vẫn cho mọi phương thức ghi như cũ. Kịch bản mới nên ghi rõ phương thức.
- Danh tính `studio-audit` (người partner E2E, EDITOR ở 4 tenant audit tổng hợp; secret
  `crm/dev/e2e-test-crm/harbour-lights-owner`, chỉ đọc trong bộ nhớ): mỗi lượt chạy đúng MỘT tenant audit
  (`UAT_STUDIO_TENANT`, mặc định `audit-atlas-hearth`; giá trị khác bị từ chối). Pilot guard ghim mọi kịch bản
  studio-audit vào tenant đó; chọn studio trên trang chooser theo tên tổng hợp, mỗi tenant một file phiên.
- **DRILL-01** (diễn tập xoá dữ liệu khi offboard tenant, CIS admin): danh tính staff `cis-admin` được ghi chỉ trong
  write set (`lib/dryrun-core.cjs` `WRITE_SET_STAFF`), trên một tenant audit tổng hợp (`UAT_DRILL_TENANT`, mặc định
  `audit-wildkind-travel`). Quay riêng, ~15 phút (chờ báo cáo DRY RUN):
  `node tools/uat/dryrun.cjs --record DRILL-01 --include-writable`. Không duyệt, không xoá gì; `after()` khôi phục
  tenant nếu một bước lỗi sau offboard. Token staff sống 15 phút và keep-alive bị chặn, nên kịch bản tự tải lại trang
  khi token gần hết hạn (proxy làm mới) và mở lại yêu cầu.
- Mỗi lệnh ghi qua `limitWrites()` (`lib/uat-page.cjs`): tối đa 1 lần (write tối đa 2 khi lần đầu 422 thiếu CTA),
  lệnh thừa bị huỷ trước khi rời trình duyệt. Bước có thể ghi đánh `step(..., { writes: true })`.
  Rule mặc định giới hạn POST; `method: 'PUT' | 'PATCH' | 'DELETE'`, một danh sách, hoặc `'*'` (mọi phương thức ghi)
  giới hạn phương thức khác; `read: true` cho phép giới hạn một GET trả phí (tìm kiếm có model); `accept(req)` lọc
  thêm (từ chối đếm vào `<name>_refused`); `strict: true` huỷ và đếm mọi phương thức ghi khác trên cùng path. Không
  `strict` thì phương thức khác rơi xuống guard trình duyệt: `allowWrites` ghi `"<METHOD> <regex>"` (hoặc
  `"PUT|PATCH <regex>"`) để chỉ cho đúng method đó (`lib/net-guard.cjs` `compileAllow`; regex trần = mọi method).
- Studio của owner đại lý rehearsal: tech lead mời owner (Tenant 360 › Members › Invite, role owner) rồi
  `node tools/uat/accept-owner-invite.cjs --since <ISO trước lúc mời>` nhận lời mời từ hộp thư e2e (tài khoản có sẵn).
- Thứ tự quay: W-01 riêng; W-02 (chọn chủ đề + góc, bài bắt đầu viết) → W-03 ngay sau (theo dõi tới khi bài giao) →
  W-04 (xuất HTML có dấu AI + bài mạng xã hội). Bàn giao id qua `work/uat-write-chain.json`, thiếu thì đọc lại Dev.

## 6. Đóng gói

```bash
python3 -I tools/uat/package.py uat <ID>_<yyyymmdd>_v<n> "<tiêu đề>"
python3 -I tools/uat/package.py intro TripPlanner-intro <yyyymmdd> "<tiêu đề>"
```

Một zip mỗi video trong `out/packages/`: MP4 mỗi ngôn ngữ, MP3 lời đọc, SRT/VTT, kịch bản lời đọc, README VI + EN.
Zip là bản gửi đi được nguyên trạng: không id nội bộ (AA-xxx), không log chạy, không `result.json`.
Tên: `<ID>_<yyyymmdd>_v<n>` (vd. `TP-PUB-01_20261030_v2`); quay lại sau khi sửa → tăng `v<n>`.

## 7. Upload Google Drive

Connector Drive chỉ mang được text; video đi bằng **rclone**, remote `aadrive:` (gốc = thư mục AdventureAsia, Nghiệp
đã cấp quyền). Chọn thư mục theo **tên**, theo loại video:

```bash
rclone copy <thư mục local> "aadrive:01 Video/Giới thiệu sản phẩm/<tên video>"
rclone copy <thư mục local> "aadrive:01 Video/UAT (kiểm thử nghiệm thu)/<round>/<app>"
rclone check <thư mục local> "<remote vừa copy>" --one-way     # phải ra 0 differences
```

Upload xong khi `rclone check` báo 0 differences. Di chuyển trên Drive bằng `rclone moveto` (link giữ nguyên).
Nghiệp tự mở quyền chia sẻ. rclone đang dùng client_id chung sắp bị khai tử trong 2026: khi rclone cảnh báo/ngừng,
tạo OAuth client riêng (Google Cloud project miễn phí) rồi `rclone config update aadrive client_id=… client_secret=…`
— giá trị không ghi vào repo hay skill.

## 8. Index và báo cáo

- Index mỗi app: `docs/audits/<date>-S<nnn>-uat/<app>.md` trong root PR — kịch bản, story, verdict, độ dài, step FAIL +
  mốc thời gian, commit SHA của app lúc quay. **Không link Drive** (repo gốc public): link Drive chỉ nằm trong trang
  artifact cho chủ doanh nghiệp và draft Jira, không bao giờ trong index public (AA-855, kế hoạch S268).
- Một trang artifact cho chủ doanh nghiệp (một tab mỗi app), lưu local theo `aa-session` (save audits locally); link
  đưa vào draft Jira cuối phiên, lời văn theo `aa-jira-update`.
- Lỗi tìm thấy → issue có sẵn hoặc issue mới (hỏi trước, `aa-linear-issue`).

## Bảo trì

- Script mới cho `tools/uat/`: header ngắn (làm gì, cách gọi, chi phí), đường dẫn tương đối theo thư mục script,
  không secret, không đường dẫn `/home/...`. `venv/`, `models/`, `work/`, `out/` đã gitignore.
- Đổi giọng, đổi luật giấy phép → sửa §4 + `references/voices-licences.md` cùng lúc.
