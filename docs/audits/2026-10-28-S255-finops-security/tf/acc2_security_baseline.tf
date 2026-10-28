# =============================================================================
# DRAFT (S255, AA-873) — NOT applied, NOT in the Infra repo, not `terraform validate`d against the root.
# Target: infra/AA-CIS-Infra/accounts/aa365/security_baseline.tf (new) + the edits to observability.tf marked
# "EDIT observability.tf" below. Every paid item is a separate decision of Nghiệp (D-19); the README of this
# folder gives the monthly quote per item. Suggested PR order: (1) free items: BPA + Access Analyzer + EventBridge
# rules; (2) CloudTrail multi-region + KMS + bucket versioning/Object Lock; (3) GuardDuty (paid, ~15-20 USD/month).
#
# Live state read 28/10/2026 (us-west-1, acc2, read-only):
#   GuardDuty: 0 detectors. Access Analyzer: 0 analyzers. Security Hub: not subscribed. AWS Config: 0 recorders.
#   S3 account BPA: NoSuchPublicAccessBlockConfiguration. All 16 buckets have bucket-level BPA 4/4 true and no
#   public policy -> the account-level switch breaks nothing.
#   CloudTrail aa-cis-dev-trail: single-region, global service events on, log file validation on, no KMS, no
#   CloudWatch Logs, management events read+write, no data events. Bucket: versioning OFF, Object Lock OFF,
#   SSE-S3, lifecycle "Deep Archive after 30 days" that is a NO-OP: the bucket's lifecycle carries
#   TransitionDefaultMinimumObjectSize = all_storage_classes_128K and CloudTrail files average ~62 KB.
#   Volume: 26/10/2026 = 297 files, 18.4 MB gzip, 77,173 management events (65,380 read-only).
#
# CI permissions (bootstrap, like AA-896's CostAnomaly* statements): aws_iam_role_policy.tf_apply in cicd_split.tf
# needs guardduty:*Detector*/*Feature*/TagResource, access-analyzer:CreateAnalyzer/TagResource/GetAnalyzer,
# s3:PutAccountPublicAccessBlock/GetAccountPublicAccessBlock, kms:CreateKey/CreateAlias/PutKeyPolicy/
# EnableKeyRotation/TagResource for alias/aa-cis-dev-cloudtrail, s3:PutBucketVersioning/PutBucketObjectLockConfiguration
# on the trail bucket, iam:CreateRole/PutRolePolicy/PassRole for the forwarder role below (within the boundary), and
# events:* on rules named aa-sec-*. Apply that statement locally with the MFA profile first (targeted), then CI.
# =============================================================================

locals {
  sec_prefix = "aa-sec-${var.environment}"
  sec_tags   = merge(local.shared_tags, { Issue = "AA-873" })

  # Principals whose changes are expected (Terraform). Their IAM/SG changes do not alert; everything else does.
  sec_expected_change_roles = ["aa-cis-infra-tf-apply", "aa-cis-infra-tf-apply-crm"]
}

# -----------------------------------------------------------------------------------------------------------
# 1. S3 account-level Block Public Access — 0 USD
# -----------------------------------------------------------------------------------------------------------
resource "aws_s3_account_public_access_block" "this" {
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------------------------------------
# 2. IAM Access Analyzer, external access, account zone of trust — 0 USD
#    (The "unused access" analyzer is 0.20 USD per IAM role/user per month: NOT created.)
# -----------------------------------------------------------------------------------------------------------
resource "aws_accessanalyzer_analyzer" "external" {
  analyzer_name = "${local.sec_prefix}-external-access"
  type          = "ACCOUNT"
  tags          = local.sec_tags
}

resource "aws_cloudwatch_event_rule" "sec_access_analyzer_finding" {
  name        = "${local.sec_prefix}-access-analyzer-finding"
  description = "IAM Access Analyzer: a new ACTIVE external-access finding (AA-873)."
  event_pattern = jsonencode({
    source        = ["aws.access-analyzer"]
    "detail-type" = ["Access Analyzer Finding"]
    detail        = { status = ["ACTIVE"] }
  })
  tags = local.sec_tags
}

resource "aws_cloudwatch_event_target" "sec_access_analyzer_finding" {
  rule      = aws_cloudwatch_event_rule.sec_access_analyzer_finding.name
  target_id = "alerts-sns"
  arn       = aws_sns_topic.alerts.arn
  input_transformer {
    input_paths = {
      resource  = "$.detail.resource"
      type      = "$.detail.resourceType"
      principal = "$.detail.principal"
    }
    input_template = "\"[aa-sec] Access Analyzer: <type> <resource> is reachable from outside the account (principal <principal>). Archive the finding if intended, else fix the policy. AA-873\""
  }
}

# -----------------------------------------------------------------------------------------------------------
# 3. GuardDuty — paid. Foundational (CloudTrail management events + VPC flow + DNS) cannot be switched off.
#    Quote for our volume (us-west-1 price list, read 28/10/2026), per month:
#      management events ~2.0-2.4 M x 4.40 USD/M      = 9-10.5
#      VPC flow + DNS     ~3-6 GB   x 1.10 USD/GB      = 3.3-6.6
#      RDS login events   2 vCPU (db.t4g.small) x 1.34 = 2.68   (var.guardduty_rds_login, default on, per issue)
#      S3 data events     ~0.25 M  x 1.20 USD/M        = 0.30   (var.guardduty_s3_data_events, default off)
#      Runtime (Fargate)  2 vCPU x 1.85 = 3.70; EC2 NAT t4g.nano 2 vCPU x 1.85 = 3.70 -> OFF
#      EBS malware, EKS, Lambda network logs -> OFF
#    => ~15-20 USD/month. The first 30 days are a free trial; read `aws guardduty get-usage-statistics` after ~7 days
#    and record actual vs quote in Linear AA-873 (Done-when).
# -----------------------------------------------------------------------------------------------------------
variable "guardduty_enabled" {
  description = "AA-873: create the GuardDuty detector (paid, ~15-20 USD/month at Dev volume)"
  type        = bool
  default     = false
}

variable "guardduty_rds_login" {
  type    = bool
  default = true
}

variable "guardduty_s3_data_events" {
  type    = bool
  default = false
}

resource "aws_guardduty_detector" "main" {
  count                        = var.guardduty_enabled ? 1 : 0
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
  tags                         = local.sec_tags
}

# Every optional feature is managed explicitly: a detector created by the API turns several of them on by default.
locals {
  guardduty_features = {
    RDS_LOGIN_EVENTS       = var.guardduty_rds_login
    S3_DATA_EVENTS         = var.guardduty_s3_data_events
    EBS_MALWARE_PROTECTION = false
    EKS_AUDIT_LOGS         = false
    LAMBDA_NETWORK_LOGS    = false
    RUNTIME_MONITORING     = false
  }
}

resource "aws_guardduty_detector_feature" "this" {
  for_each    = var.guardduty_enabled ? local.guardduty_features : {}
  detector_id = aws_guardduty_detector.main[0].id
  name        = each.key
  status      = each.value ? "ENABLED" : "DISABLED"
}

resource "aws_cloudwatch_event_rule" "sec_guardduty_finding" {
  count       = var.guardduty_enabled ? 1 : 0
  name        = "${local.sec_prefix}-guardduty-finding"
  description = "GuardDuty finding of severity >= 4 (medium and up). AA-873."
  event_pattern = jsonencode({
    source        = ["aws.guardduty"]
    "detail-type" = ["GuardDuty Finding"]
    detail        = { severity = [{ numeric = [">=", 4] }] }
  })
  tags = local.sec_tags
}

resource "aws_cloudwatch_event_target" "sec_guardduty_finding" {
  count     = var.guardduty_enabled ? 1 : 0
  rule      = aws_cloudwatch_event_rule.sec_guardduty_finding[0].name
  target_id = "alerts-sns"
  arn       = aws_sns_topic.alerts.arn
  input_transformer {
    input_paths = {
      sev   = "$.detail.severity"
      type  = "$.detail.type"
      title = "$.detail.title"
      id    = "$.detail.id"
    }
    input_template = "\"[aa-sec] GuardDuty severity <sev>: <type> - <title> (finding <id>). AA-873\""
  }
}

# -----------------------------------------------------------------------------------------------------------
# 4. CloudTrail multi-region + KMS — ~1.05 USD/month
#    First copy of management events is free in every region -> multi-region adds only S3 storage (cents).
#    KMS: 1 USD/month per key + ~15k GenerateDataKey/month (0.03 USD/10k) -> ~1.05 USD.
#    CloudWatch Logs delivery + metric filters (~5-6 GB/month ingest ~3-3.5 USD + 5 metrics 1.50 + 5 alarms 0.50
#    ~ 5 USD/month) is NOT used: the alerts below are EventBridge rules on CloudTrail events (0 USD), the pattern
#    identity_alerts.tf / crm_data.tf already use.
# -----------------------------------------------------------------------------------------------------------
data "aws_iam_policy_document" "cloudtrail_kms" {
  statement {
    sid       = "IamAdministration"
    actions   = ["kms:*"]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]
    }
  }

  statement {
    sid       = "CloudTrailEncrypt"
    actions   = ["kms:GenerateDataKey*"]
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "kms:EncryptionContext:aws:cloudtrail:arn"
      values   = ["arn:aws:cloudtrail:*:${var.account_id}:trail/*"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [local.cloudtrail_trail_arn]
    }
  }

  statement {
    sid       = "CloudTrailDescribe"
    actions   = ["kms:DescribeKey"]
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
  }

  # Readers in this account (admin role, Athena/CLI) decrypt log files; same-account + CloudTrail context only.
  statement {
    sid       = "AccountReadersDecrypt"
    actions   = ["kms:Decrypt", "kms:ReEncryptFrom"]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    condition {
      test     = "StringEquals"
      variable = "kms:CallerAccount"
      values   = [var.account_id]
    }
    condition {
      test     = "StringLike"
      variable = "kms:EncryptionContext:aws:cloudtrail:arn"
      values   = ["arn:aws:cloudtrail:*:${var.account_id}:trail/*"]
    }
  }
}

resource "aws_kms_key" "cloudtrail" {
  description             = "AA-873: CloudTrail log files of ${local.cloudtrail_trail_name}"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  policy                  = data.aws_iam_policy_document.cloudtrail_kms.json
  tags                    = local.sec_tags
}

resource "aws_kms_alias" "cloudtrail" {
  name          = "alias/${local.name_prefix}-cloudtrail"
  target_key_id = aws_kms_key.cloudtrail.key_id
}

# EDIT observability.tf — aws_cloudtrail.main: change two arguments, keep the rest.
#   is_multi_region_trail = true                       # was false
#   kms_key_id            = aws_kms_key.cloudtrail.arn # new
# The bucket policy needs no change: aws:SourceArn is the trail ARN in its home region for every region's copy.

# -----------------------------------------------------------------------------------------------------------
# 5. Trail bucket: versioning + Object Lock GOVERNANCE 365 days (D-09) — ~0.2 USD/month (6.7 GB/year standard)
#    Object Lock on an existing bucket is allowed once versioning is on; it can never be turned off again.
# -----------------------------------------------------------------------------------------------------------
resource "aws_s3_bucket_versioning" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id
  rule {
    default_retention {
      mode = "GOVERNANCE"
      days = 365
    }
  }
  depends_on = [aws_s3_bucket_versioning.cloudtrail_logs]
}

# EDIT observability.tf — replace aws_s3_bucket_lifecycle_configuration.cloudtrail_logs: the Deep Archive transition
# never fires (128 KB minimum, files ~62 KB) and would cost more than it saves if forced (per-object transition fee
# 0.05 USD/1,000 x ~9k files/month vs ~0.01 USD storage saved). Keep logs in Standard (AA-286 "retain indefinitely").
resource "aws_s3_bucket_lifecycle_configuration" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  rule {
    id     = "noncurrent-and-mpu-cleanup"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 400 # after the 365-day lock
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.cloudtrail_logs]
}

# -----------------------------------------------------------------------------------------------------------
# 6. Alerts on CloudTrail events -> alerts SNS topic — 0 USD (AWS service events on the default bus are free;
#    the cross-region forward from us-east-1 is billed as custom events, 1 USD per million, i.e. ~0).
#    IAM, root sign-in and other global-service events reach EventBridge ONLY in us-east-1, so a us-east-1 rule
#    forwards them to the us-west-1 default bus, where the rules below match them like local events.
# -----------------------------------------------------------------------------------------------------------
resource "aws_cloudwatch_event_rule" "sec_trail_tamper" {
  name        = "${local.sec_prefix}-cloudtrail-tamper"
  description = "CloudTrail stopped, deleted or reconfigured. AA-873."
  event_pattern = jsonencode({
    source        = ["aws.cloudtrail"]
    "detail-type" = ["AWS API Call via CloudTrail"]
    detail = {
      eventName = ["StopLogging", "DeleteTrail", "UpdateTrail", "PutEventSelectors", "PutInsightSelectors", "DeleteEventDataStore"]
    }
  })
  tags = local.sec_tags
}

resource "aws_cloudwatch_event_rule" "sec_sg_change" {
  name        = "${local.sec_prefix}-security-group-change"
  description = "Security group created, deleted or opened outside Terraform. AA-873."
  event_pattern = jsonencode({
    source        = ["aws.ec2"]
    "detail-type" = ["AWS API Call via CloudTrail"]
    detail = {
      eventName = ["AuthorizeSecurityGroupIngress", "AuthorizeSecurityGroupEgress", "RevokeSecurityGroupIngress",
      "RevokeSecurityGroupEgress", "CreateSecurityGroup", "DeleteSecurityGroup", "ModifySecurityGroupRules"]
      # An assumed role other than Terraform's, or an IAM user (no sessionIssuer, so anything-but alone misses it).
      "$or" = [
        { userIdentity = { sessionContext = { sessionIssuer = { userName = [{ "anything-but" = local.sec_expected_change_roles }] } } } },
        { userIdentity = { type = ["IAMUser"] } },
      ]
    }
  })
  tags = local.sec_tags
}

resource "aws_cloudwatch_event_rule" "sec_iam_change" {
  name        = "${local.sec_prefix}-iam-change"
  description = "IAM user/role/policy/key change outside Terraform (forwarded from us-east-1). AA-873."
  event_pattern = jsonencode({
    source        = ["aws.iam"]
    "detail-type" = ["AWS API Call via CloudTrail"]
    detail = {
      eventName = [{ prefix = "Create" }, { prefix = "Delete" }, { prefix = "Attach" }, { prefix = "Detach" },
        { prefix = "Put" }, { prefix = "Update" }, { prefix = "Add" }, { prefix = "Remove" },
      "DeactivateMFADevice", "EnableMFADevice", "ResyncMFADevice", "SetDefaultPolicyVersion"]
      # An assumed role other than Terraform's, or an IAM user (no sessionIssuer, so anything-but alone misses it).
      "$or" = [
        { userIdentity = { sessionContext = { sessionIssuer = { userName = [{ "anything-but" = local.sec_expected_change_roles }] } } } },
        { userIdentity = { type = ["IAMUser"] } },
      ]
    }
  })
  tags = local.sec_tags
}

# Root: any API call or console sign-in. Root sessions have no sessionIssuer, so this is its own rule.
resource "aws_cloudwatch_event_rule" "sec_root_activity" {
  name        = "${local.sec_prefix}-root-activity"
  description = "Any root user activity, incl. console sign-in (forwarded from us-east-1). AA-873."
  state       = "ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS"
  event_pattern = jsonencode({
    "detail-type" = ["AWS API Call via CloudTrail", "AWS Console Sign In via CloudTrail"]
    detail        = { userIdentity = { type = ["Root"] } }
  })
  tags = local.sec_tags
}

locals {
  sec_cloudtrail_rules = {
    trail_tamper = aws_cloudwatch_event_rule.sec_trail_tamper.name
    sg_change    = aws_cloudwatch_event_rule.sec_sg_change.name
    iam_change   = aws_cloudwatch_event_rule.sec_iam_change.name
    root         = aws_cloudwatch_event_rule.sec_root_activity.name
  }
}

resource "aws_cloudwatch_event_target" "sec_cloudtrail_rules" {
  for_each  = local.sec_cloudtrail_rules
  rule      = each.value
  target_id = "alerts-sns"
  arn       = aws_sns_topic.alerts.arn
  input_transformer {
    input_paths = {
      event     = "$.detail.eventName"
      principal = "$.detail.userIdentity.arn"
      ip        = "$.detail.sourceIPAddress"
      region    = "$.detail.awsRegion"
      time      = "$.detail.eventTime"
    }
    input_template = "\"[aa-sec] ${each.key}: <event> by <principal> from <ip> in <region> at <time>. Expected only from Terraform or a planned change; otherwise treat as an incident. AA-873\""
  }
}

# --- us-east-1 forwarder (global-service events) ---
data "aws_iam_policy_document" "sec_forwarder_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.account_id]
    }
  }
}

resource "aws_iam_role" "sec_forwarder" {
  name               = "${local.sec_prefix}-events-forwarder"
  assume_role_policy = data.aws_iam_policy_document.sec_forwarder_trust.json
  tags               = local.sec_tags
}

resource "aws_iam_role_policy" "sec_forwarder" {
  name = "put-events-us-west-1-default-bus"
  role = aws_iam_role.sec_forwarder.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "events:PutEvents"
      Resource = "arn:aws:events:${var.aws_region}:${var.account_id}:event-bus/default"
    }]
  })
}

resource "aws_cloudwatch_event_rule" "sec_global_forward" {
  provider    = aws.us_east_1
  name        = "${local.sec_prefix}-global-forward"
  description = "Forward IAM changes and root activity (global services, us-east-1 only) to ${var.aws_region}. AA-873."
  state       = "ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS"
  event_pattern = jsonencode({
    "$or" = [
      { source = ["aws.iam"], "detail-type" = ["AWS API Call via CloudTrail"] },
      { "detail-type" = ["AWS API Call via CloudTrail", "AWS Console Sign In via CloudTrail"], detail = { userIdentity = { type = ["Root"] } } },
    ]
  })
  tags = local.sec_tags
}

resource "aws_cloudwatch_event_target" "sec_global_forward" {
  provider  = aws.us_east_1
  rule      = aws_cloudwatch_event_rule.sec_global_forward.name
  target_id = "usw1-default-bus"
  arn       = "arn:aws:events:${var.aws_region}:${var.account_id}:event-bus/default"
  role_arn  = aws_iam_role.sec_forwarder.arn
}

# Test for Done-when (orchestrator, after apply): create and delete a throwaway IAM policy with the MFA admin
# session -> one "[aa-sec] iam_change" e-mail per call within ~1 minute.
