"""AA-819 S239: F19 live evidence on the deployed image (no LLM, no DB write). Planted LinkedIn text with a
fake review, a customer speaking in the first person and an independence claim, plus a CTA that mentions
reviews (tenant-owned, exempt). Runs the real gate (quality_gates.gate_authenticity) and the real
fail-closed cut (service._enforce_authenticity) from the live container code."""
import sys, json, os, subprocess
sys.path.insert(0, "/app")
from services.acp_content_writing import quality_gates as qg, service as svc
CTA = "Read the five-star reviews our travellers left, then talk to an Atlas & Hearth travel designer"
TEXT = """Paro Taktsang clings to a granite cliff 900 metres above the valley floor.

"This was the best trip of my life, the guides were incredible," says Sarah from London, who travelled with us last spring.

I booked this tour with my husband and we were blown away by every single day.

As an independent travel reviewer with no ties to any operator, I can say this itinerary is the finest in Bhutan.

The climb takes most of a morning, through blue pine and prayer flags, to the monastery's gate.

""" + CTA
gate = qg.gate_authenticity(TEXT, CTA)
ledger = [gate]
status0, held0, flags0 = svc._hold_or_ship(ledger, [])
out_text, ledger2, flags2, status2, held2, entry = svc._enforce_authenticity(
    TEXT, ledger, [], status0, held0, cta=CTA, channel="linkedin")
gate_after = qg.gate_authenticity(out_text, CTA)
print(json.dumps({
    "image": os.environ.get("IMAGE_TAG") or os.environ.get("GIT_SHA") or "",
    "gate_before": gate, "status_before_cut": status0, "held_reason_before_cut": held0,
    "repair_entry": entry, "status_after_cut": status2, "f19_after_cut": [g for g in ledger2 if g["gate"] == "F19_authenticity"],
    "gate_rerun_on_final_text": gate_after, "final_text": out_text,
    "cta_kept": CTA in out_text,
}, default=str, indent=1))
