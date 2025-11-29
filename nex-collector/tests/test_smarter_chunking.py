#!/usr/bin/env python3
"""Simple test script for smarter chunking (no pytest required)."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import (
    ContextDoc, ContextVariant, Chunk
)


def test_smarter_chunking():
    """Test smarter chunking features."""
    print("🧪 Testing Smarter Chunking for Retrieval")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Create test context doc
        print("\n1️⃣ Creating test context document...")
        ctx = ContextDoc(
            id="test-ctx-chunking",
            title="Test Context for Chunking",
            version="1.0.0",
            body_text="Test context body text."
        )
        db.add(ctx)
        db.commit()
        print("   ✅ ContextDoc created")
        
        # Create test variant
        print("\n2️⃣ Creating test variant...")
        variant = ContextVariant(
            id="test-var-chunking",
            context_id=ctx.id,
            domain="test",
            persona="tester",
            task="testing",
            body_text="Test variant body text."
        )
        db.add(variant)
        db.commit()
        print("   ✅ ContextVariant created")
        
        # Test Chunk with neighbors (bidirectional links)
        print("\n3️⃣ Testing neighbors (bidirectional links)...")
        chunk1 = Chunk(
            id="chunk-1",
            variant_id=variant.id,
            order=0,
            text="First chunk",
            neighbors=["chunk-2", "chunk-3"]
        )
        chunk2 = Chunk(
            id="chunk-2",
            variant_id=variant.id,
            order=1,
            text="Second chunk",
            neighbors=["chunk-1", "chunk-3"]
        )
        chunk3 = Chunk(
            id="chunk-3",
            variant_id=variant.id,
            order=2,
            text="Third chunk",
            neighbors=["chunk-1", "chunk-2"]
        )
        db.add_all([chunk1, chunk2, chunk3])
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="chunk-1").first()
        assert retrieved.neighbors == ["chunk-2", "chunk-3"]
        assert "chunk-2" in retrieved.neighbors
        assert "chunk-3" in retrieved.neighbors
        print("   ✅ Neighbors (bidirectional links) work correctly")
        
        # Test section_hierarchy
        print("\n4️⃣ Testing section_hierarchy...")
        chunk4 = Chunk(
            id="chunk-4",
            variant_id=variant.id,
            order=3,
            text="Section heading chunk",
            section_hierarchy={
                "level": 1,
                "section": "Introduction",
                "subsection": "Overview",
                "subsubsection": "Purpose"
            }
        )
        db.add(chunk4)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="chunk-4").first()
        assert retrieved.section_hierarchy["level"] == 1
        assert retrieved.section_hierarchy["section"] == "Introduction"
        assert retrieved.section_hierarchy["subsection"] == "Overview"
        assert retrieved.section_hierarchy["subsubsection"] == "Purpose"
        print("   ✅ Section hierarchy works correctly")
        
        # Test chunk_type
        print("\n5️⃣ Testing chunk_type...")
        chunk5 = Chunk(
            id="chunk-5",
            variant_id=variant.id,
            order=4,
            text="# Heading",
            chunk_type="heading"
        )
        chunk6 = Chunk(
            id="chunk-6",
            variant_id=variant.id,
            order=5,
            text="- Bullet point 1\n- Bullet point 2",
            chunk_type="bullet"
        )
        chunk7 = Chunk(
            id="chunk-7",
            variant_id=variant.id,
            order=6,
            text="This is a regular paragraph of text.",
            chunk_type="paragraph"
        )
        db.add_all([chunk5, chunk6, chunk7])
        db.commit()
        
        retrieved_heading = db.query(Chunk).filter_by(id="chunk-5").first()
        retrieved_bullet = db.query(Chunk).filter_by(id="chunk-6").first()
        retrieved_para = db.query(Chunk).filter_by(id="chunk-7").first()
        assert retrieved_heading.chunk_type == "heading"
        assert retrieved_bullet.chunk_type == "bullet"
        assert retrieved_para.chunk_type == "paragraph"
        print("   ✅ Chunk type works correctly")
        
        # Test overlap windows
        print("\n6️⃣ Testing overlap windows...")
        chunk8 = Chunk(
            id="chunk-8",
            variant_id=variant.id,
            order=7,
            text="This is a chunk with overlap window for semantic chunking.",
            overlap_start=0,
            overlap_end=20  # First 20 chars overlap with previous chunk
        )
        db.add(chunk8)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="chunk-8").first()
        assert retrieved.overlap_start == 0
        assert retrieved.overlap_end == 20
        print("   ✅ Overlap windows work correctly")
        
        # Test querying by chunk_type
        print("\n7️⃣ Testing querying by chunk_type...")
        headings = db.query(Chunk).filter_by(chunk_type="heading").all()
        assert len(headings) == 1
        assert headings[0].id == "chunk-5"
        
        bullets = db.query(Chunk).filter_by(chunk_type="bullet").all()
        assert len(bullets) == 1
        assert bullets[0].id == "chunk-6"
        print("   ✅ Querying by chunk_type works correctly")
        
        # Test querying by section hierarchy
        print("\n8️⃣ Testing querying by section hierarchy...")
        # Query chunks and check section_hierarchy in Python (simpler than JSON queries)
        all_chunks = db.query(Chunk).all()
        intro_chunks = [c for c in all_chunks if c.section_hierarchy and c.section_hierarchy.get("section") == "Introduction"]
        assert len(intro_chunks) == 1
        assert intro_chunks[0].id == "chunk-4"
        print("   ✅ Querying by section hierarchy works correctly")
        
        # Test optional fields
        print("\n9️⃣ Testing optional chunking fields...")
        chunk9 = Chunk(
            id="chunk-9",
            variant_id=variant.id,
            order=8,
            text="Simple chunk without chunking metadata"
        )
        db.add(chunk9)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="chunk-9").first()
        assert retrieved.neighbors is None
        assert retrieved.section_hierarchy is None
        assert retrieved.chunk_type is None
        assert retrieved.overlap_start is None
        assert retrieved.overlap_end is None
        print("   ✅ Optional chunking fields work correctly")
        
        # Test complex example with all fields
        print("\n🔟 Testing complex example with all chunking fields...")
        chunk10 = Chunk(
            id="chunk-10",
            variant_id=variant.id,
            order=9,
            text="Complex chunk with all features",
            neighbors=["chunk-9", "chunk-11"],
            section_hierarchy={
                "level": 2,
                "section": "Methods",
                "subsection": "Data Collection"
            },
            chunk_type="paragraph",
            overlap_start=10,
            overlap_end=30
        )
        db.add(chunk10)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="chunk-10").first()
        assert retrieved.neighbors == ["chunk-9", "chunk-11"]
        assert retrieved.section_hierarchy["section"] == "Methods"
        assert retrieved.chunk_type == "paragraph"
        assert retrieved.overlap_start == 10
        assert retrieved.overlap_end == 30
        print("   ✅ Complex example with all fields works correctly")
        
        print("\n" + "=" * 60)
        print("✅ All smarter chunking tests passed!")
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
    success = test_smarter_chunking()
    sys.exit(0 if success else 1)

