# AA-1038 — TripPlanner web cost on ECS (Dev), first days after the move

Read 10/11/2026 (S276) from Cost Explorer, acc2, tag `App=tripplanner`, unblended USD. Cost Explorer lags about a day,
so 09/11 is partial.

| Day | ECS (Fargate Spot) | WAF | API Gateway | Secrets Manager | S3 | CloudWatch | Total |
|---|---|---|---|---|---|---|---|
| 07/11 (before) | – | – | – | 0.041 | 0.010 | – | 0.05 |
| 08/11 (move day) | 0.124 | 0.022 | 0.044 | 0.066 | 0.011 | 0.019 | 0.29 |
| 09/11 (partial) | 0.089 | – | 0.003 | 0.041 | 0.010 | – | 0.14 |

Reading:
- The web service `aa-tripplanner-dev-web` runs one Fargate Spot task (task def :6, rollout COMPLETED, `/api/health`
  ok on `245595cb`).
- ECS is about 0.09–0.12 USD a day, about 3–4 USD a month.
- The WAF web ACL and rules are billed mostly as a monthly fee, about 7–8 USD a month.
- Secrets Manager about 1.3–2 USD a month. CloudFront requests are inside the free tier at Dev traffic.
- **Measured so far:** the cost tagged `App=tripplanner` is about 0.1–0.3 USD a day (08–09/11), about 3–9 USD a month.
- **Not visible yet:** the WAF web ACL and rule fees are billed monthly (about 7–8 USD a month at list price) and do not
  show in two days of daily data. Adding them gives an **estimated** 12–14 USD a month, in line with the 13–15 USD the
  tech lead approved in S265. The estimate is unverified until the November bill.
- Vercel is no longer used: the project was deleted on 08/11.
- Re-read at the monthly capacity review (C8, early December) with the full November bill.

Raw data: `ce-app-daily.json` (daily, grouped by the `App` tag, 01–09/11).
