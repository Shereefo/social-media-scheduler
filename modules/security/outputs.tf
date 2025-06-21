# WAF Outputs
output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].id : null
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].arn : null
}

# GuardDuty Outputs
output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = var.enable_guardduty ? aws_guardduty_detector.main[0].id : null
}

output "guardduty_detector_arn" {
  description = "ARN of the GuardDuty detector"
  value       = var.enable_guardduty ? aws_guardduty_detector.main[0].arn : null
}

# Security Hub Outputs
output "security_hub_enabled" {
  description = "Whether Security Hub is enabled"
  value       = var.enable_security_hub
}

# Secrets Manager Outputs
output "app_secrets_arn" {
  description = "ARN of the app secrets in Secrets Manager"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "tiktok_secrets_arn" {
  description = "ARN of the TikTok secrets in Secrets Manager"
  value       = aws_secretsmanager_secret.tiktok_secrets.arn
}

output "db_password" {
  description = "Generated database password"
  value       = random_password.db_password.result
  sensitive   = true
}