"""ML Model Development service layer."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, insert, update, delete, desc
from sqlalchemy.engine import Engine
from uuid import uuid4

from db.models import (
    ml_recipe, ml_recipe_version, ml_model, ml_run,
    ml_monitor_snapshot, ml_synthetic_example
)
from domains.ml_development.models import (
    ModelFamily, RecipeLevel, RecipeStatus, ModelStatus, RunStatus, RunType
)


class MLRecipeService:
    """Service for ML recipe operations."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def list_recipes(
        self,
        model_family: Optional[str] = None,
        level: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List ML recipes with filters."""
        with self.engine.connect() as conn:
            query = select(ml_recipe)
            
            if model_family:
                query = query.where(ml_recipe.c.model_family == model_family)
            if level:
                query = query.where(ml_recipe.c.level == level)
            if status:
                query = query.where(ml_recipe.c.status == status)
            
            query = query.order_by(desc(ml_recipe.c.updated_at)).limit(limit).offset(offset)
            
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get a recipe by ID."""
        with self.engine.connect() as conn:
            query = select(ml_recipe).where(ml_recipe.c.id == recipe_id)
            result = conn.execute(query).fetchone()
            return dict(result._mapping) if result else None
    
    def create_recipe(
        self,
        recipe_id: str,
        name: str,
        model_family: str,
        level: str,
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new ML recipe."""
        with self.engine.begin() as conn:
            stmt = insert(ml_recipe).values(
                id=recipe_id,
                name=name,
                model_family=model_family,
                level=level,
                status="draft",
                parent_id=parent_id,
                tags=tags or [],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            conn.execute(stmt)
            return self.get_recipe(recipe_id)
    
    def update_recipe(
        self,
        recipe_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update a recipe."""
        with self.engine.begin() as conn:
            values = {"updated_at": datetime.utcnow()}
            if name is not None:
                values["name"] = name
            if status is not None:
                values["status"] = status
            if tags is not None:
                values["tags"] = tags
            
            stmt = update(ml_recipe).where(ml_recipe.c.id == recipe_id).values(**values)
            conn.execute(stmt)
            return self.get_recipe(recipe_id)
    
    def delete_recipe(self, recipe_id: str) -> bool:
        """Delete a recipe."""
        with self.engine.begin() as conn:
            stmt = delete(ml_recipe).where(ml_recipe.c.id == recipe_id)
            result = conn.execute(stmt)
            return result.rowcount > 0


class MLRecipeVersionService:
    """Service for ML recipe version operations."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def list_versions(self, recipe_id: str) -> List[Dict[str, Any]]:
        """List all versions for a recipe."""
        with self.engine.connect() as conn:
            query = select(ml_recipe_version).where(
                ml_recipe_version.c.recipe_id == recipe_id
            ).order_by(desc(ml_recipe_version.c.created_at))
            
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific version."""
        with self.engine.connect() as conn:
            query = select(ml_recipe_version).where(ml_recipe_version.c.version_id == version_id)
            result = conn.execute(query).fetchone()
            return dict(result._mapping) if result else None
    
    def create_version(
        self,
        version_id: str,
        recipe_id: str,
        version_number: str,
        manifest_json: Dict[str, Any],
        created_by: Optional[str] = None,
        change_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new recipe version."""
        with self.engine.begin() as conn:
            stmt = insert(ml_recipe_version).values(
                version_id=version_id,
                recipe_id=recipe_id,
                version_number=version_number,
                manifest_json=manifest_json,
                created_by=created_by,
                created_at=datetime.utcnow(),
                change_note=change_note
            )
            conn.execute(stmt)
            return self.get_version(version_id)


class MLModelService:
    """Service for ML model operations."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def list_models(
        self,
        model_family: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List ML models with filters."""
        with self.engine.connect() as conn:
            query = select(ml_model)
            
            if model_family:
                query = query.where(ml_model.c.model_family == model_family)
            if status:
                query = query.where(ml_model.c.status == status)
            
            query = query.order_by(desc(ml_model.c.updated_at)).limit(limit).offset(offset)
            
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a model by ID."""
        with self.engine.connect() as conn:
            query = select(ml_model).where(ml_model.c.id == model_id)
            result = conn.execute(query).fetchone()
            return dict(result._mapping) if result else None
    
    def create_model(
        self,
        model_id: str,
        name: str,
        model_family: str,
        recipe_id: str,
        recipe_version_id: str,
        owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new ML model."""
        with self.engine.begin() as conn:
            stmt = insert(ml_model).values(
                id=model_id,
                name=name,
                model_family=model_family,
                recipe_id=recipe_id,
                recipe_version_id=recipe_version_id,
                status="draft",
                owner=owner,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            conn.execute(stmt)
            return self.get_model(model_id)
    
    def update_model(
        self,
        model_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        owner: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update a model."""
        with self.engine.begin() as conn:
            values = {"updated_at": datetime.utcnow()}
            if name is not None:
                values["name"] = name
            if status is not None:
                values["status"] = status
            if owner is not None:
                values["owner"] = owner
            
            stmt = update(ml_model).where(ml_model.c.id == model_id).values(**values)
            conn.execute(stmt)
            return self.get_model(model_id)


class MLRunService:
    """Service for ML run operations."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def list_runs(
        self,
        model_id: Optional[str] = None,
        recipe_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List ML runs with filters."""
        with self.engine.connect() as conn:
            query = select(ml_run)
            
            if model_id:
                query = query.where(ml_run.c.model_id == model_id)
            if recipe_id:
                query = query.where(ml_run.c.recipe_id == recipe_id)
            if status:
                query = query.where(ml_run.c.status == status)
            
            query = query.order_by(desc(ml_run.c.started_at)).limit(limit).offset(offset)
            
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a run by ID."""
        with self.engine.connect() as conn:
            query = select(ml_run).where(ml_run.c.id == run_id)
            result = conn.execute(query).fetchone()
            return dict(result._mapping) if result else None
    
    def create_run(
        self,
        run_id: str,
        recipe_id: str,
        recipe_version_id: str,
        run_type: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new ML run."""
        with self.engine.begin() as conn:
            stmt = insert(ml_run).values(
                id=run_id,
                model_id=model_id,
                recipe_id=recipe_id,
                recipe_version_id=recipe_version_id,
                run_type=run_type,
                status="queued",
                started_at=None,
                finished_at=None,
                metrics_json={},
                artifacts_json={},
                logs_text=None
            )
            conn.execute(stmt)
            return self.get_run(run_id)
    
    def update_run(
        self,
        run_id: str,
        status: Optional[str] = None,
        metrics_json: Optional[Dict[str, Any]] = None,
        artifacts_json: Optional[Dict[str, Any]] = None,
        logs_text: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update a run."""
        with self.engine.begin() as conn:
            values = {}
            if status is not None:
                values["status"] = status
                if status == "running" and not values.get("started_at"):
                    values["started_at"] = datetime.utcnow()
                elif status in ["succeeded", "failed"]:
                    values["finished_at"] = datetime.utcnow()
            if metrics_json is not None:
                values["metrics_json"] = metrics_json
            if artifacts_json is not None:
                values["artifacts_json"] = artifacts_json
            if logs_text is not None:
                values["logs_text"] = logs_text
            
            stmt = update(ml_run).where(ml_run.c.id == run_id).values(**values)
            conn.execute(stmt)
            return self.get_run(run_id)


class MLMonitorService:
    """Service for ML monitoring operations."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def list_snapshots(
        self,
        model_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List monitoring snapshots for a model."""
        with self.engine.connect() as conn:
            query = select(ml_monitor_snapshot).where(
                ml_monitor_snapshot.c.model_id == model_id
            ).order_by(desc(ml_monitor_snapshot.c.captured_at)).limit(limit).offset(offset)
            
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get a monitoring snapshot by ID."""
        with self.engine.connect() as conn:
            query = select(ml_monitor_snapshot).where(ml_monitor_snapshot.c.id == snapshot_id)
            result = conn.execute(query).fetchone()
            return dict(result._mapping) if result else None
    
    def create_snapshot(
        self,
        snapshot_id: str,
        model_id: str,
        performance_metrics_json: Dict[str, Any],
        drift_metrics_json: Dict[str, Any],
        data_freshness_json: Dict[str, Any],
        alerts_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a monitoring snapshot."""
        with self.engine.begin() as conn:
            stmt = insert(ml_monitor_snapshot).values(
                id=snapshot_id,
                model_id=model_id,
                captured_at=datetime.utcnow(),
                performance_metrics_json=performance_metrics_json,
                drift_metrics_json=drift_metrics_json,
                data_freshness_json=data_freshness_json,
                alerts_json=alerts_json
            )
            conn.execute(stmt)
            return self.get_snapshot(snapshot_id)


class MLSyntheticExampleService:
    """Service for ML synthetic example operations."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def get_example(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get synthetic example for a recipe."""
        with self.engine.connect() as conn:
            query = select(ml_synthetic_example).where(
                ml_synthetic_example.c.recipe_id == recipe_id
            )
            result = conn.execute(query).fetchone()
            return dict(result._mapping) if result else None
    
    def create_example(
        self,
        example_id: str,
        recipe_id: str,
        dataset_schema_json: Dict[str, Any],
        sample_rows_json: List[Dict[str, Any]],
        example_run_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a synthetic example."""
        with self.engine.begin() as conn:
            stmt = insert(ml_synthetic_example).values(
                id=example_id,
                recipe_id=recipe_id,
                dataset_schema_json=dataset_schema_json,
                sample_rows_json=sample_rows_json,
                example_run_json=example_run_json,
                created_at=datetime.utcnow()
            )
            conn.execute(stmt)
            return self.get_example(recipe_id)


