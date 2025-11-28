# modules/frontend/main.tf
# This file creates the infrastructure for hosting a static React website

# ==============================================================================
# S3 BUCKET - Stores the React build files
# ==============================================================================

# Main S3 bucket for the frontend application
resource "aws_s3_bucket" "frontend" {
  bucket = "${lower(var.project_name)}-${var.environment}-frontend"

  # Example: "tiktimer-prod-frontend"
  # lower() ensures bucket name is lowercase (S3 requirement)

  tags = {
    Name        = "${var.project_name}-${var.environment}-frontend"
    Environment = var.environment
    Purpose     = "Static website hosting"
  }
}

# ------------------------------------------------------------------------------
# Bucket Ownership Controls
# ------------------------------------------------------------------------------
# This ensures the bucket owner has full control over objects
# Important when CloudFront uploads logs or when using cross-account access

resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }

  # Why? If CloudFront writes logs, we want to own those files
}

# ------------------------------------------------------------------------------
# Public Access Block
# ------------------------------------------------------------------------------
# IMPORTANT: We keep the bucket private!
# Only CloudFront can access it (via Origin Access Identity we'll create below)

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  # Block all public access settings
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  # Security best practice: Never make the bucket public
  # Users access via CloudFront, not S3 directly
}

# ------------------------------------------------------------------------------
# Server-Side Encryption
# ------------------------------------------------------------------------------
# Encrypts files at rest in S3 (even though they're public HTML/JS)
# Good security practice and often required for compliance

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"  # AWS-managed encryption keys
    }
  }

  # Note: We use AES256 (free) instead of KMS (costs money)
  # For static files, AES256 is sufficient
}

# ------------------------------------------------------------------------------
# Versioning (Optional)
# ------------------------------------------------------------------------------
# We disable versioning for frontend files since we only need latest version
# Each deployment overwrites the previous one

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Disabled"
  }

  # Why disabled?
  # - Saves storage costs
  # - Git already versions our source code
  # - We can rollback by redeploying an older build
}

# ==============================================================================
# CLOUDFRONT ORIGIN ACCESS IDENTITY
# ==============================================================================
# This is the "key" that allows CloudFront to access the private S3 bucket
# Think of it like a service account specifically for CloudFront

resource "aws_cloudfront_origin_access_identity" "frontend" {
  comment = "OAI for ${var.project_name} ${var.environment} frontend"

  # CloudFront will use this identity to authenticate with S3
}

# ------------------------------------------------------------------------------
# S3 Bucket Policy - Grant CloudFront Access
# ------------------------------------------------------------------------------
# This policy says: "Allow CloudFront (via OAI) to read all objects"

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAI"
        Effect = "Allow"

        # Who can access? The CloudFront OAI we created above
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn
        }

        # What can they do? Read objects
        Action = "s3:GetObject"

        # Which objects? Everything in the bucket
        Resource = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  # Result: CloudFront can read files, but no one else can
  # The bucket stays private to the internet
}

# ==============================================================================
# CLOUDFRONT DISTRIBUTION - The CDN that serves your React app globally
# ==============================================================================

resource "aws_cloudfront_distribution" "frontend" {
  # Human-readable comment
  comment = "${var.project_name} ${var.environment} frontend distribution"

  # Enable the distribution (set to false to disable without destroying)
  enabled = true

  # This is critical for React Router!
  # When enabled, CloudFront serves index.html for 404s
  # React Router then handles the routing client-side
  default_root_object = "index.html"

  # Price class determines which edge locations are used
  # PriceClass_100 = North America & Europe (cheapest, covers most users)
  # PriceClass_200 = + Asia, Middle East, Africa
  # PriceClass_All = All edge locations worldwide
  price_class = "PriceClass_100"

  # HTTP/2 is faster - allows multiplexing requests
  http_version = "http2and3"

  # Support IPv6 addresses
  is_ipv6_enabled = true

  # ------------------------------------------------------------------------------
  # ORIGIN - Where CloudFront fetches files from (our S3 bucket)
  # ------------------------------------------------------------------------------

  origin {
    # Unique ID for this origin (can have multiple origins)
    origin_id   = "S3-${aws_s3_bucket.frontend.id}"

    # The S3 bucket's regional domain name
    # Example: tiktimer-prod-frontend.s3.us-east-1.amazonaws.com
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name

    # Connect CloudFront to S3 using the OAI (the "key" we created)
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.frontend.cloudfront_access_identity_path
      # Format: "origin-access-identity/cloudfront/XXXXX"
    }
  }

  # ------------------------------------------------------------------------------
  # DEFAULT CACHE BEHAVIOR - How CloudFront handles requests
  # ------------------------------------------------------------------------------

  default_cache_behavior {
    # Which origin to use (we only have one)
    target_origin_id = "S3-${aws_s3_bucket.frontend.id}"

    # Allowed HTTP methods
    # GET, HEAD = Read-only (static site)
    # OPTIONS = CORS preflight requests
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    # Viewer Protocol Policy - Force HTTPS!
    # redirect-to-https = HTTP requests get 301 redirect to HTTPS
    # https-only = Reject HTTP entirely
    viewer_protocol_policy = "redirect-to-https"

    # Caching settings - Use AWS managed policy
    # This is the modern way (vs manually configuring TTLs)
    cache_policy_id = data.aws_cloudfront_cache_policy.caching_optimized.id

    # CORS - Allow all origins to fetch resources
    # Important for fonts, API calls, etc.
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.cors_s3.id

    # Compress files for faster delivery
    # Gzip/Brotli compression for text files
    compress = true
  }

  # ------------------------------------------------------------------------------
  # CUSTOM ERROR RESPONSES - Critical for Single Page Applications!
  # ------------------------------------------------------------------------------
  # React Router Problem:
  # - User visits /create directly
  # - CloudFront looks for /create in S3(doesn't exist)
  # - CloudFront returns 404
  #
  # Solution:
  # - When CloudFront gets 404 from S3, return index.html instead
  # - React Router loads and handles /create client-side

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 300  # Cache the 404→200 mapping for 5 minutes
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 300
  }

  # ------------------------------------------------------------------------------
  # RESTRICTIONS - Geo-blocking (if needed)
  # ------------------------------------------------------------------------------
  # For now, allow all countries
  # You can restrict by country code if needed (e.g., GDPR compliance)

  restrictions {
    geo_restriction {
      restriction_type = "none"
      # To block: restriction_type = "blacklist", locations = ["CN", "RU"]
      # To allow only: restriction_type = "whitelist", locations = ["US", "CA"]
    }
  }

  # ------------------------------------------------------------------------------
  # SSL CERTIFICATE - Free HTTPS via AWS Certificate Manager
  # ------------------------------------------------------------------------------

  viewer_certificate {
    # Use CloudFront's default certificate (*.cloudfront.net)
    # This is free and works out of the box
    cloudfront_default_certificate = true

    # If you had a custom domain, you'd use:
    # acm_certificate_arn = aws_acm_certificate.cert.arn
    # ssl_support_method = "sni-only"  # Free (Server Name Indication)

    # Require TLS 1.2+ (modern security)
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # Tags for organization
  tags = {
    Name        = "${var.project_name}-${var.environment}-cloudfront"
    Environment = var.environment
    Purpose     = "Frontend CDN"
  }
}

# ==============================================================================
# DATA SOURCES - Reference AWS managed cache policies
# ==============================================================================
# AWS provides optimized cache policies - we don't need to create our own!

data "aws_cloudfront_cache_policy" "caching_optimized" {
  # AWS Managed policy: CachingOptimized
  # Caches based on query strings, headers, and cookies
  # Good for most static sites
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_origin_request_policy" "cors_s3" {
  # AWS Managed policy: CORS-S3Origin
  # Forwards necessary headers for CORS
  name = "Managed-CORS-S3Origin"
}
