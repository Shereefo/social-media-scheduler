# -----------------------------------------------------------------------
# Database credentials secret
#
# Stored as a JSON blob so Secrets Manager's native RDS rotation Lambda
# can read and update individual fields (username, password, host, etc.)
# without needing to know the full connection string format.
#
# ECS will inject the full JSON as the DATABASE_CREDENTIALS env var.
# The application reads individual fields from it, or we can use a
# second secret (db_url) that stores the full connection string.
# -----------------------------------------------------------------------
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "/${var.project_name}/${var.environment}/db-credentials"
  description             = "RDS PostgreSQL credentials for ${var.project_name} ${var.environment}"
  recovery_window_in_days = var.recovery_window_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-credentials"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = var.db_host
    port     = tostring(var.db_port)
    dbname   = var.db_name
    # Full connection string for direct DATABASE_URL injection
    url = "postgresql://${var.db_username}:${var.db_password}@${var.db_host}:${var.db_port}/${var.db_name}"
  })
}

# -----------------------------------------------------------------------
# Application secrets
#
# JWT signing key and TikTok API credentials live here.
# Values are set to placeholder strings on first apply — replace them
# via the AWS Console or CLI before the first `terraform apply` of the
# full infrastructure stack.
#
# To update a secret value without Terraform:
#   aws secretsmanager put-secret-value \
#     --secret-id /<project>/<env>/app-secrets \
#     --secret-string '{"SECRET_KEY":"...","TIKTOK_CLIENT_KEY":"...","TIKTOK_CLIENT_SECRET":"..."}'
# -----------------------------------------------------------------------
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "/${var.project_name}/${var.environment}/app-secrets"
  description             = "Application secrets for ${var.project_name} ${var.environment} (JWT key, TikTok API credentials)"
  recovery_window_in_days = var.recovery_window_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-secrets"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  # Placeholder values — must be replaced before first deploy.
  # Terraform manages the secret container and IAM wiring; secret values
  # are managed out-of-band to keep them out of Terraform state entirely.
  secret_string = jsonencode({
    SECRET_KEY           = "PLACEHOLDER_REPLACE_BEFORE_DEPLOY"
    TIKTOK_CLIENT_KEY    = "PLACEHOLDER_REPLACE_BEFORE_DEPLOY"
    TIKTOK_CLIENT_SECRET = "PLACEHOLDER_REPLACE_BEFORE_DEPLOY"
  })

  # Ignore future changes to the secret value in Terraform so that
  # out-of-band updates (e.g. key rotation) are not overwritten on the
  # next terraform apply.
  lifecycle {
    ignore_changes = [secret_string]
  }
}
