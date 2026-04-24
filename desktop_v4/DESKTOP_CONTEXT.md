# TalkWithDB Desktop Context (Version 5)

This document is the focused implementation context for the desktop product in `desktop_v4/`.

## Purpose

The desktop app is a fast, chat-first AI database assistant with plug-and-play PostgreSQL connectivity.
It is designed to feel like a native desktop tool (not a web dashboard), with local persistence and responsive interaction.

## Core UX Model

- Left panel: chat sessions/history
- Center panel: primary conversational interface
- Right panel: toggleable details (SQL + metadata + DB connect controls)
- Settings modal: connection management

### Interaction behavior

- Enter sends message
- Ctrl/Cmd + N creates a new chat
- User message appears immediately
- Assistant typing state appears immediately
- Final response replaces placeholder with progressive rendering

## Runtime Architecture

- UI: `desktop_v4/app.py` (Flet desktop interface)
- Query Orchestration: `desktop_v4/services/query_pipeline.py`
- DB Connectivity: `desktop_v4/services/connection_service.py`
- Schema Context: `desktop_v4/services/schema_service.py`
- Persistence/Cache: `desktop_v4/services/history_service.py` (SQLite)

## Query Execution Strategy

The desktop pipeline may execute multiple read-only queries per user prompt:

1. Primary generated SQL query
2. Supplementary total-count query (for completeness beyond preview limits)
3. Optional diagnostic query (trend/comparison intents):
   - Date-range spread (`MIN/MAX/COUNT`) for trend questions
   - Top-category distribution (`GROUP BY ... COUNT`) for comparison questions

All queries are passed through SQL safety validation before execution.

## Persistence Model

Stored locally in SQLite:

- Sessions (`sessions` table)
- Chat messages (`messages` table)
- Query cache (`query_cache` table)

Behavior:

- Every app launch starts a fresh new chat session
- Previous chats remain available in history
- Cache is reused for repeated prompts in same DB scope

## Operational Notes

- Desktop app run command:

```bash
python -m desktop_v4.app
```

- Required services:
  - Ollama at configured `OLLAMA_BASE_URL`
  - PostgreSQL reachable with provided credentials

## Next recommended hardening tasks

- Add connection profile save/load using secure keyring storage
- Add export (CSV/XLSX) from current chat result
- Add explicit cancel/timeout controls in the UI
- Package with PyInstaller and startup diagnostics
