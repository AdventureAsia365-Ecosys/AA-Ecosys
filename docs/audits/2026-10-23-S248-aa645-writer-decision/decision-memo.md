# AA-645 — Chọn writer cho S1 (A1): giữ Haiku A+ hay chuyển sang writer v2 (Sonnet 5.5 / Luna)?

Bản tư vấn cho Nghiệp · S248 · 23/10/2026 · Tác nhân: Claude Code
Nguồn: chỉ 3 báo cáo của A/B run 1 (chấm điểm panel, mô hình chi phí, đánh giá judge/validate). Không dùng số nào khác.

---

## 1. Kết luận + đề xuất

**Đề xuất: chuyển S1 sang writer v2 với Sonnet 5.5 (W×Sonnet).** Trên 25 tour golden, W×Sonnet có tỉ lệ lỗi nghiêm trọng bằng khoảng 1/10 của A+ hôm nay (0,0033 so với 0,0385 lỗi trên mỗi claim kiểm được, p = 0,0001 ở cả hai lượt chấm), khoảng cách lớn gấp ~17 lần nhiễu A/A, không trang nào dính gate code (A+ 16/25), xếp hạng tốt nhất, và sửa được 18/23 tour mà nhãn đánh fail. Giá: viết lại cả ~900 tour qua toàn chuỗi A1 hết khoảng **$72** (ước tính giữa; khoảng $61–105), tức hơn hôm nay ~$30 mỗi lần chạy lại toàn bộ; tháng bình thường chỉ hơn ~$1,6. Vì 900 tour này là nền dữ liệu cho cả hệ thống (atom, T-series, TripPlanner, Booking đều đọc từ đây), khoản chênh này nhỏ so với giá trị của việc nền đúng ngay từ đầu.
**Phương án thay thế: W×Luna (gpt-6-luna).** Về thống kê, W×Luna hòa với W×Sonnet (p = 0,13, chỉ 7 tour khác nhau), cũng vượt A+ rõ ràng (0,0056, sửa 17/23), và rẻ hơn khoảng 25 lần ở phần writer: ~$11 cho 900 tour, rẻ hơn hôm nay ~$31. Theo luật "hòa thì lấy model rẻ hơn", Luna sẽ thắng nếu sửa được trang META_CUT duy nhất (s1-015). Em vẫn nghiêng về Sonnet vì: xếp hạng trung bình tốt hơn rõ (0,148 so với 0,302), 0 trang gate, độ phủ số liệu cao hơn (0,661 so với 0,602), vòng sàng lọc 12 tour trước đó Sonnet đứng đầu 10–11/12 còn Luna đứng cuối, và nếu writer là Luna thì judge kiểm độ trung thực nên là Sonnet (khác họ model), nên phần tiết kiệm bị thu hẹp (xem mục 3). **Nếu anh muốn giữ đúng luật "hòa thì lấy rẻ", chọn W×Luna là hợp lý — cả hai đều tốt hơn A+ rất xa; điều quan trọng nhất là rời A+.** Cả hai lựa chọn đều cần A/B run 2 xác nhận trước khi chạy thật (mục 5).

---

## 2. Bảng so sánh

### 2.1 Chất lượng và lỗi (25 tour golden, 2 lượt chấm panel mù a/b)

| Phương án | Lỗi nghiêm trọng / claim (gộp a+b) | Lỗi nghiêm trọng / trang | Xếp hạng TB (0 = luôn nhất, 1 = luôn bét) | Trang dính gate code (/25) | Độ phủ số liệu | Tour fail được sửa (/23) |
|---|---:|---:|---:|---|---:|---:|
| A+ Haiku (hôm nay) | 0,0385 | 2,38 | 0,840 | 16 (NUMBER_NOT_IN_SOURCE 12, META_LENGTH 8) | 0,443 | 3 |
| A+ Haiku lần 2 (A/A) | 0,0406 | 2,54 | 0,822 | 16 | 0,476 | 3 |
| **W×Sonnet 5.5** | **0,0033** | 0,18 | **0,148** | **0** | 0,661 | **18** |
| E×Sonnet 5.5 | 0,0065 | 0,24 | 0,328 | 1 (META_LENGTH) | **0,691** | 17 |
| **W×Luna** | 0,0056 | 0,24 | 0,302 | 1 (META_CUT, s1-015 — tour nhãn pass) | 0,602 | 17 |
| E×Luna | 0,0130 | 0,38 | 0,560 | 0 | 0,351 | 15 |
| Trang đang live (stored) | không chấm panel | – | – | 13 | 0,479 | – |

- So với A+, cả 4 phương án mới đều khác biệt có ý nghĩa (Wilcoxon cặp, p ≤ 0,0002 gộp). So với A+ lần 2 cũng vẫn p ≤ 0,0045 ở mọi lượt.
- Khoảng cách so với A+ (bootstrap 95%): W×Sonnet −0,0351 (−0,051 đến −0,023); W×Luna −0,0329 (−0,049 đến −0,020).
- Giữa các phương án mới: W×Sonnet so với W×Luna p = 0,128; E×Sonnet so với W×Sonnet p = 0,128 — **không khác biệt có ý nghĩa**.
- Cả hai lượt chấm xếp thứ tự giống nhau: W×Sonnet < W×Luna < E×Sonnet < E×Luna < A+ < A+2.
- Tour fail còn chưa sửa được: W×Sonnet — s1-005, 006, 010, 016, 021; W×Luna — s1-005, 006, 007, 012, 016, 021 (đều là lỗi panel đánh nghiêm trọng, không phải gate code).
- Không phương án nào có lỗi writer hay phải retry trong run 1.

### 2.2 Chi phí viết lại ~900 tour (toàn chuỗi A1, ước tính giữa; khoảng thấp–cao)

| Phương án | Writer / tour (A/B run 1) | Toàn chuỗi / tour | 900 tour | Chênh so với hôm nay | Trong đó acc3 |
|---|---:|---:|---:|---:|---:|
| Hôm nay: Haiku 4.5 | $0,017 | $0,046 | $42 | – | $36,5 |
| **W×Sonnet 5.5** | $0,059 | $0,080 (0,068–0,117) | **$72** (61–105) | +$30 | $68 |
| E×Sonnet 5.5 | $0,042 | $0,058 (0,049–0,085) | $53 (44–77) | +$11 | $50 |
| **W×Luna** | $0,0024 | $0,012 (0,010–0,017) | **$11** (9–15) | −$31 | $6,5 |
| E×Luna | $0,0018 | $0,010 (0,008–0,014) | $9 (7–13) | −$33 | $5,9 |

- Ghi chú về con số "~$50": mô hình chi phí cho ra $72 (giữa) cho W×Sonnet khi tính cả judge, Jev, fix…; $53 là của E×Sonnet. Với Sonnet, riêng writer chiếm 85–90% chi phí chuỗi.
- Báo cáo chi phí dự kiến **khoảng 2 lần chạy lại toàn bộ một lần** khi chuyển (shadow/review ở bước 4, rồi một lần chạy sạch): W×Sonnet ~2 × $72, W×Luna ~2 × $11.
- Viết lại toàn bộ A1 nào cũng kéo theo atomize lại: thêm ~$30–45 cho 900 tour, **không phụ thuộc writer**. DataForSEO (~$16,6 mỗi wave) cũng vậy.

### 2.3 Chi phí theo tháng (chênh so với chuỗi Haiku hôm nay, acc3; dự báo tháng 10 ~$216)

| Phương án | Tháng thường (~45 tour) | 1 lần chạy lại toàn bộ mỗi quý (~345 tour/tháng) | Tháng giống tháng 10 (1 lần chạy lại toàn bộ + lẻ, ~945 tour) |
|---|---:|---:|---:|
| W×Sonnet 5.5 | +$1,6 | +$12 (+6%) | +$33 (+15%) |
| E×Sonnet 5.5 | +$0,7 | +$5 (+2%) | +$14 (+6%) |
| W×Luna | −$1,5 | −$11 (−5%) | −$31 (−14%) |
| E×Luna | −$1,5 | −$12 (−5%) | −$32 (−15%) |

A1 chỉ là phần nhỏ trong chi phí acc3 (atomize, A3 và T-series tốn hơn).

---

## 3. Judge / validate: giữ gì, đổi gì

Phát hiện chính: **khâu yếu không phải là model judge mà là cái judge được giao kiểm.** `s1_judge` chỉ chấm "hợp brand" và không bao giờ thấy tour nguồn, nên không kiểm được sự thật, phạm vi hay lời hứa — đúng các lỗi nằm sau phần lớn nhãn fail. Trên 50 trang golden, judge hiện tại cho qua 45/50, chỉ bắt 5/44 trang fail, κ ≈ 0,03 (gần như ngẫu nhiên), AUC 0,61. 5 trang nó bắt đúng đều có cấu trúc ngày hỏng — thứ mà day-oracle trong code đã phát hiện được.

| Bước | Đề xuất | Lý do ngắn |
|---|---|---|
| `s1_judge` (gpt-5.6-luna) | **Giữ model, không nâng cấp.** Khi nối writer mới (bước 4): chuyển điểm brand-fit thành chỉ báo cáo (không chặn), hoặc đổi thành kiểm giọng văn trung tính không phạt trang "chung chung". Bật enforce các mã day-oracle (DAY_SUBDAY_SPLIT, DAY_OUTPUT_DUPLICATE, DAY_DEPARTURE_MIDTRIP, DAY_COUNT_VS_DURATION). | Prompt judge phạt trang "generic"; trang W/E viết sát nguồn có thể bị chấm < 7 → retry → writer bị đẩy thêm thắt, sinh claim bịa. |
| `s1_brand_audit` | **Chỉ dùng kiểm tra xác định (code)**, bỏ đường LLM dự phòng (vẫn chạy trên `AA_BRAND_IDENTITY_PROMPT`). Judge lỗi → giữ trang lại (`JUDGE_UNAVAILABLE` cứng cho A1). | Bỏ prompt nhận diện Adventure Asia cuối cùng khỏi A1; đường này gần như không chạy (~$0). |
| `s1_flag_fix` (Haiku) | **Giữ Haiku**, thu hẹp: chỉ sửa meta + câu bị grounding đánh. Không nâng lên Sonnet. | Sửa 1–2 câu; repair contract tự hoàn tác sửa sai. Theo dõi gate code sau khi sửa. |
| `s1_itinerary_nudge` | **Bỏ** khi nối W/E (lịch ngày dựng bằng code). | Tiết kiệm ~$3,8/tháng. |
| `s1_source_facts` | **Bỏ route**, giữ cờ tắt. | `build_fact_table` bằng code ($0) đã khớp nguồn 8.673 giá trị, 0 sai. |
| `s1_grounding` (Jev) | **Giữ BẬT** (quyết định S247). Đo lại trên trang W/E (~$0,4 cho ~75 trang). Nếu ~1–2 câu bị đánh/tour với độ chính xác ≥ 0,95 → đặt ngưỡng reject để Jev thành cổng trung thực rẻ. | Cần n ≥ 30 so với panel trước khi đặt ngưỡng. |
| **Mới: judge trung thực có đọc nguồn** | Đây là chỗ nên tiêu tiền. 1 lần gọi/trang trên bảng fact + trang, theo rubric v1.1; chạy **shadow** trước (đang trong đợt đóng băng gate mới 4 tuần). **Khác họ model với writer:** writer Sonnet → judge gpt-5.6-luna (~$0,003/tour, ~$3 cho cả catalogue); writer Luna → judge Sonnet 5.5 (~$0,02–0,03/tour, ~$25 cho cả catalogue). Chấp nhận khi đạt mức đồng thuận nhãn 0,65–0,70 của panel. | Hiện không LLM nào kiểm sự thật đối chiếu nguồn (trừ Jev, nhưng Jev không có ngưỡng reject). |

Ý nghĩa với lựa chọn writer: nếu chọn Sonnet, judge trung thực rẻ (Luna, ~$3); nếu chọn Luna, judge trung thực phải là Sonnet (~$25). Như vậy một lần viết lại toàn bộ kèm judge trung thực là khoảng $72 + $3 (Sonnet) so với $11 + $25 (Luna) — Luna vẫn rẻ hơn, nhưng chênh còn khoảng $40 chứ không phải ~$60.

Phép đo rẻ nhất nên làm trước: chạy `score_brand_fit` offline trên các trang A/B run 1 đã có (125 verdict, ~$0,26, trần $0,5), so với panel ($0). Trả lời đúng một câu: judge có chấm thấp trang viết sát nguồn vì "chung chung" không.

---

## 4. Rủi ro và điều chưa chắc

1. **Mẫu nhỏ:** chỉ 25 tour; chỉ 2 tour có nhãn pass, nên cột "nhãn pass" gần như không nói gì.
2. **Nhiễu A/A:** hai lần chạy A+ cho chênh tỉ lệ gộp +0,0021 (bootstrap 95% −0,013 đến +0,022; p = 0,93), chênh tuyệt đối từng tour trung vị 0,017. Khoảng cách W so với A+ vượt xa mức này, nhưng **khoảng cách giữa W×Sonnet và W×Luna thì không** — đó là lý do cần run 2.
3. **Độ tin cậy của panel:** hai lượt chấm khớp nhau tốt (κ 0,849 cho "trang có lỗi nghiêm trọng", Spearman 0,897 trên số lỗi), nhưng **ngưỡng pass/fail của rubric v1.1 chưa được kiểm so với nhãn** (panel đạt 0,65/0,70 trên 20 trang held-out). Vì vậy chỉ dùng tỉ lệ lỗi nghiêm trọng và thứ hạng như **tín hiệu tương đối**, không coi là "trang đạt chuẩn".
4. **Nhãn golden** đến từ panel agent và đã được anh duyệt (cập nhật 1.0.0 → 1.1.0), không phải người chấm độc lập.
5. **Trang đang live chưa được panel chấm** — chỉ có gate code (13/25).
6. **Run 1 chỉ chạy writer + meta**, chưa chạy validator live, judge, Jev. Chi phí writer có thể lệch ±20–30%; tour dài (18–22 ngày) với Sonnet 5.5 (adaptive thinking) tốn hơn.
7. **Rủi ro lớn nhất về chi phí: retry tăng chứ không giảm.** Writer v2 bỏ phần khác biệt brand, nhưng judge A1 vẫn chấm brand. Nếu trang trung tính hay bị < 7, số lần thử tăng → kịch bản "cao" (Sonnet +45%, ~$105 cho 900 tour). Bước 4 shadow phải đo tỉ lệ judge cho qua trước khi chạy rộng.
8. **Số lần chạy/lần thử là suy ra, không đếm trực tiếp** (1,30 lần thử/run, 1,17 run/tour lấy từ số liệu S218; truy vấn đếm trực tiếp bị hook chặn, script đã sẵn ở `.tmp-session/S248/aa645cost/q.py`).
9. **Giá Luna có thể đổi:** chạy trên Bedrock acc3 với prompt caching tự động; prompt writer dài có thể làm cache khác đi.
10. **Cùng họ model:** nếu writer là Luna mà judge cũng Luna thì judge dễ dễ dãi với văn của chính họ mình (hiệu ứng chung của LLM-judge, chưa đo ở đây).

---

## 5. Bước tiếp theo

1. **A/B run 2 trên tour golden 25:50** (25 tour còn lại, chưa dùng ở run 1) để xác nhận. Các arm: A+, A+ lần 2 (A/A), W×Sonnet, W×Luna (sau khi sửa lỗi META_CUT của Luna). Writer ước tính ~$2–3 (theo giá/tour của run 1); chấm panel 2 lượt bằng agent Claude ($0). Tiêu chí chốt trước khi chạy:
   - W phải lại vượt A+ ngoài nhiễu A/A ở cả hai lượt.
   - Gộp run 1 + run 2 (n = 50) để so W×Sonnet với W×Luna. Nếu Sonnet tốt hơn có ý nghĩa → Sonnet. Nếu vẫn hòa → anh chốt: Sonnet (đề xuất của em, vì là nền dữ liệu) hoặc Luna (luật "hòa thì lấy rẻ").
   - Kèm phép đo $0,26 judge brand-fit offline trên trang run 1 + run 2.
2. **Bước 4 — nối writer thắng sau cờ (flag), mặc định tắt**, chạy shadow: đo tỉ lệ judge cho qua, số lần thử/run, gate code sau flag_fix, và Jev trên trang mới (~$0,4). Cùng lúc: brand-fit chỉ báo cáo, bật day-oracle, bỏ nudge + route source_facts, A1 brand_audit chỉ dùng code; judge trung thực đọc nguồn chạy shadow (khác họ model với writer).
3. **Chạy theo wave (paid-runs-subset)**, mỗi wave dừng lại báo cáo và chờ duyệt (theo `aa-wave-rerun`):
   - **3 tour** pilot (W×Sonnet ~$0,24 cho chuỗi A1) — kiểm end-to-end, gate, judge, Jev.
   - **≤ 50 tour** (~$4 với Sonnet) — đo lại tỉ lệ lỗi, tỉ lệ retry, chi phí thật so với mô hình.
   - **Toàn bộ ~900 tour** (~$72 với Sonnet, $61–105; hoặc ~$11 với Luna) + atomize lại (~$30–45). Không merge/deploy backend khi `shared.job` còn job hoặc đang có wave.
4. Chỉ số theo dõi trong mọi wave: số trang có "Adventure Asia" / "Design This Journey" khi nguồn không có; gate code mỗi trang; tỉ lệ judge < 7; chi phí/tour từ `shared.llm_call_log`.

---

File liên quan: `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645ab/score.json`, `pass-a.json`, `pass-b.json`, `run/summary.json`, `llmcost.txt`, `fixture-1.1.0.json`; mô hình chi phí và script đếm `/home/nghiep/projects/AA-Ecosys/.tmp-session/S248/aa645cost/q.py`.
