# Frontend Deployment & TikTok OAuth Integration

**Date**: October 19, 2025
**Session**: Frontend CloudFront Deployment + TikTok OAuth Testing
**Status**: ✅ Complete and Working

---

## Table of Contents
- [Overview](#overview)
- [Architecture Decisions](#architecture-decisions)
- [Infrastructure Deployment](#infrastructure-deployment)
- [Errors Encountered & Solutions](#errors-encountered--solutions)
- [OAuth Integration Debugging](#oauth-integration-debugging)
- [Verification & Testing](#verification--testing)
- [Key Learnings](#key-learnings)
- [Next Steps](#next-steps)

---

## Overview

This session focused on deploying the React frontend to AWS CloudFront and integrating TikTok OAuth in sandbox mode. We made the strategic decision to deploy **only the frontend infrastructure** first to test the OAuth flow before committing to a full production deployment.

### What We Accomplished

1. ✅ Deployed S3 + CloudFront for static frontend hosting (8 AWS resources)
2. ✅ Created Terms of Service and Privacy Policy pages (required by TikTok)
3. ✅ Fixed multiple CORS, OAuth, and authentication issues
4. ✅ Successfully completed end-to-end TikTok OAuth flow in sandbox mode
5. ✅ Verified token storage and user connection status display

### Key URLs

- **Frontend**: https://drds1j9h9dec0.cloudfront.net
- **Terms of Service**: https://drds1j9h9dec0.cloudfront.net/terms
- **Privacy Policy**: https://drds1j9h9dec0.cloudfront.net/privacy
- **OAuth Callback**: https://drds1j9h9dec0.cloudfront.net/api/v1/auth/tiktok/callback
- **Backend API**: http://localhost:8000 (local development)

---

## Architecture Decisions

### Decision 1: Deploy Frontend-Only First

**Rationale**: Instead of deploying all 68 Terraform resources (VPC, RDS, ECS, ALB, etc.), we chose to deploy only the frontend module (8 resources) to:

1. Test TikTok OAuth with HTTPS domain (required by TikTok)
2. Validate CloudFront + S3 hosting setup
3. Minimize AWS costs during development/testing
4. Keep backend local for easier debugging

**Resources Deployed**:
```bash
# Only frontend module (8 resources):
- aws_s3_bucket (private)
- aws_s3_bucket_public_access_block
- aws_s3_bucket_server_side_encryption_configuration
- aws_s3_bucket_versioning
- aws_s3_bucket_policy
- aws_cloudfront_origin_access_identity
- aws_cloudfront_distribution
- aws_s3_bucket_ownership_controls
```

**Resources NOT Deployed** (saved for later):
- VPC and networking (subnets, NAT gateways, security groups)
- RDS PostgreSQL database
- ECS cluster and services
- Application Load Balancer
- ECR container registry

### Decision 2: Sandbox Mode for OAuth Testing

Used TikTok's sandbox environment with test users instead of production:
- Allows OAuth testing without app review/approval
- Requires whitelisted test accounts
- Test user: `reef0703` (TikTok username)

### Decision 3: Keep Backend Local

Backend remains on `localhost:8000` during testing:
- Faster iteration on OAuth debugging
- Direct access to logs and database
- No need to rebuild/push Docker images
- CORS configured to allow CloudFront origin

---

## Infrastructure Deployment

### Step 1: Initial Terraform Plan

**Command**:
```bash
cd tiktimer-infrastructure
terraform plan
```

**Initial Error** - Missing CloudFront Permissions:
```
Error: listing CloudFront Cache Policies: User: arn:aws:iam::022499001793:user/TikTamer
is not authorized to perform: cloudfront:ListCachePolicies
```

**Solution**: Added CloudFront permissions to IAM user `TikTamer`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:ListCachePolicies",
        "cloudfront:ListOriginRequestPolicies",
        "cloudfront:ListDistributions",
        "cloudfront:GetCachePolicy",
        "cloudfront:GetOriginRequestPolicy",
        "cloudfront:CreateDistribution",
        "cloudfront:GetDistribution",
        "cloudfront:UpdateDistribution",
        "cloudfront:DeleteDistribution",
        "cloudfront:TagResource",
        "cloudfront:ListTagsForResource",
        "cloudfront:CreateCloudFrontOriginAccessIdentity",
        "cloudfront:GetCloudFrontOriginAccessIdentity",
        "cloudfront:DeleteCloudFrontOriginAccessIdentity",
        "cloudfront:CreateInvalidation"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 2: Deploy Frontend Module Only

**Command**:
```bash
cd tiktimer-infrastructure
terraform plan -target=module.frontend -out=tfplan-frontend
terraform apply tfplan-frontend
```

**Output**:
```
Plan: 8 to add, 0 to change, 0 to destroy.

Outputs:
frontend_cloudfront_distribution_id = "E3VZYQRLYMWXRM"
frontend_url = "https://drds1j9h9dec0.cloudfront.net"
frontend_s3_bucket = "tiktimer-dev-frontend"
```

**Deployment Time**: ~3-4 minutes (CloudFront distribution takes longest)

### Step 3: Build and Deploy React Frontend

**Build**:
```bash
cd tiktimer-frontend
npm run build
```

**Upload to S3**:
```bash
aws s3 sync ./dist s3://tiktimer-dev-frontend/ --delete
```

**Invalidate CloudFront Cache** (required after updates):
```bash
aws cloudfront create-invalidation \
  --distribution-id E3VZYQRLYMWXRM \
  --paths "/*"
```

**Note**: CloudFront invalidation takes 1-2 minutes to propagate globally.

---

## Errors Encountered & Solutions

### Error 1: CORS - Login Failed

**Symptom**:
```
Login failed. Please try again.
```

**Browser Console**:
```
Access to XMLHttpRequest at 'http://localhost:8000/token' from origin
'https://drds1j9h9dec0.cloudfront.net' has been blocked by CORS policy
```

**Root Cause**: Backend CORS configuration only allowed old Netlify domain and localhost, not the new CloudFront domain.

**Solution**: Updated `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lovely-kangaroo-628d2a.netlify.app",  # Old Netlify
        "https://drds1j9h9dec0.cloudfront.net",  # NEW: CloudFront frontend
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Restart Backend**:
```bash
docker-compose restart api
```

### Error 2: TikTok OAuth - "Something went wrong" (client_key error)

**Symptom**: TikTok authorization page showed:
```
Something went wrong
We couldn't log in with TikTok. This may be due to specific app settings.

If you're a developer, correct the following and try again:
• client_key
```

**URL Parameters**:
```
error=unauthorized_client
error_type=client_key
```

**Root Cause**: TikTok authorization URL had unencoded redirect_uri parameter.

**Original Code** (`backend/integrations/tiktok.py`):
```python
def get_authorization_url() -> str:
    params = {
        "client_key": settings.TIKTOK_CLIENT_KEY,
        "response_type": "code",
        "scope": "user.info.basic,video.publish",
        "redirect_uri": settings.TIKTOK_REDIRECT_URI,
        "state": "state",
    }
    # Manual string concatenation - NO URL ENCODING
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{TikTokAPI.AUTH_URL}?{query_string}"
```

**Solution**: Use proper URL encoding:
```python
from urllib.parse import urlencode

def get_authorization_url() -> str:
    params = {
        "client_key": settings.TIKTOK_CLIENT_KEY,
        "response_type": "code",
        "scope": "user.info.basic,video.publish",
        "redirect_uri": settings.TIKTOK_REDIRECT_URI,
        "state": "state",
    }
    # Use urlencode for proper URL encoding
    query_string = urlencode(params)
    return f"{TikTokAPI.AUTH_URL}?{query_string}"
```

**Before**:
```
redirect_uri=https://drds1j9h9dec0.cloudfront.net/api/v1/auth/tiktok/callback
```

**After**:
```
redirect_uri=https%3A%2F%2Fdrds1j9h9dec0.cloudfront.net%2Fapi%2Fv1%2Fauth%2Ftiktok%2Fcallback
```

### Error 3: TikTok OAuth - redirect_uri Mismatch

**Symptom**:
```
Something went wrong
If you're a developer, correct the following and try again:
• redirect_uri
```

**Root Cause**: Redirect URI in code didn't include `/api/v1` prefix that the backend actually uses.

**Investigation**:
```bash
# Check backend route structure
grep -n "router = APIRouter" backend/routes/tiktok.py
# Output: router = APIRouter(prefix="/auth/tiktok", tags=["tiktok"])

grep "include_router.*tiktok" backend/main.py
# Output: app.include_router(tiktok.router, prefix=settings.API_PREFIX)

# Check API_PREFIX value
docker exec social-media-scheduler-api python -c "from backend.config import settings; print(settings.API_PREFIX)"
# Output: /api/v1
```

**Full Backend Path**: `/api/v1/auth/tiktok/callback`
**Registered in TikTok**: `https://drds1j9h9dec0.cloudfront.net/auth/tiktok/callback` ❌

**Solution**: Updated `.env` and TikTok Developer Portal to include full path:
```bash
# Updated .env
TIKTOK_REDIRECT_URI=https://drds1j9h9dec0.cloudfront.net/api/v1/auth/tiktok/callback

# Recreate container to load new env
docker-compose up -d --force-recreate api
```

### Error 4: Frontend 404 - Callback Route Not Found

**Symptom**: After successful TikTok authorization, redirect URL showed:
```
https://drds1j9h9dec0.cloudfront.net/api/v1/auth/tiktok/callback?code=...
404 - Page not found
```

**Root Cause**: Frontend React Router had route at `/tiktok/callback` but TikTok was redirecting to `/api/v1/auth/tiktok/callback`.

**Solution**: Updated frontend route to match TikTok's redirect (`tiktimer-frontend/src/App.tsx`):
```typescript
// Before
<Route path="/tiktok/callback" element={<TikTokCallbackPage />} />

// After
<Route path="/api/v1/auth/tiktok/callback" element={<TikTokCallbackPage />} />
```

**Rebuild and Deploy**:
```bash
cd tiktimer-frontend
npm run build
aws s3 sync ./dist s3://tiktimer-dev-frontend/ --delete
aws cloudfront create-invalidation --distribution-id E3VZYQRLYMWXRM --paths "/*"
```

### Error 5: Wrong User Receiving Tokens

**Symptom**: OAuth flow completed but tokens were saved to `test_user` instead of logged-in user (`demo_user`).

**Investigation**:
```bash
# Check database
docker exec social-media-scheduler-db psql -U postgres -d scheduler \
  -c "SELECT username, tiktok_open_id IS NOT NULL as has_token FROM users;"

# Output:
#  username   | has_token
# ------------+-----------
#  test_user  | t         # ❌ Wrong user!
#  demo_user  | f
#  oauth_test | f
```

**Root Cause**: Token exchange endpoint was hardcoded for testing:

```python
# backend/routes/tiktok.py - BEFORE
@router.post("/exchange-token")
async def exchange_token(code_data: dict, db: AsyncSession = Depends(get_db)):
    # Hardcoded test user!
    result = await db.execute(select(User).where(User.username == "test_user"))
    user = result.scalars().first()

    if not user:
        # Create test user if doesn't exist
        user = User(username="test_user", email="test@example.com", ...)
        db.add(user)

    # Update test_user with tokens
    user.tiktok_access_token = token_data.get("access_token")
    # ...
```

**Solution**: Use authenticated user instead:
```python
# backend/routes/tiktok.py - AFTER
@router.post("/exchange-token")
async def exchange_token(
    code_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # ✅ Require authentication
):
    # Exchange code for token
    token_data = await TikTokAPI.exchange_code_for_token(code)

    # Update the AUTHENTICATED user
    current_user.tiktok_access_token = token_data.get("access_token")
    current_user.tiktok_refresh_token = token_data.get("refresh_token")
    current_user.tiktok_open_id = token_data.get("open_id")
    current_user.tiktok_token_expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=token_data.get("expires_in", 0)
    )

    await db.commit()
    await db.refresh(current_user)

    logger.info(f"User {current_user.username} connected TikTok account")
    return {"message": "TikTok account connected successfully"}
```

**Restart Backend**:
```bash
docker-compose restart api
```

### Error 6: Frontend Not Showing Connection Status

**Symptom**: OAuth completed successfully, tokens stored in database, but dashboard still showed "TikTok Not Connected".

**Investigation**:
```bash
# Verify tokens in database
docker exec social-media-scheduler-db psql -U postgres -d scheduler \
  -c "SELECT username, tiktok_open_id, LENGTH(tiktok_access_token) as token_length FROM users WHERE username = 'demo_user';"

# Output:
#  username  |            tiktok_open_id            | token_length
# -----------+--------------------------------------+--------------
#  demo_user | -000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB |           72
# ✅ Data is in database!

# Test API endpoint
TOKEN="..." # Get from login
curl -s http://localhost:8000/users/me -H "Authorization: Bearer $TOKEN" | jq

# Output:
# {
#   "email": "demo@tiktimer.com",
#   "username": "demo_user",
#   "id": 2,
#   "is_active": true,
#   "is_superuser": false,
#   "created_at": "2025-09-03T22:57:45.108518Z"
#   # ❌ Missing tiktok_access_token, tiktok_open_id, tiktok_token_expires_at!
# }
```

**Root Cause**: Pydantic `UserResponse` schema didn't include TikTok fields.

**Solution**: Update schema (`backend/schema.py`):
```python
# BEFORE
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True

# AFTER
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    tiktok_access_token: Optional[str] = None  # ✅ Added
    tiktok_open_id: Optional[str] = None       # ✅ Added
    tiktok_token_expires_at: Optional[datetime] = None  # ✅ Added

    class Config:
        from_attributes = True
```

**Restart Backend**:
```bash
docker-compose restart api
```

**Verify Fix**:
```bash
curl -s http://localhost:8000/users/me -H "Authorization: Bearer $TOKEN" | jq

# Output now includes TikTok fields:
# {
#   "email": "demo@tiktimer.com",
#   "username": "demo_user",
#   "id": 2,
#   "tiktok_access_token": "act.kmxQteBXre47hSURgIs695JbOrj1o30mxNZpZVCPbH2cJktU7k0rdC8rVt9B!6391.u1",
#   "tiktok_open_id": "-000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB",
#   "tiktok_token_expires_at": "2025-10-20T14:15:37.951301Z"
# }
```

**Frontend Fix**: Added user refresh after token exchange (`TikTokCallbackPage.tsx`):
```typescript
try {
  // Exchange the code for an access token
  await apiService.exchangeTikTokCode(code);

  // ✅ Refresh user data to get updated TikTok connection status
  await refreshUser();

  setStatus('success');

  setTimeout(() => {
    navigate('/dashboard');
  }, 2000);
}
```

**Rebuild and Deploy Frontend**:
```bash
cd tiktimer-frontend
npm run build
aws s3 sync ./dist s3://tiktimer-dev-frontend/ --delete
aws cloudfront create-invalidation --distribution-id E3VZYQRLYMWXRM --paths "/*"
```

---

## OAuth Integration Debugging

### TikTok Sandbox Configuration

**TikTok Developer Portal Settings**:

1. **Environment**: Sandbox (not Production)
2. **App Name**: TikTimer
3. **Client Key**: `sbawgds5na99y05zhq`
4. **Scopes Added**:
   - `user.info.basic` - Included in Login Kit
   - `video.publish` - Included in Content Posting API
   - `video.upload` - Included in Content Posting API

5. **Redirect URIs** (Sandbox):
   ```
   https://drds1j9h9dec0.cloudfront.net/api/v1/auth/tiktok/callback
   ```

6. **Legal Pages**:
   - Terms of Service: `https://drds1j9h9dec0.cloudfront.net/terms`
   - Privacy Policy: `https://drds1j9h9dec0.cloudfront.net/privacy`
   - Web/Desktop URL: `https://drds1j9h9dec0.cloudfront.net`

7. **Test Users** (Sandbox → Target Users):
   - TikTok Username: `reef0703`
   - Added: March 10, 2025

**Important**: In sandbox mode, ONLY whitelisted test users can complete OAuth. Any other TikTok account will get `unauthorized_client` error.

### OAuth Flow Sequence

**1. User Initiates Connection**:
```
User clicks "Connect TikTok Account" on dashboard
↓
Frontend calls: GET /api/v1/auth/tiktok/authorize
↓
Backend generates authorization URL
↓
Frontend redirects user to TikTok
```

**2. TikTok Authorization URL**:
```
https://www.tiktok.com/v2/auth/authorize/?
  client_key=sbawgds5na99y05zhq&
  response_type=code&
  scope=user.info.basic%2Cvideo.publish&
  redirect_uri=https%3A%2F%2Fdrds1j9h9dec0.cloudfront.net%2Fapi%2Fv1%2Fauth%2Ftiktok%2Fcallback&
  state=state
```

**3. User Authorizes on TikTok**:
```
User logs into TikTok (must be reef0703 for sandbox)
↓
User sees permission request for user.info.basic and video.publish
↓
User clicks "Authorize"
↓
TikTok redirects back with authorization code
```

**4. TikTok Callback**:
```
https://drds1j9h9dec0.cloudfront.net/api/v1/auth/tiktok/callback?
  code=Oh7Xx_Uqn6OAuDTGVgZw-3ZOpCiYkf8osWIRSYMtU1qSWfmOCHTFl5t-hv-w6zPNqd5UCVQxCUAxYiBFEsDJbvANlVoweUIfha9j8UIT2Dm2uAUHMr-P0_ilGXQHQGXBdi1VlbBou4luMWL6AwEugN_9hB2JkcfGfczSGnicPd6G8c8NWhxvHy_NHs-q-KLvpPD1oq-6U-EVL31-RnhJcc7nvbZ8xf6zXsZ2U-9DaNQ%2A0%216383.u1&
  scopes=user.info.basic%2Cvideo.publish&
  state=state
```

**5. Frontend Callback Page**:
```typescript
// TikTokCallbackPage.tsx
const code = searchParams.get('code');

// Exchange code for token
await apiService.exchangeTikTokCode(code);

// Refresh user data
await refreshUser();

// Redirect to dashboard
navigate('/dashboard');
```

**6. Backend Token Exchange**:
```
Frontend: POST /api/v1/auth/tiktok/exchange-token
Body: { "code": "Oh7Xx_Uqn6OAuDTGVgZw..." }
Headers: { "Authorization": "Bearer <user_jwt_token>" }
↓
Backend calls TikTok API: POST https://open.tiktokapis.com/v2/oauth/token/
Body:
  client_key=sbawgds5na99y05zhq
  client_secret=lcPKLlGmtzX0DJ60A9GvuUCsYjSe7uoa
  code=Oh7Xx_Uqn6OAuDTGVgZw...
  grant_type=authorization_code
  redirect_uri=https://drds1j9h9dec0.cloudfront.net/api/v1/auth/tiktok/callback
↓
TikTok Response:
{
  "access_token": "act.kmxQteBXre47hSURgIs695JbOrj1o30mxNZpZVCPbH2cJktU7k0rdC8rVt9B!6391.u1",
  "expires_in": 86400,
  "open_id": "-000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB",
  "refresh_expires_in": 31536000,
  "refresh_token": "rft.Z1J19zJ3OZ0W1z6lJWPqM0xsQz1eiSt62Seh9hFFKazqOj3wAzYEjL8DVX2m!6425.u1",
  "scope": "video.publish,user.info.basic",
  "token_type": "Bearer"
}
↓
Backend stores in database:
  current_user.tiktok_access_token = "act.kmxQ..."
  current_user.tiktok_refresh_token = "rft.Z1J1..."
  current_user.tiktok_open_id = "-000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB"
  current_user.tiktok_token_expires_at = now() + 86400 seconds
```

**7. Dashboard Shows Connection**:
```
Frontend fetches updated user: GET /users/me
↓
Response includes:
  tiktok_open_id: "-000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB"
  tiktok_token_expires_at: "2025-10-20T14:15:37.951301Z"
↓
Dashboard displays:
  ✅ Green indicator
  "Connected to TikTok"
  Account ID: -000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB
  [Disconnect] button
```

---

## Verification & Testing

### Database Verification

**Check TikTok tokens stored**:
```bash
docker exec social-media-scheduler-db psql -U postgres -d scheduler \
  -c "SELECT username, tiktok_open_id, tiktok_token_expires_at FROM users WHERE tiktok_open_id IS NOT NULL;"
```

**Expected Output**:
```
 username  |            tiktok_open_id            |    tiktok_token_expires_at
-----------+--------------------------------------+-------------------------------
 demo_user | -000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB | 2025-10-20 14:15:37.951301+00
```

### API Endpoint Testing

**1. Health Check**:
```bash
curl http://localhost:8000/health
```

**2. Login and Get Token**:
```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo_user&password=demo123"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**3. Get Current User with TikTok Data**:
```bash
TOKEN="<access_token_from_above>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/users/me | jq
```

**Response**:
```json
{
  "email": "demo@tiktimer.com",
  "username": "demo_user",
  "id": 2,
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-09-03T22:57:45.108518Z",
  "tiktok_access_token": "act.kmxQteBXre47hSURgIs695JbOrj1o30mxNZpZVCPbH2cJktU7k0rdC8rVt9B!6391.u1",
  "tiktok_open_id": "-000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB",
  "tiktok_token_expires_at": "2025-10-20T14:15:37.951301Z"
}
```

**4. Get TikTok Authorization URL**:
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/tiktok/authorize | jq
```

**5. Disconnect TikTok**:
```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/tiktok/disconnect
```

### Frontend Testing Checklist

**Test User Accounts**:
- `demo_user` / `demo123`
- `oauth_test` / `TestPassword123`

**Complete OAuth Flow Test**:

1. ✅ Open https://drds1j9h9dec0.cloudfront.net
2. ✅ Login with `demo_user` / `demo123`
3. ✅ Dashboard shows "TikTok Not Connected"
4. ✅ Click "Connect TikTok Account"
5. ✅ Redirect to TikTok authorization page
6. ✅ Login to TikTok with `reef0703` account
7. ✅ See permission request for `user.info.basic` and `video.publish`
8. ✅ Click "Authorize"
9. ✅ Redirect to callback page showing "Success!" message
10. ✅ Auto-redirect to dashboard after 2 seconds
11. ✅ Dashboard shows:
    - Green indicator
    - "Connected to TikTok"
    - Account ID: `-000f-GlBELY4AmwEdlJy7xlaLn8Ah7YJQlB`
    - "Disconnect" button enabled

**Disconnect Test**:
1. ✅ Click "Disconnect" button
2. ✅ Confirm in alert dialog
3. ✅ Page refreshes
4. ✅ Dashboard shows "TikTok Not Connected" again

### CloudFront Testing

**Test Static File Serving**:
```bash
# Check HTTP status
curl -s -o /dev/null -w "%{http_code}" https://drds1j9h9dec0.cloudfront.net
# Should return: 200

# Check HTML title
curl -s https://drds1j9h9dec0.cloudfront.net | grep -o '<title>.*</title>'
# Should return: <title>Vite + React + TS</title>

# Check which JS bundle is served
curl -s https://drds1j9h9dec0.cloudfront.net | grep -o "index-[^\"]*\.js"
# Should return: index-C4q7BzzE.js (or latest hash)
```

**Test SPA Routing** (CloudFront custom error response):
```bash
# Direct access to /terms (404 should return index.html)
curl -s https://drds1j9h9dec0.cloudfront.net/terms | grep "Terms of Service"

# Direct access to /privacy
curl -s https://drds1j9h9dec0.cloudfront.net/privacy | grep "Privacy Policy"
```

---

## Key Learnings

### 1. URL Encoding is Critical for OAuth

**Problem**: TikTok rejected OAuth requests with improperly encoded redirect URIs.

**Lesson**: Always use proper URL encoding libraries (`urllib.parse.urlencode` in Python, `URLSearchParams` in JavaScript) instead of manual string concatenation.

**Before**:
```python
query_string = "&".join([f"{k}={v}" for k, v in params.items()])
# redirect_uri=https://example.com/callback  (unencoded ❌)
```

**After**:
```python
query_string = urlencode(params)
# redirect_uri=https%3A%2F%2Fexample.com%2Fcallback  (encoded ✅)
```

### 2. Pydantic Schema Must Match What You Want to Return

**Problem**: Database had TikTok tokens but API wasn't returning them.

**Lesson**: Pydantic response models define what gets serialized. If fields aren't in the schema, they won't appear in the API response even if they exist in the database.

**Always include all fields you need in the frontend** in your response schemas.

### 3. CloudFront Caching Requires Invalidation

**Problem**: Updated React app wasn't loading - users still saw old version.

**Lesson**: CloudFront caches files at edge locations globally. After S3 uploads, you MUST invalidate the cache:
```bash
aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
```

**Invalidation takes 1-2 minutes to propagate**. Use hard refresh (`Ctrl/Cmd + Shift + R`) or incognito window to bypass browser cache.

### 4. CORS Must Include All Origins

**Problem**: Frontend couldn't call backend API due to CORS errors.

**Lesson**: When deploying frontend to a new domain (CloudFront), update backend CORS `allow_origins` list immediately. Browsers enforce same-origin policy strictly.

### 5. Docker Container Restart vs Recreate

**Problem**: Changed `.env` file but container still used old values.

**Lesson**:
- `docker-compose restart` - Restarts container but doesn't reload environment variables
- `docker-compose up -d --force-recreate` - Recreates container with new env vars

**Use recreate when changing environment variables**:
```bash
docker-compose up -d --force-recreate api
```

### 6. Terraform -target for Partial Deployments

**Problem**: Wanted to test frontend without deploying entire infrastructure.

**Lesson**: Terraform's `-target` flag allows deploying specific modules:
```bash
terraform plan -target=module.frontend -out=tfplan-frontend
terraform apply tfplan-frontend
```

**This saved ~$50/month in infrastructure costs** during development/testing phase.

### 7. Sandbox OAuth Requires Test User Whitelisting

**Problem**: OAuth worked with one TikTok account but failed with others.

**Lesson**: In TikTok sandbox mode:
- Only whitelisted "Target Users" can complete OAuth
- Any non-whitelisted account gets `unauthorized_client` error
- Must add test accounts via Developer Portal → Sandbox → Target Users

### 8. OAuth Callback Must Match Backend Route Structure

**Problem**: TikTok redirect worked but frontend showed 404.

**Lesson**: Consider full route path when configuring OAuth:
- Backend route: `API_PREFIX + router.prefix + endpoint`
- Example: `/api/v1` + `/auth/tiktok` + `/callback`
- **Full path**: `/api/v1/auth/tiktok/callback`

**Frontend React Router must match this exact path**.

### 9. Authentication Required for User-Specific Operations

**Problem**: Token exchange saved tokens to wrong user (test_user instead of logged-in user).

**Lesson**: OAuth token exchange endpoint must:
1. Require authentication (`current_user: User = Depends(get_current_active_user)`)
2. Use the authenticated user, not a hardcoded test user
3. Associate tokens with the correct user account

**Never hardcode user lookups for production endpoints**.

### 10. SPA Routing on CloudFront Needs Custom Error Responses

**Problem**: Direct URL access to `/terms` or `/privacy` returned 404.

**Lesson**: CloudFront needs custom error responses for SPA routing:
```hcl
custom_error_response {
  error_code            = 404
  response_code         = 200
  response_page_path    = "/index.html"
  error_caching_min_ttl = 300
}
```

This tells CloudFront to serve `index.html` for 404 errors, allowing React Router to handle client-side routing.

---

## Next Steps

### Immediate (Production Readiness)

1. **Move to Production OAuth**:
   - Switch TikTok app from Sandbox to Production mode
   - Submit app for TikTok review if required
   - Update redirect URIs in production environment
   - Remove test user requirement

2. **Deploy Full Backend to AWS**:
   ```bash
   terraform apply  # Deploy all 68 resources
   ```
   - VPC, RDS, ECS, ALB, ECR
   - Update frontend `VITE_API_URL` to ALB domain
   - Configure environment-specific variables

3. **Implement Token Refresh**:
   - Access tokens expire in 24 hours
   - Refresh tokens valid for 365 days
   - Add background job to refresh tokens before expiry

4. **Add Error Handling**:
   - Handle TikTok API rate limits
   - Retry logic for failed token refreshes
   - User-friendly error messages

### Security Enhancements

1. **Secure Token Storage**:
   - Consider encrypting tokens at rest (currently plaintext in DB)
   - Use AWS KMS or similar for encryption keys
   - Rotate encryption keys periodically

2. **Environment Variables**:
   - Move secrets to AWS Secrets Manager or Parameter Store
   - Remove `.env` file from production
   - Use IAM roles instead of access keys where possible

3. **HTTPS for Backend**:
   - ALB terminates HTTPS
   - Generate/use SSL certificate from ACM
   - Enforce HTTPS-only communication

4. **Rate Limiting**:
   - Add rate limiting to OAuth endpoints
   - Prevent abuse of token exchange endpoint
   - Implement user-based rate limits

### Monitoring & Logging

1. **CloudWatch Logs**:
   - Stream ECS logs to CloudWatch
   - Set up log retention policies
   - Create CloudWatch dashboards

2. **Alerts**:
   - Token refresh failures
   - OAuth error rates
   - API error rates > threshold
   - Database connection issues

3. **Analytics**:
   - Track OAuth conversion rate
   - Monitor TikTok API usage
   - User engagement metrics

### Feature Enhancements

1. **Multi-Platform Support**:
   - Add Instagram, YouTube OAuth
   - Support multiple connected accounts per user
   - Platform-specific post requirements

2. **Post Scheduling Improvements**:
   - Drag-and-drop calendar interface
   - Bulk scheduling
   - Post templates
   - Media upload support

3. **Video Upload**:
   - Implement TikTok video upload flow
   - Video preview and editing
   - Media storage (S3)
   - Upload progress tracking

### Cost Optimization

**Current Infrastructure** (Frontend-only):
- S3: ~$0.50/month (minimal storage)
- CloudFront: ~$1-2/month (low traffic)
- **Total**: ~$2-3/month

**Full Infrastructure** (when deployed):
- VPC NAT Gateway: ~$32/month
- RDS t3.micro: ~$15/month
- ALB: ~$16/month
- ECS Fargate: ~$15/month (1 task)
- S3 + CloudFront: ~$2/month
- **Total**: ~$80-90/month

**Optimization Ideas**:
- Use RDS Reserved Instances (save 40%)
- Replace NAT Gateway with NAT instances (save $25/month)
- Use Spot instances for non-critical tasks
- Implement CloudFront caching policies to reduce origin requests

---

## Commands Reference

### Terraform

```bash
# Plan specific module
terraform plan -target=module.frontend

# Apply with plan file
terraform plan -target=module.frontend -out=tfplan-frontend
terraform apply tfplan-frontend

# View outputs
terraform output

# Destroy specific module
terraform destroy -target=module.frontend
```

### AWS CLI

```bash
# S3 sync with delete
aws s3 sync ./dist s3://bucket-name/ --delete

# CloudFront invalidation
aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"

# Check invalidation status
aws cloudfront get-invalidation --distribution-id <ID> --id <invalidation-id>

# List S3 files
aws s3 ls s3://bucket-name/

# Get CloudFront distribution info
aws cloudfront get-distribution --id <ID>
```

### Docker

```bash
# Restart service
docker-compose restart api

# Recreate with new env vars
docker-compose up -d --force-recreate api

# View logs
docker logs social-media-scheduler-api --tail 50

# Follow logs
docker logs -f social-media-scheduler-api

# Execute command in container
docker exec social-media-scheduler-api python -c "from backend.config import settings; print(settings.API_PREFIX)"

# Database queries
docker exec social-media-scheduler-db psql -U postgres -d scheduler -c "SELECT * FROM users;"
```

### Frontend Development

```bash
# Install dependencies
cd tiktimer-frontend
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Type check
npm run tsc
```

### Testing

```bash
# Get JWT token
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo_user&password=demo123"

# Test authenticated endpoint
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/users/me

# Test health endpoint
curl http://localhost:8000/health

# Test CloudFront
curl -I https://drds1j9h9dec0.cloudfront.net
```

---

## File Changes Summary

### Files Modified

1. **backend/main.py**
   - Added CloudFront domain to CORS `allow_origins`

2. **backend/integrations/tiktok.py**
   - Added `from urllib.parse import urlencode`
   - Updated `get_authorization_url()` to use proper URL encoding

3. **backend/routes/tiktok.py**
   - Updated `/exchange-token` endpoint to require authentication
   - Changed from hardcoded `test_user` to `current_user`

4. **backend/schema.py**
   - Added TikTok fields to `UserResponse`:
     - `tiktok_access_token`
     - `tiktok_open_id`
     - `tiktok_token_expires_at`

5. **.env**
   - Updated `TIKTOK_REDIRECT_URI` to include `/api/v1` prefix

6. **tiktimer-frontend/src/App.tsx**
   - Updated TikTok callback route from `/tiktok/callback` to `/api/v1/auth/tiktok/callback`
   - Added imports for Terms and Privacy pages

7. **tiktimer-frontend/src/pages/TikTokCallbackPage.tsx**
   - Added `useAuth` hook
   - Added `await refreshUser()` call after token exchange

8. **tiktimer-frontend/src/contexts/AuthContext.tsx**
   - Changed ReactNode import to type-only import for TypeScript compatibility

### Files Created

1. **tiktimer-frontend/src/pages/TermsOfServicePage.tsx**
   - Complete Terms of Service page with TikTimer-specific terms

2. **tiktimer-frontend/src/pages/PrivacyPolicyPage.tsx**
   - Complete Privacy Policy page detailing data collection and usage

3. **tiktimer-infrastructure/modules/frontend/variables.tf**
   - Frontend module input variables

4. **tiktimer-infrastructure/modules/frontend/main.tf**
   - S3 bucket configuration
   - CloudFront distribution
   - Origin Access Identity
   - Security policies

5. **tiktimer-infrastructure/modules/frontend/outputs.tf**
   - CloudFront URL
   - S3 bucket name
   - Distribution ID
   - Deployment commands

6. **docs/references/DEPLOYMENT_CHECKLIST.md**
   - Step-by-step deployment guide
   - TikTok OAuth configuration instructions
   - Testing checklist

---

## Conclusion

This session successfully deployed the TikTimer frontend to AWS CloudFront and completed full TikTok OAuth integration in sandbox mode. We encountered and solved 6 major issues, learning valuable lessons about URL encoding, CORS, authentication, schema design, and CloudFront caching.

The application is now ready for sandbox testing with whitelisted TikTok accounts. The next phase will involve moving to production OAuth mode and deploying the full backend infrastructure to AWS.

**Status**: ✅ **Production-ready for sandbox testing**

**Test it**: https://drds1j9h9dec0.cloudfront.net
**Credentials**: `demo_user` / `demo123`
**Test TikTok Account**: `reef0703`
