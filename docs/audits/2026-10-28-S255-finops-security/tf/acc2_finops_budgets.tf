# =============================================================================
# DRAFT (S255, AA-896) — NOT applied, NOT in the Infra repo. Target: infra/AA-CIS-Infra/accounts/aa365/.
# Merge the pieces below into the existing files named in each section (do not add this file as is).
#
# Live facts this draft is based on (read 28/10/2026, Cost Explorer + Budgets, acc2):
#   - aa-cis-dev-monthly-total: 250 USD, actual Oct 01-27 = 176.04, AWS forecast Oct = 209.21.
#   - Run-rate 20-27/10 = 8.1-9.0 USD/day -> November ~ 255-265 USD (CRM api/web/portal 23-26/10, identity WAF
#     25/10, 50 secrets). The total budget has NO FORECASTED notification today, so the overrun is only
#     e-mailed after it happens (ACTUAL 80 % / 100 %).
#   - Per-App run-rate (x 30.4 days, 20-27/10, CRM and identity from their last 3 days):
#       shared ~100 (budget 100), cis ~66 (90), crm ~23 (25), booking ~11 (25), identity ~10 (NO budget),
#       tripplanner ~1.5 (10), untagged ~50 (only in the total).
#
# Proposal (decision D1 in the README): total 250 -> 300, add FORECASTED 100 %, add an `identity` per-App
# budget, shared 100 -> 120, crm 25 -> 35. Sum of per-App = 290 <= 300.
#
# NOT possible on acc2 (verified against the AWS guide, getting-started-ad, read 28/10/2026): "Cost monitors for
# linked accounts, cost allocation tags, and cost categories can only be created in the management account".
# acc2 is a member account of the TrueIDC payer, so an App-tag anomaly monitor (DIMENSIONAL/CUSTOM on TAG App)
# would fail with a ValidationException. The block at the end is kept commented as the exact request to hand
# to the payer (TrueIDC) if they agree to create it on their side; until then per-App spend is watched by the
# per-App budgets (FORECASTED 100 %) and the services monitor (cost_anomaly.tf, IMMEDIATE >= 5 USD).
# Cost of everything below: 0 USD (budgets without actions and Cost Anomaly Detection are free).
# =============================================================================

# --- 1. observability.tf: aws_budgets_budget.total_monthly -------------------------------------------------
# Replace limit_amount and add the third notification block.
resource "aws_budgets_budget" "total_monthly" {
  name         = "${local.name_prefix}-monthly-total"
  budget_type  = "COST"
  limit_amount = tostring(var.total_monthly_budget_usd) # was the literal "250"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_sns_topic_arns = [aws_sns_topic.alerts.arn]
  }

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_sns_topic_arns = [aws_sns_topic.alerts.arn]
  }

  # S255 (AA-896): warn before the month ends, like the per-App budgets already do.
  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "FORECASTED"
    subscriber_sns_topic_arns = [aws_sns_topic.alerts.arn]
  }

  depends_on = [time_sleep.wait_for_iam_propagation, aws_sns_topic_policy.alerts]
}

# --- 2. variables.tf ----------------------------------------------------------------------------------------
variable "total_monthly_budget_usd" {
  description = "Monthly USD budget for the whole acc2 account (AA-287; AA-896 S255: 250 -> 300 after the CRM + identity services)"
  type        = number
  default     = 300
}

# per_app_monthly_budgets: new default + validation list gains "identity" (Cognito WAF web ACL + identity secrets,
# ~10 USD/month since 25/10; data standard DM-10.1 must list the value too, see S248 finding F6).
variable "per_app_monthly_budgets" {
  description = "Monthly USD budget per App cost allocation tag value (AA-828)"
  type        = map(number)
  # AA-896 (S255): run-rate 20-27/10/2026 x 30.4: shared ~100, cis ~66, crm ~23 (portal since 26/10),
  # booking ~11, identity ~10, tripplanner ~1.5. Sum 290 <= total 300.
  default = {
    cis         = 90
    tripplanner = 10
    booking     = 25
    crm         = 35
    identity    = 10
    shared      = 120
  }

  validation {
    condition     = alltrue([for k, v in var.per_app_monthly_budgets : contains(["cis", "tripplanner", "booking", "crm", "identity", "shared"], k) && v > 0])
    error_message = "Keys must be App tag values (cis, tripplanner, booking, crm, identity, shared) and amounts must be > 0."
  }
}

# --- 3. cost_anomaly.tf: App-tag monitor — ONLY in the payer (management) account ---------------------------
# Kept as documentation. Applying it on acc2 fails (member account). Hand to TrueIDC if they offer it.
#
# resource "aws_ce_anomaly_monitor" "by_app_tag" {
#   name         = "aa-ecosys-by-App-tag"
#   monitor_type = "CUSTOM"
#   monitor_specification = jsonencode({
#     And  = null
#     Or   = null
#     Not  = null
#     Tags = { Key = "App", Values = ["cis", "booking", "tripplanner", "crm", "identity", "shared"], MatchOptions = ["EQUALS"] }
#     CostCategories = null
#     Dimensions     = null
#   })
# }
