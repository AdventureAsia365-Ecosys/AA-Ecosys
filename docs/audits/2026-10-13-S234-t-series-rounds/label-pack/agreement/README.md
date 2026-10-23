# AA-783 — label data and agreement tooling

Tooling to calibrate the S234 T9 commercial panel (4 AI lenses) and the T9 gates against human labels on the
40 pieces of `../S234-label-40.xlsx`. Criteria: `../HUONG-DAN-CHAM.md` (Vietnamese, agreed in S234).
Nothing here calls an LLM or writes to the database.

| File | Where it runs | What it does |
|---|---|---|
| `build_panel_key.py` | local, once | Reads the S234 scratch panel data and the pack's `_key` sheet, writes `panel_key.json` and embeds it in `aa783_export.py` (`--embed`). |
| `panel_key.json` | data | Per piece: the 4 lens verdicts and scores (overall, fidelity, ai_tells), majority, tie flag, fidelity audit, deciding defects, gate status at S234, sha256 of the text the panel scored. |
| `aa783_export.py` | CIS api container (ECS exec) | Read-only export: the 40 pieces (text, title, meta, source, brand) plus a hidden `key` (gate ledger, panel key, existing labels). |
| `agree.py` | local | `decode` the exec output, build `page` data for the label page (no key), compute the agreement `report`. |
| `report-s248.md` | data | The agreement report of the 40 S248 labels (AI-drafted, owner-approved) and the gate / threshold decisions taken from it (closes AA-783). |

## Label scheme (one row per piece)

Same keys as the admin Label action (AA-791, `content_piece_label`), so labels can be saved there later unchanged.

| Field | Values | Definition |
|---|---|---|
| `label` | `as_is` / `light` / `heavy` / `reject` | as-is: publish verbatim. light: ≤10 min, ≤3 sentences, no fact research. heavy: more than light, still worth keeping. reject: rewriting is faster. Unsure: pick the stricter. |
| `defects.fact` | `none` / `light` / `heavy` | A trip claim not in SOURCE (schedule, times, services, optional shown as included, pace), a number not in SOURCE, a place outside the scope, an overstatement. Correct common background knowledge is not a defect. |
| `defects.voice` | same | Not this brand's voice (vs BRAND): audience, energy, forbidden word, copied brand-pack line, CTA not the configured line. |
| `defects.format` | same | LinkedIn: <120 or >250 words, >3 hashtags, weak first line, misspelt hashtag. Blog: title/meta off scope, FAQ <3 or off-topic, instruction-style heading, repeated/broken sentence, CTA twice. |
| `defects.ai_phrasing` | same | "Not X, but Y" density, stock lines, generic opener, summary closer, many em dashes. |
| `minutes_to_fix` | integer 0–600 or null | 0 for as-is, null for reject. |
| `worst_sentences`, `reason` | text | 1–3 worst sentences verbatim; anything a gate should catch. |
| `content_sha256` | hex | sha256 of the text shown (from the page data), to catch a label made on a different text. |

Levels: `light` = present but fixed in seconds; `heavy` = the main reason the piece is not publishable verbatim.

## Agreement metrics (`agree.py report`)

1. **Light share**: human as-is / light-or-better / reject share, next to the panel's and the gate's approval
   rate, overall, per channel, per tenant×channel cell and per gate status. The offset panel − human gives the
   panel bar that matches the human 60% bar (`LIGHT_BAR`).
2. **Verdict agreement, human vs panel majority and vs each lens** (editor, brand lead, channel, client):
   exact agreement, Cohen's kappa (unweighted), quadratic-weighted kappa (ordinal scale), binary kappa on
   light-or-better vs heavy-or-worse; 95% bootstrap CIs (2,000 resamples, seed 783); confusion matrix; how often
   the panel is stricter or more lenient. Panel-internal Fleiss kappa for context. The panel "can stand in"
   when both quadratic and binary kappa reach `STAND_IN_KAPPA` (0.60, Landis–Koch substantial).
3. **Gate approve/hold vs human** (should approve = light-or-better): precision, recall, held precision,
   accuracy, kappa; the panel majority on the same footing for comparison.
4. **Per gate vs the human defect column it targets** (`GATE_COLUMN`): fired in the final ledger and on any
   attempt, against human `light|heavy` and `heavy` only: TP/FP/FN, precision, recall, and fires on pieces the
   human called light-or-better. Plus the union of all gates of a column, and each held piece's holding gate
   vs the human level in that column.
5. **Panel scores vs human defect levels** (Spearman; negative = agrees): fidelity (lens mean, each lens, the
   fidelity audit) vs `fact`; ai_tells vs `ai_phrasing`; overall vs the human verdict and vs minutes to fix.
   `voice` and `format` have no per-lens panel score (brand_voice / channel_fit were not kept in S234), so those
   two columns are compared with the gates only.
6. **Human vs human** when a second labeller (e.g. Ms. Thư) labels some of the same pieces.

n = 40, so read every kappa with its CI; a difference of one or two pieces per cell is noise.

## Run

```bash
python3 build_panel_key.py --embed          # only if the panel key must be rebuilt
# export: see the S248 lane handoff (ECS exec, read-only, --gzip --s3 …)
python3 agree.py decode raw.txt -o export.json
python3 agree.py page export.json -o page_data.json --pack ../S234-label-40.xlsx
python3 agree.py report export.json labels.json -o report.json --md report.md
```
