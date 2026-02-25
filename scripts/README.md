# TikTimer Cloud Admin Scripts

This directory contains simple automation scripts that demonstrate essential cloud administration skills. These scripts are designed to be interview-friendly while solving real operational problems for the TikTimer social media scheduler project.

## Scripts Overview

### Environment & Setup
- **`setup-environment.sh`** - Validates requirements and sets up local development environment
- **`check-services.py`** - Health check for all TikTimer services (API, database, containers)

### Monitoring & Troubleshooting
- **`view-logs.sh`** - Easy log viewer for debugging services
- **`aws-resource-check.sh`** - Inventory of AWS resources for TikTimer infrastructure

### Database Management
- **`backup-database.py`** - Creates timestamped PostgreSQL backups
- **`upgrade_datetime_columns.py`** - Database migration utility (existing)

## Quick Start

### Make Scripts Executable
```bash
chmod +x scripts/*.sh scripts/*.py
```

### Basic Usage Examples

**Environment Setup:**
```bash
./scripts/setup-environment.sh
```

**Check Service Health:**
```bash
./scripts/check-services.py
```

**View Application Logs:**
```bash
./scripts/view-logs.sh api     # API logs
./scripts/view-logs.sh db      # Database logs
./scripts/view-logs.sh all     # All logs
```

**Create Database Backup:**
```bash
./scripts/backup-database.py
./scripts/backup-database.py --list    # List existing backups
```

**Check AWS Resources:**
```bash
./scripts/aws-resource-check.sh
```

## Script Details

### setup-environment.sh
**Purpose:** Automates local development environment setup
**Skills Demonstrated:**
- Bash scripting fundamentals
- Dependency checking
- Docker container management
- Environment configuration

**Key Features:**
- Validates required tools (Docker, Docker Compose, AWS CLI)
- Creates environment configuration from templates
- Starts all services and verifies connectivity
- Provides helpful next steps and troubleshooting tips

### check-services.py
**Purpose:** Comprehensive health monitoring for all services
**Skills Demonstrated:**
- Python scripting for system monitoring
- HTTP health checks and API testing
- Docker container status checking
- Error handling and user-friendly reporting

**Key Features:**
- Checks API responsiveness and health endpoints
- Validates Docker container status
- Provides detailed status reporting with recommendations
- Proper exit codes for automation/alerting

### view-logs.sh
**Purpose:** Simplified log viewing for troubleshooting
**Skills Demonstrated:**
- Log aggregation and filtering
- User-friendly command-line interfaces
- Docker Compose log management

**Key Features:**
- Service-specific log viewing (API, Database, All)
- Real-time log streaming with proper formatting
- Color-coded output for better readability
- Graceful exit handling

### backup-database.py
**Purpose:** Automated PostgreSQL database backups
**Skills Demonstrated:**
- Database administration automation
- File system operations and organization
- Error handling and validation
- Command-line argument processing

**Key Features:**
- Timestamped backup file generation
- Database connectivity validation
- Backup size reporting and validation
- Lists existing backups with metadata
- Comprehensive error handling

### aws-resource-check.sh
**Purpose:** AWS infrastructure inventory and monitoring
**Skills Demonstrated:**
- AWS CLI automation
- Multi-service resource discovery
- Infrastructure monitoring
- Cloud resource management

**Key Features:**
- AWS credential validation
- Resource discovery across multiple services (S3, RDS, ECS, ALB)
- Regional resource checking
- Formatted reporting with status indicators

## Interview Talking Points

These scripts demonstrate key cloud admin competencies:

### **Automation Skills**
- Eliminates manual, repetitive tasks
- Reduces human error through standardized processes
- Improves operational efficiency

### **Monitoring & Troubleshooting**
- Proactive health checking
- Centralized log management
- Quick problem identification and diagnosis

### **Cloud Platform Knowledge**
- AWS service integration (S3, RDS, ECS, ALB)
- Docker containerization management
- Infrastructure as Code principles

### **System Administration**
- Database backup and recovery procedures
- Service dependency management
- Environment configuration and validation

### **Operational Excellence**
- Comprehensive error handling
- User-friendly interfaces and documentation
- Scalable and maintainable script design

## Requirements

### Local Development
- Docker & Docker Compose
- Python 3.6+ with `requests` library
- Bash shell

### AWS Operations
- AWS CLI configured with appropriate credentials
- Permissions for EC2, RDS, S3, ECS, and ELB services

## Best Practices Demonstrated

- **Error Handling:** All scripts include comprehensive error checking
- **User Experience:** Clear output with colors, progress indicators, and helpful messages
- **Documentation:** Self-documenting code with usage examples
- **Security:** No hardcoded credentials; uses environment variables and AWS profiles
- **Maintainability:** Modular functions with clear separation of concerns

## Future Enhancements

Potential additions for expanding cloud admin capabilities:
- Automated deployment scripts
- Performance monitoring and alerting
- Cost optimization reporting
- Security vulnerability scanning
- Multi-environment management (dev/staging/prod)

---

*These scripts are designed to showcase practical cloud administration skills in a simple, understandable format perfect for technical interviews and day-to-day operations.*