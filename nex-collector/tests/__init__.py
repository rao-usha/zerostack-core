#!/usr/bin/env python3
"""Tests for provenance & traceability fields."""
import hashlib
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import (
    ContextDoc, ContextVariant, Chunk, 
    SyntheticExample, Targets, ExampleType
)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        # Clean up tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_context_doc(db_session):
    """Create a test context document."""
    ctx = ContextDoc(
        id="test-ctx-1",
        title="Test Context",
        version="1.0.0",
        body_text="Test context body text for testing purposes."
    )
    db_session.add(ctx)
    db_session.commit()
    return ctx


@pytest.fixture
def test_variant(db_session, test_context_doc):
    """Create a test context variant."""
    variant = ContextVariant(
        id="test-var-1",
        context_id=test_context_doc.id,
        domain="test",
        persona="tester",
        task="testing",
        body_text="Test variant body text."
    )
    db_session.add(variant)
    db_session.commit()
    return variant


def hash_text(text: str) -> str:
    """Helper to hash text for testing."""
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"


class TestChunkProvenance:
    """Test provenance fields on Chunk model."""
    
    def test_chunk_with_provenance_fields(self, db_session, test_variant):
        """Test creating a Chunk with all provenance fields."""
        text = "This is a test chunk for provenance testing."
        chunk = Chunk(
            id="test-chunk-1",
            variant_id=test_variant.id,
            order=0,
            text=text,
            source_uri="https://example.com/test-doc.pdf",
            source_span={"start": 0, "end": len(text)},
            citation_ids=["cite-1", "cite-2"],
            text_hash=hash_text(text),
            license="CC-BY-4.0",
            usage_rights="commercial-use-allowed"
        )
        db_session.add(chunk)
        db_session.commit()
        
        # Retrieve and verify
        retrieved = db_session.query(Chunk).filter_by(id="test-chunk-1").first()
        assert retrieved is not None
        assert retrieved.source_uri == "https://example.com/test-doc.pdf"
        assert retrieved.source_span == {"start": 0, "end": len(text)}
        assert retrieved.citation_ids == ["cite-1", "cite-2"]
        assert retrieved.text_hash == hash_text(text)
        assert retrieved.license == "CC-BY-4.0"
        assert retrieved.usage_rights == "commercial-use-allowed"
    
    def test_chunk_provenance_optional(self, db_session, test_variant):
        """Test that provenance fields are optional."""
        chunk = Chunk(
            id="test-chunk-2",
            variant_id=test_variant.id,
            order=1,
            text="Simple chunk without provenance"
        )
        db_session.add(chunk)
        db_session.commit()
        
        retrieved = db_session.query(Chunk).filter_by(id="test-chunk-2").first()
        assert retrieved is not None
        assert retrieved.source_uri is None
        assert retrieved.source_span is None
        assert retrieved.citation_ids is None
        assert retrieved.text_hash is None
        assert retrieved.license is None
        assert retrieved.usage_rights is None
    
    def test_chunk_text_hash_deduplication(self, db_session, test_variant):
        """Test that text_hash can be used for de-duplication."""
        text = "Duplicate text content"
        hash_value = hash_text(text)
        
        # Create first chunk
        chunk1 = Chunk(
            id="test-chunk-3",
            variant_id=test_variant.id,
            order=0,
            text=text,
            text_hash=hash_value
        )
        db_session.add(chunk1)
        db_session.commit()
        
        # Query by hash to find duplicates
        duplicates = db_session.query(Chunk).filter_by(text_hash=hash_value).all()
        assert len(duplicates) == 1
        assert duplicates[0].id == "test-chunk-3"
    
    def test_chunk_source_span_json(self, db_session, test_variant):
        """Test that source_span stores JSON correctly."""
        chunk = Chunk(
            id="test-chunk-4",
            variant_id=test_variant.id,
            order=0,
            text="Test text",
            source_span={"start": 100, "end": 200, "line": 5}
        )
        db_session.add(chunk)
        db_session.commit()
        
        retrieved = db_session.query(Chunk).filter_by(id="test-chunk-4").first()
        assert retrieved.source_span["start"] == 100
        assert retrieved.source_span["end"] == 200
        assert retrieved.source_span["line"] == 5


class TestSyntheticExampleProvenance:
    """Test provenance fields on SyntheticExample model."""
    
    def test_synthetic_example_with_provenance_fields(self, db_session, test_variant):
        """Test creating a SyntheticExample with all provenance fields."""
        input_data = {"task": "test", "input": "Test input"}
        input_json_str = json.dumps(input_data, sort_keys=True)
        
        example = SyntheticExample(
            id="test-ex-1",
            variant_id=test_variant.id,
            example_type=ExampleType.TASK,
            input_json=input_data,
            constraints_json={},
            tags=[],
            source_uri="https://example.com/test-source.md",
            source_span={"start": 50, "end": 150},
            citation_ids=["cite-ex-1"],
            text_hash=hash_text(input_json_str),
            license="MIT",
            usage_rights="research-use-only"
        )
        db_session.add(example)
        db_session.commit()
        
        # Retrieve and verify
        retrieved = db_session.query(SyntheticExample).filter_by(id="test-ex-1").first()
        assert retrieved is not None
        assert retrieved.source_uri == "https://example.com/test-source.md"
        assert retrieved.source_span == {"start": 50, "end": 150}
        assert retrieved.citation_ids == ["cite-ex-1"]
        assert retrieved.text_hash == hash_text(input_json_str)
        assert retrieved.license == "MIT"
        assert retrieved.usage_rights == "research-use-only"
    
    def test_synthetic_example_provenance_optional(self, db_session, test_variant):
        """Test that provenance fields are optional."""
        example = SyntheticExample(
            id="test-ex-2",
            variant_id=test_variant.id,
            example_type=ExampleType.QA,
            input_json={"question": "Test?"},
            constraints_json={},
            tags=[]
        )
        db_session.add(example)
        db_session.commit()
        
        retrieved = db_session.query(SyntheticExample).filter_by(id="test-ex-2").first()
        assert retrieved is not None
        assert retrieved.source_uri is None
        assert retrieved.source_span is None
        assert retrieved.citation_ids is None
        assert retrieved.text_hash is None
        assert retrieved.license is None
        assert retrieved.usage_rights is None


class TestTargetsProvenance:
    """Test provenance fields on Targets model."""
    
    def test_targets_with_provenance_fields(self, db_session, test_variant):
        """Test creating Targets with provenance fields."""
        # First create an example
        example = SyntheticExample(
            id="test-ex-3",
            variant_id=test_variant.id,
            example_type=ExampleType.INSTRUCTION,
            input_json={"instruction": "Test"},
            constraints_json={},
            tags=[]
        )
        db_session.add(example)
        db_session.commit()
        
        # Create target with provenance
        target = Targets(
            id="test-target-1",
            example_id=example.id,
            y_text="Test target output",
            source_uri="https://example.com/target-source.txt",
            source_span={"start": 200, "end": 300},
            citation_ids=["cite-target-1", "cite-target-2"]
        )
        db_session.add(target)
        db_session.commit()
        
        # Retrieve and verify
        retrieved = db_session.query(Targets).filter_by(id="test-target-1").first()
        assert retrieved is not None
        assert retrieved.source_uri == "https://example.com/target-source.txt"
        assert retrieved.source_span == {"start": 200, "end": 300}
        assert retrieved.citation_ids == ["cite-target-1", "cite-target-2"]
    
    def test_targets_provenance_optional(self, db_session, test_variant):
        """Test that provenance fields are optional."""
        # Create example
        example = SyntheticExample(
            id="test-ex-4",
            variant_id=test_variant.id,
            example_type=ExampleType.TASK,
            input_json={"task": "test"},
            constraints_json={},
            tags=[]
        )
        db_session.add(example)
        db_session.commit()
        
        # Create target without provenance
        target = Targets(
            id="test-target-2",
            example_id=example.id,
            y_text="Simple target"
        )
        db_session.add(target)
        db_session.commit()
        
        retrieved = db_session.query(Targets).filter_by(id="test-target-2").first()
        assert retrieved is not None
        assert retrieved.source_uri is None
        assert retrieved.source_span is None
        assert retrieved.citation_ids is None


class TestProvenanceQueries:
    """Test querying by provenance fields."""
    
    def test_query_by_source_uri(self, db_session, test_variant):
        """Test querying chunks by source_uri."""
        uri = "https://example.com/doc.pdf"
        
        chunk1 = Chunk(
            id="chunk-uri-1",
            variant_id=test_variant.id,
            order=0,
            text="Text 1",
            source_uri=uri
        )
        chunk2 = Chunk(
            id="chunk-uri-2",
            variant_id=test_variant.id,
            order=1,
            text="Text 2",
            source_uri=uri
        )
        chunk3 = Chunk(
            id="chunk-uri-3",
            variant_id=test_variant.id,
            order=2,
            text="Text 3",
            source_uri="https://other.com/doc.pdf"
        )
        db_session.add_all([chunk1, chunk2, chunk3])
        db_session.commit()
        
        # Query by source_uri
        results = db_session.query(Chunk).filter_by(source_uri=uri).all()
        assert len(results) == 2
        assert {r.id for r in results} == {"chunk-uri-1", "chunk-uri-2"}
    
    def test_query_by_citation_id(self, db_session, test_variant):
        """Test querying by citation_ids."""
        example1 = SyntheticExample(
            id="ex-cite-1",
            variant_id=test_variant.id,
            example_type=ExampleType.QA,
            input_json={"q": "test"},
            constraints_json={},
            tags=[],
            citation_ids=["cite-a", "cite-b"]
        )
        example2 = SyntheticExample(
            id="ex-cite-2",
            variant_id=test_variant.id,
            example_type=ExampleType.QA,
            input_json={"q": "test2"},
            constraints_json={},
            tags=[],
            citation_ids=["cite-b", "cite-c"]
        )
        db_session.add_all([example1, example2])
        db_session.commit()
        
        # Query examples that cite "cite-b"
        # Note: PostgreSQL array contains operator
        from sqlalchemy import text
        results = db_session.query(SyntheticExample).filter(
            SyntheticExample.citation_ids.contains(["cite-b"])
        ).all()
        assert len(results) == 2
        assert {r.id for r in results} == {"ex-cite-1", "ex-cite-2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

