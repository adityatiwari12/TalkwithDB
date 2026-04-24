"""ChatGPT-style Streamlit UI for TalkWithDB."""

from datetime import datetime
import os
import re
import time
import uuid
from typing import Any, Dict, List

import requests
import streamlit as st

st.set_page_config(
    page_title="Talk with DB",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Default to 127.0.0.1 to avoid occasional localhost resolution issues on Windows.
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")
STARTER_QUESTIONS = [
    "How many users are there in the system?",
    "List all projects and their current status.",
    "Show pending tasks with assignee names.",
    "Which users have the highest number of assigned tasks?",
    "How many completed tasks does each project have?",
    "Show overdue tasks that are not completed.",
]

# Runtime prompt guidance without changing backend implementation.
RESPONSE_GUIDANCE = (
    "Generate SQL, execute it, and return a clear, user-friendly response that "
    "includes the answer, a simple explanation, and optional insight. "
    "Avoid one-line replies."
)

st.markdown(
    """
<style>
    :root {
        --bg-main: #0f172a;
        --bg-surface: #131c31;
        --bg-surface-soft: #18233b;
        --text-main: #e2e8f0;
        --text-muted: #94a3b8;
        --accent-a: #4f46e5;
        --accent-b: #7c3aed;
        --accent-user: linear-gradient(135deg, var(--accent-a), var(--accent-b));
        --shadow-soft: 0 8px 24px rgba(2, 6, 23, 0.35);
    }
    .stApp {
        background-color: var(--bg-main);
        color: var(--text-main);
    }
    .block-container {
        max-width: 100% !important;
        padding-top: 1rem;
        padding-left: 1.2rem;
        padding-right: 1.2rem;
        padding-bottom: 6rem;
    }
    [data-testid="stSidebar"] {
        background-color: #0d1427;
        border-right: 1px solid #1f2a44;
    }
    [data-testid="stSidebarContent"] {
        overflow-y: auto;
        max-height: 100vh;
    }
    .sidebar-title {
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 0.65rem;
    }
    .app-shell {
        max-width: 800px;
        margin: 0 auto 90px auto;
        padding-top: 0.3rem;
    }
    .chat-title {
        font-size: 1.35rem;
        font-weight: 650;
        margin-bottom: 0.25rem;
    }
    .chat-subtitle {
        color: var(--text-muted);
        margin-bottom: 1.15rem;
        font-size: 0.92rem;
    }
    .typing-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.65rem 0.9rem;
        border-radius: 16px;
        background: var(--bg-surface-soft);
        color: var(--text-muted);
        margin-bottom: 1rem;
        box-shadow: var(--shadow-soft);
    }
    .dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #a8b4c7;
        animation: blink 1.4s infinite ease-in-out;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink {
        0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    .stChatMessage {
        margin-bottom: 1rem;
    }
    [data-testid="stChatMessageAvatarUser"] + div {
        margin-left: auto;
        max-width: 82%;
    }
    [data-testid="stChatMessageAvatarAssistant"] + div {
        max-width: 82%;
    }
    [data-testid="stChatMessageAvatarUser"] + div [data-testid="stMarkdownContainer"] {
        background: var(--accent-user);
        color: #ffffff;
        border-radius: 20px;
        padding: 0.85rem 1rem;
        box-shadow: var(--shadow-soft);
    }
    [data-testid="stChatMessageAvatarAssistant"] + div [data-testid="stMarkdownContainer"] {
        background: var(--bg-surface);
        border-radius: 18px;
        padding: 0.9rem 1rem;
        box-shadow: var(--shadow-soft);
    }
    .assistant-sections {
        line-height: 1.55;
        font-size: 0.96rem;
    }
    .assistant-sections .section {
        margin-bottom: 0.6rem;
    }
    .assistant-sections .label {
        color: #cbd5e1;
        font-size: 0.78rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .assistant-sections .value {
        color: #e2e8f0;
    }
    [data-testid="stChatInput"] {
        background: rgba(15, 23, 42, 0.92);
        border-top: 1px solid #1f2a44;
        padding-top: 0.65rem;
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 14px !important;
        background: #131c31 !important;
        color: #e2e8f0 !important;
        border: 1px solid #253251 !important;
        transition: all 0.2s ease;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 1px #4f46e5;
    }
    .stButton > button {
        border-radius: 12px;
        border: 1px solid #2a3758;
        background: #111a2e;
        color: #d6deec;
        transition: all 0.18s ease;
    }
    .stButton > button:hover {
        border-color: #4f46e5;
        transform: translateY(-1px);
        background: #17223d;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_session_state() -> None:
    if "chats" not in st.session_state:
        first_chat_id = str(uuid.uuid4())
        st.session_state.chats = {
            first_chat_id: {
                "title": "New chat",
                "session_id": str(uuid.uuid4()),
                "messages": [],
                "created_at": datetime.now().isoformat(),
            }
        }
        st.session_state.active_chat_id = first_chat_id
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "animated_message_ids" not in st.session_state:
        st.session_state.animated_message_ids = set()


def active_chat() -> Dict[str, Any]:
    return st.session_state.chats[st.session_state.active_chat_id]


def check_api_health() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def start_new_chat() -> None:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {
        "title": "New chat",
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "created_at": datetime.now().isoformat(),
    }
    st.session_state.active_chat_id = new_id


def update_chat_title(chat_id: str) -> None:
    chat = st.session_state.chats[chat_id]
    for msg in chat["messages"]:
        if msg["role"] == "user":
            text = msg["content"].strip()
            chat["title"] = text[:36] + ("..." if len(text) > 36 else "")
            return


def call_chat_api(question: str, session_id: str) -> Dict[str, Any]:
    payload_message = (
        f"{question}\n\n"
        f"Instruction for response quality: {RESPONSE_GUIDANCE}"
    )
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={
                "message": payload_message,
                "session_id": session_id,
                "max_tables": 3,
            },
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()
        return {
            "response": f"Error: {response.status_code} - {response.text}",
            "sql_query": None,
            "results": None,
            "metadata": {},
        }
    except Exception as exc:
        return {
            "response": f"Connection error: {exc}",
            "sql_query": None,
            "results": None,
            "metadata": {},
        }


def format_assistant_response(data: Dict[str, Any]) -> str:
    raw_response = (data.get("response") or "").strip()
    sql = data.get("sql_query")
    results = data.get("results")
    metadata = data.get("metadata", {})
    row_count = metadata.get("execution", {}).get("row_count")

    answer = raw_response or "I could not generate a response."
    explanation_parts: List[str] = []
    if sql:
        explanation_parts.append("I generated SQL from your question and executed it on the database.")
    if row_count is not None:
        explanation_parts.append(f"The query returned {row_count} row(s).")
    if not explanation_parts:
        explanation_parts.append("The backend processed your question and returned this result.")

    insight = ""
    if isinstance(results, list) and results:
        first_row = results[0]
        if isinstance(first_row, dict):
            fields = ", ".join(list(first_row.keys())[:3])
            insight = f"You can drill deeper by filtering or grouping by fields like `{fields}`."

    sections = [
        (
            '<div class="section"><div class="label">Answer</div>'
            f'<div class="value">{answer}</div></div>'
        ),
        (
            '<div class="section"><div class="label">Explanation</div>'
            f'<div class="value">{" ".join(explanation_parts)}</div></div>'
        ),
    ]
    if insight:
        sections.append(
            '<div class="section"><div class="label">Insight</div>'
            f'<div class="value">{insight}</div></div>'
        )
    return f'<div class="assistant-sections">{"".join(sections)}</div>'


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Conversations</div>', unsafe_allow_html=True)
        if st.button("✨  New Chat", use_container_width=True, type="primary"):
            start_new_chat()
            st.rerun()

        for chat_id, chat in sorted(
            st.session_state.chats.items(),
            key=lambda item: item[1]["created_at"],
            reverse=True,
        ):
            is_active = chat_id == st.session_state.active_chat_id
            label = ("💬  " if is_active else "•  ") + chat["title"]
            if st.button(
                label,
                key=f"chat_switch_{chat_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_chat_id = chat_id
                st.rerun()

        st.divider()
        status = "Online" if check_api_health() else "Offline"
        st.caption(f"⚡ API {status}")


def render_messages(chat: Dict[str, Any]) -> None:
    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    st.markdown('<div class="chat-title">Talk with DB</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chat-subtitle">Ask questions in plain English. I will return answer, explanation, and insight.</div>',
        unsafe_allow_html=True,
    )

    if not chat["messages"]:
        st.caption("Try one of these sample questions:")
        cols = st.columns(2)
        for idx, question in enumerate(STARTER_QUESTIONS):
            with cols[idx % 2]:
                if st.button(
                    question,
                    key=f"starter_q_{idx}",
                    use_container_width=True,
                    disabled=st.session_state.processing,
                ):
                    submit_user_prompt(chat, question)
                    st.rerun()

    for msg in chat["messages"]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            if msg["role"] == "assistant" and msg.get("is_placeholder"):
                placeholder = st.empty()
                placeholder.markdown(
                    """
                    <div class="typing-indicator">
                        <span>Thinking</span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                if (
                    msg["role"] == "assistant"
                    and msg.get("animate")
                    and msg.get("message_id") not in st.session_state.animated_message_ids
                ):
                    _render_typewriter_assistant(msg)
                else:
                    st.markdown(msg["content"], unsafe_allow_html=(msg["role"] == "assistant"))
            if msg["role"] == "assistant" and msg.get("sql_query"):
                with st.expander("View SQL", expanded=False):
                    st.code(msg["sql_query"], language="sql")
    st.markdown("</div>", unsafe_allow_html=True)


def handle_user_input(chat: Dict[str, Any]) -> None:
    prompt = st.chat_input("Ask about your database...", disabled=st.session_state.processing)
    if not prompt or st.session_state.processing:
        return
    submit_user_prompt(chat, prompt)
    st.rerun()


def submit_user_prompt(chat: Dict[str, Any], prompt: str) -> None:
    chat["messages"].append({"role": "user", "content": prompt, "sql_query": None})
    chat["messages"].append(
        {
            "role": "assistant",
            "content": "Thinking...",
            "sql_query": None,
            "is_placeholder": True,
            "message_id": str(uuid.uuid4()),
        }
    )
    st.session_state.processing = True
    update_chat_title(st.session_state.active_chat_id)


def process_pending_turn(chat: Dict[str, Any]) -> None:
    if (
        st.session_state.processing
        and len(chat["messages"]) >= 2
        and chat["messages"][-2]["role"] == "user"
        and chat["messages"][-1]["role"] == "assistant"
        and chat["messages"][-1].get("is_placeholder")
    ):
        user_message = chat["messages"][-2]["content"]
        data = call_chat_api(user_message, chat["session_id"])
        assistant_text = format_assistant_response(data)
        chat["messages"][-1] = {
            "role": "assistant",
            "content": assistant_text,
            "sql_query": data.get("sql_query"),
            "is_placeholder": False,
            "animate": True,
            "message_id": chat["messages"][-1].get("message_id", str(uuid.uuid4())),
        }
        st.session_state.processing = False
        st.rerun()


def _render_typewriter_assistant(msg: Dict[str, Any]) -> None:
    """Render a lightweight typewriter effect, then show full formatted card."""
    container = st.empty()
    raw_html = msg.get("content", "")
    text_preview = re.sub(r"<[^>]+>", "", raw_html)
    text_preview = re.sub(r"\s+", " ", text_preview).strip()
    if not text_preview:
        container.markdown(raw_html, unsafe_allow_html=True)
    else:
        step = 8
        for idx in range(step, len(text_preview) + step, step):
            container.markdown(text_preview[:idx])
            time.sleep(0.012)
        container.markdown(raw_html, unsafe_allow_html=True)
    if msg.get("message_id"):
        st.session_state.animated_message_ids.add(msg["message_id"])


def main() -> None:
    initialize_session_state()
    render_sidebar()
    chat = active_chat()
    render_messages(chat)
    handle_user_input(chat)
    process_pending_turn(chat)


if __name__ == "__main__":
    main()
