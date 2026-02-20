import os
import sys
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

# Ensure the root directory is in the python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, 'src'))

def run_api():
    print("🚀 Launching FastAPI Backend on http://localhost:8001 ...")
    os.environ["PYTHONPATH"] = f"{ROOT_DIR};{os.path.join(ROOT_DIR, 'src')}"
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "apps.api:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload"
    ])

def run_ui():
    print("🎨 Launching Streamlit Web UI...")
    # Wait for API to potentially start
    time.sleep(3)
    os.environ["PYTHONPATH"] = f"{ROOT_DIR};{os.path.join(ROOT_DIR, 'src')}"
    subprocess.run(["streamlit", "run", "apps/ui.py", "--server.port", "8502"])

if __name__ == "__main__":
    print("🌟 Talk with DB - Professional Edition 🌟")
    print("-" * 40)
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(run_api)
        executor.submit(run_ui)
