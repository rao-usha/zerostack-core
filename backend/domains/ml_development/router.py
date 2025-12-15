"""ML Model Development API router."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import uuid4
from sqlalchemy import create_engine

from core.config import settings
from domains.ml_development.models import (
    MLRecipe, MLRecipeCreate, MLRecipeUpdate,
    MLRecipeVersion, MLRecipeVersionCreate,
    MLModel, MLModelCreate, MLModelUpdate,
    MLRun, MLRunCreate,
    MLMonitorSnapshot, MLMonitorSnapshotCreate,
    MLSyntheticExample, MLSyntheticExampleCreate,
    RecipeListResponse, ModelListResponse, RunListResponse,
    MLChatRequest, MLChatResponse,
    ModelFamily, RecipeLevel, RecipeStatus, ModelStatus, RunStatus
)
from domains.ml_development.service import (
    MLRecipeService, MLRecipeVersionService, MLModelService,
    MLRunService, MLMonitorService, MLSyntheticExampleService
)

router = APIRouter(prefix="/ml-development", tags=["ml-development"])

# Initialize services
engine = create_engine(settings.database_url)
recipe_service = MLRecipeService(engine)
version_service = MLRecipeVersionService(engine)
model_service = MLModelService(engine)
run_service = MLRunService(engine)
monitor_service = MLMonitorService(engine)
example_service = MLSyntheticExampleService(engine)


# Recipe endpoints
@router.get("/recipes", response_model=RecipeListResponse)
async def list_recipes(
    model_family: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """List ML recipes with optional filters."""
    recipes = recipe_service.list_recipes(
        model_family=model_family,
        level=level,
        status=status,
        limit=limit,
        offset=offset
    )
    return RecipeListResponse(recipes=recipes, total=len(recipes))


@router.get("/recipes/{recipe_id}", response_model=MLRecipe)
async def get_recipe(recipe_id: str):
    """Get a specific recipe."""
    recipe = recipe_service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/recipes", response_model=MLRecipe, status_code=201)
async def create_recipe(request: MLRecipeCreate):
    """Create a new ML recipe."""
    recipe_id = f"recipe_{uuid4().hex[:12]}"
    
    # Create recipe
    recipe = recipe_service.create_recipe(
        recipe_id=recipe_id,
        name=request.name,
        model_family=request.model_family.value,
        level=request.level.value,
        parent_id=request.parent_id,
        tags=request.tags
    )
    
    # Create initial version
    version_id = f"ver_{uuid4().hex[:12]}"
    version_number = "1.0.0"
    version_service.create_version(
        version_id=version_id,
        recipe_id=recipe_id,
        version_number=version_number,
        manifest_json=request.manifest,
        change_note="Initial version"
    )
    
    return recipe


@router.put("/recipes/{recipe_id}", response_model=MLRecipe)
async def update_recipe(recipe_id: str, request: MLRecipeUpdate):
    """Update a recipe."""
    recipe = recipe_service.update_recipe(
        recipe_id=recipe_id,
        name=request.name,
        status=request.status.value if request.status else None,
        tags=request.tags
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.delete("/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str):
    """Delete a recipe."""
    success = recipe_service.delete_recipe(recipe_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recipe not found")


@router.post("/recipes/{recipe_id}/clone", response_model=MLRecipe, status_code=201)
async def clone_recipe(recipe_id: str, name: str):
    """Clone a recipe to create a derived version."""
    # Get parent recipe
    parent = recipe_service.get_recipe(recipe_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent recipe not found")
    
    # Get latest version of parent
    versions = version_service.list_versions(recipe_id)
    if not versions:
        raise HTTPException(status_code=404, detail="No versions found for parent recipe")
    latest_version = versions[0]
    
    # Create new recipe as child
    new_recipe_id = f"recipe_{uuid4().hex[:12]}"
    recipe = recipe_service.create_recipe(
        recipe_id=new_recipe_id,
        name=name,
        model_family=parent["model_family"],
        level=parent["level"],
        parent_id=recipe_id,
        tags=parent.get("tags", [])
    )
    
    # Create initial version with parent's manifest
    version_id = f"ver_{uuid4().hex[:12]}"
    version_service.create_version(
        version_id=version_id,
        recipe_id=new_recipe_id,
        version_number="1.0.0",
        manifest_json=latest_version["manifest_json"],
        change_note=f"Cloned from {parent['name']}"
    )
    
    return recipe


# Recipe Version endpoints
@router.get("/recipes/{recipe_id}/versions", response_model=List[MLRecipeVersion])
async def list_recipe_versions(recipe_id: str):
    """List all versions for a recipe."""
    versions = version_service.list_versions(recipe_id)
    return versions


@router.get("/recipes/{recipe_id}/versions/{version_id}", response_model=MLRecipeVersion)
async def get_recipe_version(recipe_id: str, version_id: str):
    """Get a specific recipe version."""
    version = version_service.get_version(version_id)
    if not version or version["recipe_id"] != recipe_id:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/recipes/{recipe_id}/versions", response_model=MLRecipeVersion, status_code=201)
async def create_recipe_version(recipe_id: str, request: MLRecipeVersionCreate):
    """Create a new version of a recipe."""
    # Verify recipe exists
    recipe = recipe_service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Get existing versions to determine version number
    versions = version_service.list_versions(recipe_id)
    version_number = f"1.{len(versions)}.0"
    
    version_id = f"ver_{uuid4().hex[:12]}"
    version = version_service.create_version(
        version_id=version_id,
        recipe_id=recipe_id,
        version_number=version_number,
        manifest_json=request.manifest_json,
        created_by=request.created_by,
        change_note=request.change_note
    )
    
    return version


# Model endpoints
@router.get("/models", response_model=ModelListResponse)
async def list_models(
    model_family: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """List ML models with optional filters."""
    models = model_service.list_models(
        model_family=model_family,
        status=status,
        limit=limit,
        offset=offset
    )
    return ModelListResponse(models=models, total=len(models))


@router.get("/models/{model_id}", response_model=MLModel)
async def get_model(model_id: str):
    """Get a specific model."""
    model = model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models", response_model=MLModel, status_code=201)
async def create_model(request: MLModelCreate):
    """Register a new ML model."""
    # Verify recipe and version exist
    recipe = recipe_service.get_recipe(request.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    version = version_service.get_version(request.recipe_version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Recipe version not found")
    
    model_id = f"model_{uuid4().hex[:12]}"
    model = model_service.create_model(
        model_id=model_id,
        name=request.name,
        model_family=recipe["model_family"],
        recipe_id=request.recipe_id,
        recipe_version_id=request.recipe_version_id,
        owner=request.owner
    )
    
    return model


@router.put("/models/{model_id}", response_model=MLModel)
async def update_model(model_id: str, request: MLModelUpdate):
    """Update a model."""
    model = model_service.update_model(
        model_id=model_id,
        name=request.name,
        status=request.status.value if request.status else None,
        owner=request.owner
    )
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


# Run endpoints
@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    model_id: Optional[str] = Query(None),
    recipe_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """List ML runs with optional filters."""
    runs = run_service.list_runs(
        model_id=model_id,
        recipe_id=recipe_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return RunListResponse(runs=runs, total=len(runs))


@router.get("/runs/{run_id}", response_model=MLRun)
async def get_run(run_id: str):
    """Get a specific run."""
    run = run_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/runs", response_model=MLRun, status_code=201)
async def create_run(request: MLRunCreate):
    """Create a new ML run (training/evaluation)."""
    # Verify recipe and version exist
    recipe = recipe_service.get_recipe(request.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    version = version_service.get_version(request.recipe_version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Recipe version not found")
    
    # If model_id provided, verify it exists
    if request.model_id:
        model = model_service.get_model(request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
    
    run_id = f"run_{uuid4().hex[:12]}"
    run = run_service.create_run(
        run_id=run_id,
        recipe_id=request.recipe_id,
        recipe_version_id=request.recipe_version_id,
        run_type=request.run_type.value,
        model_id=request.model_id
    )
    
    return run


@router.put("/runs/{run_id}", response_model=MLRun)
async def update_run(
    run_id: str,
    status: Optional[str] = None,
    metrics_json: Optional[dict] = None,
    artifacts_json: Optional[dict] = None,
    logs_text: Optional[str] = None
):
    """Update a run's status, metrics, or logs."""
    run = run_service.update_run(
        run_id=run_id,
        status=status,
        metrics_json=metrics_json,
        artifacts_json=artifacts_json,
        logs_text=logs_text
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# Monitoring endpoints
@router.get("/models/{model_id}/monitoring", response_model=List[MLMonitorSnapshot])
async def list_monitoring_snapshots(
    model_id: str,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """List monitoring snapshots for a model."""
    snapshots = monitor_service.list_snapshots(
        model_id=model_id,
        limit=limit,
        offset=offset
    )
    return snapshots


@router.post("/models/{model_id}/monitoring", response_model=MLMonitorSnapshot, status_code=201)
async def create_monitoring_snapshot(model_id: str, request: MLMonitorSnapshotCreate):
    """Create a monitoring snapshot for a model."""
    # Verify model exists
    model = model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    snapshot_id = f"snap_{uuid4().hex[:12]}"
    snapshot = monitor_service.create_snapshot(
        snapshot_id=snapshot_id,
        model_id=model_id,
        performance_metrics_json=request.performance_metrics_json,
        drift_metrics_json=request.drift_metrics_json,
        data_freshness_json=request.data_freshness_json,
        alerts_json=request.alerts_json
    )
    
    return snapshot


# Synthetic Example endpoints
@router.get("/recipes/{recipe_id}/synthetic-example", response_model=MLSyntheticExample)
async def get_synthetic_example(recipe_id: str):
    """Get synthetic example for a recipe."""
    example = example_service.get_example(recipe_id)
    if not example:
        raise HTTPException(status_code=404, detail="Synthetic example not found")
    return example


@router.post("/recipes/{recipe_id}/synthetic-example", response_model=MLSyntheticExample, status_code=201)
async def create_synthetic_example(recipe_id: str, request: MLSyntheticExampleCreate):
    """Create a synthetic example for a recipe."""
    # Verify recipe exists
    recipe = recipe_service.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    example_id = f"example_{uuid4().hex[:12]}"
    example = example_service.create_example(
        example_id=example_id,
        recipe_id=recipe_id,
        dataset_schema_json=request.dataset_schema_json,
        sample_rows_json=request.sample_rows_json,
        example_run_json=request.example_run_json
    )
    
    return example


# Chat assistant endpoint
@router.post("/chat", response_model=MLChatResponse)
async def ml_chat(request: MLChatRequest):
    """Chat with ML recipe assistant using real LLM providers."""
    from llm.providers import get_provider
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get LLM provider
        provider = get_provider(request.provider, request.model)
        
        # Build system message for ML recipe assistant
        system_message = """You are an expert ML engineer and data scientist specializing in building machine learning recipes for production systems. 

Your expertise includes:
- Pricing models (price optimization, elasticity, margin/revenue optimization)
- Forecasting models (time series, ARIMA, Prophet, demand forecasting)
- Next Best Action (NBA) models (recommendation engines, uplift modeling, propensity)
- Location Scoring models (site selection, trade area analysis, demographic modeling)

You help users:
1. Choose the right model family for their use case
2. Design ML recipes (manifests) with proper feature requirements, pipeline stages, evaluation metrics, and monitoring
3. Suggest appropriate algorithms and hyperparameters
4. Define metrics and thresholds
5. Set up monitoring for drift, freshness, and performance

Always provide specific, actionable advice. When suggesting recipes, describe the key components:
- Required and optional feature sets
- Pipeline stages (quality, feature_prep, training, evaluation, deployment)
- Evaluation metrics with target thresholds
- Monitoring setup (drift detection, freshness checks, alerts)

Be concise but thorough. Use technical terminology where appropriate."""
        
        # Add context if recipe_id is provided
        context_info = ""
        if request.recipe_id:
            recipe = recipe_service.get_recipe(request.recipe_id)
            if recipe:
                context_info = f"\n\nCurrent recipe context: Working with '{recipe['name']}' ({recipe['model_family']} model, {recipe['level']} level)"
        
        # Build messages
        messages = [
            {"role": "system", "content": system_message + context_info},
            {"role": "user", "content": request.message}
        ]
        
        # Stream and collect response
        full_response = ""
        async for event in provider.stream_chat(
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        ):
            if event["type"] == "delta":
                full_response += event["content"]
            elif event["type"] == "error":
                raise Exception(f"LLM error: {event['error']}")
        
        return MLChatResponse(
            message=full_response,
            suggested_changes=None,
            timestamp=datetime.utcnow()
        )
    
    except ValueError as e:
        # Handle missing API keys gracefully
        error_message = str(e)
        if "not found" in error_message.lower():
            return MLChatResponse(
                message=f"⚠️ Configuration Error: {error_message}\n\nPlease configure the appropriate API key in your environment to use this provider.",
                suggested_changes=None,
                timestamp=datetime.utcnow()
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ML chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


