#!/usr/bin/env python3
"""Seed nex-collector database with existing data packs."""

import json
import os
import sys
from pathlib import Path

# Set environment variables for nex-collector
os.environ['DATABASE_URL'] = 'postgresql+psycopg://nex:nex@nex_db_dev:5432/nex_collector'
os.environ['OPENAI_API_KEY'] = 'dummy-key'  # Won't use OpenAI for seeding

# Add nex-collector to path
sys.path.insert(0, 'nex-collector')

from sqlalchemy.orm import Session
from nex_collector.app.db import SessionLocal
from nex_collector.app.models import ContextDoc, ContextVariant, DatasetManifest, DatasetKind

def seed_nex_collector():
    """Seed the nex-collector database with data from existing packs."""
    db: Session = SessionLocal()

    try:
        print("🌱 Seeding nex-collector database...")

        # Load data packs
        packs_dir = Path('nex-collector/data/packs')

        for pack_dir in packs_dir.iterdir():
            if pack_dir.is_dir() and pack_dir.name.endswith('@1.0.0'):
                print(f"\n📦 Processing {pack_dir.name}")

                # Load manifest
                manifest_file = pack_dir / 'manifest.json'
                if not manifest_file.exists():
                    print(f"  ❌ No manifest.json in {pack_dir.name}")
                    continue

                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)

                print(f"  ✓ Loaded manifest for {manifest['name']}")

                # Create DatasetManifest if it doesn't exist
                existing_dataset = db.query(DatasetManifest).filter(
                    DatasetManifest.id == manifest['id']
                ).first()

                if existing_dataset:
                    print(f"  ℹ️ Dataset {manifest['id']} already exists")
                else:
                    dataset = DatasetManifest(
                        id=manifest['id'],
                        name=manifest['name'],
                        version=manifest['version'],
                        kind=DatasetKind(manifest['kind']),
                        variant_ids=manifest['variant_ids'],
                        file_uris=[f"/code/data/packs/{pack_dir.name}/{f['name']}" for f in manifest['files']],
                        filters_json=manifest.get('filters', {})
                    )
                    db.add(dataset)
                    print(f"  ✓ Created dataset: {dataset.id}")

                # Create basic ContextDoc and ContextVariant if they don't exist
                for variant_id in manifest['variant_ids']:
                    # Create a basic context doc
                    context_id = f"ctx-{manifest['name'].lower().replace(' ', '-')}"
                    existing_context = db.query(ContextDoc).filter(
                        ContextDoc.id == context_id
                    ).first()

                    if not existing_context:
                        context = ContextDoc(
                            id=context_id,
                            title=f"{manifest['name']} Context",
                            version="1.0.0",
                            body_text=f"Context for {manifest['name']} domain. Generated automatically.",
                            metadata_json={"auto_generated": True, "source": "data_pack"}
                        )
                        db.add(context)
                        print(f"  ✓ Created context: {context_id}")

                    # Create a basic variant
                    existing_variant = db.query(ContextVariant).filter(
                        ContextVariant.id == variant_id
                    ).first()

                    if not existing_variant:
                        variant = ContextVariant(
                            id=variant_id,
                            context_id=context_id,
                            domain=manifest['name'].split()[0].lower(),
                            persona="assistant",
                            task="general",
                            style="professional",
                            constraints_json={},
                            body_text=f"Variant for {manifest['name']} domain."
                        )
                        db.add(variant)
                        print(f"  ✓ Created variant: {variant_id}")

        db.commit()
        print("\n✅ Successfully seeded nex-collector database!")

        # Verify what was created
        contexts = db.query(ContextDoc).count()
        variants = db.query(ContextVariant).count()
        datasets = db.query(DatasetManifest).count()

        print("
📊 Database Summary:"        print(f"   Contexts: {contexts}")
        print(f"   Variants: {variants}")
        print(f"   Datasets: {datasets}")

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_nex_collector()
