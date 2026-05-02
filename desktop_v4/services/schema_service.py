"""Schema extraction utilities for desktop query context."""

from __future__ import annotations

from typing import Any, List

from desktop_v4.services.connection_service import PostgresConnectionConfig


def _quote_pg_identifier(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


def _fetch_table_names(backend: Any, conn: Any, max_tables: int) -> List[str]:
    from desktop_v4.services.postgres_client import fetch_all

    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
    """
    rows = fetch_all(backend, conn, query)
    names = [row[0] for row in rows]
    return names[:max_tables]


def build_schema_context(config: PostgresConnectionConfig, max_tables: int = 12) -> str:
    """
    Build compact schema context for SQL generation prompts.

    This keeps prompt size bounded for local model reliability.
    """
    from desktop_v4.services.postgres_client import connect, execute_query_dicts

    backend, conn = connect(config, connect_timeout=8)
    try:
        tables = _fetch_table_names(backend, conn, max_tables)
        chunks: List[str] = []
        for table in tables:
            quoted = _quote_pg_identifier(table)
            count_rows = execute_query_dicts(
                backend,
                conn,
                f"SELECT COUNT(*) AS row_count FROM {quoted}",
            )
            row_count = count_rows[0]["row_count"] if count_rows else 0
            columns = execute_query_dicts(
                backend,
                conn,
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                ORDER BY ordinal_position
                """,
                (table,),
            )
            col_desc = ", ".join(
                f"{c['column_name']} ({c['data_type']})" for c in columns
            )
            fk_rows = execute_query_dicts(
                backend,
                conn,
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
            fk_desc = (
                ", ".join(
                    f"{r['column_name']} -> {r['ref_table']}.{r['ref_column']}"
                    for r in fk_rows
                )
                if fk_rows
                else "None"
            )
            chunks.append(
                f"Table: {table}\n"
                f"Approx rows: {row_count}\n"
                f"Columns: {col_desc}\n"
                f"Foreign keys: {fk_desc}"
            )
        return "\n\n".join(chunks)
    finally:
        conn.close()
