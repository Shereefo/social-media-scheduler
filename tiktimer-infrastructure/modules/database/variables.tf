variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "TikTimer"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "db_subnet_ids" {
  description = "List of subnet IDs for the DB"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "Security group ID for the DB"
  type        = string
}

variable "db_instance_class" {
  description = "Instance class for the DB"
  type        = string
  default     = "db.t3.micro" # Cost efficient option for development
}

variable "db_name" {
  description = "Name of the DB"
  type        = string
  default     = "tiktimerdb"
}

variable "db_username" {
  description = "Username for the DB"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Password for the DB"
  type        = string
  sensitive   = true
  default     = ""
}

variable "db_allocated_storage" {
  description = "Allocated storage in  GiB"
  type        = number
  default     = 20
}

variable "db_storage_type" {
  description = "Storage type for the DB"
  type        = string
  default     = "gp2"
}

variable "db_multi_az" {
  description = "Whether to deploy a multi-AZ DB"
  type        = bool
  default     = false # Set to false for development to save costs
}

variable "db_backup_retention_period" {
  description = "How long to retain backups in days"
  type        = number
  default     = 7
}

variable "db_deletion_protection" {
  description = "Protect the DB from being deleted"
  type        = bool
  default     = false # Set to false for development
}

variable "db_skip_final_snapshot" {
  description = "Skip final snapshot when deleting the DB"
  type        = bool
  default     = true # Set to true for development
}

variable "db_apply_immediately" {
  description = "Apply changes immediately rather than during the next maintenance window"
  type        = bool
  default     = true
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
  default     = ""
}