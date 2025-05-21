variable "aws_region" {
    description = "AWS region to deploy resources"
    type        = string
    default     = "us-east-2"
    
}

variable "environment" {
    description = "Deployment environment (dev/staging/prod)"
    type = string
    default = "dev"
}

variable "project_name" {
    description = "Name of project"
    type = string
    default = "TikTimer"
}

# Networking variables
variable "vpc_cidr" {
    description = "CIDR block for the VPC"
    type = string
    default = "10.0.0.0/16"
}

variable "availability_zones" {
    description = "List of availability zones to use"
    type = list(string)
    default = ["us-east-2a", "us-east-2b", "us-east-2c"]
  
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "app_subnet_cidrs" {
  description = "CIDR blocks for application private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "db_subnet_cidrs" {
  description = "CIDR blocks for database private subnets"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway instead of one per AZ (cost savings)"
  type        = bool
  default     = true
}

# Database Variables
variable "db_instance_class" {
  description = "Instance class for the database"
  type        = string
  default     = "db.t3.micro"  # Cost-efficient option for development
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "scheduler"
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
  default     = ""  # Will generate a random password if not provided
}

variable "db_multi_az" {
  description = "Whether to deploy a multi-AZ database"
  type        = bool
  default     = false  # Set to false for development to save costs
}

# Compute Variables
variable "container_port" {
  description = "Port exposed by the container"
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "CPU units for the container (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Memory for the container in MiB"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired count of container instances"
  type        = number
  default     = 2
}

variable "enable_autoscaling" {
  description = "Enable auto scaling for the ECS service"
  type        = bool
  default     = false
}

variable "container_image" {
  description = "Docker image for the container"
  type        = string
  default     = "public.ecr.aws/nginx/nginx:latest"  # Default to nginx for testing
}

variable "health_check_path" {
  description = "Path for health checks"
  type        = string
  default     = "/health"
}

variable "health_check_timeout" {
  description = "Timeout for health checks in seconds"
  type        = number
  default     = 5
}

variable "health_check_interval" {
  description = "Interval for health checks in seconds"
  type        = number
  default     = 30
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive successful health checks"
  type        = number
  default     = 2
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive failed health checks"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Minimum capacity for auto scaling"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum capacity for auto scaling"
  type        = number
  default     = 4
}

# Database URL for the container - constructed from DB parameters
variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
  default     = "" # Will be constructed dynamically if empty
}



# Security Variables
variable "enable_waf" {
  description = "Enable WAF for the application"
  type        = bool
  default     = false
}

variable "allowed_ip_ranges" {
  description = "List of IP ranges allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Open to all by default
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