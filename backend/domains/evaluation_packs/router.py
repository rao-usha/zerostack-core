"""API router for Evaluation Packs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection
from typing import Optional

from db.connection import get_db_connection
from .models import (
    EvaluationPack, EvaluationPackCreate, EvaluationPackUpdate,
    EvaluationPackVersion, EvaluationPackVersionCreate,
    EvaluationResult, EvaluationResultCreate,
    MonitorEvaluationSnapshot, MonitorEvaluationSnapshotCreate,
    RecipePackAttach,
    PackListResponse, EvaluationResultListResponse, MonitorSnapshotListResponse
)
from .service import (
    EvaluationPackService, EvaluationPackVersionService, RecipePackService,
    EvaluationExecutionService, MonitorEvaluationService
)


router = APIRouter(prefix="/evaluation-packs", tags=["evaluation-packs"])


# Evaluation Pack endpoints
@router.get("", response_model=PackListResponse)
def list_packs(
    model_family: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    conn: Connection = Depends(get_db_connection)
):
    """List evaluation packs with filters."""
    packs, total = EvaluationPackService.list_packs(
        conn, model_family=model_family, status=status, search=search, skip=skip, limit=limit
    )
    return {"packs": packs, "total": total}


@router.get("/{pack_id}", response_model=EvaluationPack)
def get_pack(pack_id: str, conn: Connection = Depends(get_db_connection)):
    """Get a single evaluation pack."""
    pack = EvaluationPackService.get_pack(conn, pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack


@router.post("", response_model=EvaluationPack)
def create_pack(pack_data: EvaluationPackCreate, conn: Connection = Depends(get_db_connection)):
    """Create a new evaluation pack."""
    pack = EvaluationPackService.create_pack(conn, pack_data)
    return pack


@router.put("/{pack_id}", response_model=EvaluationPack)
def update_pack(
    pack_id: str,
    pack_update: EvaluationPackUpdate,
    conn: Connection = Depends(get_db_connection)
):
    """Update an evaluation pack."""
    pack = EvaluationPackService.update_pack(conn, pack_id, pack_update)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack


@router.delete("/{pack_id}")
def delete_pack(pack_id: str, conn: Connection = Depends(get_db_connection)):
    """Delete an evaluation pack."""
    success = EvaluationPackService.delete_pack(conn, pack_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pack not found")
    return {"message": "Pack deleted successfully"}


@router.post("/{pack_id}/clone", response_model=EvaluationPack)
def clone_pack(
    pack_id: str,
    name: str = Query(...),
    conn: Connection = Depends(get_db_connection)
):
    """Clone an evaluation pack."""
    pack = EvaluationPackService.clone_pack(conn, pack_id, name)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack


# Pack Version endpoints
@router.get("/{pack_id}/versions", response_model=list[EvaluationPackVersion])
def list_pack_versions(pack_id: str, conn: Connection = Depends(get_db_connection)):
    """List all versions of a pack."""
    versions = EvaluationPackVersionService.list_versions(conn, pack_id)
    return versions


@router.post("/{pack_id}/versions", response_model=EvaluationPackVersion)
def create_pack_version(
    pack_id: str,
    version_data: EvaluationPackVersionCreate,
    conn: Connection = Depends(get_db_connection)
):
    """Create a new pack version."""
    if version_data.pack_id != pack_id:
        raise HTTPException(status_code=400, detail="Pack ID mismatch")
    version = EvaluationPackVersionService.create_version(conn, version_data)
    return version


# Recipe-Pack attachment endpoints
@router.post("/recipes/{recipe_id}/attach")
def attach_pack_to_recipe(
    recipe_id: str,
    attach_data: RecipePackAttach,
    conn: Connection = Depends(get_db_connection)
):
    """Attach a pack to a recipe."""
    if attach_data.recipe_id != recipe_id:
        raise HTTPException(status_code=400, detail="Recipe ID mismatch")
    success = RecipePackService.attach_pack(conn, recipe_id, attach_data.pack_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to attach pack")
    return {"message": "Pack attached successfully"}


@router.delete("/recipes/{recipe_id}/detach/{pack_id}")
def detach_pack_from_recipe(
    recipe_id: str,
    pack_id: str,
    conn: Connection = Depends(get_db_connection)
):
    """Detach a pack from a recipe."""
    success = RecipePackService.detach_pack(conn, recipe_id, pack_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"message": "Pack detached successfully"}


@router.get("/recipes/{recipe_id}/packs", response_model=list[EvaluationPack])
def list_recipe_packs(recipe_id: str, conn: Connection = Depends(get_db_connection)):
    """List all packs attached to a recipe."""
    packs = RecipePackService.list_recipe_packs(conn, recipe_id)
    return packs


# Execution endpoints
@router.post("/execute", response_model=EvaluationResult)
def execute_pack(
    exec_data: EvaluationResultCreate,
    conn: Connection = Depends(get_db_connection)
):
    """Execute an evaluation pack on a run."""
    try:
        result = EvaluationExecutionService.execute_pack_on_run(
            conn,
            exec_data.run_id,
            exec_data.pack_id,
            exec_data.pack_version_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs/{run_id}/results", response_model=EvaluationResultListResponse)
def list_run_evaluation_results(run_id: str, conn: Connection = Depends(get_db_connection)):
    """List all evaluation results for a run."""
    results = EvaluationExecutionService.list_run_results(conn, run_id)
    return {"results": results, "total": len(results)}


# Monitoring endpoints
@router.post("/monitor", response_model=MonitorEvaluationSnapshot)
def create_monitor_snapshot(
    snapshot_data: MonitorEvaluationSnapshotCreate,
    conn: Connection = Depends(get_db_connection)
):
    """Create a monitoring evaluation snapshot for a model."""
    try:
        snapshot = MonitorEvaluationService.create_snapshot(
            conn,
            snapshot_data.model_id,
            snapshot_data.pack_id,
            snapshot_data.pack_version_id
        )
        return snapshot
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models/{model_id}/snapshots", response_model=MonitorSnapshotListResponse)
def list_model_monitor_snapshots(model_id: str, conn: Connection = Depends(get_db_connection)):
    """List all monitoring snapshots for a model."""
    snapshots = MonitorEvaluationService.list_model_snapshots(conn, model_id)
    return {"snapshots": snapshots, "total": len(snapshots)}

