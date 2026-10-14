# AA-774 place-card fact-kind audit (S235, AI panel — pending Nghiệp approval)

Scope: 110 non-rejected cards, 732 facts (all auto_checked). Two independent lenses (A: classifier, B: compliance reviewer). Files: cards_export.json, facts_flat.json, lens_a.json, lens_b.json, consensus_plan.json.

- Writer kind → withheld, both lenses agree: 31 (A total 34, B total 35)
- Withheld → writer kind (pure background), both agree: 22
- Disagreements: 7 (3 only A, 4 only B). Recommendation: apply only Nậm Cắn #0 (border open to foreign nationals → practical); keep the other 6 (geography/background).

Root cause: the drafter appends traveller clauses ("…, making it a natural stopping point", "offers views") to physical facts. Follow-up: drafter prompt rule (AA-774 / AA-802).

## Agreed writer → withheld

- Dochula Pass #3: setting → visiting — On clear days the pass offers panoramic views of the eastern Himalayan peaks, including Masagang, Tsendagang, and Gangkar Puensum — Bhutan's
- Jampa Lhakhang #7: setting → visiting — The temple is located close to Kurje Lhakhang, another major sacred site in Bumthang, and both are often visited together.
- Kuensel Phodrang Nature Park #6: setting → visiting — The park sits on the Kuensel Phodrang hill and offers panoramic views over the Thimphu valley.
- Kuensel Phodrang Nature Park #8: setting → visiting — The surrounding nature park contains walking trails through pine and mixed forest, and is used by local residents for recreation.
- Kyichu Lhakhang #6: setting → practical — The temple is located a short distance from Paro town, making it a standard inclusion on visits to the Paro valley alongside Rinpung Dzong a
- Mongar #6: setting → practical — The Ura-Mongar highway passes through dramatic gorges and over high passes, making the drive itself a notable part of the eastern Bhutan exp
- Mongar Dzong #2: setting → visiting — It is situated on a ridge above Mongar town, offering views over the surrounding forested valleys of eastern Bhutan.
- Mongar Dzong #5: setting → practical — Mongar town itself is a staging point for travel into the remote eastern districts of Bhutan, including Lhuentse and Trashigang.
- Mongar Dzong #6: setting → practical — The road to Mongar crosses high mountain passes, and the town sits at an elevation that gives the area a cooler climate than lower eastern v
- National Handloom Development Corporation, Khaling #7: setting → practical — Khaling sits at a mid-altitude in the hills of eastern Bhutan, and the drive to reach it typically passes through forested mountain terrain 
- National Institute for Zorig Chusum #5: setting → practical — The school is located in Thimphu, Bhutan's capital city, making it easily combined with visits to other cultural sites such as the National 
- Paro Taktsang (Tiger's Nest Monastery) #7: setting → practical — The surrounding forest is composed largely of blue pine and rhododendron, and prayer flags line much of the approach trail.
- Paro Town #1: what_it_is → practical — The town is home to Bhutan's only international airport, making it the country's main entry and exit point for international travellers.
- Samdrup Jongkhar Border Crossing #2: what_it_is → practical — It is one of only a small number of official land entry and exit points into Bhutan open to tourists, making it a significant gateway for ov
- Samdrup Jongkhar Border Crossing #3: setting → practical — The nearest major Indian city on the Assam side is Guwahati, roughly 170 km from the border, making it a common arrival or departure hub for
- Samdrup Jongkhar Border Crossing #6: setting → practical — The road from Samdrup Jongkhar westward into Bhutan's interior traverses mountainous terrain and is the starting point for overland journeys
- Taktsang Monastery #3: setting → practical — The round-trip trek from the base car park passes through blue-pine and rhododendron forest; a midpoint viewpoint café offers a classic face
- Gyatso La #3: setting → visiting — The surrounding landscape is a treeless, high-altitude Himalayan plateau with broad mountain and snow-peak views.
- Old Tingri #3: setting → visiting — On clear days, the surrounding area can provide views toward major Himalayan peaks including Everest, Cho Oyu, Makalu and Lhotse.
- Peiku Tso #2: setting → visiting — Snow-covered Himalayan peaks, including Shishapangma, are visible from the lake in clear conditions.
- Lokpriya Gopinath Bordoloi International Airport #2: what_it_is → practical — It functions as the primary air gateway for travellers entering Northeast India and onward to Bhutan, with road connections to the Bhutanese
- Luang Prabang #5: setting → visiting — Mount Phousi, a hill rising roughly 100 metres above the town centre, offers panoramic views of the Mekong, the Nam Khan, and the surroundin
- Muang Khua #2: what_it_is → practical — It serves as a key transit hub for travellers moving along the Nam Ou River between Nong Khiaw to the south and Phongsali town to the north.
- Nong Khiaw #4: history → visiting — During the Second Indochina War, the region was heavily bombed and locals sheltered in caves in the limestone cliffs; one such cave, Pha Tok
- Nong Khouay #2: what_it_is → practical — Like many villages in this part of Phongsali, Nong Khouay has historically been without connection to the national electricity grid, relying
- Mandalgovi #1: setting → practical — It sits on the northern edge of the Gobi Desert, roughly midway between Ulaanbaatar and the deeper southern Gobi, making it a natural stoppi
- Mandalgovi #2: setting → practical — The town lies approximately 260 km south of Ulaanbaatar along the paved highway that continues toward Dalanzadgad.
- Mörön #1: what_it_is → practical — It serves as the main hub and gateway town for travellers heading to Khövsgöl Lake, located roughly 100 km to the north.
- Sod Camp #2: setting → visiting — It faces the Khoridol Saridag mountain range, which forms a dramatic backdrop on the opposite shore and offers trekking routes.
- Tsaatan Reindeer Herder Settlements #3: setting → practical — Their territory lies deep in the taiga, typically reached from the town of Tsagaannuur, and access requires a multi-hour horse or reindeer r
- Nậm Cắn / Nam Khan Border Crossing #1: setting → practical — On the Lao side the border post sits at around 1,300 metres above sea level in mountainous terrain, making the approach a significant climb 

## Agreed withheld → writer

- Jampa Lhakhang #4: visiting → what_it_is — The complex is an active place of worship and contains religious statues, butter lamps, and murals that have been renovated over the centuri
- Kuensel Phodrang Nature Park #5: visiting → what_it_is — The statue is hollow and houses over one hundred thousand smaller Buddha statues made of bronze and gilded in gold, installed inside the thr
- Kurje Lhakhang #3: visiting → history — A large juniper tree within the complex is traditionally believed to have grown from Guru Rinpoche's walking staff, and is considered sacred
- Kyichu Lhakhang #3: visiting → what_it_is — The original lhakhang enshrines a revered statue of Jowo Shakyamuni, and the newer temple houses a statue of Guru Rinpoche.
- Mongar Dzong #4: visiting → what_it_is — The dzong features traditional Bhutanese whitewashed stone and rammed-earth construction, with characteristic tapering walls, a central towe
- National Handloom Development Corporation, Khaling #4: visiting → what_it_is — The centre produces a range of traditional Bhutanese fabrics, including kishuthara (raw silk patterned cloth), which is characteristic of ea
- National Institute for Zorig Chusum #3: visiting → what_it_is — Students typically enroll for a multi-year programme, spending years mastering a single craft discipline under experienced master craftspeop
- Paro #4: visiting → what_it_is — The National Museum of Bhutan is housed in a former watchtower called Ta Dzong, overlooking Rinpung Dzong, and holds collections of thangkas
- Paro Town #2: visiting → setting — The main street is lined with traditional Bhutanese wooden-fronted shop-houses painted with characteristic decorative motifs, giving the tow
- Paro Town #4: visiting → what_it_is — The National Museum of Bhutan, housed in a former watchtower (Ta Dzong) above Rinpung Dzong, holds collections of thangkas, armour, textiles
- Punakha Dzong #6: visiting → what_it_is — The interior courtyards contain a utse (central tower) and several temples adorned with elaborate woodcarving, paintings, and gilded roofs t
- Trashigang #5: visiting → what_it_is — Eastern Bhutan, and Trashigang in particular, is known for distinctive hand-woven textiles, including the raw-silk Kishuthara fabric produce
- Gyirong #3: practical → setting — The town is near Gyirong Port on the China–Nepal border; the Nepal-side crossing is associated with Rasuwagadhi.
- Mount Kailash #5: visiting → what_it_is — Mount Kailash is regarded as a sacred summit and is not climbed as a conventional mountaineering objective.
- Paryang #2: visiting → setting — Paryang is a road settlement on the China National Highway 219 route through western Tibet.
- Potala Palace #3: visiting → what_it_is — The complex includes the White Palace, the Red Palace, chapels, assembly halls, murals, statues, and tomb stupas of several Dalai Lamas.
- Luang Prabang #3: visiting → what_it_is — The city contains more than 30 Buddhist temples (wats), the most prominent of which is Wat Xieng Thong, dating from the 16th century.
- Baga Gazriin Chuluu #4: practical → what_it_is — The site is protected as a nature reserve within Mongolia's network of specially protected areas.
- Erdene Zuu Monastery #5: visiting → what_it_is — The three surviving temples—dedicated to the three ages of the Buddha (childhood, adulthood, and old age)—now function as museums displaying
- Kharkhorin #4: visiting → what_it_is — The monastery's enclosing wall, approximately 400 metres on each side, is punctuated by 108 white stupas, a number of great significance in 
- Kharkhorin #7: visiting → what_it_is — A large stone tortoise sculpture, one of several originally marking the boundaries of Karakorum, still stands near Erdene Zuu and is a well-
- Ulaanbaatar #3: practical → setting — Ulaanbaatar is the coldest national capital in the world by average annual temperature, with winters regularly dropping below −20 °C.

## Applied (14/10/2026)
- 54/54 edits on 37 cards via `PATCH /admin/content-quality/place-cards/{id}/facts` (PR #716), 37 audit rows `place_card.facts_edited`. Tsaatan: writer facts 5 of 9, access fact out of the seed. AA-774 Done.
- AA-808 (PR #717): drafter rule + post-check. Trial: 5 new cards, 25 facts, 0 traveller clauses, $0.00998 (`aa808_trial.json`, `aa808_newcards.json`). 2 trial cards duplicated existing cards and were merged (Kuang Si, Zorig Chusum) → AA-809.

## Duplicate clusters today (`/place-cards/duplicates`, read-only, `aa809_duplicate_clusters.json`) — not merged, Nghiệp decides
- Town vs landmark in town (NOT duplicates, keep): Mongar / Mongar Dzong; Paro / Paro Taktsang; Punakha / Punakha Dzong; Kharkhorin / Kharkhorin Museum; Rongbuk Monastery vs Rongbuk Valley.
- Likely true duplicates: Paro / Paro Town; Zhongba / Zhongba County; Gyirong / Gyirong County; Lake Manasarovar / "eastern shore"; Rongbuk / Rongbuk Valley.
