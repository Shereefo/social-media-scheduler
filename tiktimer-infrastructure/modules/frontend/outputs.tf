# modules/frontend/outputs.tf
# These outputs expose values that other modules or users need

# ==============================================================================
# S3 OUTPUTS
# ==============================================================================

output "bucket_id" {
  description = "The name of the S3 bucket"
  value       = aws_s3_bucket.frontend.id
  # Example: "tiktimer-prod-frontend"
  # Used by CI/CD to know where to upload files
}

output "bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = aws_s3_bucket.frontend.arn
  # Example: "arn:aws:s3:::tiktimer-prod-frontend"
  # Used for IAM policies in CI/CD
}

output "bucket_regional_domain_name" {
  description = "The bucket region-specific domain name"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
  # Example: "tiktimer-prod-frontend.s3.us-east-1.amazonaws.com"
}

# ==============================================================================
# CLOUDFRONT OUTPUTS
# ==============================================================================

output "cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.id
  # Example: "E1ABCDEFG12345"
  # Used by CI/CD to invalidate cache after deployment
}

output "cloudfront_distribution_arn" {
  description = "The ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.arn
  # Used for monitoring/alerting integrations
}

output "cloudfront_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.domain_name
  # Example: "d12345abcdef.cloudfront.net"
  # THIS IS YOUR APP'S URL! Visit this to see your deployed app
}

output "cloudfront_hosted_zone_id" {
  description = "The CloudFront Route 53 zone ID"
  value       = aws_cloudfront_distribution.frontend.hosted_zone_id
  # Used if you set up a custom domain with Route53
  # CloudFront's zone ID is always Z2FDTNDATAQYW2
}

# ==============================================================================
# DEPLOYMENT INFO
# ==============================================================================

output "deployment_info" {
  description = "Summary of deployment endpoints and commands"
  value = {
    app_url            = "https://${aws_cloudfront_distribution.frontend.domain_name}"
    s3_sync_command    = "aws s3 sync ./build s3://${aws_s3_bucket.frontend.id}/"
    invalidate_command = "aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.frontend.id} --paths '/*'"
  }
  # This creates a handy reference for how to deploy!
}
