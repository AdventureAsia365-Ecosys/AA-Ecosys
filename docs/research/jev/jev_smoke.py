"""Jev smoke test for AA-634 — 4 scenarios mirroring real AA-Ecosys call sites.

Run: TYPESAFE_API_KEY=$(cat jev.key) venv/bin/python jev_smoke.py
"""
import json, time
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

GOOD = ("Day 3 climbs from Paro to Taktsang Monastery, a 900m ascent through blue pine to the "
        "cliff ledge where Guru Rinpoche meditated. Your guide times the walk to reach the "
        "prayer-wheel viewpoint before the tour buses. Design This Journey with our Bhutan team.")
BAD = ("Experience the best of this incredible destination on an unforgettable journey. "
       "Epic adventures and amazing memories await. Book now for cheap deals!")
CTA = "Design This Journey"

def f9_questions(cta):  # T10 F9 (quality_gates.gate_brand_voice) as Nouls
    return {
        "brand_fit": Noul(instructions="Does the piece fit a discreet, understated executive-adventure "
                          "brand (senior professionals, no hype, no discount language)?"),
        "cta_clear": Noul(instructions=f"Is the call to action '{cta}' present and a single unambiguous action?"),
        "human_read": Noul(instructions="Does the piece read as written by a knowledgeable human, not templated AI copy?"),
        "generic_ai": Noul(instructions="Does it contain templated superlatives with no concrete detail, "
                           "swappable onto any destination unchanged?"),
    }

ATOM = "Day 3: Hike up to Taktsang (Tiger's Nest) Monastery, perched 900m above the Paro valley."
ATOM_Q = {  # A3 atomize (atom_extraction.py) enum/int fields
    "activity_type": Choice(instructions="Primary activity type of this itinerary atom",
        criteria={k: None for k in ["trek", "bike", "food", "culture", "stay", "transit", "other"]}),
    "visual_potential": Score(instructions="Photo/video potential",
        criteria=["low", "medium", "strong"]),
}
TP_Q = {  # TripPlanner extraction/prompts.py closed taxonomy
    "activity": Choice(instructions="Activity category", criteria={k: None for k in [
        "trekking", "cultural_heritage", "wildlife_nature", "water_activities", "culinary",
        "wellness_relaxation", "adventure_sport", "local_immersion"]}),
    "intensity": Choice(instructions="Physical intensity", criteria={k: None for k in
        ["leisurely", "moderate", "active", "strenuous"]}),
    "duration": Choice(instructions="Duration", criteria={k: None for k in
        ["half_day", "full_day", "overnight", "multi_night"]}),
}

def run(client, name, state, qs):
    t = time.perf_counter()
    r = client.system_one(state=state, questions=qs)
    ms = (time.perf_counter() - t) * 1000
    out = {}
    for k, a in r.nouls.items(): out[k] = round(a.noul, 3)
    for k, a in r.choices.items(): out[k] = {"pick": a.choice, "p": {x: round(y, 3) for x, y in a.probabilities.items()}}
    for k, a in r.scores.items(): out[k] = {"expected": round(a.score, 3) if hasattr(a, "score") else None,
                                          "p": {x: round(y, 3) for x, y in a.probabilities.items()}}
    print(f"\n## {name}  ({ms:.0f} ms, model={r.model}, usage={r.usage.input_tokens}in/{r.usage.output_tokens}out)")
    print(json.dumps(out, indent=1))

with TypeSafeClient(timeout=30) as c:
    print("models:", [(m.name, m.release_date) for m in c.models.list().models])
    run(c, "F9 good piece", GOOD, f9_questions(CTA))
    run(c, "F9 bad piece", BAD, f9_questions(CTA))
    run(c, "A3 atom classify", ATOM, ATOM_Q)
    run(c, "TripPlanner component", ATOM, TP_Q)
