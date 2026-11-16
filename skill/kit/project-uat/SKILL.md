---
name: project-uat
description: User acceptance testing for business sign-off - a scripted walk through the feature with an assertion at every step, captions, an optional narration with a free local text-to-speech voice, frame and audio checks, packaging and upload, and the UAT report. Use when a feature needs the business owner's sign-off, for a pilot onboarding, for a drill or rehearsal, or when a product introduction video is asked for.
---

# project-uat

Template: `docs/templates/uat-report.md`. Parameters (in `AGENTS.md`): the apps and test sign-ins, the voices and
languages, the upload destination.

## 1. When to record

Record a UAT run when the business owner signs off a feature, when a pilot customer is onboarded, and for every drill
or rehearsal. Do not record routine changes: screenshots in the PR are enough (`project-ui-verify`).

## 2. Script

- One script per scenario, driven by an automated browser.
- Every step has an assertion (the element, the text, the number); a failed assertion fails the take. A video of a
  failing flow is never published as a pass.
- Captions say what the user does and what they should see, in the reader's language.
- Invented data only (names, places, amounts); never copy real customer data into a script.

## 3. Narration (optional)

- A free text-to-speech model that runs locally (open-source); no paid voice service.
- Check that each caption's audio fits its step and that frames are not blank or frozen.

## 4. Package and upload

- Each take is packaged with its result file (verdict, steps, timings) and uploaded; the upload is checked
  (same files and sizes at the destination) before the take's working folder is removed.
- Keep an index of takes with their verdict and link.

## 5. Report

Fill the UAT report: scenario, environment, build (commit SHA), each step with pass or fail, the link to the take,
open issues, and the sign-off line for the business owner.
