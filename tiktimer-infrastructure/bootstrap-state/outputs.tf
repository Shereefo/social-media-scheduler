output "state_bucket_name" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.tf_state.id
}

output "lock_table_name" {
  description = "DynamoDB lock table for Terraform state locking"
  value       = aws_dynamodb_table.tf_locks.name
}
