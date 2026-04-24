"""
Setup and populate PostgreSQL database with large mock data (1000+ rows, 10+ columns).
Creates extended schema and loads generated data.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / 'src' / 'chat_sql' / '.env')

# Database configuration from environment
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'chatdb'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', '1234')
}

# Extended schema with 10+ columns
SCHEMA_SQL = """
-- Drop existing tables (if any)
DROP TABLE IF EXISTS task_tags CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS task_history CASCADE;
DROP TABLE IF EXISTS comments CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- Create departments table (6 columns)
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    budget DECIMAL(12, 2) DEFAULT 0.00,
    location VARCHAR(50) DEFAULT 'HQ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table (9 columns)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'developer',
    department_id INTEGER REFERENCES departments(id),
    salary DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    hire_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table (10 columns)
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    priority VARCHAR(20) DEFAULT 'medium',
    department_id INTEGER REFERENCES departments(id),
    budget DECIMAL(12, 2) DEFAULT 0.00,
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tasks table (13 columns)
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    type VARCHAR(20) DEFAULT 'task',
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    assigned_to INTEGER REFERENCES users(id),
    project_id INTEGER REFERENCES projects(id),
    estimated_hours INTEGER DEFAULT 0,
    actual_hours INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    completed_at TIMESTAMP
);

-- Create comments table (6 columns)
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_edited BOOLEAN DEFAULT FALSE
);

-- Create task_history table (8 columns)
CREATE TABLE task_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    changed_by INTEGER REFERENCES users(id),
    field_name VARCHAR(50) NOT NULL,
    old_value VARCHAR(100),
    new_value VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

-- Create tags table (5 columns)
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(20) DEFAULT 'blue',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create task_tags junction table (3 columns)
CREATE TABLE task_tags (
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, tag_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_users_department ON users(department_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_projects_department ON projects(department_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_type ON tasks(type);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_comments_task ON comments(task_id);
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_history_task ON task_history(task_id);
CREATE INDEX idx_task_tags_task ON task_tags(task_id);
CREATE INDEX idx_task_tags_tag ON task_tags(tag_id);
"""


def get_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def setup_schema(conn):
    """Create database schema."""
    print("Setting up database schema...")
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()
    print("✓ Schema created successfully")


def load_sql_data(conn, sql_file_path):
    """Load data from SQL file."""
    print(f"\nLoading data from {sql_file_path}...")
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    with conn.cursor() as cur:
        cur.execute(sql_content)
    conn.commit()
    print("✓ Data loaded successfully")


def verify_data(conn):
    """Verify data was loaded correctly."""
    print("\n=== Verifying Data ===")
    
    tables = [
        'departments', 'users', 'projects', 'tasks', 
        'comments', 'task_history', 'tags', 'task_tags'
    ]
    
    total_rows = 0
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            total_rows += count
            print(f"  {table}: {count} rows")
    
    print(f"\n✓ TOTAL: {total_rows} rows across {len(tables)} tables")
    return total_rows


def test_connection():
    """Test database connection."""
    print("Testing database connection...")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Port: {DB_CONFIG['port']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"  User: {DB_CONFIG['user']}")
    
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"\n✓ Connected to PostgreSQL")
            print(f"  Version: {version}")
        conn.close()
        return True
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        return False


def get_table_columns(conn):
    """Get column counts for each table."""
    print("\n=== Table Column Counts ===")
    
    tables = ['departments', 'users', 'projects', 'tasks', 'comments', 'task_history', 'tags', 'task_tags']
    total_columns = 0
    
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            count = cur.fetchone()[0]
            total_columns += count
            print(f"  {table}: {count} columns")
    
    print(f"\n✓ TOTAL: {total_columns} columns across all tables")
    return total_columns


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup large database with mock data')
    parser.add_argument('--sql-file', type=str, 
                        default='./data/mock/large_mock_data.sql',
                        help='Path to SQL data file')
    parser.add_argument('--schema-only', action='store_true',
                        help='Only create schema, skip data loading')
    parser.add_argument('--test-only', action='store_true',
                        help='Only test connection, skip setup')
    
    args = parser.parse_args()
    
    # Test connection first
    if not test_connection():
        print("\nFailed to connect to database. Please check:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'chatdb' exists (create with: createdb chatdb)")
        print("  3. Credentials in .env are correct")
        sys.exit(1)
    
    if args.test_only:
        return
    
    conn = get_connection()
    
    try:
        # Setup schema
        setup_schema(conn)
        
        # Get column counts
        total_columns = get_table_columns(conn)
        
        if not args.schema_only:
            # Check if SQL file exists
            sql_path = Path(args.sql_file)
            if not sql_path.exists():
                print(f"\n✗ SQL file not found: {sql_path}")
                print("\nGenerate mock data first:")
                print("  python scripts/generate_large_mock_data.py")
                sys.exit(1)
            
            # Load data
            load_sql_data(conn, sql_path)
            
            # Verify
            total_rows = verify_data(conn)
            
            # Summary
            print("\n" + "="*50)
            print("DATABASE SETUP COMPLETE")
            print("="*50)
            print(f"Total Tables: 8")
            print(f"Total Columns: {total_columns}")
            print(f"Total Rows: {total_rows}")
            print("="*50)
        else:
            print("\n✓ Schema created (data loading skipped)")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
