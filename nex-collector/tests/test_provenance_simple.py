#!/usr/bin/env python3
"""Simple test script for provenance fields (no pytest required)."""
import hashlib
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import (
    ContextDoc, ContextVariant, Chunk, 
    SyntheticExample, Targets, ExampleType
)


def hash_text(text: str) -> str:
    """Helper to hash text for testing."""
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"


def test_provenance_fields():
    """Test provenance fields on all models."""
    print("🧪 Testing Provenance & Traceability Fields")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Create test context doc
        print("\n1️⃣ Creating test context document...")
        ctx = ContextDoc(
            id="test-ctx-provenance",
            title="Test Context for Provenance",
            version="1.0.0",
            body_text="Test context body text."
        )
        db.add(ctx)
        db.commit()
        print("   ✅ ContextDoc created")
        
        # Create test variant
        print("\n2️⃣ Creating test variant...")
        variant = ContextVariant(
            id="test-var-provenance",
            context_id=ctx.id,
            domain="test",
            persona="tester",
            task="testing",
            body_text="Test variant body text."
        )
        db.add(variant)
        db.commit()
        print("   ✅ ContextVariant created")
        
        # Test Chunk with provenance
        print("\n3️⃣ Testing Chunk provenance fields...")
        text = "This is a test chunk for provenance testing."
        chunk = Chunk(
            id="test-chunk-provenance",
            variant_id=variant.id,
            order=0,
            text=text,
            source_uri="https://example.com/test-doc.pdf",
            source_span={"start": 0, "end": len(text)},
            citation_ids=["cite-1", "cite-2"],
            text_hash=hash_text(text),
            license="CC-BY-4.0",
            usage_rights="commercial-use-allowed"
        )
        db.add(chunk)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="test-chunk-provenance").first()
        assert retrieved.source_uri == "https://example.com/test-doc.pdf"
        assert retrieved.source_span == {"start": 0, "end": len(text)}
        assert retrieved.citation_ids == ["cite-1", "cite-2"]
        assert retrieved.text_hash == hash_text(text)
        assert retrieved.license == "CC-BY-4.0"
        assert retrieved.usage_rights == "commercial-use-allowed"
        print("   ✅ Chunk provenance fields work correctly")
        
        # Test SyntheticExample with provenance
        print("\n4️⃣ Testing SyntheticExample provenance fields...")
        input_data = {"task": "test", "input": "Test input"}
        input_json_str = json.dumps(input_data, sort_keys=True)
        
        example = SyntheticExample(
            id="test-ex-provenance",
            variant_id=variant.id,
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
        db.add(example)
        db.commit()
        
        retrieved = db.query(SyntheticExample).filter_by(id="test-ex-provenance").first()
        assert retrieved.source_uri == "https://example.com/test-source.md"
        assert retrieved.source_span == {"start": 50, "end": 150}
        assert retrieved.citation_ids == ["cite-ex-1"]
        assert retrieved.text_hash == hash_text(input_json_str)
        assert retrieved.license == "MIT"
        assert retrieved.usage_rights == "research-use-only"
        print("   ✅ SyntheticExample provenance fields work correctly")
        
        # Test Targets with provenance
        print("\n5️⃣ Testing Targets provenance fields...")
        target = Targets(
            id="test-target-provenance",
            example_id=example.id,
            y_text="Test target output",
            source_uri="https://example.com/target-source.txt",
            source_span={"start": 200, "end": 300},
            citation_ids=["cite-target-1", "cite-target-2"]
        )
        db.add(target)
        db.commit()
        
        retrieved = db.query(Targets).filter_by(id="test-target-provenance").first()
        assert retrieved.source_uri == "https://example.com/target-source.txt"
        assert retrieved.source_span == {"start": 200, "end": 300}
        assert retrieved.citation_ids == ["cite-target-1", "cite-target-2"]
        print("   ✅ Targets provenance fields work correctly")
        
        # Test optional fields (can be None)
        print("\n6️⃣ Testing optional provenance fields...")
        chunk2 = Chunk(
            id="test-chunk-no-provenance",
            variant_id=variant.id,
            order=1,
            text="Simple chunk without provenance"
        )
        db.add(chunk2)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="test-chunk-no-provenance").first()
        assert retrieved.source_uri is None
        assert retrieved.source_span is None
        assert retrieved.citation_ids is None
        assert retrieved.text_hash is None
        assert retrieved.license is None
        assert retrieved.usage_rights is None
        print("   ✅ Optional provenance fields work correctly")
        
        # Test text_hash for de-duplication
        print("\n7️⃣ Testing text_hash de-duplication...")
        hash_value = hash_text("Duplicate text")
        chunk3 = Chunk(
            id="chunk-dup-1",
            variant_id=variant.id,
            order=2,
            text="Duplicate text",
            text_hash=hash_value
        )
        db.add(chunk3)
        db.commit()
        
        duplicates = db.query(Chunk).filter_by(text_hash=hash_value).all()
        assert len(duplicates) == 1
        assert duplicates[0].id == "chunk-dup-1"
        print("   ✅ Text hash de-duplication works correctly")
        
        # Test querying by source_uri
        print("\n8️⃣ Testing querying by source_uri...")
        uri = "https://example.com/doc.pdf"
        chunk4 = Chunk(
            id="chunk-uri-1",
            variant_id=variant.id,
            order=3,
            text="Text 1",
            source_uri=uri
        )
        chunk5 = Chunk(
            id="chunk-uri-2",
            variant_id=variant.id,
            order=4,
            text="Text 2",
            source_uri=uri
        )
        db.add_all([chunk4, chunk5])
        db.commit()
        
        results = db.query(Chunk).filter_by(source_uri=uri).all()
        assert len(results) == 2
        assert {r.id for r in results} == {"chunk-uri-1", "chunk-uri-2"}
        print("   ✅ Querying by source_uri works correctly")
        
        print("\n" + "=" * 60)
        print("✅ All provenance field tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
        # Clean up tables
        Base.metadata.drop_all(bind=engine)
    
    return True


if __name__ == "__main__":
    success = test_provenance_fields()
    sys.exit(0 if success else 1)

