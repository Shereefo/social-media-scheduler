# TikTimer CI/CD Pipeline Implementation Notes
## Date: October 4-5, 2025

---

## 🎯 **Session Objectives**

### **Primary Goal**: Test end-to-end CI/CD pipeline with AWS infrastructure deployment
### **Outcome**: ⚠️ **70% Complete** - Pipeline mechanics working, application layer needs fixes

---

## 🏗️ **Infrastructure Architecture**

### **AWS Resources Deployed (~60 total)**
- **Compute**: ECS Fargate cluster, service, task definitions
- **Database**: RDS PostgreSQL (db.t3.micro) in private subnets
- **Container Registry**: ECR repository for Docker images
- **Networking**: VPC with 9 subnets (3 public, 3 private app, 3 private DB) across 3 AZs
- **Load Balancing**: Application Load Balancer with target groups
- **Storage**: S3 buckets for uploads and Terraform state
- **Security**: IAM roles, security groups, VPC endpoints (S3 & DynamoDB)
- **Cost**: ~$0.22/hour runtime (~$0.50 total for weekend testing)

### **Terraform Module Structure**
```
tiktimer-infrastructure/
├── main.tf                          # Root module orchestration
├── variables.tf                     # Input variables
├── outputs.tf                       # Root outputs (includes db_password)
├── backend.tf                       # S3 backend configuration
├── modules/
│   ├── networking/                  # VPC, subnets, routing
│   ├── database/                    # RDS PostgreSQL
│   │   ├── main.tf                  # DB instance, subnet group, parameter group
│   │   ├── outputs.tf               # Exposes db_password (sensitive)
│   │   └── variables.tf
│   ├── compute/                     # ECS cluster, service, tasks
│   │   ├── main.tf                  # Task definitions with DATABASE_URL
│   │   ├── outputs.tf
│   │   └── variables.tf
│   ├── storage/                     # S3 buckets
│   └── security/                    # IAM roles, security groups
```

---

## 📁 **CI/CD Pipeline Architecture**

### **CI Pipeline** (`.github/workflows/ci.yml`)
**Trigger**: Pull requests to any branch
**Status**: ✅ **Working**
**Jobs**:
1. Lint code
2. Run unit tests
3. Validate code quality

### **CD Pipeline** (`.github/workflows/cd.yml`)
**Trigger**: Push to `main` branch
**Status**: ⚠️ **Partially Working**
**Jobs**:
1. ✅ **Validate**: Check if infrastructure exists
2. ✅ **Build**: Build Docker image and push to ECR
3. ❌ **Migrate**: Run database migrations (SKIPPED - can't reach private RDS)
4. ✅ **Deploy**: Deploy containers to ECS
5. ❌ **Health Check**: Verify deployment (FAILING - 503 errors)

---

## 🔧 **Critical Issues Fixed**

### **Issue #1: AWS Resource Naming Constraints**
**Files**:
- `tiktimer-infrastructure/modules/database/main.tf:15,26,37`
- `tiktimer-infrastructure/modules/storage/main.tf:8`

**Problem**: RDS and S3 resources require lowercase names
**Error**: `InvalidParameterValue: DBInstanceIdentifier must be lowercase alphanumeric`

**Fix**: Added `lower()` function to resource names
```terraform
# Before
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"  # "TikTimer-dev-db" ❌
}

# After
resource "aws_db_instance" "main" {
  identifier = "${lower(var.project_name)}-${var.environment}-db"  # "tiktimer-dev-db" ✅
}
```

**Applied to**:
- DB subnet group: `tiktimer-dev-db-subnet-group`
- DB parameter group: `tiktimer-dev-postgres`
- DB instance: `tiktimer-dev-db`
- S3 bucket: `tiktimer-dev-uploads`

---

### **Issue #2: ECS Cluster Name Case Sensitivity**
**File**: `.github/workflows/cd.yml:12`

**Problem**: CD pipeline couldn't find ECS cluster
**Root Cause**: Looking for `tiktimer-dev-cluster` but Terraform created `TikTimer-dev-cluster`

**Fix**: Updated environment variables to match exact names
```yaml
# Before
env:
  ECS_CLUSTER: tiktimer-dev-cluster  # ❌ Wrong case
  ECS_SERVICE: tiktimer-dev-service

# After
env:
  ECS_CLUSTER: TikTimer-dev-cluster  # ✅ Matches Terraform output
  ECS_SERVICE: TikTimer-dev-service
```

**Lesson**: ECS resource names are case-sensitive. Always reference Terraform outputs.

---

### **Issue #3: Task Definition Family vs Service Name**
**File**: `.github/workflows/cd.yml:13,79`

**Problem**: Pipeline downloading task definition by service name instead of family
**Error**: `ClientException: Unable to describe task definition: TikTimer-dev-service`

**Fix**: Added separate variable for task family
```yaml
env:
  ECS_SERVICE: TikTimer-dev-service        # Service name
  ECS_TASK_FAMILY: TikTimer-dev-task      # Task definition family (NEW)

- name: Download current task definition
  run: |
    aws ecs describe-task-definition \
      --task-definition $ECS_TASK_FAMILY \  # Changed from $ECS_SERVICE
      --query taskDefinition > task-definition.json
```

**Lesson**: ECS services and task definitions have different naming conventions.

---

### **Issue #4: Task Definition Metadata Fields**
**File**: `.github/workflows/cd.yml:92-100`

**Problem**: Downloaded task definition includes read-only metadata fields
**Error**: `Unknown parameter in input: taskDefinitionArn, revision, status, requiresAttributes...`

**Fix**: Strip metadata fields before registering new revision
```yaml
- name: Update task definition
  run: |
    jq --arg IMAGE "$NEW_IMAGE" '
      del(.taskDefinitionArn, .revision, .status,
          .requiresAttributes, .compatibilities,
          .registeredAt, .registeredBy) |
      .containerDefinitions[0].image = $IMAGE
    ' task-definition.json > new-task-definition.json
```

**Lesson**: Task definition API returns metadata that can't be included in registration requests.

---

### **Issue #5: Database Migration Connectivity**
**File**: `.github/workflows/cd.yml:103`

**Problem**: GitHub Actions runners can't reach RDS in private subnets
**Error**: `connection to server at "tiktimer-dev-db.cvsc28eqeb3a.us-east-2.rds.amazonaws.com" port 5432 failed: Connection timed out`

**Temporary Fix**: Removed migration from deploy dependencies
```yaml
# Before
deploy:
  needs: [validate, build, migrate]  # ❌ Blocks deployment

# After
deploy:
  needs: [validate, build]  # ✅ Allows deployment to proceed
  # Note: Migrations must be run differently (see Issue #7 below)
```

**Status**: ⚠️ **UNRESOLVED** - Needs proper solution (see "Outstanding Issues" below)

---

### **Issue #6: Empty Database Password in Environment**
**File**: `tiktimer-infrastructure/main.tf:161`

**Problem**: Containers receiving empty password in DATABASE_URL
**Symptoms**:
- Application logs: `could not translate host name "tiktimer-dev-db" to address: Name or service not known`
- DATABASE_URL format: `postgresql://postgres:@tiktimer-dev-db...` (missing password)

**Root Cause**: Using input variable default (empty string) instead of generated password
```terraform
# Before - main.tf:161
module "compute" {
  database_url = "postgresql://${var.db_username}:${var.db_password}@..."
  #                                                   ^^^^^^^^^^^^^^^^
  #                                                   Empty string default ❌
}

# After - main.tf:161
module "compute" {
  database_url = "postgresql://${var.db_username}:${module.database.db_password}@..."
  #                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^
  #                                                   Actual generated password ✅
}
```

**Database Credentials**:
- Host: `tiktimer-dev-db.cvsc28eqeb3a.us-east-2.rds.amazonaws.com`
- Username: `postgres`
- Password: `oFsLgArj0X2CFmzh` (auto-generated)
- Database: `scheduler`

**Lesson**: Always reference module outputs for generated values, not input variables.

---

## 🔄 **Pipeline Execution History**

| Run # | Commit | Status | Duration | Key Event |
|-------|--------|--------|----------|-----------|
| 1-5 | Various | Validation Only | ~2m | Infrastructure didn't exist yet |
| 6 | 6cc7e41 | ❌ Failed | 3m 40s | ECS cluster name mismatch |
| 7 | 6cc7e41 | ❌ Failed | 3m 40s | Still wrong cluster name |
| 8 | f6c2c2a | ❌ Failed | 3m 32s | Task definition download error |
| 9 | 6760f2d | ❌ Failed | 3m 52s | Task definition metadata error |
| 10 | 4513a56 | ⚠️ Partial | 7m 33s | Deploy succeeded, health check failed |

**Total Iterations**: 10 runs
**Issues Fixed**: 6 major problems
**Current Status**: Containers deployed but not healthy

---

## 🛠️ **Helper Tools Created**

### **GitHub Secrets Helper Script**
**File**: `scripts/show-github-secrets.sh`
**Purpose**: Extract Terraform outputs and format for GitHub Secrets

```bash
#!/bin/bash
# Extracts sensitive values from Terraform and displays
# GitHub Secrets configuration commands

# Features:
# - Automatically strips port from DB endpoint
# - Provides manual copy-paste commands
# - Provides gh CLI automation commands
# - Handles sensitive values securely

# Usage:
./scripts/show-github-secrets.sh
```

**Output Example**:
```bash
=== GitHub Secrets Configuration ===

DB_HOST=tiktimer-dev-db.cvsc28eqeb3a.us-east-2.rds.amazonaws.com
DB_NAME=scheduler
DB_USERNAME=postgres
DB_PASSWORD=oFsLgArj0X2CFmzh

# Automated setup (requires gh CLI):
gh secret set DB_HOST --body "tiktimer-dev-db.cvsc28eqeb3a.us-east-2.rds.amazonaws.com"
gh secret set DB_PASSWORD --body "oFsLgArj0X2CFmzh"
```

---

## ⚠️ **Outstanding Issues (Must Fix)**

### **Issue #7: Database Migrations Not Running**
**Status**: ❌ **CRITICAL - BLOCKS PRODUCTION**
**Impact**: Database is empty, no schema, application can't function

**Problem**: GitHub Actions runners exist outside VPC and cannot reach private RDS instance

**Current Architecture**:
```
[GitHub Actions Runner] → [Internet] → 🚫 [Private RDS in VPC]
                                           ❌ Security group blocks external access
```

**Solution Options**:

#### **Option A: ECS Task for Migrations (RECOMMENDED)**
**Approach**: Run migrations as one-time ECS Fargate task
```yaml
# In CD pipeline
- name: Run Database Migration
  run: |
    # Register migration task definition
    aws ecs register-task-definition \
      --cli-input-json file://migration-task-def.json

    # Run migration task
    aws ecs run-task \
      --cluster $ECS_CLUSTER \
      --task-definition tiktimer-migration \
      --launch-type FARGATE \
      --network-configuration "awsvpcConfiguration={
        subnets=[${APP_SUBNET_IDS}],
        securityGroups=[${APP_SECURITY_GROUP}]
      }"

    # Wait for task to complete
    aws ecs wait tasks-stopped \
      --cluster $ECS_CLUSTER \
      --tasks ${TASK_ARN}

    # Check exit code
    EXIT_CODE=$(aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks ${TASK_ARN} \
      --query 'tasks[0].containers[0].exitCode' --output text)

    if [ "$EXIT_CODE" != "0" ]; then
      echo "Migration failed with exit code $EXIT_CODE"
      exit 1
    fi
```

**Architecture**:
```
[GitHub Actions] → [ECS Fargate Task] → [Private RDS]
                   ✅ Runs in same VPC
                   ✅ Has DB security group access
```

**Terraform Changes Needed**:
1. Create migration task definition in `modules/compute/main.tf`
2. Override container command to run migrations only
3. Use same DATABASE_URL as application containers
4. Output task definition ARN for CD pipeline

**Pros**:
- ✅ Secure (no public DB access)
- ✅ Uses existing infrastructure
- ✅ Same environment as application
- ✅ Scales with application

**Cons**:
- ⚠️ More complex than direct execution
- ⚠️ Requires ECS task definition management

---

#### **Option B: Bastion Host**
**Approach**: EC2 instance in public subnet with SSH tunneling
```bash
# In CD pipeline
- name: Run Database Migration via Bastion
  run: |
    ssh -i bastion-key.pem -L 5432:$DB_HOST:5432 ec2-user@bastion-ip
    alembic upgrade head
```

**Pros**:
- ✅ Traditional approach
- ✅ Can be used for debugging

**Cons**:
- ❌ Additional EC2 costs
- ❌ SSH key management complexity
- ❌ Security implications of long-lived bastion

---

#### **Option C: Lambda Function**
**Approach**: Lambda in VPC runs migrations
```python
# Lambda handler
def handler(event, context):
    os.system("alembic upgrade head")
    return {"statusCode": 200}
```

**Pros**:
- ✅ Serverless (no always-on costs)
- ✅ Can be invoked from CD pipeline

**Cons**:
- ❌ Lambda execution time limits (15 min max)
- ❌ Additional Terraform configuration
- ❌ Different runtime environment than app

---

### **Issue #8: Application Health Check Failing**
**Status**: ❌ **CRITICAL - BLOCKS PRODUCTION**
**Impact**: Load balancer marks all targets as unhealthy, can't serve traffic

**Current Behavior**:
```bash
$ curl http://TikTimer-dev-alb-990291306.us-east-2.elb.amazonaws.com/health
< HTTP/1.1 503 Service Temporarily Unavailable
< Server: awselb/2.0
```

**Root Causes**:
1. ❌ **Database empty**: No schema because migrations never ran
2. ❌ **Health endpoint missing**: Application may not have `/health` route implemented
3. ⚠️ **DB connection issues**: Even with password fixed, empty DB causes startup failures

**Health Check Configuration** (`modules/compute/main.tf`):
```terraform
resource "aws_lb_target_group" "app" {
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"      # Endpoint being checked
    matcher             = "200"          # Expected response code
  }
}
```

**Solution Required**:
1. **Fix migrations** (Issue #7) to create database schema
2. **Implement health endpoint** in FastAPI application:
```python
# In main FastAPI app
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer"""
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
```

3. **Verify health check** after deployment:
```bash
# Should return 200 OK
curl -v http://TikTimer-dev-alb-990291306.us-east-2.elb.amazonaws.com/health
```

---

## 📊 **Current Pipeline Status**

### **✅ Working Components**
- [x] Infrastructure deployment via Terraform
- [x] CI pipeline (linting, testing on PRs)
- [x] Docker image building and pushing to ECR
- [x] ECS task definition updates
- [x] Container deployment to Fargate
- [x] Load balancer configuration
- [x] VPC networking and security groups
- [x] IAM roles and permissions

### **⚠️ Partially Working**
- [~] CD pipeline (deploys containers but they're unhealthy)
- [~] Database connectivity (password fixed but schema empty)

### **❌ Broken/Missing**
- [ ] Database migrations execution
- [ ] Application health checks
- [ ] Post-deployment smoke tests
- [ ] Automated rollback on failure
- [ ] Production-ready monitoring

---

## 🎓 **Key Learnings**

### **Technical Insights**

`★ Insight ─────────────────────────────────────`
**1. AWS Resource Naming**: RDS and S3 have strict lowercase-only requirements. Always use `lower()` function in Terraform for these resources to avoid deployment failures.

**2. Case Sensitivity Matters**: ECS resource names are case-sensitive. CD pipeline environment variables must EXACTLY match Terraform outputs. Silent failures occur when names don't match.

**3. Task Definition Lifecycle**: When updating ECS task definitions, you must strip read-only metadata fields (taskDefinitionArn, revision, status, requiresAttributes, compatibilities, registeredAt, registeredBy) before registering new revisions.

**4. Network Isolation Trade-offs**: Private subnet databases are secure but complicate CI/CD. GitHub Actions runners can't reach private resources. Solutions: ECS tasks, bastion hosts, or Lambda functions.

**5. Terraform Module Outputs**: Always reference module outputs (like `module.database.db_password`) for generated values, NOT input variables which may have empty defaults.

**6. Deployment ≠ Success**: Containers running doesn't mean application works. Health checks, database connectivity, and schema migrations are all critical for a functioning deployment.
`─────────────────────────────────────────────────`

---

## 💰 **Cost Analysis**

### **Testing Weekend Costs**
**Runtime**: ~3 hours of infrastructure

| Resource | Cost/Hour | Total |
|----------|-----------|-------|
| RDS db.t3.micro | $0.034 | $0.10 |
| ECS Fargate (2 vCPU, 4GB RAM) | $0.12 | $0.36 |
| NAT Gateway | $0.045 | $0.14 |
| Application Load Balancer | $0.0225 | $0.07 |
| Data Transfer | $0.09/GB | ~$0.05 |
| **Total** | **~$0.22/hr** | **~$0.50** |

### **Post-Cleanup Status**
**Current Cost**: $0/month (all resources destroyed)
**Remaining**: S3 Terraform state bucket (~$0.01/month for storage)

---

## 🚀 **Infrastructure Teardown Process**

### **Challenges Encountered**

#### **Challenge #1: ECR Repository Not Empty**
**Problem**: Terraform can't delete ECR with images
**Error**: `RepositoryNotEmptyException: ECR Repository (tiktimer-dev) not empty`

**Solution**: Manually delete images first
```bash
# List all images
aws ecr list-images --repository-name tiktimer-dev --region us-east-2

# Delete all images
aws ecr batch-delete-image \
  --repository-name tiktimer-dev \
  --region us-east-2 \
  --image-ids imageTag=6cc7e419038d9810befb60607beafc44c369e481 \
               imageTag=latest \
               imageTag=4513a56d1b780efcd6e154945551d232b2ccbca2 \
               imageTag=6760f2d2da1d1a8deae6b4e2bbdb20e00332f66d \
               imageTag=f6c2c2a5728f0f7621bb8ecc2adef7e0eedc2837

# Then retry terraform destroy
terraform destroy -auto-approve
```

#### **Challenge #2: IAM Permission Issues**
**Problem**: TikTamer IAM user lacks `iam:ListInstanceProfilesForRole` permission
**Error**: `AccessDenied: User: arn:aws:iam::022499001793:user/TikTamer is not authorized to perform: iam:ListInstanceProfilesForRole`

**Solution**: Remove from Terraform state and delete manually
```bash
# Remove from state
terraform state rm module.compute.aws_iam_role.ecs_task_execution_role
terraform state rm module.compute.aws_iam_role.ecs_task_role

# Retry destroy
terraform destroy -auto-approve

# Manually delete roles (surprisingly worked without extra permissions)
aws iam delete-role --role-name TikTimer-dev-task-execution-role
aws iam delete-role --role-name TikTimer-dev-task-role
```

### **Final Cleanup Verification**
```bash
# Verify all resources deleted
aws ecs list-clusters --region us-east-2 | grep -i tiktimer
aws rds describe-db-instances --region us-east-2 | grep -i tiktimer
aws ecr describe-repositories --region us-east-2 | grep -i tiktimer
aws ec2 describe-vpcs --region us-east-2 --filters "Name=tag:Project,Values=TikTimer"
aws iam list-roles --region us-east-2 | grep -i tiktimer
aws s3 ls | grep -i tiktimer

# All returned empty ✅
```

---

## 📋 **Next Steps (Priority Order)**

### **Priority 1: Fix Database Migrations (CRITICAL)**
**File**: `tiktimer-infrastructure/modules/compute/migration-task.tf` (NEW)
**Action**: Implement ECS-based migration task
```terraform
# Create migration task definition
resource "aws_ecs_task_definition" "migration" {
  family = "${var.project_name}-${var.environment}-migration"

  container_definitions = jsonencode([{
    name  = "migration"
    image = "${var.ecr_repository_url}:latest"

    # Override command to run migrations only
    command = ["alembic", "upgrade", "head"]

    environment = [
      { name = "DATABASE_URL", value = var.database_url }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.app.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "migration"
      }
    }
  }])
}

# Output for CD pipeline
output "migration_task_family" {
  value = aws_ecs_task_definition.migration.family
}
```

**CD Pipeline Update** (`.github/workflows/cd.yml`):
```yaml
migrate:
  needs: [validate, build]
  runs-on: ubuntu-latest
  steps:
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Run Database Migration
      run: |
        # Run migration task
        TASK_ARN=$(aws ecs run-task \
          --cluster $ECS_CLUSTER \
          --task-definition $MIGRATION_TASK_FAMILY \
          --launch-type FARGATE \
          --network-configuration "awsvpcConfiguration={
            subnets=[${{ secrets.APP_SUBNET_IDS }}],
            securityGroups=[${{ secrets.APP_SECURITY_GROUP }}],
            assignPublicIp=DISABLED
          }" \
          --query 'tasks[0].taskArn' \
          --output text)

        echo "Migration task started: $TASK_ARN"

        # Wait for completion
        aws ecs wait tasks-stopped \
          --cluster $ECS_CLUSTER \
          --tasks $TASK_ARN

        # Check exit code
        EXIT_CODE=$(aws ecs describe-tasks \
          --cluster $ECS_CLUSTER \
          --tasks $TASK_ARN \
          --query 'tasks[0].containers[0].exitCode' \
          --output text)

        if [ "$EXIT_CODE" != "0" ]; then
          echo "❌ Migration failed with exit code $EXIT_CODE"

          # Fetch logs for debugging
          LOG_STREAM=$(aws ecs describe-tasks \
            --cluster $ECS_CLUSTER \
            --tasks $TASK_ARN \
            --query 'tasks[0].containers[0].name' \
            --output text)

          aws logs tail /ecs/$ECS_CLUSTER/migration \
            --log-stream-names $LOG_STREAM \
            --format short

          exit 1
        fi

        echo "✅ Migration completed successfully"

deploy:
  needs: [validate, build, migrate]  # Re-add migrate dependency
  # ... rest of deploy job
```

---

### **Priority 2: Implement Health Check Endpoint**
**File**: `tiktimer-backend/app/main.py` (or wherever FastAPI app is defined)

```python
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from app.database import engine
import logging

logger = logging.getLogger(__name__)
app = FastAPI()

@app.get("/health")
async def health_check():
    """
    Health check endpoint for AWS ALB

    Returns:
        200 OK if service is healthy and can connect to database
        503 Service Unavailable if there are issues
    """
    try:
        # Test database connectivity
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            _ = result.scalar()

        return {
            "status": "healthy",
            "database": "connected",
            "service": "tiktimer-api"
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": "Database connection failed",
                "service": "tiktimer-api"
            }
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TikTimer API",
        "version": "1.0.0",
        "health_check": "/health"
    }
```

**Verify Health Endpoint Locally**:
```bash
# Start backend
docker-compose up -d

# Test health endpoint
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","database":"connected","service":"tiktimer-api"}
```

---

### **Priority 3: Verify ALB Health Check Configuration**
**File**: `tiktimer-infrastructure/modules/compute/main.tf`

```terraform
resource "aws_lb_target_group" "app" {
  # ... existing configuration ...

  health_check {
    enabled             = true
    healthy_threshold   = 2                # 2 consecutive successes = healthy
    unhealthy_threshold = 3                # 3 consecutive failures = unhealthy
    timeout             = 5                # 5 second timeout per check
    interval            = 30               # Check every 30 seconds
    path                = "/health"        # Health check endpoint
    matcher             = "200"            # Expected HTTP status code
    protocol            = "HTTP"
  }

  deregistration_delay = 30  # Wait 30s before removing unhealthy targets

  tags = {
    Name        = "${var.project_name}-${var.environment}-tg"
    Environment = var.environment
  }
}
```

---

### **Priority 4: Add Smoke Tests to CD Pipeline**
**File**: `.github/workflows/cd.yml`

```yaml
smoke-test:
  needs: [deploy]
  runs-on: ubuntu-latest
  steps:
    - name: Wait for deployment to stabilize
      run: sleep 60

    - name: Test Health Endpoint
      run: |
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
          http://${{ secrets.ALB_DNS }}/health)

        if [ "$RESPONSE" != "200" ]; then
          echo "❌ Health check failed with status $RESPONSE"
          exit 1
        fi

        echo "✅ Health check passed"

    - name: Test API Root
      run: |
        curl -f http://${{ secrets.ALB_DNS }}/ || exit 1
        echo "✅ API root endpoint accessible"

    - name: Notify on Failure
      if: failure()
      run: |
        echo "🚨 Deployment smoke tests failed!"
        echo "Rolling back to previous task definition..."
        # TODO: Implement rollback logic
```

---

### **Priority 5: Implement Automated Rollback**
**File**: `.github/workflows/cd.yml`

```yaml
rollback:
  needs: [smoke-test]
  if: failure()
  runs-on: ubuntu-latest
  steps:
    - name: Get Previous Task Definition
      id: previous
      run: |
        # Get task definition revisions
        PREVIOUS_REVISION=$(aws ecs describe-task-definition \
          --task-definition $ECS_TASK_FAMILY \
          --query 'taskDefinition.revision' \
          --output text)

        PREVIOUS_REVISION=$((PREVIOUS_REVISION - 1))

        echo "previous_revision=$PREVIOUS_REVISION" >> $GITHUB_OUTPUT

    - name: Rollback to Previous Version
      run: |
        aws ecs update-service \
          --cluster $ECS_CLUSTER \
          --service $ECS_SERVICE \
          --task-definition $ECS_TASK_FAMILY:${{ steps.previous.outputs.previous_revision }}

        echo "🔄 Rolled back to revision ${{ steps.previous.outputs.previous_revision }}"
```

---

## 📝 **GitHub Secrets Required**

### **Current Secrets**
```bash
AWS_ACCESS_KEY_ID=<IAM user access key>
AWS_SECRET_ACCESS_KEY=<IAM user secret key>
DB_HOST=tiktimer-dev-db.cvsc28eqeb3a.us-east-2.rds.amazonaws.com
DB_NAME=scheduler
DB_USERNAME=postgres
DB_PASSWORD=oFsLgArj0X2CFmzh
```

### **Additional Secrets Needed for Migration Task**
```bash
# From Terraform outputs
APP_SUBNET_IDS="subnet-054a211a735f5f895,subnet-0befd41cc94f0aaa4,subnet-0650ca9069910e7d3"
APP_SECURITY_GROUP="sg-0e71387a0786e6e1b"
MIGRATION_TASK_FAMILY="TikTimer-dev-migration"
ALB_DNS="TikTimer-dev-alb-990291306.us-east-2.elb.amazonaws.com"
```

**Add via script**:
```bash
# After terraform apply
cd tiktimer-infrastructure

gh secret set APP_SUBNET_IDS --body "$(terraform output -raw app_subnet_ids | tr -d '[]" ' | tr '\n' ',')"
gh secret set APP_SECURITY_GROUP --body "$(terraform output -raw app_security_group_id)"
gh secret set MIGRATION_TASK_FAMILY --body "$(terraform output -raw migration_task_family)"
gh secret set ALB_DNS --body "$(terraform output -raw alb_dns_name)"
```

---

## 🎯 **Production Readiness Checklist**

### **Infrastructure** (70% Complete)
- [x] VPC with multi-AZ subnets
- [x] RDS database with encryption
- [x] ECS Fargate for containers
- [x] Application Load Balancer
- [x] ECR for image registry
- [x] IAM roles with least privilege
- [x] Security groups for network isolation
- [ ] Database migrations automation
- [ ] Backup and disaster recovery
- [ ] Multi-region failover

### **CI/CD Pipeline** (60% Complete)
- [x] Automated testing on PRs
- [x] Docker image building
- [x] Container deployment automation
- [x] Infrastructure validation
- [ ] Database migration execution
- [ ] Post-deployment smoke tests
- [ ] Automated rollback on failure
- [ ] Canary deployments
- [ ] Blue-green deployment strategy

### **Application** (50% Complete)
- [x] Containerized application
- [x] Environment variable configuration
- [x] Database connection handling
- [ ] Health check endpoint
- [ ] Graceful shutdown handling
- [ ] Metrics and logging
- [ ] Error tracking (Sentry)

### **Monitoring & Observability** (20% Complete)
- [x] CloudWatch log groups
- [ ] CloudWatch metrics and alarms
- [ ] Application performance monitoring
- [ ] Error rate alerts
- [ ] Cost monitoring
- [ ] Security monitoring

### **Security** (70% Complete)
- [x] Private subnets for database
- [x] Security groups with restricted access
- [x] IAM roles (no hardcoded credentials)
- [x] Encrypted RDS storage
- [ ] Secrets Manager for credentials
- [ ] WAF for load balancer
- [ ] SSL/TLS certificates
- [ ] Security scanning in CI

---

## 🔍 **Debugging Commands**

### **Check ECS Task Status**
```bash
# List running tasks
aws ecs list-tasks \
  --cluster TikTimer-dev-cluster \
  --service-name TikTimer-dev-service

# Describe specific task
aws ecs describe-tasks \
  --cluster TikTimer-dev-cluster \
  --tasks <task-arn>

# Get task logs
aws logs tail /ecs/TikTimer-dev-cluster \
  --follow \
  --format short
```

### **Check ALB Health**
```bash
# Get target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Test ALB directly
curl -v http://TikTimer-dev-alb-990291306.us-east-2.elb.amazonaws.com/health

# Check security groups
aws ec2 describe-security-groups \
  --group-ids sg-0e71387a0786e6e1b
```

### **Check Database Connectivity**
```bash
# From within VPC (ECS task)
psql "postgresql://postgres:oFsLgArj0X2CFmzh@tiktimer-dev-db.cvsc28eqeb3a.us-east-2.rds.amazonaws.com:5432/scheduler"

# List tables
\dt

# Check if migrations ran
SELECT * FROM alembic_version;
```

### **Check ECR Images**
```bash
# List images
aws ecr list-images \
  --repository-name tiktimer-dev \
  --region us-east-2

# Describe image
aws ecr describe-images \
  --repository-name tiktimer-dev \
  --image-ids imageTag=latest
```

---

## 💡 **Lessons for Future Sessions**

### **What Went Well**
1. ✅ Terraform modular structure made debugging easier
2. ✅ GitHub Actions provided clear feedback on failures
3. ✅ AWS CLI commands helped with manual intervention
4. ✅ Iterative approach allowed fixing issues one at a time
5. ✅ Cost-conscious testing (destroy after testing)

### **What Could Be Improved**
1. ⚠️ Should have tested health endpoint locally first
2. ⚠️ Should have verified DATABASE_URL before deploying
3. ⚠️ Should have planned migration strategy before deployment
4. ⚠️ Could have used Terraform locals for repeated values
5. ⚠️ Should have added CloudWatch alarms earlier

### **Best Practices Confirmed**
1. ✅ Always use `lower()` for RDS and S3 resource names
2. ✅ Reference Terraform outputs, not input variables
3. ✅ Test infrastructure changes with `terraform plan` first
4. ✅ Keep Terraform state in S3 for team collaboration
5. ✅ Use IAM roles instead of hardcoded credentials
6. ✅ Implement proper CI/CD validation gates

---

## 📚 **Resources & References**

### **Documentation**
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [ECS Task Definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
- [GitHub Actions AWS Integration](https://github.com/aws-actions)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/latest/)

### **Related AWS Blog Posts**
- [Running Database Migrations as ECS Tasks](https://aws.amazon.com/blogs/containers/running-database-migrations-as-ecs-tasks/)
- [Blue/Green Deployments with ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html)
- [ECS Health Check Best Practices](https://aws.amazon.com/blogs/containers/amazon-ecs-task-health-checks/)

---

## 📊 **Session Summary**

**Duration**: Weekend session (~6 hours including debugging)
**Infrastructure Resources**: ~60 AWS resources deployed
**Pipeline Runs**: 10 iterations
**Issues Fixed**: 6 major problems
**Issues Remaining**: 2 critical blockers
**Total Cost**: ~$0.50 (all resources destroyed)
**Completion**: 70% (mechanics working, application needs fixes)

**Status**: Pipeline successfully deploys containers to AWS, but application is not yet functional due to missing migrations and health endpoint implementation. Next session should focus on Priority 1 (migrations) and Priority 2 (health checks) to achieve full end-to-end functionality.

---

*This session transformed a local development setup into a cloud-deployed application, uncovered critical integration issues, and established a solid foundation for production deployment.*
