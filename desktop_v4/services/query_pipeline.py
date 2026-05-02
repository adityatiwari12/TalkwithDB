"""End-to-end desktop NL-to-SQL pipeline with explainable outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional

import requests

from desktop_v4.services.connection_service import PostgresConnectionConfig
from desktop_v4.services.schema_service import build_schema_context


# Ensure src/chat_sql is importable when running from repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chat_sql.llm.result_formatter import ResultFormatter  # noqa: E402
from chat_sql.llm.sql_generator import SQLGenerator  # noqa: E402
from chat_sql.safety.sql_validator import SQLValidator  # noqa: E402


@dataclass
class DesktopQueryResult:
    question: str
    sql_query: str
    answer: str
    explanation: str
    insight: str
    intent: str = "general_query"
    rows: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    supplementary_queries: List[str] = field(default_factory=list)
    error: Optional[str] = None


class DesktopQueryPipeline:
    """Composes generation, validation, execution, and formatting for desktop."""

    def __init__(self) -> None:
        self.sql_generator = SQLGenerator()
        self.sql_validator = SQLValidator()
        self.result_formatter = ResultFormatter()
        self.base_url = self.sql_generator.base_url
        self.model = self.sql_generator.model

    def _infer_intent(self, question: str) -> str:
        """Infer user intent through LLM with safe fallback."""
        prompt = (
            "Classify this database question into one label only:\n"
            "count_query, list_query, aggregation_query, trend_query, "
            "lookup_query, comparison_query, general_query.\n\n"
            f"Question: {question}\n\n"
            "Return only the label."
        )
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=20,
            )
            if response.status_code == 200:
                label = response.json().get("response", "").strip().split()[0].lower()
                allowed = {
                    "count_query",
                    "list_query",
                    "aggregation_query",
                    "trend_query",
                    "lookup_query",
                    "comparison_query",
                    "general_query",
                }
                if label in allowed:
                    return label
        except Exception:
            pass
        lower = question.lower()
        if "how many" in lower or "count" in lower:
            return "count_query"
        if "top" in lower or "average" in lower or "sum" in lower:
            return "aggregation_query"
        if "compare" in lower or "versus" in lower:
            return "comparison_query"
        if "trend" in lower or "over time" in lower:
            return "trend_query"
        if "show" in lower or "list" in lower:
            return "list_query"
        return "general_query"

    def _execute_select(
        self,
        db: PostgresConnectionConfig,
        sql_query: str,
        timeout_seconds: int = 30,
    ) -> List[Dict[str, Any]]:
        from desktop_v4.services.postgres_client import connect, execute_query_dicts

        backend, conn = connect(db, connect_timeout=8)
        try:
            return execute_query_dicts(
                backend,
                conn,
                sql_query,
                statement_timeout_ms=int(timeout_seconds) * 1000,
            )
        finally:
            conn.close()

    def _strip_trailing_limit(self, sql_query: str) -> str:
        """Remove trailing LIMIT N so we can compute full counts when needed."""
        cleaned = sql_query.strip().rstrip(";")
        return re.sub(r"\s+LIMIT\s+\d+\s*$", "", cleaned, flags=re.IGNORECASE)

    def _compute_total_count(self, db: PostgresConnectionConfig, sql_query: str) -> Optional[int]:
        """Run a supplementary count query derived from the generated SQL."""
        base_sql = self._strip_trailing_limit(sql_query)
        if not base_sql.strip().upper().startswith("SELECT"):
            return None
        count_sql = f"SELECT COUNT(*) AS total_count FROM ({base_sql}) AS q"
        rows = self._execute_select(db=db, sql_query=count_sql, timeout_seconds=45)
        if not rows:
            return None
        value = rows[0].get("total_count")
        return int(value) if value is not None else None

    def _quote_ident(self, identifier: str) -> str:
        """Safely quote SQL identifiers for derived diagnostic queries."""
        return '"' + identifier.replace('"', '""') + '"'

    def _build_diagnostic_query(
        self,
        rows: List[Dict[str, Any]],
        base_sql: str,
        intent: str,
    ) -> Optional[str]:
        """
        Build an optional third diagnostic query for richer answers.

        - trend_query: compute date spread and point count.
        - comparison_query: compute top category distribution.
        """
        if not rows:
            return None

        sample_row = rows[0]
        if intent == "trend_query":
            for key, value in sample_row.items():
                if isinstance(value, (date, datetime)):
                    col = self._quote_ident(key)
                    return (
                        "SELECT "
                        f"MIN({col}) AS period_start, "
                        f"MAX({col}) AS period_end, "
                        "COUNT(*) AS total_points "
                        f"FROM ({base_sql}) AS q "
                        f"WHERE {col} IS NOT NULL"
                    )
            return None

        if intent == "comparison_query":
            for key, value in sample_row.items():
                if isinstance(value, str):
                    col = self._quote_ident(key)
                    return (
                        f"SELECT {col} AS category, COUNT(*) AS category_count "
                        f"FROM ({base_sql}) AS q "
                        f"WHERE {col} IS NOT NULL "
                        f"GROUP BY {col} "
                        "ORDER BY category_count DESC "
                        "LIMIT 5"
                    )
            return None

        return None

    def _deterministic_count_sql(self, question: str) -> Optional[str]:
        """
        Return deterministic COUNT SQL for explicit count intents.

        This avoids unnecessary LLM ambiguity for common questions like:
        - "how many users"
        - "number of projects"
        - "count of completed tasks"
        """
        q = question.lower()
        if not (("how many" in q) or ("number of" in q) or ("count" in q)):
            return None

        # Optional task status constraint.
        task_status = None
        for status in ["pending", "in_progress", "completed", "blocked", "cancelled"]:
            if status in q:
                task_status = status
                break

        # Entity routing.
        if re.search(r"\buser(s)?\b", q):
            return "SELECT COUNT(*) AS total_users FROM users"
        if re.search(r"\bproject(s)?\b", q):
            return "SELECT COUNT(*) AS total_projects FROM projects"
        if re.search(r"\btask(s)?\b", q):
            if task_status:
                return (
                    "SELECT COUNT(*) AS total_tasks "
                    f"FROM tasks WHERE status = '{task_status}'"
                )
            return "SELECT COUNT(*) AS total_tasks FROM tasks"

        return None

    def run(self, question: str, db: PostgresConnectionConfig) -> DesktopQueryResult:
        try:
            intent = self._infer_intent(question)
            deterministic_sql = self._deterministic_count_sql(question)

            schema_context = build_schema_context(db)
            if deterministic_sql:
                sql_query = deterministic_sql
            else:
                generated = self.sql_generator.generate_sql(
                    question=question.strip(),
                    schema_context=schema_context,
                )
                sql_query = (generated.get("sql") or "").strip()

            validation = self.sql_validator.validate_sql(sql_query)
            if not validation.is_valid:
                return DesktopQueryResult(
                    question=question,
                    sql_query=sql_query,
                    answer="The query was blocked for safety.",
                    explanation="Generated SQL did not pass validation rules.",
                    insight="Try rephrasing with clearer table/column intent.",
                    intent=intent,
                    warnings=validation.warnings,
                    error=validation.error_message or "Validation failed",
                )

            safe_sql = self.sql_validator.sanitize_sql(sql_query)
            rows = self._execute_select(db=db, sql_query=safe_sql)
            supplementary_queries: list[str] = []
            total_count: Optional[int] = None
            diagnostic_rows: List[Dict[str, Any]] = []
            diagnostic_query: Optional[str] = None

            # Optional secondary query for richer, more accurate narrative.
            # This helps when base query is limited and user needs dataset-level context.
            if intent in {"list_query", "general_query", "aggregation_query"}:
                try:
                    total_count = self._compute_total_count(db=db, sql_query=safe_sql)
                    if total_count is not None:
                        supplementary_queries.append(
                            f"SELECT COUNT(*) AS total_count FROM ({self._strip_trailing_limit(safe_sql)}) AS q"
                        )
                except Exception:
                    # Supplementary query is best-effort; do not fail primary answer.
                    total_count = None

            # Optional third diagnostic query for trend/comparison intents.
            if intent in {"trend_query", "comparison_query"}:
                try:
                    diagnostic_query = self._build_diagnostic_query(
                        rows=rows,
                        base_sql=self._strip_trailing_limit(safe_sql),
                        intent=intent,
                    )
                    if diagnostic_query:
                        diagnostic_rows = self._execute_select(
                            db=db,
                            sql_query=diagnostic_query,
                            timeout_seconds=45,
                        )
                        supplementary_queries.append(diagnostic_query)
                except Exception:
                    diagnostic_rows = []

            answer = self.result_formatter.format_result(
                question=question,
                sql_query=safe_sql,
                results=rows,
            )
            explanation = (
                "Interpreted your intent, validated SQL for read-only safety, "
                "and executed it as the primary query."
            )
            if deterministic_sql:
                explanation = (
                    "Detected an explicit count request and used a deterministic COUNT query, "
                    "then validated and executed it safely."
                )
            else:
                explanation = (
                    "Interpreted your intent, generated SQL with schema context, "
                    "validated it for read-only safety, then executed it as the primary query."
                )
            if total_count is not None:
                explanation += (
                    " I then ran a supplementary COUNT query on the same logic "
                    "to improve completeness beyond the visible row limit."
                )
            if diagnostic_query:
                explanation += (
                    " I also ran a diagnostic query to provide distribution/time-span context "
                    "for deeper interpretation."
                )
            if validation.warnings:
                explanation += " Validation warnings were detected."
            if rows:
                sample_cols = ", ".join(list(rows[0].keys())[:3])
                insight = (
                    f"Primary query returned {len(rows)} row(s)"
                )
                if total_count is not None:
                    insight += f" out of {total_count} matching row(s) in total."
                else:
                    insight += "."
                insight += f" You can refine by filtering/grouping fields like {sample_cols}."
            else:
                insight = "No rows matched. Try broader filters or different time ranges."
            if total_count is not None:
                answer += (
                    f"\n\nAdditional context: The full result set contains {total_count} matching row(s), "
                    "while the preview is intentionally limited for responsiveness."
                )
            if diagnostic_rows and intent == "trend_query":
                diag = diagnostic_rows[0]
                answer += (
                    "\n\nTrend diagnostic: "
                    f"period spans from {diag.get('period_start')} to {diag.get('period_end')} "
                    f"across {diag.get('total_points')} point(s)."
                )
            if diagnostic_rows and intent == "comparison_query":
                pairs = [
                    f"{row.get('category')}: {row.get('category_count')}"
                    for row in diagnostic_rows[:5]
                ]
                answer += (
                    "\n\nComparison diagnostic (top categories): "
                    + ", ".join(pairs)
                    + "."
                )
            return DesktopQueryResult(
                question=question,
                sql_query=safe_sql,
                answer=answer,
                explanation=explanation,
                insight=insight,
                intent=intent,
                rows=rows,
                warnings=validation.warnings,
                supplementary_queries=supplementary_queries,
            )
        except Exception as exc:
            return DesktopQueryResult(
                question=question,
                sql_query="",
                answer="I could not complete the request.",
                explanation="Execution failed before a safe result could be returned.",
                insight="Check database connectivity and Ollama model availability.",
                error=str(exc),
            )

