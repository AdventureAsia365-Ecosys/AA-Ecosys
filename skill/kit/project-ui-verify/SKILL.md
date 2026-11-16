---
name: project-ui-verify
description: Check a user interface change before calling it done - type check, lint and build, a preview deployment, the UI smoke test, the page opened in a real browser with screenshots on desktop and mobile in light and dark mode, console and network errors, real data, and kit-only components. Use whenever a page, component, table or drawer is added or changed, or a user reports that a page shows nothing or the wrong thing.
---

# project-ui-verify

Parameters (in `AGENTS.md`): the web apps, their preview hosts, the sign-in method for automated checks, the UI kit
path.

## 1. Before the browser

```bash
npx tsc --noEmit
npm run lint
NODE_OPTIONS=--max-old-space-size=2048 npm run build   # one build at a time on a shared machine
```

## 2. In the browser

Open the changed pages on the preview deployment (or locally against Dev data) with an automated browser and check:

| Check | Pass when |
|---|---|
| Renders | No error page, no empty state where data exists, no layout break |
| Viewports | Desktop (1440 wide) and mobile (390 wide) |
| Themes | Light and dark |
| Console | No error; warnings explained |
| Network | No failed request (4xx or 5xx) the page needs |
| Data | Real rows from the environment, not only fixtures |
| Language | The page opens in the primary language; a second language only when the user picks it |
| Copy | No internal issue keys or debug text in user-visible text |

Take the screenshots yourself (the automated browser and the test sign-in); do not ask a human for them.

## 3. UI kit

- Use kit components only; no one-off styled copies of a kit component.
- Never edit the kit's core files outside their canonical copy; change the canonical copy, then sync.
- A cross-cutting feature (language switch, help, layout) is built once in the kit for the whole app.

## 4. Evidence

Attach the screenshots (desktop and mobile, light and dark) and the console and network summary to the PR. A UI change
is Done only after the deployed page passes the same checks (`project-ship` section 6).

## 5. When a user reports a broken page

Reproduce on the same environment and account role first, read the console and network panes, find the failing
request, then fix the cause (API, data or page), not the symptom.
