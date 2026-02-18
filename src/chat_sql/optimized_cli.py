"""
Optimized Terminal Interface for Chat with SQL system.
Provides efficient CLI with performance monitoring and schema management.
"""

import argparse
import sys
import time
import json
from typing import Dict, Any

from core.optimized_pipeline import optimized_chat_pipeline
from core.schema_manager import schema_manager


class OptimizedChatCLI:
    """
    Optimized command-line interface for Chat with SQL.
    
    Features:
    - Performance monitoring
    - Schema management commands
    - Query optimization info
    - Batch processing
    """
    
    def __init__(self):
        """Initialize CLI."""
        self.pipeline = optimized_chat_pipeline
        self.schema_manager = schema_manager
    
    def run_interactive(self) -> None:
        """Run interactive chat session."""
        print("🚀 Chat with SQL - Optimized for Large Schemas")
        print("=" * 50)
        print("Type 'help' for commands, 'quit' to exit")
        print("=" * 50)
        
        while True:
            try:
                question = input("\n💬 Your question: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if question.lower() == 'help':
                    self._show_help()
                    continue
                
                if question.lower().startswith('/'):
                    self._handle_command(question)
                    continue
                
                # Process the question
                self._process_question(question)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _process_question(self, question: str, show_performance: bool = True) -> None:
        """
        Process a single question with performance metrics.
        
        Args:
            question: User's question
            show_performance: Whether to show performance metrics
        """
        print(f"\n🔍 Processing: {question}")
        print("⏳ Thinking...")
        
        # Process the question
        result = self.pipeline.chat_with_sql(question)
        
        # Display results
        self._display_result(result, show_performance)
    
    def _display_result(self, result: Dict[str, Any], show_performance: bool = True) -> None:
        """
        Display query result in formatted way.
        
        Args:
            result: Query result dictionary
            show_performance: Whether to show performance metrics
        """
        print("\n" + "=" * 50)
        print("📊 RESULT")
        print("=" * 50)
        
        # Answer
        print(f"\n💡 Answer:\n{result['answer']}")
        
        # SQL
        if result.get('sql'):
            print(f"\n🔧 SQL Query:\n{result['sql']}")
        
        # Explanation
        if result.get('explanation'):
            print(f"\n📝 Explanation:\n{result['explanation']}")
        
        # Results
        if result.get('results'):
            print(f"\n📋 Results ({len(result['results'])} rows):")
            for i, row in enumerate(result['results'][:5], 1):  # Show max 5 rows
                print(f"  {i}. {row}")
            if len(result['results']) > 5:
                print(f"  ... and {len(result['results']) - 5} more rows")
        
        # Warnings
        if result.get('warnings'):
            print(f"\n⚠️  Warnings:")
            for warning in result['warnings']:
                print(f"    - {warning}")
        
        # Error
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
        
        # Performance metrics
        if show_performance and result.get('performance'):
            perf = result['performance']
            print(f"\n⚡ Performance:")
            print(f"    Schema retrieval: {perf.get('schema_time_ms', 0):.1f}ms")
            print(f"    SQL generation:   {perf.get('sql_time_ms', 0):.1f}ms")
            print(f"    SQL validation:   {perf.get('validation_time_ms', 0):.1f}ms")
            print(f"    Query execution:  {perf.get('execution_time_ms', 0):.1f}ms")
            print(f"    Result formatting: {perf.get('formatting_time_ms', 0):.1f}ms")
            print(f"    🏁 Total time:     {perf.get('total_time_ms', 0):.1f}ms")
        
        print("=" * 50)
    
    def _show_help(self) -> None:
        """Display help information."""
        help_text = """
📚 Available Commands:

/help                    - Show this help message
/stats                    - Show schema and performance statistics
/refresh                   - Force refresh schema
/test <query>              - Test retrieval performance for a query
/optimize                  - Show optimization information
/batch <file>              - Process multiple questions from file
/export                    - Export schema statistics

💡 Examples:
    "How many users are there?"
    "Show tasks assigned to John"
    "What are the open projects?"
    "Count tasks by status"
        """
        print(help_text)
    
    def _handle_command(self, command: str) -> None:
        """
        Handle CLI commands.
        
        Args:
            command: Command string starting with '/'
        """
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == '/stats':
            self._show_stats()
        elif cmd == '/refresh':
            self._refresh_schema()
        elif cmd == '/test' and len(parts) > 1:
            query = ' '.join(parts[1:])
            self._test_retrieval(query)
        elif cmd == '/optimize':
            self._show_optimization_info()
        elif cmd == '/batch' and len(parts) > 1:
            filename = parts[1]
            self._process_batch(filename)
        elif cmd == '/export':
            self._export_stats()
        else:
            print(f"❌ Unknown command: {command}")
            print("Type 'help' for available commands")
    
    def _show_stats(self) -> None:
        """Display system statistics."""
        print("\n📈 System Statistics")
        print("=" * 30)
        
        # Schema stats
        stats = self.pipeline.get_schema_stats()
        
        print(f"🗄️  Schema Tables: {stats.get('total_tables', 0)}")
        print(f"🔍 Vector Store Size: {stats.get('total_tables', 0)} tables")
        print(f"📏 Embedding Dimension: {stats.get('embedding_dimension', 'N/A')}")
        
        if stats.get('last_refresh'):
            print(f"🕐 Last Schema Refresh: {stats['last_refresh']}")
        
        # Performance stats
        print(f"\n⚡ Performance:")
        print(f"    Queries Processed: {stats.get('pipeline_queries', 0)}")
        if stats.get('pipeline_avg_response_time_ms', 0) > 0:
            print(f"    Avg Response Time: {stats['pipeline_avg_response_time_ms']:.1f}ms")
        if stats.get('pipeline_total_response_time_ms', 0) > 0:
            total_sec = stats['pipeline_total_response_time_ms'] / 1000
            print(f"    Total Processing Time: {total_sec:.1f}s")
        
        print("=" * 30)
    
    def _refresh_schema(self) -> None:
        """Refresh schema and show progress."""
        print("\n🔄 Refreshing schema...")
        start_time = time.time()
        
        self.pipeline.refresh_schema()
        
        elapsed = time.time() - start_time
        print(f"✅ Schema refreshed in {elapsed:.1f}s")
    
    def _test_retrieval(self, query: str) -> None:
        """Test retrieval performance."""
        print(f"\n🧪 Testing retrieval for: {query}")
        
        result = self.pipeline.test_retrieval_performance(query)
        
        print(f"\n📊 Retrieval Test Results:")
        print(f"    Query: {result['query']}")
        print(f"    Candidate Tables: {result['candidate_count']}")
        print(f"    Retrieved Tables: {result['retrieved_count']}")
        print(f"    Pre-filter Time: {result['pre_filter_time_ms']:.1f}ms")
        print(f"    Search Time: {result['search_time_ms']:.1f}ms")
        print(f"    Total Time: {result['total_time_ms']:.1f}ms")
        
        if result['candidate_tables']:
            print(f"    Candidates: {', '.join(result['candidate_tables'])}")
        if result['retrieved_tables']:
            print(f"    Retrieved: {', '.join(result['retrieved_tables'])}")
    
    def _show_optimization_info(self) -> None:
        """Show optimization features."""
        print("\n🚀 Optimization Features")
        print("=" * 30)
        
        info = self.pipeline.get_optimization_info()
        
        print("✅ Enabled Features:")
        for feature, enabled in info['features'].items():
            status = "✅" if enabled else "❌"
            print(f"    {status} {feature.replace('_', ' ').title()}")
        
        print(f"\n⚙️  Configuration:")
        for key, value in info['configuration'].items():
            print(f"    {key}: {value}")
        
        print(f"\n📈 Performance:")
        for key, value in info['performance'].items():
            print(f"    {key}: {value}")
        
        print("=" * 30)
    
    def _process_batch(self, filename: str) -> None:
        """Process multiple questions from file."""
        try:
            with open(filename, 'r') as f:
                questions = [line.strip() for line in f if line.strip()]
            
            print(f"\n📁 Processing {len(questions)} questions from {filename}")
            
            results = []
            for i, question in enumerate(questions, 1):
                print(f"\n[{i}/{len(questions)}] {question}")
                
                start_time = time.time()
                result = self.pipeline.chat_with_sql(question)
                elapsed = time.time() - start_time
                
                results.append({
                    'question': question,
                    'result': result,
                    'processing_time_ms': elapsed * 1000
                })
                
                print(f"✅ Completed in {elapsed:.2f}s")
            
            # Save results
            output_file = filename.replace('.txt', '_results.json')
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to {output_file}")
            
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except Exception as e:
            print(f"❌ Error processing file: {e}")
    
    def _export_stats(self) -> None:
        """Export detailed statistics to file."""
        try:
            stats = self.pipeline.get_schema_stats()
            optimization_info = self.pipeline.get_optimization_info()
            
            export_data = {
                'timestamp': time.time(),
                'schema_statistics': stats,
                'optimization_info': optimization_info
            }
            
            filename = f"chat_sql_stats_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"\n💾 Statistics exported to {filename}")
            
        except Exception as e:
            print(f"❌ Error exporting stats: {e}")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Optimized Chat with SQL - Terminal Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start interactive mode
  %(prog)s "How many users?"      # Single query
  %(prog)s --batch questions.txt    # Batch processing
  %(prog)s --test "users tasks"    # Test retrieval
        """
    )
    
    parser.add_argument(
        'query', 
        nargs='?', 
        help='Natural language question to process'
    )
    
    parser.add_argument(
        '--batch', '-b',
        help='Process multiple questions from file'
    )
    
    parser.add_argument(
        '--test', '-t',
        help='Test retrieval performance for query'
    )
    
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Show system statistics'
    )
    
    parser.add_argument(
        '--refresh', '-r',
        action='store_true',
        help='Refresh schema before processing'
    )
    
    parser.add_argument(
        '--no-performance', '-np',
        action='store_true',
        help='Hide performance metrics'
    )
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = OptimizedChatCLI()
    
    # Handle refresh flag
    if args.refresh:
        cli._refresh_schema()
    
    # Handle different modes
    if args.stats:
        cli._show_stats()
    elif args.batch:
        cli._process_batch(args.batch)
    elif args.test:
        cli._test_retrieval(args.test)
    elif args.query:
        cli._process_question(args.query, show_performance=not args.no_performance)
    else:
        # Interactive mode
        cli.run_interactive()


if __name__ == "__main__":
    main()
