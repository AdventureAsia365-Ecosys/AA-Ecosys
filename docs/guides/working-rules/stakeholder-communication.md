---
id: GUIDE-15-stakeholders
title: Working rules - stakeholder communication
description: The canonical English rules for writing to people outside the technical team - progress posts for the business owner, decision requests to the tech lead, business questions and vendor messages.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-15, GUIDE-15-sessions, GUIDE-15-planning, CAT-01, GUIDE-04, AA-1104]
lang: en
---

# Working rules - stakeholder communication

A message to someone outside the technical team goes straight to a person who decides. That is why every rule below
puts a review before the send. This page holds the **rules**. The procedures, with the formats, mentions and upload
steps, are the skills [`skill/aa-jira-update/SKILL.md`](../../../skill/aa-jira-update/SKILL.md) (Jira) and
[`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) with its voice guide (other channels). If a skill and
this page disagree, the stricter rule applies until one PR fixes both.

## Who reads what

| Reader | Channel | What they get |
|---|---|---|
| Business owner | Jira: one epic per app, features as stories, a weekly platform report | Product progress: what shipped and where to see it |
| Business owner, for a decision | One report page or one neutral question form, linked from the Jira draft | Options, a recommendation, the facts behind it |
| Tech lead, for a decision | A decision page with a proposed answer per question | Plain-words context and the answer the agent would pick |
| Vendors and resellers | Chat, under the tech lead's name | The situation, the need, numbered questions |

## Progress for the business owner

1. **Draft, approve, then post.** Every Jira comment, comment edit and status change is drafted, shown to the tech
   lead word for word, and posted only after an explicit "post". "Do not post yet, post when it is done" means wait
   for the work, not skip the approval.
2. **Agents never create Jira issues or change their status** to report progress. A new request goes under the right
   app epic only when the tech lead asks for it.
3. **Report only what shipped.** No "noted, will do". Say "it works" only for a channel tested live end to end, with
   a screenshot; otherwise say what is in the system and what was not tested, and why.
4. **Plain Vietnamese, short sentences, under the tech lead's name.** No agent names, table or function names, Linear
   keys or internal decision codes. Describe the feature and where to see it; no "as promised", no filler politeness.
5. **Numbers come from this session**: a query, an endpoint or the session snapshot, each with its date and time.
6. **Product progress only.** Infrastructure and architecture choices are the tech lead's call and are not posted as
   questions to the business owner. Internal cost detail and errors already fixed stay out unless the tech lead
   wants them.
7. **Batch the drafts.** All drafts of a session are shown once, together, at the session close, before the logs are
   written ([session rules](sessions.md#session-close)). A page made for the business owner goes into the draft of
   the issue it belongs to, not loose in a chat.
8. **Material for a decision is one report page** with tables, Dev numbers marked as unstable, long-term advice
   first (W6).

## Business and legal questions

- First ask whether a change to the system removes the question. Only a question that truly needs the business
  owner goes to them: price, fee, contract, legal counsel.
- Write it as a calm proposal: the options side by side, a recommendation, no deadline pressure, no default
  assumption that a lawyer is needed. The technical part of the work continues meanwhile.
- A question page is a neutral survey form grouped by domain, each question tied to the part of the spec it serves,
  with clear choices.
- For a vendor or reseller choice, show every option on the same terms (time, cost, fees, deposit, commitments,
  whether a new contract is needed). With a contract already signed, give the best technical option without pushing
  for a new contract or more cost. Keep a recommendation once given.

## Decisions asked of the tech lead

- Never a bare question: plain-words context plus the proposed answer. Act on the proposal and report it so the tech
  lead can overrule it (W1); an open question is not a reason to stop.
- Several questions become one decision page where each answer is a click and the approval is saved. The page works
  on a phone, and a bulk action asks for a second click in the page itself (the page frame blocks browser
  confirmation dialogs).

## Vendors and resellers

- Plain everyday chat, short sentences, numbered questions, under the tech lead's name. Refer to the business owner
  as "our management", never by name or title.
- Paste only what may leave the company: no account IDs, internal cost figures, issue keys or links to internal
  pages. Summarise such pages in words.

## Related

- [Session rules](sessions.md) and [planning and issue rules](planning-and-issues.md)
- [CEO guide](../ceo.md), the business owner's own entry point
- [Release-note template](../../templates/release-note.md), its Jira draft part
