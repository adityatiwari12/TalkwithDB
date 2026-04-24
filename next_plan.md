# TalkWithDB Version 4 - Desktop Product Plan

## Goal

Ship a Windows desktop application where users can connect a database and ask natural language questions to get SQL + answers, without running separate localhost services manually.

## Current baseline (already done)

- Branch `version-4` is created and pushed.
- Existing web stack stabilized:
  - Ollama model availability checks added.
  - Streamlit API health check reliability improved.
  - Windows local setup issues documented and resolved.
- Initial desktop scaffold created in `desktop_v4/`.

## Architecture decision

Use an in-process desktop architecture (Flet + Python services):

1. **Desktop UI layer** (`desktop_v4/app.py`)
2. **Service layer** (connection, schema, NL-to-SQL orchestration)
3. **Core reuse** from `src/chat_sql/*` for generation, validation, formatting
4. **Persistence layer** for local history/config (`sqlite` + `keyring`)

This avoids brittle localhost handoffs and enables a plug-and-play installer workflow.

## Version 4 milestones

### Milestone 1 - Desktop shell + connection (in progress)

- [x] Add desktop package structure.
- [x] Add PostgreSQL connection test service.
- [x] Build initial Flet screen with connection panel and prompt box.
- [ ] Add connection profile save/load (secure password via keyring).
- [ ] Add schema preview panel.

### Milestone 2 - NL-to-SQL desktop flow

- [ ] Create `DesktopQueryPipeline` that wraps:
  - schema retrieval
  - SQL generation
  - SQL validation
  - query execution
  - result formatting
- [ ] Wire prompt submit to pipeline.
- [ ] Show generated SQL, warnings, and results table in desktop UI.
- [ ] Add cancellation and timeout controls.

### Milestone 3 - History and exports

- [ ] Persist query history into local SQLite.
- [ ] Add replay, favorites, and search.
- [ ] Add CSV and Excel export.

### Milestone 4 - Multi-database support

- [ ] Add adapter interface (`postgresql`, `sqlite` first).
- [ ] Add MySQL and SQL Server adapters.
- [ ] Add driver-aware schema introspection and SQL dialect guardrails.

### Milestone 5 - Packaging and DX

- [ ] Add PyInstaller spec for Windows executable.
- [ ] Add first-run diagnostics (Ollama/model/DB driver checks).
- [ ] Add crash-safe logging and support bundle export.

## Required code structure (target)

```text
desktop_v4/
  app.py
  README.md
  services/
    connection_service.py
    schema_service.py
    query_pipeline.py
    history_service.py
    credential_service.py
  ui/
    connection_view.py
    chat_view.py
    results_view.py
```

## Security and safety requirements

- Read-only mode by default.
- Reject non-SELECT SQL before execution.
- Hard row limits and execution timeout per query.
- Never store plaintext passwords in local files.
- Redact credentials from logs and UI error messages.

## Performance targets (MVP)

- API-equivalent response quality using existing LLM pipeline.
- P95 response time under 15 seconds on medium schema.
- App memory under 600MB during normal usage.
- Zero fatal crashes in 2-hour exploratory session.

## Execution log

### 2026-04-24

- Created and pushed branch: `version-4`.
- Added desktop dependency prep (`flet`, `keyring`) to `requirements-all.txt`.
- Added initial desktop scaffold:
  - `desktop_v4/app.py`
  - `desktop_v4/services/connection_service.py`
  - `desktop_v4/README.md`

## Next immediate tasks

1. Implement `schema_service.py` to introspect selected database and cache table metadata.
2. Implement `query_pipeline.py` that reuses `src/chat_sql` generation and validation.
3. Replace placeholder "Ask" behavior with real end-to-end NL-to-SQL execution.
4. Add a desktop results grid and SQL panel.