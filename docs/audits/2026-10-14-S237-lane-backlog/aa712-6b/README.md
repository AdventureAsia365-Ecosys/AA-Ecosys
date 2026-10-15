Role: `tripplanner`, country: Laos.

### Coverage (tour graph)

| | value |
|---|---|
| raw_tours_mapped | 987 |
| catalog_live_tours | 46 |
| legacy_graph_tours | 4 |
| legacy_key_is_live_source_id | 0 |
| legacy_key_is_tour_id_mapped | 4 |
| legacy_key_not_live | 0 |
| legacy_graph_live | 4 |
| cis_graph_tours | 45 |
| cis_graph_live | 45 |
| in_both | 4 |

### Readers

| Reader | legacy | cis |
|---|---|---|
| /browse/countries: Laos components | 428 (84 ms) | 660 (33 ms) |
| /browse/by-country: destinations / components | 154 / 428 (46 ms) | 312 / 660 (18 ms) |
| /browse/tiles, 80 one-degree cells: destinations / components / total ms | 161 / 472 / 122 | 381 / 757 / 1014 |
| /browse/tiles/10_100_10: destinations (ms) | 141 (4) | 290 (397) |
| /browse/tour-route over 46 live tours: status:match | {'404:None': 19, '200:places': 23, '200:tour_graph': 4} (8303 ms) | {'200:tour_graph': 46} (1281 ms) |
| cis located_by / precision (by-country) | | {'mapbox': 10, 'llm': 183, 'geoapify': 119} / {'None': 54, 'area': 139, 'point': 119} |

### Destination detail (union of both by-country lists)

387 destinations: same component count 20, cis more 267, cis fewer 100; only in legacy 75, only in cis 233. Time legacy 846 ms, cis 3606 ms. Largest differences (id, legacy, cis): [['052f353a-0e04-45c1-9b39-f2a2f856a3d1', 17, 6], ['99cf5698-0429-41fb-a9eb-4e923ddb70ed', 2, 13], ['6fd2e9d4-effe-44fb-b8dc-71dd5df1d780', 0, 10], ['a8ec74ad-62b4-4e52-89d3-77240f905522', 10, 0], ['dc8be442-2023-4d14-8935-84f049eb0285', 10, 0], ['309d27e9-6bc0-44d8-9f0b-0e98e88c0be5', 20, 11], ['a213cca5-b186-45ea-bfa1-97b27c67ed3d', 17, 26], ['c2344921-4bec-4855-9678-8e233adea7a7', 10, 19]].

### Routes (/browse/routes, country = Laos)

| days | legacy proposals (whole / chains) | cis proposals (whole / chains) | same tour sets | pinned days legacy / cis | ms legacy / cis |
|---|---|---|---|---|---|
| 3 | 4 (0 / 0) | 5 (3 / 0) | False | 9/12 / 10/12 | 73 / 1101 |
| 5 | 5 (1 / 1) | 5 (5 / 0) | False | 16/25 / 23/25 | 26 / 1357 |
| 7 | 5 (2 / 1) | 5 (5 / 0) | False | 20/32 / 32/35 | 31 / 1121 |
| 9 | 5 (1 / 2) | 5 (5 / 0) | False | 25/42 / 33/40 | 35 / 1067 |
| 10 | 5 (0 / 3) | 5 (5 / 0) | False | 29/50 / 40/50 | 36 / 971 |
| 12 | 5 (0 / 3) | 5 (5 / 0) | False | 33/60 / 49/53 | 41 / 969 |
| 14 | 5 (1 / 3) | 5 (5 / 0) | False | 35/70 / 53/67 | 40 / 883 |
| 16 | 5 (2 / 3) | 5 (5 / 0) | False | 40/78 / 61/75 | 45 / 807 |
| 21 | 3 (0 / 3) | 5 (1 / 4) | False | 37/63 / 94/105 | 42 / 369 |

### Search (8 fixed query vectors = embeddings of Laos components; no Bedrock call)

| q | country filter | results legacy / cis | top-10 overlap | same top-1 | ms legacy / cis |
|---|---|---|---|---|---|
| 0 | False | 60 / 60 | 0 | False | 1187 / 367 |
| 0 | True | 60 / 60 | 0 | False | 359 / 159 |
| 1 | False | 60 / 60 | 5 | True | 193 / 154 |
| 1 | True | 60 / 60 | 5 | True | 155 / 155 |
| 2 | False | 60 / 60 | 1 | False | 150 / 163 |
| 2 | True | 60 / 60 | 1 | False | 120 / 192 |
| 3 | False | 60 / 60 | 4 | True | 160 / 171 |
| 3 | True | 60 / 60 | 6 | True | 21 / 207 |
| 4 | False | 60 / 60 | 4 | False | 38 / 128 |
| 4 | True | 60 / 60 | 4 | False | 13 / 120 |
| 5 | False | 60 / 60 | 3 | False | 34 / 106 |
| 5 | True | 60 / 60 | 3 | False | 13 / 103 |
| 6 | False | 60 / 60 | 0 | False | 34 / 29 |
| 6 | True | 60 / 60 | 1 | False | 13 / 17 |
| 7 | False | 60 / 60 | 3 | False | 35 / 19 |
| 7 | True | 60 / 60 | 3 | False | 13 / 19 |

Tour-route: both 200 on 27 tours (25 with the same day count); legacy 200 but cis 404: 0 []; legacy 404 but cis 200: 19.
