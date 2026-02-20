#!/usr/bin/env python3
"""
Test to show the improvement in response length and detail
"""

import requests

def test_response_improvement():
    """Test that responses are now longer and more detailed"""
    
    base_url = "http://127.0.0.1:8001/api/chat"
    session_id = "improvement_test"
    
    test_queries = [
        "show me the complete project details including descriptions",
        "tell me about all users and their projects", 
        "list all orders with customer information",
        "show tasks for different projects",
        "how many customers and users do we have"
    ]
    
    print("📊 TESTING RESPONSE LENGTH IMPROVEMENT")
    print("=" * 60)
    
    total_chars = 0
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 40)
        
        try:
            response = requests.post(
                base_url,
                json={
                    'message': query,
                    'session_id': session_id,
                    'max_tables': 3
                },
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data['response']
                char_count = len(response_text)
                total_chars += char_count
                
                print(f"✅ Status: {response.status_code}")
                print(f"📝 Response Length: {char_count} characters")
                print(f"📊 Preview: {response_text[:150]}...")
                
                if char_count > 500:
                    print("🎯 GOOD: Detailed response!")
                elif char_count > 300:
                    print("👍 OK: Moderate length")
                else:
                    print("⚠️  SHORT: Could be more detailed")
                    
            else:
                print(f"❌ Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📈 IMPROVEMENT SUMMARY")
    print("=" * 60)
    print(f"📊 Total characters across all queries: {total_chars}")
    print(f"📈 Average response length: {total_chars // len(test_queries)} characters")
    
    if total_chars // len(test_queries) > 500:
        print("🎉 SUCCESS: Responses are now detailed and comprehensive!")
    else:
        print("⚠️  Responses could still be longer")
    
    print("\n🌐 Access the improved chat at: http://localhost:8502")
    print("💡 Try these queries in the Streamlit UI to see the improvement!")

if __name__ == "__main__":
    test_response_improvement()
