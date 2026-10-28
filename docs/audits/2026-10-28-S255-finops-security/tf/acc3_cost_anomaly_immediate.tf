# =============================================================================
# DRAFT (S255, AA-896) — NOT applied. Target: infra/AA-CIS-Infra/accounts/acc3-bedrock/cost_guard.tf
# (append; this root is applied locally with the MFA profile nghiep_aa365, like the rest of acc3).
#
# Why: acc3 carries the LLM bill. October 01-27 = 242.13 USD (budget aa3-llm-monthly-total 250, AWS forecast
# 310.41). Single days reach 29-36 USD (08/10 Haiku 4.5 judge wave 34.27; 24/10 Sonnet 5.5 S1 writer wave 36.09),
# yet the only anomaly path is a DAILY e-mail (aa3-cost-anomaly-daily, >= 10 USD), i.e. up to ~24 h late.
# IMMEDIATE alerts need an SNS subscriber in the SAME account, so this adds a small topic on acc3 with the same
# bootstrap recipient as the acc2 alerts topic (var.acc3_cost_alert_email). The DAILY subscription stays as the
# summary.
#
# Cost: SNS topic 0 USD; e-mail deliveries inside the 1,000/month free tier; Cost Anomaly Detection free -> 0 USD.
# After apply: the recipient must click the SNS confirmation e-mail once (Terraform cannot confirm e-mail).
# =============================================================================

variable "acc3_anomaly_immediate_usd" {
  description = "AA-896 (S255): total impact (USD) of an acc3 cost anomaly that is sent at once through SNS"
  type        = number
  default     = 15
}

resource "aws_sns_topic" "acc3_cost_alerts" {
  name = "aa3-cost-alerts"
  tags = { Issue = "AA-896" }
}

resource "aws_sns_topic_subscription" "acc3_cost_alerts_email" {
  topic_arn = aws_sns_topic.acc3_cost_alerts.arn
  protocol  = "email"
  endpoint  = var.acc3_cost_alert_email
}

data "aws_iam_policy_document" "acc3_cost_alerts" {
  statement {
    sid     = "AllowCostAnomalyDetection"
    effect  = "Allow"
    actions = ["SNS:Publish"]
    principals {
      type        = "Service"
      identifiers = ["costalerts.amazonaws.com"]
    }
    resources = [aws_sns_topic.acc3_cost_alerts.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }

  statement {
    sid     = "AllowBudgets"
    effect  = "Allow"
    actions = ["SNS:Publish"]
    principals {
      type        = "Service"
      identifiers = ["budgets.amazonaws.com"]
    }
    resources = [aws_sns_topic.acc3_cost_alerts.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "acc3_cost_alerts" {
  arn    = aws_sns_topic.acc3_cost_alerts.arn
  policy = data.aws_iam_policy_document.acc3_cost_alerts.json
}

resource "aws_ce_anomaly_subscription" "acc3_immediate" {
  name             = "aa3-cost-anomaly-immediate"
  frequency        = "IMMEDIATE"
  monitor_arn_list = ["arn:aws:ce::${data.aws_caller_identity.current.account_id}:anomalymonitor/${var.acc3_services_monitor_id}"]

  subscriber {
    type    = "SNS"
    address = aws_sns_topic.acc3_cost_alerts.arn
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      match_options = ["GREATER_THAN_OR_EQUAL"]
      values        = [tostring(var.acc3_anomaly_immediate_usd)]
    }
  }

  tags = { Issue = "AA-896" }

  # The service checks its publish right on the topic when the subscription is created.
  depends_on = [aws_sns_topic_policy.acc3_cost_alerts]
}

# Optional (same PR): point the acc3 budget notifications at the topic too (subscriber_sns_topic_arns) so a
# FORECASTED overrun reaches the inbox the same way; keep subscriber_email_addresses or drop it to avoid two mails.
