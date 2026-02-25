# TikTimer Deployment Checklist
## Frontend + TikTok OAuth Integration

---

## 📋 Prerequisites

- ✅ AWS CLI configured with credentials
- ✅ Terraform installed
- ✅ Node.js and npm installed
- ✅ TikTok Developer account with app created
- ✅ Backend running locally (for testing before deploy)

---

## 🚀 Deployment Steps

### **Step 1: Deploy AWS Infrastructure (15-20 minutes)**

```bash
cd tiktimer-infrastructure

# Preview changes
terraform plan

# Deploy
terraform apply
# Type 'yes' when prompted
```

**Expected Output:**
```
Outputs:

frontend_url = "https://d1a2b3c4d5e6f.cloudfront.net"
frontend_s3_bucket = "tiktimer-prod-frontend"
frontend_cloudfront_distribution_id = "E1ABCDEFG12345"
```

**✅ Save these outputs!**

📝 **Record your values:**
```
CloudFront Domain: ___________________________________
S3 Bucket: ___________________________________________
Distribution ID: _____________________________________
```

---

### **Step 2: Update TikTok Developer Portal**

1. Go to: https://developers.tiktok.com/
2. Navigate to your app dashboard
3. Find "Redirect URIs" or "OAuth Settings" section
4. **Add this URI (use YOUR CloudFront domain):**
   ```
   https://YOUR_CLOUDFRONT_DOMAIN/auth/tiktok/callback
   ```
   Example: `https://d1a2b3c4d5e6f.cloudfront.net/auth/tiktok/callback`

5. Click "Save" or "Add"
6. ⚠️ **Important:** Some apps require approval - check status
7. ✅ **Verify:** URI shows as "Approved" or "Active"

---

### **Step 3: Update Backend Environment Variable**

Edit your `.env` file:

```bash
# Change FROM:
TIKTOK_REDIRECT_URI=https://lovely-kangaroo-628d2a.netlify.app/tiktok-callback.html

# Change TO (use YOUR CloudFront domain):
TIKTOK_REDIRECT_URI=https://YOUR_CLOUDFRONT_DOMAIN/auth/tiktok/callback
```

Example:
```
TIKTOK_REDIRECT_URI=https://d1a2b3c4d5e6f.cloudfront.net/auth/tiktok/callback
```

**Restart backend to load new environment:**
```bash
docker-compose restart api

# Verify it restarted
docker-compose ps
```

---

### **Step 4: Build Frontend**

```bash
cd tiktimer-frontend

# Install dependencies (if needed)
npm install

# Build production bundle
npm run build

# Verify build succeeded
ls -la build/
# Should see: index.html, assets/ folder
```

---

### **Step 5: Deploy Frontend to S3**

```bash
# Use bucket name from Step 1
aws s3 sync build/ s3://YOUR_BUCKET_NAME/ --delete

# Example:
# aws s3 sync build/ s3://tiktimer-prod-frontend/ --delete
```

**What `--delete` does:** Removes old files from S3 that aren't in your new build

---

### **Step 6: Invalidate CloudFront Cache**

```bash
# Use distribution ID from Step 1
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"

# Example:
# aws cloudfront create-invalidation \
#   --distribution-id E1ABCDEFG12345 \
#   --paths "/*"
```

**Why?** CloudFront caches files. This tells it to fetch fresh copies.

**Wait 2-3 minutes** for invalidation to complete.

---

### **Step 7: Test OAuth Flow**

1. **Open your CloudFront URL** in browser:
   ```
   https://YOUR_CLOUDFRONT_DOMAIN
   ```

2. **Login** with demo credentials:
   ```
   Username: demo_user
   Password: demo123
   ```

3. **Navigate to Dashboard**

4. **Click "Connect TikTok Account"**

5. **Expected flow:**
   - Redirects to TikTok login page
   - Login with your TikTok account
   - Authorize app
   - Redirects back to your app
   - Shows "Connected to TikTok" with green indicator
   - Displays your TikTok Open ID

---

## 🧪 Testing Checklist

### **Frontend Tests**

- [ ] App loads at CloudFront URL
- [ ] Login page works
- [ ] Dashboard shows correctly
- [ ] Create Post page loads
- [ ] Posts page loads
- [ ] All navigation links work
- [ ] Images/assets load properly

### **TikTok OAuth Tests**

- [ ] "Connect TikTok" button visible when not connected
- [ ] Clicking button redirects to TikTok
- [ ] Can login to TikTok
- [ ] Can authorize app
- [ ] Redirects back to app (not 404)
- [ ] Shows success message
- [ ] Dashboard shows "Connected to TikTok"
- [ ] Shows TikTok Open ID
- [ ] Disconnect button works
- [ ] After disconnect, can reconnect

### **Post Creation Tests**

- [ ] Can create a post
- [ ] Post appears in posts list
- [ ] Can delete a post
- [ ] Filter tabs work
- [ ] Timestamps show correctly

---

## 🐛 Troubleshooting

### **Issue: CloudFront shows 404**

**Cause:** Files not uploaded or invalidation not complete

**Fix:**
```bash
# Re-upload files
aws s3 sync build/ s3://YOUR_BUCKET/ --delete

# Invalidate cache
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"

# Wait 2-3 minutes
```

---

### **Issue: OAuth redirect fails (404 on callback)**

**Causes:**
1. Redirect URI not added to TikTok Developer Portal
2. URI doesn't match exactly (check trailing slash, http vs https)
3. TikTok app not approved for new URI

**Fix:**
1. Double-check URI in TikTok Developer Portal
2. Ensure it's: `https://YOUR_DOMAIN/auth/tiktok/callback` (no trailing slash)
3. Check TikTok app approval status
4. Verify `.env` has correct TIKTOK_REDIRECT_URI
5. Restart backend: `docker-compose restart api`

---

### **Issue: "Failed to connect TikTok" error**

**Causes:**
1. Wrong CLIENT_KEY or CLIENT_SECRET
2. Backend can't reach TikTok API
3. TikTok rate limits

**Debug:**
```bash
# Check backend logs
docker logs social-media-scheduler-api --tail 50

# Look for errors like:
# - "Failed to exchange code for token"
# - HTTP status codes from TikTok API
```

**Fix:**
1. Verify credentials in `.env` match TikTok Developer Portal
2. Check TikTok API status: https://status.tiktokapis.com/
3. Restart backend: `docker-compose restart api`

---

### **Issue: Page loads but looks broken (no CSS)**

**Cause:** Asset paths incorrect after CloudFront deployment

**Fix:**
1. Check browser console for 404 errors
2. Verify `build/index.html` has correct asset paths
3. Rebuild frontend: `npm run build`
4. Re-upload: `aws s3 sync build/ s3://YOUR_BUCKET/ --delete`

---

## 📊 Post-Deployment Verification

### **Check CloudFront Distribution**

```bash
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID

# Look for:
# - Status: "Deployed"
# - Enabled: true
# - DefaultRootObject: "index.html"
```

### **Check S3 Bucket Contents**

```bash
aws s3 ls s3://YOUR_BUCKET/ --recursive

# Should see:
# - index.html
# - assets/ folder with JS/CSS files
```

### **Check Backend Logs**

```bash
docker logs social-media-scheduler-api --tail 100

# Look for:
# - "Application startup complete"
# - No error messages
# - Database connected
```

---

## 🎉 Success Criteria

- ✅ Frontend accessible at CloudFront URL
- ✅ User can login
- ✅ User can create posts
- ✅ User can connect TikTok account via OAuth
- ✅ Dashboard shows TikTok connection status
- ✅ No console errors in browser
- ✅ All pages load within 2 seconds

---

## 🔄 Future Deployments

After initial setup, deployments are simple:

```bash
# 1. Make changes to frontend code
# 2. Build
npm run build

# 3. Deploy
aws s3 sync build/ s3://tiktimer-prod-frontend/ --delete
aws cloudfront create-invalidation --distribution-id E1ABCDEFG12345 --paths "/*"

# Done! Changes live in 2-3 minutes
```

---

## 📝 Notes

- **CloudFront caching:** Default cache time is 24 hours
- **Invalidations:** First 1,000/month are free
- **S3 costs:** ~$0.023 per GB per month
- **CloudFront costs:** Free tier covers 1 TB transfer
- **Total expected cost:** ~$0.05/month for frontend hosting

---

## 🔗 Useful Commands

```bash
# Check CloudFront distribution status
aws cloudfront get-distribution --id YOUR_ID | grep Status

# List S3 bucket files
aws s3 ls s3://YOUR_BUCKET/ --recursive

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id YOUR_ID \
  --id INVALIDATION_ID

# View backend logs in real-time
docker logs -f social-media-scheduler-api

# Restart all services
docker-compose restart
```

---

**Last Updated:** October 18, 2025
**Project:** TikTimer - Social Media Scheduler
**Infrastructure:** AWS (S3 + CloudFront + ECS + RDS)
