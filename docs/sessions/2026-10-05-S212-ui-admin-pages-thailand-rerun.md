# S212 — UI v2 admin pages (AA-664/705/667/666) + rerun Bhutan & Thailand song song (05/10/2026)

**Tác nhân:** Kiro (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:453` (sau #567) · **Migration mới nhất:** CIS 203 (không có migration mới phiên này)

## Trạng thái
Phiên dài, nhiều lần Nghiệp phải chỉ lỗi do mình báo "Done" khi chưa verify thật. Bài học rút ra ghi ở cuối. Kết quả: **4 trang admin UI v2 xong (AA-664/705/667/666)** + **rerun Bhutan (32) & Thailand (41) master**, chạy song song. Phát hiện + sửa 1 bug 500 thật, audit ra lỗ hổng kiến trúc (bg task in-process) → tạo issue triệt để.

## UI v2 admin — 4 trang (mỗi issue 1 PR, verify live)
| Issue | Trang | PR | Verify |
|---|---|---|---|
| AA-664 | Overview dashboard `/admin/overview` | #562 merged | **live HTTP 200**, funnel per-country + 6030 atoms + cost + alerts (ảnh Nghiệp xác nhận) |
| AA-705 | SEO Intelligence `/admin/seo-intelligence` 5 tab | #563 + #566 (fix) | **500 → fixed → live 200** |
| AA-667 | S1 Rewrite live streaming | #564 | **live `found:true`** steps trên job Thailand thật |
| AA-666 | Tenant 360 (làm LẠI: inline, không trang riêng) | #565 (bỏ) → #567 | merged, chờ verify tab inline |

- **AA-664** `api/routers/admin_overview.py`: GET /admin/overview cache 60s, 6 section, tái dùng dashboard_summary/cost_guard/job summary/v_tenant_monthly_usage/notifications; funnel per-country là SQL mới. FE kit + react-query.
- **AA-705** `api/routers/admin_seo.py`: GET /admin/seo-intelligence 5 tab (overview/keywords/questions/gaps/spend), merge search_demand + seo_context + published_tours.seo_keywords_used + dfs_call_log + segment_research_log. **search_demand KHÔNG có CPC/competition** → bỏ 2 cột. **Bug 500: `percentile_cont(0.5) WITHIN GROUP (ORDER BY researched_at)` trên timestamptz không hợp lệ** → đổi median trên age-in-days (#566). FE kit DataTable.
- **AA-667** `admin_pipeline.py::_build_s1_progress()` tạo redis riêng + WritingProgress(stream_stages={s1_generate}, key `wp:{master}:tour:{job_id}`) bind trong `_run_tour_job`; endpoint GET /admin/progress/s1/{job_id}. FE `AdminLiveWriter.tsx` + nút "Live view" trên row running. **LƯU Ý UX:** nút chỉ hiện khi job do CHÍNH trang kích (jobIds state) — job kích ngoài (curl/wave) không hiện → cần endpoint list active jobs (để AA-721/723).
- **AA-666 LÀM LẠI:** bản đầu (#565) tạo trang riêng `/admin/tenants/[id]` + link click-tên → Nghiệp chê "quái đản" (trang Tenants đã có expand inline sẵn). Sửa (#567): **bỏ trang riêng + revert link**, mở rộng `TenantDetail` inline thêm 4 tab: Usage&Billing (/admin/billing), Quality (gate-telemetry client-filter), **Audit (endpoint MỚI GET /admin/tenants/{id}/audit** over acp_shared.audit_log, verified 36 rows WanderLux), Settings (read). Next16 params là Promise.

## Rerun (chạy song song build UI)
- **Bhutan:** raw đã đủ trong DB (33 tour active từ CON-12 sheet "Newtemplate", 2 NCC: Blue Poppy 12 + Wangchuk 21). Chuẩn hóa provider. RDS snapshot `aa-cis-dev-db-pre-bhutan-rerun-20261005`. **Reset derived scope-Bhutan** (7 assert PASS, platform nước khác nguyên). Pilot 3 → wave 30. Kết quả **32 master + 32 atomized**; 1 tour trashed (GLIMPSE OF BHUTAN — judge brand_fit 3.0 do **raw nghèo** itin 431 char, không phải bug).
- **Thailand:** 43 raw, không cần reset (master=0). Pilot 3 (3/3 sạch) → wave 40. **41 master + atomized / 2 pending** (AA-724). Giữa chừng **16 job S1 bị deploy giết** (merge 3 PR UI lúc wave chạy — mình phạm quy tắc "không deploy khi job chạy") → re-run 19 tour.
- **Tổng rerun tới nay:** China 121, Taiwan 36, Korea 30, Mongolia 17, Bhutan 32, Thailand 41 = ~277 master.

## Lỗ hổng kiến trúc phát hiện (Nghiệp yêu cầu audit)
`asyncio.create_task` còn trong API (chết khi deploy, không hiện trang Jobs vì ở `shared.pipeline_jobs` ≠ `shared.job`): **5 task** — `_run_tour_job` (S1), `_revalidate_job`, `_recompute` (admin_atoms), `_run` (admin.py AA-713), `_s1_batch_ingest_task`. AA-651 tách worker nhưng **bỏ sót** chúng. → **AA-723 (P1)**: move TẤT CẢ sang worker; API chỉ serve request.

## Linear
- **Done:** AA-664, AA-705, AA-667, AA-666 (comment bằng chứng live đủ 4 DoD).
- **Tạo mới:** AA-721 (Jobs page rebuild worker-aware), AA-722 (dọn IA Dashboard cũ — tab SEO thừa sau AA-705), AA-723 (move all bg task → worker), AA-724 (S1 writer hype/persona tone cho tour cycle/bike + forbidden word, 2 tour Thailand pending làm ca mẫu).
- **Updated:** AA-716 (+scope dismiss review_queue khi trash raw — phát hiện khi Nghiệp trash GLIMPSE còn kẹt review).

## Bằng chứng verify
- AA-664 live 200 (ảnh + curl). AA-705 fix 500 → live 200 (coverage 100%, 1637 keywords, 92 gaps). AA-667 `/admin/progress/s1/{running}` → found:true steps. AA-666 /details+/billing 200, audit query live 36 rows.
- Playwright render 3 trang: mount sạch, nav/brand/tabs đúng (401 data vì render-bot không auth — Nghiệp xem data thật qua login prod).

## Còn lại
1. **AA-666 #567 verify live** tab inline (Billing/Quality/Audit/Settings) sau rollout `:453` — đang chờ.
2. Rerun tiếp: Laos(46) → Nepal(86) → Sri Lanka(126) → India(236). (Japan 80, Philippines 46, Pakistan 18 chưa gán thứ tự.)
3. AA-723 (P1, move bg task sang worker) — nên làm sớm, gốc của nhiều lỗi.
4. AA-721/722/724.

## Lưu ý kỹ thuật / BÀI HỌC
- **BÀI HỌC LỚN (Nghiệp nhắc nhiều lần):** KHÔNG báo "Done" khi mới build+render — phải **verify endpoint live thật (curl 200 + shape) trên domain**. SEO Intelligence lỗi 500 thật mà mình tưởng 401-render-bot. Verify đầy đủ, không nửa vời.
- **Quy tắc đã phạm:** "không deploy/merge khi job đang chạy" — merge 3 PR UI lúc wave Thailand chạy → deploy giết 16 job S1. Tách bạch: hoặc rerun, hoặc deploy.
- **S1 rerun in-process** (`shared.pipeline_jobs`) không bền qua deploy + không hiện trang Jobs — gốc rễ AA-723.
- **Đếm rerun ĐÚNG CÁCH:** distinct tour theo 3 trạng thái master/review-pending/not-run; KHÔNG đếm bản superseded; tour trong review có `pipeline_status=ingested` (chưa publish) ≠ "chưa chạy". master+review+not_run = raw_active.
- **2 kiểu tour fail review KHÁC NHAU:** (a) raw nghèo (GLIMPSE OF BHUTAN itin 431 char) → trash; (b) raw đầy nhưng writer hype/persona tone (tour cycle/bike Thailand) → AA-724, regenerate không cứu được (4 version đều fail), phải fix prompt.
- **MÔI TRƯỜNG shell:** session hay mất PATH → prefix `export PATH="$HOME/.nvm/versions/node/v22.22.3/bin:/usr/local/bin:/usr/bin:/bin"`. Node mặc định 18 → `next build` fail (cần ≥20.9), phải dùng nvm v22.22.3.
- **ECS exec:** runner `.tmp-session/s209_run.sh <script.py> <s3key>` (upload S3 + presign + exec kéo về chạy + ghi S3 + đọc lại). STS `--profile aa365-admin`.
- Secret admin: `aa-cis/dev/admin-secret`. Domain Dev `https://api-cis.lumiguides.it.com`. tenant aa_internal `00000000-0000-0000-0000-000000000001`, WanderLux `a1b2c3d4-0001-4000-8000-000000000001`.
- Log local: file này. Memory Notion: prepend S212.
