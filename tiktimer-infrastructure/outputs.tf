
# Network module outputs
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "app_subnet_ids" {
  description = "List of application subnet IDs"
  value       = module.networking.app_subnet_ids
}

output "db_subnet_ids" {
  description = "List of database subnet IDs"
  value       = module.networking.db_subnet_ids
}


# Storage module outputs
output "uploads_bucket_id" {
  description = "The ID of the uploads S3 bucket"
  value       = module.storage.bucket_id
}

output "uploads_bucket_regional_domain_name" {
  description = "The regional domain name of the uploads S3 bucket"
  value       = module.storage.bucket_regional_domain_name
}


# Frontend module outputs
output "frontend_url" {
  description = "The URL where the frontend is deployed"
  value       = "https://${module.frontend.cloudfront_domain_name}"
}

output "frontend_cloudfront_distribution_id" {
  description = "CloudFront distribution ID (needed for cache invalidation)"
  value       = module.frontend.cloudfront_distribution_id
}

output "frontend_s3_bucket" {
  description = "S3 bucket name for frontend files"
  value       = module.frontend.bucket_id
}

output "frontend_deployment_commands" {
  description = "Commands to deploy and invalidate frontend cache"
  value       = module.frontend.deployment_info
}


# Database module outputs
output "db_instance_endpoint" {
  description = "The connection endpoint of the RDS instance"
  value       = module.database.db_instance_endpoint
}

output "db_instance_name" {
  description = "The name of the database"
  value       = module.database.db_instance_name
}

output "db_instance_port" {
  description = "The database port"
  value       = module.database.db_instance_port
}

output "db_password" {
  description = "The database password (for GitHub Secrets)"
  value       = module.database.db_password
  sensitive   = true
}

# Compute module outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.compute.alb_dns_name
}

output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = module.compute.cluster_id
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.compute.service_name
}

output "migration_task_family" {
  description = "Family name of the migration task definition for CD pipeline"
  value       = module.compute.migration_task_family
}

output "app_security_group_id" {
  description = "Security group ID for ECS tasks (needed for running migrations)"
  value       = module.compute.app_security_group_id
}

# ECR outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "ecr_repository_name" {
  description = "Name of the ECR repository"
  value       = aws_ecr_repository.app.name
}


# Security outputs 
output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = var.enable_waf ? module.security.waf_web_acl_id : null
}

output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = var.enable_guardduty ? module.security.guardduty_detector_id : null
}

# GitHub Actions OIDC outputs
output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role — set this as the AWS_DEPLOY_ROLE_ARN GitHub Secret after terraform apply"
  value       = aws_iam_role.github_actions.arn
}

# Monitoring outputs
output "alerts_sns_topic_arn" {
  description = "ARN of the CloudWatch alerts SNS topic — add email/PagerDuty subscriptions here post-apply"
  value       = module.monitoring.sns_topic_arn
}

output "dashboard_url" {
  description = "Direct URL to the CloudWatch dashboard"
  value       = module.monitoring.dashboard_url
}