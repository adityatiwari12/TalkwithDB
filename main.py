"""
Main entry point fix for proper module loading.
Add this file to resolve import issues when running from project root.
"""

import sys
import os

# Add the src directory to Python path
project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, 'src')
chat_sql_path = os.path.join(src_path, 'chat_sql')

if src_path not in sys.path:
    sys.path.insert(0, src_path)
if chat_sql_path not in sys.path:
    sys.path.insert(0, chat_sql_path)

# Now we can import properly
from chat_sql.api.v3_api import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("chat_sql.api.v3_api:app", host="127.0.0.1", port=8001, reload=True)
