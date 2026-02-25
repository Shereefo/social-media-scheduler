# TikTimer — Architecture & Design Rationale

**Scope:** Infrastructure and identity hardening (Phases 1–5)
**Audience:** Engineers joining the project, future-self code review, portfolio reference

> This document explains *why* the system is designed the way it is. For *what* changed file-by-file, see [CHANGES.md](./CHANGES.md). For setup and API usage, see the root [README](../README.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Threat Model](#threat-model)
3. [Secret Management](#secret-management)
4. [CI/CD Authentication](#cicd-authentication)
5. [Identity & Authentication](#identity--authentication)
6. [Observability](#observability)
7. [Infrastructure Layers](#infrastructure-layers)
8. [Design Trade-offs](#design-trade-offs)
9. [Future Work](#future-work)

---

## System Overview

TikTimer is a FastAPI application that schedules and publishes TikTok content. After the hardening work, the full request path looks like this:

```
Internet
    │
    ▼
AWS WAF (edge — blocks SQLi, rate limits scrapers)
    │
    ▼
Application Load Balancer (public subnet, HTTPS termination)
    │
    ▼
ECS Fargate task — FastAPI app (private subnet, no public IP)
    │               │
    │               ├── AWS Secrets Manager  (credentials at boot)
    │               └── Amazon S3            (video uploads)
    │
    ▼
Amazon RDS PostgreSQL (db subnet, accepts traffic only from ECS SG)
```

Key properties of this design:

- **No compute has a public IP.** ECS tasks live in a private subnet. Traffic in from the internet must pass through the ALB, which is the only public-facing component.
- **No credential ever appears in a task definition, Terraform state, or environment variable file.** Credentials are resolved by ECS at container start via Secrets Manager.
- **No long-lived AWS credentials exist in GitHub.** The CD pipeline authenticates using short-lived OIDC tokens.
- **Logout is real.** A `POST /auth/logout` call immediately invalidates all outstanding JWTs for that user without a database blocklist table.

---

## Threat Model

These are the specific risks the hardening work was designed to address, in rough priority order:

| Risk | What could go wrong | Mitigation |
|------|---------------------|------------|
| Leaked static AWS keys | A `git log` or CI log line exposes `AWS_ACCESS_KEY_ID`. Attacker gets long-term AWS access. | Replaced with OIDC short-lived tokens scoped to exactly this repo. |
| Credentials in Terraform state | S3 + CloudTrail shows plaintext DB passwords in state file reads. | Credentials now live only in Secrets Manager. Terraform state holds ARNs, not values. |
| Stolen JWT with no logout | User logs out on device A. Stolen token on device B remains valid for up to 30 minutes. | `token_version` counter: logout increments it; `get_current_user` rejects tokens carrying the old version. |
| Refresh token theft and replay | Attacker intercepts a refresh token and keeps issuing new access tokens indefinitely. | Rotation: each use of a refresh token atomically invalidates the previous one. Replaying a used token returns 401. |
| Insecure startup defaults | `SECRET_KEY` fallback of `"your-secret-key-needs-to-be-updated"` means a misconfigured deploy runs silently with a known signing key. | Fallback removed entirely. Missing `SECRET_KEY` or `DATABASE_URL` causes a startup crash. |
| Bearer token in API response | `GET /users/me` was returning the live TikTok access token in the JSON body. | `tiktok_access_token` removed from `UserResponse`. |
| Privilege escalation | No role model — only a boolean `is_superuser` with no scoped enforcement at endpoints. | `UserRole` enum (`user` / `admin`) added, enforced by `get_current_admin_user` FastAPI dependency. |
| No visibility into production | No alarms — an ECS crash or RDS storage exhaustion would be silent until users complained. | 9 CloudWatch alarms across all three tiers, routed to SNS email. |

---

## Secret Management

### The problem with environment variables in task definitions

The original design passed credentials as plaintext ECS environment variables:

```hcl
environment = [
  { name = "DATABASE_URL", value = "postgresql://user:password@host/db" }
]
```

This is insecure in several ways:
- The plaintext value is stored in the ECS task definition document, which anyone with `ecs:DescribeTaskDefinition` can read.
- The value ends up in Terraform state, so every team member with S3 read access sees the credential.
- Task definition history retains old values even after rotation.

### The solution: ECS native secret injection

Credentials now live in AWS Secrets Manager as JSON blobs:

```
/tiktimer/dev/app-secrets
{
  "SECRET_KEY": "...",
  "TIKTOK_CLIENT_KEY": "...",
  "TIKTOK_CLIENT_SECRET": "..."
}

/tiktimer/dev/db-credentials
{
  "username": "...",
  "password": "...",
  "host": "...",
  "url": "postgresql+asyncpg://..."
}
```

ECS resolves these at task launch time using the `valueFrom` JSON key selector syntax:

```hcl
secrets = [
  { name = "DATABASE_URL", valueFrom = "${var.db_secret_arn}:url::" },
  { name = "SECRET_KEY",   valueFrom = "${var.app_secret_arn}:SECRET_KEY::" }
]
```

The injected value is available inside the container as a normal environment variable — the application code (`config.py`, `database.py`) does not need to change. The plaintext value is never written to the task definition document.

### Why JSON blobs rather than individual secrets?

AWS charges per secret (roughly $0.40/secret/month). Storing all app credentials in a single JSON blob means one secret instead of four. The `valueFrom` JSON key selector (`secretARN:key::`) lets ECS extract individual fields at injection time, so the application still sees them as separate environment variables.

The DB credentials secret is structured as a JSON blob intentionally: AWS's native RDS rotation Lambda understands this format. When we eventually enable automatic rotation, the Lambda can update individual fields (`password`, `url`) without changing the secret structure.

---

## CI/CD Authentication

### The problem with static AWS keys in GitHub Secrets

The previous CD pipeline stored `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as GitHub Secrets. These are static credentials that:

- Must be manually rotated, and rotation must be coordinated across multiple places (the IAM user, the GitHub Secret, and any documentation).
- Carry the full permissions of the IAM user — scoping is at the IAM policy level only, not at the credential level.
- If a leaked log line or a malicious workflow fork captures them, they remain valid until manually revoked.

### The solution: GitHub Actions OIDC

GitHub can act as an OIDC identity provider. When a GitHub Actions runner starts, it can request a short-lived OIDC token from GitHub's token issuer (`https://token.actions.githubusercontent.com`). AWS can be configured to trust this issuer and allow AWS roles to be assumed via `AssumeRoleWithWebIdentity`.

The resulting design:

```
GitHub Actions runner
    │
    │  Request OIDC token (JWT signed by GitHub)
    ▼
GitHub OIDC issuer
    │
    │  Signed JWT (iss: token.actions.githubusercontent.com,
    │              sub: repo:Shereefo/social-media-scheduler:ref:refs/heads/main)
    ▼
AWS STS AssumeRoleWithWebIdentity
    │
    │  Validates: iss matches registered OIDC provider
    │             sub matches trust policy condition
    │             Token not expired (15 minutes max)
    ▼
Short-lived session credentials (valid for the duration of the job only)
```

The trust policy condition `"StringLike": {"token.actions.githubusercontent.com:sub": "repo:Shereefo/social-media-scheduler:*"}` means no other GitHub repository — even one in the same organization — can assume this role. The session credentials expire when the job ends, so there is nothing to leak or rotate.

### The IAM role is least-privilege

The inline policy on the GitHub Actions role grants exactly what the CD pipeline needs: ECR push/pull, ECS service update, ECS run-task for migrations, IAM PassRole scoped to the task execution role, ALB describe, and CloudWatch log reads. No `*` resource wildcards except where AWS requires it by design (`ecr:GetAuthorizationToken` is an account-level action).

---

## Identity & Authentication

### Access tokens: short-lived with embedded version

JWTs are signed HS256 tokens with a 30-minute expiry. The payload carries a `version` claim matching the user's current `token_version` database column:

```json
{
  "sub": "shereef",
  "version": 3,
  "exp": 1740000000
}
```

`get_current_user` validates the token signature, checks expiry (handled by the JWT library), then fetches the user row and compares `payload["version"]` against `user.token_version`. If they don't match, the token is rejected with 401 — even if the signature and expiry are valid.

This provides **stateless revocation without a blocklist table**. A blocklist would require a cache or database lookup on every authenticated request and would need TTL management to avoid growing indefinitely. The version counter achieves the same result: logout increments the counter once, and all old tokens are simultaneously invalid at the cost of a single extra integer comparison per request.

### Refresh tokens: rotation with bcrypt hash storage

Refresh tokens are long-lived (7 days) and stored as bcrypt hashes, never as raw values. The lifecycle:

```
Login
  → generate secrets.token_urlsafe(32)   [32 bytes = 256 bits of entropy]
  → store bcrypt(raw) in users.refresh_token_hash
  → return raw to client

Refresh
  → client presents raw token
  → fetch user row, verify raw against stored hash
  → if valid: generate new raw, overwrite hash, return new raw
  → old raw is now invalid (hash was overwritten)

Logout
  → increment token_version (invalidates all JWTs)
  → clear refresh_token_hash (invalidates refresh token)
```

The rotation step is atomic: the old hash is overwritten in the same transaction that stores the new hash. This means a refresh token can only be used once. If an attacker captures a refresh token in transit, they have a narrow window — using the token before the legitimate client does invalidates it, and the legitimate client's next refresh attempt will also return 401, alerting the user.

### Why bcrypt for refresh tokens?

If an attacker gains read access to the database (e.g., via SQL injection, a compromised backup, or a misconfigured RDS snapshot), raw refresh tokens in the DB would let them impersonate users immediately. Bcrypt hashes are computationally expensive to reverse and are salted, so even a complete DB dump is not immediately useful.

Access tokens don't need to be stored at all — they're validated by the JWT signature, not by a DB lookup.

---

## Observability

### Alarm design philosophy

The 9 alarms were chosen to cover the three failure modes that matter most in a containerized API:

1. **The compute tier crashed** — ECS running task count < 1. This alarm uses `treat_missing_data = "breaching"` because if CloudWatch stops receiving this metric, it usually means ECS itself has a problem. You want to know about silence, not just bad values.

2. **The compute tier is overwhelmed** — ECS CPU > 85%, ECS memory > 85%. These give advance warning before tasks start being OOM-killed or throttled.

3. **The load balancer is returning errors** — ALB 5xx count > 10/min, ALB unhealthy host count > 0. 5xx from the ALB can mean application errors or the ECS task stopped responding to health checks.

4. **The load balancer is slow** — ALB p99 latency > 2s. P99 rather than average because averages hide tail latency. A database query that's slow for 1% of requests is invisible in average latency but affects real users.

5. **The database is under stress** — RDS CPU > 80%, connection count > 70 (approaching the default PostgreSQL limit of 100 for `db.t3.micro`), free storage < 2 GiB.

All alarms route to a single SNS topic with an email subscription. A future improvement would be to route high-severity alarms (task count crash, unhealthy hosts) to a separate SNS topic with PagerDuty integration.

### Why a separate monitoring module?

The monitoring module takes metric dimension names (ECS cluster name, ALB ARN suffix, RDS instance identifier) as inputs and produces no dependencies that other modules require. This makes it purely additive — it can be removed with no impact on the rest of the stack, and it can be deployed or destroyed independently. Keeping observability concerns separate from compute/database/networking concerns also makes it easier to adjust thresholds without touching core infrastructure.

---

## Infrastructure Layers

### Network isolation

The VPC uses a three-tier subnet design:

```
Public subnets    — ALB only. Anything with a public IP lives here.
Private subnets   — ECS tasks. No public IP, outbound via NAT Gateway.
DB subnets        — RDS. No outbound internet path at all.
```

Security group rules enforce this strictly:
- The DB security group only accepts connections from the ECS task security group. Direct developer access to RDS requires a bastion or SSM Session Manager.
- The ECS task security group only accepts connections from the ALB security group. No direct access to the API from the internet.
- The ALB security group accepts HTTPS (443) from `0.0.0.0/0`.

This means a compromise of the ALB does not give direct database access — the attacker would also need to compromise an ECS task or its security group.

### Terraform state

Terraform state lives in S3 with versioning enabled and server-side encryption (SSE-S3). State locking uses a DynamoDB table — this prevents two operators from running `terraform apply` concurrently, which could corrupt state.

The bootstrap bucket and lock table are managed by a separate `bootstrap-state/` module that uses local state. This avoids the chicken-and-egg problem of needing remote state to create remote state. Once created, the bootstrap resources should be left alone — they are never destroyed by `terraform destroy` on the main configuration.

---

## Design Trade-offs

These are choices where an alternative was deliberately rejected:

### OIDC trust policy: `*` on the ref vs branch-specific

The trust policy uses `repo:Shereefo/social-media-scheduler:*` to match any branch or tag. A stricter version would be `repo:Shereefo/social-media-scheduler:ref:refs/heads/main` (production deploys from `main` only).

The `*` pattern was chosen because the CD pipeline needs to build Docker images on feature branches for preview environments. If the CD pipeline ever gains production-deploy capability (e.g., blue/green release), the trust policy should be narrowed to `refs/heads/main` and the build-only steps should use a separate role.

### Single refresh token per user

The current schema stores one `refresh_token_hash` per user, meaning a second login overwrites the first refresh token. On mobile + web combinations, this forces a re-login on one device when the other logs in.

A multi-device model would use a `refresh_tokens` table with one row per device, each with its own hash and expiry. This was not implemented because TikTimer's current user base is single-device per creator account. It's documented here as the natural next step if the product adds multi-device support.

### `/auth/refresh` scans all users

The current implementation scans all users with a non-null `refresh_token_hash` to find the token owner. This is O(n) in the number of logged-in users and will become a problem at scale.

The clean fix is to add the `username` to the `RefreshRequest` body so the endpoint can look up the user directly. This was not done to avoid coupling the client to knowing the username at the time of refresh — a design that is fine but requires a small schema change to the refresh request. It is documented in the architecture review as a known gap, not a hard bug.

### WAF, GuardDuty, Security Hub off by default

These are provisioned by the `modules/security/` module but disabled via feature flags (`enable_waf = false`, etc.) for the dev environment. The reason is cost: WAF adds roughly $20/month, GuardDuty adds $15–65/month, and Security Hub adds $2–15/month. For a single-developer dev environment with no live user traffic, these costs are not justified.

The pattern is intentional: the infrastructure code exists and is validated, so enabling them for a production environment is a one-line change in `terraform.tfvars`.

---

## Future Work

These items are known gaps, in priority order:

| Item | Why it matters | Effort |
|------|---------------|--------|
| Multi-device refresh tokens (`refresh_tokens` table) | Single-token-per-user forces re-login on second device | Medium |
| Add `username` to `RefreshRequest` | Eliminates O(n) scan on `/auth/refresh` | Small |
| TikTok token encryption at rest | TikTok access/refresh tokens currently stored plaintext in RDS | Medium |
| HTTPS on ALB with ACM certificate | ALB currently terminates HTTP — needs Route 53 + ACM for production | Medium |
| Narrow OIDC trust policy to `refs/heads/main` | Once feature branch previews are separated from production deploys | Small |
| Enable WAF + GuardDuty for production environment | Controlled by feature flags, zero code changes required | Small |
| PagerDuty / Slack integration on SNS | Replace email-only alerts with on-call routing | Small |
| Reserved Instances for production RDS | `db.t3.micro` on-demand costs ~$15/month; 1-year RI reduces to ~$8 | Small (billing) |
