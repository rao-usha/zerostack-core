#!/usr/bin/env python3
"""Simple test script for quality signals (no pytest required)."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import (
    ContextDoc, ContextVariant, Chunk, 
    SyntheticExample, Targets, TeacherRun, ExampleType
)


def test_quality_signals():
    """Test quality signals on all models."""
    print("🧪 Testing Quality Signals")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Create test context doc
        print("\n1️⃣ Creating test context document...")
        ctx = ContextDoc(
            id="test-ctx-quality",
            title="Test Context for Quality",
            version="1.0.0",
            body_text="Test context body text."
        )
        db.add(ctx)
        db.commit()
        print("   ✅ ContextDoc created")
        
        # Create test variant
        print("\n2️⃣ Creating test variant...")
        variant = ContextVariant(
            id="test-var-quality",
            context_id=ctx.id,
            domain="test",
            persona="tester",
            task="testing",
            body_text="Test variant body text."
        )
        db.add(variant)
        db.commit()
        print("   ✅ ContextVariant created")
        
        # Test Chunk with quality signals
        print("\n3️⃣ Testing Chunk quality signals...")
        chunk = Chunk(
            id="test-chunk-quality",
            variant_id=variant.id,
            order=0,
            text="This is a high-quality test chunk.",
            quality_scores_json={
                "coherence": 0.92,
                "faithfulness": 0.88,
                "toxicity": 0.05,
                "pii_flags": []
            },
            confidence=0.90
        )
        db.add(chunk)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="test-chunk-quality").first()
        assert retrieved.quality_scores_json["coherence"] == 0.92
        assert retrieved.quality_scores_json["faithfulness"] == 0.88
        assert retrieved.quality_scores_json["toxicity"] == 0.05
        assert retrieved.quality_scores_json["pii_flags"] == []
        assert retrieved.confidence == 0.90
        print("   ✅ Chunk quality signals work correctly")
        
        # Test SyntheticExample
        print("\n4️⃣ Creating test example...")
        example = SyntheticExample(
            id="test-ex-quality",
            variant_id=variant.id,
            example_type=ExampleType.TASK,
            input_json={"task": "test", "input": "Test input"},
            constraints_json={},
            tags=[]
        )
        db.add(example)
        db.commit()
        print("   ✅ SyntheticExample created")
        
        # Test TeacherRun with quality signals
        print("\n5️⃣ Testing TeacherRun quality signals...")
        teacher_run = TeacherRun(
            id="test-tr-quality",
            example_id=example.id,
            provider="openai",
            model="gpt-4o-mini",
            params_json={"temperature": 0.7},
            output_json={"text": "Test output"},
            usage_json={"total_tokens": 100},
            quality_scores_json={
                "coherence": 0.88,
                "faithfulness": 0.92,
                "toxicity": 0.02,
                "pii_flags": []
            },
            confidence=0.87
        )
        db.add(teacher_run)
        db.commit()
        
        retrieved = db.query(TeacherRun).filter_by(id="test-tr-quality").first()
        assert retrieved.quality_scores_json["coherence"] == 0.88
        assert retrieved.quality_scores_json["faithfulness"] == 0.92
        assert retrieved.quality_scores_json["toxicity"] == 0.02
        assert retrieved.confidence == 0.87
        print("   ✅ TeacherRun quality signals work correctly")
        
        # Test Targets with quality signals
        print("\n6️⃣ Testing Targets quality signals...")
        target = Targets(
            id="test-target-quality",
            example_id=example.id,
            y_text="Test target output",
            quality_scores_json={
                "coherence": 0.90,
                "faithfulness": 0.93,
                "toxicity": 0.01,
                "pii_flags": []
            },
            confidence=0.91
        )
        db.add(target)
        db.commit()
        
        retrieved = db.query(Targets).filter_by(id="test-target-quality").first()
        assert retrieved.quality_scores_json["coherence"] == 0.90
        assert retrieved.quality_scores_json["faithfulness"] == 0.93
        assert retrieved.quality_scores_json["toxicity"] == 0.01
        assert retrieved.confidence == 0.91
        print("   ✅ Targets quality signals work correctly")
        
        # Test optional fields (can be None)
        print("\n7️⃣ Testing optional quality signals...")
        chunk2 = Chunk(
            id="test-chunk-no-quality",
            variant_id=variant.id,
            order=1,
            text="Simple chunk without quality signals"
        )
        db.add(chunk2)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="test-chunk-no-quality").first()
        assert retrieved.quality_scores_json is None
        assert retrieved.confidence is None
        print("   ✅ Optional quality signals work correctly")
        
        # Test filtering by confidence
        print("\n8️⃣ Testing filtering by confidence...")
        chunk3 = Chunk(
            id="chunk-high-confidence",
            variant_id=variant.id,
            order=2,
            text="High confidence chunk",
            confidence=0.95
        )
        chunk4 = Chunk(
            id="chunk-low-confidence",
            variant_id=variant.id,
            order=3,
            text="Low confidence chunk",
            confidence=0.60
        )
        db.add_all([chunk3, chunk4])
        db.commit()
        
        high_confidence = db.query(Chunk).filter(Chunk.confidence >= 0.90).all()
        assert len(high_confidence) == 2  # chunk and chunk3
        assert all(c.confidence >= 0.90 for c in high_confidence)
        print("   ✅ Filtering by confidence works correctly")
        
        # Test quality scores with PII flags
        print("\n9️⃣ Testing quality scores with PII flags...")
        chunk5 = Chunk(
            id="chunk-with-pii",
            variant_id=variant.id,
            order=4,
            text="Chunk with potential PII",
            quality_scores_json={
                "coherence": 0.85,
                "faithfulness": 0.80,
                "toxicity": 0.10,
                "pii_flags": ["email", "phone"]
            },
            confidence=0.75
        )
        db.add(chunk5)
        db.commit()
        
        retrieved = db.query(Chunk).filter_by(id="chunk-with-pii").first()
        assert "email" in retrieved.quality_scores_json["pii_flags"]
        assert "phone" in retrieved.quality_scores_json["pii_flags"]
        print("   ✅ Quality scores with PII flags work correctly")
        
        print("\n" + "=" * 60)
        print("✅ All quality signal tests passed!")
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
    success = test_quality_signals()
    sys.exit(0 if success else 1)

