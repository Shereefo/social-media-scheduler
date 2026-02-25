#!/bin/bash
# scripts/view-logs.sh
# Simple log viewer for debugging TikTimer services
# Demonstrates basic troubleshooting skills for cloud admin interviews

# Default service is 'api' if no argument provided
SERVICE=${1:-api}

# Color codes for better readability
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "TikTimer Log Viewer"
    echo "======================"
    echo ""
    echo "Usage: $0 [service]"
    echo ""
    echo "Available services:"
    echo "  api     - View API application logs"
    echo "  db      - View PostgreSQL database logs"
    echo "  all     - View logs from all services"
    echo ""
    echo "Examples:"
    echo "  $0 api     # View API logs (default)"
    echo "  $0 db      # View database logs"
    echo "  $0 all     # View all service logs"
    echo ""
    echo "Press Ctrl+C to exit log viewing"
}

check_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "[ERROR] docker-compose not found. Please install Docker Compose."
        exit 1
    fi

    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        echo "[ERROR] docker-compose.yml not found in current directory"
        echo "Please run this script from the project root directory"
        exit 1
    fi
}

view_api_logs() {
    echo -e "${BLUE}[INFO] Viewing API logs...${NC}"
    echo "Container: social-media-scheduler-api"
    echo "Press Ctrl+C to exit"
    echo "----------------------------------------"
    docker-compose logs -f --tail=50 api
}

view_db_logs() {
    echo -e "${GREEN}[INFO] Viewing Database logs...${NC}"
    echo "Container: social-media-scheduler-db"
    echo "Press Ctrl+C to exit"
    echo "----------------------------------------"
    docker-compose logs -f --tail=50 db
}

view_all_logs() {
    echo -e "${YELLOW}[INFO] Viewing all service logs...${NC}"
    echo "Press Ctrl+C to exit"
    echo "----------------------------------------"
    docker-compose logs -f --tail=20
}

main() {
    # Check prerequisites
    check_docker_compose

    case $SERVICE in
        "api")
            view_api_logs
            ;;
        "db"|"database")
            view_db_logs
            ;;
        "all")
            view_all_logs
            ;;
        "help"|"-h"|"--help")
            print_usage
            ;;
        *)
            echo "[ERROR] Unknown service: $SERVICE"
            echo ""
            print_usage
            exit 1
            ;;
    esac
}

# Trap Ctrl+C to provide clean exit message
trap 'echo -e "\n\n[INFO] Log viewing stopped. Have a great day!"; exit 0' INT

# Run main function
main