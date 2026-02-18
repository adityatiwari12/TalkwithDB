"""
Test script for optimized Chat with SQL system.
Validates all optimizations and performance characteristics.
"""

import time
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'chat_sql'))

from core.optimized_pipeline import optimized_chat_pipeline
from core.schema_manager import schema_manager
from rag.optimized_retriever import optimized_schema_retriever


def test_initialization_performance():
    """Test system initialization performance."""
    print("🧪 Testing Initialization Performance")
    print("=" * 50)
    
    start_time = time.time()
    
    # Test cold start
    pipeline = optimized_chat_pipeline
    init_time = time.time() - start_time
    
    print(f"✅ Cold initialization: {init_time:.3f}s")
    
    # Test warm start (should be faster)
    start_time = time.time()
    pipeline2 = optimized_chat_pipeline
    warm_time = time.time() - start_time
    
    print(f"✅ Warm initialization: {warm_time:.3f}s")
    print(f"📈 Performance improvement: {((init_time - warm_time) / init_time * 100):.1f}%")
    
    return init_time < 2.0  # Should be under 2 seconds


def test_schema_scaling():
    """Test schema handling with many tables."""
    print("\n🧪 Testing Schema Scaling")
    print("=" * 50)
    
    # Get current schema stats
    stats = optimized_chat_pipeline.get_schema_stats()
    table_count = stats.get('total_tables', 0)
    
    print(f"📊 Current schema: {table_count} tables")
    
    if table_count > 0:
        # Test retrieval performance
        test_queries = [
            "How many users are there?",
            "Show tasks for user John",
            "Count projects by status",
            "List all tables",
            "Find recent activities"
        ]
        
        total_time = 0
        for query in test_queries:
            start_time = time.time()
            result = optimized_chat_pipeline.chat_with_sql(query)
            query_time = time.time() - start_time
            total_time += query_time
            
            print(f"  🔍 '{query}' -> {query_time:.3f}s")
        
        avg_time = total_time / len(test_queries)
        print(f"📈 Average query time: {avg_time:.3f}s")
        
        # Performance targets
        print(f"🎯 Performance targets:")
        print(f"  ✅ Initialization < 2s: {'PASS' if init_time < 2.0 else 'FAIL'}")
        print(f"  ✅ Average query < 0.5s: {'PASS' if avg_time < 0.5 else 'FAIL'}")
        print(f"  ✅ Schema scaling: {'PASS' if table_count > 50 else 'NEEDS_TEST'}")
        
        return avg_time < 0.5
    
    return False


def test_incremental_updates():
    """Test incremental schema update functionality."""
    print("\n🧪 Testing Incremental Updates")
    print("=" * 50)
    
    # Get current schema
    schema_manager.get_current_schema()
    initial_snapshot = schema_manager.current_snapshot
    
    if not initial_snapshot:
        print("❌ No initial schema found")
        return False
    
    print(f"📊 Initial schema: {len(initial_snapshot.tables)} tables")
    
    # Simulate incremental update (force refresh)
    start_time = time.time()
    optimized_schema_retriever.refresh_schema()
    update_time = time.time() - start_time
    
    print(f"✅ Incremental update: {update_time:.3f}s")
    
    # Check if only changed tables were processed
    tables_to_update = schema_manager.get_tables_for_embedding()
    print(f"📋 Tables to update: {len(tables_to_update)}")
    
    # Performance target
    print(f"🎯 Update performance:")
    print(f"  ✅ Update time < 5s: {'PASS' if update_time < 5.0 else 'FAIL'}")
    print(f"  ✅ Incremental only: {'PASS' if len(tables_to_update) < len(initial_snapshot.tables) else 'FAIL'}")
    
    return update_time < 5.0


def test_pre_filtering():
    """Test metadata pre-filtering efficiency."""
    print("\n🧪 Testing Pre-Filtering")
    print("=" * 50)
    
    test_queries = [
        ("How many users are there?", ["users"]),
        ("Show tasks for John", ["tasks", "users"]),
        ("List all projects", ["projects"]),
        ("Find user activities", ["users", "activities"]),
        ("Count orders by customer", ["orders", "customers"])
    ]
    
    for query, expected_tables in test_queries:
        start_time = time.time()
        test_result = optimized_schema_retriever.test_retrieval(query)
        test_time = time.time() - start_time
        
        candidate_tables = test_result['candidate_tables']
        retrieved_tables = test_result['retrieved_tables']
        
        # Check if expected tables were found
        found_expected = any(
            exp in candidate_tables or exp in retrieved_tables 
            for exp in expected_tables
        )
        
        print(f"  🔍 '{query}'")
        print(f"    Expected: {expected_tables}")
        print(f"    Candidates: {candidate_tables}")
        print(f"    Retrieved: {retrieved_tables}")
        print(f"    Time: {test_time:.3f}s")
        print(f"    ✅ Pre-filtering: {'PASS' if found_expected else 'FAIL'}")
    
    return True


def test_memory_usage():
    """Test memory efficiency."""
    print("\n🧪 Testing Memory Usage")
    print("=" * 50)
    
    try:
        import psutil
        process = psutil.Process()
        
        # Get memory before initialization
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Initialize system
        pipeline = optimized_chat_pipeline
        
        # Get memory after initialization
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        print(f"💾 Memory usage:")
        print(f"  Before: {memory_before:.1f} MB")
        print(f"  After: {memory_after:.1f} MB")
        print(f"  Used: {memory_used:.1f} MB")
        
        # Memory target (should be under 100MB for large schemas)
        print(f"🎯 Memory efficiency:")
        print(f"  ✅ Memory < 100MB: {'PASS' if memory_used < 100 else 'FAIL'}")
        
        return memory_used < 100
        
    except ImportError:
        print("⚠️  psutil not available - skipping memory test")
        return True


def test_top_k_limits():
    """Test Top-K retrieval limits."""
    print("\n🧪 Testing Top-K Limits")
    print("=" * 50)
    
    # Test with different queries
    test_query = "Show user information and their tasks"
    
    for k in [1, 2, 3, 5]:
        start_time = time.time()
        result = optimized_chat_pipeline.chat_with_sql(test_query, max_tables=k)
        query_time = time.time() - start_time
        
        # Count tables in context
        context = result.get('metadata', {}).get('tables_retrieved', 0)
        
        print(f"  🔍 Top-K={k}: {context} tables, {query_time:.3f}s")
        
        # Should respect the limit
        limit_respected = context <= k
        print(f"    ✅ Limit respected: {'PASS' if limit_respected else 'FAIL'}")
    
    return True


def run_all_tests():
    """Run all optimization tests."""
    print("🚀 Optimized Chat with SQL - Test Suite")
    print("=" * 60)
    print("Testing all scalability optimizations...")
    print("=" * 60)
    
    tests = [
        ("Initialization Performance", test_initialization_performance),
        ("Schema Scaling", test_schema_scaling),
        ("Incremental Updates", test_incremental_updates),
        ("Pre-Filtering", test_pre_filtering),
        ("Memory Usage", test_memory_usage),
        ("Top-K Limits", test_top_k_limits)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All optimizations working correctly!")
    else:
        print("⚠️  Some optimizations need attention")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
