# AA-TripPlanner-Web

Nguồn yêu cầu: Notion "AA_TripPlanner_AI — PRD Canonical v0.3 (Map-First)".

- `frontend/` Next.js (Vercel) + BFF route; `backend/` hai Lambda: `browse/handler.py` (Map/Browse, read-heavy, không gọi LLM) và `assembly/handler.py` (Trip Assembly, event log, compose/renarrate qua Bedrock). `backend/extraction/` là pipeline offline (không phải Lambda).
- Dữ liệu: `tripplanner.itinerary_components` (pipeline batch đọc atom → component), `shared.destinations` (golden record, geocode Mapbox một lần mỗi địa danh).
- Đơn vị khách pin: `itinerary_component` (destination + activity + thời lượng), không phải nguyên tour.
- "Send to advisor" là cổng người duy nhất. Chặn đăng ký bằng flag `require_registration_before_handoff`.
- Việc mở trước khi có khách thật: AA-731 (idempotent handoff, đọc `v_active_tour_atoms`, chạy lại sau wave, grounding renarrate, email advisor).
- Bàn giao sang AAA: `~/projects/AA-Ecosys/docs/tripplanner-to-aaa-handoff.md`.
