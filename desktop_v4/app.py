"""TalkWithDB Version 4 desktop chat application."""

from __future__ import annotations

import asyncio
import hashlib
import flet as ft

from desktop_v4.services.connection_service import (
    PostgresConnectionConfig,
    test_postgres_connection,
)
from desktop_v4.services.history_service import HistoryService
from desktop_v4.services.query_pipeline import DesktopQueryPipeline

STARTER_QUESTIONS = [
    "How many users are in the system?",
    "Show top 10 users by number of assigned tasks.",
    "List overdue tasks that are not completed.",
    "What are the project-wise completed task counts?",
    "Show average tasks per user.",
    "Which projects have most pending tasks?",
]


def main(page: ft.Page) -> None:
    page.title = "TalkWithDB Desktop v4"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1380
    page.window_height = 900
    page.bgcolor = "#090B16"
    page.padding = 14

    host = ft.TextField(label="Host", value="localhost", dense=True)
    port = ft.TextField(label="Port", value="5432", dense=True, width=100)
    database = ft.TextField(label="Database", value="chatdb", dense=True)
    user = ft.TextField(label="User", value="postgres", dense=True)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, dense=True)

    history = HistoryService()
    pipeline = DesktopQueryPipeline()
    active_cfg: PostgresConnectionConfig | None = None
    active_session_id = history.create_startup_session()
    is_processing = False
    active_request_id = 0
    session_list = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, expand=True)
    chat_feed = ft.Column(spacing=14, scroll=ft.ScrollMode.ALWAYS, expand=True)
    starter_wrap = ft.Wrap(spacing=8, run_spacing=8, visible=True)
    status = ft.Text("Database disconnected", color=ft.Colors.AMBER_300, size=12)
    model_badge = ft.Container(
        content=ft.Text(f"Model: {pipeline.model}", size=11, color="#D5D8FF"),
        bgcolor="#1A2040",
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=16,
    )
    prompt = ft.TextField(
        hint_text="Message TalkWithDB...",
        disabled=True,
        expand=True,
        border_color="#2B356B",
        focused_border_color="#4E63FF",
        bgcolor="#141932",
        shift_enter=True,
    )
    send_btn = ft.ElevatedButton("Ask", disabled=True)
    send_btn.style = ft.ButtonStyle(
        bgcolor="#4E63FF",
        color=ft.Colors.WHITE,
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    def assistant_card(label: str, value: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, size=11, color="#8C95C3", weight=ft.FontWeight.W_600),
                    ft.Text(value or "-", size=13, color="#E7EAFF", selectable=True),
                ],
                spacing=6,
            ),
            padding=12,
            border_radius=14,
            bgcolor="#151B37",
            border=ft.border.all(1, "#252E58"),
        )

    def user_bubble(text: str) -> ft.Row:
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(text, size=13, color=ft.Colors.WHITE),
                    bgcolor="#3A4FD9",
                    padding=12,
                    border_radius=14,
                )
            ],
            alignment=ft.MainAxisAlignment.END,
        )

    def _cache_key(question: str, cfg: PostgresConnectionConfig) -> str:
        normalized = " ".join(question.strip().lower().split())
        scope = f"{cfg.host}:{cfg.port}/{cfg.database}/{cfg.user}"
        return hashlib.sha256(f"{scope}|{normalized}".encode("utf-8")).hexdigest()

    def has_user_messages(session_id: str) -> bool:
        return any(m.role == "user" for m in history.get_messages(session_id))

    def handle_starter_click(text: str) -> None:
        if is_processing:
            return
        prompt.value = text
        on_ask(None)

    def render_starters() -> None:
        starter_wrap.controls.clear()
        if has_user_messages(active_session_id):
            starter_wrap.visible = False
            return
        starter_wrap.visible = True
        for question in STARTER_QUESTIONS:
            starter_wrap.controls.append(
                ft.OutlinedButton(
                    text=question,
                    on_click=lambda _, q=question: handle_starter_click(q),
                    style=ft.ButtonStyle(
                        color="#CFD5FF",
                        side=ft.BorderSide(1, "#2A356C"),
                        shape=ft.RoundedRectangleBorder(radius=16),
                    ),
                )
            )

    def render_chat() -> None:
        chat_feed.controls.clear()
        for item in history.get_messages(active_session_id):
            if item.role == "user":
                chat_feed.controls.append(user_bubble(item.content))
                continue

            cards = [
                assistant_card("Answer", item.answer),
                assistant_card("Explanation", item.explanation),
                assistant_card("Insight", item.insight),
            ]
            body: list[ft.Control] = cards
            if item.sql_query:
                body.append(
                    ft.Container(
                        content=ft.Text(f"SQL:\n{item.sql_query}", selectable=True, color="#C6CDF7", size=12),
                        bgcolor="#111731",
                        border_radius=12,
                        padding=10,
                        border=ft.border.all(1, "#222B55"),
                    )
                )
            chat_feed.controls.append(ft.Column(body, spacing=8))
        render_starters()

    def render_sessions() -> None:
        session_list.controls.clear()
        for rec in history.list_sessions():
            is_active = rec.session_id == active_session_id
            session_list.controls.append(
                ft.Container(
                    content=ft.Text(rec.title, size=12, color="#F3F5FF" if is_active else "#A8AFD9"),
                    padding=10,
                    border_radius=10,
                    bgcolor="#212C62" if is_active else "#111834",
                    border=ft.border.all(1, "#2D3B79" if is_active else "#1A2246"),
                    on_click=lambda _, sid=rec.session_id: switch_session(sid),
                )
            )

    def switch_session(session_id: str) -> None:
        nonlocal active_session_id
        active_session_id = session_id
        render_sessions()
        render_chat()
        page.update()

    def create_new_session(_: ft.ControlEvent) -> None:
        nonlocal active_session_id
        active_session_id = history.create_session("New chat")
        render_sessions()
        render_chat()
        page.update()

    def on_connect(_: ft.ControlEvent) -> None:
        nonlocal active_cfg
        try:
            cfg = PostgresConnectionConfig(
                host=host.value.strip(),
                port=int(port.value.strip() or "5432"),
                database=database.value.strip(),
                user=user.value.strip(),
                password=password.value,
            )
        except ValueError:
            status.value = "Invalid port"
            status.color = ft.Colors.RED_300
            page.update()
            return

        ok, error = test_postgres_connection(cfg)
        if ok:
            active_cfg = cfg
            status.value = f"Connected to {cfg.database} @ {cfg.host}:{cfg.port}"
            status.color = ft.Colors.GREEN_300
            prompt.disabled = False
            send_btn.disabled = False
        else:
            active_cfg = None
            status.value = "Connection failed"
            status.color = ft.Colors.RED_300
            history.add_message(
                active_session_id,
                role="assistant",
                content="",
                answer=f"Connection failed: {error}",
                explanation="The desktop client could not establish a DB session.",
                insight="Verify host, port, credentials, and database name.",
                intent="connection",
            )
            prompt.disabled = True
            send_btn.disabled = True
            render_chat()
        page.update()

    def on_ask(_: ft.ControlEvent) -> None:
        nonlocal is_processing
        nonlocal active_request_id
        if is_processing:
            return
        if not active_cfg:
            history.add_message(
                active_session_id,
                role="assistant",
                content="",
                answer="Connect to a database first.",
                explanation="No active database connection is available.",
                insight="Use the sidebar connection panel and click Test & Connect.",
                intent="connection",
            )
            render_chat()
            page.update()
            return
        if not prompt.value.strip():
            page.update()
            return

        question = prompt.value.strip()
        history.add_message(active_session_id, role="user", content=question)
        prompt.value = ""
        chat_feed.controls.append(user_bubble(question))
        starter_wrap.visible = False
        answer_text = ft.Text("Thinking...", size=13, color="#E7EAFF")
        explanation_text = ft.Text(
            "Interpreting intent, generating SQL, validating safety, and executing query...",
            size=13,
            color="#E7EAFF",
        )
        insight_text = ft.Text("Preparing insight...", size=13, color="#E7EAFF")
        sql_text = ft.Text("", selectable=True, color="#C6CDF7", size=12, visible=False)
        sql_container = ft.Container(
            content=sql_text,
            bgcolor="#111731",
            border_radius=12,
            padding=10,
            border=ft.border.all(1, "#222B55"),
            visible=False,
        )
        assistant_block = ft.Column(
            [
                assistant_card("Answer", ""),
                assistant_card("Explanation", ""),
                assistant_card("Insight", ""),
                sql_container,
            ],
            spacing=8,
        )
        # Replace placeholder card content with dynamic controls
        assistant_block.controls[0].content.controls[1] = answer_text
        assistant_block.controls[1].content.controls[1] = explanation_text
        assistant_block.controls[2].content.controls[1] = insight_text
        chat_feed.controls.append(assistant_block)
        is_processing = True
        active_request_id += 1
        request_id = active_request_id
        prompt.disabled = True
        send_btn.disabled = True
        page.update()

        async def animate_loader() -> None:
            dots = 0
            while is_processing and request_id == active_request_id:
                dots = (dots % 3) + 1
                answer_text.value = f"Thinking{'.' * dots}"
                page.update()
                await asyncio.sleep(0.28)

        page.run_task(animate_loader)

        async def run_pipeline_async() -> None:
            nonlocal is_processing
            cache_key = _cache_key(question, active_cfg)
            cached = history.get_cached_response(cache_key)
            if cached:
                result = None
                answer = cached["answer"]
                if cached.get("warnings"):
                    answer += "\n\nWarnings: " + "; ".join(cached["warnings"])
                answer_text.value = ""
                for idx in range(1, len(answer) + 1, 6):
                    answer_text.value = answer[:idx]
                    page.update()
                    await asyncio.sleep(0.012)
                answer_text.value = answer + "\n\n(Cached response)"
                explanation_text.value = cached["explanation"]
                insight_text.value = cached["insight"]
                if cached["sql_query"]:
                    sql_text.value = f"SQL:\n{cached['sql_query']}"
                    sql_text.visible = True
                    sql_container.visible = True
                history.add_message(
                    active_session_id,
                    role="assistant",
                    content="",
                    sql_query=cached["sql_query"],
                    answer=answer + "\n\n(Cached response)",
                    explanation=cached["explanation"],
                    insight=cached["insight"],
                    intent=cached["intent"],
                )
            else:
                result = await asyncio.to_thread(pipeline.run, question, active_cfg)

                if result.error:
                    answer_text.value = f"Error: {result.error}"
                    explanation_text.value = result.explanation
                    insight_text.value = result.insight
                    history.add_message(
                        active_session_id,
                        role="assistant",
                        content="",
                        sql_query=result.sql_query,
                        answer=f"Error: {result.error}",
                        explanation=result.explanation,
                        insight=result.insight,
                        intent=result.intent,
                    )
                else:
                    answer = result.answer
                    if result.warnings:
                        answer += "\n\nWarnings: " + "; ".join(result.warnings)
                    answer_text.value = ""
                    for idx in range(1, len(answer) + 1, 6):
                        answer_text.value = answer[:idx]
                        page.update()
                        await asyncio.sleep(0.012)
                    answer_text.value = answer
                    explanation_text.value = result.explanation
                    insight_text.value = f"{result.insight} Returned {len(result.rows)} row(s)."
                    if result.sql_query:
                        sql_text.value = f"SQL:\n{result.sql_query}"
                        sql_text.visible = True
                        sql_container.visible = True
                    history.add_message(
                        active_session_id,
                        role="assistant",
                        content="",
                        sql_query=result.sql_query,
                        answer=answer,
                        explanation=result.explanation,
                        insight=f"{result.insight} Returned {len(result.rows)} row(s).",
                        intent=result.intent,
                    )
                    history.set_cached_response(
                        cache_key=cache_key,
                        answer=answer,
                        sql_query=result.sql_query,
                        explanation=result.explanation,
                        insight=f"{result.insight} Returned {len(result.rows)} row(s).",
                        intent=result.intent,
                        warnings=result.warnings,
                    )
            latest_prompt = history.latest_user_prompt(active_session_id)
            if latest_prompt:
                history.update_title(
                    active_session_id,
                    latest_prompt[:28] + ("..." if len(latest_prompt) > 28 else ""),
                )
            render_sessions()
            render_starters()
            is_processing = False
            prompt.disabled = False
            send_btn.disabled = False
            page.update()

        page.run_task(run_pipeline_async)

    send_btn.on_click = on_ask
    prompt.on_submit = on_ask

    render_sessions()
    render_chat()

    sidebar = ft.Container(
        width=290,
        padding=14,
        border_radius=16,
        bgcolor="#0C1230",
        border=ft.border.all(1, "#1C2757"),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("TalkWithDB", size=20, weight=ft.FontWeight.BOLD, color="#E8EBFF"),
                        ft.Icon(ft.Icons.BOLT, color="#5A6BFF", size=18),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.TextField(
                    hint_text="Search sessions",
                    dense=True,
                    border_radius=10,
                    border_color="#25305F",
                    bgcolor="#12193A",
                ),
                ft.ElevatedButton(
                    "New Chat",
                    on_click=create_new_session,
                    style=ft.ButtonStyle(bgcolor="#3E53DF", color=ft.Colors.WHITE),
                ),
                ft.Divider(color="#1A244D"),
                ft.Text("Session History", size=12, color="#9EA7D5"),
                session_list,
                ft.Divider(color="#1A244D"),
                ft.Text("Connection", size=12, color="#9EA7D5"),
                host,
                ft.Row([port, user]),
                database,
                password,
                ft.ElevatedButton("Test & Connect", on_click=on_connect),
                status,
            ],
            spacing=10,
        ),
    )

    main_chat = ft.Container(
        expand=True,
        padding=20,
        border_radius=16,
        bgcolor="#0B1027",
        border=ft.border.all(1, "#1A244F"),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("What’s on your mind today?", size=38, weight=ft.FontWeight.BOLD, color="#F2F4FF"),
                        model_badge,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(
                    "Ask your data in plain English. Outputs include answer, explanation, and insight.",
                    color="#9DA5CF",
                ),
                ft.Container(content=starter_wrap, visible=True),
                ft.Container(
                    expand=True,
                    content=ft.Container(width=820, content=chat_feed),
                ),
                ft.Container(
                    bgcolor="#121833",
                    border_radius=16,
                    border=ft.border.all(1, "#2A356C"),
                    padding=10,
                    content=ft.Row([prompt, send_btn]),
                ),
            ],
            spacing=14,
        ),
    )

    page.add(
        ft.Row(
            controls=[sidebar, main_chat],
            expand=True,
            spacing=14,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)

