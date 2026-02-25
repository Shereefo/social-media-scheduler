#!/usr/bin/env python3
"""
scripts/check-services.py
Simple service health checker for TikTimer application
Demonstrates basic monitoring and Python scripting skills for cloud admin interviews
"""

import requests
import subprocess
import sys
import json
from datetime import datetime

def print_header():
    """Print a nice header for the health check"""
    print("TikTimer Service Health Check")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_api_health():
    """Check if API is responding and healthy"""
    print("[INFO] Checking API Health...")

    try:
        # Check basic connectivity
        response = requests.get('http://localhost:8000/health', timeout=10)

        if response.status_code == 200:
            print("  [SUCCESS] API is responding")

            # Try to parse JSON response for more details
            try:
                health_data = response.json()
                if isinstance(health_data, dict):
                    print(f"  [INFO] Health status: {health_data.get('status', 'Unknown')}")
                    if 'database' in health_data:
                        db_status = health_data['database']
                        print(f"  [INFO] Database connection: {db_status}")
                else:
                    print(f"  [INFO] Response: {health_data}")
            except json.JSONDecodeError:
                print(f"  [INFO] Response: {response.text[:100]}")

            return True
        else:
            print(f"  [ERROR] API returned status code: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("  [ERROR] Cannot connect to API (connection refused)")
        print("  [INFO] Is the API container running? Try: docker-compose up -d")
        return False
    except requests.exceptions.Timeout:
        print("  [ERROR] API request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] API request failed: {e}")
        return False

def check_database_container():
    """Check if database container is running"""
    print("[INFO] Checking Database Container...")

    try:
        # Check if database container is running
        result = subprocess.run([
            'docker', 'ps',
            '--filter', 'name=social-media-scheduler-db',
            '--format', '{{.Status}}'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and result.stdout.strip():
            status = result.stdout.strip()
            if "Up" in status:
                print(f"  [SUCCESS] Database container is running ({status})")
                return True
            else:
                print(f"  [ERROR] Database container status: {status}")
                return False
        else:
            print("  [ERROR] Database container not found or not running")
            return False

    except subprocess.TimeoutExpired:
        print("  [ERROR] Docker command timed out")
        return False
    except FileNotFoundError:
        print("  [ERROR] Docker command not found - is Docker installed?")
        return False
    except Exception as e:
        print(f"  [ERROR] Error checking database container: {e}")
        return False

def check_api_container():
    """Check if API container is running"""
    print("[INFO] Checking API Container...")

    try:
        # Check if API container is running
        result = subprocess.run([
            'docker', 'ps',
            '--filter', 'name=social-media-scheduler-api',
            '--format', '{{.Status}}'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and result.stdout.strip():
            status = result.stdout.strip()
            if "Up" in status:
                print(f"  [SUCCESS] API container is running ({status})")
                return True
            else:
                print(f"  [ERROR] API container status: {status}")
                return False
        else:
            print("  [ERROR] API container not found or not running")
            return False

    except subprocess.TimeoutExpired:
        print("  [ERROR] Docker command timed out")
        return False
    except Exception as e:
        print(f"  [ERROR] Error checking API container: {e}")
        return False

def print_recommendations(api_ok, db_ok, api_container_ok):
    """Print recommendations based on health check results"""
    print("\n[INFO] Recommendations:")

    if not (api_ok and db_ok and api_container_ok):
        print("  - Some services need attention")

        if not api_container_ok or not db_ok:
            print("  - Try starting services: docker-compose up -d")

        if api_container_ok and not api_ok:
            print("  - API container running but not responding - check logs:")
            print("    docker-compose logs api")

        if not db_ok:
            print("  - Check database logs: docker-compose logs db")

        print("  - View all logs: docker-compose logs")
    else:
        print("  - All services are healthy!")
        print("  - API available at: http://localhost:8000")
        print("  - API docs at: http://localhost:8000/docs")

def main():
    """Main health check function"""
    print_header()

    # Run all health checks
    api_container_ok = check_api_container()
    print()

    db_ok = check_database_container()
    print()

    api_ok = check_api_health()
    print()

    # Print summary
    print("[INFO] Summary:")
    print(f"  API Container:  {'OK' if api_container_ok else 'ERROR'}")
    print(f"  Database:       {'OK' if db_ok else 'ERROR'}")
    print(f"  API Health:     {'OK' if api_ok else 'ERROR'}")

    print_recommendations(api_ok, db_ok, api_container_ok)

    # Exit with appropriate code
    if api_ok and db_ok and api_container_ok:
        print("\n[SUCCESS] All systems operational!")
        sys.exit(0)
    else:
        print("\n[WARNING] Some systems need attention")
        sys.exit(1)

if __name__ == "__main__":
    main()