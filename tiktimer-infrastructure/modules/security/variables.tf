variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "enable_waf" {
  description = "Enable WAF for the application"
  type        = bool
  default     = false
}

variable "alb_arn" {
  description = "ARN of the application load balancer"
  type        = string
  default     = ""
}

variable "allowed_ip_ranges" {
  description = "List of IP ranges allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Open to all by default
}

variable "enable_guardduty" {
  description = "Enable GuardDuty for threat detection"
  type        = bool
  default     = false
}

variable "enable_security_hub" {
  description = "Enable Security Hub for security standards"
  type        = bool
  default     = false
}