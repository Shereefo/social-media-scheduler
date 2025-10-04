#!/bin/bash

# Script to extract Terraform outputs and display GitHub Secrets configuration
# Run this after 'terraform apply' completes successfully

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TF_DIR="$PROJECT_ROOT/tiktimer-infrastructure"

echo "========================================"
echo "  GitHub Secrets Configuration Helper"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -d "$TF_DIR" ]; then
    echo "Error: Terraform directory not found at $TF_DIR"
    exit 1
fi

cd "$TF_DIR"

# Check if terraform state exists
if ! terraform state list &> /dev/null; then
    echo "Error: No Terraform state found. Please run 'terraform apply' first."
    exit 1
fi

echo "Extracting values from Terraform outputs..."
echo ""

# Extract DB endpoint (remove port suffix to get just the host)
DB_ENDPOINT=$(terraform output -raw db_instance_endpoint 2>/dev/null || echo "")
if [ -n "$DB_ENDPOINT" ]; then
    # Remove :5432 from the endpoint to get just the hostname
    DB_HOST="${DB_ENDPOINT%:*}"
else
    echo "Warning: Could not retrieve db_instance_endpoint"
    DB_HOST="NOT_FOUND"
fi

# Extract DB password
DB_PASSWORD=$(terraform output -raw db_password 2>/dev/null || echo "NOT_FOUND")

# Extract AWS region
AWS_REGION=$(grep 'default.*us-east' "$TF_DIR/variables.tf" | head -1 | sed 's/.*"\(.*\)"/\1/' || echo "us-east-2")

echo "========================================"
echo "  Required GitHub Secrets"
echo "========================================"
echo ""
echo "Go to: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/settings/secrets/actions"
echo ""
echo "Add the following secrets:"
echo ""
echo "1. AWS_ACCESS_KEY_ID"
echo "   Value: <Your AWS Access Key ID>"
echo "   (Get from: aws configure get aws_access_key_id)"
echo ""
echo "2. AWS_SECRET_ACCESS_KEY"
echo "   Value: <Your AWS Secret Access Key>"
echo "   (Get from: aws configure get aws_secret_access_key)"
echo ""
echo "3. DB_HOST"
echo "   Value: $DB_HOST"
echo ""
echo "4. DB_PASSWORD"
echo "   Value: $DB_PASSWORD"
echo ""
echo "========================================"
echo "  Quick Copy Commands (macOS)"
echo "========================================"
echo ""
echo "# Copy DB_HOST to clipboard:"
echo "echo -n '$DB_HOST' | pbcopy"
echo ""
echo "# Copy DB_PASSWORD to clipboard:"
echo "echo -n '$DB_PASSWORD' | pbcopy"
echo ""
echo "========================================"
echo "  Using GitHub CLI (Recommended)"
echo "========================================"
echo ""
echo "If you have 'gh' CLI installed and authenticated:"
echo ""
echo "gh secret set DB_HOST --body '$DB_HOST'"
echo "gh secret set DB_PASSWORD --body '$DB_PASSWORD'"
echo ""
echo "For AWS credentials (if using same as local):"
echo "gh secret set AWS_ACCESS_KEY_ID --body \"\$(aws configure get aws_access_key_id)\""
echo "gh secret set AWS_SECRET_ACCESS_KEY --body \"\$(aws configure get aws_secret_access_key)\""
echo ""
echo "========================================"
echo "  Other Useful Outputs"
echo "========================================"
echo ""
echo "Application Load Balancer DNS:"
echo "  $(terraform output -raw alb_dns_name 2>/dev/null || echo 'NOT_FOUND')"
echo ""
echo "ECR Repository URL:"
echo "  $(terraform output -raw ecr_repository_url 2>/dev/null || echo 'NOT_FOUND')"
echo ""
echo "ECS Cluster ID:"
echo "  $(terraform output -raw ecs_cluster_id 2>/dev/null || echo 'NOT_FOUND')"
echo ""
echo "========================================"
echo ""
