# AA-712 — Geocoder research: storable coordinates for `shared.destinations`

Date: 14/10/2026 (S236). Sources: primary vendor pages only, all read on 14/10/2026. Complements
`03-design.md` §4 (Mapbox Permanent) and §8 (cost).

## Tóm tắt cho Nghiệp (tiếng Việt)

1. **Mapbox Permanent không hợp với TripPlanner** dù giá $5/1k: Product Terms (21/07/2026) §2.7.3 chỉ cho dùng Permanent Geocodes "nội bộ"; muốn hiện trong app thì phải đủ 4 điều kiện — tính năng phụ, **mỗi end-user account phải gọi API riêng**, **không lộ lat/lng cho end-user**. Bản đồ công khai của TP vi phạm cả ba. Không có free tier; trang giá còn ghi "contact Mapbox sales".
2. **Google bị loại**: cấm dùng với bản đồ không phải Google (§6.2) và chỉ cache lat/lng 30 ngày (§6.3.1).
3. **Amazon Location Places v2 (`geo-places`)**: hợp pháp để lưu (`IntendedUse=Storage`, $4.00/1k, Service Terms §82.4.a.ii), không cấm hiện trên Mapbox (§82 chỉ cấm chồng *route* HERE lên bản đồ hãng khác, §82.5.b; vẫn phải ghi nguồn §82.10 và không gắn logo/quảng cáo vào Location Data §82.4.f). Free tier AWS chỉ cho khách hàng AWS mới và chỉ gồm Core/Label — acc2 tính đủ tiền Stored. Nhưng **không có ở us-west-1**, phải gọi us-west-2 (gọi chéo region, không vấn đề). **Vấn đề lớn là độ phủ**: Bhutan, Trung Quốc/Tây Tạng, Mông Cổ, Hàn Quốc = *Unsupported*; Nepal, Lào, Tajikistan, Turkmenistan chỉ có POI *Fair*. Nhật: HERE cấm lưu kết quả ở Nhật (§82.5.a).
4. **Geoapify (dữ liệu OSM)**: được lưu vĩnh viễn ("we do not restrict you from storing results"), free 3.000 request/ngày **cho phép thương mại** → backfill 6k mất 2 ngày, **$0**; mỗi tháng ~200 cũng $0. **Phải ghi nguồn cả Geoapify lẫn OSM**: gói Free yêu cầu link "Powered by Geoapify" gần bản đồ/thông tin do dịch vụ trả về, cộng ghi nguồn dữ liệu (OSM) đi kèm bản ghi đã lưu (đính chính S236 — bản trước ghi "chỉ cần ghi nguồn OSM" là thiếu). OpenCage cũng OSM, cho lưu vĩnh viễn, €45/tháng (X-Small).
5. Chi phí 6.000 + 200/tháng (năm đầu): AWS ≈ $34 · Mapbox ≈ $42 (nhưng vướng terms) · Geoapify $0 · OpenCage ≈ €45 (1 tháng) · Google: không được dùng.
6. **Khuyến nghị**: đổi §4 sang **Geoapify làm geocoder xác nhận chính** (giữ quy trình LLM đề xuất điểm → geocoder xác nhận trong 25 km). Tuỳ chọn thêm AWS Stored cho các nước AWS phủ tốt (TH, VN, IN, KZ; KH/MM chỉ ở mức POI *Fair*) — trừ Nhật. Bỏ Mapbox Permanent; Mapbox chỉ còn làm basemap.
7. **Trước khi chốt**: chạy bake-off nhỏ ~60 tên (5/nước) qua Geoapify + AWS (SingleUse, ~$0.03) và so với điểm LLM. Chốt geocoder nào là do độ phủ thực tế, không phải do giá.
8. Rủi ro: Geoapify free không có SLA và có thể đổi điều khoản → lưu `located_by='geoapify'` + `source_version` để chạy lại được. Dữ liệu OSM theo ODbL thì theo hướng dẫn OSMF, kết quả geocode từng điểm không kéo theo share-alike.

---

## 1. Amazon Location Service — Places API v2 (`geo-places`)

### 1.1 Region availability
- Places endpoints (`places.geo.<region>.api.aws`) are listed for us-east-1, us-east-2, **us-west-2**,
  ap-southeast-1/2/5, ap-south-1, ap-northeast-1, ca-central-1, eu-central-1, eu-west-1/2, eu-south-2,
  eu-north-1, sa-east-1, us-gov-west-1. **us-west-1 is not listed.**
  — https://docs.aws.amazon.com/general/latest/gr/location.html (read 14/10/2026)
- Corroborated by the public AWS Price List: `AmazonLocationService/current/region_index.json` has no
  `us-west-1` (fetching `.../us-west-1/index.json` returns `NoSuchKey`).
  — https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonLocationService/current/region_index.json (14/10/2026)
- Consequence: the CIS worker (ECS, us-west-1) calls `boto3.client("geo-places", region_name="us-west-2")`.
  This is a plain HTTPS call to another region. IAM is global, so no VPC or infra change is needed besides
  the task-role grant.

### 1.2 Data providers and coverage
- Sources: "HERE Technologies provides … geocoding, reverse geocoding …", GrabMaps (8 Southeast Asian
  countries), Esri, and AWS Open Data (Overture/OSM) **for base maps**.
  — https://docs.aws.amazon.com/location/latest/developerguide/data-attribution.html
- v2 has **no data-source parameter**: the Geocode request has no provider field
  (https://docs.aws.amazon.com/location/latest/APIReference/API_geoplaces_Geocode.html), and the docs do
  not say which provider answers a given v2 request. GrabMaps for Places v2 is tied to ap-southeast-1/5, and
  those regions do not support `Geocode`/`IntendedUse` with GrabMaps (same API page). In us-west-2 we
  should therefore assume HERE-class global data.
- Coverage table (Places Point Address / Place POI), from
  https://docs.aws.amazon.com/location/latest/developerguide/data-quality.html (14/10/2026):

| Country | Maps | Places PA | Place POI |
|---|---|---|---|
| Bhutan | Unsupported | Unsupported | **Unsupported** |
| China (incl. Tibet) | Unsupported | Unsupported | **Unsupported** |
| Mongolia | Unsupported | Unsupported | **Unsupported** |
| South Korea | Unsupported | Unsupported | **Unsupported** |
| Nepal | Fair | Unsupported | Fair |
| Laos | Unsupported | Unsupported | Fair |
| Tajikistan | Unsupported | Unsupported | Fair |
| Turkmenistan | Unsupported | Unsupported | Fair |
| Kyrgyzstan | Unsupported | Good | Fair |
| Uzbekistan | Fair | Good | Fair |
| Cambodia | Good | Fair | Fair |
| Myanmar | Good | Fair | Fair |
| Sri Lanka | Fair | Good | Fair |
| Vietnam | Good | Good | Good |
| India | Good | Comprehensive | Good |
| Kazakhstan | Good | Comprehensive | Good |
| Thailand | Good | Comprehensive | Comprehensive |
| Japan | Comprehensive | Comprehensive | Comprehensive |

  POI "Fair" = "Only basic and high-profile landmark POI information available"; "Unsupported" = "No
  support for POIs within a country" (same page). Small villages, monasteries and passes in
  BT/CN-Tibet/MN/NP/LA are therefore unlikely to resolve.

### 1.3 IntendedUse = Storage — what it permits
- "If you are going to store the results (even for caching purposes), you must choose the *storage*
  option." Storage is supported on Geocode, ReverseGeocode, GetPlace, SearchText, SearchNearby (not
  Autocomplete/Suggest).
  — https://docs.aws.amazon.com/location/latest/developerguide/places-intended-use.html
- "You can store the Places results indefinitely for long-term use cases … set `intendedUse = Stored` …
  charged at the Stored price. The Stored pricing bucket supports all the features …, therefore, the
  maximum price you will be charged for a single Places API call is capped at the Stored price."
  Core/Advanced: "Results can't be stored permanently."
  — https://docs.aws.amazon.com/location/latest/developerguide/places-pricing.html
- API value is `Storage` (`SingleUse | Storage`): "When storing `Geocode` responses, you *must* set this
  field to `Storage` to comply with the terms of service."
  — API_geoplaces_Geocode.html (above)
- AWS Service Terms §82.4(a) (Last Updated 13/10/2026): you may not "store, or cache the data … except
  that you may store or cache … (ii) geocoding and reverse-geocoding results (other than as prohibited in
  Section 82.5.a) when you indicate the result will be stored in the API parameter".
  — https://aws.amazon.com/service-terms/ §82

### 1.4 Price and free tier (us-west-2 Price List, publicationDate 2026-09-11)
- `Places-Stored`: **$4.00 per 1,000** Geocode / SearchText / GetPlace requests (Stored).
- `Places-Core`: $0.50 / 1k (single use). `Places-Advanced`: $1.50 / 1k. Label: $0.20 / 1k.
  — https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonLocationService/current/us-west-2/index.json
- Free trial: "free trial for the first three months of usage (usage quota apply)"
  (https://docs.aws.amazon.com/location/latest/developerguide/pricing.html). The pricing page lists "20,000
  Geocode, Reverse Geocode, Search Text, Search Nearby, or Get Place requests **(Core)**" per month.
  Stored is not listed, so **budget Stored as fully paid**. The pricing page also says this allowance is
  "Included monthly, for 3 months" for **new AWS customers** (Free Tier credit programme since 15/07/2025).
  Acc2 is an existing account, so assume no free tier at all (S236 verification).
  — https://aws.amazon.com/location/pricing/

### 1.5 Display on a non-AWS basemap (Mapbox GL) and provider terms
- §82 has **no clause that forbids showing stored geocodes on another vendor's map**. The only layering
  restriction is for HERE *routes* (§82.5.b: do not "layer routes from HERE on top of a map from another
  third-party provider"). We do not use routes.
- Other §82 clauses that matter:
  - §82.4(b): do not build a product "similar to the services of the Geolocation Providers" without
    substantial independent value. A trip planner is fine.
  - §82.4(d): do not combine Location Data in a way that subjects it to open-database (ODbL) terms.
    Mixing AWS rows and OSM-derived rows in `shared.destinations` needs care. Per the OSMF geocoding
    guideline (§3.3 below), individual geocodes do not create a Derivative Database. Keep `located_by`
    per row anyway.
  - §82.4(f): do not put our marks or ads "on or in the Location Data".
  - **§82.5(a) (HERE): do not "store or cache any Location Data for Japan, including any geocoding …
    results."** Japanese places must not be stored from AWS.
  - §82.10: "You must pass through attribution for Location Data that you make available to others".
    Data-attribution page: give end users "a link to this page … (e.g., by inserting a reference in the
    End-User Terms)".
- Esri §82.6 (asset tracking) does not apply to us.

### 1.6 IAM / SDK / quotas
- boto3 client `geo-places`, with methods `geocode`, `search_text`, `get_place`, `reverse_geocode`,
  `search_nearby`, `suggest`, `autocomplete`.
  — https://docs.aws.amazon.com/boto3/latest/reference/services/geo-places.html
- Geocode request fields we would use: `QueryText` (≤ 200 chars), `Filter.IncludeCountries`,
  `BiasPosition` [lng, lat] (LLM point), `IntendedUse="Storage"`, `MaxResults`. The response gives
  `Position`, `PlaceType`, `MatchScores.Overall`, and header `x-amz-geo-pricing-bucket` (useful for cost
  logging). SearchText is the better call for POIs (monasteries, passes).
- IAM actions use the `geo-places:` prefix (`geo-places:Geocode`, `geo-places:SearchText`,
  `geo-places:GetPlace`), as in the quota names and the console policy example
  (https://docs.aws.amazon.com/location/latest/developerguide/security-iam.html, which uses `Resource: "*"`).
  Confirm the narrowest resource ARN in the Service Authorization Reference when writing Terraform.
- Default quotas: 100 requests/s each for geo-places Geocode, SearchText and GetPlace (adjustable)
  — general/latest/gr/location.html. This is far above our ≤ 5 req/s.

## 2. Mapbox Geocoding v6 — Permanent

- Price (https://www.mapbox.com/pricing, 14/10/2026): Permanent Geocoding API **$5.00 / 1,000** for
  1–500,000 requests/month and $4.00 / 1,000 above 500,000. **No free tier row** (Temporary has 100k
  free). The page says: "If you're interested in using this API, please contact Mapbox sales." It also
  says: "Results from the Permanent Geocoding API are only available for your own personal or business use,
  and cannot be used for distribution or sublicense."
- Docs (https://docs.mapbox.com/api/search/geocoding/): "Temporary results are not allowed to be cached,
  while Permanent results are allowed to be cached and stored indefinitely." "Using Permanent storage …
  requires that you have a valid credit card on file or an active enterprise contract." `permanent=true`.
  Batch is up to 50 queries, each counted as one request. Default rate limit is 1,000 req/min. "You may only
  use responses from the Geocoding API in conjunction with a Mapbox map."
- **Product Terms (Last Updated 21/07/2026)**, PDF linked from https://www.mapbox.com/legal/product-terms:
  - §2.7.1: do not use Geocoding Results "to develop a general database of points-of-interest, locations
    …", and do not "(b) display the latitudes or longitudes directly to End Users or other third parties".
  - §2.7.3 Permanent Geocodes: "Customer shall only use Permanent Geocodes for Customer's own internal
    business use. Notwithstanding …, Customer may use Permanent Geocodes in its Licensed Application if all
    following conditions are fulfilled:
    (i) access to Permanent Geocodes cannot be a primary or significant feature … but only used to support
    an ancillary or incidental feature,
    (ii) a separate API request for a Permanent Geocode shall be made for each End User account that
    accesses, uses, or relies on such Permanent Geocode in any way,
    (iii) … shall not allow an End User to … distribute a Permanent Geocode …, and
    (iv) if Permanent Geocodes are displayed in a Licensed Application, latitudes and longitudes may not
    be made available to End Users."
  - **Assessment**: TripPlanner's map of tour stops is a primary feature, and the visitors are anonymous
    (one request per end-user account is impossible). TP's API also ships lat/lng to the browser. The §4
    plan in `03-design.md` (store `permanent=true` results in `shared.destinations` and serve them to TP)
    **does not fit these conditions** without an enterprise contract that waives them.
  - Mapbox Temporary results cannot be stored (§2.7.2). So the fallback in 03-design §4 ("use Temporary
    as yes/no only, store the model point") stays legally borderline. If we accept a point *because* a
    Temporary result agreed with it, the stored row is still our own LLM point and not a Mapbox
    coordinate. Ask Mapbox before relying on that.

## 3. Other options with storage rights

### 3.1 Google Geocoding API — excluded
Google Maps Platform Service Specific Terms (last modified 10/06/2026),
https://cloud.google.com/maps-platform/terms/maps-service-terms:
- §6.2: "Customer must not use Google Maps Content from the Geocoding API in conjunction with a non-Google
  map." That rules out our Mapbox GL map.
- §6.3.1: lat/lng may be cached "for up to 30 consecutive calendar days, after which Customer must delete
  the cached latitude and longitude values". §6.3.2 allows indefinite caching only "solely to support the
  direct, End User facing functionality of the Customer Application that initiated the request" and with
  further limits.

### 3.2 Geoapify (OSM-based) — recommended
- Pricing (https://www.geoapify.com/pricing/, 14/10/2026): Free plan is **3,000 credits/day**, "No credit
  card required", up to 5 req/s. "Yes. You can use the Free plan for commercial websites, apps, and business
  projects, including in production." The same FAQ answer adds the condition: "provide the required Geoapify
  and data-source attribution … For Geoapify attribution, include a follow-link such as Powered by Geoapify
  near the map or information provided by the service." (S236 correction: Geoapify attribution is required
  on the Free plan, not only OSM.) The SLA (99.5%) applies to paid plans only. Geocoding costs 1 credit per request. Paid plans start at API 10:
  $59/month for 10,000 credits/day.
- Storage (https://www.geoapify.com/geocoding-api/ FAQ): "Our services are based on Open Data. So we do not
  restrict you from storing results. However, you have to keep all the attributions to the data source
  with the stored object or make it visible in some other way when you reuse the data." Also: "Store
  address and location data on your side without restrictions or additional costs."
- Data is OSM (plus other open data). For Bhutan, Nepal, Mongolia and Tibet, OSM is often the only source
  with village, monastery and pass names, but this is **not verified** here. See the bake-off in §5.

### 3.3 OpenCage (OSM-based)
- https://opencagedata.com/pricing (14/10/2026): Free trial is 2,500 requests/day, "testing only"; the FAQ says
  "inactive free trial accounts are deleted after three months" and "do not use it for anything mission
  critical", so it is not for production. (S236 correction: the trial is not time-limited to 3 months;
  *inactive* trial accounts are deleted after 3 months.) X-Small: **€45/month** for 10,000
  requests/day ("about €0.15 per 1,000"). One-time plans (Small/Medium/Large, valid 1 year) exist; their
  prices are rendered client-side and were not extractable, so check them on the page. Every plan lists
  "store data permanently", and the FAQ says: "You can store the data returned by the API permanently.
  Even if you are no longer a customer."

### 3.4 Nominatim
- Public instance (https://operations.osmfoundation.org/policies/nominatim/): "an absolute maximum of 1
  request per second". Bulk geocoding is strongly discouraged, and long-running scripts are limited to
  4 requests/minute. Access can be withdrawn at any time. **Not a production dependency.**
- Self-hosting means running an OSM import of Asia on our infra (RAM/disk heavy plus ops). That is not
  worth it for about 8k one-off and about 200/month.

### 3.5 OSM licence (applies to Geoapify, OpenCage, Nominatim)
OSMF Geocoding Guideline (Board-endorsed 24/08/2017),
https://osmfoundation.org/wiki/Licence/Community_Guidelines/Geocoding_-_Guideline: "Individual Geocoding
Results that are based on a Direct Hit contain an insubstantial amount of raw OSM data". Storing them in a
proprietary DB does not trigger share-alike unless results are aggregated into "the whole or a substantial
part" of OSM. The geocoder and the application must credit OpenStreetMap. TP's Mapbox basemap already shows
"© OpenStreetMap", but add an explicit line on the map/footer anyway.

## 4. Cost — 6,000 backfill + ~200/month (prices read 14/10/2026)

| Option | Backfill 6,000 | Monthly 200 | Year 1 total | Storage + Mapbox display legal? |
|---|---|---|---|---|
| AWS Places v2, Stored ($4.00/1k) | $24.00 | $0.80 | ≈ $33.60 | Yes (attribution link; **not Japan**) |
| Mapbox Permanent ($5.00/1k, no free tier) | $30.00 | $1.00 | ≈ $42.00 | **No** for a public map (Product Terms §2.7.3 i/ii/iv) |
| Geoapify Free (3,000/day, commercial OK) | $0 (2 days) | $0 | $0 | Yes ("Powered by Geoapify" link + OSM attribution) |
| Geoapify API 10 (if free tier changes) | $59 (1 month) | $0–59 | $59–708 | Yes (Geoapify + OSM attribution) |
| OpenCage X-Small (€45/mo, 10k/day) | €45 (1 day of quota) | €45 if kept; else one-time plan | ≈ €45 + one-time plan | Yes (OSM attribution) |
| Google Geocoding | — | — | — | **No** (non-Google map; 30-day cache) |
| Nominatim public | $0, ≈ 100 min at 1 req/s | $0 | $0 | Policy-fragile; not for production |

With 8,200 requests (upper bound in 03-design): AWS $32.80, Mapbox $41.00, Geoapify still $0 (3 days).

## 5. Recommendation for AA

1. **Replace Mapbox Permanent in 03-design §4 with Geoapify as the confirming geocoder.** Keep the TP
   `locate.py` method: the LLM proposes [lat, lng, country] → the geocoder is queried with country filter
   and bias → accept within 25 km (`located_by='geoapify'`), else keep the LLM point (`llm`). Mapbox stays
   the **basemap only** (no Mapbox geocoding stored). Secret becomes `aa-cis/dev/geoapify`, using the same
   pattern as DataForSEO. TP must show a "Powered by Geoapify" link near the map (Free-plan condition) plus
   the OSM credit. ⚠️ The env-var names contain underscores, so Nghiệp edits them manually in VSCode.
2. **Optional second opinion: AWS Places v2 Stored** (us-west-2), only for countries AWS rates Good or
   better (TH, VN, IN, KZ, plus KH/MM POI Fair). Skip JP (HERE §82.5.a) and skip BT/CN/MN/KR/NP/LA/TJ/TM
   (Unsupported/Fair). Cost is at most about $24 if every name is sent. Add the AWS attribution link to TP
   end-user terms if used.
3. **Gate before committing (cheap bake-off)**: about 60 real names from `shared.destinations` (5 per
   country, biased to villages, monasteries and passes). Run them through Geoapify (free), AWS SearchText
   **SingleUse** (Core $0.50/1k → about $0.03, results not stored), and the LLM point. Score each against
   a manual truth within 25 km. Choose per country from the hit rate. This follows the "paid runs: subset
   only" rule.
4. Update 03-design §4/§8: the Mapbox $21–41 line becomes $0 (Geoapify), or ≤ $33 if AWS is added.
   §4(b) still stands: the TP `located_by='mapbox'` rows came from Temporary calls and must be re-confirmed
   (now by Geoapify/AWS) or replaced by the LLM point.

### Risks
- **Coverage is unproven.** No vendor publishes per-country recall for small Himalayan or Mongolian
  places. Only the bake-off answers this. If OSM misses many, the LLM point stays the main source
  (`llm`, lower confidence, outlier guard from §4).
- **Geoapify free tier has no SLA and its terms can change.** Store `located_by`, the provider and a
  `geocoded_at` per row so a re-run on another provider is a job, not a migration. API 10 ($59/month)
  is the paid fallback.
- **Licence mixing**: AWS §82.4(d) vs ODbL. This is low risk per the OSMF guideline (individual direct
  hits), but keep the provider per row and do not bulk-export the table as an open dataset.
- **AWS region**: us-west-1 is unsupported. A cross-region call to us-west-2 is fine, but the request
  data is processed outside us-west-1 (§82.1). Not an issue for place names.
- **Mapbox**: if Nghiệp still prefers Mapbox Permanent, get a written waiver of Product Terms §2.7.3
  (ii)/(iv) under an enterprise contract first. Card-on-file self-serve does not change those conditions.
- Verify with live calls before implementation: whether AWS v2 refuses `Storage` for JP queries, and the
  exact resource ARN for `geo-places` in IAM. Neither is documented on the pages read.

## Verification (S236)

Adversarial re-check on 14/10/2026 against the cited primary sources (fetched live: AWS Price List JSON,
AWS Service Terms "Last Updated: October 13, 2026", AWS docs, Mapbox pricing/docs + Product Terms PDF dated
21/07/2026, Google Maps Service Specific Terms "Last modified June 10, 2026", Geoapify, OpenCage, OSMF).

| # | Claim | Result | Evidence |
|---|---|---|---|
| 1 | Places v2 endpoints exist in us-west-2; **us-west-1 not listed** | Confirmed | general/latest/gr/location.html region table; Price List `region_index.json` has no us-west-1, `us-west-1/index.json` returns 404 |
| 2 | AWS Places **Stored = $4.00 / 1,000** (Geocode, SearchText, GetPlace, ReverseGeocode, SearchNearby) in us-west-2 | Confirmed | Price List us-west-2, publicationDate 2026-09-11, usagetype `USW2-Usage-Default-Places-Stored` = 0.0040 USD/request. (A summarising fetch of aws.amazon.com/location/pricing/ reported "$0.50"; the page renders prices from tokens, and the Price List is authoritative — $0.50 is **Core**, not Stored.) |
| 3 | Core $0.50/1k, Advanced $1.50/1k, Label $0.20/1k | Confirmed | Same Price List |
| 4 | Free tier: 20,000 Core + 10,000 Label per month, 3 months; Stored not included | Confirmed, nuance added | Pricing page: for **new AWS customers** only; acc2 is not new → treat all usage as paid (added to §1.4) |
| 5 | Stored results may be kept indefinitely; Core/Advanced/Label may not | Confirmed | places-pricing.html |
| 6 | `IntendedUse` = `SingleUse \| Storage`; must be `Storage` when storing; not available on Autocomplete/Suggest | Confirmed | API_geoplaces_Geocode.html; places-intended-use.html |
| 7 | GrabMaps regions ap-southeast-1/5 do not support Geocode / IntendedUse | Confirmed | API_geoplaces_Geocode.html |
| 8 | Service Terms §82.4(a)(ii) allows storing geocodes when flagged in the API parameter | Confirmed | Verbatim in §82.4(a) |
| 9 | **Stored AWS geocodes may be shown on a Mapbox basemap** — no §82 clause forbids it | Confirmed | §82 read in full: the only cross-provider layering ban is §82.5(b) (HERE *routes*). Still binding: §82.4(f) (no own marks/ads in Location Data), §82.10 (pass through attribution), §82.4(b)/(d) |
| 10 | HERE §82.5(a): no storing/caching Location Data for Japan incl. geocodes | Confirmed | Verbatim. v2 does not expose the provider, so treating JP as HERE-restricted remains the safe reading |
| 11 | Esri §82.6 limited to asset management/tracking; n/a for AA | Confirmed | Verbatim |
| 12 | §82.1 requests may be processed outside the request region | Confirmed | Verbatim |
| 13 | Attribution: give End Users a link to the data-attribution page (e.g. in End-User Terms) | Confirmed | data-attribution.html |
| 14 | Coverage table (18 countries, Maps / PA / POI) and POI "Fair"/"Unsupported" definitions | Confirmed | data-quality.html, every row matched |
| 15 | Default quotas 100 req/s for geo-places Geocode/SearchText/GetPlace | Confirmed | general/latest/gr/location.html |
| 16 | boto3 `geo-places` methods; QueryText ≤ 200; BiasPosition [lng, lat]; header `x-amz-geo-pricing-bucket` | Confirmed | boto3 reference; Geocode API page |
| 17 | IAM example uses `geo-places:*` with `Resource: "*"` | Confirmed | security-iam.html (only the wildcard form appears there; per-action names come from the quota names) |
| 18 | Mapbox Permanent $5.00/1k (≤500k), $4.00/1k above; no free row; "contact Mapbox sales"; "personal or business use … no distribution or sublicense" | Confirmed | mapbox.com/pricing (Temporary: 100k free, then $0.75/$0.60/$0.45) |
| 19 | Mapbox docs: Permanent may be stored indefinitely; card on file or enterprise contract; batch ≤ 50; 1,000 req/min; "only … in conjunction with a Mapbox map" | Confirmed | docs.mapbox.com/api/search/geocoding/ |
| 20 | Mapbox Product Terms 21/07/2026 §2.7.1(b), §2.7.2, §2.7.3 (i)–(iv) wording | Confirmed | Verbatim in PDF pp. 6 |
| 21 | Google §6.2 no non-Google map; §6.3.1 30-day lat/lng cache; §6.3.2 per-End-User indefinite cache | Confirmed | Service Specific Terms, last modified 10/06/2026. §6.3.2 also requires the cache be "logically isolated to the specific End User" — reinforces exclusion |
| 22 | Geoapify Free 3,000 credits/day, no card, 5 req/s, commercial/production allowed, 1 credit per geocode; API 10 $59/mo for 10k/day | Confirmed | geoapify.com/pricing |
| 23 | Geoapify: only OSM attribution needed | **Corrected** | Free plan also requires a "Powered by Geoapify" follow-link near the map/info; stored objects must keep data-source attribution. Fixed in summary item 4, §3.2, §4 table, §5.1 |
| 24 | Geoapify storage allowed ("we do not restrict you from storing results") | Confirmed | geoapify.com/geocoding-api FAQ |
| 25 | Geoapify free has no SLA | Confirmed | SLA 99.5% stated for paid plans only |
| 26 | OpenCage X-Small €45/mo, 10k/day, ≈€0.15/1k, "store data permanently", storage survives end of contract | Confirmed | opencagedata.com/pricing |
| 27 | OpenCage trial "becomes inactive after 3 months" | **Corrected** | FAQ: "inactive free trial accounts are deleted after three months"; trial is "testing only", not mission critical. Fixed in §3.3 |
| 28 | Nominatim public: max 1 req/s; bulk discouraged; long/periodic scripts 4 req/min; access may be withdrawn | Confirmed | operations.osmfoundation.org/policies/nominatim/ |
| 29 | OSMF Geocoding Guideline endorsed 24/08/2017; direct-hit results insubstantial; share-alike only if aggregated into whole/substantial part | Confirmed | osmfoundation.org guideline |
| 30 | Cost arithmetic (AWS $24 + $9.60 = $33.60; Mapbox $42; 8,200 → $32.80 / $41.00; bake-off 60 × $0.50/1k ≈ $0.03; Nominatim 6k ≈ 100 min) | Confirmed | Recomputed |
| 31 | Summary item 6 listed KH among "well covered" AWS countries | **Corrected** (wording) | KH and MM are POI/PA *Fair*; summary now says so |
| 32 | Which provider (HERE/Esri) answers a v2 request in us-west-2 | Unverifiable | Not documented on any page read; keep the HERE-class assumption and test with live calls |
| 33 | Geoapify/OSM recall for BT/NP/MN/Tibet villages, monasteries, passes | Unverifiable | No vendor publishes it; bake-off (§5.3) remains the gate |

