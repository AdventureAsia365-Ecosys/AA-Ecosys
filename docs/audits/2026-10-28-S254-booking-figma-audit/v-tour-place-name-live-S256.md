# catalog.v_tour_place_name — live budget after the switch (S256, 29/10/2026 00:35 +07)

CIS migration 298 (CIS #1118, Infra #487, DB Migrate apply 40734310260) + AA-Booking #141 (`ad4be194`), read-only script
`live_place_name_budget.py` run in the Booking api task:

```
who=booking v_tour_place_name=True
tours= 25 v_tour_place=    381 ms  v_tour_place_name=    109 ms  budget=150 ms  tours_with_places=25  same_places=True
tours=100 v_tour_place=   1176 ms  v_tour_place_name=    274 ms  budget=500 ms  tours_with_places=100  same_places=True
list(limit=100) cold total_ms=497 degraded=[] destination_statements_ms=[103, 93, 122, 95] reads_v_tour_place=[]
BUDGET_OK
```
