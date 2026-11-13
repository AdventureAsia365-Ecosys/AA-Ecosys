# AA-1096 (lane l10): acc1 spend is alert only (root docs side)

Lane l10 of S279. The Terraform change is in AA-CIS-Infra (`accounts/acc1-bedrock/cost_guard.tf`, its own
implementation notes `docs/implementation-notes/AA-1096-l10-acc1-budget.md` there). This file covers the root docs.

## Decisions

- **ADR 0001a gets a Note S279**, not a new ADR: the change is narrow (three free billing resources on acc1 that only
  send e-mails) and it amends the Note S278 line "no paid budget or anomaly monitor". The status block points at it.
- **Account-map lines updated where they list what acc1 holds**: onboarding (account map intro and the acc1 history
  paragraph), ecosystem architecture (accounts paragraph and the diagram node), engineering handbook FinOps row and
  its `.vi.md` translation (same PR, as `docs/STYLE.md` asks).
- No account ID, address or ARN added: the recipient e-mail lives in the untracked tfvars of the Infra root.

## Changed

- Nothing beyond the brief. The `.claude/CLAUDE.md` acc1 line ("only the Bedrock role and the break-glass role") is
  agent configuration and is left to the tech lead.

## Tradeoffs

- The ADR names the values (100 USD, 50/80/100 % actual, 100 % forecast, 10 USD daily anomaly) for the reader; the
  Terraform variables of the Infra root are the source if they change.

## Should know

- Ships together with the AA-CIS-Infra PR of the same lane; the ADR note describes the state after that root is
  applied (a human, locally, acc1 break-glass profile).
