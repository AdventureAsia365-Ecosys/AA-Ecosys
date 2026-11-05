# Architecture videos and posts (tools/uat/arch)

Builds short architecture videos: a master with chapters plus up to three cut-downs per episode, a blog post with the
same story, diagrams drawn from a per-episode sketch, and a five-layer public-content gate that fails the build
on any hit. Everything runs locally at $0 (Kokoro TTS, Chromium,
ffmpeg, tesseract). Issue: AA-1021 (content series, details private).

## What never goes into this (public) repo

- Episode scripts, scene JSON (with its diagram sketches), blog drafts, rendered videos, keyframes: keep them in
  `.tmp-session/` or Drive.
- The deny-list (`deny.txt`) and the series allow-list (`ngram_allow.txt`): keep them in a private folder (`private/`
  here is gitignored; or any folder passed with `--private` / `ARCH_VIDEO_PRIVATE`). The committed `deny.example.txt`
  and `sketch.example.json` use invented names only.
- Any phrase, label, series name, on-screen tag or hashtag the videos use, and anything that describes a built episode
  (cut lengths, build date, counts). The gate's n-gram, identity and label-set checks fail a build whose text can be
  found in a public repo, and that includes text you add here. Only `gate-summary.md` (layer, status, hit count) may be
  copied into an audit page.
- A committed diagram, relabelled or not: its layout, frames and arrow routes are a visual fingerprint of a public
  figure. Every diagram in a video is a sketch drawn for that episode (`sketch.py`).
- The icon files: `setup.sh` fetches them into the gitignored cache (see Icons).

## Setup (once)

```bash
bash tools/uat/setup.sh          # venv with kokoro-onnx, models/, Playwright (shared with the UAT videos)
bash tools/uat/arch/setup.sh     # theme font (OFL), official cloud icons (both pinned + sha256), tesseract (no root)
```

## Build an episode

```bash
export ARCH_VIDEO_PRIVATE=/path/to/private        # deny.txt, optional ngram_allow.txt
tools/uat/venv/bin/python -I tools/uat/arch/make_episode.py /path/to/ep1.json --out /path/to/out [--cuts master,short]
tools/uat/venv/bin/python -I tools/uat/arch/make_episode.py /path/to/ep1.json --out /path/to/out --check   # layer 1 only
```

Output: `<out>/<slug>/` holds what may be published (`<slug>_<cut>.mp4`, `.srt`, `.vtt`, `.description.txt`,
`blog/<slug>.md`, `blog/images/*.png`). `<out>/<slug>-gate/` holds the team-only files: `gate-log.md` / `.json`
(counts per layer, cut lengths, date, tool versions, no script text), `REVIEW.md` (the layer 5 checklist) and
`gate-summary.md` (layer, status and hit count only: the one file that may be copied into a repo). Exit 0 = gate layers 1-4
passed; 1 = a gate hit; 2 = a scene or length error (for example a Short longer than 60 s).

Other environment variables: `ARCH_VIDEO_CACHE` (fonts, OCR, TTS clip cache; default `tools/uat/arch/.cache`),
`ARCH_VIDEO_WORKSPACE` (the folder holding the root repo with `apps/*` and `infra/*` for the n-gram corpus; default:
this checkout's main worktree), `ARCH_VIDEO_ROOT_REPO` (check the root repo text of another checkout, for example a
worktree with an unmerged change). Before layer 1 the build fetches every corpus repo and stops (exit 2) when one is behind its
origin default branch or cannot be compared; `ARCH_VIDEO_ALLOW_STALE=1` skips that check (note it in the gate log).

## Episode file (scene JSON)

Format and an invented, complete example: `scene.py` docstring and `tests/test_scene.py`. In short: scenes with a
chapter title, a visual (`title`, `points`, `diagram`, `end`) and sentences; each sentence has a voice key (`F` or
`M`, two approved local voices; scenes alternate by default) and the cuts it belongs to. `diagrams` maps a key to a
sketch (groups on a grid, nodes, edges; format in `sketch.py`, invented example `sketch.example.json`); a `diagram`
visual names a sketch and the labels to `reveal`, `focus` (camera) and `highlight`. Optional `identity`: extra phrases
a viewer would search for (the series name and tag are always checked). Cuts set the aspect (`16:9`, `1:1`, `4:5`, `9:16`) and
length rules (`min_s`, `max_s`); the master carries chapters (3 or more, 10 s or longer each). Write narration
in plain industry words; avoid the coined terms of the codebase and say "designed to" for anything not live.

## Phone frames and framing

- The camera never cuts a node or a label: the view takes the card's exact shape, and a node, group title or edge label
  only partly inside it is hidden whole (a frame whose title is hidden and that holds no node in view goes too).
- A diagram can have a variant for the tall cuts: key `<diagram>@<name>` with `"aspects": ["9:16", "4:5"]`, its own
  grid and `"text_scale"` / `"node_w"`, drawn from the base labels only (`scene.load` checks). A diagram visual can set
  `"aspects": {"9:16,4:5": {"focus": [...]}}` so a phone frame shows a few nodes, large. Aim for node labels of about
  28 px at 1080 wide: two columns and two or three rows per frame at `text_scale` 1.5.
- Labels too wide for a node wrap onto two lines inside one `<text>`, so page.py and the gate still read one label.

## Icons

Diagrams use the official AWS Architecture Icons: the asset package AWS publishes on its architecture icons page, which
AWS permits customers and partners to use in architecture diagrams (keep the icons unmodified: no recolouring, cropping
or flipping). `setup.sh` downloads the package from a pinned URL, checks its sha256 and extracts only the files listed
in `sketch.ICONS` into `<cache>/aws-icons` (the zip is deleted); nothing of it is committed. A newer package means a
new URL, checksum and member paths in `setup.sh` and `sketch.ICONS`.

- A node draws the icon named by `"icon"` (a key of `sketch.ICONS`, or `"none"`), else the product its label names
  ("Amazon RDS ..." draws the RDS icon), else its kind's general icon (people: users, external: internet).
- A group `"kind"` (`cloud`, `account`, `region`, `vpc`, `private-subnet`, `public-subnet`, `generic`) draws the
  official group style: border colour and corner icon; a group `"icon"` draws a service group in the category colour.
  A label starting with "AWS Cloud" picks `cloud`.
- Icons are inlined as plain shapes: `<title>`, `<desc>`, ids and classes are dropped, and an icon holding text, an
  image, a link, a style or a `url()` reference is refused, so an icon adds nothing gate layers 1-2 can read. Layer 3
  (OCR) drops glyph noise as before (words lower than 5 px).
- Without the icon folder `make_episode.py` stops with a pointer to `setup.sh`.

## The gate (gate.py)

| Layer | What it checks | When |
|---|---|---|
| 1 text | Every authored string (narration, slide text, chapters, descriptions, hashtags, blog) and every label the rendered sketches draw (read back from the SVG, one entry per label): the private deny-list, built-in identifier shapes (12-digit account IDs, ARNs, network and pool IDs, hostnames, URLs, e-mails, regions, issue / migration / ADR / session numbers, money amounts), a 5-word n-gram check and an internal-token check (snake_case, dotted, hyphenated, CamelCase, ALLCAPS, letters+digits) against every tracked file of the public repos, an identity check (series name, series tag, listed phrases: not in any public file) and a label-set check (4+ drawn multi-word labels in one public file; cloud product names do not count) | before any TTS or rendering |
| 2 DOM | Body text, SVG text/title/desc, alt / aria / title / data-* attributes, href/src of the stage page; `capture.cjs` refuses the screenshot on a hit; network requests are refused | before every keyframe |
| 3 OCR | tesseract on every keyframe and one frame every 2 s of each MP4, with one-letter fuzzy matching of deny terms; reported SKIPPED (with a warning) when tesseract is missing | after the MP4s |
| 4 artifacts | File and folder names, SRT/VTT, descriptions, blog, MP4 tags and chapter titles (ffprobe; only neutral tags allowed) | after the MP4s |
| 5 human | An independent review agent reads the script and the post, then the tech lead watches every cut (`REVIEW.md`) | before upload |

Tests: `python3 -m unittest discover -s tools/uat/arch/tests` (stdlib only; CI runs them in Docs lint). They prove that
a planted brand word, an account-ID-shaped number and a hostname each fail the text, DOM, OCR and artifact layers.

## Files

| File | Role |
|---|---|
| `make_episode.py` | the build: layer 1 (with the drawn sketch labels), TTS, timelines, capture, MP4s, layers 2-4, logs |
| `scene.py` | scene JSON validation, per-cut timelines, keyframes, caption cues, chapters, SRT/VTT/ASS |
| `sketch.py` | a per-episode diagram sketch (grid, groups, nodes, edges, official icons) drawn as plain SVG, neutral keys only |
| `page.py` | the stage page per aspect (high-contrast light theme, reveal / focus / highlight on the SVG) |
| `capture.cjs` | Playwright keyframes at 2x with the layer 2 check before each shot |
| `tts_arch.py` | Kokoro clip per sentence and voice, two-pass loudnorm, cached by text hash |
| `video.py` | keyframes + narration to MP4 (cross-fades, burned captions, chapters, no metadata) |
| `gate.py` | the five layers, also usable on its own (`python -I gate.py text|dom|ocr|artifacts ...`) |

## Limits

- The n-gram and label-set checks are a floor, not proof: an idea can be recognisable without a shared phrase.
  Layer 5 is where that is judged.
- OCR misses small or faded text; layer 2 (the DOM check) is the primary guard for what is drawn.
- Text removed from a public file stays in its git history; the gate reads the current files only.
- The male local voice sounds less natural than the female one; the tech lead judges the voice.
- A sketch is simpler than the internal views on purpose; it must still be true (layer 5 checks it against the facts).
- Dense diagrams are small in 9:16; use `focus` on a few groups for Short scenes.
