
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


# Security outputs 
output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = var.enable_waf ? module.security.waf_web_acl_id : null
}

output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = var.enable_guardduty ? module.security.guardduty_detector_id : null
}