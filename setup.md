# TalkWithDB Quick Setup

Small guide to run the app locally with minimum steps.

## 1) Install Python dependencies

```bash
python -m pip install -r requirements-all.txt
```

## 2) Start Ollama

Run Ollama server (keep it running):

```bash
ollama serve
```
if error arises in ollama use this:  $env:Path += ";C:\Users\ASUS\AppData\Local\Programs\Ollama"

Pull required models (lightweight default model + embeddings):

```bash
ollama pull llama3.2:latest
ollama pull nomic-embed-text:latest
```

## 3) Start PostgreSQL (Docker)

```bash
docker run -d --name talkwithdb_postgres ^
  -e POSTGRES_DB=chatdb ^
  -e POSTGRES_USER=postgres ^
  -e POSTGRES_PASSWORD=1234 ^
  -p 5432:5432 ^
  postgres:14-alpine
```

If container already exists:

```bash
docker start talkwithdb_postgres
```

## 4) Initialize database tables + sample data

```bash
$env:PYTHONIOENCODING="utf-8"
python chat_sql/setup_database.py
```

## 5) Run backend and UI

Terminal 1 (API):

```bash
$env:PYTHONIOENCODING="utf-8"
python -m uvicorn apps.api:app --host 0.0.0.0 --port 8001 --reload
```

Terminal 2 (Streamlit):

```bash
$env:PYTHONIOENCODING="utf-8"
python -m streamlit run apps/ui.py --server.port 8502
```

## 6) Open app

- UI: http://localhost:8502
- API health: http://localhost:8001/health

## Common quick fixes

- **Memory error from Ollama**: make sure model is `llama3.2:latest` (not `gpt-oss:20b`).
- **`date is not JSON serializable`**: fixed in current API code, just restart API.
- **Port in use**: stop old Python/Streamlit/Uvicorn process and rerun.
