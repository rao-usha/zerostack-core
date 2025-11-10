"""Seed script for Insurance Underwriter synthetic dataset."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import os
import json
from typing import Optional

# Get API base URL and token from environment
API_BASE = os.getenv("NEX_COLLECTOR_API_BASE", os.getenv("API_BASE", "http://api:8080"))
API_TOKEN = os.getenv("NEX_WRITE_TOKEN", "dev-secret")


def create_insurance_dataset():
    """Create a synthetic dataset for insurance underwriter context."""
    
    print("📊 Creating Insurance Underwriter Synthetic Dataset...")
    print(f"   API: {API_BASE}")
    
    # Step 1: Verify variant exists
    print("\n1️⃣ Verifying insurance underwriter variant exists...")
    variant_id = "var-insurance-underwriter-risk-assessment"
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            f"{API_BASE}/v1/contexts/variants/{variant_id}",
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        if resp.status_code != 200:
            print(f"   ❌ Variant {variant_id} not found!")
            print(f"      Please run seed_insurance_underwriter.py first")
            sys.exit(1)
        
        variant_data = resp.json()
        print(f"   ✓ Found variant: {variant_data['id']}")
        print(f"      Domain: {variant_data['domain']}, Persona: {variant_data['persona']}")
    
    # Step 2: Generate synthetic examples using the API
    print("\n2️⃣ Generating synthetic examples via API...")
    
    example_ids = []
    with httpx.Client(timeout=60.0) as client:
        # Generate task examples (5 examples)
        payload = {
            "variant_ids": [variant_id],
            "example_type": "task",
            "quota_per_variant": 5,
            "rules": {}
        }
        
        resp = client.post(
            f"{API_BASE}/v1/datasets/distill/examples",
            json=payload,
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if resp.status_code == 201:
            result = resp.json()
            task_ids = result.get("example_ids", [])
            example_ids.extend(task_ids)
            print(f"   ✓ Generated {len(task_ids)} task examples")
        else:
            print(f"   ⚠️  Failed to generate task examples: {resp.status_code}")
            print(f"      {resp.text}")
        
        # Generate QA examples (3 examples)
        payload["example_type"] = "qa"
        payload["quota_per_variant"] = 3
        
        resp = client.post(
            f"{API_BASE}/v1/datasets/distill/examples",
            json=payload,
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if resp.status_code == 201:
            result = resp.json()
            qa_ids = result.get("example_ids", [])
            example_ids.extend(qa_ids)
            print(f"   ✓ Generated {len(qa_ids)} QA examples")
        
        # Generate instruction examples (2 examples)
        payload["example_type"] = "instruction"
        payload["quota_per_variant"] = 2
        
        resp = client.post(
            f"{API_BASE}/v1/datasets/distill/examples",
            json=payload,
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        if resp.status_code == 201:
            result = resp.json()
            inst_ids = result.get("example_ids", [])
            example_ids.extend(inst_ids)
            print(f"   ✓ Generated {len(inst_ids)} instruction examples")
    
    print(f"\n   ✓ Total examples created: {len(example_ids)}")
    
    # Step 3: Build dataset/fine-tune pack
    print("\n3️⃣ Building fine-tune pack dataset...")
    
    dataset_id = "ds-insurance-underwriter-v1"
    dataset_name = "insurance-underwriter-risk-assessment"
    dataset_version = "1.0.0"
    
    with httpx.Client(timeout=120.0) as client:
        payload = {
            "dataset_id": dataset_id,
            "name": dataset_name,
            "version": dataset_version,
            "kind": "finetune_pack",
            "variant_ids": [variant_id],
            "filters": {
                "has_teacher_output": False  # We'll add teacher runs later if needed
            }
        }
        
        resp = client.post(
            f"{API_BASE}/v1/datasets/distill/build",
            json=payload,
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        
        resp.raise_for_status()
        result = resp.json()
        dataset_id = result.get('dataset_id', dataset_id)
        manifest = result.get('manifest', {})
        print(f"   ✓ Dataset built successfully!")
        print(f"      Dataset ID: {dataset_id}")
        print(f"      Files: {len(manifest.get('files', []))}")
        for file_info in manifest.get('files', []):
            print(f"        - {file_info.get('name')}: {file_info.get('size', 0)} bytes")
        print(f"      Examples: {manifest.get('num_examples', 0)}")
        print(f"      Train: {manifest.get('train_size', 0)}, Eval: {manifest.get('eval_size', 0)}")
    
    # Step 4: Summary
    print("\n✅ Insurance Underwriter synthetic dataset created successfully!")
    print(f"\n📊 Summary:")
    print(f"   - Variant: {variant_id}")
    print(f"   - Examples: {len(example_ids)}")
    print(f"   - Dataset: {dataset_id} ({dataset_name}@{dataset_version})")
    print(f"\n📁 Dataset files:")
    print(f"   - Location: nex-collector/data/packs/{dataset_name}@{dataset_version}/")
    print(f"\n🔍 View dataset:")
    print(f"   GET {API_BASE}/v1/datasets/{dataset_id}")


if __name__ == "__main__":
    try:
        create_insurance_dataset()
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

