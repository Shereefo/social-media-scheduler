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
  database_url      = var.database_url

  db_allocated_storage       = 20
  db_storage_type            = "gp2"
  db_backup_retention_period = 7
  db_deletion_protection     = false
  db_skip_final_snapshot     = true
  db_apply_immediately       = true
}


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
  container_image    = var.container_image
  health_check_path  = var.health_check_path

  # Create a database URL for the container to use
  database_url = "postgresql://${var.db_username}:${var.db_password}@${module.database.db_instance_endpoint}/${var.db_name}"
  depends_on = [
    module.networking,
    module.database
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