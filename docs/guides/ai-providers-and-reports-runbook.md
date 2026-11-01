---
id: GUIDE-12-ai-reports
title: AI providers and reports runbook
description: How to read and use the CIS admin pages for AI and data providers, spend and caps (AI providers, Cost Operations, Cost per app) and the report register (Reports), and what to do when a provider stops answering or spend jumps.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-cis-admin, GUIDE-04, FIN-01, OPS-04, AA-1020]
---

# AI providers and reports runbook

Part of [app access and operations](app-access-and-operations.md). A Vietnamese version of this page is
[ai-providers-and-reports-runbook.vi.md](ai-providers-and-reports-runbook.vi.md).

## 1. Who uses it

The business owner and admin staff, to answer four questions: is every paid AI and data provider answering, what did
it cost, how close is it to a cap, and did each recurring report run. All four pages are in the CIS admin and need
the **admin** role. Sign-in is the staff sign-in of the [CIS admin runbook](cis-admin-runbook.md#4-sign-in-and-out).

| Page | Menu path | Dev address |
|---|---|---|
| **AI providers** | Platform › AI & spend › AI providers | `https://aa-cis.lumiguides.it.com/admin/ai-gateway` |
| **Cost Operations** | Platform › AI & spend › Cost Operations | `https://aa-cis.lumiguides.it.com/admin/cost-ops` |
| **Cost per app** | Platform › AI & spend › Cost per app | `https://aa-cis.lumiguides.it.com/admin/platform/cost` |
| **Reports** | Platform › Overview › Reports | `https://aa-cis.lumiguides.it.com/admin/reports` |

Opening these pages calls no provider and costs nothing: every number comes from our own logs and stored checks. The
buttons that cost money say so below.

## 2. AI providers

The page has six tabs. Each tab has a **Guide** in plain words (the **Guide** tab, or **New here? Read the Guide**).

| Tab | What it shows | What you can change |
|---|---|---|
| **Providers** | Three tiles (**Spend this month**, **Spend today**, **Need a look**) and one row per paid source: **LLM connections**, **Decisions (Jev)**, **Data providers** (DataForSEO, Geoapify). Three views: **Overview**, **Connections**, **Jev credit** | **Connections**: switch a connection on or off, its limits and monthly budget, send one small test call. **Jev credit**: record a Jev top-up |
| **Routing** | Which model each pipeline stage uses first, its fallback chain and its shadow; the **LLM availability** card | **Save** (primary model), **Save route** (fallbacks and shadow) |
| **Models & trials** | Every model the platform can call, where it runs, its price, and the shadow comparisons | Switch a model on or off (prices change only through a reviewed change) |
| **Budgets** | Every spending cap: provider daily caps, job caps, connection budgets, tenant AI budgets | **Add a cap**, edit a cap. **Stops at the cap** ends a run; **Alert only** only warns |
| **Calls** | Every logged call, one by one, with its outcome and latency | Filters only |
| **Guide** | How to read the page | - |

### Read the status of a row

| Status | Meaning | What to do |
|---|---|---|
| **OK** | Answering, nothing near a limit | Nothing |
| **Degraded** | Answering, but recent calls failed | Watch; tell the engineer on duty if it lasts a day |
| **Circuit open** | Several calls in a row failed; the gateway skips this connection for a while and uses the next route | Nothing by hand; it retries by itself |
| **Low** | Balance below its alert threshold, or over 80 % of today's credits used | Plan a top-up with the tech lead |
| **Cap reached** | A budget, the balance or today's credits are used up; calls stop or fall back | Raise the cap only with the business owner's approval, or wait for the next period |
| **Off** | Switched off on purpose | Nothing |
| **No recent calls** | No answered call in 24 hours; nothing known to be wrong | Nothing |
| **Unknown** | The source could not be read, or no balance is known yet | Read the reason on the row |

### Common tasks

1. **Check before a paid run.** Open **Providers**. **Need a look** should be zero, and the connection the stage uses
   (see **Routing**) should be OK.
2. **Follow one job's calls.** Open **Jobs**, click the job, then **Open trace**; or in **Calls** choose **Only this
   job** on a row. The trace lists every paid call of that job in time order. For a whole tour: **Master Content** ›
   the tour › **Open AI trace**.
3. **Record a Jev top-up.** **Providers › Jev credit**: fill **Date** and **Amount (USD)**, then **Add top-up**. Jev
   has no balance service, so the credit left is an estimate from these top-ups minus our logged spend.
4. **Put refused jobs back.** When a provider that refused calls answers again (its row is OK), use **Re-queue refused
   jobs**. It shows the numbers first and re-queues only after you confirm, 50 at a time. The check is free; the jobs
   then run and cost what they cost the first time.

> [!WARNING]
> **Save** and **Save route** change the model of every next call of that stage. A shadow doubles the cost of the
> calls it samples. Changing a route or a cap is the tech lead's decision; ask first.

## 3. Cost Operations and Cost per app

- **Cost Operations** shows what the platform spends on AI models, DataForSEO, Jev and the AWS bill, against budget.
  Tabs: **Overview**, **AI & data spend** (by tenant, model and market), **LLM**, **DataForSEO**, **AWS bill**, **Jev**.
- **Cost per app** splits a month by app: CIS, Booking, TripPlanner, Partner CRM, plus shared (database and network)
  and identity (staff sign-in).
- **Refresh from AWS** asks Amazon for new numbers and costs about 0.04 USD per click. The pages refresh by themselves
  about once a day, so the button is rarely needed.

How to read the money is explained for the business owner in the [CEO guide, section 5](ceo.md#5-reading-the-cost);
the cost process is in [FinOps](../ops/finops.md).

## 4. Reports

**Reports** is the register of every recurring report of the platform: who reads it, how often, and whether it ran.

1. Read the tiles: **Reports in the register**, **Generated here**, **Overdue**, **Failed runs (7 days)**, **Latest KPI
   day** (the daily KPI snapshot is taken each morning at 07:30 Vietnam time for the day before).
2. Filter by family or priority, or tick **Generated here only**.
3. Open a report row. The drawer shows the decision it supports, the readers, the cadence, where it goes, the KPIs and
   its runs. Open a run to read its output.
4. **Generate now** (admin) queues an event report or a fresh run. It is ready in about a minute; press **Refresh**.

| State today | Meaning |
|---|---|
| **Up to date** | The last run covers the latest period |
| **Due** / **Overdue** | The next run is due, or late |
| **On request** | Runs only when someone presses **Generate now** |
| **First run pending** | Scheduled, not run yet |
| **Not generated here** | Written by hand from its template |

Daily, weekly and monthly reports run on their own. The business packs for the business owner are drafted here,
reviewed by the tech lead and then posted on Jira.

## 5. When something looks wrong

| You see | Then |
|---|---|
| **Need a look** above zero | Open the row; the reason line says why. Tell the engineer on duty if it is **Cap reached**, **Unknown** or **Circuit open** for more than a day |
| A budget alert e-mail | Open **Cost Operations** and **Budgets**; compare with the month so far; tell the tech lead |
| A provider row says access denied or no credit left | Do not change routes. The engineer on duty follows the [LLM access denied playbook](../ops/playbooks/llm-access-denied.md) or the [LLM cost spike playbook](../ops/playbooks/llm-cost-spike.md) |
| A report is **Overdue** or a run **Failed** | Open the run for its error; tell the engineer on duty |

During the dev phase the tech lead is the engineer on duty.

## 6. Dev-phase caveats

- The main chat-model account has refused every call since 2026-10-29: its rows show **Circuit open** or access
  denied, and AI stages wait or fail
  ([postmortem](../ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md)). Search embeddings still run.
- The direct Anthropic API path is not switched on yet; the OpenAI API is only the last resort of the judge stages.
- Dev numbers are small and unstable: test runs, not business volume. Do not read a trend from them.

## Sources (for maintainers)

Read from AA-CIS-App `main` on 2026-11-01: `frontend/app/admin/ai-gateway/messages.ts` and `guide.ts`,
`frontend/app/admin/cost-ops/messages.ts`, `frontend/app/admin/reports/messages.ts`, `frontend/lib/rbac.ts`. Report
register: [`reports/catalog.yaml`](../reports/catalog.yaml). Decisions: root ADR 0009. Keep
[ai-providers-and-reports-runbook.vi.md](ai-providers-and-reports-runbook.vi.md) in step with this page.
