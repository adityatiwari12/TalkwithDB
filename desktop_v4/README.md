# TalkWithDB Desktop - Setup and Run Guide

This guide explains how to set up and run the TalkWithDB desktop application locally.

## What This App Needs

- Python 3.11+ (recommended: 3.11 or 3.12)
- A running PostgreSQL database
- Ollama installed and running locally
- Required Ollama models pulled

## 1) Install Python Dependencies

From the project root (`TalkwithDB/TalkwithDB`), run:

```bash
pip install -r requirements.txt
```

If you are using a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Start Ollama

Ensure Ollama is running on:

- `http://localhost:11434`

Then pull required models (one-time):

```bash
ollama pull llama3.2:latest
ollama pull nomic-embed-text:latest
```

Quick health check:

```bash
ollama list
```

## 3) Start PostgreSQL

Run your PostgreSQL instance and keep these values ready:

- host
- port
- database
- user
- password

Default local values commonly used in this project:

- host: `localhost`
- port: `5432`
- database: `chatdb`
- user: `postgres`

### Option A: Start PostgreSQL with Docker (recommended)

1. Ensure Docker Desktop is running.
2. Create and run container (first time):

```bash
docker run -d --name talkwithdb_postgres ^
  -e POSTGRES_DB=chatdb ^
  -e POSTGRES_USER=postgres ^
  -e POSTGRES_PASSWORD=1234 ^
  -p 5432:5432 ^
  postgres:14-alpine
```

1. If container already exists, just start it:

```bash
docker start talkwithdb_postgres
```

1. (Optional) Confirm container status:

```bash
docker ps
```

### Option B: Start local PostgreSQL service (non-Docker)

- Start PostgreSQL from your local service manager (Windows Services / pgAdmin setup).
- Ensure it listens on `localhost:5432`.
- Use your configured database credentials in the app.

## 4) Run the Desktop App

From project root:

```bash
python -m desktop_v4.app
```

## 5) Connect Inside the App

1. Open the app and use the right-side **Details** panel.
2. Fill PostgreSQL credentials.
3. Click **Test & Connect**.
4. Once connected, ask questions in the input bar.

## 6) Desktop Features Included

- Chat-first interface with session history
- Starter prompts on fresh startup chat
- Local SQLite-based chat persistence and response cache
- SQL safety validation before execution
- Multi-query reasoning (primary + supplementary + diagnostics)
- Copy/Edit/Regenerate interactions in chat

## 7) Troubleshooting

- **Model not found**
  - Run `ollama list` and pull missing model with `ollama pull <model-name>`.
- **Ollama connection failed**
  - Confirm Ollama is running on `localhost:11434`.
- **Database connection failed**
  - Recheck host/port/user/password and ensure PostgreSQL allows local connections.
- **Port/process conflicts**
  - Close stale Python processes, then restart app.

## 8) Optional Demo Data

If your database is empty, load mock SQL data from:

- `data/mock/mock_data.sql`

Use your PostgreSQL client (`psql` or GUI tool) to import it, then rerun the app queries.