"""Realistic large content bodies for the AA-806 WAF pre-flip test.

Built from real Dev content (one raw tour + one tenant version) plus the markup an editor produces:
<p>, <ul>/<li>, <a href> with relative ../ links, quotes, <em>/<strong>, accented place names.
"""
import html
import json

RICH_INTRO = (
    '<p>From the lantern-lit lanes of <strong>Hội An</strong> to the misty limestone of <em>Hạ Long Bay</em>, '
    'this route was built for travellers who&#39;d rather ride than ride past. Your guide &mdash; '
    '&ldquo;Anh Tuấn&rdquo;, as everyone calls him &mdash; grew up in <strong>Huế</strong> and knows every '
    'back road between the Perfume River and Đà Nẵng.</p>\n'
    '<p>See our <a href="../destinations/vietnam/hue">Huế guide</a>, the '
    '<a href="../../travel-info/visas#vietnam" title="Visa information">visa notes</a> and the '
    '<a href="https://www.adventure.asia/tours/vietnam/ride-the-trail?ref=brochure&amp;utm_source=portal">full '
    'brochure</a> before you book. Questions? <a href="mailto:hello@example.com">Write to us</a>.</p>\n'
    '<ul>\n'
    '  <li><strong>Day 1&ndash;2:</strong> Hà Nội street food &amp; the night train to Huế</li>\n'
    '  <li><strong>Day 3:</strong> Imperial Citadel, Tự Đức &amp; Khải Định mausoleums by bike</li>\n'
    '  <li><strong>Day 5:</strong> Hải Vân Pass &mdash; &ldquo;the most beautiful ride in Vietnam&rdquo;</li>\n'
    '  <li><em>Optional:</em> a cooking class in Hội An (phở, bánh xèo, cao lầu) &ndash; $45 pp</li>\n'
    '</ul>\n'
    '<p><img src="../images/tours/ride-the-trail/hai-van-pass.jpg" alt="Cyclists on the Hải Vân Pass" '
    'width="1200" height="800" loading="lazy"></p>\n'
    '<blockquote><p>&ldquo;Best two weeks we&#39;ve spent anywhere &mdash; café sữa đá every morning!&rdquo; '
    '&mdash; <em>Sarah &amp; José, São Paulo</em></p></blockquote>\n'
)

RICH_MD_INTRO = (
    "## Why Huế rewards a slow day\n\n"
    "From the lantern-lit lanes of **Hội An** to the misty limestone of _Hạ Long Bay_, this route was built "
    "for travellers who'd rather ride than ride past. Your guide, \"Anh Tuấn\", grew up in **Huế** and knows "
    "every back road between the Perfume River and Đà Nẵng.\n\n"
    "- **Day 1–2:** Hà Nội street food & the night train to Huế\n"
    "- **Day 3:** Imperial Citadel, Tự Đức & Khải Định mausoleums by bike\n"
    "- _Optional:_ a cooking class in Hội An (phở, bánh xèo, cao lầu) – $45 pp\n\n"
    "Read the [Huế guide](../destinations/vietnam/hue), the [visa notes](../../travel-info/visas#vietnam) and "
    "the [full brochure](https://www.adventure.asia/tours/vietnam/ride-the-trail?ref=brochure&utm_source=portal).\n\n"
    "![Cyclists on the Hải Vân Pass](../images/tours/ride-the-trail/hai-van-pass.jpg \"Hải Vân Pass\")\n\n"
    "> \"Best two weeks we've spent anywhere — café sữa đá every morning!\" — *Sarah & José, São Paulo*\n\n"
)


def itinerary_to_html(text: str) -> str:
    out = []
    for block in text.split("\n"):
        block = block.strip()
        if not block:
            continue
        if block.lower().startswith("day "):
            out.append(f"<h3>{html.escape(block)}</h3>")
        else:
            out.append(f"<p>{html.escape(block, quote=True)}</p>")
    return "\n".join(out)


def itinerary_to_md(text: str) -> str:
    out = []
    for block in text.split("\n"):
        block = block.strip()
        if not block:
            continue
        out.append(f"### {block}" if block.lower().startswith("day ") else block)
    return "\n\n".join(out)


def plain_filler(text: str, min_bytes: int) -> str:
    """Plain prose only: no markup, no slashes/dots-before-slash, no quotes. Control for SizeRestrictions_BODY."""
    clean = "".join(ch for ch in text if ch.isalnum() or ch in " \n,-").replace("  ", " ")
    s = clean
    while len(s.encode()) < min_bytes:
        s += "\n" + clean
    return s


def build(raw: dict, version_content: dict) -> dict:
    itin = raw["src_itineraries"]
    rich_html = RICH_INTRO + itinerary_to_html(itin)
    rich_md = RICH_MD_INTRO + itinerary_to_md(itin)
    # tenant version edit: the real rewritten_content dict, with the editor's HTML in summary/itinerary
    ver_rich = dict(version_content)
    ver_rich["summary"] = RICH_INTRO + "<p>" + html.escape(str(version_content.get("summary", ""))) + "</p>"
    return {
        # admin raw tour PATCH: the real raw fields re-sent unchanged (plain text, 8.9 KB itinerary)
        "admin_raw_unchanged": {
            "src_itineraries": raw["src_itineraries"],
            "src_highlights": raw["src_highlights"],
            "inclusions": raw["inclusions"],
            "exclusions": raw["exclusions"],
        },
        # admin raw PATCH with editor-style HTML in the description
        "admin_raw_html": {"src_description": rich_html, "inclusions": raw["inclusions"]},
        # admin generated-content PATCH (Master Content edit) with HTML description + itinerary
        "admin_generated_html": {"aa_description": rich_html, "aa_itineraries": itinerary_to_html(itin)},
        # tenant inline edit of a tour version: real rewritten_content, unchanged
        "tenant_version_unchanged": {"action": "edit", "edited_content": version_content, "edited_by": "tenant"},
        # tenant inline edit with HTML in the summary
        "tenant_version_html": {"action": "edit", "edited_content": ver_rich, "edited_by": "tenant"},
        # tenant My Content hand edit of a blog piece (markdown)
        "tenant_piece_markdown": {"content_text": rich_md},
        # controls
        "control_small_html": {"content_text": RICH_INTRO},
        "control_large_plain": {"content_text": plain_filler(itin, 12000)},
        # Booking staff writes (validated limits: case notes <= 10,000; contract terms 2,000 / 5,000 / 5,000)
        "booking_case_notes": {"notes": (RICH_MD_INTRO + itinerary_to_md(itin))[:9800]},
        "booking_contract_terms": {
            "payment_terms": (
                "30% deposit within 7 days of confirmation; balance 30 days before arrival. Payment by bank "
                "transfer (VND or USD) to the account on the invoice; card payments +3%. Late payment: the "
                "supplier may release rooms after 48 hours' written notice (e-mail is fine). "
            ) * 6,
            "cancellation_policy": (RICH_MD_INTRO + "Cancellation: 60+ days 10%; 30–59 days 25%; 15–29 days 50%; "
                                    "0–14 days or no-show 100%. Force majeure per clause 9.\n\n" + itinerary_to_md(itin))[:4990],
            "notes": (RICH_INTRO + itinerary_to_html(itin))[:4990],
        },
    }


if __name__ == "__main__":
    import sys
    j = json.load(open(sys.argv[1]))
    b = build(j["raw"], {"name": "x", "summary": "y"})
    for k, v in b.items():
        print(k, len(json.dumps(v, ensure_ascii=False).encode()))
