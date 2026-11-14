---
id: GUIDE-13
title: AA Academy course files
description: How AA Academy courses are written in this folder - paths, modules, lessons, quizzes and the allowlist, how a lesson cites its sources and pins their hashes, the checks in docs lint and the learn bundle Docs sync publishes.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-13-lms, GUIDE-13-lms-inventory, GUIDE-15, CAT-00, TPL-02, AA-1104]
lang: en
---

# AA Academy course files

AA Academy is the AA learning site: role learning paths with short lessons, quizzes and labs. Learners use the academy
host `academy.<env domain>` (Dev: `academy.lumiguides.it.com`), served by the CRM web app; the courses, progress,
quizzes and certificates come from the CIS learning API (`/learn/v1`, contract
[`learn.http.v1`](../contracts/learn.http.v1.openapi.yaml)) and its schema `learn`. Staff sign in there with the staff
sign-in; agencies follow later. The CIS admin links to the academy and keeps the team view (decision D17,
[ADR 0022](../adr/0022-aa-academy-learning-platform.md)). The design, the paths and the decisions are in the
[research](../research/lms/README.md). This folder holds the courses as files, and this page is their format.

**One rule above all: a course never copies its sources.** A lesson names the sections it teaches from, by
reference, and pins a hash of each one. The reader shows the live section next to the lesson. When a source changes,
the check turns red or the lesson is marked stale, so no lesson drifts away from the rule it teaches.

## Layout

```text
docs/learn/
  README.md                         this page
  allowlist.yaml                    skill, steering and CONTEXT.md sections the bundle may publish; agency pages
  schema/*.schema.json              JSON Schemas of every file below
  paths/<path id>.yaml              one learning path: modules in order, required or elective, planned modules
  modules/<ID>-<slug>/
    module.yaml                     id, title, tier, status, version, owner, objectives, prerequisites, lessons
    lessons/<NN>-<slug>.md          the lesson body: no front-matter, the first line is the H1 title
    lessons/<NN>-<slug>.vi.md       optional Vietnamese translation of the lesson body
    quiz.yaml                       5 to 10 retrieval items, each citing the section it tests
    lab.yaml                        optional hands-on lab (closed until the lab provisioner exists)
```

The first module written in this format is [F3 How work flows](modules/F3-how-work-flows/module.yaml) on the
[Fundamentals path](paths/fundamentals.yaml). Copy it to start a new module.

## Modules and lessons

- **Module ID** is the code from the research paths (F1 to F6, E1 to E15, L1 to L9, S, C, B, O, A). The folder
  starts with it: `F3-how-work-flows`. A lesson ID is `<module>-NN`: `F3-01`.
- **Tier** is who may read the module: `staff` (every staff role) or `partner` (agency owners and agents). A path
  holds modules of its own tier only. A `partner` module cites only the catalog pages listed under `partner_pages`
  in the allowlist and allowlist sections of tier `partner` (decision D13).
- **Status** is `draft` until the tech lead approved the module, `active` when learners see it, `retired` when it
  is withdrawn. A second person approves every module (maker-checker); for quiz items an agent drafted, the approver
  is a human owner.
- **Version** follows semantic versioning: patch for wording, minor for a new lesson, major when the objectives or
  the quiz items change. A major version of a required module asks its learners to certify again.
- **A lesson body** holds only what no source holds: the objective, a short framing, a pointer to the sections and
  two or three "check yourself" questions. It carries no front-matter; its metadata lives in `module.yaml`, and its
  H1 equals the lesson title there.
- **Language.** English is the source. A Vietnamese lesson is the sibling file `<NN>-<slug>.vi.md` and the module
  lists `vi` under `languages` (decision D5).
- **Lesson types** are `reading`, `walkthrough` (a short video) and `worked-example`. The quiz and the lab are module
  files, not lessons.
- **A lesson video** (optional, decision D8) is named by the lesson's `video` field: `key` is the object key under the
  private `learn-media/` prefix (`learn-media/<module id>/<NN>-<slug>.mp4` or `.webm`) and `captions` lists the
  caption languages (`en` required), whose files sit next to it as `<key without extension>.<lang>.vtt`. Videos are
  built locally with `tools/uat` and uploaded there, never kept in git; the learning API checks access and returns a
  presigned URL that lives for the `cis.learn.video_url_ttl_seconds` setting.

## Citing a source

Each lesson lists its `sources`. A source is a reference plus a pinned hash:

```yaml
sources:
  - ref: doc:CAT-01#22-sources-of-truth-for-process-state
    sha: 9c7ffcfcea34737f
```

| Reference | Points at | Allowed when |
|---|---|---|
| `doc:<catalog id>[#anchor]` (or the bare ID) | a catalog page the docs reader publishes | the page is not owner only (SEC-*, ARCH-02/03/04) |
| `adr:<NNNN>[#anchor]` | a root ADR | always |
| `skill:<name>#anchor` | a section of `skill/<name>/SKILL.md` | the section is in the allowlist |
| `steering:<name>#anchor` | a section of `.kiro/steering/<name>.md` | the section is in the allowlist |
| `context:<repo>#anchor` | a section of an app or Infra repo's `CONTEXT.md` | the section is in the allowlist |

- **Anchor** is the GitHub heading slug. A section runs from its heading to the next heading of the same or a higher
  level. A reference without an anchor cites the whole page.
- **The pin** is the first 16 hex characters of the SHA-256 of the section. Never write it by hand: read the section,
  then run `python tools/docs/check_learn.py --pin`, which writes the current hashes into `module.yaml`.
- **When a cited section changes**, the check fails on the next pull request. The module owner reads the changed
  section, updates the lesson and the quiz items that cite it if needed, and pins again. A pin that moves without that
  review defeats the check.
- **Quiz items** cite one of their module's lesson sources, with an anchor. When that section changes, the item is
  suspended until it is reviewed.

## The allowlist

[`allowlist.yaml`](allowlist.yaml) is the only way a section of a skill, a steering file or a `CONTEXT.md` reaches
the learn bundle: one entry per section, with a tier and a reason; anything not listed is never published (default
deny). Its second list, `partner_pages`, names the catalog pages an agency module may cite. The redaction guard of the
docs reader runs on every listed section. A change to the allowlist widens who can read what, so it is reviewed as
a risky change (auth and access) before merge.

## Checks

| Where | What runs | Fails on |
|---|---|---|
| Docs lint, every root pull request that touches `docs/**` or `tools/docs/**` | `python tools/docs/check_learn.py`, and the unit tests `tools/docs/test_check_learn.py` and `tools/docs/test_learn_bundle.py` | a file that breaks its schema, a duplicate ID, a reference that does not resolve, a missing or changed pin, a partner module citing a staff page, a section cited outside the allowlist, a prerequisite cycle, an account or resource ID in course text |
| Docs sync, on master | `python tools/docs/build_learn_bundle.py`, with the app repos' `CONTEXT.md` files checked out | any course error except drift; drift is published as stale (below) |

Run them locally before pushing:

```bash
python3 tools/docs/check_learn.py
python3 tools/docs/check_learn.py --ext-root <workspace-root> --strict-external
python3 -m unittest discover -s tools/docs -p 'test_*learn*.py'
python3 tools/docs/build_learn_bundle.py --check --ext-root <workspace-root>
```

The second line also checks the `context:` sections against the app repos: `<workspace-root>` is the folder that
holds `apps/<repo>` and `infra/AA-CIS-Infra`.

## The learn bundle

The Docs sync workflow builds the learn bundle after it has uploaded the docs pages, into its own folder, and uploads
it under the docs reader prefix at `learn/`. A course error never stops the pages: the learn steps run last, a failed
build uploads nothing for learn (the previous bundle stays), and only the run turns red.

| Object | What it holds |
|---|---|
| `learn/manifest.json` | paths, modules and lessons with their metadata, every cited section with its current hash and tier, per lesson which sources are stale, and the lesson's video and caption keys (under `learn-media/`, not under `learn/`). It never holds a quiz answer |
| `learn/lessons/<module folder>/<NN>-<slug>.md` | the lesson body and its translation, redacted |
| `learn/sections/<kind>/<name>/<anchor>.md` | the redacted text of each cited section |
| `learn/quizzes/<module id>.json` | the quiz items with their answers and a `suspended` flag. Read by the learning API on the server only; answers never reach a browser before a submission |

**Stale.** On master a changed root section does not withhold the course: the lesson is marked stale, the quiz items
that cite the section are suspended, and the learning API opens a content review item for the module owner
(GUIDE-13 research §6.4). An app repo's `CONTEXT.md` that cannot be read, or whose section is gone, marks its
lessons stale the same way. The full format is in the header of `tools/docs/build_learn_bundle.py`.

## Related

- [AA Academy research and decisions](../research/lms/README.md) and the [knowledge inventory](../research/lms/inventory.md)
- [Working rules](../guides/working-rules/README.md), the rule pages lessons cite
- [Docs style guide](../STYLE.md)
