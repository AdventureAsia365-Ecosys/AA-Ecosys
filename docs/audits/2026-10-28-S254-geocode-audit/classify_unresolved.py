#!/usr/bin/env python3
"""S254 geocode audit: classify unresolved geo.place_name rows (status pending / unknown) by CAUSE.

Stdlib only, read-only, no network. Input: place_names.json (same dir). Output: unresolved_classified.json
and a printed summary. Rules are heuristics plus hand overrides written after reading every name once.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = [r for r in json.load(open(HERE / "place_names.json")) if r["status"] in ("pending", "unknown")]

# --- hand overrides (display_name, country) -> cause --------------------------------------------------
CROSS_COUNTRY = {  # real place, but in another country than the tour's stored country
    ("Irkutsk", "Mongolia"), ("Lake Baikal", "Mongolia"), ("Lake Baikal shores", "Mongolia"),
    ("Listvyanka", "Mongolia"), ("Olkhon Island", "Mongolia"), ("Karl Marx Street", "Mongolia"),
    ("Street Karl Marx", "Mongolia"), ("Kazankaya Church", "Mongolia"), ("Kazankaya Tserkov", "Mongolia"),
    ("Shver Kirova", "Mongolia"), ("Shver Kirova Cathedral", "Mongolia"), ("Central Market (Tsentralny Rynok)", "Mongolia"),
    ("Tsentralny Rynok", "Mongolia"), ("Talsy Museum", "Mongolia"), ("130 Kvartal", "Mongolia"),
    ("130 Kvartal district", "Mongolia"), ("3 Cathedral", "Mongolia"), ("Lover's Bridge", "Mongolia"),
    ("Cherskogo viewpoint", "Mongolia"), ("Eco Museum", "Mongolia"), ("HKG", "Mongolia"), ("Hong Kong", "Mongolia"),
    ("Hamulin Temple", "Mongolia"), ("bell pavilion of Hamulin Temple", "Mongolia"),
    ("white double Aobao of Hamulin Temple", "Mongolia"),
    ("Samteling Palace", "Nepal"), ("the Bhutan post office", "Nepal"), ("The longest suspension bridge in Bhutan", "Nepal"),
    ("Khumbum Stupa", "Nepal"), ("Zhaxi Temple", "Nepal"), ("Nazin Kang Sang glacier", "Nepal"), ("Horchu", "Nepal"),
    ("Namring", "Nepal"), ("Kyirung Thil", "Nepal"), ("Dolma La village", "Nepal"), ("Nandi", "Nepal"),
    ("Nandi Parvat", "Nepal"), ("Atmalingam", "Nepal"), ("Chui Gumba", "Nepal"), ("Chyo Gumba", "Nepal"),
    ("Buddha's Footprints", "Nepal"), ("Lham-chu Khir River", "Nepal"), ("Parvati-stal", "Nepal"),
    ("Parvati-sthal", "Nepal"), ("Shiva-stal", "Nepal"), ("Shiva-sthal", "Nepal"), ("Yamasthal", "Nepal"),
    ("Zuthal Puk", "Nepal"), ("Thada", "Nepal"), ("New Dongba", "Nepal"), ("the temple of Maitreya", "Nepal"),
    ("A Tibetan family", "Nepal"), ("Dafey Bhir Pass", "Nepal"), ("Kalijhora", "Nepal"), ("Kharka Dara", "Nepal"),
    ("Thulo Dhap", "Nepal"), ("Sleeping Buddha formation", "Nepal"), ("Khanda Sanglo pass and Kuber Kund", "Nepal"),
    ("Khando Sangam La", "Nepal"), ("Tarboche to Drirapuk", "Nepal"), ("Tarboche valley to Dirapuk", "Nepal"),
    ("Yamadwar to Dirapuk", "Nepal"), ("Dirapuk to Charan Sparsa", "Nepal"), ("Dolma La pass to the village of Juthulpuk", "Nepal"),
    ("Jarok Donkhang toward Shiva-tsal", "Nepal"), ("monasteries holding footprints of Guru Rinpoche", "Nepal"),
    ("Milarepa Cave", "China"), ("the Fine Arts Museum", "China"), ("the Museum of Musical Instruments", "China"),
    ("Bhutan Post Office", "Bhutan"),
    ("the halfway point to Mandara Hut", "India"), ("Last Water Point", "India"), ("moorland to Kibo Hut", "India"),
    ("rainforest to Mweka Park Gate", "India"), ("Nepal and Sikkim", "India"),
    ("karaoke bar in Kyoto", "South Korea"), ("Sake Street", "South Korea"),
    ("Shaxi to Eryuan Hot Springs", "Laos"), ("Naxi and Yi villages and farmland", "Laos"), ("Cambodian farmland", "Laos"),
    ("O'Svay community", "Laos"), ("Loeli", "Laos"), ("Dong Giao", "Laos"), ("mountain scenery into Vietnamese highlands", "Laos"),
    ("Wat Preah Kral", "Thailand"), ("Srah Damrey", "Thailand"), ("rural Laos", "Thailand"), ("Pak Mong to Nong Khiaw", "Thailand"),
    ("a small Lao village along the river", "Thailand"), ("a resort on the banks of the Kat River", "Thailand"),
    ("Xakhe", "Vietnam"), ("Xepon to Tad Lo via Saravane", "Vietnam"), ("Don Chan", "Vietnam"),
    ("Residential island, Maldives", "Sri Lanka"), ("residential island, Maldives", "Sri Lanka"),
    ("the North Korean side", "China"),
}
WELL_KNOWN = {  # notable, well-documented places a strong model / any geocoder knows
    "Summer Palace", "Grand Palace", "Norbulingka", "Tingri", "Olkhon Island", "Irkutsk Central Market",
    "Kazan Cathedral, Irkutsk", "Kirov Square", "Taltsy Architectural and Ethnographic Museum", "Baikal Museum",
    "Listvyanka Market", "Lovers’ Bridge", "130th Quarter", "Karl Marx Street", "Grand Canal", "Santang Street",
    "Mount Everest’s North Face", "Milarepa’s Cave (Nyalam)", "Mount Fortress", "Shizongshan Grottoes",
    "Haowang Tower", "Wang Jing Tower", "Wang Jing Tower (Watching Beijing Tower)", "Zunsheng Tower",
    "Bunker de Lumières", "Bunker des Lumières", "Bunker des Lumières art exhibition", "Dole Plantation",
    "Mie Castle", "Wat Tham Chaeng", "Tham Pha Cave", "Phatok Cave", "Kuang Song Waterfall",
    "Gatimaan Express", "Wat Phra That Doi Mae Ya Mon", "Wat Tham Pakpiang", "Mian Yue Rail Line", "Mianyue Line",
    "Mian Yue Line trailhead", "Jalnarayan Temple", "Jalnarayana", "Gujesori temple", "Jwala Mai Temple",
    "Mharme Lha Khang Gompa", "Mhame Lha Khang Gompa", "Everest National Park permit checking counter",
    "Chhoe Chhoe Tse Lhakhang", "Tango/Cheri Bebena", "Thada Goemba", "Jhunjhunwala Haveli", "Khandelwal Haveli",
    "Panchala Blackbuck Conservation Reserve", "Gair Ka Mandir", "Orchha Cooking School", "Echo Point Hill",
    "Muththumariamman Hindu Temple", "Muthu Mariamman Hindu Temple", "Taylors Hill", "Kasurina Beach",
    "Neelagiri Buddha Statue", "Lion's Head cave", "Volcanology Center", "Tjuvecekadan", "Turtle Island",
    "Hapjeong Junibino", "Midas's Hand", "Patriots & Peace Memorial", "Andra Fort", "ruins of Andra Fort",
    "Bang-i-Das Waterfall", "waterfall at Bang-i-Das", "Thoqsi Khar Mosque", "Godwin-Austen Glacier to Concordia",
    "Phi Phi Island", "Phi Phi Islands", "Krabi Four Islands", "Hong Island Viewpoint", "Taiwan's longest suspension bridge",
}
VARIANT = {  # misspelling / transliteration variant of a real name (often a sibling row is a near-duplicate)
    "Ranthan", "Ranthon", "Chimmin Rock", "Chimming Rock", "Anupig Falls", "Anuplig Falls", "Turungan Cave",
    "Torongan Cave", "Bonavista Reef", "Bonevista coral reef", "Burundi River", "Burungdi stream", "Kuldighar",
    "Khuldigar", "Zamphute", "Zapute", "Lungsumba Gompa", "Lungsumga Gompa", "Tserim Kang", "Tsherim Kang",
    "Ho Tay Pidok Library", "Hor Tay Phidok Library", "Tham Theung", "Tham Thueng", "Had Pha Daeng", "Hat Pha Daeng",
    "Ban Huai Pu Loei", "Ban Huay Pu Loei", "Ban Pong Kwao", "Ban Pong Kwaw", "Bann Pa Kao Lam", "Changbhंग",
    "the Ken ram Palm Oil Milling Plant", "Kenram Palm Oil Milling Plant", "Kappl", "Batac tribe", "Monobo tribe",
    "Sojoryung", "Sojoryung Mountain", "Sojoryung pass", "Duiker viewpoints", "Dormala", "Bardumal Campsite",
    "Burdumal campsites", "Chorichi Biaho", "Choricho Biaho", "Laini Odar", "Lahini Odar", "Simkota Tsho",
    "Semkotha Lake", "Janetsho Lake", "Jigmelangtsho lake", "Phume La pass", "Doupchu La Pass", "Ban Houy Mo",
    "Ban Houay Mo", "Phatang", "Pathang", "Paangarh Lake", "Pangarh Lake", "Natures Park in Malatgao",
    "Malatgao Nature Park", "Camp Camantile", "Camp Camantiles", "Panchala Black buck reserve", "Thakur Kuwan",
    "Jumlay Pokhari", "Raele", "Barrio Raele", "Mt Mahalangur", "Matkyu", "Motkyu to Jhinu Danda", "Daaulu",
    "Bhonte La", "Thombu La pass", "Prek Chu", "Wonbuchun village", "Kiu Katcham", "Big Pha Ngern", "Tad E-Tu",
    "Tad E-Tu Waterfall", "Kazankaya Church", "Kazankaya Tserkov", "Shver Kirova", "Talsy Museum", "Dok Gogma",
    "Dok Yogma", "Mount Katsuu", "Katsuu Mountain", "Mt. Katsu", "Kuang Yui Waterfall", "Ody Thach", "Gang Chen Ta (Great Tiger Mountain)",
    "Kang Che Da", "Tsekha", "Tsekha (Lahe)", "Ghorosingha", "Laha Village", "Ban Nayang", "Ban Nayang village",
    "Kavang", "Ban Kavang", "Ban Kavang village", "the small village of Kavang", "Long Lao Mai", "Ban Long Lao Mai",
}
NON_PLACE_WORDS = re.compile(
    r"\b(class|cuisine|hot pot|dinner|show|performance|culture|family|families|monks|onboard|on board|cruise|express|"
    r"compartments?|statues|architecture|camping|karaoke|noraebang|bar scene|coffee|cultivation|kithul tree|"
    r"film locations|haenyeo|people|peoples|tribe|sabani|trip end|en route|the way back|railway$|tents?$|"
    r"a sakura tree|an ngo|ngo$|beer brewery|artisan|instagram swing|toilets|ghost|homes$|kan toke|"
    r"luxury tents|houseboat|home-?stay|accommodation|bungalow$|village home|naadam|lassi|maggi|mithaiwala|"
    r"tie dye|post office|sharing seeds|patcharee|reggae bar)\b", re.I)
REGION_WORDS = re.compile(
    r"(himalaya|\branges?\b|karakoram|\bsea\b|ocean|strait|gulf coast|plains|countryside|rural |landscape|"
    r"highlands|hills$|^north korea$|^lao$|^laos and|mountain area|coastline|east coast|truong son|world heritage|"
    r"\bunesco zone|phu chi fa|western ghats|greater himalaya|eastern karakoram|the mainland|satoyama countryside|"
    r"li minority country|hmong hill country|yanbaru national park$|catchment|shola forests|dry-zone forest|"
    r"rainforests?$|sal forests|spice plantations|tea gardens|waterfalls$)", re.I)
GENERIC_HEAD = re.compile(
    r"^(the |a |an |some |several |many |more |local |one of |nearby |small |typical |traditional |scattered |"
    r"another |unique |remote |two |three |17 |ancient |old |hindu |buddhist |sacred )", re.I)
GENERIC_KIND = re.compile(
    r"^(hotel|campsite|base ?camp|basecamp|camp [12]|camp 1 to base camp|trailhead|roadhead|international airport|"
    r"airport( or (pier|railway station))?|office|departure office|office starting point|meeting point|cabin|"
    r"city palace|old city|old quarter|city wall|bird sanctuary|information center|observation deck|"
    r"socialization area|heritage village|beach destination|national trail|self-guided trail|main hiking trail|"
    r"forest camp|forest edge|hanok|homes|riverbank|the riverbank|restaurants in town|seated restaurant|"
    r"nearby restaurant|rural farm (lodge|stay)|tea planter's bungalow|safari campsite|mountain accommodation|"
    r"jain temple|mahadev temple|nandi temple|daoist temple|chinese shrine|hindu temples|tibetan monastery|"
    r"buddhist monasteries|tibetan villages|local villages|nearby villages|rural villages|hmong villages?|"
    r"khmu villages?|khammu villages|naxi village|miao village|lahu village|mon tribal village|"
    r"karen village|h'mong village|wat pa|utaki|old gompa|community kitchen|art gallery|radar|saddle point|"
    r"san jose|south road|coral island|crystal cave|sierra cave|forest camp|elephant rock|jungle beach|"
    r"bird's island|dragon cave|rock point|rock viewpoint|cool pool|oasis pool|green jungle park|"
    r"bear sanctuary|ecology museum|wildlife conservation centre|another stream|some streams|streams and small waterfalls|"
    r"the cliff|the arc|dream|river bicycle|the loft|lama's caves|sod camp|governor's mansion|governor's island|"
    r"century island|honeymoon temple|sun lake|jupiter gorge|golden tower monastery|monkey trail|the hideaway|"
    r"the other corner|the post office|international airport)$", re.I)
ROUTE = re.compile(r"\S\s+to\s+\S|–|—|->| route\b|\bsection\b|\bsegment\b|\btoward\b|\btowards\b|on the way|"
                   r"\binto\b|\bvia\b", re.I)
COMPOUND = re.compile(r"\s(and|or|&)\s|\s?/\s?", re.I)
ANNOTATED = re.compile(r"\(\s*\d[\d,]*\s*m\b|\d{3,4}\s?m\)|\(.*\)|\d{3,4}\s?m\b", re.I)


def cause(r):
    err = r["last_error"] or ""
    name = r["display_name"].strip()
    key = (name, r["country"])
    if err.startswith("unknown_country"):
        return "country_text_unparsed"
    if err in ("outside_country_polygon", "outside_country_bbox", "malformed_answer"):
        if REGION_WORDS.search(name) or re.search(r"sea|ocean|strait|\blao$", name, re.I):
            return "region_or_water_body"
        return "guard_reject_coast_island_border"
    if r["locality"]:
        return "generic_name_wrong_locality"
    if key in CROSS_COUNTRY:
        return "cross_country_tour"
    if name in WELL_KNOWN:
        return "well_known_model_miss"
    if name in VARIANT:
        return "spelling_variant"
    if ROUTE.search(name) and not re.search(r"Yali La Pass \(4820 m\)$", name):
        return "route_segment"
    if COMPOUND.search(name) and not GENERIC_HEAD.search(name):
        return "compound_name"
    if ANNOTATED.search(name):
        return "annotated_name"
    if NON_PLACE_WORDS.search(name):
        return "not_a_place"
    if REGION_WORDS.search(name):
        return "region_or_water_body"
    if GENERIC_KIND.search(name):
        return "generic_kind_name"
    if GENERIC_HEAD.search(name) or name[:1].islower():
        return "descriptive_phrase"
    return "obscure_real_place"


out = defaultdict(list)
for r in rows:
    out[cause(r)].append(r)

summary = {k: {"count": len(v), "pending": sum(1 for x in v if x["status"] == "pending"),
               "unknown": sum(1 for x in v if x["status"] == "unknown"),
               "names": [f'{x["display_name"]} [{x["country"]}]' for x in v]} for k, v in out.items()}
json.dump(summary, open(HERE / "unresolved_classified.json", "w"), ensure_ascii=False, indent=1)
tot = 0
for k, v in sorted(summary.items(), key=lambda kv: -kv[1]["count"]):
    tot += v["count"]
    print(f'{v["count"]:5d}  p={v["pending"]:4d} u={v["unknown"]:3d}  {k}')
print(tot)
