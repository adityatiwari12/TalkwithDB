"""Database connection helpers for desktop app."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import psycopg2


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
        conn = psycopg2.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
            connect_timeout=5,
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True, None
    except Exception as exc:  # pragma: no cover - depends on local services
        return False, str(exc)
    finally:
        if conn:
            conn.close()

