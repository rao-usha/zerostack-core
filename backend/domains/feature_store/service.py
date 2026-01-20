"""Feature store service layer."""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from .db_models import feature_entities, feature_definitions, feature_sets, feature_set_features
from .models import (
    EntityCreate, EntityUpdate,
    FeatureDefinitionCreate, FeatureDefinitionUpdate, FeatureStatus,
    FeatureSetCreate, FeatureSetUpdate,
)

logger = logging.getLogger(__name__)


class FeatureStoreService:
    """Service for feature store operations."""

    def __init__(self, session: Session):
        self.session = session

    # ========================================================================
    # Entity Operations
    # ========================================================================

    def create_entity(self, data: EntityCreate, created_by: str = None) -> dict:
        """Create a new feature entity."""
        entity_id = func.gen_random_uuid()
        now = datetime.utcnow()

        stmt = feature_entities.insert().values(
            name=data.name,
            description=data.description,
            join_keys=data.join_keys,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        ).returning(feature_entities)

        result = self.session.execute(stmt)
        row = result.fetchone()
        self.session.commit()

        logger.info(f"Created entity: {data.name}")
        return dict(row._mapping)

    def get_entity(self, entity_id: UUID) -> Optional[dict]:
        """Get entity by ID."""
        stmt = select(feature_entities).where(feature_entities.c.id == entity_id)
        result = self.session.execute(stmt)
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def get_entity_by_name(self, name: str) -> Optional[dict]:
        """Get entity by name."""
        stmt = select(feature_entities).where(feature_entities.c.name == name)
        result = self.session.execute(stmt)
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def list_entities(self, page: int = 1, page_size: int = 50) -> tuple[List[dict], int]:
        """List entities with pagination."""
        # Count total
        count_stmt = select(func.count()).select_from(feature_entities)
        total = self.session.execute(count_stmt).scalar()

        # Get page
        offset = (page - 1) * page_size
        stmt = (
            select(feature_entities)
            .order_by(feature_entities.c.name)
            .offset(offset)
            .limit(page_size)
        )
        result = self.session.execute(stmt)
        items = [dict(row._mapping) for row in result.fetchall()]

        return items, total

    def update_entity(self, entity_id: UUID, data: EntityUpdate) -> Optional[dict]:
        """Update an entity."""
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return self.get_entity(entity_id)

        updates["updated_at"] = datetime.utcnow()

        stmt = (
            feature_entities.update()
            .where(feature_entities.c.id == entity_id)
            .values(**updates)
            .returning(feature_entities)
        )
        result = self.session.execute(stmt)
        row = result.fetchone()
        self.session.commit()

        return dict(row._mapping) if row else None

    def delete_entity(self, entity_id: UUID) -> bool:
        """Delete an entity."""
        stmt = feature_entities.delete().where(feature_entities.c.id == entity_id)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    # ========================================================================
    # Feature Definition Operations
    # ========================================================================

    def create_feature_definition(self, data: FeatureDefinitionCreate) -> dict:
        """Create a new feature definition."""
        now = datetime.utcnow()

        stmt = feature_definitions.insert().values(
            name=data.name,
            entity_id=data.entity_id,
            version=1,
            dtype=data.dtype.value,
            transformation_type=data.transformation_type.value,
            transformation_code=data.transformation_code,
            source_table=data.source_table,
            description=data.description,
            owner=data.owner,
            tags=data.tags,
            computation_mode=data.computation_mode.value,
            refresh_schedule=data.refresh_schedule,
            ttl_seconds=data.ttl_seconds,
            status=FeatureStatus.DRAFT.value,
            created_at=now,
            updated_at=now,
        ).returning(feature_definitions)

        result = self.session.execute(stmt)
        row = result.fetchone()
        self.session.commit()

        logger.info(f"Created feature definition: {data.name} v1")
        return dict(row._mapping)

    def get_feature_definition(self, feature_id: UUID) -> Optional[dict]:
        """Get feature definition by ID."""
        stmt = select(feature_definitions).where(feature_definitions.c.id == feature_id)
        result = self.session.execute(stmt)
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def get_feature_definition_by_name(self, name: str, version: int = None) -> Optional[dict]:
        """Get feature definition by name (optionally specific version)."""
        if version:
            stmt = select(feature_definitions).where(
                and_(
                    feature_definitions.c.name == name,
                    feature_definitions.c.version == version
                )
            )
        else:
            # Get latest version
            stmt = (
                select(feature_definitions)
                .where(feature_definitions.c.name == name)
                .order_by(feature_definitions.c.version.desc())
                .limit(1)
            )
        result = self.session.execute(stmt)
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def list_feature_definitions(
        self,
        entity_id: UUID = None,
        status: str = None,
        search: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[dict], int]:
        """List feature definitions with filtering and pagination."""
        # Build filter conditions
        conditions = []
        if entity_id:
            conditions.append(feature_definitions.c.entity_id == entity_id)
        if status:
            conditions.append(feature_definitions.c.status == status)
        if search:
            conditions.append(feature_definitions.c.name.ilike(f"%{search}%"))

        # Count total
        count_stmt = select(func.count()).select_from(feature_definitions)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = self.session.execute(count_stmt).scalar()

        # Get page
        offset = (page - 1) * page_size
        stmt = (
            select(feature_definitions)
            .order_by(feature_definitions.c.name, feature_definitions.c.version.desc())
            .offset(offset)
            .limit(page_size)
        )
        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = self.session.execute(stmt)
        items = [dict(row._mapping) for row in result.fetchall()]

        return items, total

    def update_feature_definition(self, feature_id: UUID, data: FeatureDefinitionUpdate) -> Optional[dict]:
        """Update a feature definition (status only, or create new version for code changes)."""
        current = self.get_feature_definition(feature_id)
        if not current:
            return None

        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return current

        # Handle enum values
        if "computation_mode" in updates:
            updates["computation_mode"] = updates["computation_mode"].value
        if "status" in updates:
            updates["status"] = updates["status"].value

        updates["updated_at"] = datetime.utcnow()

        stmt = (
            feature_definitions.update()
            .where(feature_definitions.c.id == feature_id)
            .values(**updates)
            .returning(feature_definitions)
        )
        result = self.session.execute(stmt)
        row = result.fetchone()
        self.session.commit()

        return dict(row._mapping) if row else None

    def create_feature_version(self, feature_id: UUID, new_code: str, description: str = None) -> Optional[dict]:
        """Create a new version of a feature definition."""
        current = self.get_feature_definition(feature_id)
        if not current:
            return None

        now = datetime.utcnow()
        new_version = current["version"] + 1

        stmt = feature_definitions.insert().values(
            name=current["name"],
            entity_id=current["entity_id"],
            version=new_version,
            dtype=current["dtype"],
            transformation_type=current["transformation_type"],
            transformation_code=new_code,
            source_table=current["source_table"],
            description=description or current["description"],
            owner=current["owner"],
            tags=current["tags"],
            computation_mode=current["computation_mode"],
            refresh_schedule=current["refresh_schedule"],
            ttl_seconds=current["ttl_seconds"],
            status=FeatureStatus.DRAFT.value,
            created_at=now,
            updated_at=now,
        ).returning(feature_definitions)

        result = self.session.execute(stmt)
        row = result.fetchone()
        self.session.commit()

        logger.info(f"Created feature version: {current['name']} v{new_version}")
        return dict(row._mapping)

    def delete_feature_definition(self, feature_id: UUID) -> bool:
        """Delete a feature definition."""
        stmt = feature_definitions.delete().where(feature_definitions.c.id == feature_id)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    # ========================================================================
    # Feature Set Operations
    # ========================================================================

    def create_feature_set(self, data: FeatureSetCreate) -> dict:
        """Create a new feature set."""
        now = datetime.utcnow()

        stmt = feature_sets.insert().values(
            name=data.name,
            entity_id=data.entity_id,
            description=data.description,
            owner=data.owner,
            tags=data.tags,
            created_at=now,
            updated_at=now,
        ).returning(feature_sets)

        result = self.session.execute(stmt)
        row = result.fetchone()
        feature_set = dict(row._mapping)

        # Add initial features if provided
        if data.feature_ids:
            self._add_features_to_set(feature_set["id"], data.feature_ids)

        self.session.commit()
        logger.info(f"Created feature set: {data.name}")
        return feature_set

    def get_feature_set(self, set_id: UUID) -> Optional[dict]:
        """Get feature set by ID."""
        stmt = select(feature_sets).where(feature_sets.c.id == set_id)
        result = self.session.execute(stmt)
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def get_feature_set_with_features(self, set_id: UUID) -> Optional[dict]:
        """Get feature set with all its features."""
        feature_set = self.get_feature_set(set_id)
        if not feature_set:
            return None

        # Get features in this set
        stmt = (
            select(feature_definitions)
            .join(feature_set_features, feature_set_features.c.feature_definition_id == feature_definitions.c.id)
            .where(feature_set_features.c.feature_set_id == set_id)
            .order_by(feature_definitions.c.name)
        )
        result = self.session.execute(stmt)
        features = [dict(row._mapping) for row in result.fetchall()]

        feature_set["features"] = features
        feature_set["feature_count"] = len(features)
        return feature_set

    def list_feature_sets(
        self,
        entity_id: UUID = None,
        search: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[dict], int]:
        """List feature sets with filtering and pagination."""
        conditions = []
        if entity_id:
            conditions.append(feature_sets.c.entity_id == entity_id)
        if search:
            conditions.append(feature_sets.c.name.ilike(f"%{search}%"))

        # Count total
        count_stmt = select(func.count()).select_from(feature_sets)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = self.session.execute(count_stmt).scalar()

        # Get page
        offset = (page - 1) * page_size
        stmt = (
            select(feature_sets)
            .order_by(feature_sets.c.name)
            .offset(offset)
            .limit(page_size)
        )
        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = self.session.execute(stmt)
        items = [dict(row._mapping) for row in result.fetchall()]

        return items, total

    def update_feature_set(self, set_id: UUID, data: FeatureSetUpdate) -> Optional[dict]:
        """Update a feature set."""
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return self.get_feature_set(set_id)

        updates["updated_at"] = datetime.utcnow()

        stmt = (
            feature_sets.update()
            .where(feature_sets.c.id == set_id)
            .values(**updates)
            .returning(feature_sets)
        )
        result = self.session.execute(stmt)
        row = result.fetchone()
        self.session.commit()

        return dict(row._mapping) if row else None

    def delete_feature_set(self, set_id: UUID) -> bool:
        """Delete a feature set."""
        stmt = feature_sets.delete().where(feature_sets.c.id == set_id)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    def add_features_to_set(self, set_id: UUID, feature_ids: List[UUID]) -> int:
        """Add features to a set. Returns count added."""
        count = self._add_features_to_set(set_id, feature_ids)
        self.session.commit()
        return count

    def _add_features_to_set(self, set_id: UUID, feature_ids: List[UUID]) -> int:
        """Internal: Add features to a set (no commit)."""
        added = 0
        for feature_id in feature_ids:
            try:
                stmt = feature_set_features.insert().values(
                    feature_set_id=set_id,
                    feature_definition_id=feature_id,
                )
                self.session.execute(stmt)
                added += 1
            except Exception:
                # Likely duplicate, skip
                pass
        return added

    def remove_features_from_set(self, set_id: UUID, feature_ids: List[UUID]) -> int:
        """Remove features from a set. Returns count removed."""
        stmt = feature_set_features.delete().where(
            and_(
                feature_set_features.c.feature_set_id == set_id,
                feature_set_features.c.feature_definition_id.in_(feature_ids)
            )
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount
