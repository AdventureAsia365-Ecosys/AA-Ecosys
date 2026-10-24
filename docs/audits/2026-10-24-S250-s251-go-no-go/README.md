---
id: PROD-01-s1-go-no-go-final
title: "S1-first step 5: final written go/no-go (S250) after the shadow ≤50, the blind panel and the real waves"
description: "Bản go/no-go cuối cho AA-926/916/924/790, Writing Memory P1+, brand-fit và writer v2 làm mặc định A1: đóng 4 điều kiện của bản S249 bằng bằng chứng."
type: report
status: draft
owner: nghiep
audience: [engineer, cto, agent]
applies_to: [cis-core]
last_reviewed: 2026-10-24
review_every_days: 180
related: [AA-645, AA-926, AA-916, AA-924, AA-790, PROD-01-s1-go-no-go]
---

# S1-first bước 5: go / no-go cuối (S250)

Bản tư vấn cho Nghiệp · S250 · 24/10/2026 · Tác nhân: Claude Code · Refs AA-645, AA-926, AA-916, AA-924, AA-790

Bản này nối tiếp bản S249 ([../2026-10-24-S249-s1-go-no-go/README.md](../2026-10-24-S249-s1-go-no-go/README.md)) và
không lặp lại bảng số đo của bản đó. Nó ghi 4 điều kiện đã đóng, chốt từng hạng mục và đếm cổng. Chỉ đọc dữ liệu có
sẵn, $0. Số mới nằm trong [`numbers.json`](numbers.json) cạnh file này (ảnh chụp ledger lúc 12:55Z).

**Quyết định đã ghi nhận:** GO cho **AA-926, AA-924, AA-916, AA-790** theo lần duyệt chung của anh ở S250 ("duyệt luôn
theo kế hoạch"). AA-790 GO theo cách tách ở mục 3 (6a, 6b): không thêm cổng nào trong 4 tuần đóng băng.

## English summary (for Linear)

All four S249 conditions are closed.
(a) The blind panel on the 50 shadow pairs ran twice: new 0.0015 / 0.0004 vs live 0.051 / 0.053 serious errors per
checkable claim; 42/0 and 41/0 tours better/worse.
(b) The day-loss hole is fixed in CIS #976: meal false positive removed, `days_kept` repair-contract invariant,
`ITINERARY_DAY_COUNT_MISMATCH` hard on v2 drafts only; gate count unchanged; replay 1 → 0 short-published tours.
(c)+(d) Nghiệp approved the catalogue (d04) with a small-wave rule and a $120 cap. The real pilot (3/3) and the real
wave ≤50 (50/50 published and atomized, 0 stop conditions, $3.84) passed.
Country waves Mongolia, Pakistan, South Korea, Bhutan and Taiwan closed with 0 stop conditions. Ledger at writing
time: 7 closed waves, 162 / 810 tours, 0 stayed on v1, gate pages 61 → 11, $11.89 / $120 ($0.073 per tour);
Thailand was running and is not counted.

Decisions (Nghiệp's S250 blanket approval covers AA-926, AA-924, AA-916 and AA-790):
- S1 catalogue rewrite: GO (running).
- Writer v2 as the A1 default after the last wave: GO (new item).
- AA-926: GO now, merge in a CIS deploy gap.
- AA-916: GO, WM-03 (CIS migration **277**) + WM-05 first; reason codes use registry constants.
- AA-924: GO after AA-926, before AA-790.
- AA-790: GO, split. (6a) The post-repair integrity check is a new invariant in
  `services/quality/repair_contract.py` that delegates its detectors to `services/acp_content_writing/text_integrity`
  (`hygiene.integrity_problems` plus the new split-paragraph and dangling-tail detectors). It reverts the broken edit
  and logs `degraded: repair_contract`; it is not a gate. (6b) The tenant-voice rubric ships as an **offline scorer**
  (`voice_rubric.py` + replay script, results to `quality_shadow` / admin flags), not as a ledger or registry gate,
  during the gate freeze. A blocking rubric gate stays NO-GO until κ ≥ 0.6 on human labels and the freeze ends (~19/11).
- Writing Memory P1+: after the waves, with P0 data. Brand-fit v2: report-only. AA-765 / AA-900: unblocked.

Gate count: 3 A1 gates stop deciding on v2 drafts + 2 T10 gates merged by AA-924 = 5. This holds only if AA-790 adds
no gate (6b above). AA-926's registry must confirm the list.

## 1. Bốn điều kiện của bản S249: đã đóng

| # | Điều kiện (S249 §3.1) | Trạng thái | Bằng chứng |
|---|---|---|---|
| a | Panel mù trên 50 cặp mới–live | **Đóng** | [panel50.md](../2026-10-24-S249-s1-go-no-go/panel50.md): lượt a 4/2.599 = 0,0015 so với 145/2.835 = 0,0511; lượt b 0,0004 so với 0,0530; theo tour 42/0 và 41/0 (Wilcoxon p ≈ 2·10⁻⁸); trang hard-fail 1 so với 20; xếp hạng mới hơn 49 và 48/50 [`numbers.json` → `panel50`]. Lưu ý giữ nguyên: panel khắt hơn nhãn người (AA-783 κ 0,40), nên đây là so sánh tương đối. |
| b | Lỗ "mất ngày" | **Đóng** | CIS #976 (969d221b, đã deploy trước pilot thật). Nguyên nhân là flag_fix (Haiku) viết lại cả lịch trình sau một báo nhầm giờ ăn, không phải writer. Sửa: (1) dòng bữa ăn chép đúng từ nguồn không còn bị coi là bịa; (2) bất biến `days_kept` trong `services/quality/repair_contract.py`: lần sửa nào làm mất, thêm hay đánh số lại ngày thì bị hoàn tác; (3) cách 1a: `ITINERARY_DAY_COUNT_MISMATCH` chặn Master chỉ với bản nháp v2 (`graph.V2_HARD_BLOCK_CODES`). Không thêm mã, không thêm detector. Replay $0 trên 50 bản ghi: publish thiếu ngày 1 → 0; lần viết lại cả lịch trình 34 → 26 [`numbers.json` → `dayloss_fix_cis_976`]. Wave thật: `day_loss` = 0 ở cả 7 wave đã đóng. |
| c | Checklist chuẩn bị [IM §6] | **Đóng** | Duyệt d04 mục 4 (comment AA-645 24/10 05:32): snapshot RDS mỗi wave (`aa-cis-dev-db-pre-s1-*`), `PLACE_PIPELINE_AUTO` tắt, không deploy backend CIS trong wave, tag Sentry theo wave, kiểm quota acc3. Mỗi wave có file snapshot/close trong `realpilot/`; `place_pipeline_ran` = false ở mọi wave. |
| d | Luật dừng wave nhỏ + tour Lào bị giữ | **Đóng** | Anh chốt: wave < 10 tour dừng khi ≥ 2 tour ở lại v1 hoặc có bất kỳ lỗi nặng nào; từ 10 tour giữ luật 10%. Pilot thật 3 tour Lào: 3/3 publish, VIENTIANE không bị giữ (lần này flag_fix sửa được giờ ăn), 0 điều kiện dừng, $0,27. |

## 2. Wave thật tới lúc viết

Nguồn: `cw_ledger.py` (in ra "country waves: 109 tours $7.7886; running total $11.89 / $120"), file `-d13.txt`,
`-report.json`, `-cost.json` của từng wave [`numbers.json` → `wave_ledger`].

| Wave | Tour | Ở lại v1 | Trang dính cổng trước → sau | Độ phủ số liệu | Brand fit (chỉ báo cáo) | Chi phí |
|---|---:|---:|---|---|---|---:|
| Pilot thật (Lào) | 3 | 0 | 2/3 → 0/3 | 0,452 → 0,541 | 7,67 → 7,33 | $0,268 |
| Wave ≤50 (13 nước) | 50 | 0 | 13/50 → 4/50 | 0,415 → 0,672 | 7,58 → 7,56 | $3,839 |
| Mongolia | 13 | 0 | 9/13 → 0/13 | 0,724 → 0,781 | 7,92 → 8,00 | $0,836 |
| Pakistan | 14 | 0 | 5/14 → 2/14 | 0,477 → 0,606 | 7,57 → 7,86 | $1,277 |
| South Korea | 26 | 0 | 15/26 → 3/26 | 0,480 → 0,698 | 7,58 → 8,31 | $2,377 |
| Bhutan | 27 | 0 | 9/27 → 0/27 | 0,446 → 0,843 | 7,56 → 6,96 | $1,753 |
| Taiwan | 29 | 0 | 8/29 → 2/29 | 0,481 → 0,598 | 7,79 → 8,76 | $1,546 |
| **Luỹ kế (7 wave đã đóng)** | **162 / 810** | **0** | **61 → 11** | | | **$11,89 / $120** |

- Không wave nào bật điều kiện dừng. Mọi wave: Jev chạy đủ, 0 mất ngày, 0 đường lịch trình cũ, 0 rò tên thương hiệu,
  0 atomize lỗi. Không tour nào phải chờ duyệt.
- Chi phí trung bình $0,073 mỗi tour (cả S1 và A3), dưới trần mô hình $0,12.
- Wave ≤50: lần kiểm giữa chừng (`aa645-w50-report.txt`, trước khi A3 chạy xong) có `stop = true` vì tour chưa atomize;
  lần kiểm cuối (`aa645-w50-report2.txt`) là `stop = false`. Bảng dùng lần kiểm cuối.
- Wave Thailand bắt đầu 12:25Z và đang chạy lúc viết, nên không tính. Các wave sau cập nhật trong báo cáo AA-645.

## 3. Quyết định theo hạng mục

| # | Hạng mục | Quyết định | Lý do | Điều kiện / cách làm |
|---|---|---|---|---|
| 1 | Viết lại S1 cả catalogue bằng writer v2 | **GO (đang chạy)** | Anh đã duyệt (d04 + checkpoint 2); mục 1 + 2. | Giữ luật dừng; báo cáo từng wave kèm chi phí; khi xong: báo cáo tổng, khôi phục công tắc. |
| 2 | Writer v2 làm **mặc định** cho A1 (tour mới, sau wave cuối) | **GO (đề xuất mới)** | Đây là bước 4 của kế hoạch S246 ("nối nhánh thắng vào đường S1"). Theo kế hoạch khôi phục hiện tại, sau wave cuối worker về revision không có `S1_WRITER_V2` và route `s1_generate` về Haiku, nên tour mới lại được viết bằng v1, trong khi panel cho thấy v1 có lỗi nghiêm trọng cao hơn ~35–100 lần. | Một PR nhỏ của AA-645 sau wave cuối: đưa flag vào cấu hình chuẩn của worker thay vì revision tay, và route `s1_generate` = sonnet-5-5 (acc3). T2 không đổi. Chi phí ~$0,07 mỗi tour mới. Không thêm cổng. |
| 3 | AA-926 registry (nhánh đang giữ) | **GO ngay** | Không thêm cổng: chỉ thêm sổ đăng ký, một file ngưỡng và lint. Điều kiện S246 "S1 khá lên thật trước" đã đạt (mục 1a). Dùng registry để đếm cổng (mục 4). | Rebase lên main (84 commit; xung đột chắc chắn ở `services/quality/__init__.py` và `graph.py`). Đăng ký thêm các mã mới: `ITINERARY_DAY_COUNT_MISMATCH` hard ở v2 và soft ở v1/T2; `degraded: repair_contract` (`days_kept`); các mức chặn trần của brand-fit v2; mã chỉ báo cáo v2 (`ITINERARY_STILL_COMPRESSED`, `DFS_INTENT_UNDERUSED`, `META_CUT_SIGNATURE`); mã day-oracle (`DAY_*`, `DAY_CHECK_SKIPPED`) với chế độ shadow/enforce; `ITINERARY_MEAL_TIME_INVENTED`, `HIGHLIGHTS_OPTIONAL_LANGUAGE`; mã `s1_checks`. Sinh lại snapshot gate và chạy test tương đương ra cùng quyết định. Lint: số cổng không tăng. Cần review độc lập vì PR đổi `ci.yml`. Merge và deploy trong khoảng nghỉ giữa wave (G2), **trước** AA-924, AA-790 và AA-916 vì cả ba sửa `service.py`. |
| 4 | AA-916 Writing Memory P0 | **GO** | Đây là phần WM duy nhất kế hoạch S246 giữ ở bước 5. Admin sửa tay tour v2 sẽ là tín hiệu thật đầu tiên. | WM-03 (migration CIS **277** `shared.writing_signal`, RLS + FORCE, xoá được) cộng WM-05 (lưu sửa A1 theo trường) làm trước; WM-04/06/07/08 sau. Mã lý do (`suggested_reason`) phải dùng hằng của registry AA-926, không viết literal tên cổng (lint AA-926 sẽ chặn). Cần review độc lập (migration + RLS). DB Migrate apply chỉ khi không có wave mở (G3). Phần sửa vòng thử T9 trong `service.py` (S2) đi **sau** AA-790 phần 6a, vì hai việc sửa cùng một vòng lặp. |
| 5 | AA-924 mức độ theo vi phạm + gộp cổng | **GO, sau AA-926** | Bớt cổng T10 26 → 24, góp vào mục tiêu bước 5. | Replay trên bài S234 + golden phải ra cùng quyết định passed/held, hoặc giải thích từng khác biệt. Làm trước AA-790, và báo số cổng sau cả hai. Ưu tiên thấp (T-series, tenant giả). |
| 6a | AA-790 phần "kiểm toàn vẹn sau sửa" (câu mồ côi, đoạn bị tách, đuôi câu cụt) | **GO** | Chạy bằng code và chỉ hoàn tác lần sửa hỏng, không giữ bài, nên không phải cổng. Cùng cơ chế với `days_kept`. | Viết thành **một bất biến mới trong `services/quality/repair_contract.py`**. Bất biến này không tự dò lỗi mà gọi detector ở `services/acp_content_writing/text_integrity` (`hygiene.integrity_problems` có sẵn, thêm detector đoạn bị tách và đuôi câu cụt). Áp cho đường sửa T3/T10 và các bước sửa tất định trong `service.py` (`hygiene.autofix`, `add_family_caveats`, bỏ FAQ, `fix_trip_facts`, `length_trim.trim_to_band`). Khi vi phạm: hoàn tác bước đó, ghi lý do, ghi `degraded: repair_contract`. Không thêm mục nào vào ledger cổng hay registry. |
| 6b | AA-790 phần rubric giọng tenant | **GO dạng chấm offline; cổng chặn: NO-GO lúc này** | Cổng chặn chưa sẵn sàng về kỹ thuật: κ panel–nhãn 0,401 (0,135–0,652) < 0,6; nhãn là bản nháp của Claude; và đây là cổng LLM mới trong lúc đóng băng 4 tuần (tới ~19/11). | Trong lúc đóng băng, AA-790B ship như **bộ chấm offline**: `voice_rubric.py` cộng script replay, kết quả ghi vào `quality_shadow` hoặc cờ admin; **không** đăng ký vào `taxonomy.yaml`/registry, không vào ledger cổng T10, nên số cổng của AA-924 không đổi. Đăng ký thành cổng (shadow rồi enforce) chỉ sau khi hết đóng băng và có nhãn người (Label Desk) với κ ≥ 0,6. Khi tới lúc đó, đề xuất tách thành issue riêng (hỏi anh trước khi tạo). |
| 7 | Writing Memory P1+ (AA-917…923) | **Chưa** | Cần dữ liệu P0. | Xem lại khi wave catalogue xong và có ≥ vài chục tín hiệu WM-05. |
| 8 | Brand-fit v2 làm cổng A1 | **Giữ chỉ báo cáo** | Brand fit đi hai chiều giữa các wave (Bhutan 7,56 → 6,96; Taiwan 7,79 → 8,76; wave ≤50 7,58 → 7,56), trong khi panel và cổng code đều thấy bản mới tốt hơn rõ. Hai cột trước/sau còn dùng hai rubric khác nhau (v1 và `a1-voice-v2/1`). Rubric chưa đo đúng thứ cần đo. | v2.1 (tách nền địa danh đúng khỏi lời hứa về chuyến đi) để sau wave. |
| 9 | AA-765, AA-900 (đang chờ "sau go/no-go") | **Mở khoá** | AA-765 là refactor gateway (gộp judge client, chuyển dispatch T11). AA-900 là tài liệu LLM ops, đánh số prompt và một bước eval thủ công khi phát hành prompt. Không việc nào thêm cổng nội dung. | Theo thứ tự lane L1, sau AA-926. Nếu AA-900 định thêm một cổng trong pipeline thì phần đó chờ hết đóng băng. |

## 4. Mục tiêu "xoá ≥ 5 cổng" (S246 bước 5)

- **A1, bản nháp v2: 3 cổng không còn quyết định gì** (nguồn: CIS main 85f13ba8):
  - brand-fit retry: `A1_V2_BRAND_FIT_GATE` chưa đặt, judge v2 chỉ chặn khi biến này = `enforce` (`judge_node.py`);
  - `ITINERARY_STILL_COMPRESSED` (tỉ lệ độ dài theo ngày);
  - `DFS_INTENT_UNDERUSED`.

  Hai mã sau chỉ ghi vào `quality_shadow` qua `_v2_report` trong `graph.py`, không trừ điểm.
- **T10: 2 cổng bị gộp qua AA-924** (F15_voice_warn → F15_voice; F2_banned_patterns + F2_brand_forbidden + danh sách
  stock của F15 → một cổng lexicon).
- Cộng là **5**.
- Lưu ý: 3 cổng A1 vẫn còn hiệu lực trên đường v1 (54 tour golden, 39 tour cưỡi voi, T2). Chúng chỉ bị bỏ hẳn khi mục 2
  xong và đường v1 của A1 thôi dùng. PR AA-926 phải in danh sách này từ registry; lệch thì ghi lại ở đây.
- Số cổng trong registry không tăng trong 4 tuần đóng băng. #976 không thêm mã: nó đổi lớp một mã có sẵn, chỉ với bản
  nháp v2. Con số 5 đứng được vì AA-790 không thêm cổng: 6a là bất biến của hợp đồng sửa, 6b là bộ chấm offline (mục 3).

## 5. Thứ tự làm (không tốn tiền trừ wave đã duyệt)

1. Các wave AA-645 chạy tiếp theo driver. PR nào cần deploy backend CIS hay DB Migrate thì chèn vào khoảng nghỉ giữa
   wave (G1–G4 trong lịch S250).
2. AA-926: rebase, thêm mã mới, review độc lập, rồi merge và deploy trong khoảng nghỉ G2; kiểm live trang Content Quality.
3. AA-916 WM-03: migration CIS 277 cùng bản copy Infra, review, rồi apply ngoài wave (G3).
4. Lane CIS chạy nối tiếp trên `service.py`: AA-924 PR1, rồi AA-790 6a + 6b, rồi AA-916 phần ghi tín hiệu (WM-04/05/08)
   và mã lý do (WM-06). Deploy chung trong khoảng nghỉ G4.
5. Khi wave cuối xong: PR mục 2 (writer v2 mặc định), báo cáo tổng AA-645.
6. `plan.json` và `docs/backlog/README.md` (tiêu chí M2a "Quyết định go/no-go bằng văn bản…" = xong, dòng 6–9, AA-765/900)
   cập nhật trong root PR đóng phiên, không trong PR này, vì các lane khác đang chạy.

## 6. Không cần anh duyệt thêm

Mọi mục trên nằm trong kế hoạch anh đã duyệt (S246 bước 5, d04, S250 "duyệt luôn theo kế hoạch"). Không có chi phí mới
ngoài trần $120 của AA-645. Mục 2 là đổi cấu hình, tốn ~$0,07 mỗi tour mới. Mục 6b chỉ là NO-GO cho cổng chặn, dựa trên
số đo (κ) và luật đóng băng anh đã chốt, không phải một cổng do agent đặt ra.
