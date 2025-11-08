"""Dataset routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..distill.sampler import ExampleSampler
from ..distill.builder import build_dataset
import uuid


router = APIRouter(prefix="/v1/datasets", tags=["datasets"])


@router.post("/distill/examples", status_code=201)
def distill_examples(
    payload: schemas.DistillExamplesRequest,
    db: Session = Depends(get_db)
):
    """Generate synthetic examples from variants."""
    # Validate variants exist
    variants = db.query(models.ContextVariant).filter(
        models.ContextVariant.id.in_(payload.variant_ids)
    ).all()
    if len(variants) != len(payload.variant_ids):
        raise HTTPException(status_code=404, detail="Some variants not found")
    
    # Sample examples
    sampler = ExampleSampler()
    # Convert schema enum to model enum
    model_example_type = models.ExampleType(payload.example_type.value)
    example_ids = sampler.sample(
        db,
        payload.variant_ids,
        model_example_type,
        payload.quota_per_variant,
        payload.rules
    )
    
    return {
        "example_ids": example_ids,
        "count": len(example_ids)
    }


@router.post("/distill/build", status_code=202)
def build_dataset_endpoint(
    payload: schemas.DistillBuildRequest,
    db: Session = Depends(get_db)
):
    """Build a dataset from examples."""
    # Validate variants exist
    variants = db.query(models.ContextVariant).filter(
        models.ContextVariant.id.in_(payload.variant_ids)
    ).all()
    if len(variants) != len(payload.variant_ids):
        raise HTTPException(status_code=404, detail="Some variants not found")
    
    # Generate dataset ID
    dataset_id = f"ds-{uuid.uuid4().hex[:12]}"
    
    # Build dataset
    try:
        manifest = build_dataset(
            db,
            dataset_id,
            payload.name,
            payload.version,
            models.DatasetKind(payload.kind.value),
            payload.variant_ids,
            payload.filters
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Save manifest to DB
    obj = models.DatasetManifest(
        id=dataset_id,
        name=payload.name,
        version=payload.version,
        kind=models.DatasetKind(payload.kind.value),
        context_id=variants[0].context_id if variants else None,
        variant_ids=payload.variant_ids,
        file_uris=[f["path"] for f in manifest.get("files", [])],
        filters_json=payload.filters
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    
    return {
        "dataset_id": dataset_id,
        "manifest": manifest,
        "status": "built"
    }


@router.get("", response_model=list[schemas.DatasetManifestResponse])
def list_datasets(
    db: Session = Depends(get_db)
):
    """List all dataset manifests."""
    manifests = db.query(models.DatasetManifest).all()
    return manifests


@router.get("/{dataset_id}", response_model=schemas.DatasetManifestResponse)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Get a dataset manifest by ID."""
    manifest = db.query(models.DatasetManifest).filter(
        models.DatasetManifest.id == dataset_id
    ).first()
    if not manifest:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return manifest
