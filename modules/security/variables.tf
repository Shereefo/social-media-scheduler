variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

# WAF Configuration
variable "enable_waf" {
  description = "Enable WAF for the application"
  type        = bool
  default     = false
}

variable "alb_arn" {
  description = "ARN of the application load balancer to associate with WAF"
  type        = string
  default     = ""
}

variable "allowed_ip_ranges" {
  description = "List of IP ranges allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Open to all by default
}

# GuardDuty Configuration
variable "enable_guardduty" {
  description = "Enable GuardDuty for threat detection"
  type        = bool
  default     = false
}

# Security Hub Configuration
variable "enable_security_hub" {
  description = "Enable Security Hub for security standards compliance"
  type        = bool
  default     = false
}

# Database configuration for secrets
variable "database_host" {
  description = "Database host endpoint"
  type        = string
  default     = ""
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = ""
}

variable "database_user" {
  description = "Database username"
  type        = string
  default     = ""
}

# TikTok API configuration
variable "tiktok_client_id" {
  description = "TikTok API Client ID"
  type        = string
  default     = ""
}

variable "tiktok_client_secret" {
  description = "TikTok API Client Secret"
  type        = string
  default     = ""
}

variable "tiktok_redirect_uri" {
  description = "TikTok OAuth redirect URI"
  type        = string
  default     = ""
}