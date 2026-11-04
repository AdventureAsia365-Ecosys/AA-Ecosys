# AA-1043 — Amazon Location Service vs Geoapify, small trial (S267, 04/11/2026)

Tech lead request: test the AWS-native geocoder on a small sample, no data overwrite, capped cost.

## Method

- Sample: 50 places with an accepted Geoapify point (`shared.destinations`), read-only, seeded, 9 countries
  (IN, NP, CN, LK, KR, JP, PH, LA, TW), with hard cases: 8 non-Latin names, 8 islands, 9 temples, 6 diacritics,
  4 areas. Script `geo_sample.py` (one SELECT in a READ ONLY transaction).
- Calls: Amazon Location Places API v2 in us-west-2 (no endpoint in us-west-1). One `Geocode` per place
  (name + locality, country filter, `IntendedUse=Storage` so the price matches how we keep points), `SearchText` with
  a country bias when Geocode found nothing, one extra probe with the local-script name where we have one.
  Script `geo_trial.py`, hard cap 120 requests, no retries, account check before any call.
- Nothing was written to the database or to any AWS resource. Outputs: `aws_location_trial.csv`,
  `aws_location_trial_summary.json`.

## Results

| Measure | Value |
|---|---|
| Requests / cost | 81 requests, all billed Stored (4.00 USD per 1,000) = **0.32 USD** |
| Found | 44 of 50 (88 %); the 6 not found are **all in South Korea** |
| Country match (found) | 100 % |
| Distance to the stored Geoapify point | median 19 km, p90 1,475 km; 12 within 1 km, 18 within 5 km, 21 over 25 km |

Hand review of the largest gaps (stored point vs Amazon's answer): the stored Geoapify points are right and Amazon
matched the wrong place, often by name similarity:

| Place | Amazon answer | Gap |
|---|---|---|
| Drepung Monastery (Lhasa) | "Yan Chi Monastery" | 2,424 km |
| Ngamring lake (Tibet) | a casino in Macao | 2,749 km |
| the Wu Gorge (Yangtze) | a resort hotel in Macao | 1,065 km |
| Manas National Park (Assam) | a park in Delhi | 1,388 km |
| Ikema Island (Okinawa) | Ikoma district, Nara | 1,475 km |
| Batad Saddle Junction (Ifugao) | "Junction", Mindanao | 1,182 km |

Coverage is weak in mainland China (answers drift to Macao/Hong Kong), missing in South Korea, and poor for
landmark names (POI search by name) across the region.

## Price comparison

- Amazon Location Places v2 (us-west-2, AWS price list 2026-09-11): Geocode / SearchText Core 0.50, Advanced 1.50,
  **Stored 4.00 USD per 1,000**. We store coordinates, so our use is the Stored bucket; the Core free tier does not
  cover it.
- Geoapify: today's use stays inside its free daily credits (the daily credit guard in the CIS geo jobs).

## Recommendation

**Keep Geoapify** as the geocoder. Amazon Location is less accurate on our Asian places, has no Korea data and costs
more for stored results. Not worth adding even as a fallback. Revisit only if Geoapify's terms or price change.
