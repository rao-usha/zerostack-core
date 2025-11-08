"""Build Parquet/JSONL datasets and fine-tune packs."""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from sqlalchemy.orm import Session
from ..models import SyntheticExample, ContextVariant, DatasetKind
from ..config import settings


def build_dataset(
    db: Session,
    dataset_id: str,
    name: str,
    version: str,
    kind: DatasetKind,
    variant_ids: List[str],
    filters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build a dataset from examples.
    
    Returns manifest dict with file URIs and hashes.
    """
    # Get variants
    variants = db.query(ContextVariant).filter(ContextVariant.id.in_(variant_ids)).all()
    if not variants:
        raise ValueError(f"No variants found for IDs: {variant_ids}")
    
    # Get examples from variants
    examples = db.query(SyntheticExample).filter(
        SyntheticExample.variant_id.in_(variant_ids)
    ).all()
    
    if not examples:
        raise ValueError("No examples found in variants")
    
    # Apply filters
    from .filters import apply_filters
    filtered_examples = apply_filters(examples, filters, settings.REQUIRE_APPROVAL)
    
    if not filtered_examples:
        raise ValueError("No examples passed filters")
    
    # Create dataset directory
    data_dir = Path(settings.DATA_DIR)
    if kind == DatasetKind.FINETUNE_PACK:
        dataset_dir = data_dir / "packs" / f"{name}@{version}"
    else:
        dataset_dir = data_dir / name / version
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    file_uris = []
    
    # Build examples DataFrame
    examples_rows = []
    for example in filtered_examples:
        examples_rows.append({
            "id": example.id,
            "variant_id": example.variant_id,
            "example_type": example.example_type.value,
            "input": json.dumps(example.input_json),
            "constraints": json.dumps(example.constraints_json),
            "tags": example.tags
        })
    
    examples_df = pd.DataFrame(examples_rows)
    
    # For fine-tune packs, create JSONL
    if kind == DatasetKind.FINETUNE_PACK:
        # Create train/eval splits
        train_size = int(len(examples_df) * 0.9)
        train_df = examples_df[:train_size]
        eval_df = examples_df[train_size:]
        
        # Build JSONL format (instruction-following format)
        train_rows = []
        for _, row in train_df.iterrows():
            example = next(e for e in filtered_examples if e.id == row["id"])
            input_data = example.input_json
            
            # Get teacher output as target
            target_text = ""
            if example.teacher_runs:
                teacher_run = example.teacher_runs[-1]
                if teacher_run.output_json:
                    target_text = teacher_run.output_json.get("text", "")
            
            jsonl_row = {
                "instruction": input_data.get("instruction", input_data.get("question", input_data.get("task", ""))),
                "input": input_data.get("input", input_data.get("context_preview", "")),
                "output": target_text
            }
            train_rows.append(jsonl_row)
        
        # Write train.jsonl
        train_path = dataset_dir / "train.jsonl"
        with open(train_path, "w") as f:
            for row in train_rows:
                f.write(json.dumps(row) + "\n")
        file_uris.append(str(train_path))
        
        # Write eval.jsonl
        eval_rows = []
        for _, row in eval_df.iterrows():
            example = next(e for e in filtered_examples if e.id == row["id"])
            input_data = example.input_json
            
            target_text = ""
            if example.teacher_runs:
                teacher_run = example.teacher_runs[-1]
                if teacher_run.output_json:
                    target_text = teacher_run.output_json.get("text", "")
            
            jsonl_row = {
                "instruction": input_data.get("instruction", input_data.get("question", input_data.get("task", ""))),
                "input": input_data.get("input", input_data.get("context_preview", "")),
                "output": target_text
            }
            eval_rows.append(jsonl_row)
        
        eval_path = dataset_dir / "eval.jsonl"
        with open(eval_path, "w") as f:
            for row in eval_rows:
                f.write(json.dumps(row) + "\n")
        file_uris.append(str(eval_path))
        
        # Create manifest
        manifest = {
            "id": dataset_id,
            "name": name,
            "version": version,
            "kind": kind.value,
            "variant_ids": variant_ids,
            "filters": filters,
            "files": [
                {"name": "train.jsonl", "path": str(train_path), "hash": _compute_hash(train_path)},
                {"name": "eval.jsonl", "path": str(eval_path), "hash": _compute_hash(eval_path)}
            ],
            "num_examples": len(filtered_examples),
            "train_size": len(train_rows),
            "eval_size": len(eval_rows)
        }
        
        manifest_path = dataset_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        file_uris.append(str(manifest_path))
        
        return manifest
    
    else:
        # Regular Parquet dataset
        examples_path = dataset_dir / "examples.parquet"
        examples_df.to_parquet(examples_path, index=False)
        file_uris.append(str(examples_path))
        
        # Targets
        from .targets import extract_targets_from_runs
        targets_df = extract_targets_from_runs(filtered_examples)
        if not targets_df.empty:
            targets_path = dataset_dir / "targets.parquet"
            targets_df.to_parquet(targets_path, index=False)
            file_uris.append(str(targets_path))
        
        # Create manifest
        manifest = {
            "id": dataset_id,
            "name": name,
            "version": version,
            "kind": kind.value,
            "variant_ids": variant_ids,
            "filters": filters,
            "files": [{"name": Path(uri).name, "path": uri, "hash": _compute_hash(Path(uri))} 
                     for uri in file_uris],
            "num_examples": len(filtered_examples)
        }
        
        manifest_path = dataset_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        return manifest


def _compute_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
