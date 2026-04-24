# TalkWithDB Desktop v4 (WIP)

This folder contains the desktop migration target for Version 4.

## Current status

- Initial Flet desktop shell is created.
- PostgreSQL connection form and connectivity test are implemented.
- NL prompt capture is wired in UI (pipeline integration pending).

## Run

```bash
python -m desktop_v4.app
```

## Next milestones

1. Integrate `src/chat_sql` SQL generation + safety validation into desktop flow.
2. Add query execution and results table rendering.
3. Add local history persistence (SQLite).
4. Add multi-database adapter abstraction.
