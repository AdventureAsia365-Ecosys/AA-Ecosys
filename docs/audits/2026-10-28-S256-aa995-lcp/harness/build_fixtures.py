"""AA-995 S256: fixtures for a local production build of TripPlanner without the browse API key.

Built from public production answers only (the /api/browse BFF list + by-country, and the rendered HTML/JSON-LD of
three pages), so the local build shows the same photos, tours and places as production for the measured pages.
The same fixtures serve the before and the after build: the comparison isolates the frontend change.
"""
import json
import re
import collections
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "raw"
OUT = Path(__file__).resolve().parent / "fixtures"
OUT.mkdir(exist_ok=True)
CIS = "https://api-cis.lumiguides.it.com/content/photos/"

cards = json.load(open(RAW / "cards.json"))
featured = json.load(open(RAW / "featured.json"))["tours"]
by_slug = {c["slug"]: c for c in cards}


def ld(html, typ):
    for m in re.finditer(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        x = json.loads(m.group(1))
        if x.get("@type") == typ:
            return x
    return None


def photo(pid, label):
    return {"photo_id": pid, "place_label": label, "width": 1600, "height": 900,
            "url": f"{CIS}{pid}?size=large", "url_small": f"{CIS}{pid}?size=small"}


# --- countries (CountrySummary) -------------------------------------------------------------------------------
groups = collections.OrderedDict()
for c in cards:
    groups.setdefault(c["country_slug"], []).append(c)
countries = []
for slug, cs in groups.items():
    days = [c["duration_days"] for c in cs if c["duration_days"]]
    cov = next((c for c in cs if c["cover_url"] and c["cover_source"] == "tour"), None)
    countries.append({"country": cs[0]["country"], "slug": slug, "tour_count": len(cs),
                      "min_days": min(days) if days else None, "max_days": max(days) if days else None,
                      "cover_url": cov["cover_url"] if cov else None,
                      "cover_url_small": cov["cover_url_small"] if cov else None, "updated_at": None})
countries.sort(key=lambda x: -x["tour_count"])
json.dump({"countries": countries}, open(OUT / "destinations.json", "w"))

# --- destination pages ----------------------------------------------------------------------------------------
bhutan_html = open(RAW / "bhutan.html").read()
bh_ld = ld(bhutan_html, "TouristDestination")


def destination(slug, cover_url, places_file):
    cs = groups[slug]
    days = [c["duration_days"] for c in cs if c["duration_days"]]
    places = []
    if places_file and (RAW / places_file).exists():
        for p in json.load(open(RAW / places_file))["destinations"][:24]:
            places.append({"destination_id": p["id"], "name": p["name"], "lat": p["lat"], "lng": p["lng"],
                           "tour_count": p.get("component_count", 1), "activity_types": [], "cover_url": None,
                           "located_by": p.get("located_by"), "precision": p.get("precision")})
    return {"country": cs[0]["country"], "slug": slug, "tour_count": len(cs), "min_days": min(days) if days else None,
            "max_days": max(days) if days else None, "top_activities": ["culture", "trek", "transit"],
            "cover_url": cover_url, "tours": cs[:12], "places": places, "photos": []}


dest = {"bhutan": destination("bhutan", bh_ld["image"], "bycountry-bhutan.json")}
for slug in groups:
    if slug not in dest:
        cov = next((c["cover_url"] for c in groups[slug] if c["cover_url"]), None)
        dest[slug] = destination(slug, cov, None)
json.dump(dest, open(OUT / "destination_pages.json", "w"))

# --- tour detail (the measured Sri Lanka tour; others get a card-based detail) ----------------------------------
tour_html = open(RAW / "tour.html").read()
trip = ld(tour_html, "TouristTrip")
SLUG = "sri-lanka-cultural-tour-kandy-dambulla-and-sigiriya-3-days-sri-lanka-28e22489"
card = by_slug[SLUG]
ids, labels = [], {}
for m in re.finditer(r'content/photos/([0-9a-f-]{36})\?size=(?:small|large)"(?: [^>]*?alt="([^"]*)")?', tour_html):
    pid, alt = m.group(1), m.group(2)
    if pid not in labels or (alt and not labels[pid]):
        labels[pid] = alt
    if pid not in ids:
        ids.append(pid)
for u in trip["image"]:
    pid = u.split("/")[-1].split("?")[0]
    if pid not in ids:
        ids.append(pid)
first = trip["image"][0].split("/")[-1].split("?")[0]
ids.remove(first)
ids.insert(0, first)
labels[first] = labels.get(first) or "Colombo"
sl_places = json.load(open(RAW / "bycountry-srilanka.json"))["destinations"]
wanted = ["Pinnawala", "Kandy", "Tooth", "Dambulla", "Sigiriya", "Colombo"]
places = []
for i, w in enumerate(wanted):
    p = next((x for x in sl_places if w.lower() in (x["name"] or "").lower()), None)
    if p:
        places.append({"day_number": 1 + min(i // 2, 2), "position": i, "place_name": p["name"], "place_display_name": p["name"],
                       "destination_id": p["id"], "destination_name": p["name"], "lat": p["lat"], "lng": p["lng"],
                       "activity_types": ["culture"], "located_by": p.get("located_by"), "precision": p.get("precision") or "point"})
days = []
for e in trip["itinerary"]["itemListElement"]:
    n, title = re.match(r"Day (\d+): (.*)", e["name"]).groups()
    days.append({"day_number": int(n), "title": title, "body": e.get("description", ""),
                 "places": [p["place_name"] for p in places if p["day_number"] == int(n)]})


def detail(c, photos, days, places, extra=None):
    d = {k: c.get(k) for k in ["source_id", "tour_id", "slug", "title", "subtitle", "summary", "highlights", "country",
                                "country_slug", "duration_raw", "duration_days", "best_time_to_go", "lifecycle_stage",
                                "cover_url", "cover_source", "cover_place", "published_at", "updated_at"]}
    d.update({"description": c.get("summary"), "activities": ["culture", "transit"],
              "inclusions": "Private chauffeur guide\nAccommodation as listed\nEntrance fees as listed",
              "exclusions": "International flights\nVisa\nTips", "group_size": None, "itinerary_text": None,
              "photo_count": len(photos), "days": days, "places": places,
              "photos": [dict(p, position=i) for i, p in enumerate(photos)]})
    d.update(extra or {})
    return d


tours = {SLUG: detail(card, [photo(p, labels.get(p) or None) for p in ids], days, places)}
json.dump(tours, open(OUT / "tours.json", "w"))
json.dump(cards, open(OUT / "cards.json", "w"))
json.dump({"tours": [{"slug": c["slug"], "updated_at": None} for c in cards],
           "countries": [{"slug": c["slug"], "country": c["country"], "updated_at": None} for c in countries]},
          open(OUT / "sitemap.json", "w"))
json.dump({"featured": [c["slug"] for c in featured]}, open(OUT / "featured.json", "w"))
print("countries", len(countries), "tour photos", len(ids), "places", len(places), "days", len(days))
