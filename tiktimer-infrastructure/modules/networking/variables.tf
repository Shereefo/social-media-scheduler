variable "vpc_cidr" {
    description = " CIDR block for the VPC"
    type = string
    default = "10.0.0.0/16"
}


variable "project_name" {
    description = "Name of project"
    type = string
}

variable  "environment" {
    description = "Deployment environment"
    type = string
    
}

variable "aws_region" {
    description = "AWS region"
    type = string
}

variable "availability_zones" {
    description = "AZs within the AWS region" 
    type = list(string)
}

variable "public_subnet_cidrs" {
    description = "CIDR blocks for public subnets"
    type = list(string)
    default = [ "10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24" ]
}

variable "app_subnet_cidrs" {
  description = "CIDR blocks for application private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "db_subnet_cidrs" {
  description = "CIDR blocks for DB private subnets"
    type = list(string)
    default = [ "10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24" ]
}

variable "single_nat_gateway" {
    description = "Create a single NAT gateway"
    type = bool
    default = true
}