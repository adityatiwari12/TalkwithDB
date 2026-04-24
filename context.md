# TalkWithDB - Agent Context Guide

## Project Overview

**TalkWithDB** is a RAG-based Natural Language to SQL system that allows non-technical users to query PostgreSQL databases using natural language. The system uses Ollama (local LLM) for SQL generation and result formatting, with FAISS for vector-based schema retrieval.

### Key Features
- Natural language to SQL translation using RAG
- Hybrid search (BM25 + Vector) for schema retrieval
- SQL validation and safety guardrails (read-only enforcement)
- Real-time WebSocket chat interface
- Conversation memory for multi-turn queries
- **Fine-tuning pipeline for SQL-specific datasets**
- **LoRA-based parameter-efficient training (freeze base, train adapters)**

### LLM Model
- **Base Model**: `gpt-oss:20b` (20B parameters) via Ollama
- **Fine-tuning**: LoRA (Low-Rank Adaptation) - freezes base weights, trains only adapter layers
- **Hardware Support**: 8GB+ VRAM (RTX 3060 Ti, 4060, 3070) to 40GB+ (A100)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TalkWithDB Architecture                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐      HTTP/WebSocket      ┌─────────────────────────────┐  │
│  │   Streamlit  │ ◄──────────────────────► │      FastAPI Backend        │  │
│  │    UI :8502  │                          │        :8001                │  │
│  └──────────────┘                            └─────────────────────────────┘  │
│                                                         │                    │
│                              ┌──────────────────────────┼────────────────┐  │
│                              │                          │                │  │
│                              ▼                          ▼                ▼  │
│                     ┌──────────────┐            ┌─────────────┐    ┌─────────┐ │
│                     │  RAG Engine  │            │   Ollama    │    │PostgreSQL│ │
│                     │  (FAISS/BM25)│            │   :11434    │    │ :5432   │ │
│                     └──────────────┘            └─────────────┘    └─────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. User sends natural language query via Streamlit UI
2. FastAPI backend receives query and processes through RAG pipeline:
   - Query rewriting and expansion
   - Hybrid search (BM25 + FAISS) retrieves relevant schema
   - LLM re-ranking selects top-k tables
3. SQL Generator (Ollama gpt-oss:20b) creates SQL from schema context
4. SQL Validator checks for safety (SELECT-only, deny-list patterns)
5. Query executes against PostgreSQL
6. Result Formatter (Ollama) generates natural language response
7. Response returned to UI with SQL, results, and metadata

---

## Project Structure

```
c:\Users\ASUS\Desktop\TalkwithDB\TalkwithDB/
│
├── apps/                          # Application entry points
│   ├── api.py                     # FastAPI backend (:8001)
│   └── ui.py                      # Streamlit UI (:8502)
│
├── src/chat_sql/                  # Main source code
│   ├── api/                       # API implementations
│   ├── core/                      # Pipeline implementations
│   │   └── optimized_pipeline.py  # Main chat pipeline
│   ├── db/                        # Database layer
│   │   ├── connection.py          # PostgreSQL connection
│   │   └── schema_loader.py       # Schema extraction
│   ├── llm/                       # LLM integration
│   │   ├── sql_generator.py       # SQL generation via Ollama
│   │   └── result_formatter.py    # Natural language formatting
│   ├── rag/                       # RAG components
│   │   ├── advanced_rag.py        # Advanced RAG pipeline
│   │   ├── embedder.py            # Ollama embedding client
│   │   ├── optimized_retriever.py # Schema retrieval
│   │   ├── optimized_vector_store.py # FAISS wrapper
│   │   └── retriever.py           # Basic retriever
│   ├── safety/                    # Security layer
│   │   └── sql_validator.py       # SQL validation & guardrails
│   ├── config.py                  # Configuration settings
│   └── .env.example               # Environment template
│
├── chat_sql/                      # Legacy/alternative implementation
│   ├── app.py                     # Standalone Flask/FastAPI app
│   ├── pipeline/
│   │   └── chat_with_sql.py      # V1 pipeline
│   └── setup_database.py          # Database initialization
│
├── training/                      # Fine-tuning pipeline
│   ├── README.md                  # Training documentation
│   ├── prepare_data.py            # Dataset preparation (Spider, BIRD)
│   ├── train_sql.py               # Standard training (24GB+ VRAM)
│   ├── train_sql_low_vram.py      # 8GB VRAM training (RTX 3060 Ti)
│   ├── export_to_ollama.py        # Export to Ollama GGUF
│   ├── Modelfile                  # Ollama model config
│   └── requirements.txt           # Training dependencies
│
├── data/                          # Data storage
│   ├── schema_snapshots/          # Schema JSON snapshots
│   ├── schema_vectors.faiss      # FAISS vector index
│   └── schema_vectors_metadata.json
│
├── docker/                        # Docker configuration
│   ├── docker-compose.yml         # Dev environment
│   ├── docker-compose.prod.yml    # Production setup
│   ├── Dockerfile
│   └── init.sql                   # DB initialization script
│
├── docs/                          # Documentation
│   ├── architecture/              # System design docs
│   └── development/               # Setup guides
│
├── tests/                         # Test suite
│
├── main.py                        # Launcher (API + UI)
├── chat_v3.py                     # V3 orchestrator entry point
├── pyproject.toml                 # Project configuration
├── requirements-v3.txt            # Main dependencies
└── context.md                     # This file
```

---

## Dependencies & Installation

### External Services Required

1. **Ollama** (Local LLM server)
   - Port: 11434
   - Models required: `gpt-oss:20b` (3B), `nomic-embed-text`
   - Install: https://ollama.com/download

2. **PostgreSQL** (Database)
   - Port: 5432
   - Database: `chatdb` (or as configured)
   - Default credentials: postgres/1234

### Python Dependencies

Core requirements from `requirements-v3.txt`:

```
# Web Framework
fastapi>=0.104.0
uvicorn>=0.24.0
websockets>=12.0
streamlit>=1.28.0

# Database
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.0

# Vector Store & ML
faiss-cpu>=1.7.4
numpy>=1.24.0
scikit-learn>=1.3.0
rank-bm25>=0.2.2

# LLM & AI
ollama>=0.1.0
langchain>=0.0.325
langchain-community>=0.0.10

# Utilities
pydantic>=2.4.0
requests>=2.31.0
python-dotenv>=1.0.0
pandas>=2.1.0
plotly>=5.17.0

# Optional/Scaling
redis>=5.0.0
celery>=5.3.0
prometheus-client>=0.18.0
```

### Installation Steps

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements-v3.txt
   ```

2. **Install and start Ollama:**
   ```bash
   # Download from https://ollama.com/download
   # Then pull required models:
   ollama pull gpt-oss:20b
   ollama pull nomic-embed-text
   ```

3. **Setup PostgreSQL:**
   ```bash
   # Option A: Using Docker (recommended)
   cd docker
   docker-compose up -d

   # Option B: Local PostgreSQL
   # Install PostgreSQL, create database 'chatdb'
   ```

4. **Configure environment:**
   ```bash
   cp src/chat_sql/.env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database schema:**
   ```bash
   python chat_sql/setup_database.py
   ```

6. **Start the application:**
   ```bash
   # Option A: Start both API and UI
   python main.py

   # Option B: Start separately
   python chat_v3.py --api-only    # API only
   python chat_v3.py --ui-only     # UI only
   ```

### Fine-Tuning (Optional)

Improve SQL accuracy by fine-tuning on Text-to-SQL datasets:

```bash
cd training
pip install -r requirements.txt

# For 24GB+ VRAM (RTX 4090, A100):
python prepare_data.py --dataset spider --output ./data/spider.json
python train_sql.py \
    --model_name gpt-oss:20b \
    --dataset ./data/spider.json \
    --output ./output

# For 8GB VRAM (RTX 3060 Ti, 4060):
python train_sql_low_vram.py \
    --model_name gpt-oss:20b \
    --dataset ./data/spider.json \
    --output ./output \
    --max_samples 500

# Export to Ollama
python export_to_ollama.py \
    --checkpoint ./output/final \
    --name gpt-oss-20b-sql
```

**LoRA Configuration** (Parameter-Efficient Training):
- Base model weights: **FROZEN** (not updated)
- Trainable parameters: LoRA adapters (rank 16-64)
- Memory savings: ~90% reduction vs full fine-tuning
- Typical trainable params: ~0.5-2% of total

---

## Configuration

### Environment Variables (.env)

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=gpt-oss:20b
OLLAMA_EMBED_MODEL=nomic-embed-text

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chatdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234

# App Settings
MAX_ROWS=200
SQL_TIMEOUT_SECONDS=30
MAX_QUESTION_LENGTH=500
TOP_K_RETRIEVAL=5
```

### Configuration Class

Located at `src/chat_sql/config.py`:
- `Config.database_url` - PostgreSQL connection string
- `Config.OLLAMA_*` - Ollama server settings
- `Config.MAX_RESULT_ROWS` - Query result limit
- `config.validate()` - Validates required configuration

---

## Key Entry Points

| File | Purpose | Port |
|------|---------|------|
| `main.py` | Launcher - starts both API and UI | 8001, 8502 |
| `chat_v3.py` | V3 orchestrator with CLI args | 8001, 8502 |
| `apps/api.py` | FastAPI backend only | 8001 |
| `apps/ui.py` | Streamlit UI only | 8502 |
| `chat_ui_enhanced.py` | Enhanced UI (standalone) | 8502 |
| `chat_sql/app.py` | Simple standalone app | 5000 |

---

## Database Schema

### Tables

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to INTEGER REFERENCES users(id),
    project_id INTEGER REFERENCES projects(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE
);
```

### Indexes
- `idx_tasks_assigned_to` on tasks(assigned_to)
- `idx_tasks_project_id` on tasks(project_id)
- `idx_tasks_status` on tasks(status)

---

## Safety & Security

### SQL Validation Layers

1. **Prompt Constraint**: System prompt instructs SELECT-only generation
2. **Application Validation**:
   - SELECT-only check (query must start with SELECT)
   - 19-keyword deny-list (INSERT, UPDATE, DELETE, DROP, etc.)
   - 6 injection regex patterns
   - Auto-LIMIT 200 rows
   - Comment stripping
3. **Database Access Control**: PostgreSQL read-only user with SELECT-only grants

### Deny-List Keywords

```python
forbidden = [
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE',
    'CREATE', 'REPLACE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK',
    'EXECUTE', 'CALL', 'MERGE', 'UNION', 'INTERSECT', 'EXCEPT'
]
```

---

## Development Guidelines

### Code Organization

- **RAG Layer**: `src/chat_sql/rag/` - Vector search, embeddings, retrieval
- **LLM Layer**: `src/chat_sql/llm/` - SQL generation, result formatting
- **DB Layer**: `src/chat_sql/db/` - Connections, schema loading
- **Safety Layer**: `src/chat_sql/safety/` - Validation, sanitization
- **API Layer**: `src/chat_sql/api/` - FastAPI endpoints

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test categories
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests (needs DB)
pytest -m e2e          # End-to-end tests
```

### Code Style

- Black formatter (line length: 88)
- isort for imports
- mypy for type checking
- Use type hints on all function signatures

---

## Common Issues & Solutions

### Issue: Ollama connection failed
**Solution**: Ensure Ollama is running: `ollama serve` or check system tray

### Issue: PostgreSQL connection failed
**Solution**: 
- Check Docker: `docker ps`
- Verify credentials in `.env`
- Ensure database exists: `createdb chatdb`

### Issue: FAISS index not found
**Solution**: Run schema initialization to build vector index

### Issue: SQL generation timeout
**Solution**: 
- First request loads model (slower)
- Increase timeout in config
- Check Ollama logs

---

## API Endpoints

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Main chat endpoint |
| `/api/schema` | GET | Get database schema |
| `/api/sessions/{id}` | GET | Get session info |
| `/api/health` | GET | Health check |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/chat` | Real-time chat WebSocket |

---

## Version History

- **V1**: Basic NL-to-SQL without RAG (35% accuracy)
- **V2**: FAISS-based RAG (55% accuracy)
- **V3**: Hybrid RAG (BM25 + Vector) with LLM re-ranking (65% accuracy)

---

## Resources

- **GitHub**: https://github.com/adityatiwari12/TalkwithDB
- **Documentation**: `docs/` directory
- **Design PDF**: `Designing a "Chat with SQL" System Using RAG.pdf`
