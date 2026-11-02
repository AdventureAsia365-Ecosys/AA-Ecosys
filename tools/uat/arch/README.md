# Architecture videos and posts (tools/uat/arch)

Builds short, anonymized architecture explainers ("engineering notes") from the internal diagrams in
`docs/architecture/diagrams/`: one YouTube master plus three cut-downs per episode, a blog post with the same story, and
a five-layer public-content gate that fails the build on any hit. Everything runs locally at $0 (Kokoro TTS, Chromium,
ffmpeg, tesseract). Plan and rules: `docs/audits/2026-11-01-S262-arch-video-plan/README.md`; issue AA-1021.

## What never goes into this (public) repo

- Episode scripts, scene JSON, blog drafts, rendered videos, keyframes: keep them in `.tmp-session/` or Drive.
- The label profile (`labels.public.json`) and the deny-list (`deny.txt`): keep them in a private folder (`private/`
  here is gitignored; or any folder passed with `--private` / `ARCH_VIDEO_PRIVATE`). The committed
  `labels.public.example.json` and `deny.example.txt` use invented names only.
- Any phrase or label the videos use. The gate's n-gram and label-set checks fail a build whose text can be found in a
  public repo, and that includes text you add here.

## Setup (once)

```bash
bash tools/uat/setup.sh          # venv with kokoro-onnx, models/, Playwright (shared with the UAT videos)
bash tools/uat/arch/setup.sh     # IBM Plex Sans (OFL, pinned + sha256) and tesseract unpacked without root
```

## Build an episode

```bash
export ARCH_VIDEO_PRIVATE=/path/to/private        # deny.txt, labels.public.json, optional ngram_allow.txt
tools/uat/venv/bin/python -I tools/uat/arch/make_episode.py /path/to/ep1.json --out /path/to/out [--cuts master,short]
```

Output: `<out>/<slug>/` holds what may be published (`<slug>_<cut>.mp4`, `.srt`, `.vtt`, `.description.txt`,
`blog/<slug>.md`, `blog/images/*.png`). `<out>/<slug>-gate/` holds the team-only files: `gate-log.md` / `.json`
(counts per layer, tool versions, no script text) and `REVIEW.md` (the layer 5 checklist). Exit 0 = gate layers 1-4
passed; 1 = a gate hit; 2 = a scene or length error (for example a Short longer than 60 s).

Other environment variables: `ARCH_VIDEO_CACHE` (fonts, OCR, TTS clip cache; default `tools/uat/arch/.cache`),
`ARCH_VIDEO_WORKSPACE` (the folder holding the root repo with `apps/*` and `infra/*` for the n-gram corpus; default:
this checkout's main worktree), `ARCH_VIDEO_ROOT_REPO` (check the root repo text of another checkout, for example a
worktree with an unmerged change).

## Episode file (scene JSON)

Format and an invented, complete example: `scene.py` docstring and `tests/test_scene.py`. In short: scenes with a
chapter title, a visual (`title`, `points`, `diagram`, `end`) and sentences; each sentence has a voice (`F` = af_heart,
`M` = am_michael; scenes alternate by default) and the cuts it belongs to. A `diagram` visual names a diagram and the
public labels to `reveal`, `focus` (camera) and `highlight`. Cuts set the aspect (`16:9`, `1:1`, `4:5`, `9:16`) and
length rules (`min_s`, `max_s`); the master carries YouTube chapters (3 or more, 10 s or longer each). Write narration
in plain industry words; avoid the coined terms of the codebase and say "designed to" for anything not live.

## The gate (gate.py)

| Layer | What it checks | When |
|---|---|---|
| 1 text | Every authored string (narration, slide text, chapters, descriptions, hashtags, blog) and every public label: the private deny-list, built-in identifier shapes (12-digit account IDs, ARNs, network and pool IDs, hostnames, URLs, e-mails, regions, issue / migration / ADR / session numbers, money amounts), a 5-word n-gram check and an internal-token check against every tracked file of the public repos, and a label-set check (4+ public labels in one public file) | before any TTS or rendering |
| 2 DOM | Body text, SVG text/title/desc, alt / aria / title / data-* attributes, href/src of the stage page; `capture.cjs` refuses the screenshot on a hit; network requests are refused | before every keyframe |
| 3 OCR | tesseract on every keyframe and one frame every 2 s of each MP4, with one-letter fuzzy matching of deny terms; reported SKIPPED (with a warning) when tesseract is missing | after the MP4s |
| 4 artifacts | File and folder names, SRT/VTT, descriptions, blog, MP4 tags and chapter titles (ffprobe; only neutral tags allowed) | after the MP4s |
| 5 human | An independent review agent reads the script and the post, then the tech lead watches every cut (`REVIEW.md`) | before upload |

Tests: `python3 -m unittest discover -s tools/uat/arch/tests` (stdlib only; CI runs them in Docs lint). They prove that
a planted brand word, an account-ID-shaped number and a hostname each fail the text, DOM, OCR and artifact layers.

## Files

| File | Role |
|---|---|
| `make_episode.py` | the build: layer 1, diagrams through the profile, TTS, timelines, capture, MP4s, layers 2-4, logs |
| `scene.py` | scene JSON validation, per-cut timelines, keyframes, caption cues, chapters, SRT/VTT/ASS |
| `labels.py` | the label profile: map / drop / rewrite diagram text, strip titles and links, neutral icons |
| `page.py` | the stage page per aspect (neutral theme, reveal / focus / highlight on the SVG) |
| `capture.cjs` | Playwright keyframes at 2x with the layer 2 check before each shot |
| `tts_arch.py` | Kokoro clip per sentence and voice, two-pass loudnorm, cached by text hash |
| `video.py` | keyframes + narration to MP4 (cross-fades, burned captions, chapters, no metadata) |
| `gate.py` | the five layers, also usable on its own (`python -I gate.py text|dom|ocr|artifacts ...`) |

## Limits

- The n-gram and label-set checks are a floor, not proof: an idea can be recognisable without a shared phrase.
  Layer 5 is where that is judged.
- OCR misses small or faded text; layer 2 (the DOM check) is the primary guard for what is drawn.
- Text removed from a public file stays in its git history; the gate reads the current files only.
- Kokoro male voices sound less natural than af_heart; the tech lead judges the voice.
- Dense diagrams are small in 9:16; use `focus` on a few groups for Short scenes.
