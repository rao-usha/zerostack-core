"""Asset versioning service for tracking derived asset history.

Provides:
- Version chain tracking
- History retrieval
- Rollback capability
"""
import logging
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AssetVersion:
    """A version of a derived asset."""
    asset_id: str
    version_number: int
    status: str  # 'current', 'replaced', 'archived'
    created_at: datetime
    storage_uri: str
    metrics: dict
    replaced_by_id: Optional[str]
    
    def to_dict(self) -> dict:
        return {
            'asset_id': self.asset_id,
            'version_number': self.version_number,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'storage_uri': self.storage_uri,
            'metrics': self.metrics,
            'replaced_by_id': self.replaced_by_id
        }


@dataclass
class AssetHistory:
    """Full version history of an asset lineage."""
    current_asset_id: str
    current_version: int
    total_versions: int
    versions: List[AssetVersion]
    
    def to_dict(self) -> dict:
        return {
            'current_asset_id': self.current_asset_id,
            'current_version': self.current_version,
            'total_versions': self.total_versions,
            'versions': [v.to_dict() for v in self.versions]
        }


class AssetVersioningService:
    """Service for managing asset version history."""
    
    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)
    
    def get_asset_history(self, asset_id: str) -> AssetHistory:
        """
        Get the full version history for an asset.
        
        Follows the parent_asset_id chain to find all versions.
        
        Args:
            asset_id: Any asset ID in the version chain
            
        Returns:
            AssetHistory with all versions
        """
        # First, find the root asset (oldest in chain)
        root_id = self._find_root_asset(asset_id)
        
        # Then get all descendants
        versions = self._get_version_chain(root_id)
        
        if not versions:
            return AssetHistory(
                current_asset_id=asset_id,
                current_version=0,
                total_versions=0,
                versions=[]
            )
        
        # Find current version (no replaced_by)
        current = next((v for v in versions if v.status == 'current'), versions[-1])
        
        return AssetHistory(
            current_asset_id=current.asset_id,
            current_version=current.version_number,
            total_versions=len(versions),
            versions=versions
        )
    
    def create_new_version(
        self,
        parent_asset_id: str,
        new_asset_id: str,
        storage_uri: str,
        metrics: dict = None
    ) -> AssetVersion:
        """
        Create a new version of an asset.
        
        Links the new asset to the parent and marks the parent as replaced.
        
        Args:
            parent_asset_id: The asset being superseded
            new_asset_id: The new asset ID
            storage_uri: Storage location of new asset
            metrics: Metrics for the new asset
            
        Returns:
            The new AssetVersion
        """
        # Get parent's version number
        parent_query = "SELECT version_number FROM ml_derived_assets WHERE id = :id"
        with self.engine.connect() as conn:
            result = conn.execute(text(parent_query), {'id': parent_asset_id}).fetchone()
            parent_version = result[0] if result else 0
        
        new_version = parent_version + 1
        
        # Update parent to mark as replaced
        update_parent = """
            UPDATE ml_derived_assets 
            SET replaced_by_asset_id = :new_id
            WHERE id = :parent_id
        """
        
        # Update new asset with version info
        update_new = """
            UPDATE ml_derived_assets 
            SET parent_asset_id = :parent_id,
                version_number = :version
            WHERE id = :new_id
        """
        
        with self.engine.begin() as conn:
            conn.execute(text(update_parent), {
                'new_id': new_asset_id,
                'parent_id': parent_asset_id
            })
            conn.execute(text(update_new), {
                'parent_id': parent_asset_id,
                'version': new_version,
                'new_id': new_asset_id
            })
        
        logger.info(f"Created asset version {new_version}: {new_asset_id} (parent: {parent_asset_id})")
        
        return AssetVersion(
            asset_id=new_asset_id,
            version_number=new_version,
            status='current',
            created_at=datetime.utcnow(),
            storage_uri=storage_uri,
            metrics=metrics or {},
            replaced_by_id=None
        )
    
    def rollback_to_version(self, target_asset_id: str) -> str:
        """
        Rollback to a previous version of an asset.
        
        This doesn't delete newer versions, but creates a new "current"
        that references the target version's data.
        
        Args:
            target_asset_id: The asset version to rollback to
            
        Returns:
            ID of the new current asset (copy of target)
        """
        # Get target asset details
        query = """
            SELECT * FROM ml_derived_assets WHERE id = :id
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'id': target_asset_id}).fetchone()
        
        if not result:
            raise ValueError(f"Asset {target_asset_id} not found")
        
        target = dict(result._mapping)
        
        # Find current version in the chain
        history = self.get_asset_history(target_asset_id)
        if not history.versions:
            raise ValueError("No version history found")
        
        current = next((v for v in history.versions if v.status == 'current'), None)
        if not current:
            raise ValueError("No current version found")
        
        # Create a new version that copies the target
        # This is a "rollback version" - new entry pointing to old data
        insert_query = """
            INSERT INTO ml_derived_assets (
                source_run_id, name, asset_type, storage_uri, manifest_uri,
                metrics_json, tags, approval_state, notes, parent_asset_id,
                version_number
            )
            SELECT 
                source_run_id, 
                name || ' (rollback to v' || :target_version || ')',
                asset_type, 
                storage_uri, 
                manifest_uri,
                metrics_json, 
                tags, 
                'pending',
                'Rolled back from version ' || :current_version || ' to version ' || :target_version,
                :current_id,
                :new_version
            FROM ml_derived_assets
            WHERE id = :target_id
            RETURNING id
        """
        
        with self.engine.begin() as conn:
            # Mark current as replaced
            conn.execute(text("""
                UPDATE ml_derived_assets 
                SET replaced_by_asset_id = NULL 
                WHERE id = :id
            """), {'id': current.asset_id})
            
            # Create rollback version
            result = conn.execute(text(insert_query), {
                'target_id': target_asset_id,
                'target_version': target.get('version_number', 0),
                'current_id': current.asset_id,
                'current_version': current.version_number,
                'new_version': current.version_number + 1
            })
            new_id = str(result.fetchone()[0])
            
            # Update the previous current to point to new version
            conn.execute(text("""
                UPDATE ml_derived_assets 
                SET replaced_by_asset_id = :new_id 
                WHERE id = :current_id
            """), {'new_id': new_id, 'current_id': current.asset_id})
        
        logger.info(f"Rolled back to version {target.get('version_number', 0)}, created new version {new_id}")
        
        return new_id
    
    def _find_root_asset(self, asset_id: str) -> str:
        """Find the root (first) asset in a version chain."""
        query = """
            WITH RECURSIVE chain AS (
                SELECT id, parent_asset_id, 1 as depth
                FROM ml_derived_assets
                WHERE id = :asset_id
                
                UNION ALL
                
                SELECT a.id, a.parent_asset_id, c.depth + 1
                FROM ml_derived_assets a
                JOIN chain c ON a.id = c.parent_asset_id
                WHERE c.depth < 100  -- Safety limit
            )
            SELECT id FROM chain
            WHERE parent_asset_id IS NULL
            LIMIT 1
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'asset_id': asset_id}).fetchone()
            if result:
                return str(result[0])
        
        # If no root found, this asset is the root
        return asset_id
    
    def _get_version_chain(self, root_id: str) -> List[AssetVersion]:
        """Get all versions descending from a root asset."""
        query = """
            WITH RECURSIVE chain AS (
                SELECT id, parent_asset_id, version_number, created_at, 
                       storage_uri, metrics_json, replaced_by_asset_id, 1 as depth
                FROM ml_derived_assets
                WHERE id = :root_id
                
                UNION ALL
                
                SELECT a.id, a.parent_asset_id, a.version_number, a.created_at,
                       a.storage_uri, a.metrics_json, a.replaced_by_asset_id, c.depth + 1
                FROM ml_derived_assets a
                JOIN chain c ON a.parent_asset_id = c.id
                WHERE c.depth < 100  -- Safety limit
            )
            SELECT * FROM chain ORDER BY version_number ASC
        """
        
        versions = []
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'root_id': root_id})
            for row in result:
                row_dict = dict(row._mapping)
                status = 'replaced' if row_dict.get('replaced_by_asset_id') else 'current'
                versions.append(AssetVersion(
                    asset_id=str(row_dict['id']),
                    version_number=row_dict.get('version_number', 1),
                    status=status,
                    created_at=row_dict['created_at'],
                    storage_uri=row_dict.get('storage_uri', ''),
                    metrics=row_dict.get('metrics_json') or {},
                    replaced_by_id=str(row_dict['replaced_by_asset_id']) if row_dict.get('replaced_by_asset_id') else None
                ))
        
        return versions
    
    def compare_versions(self, version1_id: str, version2_id: str) -> dict:
        """
        Compare two versions of an asset.
        
        Returns differences in metrics.
        """
        query = """
            SELECT id, version_number, metrics_json, created_at
            FROM ml_derived_assets
            WHERE id IN (:id1, :id2)
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'id1': version1_id, 'id2': version2_id})
            rows = {str(r['id']): dict(r._mapping) for r in result}
        
        if len(rows) != 2:
            raise ValueError("One or both versions not found")
        
        v1 = rows[version1_id]
        v2 = rows[version2_id]
        
        metrics1 = v1.get('metrics_json') or {}
        metrics2 = v2.get('metrics_json') or {}
        
        # Find all metrics
        all_metrics = set(metrics1.keys()) | set(metrics2.keys())
        
        comparison = {
            'version1': {
                'id': version1_id,
                'version_number': v1.get('version_number', 1),
                'created_at': v1['created_at'].isoformat() if v1.get('created_at') else None
            },
            'version2': {
                'id': version2_id,
                'version_number': v2.get('version_number', 1),
                'created_at': v2['created_at'].isoformat() if v2.get('created_at') else None
            },
            'metrics_comparison': {}
        }
        
        for metric in all_metrics:
            val1 = metrics1.get(metric)
            val2 = metrics2.get(metric)
            
            change = None
            change_percent = None
            if val1 is not None and val2 is not None and isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                change = val2 - val1
                if val1 != 0:
                    change_percent = ((val2 - val1) / abs(val1)) * 100
            
            comparison['metrics_comparison'][metric] = {
                'version1_value': val1,
                'version2_value': val2,
                'change': change,
                'change_percent': round(change_percent, 2) if change_percent is not None else None
            }
        
        return comparison


# Singleton instance
_service_instance: Optional[AssetVersioningService] = None


def get_asset_versioning_service() -> AssetVersioningService:
    """Get singleton asset versioning service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AssetVersioningService()
    return _service_instance
