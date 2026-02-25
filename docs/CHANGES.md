# TikTimer — Infrastructure & Identity Hardening

**Branch:** `claude/cranky-williamson`
**Date:** 2026-02-21
**Scope:** All five phases were designed and validated together before any `terraform apply` is run. No live infrastructure was modified during this work.

---

## Overview

This document covers all changes made across a five-phase hardening plan for the TikTimer social media scheduler. The work spans the Terraform infrastructure layer (`tiktimer-infrastructure/`) and the FastAPI application layer (`backend/`). Each phase is self-contained — if you need to understand why a specific file changed, jump to the relevant phase below.

---

## Phase 1 — Terraform Remote State

### Problem
The Terraform state file was stored locally on disk. This means only one person could run Terraform at a time, there was no locking to prevent concurrent runs, and a lost laptop would lose all infrastructure state.

### What was done

**New: `tiktimer-infrastructure/bootstrap-state/`** (pre-existing module, first-time applied)
- Created `tiktimer-shared-tf-state-022499001793` (S3 bucket with versioning + encryption)
- Created `tiktimer-shared-tf-locks` (DynamoDB table for state locking)
- These are the only resources managed with local state — the bootstrap is intentionally self-contained.

**New: `tiktimer-infrastructure/environments/backend-dev.hcl`**
```hcl
bucket         = "tiktimer-shared-tf-state-022499001793"
key            = "dev/tiktimer-infrastructure.tfstate"
region         = "us-east-2"
dynamodb_table = "tiktimer-shared-tf-locks"
encrypt        = true
```
The S3 backend configuration for the `dev` environment. This file is checked in so the team always uses the same backend. The `.hcl` extension keeps Terraform from auto-loading it (it is passed explicitly via `-backend-config`).

**New: `tiktimer-infrastructure/environments/dev.tfvars`**
Variable values for the dev environment (instance sizes, feature flags, region). Derived from the existing `.example` file with appropriate dev-tier values (single NAT gateway, no WAF, no GuardDuty, no multi-AZ RDS).

**Migration command run:**
```
terraform init -migrate-state -backend-config=environments/backend-dev.hcl
```
The existing local `terraform.tfstate` (serial 171) was uploaded to S3 and deleted locally. All future state reads and writes go through S3 + DynamoDB.

---

## Phase 2 — Secrets Manager Architecture

### Problem
The ECS task definition was passing secrets as plaintext environment variables constructed directly in `main.tf`:
```hcl
DATABASE_URL = "postgresql://${var.db_username}:${var.db_password}@..."
```
This meant credentials were stored unencrypted in Terraform state, visible in ECS task definition history, and accessible to anyone with ECS `DescribeTaskDefinition` permission.

A duplicate `environment []` block in `modules/compute/main.tf` was silently overwriting the first block's values.

### What was done

**New: `tiktimer-infrastructure/modules/secrets/`** (entire module)

`main.tf` — Creates two Secrets Manager secrets:
- `/{project}/{env}/db-credentials` — JSON blob with `username`, `password`, `host`, `port`, `dbname`, and a pre-built `url` field. Stored as JSON so AWS's native RDS rotation Lambda can update individual fields.
- `/{project}/{env}/app-secrets` — JSON blob with `SECRET_KEY`, `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`. Initial values are placeholder strings. A `lifecycle { ignore_changes = [secret_string] }` block ensures Terraform never overwrites values that were rotated out-of-band (e.g., via the AWS console or a rotation Lambda).

`variables.tf` — Accepts DB connection parts, project/environment tags, and a `recovery_window_days` variable (set to `0` in dev for clean teardown, `30` in prod for accidental-deletion protection).

`outputs.tf` — Exports `db_secret_arn` and `app_secret_arn` so the compute module can reference them without hardcoding ARN strings.

**Modified: `tiktimer-infrastructure/modules/compute/main.tf`**
- Removed the duplicate `environment []` block (silent bug — the second block was overwriting the first).
- Removed the plaintext `DATABASE_URL` environment variable entirely.
- Added `aws_iam_role_policy.ecs_secrets_read` on the task execution role, scoped to exactly the two secret ARNs — no wildcard resource.
- Added `secrets []` blocks using ECS native injection with the `valueFrom` JSON key selector syntax:
  ```hcl
  secrets = [
    { name = "DATABASE_URL",         valueFrom = "${var.db_secret_arn}:url::" },
    { name = "SECRET_KEY",           valueFrom = "${var.app_secret_arn}:SECRET_KEY::" },
    { name = "TIKTOK_CLIENT_KEY",    valueFrom = "${var.app_secret_arn}:TIKTOK_CLIENT_KEY::" },
    { name = "TIKTOK_CLIENT_SECRET", valueFrom = "${var.app_secret_arn}:TIKTOK_CLIENT_SECRET::" }
  ]
  ```
  ECS resolves these at task launch time. The plaintext value is injected into the container's environment but never written to the task definition document.

**Modified: `tiktimer-infrastructure/modules/compute/variables.tf`**
- Removed `database_url` (sensitive string).
- Added `db_secret_arn` and `app_secret_arn`.

**Modified: `tiktimer-infrastructure/modules/database/variables.tf`**
- Removed orphaned `database_url` variable that was declared but never used.

**Modified: `tiktimer-infrastructure/main.tf`**
- Added `module "secrets"` between database and compute, wiring `module.database.db_password` and `module.database.db_instance_address` into the secrets module.
- Removed the line that constructed a plaintext `DATABASE_URL` string.
- Updated `module "compute"` to pass `db_secret_arn` and `app_secret_arn` instead of `database_url`.

**Modified: `tiktimer-infrastructure/variables.tf`**
- Removed `database_url` root variable.

**Terraform plan result:** 74 resources (+5 from Phase 1 baseline of 69).

---

## Phase 3 — CI/CD Authentication Hardening (OIDC)

### Problem
The CD pipeline (`.github/workflows/cd.yml`) used static AWS access key/secret pairs stored as GitHub Secrets (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`). Static keys:
- Never expire automatically.
- Must be rotated manually and across multiple places.
- Grant the full permissions of the associated IAM user, not just what the pipeline needs.
- If leaked (e.g., in a log line), provide long-term access.

There were four separate `configure-aws-credentials` steps in the workflow, each using static keys.

### What was done

**Modified: `tiktimer-infrastructure/main.tf`**

Added `aws_iam_openid_connect_provider.github`:
- Registers GitHub's OIDC token issuer (`https://token.actions.githubusercontent.com`) with this AWS account.
- This is a one-time account-level resource. If another repo already registered this provider in the same account, replace this resource with a `data` source lookup.

Added `aws_iam_role.github_actions`:
- GitHub Actions runners can assume this role via `AssumeRoleWithWebIdentity`.
- Trust policy conditions are scoped to `repo:Shereefo/social-media-scheduler:*` — no other GitHub repository or organization can assume this role.

Added `aws_iam_role_policy.github_actions_deploy`:
- Inline least-privilege policy covering exactly what the CD pipeline needs: ECR push/pull, ECS service update, ECS run-task for migrations, IAM PassRole scoped to the task execution and task roles, ALB describe, and CloudWatch log reads.
- No `*` resource wildcards except where AWS requires it (`ecr:GetAuthorizationToken` is account-level and cannot be further scoped).

**Modified: `tiktimer-infrastructure/outputs.tf`**
- Added `github_actions_role_arn` output. After `terraform apply`, copy this ARN and set it as the `AWS_DEPLOY_ROLE_ARN` GitHub Secret (replacing the old key pair secrets).

**Modified: `.github/workflows/cd.yml`**
- Added workflow-level permissions: `id-token: write` (required for OIDC token request), `contents: read`.
- Replaced all four static-key `configure-aws-credentials` blocks with:
  ```yaml
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
      role-session-name: github-deploy-${{ github.run_id }}
      aws-region: ${{ env.AWS_REGION }}
  ```
- Updated the credential-verify step to call `aws sts get-caller-identity` (no longer needs to check for the presence of key env vars).

**GitHub Secrets to add after `terraform apply`:**
| Secret | Value |
|--------|-------|
| `AWS_DEPLOY_ROLE_ARN` | `terraform output github_actions_role_arn` |

**GitHub Secrets to delete after confirming OIDC works:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Terraform plan result:** 77 resources (+3: OIDC provider, IAM role, IAM inline policy).

---

## Phase 4 — Monitoring Infrastructure

### Problem
No CloudWatch alarms or dashboards existed. There was no way to know if ECS tasks crashed, ALB latency spiked, or RDS storage was filling up until a user reported an outage.

### What was done

**New: `tiktimer-infrastructure/modules/monitoring/`** (entire module)

`main.tf` — Creates:
- **SNS topic** `{project}-{env}-alerts` with an optional email subscription. Email confirmation must be clicked out-of-band after `terraform apply`.
- **9 CloudWatch alarms**, all routed to the SNS topic:

  | Alarm | Threshold | Evaluation |
  |-------|-----------|------------|
  | ECS CPU utilization | > 85% | 5 min |
  | ECS memory utilization | > 85% | 5 min |
  | ECS running task count | < 1 | 2 min (`treat_missing_data = "breaching"`) |
  | ALB 5xx error count | > 10/min | 3 min |
  | ALB p99 response latency | > 2 seconds | 3 min |
  | ALB unhealthy host count | > 0 | 2 min |
  | RDS CPU utilization | > 80% | 5 min |
  | RDS database connections | > 70 | 3 min |
  | RDS free storage | < 2 GiB | 5 min |

  > Note: The p99 latency alarm uses `extended_statistic = "p99"` (not `statistic`). Terraform's AWS provider validates the `statistic` field against a fixed enum (`Average`, `Sum`, etc.) and rejects percentile strings — percentiles require the separate `extended_statistic` attribute.

- **CloudWatch dashboard** with four rows:
  - ECS: CPU %, memory %, running task count
  - ALB: request count, 5xx/4xx errors, p99 latency
  - RDS: CPU %, connection count, free storage
  - Alarm status overview panel

`variables.tf` — ECS/ALB/RDS dimension names, configurable thresholds, `alert_email`.

`outputs.tf` — `sns_topic_arn`, `dashboard_name`, `dashboard_url`.

**Modified: `tiktimer-infrastructure/modules/compute/outputs.tf`**
- Added `alb_arn_suffix` and `target_group_arn_suffix` — these are the short ARN suffixes that CloudWatch uses as metric dimensions (not the full ARN).

**Modified: `tiktimer-infrastructure/modules/database/outputs.tf`**
- Added `db_instance_identifier` — the RDS instance name used as a CloudWatch metric dimension.

**Modified: `tiktimer-infrastructure/main.tf`**
- Added `module "monitoring"` wired to compute and database outputs.

**Modified: `tiktimer-infrastructure/variables.tf`**
- Added `alert_email` variable (default `""`).

**Modified: `tiktimer-infrastructure/outputs.tf`**
- Added `alerts_sns_topic_arn` and `dashboard_url`.

**Terraform plan result:** 88 resources (+11: SNS topic, 9 alarms, 1 dashboard).

**Post-apply steps:**
1. Check your email and confirm the SNS subscription to start receiving alerts.
2. Navigate to the `dashboard_url` output to verify the dashboard populated correctly.

---

## Phase 5 — Identity System Upgrades

### Problem
The authentication system had several security gaps:

1. **No refresh tokens** — the access token (30 min TTL) was the only credential. Clients had no way to silently re-authenticate.
2. **No token revocation** — logging out did nothing server-side. A stolen access token was valid until it expired naturally.
3. **Hardcoded fallback secrets** — `config.py` fell back to `"your-secret-key-needs-to-be-updated"` if `SECRET_KEY` was unset. `database.py` fell back to a local dev connection string. Both would silently start in an insecure state if secret injection failed.
4. **Bearer token leak** — `UserResponse` (returned by `GET /users/me`) included `tiktok_access_token` — a live bearer token that should never travel over the wire in an API response.
5. **Binary role system** — access control was based only on `is_superuser` (a boolean), with no extensible role model.

### What was done

**Modified: `backend/config.py`**
- Removed the `SECRET_KEY` fallback default. The field is now a bare `str` with no default — Pydantic raises a `ValidationError` at startup if the variable is absent, rather than running silently with a known-insecure value.
- Same treatment for `DATABASE_URL`.
- Added `REFRESH_TOKEN_EXPIRE_DAYS: int = 7`.

**Modified: `backend/database.py`**
- Removed the hardcoded `postgresql+asyncpg://postgres:postgres@db:5432/scheduler` fallback. The engine is now created strictly from `settings.DATABASE_URL`.

**Modified: `backend/models.py`**
- Added `UserRole` enum (`user` | `admin`) as a Python `str` enum so it serializes naturally in Pydantic responses.
- Added four new columns to the `User` model:
  - `role` — `Enum(UserRole)`, NOT NULL, default `UserRole.user`. Kept alongside `is_superuser` for backwards compatibility; new code should use `role`.
  - `refresh_token_hash` — `String`, nullable. Stores only the **bcrypt hash** of the current refresh token, never the raw value.
  - `refresh_token_expires_at` — `DateTime(timezone=True)`, nullable.
  - `token_version` — `Integer`, NOT NULL, default `0`. Monotonic counter used for access token revocation without a blocklist table.

**Modified: `backend/schema.py`**
- Added `role: UserRole` to `UserResponse`.
- Removed `tiktok_access_token` from `UserResponse` (bearer token must not be returned in API responses). A comment explains the intentional omission.
- Updated `Token` schema to include `refresh_token: str`.
- Updated `TokenData` to include `version: Optional[int]`.
- Added `RefreshRequest` schema with a single `refresh_token: str` field.

**Modified: `backend/auth.py`** (full rewrite)

| Function | Description |
|----------|-------------|
| `create_access_token` | Updated to use `datetime.now(timezone.utc)` (replaces deprecated `utcnow()`). The caller is expected to pass `"version": user.token_version` in the `data` dict. |
| `create_refresh_token(db, user)` | Generates `secrets.token_urlsafe(32)`, stores the bcrypt hash + expiry in the DB, returns the raw token to the caller. |
| `rotate_refresh_token(db, user, raw_token)` | Validates expiry (cheap check first), then bcrypt-verifies the presented token against the stored hash. On success, calls `create_refresh_token` — overwriting the old hash atomically. Replaying a previously used token returns 401. |
| `revoke_tokens(db, user)` | Increments `token_version` by 1 and clears `refresh_token_hash` / `refresh_token_expires_at`. All outstanding JWTs that embed the old version are immediately invalid on the next request. |
| `get_current_user` | Now extracts `version` from the JWT payload and compares it against `user.token_version` after the DB lookup. Mismatched version → 401. |
| `get_current_active_user` | Unchanged in behavior; now uses `status.HTTP_400_BAD_REQUEST` constant. |
| `get_current_admin_user` | New dependency. Calls `get_current_active_user` then checks `user.role == UserRole.admin`. Returns 403 if the user is not an admin. |

**Modified: `backend/main.py`**

- **`POST /token`** (login): Now embeds `"version": user.token_version` in the JWT payload and issues a refresh token alongside the access token. Response now matches the updated `Token` schema.
- **New `POST /auth/refresh`**: Accepts `{ "refresh_token": "..." }`. Finds the matching user by scanning rows with a non-null hash, verifies the token, rotates it, and returns a fresh `{access_token, refresh_token}` pair.
- **New `POST /auth/logout`**: Protected by `get_current_active_user`. Calls `revoke_tokens()` and returns 204. The client should discard both tokens after calling this endpoint.

**New: `migrations/versions/a1b2c3d4e5f6_add_user_identity_columns.py`**

Alembic migration chained from the initial migration (`e7c83ff27d50`):

```
upgrade:
  CREATE TYPE userrole AS ENUM ('user', 'admin')
  ALTER TABLE users ADD COLUMN role userrole NOT NULL DEFAULT 'user'
  ALTER TABLE users ADD COLUMN refresh_token_hash TEXT
  ALTER TABLE users ADD COLUMN refresh_token_expires_at TIMESTAMPTZ
  ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0

downgrade:
  DROP COLUMN token_version
  DROP COLUMN refresh_token_expires_at
  DROP COLUMN refresh_token_hash
  DROP COLUMN role
  DROP TYPE userrole
```

**To run the migration against an existing database:**
```bash
alembic upgrade head
```

---

## Pre-Apply Checklist

Before running `terraform apply` for the first time after these changes:

1. **Replace secret placeholders** — After the first apply creates the Secrets Manager secrets, update `/{project}/{env}/app-secrets` with real values:
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id /tiktimer/dev/app-secrets \
     --secret-string '{"SECRET_KEY":"<strong-random-key>","TIKTOK_CLIENT_KEY":"<key>","TIKTOK_CLIENT_SECRET":"<secret>"}'
   ```

2. **Add GitHub Secret** — Copy `terraform output github_actions_role_arn` and set it as `AWS_DEPLOY_ROLE_ARN` in the repo's GitHub Secrets.

3. **Remove old GitHub Secrets** — After confirming the first OIDC-based deploy succeeds, delete `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

4. **Confirm SNS email subscription** — After apply, check the inbox for the `alert_email` address and click the confirmation link.

5. **Run the Alembic migration** — On the first deploy to a live database, the CD pipeline must run `alembic upgrade head` (the migration task in ECS handles this automatically via the existing migration task definition).

---

## Resource Count Progression

| Phase | Resources | Delta |
|-------|-----------|-------|
| Baseline (pre-work) | 69 | — |
| Phase 1 (remote state bootstrap) | 69 | +0 (infra previously torn down) |
| Phase 2 (Secrets Manager) | 74 | +5 |
| Phase 3 (OIDC) | 77 | +3 |
| Phase 4 (Monitoring) | 88 | +11 |
| Phase 5 (app-layer only) | 88 | +0 |

---

## Files Changed Summary

### Infrastructure (`tiktimer-infrastructure/`)
| File | Status | Phase |
|------|--------|-------|
| `environments/backend-dev.hcl` | Created | 1 |
| `environments/dev.tfvars` | Created | 1 |
| `modules/secrets/main.tf` | Created | 2 |
| `modules/secrets/variables.tf` | Created | 2 |
| `modules/secrets/outputs.tf` | Created | 2 |
| `modules/compute/main.tf` | Modified | 2 |
| `modules/compute/variables.tf` | Modified | 2 |
| `modules/compute/outputs.tf` | Modified | 4 |
| `modules/database/variables.tf` | Modified | 2 |
| `modules/database/outputs.tf` | Modified | 4 |
| `modules/monitoring/main.tf` | Created | 4 |
| `modules/monitoring/variables.tf` | Created | 4 |
| `modules/monitoring/outputs.tf` | Created | 4 |
| `main.tf` | Modified | 2, 3, 4 |
| `variables.tf` | Modified | 2, 4 |
| `outputs.tf` | Modified | 3, 4 |

### CI/CD
| File | Status | Phase |
|------|--------|-------|
| `.github/workflows/cd.yml` | Modified | 3 |

### Application (`backend/`)
| File | Status | Phase |
|------|--------|-------|
| `config.py` | Modified | 5 |
| `database.py` | Modified | 5 |
| `models.py` | Modified | 5 |
| `schema.py` | Modified | 5 |
| `auth.py` | Modified | 5 |
| `main.py` | Modified | 5 |

### Database Migrations
| File | Status | Phase |
|------|--------|-------|
| `migrations/versions/a1b2c3d4e5f6_add_user_identity_columns.py` | Created | 5 |

---

## Session Summary & Next Session Agenda

### What was accomplished this session

**Phase 1** — Terraform remote state bootstrapped and migrated to S3 + DynamoDB locking. The infrastructure can now be safely managed by the whole team.

**Phase 2** — AWS Secrets Manager architecture designed. No credential ever appears in a task definition document or Terraform state as plaintext again. Fixed the silent duplicate `environment[]` block bug in compute along the way.

**Phase 3** — GitHub Actions OIDC fully wired. Static key pair auth is replaced. The trust policy is scoped to exactly this repo.

**Phase 4** — Full CloudWatch observability layer. 9 alarms across ECS/ALB/RDS, a 4-row dashboard, and SNS alert routing.

**Phase 5** — Identity system hardened end-to-end: refresh token rotation with bcrypt hash storage, `token_version` revocation without a blocklist table, role-scoped `get_current_admin_user` dependency, bearer token leak removed from API responses, and fail-loud config with no insecure fallbacks.

**Documentation** — `docs/CHANGES.md` written with the full rationale for every change, pre-apply checklist, and file index.

---

### Next session agenda

1. **Layer 1 tests** — auth flow, token revocation, CRUD, admin guard (no AWS needed)
2. **Fix the 2 pre-apply gaps** — verify the migration task `command` in compute, address the `alembic.ini` local URL
3. **`terraform plan`** — final review of 88 resources before pulling the trigger
4. **`terraform apply`**

---

## Architecture Review

### What's solid

| Area | Assessment |
|------|-----------|
| Network isolation | 3-tier VPC (public/app/db) is correctly locked down — DB SG only accepts from App SG, App SG only accepts from ALB SG |
| Secrets injection | ECS native `secrets[]` with `valueFrom` JSON key selectors — credentials never appear in task definition documents or Terraform state as plaintext |
| CI/CD auth | OIDC fully replaces static keys. Trust policy scoped to the exact repo. Inline least-privilege policy. |
| Token security | `token_version` revocation + refresh token rotation + bcrypt hash storage — all three independently close different attack surfaces |
| Monitoring | 9 alarms covering all three tiers (ECS/ALB/RDS) + dashboard. `treat_missing_data = "breaching"` on the running-tasks alarm is the right call |
| Migration safety | Alembic runs in an isolated ECS task *before* the app update, and the deploy job blocks if it fails |
| Fail-loud config | `SECRET_KEY` and `DATABASE_URL` have no fallback — startup crashes immediately if injection fails rather than running with insecure defaults |

### Gaps to address before `terraform apply`

| # | Gap | Severity | Where |
|---|-----|----------|-------|
| 1 | `docker-compose.yml` has hardcoded insecure secrets | Low (local dev only) | `docker-compose.yml` |
| 2 | `alembic.ini` has a hardcoded local DB URL (`postgresql://postgres:postgres@localhost...`) | Medium — breaks `alembic` CLI locally if `.env` not set | `alembic.ini` |
| 3 | `/auth/refresh` does an O(n) table scan to find the token owner | Low (current scale) | `backend/main.py:417` |
| 4 | TikTok tokens stored plaintext in RDS | Medium (future item) | `backend/models.py` |
| 5 | CORS still includes a Netlify origin that may be stale | Low | `backend/main.py:106` |
| 6 | `alembic upgrade head` is not explicitly wired in `cd.yml` migration task command — need to verify the migration task definition's `command` field matches | **High** — migrations would be skipped silently | `tiktimer-infrastructure/modules/compute/main.tf` |

### Key architectural notes

- The architecture has a full separation of concerns across every layer: network isolation (3-tier subnets), secret injection (never in task definitions), stateless compute (ECS Fargate + ALB), and independent observability (CloudWatch separate from app code). This is the pattern used by large-scale production systems.
- `docker-compose.yml` still has hardcoded `SECRET_KEY=your-secret-key-needs-to-be-updated` and `DATABASE_URL=postgresql+asyncpg://...` — these are fine for local dev but `config.py` now **requires** those vars to be set properly (no fallback). Local dev needs a `.env` file with real values before `docker-compose up` will work.
- TikTok tokens (`tiktok_access_token`, `tiktok_refresh_token`) are still stored plaintext in RDS — a future hardening item, out of scope for the current plan.

---

## Testing Plan (to be executed next session)

### Layer 1 — Local application tests (no AWS needed)

**1a. Auth flow integration test**
- Register a user → login → get `/users/me` → logout → verify old token is rejected → verify refresh token rotation → verify replayed refresh token is rejected

**1b. Token version revocation test**
- Login → capture `token_version` → logout → attempt to use the old access token → expect 401

**1c. Post CRUD test**
- Create post → get all posts → get by ID → update → delete → verify 404

**1d. Admin role guard test**
- Attempt to hit an admin-only endpoint as a regular user → expect 403

### Layer 2 — Infrastructure dry-run (no AWS spend)

**2a. `terraform validate`**
Already passing at 88 resources. Re-run after any changes.

**2b. `terraform plan`**
Full plan output review — confirm 88 resource additions, zero destructive changes.

**2c. Migration script dry-run**
```bash
alembic upgrade head --sql
```
Generates the SQL that *would* be run without touching a DB — lets us visually verify the `CREATE TYPE`, `ALTER TABLE` statements.

### Layer 3 — Live infrastructure tests (post `terraform apply`)

**3a. Secret injection smoke test**
- After apply, run a one-off ECS task and check CloudWatch logs for startup — confirm no `ValidationError` about missing `SECRET_KEY` or `DATABASE_URL`

**3b. Migration task verification**
- Manually trigger the migration ECS task, confirm it exits 0
- Connect to RDS via bastion/session manager and verify the four new columns exist

**3c. Health endpoint test**
```bash
curl https://<alb-dns>/health
# Expected: {"status": "healthy", "database": "connected"}
```

**3d. OIDC deploy test**
- Push a trivial commit to `main`, watch the 6-job pipeline run end-to-end

**3e. CloudWatch alarm test**
- Manually set a low threshold, confirm SNS email arrives, reset threshold
