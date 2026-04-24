"""
Dataset preparation for Text-to-SQL fine-tuning.
Downloads and formats Spider, BIRD, and other datasets.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from datasets import load_dataset


SYSTEM_PROMPT = """You are a PostgreSQL expert. Given a database schema and a natural language question, generate a valid SQL query.

Rules:
- Only use tables and columns from the provided schema
- Always add LIMIT 200 if not specified
- Return only the SQL query, no explanation, no markdown
- Use appropriate JOINs based on the schema relationships
- Use proper PostgreSQL syntax
"""


def format_spider_example(example: Dict) -> Dict[str, str]:
    """Format a Spider example for training."""
    schema = example.get('schema', {})
    schema_str = _schema_to_string(schema)
    
    return {
        'instruction': SYSTEM_PROMPT,
        'input': f"Schema:\n{schema_str}\n\nQuestion: {example['question']}",
        'output': example['query'],
        'database': example.get('db_id', 'unknown'),
        'difficulty': example.get('difficulty', 'unknown'),
        'source': 'spider'
    }


def format_bird_example(example: Dict) -> Dict[str, str]:
    """Format a BIRD example for training."""
    schema = example.get('schema', {})
    evidence = example.get('evidence', '')
    
    schema_str = _schema_to_string(schema)
    if evidence:
        schema_str += f"\n\nExternal Knowledge: {evidence}"
    
    return {
        'instruction': SYSTEM_PROMPT,
        'input': f"Schema:\n{schema_str}\n\nQuestion: {example['question']}",
        'output': example['SQL'],
        'database': example.get('db_id', 'unknown'),
        'difficulty': example.get('difficulty', 'unknown'),
        'source': 'bird'
    }


def _schema_to_string(schema: Dict) -> str:
    """Convert schema dict to readable string."""
    if isinstance(schema, str):
        return schema
    
    parts = []
    for table_name, columns in schema.items():
        col_strs = []
        for col in columns:
            if isinstance(col, dict):
                col_name = col.get('name', col.get('column_name', ''))
                col_type = col.get('type', col.get('data_type', ''))
                col_strs.append(f"{col_name} ({col_type})")
            else:
                col_strs.append(str(col))
        parts.append(f"Table: {table_name}\nColumns: {', '.join(col_strs)}")
    
    return '\n\n'.join(parts)


def load_spider(split: str = 'train') -> List[Dict]:
    """Load Spider dataset from HuggingFace."""
    print(f"Loading Spider {split} split...")
    
    try:
        dataset = load_dataset("xlangai/spider", split=split)
        examples: List[Dict] = []
        for item in dataset:  # type: ignore
            ex = format_spider_example({
                'question': item.get('question', ''),
                'query': item.get('query', ''),
                'db_id': item.get('db_id', ''),
                'schema': item.get('schema', {}),
                'difficulty': item.get('difficulty', 'unknown')
            })
            examples.append(ex)
        return examples
    except Exception as e:
        print(f"Error loading Spider: {e}")
        print("Try: pip install datasets")
        return []


def load_bird(split: str = 'train') -> List[Dict]:
    """Load BIRD-SQL dataset."""
    print(f"Loading BIRD-SQL {split} split...")
    
    try:
        dataset = load_dataset("bird-sql/bird", split=split)
        examples: List[Dict] = []
        for item in dataset:  # type: ignore
            ex = format_bird_example({
                'question': item.get('question', ''),
                'SQL': item.get('SQL', ''),
                'db_id': item.get('db_id', ''),
                'schema': item.get('schema', {}),
                'evidence': item.get('evidence', ''),
                'difficulty': item.get('difficulty', 'unknown')
            })
            examples.append(ex)
        return examples
    except Exception as e:
        print(f"Error loading BIRD: {e}")
        return []


def load_custom_sql_data(filepath: Path) -> List[Dict]:
    """Load custom SQL dataset from JSON file."""
    print(f"Loading custom data from {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'examples' in data:
        return data['examples']
    else:
        return [data]


def combine_datasets(datasets: List[List[Dict]], weights: Optional[List[float]] = None) -> List[Dict]:
    """Combine multiple datasets with optional weighting."""
    if weights is None:
        weights = [1.0] * len(datasets)
    
    combined = []
    for dataset, weight in zip(datasets, weights):
        # Sample according to weight
        n_samples = int(len(dataset) * weight)
        sampled = dataset[:n_samples] if n_samples < len(dataset) else dataset
        combined.extend(sampled)
    
    return combined


def save_dataset(examples: List[Dict], output_path: Path, format: str = 'json'):
    """Save formatted dataset."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(examples, f, indent=2, ensure_ascii=False)
    elif format == 'jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    elif format == 'sharegpt':
        # Format for Axolotl/LLaMA-Factory ShareGPT format
        sharegpt_data = []
        for ex in examples:
            sharegpt_data.append({
                'conversations': [
                    {'from': 'system', 'value': ex['instruction']},
                    {'from': 'human', 'value': ex['input']},
                    {'from': 'gpt', 'value': ex['output']}
                ]
            })
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sharegpt_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(examples)} examples to {output_path}")


def print_statistics(examples: List[Dict]):
    """Print dataset statistics."""
    print("\n=== Dataset Statistics ===")
    print(f"Total examples: {len(examples)}")
    
    sources = {}
    difficulties = {}
    for ex in examples:
        src = ex.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1
        
        diff = ex.get('difficulty', 'unknown')
        difficulties[diff] = difficulties.get(diff, 0) + 1
    
    print(f"\nBy source:")
    for src, count in sources.items():
        print(f"  {src}: {count}")
    
    print(f"\nBy difficulty:")
    for diff, count in difficulties.items():
        print(f"  {diff}: {count}")


def main():
    parser = argparse.ArgumentParser(description='Prepare Text-to-SQL datasets')
    parser.add_argument('--dataset', type=str, nargs='+', 
                        choices=['spider', 'bird', 'minidev', 'custom'],
                        help='Dataset(s) to load')
    parser.add_argument('--custom-path', type=str,
                        help='Path to custom dataset JSON file')
    parser.add_argument('--split', type=str, default='train',
                        help='Dataset split (train/dev)')
    parser.add_argument('--combine', action='store_true',
                        help='Combine multiple datasets')
    parser.add_argument('--weights', type=float, nargs='+',
                        help='Weights for combining datasets (e.g., 0.5 0.5)')
    parser.add_argument('--output', type=str, required=True,
                        help='Output file path')
    parser.add_argument('--format', type=str, default='json',
                        choices=['json', 'jsonl', 'sharegpt'],
                        help='Output format')
    parser.add_argument('--max-samples', type=int,
                        help='Maximum samples per dataset')
    
    args = parser.parse_args()
    
    all_examples = []
    
    for dataset_name in args.dataset:
        if dataset_name == 'spider':
            examples = load_spider(args.split)
        elif dataset_name == 'bird':
            examples = load_bird(args.split)
        elif dataset_name == 'minidev':
            # BIRD Mini-Dev is a subset
            examples = load_bird('minidev')
        elif dataset_name == 'custom':
            if not args.custom_path:
                print("Error: --custom-path required for custom dataset")
                continue
            examples = load_custom_sql_data(Path(args.custom_path))
        else:
            print(f"Unknown dataset: {dataset_name}")
            continue
        
        if args.max_samples and len(examples) > args.max_samples:
            examples = examples[:args.max_samples]
        
        all_examples.append(examples)
        print(f"Loaded {len(examples)} examples from {dataset_name}")
    
    # Combine or use first
    if args.combine and len(all_examples) > 1:
        weights = args.weights or [1.0] * len(all_examples)
        final_examples = combine_datasets(all_examples, weights)
    elif all_examples:
        final_examples = all_examples[0]
    else:
        print("No examples loaded!")
        return
    
    print_statistics(final_examples)
    save_dataset(final_examples, args.output, args.format)
    
    print(f"\nDone! Output saved to: {args.output}")


if __name__ == '__main__':
    main()
