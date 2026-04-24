# Text-to-SQL Fine-Tuning Guide

Fine-tuning `gpt-oss:20b` on SQL-specific datasets to improve NL-to-SQL accuracy.

## Recommended Datasets

| Dataset | Size | Complexity | Best For |
|---------|------|------------|----------|
| **Spider 1.0** | 10k+ queries, 200 DBs | High (cross-domain) | General purpose |
| **BIRD-SQL** | 12k+ queries, 95 DBs | Very High (external knowledge) | Complex real-world queries |
| **BIRD-SQL Mini-Dev** | 500 queries, 11 DBs | Medium | Quick experimentation |
| **SParC** | 12k+ multi-turn | High | Conversational SQL |
| **CoSQL** | 30k+ turns | High | Dialogue-based queries |

## Fine-Tuning Methods

### 1. QLoRA (Recommended for 20B models)
- **Memory**: ~20-24GB VRAM (can run on single A100 or dual RTX 4090)
- **Method**: 4-bit quantization + LoRA adapters
- **Time**: 2-4 hours for 10k examples

### 2. Full Fine-tuning
- **Memory**: ~80GB+ VRAM (requires H100/A100 80GB or multi-GPU)
- **Method**: Unfrozen weights
- **Time**: 6-12 hours

## Quick Start

```bash
cd training

# 1. Install training dependencies
pip install unsloth transformers datasets trl peft accelerate bitsandbytes

# 2. Download and prepare dataset
python prepare_data.py --dataset spider --output ./data

# 3. Start training (QLoRA)
python train_sql.py \
    --model_name gpt-oss:20b \
    --dataset ./data/spider.json \
    --output ./output \
    --method qlora \
    --epochs 3 \
    --batch_size 4

# 4. Export to Ollama
python export_to_ollama.py \
    --checkpoint ./output/final \
    --name gpt-oss-20b-sql
```

## Dataset Format

Each training example should follow this JSON structure:

```json
{
  "instruction": "Convert natural language to SQL",
  "input": "What are the names of users who have pending tasks?",
  "schema": "Table: users(id, name, email); Table: tasks(id, title, status, assigned_to)",
  "output": "SELECT DISTINCT u.name FROM users u JOIN tasks t ON u.id = t.assigned_to WHERE t.status = 'pending'",
  "database": "chat_sql_db",
  "difficulty": "medium"
}
```

## Expected Accuracy Improvements

| Model | Spider Dev (EM) | BIRD Dev (EX) |
|-------|-----------------|---------------|
| Base (gpt-oss:20b) | ~45% | ~35% |
| + Spider FT | ~65-70% | ~50% |
| + BIRD FT | ~60% | ~55-60% |
| + Combined | ~68-72% | ~58-62% |

## Ollama Integration

After training, create a custom Ollama model:

```bash
# Create Modelfile
cat > Modelfile << 'EOF'
FROM ./gguf-model.bin
PARAMETER temperature 0.1
PARAMETER num_predict 500
SYSTEM """You are a PostgreSQL expert. Generate only valid SELECT SQL queries.
Rules:
- Only use tables and columns from the provided schema
- Always add LIMIT 200 if not specified
- Return only the SQL query, no explanation
- Use appropriate JOINs based on the schema relationships"""
EOF

# Import into Ollama
ollama create gpt-oss-20b-sql -f Modelfile

# Update project config
export OLLAMA_LLM_MODEL=gpt-oss-20b-sql
```

## Advanced: Multi-Dataset Training

Combine multiple datasets for better generalization:

```python
# prepare_data.py --combine
python prepare_data.py \
    --combine spider bird minidev \
    --weights 0.4 0.4 0.2 \
    --output ./data/combined.json
```

## Hardware Requirements

| Setup | VRAM | Estimated Cost (cloud) |
|-------|------|------------------------|
| QLoRA RTX 4090 | 24GB | $0.50/hr |
| QLoRA A100 40GB | 40GB | $1.10/hr |
| **QLoRA RTX 3060 Ti** | **8GB** | **N/A (local)** |
| Full FT A100 80GB | 80GB | $2.20/hr |
| Full FT 2x A100 | 160GB | $4.40/hr |

### RTX 3060 Ti / 8GB VRAM Setup

For 8GB GPUs (RTX 3060 Ti, 4060, 3070, etc.), use the low-VRAM script:

```bash
# Use the low-VRAM training script
python train_sql_low_vram.py \
    --model_name gpt-oss:20b \
    --dataset ./data/spider.json \
    --output ./output \
    --epochs 1 \
    --max_samples 500
```

**Optimizations applied:**
- Batch size: 1 (required for 8GB)
- Sequence length: 2048 (reduced from 4096)
- LoRA rank: 16 (reduced from 64)
- CPU offloading enabled
- 8-bit optimizer
- Gradient checkpointing

**Expected training time:** 3-5 hours for 500 samples

⚠️ **Note:** Training will be slower due to CPU offloading, but it will work on your RTX 3060 Ti.

## Troubleshooting

**Out of Memory**: Reduce batch size, increase gradient accumulation
**Slow training**: Enable flash attention, use deepspeed
**Poor SQL quality**: Check dataset quality, increase epochs
**Overfitting**: Add validation set, use early stopping

## Resources

- [Awesome-Text2SQL](https://github.com/eosphoros-ai/Awesome-Text2SQL)
- [Spider Leaderboard](https://yale-lily.github.io/spider)
- [BIRD Benchmark](https://bird-bench.github.io/)
- [Unsloth Docs](https://docs.unsloth.ai/)
