"""Schema extraction utilities for desktop query context."""

from __future__ import annotations

from typing import List

import psycopg2
from psycopg2.extras import RealDictCursor

from desktop_v4.services.connection_service import PostgresConnectionConfig


def _fetch_table_names(conn: psycopg2.extensions.connection) -> List[str]:
    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]


def build_schema_context(config: PostgresConnectionConfig, max_tables: int = 12) -> str:
    """
    Build compact schema context for SQL generation prompts.

    This keeps prompt size bounded for local model reliability.
    """
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        connect_timeout=8,
    )
    try:
        tables = _fetch_table_names(conn)[:max_tables]
        chunks: list[str] = []
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            for table in tables:
                cursor.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (table,),
                )
                columns = cursor.fetchall()
                col_desc = ", ".join(f"{c['column_name']} ({c['data_type']})" for c in columns)
                chunks.append(f"Table: {table}\nColumns: {col_desc}")
        return "\n\n".join(chunks)
    finally:
        conn.close()

