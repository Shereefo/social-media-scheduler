# Security Module for TikTimer Infrastructure

Comprehensive security hardening module for AWS infrastructure.

## Features
- AWS Secrets Manager integration
- WAF protection with SQL injection blocking
- GuardDuty threat detection
- Security Hub compliance monitoring
- IAM security hardening

## Usage
```hcl
module "security" {
  source = "./modules/security"
  
  project_name = "tiktimer"
  environment  = "dev"
  vpc_id       = "vpc-xxxxxxxxx"
  
  enable_waf         = true
  enable_guardduty   = true
  enable_security_hub = true
}
```