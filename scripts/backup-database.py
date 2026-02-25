#!/usr/bin/env python3
"""
scripts/backup-database.py
Simple database backup utility for TikTimer PostgreSQL database
Demonstrates database management and automation skills for cloud admin interviews
"""

import subprocess
import datetime
import os
import sys
import argparse

def create_backup_directory():
    """Create backups directory if it doesn't exist"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"[INFO] Created backup directory: {backup_dir}")
    return backup_dir

def generate_backup_filename():
    """Generate timestamped backup filename"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"tiktimer_backup_{timestamp}.sql"

def check_database_container():
    """Check if database container is running"""
    try:
        result = subprocess.run([
            'docker', 'ps',
            '--filter', 'name=social-media-scheduler-db',
            '--format', '{{.Names}}'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and result.stdout.strip():
            print("[SUCCESS] Database container is running")
            return True
        else:
            print("[ERROR] Database container is not running")
            print("[INFO] Start it with: docker-compose up -d db")
            return False

    except Exception as e:
        print(f"[ERROR] Error checking database container: {e}")
        return False

def create_backup(backup_dir, filename, verbose=False):
    """Create database backup using pg_dump"""
    backup_path = os.path.join(backup_dir, filename)

    # pg_dump command to run inside the database container
    pg_dump_cmd = [
        "docker-compose", "exec", "-T", "db",
        "pg_dump",
        "-U", "postgres",
        "-d", "scheduler",
        "--no-password"
    ]

    try:
        print(f"[INFO] Creating backup: {backup_path}")

        if verbose:
            print(f"[DEBUG] Running command: {' '.join(pg_dump_cmd)}")

        # Run pg_dump and save output to file
        with open(backup_path, 'w') as backup_file:
            result = subprocess.run(
                pg_dump_cmd,
                stdout=backup_file,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300  # 5 minute timeout
            )

        # Check if backup was successful
        if result.returncode == 0:
            # Get backup file size
            file_size = os.path.getsize(backup_path)
            file_size_mb = file_size / (1024 * 1024)

            print(f"[SUCCESS] Backup created successfully!")
            print(f"[INFO] Location: {backup_path}")
            print(f"[INFO] Size: {file_size:,} bytes ({file_size_mb:.2f} MB)")

            # Basic validation - check if file has content
            if file_size > 0:
                print("[SUCCESS] Backup file appears to contain data")
                return True
            else:
                print("[WARNING] Warning: Backup file is empty")
                return False
        else:
            print(f"[ERROR] Backup failed!")
            if result.stderr:
                print(f"[ERROR] Error details: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("[ERROR] Backup operation timed out (>5 minutes)")
        return False
    except Exception as e:
        print(f"[ERROR] Error creating backup: {e}")
        return False

def list_existing_backups(backup_dir):
    """List existing backup files"""
    if not os.path.exists(backup_dir):
        print("[INFO] No backup directory found")
        return

    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql')]

    if backup_files:
        print(f"\n[INFO] Existing backups in {backup_dir}:")
        backup_files.sort(reverse=True)  # Show newest first

        for backup_file in backup_files[:5]:  # Show last 5 backups
            file_path = os.path.join(backup_dir, backup_file)
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

            print(f"  - {backup_file}")
            print(f"    Size: {file_size_mb:.2f} MB")
            print(f"    Date: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if len(backup_files) > 5:
            print(f"  ... and {len(backup_files) - 5} more backup(s)")
    else:
        print(f"[INFO] No existing backups found in {backup_dir}")

def main():
    """Main backup function with command line argument support"""
    parser = argparse.ArgumentParser(description='Backup TikTimer PostgreSQL database')
    parser.add_argument('--list', action='store_true', help='List existing backups')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    print("TikTimer Database Backup Utility")
    print("=" * 40)
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create backup directory
    backup_dir = create_backup_directory()

    # If --list flag is used, just show existing backups
    if args.list:
        list_existing_backups(backup_dir)
        return

    # Check if database container is running
    if not check_database_container():
        sys.exit(1)

    # Create backup
    filename = generate_backup_filename()
    success = create_backup(backup_dir, filename, args.verbose)

    if success:
        print("\n[SUCCESS] Backup completed successfully!")

        # Show existing backups
        list_existing_backups(backup_dir)

        print("\n[INFO] Tips:")
        print("  - Store backups in a secure, separate location")
        print("  - Test backup restoration periodically")
        print("  - Consider automating backups with cron jobs")
    else:
        print("\n[ERROR] Backup failed!")
        print("\n[INFO] Troubleshooting:")
        print("  - Ensure database container is running: docker-compose up -d db")
        print("  - Check database logs: docker-compose logs db")
        print("  - Verify database connectivity")
        sys.exit(1)

if __name__ == "__main__":
    main()