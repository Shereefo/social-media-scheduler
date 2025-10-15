# Database Migration Implementation Summary
## ECS-Based Migration Solution

---

## ✅ What We Just Implemented

### **1. Migration Task Definition (Terraform)**
**File**: `tiktimer-infrastructure/modules/compute/main.tf:189-235`

Created a new ECS Fargate task definition specifically for running database migrations:
- **Task Family**: `TikTimer-dev-migration`
- **CPU**: 256 (0.25 vCPU) - minimal resources for migrations
- **Memory**: 512 MB - sufficient for Alembic
- **Command Override**: `["alembic", "upgrade", "head"]` - runs migrations instead of starting the app
- **Environment**: Same DATABASE_URL as application containers
- **Network**: Runs in same VPC/subnets as application, can reach private RDS

### **2. Terraform Outputs**
**File**: `tiktimer-infrastructure/modules/compute/outputs.tf:76-89`
**File**: `tiktimer-infrastructure/outputs.tf:74-82`

Added outputs needed by CD pipeline:
- `migration_task_family`: Task definition name for running migrations
- `app_security_group_id`: Security group ID for ECS tasks
- `app_subnet_ids`: Already existed, needed for VPC configuration

### **3. CD Pipeline Migration Job**
**File**: `.github/workflows/cd.yml:145-217`

Completely replaced the old Python-based migration with ECS task execution:
- Runs migration as Fargate task in VPC (can reach private RDS)
- Waits for task completion with 10-minute timeout
- Checks exit code to detect failures
- Fetches logs if migration fails
- Blocks deployment if migration fails

### **4. Deploy Job Dependency**
**File**: `.github/workflows/cd.yml:223`

Re-added migration as deployment dependency:
```yaml
needs: [validate, build, migrate]  # Now includes migrate again
```

---

## 📋 Steps to Test This Implementation

### **Step 1: Deploy Infrastructure**
```bash
cd tiktimer-infrastructure

# Plan to see what will be created
terraform plan

# Apply changes (creates migration task definition)
terraform apply
```

**Expected Output**:
- New resource: `module.compute.aws_ecs_task_definition.migration`
- New outputs: `migration_task_family`, `app_security_group_id`

### **Step 2: Extract New Terraform Outputs**
```bash
# Get values for GitHub Secrets
terraform output -raw migration_task_family
# Output: TikTimer-dev-migration

terraform output -raw app_security_group_id
# Output: sg-xxxxxxxxxxxxxxxxx

terraform output -json app_subnet_ids
# Output: ["subnet-xxx", "subnet-yyy", "subnet-zzz"]
```

### **Step 3: Add GitHub Secrets**
```bash
# Using gh CLI
gh secret set MIGRATION_TASK_FAMILY --body "$(terraform output -raw migration_task_family)"

gh secret set APP_SECURITY_GROUP --body "$(terraform output -raw app_security_group_id)"

# Format subnet IDs as comma-separated string (remove brackets and quotes)
SUBNETS=$(terraform output -json app_subnet_ids | jq -r 'join(",")')
gh secret set APP_SUBNET_IDS --body "$SUBNETS"

# Verify secrets were added
gh secret list
```

**Or add manually via GitHub UI**:
1. Go to: https://github.com/Shereefeo/social-media-scheduler/settings/secrets/actions
2. Add new secrets:
   - `MIGRATION_TASK_FAMILY` = `TikTimer-dev-migration`
   - `APP_SECURITY_GROUP` = `sg-xxxxxxxxxxxxxxxxx` (from terraform output)
   - `APP_SUBNET_IDS` = `subnet-xxx,subnet-yyy,subnet-zzz` (comma-separated, no spaces)

### **Step 4: Commit and Push Changes**
```bash
git add .github/workflows/cd.yml
git add tiktimer-infrastructure/

git commit -m "Implement ECS-based database migrations

- Add migration task definition to Terraform
- Update CD pipeline to run migrations via ECS Fargate
- Re-enable migration dependency for deployment
- Migrations now run in VPC with access to private RDS"

git push origin main
```

### **Step 5: Monitor Pipeline Execution**
1. Go to: https://github.com/Shereefeo/social-media-scheduler/actions
2. Watch the "TikTimer Dev CD Pipeline" workflow
3. Check each job:
   - ✅ **Validate**: Should pass
   - ✅ **Build**: Should build and push Docker image
   - ⏳ **Migrate**: NEW - Should run ECS migration task
   - ⏳ **Deploy**: Should deploy containers after migrations complete

### **Step 6: Verify Migration Logs**
If migration succeeds:
```bash
# View ECS migration logs
aws logs tail /ecs/TikTimer-dev-cluster \
  --follow \
  --filter-pattern "migration" \
  --format short
```

If migration fails:
- Check GitHub Actions logs for error details
- View CloudWatch logs for full migration output
- Check ECS console for task status

### **Step 7: Verify Database Schema**
```bash
# Connect to RDS from ECS task
aws ecs execute-command \
  --cluster TikTimer-dev-cluster \
  --task <task-id> \
  --container tiktimer-app \
  --interactive \
  --command "/bin/bash"

# Inside container:
psql $DATABASE_URL

# Check Alembic version
SELECT * FROM alembic_version;

# List tables
\dt

# Exit
\q
exit
```

---

## 🔍 How It Works

### **Architecture Flow**

```
┌─────────────────────┐
│  GitHub Actions     │
│  (CD Pipeline)      │
└──────────┬──────────┘
           │
           │ 1. Trigger migration
           ▼
┌─────────────────────────────────┐
│  ECS Fargate                    │
│  Migration Task                 │
│  - Image: tiktimer-app:latest   │
│  - Command: alembic upgrade head│
│  - Network: App subnets (VPC)   │
│  - Security: App security group │
└──────────┬──────────────────────┘
           │
           │ 2. Connect via VPC
           ▼
┌─────────────────────────┐
│  RDS PostgreSQL         │
│  (Private Subnets)      │
│  - tiktimer-dev-db      │
│  - Security Group       │
└─────────────────────────┘
           │
           │ 3. Execute migrations
           ▼
┌─────────────────────────┐
│  Database Schema        │
│  - Tables created       │
│  - Alembic version set  │
└─────────────────────────┘
```

### **Why This Works**

1. **Network Access**: ECS task runs in same VPC/subnets as application, has access to private RDS
2. **Security**: Uses same security group as application, already allowed in database security group
3. **Environment Parity**: Same Docker image, same DATABASE_URL, same environment as production app
4. **No External Access**: No need for public database access or bastion hosts
5. **Logs**: CloudWatch Logs capture all migration output for debugging

---

## 🐛 Troubleshooting

### **Issue: Migration task not found**
**Error**: `ClientException: Unable to describe task definition: TikTimer-dev-migration`

**Solution**:
```bash
# Verify task definition exists
aws ecs list-task-definitions --family-prefix TikTimer-dev-migration

# If missing, re-run terraform apply
cd tiktimer-infrastructure
terraform apply
```

### **Issue: Network timeout**
**Error**: `Connection timed out` or `Could not connect to server`

**Solution**:
```bash
# Verify security group rules
aws ec2 describe-security-groups \
  --group-ids <app-security-group-id>

# Check that DB security group allows inbound from app security group
aws ec2 describe-security-groups \
  --group-ids <db-security-group-id>

# Should see ingress rule like:
# Source: sg-xxxxxxxxxxxxxxxxx (app security group)
# Port: 5432
```

### **Issue: Authentication failure**
**Error**: `password authentication failed for user "postgres"`

**Solution**:
```bash
# Verify DATABASE_URL in task definition
aws ecs describe-task-definition \
  --task-definition TikTimer-dev-migration \
  --query 'taskDefinition.containerDefinitions[0].environment'

# Should contain DATABASE_URL with correct password
# If wrong, update main.tf line 161 and re-apply terraform
```

### **Issue: Migration task fails with exit code 1**
**Check migration logs**:
```bash
# Get recent migration task ARN
TASK_ARN=$(aws ecs list-tasks \
  --cluster TikTimer-dev-cluster \
  --family TikTimer-dev-migration \
  --query 'taskArns[0]' \
  --output text)

# Get task ID
TASK_ID=$(echo $TASK_ARN | awk -F/ '{print $NF}')

# View logs
aws logs tail /ecs/TikTimer-dev-cluster \
  --log-stream-names "migration/migration/$TASK_ID" \
  --format short
```

---

## 📊 Expected Results

### **Successful Migration**
```
✅ Build Docker Image
✅ Database Migration
   └─ Migration task started: arn:aws:ecs:us-east-2:xxx:task/TikTimer-dev-cluster/abc123
   └─ Waiting for migration to complete...
   └─ Migration task finished with exit code: 0
   └─ ✅ Database migration completed successfully
✅ Deploy to ECS
✅ Health Check
```

### **Database After Migration**
```sql
-- Should have tables created by Alembic
\dt
          List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | alembic_version | table | postgres
 public | users           | table | postgres
 public | posts           | table | postgres
 public | social_accounts | table | postgres

-- Alembic version should be set
SELECT * FROM alembic_version;
 version_num
-------------
 <latest_revision_id>
```

---

## 🎯 What's Next After Migration Works

### **Priority 1: Implement Health Check Endpoint**
**File**: Backend FastAPI application

```python
@app.get("/health")
async def health_check():
    """Health endpoint for ALB"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unavailable")
```

### **Priority 2: Test Complete Deployment**
```bash
# After health endpoint is implemented
git add app/main.py
git commit -m "Add health check endpoint"
git push origin main

# Wait for deployment
# Test health check
curl http://TikTimer-dev-alb-xxx.us-east-2.elb.amazonaws.com/health
# Should return: {"status":"healthy","database":"connected"}
```

### **Priority 3: Add Smoke Tests**
Update `.github/workflows/cd.yml` to add post-deployment verification:
```yaml
smoke-test:
  needs: [deploy]
  steps:
    - name: Test Health Endpoint
      run: curl -f ${{ secrets.ALB_DNS }}/health
    - name: Test API Root
      run: curl -f ${{ secrets.ALB_DNS }}/
```

---

## 📝 Summary

### **Changes Made**
- ✅ Created ECS migration task definition in Terraform
- ✅ Added Terraform outputs for migration configuration
- ✅ Updated CD pipeline to use ECS-based migrations
- ✅ Re-enabled migration dependency in deploy job
- ✅ Added comprehensive error handling and logging

### **Benefits of This Approach**
1. **Secure**: No public database access required
2. **Reliable**: Same environment as production app
3. **Debuggable**: CloudWatch logs capture all output
4. **Scalable**: Works for any database size
5. **Fast**: Runs in AWS, no network latency

### **Remaining Work**
1. Deploy infrastructure with new migration task
2. Add GitHub Secrets for migration configuration
3. Test migration execution via CD pipeline
4. Implement health check endpoint in application
5. Verify complete end-to-end deployment

---

## 🔗 Related Documentation

- **Main Implementation Notes**: [CICD_IMPLEMENTATION_NOTES.md](./CICD_IMPLEMENTATION_NOTES.md)
- **Development Session**: [DEVELOPMENT_SESSION_SUMMARY.md](./DEVELOPMENT_SESSION_SUMMARY.md)
- **AWS Blog**: [Running Database Migrations as ECS Tasks](https://aws.amazon.com/blogs/containers/running-database-migrations-as-ecs-tasks/)
- **Alembic Docs**: [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

---

*This implementation follows AWS best practices for running database migrations in containerized applications, ensuring secure, reliable, and debuggable schema management.*
