# DB  Subnet group
resource "aws_db_subnet_group" "main" {
  name       = "${lower(var.project_name)}-${var.environment}-db-subnet-group"
  subnet_ids = var.db_subnet_ids


  tags = {
    Name        = "${var.project_name}-${var.environment}-db-subnet-group"
    Environment = var.environment
  }
}

# DB parameter group
resource "aws_db_parameter_group" "main" {
  name   = "${lower(var.project_name)}-${var.environment}-postgres"
  family = "postgres15" # Update if needed

  parameter {
    name  = "log_connections"
    value = "1"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-postgres"
    Environment = var.environment
  }
}

# Create a random password for the database
resource "random_password" "db_password" {
  count   = var.db_password == "" ? 1 : 0
  length  = 16
  special = false
}

# RDS PostgreSQL instance
resource "aws_db_instance" "main" {
  identifier           = "${lower(var.project_name)}-${var.environment}-db"
  allocated_storage    = var.db_allocated_storage
  storage_type         = var.db_storage_type
  engine               = "postgres"
  engine_version       = "15.10" # Update to the desired version
  instance_class       = var.db_instance_class
  db_name              = var.db_name
  username             = var.db_username
  password             = var.db_password != "" ? var.db_password : random_password.db_password[0].result
  parameter_group_name = aws_db_parameter_group.main.name
  db_subnet_group_name = aws_db_subnet_group.main.name

  vpc_security_group_ids = [var.db_security_group_id]

  multi_az                = var.db_multi_az
  backup_retention_period = var.db_backup_retention_period
  deletion_protection     = var.db_deletion_protection
  skip_final_snapshot     = var.db_skip_final_snapshot
  apply_immediately       = var.db_apply_immediately

  # If you need enhanced monitoring
  monitoring_interval = 0 # Set to 0 to disable enhanced monitoring (cost saving)

  # If you need performance insights
  performance_insights_enabled = false # Set to false for cost savings

  # If you need encryption
  storage_encrypted = true # Always enable encryption for security

  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Environment = var.environment
  }

  # Prevent deletion impact by changes to tags
  lifecycle {
    ignore_changes = [tags]
  }
}