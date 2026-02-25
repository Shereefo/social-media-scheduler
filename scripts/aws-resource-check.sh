#!/bin/bash
# scripts/aws-resource-check.sh
# Simple AWS resource inventory for TikTimer infrastructure
# Demonstrates basic AWS CLI usage and cloud resource management

# Configuration
REGION=${AWS_REGION:-us-east-2}
PROJECT_NAME="tiktimer"
ENVIRONMENT=${ENVIRONMENT:-dev}

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}TikTimer AWS Resource Check${NC}"
    echo "==================================="
    echo "Region: $REGION"
    echo "Project: $PROJECT_NAME"
    echo "Environment: $ENVIRONMENT"
    echo "Timestamp: $(date)"
    echo ""
}

check_aws_setup() {
    echo -e "${BLUE}[INFO] Checking AWS CLI Setup...${NC}"

    # Check if AWS CLI is installed
    if ! command -v aws >/dev/null 2>&1; then
        echo -e "${RED}[ERROR] AWS CLI not installed${NC}"
        echo "[INFO] Install with: pip install awscli"
        exit 1
    fi

    echo "[SUCCESS] AWS CLI is installed"

    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        echo -e "${RED}[ERROR] AWS credentials not configured${NC}"
        echo "[INFO] Configure with: aws configure"
        exit 1
    fi

    # Get current AWS account info
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --query Arn --output text)

    echo "[SUCCESS] AWS credentials configured"
    echo "  Account ID: $ACCOUNT_ID"
    echo "  Identity: $USER_ARN"
    echo ""
}

check_s3_buckets() {
    echo -e "${BLUE}[INFO] Checking S3 Buckets...${NC}"

    # List all S3 buckets and filter for TikTimer-related ones
    BUCKETS=$(aws s3api list-buckets --query 'Buckets[?contains(Name, `tiktimer`) || contains(Name, `TikTimer`)].Name' --output text 2>/dev/null)

    if [ -n "$BUCKETS" ] && [ "$BUCKETS" != "None" ]; then
        echo "Found TikTimer S3 buckets:"
        for bucket in $BUCKETS; do
            echo "  - $bucket"

            # Get bucket region
            BUCKET_REGION=$(aws s3api get-bucket-location --bucket "$bucket" --query 'LocationConstraint' --output text 2>/dev/null || echo "us-east-1")
            if [ "$BUCKET_REGION" = "None" ]; then
                BUCKET_REGION="us-east-1"
            fi
            echo "      Region: $BUCKET_REGION"

            # Get bucket size (simplified - just object count)
            OBJECT_COUNT=$(aws s3api list-objects-v2 --bucket "$bucket" --query 'KeyCount' --output text 2>/dev/null || echo "0")
            echo "      Objects: $OBJECT_COUNT"
        done
    else
        echo -e "${YELLOW}[WARNING] No TikTimer S3 buckets found${NC}"
        echo "[INFO] Buckets may not be created yet or use different naming"
    fi
    echo ""
}

check_rds_instances() {
    echo -e "${BLUE}[INFO] Checking RDS Instances...${NC}"

    # Look for TikTimer database instances
    RDS_INSTANCES=$(aws rds describe-db-instances --region "$REGION" --query "DBInstances[?contains(DBInstanceIdentifier, '$PROJECT_NAME')].{Name:DBInstanceIdentifier,Status:DBInstanceStatus,Engine:Engine,Class:DBInstanceClass}" --output table 2>/dev/null)

    if [ -n "$RDS_INSTANCES" ] && echo "$RDS_INSTANCES" | grep -q "Name"; then
        echo "Found TikTimer RDS instances:"
        echo "$RDS_INSTANCES"
    else
        echo -e "${YELLOW}[WARNING] No TikTimer RDS instances found${NC}"
        echo "[INFO] Database may not be deployed yet"
    fi
    echo ""
}

check_ecs_resources() {
    echo -e "${BLUE}[INFO] Checking ECS Resources...${NC}"

    # Check for ECS clusters
    ECS_CLUSTERS=$(aws ecs list-clusters --region "$REGION" --query "clusterArns[?contains(@, '$PROJECT_NAME')]" --output text 2>/dev/null)

    if [ -n "$ECS_CLUSTERS" ] && [ "$ECS_CLUSTERS" != "None" ]; then
        echo "Found TikTimer ECS clusters:"
        for cluster_arn in $ECS_CLUSTERS; do
            cluster_name=$(echo "$cluster_arn" | cut -d'/' -f2)
            echo "  - $cluster_name"

            # Get cluster status
            CLUSTER_STATUS=$(aws ecs describe-clusters --region "$REGION" --clusters "$cluster_arn" --query 'clusters[0].status' --output text 2>/dev/null)
            echo "      Status: $CLUSTER_STATUS"

            # Get services in cluster
            SERVICES=$(aws ecs list-services --region "$REGION" --cluster "$cluster_arn" --query 'serviceArns' --output text 2>/dev/null)
            if [ -n "$SERVICES" ] && [ "$SERVICES" != "None" ]; then
                SERVICE_COUNT=$(echo "$SERVICES" | wc -w)
                echo "      Services: $SERVICE_COUNT"
            else
                echo "      Services: 0"
            fi
        done
    else
        echo -e "${YELLOW}[WARNING] No TikTimer ECS clusters found${NC}"
        echo "[INFO] ECS infrastructure may not be deployed yet"
    fi
    echo ""
}

check_load_balancers() {
    echo -e "${BLUE}[INFO] Checking Load Balancers...${NC}"

    # Check for Application Load Balancers
    ALBS=$(aws elbv2 describe-load-balancers --region "$REGION" --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME')].{Name:LoadBalancerName,State:State.Code,Type:Type}" --output table 2>/dev/null)

    if [ -n "$ALBS" ] && echo "$ALBS" | grep -q "Name"; then
        echo "Found TikTimer load balancers:"
        echo "$ALBS"
    else
        echo -e "${YELLOW}[WARNING] No TikTimer load balancers found${NC}"
        echo "[INFO] Load balancers may not be deployed yet"
    fi
    echo ""
}

print_summary() {
    echo -e "${BLUE}[INFO] Summary${NC}"
    echo "============"
    echo "[SUCCESS] AWS CLI configured and working"
    echo "[INFO] Resource check completed for region: $REGION"
    echo ""
    echo -e "${YELLOW}[INFO] Notes:${NC}"
    echo "- Resources may not exist if infrastructure hasn't been deployed"
    echo "- Some resources might use different naming conventions"
    echo "- Check other regions if resources are expected but not found"
    echo ""
    echo -e "${GREEN}[INFO] Next Steps:${NC}"
    echo "- Deploy infrastructure: cd tiktimer-infrastructure && terraform apply"
    echo "- Check specific resource: aws <service> describe-<resource>"
    echo "- Monitor costs: aws ce get-cost-and-usage (if Cost Explorer enabled)"
}

main() {
    print_header
    check_aws_setup
    check_s3_buckets
    check_rds_instances
    check_ecs_resources
    check_load_balancers
    print_summary
}

# Run main function
main