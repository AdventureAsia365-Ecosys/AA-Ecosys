---
id: PROD-01-geocode-audit-s254
title: "Geocode audit of CIS place names (S254)"
description: "Read-only audit of geo.place_name on Dev: about 75% of resolved pins correct, Geoapify about 91% vs LLM-proposed coordinates 53-60%, 1,621 unresolved names classified, and a ranked 8-step fix plan."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-cis]
last_reviewed: 2026-10-28
review_every_days: 180
related: [AA-990]
---

# Geocode audit of CIS place names (S254, 28/10/2026)

Read-only audit of `geo.place_name` on Dev. Nothing was pushed, merged, run against the DB or migrated, and no paid
geocoder or LLM call was made: cost $0. The verification verdicts come from agent judgement (own geographic knowledge),
not from a second geocoder. Treat them as a careful reviewer's read, not ground truth.

Files in this folder:

| file | what |
|---|---|
| `README.md` | this report |
| `verified.json` | the 600 verified rows: every input field (point, ISO, precision, provider, flags, rule detail) plus `verdict`, `expected`, `note`, `cause` |
| `flags-summary.json` | rule counts, overlaps, provenance breakdown, verification rates, the two overall estimates, projected counts |
| `unresolved_classified.json`, `classify_unresolved.py` | classification of the 1,621 unresolved names (§6) |
| `rules.py`, `join_verified.py`, `build_report.py` | the scripts. They read `place_names.json` / `flags.json` / `shard-*.json` from `.tmp-session/S254/geoaudit/` (not committed: 6 MB dump), so rerun them from there |

## 1. Answer first

- **About 75 % of resolved names have a correct pin** (95 % interval about 71–80 %). About 21 % are wrong in some way
  (interval 17–25 %); the remaining ~4 % could not be judged. Two independent stratifications give the same answer:
  by flag status 75.4 % [71.2, 79.6] and by provenance 74.8 % [70.9, 78.6].
- **Provenance is the real predictor, not the rules.** Rows located by Geoapify are ~91 % correct (114/125 in the random
  sample). Rows whose coordinates were proposed by the LLM are ~53–60 % correct (40/75 in the random sample, 199/333 across
  all verified). The 3,770 LLM-located rows hold roughly 1,400 of the ~1,700 estimated bad pins (about 83 %).
- **The rule flags barely separate good rows from bad ones.** Error rate is 19 % in the random unflagged sample and 26 %
  in the 400 highest-risk flagged rows. Only `precision_area_site` (36 %) and `dup_coords` (29 %) are clearly above the
  baseline; `provenance_null` (14 %) is below it.
- **Top error types** (verified rows; projected count over 7,924 in brackets): off-target LLM coordinate in the right
  region 45; town/area centroid instead of the site 44 [~500]; not a place 28 [~300]; homonym resolved in the wrong city
  20; Hong Kong/Macau stored as CN 4 (20 rows in the data).
- **Unresolved 1,621 names**: about half are extraction garbage (descriptions, route legs, generic words, non-places),
  about 690 are real places the LLM did not know. One fix pattern covers most of it: filter at extraction, then a
  geocoder-only fallback checked against the tour route.

## 2. Scope

| | rows |
|---|---|
| `geo.place_name` total | 9,545 |
| resolved (audited by rules + verification) | 7,924 |
| pending | 1,203 (746 of them already on try 2) |
| unknown | 418 |

Resolved rows by provenance:

| geocoder_provider / located_by | precision | rows |
|---|---|---|
| geoapify / geoapify | point 3,721, line 164, area 59 | 3,944 |
| geoapify / llm | area 3,205, line 123 | 3,328 |
| null / llm | null 439, line 3 | 442 |
| null / mapbox | null | 210 |

## 3. Method

1. **Dump** (read-only) of `geo.place_name` joined to the destination row: name, tour, tour country, locality,
   status, point, ISO, precision, confidence, provider, `located_by`, review reason.
2. **Rules** (`rules.py`, stdlib, no network) over the 7,924 resolved rows:
   - `bbox`: point outside the bounding box of its own ISO country.
   - `null_island` / `zero_coords` / `swapped_sign`: degenerate coordinates.
   - `country`: place ISO not equal to and not a neighbour of the tour's country (neighbour map includes common
     combined-tour pairs).
   - `tour_spread`: point far from the tour's median point (km in `detail`).
   - `dup_coords`: 3 or more distinct names on one coordinate. The group is skipped only when every row has the same
     non-null locality; 7,818 of 7,924 rows have no locality, so in practice the rule nearly always fires.
   - `precision_area_site`: `geo_precision = area` but `name_norm` contains a whole-word site keyword (temple, museum,
     gate, hut, fort, ...).
   - `provenance_null`: `geocoder_provider` is null.
3. **Verification sample**: the 400 flagged rows with the highest risk score (all 297 country/spread rows, then
   dup_coords, precision, provenance) plus 200 random unflagged rows (seed 254), shuffled into 10 shards of 60.
   Each row got one verdict: `correct`, `too_coarse` (right area, generic centroid instead of the named site),
   `wrong_place`, `wrong_country` (point right, ISO wrong, or point in the wrong country), `not_a_place`, `unsure`.
   Tolerance: a site within ~2–4 km, a village or town within ~5 km, an area or line with the point inside the feature.
4. **Estimates**: stratified by flag status (unflagged stratum from the random sample, flagged stratum from the 400)
   and, as a cross-check, by `located_by` × flagged. Finite-population correction applied. The 1,921 flagged rows that
   were not verified are assumed to behave like the verified 400; those 400 were picked as highest risk, so this
   errs toward pessimism.

## 4. Rule results

| flag | rows |
|---|---|
| dup_coords | 927 (243 coordinate groups) |
| precision_area_site | 755 |
| provenance_null | 652 |
| tour_spread | 260 |
| country | 38 |
| bbox | 0 |
| null_island / zero_coords / swapped_sign | 0 |
| **rows with at least one flag** | **2,321** |

- **bbox**: all 22 ISO codes in the data have a box; no row falls outside its own box. Gross errors (swapped sign,
  null island, other continent) are absent.
- **country (38)**, three groups:
  - 24 TZ places in two Kilimanjaro tours (Machame, Marangu) whose source country is "India". Coordinates are TZ and
    right; the tour country in the source data is wrong.
  - 13 VN places in Bangkok → Ho Chi Minh City cycling tours stored as "Thailand". A true cross-border tour (via
    Cambodia); flagged only because VN is not a TH neighbour in the map.
  - 1 NP point in the Pakistan tour "Islamabad, Peshawar, Swat, Kalash and Hunza" (`himalayas` → Pokhara): a real error.
- **Cross-border accepted as neighbour**: 443 rows (largest: CN in Nepal tours 116, VN in Laos tours 72, KH in
  Thailand tours 51). These are expected for Kailash, Laos–Vietnam and Angkor itineraries.
- **dup_coords** is mostly a specific site placed on its town centre: 14 Jaipur names on 26.9124, 75.7873; 12 Luang
  Prabang names on one point; Kailash kora monasteries and passes stacked on the summit (9 names) and one other point.

Flag combinations:

| combination | rows | | pair | rows |
|---|---|---|---|---|
| dup_coords only | 679 | | dup & precision | 113 |
| precision_area_site only | 619 | | dup & provenance | 104 |
| provenance_null only | 522 | | dup & spread | 44 |
| tour_spread only | 168 | | provenance & spread | 35 |
| dup + precision | 110 | | precision & spread | 25 |
| dup + provenance | 94 | | | |
| country only | 35 | | | |
| dup + spread | 31 | | | |
| provenance + spread | 25 | | | |
| precision + spread | 22 | | | |
| dup + provenance + spread | 10 | | | |
| dup + precision + spread | 3 | | | |
| country + provenance / + precision / + spread | 1 each | | | |

## 5. Verification results

### 5.1 Accuracy

| group | n | correct | errors | unsure | correct rate (95 % CI) | error rate (95 % CI) |
|---|---|---|---|---|---|---|
| random unflagged sample | 200 | 154 | 38 | 8 | 77.0 % (70.7–82.3) | 19.0 % (14.2–25.0) |
| flagged, top-400 by risk | 400 | 286 | 103 | 11 | 71.5 % (66.9–75.7) | 25.8 % (21.7–30.3) |
| **all resolved, flag-stratified** | 7,924 | | | | **75.4 % (71.2–79.6)** | **21.0 % (17.0–24.9)** |
| all resolved, provenance-stratified | 7,924 | | | | 74.8 % (70.9–78.6) | 21.5 % (17.9–25.2) |

Verdict counts:

| verdict | random 200 | flagged 400 | projected over 7,924 |
|---|---|---|---|
| correct | 154 | 286 | ~5,970 |
| wrong_place | 19 | 44 | ~790 |
| too_coarse | 11 | 33 | ~500 |
| not_a_place | 6 | 22 | ~300 |
| wrong_country | 2 | 4 | ~80 |
| unsure | 8 | 11 | ~290 |

The projection scales each stratum's verdict mix to its population; the margin on each line is about ±30 % of the value.

### 5.2 By provenance (the strongest signal)

| located_by | resolved rows | verified | correct (all verified) | correct (random sample) |
|---|---|---|---|---|
| geoapify | 3,944 | 258 | 90.3 % | 91.2 % (114/125) |
| llm | 3,770 | 333 | 59.8 % | 53.3 % (40/75) |
| mapbox | 210 | 9 | 8/9 | — |

- LLM-located rows are almost all `geo_precision = area` and carry LLM-written coordinates. 804 of them have
  coordinates rounded to two decimals or fewer; those are 54 % correct against 61 % for 3–4 decimals, so rounding is
  a weak extra signal.
- Geoapify errors are a different kind: the right name matched to the wrong POI (Princess Street in Mumbai instead of
  Fort Kochi, National Gandhi Museum in Delhi instead of Madurai, Shaanxi History Museum's Xianyang branch, the
  Annapurna rural municipality instead of the peak).

### 5.3 Error rate per rule (flagged 400)

| flag | verified | error rate | comment |
|---|---|---|---|
| precision_area_site | 129 | 35.7 % | best rule: mostly centroids standing in for a named site |
| dup_coords | 147 | 28.6 % | same pattern; fires on legitimate town names too |
| country | 38 | 26.3 % | 24 of 38 are a source-data country error, not a geocode error; only 1 real wrong_country (`himalayas`) |
| tour_spread | 260 | 22.7 % | barely above the 19 % baseline; long or multi-country tours trip it by design |
| provenance_null | 36 | 13.9 % | below baseline; null provider is a bookkeeping gap, not a quality signal |

### 5.4 Error types

| cause | verified rows | examples |
|---|---|---|
| Off-target coordinate in the right region (mostly LLM-proposed, 5–100 km off) | 45 | Kilimanjaro huts and gates 25–55 km off (Mandara, Barafu, Marangu Gate); Kong Lor cave 70 km off; Jait Sagar ~100 km W of Bundi; Qiao Family Compound 30 km off |
| Centroid instead of the site (`too_coarse`) | 44 | Kailash kora monasteries on the summit pin; Gyantse Kumbum/Pelkor Chode on the town centroid; Karni Mata (Deshnoke) on Bikaner; Angkor Thom on Siem Reap |
| Not a place | 28 | route legs (`border to chau doc`, `lhasa to gyantse`), hotels (`hotel in seoul`, `... or similar`), activities (`jaipur balloon ride`), people (`tsaatan family`), two sites in one name |
| Homonym resolved in the wrong city | 20 | City Wall / Bell and Drum Tower → Beijing on Xi'an tours; Grand Canal → central Shanghai; San Agustin Church → Palawan instead of Intramuros; Victory Square → Urumqi instead of Bishkek |
| Hong Kong / Macau stored as CN | 4 | `hong kong`, `central hong kong`, `shum shui po`, `yuen po street bird market`. All 13 rows in the HK box and all 7 in the Macau box carry CN |

Other systematic defects found while verifying:

- **Name normalisation drops a leading "An"** as if it were an article: `An Binh Island` → `binh island` (now pinned
  near Can Tho, 35 km off), `An Ping Old Street` → `ping old street`. 25 rows lose a leading "an"; most are real
  articles, but Vietnamese/Chinese proper nouns starting with "An" are broken.
- **Source tour country errors**: the two Kilimanjaro tours are stored as India; "Bhutan Cultural Tour" carries Nepal.
  Per the S252 rule (tour country = source Excel row) this is a content correction, not a geocoder fix.

### 5.5 Wrong rows (wrong_country, wrong_place, too_coarse: 113)

Current point is `lat, lng ISO (located_by/precision)`.

| # | verdict | name | tour | current point | expected |
|---|---|---|---|---|---|
| 1 | wrong_country | central hong kong | Highlights of China: Shanghai, Beijing, Xi'an… | 22.2796, 114.1627 CN (llm/area) | Same point, country_iso2 HK |
| 2 | wrong_country | himalayas | Islamabad, Peshawar, Swat, Kalash and Hunza T… | 28.1809, 83.9317 NP (geoapify/point) | Pakistan side of the range, e.g. Nanga Parbat area ~35.24, 74.59 |
| 3 | wrong_country | hong kong | Beijing to Hong Kong Route — 13 Days | 22.3193, 114.1694 CN (llm/null) | Same coords (22.32,114.17); ISO2 should be HK |
| 4 | wrong_country | shum shui po | Hong Kong Walking Tour — 1 Day | 22.3300, 114.1600 CN (llm/area) | Same point (22.33, 114.16), but country_iso2 HK |
| 5 | wrong_country | victory square | Cultural tour of Kazakhstan, Kyrgyzstan and C… | 43.9000, 87.6300 CN (llm/area) | Victory Square, Bishkek, KG, about 42.868,74.604 |
| 6 | wrong_country | yuen po street bird market | Hong Kong Island and Kowloon Guided Tour — 1 … | 22.3259, 114.1738 CN (geoapify/point) | Same coords (Mong Kok, 22.325,114.174); ISO2 should be HK |
| 7 | wrong_place | 400 year old residence of the gao family | Tibet: Beijing to Kathmandu — 21 Days | 37.8706, 112.5489 CN (llm/area) | Gao Family Mansion, Muslim Quarter, Xi'an ~34.265, 108.942 |
| 8 | wrong_place | ancient city wall | Tibet Encompassed — 14 Days | 29.6500, 91.1167 CN (llm/area) | Xi'an City Wall ~34.26,108.95 |
| 9 | wrong_place | ancient city wall | Beijing to Xi'an: Terracotta Warriors, City W… | 39.8983, 116.4175 CN (llm/area) | Xi'an City Wall, about 34.26, 108.94 |
| 10 | wrong_place | barafu | Kilimanjaro Trek via the Machame Route — 8 Da… | -3.4667, 37.0000 TZ (llm/area) | Barafu Camp, Kilimanjaro, about -3.095, 37.372 |
| 11 | wrong_place | barafu hut | Kilimanjaro Trek via the Machame Route — 8 Da… | -3.4667, 37.0000 TZ (llm/area) | Barafu Camp ~-3.10, 37.37 |
| 12 | wrong_place | bell and drum tower | Silk Road China Tour — 15 Days | 39.9387, 116.3954 CN (llm/null) | Xi'an Bell & Drum Towers ~34.261, 108.943 |
| 13 | wrong_place | binh island | Bangkok to Ho Chi Minh City by Bicycle — 14 D… | 10.0124, 105.7488 VN (mapbox/null) | An Binh Island, Vinh Long ~10.26, 105.96 |
| 14 | wrong_place | bird nest | China Adventure: Beijing to Hong Kong — 20 Da… | 39.9363, 116.3976 CN (geoapify/point) | Beijing National Stadium (Bird's Nest), ~39.993, 116.397 |
| 15 | wrong_place | buddha park | Sikkim Honeymoon Tour: Gangtok, Lachung and P… | 27.3333, 88.6167 IN (llm/area) | Buddha Park (Tathagata Tsal), Ravangla ~27.30, 88.36 |
| 16 | wrong_place | chiang mais man made canyon | Northern Thailand Adventure — 14 Days | 18.7061, 99.0267 TH (llm/area) | Grand Canyon Chiang Mai, Hang Dong ~18.697, 98.892 |
| 17 | wrong_place | chonggu monastery | West Sichuan: Chengdu, Kangding and Yading Na… | 28.4500, 99.9167 CN (llm/area) | Chonggu Temple, Yading Nature Reserve ~28.45, 100.34 |
| 18 | wrong_place | chui gompa | Kailash and Guge Kingdom Tour — 14 Days | 31.0667, 81.3167 CN (llm/area) | Chiu Gompa, NW shore of Lake Manasarovar, about 30.77,81.30 (CN) |
| 19 | wrong_place | city wall | China by Bike — 16 Days | 39.9042, 116.3912 CN (llm/area) | Xi'an City Wall ~34.259, 108.947 |
| 20 | wrong_place | dharma cave | China Explorer: Beijing, Xi'an, Huashan, Luoy… | 34.4833, 110.0833 CN (llm/area) | Bodhidharma Cave, Wuru Peak above Shaolin Temple ~34.515, 112.94 |
| 21 | wrong_place | dilwara jain temples | Rajasthan Heritage Tour — 22 Days | 24.7832, 72.7855 IN (geoapify/point) | Dilwara Temples, Mount Abu, ~24.609, 72.723 |
| 22 | wrong_place | doi mae salong | Thailand & Cambodia: Bike, Kayak & Trek — 12 … | 20.2667, 99.6333 TH (llm/null) | Mae Salong (Santikhiri) ~20.165, 99.62 |
| 23 | wrong_place | ganden kora | Mount Kailash Journey from Lhasa — 14 Days | 29.8833, 91.4833 CN (llm/area) | Ganden Monastery ~29.757, 91.474 |
| 24 | wrong_place | grand canal | Beijing to Hong Kong via Zhangjiajie and Yang… | 31.2310, 121.4740 CN (llm/line) | A Grand Canal section, e.g. Suzhou ~31.30, 120.60 or Hangzhou ~30.32, 120.14 |
| 25 | wrong_place | grand canal | China Highlights: Beijing, Xi'an, Shanghai an… | 31.2304, 121.4737 CN (llm/line) | Grand Canal at Suzhou ~31.30, 120.60 |
| 26 | wrong_place | grand canal of china | Beijing to Hong Kong via Zhangjiajie and Yang… | 36.0000, 113.0000 CN (llm/line) | A Grand Canal section on the route, e.g. Hangzhou ~30.32, 120.14 or Suzhou ~31.30, 120.60 |
| 27 | wrong_place | guheshwori shaktipeeth | Best of Nepal: Kathmandu, Pokhara and Chitwan… | 27.6785, 85.4415 NP (geoapify/point) | Guhyeshwari Temple near Pashupatinath, Kathmandu ~27.7106, 85.3540 |
| 28 | wrong_place | hunters school in kiwit village | Taiwan's East Coast: Indigenous Trails, Templ… | 23.9667, 121.5833 TW (llm/area) | Kiwit (Qimei) Amis village, Ruisui, Hualien ~23.49, 121.38 |
| 29 | wrong_place | immaculate conception cathedral | Philippines Highlands to Islands: Manila, Ban… | 10.1833, 118.9833 PH (llm/area) | Puerto Princesa Cathedral ~9.740, 118.735 (or Manila Cathedral 14.592, 120.974) |
| 30 | wrong_place | jait sagar lake | Rajasthan Festival Circuit — 15 Days | 25.4167, 74.6333 IN (llm/area) | Jait Sagar Lake, Bundi ~25.46, 75.645 |
| 31 | wrong_place | janardanaswamy temple | Delhi to Kochi: Taj Mahal, Rajasthan, Goa and… | 8.5833, 76.9167 IN (llm/area) | Janardana Swamy Temple, Varkala ~8.734, 76.708 |
| 32 | wrong_place | jiksun village | Rupin Pass Trek — 8 Days in the Himachal Hima… | 31.4167, 77.8167 IN (llm/area) | Jiskun, Rupin valley, Uttarakhand, about 31.19,78.0 |
| 33 | wrong_place | jinshan park | Beijing, Hangzhou and Shanghai Cultural Tour … | 39.9950, 116.3913 CN (llm/area) | Jingshan Park, Beijing ~39.925, 116.397 |
| 34 | wrong_place | khichan | Rajasthan: Palaces, Forts & Desert — 20 Days | 27.0833, 72.6833 IN (llm/area) | Khichan village near Phalodi, about 27.135, 72.41 |
| 35 | wrong_place | konglor water cave | Pakse to Vientiane Cycling via the Thakhek Lo… | 17.3167, 104.5667 LA (llm/area) | Kong Lor cave, Khammouane, about 17.98,104.80 |
| 36 | wrong_place | lad koh | Thailand: Temples, Hilltribes & Gulf Islands … | 9.7451, 100.0249 TH (geoapify/point) | Lad Koh viewpoint, Koh Samui (Chaweng-Lamai road) ~9.50, 100.06 |
| 37 | wrong_place | mandara hut | Mount Kilimanjaro Trek via the Marangu Route,… | -3.0500, 37.2833 TZ (llm/area) | Mandara Hut, Marangu route ~-3.14, 37.51 (SE slope) |
| 38 | wrong_place | mao zedong mausoleum | China by Bike — 16 Days | 39.9327, 116.3065 CN (geoapify/point) | Tiananmen Square, Beijing ~39.899, 116.391 |
| 39 | wrong_place | marangu gate | Mount Kilimanjaro Trek via the Marangu Route,… | -3.2500, 37.2167 TZ (llm/area) | Marangu Gate, Kilimanjaro NP ~-3.237, 37.523 |
| 40 | wrong_place | minaret | Cycle Xinjiang — 13 Days | 42.9400, 89.5300 CN (llm/area) | Emin Minaret, Turpan ~42.919, 89.214 |
| 41 | wrong_place | monster city | Cycle Xinjiang — 13 Days | 45.5900, 85.6700 CN (llm/area) | Urho (Wuerhe) Ghost/Devil City ~46.10,85.72 |
| 42 | wrong_place | mount li | China by Bike — 16 Days | 34.2167, 109.5833 CN (llm/area) | Lishan, Lintong (Xi'an) ~34.35,109.22 |
| 43 | wrong_place | mt annapurna | Annapurna Base Camp Trek with Poon Hill — 16 … | 28.4234, 83.7371 NP (geoapify/point) | Annapurna I summit, about 28.596, 83.820 |
| 44 | wrong_place | mt lishan | China by Bike — 16 Days | 34.2167, 109.5667 CN (llm/area) | Li Mountain (Lishan), Lintong, Xi'an ~34.36, 109.23 |
| 45 | wrong_place | mt palay palay | Birding in Manila, Mt. Makiling, Villa Escude… | 14.3667, 120.8833 PH (llm/area) | Mt Palay-Palay/Pico de Loro, Ternate-Nasugbu, about 14.22,120.64 |
| 46 | wrong_place | mt shibaoshan | Beijing, Hangzhou and Shanghai Cultural Tour … | 26.4700, 99.8700 CN (llm/area) | Baoshi Hill (Baoshishan, Baochu Pagoda), West Lake, Hangzhou ~30.262, 120.146 |
| 47 | wrong_place | muthurajawela wetland | Sri Lanka Leisure Tour: Kotugoda, Kalupahana … | 6.8961, 79.9104 LK (geoapify/point) | Muthurajawela marsh, Wattala/Ja-Ela ~7.05, 79.89 |
| 48 | wrong_place | national gandhi museum | South India: Chennai to Kochi — 13 Days | 28.6388, 77.2458 IN (geoapify/point) | Gandhi Memorial Museum, Madurai ~9.930, 78.138 |
| 49 | wrong_place | oketsu giants kettles | Shima Onsen by Rental Bicycle — 2 Days (1 Nig… | 36.6200, 138.6300 JP (llm/area) | Shima no Oketsu potholes on the Shima river, Nakanojo ~36.66, 138.79 |
| 50 | wrong_place | pakxang | Laos: Oudomxay Province Cycling — 8 Days, Dir… | 18.3700, 103.6500 LA (llm/area) | Likely Pak Xeng (Luang Prabang/Oudomxay area), ~20.2, 102.6 |
| 51 | wrong_place | phou khoun | Laos & Central Vietnam by Bike: Luang Prabang… | 19.6833, 102.2167 LA (llm/area) | Phou Khoun town (Rt 13/Rt 7 junction) ~19.45, 102.44 |
| 52 | wrong_place | pingan | South China: Hong Kong to Chengdu — 8 Days | 24.6167, 110.1000 CN (llm/area) | Ping'an village, Longji terraces, about 25.757, 110.127 |
| 53 | wrong_place | princess street | Southern India: Kochi to Kochi — 15 Days | 18.9466, 72.8217 IN (geoapify/line) | Princess Street, Fort Kochi, ~9.966, 76.242 |
| 54 | wrong_place | qiao family compound | Beijing to Hong Kong Overland Tour — 16 Days | 37.5333, 112.1333 CN (llm/area) | Qiao Family Compound, Qi County ~37.42, 112.43 |
| 55 | wrong_place | qiaos family mansion | Beijing to Hong Kong Overland Tour — 16 Days | 37.5333, 112.1333 CN (llm/area) | Qiao Family Compound, Qiaojiabao, Qi County, Shanxi, ~37.40, 112.43 |
| 56 | wrong_place | qiaotou | China Tour: Beijing, Xi'an, Yunnan, Guilin an… | 26.8700, 99.9800 CN (llm/area) | Qiaotou (Hutiaoxia town), Tiger Leaping Gorge ~27.21, 100.10 |
| 57 | wrong_place | railway market | Thailand: Rail, Ruins & Rainforest — 13 Days | 13.6917, 100.3167 TH (llm/area) | Maeklong Railway Market, Samut Songkhram, about 13.407, 100.000 |
| 58 | wrong_place | ruing village | Bagini Glacier Trek — 8 Days | 30.5167, 79.9833 IN (llm/area) | Ruing village near Jumma, Dhauliganga valley, Chamoli ~30.59, 79.77 |
| 59 | wrong_place | san agustin church | Palawan Circuit: Manila, Coron, El Nido and P… | 9.9833, 118.7333 PH (llm/area) | San Agustin Church, Intramuros, Manila ~14.589, 120.975 |
| 60 | wrong_place | savitri devi temple | India and Sri Lanka Experience — 24 Days | 26.4900, 74.0200 IN (llm/area) | Savitri Mata Temple, Ratnagiri hill, Pushkar ~26.478, 74.545 |
| 61 | wrong_place | shaanxi history museum | China Golden Triangle: Beijing, Xi'an and Sha… | 34.4080, 108.8595 CN (geoapify/point) | Shaanxi History Museum (main), Xiaozhai, Xi'an ~34.224, 108.954 |
| 62 | wrong_place | shaxi old town | China Tour: Beijing, Xi'an, Yunnan, Guilin an… | 26.5400, 99.9000 CN (llm/area) | Shaxi (Sideng) ~26.32, 99.85 |
| 63 | wrong_place | shennv valley the goddess stream | Tibet Encompassed — 14 Days | 31.0500, 110.3667 CN (llm/area) | Shennv Xi (Goddess Stream), Wu Gorge, Wushan ~31.04, 110.15 |
| 64 | wrong_place | shizhongshan grottoes | China Tour: Beijing, Xi'an, Yunnan, Guilin an… | 26.8833, 99.9167 CN (llm/area) | Shizhong Temple grottoes in Shibaoshan, Jianchuan ~26.39, 99.80 |
| 65 | wrong_place | tomb of itmad ud daulah | Rajasthan Desert Tour from Delhi | 27.9925, 78.0264 IN (llm/area) | Itmad-ud-Daulah tomb, Agra ~27.193, 78.031 |
| 66 | wrong_place | tuyuq ancient village | Cultural tour of Kazakhstan, Kyrgyzstan and C… | 42.8500, 89.9500 CN (llm/area) | Tuyoq village ~42.86,89.69 |
| 67 | wrong_place | waikkal | Sri Lanka: Beach, Reefs & Wilpattu Wildlife —… | 7.5167, 79.9667 LK (llm/area) | Waikkal, north of Negombo, about 7.28,79.85 |
| 68 | wrong_place | wat tham pla | Thailand by Water, Rail & Trail — 9 Days | 20.0167, 99.8833 TH (llm/area) | Wat Tham Pla (monkey cave temple), Mae Sai district, ~20.33, 99.87 |
| 69 | wrong_place | zuthulphuk monastery | Tibet: Beijing to Kathmandu — 21 Days | 30.7167, 81.3167 CN (llm/area) | Zutulpuk Monastery, Kailash kora ~31.10, 81.36 |
| 70 | too_coarse | angkor thom | Laos to Cambodia by Bicycle: Plateau Coffee, … | 13.3591, 103.8611 KH (geoapify/point) | Angkor Thom (Bayon) ~13.441, 103.859 |
| 71 | too_coarse | aryabal meditation temple | Central Mongolia — 7 Days, 6 Nights | 47.8333, 107.4667 MN (llm/area) | Aryapala temple, Terelj ~47.96, 107.45 |
| 72 | too_coarse | bunun slate stone house | Walami Trail Trek, Yushan National Park — 2 D… | 23.4700, 121.0000 TW (llm/area) | Walami Trail area ~23.35, 121.18 |
| 73 | too_coarse | cave of bhagwabasa | Roopkund Trek — 8 Days | 30.2333, 79.6667 IN (llm/area) | Bhagwabasa ~30.255, 79.72 |
| 74 | too_coarse | clock tower markets | Rajasthan Festival Circuit — 15 Days | 26.2389, 73.0243 IN (llm/area) | Ghanta Ghar/Sardar Market, Jodhpur, about 26.294,73.024 |
| 75 | too_coarse | dirakpuk monastery | Mount Kailash Journey from Lhasa — 14 Days | 31.0667, 81.3167 CN (llm/area) | Drira Phuk Monastery, north face of Kailash ~31.105, 81.295 |
| 76 | too_coarse | dirapuk monastery | Mount Kailash Journey from Lhasa — 14 Days | 31.0667, 81.3167 CN (llm/area) | Dirapuk Gompa on the north side of the kora, ~31.11, 81.30 |
| 77 | too_coarse | drolma la pass | Tibet: Beijing to Kathmandu — 21 Days | 31.0667, 81.3167 CN (llm/area) | Drolma La ~31.10, 81.34 |
| 78 | too_coarse | dzong fort | Tibet Express: Lhasa, Gyantse and Shigatse — … | 28.9167, 89.6000 CN (llm/area) | Gyantse Dzong ~28.962,89.601 (or Shigatse Dzong ~29.272,88.880) |
| 79 | too_coarse | guanwu waterfall trail | Guanwu National Forest Guided Day Tour from T… | 24.6700, 121.1700 TW (llm/area) | Guanwu Waterfall trail, Guanwu NFRA ~24.505, 121.115 |
| 80 | too_coarse | jami masjid | Hyderabad to Mumbai: Heritage Cities of South… | 16.8302, 75.7100 IN (llm/area) | Jama Masjid, Vijayapura ~16.825, 75.727 |
| 81 | too_coarse | jewish quarter | Delhi to Kochi: Taj Mahal, Rajasthan, Goa and… | 9.9816, 76.2590 IN (llm/area) | Jew Town, Mattancherry ~9.957, 76.259 |
| 82 | too_coarse | kali gandaki gorge | Pokhara Jomsom Muktinath Trek — 9 Days | 28.6500, 83.5000 NP (llm/area) | Gorge at Lete/Ghasa, about 28.63,83.62 |
| 83 | too_coarse | kanta elephant sanctuary | Thailand: Temples, Hilltribes & Gulf Islands … | 18.7667, 98.9333 TH (llm/area) | — |
| 84 | too_coarse | karni devi temple | Rajasthan Tour from Delhi: Agra, Jaipur, Udai… | 28.0229, 73.3119 IN (llm/area) | Karni Mata Temple, Deshnoke ~27.79, 73.34 |
| 85 | too_coarse | karola glacier | Highlights of Tibet: Beijing to Lhasa — 13 Da… | 28.9833, 90.2333 CN (llm/area) | Karo La glacier by the G349 road, about 28.92,90.10 |
| 86 | too_coarse | khaling national institute for the disabled | Motorcycle Cross Country, Bhutan — 11 Days | 27.0500, 91.6833 BT (llm/area) | Muenselling Institute, Khaling town, about 27.20,91.55 |
| 87 | too_coarse | khone phapheng cascade falls | Southern Laos: Plateau, Temple & Mekong — 5 D… | 13.9667, 105.9833 LA (llm/area) | Khone Phapheng falls ~13.955, 105.940 |
| 88 | too_coarse | koneswaram temple | Sri Lanka North-East: Jaffna, Trincomalee, Pa… | 8.5667, 81.2333 LK (llm/area) | Koneswaram on Swami Rock, Fort Frederick, about 8.583,81.245 |
| 89 | too_coarse | kuensel phodrang nature park | Bhutan: Culinary Trail East to West — 10 Days | 27.4712, 89.6339 BT (llm/area) | Buddha Dordenma / Kuensel Phodrang, about 27.443,89.645 |
| 90 | too_coarse | kumbum monastery in qinghai | Highlights of Tibet Tour: Beijing, Xi'an and … | 36.6200, 101.5700 CN (llm/area) | Kumbum (Ta'er Si), Huangzhong ~36.488, 101.568 |
| 91 | too_coarse | kumbum pagoda | Mount Kailash Tour: Lhasa, Kailash Kora and E… | 28.9200, 89.6000 CN (llm/area) | Gyantse Kumbum (Pelkor Chode), about 28.949, 89.630 |
| 92 | too_coarse | memorial monument of lieutenant general buckner | Okinawa Historical Tour: The Battle of Okinaw… | 26.0833, 127.7167 JP (llm/area) | Buckner memorial, Itoman, about 26.103, 127.680 |
| 93 | too_coarse | mountain pass 15 km outside dien bien | Laos and Vietnam Cycling Tour from Luang Prab… | 21.4000, 103.0000 VN (llm/area) | Unnamed pass about 15 km from Dien Bien Phu; exact spot unknown |
| 94 | too_coarse | new shira campsite | Kilimanjaro Trek via the Machame Route — 8 Da… | -3.1000, 37.3000 TZ (llm/area) | Shira 2 / New Shira Camp ~-3.04,37.26 |
| 95 | too_coarse | nine bend stream | Beijing to Hong Kong Overland Tour — 16 Days | 27.7167, 118.0333 CN (llm/line) | Jiuqu Xi, Wuyishan scenic area ~27.65, 117.96 |
| 96 | too_coarse | oldest temple in chiang mai | Northern Thailand Adventure — 14 Days | 18.7883, 98.9853 TH (llm/area) | Wat Chiang Man ~18.794, 98.989 |
| 97 | too_coarse | onglathang glacier | Sikkim Kangchenjunga Trek — 21 Days | 27.5500, 88.1000 IN (llm/area) | Onglakthang glacier below Goecha La ~27.60,88.16 |
| 98 | too_coarse | pelkhor choede monastery | Beijing to Kathmandu via Lhasa and Everest — … | 28.9167, 89.6000 CN (llm/area) | Pelkor Chode (Palcho) Monastery, Gyantse ~28.948, 89.63 |
| 99 | too_coarse | pelkor chode monastery | Beijing to Kathmandu Overland via Tibet — 15 … | 28.9200, 89.6000 CN (llm/area) | Pelkor Chode (Palcho) Monastery, Gyantse ~28.948, 89.63 |
| 100 | too_coarse | raj mandir | Golden Triangle: Delhi, Agra and Jaipur, 8 Da… | 26.9124, 75.7873 IN (llm/area) | Raj Mandir cinema, Jaipur ~26.916, 75.811 |
| 101 | too_coarse | ram nagar fort | Delhi, Varanasi, Agra and Jaipur — 11 Days | 25.3176, 83.0130 IN (llm/area) | Ramnagar Fort ~25.284,83.028 |
| 102 | too_coarse | rishengchang exchange museum | Pingyao Private Day Tour from Xi'an — 1 Day | 37.1897, 112.1761 CN (llm/area) | Rishengchang, West Street, Pingyao ~37.201, 112.178 |
| 103 | too_coarse | ryugu | Nikko and Oze Katashina — 3 Days | 36.8667, 139.2333 JP (llm/area) | Ryugu (Ryugu-goya) in Ozegahara marsh ~36.926, 139.237 |
| 104 | too_coarse | samity lake | Sikkim Kangchenjunga Trek — 21 Days | 27.6833, 88.2000 IN (llm/area) | Samiti Lake on the Goecha La route, ~27.59, 88.17 |
| 105 | too_coarse | shibaoshan | China Tour: Beijing, Xi'an, Yunnan, Guilin an… | 26.5000, 99.8700 CN (llm/area) | Shibaoshan scenic area, Jianchuan (near Shaxi) ~26.38, 99.80 |
| 106 | too_coarse | temple of the holy bo tree | Sri Lanka Honeymoon Tour: Anuradhapura, Kandy… | 8.3114, 80.4037 LK (llm/area) | Jaya Sri Maha Bodhi ~8.345, 80.397 |
| 107 | too_coarse | terracotta army | China Adventure: Beijing to Hong Kong — 20 Da… | 34.4067, 109.2277 CN (geoapify/point) | Terracotta Army pits ~34.385, 109.273 |
| 108 | too_coarse | tham xang or tham hoi caves | Laos by Bike: Luang Prabang to Vientiane — 7 … | 18.9167, 102.4333 LA (llm/area) | Tham Xang/Tham Hoi, north of Vang Vieng ~19.04, 102.42 |
| 109 | too_coarse | urumqi airport | Cultural tour of Kazakhstan, Kyrgyzstan and C… | 43.8185, 87.5942 CN (geoapify/point) | Urumqi Diwopu International Airport ~43.907,87.474 |
| 110 | too_coarse | varanasis spiritual lanes | India's Golden Triangle & Varanasi — 8 Days | 25.3176, 82.9739 IN (llm/area) | Old city lanes near Dashashwamedh ~25.31,83.01 |
| 111 | too_coarse | wat tham pla fish cave temple | Thailand by Water, Rail & Trail — 9 Days | 19.9167, 99.8833 TH (llm/area) | Wat Tham Pla, Mae Sai district ~20.332, 99.858 |
| 112 | too_coarse | xegar | Beijing to Kathmandu Overland via Tibet — 15 … | 28.3700, 87.3000 CN (llm/area) | Xegar/Shelkar (New Tingri) ~28.66, 87.12 |
| 113 | too_coarse | zutrul puk | Tibet: Beijing to Kathmandu — 21 Days | 31.0700, 81.3100 CN (llm/area) | Zutulpuk Monastery on Kailash kora ~31.10, 81.36 |

Not-a-place rows (28):

| name | tour | kind |
|---|---|---|
| border to chau doc | Bangkok to Ho Chi Minh City by Bicycle — 14 D… | route segment |
| chhomrong khola to chhomrong | Annapurna Base Camp Trek with Poonhill — 15 D… | route segment |
| doi chang mub to mae sai | Thailand & Cambodia: Bike, Kayak & Trek — 12 … | route segment |
| eco lodge in habarana | Sri Lanka Birding Tour — 18 Days | lodging |
| ganpati palace or similar | Delhi to Kathmandu: India and Nepal — 15 Days | lodging |
| group hotel in delhi | Nubra Valley Trek with Samgyal and Dawa Peaks… | lodging |
| hagari village to aewol port | South Korea: Seoul, Seoraksan, Andong, Busan … | route segment |
| hotel | Best of Nepal: Kathmandu, Pokhara and Chitwan… | lodging |
| hotel in central new delhi | India Snapshot: Delhi, Agra and Jaipur — 6 Da… | lodging |
| hotel in chiang mais old city | Northern Thailand and Laos Cycling Tour — 12 … | lodging |
| hotel in delhi | Nanda Devi and Panch Chuli Trek, Kumaon — 14 … | lodging |
| hotel in seoul | Coast 2 Coast Cycling Across South Korea — 5 … | lodging |
| hotel lobby in seoul | South Korea Highlights — 7 Days, 6 Nights | lodging |
| jaipur balloon ride | Delhi to Kochi: Taj Mahal, Rajasthan, Goa and… | activity / people / description |
| jiankou to mutianyu | China Explorer: Beijing, Xi'an, Huashan, Luoy… | route segment |
| lhasa to gyantse | Private Tour: Lhasa, Gyantse and Shigatse — 5… | route segment |
| mae sai to the golden triangle | Thailand and Cambodia Multisport Tour — 12 Da… | route segment |
| metropolo jinjiang classiq shanghai nanjing road or similar | Highlights of China: Beijing, Xi'an, Chengdu,… | lodging |
| mountain heading toward mt zao | Tohoku Cherry Blossom Bike Tour — 8 Days | activity / people / description |
| one of the restaurants in the fort | Sri Lanka and Maldives Budget Tour — 16 Days | activity / people / description |
| pakse to champasak | Southern Laos by Bike: Mekong Islands, Temple… | route segment |
| phnom den tinh bien border to chau doc | Cycle Bangkok to Ho Chi Minh City: Thailand, … | route segment |
| phonsavan to paksan | Laos by Bicycle: Luang Prabang to the Cambodi… | route segment |
| pre booked hotel in arusha | Mount Kilimanjaro Trek via the Marangu Route,… | lodging |
| temple of heaven and summer palace | Beijing to Hong Kong Overland Tour — 16 Days | compound |
| tsaatan family | Naadam Festival in Khuvsgul Province, Mongoli… | activity / people / description |
| udaipur cooking school | Delhi to Kochi: Taj Mahal, Rajasthan, Goa and… | activity / people / description |
| zutrul phuk to darchen | Mount Kailash Tour: Lhasa, Kailash Kora and E… | route segment |

Unsure rows (19), to check with a geocoder or by hand:

| name | tour | current point | note |
|---|---|---|---|
| bagar | Annapurna Base Camp Trek via Ghorepani — 12 D… | 28.5500, 83.8700 NP (llm/area) | Point is in Annapurna Sanctuary ~2 km N of ABC; Bagar may be the trail stop near Deurali/… |
| bell and drum towers | China Express: Beijing, Xi'an and Shanghai — … | 39.9389, 116.3950 CN (llm/area) | Point is Beijing's Bell & Drum Towers; tour also visits Xi'an whose Bell & Drum Towers ar… |
| butter sculpture exhibition | China Tibet Encompassed — 16 Days | 29.6500, 91.1200 CN (llm/area) | An exhibition, not a place, geocoded to the Lhasa centroid. The famous butter sculptures … |
| city god temple area | China: From Great Wall to Shaolin — 11 Days | 31.2276, 121.4916 CN (llm/null) | Point is correct for the Shanghai City God Temple (Yuyuan). Check that this tour visits S… |
| danao adventure park | Dumaguete, Siquijor and Bohol Adventure — 8 D… | 9.9578, 124.1789 PH (geoapify/point) | Point is interior Bohol; EAT Danao park is in Danao municipality (~10.0, 124.2); cannot c… |
| dikpala | Mount Kailash Tour: Lhasa, Kailash Kora and E… | 31.0700, 81.3100 CN (llm/area) | Possibly a garbled Dirapuk, or the deity term 'dikpala' (guardian), not a place. Point is… |
| elephant peace project | Thailand & Cambodia: Bike, Kayak & Trek — 12 … | 19.9704, 99.6873 TH (geoapify/point) | A small elephant project; location cannot be confirmed. The point is just west of Chiang … |
| katpana cold desert | Baltistan, Deosai, Fairy Meadows and Hunza — … | 35.3667, 75.6167 PK (llm/area) | Point is in the Skardu desert zone but N of the Indus, about 6-8 km from Katpana; may be … |
| khatang | Pikey Peak Trek — 7 Days | 27.7576, 86.5953 NP (geoapify/point) | Point is about 20 km north of Pikey Peak toward Solu/Lukla. Cannot confirm where the Khat… |
| khejarla | Luxury North India With Kerala — 16 Days | 26.6000, 73.6167 IN (llm/area) | Khejarla Fort village is in Jodhpur district (east of Jodhpur, near Pipar). 26.6, 73.62 i… |
| kings palace | Delhi to Kathmandu: India and Nepal — 15 Days | 28.2096, 83.9856 NP (llm/area) | Point is Pokhara (near Ratna Mandir). Fits only if the itinerary means the Pokhara royal … |
| lao museum of art | Laos: Three Rivers by Bike and Boat — 14 Days | 19.8845, 102.1348 LA (llm/area) | Point is Luang Prabang centre; cannot confirm a 'Lao Museum of Art' there (could be a Vie… |
| mount lishan | China by Bike: Guangdong to Beijing — 16 Days | 34.2247, 109.2078 CN (llm/null) | Point is about 13 km south of the main Lishan summit area. It may sit at the southern edg… |
| muang khua district | Tribal Routes: Northern Laos Cycling Tour — 8… | 21.0667, 102.1833 LA (llm/area) | Rounded area point about 35 km west of Muang Khua town on the Nou river. Unclear whether … |
| panchachuli | Sikkim Kangchenjunga Trek — 21 Days | 30.1833, 80.4167 IN (llm/area) | The point is correct for the Panchachuli massif (Pithoragarh, Uttarakhand). But it is ~80… |
| pho chau | Laos & Central Vietnam by Bike: Luang Prabang… | 18.4500, 105.6167 VN (llm/area) | Right province and route (QL8 from Cau Treo), but the point may be about 20 km east of th… |
| phoktey dara | Singalila Pass and Phoktey Dara Trek — 7 Days | 27.3800, 88.1500 IN (llm/area) | Point is on the Singalila ridge, West Sikkim, plausibly near Phoktey Dara; cannot confirm… |
| tordi sagar | Delhi to Kochi: Taj Mahal, Rajasthan, Goa and… | 26.0833, 75.9167 IN (llm/area) | Tordi Sagar is in Tonk district, Rajasthan; point is in that district but exact location … |
| wilpattu national park entrance | Wilpattu Safari and Negombo Beach Honeymoon, … | 8.3076, 80.1480 LK (geoapify/area) | The point is on the Wilpattu side of the A12; cannot confirm it is at the Hunuwilagama en… |

## 6. Provenance of the 652 rows without a geocoder

- `located_by`: 442 `llm`, 210 `mapbox`. Every row has some `located_by`; all 210 mapbox rows in the dataset are here.
- `geo_precision`: 649 null and 3 `line`. These are exactly the 649 null-precision rows in the whole resolved set.
- `confidence` and `review_reason` are null on all 652.
- Top countries: KR 104, NP 103, CN 87, BT 64, IN 64, LA 51, TH 49, MN 48, LK 45, JP 25.
- Other flags on these rows: dup_coords 104, tour_spread 35, country 1.
- Verified quality is not worse than average (29/36 correct, 13.9 % error). They look like rows written by an older
  path (pre-`geocoder_provider` / pre-precision): a metadata backfill, not a re-geocode. One real bug among them:
  `binh island` (mapbox, the "An" strip above).

## 7. Unresolved names (1,621)

1,203 pending + 418 unknown. 1,595 failed with `unknown_to_model` (the model returned null), 21 were rejected by the
polygon/bbox guard, 4 failed on a "Tibet, China" country answer and 1 was malformed. Retrying the same LLM prompt
almost always returns null again. Counts below are estimates (regex rules plus hand overrides after reading all 1,621
names; group boundaries ±10 %). Full detail: `unresolved_classified.json`.

| cause | ~count | examples | recommended handling |
|---|---|---|---|
| Small real place the model does not know (villages, trek camps, passes, lodges) | 519 | Dalzampa, Labatama, Chere Chaur, Ban Son Koua, Mogamiya Ryokan | Geocoder-only fallback on a null answer (no LLM), accepted only within N km of the tour's stops for day ±1; lodging falls back to its overnight town at `area`; the rest to a review queue in `/admin/places` grouped by tour |
| Descriptive phrase, not a name | 277 | "a small Lao village along the river", "the village of Gogina", "viewpoint above Dzongri" | Strip wrappers ("the village of X" → X) and resolve the anchor; "kind in/of <Town>" → town at `area` or drop; no anchor → non-place. Tighten the extraction prompt to return proper names only |
| Route segment / transit leg | 223 | Dingboche to Lobuche, Saga to Darchen, Ngawal–Manang route | Split on to / – / via / toward, resolve each endpoint, optionally store a line between them |
| Spelling or transliteration variant | 102 | Ranthan/Ranthon, Kuldighar/Khuldigar, mixed Latin/Devanagari | Fuzzy-cluster within tour/country so one resolution covers all spellings; non-Latin guard; alias table (content) |
| Real place in another country than the tour's stored country | 94 | Irkutsk/Baikal under Mongolia, Kailash kora under Nepal, Kilimanjaro under India | Give the locate step the day text and the tour's other resolved stops/countries; on null, retry the geocoder in candidate countries from the tour name |
| Generic kind-only name | 90 | base camp, Camp 1, international airport, Jain temple | Extend the generic stop-list; resolve as `<kind> (<Town>)` at `area` only with a reliable locality, else drop |
| Not a place at all | 81 | Korean cooking class, Sichuan Hot Pot, monks, Shatabdi Express | Kind classifier at extraction; new status `non_place` so the row leaves the retry loop |
| Region / range / sea | 68 | the Himalayas, Arabian Sea, rural Laos | Store as region (label/shape, never a pin) or drop; exclude seas from the polygon guard |
| Well-known place the model still returned null for | 67 | Norbulingka, Tingri, Olkhon Island, Phi Phi Islands | Geocoder-only fallback; stop repeating the same prompt |
| Compound name ("A and B", "A or B", "A/B") | 48 | Kabru and Pandim, Swat or Peshawar | Split when every part is a proper noun; drop list-of-peoples forms |
| Annotated name (altitude, "(or similar)") | 18 | Yali La Pass (4820 m), Hanok Stay (or similar) | Strip `(\d+ ?m)` and "(or similar)" in normalisation; keep a bracketed alias as a second name form |
| Generic name keyed to the wrong locality | 15 | Summer Palace \| Shanghai, Grand Palace \| Chiang Mai, Old City \| <hotel name> | Named-landmark allow-list; build locality from the town in the same sentence/day, never from a hotel; on null retry with day ±1 towns |
| Guard reject of a correct coastal / island / border place | 15 | Phi Phi Islands, Turtle Island (Yilan), Rui La | Higher-resolution polygons (Natural Earth 10m / GADM with minor islands) or a larger coastal buffer; accept border passes inside either neighbour |
| Country text not parsed ("Tibet, China") | 4 | Norbulingka, Tingri, Lalung La | Lenient country reader: split on comma/slash/brackets, take the part that resolves to one ISO; map Tibet/TAR to CN |

## 8. Fix plan (ranked; generic system fixes first)

1. **Coordinates come from a geocoder, never from the LLM.** The LLM may propose a canonical name, country and town;
   the point is then a Geoapify forward search biased to that town/country and accepted only within a distance of the
   tour's day ±1 stops. Rows with only an LLM point become `area` + `review_reason = llm_point` and are not drawn as
   exact pins. Then re-locate the 3,770 `located_by = llm` rows through that path (free-tier volume over a few days;
   confirm the quota first). Fixes most of the ~790 wrong_place and the off-target class.
2. **Route-coherence guard** for every resolved row: distance to the same tour's stops on day ±1 above a threshold
   (e.g. 50 km for sites, larger for long transfer days) → `needs_review`. Replace `tour_spread` (median-based, 23 %
   precision) with this. It catches the Kilimanjaro huts, Kong Lor, Jait Sagar, Dilwara and the homonym class.
3. **Context-aware disambiguation of generic landmark names** (City Wall, Bell and Drum Tower, Grand Canal, Gandhi
   Museum, Princess Street, San Agustin, Victory Square): locality from the town named in the same sentence or day,
   never from the overnight hotel; a named-landmark allow-list so Summer Palace / Grand Palace are not treated as generic.
4. **Extraction filter before any paid call**: split route legs and compounds, strip wrappers, altitude and
   "(or similar)", classify activities/people/lodging/transport/regions, add a `non_place` status. Removes the ~300
   not_a_place pins in the resolved set and about 805 of the 1,621 unresolved names.
5. **Centroid fallback is explicit**: when a site-type name lands on a town centroid, store `precision = area` and
   `review_reason = centroid_fallback`, and show it as an area, not a pin. Rework `dup_coords` to "site-type name on a
   coordinate shared by ≥ 3 names" so it stops firing on town names.
6. **Small deterministic fixes**: ISO from point-in-polygon including HK and MO (20 rows now CN); lenient country
   reader ("Tibet, China"); `name_norm` keeps a leading "An" when the next word is capitalised (An Binh, An Ping);
   higher-resolution polygons or a coastal buffer for islands; backfill `geocoder_provider`/precision on the 652
   provenance-null rows; geocoder-only fallback and stop-after-first-null for the unresolved queue.
7. **Content (not system)**: hand pins for the 113 wrong/coarse rows in §5.5 (most have an `expected` point ready),
   the 19 unsure rows, the alias table for spelling variants, and the residual unresolved review queue in
   `/admin/places`. Source tour-country fixes for the Kilimanjaro tours (India → Tanzania) and "Bhutan Cultural Tour"
   (Nepal → Bhutan) go to the source Excel owner; the geocoder already uses each place's own ISO.
8. **Measure again** after items 1–6: rerun `rules.py` and a fresh 200-row random sample stratified by `located_by`;
   target ≥ 90 % correct overall (Geoapify-located rows are at ~91 % today).
