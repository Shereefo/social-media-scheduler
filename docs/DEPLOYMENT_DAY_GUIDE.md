# TikTimer Deployment Day Guide

**Purpose:** Complete AWS deployment with screen recording for demo purposes.

**Prerequisites:**
- ✅ TikTok API v2 integration complete
- ✅ Frontend video upload feature working
- ✅ Simulation mode tested and working
- ✅ Local OAuth flow validated
- ✅ All code changes committed to `feature/frontend-improvements` branch

---

## Pre-Deployment Checklist

### 1. Code Preparation
- [ ] Review all changes on `feature/frontend-improvements` branch
- [ ] Run local tests to ensure everything works in simulation mode
- [ ] Check that all environment variables are documented
- [ ] Ensure `.env.example` file is up to date with all required variables

### 2. Git Operations
- [ ] Ensure all changes are committed on `feature/frontend-improvements`
- [ ] Merge `feature/frontend-improvements` into `main` branch
  ```bash
  git checkout main
  git merge feature/frontend-improvements
  git push origin main
  ```
- [ ] Tag the release for tracking
  ```bash
  git tag -a v1.0.0-deployment -m "Initial production deployment"
  git push origin v1.0.0-deployment
  ```

### 3. TikTok Developer Portal Setup
- [ ] Log into [TikTok Developer Portal](https://developers.tiktok.com/)
- [ ] Navigate to your app settings
- [ ] **DO NOT update redirect URI yet** - wait until AWS ALB is provisioned
- [ ] Note down your Client Key and Client Secret (should already be in `.env`)
- [ ] Verify scopes are set to: `user.info.basic,video.publish`

---

## AWS Infrastructure Deployment

### 4. Update Terraform Configuration

**Backend S3 Configuration:**
- [ ] Navigate to `tiktimer-infrastructure/` directory
- [ ] Ensure S3 backend bucket exists: `tiktimer-terraform-state-2024`
- [ ] Verify `backend.tf` is configured correctly

**Environment Variables:**
- [ ] Update `tiktimer-infrastructure/terraform.tfvars` with production values:
  ```hcl
  tiktok_client_key     = "your-client-key"
  tiktok_client_secret  = "your-client-secret"
  # Redirect URI will be updated after ALB is created
  scheduler_simulation_mode = "false"  # Real TikTok API calls
  ```

**Database Configuration:**
- [ ] Review RDS settings in `main.tf` (PostgreSQL instance size, backup retention)
- [ ] Ensure database credentials are stored securely (consider AWS Secrets Manager)

### 5. Terraform Apply - Backend Infrastructure

```bash
cd tiktimer-infrastructure
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

**Expected Resources:**
- [ ] VPC with public/private subnets
- [ ] RDS PostgreSQL instance
- [ ] ECS Cluster
- [ ] Application Load Balancer (ALB)
- [ ] ECS Task Definition for backend API
- [ ] CloudWatch Log Groups
- [ ] Security Groups
- [ ] IAM Roles and Policies

**After Apply:**
- [ ] Note the ALB DNS name from Terraform output
- [ ] Note the RDS endpoint from Terraform output
- [ ] Wait for RDS instance to be fully available (~5-10 minutes)

### 6. Update TikTok OAuth Redirect URI

**Get ALB URL:**
```bash
# From terraform output
terraform output alb_dns_name
# Example: tiktimer-alb-123456789.us-east-1.elb.amazonaws.com
```

**Update Redirect URI:**
- [ ] Go to TikTok Developer Portal
- [ ] Update Redirect URI to: `https://<ALB_DNS>/api/v1/tiktok/callback`
- [ ] Save changes (may take a few minutes to propagate)

**Update Terraform:**
- [ ] Update `tiktimer-infrastructure/terraform.tfvars`:
  ```hcl
  tiktok_redirect_uri = "https://<ALB_DNS>/api/v1/tiktok/callback"
  ```
- [ ] Re-apply Terraform to update backend environment variables:
  ```bash
  terraform apply
  ```

### 7. Database Migration

**Option A: Fresh Database (Recommended for Demo)**
- [ ] Backend will auto-create tables on first startup via `lifespan` in `main.py`
- [ ] Verify logs show: "Database tables created successfully"

**Option B: Migrate Existing Data (If Needed)**
- [ ] Export local PostgreSQL data:
  ```bash
  docker exec social-media-scheduler-db pg_dump -U postgres scheduler > backup.sql
  ```
- [ ] Connect to RDS instance via bastion host or VPC peering
- [ ] Import data to RDS

### 8. Frontend Deployment

**Update Frontend Environment:**
- [ ] Navigate to `tiktimer-frontend/`
- [ ] Update `.env.production` with ALB endpoint:
  ```env
  VITE_API_URL=https://<ALB_DNS>/api/v1
  ```

**Build and Deploy to S3:**
```bash
cd tiktimer-frontend
npm run build

# Upload to S3 bucket
aws s3 sync dist/ s3://tiktimer-frontend-bucket --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths "/*"
```

**Terraform for Frontend (If Not Already Deployed):**
- [ ] Navigate to `tiktimer-infrastructure/`
- [ ] Ensure frontend module is enabled in `main.tf`
- [ ] Apply frontend infrastructure:
  ```bash
  terraform apply -target=module.frontend
  ```

**Expected Frontend Resources:**
- [ ] S3 bucket for static hosting
- [ ] CloudFront distribution
- [ ] Route 53 DNS records (if using custom domain)
- [ ] ACM SSL certificate (if using custom domain)

---

## Deployment Verification

### 9. Backend Health Checks

**Test ALB Health Endpoint:**
```bash
curl https://<ALB_DNS>/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "api_version": "0.1.0",
  "database": "connected",
  "service": "tiktimer-api"
}
```

**Check ECS Task Logs:**
- [ ] Go to AWS Console → ECS → Clusters → tiktimer-cluster
- [ ] Click on the running task
- [ ] View CloudWatch logs
- [ ] Verify "Scheduler task started" message appears
- [ ] Verify "Database tables created successfully" message appears

### 10. Frontend Verification

**Test CloudFront URL:**
- [ ] Open CloudFront URL in browser
- [ ] Verify frontend loads correctly
- [ ] Check browser console for errors
- [ ] Verify API calls go to correct ALB endpoint

**Test Registration/Login:**
- [ ] Register a new test user
- [ ] Log in with credentials
- [ ] Verify JWT token is stored correctly
- [ ] Check that Dashboard loads

### 11. TikTok OAuth Flow Test

**Complete OAuth Flow:**
- [ ] Click "Connect TikTok Account" in Dashboard
- [ ] Should redirect to TikTok authorization page
- [ ] Authorize the app
- [ ] Should redirect back to your CloudFront URL with authorization code
- [ ] Backend should exchange code for access token
- [ ] Verify success message in frontend
- [ ] Check backend logs to confirm token exchange succeeded

**Verify Token Storage:**
```bash
# Query RDS to confirm token was saved (use bastion host or RDS query editor)
SELECT username, tiktok_access_token IS NOT NULL as has_token, tiktok_token_expires_at
FROM users
WHERE username = 'your-test-user';
```

### 12. Video Upload Test

**Upload Test Video:**
- [ ] Navigate to "Upload Video" page
- [ ] Select a short test video (5-10 seconds recommended)
- [ ] Add caption/description
- [ ] Click upload
- [ ] Verify upload progress bar works
- [ ] Verify success message appears

**Verify S3 Storage:**
```bash
# List uploaded videos in S3
aws s3 ls s3://tiktimer-video-uploads/ --recursive
```

### 13. Post Scheduling Test

**Create Scheduled Post:**
- [ ] Navigate to "Schedule Post" page
- [ ] Select uploaded video
- [ ] Write caption
- [ ] Set schedule time (2-3 minutes in the future for quick test)
- [ ] Platform: TikTok
- [ ] Submit

**Verify Post Created:**
- [ ] Check "Posts" page shows scheduled post
- [ ] Status should be "scheduled"
- [ ] Verify scheduled time is correct

**Wait for Scheduler:**
- [ ] Wait for scheduled time to pass
- [ ] Scheduler runs every 60 seconds
- [ ] Watch ECS task logs in CloudWatch

**Expected Log Output:**
```
INFO: Found 1 posts ready to publish
INFO: Attempting to publish TikTok post <ID> for user <username>
INFO: Published TikTok post <ID> with video. TikTok ID: <tiktok_publish_id>
INFO: Successfully published scheduled TikTok post <ID>
```

**Verify on TikTok:**
- [ ] Log into TikTok mobile app or web
- [ ] Check your drafts/posts (privacy is set to SELF_ONLY)
- [ ] Verify video appears and is processing
- [ ] **CAPTURE SCREENSHOT/SCREEN RECORDING** 🎥

**Verify in Dashboard:**
- [ ] Refresh Posts page
- [ ] Status should change from "scheduled" → "published"
- [ ] **CAPTURE SCREENSHOT** 🎥

---

## Screen Recording Checklist

### 14. Demo Recording Script

**Recording Setup:**
- [ ] Clear browser cache and cookies
- [ ] Close unnecessary browser tabs
- [ ] Set screen resolution to 1920x1080 for best quality
- [ ] Start screen recording software (QuickTime, OBS, etc.)
- [ ] Open CloudFront URL in incognito/private window

**Demo Flow (Record This):**

1. **Landing Page** (30 seconds)
   - [ ] Show CloudFront URL in address bar
   - [ ] Navigate through landing page

2. **Registration** (30 seconds)
   - [ ] Register new user account
   - [ ] Show successful registration

3. **Login** (15 seconds)
   - [ ] Log in with new credentials
   - [ ] Show Dashboard loads

4. **TikTok OAuth** (1 minute)
   - [ ] Click "Connect TikTok Account"
   - [ ] Show redirect to TikTok authorization
   - [ ] Authorize app
   - [ ] Show successful callback and connection status

5. **Video Upload** (1 minute)
   - [ ] Navigate to Upload page
   - [ ] Select test video file
   - [ ] Add caption
   - [ ] Show upload progress
   - [ ] Show upload success

6. **Schedule Post** (1 minute)
   - [ ] Navigate to Schedule Post page
   - [ ] Select uploaded video from dropdown
   - [ ] Write engaging caption
   - [ ] Set schedule time (2 minutes from now)
   - [ ] Submit post
   - [ ] Show post appears in Posts list with "scheduled" status

7. **AWS Console - Show Infrastructure** (2 minutes)
   - [ ] Open AWS Console
   - [ ] Show ECS cluster running
   - [ ] Show RDS instance
   - [ ] Show ALB with healthy targets
   - [ ] Show S3 buckets (frontend + video uploads)
   - [ ] Show CloudFront distribution
   - [ ] Show CloudWatch logs with scheduler running

8. **Wait for Scheduled Time** (Variable - fast-forward in editing)
   - [ ] Pause recording or fast-forward during wait
   - [ ] Resume when scheduled time approaches

9. **CloudWatch Logs - Show Scheduler** (1 minute)
   - [ ] Open CloudWatch Logs
   - [ ] Show scheduler picking up post
   - [ ] Show "Found 1 posts ready to publish"
   - [ ] Show TikTok API call logs
   - [ ] Show "Successfully published scheduled TikTok post"

10. **Verify in Dashboard** (30 seconds)
    - [ ] Refresh Posts page
    - [ ] Show status changed to "published"
    - [ ] Highlight the timestamp

11. **Verify on TikTok** (1 minute)
    - [ ] Open TikTok app/web
    - [ ] Navigate to your profile
    - [ ] Show the posted video (in drafts or posts depending on privacy)
    - [ ] **THIS IS THE MONEY SHOT** 🎥💰

**Total Recording Time:** ~10-12 minutes (can be edited down to 5-7 minutes)

---

## Post-Deployment Tasks

### 15. Security Hardening

- [ ] Review security group rules (restrict to necessary ports only)
- [ ] Enable VPC Flow Logs for network monitoring
- [ ] Set up AWS WAF rules for ALB (if needed)
- [ ] Enable GuardDuty for threat detection
- [ ] Review IAM policies for least privilege
- [ ] Enable MFA for AWS root account
- [ ] Set up AWS Backup for RDS automated backups

### 16. Monitoring Setup

**CloudWatch Alarms:**
- [ ] ALB 5xx error rate > 5%
- [ ] ECS CPU utilization > 80%
- [ ] ECS memory utilization > 80%
- [ ] RDS CPU utilization > 80%
- [ ] RDS storage space < 20% free
- [ ] RDS connection count > 80% of max

**CloudWatch Dashboards:**
- [ ] Create dashboard with key metrics (API requests, database connections, task count)

**Log Retention:**
- [ ] Set CloudWatch log retention to 30 days (or desired period)

### 17. Cost Optimization

- [ ] Review running resources in AWS Cost Explorer
- [ ] Set up billing alerts for unexpected costs
- [ ] Consider using Reserved Instances for long-term savings (if keeping deployed)
- [ ] Enable S3 lifecycle policies to move old videos to cheaper storage tiers

### 18. Documentation Updates

- [ ] Update `README.md` with deployment instructions
- [ ] Document environment variables and their sources
- [ ] Create runbook for common operations (restart service, check logs, etc.)
- [ ] Document rollback procedure
- [ ] Add architecture diagram showing AWS components

---

## Troubleshooting Guide

### Common Issues and Solutions

**Issue: ECS Task Fails to Start**
- Check CloudWatch logs for error messages
- Verify environment variables are set correctly in ECS task definition
- Ensure Docker image is pushed to ECR successfully
- Check security group allows outbound internet access for RDS connection

**Issue: Database Connection Fails**
- Verify RDS security group allows inbound traffic from ECS tasks
- Check DATABASE_URL format: `postgresql+asyncpg://user:password@host:5432/dbname`
- Ensure RDS instance is in available state
- Check VPC routing and subnet configuration

**Issue: TikTok OAuth Redirect Fails**
- Verify redirect URI exactly matches what's in TikTok Developer Portal
- Ensure ALB has HTTPS listener configured
- Check frontend is sending correct redirect_uri parameter
- Review TikTok Developer Portal for any app review requirements

**Issue: Video Upload Fails**
- Check S3 bucket permissions (ECS task role should have PutObject permission)
- Verify file size limits (increase if needed)
- Check CORS configuration on S3 bucket
- Review frontend upload code for timeout issues

**Issue: Scheduler Not Publishing Posts**
- Check CloudWatch logs for scheduler errors
- Verify SCHEDULER_SIMULATION_MODE is set to "false"
- Ensure user has valid TikTok access token
- Check TikTok API response for error messages
- Verify scheduled_time is in the past when scheduler runs

**Issue: CloudFront Shows Old Content**
- Create CloudFront invalidation: `aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"`
- Wait 2-3 minutes for invalidation to complete
- Clear browser cache

---

## Rollback Plan

### If Deployment Fails:

**Database Rollback:**
```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier tiktimer-db-rollback \
  --db-snapshot-identifier <snapshot-id>
```

**Frontend Rollback:**
```bash
# Revert to previous S3 version
aws s3 sync s3://tiktimer-frontend-bucket-backup/ s3://tiktimer-frontend-bucket/
```

**Backend Rollback:**
```bash
# Update ECS task definition to previous revision
aws ecs update-service \
  --cluster tiktimer-cluster \
  --service tiktimer-backend \
  --task-definition tiktimer-backend:<previous-revision>
```

---

## Success Criteria

✅ **Deployment is successful when:**
1. ALB health check returns 200 OK
2. Frontend loads without errors
3. User can register and login
4. TikTok OAuth flow completes successfully
5. Video uploads to S3
6. Post schedules successfully
7. Scheduler picks up post at scheduled time
8. TikTok API accepts video and returns success
9. Video appears on TikTok account
10. Dashboard shows post status as "published"

---

## Post-Demo Cleanup (Optional)

**If you want to tear down to save costs:**

```bash
cd tiktimer-infrastructure
terraform destroy
```

**Keep in mind:**
- RDS snapshots will be retained (you may be charged for snapshot storage)
- S3 buckets with data won't be deleted automatically (need to empty first)
- CloudWatch logs will be retained based on retention settings

**Before destroying:**
- [ ] Download any important data
- [ ] Export database for backup
- [ ] Download screen recording and demo video
- [ ] Document lessons learned

---

## Notes

- **Estimated deployment time:** 2-3 hours (including AWS resource provisioning wait times)
- **Best time to deploy:** During off-peak hours or weekend
- **Required accounts:** AWS account, TikTok Developer account
- **Cost estimate:** ~$50-100/month if left running (mainly RDS + ALB + data transfer)

**Remember:** This is a demonstration deployment. For production, you'd want:
- Custom domain with SSL/TLS certificate
- Multi-AZ RDS for high availability
- Auto-scaling for ECS tasks
- CDN caching optimizations
- Enhanced monitoring and alerting
- Automated CI/CD pipeline
- Comprehensive security scanning

---

## Final Checklist Before Recording

- [ ] All AWS resources are healthy and running
- [ ] Test user can complete full flow end-to-end
- [ ] TikTok developer account is ready
- [ ] Test video file is prepared (5-10 seconds, < 5MB)
- [ ] Screen recording software is tested and working
- [ ] Battery is charged / laptop is plugged in
- [ ] Notifications are turned off (Do Not Disturb mode)
- [ ] Browser bookmarks/history cleared for clean demo
- [ ] Microphone tested (if doing voiceover)
- [ ] Demo script reviewed and rehearsed

---

**Good luck with your deployment! 🚀**

*You've built a solid foundation with simulation mode testing and TikTok API v2 integration. The deployment should go smoothly!*
