# Security Module for TikTimer Infrastructure

# Get current AWS account ID and caller information
data "aws_caller_identity" "current" {}

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
    priority = 1

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
    priority = 2

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

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 3

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

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-web-acl"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-web-acl"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Enable GuardDuty for threat detection
resource "aws_guardduty_detector" "main" {
  count = var.enable_guardduty ? 1 : 0
  
  enable = true
  
  # Optional: Enable S3 protection
  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = false # Set to true if using EKS
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-guardduty"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Enable Security Hub for security standards compliance
resource "aws_securityhub_account" "main" {
  count = var.enable_security_hub ? 1 : 0
  
  enable_default_standards = true
  
  depends_on = [
    aws_config_configuration_recorder.main
  ]
}

# AWS Secrets Manager for sensitive configuration
resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
  upper   = true
  lower   = true
  numeric = true
}

# App secrets (database, JWT, etc.)
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${var.project_name}-${var.environment}-app-secrets"
  description             = "Application secrets for ${var.project_name}"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-secrets"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    DB_PASSWORD = random_password.db_password.result
    JWT_SECRET  = random_password.jwt_secret.result
    DB_HOST     = var.database_host
    DB_NAME     = var.database_name
    DB_USER     = var.database_user
  })
}

# TikTok API secrets
resource "aws_secretsmanager_secret" "tiktok_secrets" {
  name                    = "${var.project_name}-${var.environment}-tiktok-secrets"
  description             = "TikTok API secrets for ${var.project_name}"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-tiktok-secrets"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "tiktok_secrets" {
  secret_id = aws_secretsmanager_secret.tiktok_secrets.id
  secret_string = jsonencode({
    TIKTOK_CLIENT_ID     = var.tiktok_client_id
    TIKTOK_CLIENT_SECRET = var.tiktok_client_secret
    TIKTOK_REDIRECT_URI  = var.tiktok_redirect_uri
  })
}