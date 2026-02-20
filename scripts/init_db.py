"""
Database setup script for Chat with SQL system.
Creates sample database with users, projects, and tasks tables.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import os
import sys
import os

# Add src to path for absolute imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))

from chat_sql.config import config


class DatabaseSetup:
    """Handles database setup and sample data insertion."""
    
    def __init__(self):
        """Initialize database setup."""
        self.connection_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'database': 'postgres',  # Connect to default database first
            'user': config.DB_USER,
            'password': config.DB_PASSWORD
        }
    
    def create_database(self) -> None:
        """Create the chat_sql_db database if it doesn't exist."""
        try:
            # Connect to postgres database
            conn = psycopg2.connect(**self.connection_params)
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                # Check if database exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (config.DB_NAME,)
                )
                
                if not cursor.fetchone():
                    # Create database
                    cursor.execute(f"CREATE DATABASE {config.DB_NAME}")
                    print(f"Database '{config.DB_NAME}' created successfully")
                else:
                    print(f"Database '{config.DB_NAME}' already exists")
            
            conn.close()
            
        except psycopg2.Error as e:
            print(f"Error creating database: {e}")
            raise
    
    def create_tables(self) -> None:
        """Create sample tables: users, projects, tasks."""
        # Update connection to use the new database
        db_params = self.connection_params.copy()
        db_params['database'] = config.DB_NAME
        
        try:
            conn = psycopg2.connect(**db_params)
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                # Drop existing tables if they exist (for clean setup)
                cursor.execute("DROP TABLE IF EXISTS tasks CASCADE")
                cursor.execute("DROP TABLE IF EXISTS projects CASCADE")
                cursor.execute("DROP TABLE IF EXISTS users CASCADE")
                
                # Create users table
                cursor.execute("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create projects table
                cursor.execute("""
                    CREATE TABLE projects (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create tasks table
                cursor.execute("""
                    CREATE TABLE tasks (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        assigned_to INTEGER REFERENCES users(id),
                        project_id INTEGER REFERENCES projects(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        due_date DATE
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to)")
                cursor.execute("CREATE INDEX idx_tasks_project_id ON tasks(project_id)")
                cursor.execute("CREATE INDEX idx_tasks_status ON tasks(status)")
                
                print("Tables created successfully")
            
            conn.close()
            
        except psycopg2.Error as e:
            print(f"Error creating tables: {e}")
            raise
    
    def insert_sample_data(self) -> None:
        """Insert sample data into the tables."""
        db_params = self.connection_params.copy()
        db_params['database'] = config.DB_NAME
        
        try:
            conn = psycopg2.connect(**db_params)
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                # Insert sample users
                users_data = [
                    ('Aditya Kumar', 'aditya@example.com'),
                    ('Rohit Sharma', 'rohit@example.com'),
                    ('Priya Singh', 'priya@example.com'),
                    ('Anjali Patel', 'anjali@example.com'),
                    ('Vikram Reddy', 'vikram@example.com')
                ]
                
                for name, email in users_data:
                    cursor.execute(
                        "INSERT INTO users (name, email) VALUES (%s, %s)",
                        (name, email)
                    )
                
                # Insert sample projects
                projects_data = [
                    ('Website Redesign', 'Complete overhaul of company website'),
                    ('Mobile App Development', 'Create new mobile application'),
                    ('Database Migration', 'Migrate legacy database to new system'),
                    ('API Integration', 'Integrate third-party APIs'),
                    ('Security Audit', 'Comprehensive security assessment')
                ]
                
                for name, description in projects_data:
                    cursor.execute(
                        "INSERT INTO projects (name, description) VALUES (%s, %s)",
                        (name, description)
                    )
                
                # Insert sample tasks
                tasks_data = [
                    ('Design homepage mockup', 'in_progress', 1, 1, '2024-02-20'),
                    ('Implement user authentication', 'pending', 2, 1, '2024-02-25'),
                    ('Create database schema', 'completed', 1, 3, '2024-02-15'),
                    ('Setup development environment', 'completed', 3, 2, '2024-02-10'),
                    ('Write API documentation', 'in_progress', 4, 4, '2024-02-22'),
                    ('Test payment gateway', 'pending', 2, 4, '2024-02-28'),
                    ('Optimize database queries', 'completed', 1, 3, '2024-02-12'),
                    ('Design mobile UI', 'in_progress', 3, 2, '2024-02-24'),
                    ('Implement search functionality', 'pending', 5, 1, '2024-03-01'),
                    ('Setup CI/CD pipeline', 'completed', 4, 2, '2024-02-08'),
                    ('Conduct security testing', 'in_progress', 5, 5, '2024-02-26'),
                    ('Create user manual', 'pending', 3, 1, '2024-03-05'),
                    ('Fix responsive design issues', 'completed', 1, 1, '2024-02-14'),
                    ('Implement caching layer', 'pending', 2, 3, '2024-03-02'),
                    ('Setup monitoring tools', 'completed', 4, 5, '2024-02-11'),
                    ('Review code quality', 'in_progress', 5, 2, '2024-02-23'),
                    ('Deploy to staging', 'pending', 3, 2, '2024-02-27'),
                    ('Create backup strategy', 'completed', 1, 3, '2024-02-13'),
                    ('Implement rate limiting', 'pending', 2, 4, '2024-03-03'),
                    ('Conduct user testing', 'in_progress', 4, 1, '2024-02-25'),
                    ('Setup SSL certificates', 'completed', 5, 5, '2024-02-09'),
                    ('Optimize image loading', 'pending', 1, 1, '2024-03-04'),
                    ('Create deployment scripts', 'completed', 3, 2, '2024-02-16'),
                    ('Implement logging system', 'pending', 2, 3, '2024-03-06')
                ]
                
                for title, status, assigned_to, project_id, due_date in tasks_data:
                    cursor.execute(
                        """
                        INSERT INTO tasks (title, status, assigned_to, project_id, due_date) 
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (title, status, assigned_to, project_id, due_date)
                    )
                
                print("Sample data inserted successfully")
            
            conn.close()
            
        except psycopg2.Error as e:
            print(f"Error inserting sample data: {e}")
            raise
    
    def verify_setup(self) -> None:
        """Verify the database setup by checking table contents."""
        db_params = self.connection_params.copy()
        db_params['database'] = config.DB_NAME
        
        try:
            conn = psycopg2.connect(**db_params)
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check users
                cursor.execute("SELECT COUNT(*) as count FROM users")
                users_count = cursor.fetchone()['count']
                
                # Check projects
                cursor.execute("SELECT COUNT(*) as count FROM projects")
                projects_count = cursor.fetchone()['count']
                
                # Check tasks
                cursor.execute("SELECT COUNT(*) as count FROM tasks")
                tasks_count = cursor.fetchone()['count']
                
                print(f"\nDatabase Setup Verification:")
                print(f"Users: {users_count}")
                print(f"Projects: {projects_count}")
                print(f"Tasks: {tasks_count}")
                
                # Show sample data
                cursor.execute("SELECT name, email FROM users LIMIT 3")
                users = cursor.fetchall()
                print(f"\nSample Users:")
                for user in users:
                    print(f"  - {user['name']} ({user['email']})")
                
                cursor.execute("SELECT title, status FROM tasks LIMIT 5")
                tasks = cursor.fetchall()
                print(f"\nSample Tasks:")
                for task in tasks:
                    print(f"  - {task['title']} ({task['status']})")
            
            conn.close()
            
        except psycopg2.Error as e:
            print(f"Error verifying setup: {e}")
            raise
    
    def setup_complete(self) -> None:
        """Run the complete database setup."""
        print("Starting database setup...")
        
        try:
            self.create_database()
            self.create_tables()
            self.insert_sample_data()
            self.verify_setup()
            
            print("\n✅ Database setup completed successfully!")
            print(f"Database: {config.DB_NAME}")
            print(f"Host: {config.DB_HOST}:{config.DB_PORT}")
            
        except Exception as e:
            print(f"\n❌ Database setup failed: {e}")
            raise


def main():
    """Main function to run database setup."""
    setup = DatabaseSetup()
    setup.setup_complete()


if __name__ == "__main__":
    main()
