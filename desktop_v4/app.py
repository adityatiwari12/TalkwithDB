"""TalkWithDB Version 5 desktop chat application."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any, Optional

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
    page.title = "TalkWithDB Desktop"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1440
    page.window_height = 920
    page.bgcolor = "#0A0F1F"
    page.padding = 10

    history = HistoryService()
    pipeline = DesktopQueryPipeline()

    active_cfg: Optional[PostgresConnectionConfig] = None
    active_session_id = history.create_startup_session()
    is_processing = False
    active_request_id = 0
    details_visible = True
    editing_message_id: Optional[int] = None
    should_stick_to_bottom = True
    scroll_threshold_px = 140

    # Right panel details state
    details_sql = ft.Text("", size=12, color="#C9D3FF", selectable=True)
    details_meta = ft.Text("No query executed yet.", size=12, color="#9BA7D9", selectable=True)
    details_cached = ft.Text("", size=11, color="#7FA8FF")

    # Connection controls (settings modal)
    host = ft.TextField(label="Host", value="localhost", dense=True)
    port = ft.TextField(label="Port", value="5432", dense=True, width=120)
    database = ft.TextField(label="Database", value="chatdb", dense=True)
    user = ft.TextField(label="User", value="postgres", dense=True)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, dense=True)
    status = ft.Text("DB disconnected", color="#D4A52F", size=12)

    session_list = ft.Column(spacing=6, scroll=ft.ScrollMode.ALWAYS, expand=True)
    chat_feed = ft.Column(spacing=10, scroll=ft.ScrollMode.ALWAYS, expand=True, auto_scroll=False)
    starter_wrap = ft.Column(spacing=6, visible=True)

    prompt = ft.TextField(
        hint_text="Ask your database...",
        disabled=True,
        expand=True,
        shift_enter=True,
        border_color="#2C3D73",
        focused_border_color="#5B75FF",
        bgcolor="#101733",
        dense=True,
    )
    send_btn = ft.ElevatedButton(
        "Send",
        disabled=True,
        style=ft.ButtonStyle(
            bgcolor="#4C67FF",
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
    )
    input_hint = ft.Text("", size=11, color="#9FB0E8", visible=False)

    details_panel = ft.Container(
        width=340,
        padding=12,
        border_radius=10,
        bgcolor="#0D152E",
        border=ft.border.all(1, "#1F2B54"),
        visible=details_visible,
        content=ft.Column(
            [
                ft.Text("Details", size=14, weight=ft.FontWeight.BOLD, color="#E6EBFF"),
                ft.Divider(color="#1A2445"),
                ft.Text("Database Connection", size=12, color="#AAB6E8"),
                host,
                ft.Row([port, user]),
                database,
                password,
                ft.Row(
                    [
                        ft.ElevatedButton("Test & Connect", on_click=lambda e: on_connect(e)),
                        ft.IconButton(
                            ft.Icons.SETTINGS,
                            tooltip="Open settings modal",
                            on_click=lambda e: open_settings(e),
                        ),
                    ]
                ),
                status,
                details_cached,
                ft.Divider(color="#1A2445"),
                ft.Text("SQL", size=12, color="#AAB6E8"),
                ft.Container(
                    content=details_sql,
                    padding=8,
                    border_radius=8,
                    bgcolor="#0A1126",
                    border=ft.border.all(1, "#1A2A52"),
                ),
                ft.Divider(color="#1A2445"),
                ft.Text("Metadata", size=12, color="#AAB6E8"),
                details_meta,
            ],
            spacing=8,
        ),
    )

    def _cache_key(question: str, cfg: PostgresConnectionConfig) -> str:
        normalized = " ".join(question.strip().lower().split())
        scope = f"{cfg.host}:{cfg.port}/{cfg.database}/{cfg.user}"
        return hashlib.sha256(f"{scope}|{normalized}".encode("utf-8")).hexdigest()

    def has_user_messages(session_id: str) -> bool:
        return any(m.role == "user" for m in history.get_messages(session_id))

    def render_starters() -> None:
        starter_wrap.controls.clear()
        if has_user_messages(active_session_id):
            starter_wrap.visible = False
            return
        starter_wrap.visible = True
        for question in STARTER_QUESTIONS:
            starter_wrap.controls.append(
                ft.ElevatedButton(
                    question,
                    on_click=lambda _, q=question: handle_starter_click(q),
                    style=ft.ButtonStyle(
                        color="#D6DEFF",
                        bgcolor="#101933",
                        side=ft.BorderSide(1, "#2B3F77"),
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                )
            )

    def _assistant_full_text(item: Any) -> str:
        parts = [item.answer or ""]
        if (item.explanation or "").strip():
            parts.append(item.explanation)
        if (item.insight or "").strip():
            parts.append(item.insight)
        return "\n\n".join([p for p in parts if p.strip()])

    def user_bubble(message_id: int, text: str) -> ft.Row:
        edit_btn = ft.IconButton(
            ft.Icons.EDIT_OUTLINED,
            icon_size=14,
            icon_color="#AFC0FF",
            tooltip="Edit and re-run",
            on_click=lambda _: on_edit_user_message(message_id, text),
        )
        action_wrap = ft.Row([edit_btn], alignment=ft.MainAxisAlignment.END)

        return ft.Row(
            [
                action_wrap,
                ft.Container(
                    content=ft.Text(text, size=13, color=ft.Colors.WHITE),
                    bgcolor="#3E5AE0",
                    padding=10,
                    border_radius=10,
                )
            ],
            alignment=ft.MainAxisAlignment.END,
        )

    def assistant_message(
        message_id: int,
        answer: str,
        explanation: str,
        insight: str,
        allow_regenerate: bool,
    ) -> ft.Container:
        body = [ft.Text(answer, size=15, weight=ft.FontWeight.W_600, color="#EEF2FF")]
        if explanation.strip():
            body.append(ft.Text(explanation, size=12, color="#C7D0F5"))
        if insight.strip():
            body.append(ft.Text(insight, size=11, color="#8C9ACF"))

        copied_text = ft.Text("Copied", size=10, color="#9FD7A8", visible=False)
        copy_btn = ft.IconButton(
            ft.Icons.CONTENT_COPY_OUTLINED,
            icon_size=14,
            icon_color="#AFC0FF",
            tooltip="Copy response",
            on_click=lambda _: on_copy_assistant_message(message_id, copied_text),
        )
        regen_btn = ft.IconButton(
            ft.Icons.REPLAY_OUTLINED,
            icon_size=14,
            icon_color="#AFC0FF" if allow_regenerate else "#5C668B",
            tooltip="Regenerate response" if allow_regenerate else "Only latest response can regenerate",
            disabled=not allow_regenerate,
            on_click=lambda _: on_regenerate_assistant(message_id),
        )
        actions = ft.Row([copy_btn, regen_btn, copied_text], spacing=2, alignment=ft.MainAxisAlignment.END)

        return ft.Container(
            content=ft.Column([actions, *body], spacing=6),
            padding=10,
            border_radius=10,
            bgcolor="#121B38",
            border=ft.border.all(1, "#23315E"),
            ink=True,
        )

    def render_chat() -> None:
        chat_feed.controls.clear()
        messages = history.get_messages(active_session_id)
        assistant_ids = [m.id for m in messages if m.role == "assistant"]
        latest_assistant_id = assistant_ids[-1] if assistant_ids else None
        for item in messages:
            if item.role == "user":
                chat_feed.controls.append(user_bubble(item.id, item.content))
            else:
                chat_feed.controls.append(
                    assistant_message(
                        message_id=item.id,
                        answer=item.answer or "",
                        explanation=item.explanation or "",
                        insight=item.insight or "",
                        allow_regenerate=item.id == latest_assistant_id,
                    )
                )
        render_starters()
        maybe_scroll_to_bottom(force=False)

    def on_chat_scroll(event: ft.OnScrollEvent) -> None:
        nonlocal should_stick_to_bottom
        max_extent = float(getattr(event, "max_scroll_extent", 0.0) or 0.0)
        pixels = float(getattr(event, "pixels", 0.0) or 0.0)
        distance_from_bottom = max_extent - pixels
        should_stick_to_bottom = distance_from_bottom <= scroll_threshold_px

    def maybe_scroll_to_bottom(force: bool = False) -> None:
        if not (force or should_stick_to_bottom):
            return
        try:
            # offset=-1 scrolls to end in Flet scrollable controls.
            chat_feed.scroll_to(offset=-1, duration=220)
        except Exception:
            pass

    def on_copy_assistant_message(message_id: int, copied_label: ft.Text) -> None:
        messages = history.get_messages(active_session_id)
        msg = next((m for m in messages if m.id == message_id and m.role == "assistant"), None)
        if not msg:
            return
        copied_value = _assistant_full_text(msg)

        async def do_copy_and_feedback() -> None:
            copied_ok = False
            try:
                # This build exposes async clipboard service.
                await page.clipboard.set(copied_value)
                copied_ok = True
            except Exception:
                try:
                    # Fallback for builds exposing sync/alternate API.
                    if hasattr(page, "set_clipboard"):
                        page.set_clipboard(copied_value)
                        copied_ok = True
                except Exception:
                    copied_ok = False

            copied_label.value = "Copied" if copied_ok else "Copy failed"
            copied_label.color = "#9FD7A8" if copied_ok else "#FF9C9C"
            copied_label.visible = True
            page.update()
            await asyncio.sleep(1.0)
            copied_label.visible = False
            page.update()

        page.run_task(do_copy_and_feedback)

    def on_edit_user_message(message_id: int, content: str) -> None:
        nonlocal editing_message_id
        if is_processing:
            return
        editing_message_id = message_id
        prompt.value = content
        input_hint.value = "Editing previous question - submit to replace and re-run"
        input_hint.visible = True
        prompt.focus()
        page.update()

    def on_regenerate_assistant(message_id: int) -> None:
        if is_processing:
            return
        prev_user = history.get_previous_user_message(active_session_id, message_id)
        if not prev_user:
            return
        on_ask(
            None,
            question_override=prev_user.content,
            regenerate_assistant_id=message_id,
        )

    def render_sessions() -> None:
        session_list.controls.clear()
        for rec in history.list_sessions():
            is_active = rec.session_id == active_session_id
            session_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                rec.title,
                                size=12,
                                color="#EFF3FF" if is_active else "#A3AFDA",
                                expand=True,
                                no_wrap=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_size=14,
                                icon_color="#8E9ACB",
                                tooltip="Delete chat",
                                on_click=lambda _, sid=rec.session_id: delete_session(sid),
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=8,
                    border_radius=8,
                    bgcolor="#1D2A59" if is_active else "#0F1733",
                    border=ft.border.all(1, "#2C3E79" if is_active else "#1A2448"),
                    on_click=lambda _, sid=rec.session_id: switch_session(sid),
                    ink=True,
                )
            )

    def delete_session(session_id: str) -> None:
        nonlocal active_session_id
        if is_processing:
            return
        history.delete_session(session_id)
        sessions = history.list_sessions()
        if not sessions:
            active_session_id = history.create_session("New chat")
        elif active_session_id == session_id:
            active_session_id = sessions[0].session_id
        render_sessions()
        render_chat()
        page.update()

    def switch_session(session_id: str) -> None:
        nonlocal active_session_id
        active_session_id = session_id
        render_sessions()
        render_chat()
        page.update()

    def create_new_session(_: Any = None) -> None:
        nonlocal active_session_id
        if is_processing:
            return
        active_session_id = history.create_session("New chat")
        render_sessions()
        render_chat()
        page.update()

    def open_settings(_: Any = None) -> None:
        settings_dialog.open = True
        page.dialog = settings_dialog
        page.update()

    def close_settings(_: Any = None) -> None:
        settings_dialog.open = False
        page.update()

    def on_connect(_: Any = None) -> None:
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
            status.color = "#FF7A7A"
            page.update()
            return

        ok, error = test_postgres_connection(cfg)
        if ok:
            active_cfg = cfg
            status.value = f"Connected: {cfg.database} @ {cfg.host}:{cfg.port}"
            status.color = "#79D88A"
            prompt.disabled = False
            send_btn.disabled = False
        else:
            active_cfg = None
            status.value = f"Connection failed: {error}"
            status.color = "#FF7A7A"
            prompt.disabled = True
            send_btn.disabled = True
        page.update()

    def handle_starter_click(text: str) -> None:
        if is_processing:
            return
        prompt.value = text
        on_ask(None)

    async def typewriter_render(text_control: ft.Text, text: str) -> None:
        text_control.value = ""
        for idx in range(1, len(text) + 1, 7):
            text_control.value = text[:idx]
            page.update()
            maybe_scroll_to_bottom(force=False)
            await asyncio.sleep(0.01)
        text_control.value = text
        page.update()
        maybe_scroll_to_bottom(force=False)

    def on_ask(
        _: Any = None,
        question_override: Optional[str] = None,
        regenerate_assistant_id: Optional[int] = None,
    ) -> None:
        nonlocal is_processing
        nonlocal active_request_id
        nonlocal editing_message_id

        if is_processing:
            return
        if not active_cfg:
            status.value = "Connect database from Settings first."
            status.color = "#FF7A7A"
            page.update()
            return

        question = (question_override if question_override is not None else prompt.value).strip()
        if not question:
            return

        is_regenerate = regenerate_assistant_id is not None
        is_editing = editing_message_id is not None and not is_regenerate and question_override is None
        target_assistant_id = regenerate_assistant_id

        prompt.value = ""
        if not is_regenerate:
            input_hint.visible = False

        # Single unified assistant placeholder
        answer_text = ft.Text("Thinking.", size=15, weight=ft.FontWeight.W_600, color="#EEF2FF")
        explanation_text = ft.Text("", size=12, color="#C7D0F5")
        insight_text = ft.Text("", size=11, color="#8C9ACF")
        assistant_block = ft.Container(
            content=ft.Column([answer_text, explanation_text, insight_text], spacing=6),
            padding=10,
            border_radius=10,
            bgcolor="#121B38",
            border=ft.border.all(1, "#23315E"),
        )

        if is_regenerate and target_assistant_id is not None:
            render_chat()
            existing_messages = history.get_messages(active_session_id)
            target_index = next(
                (idx for idx, m in enumerate(existing_messages) if m.id == target_assistant_id and m.role == "assistant"),
                None,
            )
            if target_index is None:
                return
            chat_feed.controls[target_index] = assistant_block
        elif is_editing and editing_message_id is not None:
            history.update_user_message(active_session_id, editing_message_id, question)
            history.truncate_after_message(active_session_id, editing_message_id)
            history.add_message(active_session_id, role="assistant", content="")
            editing_message_id = None
            render_chat()
            if chat_feed.controls:
                chat_feed.controls[-1] = assistant_block
        else:
            history.add_message(active_session_id, role="user", content=question)
            history.add_message(active_session_id, role="assistant", content="")
            render_chat()
            if chat_feed.controls:
                chat_feed.controls[-1] = assistant_block
            starter_wrap.visible = False

        is_processing = True
        active_request_id += 1
        request_id = active_request_id
        prompt.disabled = True
        send_btn.disabled = True
        page.update()
        maybe_scroll_to_bottom(force=True)

        async def animate_loader() -> None:
            dots = 0
            while is_processing and request_id == active_request_id:
                dots = (dots % 3) + 1
                answer_text.value = "Thinking" + ("." * dots)
                page.update()
                await asyncio.sleep(0.28)

        async def run_pipeline_async() -> None:
            nonlocal is_processing
            cache_key = _cache_key(question, active_cfg)
            cached = history.get_cached_response(cache_key)
            from_cache = False
            result_payload: dict[str, Any] = {}

            if cached:
                from_cache = True
                final_answer = cached["answer"]
                if cached.get("warnings"):
                    final_answer += "\nWarnings: " + "; ".join(cached["warnings"])
                await typewriter_render(answer_text, final_answer)
                explanation_text.value = cached["explanation"]
                insight_text.value = cached["insight"]
                result_payload = {
                    "sql_query": cached["sql_query"],
                    "answer": final_answer,
                    "explanation": cached["explanation"],
                    "insight": cached["insight"],
                    "intent": cached["intent"],
                }
                details_sql.value = cached["sql_query"] or "No SQL available."
                details_meta.value = f"Intent: {cached['intent']}\nWarnings: {', '.join(cached.get('warnings', [])) or 'None'}"
                details_cached.value = "Cached response"
            else:
                result = await asyncio.to_thread(pipeline.run, question, active_cfg)
                if result.error:
                    await typewriter_render(answer_text, f"Error: {result.error}")
                    explanation_text.value = result.explanation
                    insight_text.value = result.insight
                    result_payload = {
                        "sql_query": result.sql_query,
                        "answer": f"Error: {result.error}",
                        "explanation": result.explanation,
                        "insight": result.insight,
                        "intent": result.intent,
                    }
                    details_sql.value = result.sql_query or "No SQL available."
                    details_meta.value = "Execution error"
                    details_cached.value = ""
                else:
                    final_answer = result.answer
                    if result.warnings:
                        final_answer += "\nWarnings: " + "; ".join(result.warnings)
                    await typewriter_render(answer_text, final_answer)
                    explanation_text.value = result.explanation
                    insight_text.value = result.insight
                    result_payload = {
                        "sql_query": result.sql_query,
                        "answer": final_answer,
                        "explanation": result.explanation,
                        "insight": result.insight,
                        "intent": result.intent,
                    }
                    history.set_cached_response(
                        cache_key=cache_key,
                        answer=final_answer,
                        sql_query=result.sql_query,
                        explanation=result.explanation,
                        insight=result.insight,
                        intent=result.intent,
                        warnings=result.warnings,
                    )
                    details_sql.value = result.sql_query or "No SQL available."
                    details_meta.value = (
                        f"Intent: {result.intent}\n"
                        f"Rows: {len(result.rows)}\n"
                        f"Warnings: {', '.join(result.warnings) or 'None'}\n"
                        f"Supplementary queries: {len(result.supplementary_queries)}"
                    )
                    details_cached.value = ""

            if is_regenerate and target_assistant_id is not None:
                history.update_assistant_message(
                    session_id=active_session_id,
                    message_id=target_assistant_id,
                    sql_query=result_payload.get("sql_query", ""),
                    answer=result_payload.get("answer", ""),
                    explanation=result_payload.get("explanation", ""),
                    insight=result_payload.get("insight", ""),
                    intent=result_payload.get("intent", "general_query"),
                )
            else:
                latest = history.get_messages(active_session_id)
                if latest:
                    last_message = latest[-1]
                    if last_message.role == "assistant":
                        history.update_assistant_message(
                            session_id=active_session_id,
                            message_id=last_message.id,
                            sql_query=result_payload.get("sql_query", ""),
                            answer=result_payload.get("answer", ""),
                            explanation=result_payload.get("explanation", ""),
                            insight=result_payload.get("insight", ""),
                            intent=result_payload.get("intent", "general_query"),
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
            input_hint.visible = False
            if not from_cache:
                page.update()
            page.update()
            maybe_scroll_to_bottom(force=False)

        page.run_task(animate_loader)
        page.run_task(run_pipeline_async)

    def toggle_details(_: Any = None) -> None:
        nonlocal details_visible
        details_visible = not details_visible
        details_panel.visible = details_visible
        page.update()

    def on_keyboard(event: ft.KeyboardEvent) -> None:
        key = (event.key or "").lower()
        if key == "n" and (getattr(event, "ctrl", False) or getattr(event, "meta", False)):
            create_new_session()

    settings_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Database Settings"),
        content=ft.Column(
            [host, ft.Row([port, user]), database, password, status],
            tight=True,
            spacing=10,
        ),
        actions=[
            ft.TextButton("Close", on_click=close_settings),
            ft.ElevatedButton("Test & Connect", on_click=on_connect),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    send_btn.on_click = on_ask
    prompt.on_submit = on_ask
    page.on_keyboard_event = on_keyboard
    chat_feed.on_scroll = on_chat_scroll

    render_sessions()
    render_chat()

    sidebar = ft.Container(
        width=250,
        padding=10,
        border_radius=10,
        bgcolor="#0C1530",
        border=ft.border.all(1, "#1E2A52"),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("TalkWithDB", size=16, weight=ft.FontWeight.BOLD, color="#EEF2FF"),
                        ft.Icon(ft.Icons.SMART_TOY, size=16, color="#6F84FF"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.ElevatedButton(
                    "New Chat",
                    on_click=create_new_session,
                    style=ft.ButtonStyle(
                        bgcolor="#253EBC",
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
                ft.Divider(color="#1A2445"),
                session_list,
            ],
            spacing=8,
        ),
    )

    top_bar = ft.Row(
        [
            ft.Text("Database Assistant", size=20, weight=ft.FontWeight.BOLD, color="#F2F4FF"),
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(f"Model: {pipeline.model}", size=11, color="#D4DDFF"),
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        border_radius=14,
                        bgcolor="#172043",
                    ),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Settings", on_click=open_settings),
                    ft.IconButton(
                        ft.Icons.CHEVRON_RIGHT if details_visible else ft.Icons.CHEVRON_LEFT,
                        tooltip="Toggle details panel",
                        on_click=toggle_details,
                    ),
                ]
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    main_chat = ft.Container(
        expand=True,
        padding=12,
        border_radius=10,
        bgcolor="#0B1228",
        border=ft.border.all(1, "#1E2B54"),
        content=ft.Column(
            [
                top_bar,
                ft.Container(content=starter_wrap),
                ft.Container(
                    expand=True,
                    content=ft.Container(width=920, content=chat_feed),
                ),
                ft.Container(
                    bgcolor="#101936",
                    border_radius=10,
                    border=ft.border.all(1, "#2A3D75"),
                    padding=8,
                    content=ft.Column(
                        [
                            input_hint,
                            ft.Row([prompt, send_btn]),
                        ],
                        spacing=4,
                    ),
                ),
            ],
            spacing=8,
        ),
    )

    page.add(
        ft.Row(
            controls=[sidebar, main_chat, details_panel],
            expand=True,
            spacing=10,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)

