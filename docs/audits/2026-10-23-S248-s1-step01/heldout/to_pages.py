#!/usr/bin/env python3
"""Turn the held-out fetch (fetch_heldout.py output, .json.gz) into the page list fixture_report.py --pages reads.

  python3 to_pages.py <fetched.json.gz> pages.json
"""
import gzip
import json
import sys

rows = json.loads(gzip.decompress(open(sys.argv[1], "rb").read()))
pages = []
for r in rows["rows"]:
    hl = r["src_highlights"]
    pages.append({
        "sample_id": r["tour_id"],
        "tour": {"name": r["src_name"], "subtitle": r["src_subtitle"], "summary": r["src_summary"],
                 "description": r["src_description"], "highlights": json.loads(hl) if isinstance(hl, str) else hl,
                 "itineraries": r["src_itineraries"], "country": r["country"], "duration": r["duration"],
                 "price": r["price_raw"], "inclusions": r["inclusions"], "exclusions": r["exclusions"]},
        "output": {"name": r["aa_name"], "subtitle": r["aa_subtitle"], "summary": r["aa_summary"],
                   "description": r["aa_description"],
                   "highlights": json.loads(r["aa_highlights"]) if isinstance(r["aa_highlights"], str)
                   else r["aa_highlights"], "itineraries": r["aa_itineraries"], "seo_title": r["seo_title"],
                   "seo_meta": r["seo_meta"]},
        "label": None,
    })
json.dump(pages, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
print(len(pages), "pages; catalog stats:", rows["stats"])
