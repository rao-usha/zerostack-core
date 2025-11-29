#!/usr/bin/env python3
"""Load existing data packs into the main NEX database."""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, 'backend')

from sqlalchemy.orm import Session
from db import SessionLocal
from models import DatasetManifest, DatasetKind


def load_existing_packs():
    """Load existing data pack manifests into the main NEX database."""
    db: Session = SessionLocal()

    try:
        packs_dir = Path('nex-collector/data/packs')
        print(f'Loading data packs from {packs_dir}')

        for pack_dir in packs_dir.iterdir():
            if pack_dir.is_dir():
                manifest_file = pack_dir / 'manifest.json'
                if manifest_file.exists():
                    print(f'Loading {pack_dir.name}...')
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)

                    # Check if already exists
                    existing = db.query(DatasetManifest).filter(
                        DatasetManifest.id == manifest['id']
                    ).first()

                    if existing:
                        print(f'  Dataset {manifest["id"]} already exists, skipping')
                        continue

                    # Create DatasetManifest in main database
                    dataset = DatasetManifest(
                        id=manifest['id'],
                        name=manifest['name'],
                        version=manifest['version'],
                        kind=DatasetKind(manifest['kind']),
                        variant_ids=manifest['variant_ids'],
                        file_uris=[f['path'].replace('/code/', '') for f in manifest['files']],
                        filters_json=manifest.get('filters', {})
                    )
                    db.add(dataset)
                    print(f'  Added dataset: {dataset.id}')

        db.commit()
        print('All data packs loaded successfully into main database!')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    load_existing_packs()
