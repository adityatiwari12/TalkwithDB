"""
Low-VRAM fine-tuning for Text-to-SQL on 8GB GPUs (RTX 3060 Ti, 4060, etc.)
Uses CPU offloading, gradient checkpointing, and aggressive memory optimizations.
"""

import os
import argparse
import torch
from pathlib import Path
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel

# Memory-optimized settings for 8GB VRAM
MAX_SEQ_LENGTH = 2048  # Reduced from 4096
DEFAULT_LORA_R = 16    # Reduced from 64
DEFAULT_LORA_ALPHA = 32  # Reduced from 128


def load_model_low_vram(model_name: str):
    """Load model with extreme memory optimizations."""
    print(f"Loading model with 8GB VRAM optimizations: {model_name}")
    print("⚠️  This will use CPU offloading - training will be slower")
    
    # Force garbage collection
    import gc
    gc.collect()
    torch.cuda.empty_cache()
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=torch.float16,  # Use fp16 instead of bf16 for compatibility
        load_in_4bit=True,
        # Memory optimizations
        device_map="auto",  # Auto device mapping with CPU offloading
        max_memory={0: "7GiB", "cpu": "30GiB"},  # Limit GPU to 7GB, use CPU for rest
    )
    
    return model, tokenizer


def setup_lora_low_vram(model, r: int = 16, alpha: int = 32):
    """Setup LoRA with minimal memory footprint."""
    print(f"Setting up LoRA (r={r}, alpha={alpha}) with gradient checkpointing")
    
    model = FastLanguageModel.get_peft_model(
        model,
        r=r,
        target_modules=[
            "q_proj", "v_proj",  # Only key projections - saves memory
        ],
        lora_alpha=alpha,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",  # Critical for 8GB
        random_state=3407,
        use_rslora=False,
    )
    
    return model


def format_sql_prompt(examples):
    """Format examples for training - shorter for memory efficiency."""
    texts = []
    for i in range(len(examples['instruction'])):
        # Compact format to reduce sequence length
        text = f"### Instruction:\n{examples['instruction'][i]}\n\n### Input:\n{examples['input'][i]}\n\n### Response:\n{examples['output'][i]}"
        texts.append(text)
    return {'text': texts}


def load_sql_dataset(dataset_path: str, tokenizer, max_samples = None):
    """Load dataset with optional size limit for faster training."""
    print(f"Loading dataset from: {dataset_path}")
    
    from datasets import load_dataset
    
    ext = Path(dataset_path).suffix
    if ext == '.jsonl':
        dataset = load_dataset('json', data_files=str(dataset_path), split='train')
    else:
        dataset = load_dataset('json', data_files=str(dataset_path), split='train')
    
    # Limit samples for low VRAM training (fewer samples = less memory)
    if max_samples and len(dataset) > max_samples:
        dataset = dataset.select(range(max_samples))
        print(f"Limited to {max_samples} samples for memory efficiency")
    
    print(f"Loaded {len(dataset)} examples")
    dataset = dataset.map(format_sql_prompt, batched=True)
    
    return dataset


def train_low_vram(
    model_name: str,
    dataset_path: str,
    output_dir: str,
    epochs: int = 1,  # Fewer epochs for faster training
    batch_size: int = 1,  # Must be 1 for 8GB
    gradient_accumulation_steps: int = 8,  # Higher to compensate
    learning_rate: float = 5e-4,  # Slightly higher for small batches
    lora_r: int = 16,
    lora_alpha: int = 32,
    max_samples: int = 1000,  # Limit samples
):
    """Main training loop optimized for 8GB VRAM."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Check available VRAM
    if torch.cuda.is_available():
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"\n=== GPU Info ===")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {vram:.1f} GB")
        
        if vram < 10:  # Less than 10GB
            print("⚠️  Low VRAM detected - applying aggressive optimizations")
            print("   - Batch size: 1")
            print("   - Max sequence length: 2048")
            print("   - LoRA rank: 16")
            print("   - CPU offloading enabled")
    else:
        print("ERROR: No GPU detected!")
        return None
    
    # Load model
    model, tokenizer = load_model_low_vram(model_name)
    
    # Setup LoRA
    model = setup_lora_low_vram(model, r=lora_r, alpha=lora_alpha)
    
    # Load dataset
    dataset = load_sql_dataset(dataset_path, tokenizer, max_samples=max_samples)
    
    # Simple train/val split
    if len(dataset) > 200:
        split_dataset = dataset.train_test_split(test_size=0.1, seed=42)
        train_dataset = split_dataset['train']
        eval_dataset = split_dataset['test']
    else:
        train_dataset = dataset
        eval_dataset = None
    
    # Memory-optimized training arguments
    training_args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=epochs,
        per_device_train_batch_size=1,  # CRITICAL: Must be 1 for 8GB
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=gradient_accumulation_steps,
        warmup_steps=5,
        learning_rate=learning_rate,
        fp16=True,  # Use fp16 on 30-series cards
        bf16=False,  # 3060 Ti doesn't support bf16 well
        logging_steps=10,
        optim="adamw_8bit",  # 8-bit optimizer saves VRAM
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        max_grad_norm=0.3,
        # group_by_length removed - not supported in this transformers version
        report_to="none",
        save_strategy="epoch",  # Save per epoch to reduce disk I/O
        save_total_limit=1,  # Keep only last checkpoint
        eval_strategy="no" if eval_dataset is None else "epoch",
        load_best_model_at_end=False,  # Saves memory
        dataloader_num_workers=0,  # Reduces CPU memory
        remove_unused_columns=False,  # Prevents errors
    )
    
    # Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=1,  # Reduce parallelism for memory
        packing=True,  # Enable packing for efficiency
        args=training_args,
    )
    
    # Train
    print("\n=== Starting Training (Low VRAM Mode) ===")
    print(f"Training samples: {len(train_dataset)}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: 1 (fixed)")
    print(f"Gradient accumulation: {gradient_accumulation_steps}")
    print(f"Effective batch size: {gradient_accumulation_steps}")
    print(f"Learning rate: {learning_rate}")
    print(f"LoRA: r={lora_r}, alpha={lora_alpha}")
    print(f"\n⚠️  Training will be slower due to CPU offloading")
    print("   Expected time: ~2-4 hours for 1000 samples\n")
    
    trainer.train()
    
    # Save final model
    final_path = output_path / "final"
    print(f"\nSaving final model to: {final_path}")
    
    model.save_pretrained(str(final_path))
    tokenizer.save_pretrained(str(final_path))
    
    # Save config
    import json
    config = {
        'base_model': model_name,
        'lora_r': lora_r,
        'lora_alpha': lora_alpha,
        'epochs': epochs,
        'training_mode': 'low_vram_8gb',
        'max_seq_length': MAX_SEQ_LENGTH,
    }
    with open(final_path / 'training_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n=== Training Complete ===")
    print(f"Model saved to: {final_path}")
    print(f"\nTo export to Ollama:")
    print(f"  python export_to_ollama.py --checkpoint {final_path} --name gpt-oss-20b-sql")
    
    return final_path


def main():
    parser = argparse.ArgumentParser(description='Fine-tune on 8GB VRAM GPU')
    parser.add_argument('--model_name', type=str, default='gpt-oss:20b',
                        help='Base model name or path')
    parser.add_argument('--dataset', type=str, required=True,
                        help='Path to training dataset')
    parser.add_argument('--output', type=str, default='./output_low_vram',
                        help='Output directory')
    parser.add_argument('--epochs', type=int, default=1,
                        help='Number of epochs (default: 1 for speed)')
    parser.add_argument('--gradient_accumulation_steps', type=int, default=8,
                        help='Gradient accumulation steps (default: 8)')
    parser.add_argument('--learning_rate', type=float, default=5e-4,
                        help='Learning rate (default: 5e-4)')
    parser.add_argument('--lora_r', type=int, default=16,
                        help='LoRA rank (default: 16)')
    parser.add_argument('--lora_alpha', type=int, default=32,
                        help='LoRA alpha (default: 32)')
    parser.add_argument('--max_samples', type=int, default=1000,
                        help='Max samples to use (default: 1000, use fewer if OOM)')
    
    args = parser.parse_args()
    
    train_low_vram(
        model_name=args.model_name,
        dataset_path=args.dataset,
        output_dir=args.output,
        epochs=args.epochs,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        max_samples=args.max_samples,
    )


if __name__ == '__main__':
    main()
