"""
Setup script for Ollama models.
Downloads and pulls required models for the Chat with SQL system.
"""

import subprocess
import sys
import requests
import time
import os

# Add src to path for absolute imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))

from chat_sql.config import config


class OllamaSetup:
    """Handles Ollama setup and model downloads."""
    
    def __init__(self):
        """Initialize Ollama setup."""
        self.base_url = config.OLLAMA_BASE_URL
        self.llm_model = config.OLLAMA_LLM_MODEL
        self.embed_model = config.OLLAMA_EMBED_MODEL
    
    def check_ollama_running(self) -> bool:
        """
        Check if Ollama is running.
        
        Returns:
            True if Ollama is accessible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def check_model_installed(self, model_name: str) -> bool:
        """
        Check if a specific model is installed.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model is installed
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"].startswith(model_name) for model in models)
            return False
        except requests.exceptions.RequestException:
            return False
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful
        """
        print(f"Pulling {model_name} model...")
        
        try:
            # Use subprocess to run ollama pull command
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"✅ Successfully pulled {model_name}")
                return True
            else:
                print(f"❌ Failed to pull {model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout while pulling {model_name}")
            return False
        except FileNotFoundError:
            print("❌ 'ollama' command not found. Please install Ollama first.")
            return False
        except Exception as e:
            print(f"❌ Error pulling {model_name}: {e}")
            return False
    
    def setup_models(self) -> None:
        """Setup all required models."""
        print("🚀 Setting up Ollama models for Chat with SQL...")
        
        # Check if Ollama is running
        if not self.check_ollama_running():
            print("❌ Ollama is not running. Please start Ollama first:")
            print("   - On macOS: `brew services start ollama`")
            print("   - On Linux: `systemctl start ollama` or `ollama serve`")
            print("   - On Windows: Start Ollama application")
            sys.exit(1)
        
        print(f"✅ Ollama is running at {self.base_url}")
        
        # Check and pull LLM model
        if not self.check_model_installed(self.llm_model):
            print(f"📥 LLM model '{self.llm_model}' not found. Pulling...")
            if not self.pull_model(self.llm_model):
                print(f"❌ Failed to setup LLM model '{self.llm_model}'")
                sys.exit(1)
        else:
            print(f"✅ LLM model '{self.llm_model}' is already installed")
        
        # Check and pull embedding model
        if not self.check_model_installed(self.embed_model):
            print(f"📥 Embedding model '{self.embed_model}' not found. Pulling...")
            if not self.pull_model(self.embed_model):
                print(f"❌ Failed to setup embedding model '{self.embed_model}'")
                sys.exit(1)
        else:
            print(f"✅ Embedding model '{self.embed_model}' is already installed")
        
        print("\n🎉 All models are ready!")
        print(f"   - LLM Model: {self.llm_model}")
        print(f"   - Embedding Model: {self.embed_model}")
    
    def test_models(self) -> None:
        """Test if models are working correctly."""
        print("\n🧪 Testing models...")
        
        # Test embedding model
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embed_model,
                    "prompt": "test"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                embedding = response.json().get("embedding", [])
                print(f"✅ Embedding model working (dimension: {len(embedding)})")
            else:
                print(f"❌ Embedding model test failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing embedding model: {e}")
        
        # Test LLM model
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": "Say 'Hello World'",
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json().get("response", "")
                print(f"✅ LLM model working: '{result.strip()}'")
            else:
                print(f"❌ LLM model test failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing LLM model: {e}")


def main():
    """Main setup function."""
    setup = OllamaSetup()
    
    try:
        setup.setup_models()
        setup.test_models()
        print("\n🚀 Ollama setup complete! You can now run the Chat with SQL system.")
        
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
