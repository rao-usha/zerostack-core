"""Tests for dictionary semantics functionality."""
import pytest
from uuid import uuid4
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

from domains.data_explorer.dictionary_semantics_models import (
    DictionaryEntry,
    DictionaryEntrySemantics,
    DictionaryGrain,
    DictionaryRelationship,
    EntryType,
    RelationshipKind,
)
from domains.data_explorer import dictionary_semantics_service as service


@pytest.fixture(name="session")
def session_fixture():
    """Create test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_entry(session: Session):
    """Test creating a dictionary entry."""
    entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.TABLE.value,
        title="test_table",
        database_name="default",
        schema_name="public",
        table_name="test_table",
        description="Test table"
    )
    
    assert entry.id is not None
    assert entry.entry_type == EntryType.TABLE.value
    assert entry.title == "test_table"


def test_upsert_semantics(session: Session):
    """Test upserting semantics."""
    # Create entry
    entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.TABLE.value,
        title="test_table",
        database_name="default",
        schema_name="public",
        table_name="test_table"
    )
    
    # Upsert semantics
    decision_context = {
        "primary_decisions": ["Test decision"],
        "decision_frequency": "daily"
    }
    
    semantics = service.upsert_semantics(
        session,
        entry.id,
        decision_context=decision_context
    )
    
    assert semantics.entry_id == entry.id
    assert semantics.decision_context["primary_decisions"] == ["Test decision"]


def test_validate_semantics_blocks(session: Session):
    """Test semantics validation."""
    # Valid confidence score
    valid, errors = service.validate_semantics_blocks(
        validation_state={"confidence_score": 0.8}
    )
    assert valid
    assert len(errors) == 0
    
    # Invalid confidence score
    valid, errors = service.validate_semantics_blocks(
        validation_state={"confidence_score": 1.5}
    )
    assert not valid
    assert len(errors) > 0


def test_upsert_grain(session: Session):
    """Test upserting grain."""
    # Create entry
    entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.TABLE.value,
        title="test_table",
        database_name="default",
        schema_name="public",
        table_name="test_table"
    )
    
    # Upsert grain
    grain = service.upsert_grain(
        session,
        entry.id,
        entity="one row per customer",
        primary_key=["customer_id"],
        time_grain="day"
    )
    
    assert grain.entry_id == entry.id
    assert grain.entity == "one row per customer"
    assert grain.primary_key == ["customer_id"]


def test_create_relationship(session: Session):
    """Test creating a relationship."""
    # Create two entries
    left_entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.COLUMN.value,
        title="orders.customer_id",
        database_name="default",
        schema_name="public",
        table_name="orders",
        column_name="customer_id"
    )
    
    right_entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.COLUMN.value,
        title="customers.id",
        database_name="default",
        schema_name="public",
        table_name="customers",
        column_name="id"
    )
    
    # Create relationship
    rel = service.create_relationship(
        session,
        relationship_kind=RelationshipKind.CANDIDATE.value,
        left_entry_id=left_entry.id,
        right_entry_id=right_entry.id,
        relationship_type="foreign_key_like",
        cardinality="many_to_one",
        confidence_score=0.9
    )
    
    assert rel.id is not None
    assert rel.left_entry_id == left_entry.id
    assert rel.right_entry_id == right_entry.id
    assert rel.cardinality == "many_to_one"


def test_update_relationship_status(session: Session):
    """Test updating relationship status."""
    # Create entries and relationship
    left_entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.COLUMN.value,
        title="test.col1",
        database_name="default",
        schema_name="public",
        table_name="test",
        column_name="col1"
    )
    
    right_entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.COLUMN.value,
        title="test.col2",
        database_name="default",
        schema_name="public",
        table_name="test",
        column_name="col2"
    )
    
    rel = service.create_relationship(
        session,
        relationship_kind=RelationshipKind.CANDIDATE.value,
        left_entry_id=left_entry.id,
        right_entry_id=right_entry.id,
        relationship_type="foreign_key_like",
        status="suggested"
    )
    
    # Update status
    updated_rel = service.update_relationship_status(session, rel.id, "approved")
    
    assert updated_rel.status == "approved"


def test_delete_relationship(session: Session):
    """Test deleting a relationship."""
    # Create entries and relationship
    left_entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.COLUMN.value,
        title="test.col1",
        database_name="default",
        schema_name="public",
        table_name="test",
        column_name="col1"
    )
    
    right_entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.COLUMN.value,
        title="test.col2",
        database_name="default",
        schema_name="public",
        table_name="test",
        column_name="col2"
    )
    
    rel = service.create_relationship(
        session,
        relationship_kind=RelationshipKind.CANDIDATE.value,
        left_entry_id=left_entry.id,
        right_entry_id=right_entry.id,
        relationship_type="foreign_key_like",
        status="suggested"
    )
    
    # Delete (should be hard delete for suggested)
    hard_deleted = service.delete_relationship(session, rel.id, force=False)
    
    assert hard_deleted


def test_get_context_blob(session: Session):
    """Test getting context blob."""
    # Create entry with semantics
    entry = service.get_or_create_entry(
        session,
        entry_type=EntryType.TABLE.value,
        title="test_table",
        database_name="default",
        schema_name="public",
        table_name="test_table",
        description="Test table"
    )
    
    service.upsert_semantics(
        session,
        entry.id,
        decision_context={"primary_decisions": ["Test"]},
        validation_state={"confidence_score": 0.8}
    )
    
    service.upsert_grain(
        session,
        entry.id,
        entity="one row per record",
        primary_key=["id"]
    )
    
    # Get context blob
    context = service.get_entry_context_blob(session, entry.id, include_relationships=False)
    
    assert context["entry"]["id"] == str(entry.id)
    assert context["entry"]["title"] == "test_table"
    assert "decision_context" in context
    assert "grain" in context
    assert context["grain"]["entity"] == "one row per record"

