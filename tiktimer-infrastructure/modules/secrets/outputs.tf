output "db_secret_arn" {
  description = "ARN of the database credentials secret — passed to the compute module for ECS secrets injection"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "db_secret_name" {
  description = "Name of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.name
}

output "app_secret_arn" {
  description = "ARN of the application secrets (JWT key, TikTok credentials) — passed to the compute module for ECS secrets injection"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "app_secret_name" {
  description = "Name of the application secrets"
  value       = aws_secretsmanager_secret.app_secrets.name
}
