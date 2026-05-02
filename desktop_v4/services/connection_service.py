"""Database connection helpers for desktop app."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PostgresConnectionConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


def test_postgres_connection(config: PostgresConnectionConfig) -> tuple[bool, Optional[str]]:
    """Return (ok, error_message) for PostgreSQL connectivity check."""
    conn = None
    try:
        from desktop_v4.services.postgres_client import connect

        backend, conn = connect(config, connect_timeout=5)
        if backend == "psycopg2":
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        else:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            finally:
                cursor.close()
        return True, None
    except Exception as exc:  # pragma: no cover - depends on local services
        return False, str(exc)
    finally:
        if conn is not None:
            conn.close()
