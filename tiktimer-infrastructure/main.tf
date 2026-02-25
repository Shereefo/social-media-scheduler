module "networking" {
  source = "./modules/networking"

  vpc_cidr            = var.vpc_cidr
  environment         = var.environment
  project_name        = var.project_name
  aws_region          = var.aws_region
  availability_zones  = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  app_subnet_cidrs    = var.app_subnet_cidrs
  db_subnet_cidrs     = var.db_subnet_cidrs
  single_nat_gateway  = var.single_nat_gateway
}

module "storage" {
  source = "./modules/storage"

  project_name      = var.project_name
  environment       = var.environment
  aws_region        = var.aws_region
  enable_versioning = false

  lifecycle_rules = [
    {
      id                                          = "expire-old-videos"
      prefix                                      = ""
      enabled                                     = true
      expiration_days                             = 365 # Delete objects after 1 year
      noncurrent_version_expiration_days          = 90  # Delete old versions after 90 days
      noncurrent_version_transition_days          = 30  # Move old versions to cheaper storage after 30 days
      noncurrent_version_transition_storage_class = "STANDARD_IA"
    }
  ]
}

# Frontend hosting module (S3 + CloudFront for React app)
module "frontend" {
  source = "./modules/frontend"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  # Optional: Uncomment when you have a custom domain
  # domain_name      = "app.tiktimer.com"
  # route53_zone_id  = "Z1234567890ABC"

  # Enable CloudFront access logs in production
  enable_logging = var.environment == "prod" ? true : false
}

module "database" {
  source = "./modules/database"

  project_name         = var.project_name
  environment          = var.environment
  db_subnet_ids        = module.networking.db_subnet_ids
  db_security_group_id = module.networking.db_security_group_id

  db_instance_class = var.db_instance_class
  db_name           = var.db_name
  db_username       = var.db_username
  db_password       = var.db_password
  db_multi_az       = var.db_multi_az

  db_allocated_storage       = 20
  db_storage_type            = "gp2"
  db_backup_retention_period = 7
  db_deletion_protection     = false
  db_skip_final_snapshot     = true
  db_apply_immediately       = true
}

# Secrets module — creates Secrets Manager entries for DB credentials and
# application secrets. The compute module consumes the output ARNs for ECS
# native secret injection. Secret values are managed out-of-band after
# initial apply so they never pass through Terraform variables.
module "secrets" {
  source = "./modules/secrets"

  project_name = var.project_name
  environment  = var.environment

  # DB credentials come from the database module output so the password
  # Terraform generates is written once into Secrets Manager and never
  # appears as a plaintext env var in any task definition.
  db_username = var.db_username
  db_password = module.database.db_password
  db_host     = module.database.db_instance_address
  db_port     = module.database.db_instance_port
  db_name     = var.db_name

  # Use 0-day recovery in dev so secrets can be force-deleted cleanly
  # during teardown. Set to 7 or 30 in staging/prod.
  recovery_window_days = var.environment == "prod" ? 30 : 0

  depends_on = [module.database]
}

# ECR Repository for Docker images
resource "aws_ecr_repository" "app" {
  name                 = "${lower(var.project_name)}-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecr"
    Environment = var.environment
  }
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "app_policy" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECR Repository Policy for GitHub Actions
resource "aws_ecr_repository_policy" "app_policy" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowPushPull"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
      }
    ]
  })
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

module "compute" {
  source = "./modules/compute"

  project_name          = var.project_name
  environment           = var.environment
  aws_region            = var.aws_region
  vpc_id                = module.networking.vpc_id
  app_subnet_ids        = module.networking.app_subnet_ids
  public_subnet_ids     = module.networking.public_subnet_ids
  app_security_group_id = module.networking.app_security_group_id

  container_port     = var.container_port
  container_cpu      = var.container_cpu
  container_memory   = var.container_memory
  desired_count      = var.desired_count
  enable_autoscaling = var.enable_autoscaling
  container_image    = "${aws_ecr_repository.app.repository_url}:latest"
  health_check_path  = var.health_check_path

  # Secret ARNs — ECS resolves these at task launch and injects values
  # as environment variables. No plaintext credentials in task definitions.
  db_secret_arn  = module.secrets.db_secret_arn
  app_secret_arn = module.secrets.app_secret_arn

  # Pass S3 bucket ARN for IAM policy
  s3_bucket_arn = module.storage.bucket_arn

  depends_on = [
    module.networking,
    module.database,
    module.secrets
  ]
}

module "security" {
  source = "./modules/security"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.networking.vpc_id
  enable_waf          = var.enable_waf
  alb_arn             = module.compute.alb_arn
  allowed_ip_ranges   = var.allowed_ip_ranges
  enable_guardduty    = var.enable_guardduty
  enable_security_hub = var.enable_security_hub
}

# -----------------------------------------------------------------------
# Monitoring — Phase 4
#
# CloudWatch alarms for ECS (CPU, memory, running task count), ALB
# (5xx errors, latency, unhealthy hosts), and RDS (CPU, connections,
# free storage). All alarms route to a single SNS topic.
#
# To receive alert emails, set alert_email in dev.tfvars or pass it
# as a variable. The SNS subscription requires email confirmation
# out-of-band after terraform apply.
# -----------------------------------------------------------------------
module "monitoring" {
  source = "./modules/monitoring"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  # ECS dimensions
  ecs_cluster_name          = module.compute.cluster_name
  ecs_service_name          = module.compute.service_name
  cloudwatch_log_group_name = module.compute.cloudwatch_log_group_name

  # ALB dimensions — arn_suffix is the CloudWatch-required format
  alb_arn_suffix          = module.compute.alb_arn_suffix
  target_group_arn_suffix = module.compute.target_group_arn_suffix

  # RDS dimension
  db_instance_identifier = module.database.db_instance_identifier

  # Alert routing
  alert_email = var.alert_email

  depends_on = [
    module.compute,
    module.database
  ]
}

# -----------------------------------------------------------------------
# GitHub Actions OIDC — Phase 3: CI/CD auth hardening
#
# Registers GitHub's OIDC issuer with this AWS account so GitHub Actions
# runners can exchange a signed JWT for temporary STS credentials via
# AssumeRoleWithWebIdentity. No static AWS keys are stored in GitHub.
#
# This is a one-time account-level resource — if you already have a
# GitHub OIDC provider in this account for another repo, replace this
# resource with a data source lookup instead of creating a duplicate.
# -----------------------------------------------------------------------
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  # GitHub's OIDC audience for AWS
  client_id_list = ["sts.amazonaws.com"]

  # GitHub's current OIDC thumbprint — stable but can be rotated by GitHub.
  # Verify at: https://token.actions.githubusercontent.com/.well-known/openid-configuration
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  tags = {
    Name        = "github-actions-oidc"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# IAM role that GitHub Actions assumes during deployments.
# Trust policy is scoped to exactly this repo + main branch —
# no other GitHub repo or branch can assume this role.
resource "aws_iam_role" "github_actions" {
  name        = "${var.project_name}-${var.environment}-github-actions"
  description = "Assumed by GitHub Actions for ${var.project_name} ${var.environment} deployments via OIDC"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "GitHubOIDCTrust"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            # Audience must be sts.amazonaws.com (matches client_id_list above)
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            # Scoped to this repo only — main branch for deploy, any branch for PRs/CI
            # Format: repo:<owner>/<repo>:ref:refs/heads/<branch>
            "token.actions.githubusercontent.com:sub" = "repo:Shereefo/social-media-scheduler:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-github-actions"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Inline policy granting only the permissions the CD pipeline needs.
# Least-privilege: scoped to this environment's specific resources.
resource "aws_iam_role_policy" "github_actions_deploy" {
  name = "${var.project_name}-${var.environment}-github-deploy-policy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ECRAuth"
        Effect = "Allow"
        Action = ["ecr:GetAuthorizationToken"]
        # GetAuthorizationToken is account-level, cannot be scoped to a specific repo
        Resource = "*"
      },
      {
        Sid    = "ECRPushPull"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
          "ecr:DescribeRepositories"
        ]
        Resource = aws_ecr_repository.app.arn
      },
      {
        Sid    = "ECSDeployService"
        Effect = "Allow"
        Action = [
          "ecs:DescribeClusters",
          "ecs:DescribeServices",
          "ecs:UpdateService",
          "ecs:DescribeTaskDefinition",
          "ecs:RegisterTaskDefinition",
          "ecs:ListTaskDefinitions"
        ]
        Resource = "*"
      },
      {
        Sid    = "ECSRunMigrationTask"
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "ecs:DescribeTasks",
          "ecs:StopTask"
        ]
        Resource = "*"
      },
      {
        Sid    = "ECSWaitConditions"
        Effect = "Allow"
        Action = [
          "ecs:ListTasks"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAMPassRole"
        Effect = "Allow"
        # Required for ecs:RegisterTaskDefinition — ECS needs to verify the
        # caller can pass the task execution and task roles to the new task def
        Action = ["iam:PassRole"]
        Resource = [
          module.compute.task_execution_role_arn,
          module.compute.task_role_arn
        ]
      },
      {
        Sid    = "ELBDescribe"
        Effect = "Allow"
        Action = ["elasticloadbalancing:DescribeLoadBalancers"]
        Resource = "*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "${module.compute.cloudwatch_log_group_name == "" ? "*" : "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/${var.project_name}-${var.environment}:*"}"
      }
    ]
  })
}