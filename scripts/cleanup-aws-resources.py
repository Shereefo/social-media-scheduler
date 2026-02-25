#!/usr/bin/env python3
"""
scripts/cleanup-aws-resources.py
AWS Resource Cleanup Script for TikTimer Infrastructure
Demonstrates cloud admin capabilities: resource auditing, cost optimization, safe cleanup
Focuses on actual TikTimer resources: ECR images, CloudWatch logs, S3 objects, ECS tasks
"""

import boto3
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from collections import defaultdict


class TikTimerCleaner:
    """TikTimer AWS resource cleanup utility"""

    def __init__(self, dry_run: bool = True, project_name: str = "tiktimer",
                 environment: str = "dev", region: str = "us-east-1"):
        """
        Initialize cleanup tool

        Args:
            dry_run: If True, only report what would be deleted
            project_name: Project name for resource filtering
            environment: Environment (dev/staging/prod)
            region: AWS region
        """
        self.dry_run = dry_run
        self.project_name = project_name.lower()
        self.environment = environment
        self.region = region

        # Initialize AWS clients
        self.ecr = boto3.client('ecr', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.ecs = boto3.client('ecs', region_name=region)
        self.iam = boto3.client('iam')

        self.stats = defaultdict(int)

    def print_header(self):
        """Print script header"""
        mode = "DRY RUN MODE" if self.dry_run else "LIVE MODE"
        print("=" * 70)
        print(f"TikTimer AWS Resource Cleanup - {mode}")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project: {self.project_name}")
        print(f"Environment: {self.environment}")
        print(f"Region: {self.region}")
        print()

        if not self.dry_run:
            print("[WARNING] Running in LIVE mode - resources will be deleted!")
            response = input("Type 'DELETE' to confirm: ")
            if response != 'DELETE':
                print("[INFO] Cleanup cancelled")
                sys.exit(0)
            print()

    def cleanup_old_ecr_images(self, keep_count: int = 10) -> int:
        """
        Remove old ECR images, keeping the most recent N images

        Args:
            keep_count: Number of recent images to keep

        Returns:
            Number of images deleted
        """
        print(f"[INFO] Scanning ECR repository for old images (keeping {keep_count} recent)...")
        deleted = 0

        try:
            repo_name = f"{self.project_name}-{self.environment}"

            # List all images in the repository
            try:
                response = self.ecr.describe_images(
                    repositoryName=repo_name,
                    filter={'tagStatus': 'TAGGED'}
                )
            except self.ecr.exceptions.RepositoryNotFoundException:
                print(f"  [INFO] Repository '{repo_name}' not found - skipping")
                return 0

            images = response.get('imageDetails', [])

            if not images:
                print("  [OK] No images found in repository")
                return 0

            # Sort by push date (newest first)
            images.sort(key=lambda x: x['imagePushedAt'], reverse=True)

            # Images to delete (keep the first keep_count images)
            images_to_delete = images[keep_count:]

            if not images_to_delete:
                print(f"  [OK] Only {len(images)} image(s) found, all within keep limit")
                return 0

            print(f"  [FOUND] {len(images_to_delete)} old image(s) to delete:")

            for image in images_to_delete:
                image_tag = image.get('imageTags', ['untagged'])[0]
                pushed_date = image['imagePushedAt'].strftime('%Y-%m-%d %H:%M:%S')
                image_size_mb = image.get('imageSizeInBytes', 0) / (1024 * 1024)

                print(f"    - Tag: {image_tag}, "
                      f"Pushed: {pushed_date}, "
                      f"Size: {image_size_mb:.2f} MB")

                if not self.dry_run:
                    try:
                        self.ecr.batch_delete_image(
                            repositoryName=repo_name,
                            imageIds=[{'imageTag': image_tag}]
                        )
                        deleted += 1
                    except Exception as e:
                        print(f"      [ERROR] Failed to delete {image_tag}: {e}")
                else:
                    deleted += 1

            if self.dry_run:
                print(f"  [DRY RUN] Would delete {deleted} image(s)")
            else:
                print(f"  [SUCCESS] Deleted {deleted} image(s)")

            self.stats['ecr_images_deleted'] = deleted
            return deleted

        except Exception as e:
            print(f"  [ERROR] Failed to cleanup ECR images: {e}")
            return 0

    def cleanup_old_cloudwatch_logs(self, retention_days: int = 30) -> int:
        """
        Delete CloudWatch log streams older than retention period

        Args:
            retention_days: Delete logs older than this many days

        Returns:
            Number of log streams deleted
        """
        print(f"\n[INFO] Scanning CloudWatch logs (retention: {retention_days} days)...")
        deleted = 0
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        try:
            log_group_name = f"/ecs/{self.project_name}-{self.environment}"

            # Check if log group exists
            try:
                self.logs.describe_log_groups(logGroupNamePrefix=log_group_name)
            except self.logs.exceptions.ResourceNotFoundException:
                print(f"  [INFO] Log group '{log_group_name}' not found - skipping")
                return 0

            # List all log streams
            paginator = self.logs.get_paginator('describe_log_streams')

            old_streams = []
            for page in paginator.paginate(logGroupName=log_group_name):
                for stream in page['logStreams']:
                    # Check last event time
                    last_event_time = stream.get('lastEventTimestamp')
                    if last_event_time:
                        last_event_date = datetime.fromtimestamp(
                            last_event_time / 1000, tz=timezone.utc
                        )

                        if last_event_date < cutoff_date:
                            days_old = (datetime.now(timezone.utc) - last_event_date).days
                            old_streams.append({
                                'name': stream['logStreamName'],
                                'lastEvent': last_event_date,
                                'daysOld': days_old
                            })

            if not old_streams:
                print("  [OK] No old log streams found")
                return 0

            print(f"  [FOUND] {len(old_streams)} old log stream(s):")

            for stream in old_streams[:10]:  # Show first 10
                print(f"    - {stream['name']} ({stream['daysOld']} days old)")

            if len(old_streams) > 10:
                print(f"    ... and {len(old_streams) - 10} more")

            if not self.dry_run:
                for stream in old_streams:
                    try:
                        self.logs.delete_log_stream(
                            logGroupName=log_group_name,
                            logStreamName=stream['name']
                        )
                        deleted += 1
                    except Exception as e:
                        print(f"      [ERROR] Failed to delete {stream['name']}: {e}")

                print(f"  [SUCCESS] Deleted {deleted} log stream(s)")
            else:
                deleted = len(old_streams)
                print(f"  [DRY RUN] Would delete {deleted} log stream(s)")

            self.stats['log_streams_deleted'] = deleted
            return deleted

        except Exception as e:
            print(f"  [ERROR] Failed to cleanup CloudWatch logs: {e}")
            return 0

    def cleanup_old_s3_videos(self, bucket_suffix: str = "uploads",
                             days_old: int = 365) -> int:
        """
        Delete old video files from S3 uploads bucket

        Args:
            bucket_suffix: Bucket name suffix (e.g., 'uploads')
            days_old: Delete objects older than this many days

        Returns:
            Number of objects deleted
        """
        print(f"\n[INFO] Scanning S3 bucket for old videos ({days_old}+ days)...")
        deleted = 0
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        try:
            bucket_name = f"{self.project_name}-{self.environment}-{bucket_suffix}"

            # Check if bucket exists
            try:
                self.s3.head_bucket(Bucket=bucket_name)
            except:
                print(f"  [INFO] Bucket '{bucket_name}' not found - skipping")
                return 0

            # List objects
            paginator = self.s3.get_paginator('list_objects_v2')

            old_objects = []
            total_size_bytes = 0

            for page in paginator.paginate(Bucket=bucket_name):
                for obj in page.get('Contents', []):
                    if obj['LastModified'] < cutoff_date:
                        days_old_count = (datetime.now(timezone.utc) - obj['LastModified']).days
                        old_objects.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'lastModified': obj['LastModified'],
                            'daysOld': days_old_count
                        })
                        total_size_bytes += obj['Size']

            if not old_objects:
                print("  [OK] No old objects found")
                return 0

            total_size_mb = total_size_bytes / (1024 * 1024)
            print(f"  [FOUND] {len(old_objects)} old object(s) "
                  f"(Total size: {total_size_mb:.2f} MB):")

            for obj in old_objects[:10]:
                size_mb = obj['size'] / (1024 * 1024)
                print(f"    - {obj['key']} ({size_mb:.2f} MB, {obj['daysOld']} days old)")

            if len(old_objects) > 10:
                print(f"    ... and {len(old_objects) - 10} more")

            if not self.dry_run:
                # Delete in batches of 1000 (S3 limit)
                for i in range(0, len(old_objects), 1000):
                    batch = old_objects[i:i+1000]
                    delete_objects = [{'Key': obj['key']} for obj in batch]

                    try:
                        self.s3.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': delete_objects}
                        )
                        deleted += len(batch)
                    except Exception as e:
                        print(f"      [ERROR] Failed to delete batch: {e}")

                print(f"  [SUCCESS] Deleted {deleted} object(s), "
                      f"freed {total_size_mb:.2f} MB")
            else:
                deleted = len(old_objects)
                print(f"  [DRY RUN] Would delete {deleted} object(s), "
                      f"would free {total_size_mb:.2f} MB")

            self.stats['s3_objects_deleted'] = deleted
            self.stats['s3_space_freed_mb'] = total_size_mb
            return deleted

        except Exception as e:
            print(f"  [ERROR] Failed to cleanup S3 objects: {e}")
            return 0

    def stop_idle_ecs_tasks(self) -> int:
        """
        Find and stop ECS tasks that have been running for a long time
        (useful for dev environments)

        Returns:
            Number of tasks stopped
        """
        print(f"\n[INFO] Scanning for long-running ECS tasks...")
        stopped = 0

        try:
            cluster_name = f"{self.project_name}-{self.environment}-cluster"

            # List tasks in cluster
            try:
                task_arns = self.ecs.list_tasks(cluster=cluster_name)['taskArns']
            except:
                print(f"  [INFO] Cluster '{cluster_name}' not found - skipping")
                return 0

            if not task_arns:
                print("  [OK] No tasks running")
                return 0

            # Get task details
            tasks = self.ecs.describe_tasks(cluster=cluster_name, tasks=task_arns)['tasks']

            long_running_tasks = []
            for task in tasks:
                # Calculate running time
                created_at = task['createdAt']
                running_time = datetime.now(timezone.utc) - created_at
                hours_running = running_time.total_seconds() / 3600

                # Flag tasks running for more than 24 hours (adjust as needed)
                if hours_running > 24:
                    long_running_tasks.append({
                        'arn': task['taskArn'],
                        'hoursRunning': hours_running,
                        'lastStatus': task['lastStatus']
                    })

            if not long_running_tasks:
                print("  [OK] No long-running tasks found")
                return 0

            print(f"  [FOUND] {len(long_running_tasks)} long-running task(s):")
            for task in long_running_tasks:
                task_id = task['arn'].split('/')[-1]
                print(f"    - {task_id} ({task['hoursRunning']:.1f} hours)")

            if self.environment == 'dev':
                print("  [INFO] Auto-stopping long-running tasks is disabled for safety")
                print("  [INFO] To stop tasks manually, run:")
                print(f"    aws ecs stop-task --cluster {cluster_name} --task <task-id>")
            else:
                print("  [INFO] Only stopping tasks in 'dev' environment for safety")

            # Only stop in dev environment and if not dry run
            # if self.environment == 'dev' and not self.dry_run:
            #     for task in long_running_tasks:
            #         self.ecs.stop_task(cluster=cluster_name, task=task['arn'])
            #         stopped += 1

            return stopped

        except Exception as e:
            print(f"  [ERROR] Failed to check ECS tasks: {e}")
            return 0

    def audit_iam_roles(self) -> List[Dict[str, Any]]:
        """
        Audit IAM roles created by TikTimer for unused permissions

        Returns:
            List of IAM roles with analysis
        """
        print(f"\n[INFO] Auditing TikTimer IAM roles...")

        try:
            roles_analyzed = []

            # Get roles created by our project
            paginator = self.iam.get_paginator('list_roles')

            for page in paginator.paginate():
                for role in page['Roles']:
                    role_name = role['RoleName']

                    # Filter for our project roles
                    if self.project_name in role_name.lower():
                        # Get attached policies
                        attached_policies = self.iam.list_attached_role_policies(
                            RoleName=role_name
                        )['AttachedPolicies']

                        roles_analyzed.append({
                            'RoleName': role_name,
                            'CreateDate': role['CreateDate'],
                            'AttachedPolicies': [p['PolicyName'] for p in attached_policies],
                            'PolicyCount': len(attached_policies)
                        })

            if not roles_analyzed:
                print("  [OK] No TikTimer IAM roles found")
                return []

            print(f"  [FOUND] {len(roles_analyzed)} IAM role(s):")
            for role in roles_analyzed:
                age_days = (datetime.now(timezone.utc) - role['CreateDate']).days
                print(f"    - {role['RoleName']}")
                print(f"      Age: {age_days} days, Policies: {role['PolicyCount']}")
                for policy in role['AttachedPolicies']:
                    print(f"        * {policy}")

            self.stats['iam_roles_audited'] = len(roles_analyzed)
            return roles_analyzed

        except Exception as e:
            print(f"  [ERROR] Failed to audit IAM roles: {e}")
            return []

    def generate_report(self):
        """Generate summary report"""
        print("\n" + "=" * 70)
        print("CLEANUP SUMMARY")
        print("=" * 70)
        print(f"ECR Images Deleted:        {self.stats.get('ecr_images_deleted', 0)}")
        print(f"CloudWatch Streams Deleted: {self.stats.get('log_streams_deleted', 0)}")
        print(f"S3 Objects Deleted:        {self.stats.get('s3_objects_deleted', 0)}")
        print(f"S3 Space Freed (MB):       {self.stats.get('s3_space_freed_mb', 0):.2f}")
        print(f"IAM Roles Audited:         {self.stats.get('iam_roles_audited', 0)}")
        print()

        # Cost estimate (rough)
        s3_cost_saved = self.stats.get('s3_space_freed_mb', 0) * 0.023 / 1024  # $0.023/GB
        print(f"Estimated monthly cost savings: ${s3_cost_saved:.2f}")
        print()

        if self.dry_run:
            print("[INFO] This was a DRY RUN - no changes were made")
            print("[INFO] Run with --live flag to perform actual cleanup")
        else:
            print("[INFO] Cleanup completed in LIVE mode")

        print("=" * 70)


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='TikTimer AWS Resource Cleanup Script'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Run in live mode (actually delete resources)'
    )
    parser.add_argument(
        '--environment',
        default='dev',
        choices=['dev', 'staging', 'prod'],
        help='Environment to clean up (default: dev)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--keep-images',
        type=int,
        default=10,
        help='Number of recent ECR images to keep (default: 10)'
    )
    parser.add_argument(
        '--log-retention-days',
        type=int,
        default=30,
        help='Delete CloudWatch logs older than N days (default: 30)'
    )
    parser.add_argument(
        '--s3-retention-days',
        type=int,
        default=365,
        help='Delete S3 objects older than N days (default: 365)'
    )

    args = parser.parse_args()

    # Safety check for production
    if args.environment == 'prod' and args.live:
        print("[ERROR] Production cleanup requires additional confirmation")
        response = input("Are you SURE you want to cleanup production? Type 'PRODUCTION': ")
        if response != 'PRODUCTION':
            print("[INFO] Cleanup cancelled")
            sys.exit(0)

    # Initialize cleaner
    cleaner = TikTimerCleaner(
        dry_run=not args.live,
        environment=args.environment,
        region=args.region
    )
    cleaner.print_header()

    # Run cleanup operations
    cleaner.cleanup_old_ecr_images(keep_count=args.keep_images)
    cleaner.cleanup_old_cloudwatch_logs(retention_days=args.log_retention_days)
    cleaner.cleanup_old_s3_videos(days_old=args.s3_retention_days)
    cleaner.stop_idle_ecs_tasks()
    cleaner.audit_iam_roles()

    # Generate report
    cleaner.generate_report()

    print("\n[SUCCESS] Cleanup script completed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
