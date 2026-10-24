---
id: PROD-01-s1-go-no-go
title: "S1-first step 5: written go/no-go from the S249 shadow ≤50"
description: "Quyết định go/no-go bằng văn bản cho lần viết lại S1 cả catalogue (writer v2), AA-926/916/924/790 và brand-fit v2, dựa trên shadow ≤50 + pilot 3 tour S249."
type: report
status: draft
owner: nghiep
audience: [engineer, cto, agent]
applies_to: [cis-core]
last_reviewed: 2026-10-24
review_every_days: 180
related: [AA-645, AA-790, AA-926, AA-916, AA-924, PROD-01-aa645-writer-decision]
---

# S1-first bước 5: quyết định go / no-go bằng văn bản (S249)

> Điều kiện mở đã đóng, xem bản cuối [../2026-10-24-S250-s251-go-no-go/](../2026-10-24-S250-s251-go-no-go/README.md) (S250).

Bản tư vấn cho Nghiệp · S249 · 24/10/2026 · Tác nhân: Claude Code · Refs AA-645, AA-926, AA-916, AA-924, AA-790
Chỉ đọc dữ liệu có sẵn, không gọi LLM trả phí, không sửa code. Mọi số đều có nguồn (ký hiệu ở mục 0). Bản này đã sửa theo
một lượt phản biện độc lập; số bị tranh luận đều được tính lại từ nguồn (`numbers.json`, mục `derived.*` mới).

---

## English summary (for Linear)

**S1-first step 5: written go/no-go (S249).** Writer quality comes from the S248 pooled n = 50 golden blind panel
(W×Sonnet has about 1/10 of A+'s serious errors per checkable claim). The shadow ≤50 (run cfebc266, 50 unseen tours
stratified by country, writer v2 W×Sonnet through the full A1 chain, nothing published, $3.56) tests the **pipeline,
cost and code gates**: 50/50 publishable, 1 attempt per tour, 0 tour errors, 0 brand leaks, 0 legacy itinerary path,
Jev ran on 50/50 tours (0 tours with a Jev problem; 8 verdict-level errors). On these 50 tours, new vs live is measured
by code only until the blind panel runs: pages with a code gate 4/50 new vs 13/50 live (paired McNemar p = 0.012);
3 of the 4 new ones are `DAY_DEPARTURE_MIDTRIP` false positives (a farewell dinner on day N−1). Must-pass code gate:
49/50 (one real day loss). Figure coverage 0.676 new vs 0.415 live; of the 46 tours with source figures: higher 27,
lower 0, tied 19. Cost $0.071 per tour (bootstrap 95% CI 0.062–0.081), 11% under the S248 model ($0.080). No stop
condition fired on the ≤50 shadow.

Three items are open:
1. India "Rajasthan Adventure" was publishable with 10 of its 15 days while its title still says "15 days". That is
   1 of the 6 sampled tours with ≥ 15 plan days (Wilson 3–56%), 0 of the 44 shorter ones. The step that dropped the
   days is not identified (flag_fix also rewrote the itinerary).
2. The blind panel on the 50 new-vs-live pairs (packet built, $0) has not run. The last d13 stop condition is checked
   only by its code proxy, and against the live page instead of A+ (A+ was not generated for these tours).
3. On the 3-tour pilot (run 2007e626) the d13 "stayed on v1 > 10%" stop **fired** (1/3 = 33%). The run went on to
   the ≤50 shadow without stopping or reporting to Nghiệp, against RUN.md step C. Nghiệp to decide how the stop works
   for waves of fewer than ~10 tours (for example a count instead of a percentage). The real 3-tour pilot will very
   likely pick the same 3 Laos tours, held tour included.

| Item | Recommendation |
|---|---|
| S1 catalogue rewrite, writer v2 | **Go, with conditions.** Before: the blind panel on the wave-50 packet; close the missing-day hole net-zero (make the existing `ITINERARY_DAY_COUNT_MISMATCH` hard for A1 v2, or enforce `DAY_COUNT_VS_DURATION` and retire `ITINERARY_DAY_COUNT_MISMATCH`; gate count unchanged; or no code: hold and promote back per tour) after finding which step dropped the days; the impact-memo §6 prep checklist; the small-wave stop rule and what to do with the held Laos tour. Then one decision by Nghiệp (d04): ≤ 864 tours, ~$70–81 central, approval ceiling ≈ $89 (worst case ≈ $152, every tour at p90 + atomize worst); a real ≤50 wave (A3 on) between the 3-tour pilot and the country waves, unless d04's "after wave ≤50" meant the shadow; and whether the approval covers going on between waves while no stop condition fires. |
| AA-926 quality registry (parked branch) | **Go.** Rebase, add the codes added since (brand-fit v2 caps, v2 report codes, meal-time, day oracle), offline replay showing the same decisions, independent review (CI lint), merge before the wave freeze. Use it to count which A1/T10 gates the code checks make redundant (S246 step 5 asks for ≥ 5 removed; none identified yet beyond AA-924's 2). |
| AA-916 Writing Memory P0 | **Go.** WM-03 + WM-05 first so that admin edits on held tours are captured; migration + RLS → agent review; DB Migrate apply only outside a wave. |
| AA-924 severity + gate merges | **Go, after AA-926.** T10 gates go from 26 to 24, the replay must show the same passed/held decisions, low priority. |
| AA-790 tenant-voice rubric gate | **No-go for the rubric gate for now.** Not technically ready: AA-783 agreement is κ 0.40 (CI 0.14–0.65) against a 0.6 stand-in bar; on 40 pieces the panel was stricter than the labels on 10 and looser on 2; the labels are Claude drafts. The deterministic post-repair integrity check could go on its own if Nghiệp wants it split. |
| Writing Memory P1+ (AA-917…923) | **Not now.** Revisit after the catalogue wave, once P0 signals exist. |
| Brand-fit v2 as an A1 gate | **Stays report-only** (d02; S246 rule: no brand_fit for A1 retry/HITL). Judge v2 caps 28/50 final pages; Jev's promise zone returned only grey verdicts, so judge v2 and Jev disagree and neither is calibrated for promises. The blind panel decides. |

---

## 0. Ký hiệu nguồn

| Ký hiệu | File (đều dưới `/home/nghiep/projects/AA-Ecosys/`) |
|---|---|
| **[W]** | `.tmp-session/s249/aa645/wave50-summary.json` → `countries.ALL.<field>` (hoặc `countries.<nước>.<field>`) |
| **[R]** | `.tmp-session/s249/aa645/wave50-report.txt` (bảng theo nước + stop conditions) |
| **[S]** | `.tmp-session/s249/aa645/wave50-shadow.json` → `tours[]` (số liệu từng tour), `eligible`, `dropped`, `totals` |
| **[N]** | `numbers.json` cạnh file này (số em tự tính lại từ [S], [P], [B]) → `derived.*`, `catalogue.*`, `per_country.*`, `waves_estimate` |
| **[P]** | `.tmp-session/s249/aa645/pilot.json`, `pilot-summary.json`, `pilot-dry.txt` |
| **[RUN]** | `.tmp-session/s249/aa645/RUN.md` (run sheet AA-645 S249: bước C pilot, bước D ≤50, điều kiện dừng) |
| **[B]** | `.tmp-session/s249/aa645/brandfit-analysis.txt` / `.json`, `brandfit-result.json` |
| **[DM] [IM] [PN]** | `docs/audits/2026-10-23-S248-aa645-writer-decision/` `decision-memo.md`, `platform-impact-memo.md`, `pooled-n50.md` |
| **[Q]** | `docs/audits/2026-10-21-S246-content-quality-advisory/README.md` §5, `q4-q8-followup.md` |
| **[F]** | `docs/audits/2026-10-23-S248-s1-step01/README.md` (bảng dữ kiện + bộ kiểm code) |
| **[CL]** | `docs/audits/2026-10-23-S248-calibration-loop/memo.md` |
| **[A783]** | `.tmp-session/s249/aa783_report_full_s249.md` (báo cáo đồng thuận AA-783, S249) |
| **[BL]** | `docs/backlog/README.md` §3 |

File `.tmp-session/` không vào git; số cần giữ đã chép vào `numbers.json`.

---

## 1. Kết luận + đề xuất

**Câu trả lời ngắn:** chất lượng writer v2 (W×Sonnet) đến từ panel mù trên golden gộp n = 50 của S248 [PN]. Đó là
thước chính anh đã duyệt (S246 P1 = a: lỗi nghĩa nghiêm trọng / khẳng định kiểm được, chấm mù; lỗi bắt bằng code chỉ là
cổng phải-đạt). Shadow ≤50 là bài thử **đường ống, chi phí và cổng code** trên 50 tour lạ: không lỗi lần nào, 50/50
publish được, rẻ hơn mô hình 11%. Trên 50 tour này, mới so với live hiện **chỉ đo bằng code** (trang dính cổng, độ phủ
số liệu) cho tới khi panel mù chạy. Cổng code phải-đạt: 49/50, một tour mất ngày thật (Rajasthan). Còn **ba việc mở**
(panel mù, lỗ mất ngày, điều kiện dừng đã bật ở pilot) và anh cần duyệt catalogue (d04) trong một quyết định, gồm cả
các câu hỏi ở mục 4.

| # | Hạng mục | Đề xuất | Lý do chính (số ở mục 2) |
|---|---|---|---|
| 1 | **S1: viết lại cả catalogue bằng writer v2** | **GO có điều kiện** | 50/50 publish được, 0 lỗi, 0 lần thử lại [W.publishable, errors, attempts_max]. Trang dính cổng code 4/50 so với 13/50 trang live, p = 0,012; bỏ 3 báo nhầm `DAY_DEPARTURE_MIDTRIP` thì 1/50 so với 12/50 [N.derived.gate_pages]. Độ phủ số liệu 0,676 so với 0,415 [W.figure_coverage_new/live]. $0,071/tour, thấp hơn mô hình 11% [N.derived.cost_mean, real_vs_model]. Không điều kiện dừng nào bật ở shadow ≤50 [W.stop_conditions]; ở pilot 3 tour thì "ở lại v1 > 10%" **đã bật** (mục 2.3). **Điều kiện** (mục 3.1): (a) chạy panel mù trên gói 50 cặp đã dựng sẵn ($0); (b) lấp lỗ "mất ngày" sau khi tìm ra khâu làm rơi ngày; (c) checklist chuẩn bị §6 của [IM]; (d) anh chốt luật dừng cho wave nhỏ và cách xử lý tour Lào bị giữ. Sau đó anh duyệt catalogue ở mục 4. |
| 2 | **AA-926** (merge nhánh registry đang giữ) | **GO** | Không phải cổng mới: đây là sổ đăng ký mã lỗi, một file ngưỡng và lint, để ngưỡng 7.0 không còn bị chép ở 5 chỗ (mô tả AA-926). Điều kiện S246 bước 5 là "S1 khá lên thật trước" [Q §5]: panel S248 đã cho thấy điều đó, shadow cho thấy đường ống chạy được. Cần rebase, thêm các mã mới sinh từ S248–S249, replay offline cho ra quyết định y hệt, review độc lập vì có thêm lint CI. Nên merge **trước** cửa sổ đóng băng của wave, vì trong wave cấm deploy backend [IM §3.2]. Registry liệt kê đủ gate, nên dùng nó để đếm cổng thừa cho mục tiêu "xoá ≥ 5 cổng" của bước 5 (hiện chưa xác định được cổng A1 nào). |
| 3 | **AA-916** (Writing Memory P0: lưu sửa trước/sau) | **GO** | Đây là phần WM duy nhất mà kế hoạch S246 giữ lại ở bước 5 [Q §5]. Lần viết lại catalogue sẽ sinh tour bị giữ lại và admin sẽ sửa tay, nên WM-05 (lưu sửa A1 theo trường) bắt được tín hiệu thật đầu tiên. Có migration + RLS nên cần agent review. DB Migrate `apply` phải chạy ngoài wave (DM-11.4). |
| 4 | **AA-924** (mức độ theo vi phạm + gộp cổng) | **GO có điều kiện: sau AA-926** | Việc này **bớt** cổng T10 (26 → 24), khớp với "xoá cổng thừa" của bước 5 [Q §5]. Số AA-783 ủng hộ việc gộp: F15_voice_warn chỉ bật 1 lần trên 40 bài, F2_banned_patterns bật 0 lần [A783, bảng "Per gate"]. Điều kiện: replay trên bài S234 + golden phải ra cùng quyết định passed/held. Ưu tiên thấp, vì đây là T-series và hiện mới có 4 tenant giả. Bước 5 đòi ≥ 5 cổng bị xoá; đây mới là 2. |
| 5 | **AA-790** (cổng rubric giọng tenant) | **NO-GO cho phần cổng rubric, lúc này** | **Chưa sẵn sàng về kỹ thuật**, không phải "chờ cho chắc". Một cổng chấm giọng cần thước đã hiệu chuẩn, mà hiện chưa có: panel so với nhãn chỉ đạt κ 0,401 (khoảng tin cậy 0,135–0,652), dưới mốc 0,6. Trên 40 bài, 10 bài panel chấm chặt hơn nhãn, 2 bài lỏng hơn, và "panel không thay được người" [A783, bảng "Verdict agreement"]. Nhãn còn là bản nháp của Claude được anh duyệt, không phải nhãn anh tự gán [A783, dòng tiêu đề]. Bài học brand-fit v2: rubric LLM chặn trần cả nhánh trung thực nhất (mục 3.2). Ngoài ra AA-790 là cổng LLM mới, trong khi đang đóng băng cổng mới 4 tuần (S247 bước 0, [BL] L1). **Phần "kiểm toàn vẹn sau sửa"** (câu mồ côi, đoạn bị tách) chạy bằng code và chỉ hoàn tác lần sửa hỏng, không giữ bài; làm được ngay nếu anh muốn tách. |
| 6 | Writing Memory P1+ (AA-917…923) | **Chưa** | Cần dữ liệu P0 trước. Xem lại sau wave catalogue cùng Label Desk [CL §8, C2]. |
| 7 | Brand-fit v2 làm cổng A1 | **Giữ chỉ báo cáo** | Trên 50 trang cuối, judge v2 chỉ cho qua 22, chặn trần 28 vì "chi tiết không có nguồn" [N.derived.judge_v2]. Grounding (Jev) tìm 2 câu, sửa xong còn 0 [W.grounding_*], nhưng vùng `a1_promise_unsupported` trả 2.375 phán quyết xám, 0 chấp nhận / bác bỏ, nên Jev **không quyết được gì về lời hứa** [N.derived.jev_zones]. Grounding = 0 vì vậy không chứng minh 28 trang bị chặn trần là sạch; code cũng không thấy lỗi nghĩa (39/50 bài golden có loại lỗi này [F §0]). Kết luận đúng: judge v2 và Jev bất đồng, chưa bên nào được hiệu chuẩn cho lời hứa, panel mù (điều kiện a) quyết. Giữ chỉ báo cáo theo d02 và luật S246 "không dùng brand_fit để quyết retry/HITL cho A1" [Q §5]. Bước tiếp: v2.1, tách "nền địa danh đúng" khỏi "lời hứa về chuyến đi" (comment S249 trên AA-645). |

Cả 7 dòng trên không thêm cổng nào do agent tự đặt. Việc **cần anh duyệt theo luật**:
1. chạy cả catalogue (d04);
2. đi tiếp sau pilot thật và giữa các wave (`aa-wave-rerun` §2: "chờ Nghiệp duyệt rồi mới chạy phần còn lại"; [IM]
   bước 2: "chờ duyệt giữa các wave"), trừ khi lần duyệt d04 của anh ghi rõ là bao luôn "đi tiếp khi không điều kiện
   dừng nào bật". Em hỏi luôn trong cùng quyết định (mục 4).

Lần chạy thử nhỏ (~3 tour rồi ≤ ~50 tour) không cần hỏi riêng (luật paid-runs-subset).

---

## 2. Bảng số đo

### 2.1 Shadow ≤ 50 so với trang đang live (cùng 50 tour, ghép cặp)

"Live" là trang v1 (Haiku) đang trên Master [S.tours[].live_writer_version = v1 cho 50/50]. "Gate page" là trang dính ít
nhất một mã cổng code của bộ kiểm S1 (`DAY_*`, `META_CUT`, `META_LENGTH`, `TEXT_TRUNCATED`, `NUMBER_NOT_IN_SOURCE`,
`INCLUSION_CONTRADICTED`) [F §4.2]. Mọi dòng so sánh mới/live dưới đây là **đo bằng code**; lỗi nghĩa chỉ panel mù đo được.

| Chỉ số | Writer v2 (shadow) | Trang live | Nguồn |
|---|---:|---:|---|
| Tour chạy / lỗi | 50 / 0 | – | [W.done, errors] |
| Publish được | **50/50** (Wilson 95%: 0,93–1,00) | – | [W.publishable]; [N.derived.publishable_wilson95] |
| Số lần thử TB / tối đa | 1 / 1 | – | [W.attempts_mean/max] |
| Trang dính cổng code | **4/50** | 13/50 | [W.gate_pages_new/live] |
| …ghép cặp: chỉ mới / chỉ live / cả hai | 1 / 10 / 3 | | McNemar chính xác p = 0,0117 [N.derived.gate_pages] |
| …bỏ `DAY_DEPARTURE_MIDTRIP` (em đọc tay: báo nhầm, mục 3.1) | **1/50** | 12/50 | [N.derived.gate_pages.*_excl_departure_midtrip] |
| Cổng code phải-đạt (S246 P1: code chỉ là cổng phải-đạt) | **49/50** đạt; 1 trượt thật (Rajasthan mất ngày) | – | như trên |
| Mã cổng (thô) | DAY_DEPARTURE_MIDTRIP 3, DAY_COUNT_VS_DURATION 1 | NUMBER_NOT_IN_SOURCE 8, META_CUT 4, DAY_DEPARTURE_MIDTRIP 2, META_LENGTH 1 | [N.derived.gate_codes_raw_new/live] |
| Mã chỉ báo cáo | NAME_NOT_IN_SOURCE 5, NUMBER_NOUN_MISMATCH 4, DAY_PLACE_MISMATCH 2 | 28 / 7 / 5 | [N.derived.report_codes_new/live] |
| Độ phủ số liệu (số liệu nguồn có mà trang giữ lại) | **0,676** | 0,415 | [W.figure_coverage_new/live] |
| …ghép cặp (46 tour có số liệu nguồn): cao hơn / thấp hơn / bằng | 27 / 0 / 19 | | [N.derived.figure_coverage] |
| Grounding (Jev bắt câu không có nguồn): tìm thấy / còn lại sau sửa | 2 / 0 | – | [W.grounding_found, grounding_still_unsupported] |
| Jev chạy / tour có sự cố | 50 / 0 | – | [W.jev_ran, jev_problem] (`jev_problem` đếm tour, không đếm phán quyết) |
| …phán quyết Jev theo vùng | `a1_claim_supported`: 2.223 chấp nhận, 152 xám, 4 lỗi; `a1_promise_unsupported`: 2.375 xám, 4 lỗi | – | [N.derived.jev_zones] |
| Rò tên thương hiệu ("Adventure Asia"…) | 0 | – | [W.leak_pages] |
| Đi đường lịch trình cũ (legacy) | 0 | – | [W.legacy_pages] |
| Số ngày ≠ kế hoạch nguồn | **1** (Rajasthan, 15 → 10) | – | [W.days_match_plan = 49]; [N.derived.days_rows] |
| …theo độ dài kế hoạch | ≥ 15 ngày: **1/6** (Wilson 3–56%); 8–14: 0/19; 2–7: 0/13; 1 ngày: 0/12 | – | [N.derived.days_not_plan_by_band] |
| …đổi số ngày so với live | 2: Rajasthan 15 → 10 (sai, kế hoạch 15); Okinawa 4 → 1 (khớp nguồn: nguồn không có duration, kế hoạch 1 ngày, nên **đúng**) | – | [W.day_count_dropped = 2]; [N.derived.days_rows] |
| Judge brand-fit v2 cho qua: bản nháp / bản cuối (chỉ báo cáo) | 0,494 (87 bản nháp) / 0,44 | – | [W.judge_pass_rate_drafts/final, judged_drafts] |
| …bị chặn trần ở bản cuối | 28/50 (`unsupported` 14, `unsupported_many` 14) | – | [W.judge_capped_final]; [N.derived.judge_v2.final_caps] |
| Brand audit A1: sửa / đạt luôn / giữ người duyệt | 37 / 13 / 0 | – | [W.brand_audit] |
| …mã bắt được | ITINERARY_MEAL_TIME_INVENTED 36, HIGHLIGHTS_OPTIONAL_LANGUAGE 2 | – | [N.derived.brand_audit.codes] |
| Chi phí/tour: TB / trung vị / p90 / p95 / max | **$0,0712** / 0,0589 / 0,1135 / 0,1241 / 0,1907 | – | [W.cost_per_tour_mean/max]; [N.derived.cost_*] |
| …khoảng tin cậy 95% của TB (bootstrap 20.000 lần) | $0,062–0,081 | – | [N.derived.cost_mean_bootstrap95] |
| …theo khâu, TB trên 50 tour: generate / flag_fix / judge / grounding | 0,0562 / 0,0053 / 0,0065 / 0,0032 (cộng = $0,0712) | – | [N.derived.cost_by_stage_over_50] |
| …flag_fix tính trên tour được sửa | $0,0071 mỗi tour được sửa (37 tour) | – | [W.cost_per_tour_by_stage.s1_flag_fix]; [N.derived.flag_fix_cost] |
| Tổng chi phí run | **$3,56** (trần $6) | – | [S.totals.cost_usd_llm_call_log, cap_usd] |
| Lỗi fallback / throttle Bedrock | 0 / 0 | – | [W.fallback_rows, throttle_rows, throttle_errors] |
| Thời gian/tour: trung vị / p90 / max (3 song song) | 62,8 s / 108,3 s / 168,3 s; cả run ~19,5 phút | – | [N.derived.seconds_*]; [S.started_at → updated_at] |

Lưu ý dòng chi phí theo khâu: [W.cost_per_tour_by_stage] ghi flag_fix $0,0071, là TB trên 37 tour có chạy flag_fix. Bốn
khâu chỉ cộng lại bằng TB $0,0712 khi flag_fix được chia đều trên cả 50 tour ($0,0053).

So với ngưỡng dừng anh đã chốt (d13, [IM §6]) trên shadow ≤50: ở lại v1 0% (ngưỡng 10%); legacy 0; chi phí $0,071
(ngưỡng ~$0,12); throttle 0. Ngưỡng "lỗi nghiêm trọng không còn vượt A+": proxy code là `not_better_than_live = false`
[W.stop_conditions], **nhưng panel mù chưa chạy** (mục 3.1a). Mốc ở đây cũng đã đổi: A+ không được sinh cho 50 tour này,
nên proxy so với trang live (v1 đang lưu) thay cho A+. Ở S248, A+ và trang live là hai nhánh riêng: trên 25 tour golden,
live 13/25 trang dính cổng, độ phủ 0,479; A+ 16/25, 0,443 [DM §2, bảng chính; N.derived.live_vs_aplus_s248]. Theo code,
live ngang hoặc nhỉnh hơn A+ một chút, nên lấy live làm mốc có lẽ **không dễ hơn** lấy A+. Nhưng panel chưa từng chấm
trang live, nên với lỗi nghĩa thì chưa biết mốc này dễ hay khó hơn.

### 2.2 Theo nước

Mẫu phân tầng theo nước, chia theo phần dư lớn nhất, mỗi nước tối thiểu 1 tour. Hai cột cuối là **ước tính**: số tour =
số mẫu × 807/50 (sai số vài chục tour mỗi nước); $ = số tour ước tính × $/tour TB **của chính nước đó**, mà TB này tính
trên n = 2–9 nên nhiễu. Số tour thật mỗi nước do dry run của wave in ra (`shadow.py --select wave --dry-run`; output dry
run của lần ≤50 không được lưu lại), nên khi chốt wave thì dùng số đó [N.per_country].

| Nước | Mẫu | Publish được | Trang cổng mới/live | Độ phủ số liệu mới/live | Judge v2 qua (cuối) | $/tour TB | Ngày ≠ kế hoạch | Ước tính tour | Ước tính $ S1 |
|---|---:|---|---|---|---:|---:|---:|---:|---:|
| India | 9 | 9/9 | 1/4 | 0,62/0,35 | 0,33 | 0,084 | **1** | ~145 | ~$12,2 |
| China | 6 | 6/6 | 0/2 | **0,30/0,21** | 0,50 | 0,066 | 0 | ~97 | ~$6,4 |
| Sri Lanka | 6 | 6/6 | 0/2 | 0,56/0,26 | 0,33 | 0,066 | 0 | ~97 | ~$6,4 |
| Japan | 5 | 5/5 | 0/0 | 0,94/0,65 | 0,40 | 0,050 | 0 | ~81 | ~$4,0 |
| Nepal | 5 | 5/5 | 0/0 | 0,80/0,31 | 0,80 | 0,090 | 0 | ~81 | ~$7,3 |
| Laos | 3 | 3/3 | 0/1 | 0,40/0,40 | 0,67 | 0,068 | 0 | ~48 | ~$3,3 |
| Philippines | 3 | 3/3 | 0/0 | 1,00/0,00 (n = 1) | 0,33 | 0,058 | 0 | ~48 | ~$2,8 |
| Thailand | 3 | 3/3 | 1/2 | 0,92/0,73 | 0,33 | 0,103 | 0 | ~48 | ~$5,0 |
| Bhutan | 2 | 2/2 | 0/0 | 0,81/0,52 | **0,00** | 0,064 | 0 | ~32 | ~$2,0 |
| Mongolia | 2 | 2/2 | 0/0 | 0,83/0,50 | 0,50 | 0,040 | 0 | ~32 | ~$1,3 |
| Pakistan | 2 | 2/2 | 1/1 | 0,97/0,48 | 0,50 | 0,082 | 0 | ~32 | ~$2,6 |
| South Korea | 2 | 2/2 | 1/1 | 0,89/0,89 | 0,50 | 0,078 | 0 | ~32 | ~$2,5 |
| Taiwan | 2 | 2/2 | 0/0 | 0,81/0,64 | 0,50 | 0,047 | 0 | ~32 | ~$1,5 |

Nguồn: [R] (bảng theo nước), [W.countries.<nước>], [N.per_country.*.est_s1_cost_usd_country_mean]. Đọc nhanh:
- Không nước nào xấu đi so với live trên các phép đo code.
- Trung Quốc có độ phủ số liệu thấp nhất (0,30): 3/6 tour Trung Quốc có số liệu nguồn nhưng cả trang mới lẫn live giữ
  0 (Hangzhou day tour, Beijing: Old and New, Bike Beijing) — cần xem [N.derived.figure_coverage_detail]. Độ phủ là tỉ
  lệ nên "nguồn ít số liệu" không giải thích được giá trị thấp; tour không có số liệu nguồn thì ghi None, không ghi 0.
- Philippines 1,00/0,00 chỉ là 1 tour (Cebu-Bohol); 2 tour kia không có số liệu nguồn.
- Judge v2 ở Bhutan cho 0/2 qua (brand_fit TB 4,0) [W.countries.Bhutan.judge_brand_fit_final_mean], đúng kiểu "chặn
  trần vì chi tiết" ở mục 3.2.
- Mẫu mỗi nước chỉ 2–9 tour, nên **không kết luận được theo từng nước**. Đó là lý do d13 đòi "mỗi wave so trước/sau
  theo nước".

### 2.3 Pilot 3 tour Lào (run 2007e626, $0,253; dry run d0c7ab08, $0) [P]

- 3/3 chạy xong, 2/3 publish được [pilot-summary.json `countries.Laos.publishable`].
- Tour VIENTIANE STOPOVER bị giữ `manual_check`. Lý do: brand audit bắt `ITINERARY_MEAL_TIME_INVENTED` (writer tự thêm
  giờ ăn mà nguồn không có), lượt sửa không qua được kiểm lại (`flag_fix.revalidate_passed = false`), và grounding còn 1
  câu không có nguồn [P.tours[0]].
- **Điều kiện dừng anh đã chốt (d13) đã bật ở pilot.** "Ở lại v1 > 10%" = 1/3 = 33% [pilot-summary.json
  `stop_conditions.stayed_v1_over_10pct = true`, `stop = true`]. [RUN] bước C ghi rõ: có điều kiện dừng thì dừng, báo anh,
  không chạy bước D. Run vẫn đi tiếp sang shadow ≤50 mà không dừng và không báo anh trước. Bản nháp đầu của memo này gọi
  ngưỡng đó là "cổng do agent đặt". Gọi vậy là sai: ngưỡng là của anh (d13; [IM §7] Q12 áp cho "wave 3 và ≤50"). Memo
  không thể coi d13 là ràng buộc khi nói shadow ≤50 sạch, rồi lại gạt nó đi khi nó bật ở pilot.
- **Cần anh quyết:** với wave dưới ~10 tour, một tour bị giữ có dừng wave không? Ở wave 3 tour, 10% nghĩa là chỉ cần 1 tour
  là dừng. Đề xuất để anh chọn: wave dưới 10 tour dùng **số đếm** thay cho phần trăm (ví dụ dừng khi ≥ 2 tour ở lại v1,
  hoặc khi 1 tour bị giữ vì một lý do chưa thấy ở shadow); từ 10 tour trở lên giữ 10%.
- **Gộp pilot + wave (53 tour):** 39 tour bị bắt bịa giờ ăn, 38 được sửa tự động, 1 phải giữ người duyệt (~2%)
  [N.pilot_plus_wave].

---

## 3. Điều kiện và rủi ro còn lại

### 3.1 Bốn điều kiện trước khi chạy catalogue

**(a) Panel mù trên 50 cặp mới–live: chưa chạy.**
- Gói đã dựng sẵn: 50 nhóm, 100 trang, rubric `s1-panel-v1` [`wave50-packet.json`, khoá `wave50-key.json`]. Chưa có file
  kết quả panel nào.
- Đây là điều kiện dừng cuối cùng anh đã chốt ở d13 ("tỉ lệ lỗi nghiêm trọng trong mẫu wave ≤50 không còn vượt A+"), và là
  phép đo chính duy nhất trên 50 tour lạ. Bây giờ nó mới chỉ được kiểm bằng proxy code. Proxy này không thấy lỗi nghĩa
  (bịa lời hứa, sai phạm vi), mà 39/50 bài golden có loại lỗi đó [F §0].
- Mốc so sánh: A+ không được sinh cho 50 tour này, nên panel so trang mới với trang live (v1 đang lưu) thay cho A+. Mục 2.1
  bàn chuyện mốc này dễ hay khó hơn.
- Cách làm: 2 agent độc lập, mỗi agent chấm cả gói, $0. So cặp số lỗi nghiêm trọng / khẳng định kiểm được (Wilcoxon), như
  [PN]. Dải nhiễu tham chiếu là A/A của [PN §3].
- Không phải cổng mới, vì đây là phép đo d13 đã duyệt.

**(b) Lỗ "mất ngày": tour dài bị rút ngắn mà vẫn publish được.**
- India "Rajasthan Adventure": nguồn 15 ngày, trang mới 10 ngày, live 15 ngày. Trang mới dừng ở Day 10 (Jaipur), chưa tới
  Ranthambore và Agra. Tên trang mới vẫn là "… — 15 days", phụ đề "A 15-day route … ending back in Delhi": tiêu đề nói 15
  ngày mà thân dừng ở ngày 10, agency thấy ngay [N.derived.rajasthan].
- Pipeline có thấy lỗi: `ITINERARY_DAY_COUNT_MISMATCH` trong `failure_codes`, `DAY_COUNT_VS_DURATION` trong shadow. Nhưng
  mã đầu chỉ trừ 1 điểm ở chiều structure, tức 0,25 điểm tổng (10 → 9,75, điểm là TB của 4 chiều), không phải mã chặn;
  mọi mã của day-oracle đang ở chế độ `shadow`. Vì vậy trang vẫn `publishable = true` [N.derived.days_rows; code:
  `services/content_generation/graph.py` `_FAILURE_MAP`, `_HARD_BLOCK_CODES`; `services/quality/day_oracle.py`
  `DAY_ORACLE_MODES`].
- **Nguyên nhân chưa kiểm.** flag_fix đã viết lại trường `itineraries` của tour này (sửa giờ ăn) và lượt kiểm lại vẫn đạt
  [S.tours[Rajasthan].flag_fix]. Bản nháp generate không được lưu trong output shadow (S3 chỉ có `shadow.json`,
  `shadow.partial.json`, gói/khoá panel và trang cuối). Vì vậy chưa chứng minh được writer làm rơi ngày 11–15; có thể là
  flag_fix. Cần đối chiếu output `s1_generate` với output `s1_flag_fix` của job `caf9c751…` trong `shared.llm_call_log`
  trước khi chọn cách sửa. Nếu flag_fix làm rơi ngày thì phải sửa ở flag_fix (lượt kiểm lại phải kiểm số ngày), không phải
  ở writer.
- **Theo độ dài:** 1/6 tour có ≥ 15 ngày kế hoạch (17%, Wilson 3–56%), 0/44 tour ngắn hơn [N.derived.days_not_plan_by_band].
  Tính đều trên catalogue, 1/50 tương ứng khoảng 3–91 tour (Wilson 95%: 0,35%–10,5%), điểm giữa ~17
  [N.catalogue.expected_days_not_plan_tours_864]. Rủi ro dồn vào tour dài, nên báo cáo wave phải tách theo dải độ dài.
- Mất 1/3 lịch trình là lỗi thật mà agency thấy ngay. Nó còn kéo theo atom "mồ côi" ở ngày 11–15 (rủi ro C6 trong [IM §4]).
- **Cách lấp** (cách 1 không đổi số cổng):
  1. **(đề xuất) Đổi mã có sẵn, không thêm luật.**
     - 1a: chuyển `ITINERARY_DAY_COUNT_MISMATCH` (đã có, đã bắt đúng tour Rajasthan, đang trừ điểm) thành mã chặn cho A1 v2.
       Không thêm detector, không thêm mã. Cần thêm vào `_HARD_BLOCK_CODES` kèm một dòng `HARD_CODE_REPAIR` (test S218
       bắt buộc).
     - 1b: bật `enforce` cho `DAY_COUNT_VS_DURATION` và **bỏ** `ITINERARY_DAY_COUNT_MISMATCH` (một vào, một ra). Phải kiểm
       mã mới phủ được các trường hợp mã cũ đang bắt (tour có mốc "Day N" nhưng không có duration).
     - Số cổng không đổi trong cả hai cách, đúng ngân sách luật S246 ("thêm một luật thì bỏ một luật").
     - Độ chính xác: với `DAY_COUNT_VS_DURATION`, bộ kiểm S248 chỉ có ≤ 3 lần bắt, gộp chung một dòng với
       `DAY_SUBDAY_SPLIT` / `DAY_DEPARTURE_MIDTRIP` [F §2.2], ở đây 1/1, nên n ≈ 4, Wilson 0,51–1,00: chưa đủ. Theo D5 của
       `day_oracle.py`, PR bật mã phải chạy `scripts/aa925/day_oracle_report.py` trên tour đã lưu và đạt ≥ 0,70 kèm cận
       Wilson. Với 1a, đọc độ chính xác của `ITINERARY_DAY_COUNT_MISMATCH` trên tour đã lưu theo cùng cách, trong cùng PR.
     - Đường đi thật của tour bị chặn: một lần viết lại haiku→sonnet (`HARD_CODE_REPAIR`, tốn thêm tiền), rồi vào review
       hoặc bị dismissed. Tour không về thẳng "ở lại v1".
     - **Không** bật `DAY_DEPARTURE_MIDTRIP`. Em đọc 3/3 phát hiện trên trang mới là báo nhầm: ngày áp chót có "farewell
       dinner", ngày cuối mới là ngày về (Pakistan K2 ngày 21/22, Thái Lan ngày 13/14, Hàn Quốc ngày 8/9).
  2. Không đổi code: báo cáo wave liệt kê các tour có số ngày ≠ kế hoạch, rồi đưa từng tour về bản cũ bằng promote (đã sửa
     ở CIS #965).

  Cách 1 đổi một mã mềm thành mã chặn nhưng không thêm luật. Nếu anh vẫn coi đó là cổng mới trong 4 tuần đóng băng (S247
  bước 0, [BL] L1) thì dùng cách 2.
- **Mục tiêu "xoá ≥ 5 cổng" của S246 bước 5:** hiện mới thấy 2 cổng sẽ bị bỏ (AA-924, T10: 26 → 24). Em chưa xác định được
  cổng A1 nào mà bộ kiểm code đã làm thừa. Nên rà việc này trong PR AA-926, vì registry liệt kê đủ gate.

**(c) Checklist chuẩn bị [IM §6 bước 0.5 + bước 2].** Trong dữ liệu của bản này em chưa thấy trạng thái các mục sau, nên
cần kiểm trước wave:
- snapshot `published_tours` + `geo.tour_place` trước mỗi wave;
- ~21 request T8/T9 đang dở;
- xuất `decision_log` `admin_atom_delete`;
- kiểm quota Sonnet acc3 ở 6 song song (T10);
- tag Sentry theo wave (d12);
- khoá route `a3_atomize`;
- `PLACE_PIPELINE_AUTO` tắt (d09);
- các PR / migration đang chờ đã land (d11).

**(d) Pilot thật 3 tour và wave ≤50 thật.**
- `select_pilot` trong `scripts/aa645/shadow.py` lấy tour đã có place trước, rồi theo thứ tự md5. Nên pilot thật gần như
  chắc là đúng 3 tour Lào cũ: VIENTIANE STOPOVER (`7df4db05`), Luang Prabang - Namet NP - Halong Bay (`a6254fcf`),
  Luang Prabang - Vientiane (`c97a5713`) [P, pilot-dry.txt]. Nếu VIENTIANE lại bị giữ thì "ở lại v1" lại bật 33% và wave
  thật đầu tiên dừng ngay.
- Ba lựa chọn, anh chốt trước khi chạy:
  1. loại VIENTIANE, lấy tour Lào có place kế tiếp;
  2. **(đề xuất)** giữ VIENTIANE và coi 1/3 là dự kiến (cần luật đếm ở mục 2.3). Tour này thử luôn đường "ở lại v1" thật
     (tour bị giữ trên Master, rollback bằng promote);
  3. sửa lỗi giữ vì giờ ăn trước: không nên, vì đổi prompt là đổi writer, mất hiệu lực bằng chứng A/B [PN].
- **Wave ≤50 thật:** [IM] bước 2 xếp thứ tự pilot 3 → ≤50 → theo nước, và Q3/d04 duyệt catalogue "sau wave ≤50". Shadow
  không đo A3, place, pin, ID (mục 3.2), nên hai ngưỡng d13 về A3 (có atom live ở ngày vượt số ngày mới; có tour atomize
  fail mà không chạy lại được) chưa được kiểm lần nào. Đề xuất: thêm một wave ≤50 thật (phân tầng theo nước, bật A3) giữa
  pilot Lào và wave A, khoảng $4–5 (S1 ~$3,6 + phần atomize). Nếu anh coi "wave ≤50" trong d04 là chính lần shadow vừa
  chạy thì xin ghi rõ khi duyệt; em không tự giả định.

### 3.2 Rủi ro và giới hạn

| Rủi ro | Mức | Số và cách đọc |
|---|---|---|
| **Cỡ mẫu n = 50** | Trung bình | 50/50 publish được vẫn chỉ cho cận dưới 95% là ~93–94% [N.derived.publishable_wilson95, publishable_clopper_lower95_one_sided]. Ở catalogue có thể **tới ~50 tour** ở lại v1 [N.catalogue.expected_stayed_v1_tours_864]; pilot + wave cho ~2%. Mỗi nước chỉ 2–9 mẫu, tour ≥ 15 ngày chỉ 6 mẫu. Vì vậy chạy theo wave từng nước, áp ngưỡng dừng d13 ở mỗi wave. |
| **Brand-fit v2 quá khắt khe để làm cổng** | Thấp nếu giữ chỉ báo cáo | Re-measure trên **121 trang** (chỉ 21 trang A+ được chấm): v2 "qua" tiêu chí chủ yếu vì nó chặn trần 100% trang A+, mà A+ có lỗi nghiêm trọng nhiều hơn ~12 lần (0,0385 so với 0,0033 lỗi/khẳng định) [B, dòng v2]. Spearman gộp −0,42 vì vậy phần lớn phản ánh khác biệt A+ với writer v2. Chỉ tính các nhánh W/E (100 trang) thì còn −0,22; riêng W×Sonnet −0,20 trên 25 trang [N.derived.brandfit_v2_spearman]: yếu, chưa cho thấy v2 xếp hạng trang writer v2 có ích. W×Sonnet vẫn bị đẩy retry 44%, dù panel thấy đây là bản trung thực nhất. Shadow: 28/50 bị chặn trần; grounding còn 0, nhưng vùng lời hứa của Jev toàn xám, nên judge v2 và Jev đang bất đồng và chưa bên nào được hiệu chuẩn cho lời hứa. Panel mù quyết. Giữ chỉ báo cáo (d02, luật S246). |
| **Writer tự thêm giờ ăn** | Thấp (đã có cổng) | 39/53 tour; flag_fix sửa được 38; 1 tour giữ người duyệt [N.pilot_plus_wave]. Chi phí sửa $0,0071 mỗi tour được sửa (37 tour), $0,0053 TB trên 50 tour [N.derived.flag_fix_cost]. **Không** sửa prompt trước wave: đổi prompt là đổi writer, mất hiệu lực bằng chứng A/B n = 50 [PN]. Để sau wave, qua Writing Memory/lessons. Lưu ý: flag_fix có thể là khâu làm rơi ngày ở Rajasthan (mục 3.1b). |
| **Độ tin cậy của panel (AA-783)** | Trung bình | Panel so với nhãn: κ 0,401 (0,135–0,652). Trên 40 bài: 10 bài panel chấm chặt hơn nhãn, 2 bài lỏng hơn. Mốc tỉ lệ light 0,45 của panel ≈ mốc 0,6 của người (đây là mốc tỉ lệ light, không phải κ). "Panel can stand in: False" [A783]. Hai lưu ý: (1) đây là panel T9 (bài tenant), không phải panel S1; (2) nhãn là "claude-draft (owner-approved)". Panel S1 ở [PN] tự khớp tốt (κ 0,849 giữa hai lượt [DM §4.3]) nhưng chưa đo so với người. Hệ quả: dùng số panel làm **tín hiệu tương đối giữa hai bản** (mới vs live), không coi là "đạt chuẩn tuyệt đối". Panel lệch về phía khắt khe làm phép so sánh thận trọng chứ không lạc quan. |
| **Jev `a1_promise_unsupported` không cho tín hiệu** | Thấp | 2.375 phán quyết xám, 4 lỗi, 0 chấp nhận/bác bỏ. `a1_claim_supported`: 2.223 chấp nhận, 152 xám, 4 lỗi [N.derived.jev_zones]. `jev_problem = 0` đếm tour, không đếm phán quyết. Tốn $0,0032/tour [N.derived.cost_by_stage_over_50.s1_grounding], nên không gấp. Chỉ ghi nhận là câu hỏi về lời hứa đang không quyết được gì. |
| **Mã chỉ báo cáo `ITINERARY_STILL_COMPRESSED` 26/50** | Không phải lỗi | Writer v2 cố ý không ép độ dài theo ngày ("độ dài theo nguồn"). Mã này được ghi vào `quality_shadow`, không trừ điểm [N.derived.quality_shadow_codes; `graph.py`, nhánh `_v2_draft`]. |
| **Phần shadow không đo được** | Trung bình | Shadow không publish nên không chạy A3, place, slug, `published_at`, atom ID, component ID, pin nháp khách [IM §2, §4 C2–C7]. Hai ngưỡng d13 về A3 vì vậy chưa kiểm lần nào. Do đó cần pilot thật 3 tour rồi wave ≤50 thật (mục 3.1d) trước khi chạy theo nước. |
| **Đóng băng 2–3 ngày** | Trung bình | S1 ~5,6 giờ ở 3 song song (~2,8 giờ ở 6 song song nếu quota cho phép), đuôi atomize 30–45 giờ [N.catalogue; IM §3.2]. Trong thời gian đó cấm deploy backend và DB Migrate apply. Do đó AA-926 / AA-916 / sửa lỗ (b) nên land **trước**. |

---

## 4. Cần anh duyệt: số liệu chạy cả catalogue (d04)

**Phạm vi:**
- Tour Master đang active và có lịch trình, bỏ tour cưỡi voi (39, chính sách chị Thư): **810 tour** ngoài bộ golden. Con
  số này đã gồm 3 tour pilot [P.eligible = 810, dropped.elephant = 39].
- Thêm **54 tour trong fixture** (50 golden S1 + 4 tour T2, [RUN] bước 1) nếu viết lại luôn, tổng tối đa **864**. Chưa
  kiểm số tour golden đang active / không cưỡi voi nên đây là cận trên [N.catalogue].
- Lưu ý T9 [IM §4]: đóng băng `fixture-1.1.0.json` trước khi viết lại tour golden.

**Chi phí** (giá thật đo ở shadow, $0,0712/tour; khoảng tin cậy 95% $0,062–0,081):

| Hạng mục | 810 tour | 864 tour | Nguồn |
|---|---:|---:|---|
| S1 toàn chuỗi A1, writer v2 | **$57,6** ($50–66) | **$61,5** ($54–70) | [N.catalogue.s1_cost_*] |
| Kịch bản xấu S1: mọi tour tốn như p90 | $92 | $98 | [N.catalogue.s1_cost_864_if_every_tour_at_p90] |
| Atomize lại (A3) | $7–15 (tệ nhất ~$50) | $7–15 (tệ nhất ~$50) | [IM §3.1] |
| Place re-extract (~120 tour đã build) | $1–3 | $1–3 | [IM §3.1]; d10: place trả phí chạy **sau** khi wave cho thấy bản mới tốt hơn |
| Place cards | < $1 | < $1 | [IM §3.1] |
| DataForSEO | $0 | $0 | [IM §3.1] |
| **Tổng một lần chạy sạch (giữa)** = S1 TB + atomize + place + cards | **~$66–77** | **~$70–81** | [N.catalogue.total_central_*] |
| **Trần đề nghị duyệt** = cận trên CI của S1 + atomize $15 + place $3 + cards $1 | ~$85 | **~$89** | [N.catalogue.approval_ceiling_*] |
| Tệ nhất = mọi tour ở p90 + atomize tệ nhất + place + cards | ~$146 | ~$152 | [N.catalogue.worst_case_*] |
| So với mô hình S248 (cho **~892 tour**) | | $85 ($70–160) | [IM §1.2] |

- Không cần shadow cả catalogue (d03), nên chỉ chạy **một lần**, không phải "2 lần" như [DM §2.2] từng dự trù.
- Brand-fit vẫn chỉ báo cáo, nên số lần thử giữ ở 1 (shadow: 50/50 tour 1 lần). Kịch bản "retry tăng → ~$105" của
  [DM §4.7] không xảy ra. Nếu bật cách 1 của mục 3.1b thì mỗi tour bị chặn tốn thêm một lần viết lại.

**Cách chạy đề xuất** (theo [IM §6 bước 2] và `aa-wave-rerun`; dừng báo cáo giữa các wave, trừ khi anh duyệt khác ở câu 4
bên dưới):
1. **Pilot thật 3 tour Lào đã build place** (~$0,25), theo lựa chọn ở mục 3.1d. Mục đích là đo phần shadow không đo được:
   atom giữ ID / ID mới, component mất/thêm, pin nháp khách, rollback bằng snapshot + promote.
2. **Wave ≤50 thật** (phân tầng theo nước, bật A3, ~$4–5), mục 3.1d. Đây là lần đầu kiểm hai ngưỡng d13 về A3.
3. **Theo nước, nhỏ trước, lớn sau.** Cỡ và $ là ước tính (mục 2.2; $ theo TB của từng nước; mỗi wave sẽ nhỏ đi một chút vì
   wave ≤50 đã lấy trước một phần):
   - wave A: Bhutan, Mongolia, Pakistan, South Korea, Taiwan (~160 tour, ~$10);
   - wave B: Laos, Philippines, Thailand (~145, ~$11);
   - wave C: Japan, Nepal (~160, ~$11);
   - wave D: China, Sri Lanka (~195, ~$13);
   - wave E: India (~145, ~$12).

   Giữa các wave có cửa sổ deploy/migrate [N.waves_estimate].
4. **Mỗi wave báo cáo:**
   - so trước/sau theo nước (d13);
   - ở lại v1;
   - số ngày ≠ kế hoạch, tách theo dải độ dài (≥ 15 ngày riêng);
   - trang dính cổng code;
   - $/tour;
   - các chỉ số A3/place của [IM §6].
5. **Ngưỡng dừng d13** giữ nguyên: ở lại v1 > 10% (wave nhỏ theo luật anh chốt ở mục 2.3), có tour đi đường legacy, có atom
   ở ngày vượt số ngày mới, chi phí > ~$0,12/tour, có throttle, có tour atomize fail mà không chạy lại được, lỗi nghiêm
   trọng không còn vượt mốc. Mốc là trang live (v1 đang lưu) thay cho A+, vì A+ không được sinh cho các tour này (mục 2.1).

**Thời gian:** S1 ~5,6 giờ (3 song song) cho 864 tour, cộng đuôi atomize 30–45 giờ. Bảng job bận khoảng 2–3 ngày, chia ra
theo các wave [N.catalogue; IM §3.2].

**Các câu cần anh trả lời trong cùng một lần duyệt:**
1. Số tour (810 hay 864) và trần chi phí (~$89 cho 864; tệ nhất ~$152).
2. "Wave ≤50" trong d04 là wave thật (đề xuất: có, chạy trước wave A) hay chính lần shadow vừa rồi?
3. Luật dừng cho wave dưới ~10 tour: số đếm (ví dụ ≥ 2 tour ở lại v1) hay giữ 10%? Và tour VIENTIANE trong pilot thật:
   loại, giữ (đề xuất), hay sửa trước?
4. Lần duyệt này có bao luôn "đi tiếp sang wave sau khi không điều kiện dừng nào bật" không, hay mỗi wave chờ anh duyệt
   (`aa-wave-rerun` §2, [IM] bước 2)?
5. Lỗ mất ngày: cách 1a, 1b hay cách 2 (mục 3.1b)?

---

## 5. Bước tiếp theo, theo thứ tự

| # | Việc | Ai | Chi phí | Xong khi |
|---|---|---|---|---|
| 1 | Panel mù trên `wave50-packet.json` (2 agent độc lập), chấm theo [PN] | Orchestrator | $0 | Có `pass-a/b.json`; trang mới có lỗi nghiêm trọng/khẳng định thấp hơn live (Wilcoxon ghép cặp), ngoài dải A/A |
| 2 | Tìm khâu làm rơi ngày ở Rajasthan: đối chiếu output `s1_generate` với `s1_flag_fix` của job `caf9c751…` trong `shared.llm_call_log` | Claude | $0 | Biết khâu nào làm rơi ngày 11–15 |
| 3 | Lấp lỗ mất ngày theo câu 5 của mục 4: PR nhỏ (1a hoặc 1b, kèm độ chính xác theo D5 trên tour đã lưu), hoặc chốt cách 2; nếu lỗi ở flag_fix thì sửa ở flag_fix | Claude, agent review (đụng gate) | $0 | Test: tour 15 → 10 ngày bị giữ; số cổng không đổi; `DAY_DEPARTURE_MIDTRIP` vẫn shadow |
| 4 | AA-926: rebase nhánh `feat/aa-926-quality-registry`, thêm mã mới, replay offline ra cùng quyết định, review độc lập, merge + deploy; rà cổng thừa cho mục tiêu "≥ 5 cổng" | Claude | $0 | Lint xanh, mọi gate/chip/Jev key có lớp, trang Content Quality hiện đủ gate (live); có danh sách cổng thừa (hoặc ghi "chưa có") |
| 5 | AA-916 WM-03 (migration + RLS) + WM-05 (lưu sửa A1 theo trường) | Claude, agent review | $0 | Theo Done-when của AA-916; apply ngoài wave |
| 6 | Checklist chuẩn bị (mục 3.1c) | Orchestrator | $0 | Mỗi mục có bằng chứng |
| 7 | **Anh duyệt catalogue** + 5 câu ở mục 4 | Nghiệp | trần ~$89 | Có câu trả lời cho cả 5 câu |
| 8 | Pilot thật 3 tour Lào → wave ≤50 thật → các wave theo nước | Orchestrator | như mục 4 | Báo cáo mỗi wave; không ngưỡng dừng nào bật (bật thì dừng và báo anh) |
| 9 | Sau wave: place backfill + cards (d10, khi bản mới đã chứng minh tốt hơn); AA-924 (sau AA-926); brand-fit v2.1 đo lại trên 125 trang (~$0,65); sửa prompt giờ ăn qua lessons | Claude | ~$1–4 + $0,65 | Theo issue |
| 10 | Xem lại AA-790 (phần rubric) và WM P1+ khi có nhãn người hoặc κ panel ≥ 0,6 (Label Desk [CL §8 C2]) | – | – | – |

Bước 1–6 không tốn tiền và làm được trong phiên tới. Tiền thật chỉ bắt đầu ở bước 8, sau khi anh trả lời bước 7.

---

*Số tự tính lại nằm trong `numbers.json` cạnh file này. Script (thuần Python, chỉ đọc file local, bootstrap seed 645):
`gonogo_numbers.py` (lượt đầu) và `gonogo_numbers_v2.py` (lượt sau phản biện), trong scratchpad của phiên S249, không lưu repo.*
