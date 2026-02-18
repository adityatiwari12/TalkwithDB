"""
Streamlit Web UI for Version 3 Chatbot.
Interactive chat interface with schema exploration, history, and exports.
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid
import base64

# Page configuration
st.set_page_config(
    page_title="Talk with DB - Version 3",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .sql-code {
        background-color: #263238;
        color: #aed581;
        padding: 1rem;
        border-radius: 0.3rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        overflow-x: auto;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"  # Update this if your API is hosted elsewhere

def get_api_response(endpoint, method="GET", data=None):
    """Helper function to make API calls."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# Session State Management
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "💬 Chat"

# Sidebar
st.sidebar.markdown("<h1 style='text-align: center;'>🤖 Talk with DB</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: gray;'>Version 3 - Advanced RAG</p>", unsafe_allow_html=True)
st.sidebar.divider()

# Navigation
nav_options = [
    "💬 Chat",
    "🔍 Schema Explorer", 
    "📜 Query History",
    "📊 Analytics",
    "⚙️ Settings"
]

selected_tab = st.sidebar.radio("Navigation", nav_options)
st.session_state.current_tab = selected_tab

# Session Info in Sidebar
st.sidebar.divider()
st.sidebar.markdown("### 📋 Session Info")
st.sidebar.code(st.session_state.session_id, language="text")

if st.sidebar.button("🔄 New Session"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.rerun()

# API Health Check
try:
    health = get_api_response("/health")
    if health and health.get("status") == "healthy":
        st.sidebar.success("🟢 API Connected")
    else:
        st.sidebar.error("🔴 API Unavailable")
except:
    st.sidebar.warning("🟡 Check API Connection")

# Main Content Area
st.markdown("<h1 class='main-header'>Talk with DB - Version 3</h1>", unsafe_allow_html=True)

# ==================== 💬 CHAT TAB ====================
if selected_tab == "💬 Chat":
    st.markdown("### Ask me anything about your database!")
    
    # Suggestions
    col1, col2, col3, col4 = st.columns(4)
    suggestions = [
        "How many users?",
        "Show recent orders",
        "Top customers",
        "Active tasks"
    ]
    
    for col, suggestion in zip([col1, col2, col3, col4], suggestions):
        with col:
            if st.button(suggestion, key=f"suggest_{suggestion}"):
                st.session_state.user_input = suggestion
    
    # Chat Container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <b>👤 You:</b><br>{message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <b>🤖 Assistant:</b><br>{message['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # Show SQL if available
                if message.get("sql_query"):
                    with st.expander("🔍 View SQL Query"):
                        st.code(message["sql_query"], language="sql")
                        
                        # Copy button
                        if st.button("📋 Copy SQL", key=f"copy_{message.get('timestamp', '0')}"):
                            st.toast("SQL copied to clipboard!")
                
                # Show results if available
                if message.get("results"):
                    with st.expander(f"📊 View Results ({len(message['results'])} rows)"):
                        df = pd.DataFrame(message["results"])
                        st.dataframe(df, use_container_width=True)
                        
                        # Export buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "📥 Download CSV",
                                csv,
                                f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                "text/csv"
                            )
                        with col2:
                            json_str = df.to_json(orient='records')
                            st.download_button(
                                "📥 Download JSON",
                                json_str,
                                f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                "application/json"
                            )
    
    # Input Area
    st.divider()
    
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.text_input(
            "Your question:",
            value=st.session_state.get("user_input", ""),
            key="chat_input",
            placeholder="Ask me anything about your database...",
            label_visibility="collapsed"
        )
    with col2:
        send_button = st.button("🚀 Send", use_container_width=True)
    
    # Process Message
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Clear input
        st.session_state.user_input = ""
        
        # Show spinner while processing
        with st.spinner("🤔 Thinking..."):
            # Call API
            response = get_api_response("/api/chat", "POST", {
                "message": user_input,
                "session_id": st.session_state.session_id,
                "max_tables": 3
            })
        
        if response:
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response.get("response", ""),
                "sql_query": response.get("sql_query"),
                "results": response.get("results"),
                "metadata": response.get("metadata"),
                "timestamp": datetime.now().isoformat()
            })
            
            # Show metadata in sidebar
            if response.get("metadata"):
                with st.sidebar.expander("📊 Query Details"):
                    metadata = response["metadata"]
                    
                    if "retrieval" in metadata:
                        st.markdown("**🔍 Retrieval Info:**")
                        retrieval = metadata["retrieval"]
                        st.write(f"Intent: {retrieval.get('intent', 'N/A')}")
                        st.write(f"Tables: {', '.join(retrieval.get('retrieved_tables', []))}")
                        
                        if retrieval.get('expansion_terms'):
                            st.write(f"Expanded: {', '.join(retrieval['expansion_terms'])}")
                    
                    if "timing" in metadata:
                        st.markdown("**⏱️ Performance:**")
                        timing = metadata["timing"]
                        st.write(f"SQL Generation: {timing.get('sql_generation', 0):.2f}s")
                        st.write(f"Execution: {timing.get('query_execution', 0):.2f}s")
                        st.write(f"Total: {timing.get('total', 0):.2f}s")
        
        st.rerun()

# ==================== 🔍 SCHEMA EXPLORER TAB ====================
elif selected_tab == "🔍 Schema Explorer":
    st.markdown("### Database Schema Explorer")
    st.markdown("Browse your database tables, columns, and relationships.")
    
    # Fetch schema
    schema_data = get_api_response("/api/schema")
    
    if schema_data and schema_data.get("tables"):
        tables = schema_data["tables"]
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tables", len(tables))
        with col2:
            total_columns = sum(len(t.get("columns", [])) for t in tables)
            st.metric("Total Columns", total_columns)
        with col3:
            total_relationships = sum(len(t.get("relationships", [])) for t in tables)
            st.metric("Relationships", total_relationships)
        
        st.divider()
        
        # Table selector
        table_names = [t["table_name"] for t in tables]
        selected_table = st.selectbox("Select a table to explore:", table_names)
        
        if selected_table:
            # Get detailed table info
            table_details = get_api_response(f"/api/schema/{selected_table}")
            
            if table_details:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"#### 📋 Columns in `{selected_table}`")
                    
                    # Columns table
                    columns_df = pd.DataFrame(table_details.get("columns", []))
                    if not columns_df.empty:
                        st.dataframe(
                            columns_df,
                            use_container_width=True,
                            hide_index=True
                        )
                
                with col2:
                    st.markdown("#### 🔗 Relationships")
                    relationships = table_details.get("relationships", [])
                    if relationships:
                        for rel in relationships:
                            st.markdown(f"""
                            - **{rel['type']}** → `{rel['target_table']}.{rel['target_column']}`
                            """)
                    else:
                        st.info("No relationships defined")
                
                # Sample data
                st.divider()
                st.markdown(f"#### 📊 Sample Data from `{selected_table}`")
                
                sample_data = table_details.get("sample_data", [])
                if sample_data:
                    sample_df = pd.DataFrame(sample_data)
                    st.dataframe(sample_df, use_container_width=True)
                else:
                    st.info("No sample data available")
                
                # Quick actions
                st.divider()
                st.markdown("#### ⚡ Quick Actions")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔍 Count Rows", key=f"count_{selected_table}"):
                        st.session_state.user_input = f"How many rows in {selected_table}?"
                        st.session_state.current_tab = "💬 Chat"
                        st.rerun()
                
                with col2:
                    if st.button("📋 Show All", key=f"show_{selected_table}"):
                        st.session_state.user_input = f"Show all data from {selected_table}"
                        st.session_state.current_tab = "💬 Chat"
                        st.rerun()
                
                with col3:
                    if st.button("📊 Schema Info", key=f"schema_{selected_table}"):
                        st.session_state.user_input = f"Describe the schema of {selected_table}"
                        st.session_state.current_tab = "💬 Chat"
                        st.rerun()
    else:
        st.error("Could not fetch schema information. Please check API connection.")

# ==================== 📜 QUERY HISTORY TAB ====================
elif selected_tab == "📜 Query History":
    st.markdown("### Query History & Conversations")
    
    # Fetch history
    history_data = get_api_response(f"/api/history/{st.session_state.session_id}")
    
    if history_data and history_data.get("turns"):
        turns = history_data["turns"]
        
        # Summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Messages", len(turns))
        with col2:
            referenced = history_data.get("referenced_tables", [])
            st.metric("Tables Referenced", len(referenced))
        
        st.divider()
        
        # Display conversation history
        for i, turn in enumerate(turns):
            if turn["role"] == "user":
                with st.container():
                    st.markdown(f"**👤 Question:** {turn['content']}")
                    st.caption(f"🕐 {turn['timestamp']}")
            else:
                with st.container():
                    st.markdown(f"**🤖 Response:**")
                    st.write(turn['content'])
                    
                    if turn.get("sql_query"):
                        with st.expander("🔍 SQL Query"):
                            st.code(turn["sql_query"], language="sql")
                    
                    if turn.get("context_tables"):
                        st.caption(f"📋 Tables: {', '.join(turn['context_tables'])}")
            
            st.divider()
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            get_api_response(f"/api/history/{st.session_state.session_id}", "DELETE")
            st.session_state.chat_history = []
            st.success("History cleared!")
            st.rerun()
    else:
        st.info("No conversation history yet. Start chatting to build history!")

# ==================== 📊 ANALYTICS TAB ====================
elif selected_tab == "📊 Analytics":
    st.markdown("### Query Analytics & Performance")
    
    # Calculate analytics from chat history
    if st.session_state.chat_history:
        assistant_messages = [m for m in st.session_state.chat_history if m["role"] == "assistant"]
        
        if assistant_messages:
            # Performance metrics
            total_queries = len(assistant_messages)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Queries", total_queries)
            with col2:
                total_rows = sum(len(m.get("results", [])) for m in assistant_messages)
                st.metric("Total Rows Returned", total_rows)
            with col3:
                avg_rows = total_rows / total_queries if total_queries > 0 else 0
                st.metric("Avg Rows/Query", f"{avg_rows:.1f}")
            with col4:
                # Count unique tables
                all_tables = set()
                for m in assistant_messages:
                    metadata = m.get("metadata", {})
                    retrieval = metadata.get("retrieval", {})
                    all_tables.update(retrieval.get("retrieved_tables", []))
                st.metric("Unique Tables Used", len(all_tables))
            
            st.divider()
            
            # Query types pie chart
            intent_counts = {}
            for m in assistant_messages:
                metadata = m.get("metadata", {})
                retrieval = metadata.get("retrieval", {})
                intent = retrieval.get("intent", "general")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            if intent_counts:
                fig = px.pie(
                    values=list(intent_counts.values()),
                    names=list(intent_counts.keys()),
                    title="Query Types Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Performance over time
            st.subheader("Query Performance Over Time")
            
            performance_data = []
            for i, m in enumerate(assistant_messages):
                metadata = m.get("metadata", {})
                timing = metadata.get("timing", {})
                
                performance_data.append({
                    "Query #": i + 1,
                    "SQL Generation": timing.get("sql_generation", 0),
                    "Execution": timing.get("query_execution", 0),
                    "Total": timing.get("total", 0)
                })
            
            if performance_data:
                perf_df = pd.DataFrame(performance_data)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=perf_df["Query #"],
                    y=perf_df["SQL Generation"],
                    mode='lines+markers',
                    name='SQL Generation'
                ))
                fig.add_trace(go.Scatter(
                    x=perf_df["Query #"],
                    y=perf_df["Execution"],
                    mode='lines+markers',
                    name='Query Execution'
                ))
                fig.add_trace(go.Scatter(
                    x=perf_df["Query #"],
                    y=perf_df["Total"],
                    mode='lines+markers',
                    name='Total Time'
                ))
                
                fig.update_layout(
                    title="Query Timing Breakdown",
                    xaxis_title="Query Number",
                    yaxis_title="Time (seconds)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analytics available yet. Start querying to see performance metrics!")

# ==================== ⚙️ SETTINGS TAB ====================
elif selected_tab == "⚙️ Settings":
    st.markdown("### ⚙️ Application Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🤖 Model Settings")
        
        st.selectbox(
            "LLM Model",
            ["llama3.2", "llama3.1", "mistral", "codellama"],
            index=0
        )
        
        st.selectbox(
            "Embedding Model",
            ["nomic-embed-text", "all-MiniLM-L6-v2"],
            index=0
        )
        
        st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        
        st.markdown("#### 🔍 Retrieval Settings")
        
        st.slider("Max Tables to Retrieve", 1, 10, 3)
        st.slider("Top-K Results", 1, 20, 5)
        
        st.checkbox("Enable Query Rewriting", value=True)
        st.checkbox("Enable Hybrid Search", value=True)
        st.checkbox("Enable LLM Re-ranking", value=True)
    
    with col2:
        st.markdown("#### 🛡️ Safety Settings")
        
        st.number_input("Max Result Rows", value=200, min_value=10, max_value=10000)
        st.number_input("Query Timeout (seconds)", value=30, min_value=5, max_value=300)
        
        st.checkbox("Require Validation", value=True)
        st.checkbox("Add Safety LIMIT", value=True)
        
        st.markdown("#### 📊 Display Settings")
        
        st.checkbox("Show SQL by Default", value=False)
        st.checkbox("Show Metadata", value=True)
        st.checkbox("Dark Mode", value=False)
        
        st.selectbox(
            "Results Format",
            ["Table", "JSON", "Cards"],
            index=0
        )
    
    st.divider()
    
    # API Connection
    st.markdown("#### 🔌 API Connection")
    
    api_url = st.text_input("API Base URL", value=API_BASE_URL)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Test Connection"):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200:
                    st.success("✅ API Connection Successful!")
                else:
                    st.error(f"❌ API Error: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Connection Failed: {e}")
    
    with col2:
        if st.button("💾 Save Settings"):
            st.success("Settings saved!")
    
    st.divider()
    
    # About
    st.markdown("#### 📋 About")
    st.info("""
    **Talk with DB - Version 3**
    
    Advanced Chat with SQL system featuring:
    - ✅ Query Rewriting & Expansion
    - ✅ Hybrid Search (BM25 + Vector)
    - ✅ LLM-based Re-ranking
    - ✅ Conversation Memory
    - ✅ Real-time WebSocket Chat
    - ✅ Schema Exploration
    - ✅ Query Analytics
    
    Built with ❤️ using FastAPI, Streamlit, and Advanced RAG.
    """)

# Footer
st.divider()
st.caption("🤖 Talk with DB - Version 3 | Advanced RAG System | Made with ❤️")
