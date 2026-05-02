"""PostgreSQL connectivity for the desktop app (psycopg2 with pg8000 fallback)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from desktop_v4.services.connection_service import PostgresConnectionConfig

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:  # pragma: no cover - environment specific
    psycopg2 = None
    RealDictCursor = None

try:
    import pg8000
except Exception:  # pragma: no cover - environment specific
    pg8000 = None

Backend = Literal["psycopg2", "pg8000"]


def driver_unavailable_message() -> str:
    parts: list[str] = []
    if psycopg2 is None:
        parts.append("psycopg2 did not load (often blocked by Windows DLL policy)")
    if pg8000 is None:
        parts.append("pg8000 is not installed; run: pip install pg8000")
    return "No PostgreSQL driver available. " + " ".join(parts)


def connect(
    config: PostgresConnectionConfig, *, connect_timeout: int = 8
) -> Tuple[Backend, Any]:
    """Open a connection, preferring psycopg2 when it actually loads."""
    if psycopg2 is not None:
        conn = psycopg2.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
            connect_timeout=connect_timeout,
        )
        return "psycopg2", conn
    if pg8000 is not None:
        conn = pg8000.connect(
            user=config.user,
            password=config.password if config.password is not None else "",
            host=config.host,
            port=int(config.port),
            database=config.database,
            timeout=float(connect_timeout),
        )
        return "pg8000", conn
    raise RuntimeError(driver_unavailable_message())


def fetch_all(
    backend: Backend,
    conn: Any,
    sql: str,
    params: Optional[Sequence[Any]] = None,
) -> List[Tuple[Any, ...]]:
    """Run a query and return all rows as tuples."""
    params = params or ()
    if backend == "psycopg2":
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return list(cursor.fetchall())
    finally:
        cursor.close()


def _pg8000_rows_as_dicts(cursor: Any) -> List[Dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    cols = [d[0] for d in (cursor.description or ())]
    return [dict(zip(cols, row)) for row in rows]


def execute_query_dicts(
    backend: Backend,
    conn: Any,
    sql: str,
    params: Optional[Sequence[Any]] = None,
    *,
    statement_timeout_ms: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Execute a statement and return rows as dicts (column name -> value)."""
    params = params or ()
    if backend == "psycopg2":
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if statement_timeout_ms is not None:
                cursor.execute(f"SET statement_timeout = {int(statement_timeout_ms)}")
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    cursor = conn.cursor()
    try:
        if statement_timeout_ms is not None:
            cursor.execute(f"SET statement_timeout = {int(statement_timeout_ms)}")
        cursor.execute(sql, params)
        return _pg8000_rows_as_dicts(cursor)
    finally:
        cursor.close()
