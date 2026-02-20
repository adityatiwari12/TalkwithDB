# Talk with DB - Version 3.1 🚀 

## 🤖 **The Ultimate AI-Powered Natural Language to SQL Assistant**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Ollama](https://img.shields.io/badge/Ollama-LLMs-FF6B35.svg)](https://ollama.ai)

---

## 📸 **System in Action**

````carousel
![Top Landing - Most Asked Questions Interface](file:///c:/Users/tiwar/OneDrive/Desktop/talk_to_db/docs/assets/screenshots/image.png)
<!-- slide -->
![Deep Analysis - Detailed SQL and Metrics Response](file:///c:/Users/tiwar/OneDrive/Desktop/talk_to_db/docs/assets/screenshots/Screenshot%202026-02-20%20132225.png)
<!-- slide -->
![Execution Flow - Real-time Pipeline Logs](file:///c:/Users/tiwar/OneDrive/Desktop/talk_to_db/docs/assets/screenshots/user_query_and_output.png)
<!-- slide -->
![Performance Metrics - System Optimization Timing](file:///c:/Users/tiwar/OneDrive/Desktop/talk_to_db/docs/assets/screenshots/result_metrics.png)
````

---

## 🏗️ **Master Architecture & Connectivity**

The "Talk with DB" ecosystem is a multi-layered distributed system designed for scale.

### **System Connectivity Diagram**

```mermaid
graph TD
    User["👤 End User"] --> UI["🎨 Streamlit UI (chat_ui.py)"]
    UI <--> API["⚡ FastAPI Gateway (v3_api.py)"]
    
    subgraph "The Intelligence Engine"
        API <--> RAG["🧠 Advanced RAG Pipeline (advanced_rag.py)"]
        RAG <--> Hybrid["🔍 Hybrid Searcher (BM25 + Vector)"]
        RAG <--> Rerank["📈 LLM Re-ranker (Ollama)"]
    end
    
    subgraph "The Generative Layer"
        RAG --> SQLG["✍️ SQL Generator (sql_generator.py)"]
        SQLG <--> Ollama["🤖 Ollama (Llama 3.2)"]
    end
    
    subgraph "The Persistence & Safety Layer"
        SQLG --> Val["🛡️ SQL Validator (sql_validator.py)"]
        Val --> PGD["🐘 PostgreSQL Database"]
    end
```

---

## 🔬 **Core Logic: Deep-Dive into Components**

### **1. The RAG Pipeline (The "Brain")**
**File:** `src/chat_sql/rag/advanced_rag.py`

The system doesn't just "guess". It follows a rigorous 4-stage retrieval process:

```python
# Conceptualized Logic within AdvancedRAGPipeline.retrieve()
def retrieve(self, question, session_id):
    # 1. Expand question synonyms (Revenue -> Sales, Income)
    enhanced_query = self.query_rewriter.rewrite(question)
    
    # 2. Hybrid Search (Semantic + Keyword)
    # BM25 finds "Orders", Vector finds "Sales Transactions"
    initial_candidates = self.hybrid_searcher.search(enhanced_query)
    
    # 3. LLM Judgment (Contextual Validation)
    # LLM decides: "Orders table is more relevant than Shipments for this pricing question"
    final_tables = self.reranker.rerank(question, initial_candidates)
    
    return final_tables
```

### **2. The Security Gatekeeper (Safety Logic)**
**File:** `src/chat_sql/safety/sql_validator.py`

Every generated query is scrutinized by a multi-layer regex engine before execution.

```python
# Security Logic in SQLValidator
FORBIDDEN = ['DROP', 'DELETE', 'UPDATE', 'TRUNCATE', 'ALTER']

def validate_sql(self, sql):
    # Layer 1: Read-Only Enforcement
    if not sql.strip().upper().startswith('SELECT'):
        return "ERROR: Only read operations permitted"
        
    # Layer 2: Injection & Pattern Blocking
    for word in FORBIDDEN:
        if word in sql.upper():
            return f"SECURITY ALERT: Blocked {word}"
            
    # Layer 3: Denial-of-Service Prevention
    # Automatically injected LIMIT 200 on all queries
    return "VALID"
```

### **3. The SQL Fabricator**
**File:** `src/chat_sql/llm/sql_generator.py`

Uses sophisticated prompt engineering to guide Ollama (Llama 3.2) in generating precise, ANSI-compliant SQL.

> [!IMPORTANT]
> **Constraint Logic**: The generator is instructed never to hallucinate table names. It is strictly limited to the `schema_context` provided by the RAG pipeline.

### **4. The API Bridge**
**File:** `src/chat_sql/api/v3_api.py`

A high-performance FastAPI server that manages WebSockets and REST endpoints. It orchestrates the entire flow:
`Request` -> `RAG` -> `SQL Gen` -> `Validator` -> `DB` -> `Result Format` -> `Response`.

---

## ⚡ **Step-by-Step Data Flow**

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant UI as 🎨 Streamlit
    participant API as 🌐 FastAPI
    participant RAG as 🧠 RAG Engine
    participant DB as 🐘 PostgreSQL

    U->>UI: Types "How is revenue trending?"
    UI->>API: POST /api/chat
    API->>RAG: retrieve_context(question)
    Note over RAG: Analyzes Table Embeddings
    RAG-->>API: Returns `sales` and `products` schema
    API->>API: generates_sql(question, schema)
    API->>API: validate_sql(query)
    API->>DB: EXECUTING SELECT...
    DB-->>API: Returns raw rows
    API->>API: format_natural_language(rows)
    API-->>UI: Returning Answer + Metadata
    UI->>U: Displays "Revenue is up 12%..."
```

---

## � **Performance Benchmarks**

| Milestone | Time (Avg) | Logic |
|-----------|------------|-------|
| **Schema Retrieval** | ~2.1s | FAISS Parallel Vector Search |
| **SQL Generation** | ~25.9s | Ollama 3.2 Intelligent Processing |
| **SQL Validation** | ~0.4ms | Regex Pattern Recognition |
| **DB Execution** | ~0.2s | PostgreSQL Indexed Querying |
| **Response Formatting**| ~17s | Context-Aware Summarization |

---

## 🛠️ **Installation & Connectivity Map**

### **Port Usage**
*   **8001**: FastAPI Backend (System Core)
*   **8502**: Streamlit Web UI (Human Interface)
*   **11434**: Ollama LLM Engine (Internal Brain)
*   **5432**: PostgreSQL (Data Persistence)

### **One-Click Startup**
```bash
# Recommended Launch Pattern
python chat_v3.py
```

---

## � **Operational Metrics**
*   **Schema Discovery**: 100% Automatic (Foreign Keys, Data Types, Nullability).
*   **Session Management**: Persistent memory for multi-turn conversations.
*   **Most Asked Questions**: Pre-configured logic triggers for instant BI insights.

---

Made with ❤️ by [Aditya Tiwari](https://github.com/adityatiwari12)
Footer: *Version 3.1 - Production Ready Release*
