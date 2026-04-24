"""
View and verify database data with SQL queries.
Connects to PostgreSQL and displays table statistics, sample rows, and relationships.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tabulate import tabulate

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / 'src' / 'chat_sql' / '.env')

# Try to import psycopg2, handle gracefully if not available
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("Warning: psycopg2 not installed. Install with: pip install psycopg2-binary")


# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'chatdb'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', '1234')
}


def get_public_tables(conn):
    """Get existing public base tables."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        return [row[0] for row in cur.fetchall()]


def table_exists(conn, table_name):
    """Check if a table exists in public schema."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, (table_name,))
        return cur.fetchone()[0]


def get_table_columns(conn, table_name):
    """Get column names for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        return [row[0] for row in cur.fetchall()]


def get_connection():
    """Get database connection."""
    if not HAS_PSYCOPG2:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    return psycopg2.connect(**DB_CONFIG)


def show_connection_info():
    """Display database connection info."""
    print("\n" + "="*60)
    print("DATABASE CONNECTION INFO")
    print("="*60)
    print(f"Host:     {DB_CONFIG['host']}")
    print(f"Port:     {DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User:     {DB_CONFIG['user']}")
    print("="*60)


def check_connection():
    """Test database connection."""
    if not HAS_PSYCOPG2:
        print("\n✗ psycopg2 not installed")
        print("  Install: pip install psycopg2-binary")
        return False
    
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"\n✓ Connected to PostgreSQL")
            print(f"  Version: {version.split()[0]} {version.split()[1]}")
        conn.close()
        return True
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        return False


def show_table_counts(conn):
    """Show row counts for all tables."""
    print("\n" + "="*60)
    print("TABLE ROW COUNTS")
    print("="*60)
    
    tables = get_public_tables(conn)
    
    data = []
    total = 0
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            total += count
            data.append([table, count])
    
    data.append(["-"*20, "-"*10])
    data.append(["TOTAL", total])
    
    print(tabulate(data, headers=["Table", "Rows"], tablefmt="grid"))


def show_column_counts(conn):
    """Show column counts for all tables."""
    print("\n" + "="*60)
    print("TABLE COLUMN COUNTS")
    print("="*60)
    
    tables = get_public_tables(conn)
    
    data = []
    total = 0
    with conn.cursor() as cur:
        for table in tables:
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            count = cur.fetchone()[0]
            total += count
            data.append([table, count])
    
    data.append(["-"*20, "-"*10])
    data.append(["TOTAL", total])
    
    print(tabulate(data, headers=["Table", "Columns"], tablefmt="grid"))


def show_sample_data(conn, table, limit=5):
    """Show sample rows from a table."""
    print(f"\n" + "="*60)
    print(f"SAMPLE DATA: {table.upper()}")
    print("="*60)
    
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table} LIMIT {limit}")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    
    if rows:
        print(tabulate(rows, headers=columns, tablefmt="grid", maxcolwidths=30))
    else:
        print("(No data)")


def show_table_schema(conn, table):
    """Show table schema (columns and types)."""
    print(f"\n" + "="*60)
    print(f"SCHEMA: {table.upper()}")
    print("="*60)
    
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """)
        rows = cur.fetchall()
    
    headers = ["Column", "Type", "Nullable", "Default"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def show_task_stats(conn):
    """Show task statistics."""
    print("\n" + "="*60)
    print("TASK STATISTICS")
    print("="*60)
    
    if not table_exists(conn, "tasks"):
        print("tasks table not found in current schema.")
        return

    task_columns = set(get_table_columns(conn, "tasks"))

    with conn.cursor() as cur:
        # Status distribution
        if "status" in task_columns:
            cur.execute("""
                SELECT status, COUNT(*) as count,
                       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 1) as percentage
                FROM tasks
                GROUP BY status
                ORDER BY count DESC
            """)
            status_data = cur.fetchall()
            print("\nStatus Distribution:")
            print(tabulate(status_data, headers=["Status", "Count", "%"], tablefmt="grid"))
        else:
            print("\nStatus Distribution: column 'status' not found.")

        # Priority distribution (optional)
        if "priority" in task_columns:
            cur.execute("""
                SELECT priority, COUNT(*) as count
                FROM tasks
                GROUP BY priority
                ORDER BY count DESC
            """)
            priority_data = cur.fetchall()
            print("\nPriority Distribution:")
            print(tabulate(priority_data, headers=["Priority", "Count"], tablefmt="grid"))
        else:
            print("\nPriority Distribution: column 'priority' not found.")
        
        # Assignment stats
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(assigned_to) as assigned,
                COUNT(*) - COUNT(assigned_to) as unassigned
            FROM tasks
        """)
        assign_data = cur.fetchall()
        print("\nAssignment Stats:")
        print(tabulate(assign_data, headers=["Total", "Assigned", "Unassigned"], tablefmt="grid"))


def show_top_users(conn):
    """Show users with most tasks."""
    print("\n" + "="*60)
    print("TOP 10 USERS BY TASK COUNT")
    print("="*60)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                COUNT(t.id) as task_count
            FROM users u
            LEFT JOIN tasks t ON u.id = t.assigned_to
            GROUP BY u.id, u.name, u.email
            ORDER BY task_count DESC
            LIMIT 10
        """)
        rows = cur.fetchall()
    
    print(tabulate(rows, headers=["ID", "Name", "Email", "Tasks"], tablefmt="grid"))


def show_project_summary(conn):
    """Show project summary with task counts."""
    print("\n" + "="*60)
    print("PROJECT SUMMARY (Top 10 by tasks)")
    print("="*60)
    
    if not table_exists(conn, "projects"):
        print("projects table not found in current schema.")
        return

    project_columns = set(get_table_columns(conn, "projects"))
    has_status = "status" in project_columns
    has_priority = "priority" in project_columns

    select_cols = ["p.id", "p.name"]
    group_cols = ["p.id", "p.name"]
    headers = ["ID", "Name"]
    if has_status:
        select_cols.append("p.status")
        group_cols.append("p.status")
        headers.append("Status")
    if has_priority:
        select_cols.append("p.priority")
        group_cols.append("p.priority")
        headers.append("Priority")
    select_cols.append("COUNT(t.id) as task_count")
    headers.append("Tasks")

    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT
                {", ".join(select_cols)}
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            GROUP BY {", ".join(group_cols)}
            ORDER BY task_count DESC
            LIMIT 10
        """)
        rows = cur.fetchall()

    print(tabulate(rows, headers=headers, tablefmt="grid"))


def show_department_stats(conn):
    """Show department statistics."""
    print("\n" + "="*60)
    print("DEPARTMENT STATISTICS")
    print("="*60)
    
    if not table_exists(conn, "departments"):
        print("departments table not found in current schema. Skipping department stats.")
        return

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                d.id,
                d.name,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(DISTINCT p.id) as project_count,
                d.budget
            FROM departments d
            LEFT JOIN users u ON d.id = u.department_id
            LEFT JOIN projects p ON d.id = p.department_id
            GROUP BY d.id, d.name, d.budget
            ORDER BY user_count DESC
        """)
        rows = cur.fetchall()

    print(tabulate(rows, headers=["ID", "Name", "Users", "Projects", "Budget"], tablefmt="grid"))


def run_sample_queries(conn):
    """Run and display sample NL-to-SQL queries."""
    print("\n" + "="*60)
    print("SAMPLE QUERIES")
    print("="*60)
    
    queries = [
        {
            "question": "How many users are in the system?",
            "sql": "SELECT COUNT(*) FROM users"
        },
        {
            "question": "List pending tasks",
            "sql": "SELECT id, title, status FROM tasks WHERE status = 'pending' LIMIT 5"
        },
        {
            "question": "Users with most tasks",
            "sql": """
                SELECT u.name, COUNT(t.id) as task_count 
                FROM users u 
                JOIN tasks t ON u.id = t.assigned_to 
                GROUP BY u.id, u.name 
                ORDER BY task_count DESC 
                LIMIT 5
            """
        },
        {
            "question": "Overdue tasks",
            "sql": """
                SELECT t.id, t.title, t.due_date, u.name as assigned
                FROM tasks t
                LEFT JOIN users u ON t.assigned_to = u.id
                WHERE t.due_date < CURRENT_DATE
                AND t.status NOT IN ('completed', 'cancelled')
                LIMIT 5
            """
        }
    ]
    
    for i, q in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Q: {q['question']}")
        print(f"SQL: {q['sql']}")
        
        try:
            with conn.cursor() as cur:
                cur.execute(q['sql'])
                rows = cur.fetchall()
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    print("Result:")
                    print(tabulate(rows, headers=columns, tablefmt="grid"))
        except Exception as e:
            print(f"Error: {e}")


def export_to_csv(conn, table, output_dir='./data/export'):
    """Export table to CSV."""
    import csv
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_file = Path(output_dir) / f"{table}.csv"
    
    if not table_exists(conn, table):
        print(f"✗ Table '{table}' not found.")
        return

    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    
    print(f"✓ Exported {len(rows)} rows to {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='View database data')
    parser.add_argument('--table', type=str, help='Show specific table data')
    parser.add_argument('--schema', type=str, help='Show table schema')
    parser.add_argument('--limit', type=int, default=5, help='Limit rows displayed')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--all', action='store_true', help='Show everything')
    parser.add_argument('--export', type=str, help='Export table to CSV')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    
    args = parser.parse_args()
    
    # Show connection info
    show_connection_info()
    
    # Test connection
    if not check_connection():
        print("\nConnection failed. Please:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check credentials in .env file")
        print("  3. Create database: createdb chatdb")
        sys.exit(1)
    
    if args.test:
        return
    
    # Connect and show data
    conn = get_connection()
    
    try:
        if args.all:
            # Show everything
            show_table_counts(conn)
            show_column_counts(conn)
            show_task_stats(conn)
            show_top_users(conn)
            show_project_summary(conn)
            show_department_stats(conn)
            run_sample_queries(conn)
            
            # Show sample data for main tables
            for table in ['users', 'projects', 'tasks']:
                show_sample_data(conn, table, 3)
                
        elif args.table:
            show_sample_data(conn, args.table, args.limit)
            
        elif args.schema:
            show_table_schema(conn, args.schema)
            
        elif args.stats:
            show_table_counts(conn)
            show_column_counts(conn)
            show_task_stats(conn)
            
        elif args.export:
            export_to_csv(conn, args.export)
            
        else:
            # Default: show overview
            show_table_counts(conn)
            show_column_counts(conn)
            print("\nTip: Use --all to see everything, --table <name> for specific table")
            print("     Use --stats for detailed statistics")
            
    finally:
        conn.close()
        print("\n" + "="*60)
        print("Done!")
        print("="*60)


if __name__ == '__main__':
    main()
