"""Service layer for Evaluation Packs."""
from sqlalchemy import select, insert, update, delete, and_, func, text
from sqlalchemy.engine import Connection
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
import random

from db.models import (
    evaluation_pack, evaluation_pack_version, recipe_evaluation_pack,
    evaluation_result, monitor_evaluation_snapshot, ml_run, ml_model
)
from .models import (
    EvaluationPack, EvaluationPackCreate, EvaluationPackUpdate,
    EvaluationPackVersion, EvaluationPackVersionCreate,
    EvaluationResult, EvaluationResultCreate,
    MonitorEvaluationSnapshot, MonitorEvaluationSnapshotCreate,
    EvalStatus, MetricDefinition, MetricDirection
)


class EvaluationPackService:
    """Service for managing evaluation packs."""
    
    @staticmethod
    def list_packs(
        conn: Connection,
        model_family: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict], int]:
        """List evaluation packs with filters."""
        query = select(evaluation_pack)
        
        # Apply filters
        conditions = []
        if model_family:
            conditions.append(evaluation_pack.c.model_family == model_family)
        if status:
            conditions.append(evaluation_pack.c.status == status)
        if search:
            conditions.append(
                (evaluation_pack.c.name.ilike(f"%{search}%")) |
                (evaluation_pack.c.id.ilike(f"%{search}%"))
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(evaluation_pack)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = conn.execute(count_query).scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(evaluation_pack.c.created_at.desc())
        
        result = conn.execute(query)
        packs = [dict(row._mapping) for row in result]
        
        return packs, total
    
    @staticmethod
    def get_pack(conn: Connection, pack_id: str) -> Optional[Dict]:
        """Get a single evaluation pack."""
        query = select(evaluation_pack).where(evaluation_pack.c.id == pack_id)
        result = conn.execute(query).first()
        return dict(result._mapping) if result else None
    
    @staticmethod
    def create_pack(conn: Connection, pack_data: EvaluationPackCreate) -> Dict:
        """Create a new evaluation pack."""
        pack_id = pack_data.id or f"pack_{pack_data.model_family}_{uuid4().hex[:8]}"
        
        insert_stmt = insert(evaluation_pack).values(
            id=pack_id,
            name=pack_data.name,
            model_family=pack_data.model_family,
            status=pack_data.status,
            tags=pack_data.tags,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        conn.execute(insert_stmt)
        conn.commit()
        
        return EvaluationPackService.get_pack(conn, pack_id)
    
    @staticmethod
    def update_pack(conn: Connection, pack_id: str, pack_update: EvaluationPackUpdate) -> Optional[Dict]:
        """Update an evaluation pack."""
        update_data = {k: v for k, v in pack_update.model_dump().items() if v is not None}
        if not update_data:
            return EvaluationPackService.get_pack(conn, pack_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        update_stmt = update(evaluation_pack).where(
            evaluation_pack.c.id == pack_id
        ).values(**update_data)
        
        conn.execute(update_stmt)
        conn.commit()
        
        return EvaluationPackService.get_pack(conn, pack_id)
    
    @staticmethod
    def delete_pack(conn: Connection, pack_id: str) -> bool:
        """Delete an evaluation pack."""
        delete_stmt = delete(evaluation_pack).where(evaluation_pack.c.id == pack_id)
        result = conn.execute(delete_stmt)
        conn.commit()
        return result.rowcount > 0
    
    @staticmethod
    def clone_pack(conn: Connection, pack_id: str, new_name: str) -> Optional[Dict]:
        """Clone an evaluation pack."""
        original = EvaluationPackService.get_pack(conn, pack_id)
        if not original:
            return None
        
        # Get latest version of original
        versions = EvaluationPackVersionService.list_versions(conn, pack_id)
        if not versions:
            return None
        
        latest_version = versions[0]
        
        # Create new pack
        new_pack_id = f"pack_{original['model_family']}_{uuid4().hex[:8]}"
        insert_stmt = insert(evaluation_pack).values(
            id=new_pack_id,
            name=new_name,
            model_family=original['model_family'],
            status='draft',
            tags=original['tags'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        conn.execute(insert_stmt)
        
        # Create version for new pack
        new_version_id = f"ver_{new_pack_id}_v1"
        pack_json_dict = dict(latest_version['pack_json'])
        pack_json_dict['id'] = new_pack_id
        pack_json_dict['name'] = new_name
        
        insert_version_stmt = insert(evaluation_pack_version).values(
            version_id=new_version_id,
            pack_id=new_pack_id,
            version_number="1.0.0",
            pack_json=pack_json_dict,
            created_by="system",
            created_at=datetime.utcnow(),
            change_note=f"Cloned from {pack_id}"
        )
        conn.execute(insert_version_stmt)
        conn.commit()
        
        return EvaluationPackService.get_pack(conn, new_pack_id)


class EvaluationPackVersionService:
    """Service for managing pack versions."""
    
    @staticmethod
    def list_versions(conn: Connection, pack_id: str) -> List[Dict]:
        """List all versions of a pack."""
        query = select(evaluation_pack_version).where(
            evaluation_pack_version.c.pack_id == pack_id
        ).order_by(evaluation_pack_version.c.created_at.desc())
        
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]
    
    @staticmethod
    def get_version(conn: Connection, version_id: str) -> Optional[Dict]:
        """Get a specific pack version."""
        query = select(evaluation_pack_version).where(
            evaluation_pack_version.c.version_id == version_id
        )
        result = conn.execute(query).first()
        return dict(result._mapping) if result else None
    
    @staticmethod
    def create_version(conn: Connection, version_data: EvaluationPackVersionCreate) -> Dict:
        """Create a new pack version."""
        version_id = version_data.version_id or f"ver_{version_data.pack_id}_{uuid4().hex[:8]}"
        
        insert_stmt = insert(evaluation_pack_version).values(
            version_id=version_id,
            pack_id=version_data.pack_id,
            version_number=version_data.version_number,
            pack_json=version_data.pack_json.model_dump(),
            created_by=version_data.created_by,
            created_at=datetime.utcnow(),
            change_note=version_data.change_note
        )
        
        conn.execute(insert_stmt)
        conn.commit()
        
        return EvaluationPackVersionService.get_version(conn, version_id)


class RecipePackService:
    """Service for attaching packs to recipes."""
    
    @staticmethod
    def attach_pack(conn: Connection, recipe_id: str, pack_id: str) -> bool:
        """Attach a pack to a recipe."""
        insert_stmt = insert(recipe_evaluation_pack).values(
            recipe_id=recipe_id,
            pack_id=pack_id,
            created_at=datetime.utcnow()
        )
        try:
            conn.execute(insert_stmt)
            conn.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    def detach_pack(conn: Connection, recipe_id: str, pack_id: str) -> bool:
        """Detach a pack from a recipe."""
        delete_stmt = delete(recipe_evaluation_pack).where(
            and_(
                recipe_evaluation_pack.c.recipe_id == recipe_id,
                recipe_evaluation_pack.c.pack_id == pack_id
            )
        )
        result = conn.execute(delete_stmt)
        conn.commit()
        return result.rowcount > 0
    
    @staticmethod
    def list_recipe_packs(conn: Connection, recipe_id: str) -> List[Dict]:
        """List all packs attached to a recipe."""
        query = select(evaluation_pack).select_from(
            evaluation_pack.join(
                recipe_evaluation_pack,
                evaluation_pack.c.id == recipe_evaluation_pack.c.pack_id
            )
        ).where(recipe_evaluation_pack.c.recipe_id == recipe_id)
        
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]


class EvaluationExecutionService:
    """Service for executing evaluation packs."""
    
    @staticmethod
    def execute_pack_on_run(
        conn: Connection,
        run_id: str,
        pack_id: str,
        pack_version_id: Optional[str] = None
    ) -> Dict:
        """Execute an evaluation pack on a run."""
        # Get pack version (latest if not specified)
        if not pack_version_id:
            versions = EvaluationPackVersionService.list_versions(conn, pack_id)
            if not versions:
                raise ValueError(f"No versions found for pack {pack_id}")
            pack_version = versions[0]
            pack_version_id = pack_version['version_id']
        else:
            pack_version = EvaluationPackVersionService.get_version(conn, pack_version_id)
        
        # Get run data
        run_query = select(ml_run).where(ml_run.c.id == run_id)
        run_result = conn.execute(run_query).first()
        if not run_result:
            raise ValueError(f"Run {run_id} not found")
        
        run_data = dict(run_result._mapping)
        
        # Execute evaluation (v1: mock with some logic)
        results = EvaluationExecutionService._mock_evaluate(
            pack_version['pack_json'],
            run_data.get('metrics_json', {})
        )
        
        # Determine overall status
        status = EvaluationExecutionService._determine_status(results)
        
        # Create result record
        result_id = f"eval_{run_id}_{pack_id}_{uuid4().hex[:8]}"
        insert_stmt = insert(evaluation_result).values(
            id=result_id,
            run_id=run_id,
            pack_id=pack_id,
            pack_version_id=pack_version_id,
            executed_at=datetime.utcnow(),
            status=status,
            results_json=results,
            summary_text=EvaluationExecutionService._generate_summary(results, status)
        )
        
        conn.execute(insert_stmt)
        conn.commit()
        
        # Return the result
        query = select(evaluation_result).where(evaluation_result.c.id == result_id)
        result = conn.execute(query).first()
        return dict(result._mapping) if result else None
    
    @staticmethod
    def _mock_evaluate(pack_json: Dict, run_metrics: Dict) -> Dict:
        """Mock evaluation logic (v1)."""
        results = {
            "metrics": [],
            "slices": [],
            "comparators": []
        }
        
        # Evaluate each metric
        for metric_def in pack_json.get('metrics', []):
            metric_key = metric_def['key']
            
            # Get actual value from run or generate mock
            actual_value = run_metrics.get(metric_key)
            if actual_value is None:
                # Generate deterministic mock value based on metric type
                if 'MAPE' in metric_key or 'MAE' in metric_key:
                    actual_value = random.uniform(0.1, 0.3)
                elif 'RMSE' in metric_key:
                    actual_value = random.uniform(20, 100)
                elif 'uplift' in metric_key:
                    actual_value = random.uniform(0.05, 0.20)
                elif 'precision' in metric_key:
                    actual_value = random.uniform(0.15, 0.35)
                elif 'correlation' in metric_key:
                    actual_value = random.uniform(0.60, 0.85)
                else:
                    actual_value = random.uniform(0.5, 1.0)
            
            # Check thresholds
            thresholds = metric_def.get('thresholds', {})
            direction = metric_def.get('direction', 'higher_is_better')
            
            metric_status = EvaluationExecutionService._check_threshold(
                actual_value, thresholds, direction
            )
            
            results["metrics"].append({
                "key": metric_key,
                "display_name": metric_def.get('display_name', metric_key),
                "actual_value": actual_value,
                "thresholds": thresholds,
                "status": metric_status,
                "direction": direction
            })
        
        return results
    
    @staticmethod
    def _check_threshold(value: float, thresholds: Dict, direction: str) -> str:
        """Check if a value passes thresholds."""
        promote = thresholds.get('promote')
        warn = thresholds.get('warn')
        fail = thresholds.get('fail')
        
        if direction == 'lower_is_better':
            if fail and value >= fail:
                return 'fail'
            elif warn and value >= warn:
                return 'warn'
            elif promote and value <= promote:
                return 'pass'
            else:
                return 'pass'
        else:  # higher_is_better
            if fail and value <= fail:
                return 'fail'
            elif warn and value <= warn:
                return 'warn'
            elif promote and value >= promote:
                return 'pass'
            else:
                return 'pass'
    
    @staticmethod
    def _determine_status(results: Dict) -> str:
        """Determine overall status from metric results."""
        metric_statuses = [m['status'] for m in results.get('metrics', [])]
        
        if 'fail' in metric_statuses:
            return 'fail'
        elif 'warn' in metric_statuses:
            return 'warn'
        else:
            return 'pass'
    
    @staticmethod
    def _generate_summary(results: Dict, status: str) -> str:
        """Generate human-readable summary."""
        total = len(results.get('metrics', []))
        passed = sum(1 for m in results.get('metrics', []) if m['status'] == 'pass')
        warned = sum(1 for m in results.get('metrics', []) if m['status'] == 'warn')
        failed = sum(1 for m in results.get('metrics', []) if m['status'] == 'fail')
        
        return f"Evaluation {status.upper()}: {passed}/{total} metrics passed, {warned} warnings, {failed} failures"
    
    @staticmethod
    def list_run_results(conn: Connection, run_id: str) -> List[Dict]:
        """List all evaluation results for a run."""
        query = select(evaluation_result).where(
            evaluation_result.c.run_id == run_id
        ).order_by(evaluation_result.c.executed_at.desc())
        
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]


class MonitorEvaluationService:
    """Service for model monitoring evaluations."""
    
    @staticmethod
    def create_snapshot(
        conn: Connection,
        model_id: str,
        pack_id: str,
        pack_version_id: Optional[str] = None
    ) -> Dict:
        """Create a monitoring snapshot for a model."""
        # Get pack version
        if not pack_version_id:
            versions = EvaluationPackVersionService.list_versions(conn, pack_id)
            if not versions:
                raise ValueError(f"No versions found for pack {pack_id}")
            pack_version = versions[0]
            pack_version_id = pack_version['version_id']
        else:
            pack_version = EvaluationPackVersionService.get_version(conn, pack_version_id)
        
        # Mock evaluation for monitoring (v1)
        results = EvaluationExecutionService._mock_evaluate(
            pack_version['pack_json'],
            {}
        )
        status = EvaluationExecutionService._determine_status(results)
        
        # Create snapshot
        snapshot_id = f"mon_{model_id}_{pack_id}_{uuid4().hex[:8]}"
        insert_stmt = insert(monitor_evaluation_snapshot).values(
            id=snapshot_id,
            model_id=model_id,
            captured_at=datetime.utcnow(),
            pack_id=pack_id,
            pack_version_id=pack_version_id,
            status=status,
            results_json=results
        )
        
        conn.execute(insert_stmt)
        conn.commit()
        
        # Return the snapshot
        query = select(monitor_evaluation_snapshot).where(
            monitor_evaluation_snapshot.c.id == snapshot_id
        )
        result = conn.execute(query).first()
        return dict(result._mapping) if result else None
    
    @staticmethod
    def list_model_snapshots(conn: Connection, model_id: str) -> List[Dict]:
        """List all monitoring snapshots for a model."""
        query = select(monitor_evaluation_snapshot).where(
            monitor_evaluation_snapshot.c.model_id == model_id
        ).order_by(monitor_evaluation_snapshot.c.captured_at.desc())
        
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]

