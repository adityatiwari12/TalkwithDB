# Setup Guide for New Developers

## Welcome to the Team! 👋

This guide will help you get the Chat with SQL system up and running on your local machine. By the end of this guide, you'll have a fully functional development environment.

## Prerequisites

Before you begin, make sure you have the following installed:

### Required Software
- **Python 3.8+** (Recommended: 3.11)
- **PostgreSQL 12+** (Recommended: 14+)
- **Git** for version control
- **Docker** (optional, for containerized setup)
- **VS Code** or your preferred IDE

### System Requirements
- **RAM**: 8GB minimum (16GB recommended for Ollama)
- **Storage**: 10GB free space
- **CPU**: Multi-core processor recommended

## Step 1: Environment Setup

### 1.1 Clone the Repository

```bash
# Clone the repository
git clone https://github.com/adityatiwari12/TalkwithDB.git
cd talk_to_db

# Create a feature branch for your work
git checkout -b feature/your-feature-name
```

### 1.2 Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation
python --version
pip --version
```

### 1.3 Install Dependencies

```bash
# Navigate to source directory
cd src/chat_sql

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy pre-commit

# Verify installation
pip list
```

## Step 2: Database Setup

### 2.1 Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
Download and install from [postgresql.org](https://postgresql.org/download/windows/)

### 2.2 Create Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE chatdb;
CREATE USER chatuser WITH PASSWORD 'chatpass123';
GRANT ALL PRIVILEGES ON DATABASE chatdb TO chatuser;
\q

# Test connection
psql -h localhost -U chatuser -d chatdb
```

### 2.3 Setup Sample Data

```bash
# Run the database setup script
python setup_database.py

# Verify setup
psql -h localhost -U chatuser -d chatdb -c "\dt"
```

## Step 3: Ollama Setup

### 3.1 Install Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [ollama.ai](https://ollama.ai/download)

### 3.2 Start Ollama Service

```bash
# Start Ollama
ollama serve

# In another terminal, verify it's running
ollama list
```

### 3.3 Setup Required Models

```bash
# Run the Ollama setup script
python setup_ollama.py

# Or manually pull models
ollama pull llama3.2
ollama pull nomic-embed-text

# Verify models
ollama list
```

## Step 4: Configuration

### 4.1 Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit the configuration file
nano .env  # or use your preferred editor
```

**Example `.env` file:**
```env
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chatdb
POSTGRES_USER=chatuser
POSTGRES_PASSWORD=chatpass123

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text

# Application Configuration
TOP_K_RETRIEVAL=5
MAX_RESULT_ROWS=200
SQL_TIMEOUT_SECONDS=30
MAX_QUESTION_LENGTH=500

# Development Configuration
DEBUG=true
LOG_LEVEL=INFO
```

### 4.2 Verify Configuration

```bash
# Test database connection
python -c "from db.connection import db_connection; print(db_connection.test_connection())"

# Test Ollama connection
python -c "from rag.embedder import embedder; print('Ollama connected')"
```

## Step 5: Run the Application

### 5.1 Start the API Server

```bash
# Navigate to source directory
cd src/chat_sql

# Start the FastAPI server
python api/app.py

# Or use uvicorn directly
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 5.2 Verify the Application

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test schema stats
curl http://localhost:8000/schema/stats

# Test a simple query
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show all users"}'
```

### 5.3 Access API Documentation

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Step 6: Development Tools Setup

### 6.1 Code Formatting and Linting

```bash
# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/
flake8 src/
mypy src/

# Format a specific file
black src/chat_sql/api/app.py
```

### 6.2 Testing Setup

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ --cov-report=html

# Run specific test file
pytest tests/unit/test_sql_validator.py

# Run with verbose output
pytest -v
```

### 6.3 IDE Configuration (VS Code)

**Install these extensions:**
- Python
- Pylance
- Black Formatter
- Python Docstring Generator
- GitLens

**VS Code settings (`.vscode/settings.json`):**
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## Step 7: Common Development Tasks

### 7.1 Adding a New Database Table

1. **Create migration:**
```bash
# Create new migration file
python scripts/create_migration.py add_new_table
```

2. **Update schema cache:**
```bash
curl -X POST http://localhost:8000/schema/refresh
```

3. **Test with queries:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show data from new_table"}'
```

### 7.2 Modifying Safety Rules

Edit `src/chat_sql/safety/sql_validator.py`:

```python
# Add new validation rule
class CustomValidationRule(ValidationRule):
    def validate(self, sql: str) -> ValidationResult:
        # Your custom validation logic
        if "dangerous_pattern" in sql:
            return ValidationResult(
                is_valid=False,
                error="Custom validation failed"
            )
        return ValidationResult(is_valid=True)

# Register the rule
self.validator.add_rule(CustomValidationRule())
```

### 7.3 Adding New API Endpoints

Edit `src/chat_sql/api/app.py`:

```python
@app.get("/custom-endpoint")
async def custom_endpoint():
    """Custom endpoint description."""
    try:
        # Your logic here
        return {"message": "Success"}
    except Exception as e:
        raise HTTPException(500, str(e))
```

### 7.4 Debugging Tips

**Enable debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Use Python debugger:**
```python
import pdb; pdb.set_trace()
```

**Check application logs:**
```bash
# View logs in real-time
tail -f logs/app.log

# Or use docker logs if running in container
docker-compose logs -f app
```

## Step 8: Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Ollama connection failed"
**Solution:**
```bash
# Check if Ollama is running
ollama list

# Restart Ollama
ollama serve

# Check URL in .env file
grep OLLAMA_BASE_URL .env
```

#### Issue 2: "Database connection failed"
**Solution:**
```bash
# Check PostgreSQL status
pg_isready

# Test connection manually
psql -h localhost -U chatuser -d chatdb

# Check credentials in .env
grep POSTGRES .env
```

#### Issue 3: "SQL generation failed"
**Solution:**
```bash
# Check schema cache
curl http://localhost:8000/schema/stats

# Refresh schema
curl -X POST http://localhost:8000/schema/refresh

# Check model availability
ollama list
```

#### Issue 4: "Port already in use"
**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn api.app:app --port 8001
```

### Getting Help

1. **Check logs**: Look at application logs for detailed error messages
2. **Read documentation**: Check `docs/` directory for detailed guides
3. **Ask the team**: Create an issue at https://github.com/adityatiwari12/TalkwithDB/issues
4. **Search existing issues**: Check if someone else had the same problem

## Step 9: Best Practices

### Code Quality
- Follow PEP 8 style guidelines
- Write meaningful commit messages
- Add docstrings to all functions and classes
- Write tests for new features

### Security
- Never commit secrets to version control
- Use environment variables for configuration
- Follow the principle of least privilege
- Review security implications of changes

### Performance
- Monitor query execution times
- Optimize database queries
- Use connection pooling
- Cache frequently accessed data

### Collaboration
- Create feature branches for all work
- Request code reviews before merging
- Update documentation when making changes
- Participate in code reviews

## Step 10: Next Steps

Now that you have the development environment set up, here's what to do next:

1. **Explore the codebase**: Read through the main components
2. **Run the tests**: Familiarize yourself with the test suite
3. **Make a small change**: Fix a bug or add a minor feature
4. **Review the architecture**: Read the system design documents
5. **Join team discussions**: Participate in planning and design meetings

## Resources

### Documentation
- [System Architecture](../architecture/system-design.md)
- [Database Design](../architecture/database-design.md)
- [Workflow Documentation](../architecture/workflow.md)
- [API Reference](../api/openapi.json)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://ollama.ai/documentation)
- [PostgreSQL Documentation](https://postgresql.org/docs/)
- [Python Best Practices](https://pep8.org/)

### Team Communication
- **GitHub**: https://github.com/adityatiwari12/TalkwithDB/discussions
- **Issues**: https://github.com/adityatiwari12/TalkwithDB/issues

---

Welcome aboard! We're excited to have you on the team. If you have any questions or need help getting started, don't hesitate to reach out. 🚀
