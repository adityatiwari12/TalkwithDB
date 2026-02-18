#!/usr/bin/env python3
"""
Interactive Chat with SQL Command Line Interface.
Natural language to SQL conversion with RAG and local LLM processing.
"""

import sys
import traceback
from pipeline.chat_with_sql import chat_pipeline


class ChatSQLCLI:
    """Interactive command-line interface for Chat with SQL."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.pipeline = chat_pipeline
        self.running = True
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        print("🤖 Chat with SQL - Natural Language to SQL Converter")
        print("=" * 60)
        print("💡 Type your natural language questions about the database")
        print("🔒 Only SELECT queries are allowed for safety")
        print("⚡ Type 'quit' or 'exit' to stop")
        print("📊 Type 'stats' to see database statistics")
        print("🔍 Type 'help' for sample queries")
        print("=" * 60)
    
    def display_help(self):
        """Display help information and sample queries."""
        print("\n🔍 Sample Queries You Can Try:")
        print("-" * 40)
        print("1. Show all users")
        print("2. How many tasks does each user have?")
        print("3. Which users have more than 8 tasks?")
        print("4. What are the tasks assigned to Amit Nair?")
        print("5. Which projects have the most pending tasks?")
        print("6. Show completed tasks in the last 30 days")
        print("7. Which users have the most completed tasks?")
        print("8. What is the task status breakdown?")
        print("9. Show overdue tasks")
        print("10. Which projects have the most tasks assigned?")
        print("11. Show users with pending tasks")
        print("12. What are the top 5 projects by task count?")
        print("13. Show tasks assigned to each project")
        print("14. Which users have no tasks assigned?")
        print("15. Show tasks created in the last week")
        print("-" * 40)
        print("💡 You can ask questions in natural language!")
        print()
    
    def display_stats(self):
        """Display database statistics."""
        try:
            from db.connection import db_connection
            from db.schema_loader import schema_loader
            
            print("\n📊 Database Statistics")
            print("-" * 30)
            
            # Get user count
            with db_connection.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    users_count = cursor.fetchone()[0]
                    print(f"👥 Users: {users_count}")
                    
                    cursor.execute("SELECT COUNT(*) FROM projects")
                    projects_count = cursor.fetchone()[0]
                    print(f"📁 Projects: {projects_count}")
                    
                    cursor.execute("SELECT COUNT(*) FROM tasks")
                    tasks_count = cursor.fetchone()[0]
                    print(f"📋 Tasks: {tasks_count}")
                    
                    # Task status breakdown
                    cursor.execute("""
                        SELECT status, COUNT(*) as count 
                        FROM tasks 
                        GROUP BY status 
                        ORDER BY count DESC
                    """)
                    status_breakdown = cursor.fetchall()
                    print("\n📈 Task Status Breakdown:")
                    for status, count in status_breakdown:
                        emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "on_hold": "⏸️", "cancelled": "❌"}
                        print(f"   {emoji.get(status, '📝')} {status}: {count}")
            
            # Schema info
            schema_stats = self.pipeline.get_schema_stats()
            print(f"\n🔍 Schema Documents: {schema_stats['total_documents']}")
            print(f"🧠 Embedding Model: {schema_stats['model_name']}")
            
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
    
    def process_question(self, question):
        """Process a natural language question."""
        if not question.strip():
            print("❌ Please enter a question.")
            return
        
        print(f"\n🤔 Processing: '{question}'")
        print("🔍 Retrieving schema...")
        
        try:
            # Process the question through the pipeline
            result = self.pipeline.chat_with_sql(question)
            
            # Display results
            print("✅ SQL Generated:")
            print(f"   {result['sql']}")
            
            if result['warnings']:
                print("⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"   - {warning}")
            
            print(f"📊 Results: {len(result['results'])} rows found")
            
            if result['results']:
                print("📋 Sample Results:")
                for i, row in enumerate(result['results'][:5], 1):
                    print(f"   {i}. {row}")
                if len(result['results']) > 5:
                    print(f"   ... and {len(result['results']) - 5} more rows")
            
            print(f"💬 Answer:")
            print(f"   {result['answer']}")
            
        except Exception as e:
            print(f"❌ Error processing question: {str(e)}")
            print("🔍 Please try rephrasing your question.")
            print("💡 Use 'help' to see sample queries.")
    
    def run(self):
        """Run the interactive CLI."""
        self.display_welcome()
        
        while self.running:
            try:
                # Get user input
                question = input("\n💬 Ask your database question: ").strip()
                
                # Handle special commands
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    self.running = False
                elif question.lower() in ['help', 'h']:
                    self.display_help()
                elif question.lower() in ['stats', 'statistics', 's']:
                    self.display_stats()
                elif question.lower() in ['clear', 'cls']:
                    # Clear screen (works on most terminals)
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.display_welcome()
                elif question.lower() == '':
                    continue
                else:
                    # Process the question
                    self.process_question(question)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.running = False
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                print("🔍 Please try again or type 'quit' to exit.")


def main():
    """Main entry point for the CLI."""
    try:
        cli = ChatSQLCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
