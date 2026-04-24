"""
Export fine-tuned model to Ollama-compatible GGUF format.
Creates a Modelfile and imports into Ollama.
"""

import os
import argparse
import subprocess
from pathlib import Path
from typing import Optional
from unsloth import FastLanguageModel


def export_to_gguf(
    checkpoint_path: str,
    output_path: str,
    quantization: str = 'Q4_K_M',
    base_model: Optional[str] = None,
):
    """Export fine-tuned model to GGUF format."""
    print(f"Loading model from: {checkpoint_path}")
    
    # Load the fine-tuned model
    if base_model:
        # Load with base model + LoRA
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=base_model,
            max_seq_length=4096,
            dtype=None,
            load_in_4bit=False,
        )
        # Merge LoRA weights
        model = FastLanguageModel.get_peft_model(
            model,
            r=64,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ],
            lora_alpha=128,
        )
        model.load_adapter(checkpoint_path, adapter_name='default')
        model = model.merge_and_unload()
    else:
        # Direct load (if full fine-tune)
        from transformers import AutoModelForCausalLM, AutoTokenizer
        model = AutoModelForCausalLM.from_pretrained(checkpoint_path)
        tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
    
    print(f"Exporting to GGUF with quantization: {quantization}")
    
    # Save to temporary directory
    temp_path = Path(output_path).parent / 'temp_export'
    temp_path.mkdir(exist_ok=True)
    
    model.save_pretrained(str(temp_path))
    tokenizer.save_pretrained(str(temp_path))
    
    # Convert to GGUF using llama.cpp convert script
    # Note: Requires llama.cpp installed
    gguf_path = Path(output_path)
    
    print(f"GGUF model will be saved to: {gguf_path}")
    print("\nTo convert to GGUF, run:")
    print(f"python llama.cpp/convert_hf_to_gguf.py {temp_path} --outfile {gguf_path} --outtype {quantization}")
    
    return str(gguf_path)


def create_modelfile(model_name: str, gguf_path: str, system_prompt: Optional[str] = None):
    """Create Ollama Modelfile."""
    
    if system_prompt is None:
        system_prompt = """You are a PostgreSQL expert. Generate only valid SELECT SQL queries.

Rules:
- Only use tables and columns from the provided schema
- Always add LIMIT 200 if not specified
- Return only the SQL query, no explanation, no markdown
- Use appropriate JOINs based on the schema relationships
- Use proper PostgreSQL syntax

Example:
Schema: Table users(id, name), Table tasks(id, title, assigned_to)
Question: Show me all users with tasks
SQL: SELECT DISTINCT u.name FROM users u JOIN tasks t ON u.id = t.assigned_to LIMIT 200"""
    
    modelfile_content = f'''FROM {gguf_path}

PARAMETER temperature 0.1
PARAMETER num_predict 500
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

SYSTEM """{system_prompt}"""'''
    
    modelfile_path = Path(gguf_path).parent / 'Modelfile'
    with open(modelfile_path, 'w') as f:
        f.write(modelfile_content)
    
    print(f"\nModelfile created: {modelfile_path}")
    return str(modelfile_path)


def import_to_ollama(model_name: str, modelfile_path: str):
    """Import model into Ollama."""
    print(f"\nImporting model '{model_name}' into Ollama...")
    
    try:
        result = subprocess.run(
            ['ollama', 'create', model_name, '-f', modelfile_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Model imported successfully!")
        print(f"  Run with: ollama run {model_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Import failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Ollama not found. Is it installed?")
        print("  Install from: https://ollama.com/download")
        return False


def main():
    parser = argparse.ArgumentParser(description='Export fine-tuned model to Ollama')
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to fine-tuned model checkpoint')
    parser.add_argument('--base-model', type=str, default='gpt-oss:20b',
                        help='Base model name (if using LoRA)')
    parser.add_argument('--name', type=str, default='gpt-oss-20b-sql',
                        help='Name for Ollama model')
    parser.add_argument('--output', type=str, default='./gguf',
                        help='Output directory for GGUF')
    parser.add_argument('--quantization', type=str, default='Q4_K_M',
                        choices=['Q4_0', 'Q4_K_M', 'Q5_K_M', 'Q6_K', 'Q8_0', 'f16'],
                        help='GGUF quantization type')
    parser.add_argument('--system-prompt', type=str,
                        help='Custom system prompt for Modelfile')
    parser.add_argument('--skip-export', action='store_true',
                        help='Skip GGUF export (use existing file)')
    parser.add_argument('--gguf-path', type=str,
                        help='Path to existing GGUF file')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export to GGUF
    if not args.skip_export:
        gguf_path = output_dir / f'{args.name}.gguf'
        export_to_gguf(
            checkpoint_path=args.checkpoint,
            output_path=str(gguf_path),
            quantization=args.quantization,
            base_model=args.base_model,
        )
    else:
        gguf_path = Path(args.gguf_path)
    
    # Create Modelfile
    modelfile_path = create_modelfile(
        model_name=args.name,
        gguf_path=str(gguf_path),
        system_prompt=args.system_prompt,
    )
    
    # Import to Ollama
    import_to_ollama(args.name, modelfile_path)
    
    print("\n=== Export Complete ===")
    print(f"To use in TalkWithDB:")
    print(f"  export OLLAMA_LLM_MODEL={args.name}")
    print(f"  # Or update src/chat_sql/config.py")
    print(f"  # OLLAMA_LLM_MODEL: str = os.getenv('OLLAMA_LLM_MODEL', '{args.name}')")


if __name__ == '__main__':
    main()
