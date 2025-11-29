"""Data explorer routes for querying all tables."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from typing import Optional, List, Dict, Any
from ..db import get_db
from .. import models
import json


router = APIRouter(prefix="/v1/explorer", tags=["explorer"])


@router.get("/tables")
def list_tables():
    """List all available tables."""
    tables = [
        {"name": "context_docs", "model": "ContextDoc", "description": "Context documents"},
        {"name": "context_variants", "model": "ContextVariant", "description": "Context variants with facets"},
        {"name": "chunks", "model": "Chunk", "description": "Text chunks with embeddings"},
        {"name": "feature_vectors", "model": "FeatureVector", "description": "Extracted structured features"},
        {"name": "synthetic_examples", "model": "SyntheticExample", "description": "Synthetic examples"},
        {"name": "teacher_runs", "model": "TeacherRun", "description": "Teacher model outputs"},
        {"name": "targets", "model": "Targets", "description": "Distilled labels"},
        {"name": "dataset_manifests", "model": "DatasetManifest", "description": "Dataset manifests"},
        {"name": "quality_assessments", "model": "QualityAssessment", "description": "Quality assessments"},
    ]
    return {"tables": tables}


@router.get("/tables/{table_name}")
def query_table(
    table_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Query a specific table."""
    # Map table names to models
    model_map = {
        "context_docs": models.ContextDoc,
        "context_variants": models.ContextVariant,
        "chunks": models.Chunk,
        "feature_vectors": models.FeatureVector,
        "synthetic_examples": models.SyntheticExample,
        "teacher_runs": models.TeacherRun,
        "targets": models.Targets,
        "dataset_manifests": models.DatasetManifest,
        "quality_assessments": models.QualityAssessment,
    }
    
    if table_name not in model_map:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    model = model_map[table_name]
    
    # Get total count
    total = db.query(model).count()
    
    # Query with pagination
    items = db.query(model).offset(offset).limit(limit).all()
    
    # Convert to dict, handling JSON columns
    def serialize_item(item):
        result = {}
        for column in inspect(item.__class__).columns:
            value = getattr(item, column.name)
            # Handle JSON columns
            if isinstance(value, (dict, list)):
                result[column.name] = value
            # Handle datetime
            elif hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat()
            # Handle arrays
            elif isinstance(value, list):
                result[column.name] = value
            else:
                result[column.name] = value
        return result
    
    serialized_items = [serialize_item(item) for item in items]
    
    return {
        "table": table_name,
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(serialized_items),
        "data": serialized_items
    }


@router.get("/tables/{table_name}/count")
def get_table_count(
    table_name: str,
    db: Session = Depends(get_db)
):
    """Get count of records in a table."""
    model_map = {
        "context_docs": models.ContextDoc,
        "context_variants": models.ContextVariant,
        "chunks": models.Chunk,
        "feature_vectors": models.FeatureVector,
        "synthetic_examples": models.SyntheticExample,
        "teacher_runs": models.TeacherRun,
        "targets": models.Targets,
        "dataset_manifests": models.DatasetManifest,
        "quality_assessments": models.QualityAssessment,
    }
    
    if table_name not in model_map:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    model = model_map[table_name]
    count = db.query(model).count()
    
    return {"table": table_name, "count": count}

