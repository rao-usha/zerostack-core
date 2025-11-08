#!/usr/bin/env python3
"""Test script to verify the service is working."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import (
    ContextDoc, ContextVariant, 
    SyntheticExample, TeacherRun, DatasetManifest,
    Chunk, FeatureVector
)


def inspect_data():
    """Inspect all data in the database."""
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("📊 DATABASE INSPECTION")
        print("=" * 60)
        
        # ContextDocs
        contexts = db.query(ContextDoc).all()
        print(f"\n📄 ContextDocs: {len(contexts)}")
        for ctx in contexts:
            print(f"   - {ctx.id}: {ctx.title} (v{ctx.version})")
            print(f"     Created: {ctx.created_at}")
            if ctx.nex_context_id:
                print(f"     NEX Link: {ctx.nex_context_id}@{ctx.nex_context_version}")
        
        # ContextVariants
        variants = db.query(ContextVariant).all()
        print(f"\n🔀 ContextVariants: {len(variants)}")
        for var in variants:
            print(f"   - {var.id}:")
            print(f"     Domain: {var.domain}, Persona: {var.persona}, Task: {var.task}, Style: {var.style}")
            print(f"     Body length: {len(var.body_text)} chars")
            print(f"     Created: {var.created_at}")
            
            # Show feature vector
            if var.feature_vector:
                features = var.feature_vector.features_json
                print(f"     Features: {features.get('domain')}/{features.get('persona')}/{features.get('task')}")
            
            # Show chunks
            chunks = var.chunks
            if chunks:
                print(f"     Chunks: {len(chunks)}")
        
        # SyntheticExamples
        examples = db.query(SyntheticExample).all()
        print(f"\n📝 SyntheticExamples: {len(examples)}")
        for ex in examples:
            print(f"   - {ex.id}:")
            print(f"     Variant: {ex.variant_id}")
            print(f"     Type: {ex.example_type.value}")
            print(f"     Tags: {ex.tags}")
            print(f"     Created: {ex.created_at}")
            
            # Show teacher runs
            if ex.teacher_runs:
                print(f"     Teacher runs: {len(ex.teacher_runs)}")
                for tr in ex.teacher_runs:
                    if tr.output_json:
                        text = tr.output_json.get("text", "")[:50]
                        print(f"       - {tr.id}: {text}...")
        
        # TeacherRuns
        teacher_runs = db.query(TeacherRun).all()
        print(f"\n🎓 TeacherRuns: {len(teacher_runs)}")
        for tr in teacher_runs:
            print(f"   - {tr.id}:")
            print(f"     Example: {tr.example_id}")
            print(f"     Provider: {tr.provider}, Model: {tr.model}")
            if tr.output_json:
                text = tr.output_json.get("text", "")
                print(f"     Output length: {len(text)} chars")
            if tr.usage_json:
                usage = tr.usage_json
                print(f"     Tokens: {usage.get('total_tokens', 0)}")
            print(f"     Created: {tr.created_at}")
        
        # DatasetManifests
        datasets = db.query(DatasetManifest).all()
        print(f"\n📦 DatasetManifests: {len(datasets)}")
        for ds in datasets:
            print(f"   - {ds.id}: {ds.name} v{ds.version}")
            print(f"     Kind: {ds.kind.value}")
            print(f"     Variants: {len(ds.variant_ids)}")
            print(f"     Files: {len(ds.file_uris)}")
            print(f"     Created: {ds.created_at}")
            for uri in ds.file_uris[:3]:  # Show first 3
                print(f"       - {Path(uri).name}")
        
        print("\n" + "=" * 60)
        print("✅ Inspection complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error inspecting data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    inspect_data()

