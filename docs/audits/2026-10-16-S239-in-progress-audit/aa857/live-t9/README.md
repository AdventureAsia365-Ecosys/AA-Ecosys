# AA-857 live T9 write on the fixed Subject (S239, Claude Code)

- **Tenant:** terra-family (`20d07d32-ed98-405f-81d5-0c2399c9fcdf`), test tenant. The api_key came from Secrets Manager at run time. No key or JWT is printed or saved.
- **Subject:** `3833fa3d-9587-4e18-9dff-804652bf717d`. Channel linkedin. Segment `50870fc4cfa77887` "Traditional Arts & Craft School", action "visit". Seed atom `c64ebfc5d8c3b815` "Traditional School of Arts and Craft", Bhutan.
- **Why:** before AA-857 this place shared a Segment with "National Library", and the National Library subject produced a post about this craft school.
- **Run window:** 2026-10-16 08:35:25 to 08:36:31 UTC.
- **Method:** tenant API only, the same flow as the AA-668 run: pick, goal, angles, choose angle 0, write, then poll. Each paid POST was sent once. Cost was read afterwards through the admin job-runner API (read-only).
- **Not done:** no publishing and no channel connection.

## Verdict: PASS

| Check | Result |
|---|---|
| Subject pickable | Present in `GET /v1/slate` as `proposed` (score 2203, cleared the LinkedIn bar). `POST /v1/subjects/{id}/pick` returned **200** with request `41e94397-aa14-45f6-9e23-337a0362fd19` and atom `c64ebfc5d8c3b815`. |
| Angle gate | Goal `introduction_awareness` returned 202. Three angles arrived in about 20 s. `choose {idx:0}` picked "Watching Craft Become Skill Over Years" and returned 200. |
| Write | `POST …/write` returned **202** with piece `6925acce-b2ed-49bd-a52b-41a74a2e6d60`. The piece was ready about 37 s later. |
| Piece status | Tenant view: `ready_state: ready`, channel `linkedin`. Admin `/admin/content-quality/pieces/{id}`: **`approved`**, held_reason null. Progress: `done`, revision 1, all 5 steps done. |
| About the right place | **Yes.** The post is about the National Institute for Zorig Chusum (the Traditional School of Arts and Craft) in Thimphu, Bhutan. |
| No other country's place | **Yes.** The only places named are Thimphu and Bhutan. A keyword scan found no "National Library", no Paro or Punakha, and none of the neighbouring countries or cities. |
| Cost | t8_angles: $0.027799 (1 call). t9_write: $0.028070 (9 calls). **Total: $0.055869.** The write is within the ~$0.03 budget, and the total is under the $0.15 cap. |

Quote from the piece:

> "At the National Institute for Zorig Chusum, students master a single craft over years of study."
>
> "Because this is a government-run school in Thimphu dedicated to formal craft education, it carries a clear educational thread that fits naturally into a family itinerary."

The hashtags are `#Thimphu #ZorigChusum #Bhutan`. The post ends with the brand default CTA.

## Notes

- The text names the place "National Institute for Zorig Chusum", not the seed's "Traditional School of Arts and Craft". They are the same institution in Thimphu.
- Angle 0 mentions "a culinary trail itinerary" and "the 10-day Bhutan Culinary Trail". These come from the anchor tour, "Bhutan: Culinary Trail East to West — 10 Days", which is in the same country. The finished post does not mention the tour.

## Files

- `live_t9.py`: the tenant API run.
- `admin_jobs_cost.mjs`: read-only admin job and LLM cost read.
- Tenant responses:
  - `raw/00_*`: slate and subject row
  - `raw/01_pick.json`
  - `raw/02_goal.json`
  - `raw/03_request_angles.json`
  - `raw/04_choose.json`
  - `raw/05_write.json`
  - `raw/07_piece_final.json`: full text
  - `raw/08_latest_piece.json`
  - `raw/09_review.json`
  - `raw/10_progress.json`
  - `raw/11_request_final.json`
- `raw/12_admin_jobs_llm_cost.json`: job rows, LLM calls and the admin piece status.
