# TikTimer Infrastructure

This Terraform root now expects a remote backend (S3 + DynamoDB locking) and environment-specific config.

## 1) Bootstrap remote state resources

The backend resources are managed separately to avoid the backend self-reference problem.

```bash
cd tiktimer-infrastructure/bootstrap-state
terraform init
terraform apply \
  -var="project_name=tiktimer" \
  -var="environment=shared" \
  -var="aws_region=us-east-2"
```

Capture outputs:
- `state_bucket_name`
- `lock_table_name`

## 2) Create environment backend files

Copy and edit the backend templates:

```bash
cd tiktimer-infrastructure
for env in dev staging prod; do
  cp "environments/backend-${env}.hcl.example" "environments/backend-${env}.hcl"
done
```

Set:
- `bucket` to the bootstrap `state_bucket_name`
- `dynamodb_table` to the bootstrap `lock_table_name`
- `key` unique per environment

## 3) Create environment tfvars files

Copy and adjust each tfvars template:

```bash
cd tiktimer-infrastructure
for env in dev staging prod; do
  cp "environments/${env}.tfvars.example" "environments/${env}.tfvars"
done
```

Keep secrets out of tfvars committed to git.

## 4) Initialize and deploy per environment

```bash
cd tiktimer-infrastructure

# Dev
terraform init -reconfigure -backend-config=environments/backend-dev.hcl
terraform workspace select dev || terraform workspace new dev
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars

# Staging
terraform init -reconfigure -backend-config=environments/backend-staging.hcl
terraform workspace select staging || terraform workspace new staging
terraform plan -var-file=environments/staging.tfvars
terraform apply -var-file=environments/staging.tfvars

# Prod
terraform init -reconfigure -backend-config=environments/backend-prod.hcl
terraform workspace select prod || terraform workspace new prod
terraform plan -var-file=environments/prod.tfvars
terraform apply -var-file=environments/prod.tfvars
```

## 5) Migrate existing local state

If you already deployed with local state, migrate once for each environment:

```bash
cd tiktimer-infrastructure
terraform init -migrate-state -backend-config=environments/backend-dev.hcl
```

Run this in the correct workspace and with the matching tfvars for each environment.

## Notes

- Root module requires `environment` to be one of `dev`, `staging`, or `prod`.
- `*.tfvars` remains git-ignored by design.
- Remote backend config files (`backend-*.hcl`) should also stay uncommitted if they include account-specific values.
