"""Version 4 desktop shell (initial scaffold)."""

from __future__ import annotations

import flet as ft

from desktop_v4.services.connection_service import (
    PostgresConnectionConfig,
    test_postgres_connection,
)


def main(page: ft.Page) -> None:
    page.title = "TalkWithDB Desktop v4"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 800

    host = ft.TextField(label="Host", value="localhost", width=260)
    port = ft.TextField(label="Port", value="5432", width=120)
    database = ft.TextField(label="Database", value="chatdb", width=220)
    user = ft.TextField(label="User", value="postgres", width=180)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=220)

    status = ft.Text("Disconnected", color=ft.Colors.AMBER_300)
    output = ft.Text("Connect to start querying your database.", selectable=True)
    prompt = ft.TextField(
        label="Ask in natural language",
        hint_text="Example: Show top 10 users by task count",
        disabled=True,
        expand=True,
    )
    send_btn = ft.ElevatedButton("Ask", disabled=True)

    def on_connect(_: ft.ControlEvent) -> None:
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
            output.value = "Port must be a valid integer."
            page.update()
            return

        ok, error = test_postgres_connection(cfg)
        if ok:
            status.value = "Connected"
            status.color = ft.Colors.GREEN_300
            output.value = (
                "Database connection is healthy.\n"
                "Next: wire NL-to-SQL pipeline into this desktop flow."
            )
            prompt.disabled = False
            send_btn.disabled = False
        else:
            status.value = "Connection failed"
            status.color = ft.Colors.RED_300
            output.value = f"Could not connect: {error}"
            prompt.disabled = True
            send_btn.disabled = True
        page.update()

    def on_ask(_: ft.ControlEvent) -> None:
        output.value = (
            "Desktop v4 scaffold active.\n\n"
            f"Question captured: {prompt.value}\n\n"
            "Next milestone wires this to the existing SQL generator and validator."
        )
        page.update()

    send_btn.on_click = on_ask

    page.add(
        ft.Row(
            controls=[
                ft.Container(
                    width=370,
                    padding=16,
                    border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
                    border_radius=10,
                    content=ft.Column(
                        controls=[
                            ft.Text("Connection", size=20, weight=ft.FontWeight.BOLD),
                            host,
                            ft.Row([port, user]),
                            database,
                            password,
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton("Test & Connect", on_click=on_connect),
                                    status,
                                ]
                            ),
                        ],
                        tight=True,
                    ),
                ),
                ft.VerticalDivider(width=12),
                ft.Container(
                    expand=True,
                    padding=16,
                    border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
                    border_radius=10,
                    content=ft.Column(
                        controls=[
                            ft.Text("Ask your database", size=20, weight=ft.FontWeight.BOLD),
                            ft.Row([prompt, send_btn]),
                            ft.Divider(),
                            ft.Text("Assistant Output", weight=ft.FontWeight.BOLD),
                            output,
                        ]
                    ),
                ),
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)

