#!/usr/bin/env python3
"""
Comprehensive test script for Talk with DB Version 3
Tests all major components and functionality
"""

import sys
import os
import requests
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_database_connection():
    """Test database connectivity and data"""
    print("🔍 Testing Database Connection...")
    try:
        from src.chat_sql.db.connection import db_connection
        
        # Test basic connection
        db_connection.test_connection()
        print("✅ Database connection successful")
        
        # Test sample data
        result = db_connection.execute_query('SELECT COUNT(*) as count FROM users')
        user_count = result[0]['count']
        print(f"✅ Found {user_count} users in database")
        
        result = db_connection.execute_query('SELECT COUNT(*) as count FROM projects')
        project_count = result[0]['count']
        print(f"✅ Found {project_count} projects in database")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_schema_loader():
    """Test schema loading functionality"""
    print("\n🔍 Testing Schema Loader...")
    try:
        from src.chat_sql.db.schema_loader import schema_loader
        
        tables = schema_loader.get_all_tables()
        print(f"✅ Found {len(tables)} tables: {tables}")
        
        # Test getting table info
        if tables:
            table_info = schema_loader.get_table_info(tables[0])
            print(f"✅ Table info for {tables[0]}: {len(table_info.columns)} columns")
        
        return True
    except Exception as e:
        print(f"❌ Schema loader test failed: {e}")
        return False

def test_ollama_connection():
    """Test Ollama API connectivity"""
    print("\n🔍 Testing Ollama Connection...")
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = [model['name'] for model in response.json().get('models', [])]
            print(f"✅ Ollama connected successfully")
            print(f"✅ Available models: {models}")
            return True
        else:
            print(f"❌ Ollama returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🔍 Testing API Endpoints...")
    try:
        # Test health endpoint
        response = requests.get('http://127.0.0.1:8001/health', timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"✅ Health response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test schema endpoint
        response = requests.get('http://127.0.0.1:8001/api/schema', timeout=10)
        if response.status_code == 200:
            schema_data = response.json()
            print(f"✅ Schema endpoint working")
            print(f"✅ Found {schema_data.get('total_tables', 0)} tables")
        else:
            print(f"❌ Schema endpoint failed: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_streamlit_ui():
    """Test Streamlit UI accessibility"""
    print("\n🔍 Testing Streamlit UI...")
    try:
        response = requests.get('http://localhost:8502', timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit UI accessible")
            return True
        else:
            print(f"❌ Streamlit UI returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streamlit UI test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 TALK WITH DB VERSION 3 - COMPREHENSIVE TEST")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # Run all tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Schema Loader", test_schema_loader()))
    results.append(("Ollama Connection", test_ollama_connection()))
    results.append(("API Endpoints", test_api_endpoints()))
    results.append(("Streamlit UI", test_streamlit_ui()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is fully operational!")
        print("\n🌐 Access URLs:")
        print("   • API Documentation: http://127.0.0.1:8001/docs")
        print("   • Streamlit UI: http://localhost:8502")
        print("   • API Health: http://127.0.0.1:8001/health")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
