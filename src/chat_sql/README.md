# Chat with SQL - RAG-Based Natural Language to SQL System

A production-style prototype that converts natural language questions into safe SQL queries using Retrieval-Augmented Generation (RAG) with **Ollama** for local LLM processing.

## 🏗️ Architecture

The system follows this pipeline:
1. **User Question** → Natural language input
2. **Schema Retrieval** → RAG-based relevant schema extraction using Ollama embeddings
3. **SQL Generation** → Ollama LLM generates SQL using only retrieved schema
4. **SQL Validation** → Safety checks (SELECT-only, no dangerous patterns)
5. **Query Execution** → Execute on PostgreSQL
6. **Result Formatting** → Convert results to natural language using Ollama

## 📁 Project Structure

```
chat_sql/
│
├── app.py                 # FastAPI entry point
├── config.py              # Configuration (DB, model keys)
├── requirements.txt
├── setup_database.py      # Database setup script
├── setup_ollama.py         # Ollama model setup script
├── README.md
│
├── db/
│   ├── connection.py      # Database connection management
│   └── schema_loader.py   # Schema extraction and formatting
│
├── rag/
│   ├── embedder.py        # Text embedding using Ollama
│   ├── vector_store.py    # FAISS vector store for schema embeddings
│   └── retriever.py       # RAG-based schema retrieval
│
├── llm/
│   ├── sql_generator.py   # Ollama-based SQL generation
│   └── result_formatter.py # Natural language result formatting
│
├── safety/
│   └── sql_validator.py   # SQL safety validation
│
└── pipeline/
    └── chat_with_sql.py    # Main pipeline orchestration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- **Ollama** installed and running (for local LLM processing)

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### 2. Start Ollama

```bash
# Start Ollama service
ollama serve

# Or on macOS with brew
brew services start ollama
```

### 3. Setup Environment

```bash
# Clone or navigate to project directory
cd chat_sql

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### 4. Setup Ollama Models

```bash
# Setup required models (llama3.2, nomic-embed-text)
python setup_ollama.py
```

This will:
- Check if Ollama is running
- Pull `llama3.2` model for SQL generation
- Pull `nomic-embed-text` model for embeddings
- Test both models

### 5. Setup Database

```bash
# Run database setup script
python setup_database.py
```

This will:
- Create the `chatdb` database
- Create `users`, `projects`, and `tasks` tables
- Insert sample data for testing

### 6. Start the API Server

```bash
# Start FastAPI server
python app.py

# Or use uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## 📊 Sample Database Schema

The system uses a simple project management database:

```sql
users (id, name, email)
projects (id, name, description)
tasks (id, title, status, assigned_to, project_id, created_at, due_date)
```

The sample data includes:
- 5 users
- 5 projects  
- 25 tasks with various statuses

## 🔌 API Endpoints

### Chat Endpoint
```http
POST /chat
Content-Type: application/json

{
  "question": "Which users have more than 3 tasks?"
}
```

**Response:**
```json
{
  "answer": "Aditya has 5 tasks. Rohit has 4 tasks.",
  "sql": "SELECT u.name, COUNT(t.id) as task_count FROM users u LEFT JOIN tasks t ON u.id = t.assigned_to GROUP BY u.id, u.name HAVING COUNT(t.id) > 3 LIMIT 200",
  "explanation": "This query counts tasks per user and filters for those with more than 3 tasks",
  "results": [
    {"name": "Aditya", "task_count": 5},
    {"name": "Rohit", "task_count": 4}
  ],
  "warnings": [],
  "error": null,
  "metadata": {
    "result_count": 2,
    "schema_retrieved": true,
    "sql_validated": true
  }
}
```

### Health Check
```http
GET /health
```

### Schema Statistics
```http
GET /schema/stats
```

### Refresh Schema
```http
POST /schema/refresh
```

### Configuration
```http
GET /config
```

## 🔒 Safety Features

### SQL Validation
- **SELECT-only queries**: Rejects INSERT, UPDATE, DELETE, DROP, etc.
- **Pattern detection**: Blocks dangerous SQL patterns
- **System table protection**: Prevents access to system tables
- **Injection detection**: Identifies potential SQL injection attempts
- **Result limiting**: Automatically adds LIMIT clause (default: 200 rows)

### Example Safety Violations
```sql
-- REJECTED: Not a SELECT query
UPDATE users SET name = 'hacked' WHERE id = 1;

-- REJECTED: Multiple statements
SELECT * FROM users; DROP TABLE users;

-- REJECTED: System table access
SELECT * FROM pg_user;

-- REJECTED: SQL injection pattern
SELECT * FROM users WHERE name = 'admin' OR 1=1;
```

## 🧪 Example Queries

Try these sample questions:

```bash
# Basic queries
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show all users"}'

# Aggregation queries
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many tasks does each user have?"}'

# JOIN queries
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the tasks assigned to Aditya?"}'

# Complex queries
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "Which projects have the most pending tasks?"}'
```

## 🔧 Configuration Options

| Setting | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_LLM_MODEL` | `llama3.2` | Model for SQL generation |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model for text embeddings |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_DB` | `chatdb` | Database name |
| `TOP_K_RETRIEVAL` | `5` | Number of schema documents to retrieve |
| `MAX_ROWS` | `200` | Maximum rows returned per query |
| `SQL_TIMEOUT_SECONDS` | `30` | SQL query timeout |
| `MAX_QUESTION_LENGTH` | `500` | Maximum question length |

## 🛠️ Development

### Adding New Tables

1. Add tables to your PostgreSQL database
2. Refresh the schema:
```bash
curl -X POST "http://localhost:8000/schema/refresh"
```

### Custom Embedding Models

Modify `.env`:
```env
OLLAMA_EMBED_MODEL=your-custom-model-name
```

### Safety Rules

Edit `safety/sql_validator.py` to customize:
- Forbidden keywords
- Dangerous patterns
- System table restrictions

## 🧪 Testing

### Test Ollama Connection
```bash
python -c "from rag.embedder import embedder; print('Ollama connected')"
```

### Test Database Connection
```bash
python -c "from db.connection import db_connection; print(db_connection.test_connection())"
```

### Test Schema Retrieval
```bash
python -c "from rag.retriever import schema_retriever; print(schema_retriever.get_stats())"
```

### Test Pipeline
```bash
python -c "from pipeline.chat_with_sql import chat_pipeline; print(chat_pipeline.chat_with_sql('Show all users')['answer'])"
```

## 📈 Performance Considerations

- **Embedding Cache**: Schema embeddings are cached in FAISS for fast retrieval
- **Connection Pooling**: Database connections are managed efficiently
- **Result Limiting**: Automatic LIMIT prevents large result sets
- **Schema Refresh**: Only refresh when database schema changes
- **Local Processing**: Ollama provides fast local inference without API delays

## 🔍 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   - Check Ollama is running: `ollama list`
   - Verify Ollama URL in `.env`
   - Start Ollama: `ollama serve`

2. **Model Not Found**
   - Run setup script: `python setup_ollama.py`
   - Check installed models: `ollama list`
   - Pull models manually: `ollama pull llama3.2`

3. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection parameters in `.env`
   - Ensure database exists (run `setup_database.py`)

4. **SQL Generation Errors**
   - Check if schema was loaded: `GET /schema/stats`
   - Refresh schema if database structure changed
   - Review safety validation logs

5. **Slow Response Times**
   - Check Ollama model performance
   - Consider smaller models for faster inference
   - Monitor system resources

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation at `http://localhost:8000/docs`
- Examine the logs for detailed error messages
