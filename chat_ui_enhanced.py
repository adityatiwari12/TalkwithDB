"""
Professional Streamlit Web UI for Version 3 Chatbot.
Enhanced with modern design, quick questions, and detailed query processing display.
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
import time
from typing import Dict, List, Any

# Page configuration
st.set_page_config(
    page_title="Talk with DB - Professional AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS for professional look
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(45deg, #1f77b4, #9c27b0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Chat styling */
    .chat-container {
        max-width: 1000px;
        margin: 0 auto;
    }
    
    .chat-message {
        padding: 1.2rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .chat-message:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .user-message {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        border-left: 5px solid #2196f3;
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f3e5f5, #e1bee7);
        border-left: 5px solid #9c27b0;
        margin-right: 2rem;
    }
    
    .processing-message {
        background: linear-gradient(135deg, #fff3e0, #ffe0b2);
        border-left: 5px solid #ff9800;
        margin-right: 2rem;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
    }
    
    /* SQL Code styling */
    .sql-code {
        background: #263238;
        color: #aed581;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        overflow-x: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Quick questions styling */
    .quick-questions {
        background: linear-gradient(135deg, #f5f5f5, #e8eaf6);
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .question-button {
        background: linear-gradient(135deg, #2196f3, #1976d2);
        color: white;
        border: none;
        padding: 0.8rem 1.2rem;
        border-radius: 2rem;
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3);
    }
    
    .question-button:hover {
        background: linear-gradient(135deg, #1976d2, #1565c0);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(33, 150, 243, 0.4);
    }
    
    /* Metrics styling */
    .metric-card {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #4caf50;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #4caf50;
    }
    
    .metric-label {
        color: #666;
        font-size: 0.9rem;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-online {
        background-color: #4caf50;
        animation: pulse-green 2s infinite;
    }
    
    .status-processing {
        background-color: #ff9800;
        animation: pulse-orange 1.5s infinite;
    }
    
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
        100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
    }
    
    @keyframes pulse-orange {
        0% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 152, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0); }
    }
    
    /* Hide streamlit branding */
    .stDeployButton {
        display: none;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .user-message, .assistant-message, .processing-message {
            margin-left: 0.5rem;
            margin-right: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8001"

# Most asked questions
MOST_ASKED_QUESTIONS = [
    "How many users are in the system?",
    "Show me recent orders with details",
    "List all projects and their status",
    "What are the tasks for Project 1?",
    "Count total customers",
    "Show orders by customer",
    "List all products",
    "Show pending tasks",
    "What are the completed projects?",
    "Show revenue by month"
]

def initialize_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'processing' not in st.session_state:
        st.session_state.processing = False

def check_api_health():
    """Check if API is healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_database_schema():
    """Get database schema information"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/schema", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def send_chat_message(message: str) -> Dict[str, Any]:
    """Send message to chat API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={
                'message': message,
                'session_id': st.session_state.session_id,
                'max_tables': 3
            },
            timeout=90
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'response': f"Error: {response.status_code} - {response.text}",
                'sql_query': None,
                'results': None,
                'metadata': {}
            }
    except Exception as e:
        return {
            'response': f"Connection error: {str(e)}",
            'sql_query': None,
            'results': None,
            'metadata': {}
        }

def display_chat_message(message: str, is_user: bool = False, sql_query: str = None, 
                        processing_time: float = None, result_count: int = None):
    """Display a chat message with enhanced styling"""
    if is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 You:</strong> {message}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show processing information if available
        processing_info = ""
        if processing_time:
            processing_info = f"<br><small>⏱️ Processing time: {processing_time:.2f}s</small>"
        if result_count is not None:
            processing_info += f"<br><small>📊 Results: {result_count} rows returned</small>"
        
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>🤖 Assistant:</strong> {message}{processing_info}
        </div>
        """, unsafe_allow_html=True)
        
        # Show SQL query if available
        if sql_query:
            with st.expander("🔍 View SQL Query", expanded=False):
                st.markdown(f"""
                <div class="sql-code">
                {sql_query}
                </div>
                """, unsafe_allow_html=True)

def display_processing_message(message: str):
    """Display a processing message with animation"""
    st.markdown(f"""
    <div class="chat-message processing-message">
        <strong>⚙️ Processing:</strong> {message}
    </div>
    """, unsafe_allow_html=True)

def display_quick_questions():
    """Display most asked questions as clickable buttons"""
    st.markdown("""
    <div class="quick-questions">
        <h3>💡 Most Asked Questions</h3>
        <p>Click on any question below to get instant answers:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for better layout
    cols = st.columns(2)
    
    for i, question in enumerate(MOST_ASKED_QUESTIONS):
        col = cols[i % 2]
        with col:
            if st.button(question, key=f"quick_q_{i}", use_container_width=True):
                # Trigger the question
                handle_question_click(question)

def handle_question_click(question: str):
    """Handle quick question click"""
    # Add user message to history
    st.session_state.chat_history.append({
        'message': question,
        'is_user': True,
        'timestamp': datetime.now()
    })
    
    # Set processing state
    st.session_state.processing = True
    
    # Process the question
    process_question(question)

def process_question(question: str):
    """Process a question and display results"""
    # Display processing message
    display_processing_message(f"Analyzing your question: '{question}'")
    
    # Get response from API
    response_data = send_chat_message(question)
    
    # Extract metadata
    metadata = response_data.get('metadata', {})
    timing = metadata.get('timing', {})
    execution = metadata.get('execution', {})
    
    processing_time = timing.get('total', 0)
    result_count = execution.get('row_count', 0)
    
    # Add assistant response to history
    st.session_state.chat_history.append({
        'message': response_data['response'],
        'is_user': False,
        'sql_query': response_data.get('sql_query'),
        'processing_time': processing_time,
        'result_count': result_count,
        'timestamp': datetime.now()
    })
    
    # Reset processing state
    st.session_state.processing = False
    
    # Rerun to update the display
    st.rerun()

def display_sidebar():
    """Display enhanced sidebar"""
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🤖 Talk with DB</div>', unsafe_allow_html=True)
        
        # API Status
        api_healthy = check_api_health()
        status_color = "🟢" if api_healthy else "🔴"
        st.write(f"{status_color} API Status: {'Online' if api_healthy else 'Offline'}")
        
        # Session Info
        st.write("---")
        st.write("**Session Info:**")
        st.write(f"ID: `{st.session_state.session_id[:8]}...`")
        st.write(f"Messages: {len(st.session_state.chat_history)}")
        
        # Database Schema Info
        schema_info = get_database_schema()
        if schema_info:
            st.write("---")
            st.write("**Database Schema:**")
            st.write(f"Tables: {schema_info.get('total_tables', 0)}")
            
            if schema_info.get('tables'):
                table_names = [table['table_name'] for table in schema_info['tables'][:5]]
                st.write(f"Sample: {', '.join(table_names)}")
        
        # Statistics
        st.write("---")
        st.write("**Statistics:**")
        
        # Count different types of queries
        user_queries = [msg for msg in st.session_state.chat_history if msg['is_user']]
        st.write(f"Queries asked: {len(user_queries)}")
        
        if st.session_state.chat_history:
            # Calculate average response time
            response_times = [msg.get('processing_time', 0) for msg in st.session_state.chat_history 
                            if not msg['is_user'] and msg.get('processing_time')]
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                st.write(f"Avg response time: {avg_time:.2f}s")
        
        # Clear chat button
        st.write("---")
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

def display_main_interface():
    """Display the main chat interface"""
    # Header
    st.markdown('<h1 class="main-header">🤖 Talk with DB - Professional AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your intelligent database companion for natural language queries</p>', unsafe_allow_html=True)
    
    # Quick questions section
    display_quick_questions()
    
    # Chat history
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        for msg in st.session_state.chat_history:
            if msg['is_user']:
                display_chat_message(msg['message'], is_user=True)
            else:
                display_chat_message(
                    msg['message'], 
                    is_user=False,
                    sql_query=msg.get('sql_query'),
                    processing_time=msg.get('processing_time'),
                    result_count=msg.get('result_count')
                )
        
        # Show processing indicator if currently processing
        if st.session_state.processing:
            display_processing_message("Processing your request...")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input section
    st.write("---")
    
    # Chat input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "💬 Ask me anything about your database:",
            placeholder="e.g., 'Show me recent orders with customer details'",
            key="user_input",
            disabled=st.session_state.processing
        )
    
    with col2:
        send_button = st.button(
            "🚀 Send",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.processing or not user_input.strip()
        )
    
    # Handle user input
    if (send_button or user_input) and user_input.strip() and not st.session_state.processing:
        # Add user message to history
        st.session_state.chat_history.append({
            'message': user_input,
            'is_user': True,
            'timestamp': datetime.now()
        })
        
        # Set processing state
        st.session_state.processing = True
        
        # Process the question
        process_question(user_input)

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Display sidebar
    display_sidebar()
    
    # Display main interface
    display_main_interface()
    
    # Footer
    st.write("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🤖 <strong>Talk with DB Version 3</strong> - Professional AI Database Assistant</p>
        <p>Powered by Advanced RAG • Llama 3.2 • PostgreSQL</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
