"""Dataset API router."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from uuid import UUID
from domains.datasets.models import (
    Dataset, DatasetCreate, Transform, SyntheticDataRequest, SyntheticDataResult,
    DatasetStatus
)
from domains.datasets.service import DatasetRegistry, TransformService, SyntheticDataService

router = APIRouter(prefix="/datasets", tags=["datasets"])

dataset_registry = DatasetRegistry()
transform_service = TransformService()
synthetic_data_service = SyntheticDataService()


@router.post("", response_model=Dataset, status_code=201)
async def create_dataset(dataset: DatasetCreate):
    """Create a new dataset."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/upload", status_code=201)
async def upload_dataset(
    name: str = Form(...),
    org_id: str = Form("demo"),
    file: UploadFile = File(...)
):
    """
    Upload a dataset file.
    
    TODO: stream to ObjectStore, compute sha256, basic sniff for schema
    """
    return {
        "dataset": {"name": name, "org_id": org_id},
        "version": {"id": "dv_stub", "sha256": "stub", "path": f"/objects/{name}"},
        "status": "stub"
    }


@router.get("/{dataset_id}/versions")
def list_versions(dataset_id: str):
    """List versions for a dataset."""
    return {"dataset_id": dataset_id, "versions": []}


@router.get("", response_model=List[Dataset])
async def list_datasets(status: Optional[DatasetStatus] = None):
    """List datasets."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{dataset_id}", response_model=Dataset)
async def get_dataset(dataset_id: UUID):
    """Get a dataset."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{dataset_id}", response_model=Dataset)
async def update_dataset(dataset_id: UUID, update: dict):
    """Update a dataset."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: UUID):
    """Delete a dataset."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{dataset_id}/transforms", response_model=Transform, status_code=201)
async def create_transform(
    dataset_id: UUID,
    name: str,
    transform_type: str,
    config: dict
):
    """Create a transform."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{dataset_id}/transforms", response_model=List[Transform])
async def list_transforms(dataset_id: UUID):
    """List transforms for a dataset."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/synthetic/generate", response_model=SyntheticDataResult, status_code=201)
async def generate_synthetic_data(request: SyntheticDataRequest):
    """Generate synthetic data."""
    raise HTTPException(status_code=501, detail="Not implemented")

