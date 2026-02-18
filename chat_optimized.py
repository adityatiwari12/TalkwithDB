#!/usr/bin/env python3
"""
Optimized Chat with SQL - Entry Point
Scalable RAG implementation for large database schemas.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'chat_sql'))

from optimized_cli import main

if __name__ == "__main__":
    main()
