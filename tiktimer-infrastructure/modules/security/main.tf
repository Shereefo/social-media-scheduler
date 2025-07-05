# modules/security/main.tf

# WAF Web ACL for protection against common web exploits
resource "aws_wafv2_web_acl" "main" {
  count       = var.enable_waf ? 1 : 0
  name        = "${var.project_name}-${var.environment}-web-acl"
  description = "Web ACL for ${var.project_name}-${var.environment}"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  # AWS Managed Rules for common threats
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 0

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # SQL Injection protection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # IP Rate limiting
  rule {
    name     = "RateLimitRule"
    priority = 2

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # IP restriction (if not open to all)
  dynamic "rule" {
    for_each = length(var.allowed_ip_ranges) == 1 && var.allowed_ip_ranges[0] == "0.0.0.0/0" ? [] : [1]
    content {
      name     = "IPRestrictionRule"
      priority = 3

      action {
        block {}
      }

      statement {
        not_statement {
          statement {
            ip_set_reference_statement {
              arn = aws_wafv2_ip_set.allowed_ips[0].arn
            }
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "IPRestrictionRule"
        sampled_requests_enabled   = true
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-web-acl"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-web-acl"
    Environment = var.environment
  }
}

# IP set for allowed IPs (if restricting access)
resource "aws_wafv2_ip_set" "allowed_ips" {
  count              = length(var.allowed_ip_ranges) == 1 && var.allowed_ip_ranges[0] == "0.0.0.0/0" ? 0 : 1
  name               = "${var.project_name}-${var.environment}-allowed-ips"
  description        = "Allowed IP addresses"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  addresses          = var.allowed_ip_ranges

  tags = {
    Name        = "${var.project_name}-${var.environment}-allowed-ips"
    Environment = var.environment
  }
}

# Associate WAF with ALB (if enabled)
resource "aws_wafv2_web_acl_association" "main" {
  count        = var.enable_waf ? 1 : 0
  resource_arn = var.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.main[0].arn
}

# Enable GuardDuty for threat detection
resource "aws_guardduty_detector" "main" {
  count = var.enable_guardduty ? 1 : 0

  enable = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-guardduty"
    Environment = var.environment
  }
}

# Enable Security Hub for security standards compliance
resource "aws_securityhub_account" "main" {
  count = var.enable_security_hub ? 1 : 0
}

# Enable AWS Config (required for Security Hub)
resource "aws_config_configuration_recorder" "main" {
  count = var.enable_security_hub ? 1 : 0

  name     = "${var.project_name}-${var.environment}-config-recorder"
  role_arn = aws_iam_role.config_role[0].arn

  recording_group {
    all_supported = true
  }
}

# IAM role for AWS Config
resource "aws_iam_role" "config_role" {
  count = var.enable_security_hub ? 1 : 0

  name = "${var.project_name}-${var.environment}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-config-role"
    Environment = var.environment
  }
}

# Attach AWS Config policy to the role
resource "aws_iam_role_policy_attachment" "config_policy" {
  count = var.enable_security_hub ? 1 : 0

  role       = aws_iam_role.config_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSConfigRole"
}

# S3 bucket for AWS Config recordings
resource "aws_s3_bucket" "config" {
  count = var.enable_security_hub ? 1 : 0

  bucket = "${var.project_name}-${var.environment}-config-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-config"
    Environment = var.environment
  }
}

# AWS Config delivery channel
resource "aws_config_delivery_channel" "main" {
  count = var.enable_security_hub ? 1 : 0

  name           = "${var.project_name}-${var.environment}-config-delivery"
  s3_bucket_name = aws_s3_bucket.config[0].bucket

  depends_on = [aws_config_configuration_recorder.main]
}

# Enable AWS Config recorder
resource "aws_config_configuration_recorder_status" "main" {
  count = var.enable_security_hub ? 1 : 0

  name       = aws_config_configuration_recorder.main[0].name
  is_enabled = true

  depends_on = [aws_config_delivery_channel.main]
}

# Get the current AWS account ID
data "aws_caller_identity" "current" {}