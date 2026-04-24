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
                    f"SELECT COUNT(*) AS row_count FROM {table}"
                )
                row_count = cursor.fetchone()["row_count"]
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
                cursor.execute(
                    """
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS ref_table,
                        ccu.column_name AS ref_column
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = 'public'
                      AND tc.table_name = %s
                    """,
                    (table,),
                )
                fk_rows = cursor.fetchall()
                fk_desc = ", ".join(
                    f"{r['column_name']} -> {r['ref_table']}.{r['ref_column']}" for r in fk_rows
                ) if fk_rows else "None"
                chunks.append(
                    f"Table: {table}\n"
                    f"Approx rows: {row_count}\n"
                    f"Columns: {col_desc}\n"
                    f"Foreign keys: {fk_desc}"
                )
        return "\n\n".join(chunks)
    finally:
        conn.close()

