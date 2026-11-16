---
name: project-business-update
description: Progress updates for the business owner and other readers outside the engineering team - draft first, approval by the tech lead, then post; describe shipped features in plain words with evidence, never internal tracker keys or technical decisions. Use when reporting progress on the business channel, writing the weekly report, reading a new business request, or preparing a page for the business owner.
---

# project-business-update

Parameters (in `AGENTS.md`): the business channel (tracker project, chat or mail), the epics per product, the reader's
language, how a mention is written.

## 1. Rules

- **Draft, approve, then post.** Every update is a draft until the tech lead approves it. Never post, create an issue
  or change a status on the business channel on your own.
- **All drafts once, at session close**, not one approval request at a time during the session.
- **Report what shipped, when it shipped.** A feature request is noted in the engineering tracker; the business update
  comes after it is verified live, with the evidence.
- **Claims need live evidence per channel.** Say "works" only for what was tested live end to end; say what was not
  tested.
- **Plain words.** Short sentences, the reader's language, roles not internal names; no internal tracker keys, no
  questions back to the reader unless a decision is really theirs.
- **Business, not technology.** Architecture and infrastructure are the tech lead's decisions and stay out of the
  update. A business, legal or commercial question goes as calm options with a recommendation.
- **One page for a long report**: a single report page (numbers flagged when they come from a test environment),
  linked from the update, not a stream of messages.

## 2. Draft shape

```markdown
<Greeting and mention of the reader>

**<Feature or area>** - live on <environment> since <date>.
- What it does for the reader, in one or two lines.
- How to try it: <link or steps>.
- Evidence: <screenshot or short video>.

**Next:** <one line>.
```

## 3. Weekly report

One update a week on the report epic: shipped features (with evidence), what is in progress, risks the business
should know, cost against budget. Numbers come from the session snapshots, never from memory.

## 4. Reading requests

When the reader asks for something new: acknowledge it in the draft, record it in the engineering tracker with the
reader's words quoted, and answer on the business channel only after it ships.
