# Development and Deployment Scripts

## setup.sh - Environment Setup Script

```bash
#!/bin/bash

# Chat with SQL - Environment Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up Chat with SQL development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r src/chat_sql/requirements.txt
pip install -e .[dev]

# Setup pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

# Copy environment file
if [ ! -f "src/chat_sql/.env" ]; then
    echo "📝 Creating environment file..."
    cp src/chat_sql/.env.example src/chat_sql/.env
    echo "⚠️  Please edit src/chat_sql/.env with your configuration"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p tests/reports

echo "✅ Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit src/chat_sql/.env with your configuration"
echo "2. Install and start PostgreSQL"
echo "3. Install and start Ollama"
echo "4. Run 'python src/chat_sql/setup_database.py'"
echo "5. Run 'python src/chat_sql/setup_ollama.py'"
echo "6. Run 'python src/chat_sql/api/app.py' to start the server"
```

## deploy.sh - Deployment Script

```bash
#!/bin/bash

# Chat with SQL - Deployment Script
# This script deploys the application to production

set -e

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "🚀 Deploying Chat with SQL to $ENVIRONMENT environment..."

# Check if we're on the right branch
if [ "$ENVIRONMENT" = "production" ]; then
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "master" ]; then
        echo "❌ Must be on master branch to deploy to production"
        exit 1
    fi
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin master

# Run tests
echo "🧪 Running tests..."
pytest tests/ --cov=src/ --cov-fail-under=80

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t chat-sql:$VERSION .

# Tag and push to registry
if [ "$ENVIRONMENT" = "production" ]; then
    echo "📤 Pushing to production registry..."
    docker tag chat-sql:$VERSION registry.company.com/chat-sql:$VERSION
    docker push registry.company.com/chat-sql:$VERSION
fi

# Deploy using Docker Compose
echo "🚢 Deploying with Docker Compose..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose -f docker/docker-compose.prod.yml up -d
else
    docker-compose up -d
fi

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec app python src/chat_sql/setup_database.py

# Health check
echo "🏥 Running health check..."
sleep 10
health_check=$(curl -s http://localhost:8000/health | jq -r '.status')
if [ "$health_check" = "healthy" ]; then
    echo "✅ Deployment successful!"
else
    echo "❌ Health check failed"
    exit 1
fi

echo "🎉 Deployment to $ENVIRONMENT completed!"
```

## backup.sh - Database Backup Script

```bash
#!/bin/bash

# Chat with SQL - Database Backup Script

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME=${POSTGRES_DB:-chatdb}
DB_HOST=${POSTGRES_HOST:-localhost}
DB_USER=${POSTGRES_USER:-chatuser}

echo "💾 Creating database backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Compress backup
gzip "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Remove old backups (keep last 7 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "✅ Backup completed: backup_$TIMESTAMP.sql.gz"
```

## restore.sh - Database Restore Script

```bash
#!/bin/bash

# Chat with SQL - Database Restore Script

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/backup_20240215_120000.sql.gz"
    exit 1
fi

BACKUP_FILE=$1
DB_NAME=${POSTGRES_DB:-chatdb}
DB_HOST=${POSTGRES_HOST:-localhost}
DB_USER=${POSTGRES_USER:-chatuser}

echo "🔄 Restoring database from backup..."

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Extract backup if compressed
if [[ $BACKUP_FILE == *.gz ]]; then
    echo "📦 Extracting backup..."
    gunzip -c "$BACKUP_FILE" > /tmp/restore.sql
    RESTORE_FILE="/tmp/restore.sql"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Restore database
echo "🗄️ Restoring database..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < "$RESTORE_FILE"

# Clean up
if [ -f "/tmp/restore.sql" ]; then
    rm /tmp/restore.sql
fi

echo "✅ Database restore completed!"
```

## test.sh - Test Runner Script

```bash
#!/bin/bash

# Chat with SQL - Test Runner Script

set -e

TEST_TYPE=${1:-all}
COVERAGE=${2:-true}

echo "🧪 Running tests..."

case $TEST_TYPE in
    "unit")
        echo "🔬 Running unit tests..."
        pytest tests/unit/ -v
        ;;
    "integration")
        echo "🔗 Running integration tests..."
        pytest tests/integration/ -v
        ;;
    "e2e")
        echo "🌐 Running end-to-end tests..."
        pytest tests/e2e/ -v
        ;;
    "security")
        echo "🔒 Running security tests..."
        pytest -m security -v
        ;;
    "performance")
        echo "⚡ Running performance tests..."
        pytest -m performance -v
        ;;
    "all")
        echo "🎯 Running all tests..."
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/ --cov=src/ --cov-report=html --cov-report=term-missing
        else
            pytest tests/ -v
        fi
        ;;
    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Available types: unit, integration, e2e, security, performance, all"
        exit 1
        ;;
esac

echo "✅ Tests completed!"
```

## lint.sh - Code Linting Script

```bash
#!/bin/bash

# Chat with SQL - Code Linting Script

set -e

echo "🔍 Running code linting..."

# Format code
echo "🎨 Formatting code with black..."
black src/ tests/

# Sort imports
echo "📚 Sorting imports with isort..."
isort src/ tests/

# Lint with flake8
echo "🔧 Linting with flake8..."
flake8 src/ tests/

# Type checking
echo "📝 Type checking with mypy..."
mypy src/

# Security check
echo "🔒 Running security check with bandit..."
bandit -r src/

echo "✅ Code linting completed!"
```

## monitor.sh - Monitoring Script

```bash
#!/bin/bash

# Chat with SQL - Monitoring Script

set -e

echo "📊 System Health Monitor"

# Check if application is running
if pgrep -f "python.*app.py" > /dev/null; then
    echo "✅ Application is running"
else
    echo "❌ Application is not running"
fi

# Check database connection
echo "🗄️ Checking database connection..."
if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} > /dev/null 2>&1; then
    echo "✅ Database is accessible"
else
    echo "❌ Database is not accessible"
fi

# Check Ollama service
echo "🤖 Checking Ollama service..."
if curl -s ${OLLAMA_BASE_URL:-http://localhost:11434}/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "❌ Ollama is not running"
fi

# API Health Check
echo "🏥 Checking API health..."
health_response=$(curl -s http://localhost:8000/health 2>/dev/null || echo '{"status":"error"}')
health_status=$(echo $health_response | jq -r '.status' 2>/dev/null || echo "error")

if [ "$health_status" = "healthy" ]; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed"
fi

# System resources
echo "💾 System Resources:"
echo "Memory usage: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk usage: $(df -h . | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
echo "CPU load: $(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')"

# Recent errors
echo "📋 Recent errors (last 10):"
if [ -f "logs/app.log" ]; then
    tail -n 100 logs/app.log | grep ERROR | tail -n 10 || echo "No recent errors"
else
    echo "No log file found"
fi

echo "📊 Monitoring completed!"
```

## cleanup.sh - Cleanup Script

```bash
#!/bin/bash

# Chat with SQL - Cleanup Script

set -e

echo "🧹 Cleaning up..."

# Clean Python cache
echo "🐍 Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Clean test coverage
echo "📊 Cleaning test coverage..."
rm -rf htmlcov/
rm -rf .coverage
rm -rf .pytest_cache/

# Clean build artifacts
echo "🏗️ Cleaning build artifacts..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

# Clean logs (keep last 7 days)
echo "📋 Cleaning old logs..."
find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Clean Docker
echo "🐳 Cleaning Docker..."
docker system prune -f
docker volume prune -f

# Clean temporary files
echo "🗑️ Cleaning temporary files..."
rm -rf /tmp/restore.sql
rm -rf /tmp/chat_sql_*

echo "✅ Cleanup completed!"
```

## Makefile

```makefile
# Chat with SQL - Makefile

.PHONY: help install test lint format clean build deploy monitor

# Default target
help:
	@echo "Chat with SQL - Available commands:"
	@echo "  install     Install dependencies and setup environment"
	@echo "  test        Run all tests"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-int    Run integration tests only"
	@echo "  lint        Run code linting and formatting"
	@echo "  format      Format code with black and isort"
	@echo "  clean       Clean build artifacts and cache"
	@echo "  build       Build Docker image"
	@echo "  deploy      Deploy to production"
	@echo "  monitor     Check system health"
	@echo "  backup      Create database backup"
	@echo "  restore     Restore database from backup"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	python -m venv venv
	source venv/bin/activate && pip install --upgrade pip
	source venv/bin/activate && pip install -r src/chat_sql/requirements.txt
	source venv/bin/activate && pip install -e .[dev]
	source venv/bin/activate && pre-commit install
	@echo "✅ Installation complete!"

# Run tests
test:
	@echo "🧪 Running all tests..."
	source venv/bin/activate && pytest tests/ --cov=src/ --cov-report=html

test-unit:
	@echo "🔬 Running unit tests..."
	source venv/bin/activate && pytest tests/unit/ -v

test-int:
	@echo "🔗 Running integration tests..."
	source venv/bin/activate && pytest tests/integration/ -v

# Code quality
lint:
	@echo "🔍 Running linting..."
	source venv/bin/activate && flake8 src/ tests/
	source venv/bin/activate && mypy src/
	source venv/bin/activate && bandit -r src/

format:
	@echo "🎨 Formatting code..."
	source venv/bin/activate && black src/ tests/
	source venv/bin/activate && isort src/ tests/

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage .pytest_cache/
	docker system prune -f

# Build
build:
	@echo "🐳 Building Docker image..."
	docker build -t chat-sql:latest .

# Deploy
deploy:
	@echo "🚀 Deploying to production..."
	./scripts/deploy.sh production

# Monitor
monitor:
	@echo "📊 Checking system health..."
	./scripts/monitor.sh

# Database operations
backup:
	@echo "💾 Creating backup..."
	./scripts/backup.sh

restore:
	@echo "🔄 Restoring from backup..."
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore FILE=backup_file"; exit 1; fi
	./scripts/restore.sh $(FILE)

# Development server
dev:
	@echo "🚀 Starting development server..."
	source venv/bin/activate && python src/chat_sql/api/app.py

# Production server
prod:
	@echo "🏭 Starting production server..."
	docker-compose -f docker/docker-compose.prod.yml up -d

# Setup database
setup-db:
	@echo "🗄️ Setting up database..."
	source venv/bin/activate && python src/chat_sql/setup_database.py

# Setup Ollama
setup-ollama:
	@echo "🤖 Setting up Ollama..."
	source venv/bin/activate && python src/chat_sql/setup_ollama.py
```

These scripts provide a comprehensive toolkit for development, deployment, and maintenance of the Chat with SQL system.
