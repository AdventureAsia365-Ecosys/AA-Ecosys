# AA-712 — Geocoder bake-off (Geoapify vs Amazon Location Places v2)

S236 · 14/10/2026 · Tác nhân: Claude Code · Input: `.tmp-session/s236/bake_sample.json` (71 tên, 13 nước) · Context: [04-geocoder-research.md](04-geocoder-research.md)

## Tóm tắt cho Nghiệp

1. **Geoapify thắng rõ, dùng làm geocoder chính cho mọi nước.** Trên 64 tên thật: Geoapify ra đúng địa điểm (hoặc sát nó) 38/64 (59%), AWS Geocode chỉ 14/64 (22%). Nhóm khó (tu viện/đèo/hồ/làng): Geoapify 18/29, AWS 1/29.
2. **AWS Geocode gần như chỉ tìm được thành phố.** BT/CN/MN/LA: 0 kết quả đúng. NP/TW: toàn trùng tên sai chỗ (Annapurna → Koshi 334 km, Erawan → Loei 450 km). Nếu vẫn dùng AWS thì phải dùng **SearchText**, không phải Geocode (probe 8 POI: SearchText trúng 4/8, Geocode 0/8).
3. **Theo nước:** Geoapify cho tất cả. AWS SearchText (Storage) chỉ đáng làm ý kiến thứ hai ở TH, IN, VN, KH, LK. Không dùng AWS cho JP (cấm lưu), BT/CN/MN/KR (không có dữ liệu), NP/TW/LA (sai nhiều hơn đúng).
4. **TW và KR yếu ở cả hai** (TW 1/6, KR 1/4). Hướng sửa: LLM trả thêm tên bản địa (中文/한글), query cả hai tên.
5. **Luật nhận kết quả Geoapify:** KHÔNG dựa vào `rank.confidence`. POI đúng vẫn hay có confidence = 0 (Jokhang, Khuvsgul, Li Phi, Yol), nên luật đó bỏ sót 9/38 điểm đúng. Thay vào đó, xét top-3 và nhận ứng viên đầu tiên đạt cả 3 điều kiện:
   (a) tên khớp sau chuẩn hoá: bỏ dấu, ngoặc, độ cao; mọi từ riêng phải có mặt;
   (b) `result_type` không phải country/state/county/postcode, và chỉ nhận `city` khi query chính là thị trấn/làng;
   (c) cách điểm LLM ≤ 25 km, riêng hồ/sông/thung lũng nới lên ≤ 50 km.
   Trên mẫu, "tên khớp ≥ 0.5 + ≤ 50 km" giữ 34/38 điểm đúng và chỉ lọt 3 điểm sai.
6. **Không provider nào xác nhận:** giữ điểm LLM với `located_by='llm'`. Hiển thị ở mức "khu vực" (không cắm pin chính xác) và đưa vào hàng review cho nhóm khó.
7. **Tên chung chung thì không geocode:** "ger camp", "local market", "village center", "fishing village". Lọc từ đầu (không có danh từ riêng) và dùng điểm thành phố/ngày của tour. Chuẩn hoá query trước khi gửi: bỏ "(5,164m)", tách "X to Y", tách "X, City".
8. Điểm `null` (legacy) thường sai xa: Khone Phapheng lệch 670 km, Ritigala 101 km. Điểm `llm` khá tốt (median 13 km tới điểm Geoapify khớp tên). AWS SingleUse đã gọi **79 request ≈ $0.04**.

---

## Details (English)

### Method
- **Sample**: 71 rows across 13 countries. 7 rows are generic phrases, not place names (rows 15, 20, 22, 23, 31, 46, 48: ger camp, fishing village, northern Okinawa fishing villages, living reefs, local market, village center, Dolce Hotel or glamping site). They appear in "All 71"; the "Real names (64)" slices exclude them.
- **Geoapify**: `/v1/geocode/search?text=<name>&filter=countrycode:<iso2>&format=json&limit=3`, free tier, about 3 req/s. The key was read from `aa-cis/dev/geoapify` and is not in any saved file.
- **Amazon Location Places v2 Geocode**: `aws geo-places geocode --query-text <name> --filter IncludeCountries=<iso3> --intended-use SingleUse --max-results 3 --region us-west-2` (71 calls). Every response reported `PricingBucket: Core`. No call errored, including the *Unsupported* countries: they returned empty lists or unrelated streets.
- **SearchText probe** (8 calls): `geo-places search-text` with `BiasPosition` = reference point, `IncludeCountries`, `Language=en`, SingleUse. Rows: Nago Pineapple Park, Nasu Imperial Villa, Khone Phapheng, Li Phi, Erawan, Cheow Lan, Kelaniya Temple, Zatrwa La. The research (04 §1) names SearchText as the POI call, and Geocode returned almost no POIs here, so this probe checks that claim within budget.
- **Labels**: each provider's top result was hand-labelled. These labels are judgement, not ground truth.
  - `N` = the named place
  - `R` = related or partial: adjacent POI at the same site, a road or hotel named after the place, one endpoint of "X to Y", or the locality that is the place
  - `F` = admin fallback: a city, district or county that contains a POI
  - `W` = wrong: a homonym elsewhere, an unrelated POI, or a generic-word match
  - `—` = no result
- **Reference** = the stored lat/lng. It is trustworthy only for `mapbox` (20 rows). `llm` (35 rows) is a weak reference, and `null` (16 rows) is often far off. Distances are haversine km from the top result to the reference.
- **`sim`** = automatic name similarity: the share of distinctive query tokens found in the result name, after lower-casing, removing diacritics and parentheses, and dropping generic words such as temple/lake/pass/village. It drives the acceptance-rule table.
- Scripts, key-free raw JSON and scored output are in the session scratchpad (`bake/`) and are not committed.

### Results — overall
"Admin fallback", "Wrong" and the distance columns are counted only over rows where the provider returned a result.

| Slice | Provider | n | Found | Named place | Named or related | Admin fallback (of found) | Wrong (of found) | Median km to ref | ≤ 25 km | > 100 km |
|---|---|---|---|---|---|---|---|---|---|---|
| All 71 | Geoapify | 71 | 60/71 (85%) | 32/71 (45%) | 38/71 (54%) | 2/60 (3%) | 20/60 (33%) | 10.2 | 34/60 (57%) | 21/60 (35%) |
| All 71 | AWS Geocode | 71 | 30/71 (42%) | 13/71 (18%) | 14/71 (20%) | 3/30 (10%) | 13/30 (43%) | 4.0 | 16/30 (53%) | 13/30 (43%) |
| Real names (64) | Geoapify | 64 | 55/64 (86%) | 32/64 (50%) | 38/64 (59%) | 2/55 (4%) | 15/55 (27%) | 8.4 | 34/55 (62%) | 16/55 (29%) |
| Real names (64) | AWS Geocode | 64 | 29/64 (45%) | 13/64 (20%) | 14/64 (22%) | 3/29 (10%) | 12/29 (41%) | 3.3 | 16/29 (55%) | 12/29 (41%) |
| Hard (real) | Geoapify | 29 | 28/29 (97%) | 15/29 (52%) | 18/29 (62%) | 2/28 (7%) | 8/28 (29%) | 9.3 | 18/28 (64%) | 8/28 (29%) |
| Hard (real) | AWS Geocode | 29 | 9/29 (31%) | 1/29 (3%) | 1/29 (3%) | 3/9 (33%) | 5/9 (56%) | 149.2 | 3/9 (33%) | 5/9 (56%) |
| Normal (real) | Geoapify | 35 | 27/35 (77%) | 17/35 (49%) | 20/35 (57%) | 0/27 (0%) | 7/27 (26%) | 5.3 | 16/27 (59%) | 8/27 (30%) |
| Normal (real) | AWS Geocode | 35 | 20/35 (57%) | 12/35 (34%) | 13/35 (37%) | 0/20 (0%) | 7/20 (35%) | 1.6 | 13/20 (65%) | 7/20 (35%) |
| Ref = mapbox | Geoapify | 20 | 19/20 (95%) | 12/20 (60%) | 14/20 (70%) | 2/19 (11%) | 3/19 (16%) | 0.9 | 15/19 (79%) | 3/19 (16%) |
| Ref = mapbox | AWS Geocode | 20 | 14/20 (70%) | 10/20 (50%) | 10/20 (50%) | 1/14 (7%) | 3/14 (21%) | 0.6 | 11/14 (79%) | 3/14 (21%) |
| Ref = llm | Geoapify | 35 | 29/35 (83%) | 15/35 (43%) | 19/35 (54%) | 0/29 (0%) | 10/29 (34%) | 13.0 | 16/29 (55%) | 9/29 (31%) |
| Ref = llm | AWS Geocode | 35 | 11/35 (31%) | 3/35 (9%) | 4/35 (11%) | 0/11 (0%) | 7/11 (64%) | 149.2 | 4/11 (36%) | 7/11 (64%) |
| Ref = null | Geoapify | 16 | 12/16 (75%) | 5/16 (31%) | 5/16 (31%) | 0/12 (0%) | 7/12 (58%) | 193.6 | 3/12 (25%) | 9/12 (75%) |
| Ref = null | AWS Geocode | 16 | 5/16 (31%) | 0/16 (0%) | 0/16 (0%) | 2/5 (40%) | 3/5 (60%) | 119.2 | 1/5 (20%) | 3/5 (60%) |

Reading:
- AWS's low median distance (4 km) comes from city-name rows such as Bikaner, Galle and HCMC. On hard rows its median is 149 km.
- Union of both providers (N or R by either): 40/64. AWS adds only 2 rows Geoapify missed: Laomei (#57) and Bangkok Chinatown (#65).
- Geoapify's top-3 would rescue more rows: Hahoe Village is candidate #2 for #44, and Phi Phi resorts are #2 and #3 for #64.

### Results — per country (real names only)

| Country | n (real) | Geoapify named | Geoapify named+related | AWS named | AWS named+related | AWS admin fallback | Wrong G / A | Neither found the place |
|---|---|---|---|---|---|---|---|---|
| Bhutan | 6 | 3 | 5 | 0 | 0 | 0 | 0 / 0 | 1 |
| Cambodia | 2 | 1 | 2 | 2 | 2 | 0 | 0 / 0 | 0 |
| China | 6 | 3 | 3 | 0 | 0 | 0 | 2 / 1 | 3 |
| India | 5 | 3 | 3 | 3 | 3 | 0 | 2 / 2 | 2 |
| Japan | 3 | 3 | 3 | 1 | 1 | 0 | 0 / 0 | 0 |
| Laos | 5 | 3 | 3 | 0 | 0 | 0 | 0 / 1 | 2 |
| Mongolia | 6 | 4 | 5 | 0 | 0 | 0 | 1 / 0 | 1 |
| Nepal | 6 | 2 | 3 | 0 | 1 | 0 | 2 / 3 | 3 |
| South Korea | 4 | 1 | 1 | 0 | 0 | 1 | 2 / 0 | 3 |
| Sri Lanka | 6 | 4 | 4 | 2 | 2 | 2 | 1 / 0 | 2 |
| Taiwan | 6 | 0 | 1 | 1 | 1 | 0 | 1 / 3 | 4 |
| Thailand | 6 | 3 | 3 | 2 | 2 | 0 | 3 / 1 | 2 |
| Vietnam | 3 | 2 | 2 | 2 | 2 | 0 | 1 / 1 | 1 |

Notes on the Unsupported countries:
- The research's "Unsupported" countries (BT, CN, MN, KR) did not error. AWS returned nothing, or noise such as a Beijing street for Guangning or the Jeonju locality for Hanok Village.
- AWS returned 0 POIs in Laos and Nepal, which the research rated POI "Fair".

### AWS SearchText probe (8 hard POIs; Geocode found 0/8 of them)

| Row | SearchText top result | Label |
|---|---|---|
| Nago Pineapple Park (JP) | Nago Pineapple Park 26.6164, 127.9697 | N (but JP storage banned) |
| Nasu Imperial Villa (JP) | Fujitsu Villa Nasu | W |
| Khone Phapheng Falls (LA) | Khonephapheng Resort & Golf Club ~2.5 km from falls | R (hotel) |
| Li Phi Waterfall (LA) | Phi Dao Hotel (Pakse area) | W |
| Erawan Waterfall (TH) | Erawan Falls 14.3687, 99.1445 | N |
| Cheow Lan Lake (TH) | Cheow Lan Lake Travel / View Point 8.97, 98.81 | N |
| Kelaniya Temple (LK) | Kelaniya Temple 6.9531, 79.9207 | N |
| Zatrwa La Pass (NP) | Thorong La Pass (305 km away) | W |

SearchText is clearly the right AWS call for POIs: 4/8 named against 0/8 for Geocode. It is good in TH/LK, weak in LA/NP, and its Japan results cannot be stored anyway.

### Acceptance rules (Geoapify top result, 55 real-name rows with a result)

| Rule | Accepted | Correct (N/R) | Wrong/fallback accepted | Recall of correct |
|---|---|---|---|---|
| accept everything | 55 | 38 | 17 | 38/38 (100%) |
| rank.confidence ≥ 0.8 | 31 | 29 | 2 | 29/38 (76%) |
| name similarity = 1.0 | 38 | 32 | 6 | 32/38 (84%) |
| name sim ≥ 0.5 | 48 | 37 | 11 | 37/38 (97%) |
| within 25 km of LLM/ref point | 34 | 32 | 2 | 32/38 (84%) |
| name sim = 1.0 AND type ≠ country/state/county/postcode | 37 | 31 | 6 | 31/38 (82%) |
| name sim = 1.0 AND ≤ 25 km of ref | 27 | 26 | 1 | 26/38 (68%) |
| name sim ≥ 0.5 AND ≤ 50 km of ref | 37 | 34 | 3 | 34/38 (89%) |

Findings that matter for the rule:
- **`rank.confidence` is not usable for POIs.** Correct `amenity` hits often score 0: Jokhang, Lake Khuvsgul, Li Phi Falls, Yol, Khorgo and the Taktshang site. It misses 9 correct rows. It also accepts homonyms that score high, such as Bhangarh in Madhya Pradesh (0.9) and the Chiang Mai Chinatown (1.0).
- **Distance to the LLM point is the strongest single filter.** Of the rows it wrongly rejects, 3 have a bad legacy `null` reference, and the other 3 are long features: Manas River, the Tingtibi road and Cheow Lan Lake. That is why lakes, rivers and valleys get a 50 km radius.
- **Name match alone lets homonyms through**: Bhangarh MP, Wohushan reservoir, Golden Grotto, Ban Phai Koh Don and Chiang Mai Chinatown. So name match must be combined with distance.
- **Proposed rule**: scan the top 3 and take the first candidate that passes all of these:
  - `sim` = 1.0, or `sim` ≥ 0.5 when the query has ≥ 2 distinctive tokens;
  - `result_type` is not country/state/county/postcode, and `city` only when the query is itself a settlement;
  - distance to the LLM point ≤ 25 km, or ≤ 50 km for lake/river/valley/park/trail.

  Store it as `located_by='geoapify'`. If nothing passes, fall back to `llm`.
- **AWS**: `MatchScores.Overall ≥ 0.9` accepted 12 rows, all correct, but 9 of the 12 are cities. Use it as a second opinion only.

### Disagreements > 25 km — judgement (geographic knowledge, not verified fact)

| # | Row | Disagreement | Judgement |
|---|---|---|---|
| 3 | Manas River (BT) | G vs LLM 39 km | Both points lie on or near the Manas river system, which is a long line. Accept G. |
| 11 | Guangning (CN) | G vs AWS 1,845 km | G is right: Guangning County, Guangdong, matches the mapbox ref. AWS returned "Guangming Rd", Beijing. |
| 14 | Bhangarh village (IN) | G vs AWS 658 km | Both wrong: Bhangarh in Madhya Pradesh, and Bhalswa in Delhi. The mapbox ref (27.096, 76.288) is Bhangarh Fort, Alwar, Rajasthan, which is the correct place. |
| 16 | Rangaji Temple (IN) | G vs AWS 597 km | Both wrong (Trivandrum, Chennai). The LLM point (27.575, 77.697) is the Vrindavan Rangaji temple, which is right. |
| 29 | Khone Phapheng Falls (LA) | G vs ref 671 km | G is right (13.96, 105.99, Khong district). The legacy `null` ref in northern Laos is wrong. |
| 30 | Laos Buffalo Dairy (LA) | G vs ref 139 km | G is plausibly right (19.79, 101.99, near Luang Prabang). AWS returned "Buffalo Tours", and the `null` ref is wrong. |
| 38 | Annapurna South Base Camp (NP) | G vs AWS 334 km | G is right: Annapurna Base Camp, 28.53, 83.88. AWS returned the homonym admin unit "Annapurna" in Koshi. |
| 41 | Gorakshep (5,164m) (NP) | G vs AWS 393 km | Both wrong, because "(5,164m)" polluted the query. The LLM point (28.0, 86.86) is about 3 km from real Gorak Shep (≈27.98, 86.83). |
| 52 | Ritigala Monastery (LK) | G vs ref 101 km | G is right (8.118, 80.665). AWS returned a nearby "Ritigala" district, which is a fallback. The `null` ref is wrong. |
| 57 | Laomei River, New Taipei (TW) | G vs AWS 46 km | AWS is right (Laomei, 25.29, 121.545, matching the mapbox ref). G fell back to the New Taipei county centroid. |
| 58 | Taipingshan Villa (TW) | G vs AWS 141 km | G is right: Taipingshan, Yilan, 24.49, 121.54. AWS returned the homonym 太平 in Chiayi. The LLM point is about 10 km off. |
| 62 | Cheow Lan Lake (TH) | G vs LLM 33 km | Uncertain. G (8.95, 98.61) may sit on the western arm of the reservoir. SearchText (8.97, 98.81, the dam viewpoint) is the safer pin. The LLM point (98.91) looks east of the lake. |
| 63 | Erawan Waterfall (TH) | G vs AWS 449 km | G is right: Kanchanaburi, 14.368, 99.144. AWS returned the Erawan district in Loei. |
| 65 | Chinatown (TH) | G vs AWS 587 km | The query is ambiguous. AWS returned Bangkok Yaowarat, which fits this tour's LLM point. G's top result is the Chiang Mai Chinatown, and Bangkok is its #2. This needs the distance rule. |
| 68 | An Binh Island (VN) | G vs AWS 1,068 km | Both wrong. The mapbox ref (10.01, 105.75) is likely An Bình ward in Cần Thơ, not An Binh Island in Vĩnh Long (≈10.24, 105.98). The ref itself is suspect. |

Also, for #21 Nasu Imperial Villa, G (37.088, 140.024) is plausibly the real Goyotei. The mapbox ref, 11 km away, looks like Nasu town.

### Per-row results
(Columns: # | Country | Name | Ref (by) | Hard | Geoapify top: type / conf / sim / km / label — name | AWS Geocode top: type / score / km / label | G↔A km)

| # | Country | Name | Ref (by) | Hard | Geoapify top: type / conf / sim / km / label | AWS top: type / score / km / label | G↔A km |
|---|---|---|---|---|---|---|---|
| 0 | Bhutan | Chorten Kora temple | 27.503, 91.556 (llm) | Y | amenity / 0.67 / 1.00 / 13.0 / **N** — Chorten Kora | — |  |
| 1 | Bhutan | Dochu La Pass | 27.483, 89.783 (llm) | Y | amenity / 0.90 / 1.00 / 3.5 / **N** — Dochu La | — |  |
| 2 | Bhutan | Taktshang Monastery | 27.494, 89.362 (mapbox) | Y | amenity / 0.00 / 0.00 / 0.6 / **R** — Öselgang monastery | — |  |
| 3 | Bhutan | Manas River | 26.850, 90.650 (llm) |  | amenity / 1.00 / 1.00 / 39.5 / **N** — Manas River | — |  |
| 4 | Bhutan | ThombuShong | 27.700, 89.500 (llm) |  | — | — |  |
| 5 | Bhutan | Tingtibi | 26.967, 90.733 (llm) |  | street / 1.00 / 1.00 / 25.4 / **R** — Tingtibi - Zhemgang Highway | — |  |
| 6 | Cambodia | Phnom Penh | 11.568, 104.922 (mapbox) |  | postcode / 1.00 / 1.00 / 10.3 / **R** — Phnom Penh Garbage Dump | Locality / 1.00 / 4.8 / **N** | 9 |
| 7 | Cambodia | Siem Reap | 13.355, 103.855 (mapbox) |  | city / 1.00 / 1.00 / 0.9 / **N** — Siem Reap | Locality / 1.00 / 2.2 / **N** | 3 |
| 8 | China | Huashan's five peaks | 34.485, 110.087 (llm) | Y | amenity / 0.00 / 0.33 / 949.8 / **W** — Five Sen5es | — |  |
| 9 | China | Jokhang Temple and Barkhor Street | 29.653, 91.118 (llm) | Y | amenity / 0.00 / 0.50 / 1.4 / **N** — Jokhang Monastery | — |  |
| 10 | China | Tashilhunpo Monastery | 29.250, 88.883 (llm) | Y | amenity / 1.00 / 1.00 / 2.4 / **N** — Tashilhunpo Monastery | — |  |
| 11 | China | Guangning | 23.634, 112.433 (mapbox) |  | city / 1.00 / 1.00 / 0.2 / **N** — Guangning County | Street / 0.78 / 1845.3 / **W** | 1845 |
| 12 | China | Liannan and Lianshan mountains | 24.728, 112.282 (mapbox) |  | — | — |  |
| 13 | China | Wohushan Great Wall | 40.683, 117.167 (llm) |  | amenity / 0.00 / 1.00 / 467.0 / **W** — Wohushan Shuiku | — |  |
| 14 | India | Bhangarh village | 27.096, 76.288 (mapbox) | Y | city / 0.90 / 1.00 / 467.6 / **W** — Bhangarh | SubDistrict / 0.73 / 201.8 / **W** | 658 |
| 15 | India | ger camp *(generic)* | 18.518, 73.888 (null) | Y | amenity / 0.00 / 0.00 / 303.2 / **W** — Camp Church (Saint Mary Church) | — |  |
| 16 | India | Rangaji Temple | 27.575, 77.697 (llm) | Y | city / 0.00 / 0.00 / 2126.0 / **W** — Temple Jn | SubDistrict / 0.77 / 1644.6 / **W** | 597 |
| 17 | India | Bikaner | 28.016, 73.313 (mapbox) |  | city / 1.00 / 1.00 / 0.5 / **N** — Bikaner | Locality / 1.00 / 0.1 / **N** | 1 |
| 18 | India | Jaisalmer | 26.914, 70.912 (mapbox) |  | city / 1.00 / 1.00 / 0.2 / **N** — Jaisalmer | Locality / 1.00 / 0.7 / **N** | 1 |
| 19 | India | Saheliyon Ki Bari | 24.595, 73.685 (llm) |  | amenity / 1.00 / 1.00 / 0.9 / **N** — Saheliyon-Ki-Bari | District / 0.93 / 0.7 / **N** | 1 |
| 20 | Japan | fishing village *(generic)* | 37.500, 138.000 (null) | Y | amenity / 1.00 / 1.00 / 278.2 / **W** — Monument to Fukushima Fishing Village | SubDistrict / 0.71 / 119.2 / **W** | 281 |
| 21 | Japan | Nasu Imperial Villa | 37.019, 140.120 (mapbox) | Y | amenity / 1.00 / 1.00 / 11.4 / **N** — Nasu Imperial Villa | — |  |
| 22 | Japan | northern Okinawa fishing villages *(generic)* | 27.942, 128.201 (null) | Y | — | — |  |
| 23 | Japan | living reefs *(generic)* | 37.500, 138.000 (null) |  | amenity / 0.00 / 0.50 / 387.4 / **W** — LIVING HOUSE | — |  |
| 24 | Japan | Nago Pineapple Park | 26.589, 127.984 (mapbox) |  | amenity / 1.00 / 1.00 / 3.3 / **N** — Nago Pineapple Park | — |  |
| 25 | Japan | Takayama | 36.143, 137.256 (mapbox) |  | city / 1.00 / 1.00 / 0.6 / **N** — Takayama | Locality / 1.00 / 0.5 / **N** | 1 |
| 26 | Laos | cave complexes near Vang Vieng | 18.926, 102.448 (mapbox) | Y | city / 0.24 / 1.00 / 0.7 / **F** — Vang Vieng | — |  |
| 27 | Laos | Li Phi Waterfall | 13.983, 105.983 (llm) | Y | amenity / 0.00 / 1.00 / 8.4 / **N** — Li Phi Falls | — |  |
| 28 | Laos | Tham Ting and Tham Thueng caves | 19.889, 102.136 (null) | Y | — | — |  |
| 29 | Laos | Khone Phapheng Falls | 19.829, 104.538 (null) |  | amenity / 1.00 / 1.00 / 670.5 / **N** — Khone Phapheng Falls | — |  |
| 30 | Laos | Laos Buffalo Dairy | 19.305, 103.203 (null) |  | amenity / 1.00 / 1.00 / 138.6 / **N** — Laos Buffalo Dairy | PointOfInterest / 0.65 / 129.0 / **W** | 19 |
| 31 | Laos | local market *(generic)* | 19.304, 103.209 (null) |  | amenity / 1.00 / 1.00 / 248.6 / **W** — Local market | — |  |
| 32 | Mongolia | Khuvsgul Lake | 51.000, 100.500 (llm) | Y | amenity / 0.00 / 1.00 / 2.7 / **N** — Lake Khuvsgul | — |  |
| 33 | Mongolia | Terelj valley | 47.860, 107.451 (llm) | Y | amenity / 0.70 / 1.00 / 14.4 / **R** — Terelj Hotel | — |  |
| 34 | Mongolia | Yol Valley (Vulture Valley) | 43.517, 104.067 (llm) | Y | amenity / 0.00 / 1.00 / 0.7 / **N** — Yol | — |  |
| 35 | Mongolia | Chinggis Khan equestrian statue | 47.808, 107.536 (llm) |  | amenity / 0.00 / 0.33 / 46.7 / **W** — E Mart Chinggis | — |  |
| 36 | Mongolia | Khorgo Volcano crater | 48.180, 99.860 (llm) |  | amenity / 0.00 / 0.50 / 4.1 / **N** — khorgo | — |  |
| 37 | Mongolia | Turtle Rock | 47.860, 107.430 (llm) |  | amenity / 1.00 / 1.00 / 5.3 / **N** — Turtle Rock | — |  |
| 38 | Nepal | Annapurna South Base Camp | 28.531, 83.878 (null) | Y | city / 0.90 / 0.50 / 0.3 / **N** — Annapurna Base Camp | Locality / 0.41 / 334.1 / **W** | 334 |
| 39 | Nepal | Cho La Pass to Dzongla | 27.933, 86.783 (llm) | Y | street / 0.00 / 0.00 / 309.1 / **W** — Mohare Danda to Hampal pass | — |  |
| 40 | Nepal | Zatrwa La Pass | 27.667, 86.783 (llm) | Y | amenity / 0.90 / 1.00 / 2.6 / **N** — Zatrwa La | — |  |
| 41 | Nepal | Gorakshep (5,164m) | 28.000, 86.858 (llm) |  | amenity / 0.08 / 0.00 / 596.2 / **W** — CADRE Kailari 5 164m | District / 0.43 / 206.4 / **W** | 393 |
| 42 | Nepal | Koto to Meta | 28.633, 84.217 (llm) |  | city / 0.33 / 0.50 / 10.0 / **R** — Koto | District / 0.40 / 3.3 / **R** | 12 |
| 43 | Nepal | Phunki Tenga | 27.828, 86.758 (llm) |  | — | District / 0.36 / 483.5 / **W** |  |
| 44 | South Korea | Hahoe Folk Village, Andong | 36.565, 128.726 (null) | Y | amenity / 0.75 / 0.50 / 3.6 / **W** — Andong Folk Village | — |  |
| 45 | South Korea | Hanok Village, Jeonju | 35.822, 127.148 (mapbox) | Y | amenity / 0.81 / 0.50 / 0.9 / **N** — Hanok Maeul Village | Locality / 0.33 / 0.6 / **F** | 2 |
| 46 | South Korea | village center *(generic)* | 36.500, 127.800 (null) | Y | amenity / 1.00 / 1.00 / 131.8 / **W** — Seorae Global Village Center | — |  |
| 47 | South Korea | Daehan Dawon | 34.772, 127.080 (llm) |  | city / 0.50 / 0.50 / 144.5 / **W** — Daehan | — |  |
| 48 | South Korea | Dolce Hotel or glamping site *(generic)* | 36.500, 127.800 (null) |  | — | — |  |
| 49 | South Korea | Soesokkak Estuary | 33.253, 126.519 (llm) |  | — | — |  |
| 50 | Sri Lanka | Kelaniya Temple | 6.950, 79.917 (null) | Y | amenity / 1.00 / 1.00 / 0.2 / **N** — Kelaniya Temple | Locality / 0.57 / 0.7 / **F** | 1 |
| 51 | Sri Lanka | Koneshwara Hindu temple | 8.577, 81.234 (llm) | Y | amenity / 0.67 / 0.00 / 189.8 / **W** — hindu temple | — |  |
| 52 | Sri Lanka | Ritigala Monastery | 7.374, 80.139 (null) | Y | amenity / 0.81 / 1.00 / 101.0 / **N** — Ritigala Ancient Buddhist Monastery | District / 0.47 / 97.4 / **F** | 4 |
| 53 | Sri Lanka | Back of Beyond Dehigaha Ela Eco Lodge | 6.380, 80.310 (null) |  | — | — |  |
| 54 | Sri Lanka | Balapitiya | 6.276, 80.039 (mapbox) |  | city / 1.00 / 1.00 / 0.5 / **N** — Balapitiya | Locality / 1.00 / 0.5 / **N** | 1 |
| 55 | Sri Lanka | Galle | 6.026, 80.218 (mapbox) |  | city / 1.00 / 1.00 / 0.8 / **N** — Galle | Locality / 1.00 / 0.9 / **N** | 0 |
| 56 | Taiwan | Golden Waterfalls | 25.107, 121.858 (llm) | Y | amenity / 0.00 / 1.00 / 116.3 / **W** — Golden Grotto | — |  |
| 57 | Taiwan | Laomei River (Dream Valley), New Taipei City | 25.288, 121.547 (mapbox) | Y | county / 0.00 / 0.50 / 46.2 / **F** — New Taipei | District / 0.54 / 0.3 / **N** | 46 |
| 58 | Taiwan | Taipingshan Villa | 24.517, 121.633 (llm) | Y | city / 0.90 / 1.00 / 10.1 / **R** — Taipingshan | District / 0.44 / 149.2 / **W** | 141 |
| 59 | Taiwan | Caoling Historic Trail | 25.033, 121.917 (llm) |  | — | Street / 0.65 / 202.0 / **W** |  |
| 60 | Taiwan | Jancing Historic Trail | 24.502, 121.451 (llm) |  | — | Street / 0.65 / 132.5 / **W** |  |
| 61 | Taiwan | Taiwan Hemlock Trail | 24.501, 121.454 (llm) |  | — | — |  |
| 62 | Thailand | Cheow Lan Lake | 8.928, 98.907 (llm) | Y | amenity / 1.00 / 1.00 / 32.7 / **N** — cheow lan lake | — |  |
| 63 | Thailand | Erawan Waterfall | 14.372, 99.153 (llm) | Y | amenity / 1.00 / 1.00 / 1.0 / **N** — Erawan Waterfall | Locality / 0.40 / 447.9 / **W** | 449 |
| 64 | Thailand | Koh Phi Phi village | 7.683, 98.766 (mapbox) | Y | city / 0.23 / 1.00 / 1038.7 / **W** — Ban Phai Koh Don | — |  |
| 65 | Thailand | Chinatown | 13.740, 100.514 (llm) |  | street / 1.00 / 1.00 / 587.3 / **W** — Chinatown | District / 1.00 / 0.6 / **N** | 587 |
| 66 | Thailand | Houay Fai | 18.805, 100.788 (null) |  | amenity / 0.00 / 0.50 / 450.0 / **W** — Houay Nangxot | — |  |
| 67 | Thailand | Sukhothai Historical Park | 17.017, 99.703 (llm) |  | amenity / 1.00 / 1.00 / 0.4 / **N** — Sukhothai Historical Park | PointOfInterest / 1.00 / 0.5 / **N** | 0 |
| 68 | Vietnam | An Binh Island | 10.012, 105.749 (mapbox) |  | city / 0.00 / 0.50 / 1165.0 / **W** — Thái Bình Ward | District / 0.50 / 146.0 / **W** | 1068 |
| 69 | Vietnam | Chau Doc | 10.709, 105.118 (mapbox) |  | city / 1.00 / 1.00 / 0.1 / **N** — Châu Đốc | Locality / 1.00 / 0.3 / **N** | 0 |
| 70 | Vietnam | Ho Chi Minh City | 10.776, 106.702 (mapbox) |  | city / 1.00 / 1.00 / 1.6 / **N** — Ho Chi Minh City | SubRegion / 1.00 / 0.1 / **N** | 2 |

### Cost
- Amazon Location: 71 Geocode + 8 SearchText = **79 SingleUse requests**, all in the `Core` bucket at $0.50/1k, about **$0.04**.
- Geoapify: 71 free-tier requests, $0.
