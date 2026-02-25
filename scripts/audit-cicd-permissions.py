#!/usr/bin/env python3
"""
scripts/audit-cicd-permissions.py
Audit IAM Permissions for GitHub Actions CI/CD Pipeline
Validates that the CI/CD service account has correct permissions for TikTimer deployment
Perfect for IAM admin interviews - shows understanding of least-privilege for automation
"""

import boto3
import json
from datetime import datetime
from tabulate import tabulate


def get_cicd_required_permissions():
    """
    Define the exact permissions GitHub Actions needs for TikTimer deployment
    Based on .github/workflows/cd.yml analysis
    """
    return {
        'ECR - Push Images': [
            'ecr:GetAuthorizationToken',
            'ecr:BatchCheckLayerAvailability',
            'ecr:InitiateLayerUpload',
            'ecr:UploadLayerPart',
            'ecr:CompleteLayerUpload',
            'ecr:PutImage',
            'ecr:DescribeRepositories',
            'ecr:ListImages'
        ],
        'ECS - Deploy Services': [
            'ecs:DescribeClusters',
            'ecs:DescribeServices',
            'ecs:DescribeTaskDefinition',
            'ecs:RegisterTaskDefinition',
            'ecs:UpdateService',
            'ecs:ListTasks',
            'ecs:DescribeTasks'
        ],
        'ELB - Health Checks': [
            'elasticloadbalancing:DescribeLoadBalancers',
            'elasticloadbalancing:DescribeTargetGroups',
            'elasticloadbalancing:DescribeTargetHealth'
        ],
        'IAM - Pass Role to ECS': [
            'iam:PassRole'  # Needed to assign roles to ECS tasks
        ],
        'STS - Verify Identity': [
            'sts:GetCallerIdentity'
        ]
    }


def audit_user_permissions(username):
    """
    Audit what permissions a specific IAM user actually has

    Args:
        username: IAM username (e.g., 'github-actions-tiktimer')
    """
    print("=" * 80)
    print(f"TikTimer CI/CD IAM Permission Audit")
    print("=" * 80)
    print(f"User: {username}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    iam = boto3.client('iam')

    try:
        # 1. Check if user exists
        print("[STEP 1] Checking if user exists...")
        try:
            user_info = iam.get_user(UserName=username)
            print(f"  ✓ User found: {username}")
            print(f"  Created: {user_info['User']['CreateDate'].strftime('%Y-%m-%d')}")
            print()
        except iam.exceptions.NoSuchEntityException:
            print(f"  ✗ ERROR: User '{username}' not found")
            print(f"  Create it with: aws iam create-user --user-name {username}")
            return

        # 2. Check access keys
        print("[STEP 2] Checking access keys...")
        keys_response = iam.list_access_keys(UserName=username)
        access_keys = keys_response['AccessKeyMetadata']

        if not access_keys:
            print(f"  ⚠ WARNING: No access keys found for {username}")
            print(f"  Create one with: aws iam create-access-key --user-name {username}")
        else:
            print(f"  ✓ Found {len(access_keys)} access key(s):")
            for key in access_keys:
                age_days = (datetime.now(key['CreateDate'].tzinfo) - key['CreateDate']).days
                print(f"    - {key['AccessKeyId']}: {key['Status']} (Age: {age_days} days)")

                # Check last usage
                last_used = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                if 'LastUsedDate' in last_used['AccessKeyLastUsed']:
                    last_date = last_used['AccessKeyLastUsed']['LastUsedDate']
                    days_ago = (datetime.now(last_date.tzinfo) - last_date).days
                    region = last_used['AccessKeyLastUsed'].get('Region', 'N/A')
                    print(f"      Last used: {days_ago} days ago in {region}")
                else:
                    print(f"      Last used: Never")
        print()

        # 3. Get user's attached policies
        print("[STEP 3] Checking attached IAM policies...")
        user_policies = iam.list_attached_user_policies(UserName=username)
        attached_policies = user_policies['AttachedPolicies']

        if not attached_policies:
            print(f"  ⚠ WARNING: No policies attached to user")
            print(f"  User has no permissions!")
        else:
            print(f"  ✓ Found {len(attached_policies)} attached policy(ies):")
            for policy in attached_policies:
                print(f"    - {policy['PolicyName']}")
        print()

        # 4. Get user's groups
        print("[STEP 4] Checking group memberships...")
        groups_response = iam.list_groups_for_user(UserName=username)
        groups = groups_response['Groups']

        if groups:
            print(f"  ✓ User is in {len(groups)} group(s):")
            for group in groups:
                print(f"    - {group['GroupName']}")

                # List policies attached to each group
                group_policies = iam.list_attached_group_policies(
                    GroupName=group['GroupName']
                )
                for policy in group_policies['AttachedPolicies']:
                    print(f"      * {policy['PolicyName']}")
        else:
            print(f"  • User is not in any groups")
        print()

        # 5. Check required permissions vs actual
        print("[STEP 5] Validating CI/CD permissions...")
        required_perms = get_cicd_required_permissions()

        # Get all policies (direct + group)
        all_policy_arns = set()
        for policy in attached_policies:
            all_policy_arns.add(policy['PolicyArn'])

        for group in groups:
            group_policies = iam.list_attached_group_policies(
                GroupName=group['GroupName']
            )
            for policy in group_policies['AttachedPolicies']:
                all_policy_arns.add(policy['PolicyArn'])

        # Analyze each policy document
        all_actions = set()
        for policy_arn in all_policy_arns:
            try:
                # Get default policy version
                policy = iam.get_policy(PolicyArn=policy_arn)
                default_version = policy['Policy']['DefaultVersionId']

                # Get policy document
                policy_version = iam.get_policy_version(
                    PolicyArn=policy_arn,
                    VersionId=default_version
                )
                document = policy_version['PolicyVersion']['Document']

                # Extract allowed actions
                for statement in document.get('Statement', []):
                    if statement.get('Effect') == 'Allow':
                        actions = statement.get('Action', [])
                        if isinstance(actions, str):
                            actions = [actions]

                        for action in actions:
                            all_actions.add(action)

            except Exception as e:
                print(f"  ⚠ Could not analyze policy {policy_arn}: {e}")

        # Compare required vs actual
        results = []
        for category, required_actions in required_perms.items():
            for action in required_actions:
                has_permission = (
                    action in all_actions or
                    '*' in all_actions or
                    f"{action.split(':')[0]}:*" in all_actions
                )

                results.append({
                    'Category': category,
                    'Action': action,
                    'Status': '✓ Yes' if has_permission else '✗ Missing'
                })

        # Print results table
        table_data = [[r['Category'], r['Action'], r['Status']] for r in results]
        print(tabulate(table_data, headers=['Category', 'Required Permission', 'Status'],
                      tablefmt='grid'))

        # Summary
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)

        missing = [r for r in results if 'Missing' in r['Status']]
        if missing:
            print(f"⚠ MISSING {len(missing)} required permission(s) for CI/CD pipeline!")
            print()
            print("Missing permissions:")
            for r in missing:
                print(f"  - {r['Action']} ({r['Category']})")
            print()
            print("RECOMMENDATION: Attach a policy with these permissions")
            print(f"See: .github/workflows/cd.yml for where these are used")
        else:
            print(f"✓ User has ALL required permissions for CI/CD pipeline!")
            print(f"✓ GitHub Actions can deploy TikTimer successfully")

        print("=" * 80)

    except Exception as e:
        print(f"[ERROR] Failed to audit user: {e}")


def generate_policy_document():
    """Generate a least-privilege IAM policy for GitHub Actions"""
    print("\n" + "=" * 80)
    print("RECOMMENDED IAM POLICY FOR GITHUB ACTIONS")
    print("=" * 80)

    # Get account ID
    try:
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
    except:
        account_id = "YOUR_ACCOUNT_ID"

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ECRPushAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:PutImage",
                    "ecr:DescribeRepositories",
                    "ecr:ListImages"
                ],
                "Resource": "*"
            },
            {
                "Sid": "ECSDeployAccess",
                "Effect": "Allow",
                "Action": [
                    "ecs:DescribeClusters",
                    "ecs:DescribeServices",
                    "ecs:DescribeTaskDefinition",
                    "ecs:RegisterTaskDefinition",
                    "ecs:UpdateService",
                    "ecs:ListTasks",
                    "ecs:DescribeTasks"
                ],
                "Resource": "*"
            },
            {
                "Sid": "ELBHealthCheckAccess",
                "Effect": "Allow",
                "Action": [
                    "elasticloadbalancing:DescribeLoadBalancers",
                    "elasticloadbalancing:DescribeTargetGroups",
                    "elasticloadbalancing:DescribeTargetHealth"
                ],
                "Resource": "*"
            },
            {
                "Sid": "PassRoleToECS",
                "Effect": "Allow",
                "Action": "iam:PassRole",
                "Resource": f"arn:aws:iam::{account_id}:role/tiktimer-*",
                "Condition": {
                    "StringEquals": {
                        "iam:PassedToService": "ecs-tasks.amazonaws.com"
                    }
                }
            },
            {
                "Sid": "VerifyIdentity",
                "Effect": "Allow",
                "Action": "sts:GetCallerIdentity",
                "Resource": "*"
            }
        ]
    }

    print(json.dumps(policy, indent=2))
    print()
    print("To use this policy:")
    print("1. Save to file: github-actions-policy.json")
    print("2. Create policy: aws iam create-policy --policy-name TikTimer-GitHub-Actions "
          "--policy-document file://github-actions-policy.json")
    print("3. Attach to user: aws iam attach-user-policy --user-name github-actions-tiktimer "
          "--policy-arn arn:aws:iam::ACCOUNT_ID:policy/TikTimer-GitHub-Actions")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Audit IAM permissions for TikTimer CI/CD pipeline'
    )
    parser.add_argument('--username', default='github-actions-tiktimer',
                       help='IAM username for GitHub Actions (default: github-actions-tiktimer)')
    parser.add_argument('--generate-policy', action='store_true',
                       help='Generate recommended IAM policy JSON')

    args = parser.parse_args()

    if args.generate_policy:
        generate_policy_document()
    else:
        audit_user_permissions(args.username)
