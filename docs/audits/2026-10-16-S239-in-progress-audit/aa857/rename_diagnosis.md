# AA-857 repair: why 43 kept Segments get renamed (dry run v3)

S239, 16/10/2026. Read-only analysis. Inputs: `repair_dryrun_v3_full.json` (the latest dry run, after CIS #768
84bba941 was deployed), `split_dryrun.json` (it has per-tour landing labels, which v3 does not have),
`mixed_segments.json`, `.tmp-session/s239/aa857_repair_apply.py`, and deployed
`services/acp_contract/segment_matching.py` at 84bba941. I ran the deployed pure functions locally to reproduce the
cases. I made no DB, AWS or ECS calls.

## Verdict

- **Do not apply v3.** The README gate (`plan_segments_renamed` must be 0) is right. Of the 43 renamed kept Segments,
  **35 change meaning** and 8 are benign.
- **This is not a simulation artifact.** All 43 relabels are writes to an id the run *claimed*. #768 still allows
  those: it only protects unclaimed ids. The apply would write the same labels. v2 (before the deploy) and v3 (after)
  have identical `summary` and `simulation`.
- **Root cause.** The repair detaches only *other-country* members. A kept id also holds **same-country members of
  other places**, glued there before #762.
  - Each re-run keeper-country tour that holds such an atom derives a component from its own atoms only.
  - That component claims the kept id, and the deployed upsert relabels the id with the component's label.
  - The stored label is defended only by the id's pseudo-atom. That pseudo-atom is either filtered out of the pool
    (its label is rule transit / unnamed_place) or loses the claim. The last re-run tour, in tour_id order, wins.
- **Minimal correct rule.** A kept id holds only the atoms whose place IS its original canonical place (the deployed
  seed rule `match_grade`, keeper country). It always keeps its original label.
  - Detach every other member, including same-country members of other places.
  - Guard every write to a kept id: other places are split off to a re-minted id, and the label is pinned.
  - A label pin alone is not enough (§5).

## 1. Classification of the 43

The test is whether the new label is the same place as the old one under the deployed Subject seed rule
`subject_seed.match_grade(old_place, new_place)`. This is the same rule the keeper choice uses.

| Class | n | Ids |
|---|---|---|
| Benign, action only (place string unchanged) | 6 | b9111b6c Kathmandu, dbab0b48 a local restaurant, e137fac1 local farmhouse, f4b040f1 Colombo, f72fa4f7 Luang Prabang, f7b7861f Kathmandu |
| Benign, case or article (grade 0) | 2 | b7dc862c the morning market -> Morning Market, e11cd23f hotel -> Hotel |
| Narrowing, loose match (grade 4: A3's own subset relation) | 5 | 8403eb18 Lhasa -> Lhasa station, bec66e43 tea plantations -> Longjing tea plantations, c5af6527 the ridge -> Singalila Ridge, cb155208 resort -> resort in Kumarakom, fcc1ea70 stream -> Aleo Nallah stream |
| Generic label -> one named member (seed test fails) | 9 | af96d6b4, d3de1529, d97b1057, e4cf4125, f1ce0648, f734d599, f8aaa422, fd175d52, fdd61fc7 |
| **Different named place** | 21 | 92a9 Chele La -> Dochu La, ba72, c081, c88e, cf55, d3e7 Dolma La -> Baga La, **d8aa Gyeongju -> National Folk Museum**, d94b Nam Ou -> Nam Song, e37a Darchen -> Taklakot, **f592 Delhi -> hotel**, f5b7 Yala -> Wilpattu, f5c1 Chengdu -> Shigatse, f5fc, **f60a Dal Lake -> Periyar NP**, f907, f9ea Karo La -> Cho La, fcc3 Amanwella -> Tangalle, fd5d airport -> your hotel, fe1d, fe8c, **fe94 Dal Lake -> Delhi hotel** |

**Meaning-changing = 35.** That is 21 different places, plus 9 generic-to-specific, plus 5 loose narrowings. In
the last two groups the label now names one member's specific place, while the other members are other lodges,
hotels, villages and so on.

The verify step compares `canonical_place` strings exactly, so it would FAIL on 37: everything except the 6
action-only renames.

### Per id

Column notes:

- **"Label in pool?"**
  - *excluded*: the stored label is rule `unnamed_place` (always out), or `transit`, which is out unless the members
    are typed non-transit. Member types are not in the dry run.
  - *contested*: the pseudo-atom is in the pool but in a different component.
- **"Keeper-country landings"**: the labels written onto the id by each keeper-country re-run tour, in tour_id
  order. They come from `split_dryrun.json` `per_tour[].landed`, which was the same claim path before #768 and
  without the wrapper.
- **"Aliases in"**: v3 `alias_merges` whose target is this id.
- **"Routes (sample)"**: current Routes on the id in `mixed_segments.json`. That file lists only 200 of 475 rows,
  so the count is a lower bound.

| Id | Keeper | Old -> new place | Class | Label in pool? | Keeper-country landings (label written, count) | Aliases in | Subjects | Route requests | Routes (sample) |
|---|---|---|---|---|---|---|---|---|---|
| `92a9a99ae4f0125b` | Bhutan | Chele La Pass -> Dochu La Pass | DIFFERENT PLACE | pseudo-X excluded (label rule-transit) | Dochu La Pass x1 | 0 | - | - | - |
| `ba72d00acb41dcc0` | Sri Lanka | the lodge -> Habarana | DIFFERENT PLACE | pseudo-X excluded (label rule-transit) | the lodge x5; Cinnamon Lodge x1; Hideaway Lodge x1; The Other Corner x2; Nil Diya Mankada Safari Lodge x1; Habarana x3 | 3 | - | - | - |
| `c08137e64cdd9ad8` | India | camp -> Thar Desert | DIFFERENT PLACE | pseudo-X excluded (label rule-unnamed_place) | none in split run | 0 | - | - | - |
| `c88e8721977ee129` | India | hotel -> Delhi | DIFFERENT PLACE | pseudo-X excluded (label rule-transit) | hotel x3; hotel in Varanasi x1; Delhi x1 | 0 | - | - | - |
| `cf5551d6dd84f169` | India | local bazaars -> Old City | DIFFERENT PLACE | pseudo-X excluded (label rule-unnamed_place) | Jaipur x1; Old City x1 | 1 | - | - | - |
| `d3e7b229c140d760` | Nepal | Dolma La -> Baga La Pass | DIFFERENT PLACE | pseudo-X in pool, contested | Dolma La x3; Kang La Pass x1; Cho La Pass x2; Baga La Pass x7 | 1 | - | - | 9 |
| `d8aa8991e02d6754` | South Korea | Gyeongju -> National Folk Museum | DIFFERENT PLACE | pseudo-X in pool, contested | Gyeongju x1; National Folklore Museum x2; National Folk Museum x3 | 1 | used 1, proposed 4 | 1 | 6 |
| `d94bb759a5dd0dbb` | Laos | Nam Ou -> Nam Song River | DIFFERENT PLACE | pseudo-X in pool, contested | Nam Song River x3; Nam Lik River x1; Nam Ou River x1; Nam Ou x6 | 0 | - | - | 9 |
| `e37ac03172ceb3e4` | Nepal | Darchen -> Taklakot (Purang) | DIFFERENT PLACE | pseudo-X excluded (label rule-transit) | Taklakot (Purang) x1 | 0 | - | - | - |
| `f59272229436fbe4` | India | Delhi -> hotel | DIFFERENT PLACE | pseudo-X excluded (label rule-transit) | palace restaurant x1; a hotel in Delhi x1; hotel x4; Delhi hotel x1; Delhi x1 | 4 | - | - | - |
| `f5b7ca3fa9e4e3f6` | Sri Lanka | Yala -> Wilpattu | DIFFERENT PLACE | pseudo-X in pool, contested | Wilpattu x2; Weheragala National Park x8; Yala's grassland, scrub forest, and network of seasonal reservoirs x1; Wilpattu National Park x1; Udawalawe National Park x3; Yala x6 | 1 | - | - | 3 |
| `f5c1116376ca2c53` | China | Chengdu -> Shigatse | DIFFERENT PLACE | pseudo-X in pool, contested | Qinghui Garden Hotel x1; hotel x4; Chengdu x1; Ramada Hotel x1; the hotel x4; Bishkek hotel x1; Shigatse x1 | 4 | - | - | 10 |
| `f5fcd4bfbed01666` | Sri Lanka | The Hideaway -> 98 Acre Resort | DIFFERENT PLACE | pseudo-X in pool, contested | 98 Acre Resort x2 | 0 | - | - | 10 |
| `f60a56fbf58add32` | India | Dal Lake -> Periyar National Park | DIFFERENT PLACE | pseudo-X in pool, contested | Mattupetty Dam x1; Periyar National Park x1 | 1 | proposed 5 | 4 | 5 |
| `f90746ac740f6bf4` | Nepal | Bamboo -> rhododendron forest of Lhamuje | DIFFERENT PLACE | pseudo-X in pool, contested | Bamboo x2; forest and rivers en route to Tadapani x1; rhododendron forest of Lhamuje x1 | 1 | - | - | 7 |
| `f9eaa1527833589d` | Nepal | Karo La -> Cho La Pass | DIFFERENT PLACE | pseudo-X in pool, contested | Karo La x1; Cho La Pass x2 | 0 | - | - | 3 |
| `fcc365a2b170fa9c` | Sri Lanka | Amanwella -> Tangalle | DIFFERENT PLACE | pseudo-X in pool, contested | Amanwella x2; Galle x1; Anantara Peace Heaven Tangalle Resort x1; Anantara Peace Haven Tangalle Resort x1; Tangalle x3 | 2 | - | - | 7 |
| `fd5d0701f1d6a57f` | China | airport -> your hotel | DIFFERENT PLACE | pseudo-X excluded (label rule-transit) | hotel lobby x4; your hotel x2 | 0 | - | - | - |
| `fe1d5b0a5d58142e` | Nepal | bridge -> Dudh Kosi | DIFFERENT PLACE | pseudo-X excluded (label rule-unnamed_place) | Nepal's longest suspension bridge x1; Kerung x1; Dudh Koshi River x1; Samagaon x1; Dudh Kosi x2 | 3 | - | - | - |
| `fe8c48341e917ea0` | India | Forest -> ridge crest at Ranthon | DIFFERENT PLACE | pseudo-X excluded (label rule-unnamed_place) | ridge crest at Ranthon x1 | 0 | - | - | - |
| `fe9452782e900af1` | India | Dal Lake -> Delhi hotel | DIFFERENT PLACE | pseudo-X excluded (label rule-transit) | hotel x2; Leh x1; Delhi x3; airport-accessible hotel x1; hotel in Agra x1; Cochin x1; Delhi hotel x1 | 3 | - | - | - |
| `af96d6b42ad1b638` | Nepal | the hotel -> Himalaya Hotel | generic -> one named member (seed test fails) | pseudo-X excluded (label rule-unnamed_place) | Kathmandu x11; Himalaya Hotel x1 | 1 | - | - | - |
| `d3de152934004186` | India | beach -> Marina Beach | generic -> one named member (seed test fails) | pseudo-X excluded (label rule-unnamed_place) | Promenade Beach x1; Marina Beach x1 | 0 | - | - | - |
| `d97b105781a19626` | Sri Lanka | village -> Dambana Veddha village | generic -> one named member (seed test fails) | pseudo-X excluded (label rule-unnamed_place) | Dambana Veddha village x1 | 0 | - | - | - |
| `e4cf412529213044` | South Korea | village -> Bukchon Village | generic -> one named member (seed test fails) | pseudo-X excluded (label rule-unnamed_place) | Andong Hahoe Village x1; Seongeup Folk Village x1; Hahoe Folk Village x1; Hahoe Village x2; Bukchon Village x3 | 2 | - | - | - |
| `f1ce0648e75934f1` | Sri Lanka | the lodge -> The Other Corner Lodge | generic -> one named member (seed test fails) | pseudo-X excluded (label rule-unnamed_place) | Polwaththa Eco Lodge x1; The Other Corner Lodge x1 | 0 | - | - | - |
| `f734d599923500c2` | China | a local Buddhist monastery -> Pawangka Monastery | generic -> one named member (seed test fails) | pseudo-X in pool, contested | Pawangka Monastery x2 | 0 | used 2, picked 1, proposed 2 | 4 | 21 |
| `f8aaa42206663558` | Sri Lanka | the hotel -> Hotel Sinharagama | generic -> one named member (seed test fails) | pseudo-X excluded (label rule-transit) | the hotel x14; Goldi Sands x2; Bay Vista Hotel x1; Hotel Sinharagama x2 | 1 | - | - | - |
| `fd175d52fc6f284a` | India | desert camp -> Naerak village camp | generic -> one named member (seed test fails) | pseudo-X excluded (label rule-transit) | Naerak village camp x1 | 0 | - | - | - |
| `fdd61fc74750beba` | Bhutan | Forest -> blue pine forest to Phajoding Gompa | generic -> one named member (seed test fails) | pseudo-X excluded (label rule-unnamed_place) | blue pine forest to Phajoding Gompa x1 | 0 | - | - | - |
| `8403eb182c6df3f9` | China | Lhasa -> Lhasa station | narrowing, seed-rule loose match (grade 4) | pseudo-X excluded (label rule-transit) | Lhasa station x1 | 0 | - | - | - |
| `bec66e43b136473e` | China | tea plantations -> Longjing tea plantations | narrowing, seed-rule loose match (grade 4) | pseudo-X excluded (label rule-unnamed_place) | Longjing tea plantations x2 | 0 | - | - | - |
| `c5af65271a5a586f` | India | the ridge -> Singalila Ridge | narrowing, seed-rule loose match (grade 4) | pseudo-X excluded (label rule-unnamed_place) | Singalila Ridge x1 | 1 | - | - | - |
| `cb1552080f6e9a47` | India | resort -> resort in Kumarakom | narrowing, seed-rule loose match (grade 4) | pseudo-X excluded (label rule-unnamed_place) | backwater resort x1; wildlife resort x3; Marari resort x1; resort in Kumarakom x1 | 2 | - | - | - |
| `fcc1ea709b9c4fba` | India | stream -> Aleo Nallah stream | narrowing, seed-rule loose match (grade 4) | pseudo-X excluded (label rule-unnamed_place) | Aleo Nallah stream x1 | 0 | - | - | - |
| `b7dc862cb82726ce` | Laos | the morning market -> Morning Market | benign: same place (case/article) | pseudo-X excluded (label rule-unnamed_place) | Morning Market x1 | 0 | - | - | - |
| `b9111b6c76b46e05` | Nepal | Kathmandu -> Kathmandu | benign: same place, action only | pseudo-X in pool, contested | Kathmandu x8; Durbar Square x9 | 2 | - | - | 5 |
| `dbab0b48e381b1cf` | China | a local restaurant -> a local restaurant | benign: same place, action only | pseudo-X excluded (label rule-transit) | local restaurant x14 | 0 | - | - | - |
| `e11cd23f51829202` | India | hotel -> Hotel | benign: same place (case/article) | pseudo-X excluded (label rule-transit) | Delhi x1; the hotel x4; Agra x1; Hotel x17 | 3 | - | - | - |
| `e137fac113c9e6b6` | Bhutan | local farmhouse -> local farmhouse | benign: same place, action only | pseudo-X excluded (label rule-unnamed_place) | local farmhouse x1 | 0 | - | - | - |
| `f4b040f153591b1e` | Sri Lanka | Colombo -> Colombo | benign: same place, action only | pseudo-X excluded (label rule-transit) | Colombo x1 | 0 | - | - | - |
| `f72fa4f7b9f0ec19` | Laos | Luang Prabang -> Luang Prabang | benign: same place, action only | pseudo-X in pool, contested | Luang Prabang x5; Vang Vieng's limestone slopes x1 | 1 | proposed 6 | 1 | 6 |
| `f7b7861f791d5a2a` | Nepal | Kathmandu -> Kathmandu | benign: same place, action only | pseudo-X in pool, contested | Kathmandu x9; Pokhara x2; Lhasa x1 | 2 | - | - | - |

Every Subject and route request on a renamed id sits on 3 meaning-changing ids, with one exception: the benign
f72fa4f7 has 6 proposed Subjects (seed -> seed, unaffected) and 1 approved route request. The 3 ids:

- **d8aa8991 Gyeongju.**
  - Subjects:
    - used 766e9956 (tenant 20d07d32, the S239 "Gyeongju -> Lok Virsa Museum" post);
    - proposed 7b594020 (tenant 885d4916);
    - proposed ece32ec7 and 972c7d41 (tenant 20d07d32);
    - proposed d61efdbb (tenant 9149d3c6).
  - Approved route request: 41e41098.
- **f60a56fb Dal Lake.**
  - Subjects:
    - proposed e64167ac (tenant 692a3214);
    - proposed 5d211b8a, 6bed9f76 and 0d6b0815 (tenant 20d07d32);
    - proposed ef3eb37d (tenant 9149d3c6).
  - Approved route requests: 15e682d0, 1dfbf5e6, 3bf7a5f7 and b96797b8.
- **f734d599 "a local Buddhist monastery".**
  - Subjects:
    - used 647021fe (tenant 9149d3c6) and 0a8fe5b1 (tenant 20d07d32);
    - **picked 58830c09** (tenant 885d4916). Its in-flight `pending_choice` request a7ba72cf has atom 04369bde
      (Pawangka Monastery, China) and `needs_decision = not_on_tenant_tours`;
    - proposed 25b3a0e0 and 65939089 (tenant 20d07d32).
  - Route requests: the same 4 as f60a.

For these 3 ids, `subjects_predicted.outcome_after` was computed against the **renamed** label
(`predict_subjects` uses `place_after`, script lines 629-634). The predicted Subject outcomes for them are therefore
not meaningful.

**Full Route count.** It is not in the dry run, because `SIDE_ROUTES_SQL` only runs for alias old ids. To get it, the
orchestrator can run `SIDE_ROUTES_SQL` with the 35 ids, read only.

## 2. Why the kept id ends up with another place's label

Code references are to deployed `segment_matching.py` at 84bba941 and to `aa857_repair_apply.py`.

### A. The kept id still holds same-country members of other places (root)

`compute_plan` detaches only members whose known country differs from the keeper (script lines 378-379).

The kept ids are multi-place *inside* the keeper country. In the split run, the keeper-country landings show 2 to 8
distinct places per id:

- fe94 "Dal Lake": Delhi, Leh, Cochin, hotel in Agra, Delhi hotel, airport-accessible hotel (140 India members);
- f5b7 "Yala": Weheragala, Udawalawe, Wilpattu;
- f5c1 "Chengdu": Shigatse, Ramada Hotel, Bishkek hotel;
- d8aa "Gyeongju": National Folk(lore) Museum.

Two Segments with label "Dal Lake" (f60a and fe94) even have **no Dal Lake member at all**: f60a's keeper rule is
`no_member_matches_subject_place`.

### B. How these ids became multi-place: `reconcile_ids` keeps the largest prior id

When one derived Segment carries several prior ids, the loop over `sorted(_claims(...))` reassigns
`ids[claimant] = prior` for every later prior (lines 310-322). So the **lexicographically largest** id survives,
whatever share of the atoms it holds.

Reproduced locally: `{a1: 1111aaaa, a2: ffff0000, a3: 8888bbbb}` and `{a1: ffff0000, a2: 1111aaaa, a3: 1111aaaa}`
both end on `ffff0000`.

High ids are therefore sinks for every bridging merge:

- 85 of the 96 mixed ids start with b–f. About 30 would be expected at random.
- In v3, 60 alias merges target a plan id, and 40 of those target a renamed one. fe94, f592 and f5c1 absorb 3–4
  Segments each.
- All 7 plan ids that give way go to a larger id: d0b4->d911, dd2f->f5c1, e845->fc48, eed0->fc48, e11c->fb02,
  b7dc->fa10, fd5d->ffea.

So the repair keeps feeding the same sinks.

### C. Each re-run tour relabels the kept id from its own component

`run_segment_matching` derives Segments from **this tour's atoms plus one pseudo-atom per candidate existing
Segment** (lines 937-973). It never looks at the kept id's other members. A keeper-country tour T with an atom on
the kept id X:

1. **Pseudo-X not in the pool** (24 of the 35: labels such as "transfer to…", "drive to", "arrive at", "the hotel",
   "village", "Forest").
   - `joinable_existing` filters by `_existing_forms_segment` (line 957) **before** `_candidate_pseudo_atoms(...,
     keep=held)` (lines 959-965). The `keep` set cannot bring back a held Segment that the filter dropped.
   - T's component is then the only contender for X.
2. **Pseudo-X in the pool but another place** (11 of the 35: Gyeongju, Yala, Nam Ou, Dolma La, Chengdu…). T's atom
   does not join pseudo-X, so `_claims` (lines 334-358) splits X between them:
   - pseudo-X's component holds 1;
   - T's component holds k.
   - Pseudo-X keeps X outright only when its re-derived id equals X. That is false for all 11, because these ids
     are mints of another moment or country (RESIDUAL-22 drift).
   - So T wins when k ≥ 2, or on the tie-break (the smaller derived id).
3. T's component is written as X. X is in `claimed` (line 977), so the upsert's `$4` is true (lines 997-1000), and
   `canonical_place` / `canonical_action` become T's label.
4. Every keeper-country tour that holds a stale atom on X does this. The **last one in tour_id order** decides the
   final label. Example, d8aa: Gyeongju, then National Folklore Museum ×2, then National Folk Museum ×3.

Reproduced with the deployed functions (one re-run tour, real labels):

```
fe9452782e900af1 'Dal Lake / transfer to a houseboat or hotel', members untyped -> pseudo-X excluded
   fe9452782e900af1 (=X): 'Delhi hotel' / 'transfer and rest' [WRITTEN] -> relabels X (claimed)
92a9a99ae4f0125b 'Chele La Pass / drive to', members untyped -> pseudo-X excluded (although it would re-derive X)
   92a9a99ae4f0125b (=X): 'Dochu La Pass' / 'drive to and view panoramic vistas' [WRITTEN] -> relabels X
d8aa8991e02d6754 'Gyeongju / visit archaeological remains…' -> pseudo-X in pool, separate component
   d8aa8991e02d6754 (=X): 'National Folk Museum' / 'visit' [WRITTEN] -> relabels X
   ad07e5172a561900: 'Gyeongju / …' [pseudo-only, not written]
f59272229436fbe4 'Delhi / dine together' + T 'hotel / eat breakfast' -> X relabelled 'hotel / eat breakfast'
f5b7ca3fa9e4e3f6 'Yala / …' + T 2× 'Wilpattu / conduct … safari' -> X relabelled 'Wilpattu' (k=2 beats 1)
```

### D. A3 never removes a stale membership

The member write is `INSERT … ON CONFLICT DO NOTHING` (lines 1013-1018), and `atom_segment_member`'s key is
`(segment_id, atom_id)`, so an atom can sit in several Segments. When pseudo-X does win (for example "Dal Lake" with
typed members), T's other-place atom gets a new Segment **and stays on X**.

Re-running a tour therefore never cleans X. Only the repair's detach can remove those atoms.

### E. The simulation is right for these 43; #768 does not change them

The causes suggested in the brief, checked one by one:

- **"The simulation relabels differently from #768."** The simulation relabels every written id unconditionally
  (script lines 534-535). #768 relabels only claimed or memberless ids. That matters only for unclaimed writes, and
  there are 2 of those (`638e7a1e…` Minneriya and `bc1728b4…` Kathmandu), neither a plan id. All 43 are claimed
  writes, so the apply would produce the same labels.
- **"The label recompute ignores the original canonical."** Yes. In `derive_segments` the original label survives
  only as the pseudo-atom's key: it wins `_canonical` and the label `min()` only when it is in T's component. It is
  never compared with the stored label.
- **"The keeper's own seed atoms re-derive into a new id and the leftovers keep the old id."** Not the main path. The
  seed atoms mostly stay on X. It is the leftover same-country other-place atoms that *re-run* and claim X.
- **Real simulation limits.**
  - `apart = ∅`: Jev never keeps a pair apart, so this is an upper bound on joins. It affects names that share
    tokens (Chele/Dochu La Pass, Nam Ou/Nam Song River), not the mechanism.
  - v3 has no per-tour landing detail. For c08137e6 ("camp" -> "Thar Desert"), no India writer is visible in the
    split run.
- **Ids minted from the place that now takes them.** Eight ids are the mint of the new label in the keeper country:
  8403 Lhasa station, d97b, f1ce, f5fc, f60a Periyar NP, f8aa, fd17, fd5d.
  - Even after a detach, a fresh derivation of that place mints exactly X.
  - It is the same country, so `REMINT_SCOPE="foreign"` does not re-mint it, and it would land on X again as an
    unclaimed same-country write.
  - The rule below must cover this.

## 3. Proposed repair rule (minimal, correct)

**Invariant for every kept (plan) id X with snapshot label L and keeper country K:**

1. X holds only atoms whose place is L's place.
2. X keeps L.

The test is `seed(atom) := match_grade(L.place, atom, alias_cards) is not None`, applied to atoms of K (or of
unknown country). It is the same function and the same alias cards as `compute_plan`'s keeper rule.

1. **Detach (in `compute_plan`).** Detach every member of X that is not a seed, from any country. This adds the
   same-country members of other places to today's foreign rows.
   - A plan id with **no seed in K** is retired (all members detached, no alias row). Today that means at least f60a
     (Dal Lake) and f734 (a local Buddhist monastery), plus any `subject_place_in_several_countries` id whose keeper
     country has no seed.
   - List the retired ids for Nghiệp. Their proposed Subjects go at the t7 refresh. Picked and used Subjects keep
     their frozen atom.
2. **Re-run set.** The tours of every detached live atom. This is larger than 543, and the dry run gives the number.
3. **Plan-id guard** (in `_guarded_reconcile` for apply, and the same pure function in `simulate`). It runs after
   `reconcile_ids` and `avoid_foreign_ids`. For each Segment the run would write with id X:
   - **It contains pseudo-X or at least one seed atom.** Keep the id. Split its non-seed real atoms off into a
     sibling with id `remint_id(X, own_country, n)` and the sibling's own canonical label. Set the place and action
     of X's Segment to L (**label pin**). The deployed claimed-relabel then writes L back unchanged.
   - **It contains neither.** Re-mint the whole Segment and remap aliases that point at X, as `avoid_foreign_ids`
     does. This covers the 8 "minted from the new place" ids.
   - **An alias row X -> Y.** Allow it only when Y's component contains a seed of L (a same-place merge). Otherwise
     keep X: drop the alias and re-mint Y's component as above.
   - The guard needs each tour's atom places and countries. Load them in `refresh_guard(tour_id)`, which already has
     the tour.
4. **Gates.**
   - Dry run: `plan_segments_renamed` (exact string) = 0, plus a new `plan_segments_multi_place` = 0 (every live
     member of a plan id is a seed of L).
   - Verify: the same `plan_segments_multi_place` check, next to `plan_segments_relabelled`.
   - Report `plan_ids_retired`.
   - Have `predict_subjects` judge against L, not `place_after`.
5. **Keep `REMINT_SCOPE="foreign"`.** `any_member` would also re-mint the 2 legitimate same-moment joins (Minneriya,
   Kathmandu bc1728b4) and split real Segments. The plan-id guard is the narrow version of what is needed.

**Expected effect.**

- Detached other-place atoms have no prior on X, so they cannot claim it.
- A seed atom's component may still claim X when pseudo-X is excluded, but the pin keeps L.
- Fresh mints of X are re-minted.
- The result is 0 renamed kept ids and 0 multi-place kept ids, at the cost of more detach rows, more re-run tours,
  and the retired ids.

## 4. Outside the 43 (report, not gated today)

v3 also renames **295 non-plan Segments** by the same claimed-relabel path. 128 of them fail the same seed test.

Examples:

- 1c397b64 Kanha NP -> Bandhavgarh NP;
- 2cd24169 Shaxi -> Luoyang old town;
- 40c4a307 Dutch Fort -> Galle Fort;
- **52382434 Udawalawe NP (Sri Lanka) -> Ranthambore NP (India)**.

The deployed A3 does the same on every `a3_atomize`. Suggest at least counting them in the dry-run summary
(`non_plan_renamed_other_place`) so that Nghiệp approves them knowingly.

## 5. Options I rejected

- **Pin the plan labels only.** The label would be right, but X keeps the other-place members, for example 140 India
  members under "Dal Lake", mostly Delhi hotels. It also keeps absorbing alias merges (§2B). Route landing still
  lands them on X, and the next `a3_atomize` relabels again, because the deployed code has no pin.
- **`REMINT_SCOPE="any_member"`.** It does not stop claimed relabels, and it splits legitimate same-moment Segments.
- **Re-run the keeper-country tours too.** That makes it worse: more claimants on X, and the last writer still wins.

## 6. Durable CIS follow-ups (for Nghiệp to decide; no Linear issue created)

These change A3 behaviour for every tour. Each needs an ADR or design note, not AA-857's repair script.

1. **Let a held Segment defend its id.** Bring held Segments into the pool even when `_existing_forms_segment` is
   false. Alternatively, in `_claims`, give a prior id only to the component that contains its pseudo-atom when that
   pseudo-atom is in the pool.
2. **Relabel a claimed id only on a same-place label.** Do it only when the new canonical place matches the stored
   one under `match_grade`.
3. **Remove a stale membership** when an atom's new component does not keep that Segment's id (§2D).
4. **Revisit "largest prior wins"** in `reconcile_ids` for bridging merges (§2B). For example, let the id holding
   most atoms win, as the `_claims` docstring describes.

## 7. Limits of this analysis

- No DB access. I did not have member-level data for the plan ids.
- The landings come from the split dry run (deployed functions without the wrapper). The keeper-country claim path is
  the same, but foreign collisions differ there.
- Member `activity_type`s are unknown, so "excluded" for transit labels assumes untyped or transit members.
  `unnamed_place` is always excluded.
- The Route counts are a lower bound from a 200-row sample.

Scripts used: scratchpad `classify.py`, `repro.py`, `nonplan.py` and `largest.py`. They run the deployed module from
`git show origin/main:services/acp_contract/segment_matching.py` with `apps/AA-CIS-App/.venv`.
