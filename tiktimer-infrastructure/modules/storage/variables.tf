variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "tiktimer"
}


variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-2"
}

variable "enable_versioning" {
  description = "Enable versioning for S3 bucket"
  type        = bool
  default     = false
}

variable "enable_encryption" {
  description = "Enable server-side encryption for the S3 bucket"
  type        = bool
  default     = true
}

variable "encryption_algorithm" {
  description = "SSE algorithm"
  type        = string
  default     = "AES256"
}

variable "lifecycle_rules" {
  description = "List of lifecycle rules to configure"
  type = list(object({
    id                                          = string
    prefix                                      = string
    enabled                                     = bool
    expiration_days                             = number
    noncurrent_version_expiration_days          = number
    noncurrent_version_transition_days          = number
    noncurrent_version_transition_storage_class = string
  }))
  default = []
}


