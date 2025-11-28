# modules/frontend/variables.tf
# This file defines all inputs that our frontend module accepts

variable "project_name" {
  description = "Name of the project (e.g., 'tiktimer')"
  type        = string
  # Used to name resources: tiktimer-prod-frontend
}

variable "environment" {
  description = "Environment name (e.g., 'dev', 'staging', 'prod')"
  type        = string
  # Allows different configs for different environments
}

variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
  # CloudFront certificates MUST be in us-east-1
}

variable "domain_name" {
  description = "Custom domain for the frontend (optional, e.g., 'app.tiktimer.com')"
  type        = string
  default     = ""
  # Leave empty to use CloudFront's default domain
  # Set this later when you register a domain
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for custom domain (optional)"
  type        = string
  default     = ""
  # Only needed if using custom domain
}

variable "enable_logging" {
  description = "Enable CloudFront access logs"
  type        = bool
  default     = false
  # Useful for production to track usage
}
