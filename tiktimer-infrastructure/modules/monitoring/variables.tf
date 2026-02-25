variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "TikTimer"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

# ── ECS ─────────────────────────────────────────────────────────────────────
variable "ecs_cluster_name" {
  description = "ECS cluster name (used as CloudWatch dimension)"
  type        = string
}

variable "ecs_service_name" {
  description = "ECS service name (used as CloudWatch dimension)"
  type        = string
}

variable "cloudwatch_log_group_name" {
  description = "CloudWatch log group name for the ECS application"
  type        = string
}

# ── ALB ─────────────────────────────────────────────────────────────────────
variable "alb_arn_suffix" {
  description = "ALB ARN suffix (e.g. app/TikTimer-dev-alb/abc123) — used as CloudWatch dimension"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix — used as CloudWatch dimension for per-TG metrics"
  type        = string
}

# ── RDS ─────────────────────────────────────────────────────────────────────
variable "db_instance_identifier" {
  description = "RDS DB instance identifier (used as CloudWatch dimension)"
  type        = string
}

# ── Alarm thresholds ─────────────────────────────────────────────────────────
variable "ecs_cpu_threshold" {
  description = "ECS service CPU utilization % that triggers a HIGH alarm"
  type        = number
  default     = 85
}

variable "ecs_memory_threshold" {
  description = "ECS service memory utilization % that triggers a HIGH alarm"
  type        = number
  default     = 85
}

variable "alb_5xx_threshold" {
  description = "Number of ALB HTTP 5xx errors per minute that triggers an alarm"
  type        = number
  default     = 10
}

variable "alb_latency_threshold" {
  description = "ALB target response time in seconds that triggers a HIGH latency alarm"
  type        = number
  default     = 2
}

variable "rds_cpu_threshold" {
  description = "RDS CPU utilization % that triggers an alarm"
  type        = number
  default     = 80
}

variable "rds_connections_threshold" {
  description = "RDS connection count that triggers an alarm (db.t3.micro max is ~85)"
  type        = number
  default     = 70
}

variable "rds_storage_threshold" {
  description = "RDS free storage space in bytes below which an alarm fires (default 2 GiB)"
  type        = number
  default     = 2147483648 # 2 GiB
}

# ── Notification ─────────────────────────────────────────────────────────────
variable "alert_email" {
  description = "Email address for alarm notifications. Leave empty to create the SNS topic without a subscription (add one manually post-apply)."
  type        = string
  default     = ""
}
