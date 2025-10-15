# TikTimer CI/CD Quick Reference Guide
## Essential Commands and Information

---

## 📚 Documentation Index

- **[CICD_IMPLEMENTATION_NOTES.md](./CICD_IMPLEMENTATION_NOTES.md)**: Complete CI/CD session notes, all issues and fixes
- **[MIGRATION_IMPLEMENTATION_SUMMARY.md](./MIGRATION_IMPLEMENTATION_SUMMARY.md)**: Database migration implementation details
- **[DEVELOPMENT_SESSION_SUMMARY.md](./DEVELOPMENT_SESSION_SUMMARY.md)**: Frontend development session notes

---

## 🚀 Quick Start Commands

### **Deploy Infrastructure**
```bash
cd tiktimer-infrastructure
terraform init
terraform plan
terraform apply
```

### **Destroy Infrastructure**
```bash
# Delete ECR images first
aws ecr batch-delete-image \
  --repository-name tiktimer-dev \
  --region us-east-2 \
  --image-ids $(aws ecr list-images --repository-name tiktimer-dev --region us-east-2 --query 'imageIds[*]' --output json)

# Then destroy
terraform destroy -auto-approve
```

### **Configure GitHub Secrets**
```bash
cd tiktimer-infrastructure

# After terraform apply, run:
./scripts/show-github-secrets.sh

# Or manually with gh CLI:
gh secret set DB_HOST --body "$(terraform output -raw db_instance_endpoint | cut -d: -f1)"
gh secret set DB_PASSWORD --body "$(terraform output -raw db_password)"
gh secret set MIGRATION_TASK_FAMILY --body "$(terraform output -raw migration_task_family)"
gh secret set APP_SECURITY_GROUP --body "$(terraform output -raw app_security_group_id)"
gh secret set APP_SUBNET_IDS --body "$(terraform output -json app_subnet_ids | jq -r 'join(",")')"
```

---

## 🔧 AWS Resource Quick Reference

### **Infrastructure Details**
- **Region**: us-east-2 (Ohio)
- **VPC**: 10.0.0.0/16
- **Availability Zones**: 3 (us-east-2a, us-east-2b, us-east-2c)
- **Subnets**: 9 total (3 public, 3 private app, 3 private DB)

### **Key Resource Names**
```
ECS Cluster:        TikTimer-dev-cluster
ECS Service:        TikTimer-dev-service
Task Family:        TikTimer-dev-task
Migration Task:     TikTimer-dev-migration
ECR Repository:     tiktimer-dev
RDS Instance:       tiktimer-dev-db
ALB:                TikTimer-dev-alb
S3 Uploads Bucket:  tiktimer-dev-uploads
S3 State Bucket:    tiktimer-terraform-state
```

### **Database Connection**
```bash
Host:     tiktimer-dev-db.cvsc28eqeb3a.us-east-2.rds.amazonaws.com
Port:     5432
Database: scheduler
Username: postgres
Password: <from terraform output -raw db_password>

# Connection string format:
postgresql://postgres:<password>@<host>:5432/scheduler
```

---

## 🐛 Common Debugging Commands

### **Check ECS Service Status**
```bash
aws ecs describe-services \
  --cluster TikTimer-dev-cluster \
  --services TikTimer-dev-service \
  --region us-east-2
```

### **Check Running Tasks**
```bash
aws ecs list-tasks \
  --cluster TikTimer-dev-cluster \
  --region us-east-2
```

### **View Container Logs**
```bash
# Real-time logs
aws logs tail /ecs/TikTimer-dev-cluster \
  --follow \
  --region us-east-2

# Specific log stream
aws logs tail /ecs/TikTimer-dev-cluster \
  --log-stream-names "ecs/tiktimer-app/<task-id>" \
  --format short \
  --region us-east-2
```

### **Check ALB Target Health**
```bash
# Get target group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
  --names TikTimer-dev-tg \
  --region us-east-2 \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --region us-east-2
```

### **Test Application Endpoints**
```bash
# Get ALB DNS
ALB_DNS=$(cd tiktimer-infrastructure && terraform output -raw alb_dns_name)

# Test health endpoint
curl -v http://$ALB_DNS/health

# Test root endpoint
curl -v http://$ALB_DNS/

# Test with retry
for i in {1..5}; do
  echo "Attempt $i:"
  curl -s http://$ALB_DNS/health | jq
  sleep 2
done
```

### **Manual Migration Execution**
```bash
# Run migration task manually
aws ecs run-task \
  --cluster TikTimer-dev-cluster \
  --task-definition TikTimer-dev-migration \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[$(cd tiktimer-infrastructure && terraform output -json app_subnet_ids | jq -r 'join(","))],
    securityGroups=[$(cd tiktimer-infrastructure && terraform output -raw app_security_group_id)],
    assignPublicIp=DISABLED
  }" \
  --region us-east-2
```

---

## 🔍 Troubleshooting Checklist

### **Pipeline Failing?**
1. ✅ Check GitHub Actions logs: https://github.com/Shereefeo/social-media-scheduler/actions
2. ✅ Verify GitHub Secrets are set correctly
3. ✅ Ensure infrastructure is deployed (`terraform apply`)
4. ✅ Check ECS cluster exists and is active
5. ✅ Verify ECR repository has latest image

### **Migrations Failing?**
1. ✅ Check migration task logs in CloudWatch
2. ✅ Verify DATABASE_URL is correct in task definition
3. ✅ Ensure app security group can reach database
4. ✅ Check database connection from ECS task
5. ✅ Verify Alembic migrations directory exists in Docker image

### **Health Checks Failing?**
1. ✅ Verify `/health` endpoint is implemented in FastAPI
2. ✅ Check if database migrations have run successfully
3. ✅ Test database connection from application
4. ✅ Check CloudWatch logs for application errors
5. ✅ Verify security groups allow ALB -> ECS communication

### **Deployment Not Updating?**
1. ✅ Check if new Docker image was pushed to ECR
2. ✅ Verify task definition was updated with new image
3. ✅ Check ECS service for deployment status
4. ✅ Look for "RUNNING" tasks with new image tag
5. ✅ Check deployment circuit breaker hasn't been triggered

---

## 📊 Cost Monitoring

### **Hourly Costs (when running)**
```
RDS db.t3.micro:      $0.034/hour
ECS Fargate:          $0.120/hour (2 vCPU, 4GB)
NAT Gateway:          $0.045/hour
ALB:                  $0.023/hour
Data Transfer:        $0.090/GB
                      ─────────────
Total (approx):       $0.22/hour
```

### **Daily/Monthly Estimates**
```
Per Day:    $5.28  (if running 24/7)
Per Month:  $158.40 (if running 24/7)

For testing: ~$0.50 for a few hours
```

### **Check Current Costs**
```bash
# Via AWS CLI
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-05 \
  --granularity DAILY \
  --metrics BlendedCost \
  --region us-east-1

# Or check AWS Cost Explorer in console:
# https://console.aws.amazon.com/cost-management/home#/cost-explorer
```

---

## 🔐 Security Best Practices

### **IAM Permissions**
- ✅ Use IAM user (TikTamer) for deployments, not root
- ✅ Store credentials in GitHub Secrets, never commit
- ✅ Rotate access keys regularly
- ✅ Follow principle of least privilege

### **Network Security**
- ✅ Database in private subnets (no public access)
- ✅ Security groups restrict traffic to necessary ports
- ✅ Application communicates with DB via internal VPC
- ✅ ALB is only public-facing component

### **Secrets Management**
- ✅ Database password auto-generated by Terraform
- ✅ Sensitive outputs marked as `sensitive = true`
- ✅ GitHub Secrets encrypted at rest
- ✅ Consider AWS Secrets Manager for production

---

## 🎯 Current Status Summary

### **✅ Working**
- Infrastructure deployment via Terraform
- CI pipeline (testing on PRs)
- Docker image building and ECR push
- ECS container deployment
- Load balancer configuration
- VPC networking and security

### **🔧 Just Implemented**
- ECS-based database migrations
- Migration task definition
- CD pipeline migration job
- Terraform outputs for migration config

### **⏳ Next Steps**
1. Deploy infrastructure with migration task
2. Add new GitHub Secrets
3. Implement `/health` endpoint in FastAPI
4. Test complete end-to-end deployment
5. Verify application is serving traffic

### **❌ Known Issues**
- Health check endpoint not yet implemented
- Database schema still empty (migrations not run yet)
- Application returns 503 errors (needs health endpoint)

---

## 📞 Useful Links

- **GitHub Repository**: https://github.com/Shereefeo/social-media-scheduler
- **GitHub Actions**: https://github.com/Shereefeo/social-media-scheduler/actions
- **AWS Console (Ohio)**: https://us-east-2.console.aws.amazon.com/
- **ECS Console**: https://us-east-2.console.aws.amazon.com/ecs/v2/clusters/TikTimer-dev-cluster
- **RDS Console**: https://us-east-2.console.aws.amazon.com/rds/home?region=us-east-2#database:id=tiktimer-dev-db
- **CloudWatch Logs**: https://us-east-2.console.aws.amazon.com/cloudwatch/home?region=us-east-2#logsV2:log-groups/log-group//ecs/TikTimer-dev-cluster

---

## 💾 Backup Commands

### **Backup Database**
```bash
# From ECS task with PostgreSQL client
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Or via script (see scripts/backup-database.py)
python scripts/backup-database.py
```

### **Backup Terraform State**
```bash
# State is in S3: tiktimer-terraform-state
aws s3 cp s3://tiktimer-terraform-state/dev/terraform.tfstate ./backup/terraform-state-$(date +%Y%m%d).tfstate
```

---

## 🔄 Typical Development Workflow

### **1. Local Development**
```bash
# Run backend
docker-compose up -d

# Run frontend
cd tiktimer-frontend
npm run dev

# Make changes, test locally
```

### **2. Create Feature Branch**
```bash
git checkout -b feature/my-feature
# Make changes
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

### **3. Open Pull Request**
- CI pipeline runs automatically
- Review changes, ensure tests pass
- Merge to main when ready

### **4. Deploy to AWS**
- Merge triggers CD pipeline
- Build -> Migrate -> Deploy -> Health Check
- Monitor via GitHub Actions

### **5. Test Deployment**
```bash
# Get ALB DNS
ALB_DNS=$(cd tiktimer-infrastructure && terraform output -raw alb_dns_name)

# Test endpoints
curl http://$ALB_DNS/health
curl http://$ALB_DNS/docs  # FastAPI docs
```

### **6. Tear Down (if testing)**
```bash
cd tiktimer-infrastructure
terraform destroy -auto-approve
```

---

*Last Updated: October 5, 2025*
*For detailed implementation notes, see [CICD_IMPLEMENTATION_NOTES.md](./CICD_IMPLEMENTATION_NOTES.md)*
