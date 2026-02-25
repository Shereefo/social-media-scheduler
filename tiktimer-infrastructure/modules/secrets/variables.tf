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

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "db_host" {
  description = "Database host endpoint (without port)"
  type        = string
  default     = ""
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "scheduler"
}

variable "recovery_window_days" {
  description = "Number of days Secrets Manager waits before deleting a secret (0 = force delete, useful in dev)"
  type        = number
  default     = 0
}
