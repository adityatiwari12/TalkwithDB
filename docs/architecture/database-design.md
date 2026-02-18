# Database Design Documentation

## Overview

This document describes the database design for the Chat with SQL system, including both the application's internal database structure and the target databases that users can query against.

## System Database Schema

The Chat with SQL system maintains its own database for configuration, caching, and audit purposes.

### 1. Configuration Tables

#### app_config
Stores application configuration and settings.

```sql
CREATE TABLE app_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample data
INSERT INTO app_config (key, value, description) VALUES
('max_result_rows', '200', 'Maximum number of rows returned per query'),
('sql_timeout_seconds', '30', 'SQL query timeout in seconds'),
('top_k_retrieval', '5', 'Number of schema documents to retrieve');
```

#### database_connections
Stores configured database connections for users to query.

```sql
CREATE TABLE database_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER DEFAULT 5432,
    database_name VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL,
    connection_type VARCHAR(50) DEFAULT 'postgresql',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Schema Cache Tables

#### schema_cache
Caches database schema information for faster retrieval.

```sql
CREATE TABLE schema_cache (
    id SERIAL PRIMARY KEY,
    database_connection_id INTEGER REFERENCES database_connections(id),
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100),
    column_type VARCHAR(100),
    is_nullable BOOLEAN DEFAULT true,
    column_default TEXT,
    is_primary_key BOOLEAN DEFAULT false,
    is_foreign_key BOOLEAN DEFAULT false,
    foreign_key_table VARCHAR(100),
    foreign_key_column VARCHAR(100),
    table_description TEXT,
    column_description TEXT,
    sample_values TEXT, -- JSON array of sample values
    embedding_vector FLOAT[], -- For vector similarity search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(database_connection_id, table_name, column_name)
);
```

#### schema_embeddings
Stores pre-computed embeddings for schema elements.

```sql
CREATE TABLE schema_embeddings (
    id SERIAL PRIMARY KEY,
    schema_cache_id INTEGER REFERENCES schema_cache(id),
    embedding_model VARCHAR(100) NOT NULL,
    embedding_vector FLOAT[] NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Query History Tables

#### query_history
Stores history of all queries processed by the system.

```sql
CREATE TABLE query_history (
    id SERIAL PRIMARY KEY,
    user_question TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    sql_is_valid BOOLEAN NOT NULL,
    execution_time_ms INTEGER,
    result_count INTEGER,
    error_message TEXT,
    llm_model VARCHAR(100),
    embedding_model VARCHAR(100),
    database_connection_id INTEGER REFERENCES database_connections(id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### query_results
Stores actual query results for audit and debugging.

```sql
CREATE TABLE query_results (
    id SERIAL PRIMARY KEY,
    query_history_id INTEGER REFERENCES query_history(id),
    result_data JSONB NOT NULL, -- Query results as JSON
    result_format VARCHAR(50) DEFAULT 'json',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. User Management Tables (Optional)

#### users
User management for multi-tenant deployments.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### user_sessions
Session management for authenticated users.

```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Sample User Database

For demonstration purposes, the system includes a sample project management database that users can query.

### Project Management Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(50),
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    assigned_to INTEGER REFERENCES users(id),
    project_id INTEGER REFERENCES projects(id),
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    start_date DATE,
    due_date DATE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Time tracking table
CREATE TABLE time_entries (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id),
    user_id INTEGER REFERENCES users(id),
    hours DECIMAL(5,2) NOT NULL,
    description TEXT,
    entry_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project teams table
CREATE TABLE project_teams (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(project_id, user_id)
);
```

### Sample Data

```sql
-- Insert sample users
INSERT INTO users (name, email, department, role) VALUES
('Aditya Kumar', 'aditya@example.com', 'Engineering', 'Developer'),
('Priya Sharma', 'priya@example.com', 'Engineering', 'Senior Developer'),
('Rohit Verma', 'rohit@example.com', 'Product', 'Product Manager'),
('Neha Patel', 'neha@example.com', 'Design', 'UX Designer'),
('Vikram Singh', 'vikram@example.com', 'Engineering', 'DevOps Engineer');

-- Insert sample projects
INSERT INTO projects (name, description, status, start_date, end_date, budget) VALUES
('Website Redesign', 'Complete redesign of company website', 'active', '2024-01-01', '2024-06-30', 50000.00),
('Mobile App Development', 'Native mobile app for iOS and Android', 'active', '2024-02-01', '2024-12-31', 150000.00),
('API Integration', 'Integration with third-party APIs', 'completed', '2023-11-01', '2024-01-31', 25000.00),
('Database Migration', 'Migrate legacy database to new system', 'planning', '2024-03-01', '2024-08-31', 75000.00),
('Security Audit', 'Comprehensive security assessment', 'active', '2024-01-15', '2024-03-15', 30000.00);

-- Insert sample tasks
INSERT INTO tasks (title, description, status, priority, assigned_to, project_id, estimated_hours, due_date) VALUES
('Design Homepage', 'Create mockups for new homepage design', 'completed', 'high', 4, 1, 40.0, '2024-01-15'),
('Implement User Auth', 'Add user authentication system', 'in_progress', 'high', 1, 2, 60.0, '2024-03-01'),
('Database Schema', 'Design database schema for mobile app', 'completed', 'medium', 2, 2, 30.0, '2024-02-15'),
('API Documentation', 'Document all API endpoints', 'pending', 'low', 3, 3, 20.0, '2024-02-01'),
('Security Testing', 'Perform security penetration testing', 'pending', 'high', 5, 5, 50.0, '2024-03-10'),
('UI Components', 'Create reusable UI components', 'in_progress', 'medium', 1, 1, 35.0, '2024-02-20'),
('Performance Optimization', 'Optimize database queries', 'completed', 'medium', 2, 4, 25.0, '2024-02-10'),
('Deploy to Production', 'Deploy application to production server', 'pending', 'high', 5, 1, 15.0, '2024-03-05');

-- Insert time entries
INSERT INTO time_entries (task_id, user_id, hours, description, entry_date) VALUES
(1, 4, 8.0, 'Homepage mockup design', '2024-01-10'),
(1, 4, 6.5, 'Homepage revisions', '2024-01-12'),
(2, 1, 7.0, 'Authentication backend', '2024-02-01'),
(2, 1, 5.5, 'JWT token implementation', '2024-02-03'),
(3, 2, 4.0, 'Database design review', '2024-02-05'),
(6, 1, 6.0, 'Button component development', '2024-02-08'),
(7, 2, 5.0, 'Query optimization', '2024-02-06'),
(7, 2, 4.5, 'Index optimization', '2024-02-07');
```

## Schema Extraction Process

### 1. Automated Schema Discovery

The system automatically discovers database schema using the following process:

```sql
-- Get all tables
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Get table columns
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = ? AND table_schema = 'public';

-- Get primary keys
SELECT kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'PRIMARY KEY' 
    AND tc.table_name = ?;

-- Get foreign keys
SELECT
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = ?;
```

### 2. Sample Data Analysis

The system analyzes sample data to improve understanding:

```sql
-- Get sample values for categorical columns
SELECT DISTINCT column_name, 
       array_agg(DISTINCT column_name LIMIT 10) as sample_values
FROM table_name
GROUP BY column_name;

-- Get data distribution for numeric columns
SELECT 
    column_name,
    MIN(column_name) as min_value,
    MAX(column_name) as max_value,
    AVG(column_name) as avg_value,
    COUNT(*) as total_count
FROM table_name
GROUP BY column_name;
```

## Indexing Strategy

### 1. Performance Indexes

```sql
-- Query history indexes
CREATE INDEX idx_query_history_created_at ON query_history(created_at);
CREATE INDEX idx_query_history_user_question ON query_history USING gin(to_tsvector('english', user_question));
CREATE INDEX idx_query_history_sql ON query_history USING gin(to_tsvector('english', generated_sql));

-- Schema cache indexes
CREATE INDEX idx_schema_cache_table ON schema_cache(table_name);
CREATE INDEX idx_schema_cache_connection ON schema_cache(database_connection_id);

-- Vector similarity index (if using pgvector)
CREATE INDEX idx_schema_embeddings_vector ON schema_embeddings USING ivfflat (embedding_vector vector_cosine_ops);
```

### 2. Full-Text Search Indexes

```sql
-- For natural language search
CREATE INDEX idx_schema_fulltext ON schema_cache USING gin(
    to_tsvector('english', table_name || ' ' || COALESCE(column_name, '') || ' ' || COALESCE(table_description, '') || ' ' || COALESCE(column_description, ''))
);
```

## Data Migration Strategy

### 1. Version Control

```sql
-- Migration tracking
CREATE TABLE schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Migration Scripts

Each migration script includes:
- Version number
- Up migration
- Down migration
- Validation checks

## Security Considerations

### 1. Data Encryption

- **Password Encryption**: Using bcrypt for user passwords
- **Connection Credentials**: Encrypted at rest using application key
- **Sensitive Data**: Audit logs with PII redaction

### 2. Access Control

```sql
-- Row Level Security for multi-tenancy
ALTER TABLE query_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_own_queries ON query_history
    FOR ALL TO authenticated_users
    USING (user_id = current_user_id());
```

### 3. Audit Trail

```sql
-- Audit logging
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Performance Optimization

### 1. Connection Pooling

```python
# Database connection pool configuration
POOL_CONFIG = {
    'min_connections': 5,
    'max_connections': 20,
    'connection_timeout': 30,
    'idle_timeout': 300
}
```

### 2. Query Optimization

- **Prepared Statements**: For repeated query patterns
- **Result Caching**: For frequently accessed data
- **Partitioning**: For large historical tables

### 3. Monitoring

```sql
-- Performance monitoring view
CREATE VIEW query_performance AS
SELECT 
    date_trunc('hour', created_at) as hour,
    COUNT(*) as query_count,
    AVG(execution_time_ms) as avg_execution_time,
    AVG(result_count) as avg_result_count
FROM query_history
WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
GROUP BY date_trunc('hour', created_at)
ORDER BY hour DESC;
```

## Backup and Recovery

### 1. Backup Strategy

- **Daily Full Backups**: Complete database backup
- **Hourly Incremental**: Transaction log backups
- **Point-in-Time Recovery**: Using WAL files

### 2. Disaster Recovery

- **Geographic Replication**: Multi-region deployment
- **Failover Automation**: Automatic promotion of replicas
- **Data Validation**: Consistency checks after recovery

## Conclusion

This database design provides a robust foundation for the Chat with SQL system, supporting:

- **Multi-database Support**: Flexible connection management
- **Performance Optimization**: Efficient caching and indexing
- **Security**: Comprehensive access control and encryption
- **Auditability**: Complete query history and logging
- **Scalability**: Designed for growth and expansion

The schema is designed to be extensible, allowing for future enhancements while maintaining backward compatibility.
