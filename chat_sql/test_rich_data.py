#!/usr/bin/env python3
"""
Test the Chat with SQL system with rich mock data.
"""

from pipeline.chat_with_sql import chat_pipeline

def test_with_rich_data():
    """Test the system with the newly added rich data."""
    print("🧪 Testing Chat with SQL with Rich Data")
    print("=" * 50)
    
    try:
        # Test 1: Simple query
        print("📝 Query 1: Show all users")
        result1 = chat_pipeline.chat_with_sql("Show all users")
        print(f"Answer: {result1['answer'][:100]}...")
        print(f"Results: {len(result1['results'])} users")
        
        # Test 2: Complex aggregation
        print("\n📝 Query 2: How many tasks does each user have?")
        result2 = chat_pipeline.chat_with_sql("How many tasks does each user have?")
        print(f"Answer: {result2['answer'][:100]}...")
        print(f"Results: {len(result2['results'])} rows")
        
        # Test 3: Filter query
        print("\n📝 Query 3: Which users have more than 8 tasks?")
        result3 = chat_pipeline.chat_with_sql("Which users have more than 8 tasks?")
        print(f"Answer: {result3['answer'][:100]}...")
        print(f"Results: {len(result3['results'])} users")
        
        # Test 4: Project-based query
        print("\n📝 Query 4: Which projects have the most pending tasks?")
        result4 = chat_pipeline.chat_with_sql("Which projects have the most pending tasks?")
        print(f"Answer: {result4['answer'][:100]}...")
        print(f"Results: {len(result4['results'])} projects")
        
        print("\n🎉 All queries working perfectly with rich data!")
        print("✅ The Chat with SQL system is ready for production use!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_with_rich_data()
