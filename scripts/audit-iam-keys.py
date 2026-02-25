#!/usr/bin/env python3
"""
scripts/audit-iam-keys.py
Simple IAM Access Key Auditor for TikTimer
Checks for security issues: old keys, unused keys, users without MFA
Perfect for IAM admin interview - shows security awareness and automation
"""

import boto3
import sys
from datetime import datetime, timezone, timedelta
from tabulate import tabulate


def audit_access_keys(project_name="tiktimer", max_age_days=90):
    """
    Audit IAM access keys for security issues

    Checks for:
    - Keys older than max_age_days
    - Keys that haven't been used recently
    - Users without MFA enabled

    Args:
        project_name: Filter users by project name
        max_age_days: Flag keys older than this
    """
    print("=" * 70)
    print(f"TikTimer IAM Access Key Audit")
    print("=" * 70)
    print(f"Checking for keys older than {max_age_days} days")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    iam = boto3.client('iam')
    findings = []

    try:
        # Get all users
        print("[INFO] Scanning IAM users...\n")
        paginator = iam.get_paginator('list_users')

        for response in paginator.paginate():
            for user in response['Users']:
                username = user['UserName']

                # Skip users not in our project (optional filter)
                # Uncomment to filter: if project_name not in username.lower(): continue

                # Get user's access keys
                keys_response = iam.list_access_keys(UserName=username)

                for key_metadata in keys_response['AccessKeyMetadata']:
                    access_key_id = key_metadata['AccessKeyId']
                    key_status = key_metadata['Status']
                    created_date = key_metadata['CreateDate']

                    # Calculate key age
                    key_age = datetime.now(timezone.utc) - created_date
                    key_age_days = key_age.days

                    # Get last used info
                    last_used_response = iam.get_access_key_last_used(
                        AccessKeyId=access_key_id
                    )
                    last_used_date = last_used_response['AccessKeyLastUsed'].get('LastUsedDate')

                    # Calculate days since last use
                    if last_used_date:
                        days_since_use = (datetime.now(timezone.utc) - last_used_date).days
                    else:
                        days_since_use = "Never"

                    # Check MFA status
                    mfa_devices = iam.list_mfa_devices(UserName=username)
                    has_mfa = len(mfa_devices['MFADevices']) > 0

                    # Determine issues
                    issues = []
                    if key_age_days > max_age_days:
                        issues.append(f"OLD ({key_age_days} days)")
                    if days_since_use == "Never":
                        issues.append("NEVER USED")
                    elif isinstance(days_since_use, int) and days_since_use > 90:
                        issues.append(f"UNUSED ({days_since_use} days)")
                    if not has_mfa:
                        issues.append("NO MFA")
                    if key_status == 'Inactive':
                        issues.append("INACTIVE")

                    # Add to findings
                    findings.append({
                        'User': username,
                        'Key ID': access_key_id[-4:] + '...',  # Last 4 chars for security
                        'Age (days)': key_age_days,
                        'Last Used': days_since_use if days_since_use != "Never" else "Never",
                        'MFA': 'Yes' if has_mfa else 'No',
                        'Status': key_status,
                        'Issues': ', '.join(issues) if issues else 'OK'
                    })

        # Print results
        if findings:
            print(f"[FOUND] {len(findings)} access key(s):\n")

            # Print table
            table = [[
                f['User'],
                f['Key ID'],
                f['Age (days)'],
                f['Last Used'],
                f['MFA'],
                f['Status'],
                f['Issues']
            ] for f in findings]

            headers = ['User', 'Key ID', 'Age', 'Last Used', 'MFA', 'Status', 'Issues']
            print(tabulate(table, headers=headers, tablefmt='grid'))

            # Summary
            print(f"\n{'='*70}")
            print("SUMMARY")
            print(f"{'='*70}")

            old_keys = [f for f in findings if 'OLD' in f['Issues']]
            unused_keys = [f for f in findings if 'UNUSED' in f['Issues'] or 'NEVER' in f['Issues']]
            no_mfa = [f for f in findings if 'NO MFA' in f['Issues']]

            print(f"Total Keys:          {len(findings)}")
            print(f"Keys > {max_age_days} days:      {len(old_keys)}")
            print(f"Unused Keys:         {len(unused_keys)}")
            print(f"Users without MFA:   {len(no_mfa)}")

            # Recommendations
            print(f"\n{'='*70}")
            print("RECOMMENDATIONS")
            print(f"{'='*70}")

            if old_keys:
                print("[ACTION] Rotate old access keys:")
                for f in old_keys[:3]:
                    print(f"  - aws iam update-access-key --user-name {f['User']} "
                          f"--access-key-id <full-key-id> --status Inactive")

            if unused_keys:
                print("\n[ACTION] Deactivate unused keys:")
                for f in unused_keys[:3]:
                    print(f"  - Review and delete key for user: {f['User']}")

            if no_mfa:
                print("\n[ACTION] Enable MFA for users:")
                for f in no_mfa[:3]:
                    print(f"  - User: {f['User']}")

            # Exit code based on issues
            if old_keys or unused_keys or no_mfa:
                print(f"\n[WARNING] Found security issues that need attention")
                sys.exit(1)
            else:
                print(f"\n[SUCCESS] No security issues found!")
                sys.exit(0)
        else:
            print("[INFO] No IAM users or access keys found")
            sys.exit(0)

    except Exception as e:
        print(f"[ERROR] Failed to audit access keys: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Audit IAM access keys for security issues')
    parser.add_argument('--max-age', type=int, default=90,
                       help='Flag keys older than N days (default: 90)')
    parser.add_argument('--project', default='tiktimer',
                       help='Filter users by project name (default: tiktimer)')

    args = parser.parse_args()

    audit_access_keys(project_name=args.project, max_age_days=args.max_age)
