variable "aws_region" {
  description = "AWS region for Terraform backend resources"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Project name used in backend resource naming"
  type        = string
  default     = "tiktimer"
}

variable "environment" {
  description = "Environment used in backend resource naming"
  type        = string
  default     = "shared"
}
