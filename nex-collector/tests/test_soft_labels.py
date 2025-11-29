#!/usr/bin/env python3
"""Simple test script for Soft Labels (no pytest required)."""
import sys
from pathlib import Path
import math

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import (
    ContextDoc, ContextVariant, SyntheticExample, TeacherRun, Targets, ExampleType
)
from app.distill.soft_labels import (
    extract_logprobs_to_probs,
    aggregate_probs_from_runs,
    extract_text_class_probs,
    create_soft_labels_from_runs
)
from app.distill.targets import create_target_with_soft_labels


def test_soft_labels():
    """Test soft label extraction and aggregation."""
    print("🧪 Testing Soft Labels > Hard Labels")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Create test context doc
        print("\n1️⃣ Creating test context document...")
        ctx = ContextDoc(
            id="test-ctx-soft",
            title="Test Context for Soft Labels",
            version="1.0.0",
            body_text="Test context body text."
        )
        db.add(ctx)
        db.commit()
        print("   ✅ ContextDoc created")
        
        # Create test variant
        print("\n2️⃣ Creating test variant...")
        variant = ContextVariant(
            id="test-var-soft",
            context_id=ctx.id,
            domain="test",
            persona="tester",
            task="testing",
            body_text="Test variant body text."
        )
        db.add(variant)
        db.commit()
        print("   ✅ ContextVariant created")
        
        # Create test example
        print("\n3️⃣ Creating test example...")
        example = SyntheticExample(
            id="test-ex-soft",
            variant_id=variant.id,
            example_type=ExampleType.QA,
            input_json={"question": "What is the risk level?"},
            constraints_json={},
            tags=[]
        )
        db.add(example)
        db.commit()
        print("   ✅ SyntheticExample created")
        
        # Create teacher runs with logprobs
        print("\n4️⃣ Creating teacher runs with logprobs...")
        runs_data = [
            {
                "id": "tr-soft-1",
                "text": "moderate",
                "logprobs": {
                    "tokens": ["moderate", "low", "high"],
                    "token_logprobs": [math.log(0.5), math.log(0.3), math.log(0.2)],
                    "top_logprobs": [
                        {"token": "moderate", "logprob": math.log(0.5)},
                        {"token": "low", "logprob": math.log(0.3)},
                        {"token": "high", "logprob": math.log(0.2)}
                    ]
                },
                "confidence": 0.9
            },
            {
                "id": "tr-soft-2",
                "text": "moderate",
                "logprobs": {
                    "tokens": ["moderate", "low", "high"],
                    "token_logprobs": [math.log(0.6), math.log(0.25), math.log(0.15)],
                    "top_logprobs": [
                        {"token": "moderate", "logprob": math.log(0.6)},
                        {"token": "low", "logprob": math.log(0.25)},
                        {"token": "high", "logprob": math.log(0.15)}
                    ]
                },
                "confidence": 0.85
            },
            {
                "id": "tr-soft-3",
                "text": "low",
                "logprobs": {
                    "tokens": ["low", "moderate", "high"],
                    "token_logprobs": [math.log(0.4), math.log(0.35), math.log(0.25)],
                    "top_logprobs": [
                        {"token": "low", "logprob": math.log(0.4)},
                        {"token": "moderate", "logprob": math.log(0.35)},
                        {"token": "high", "logprob": math.log(0.25)}
                    ]
                },
                "confidence": 0.75
            },
        ]
        
        teacher_runs = []
        for run_data in runs_data:
            run = TeacherRun(
                id=run_data["id"],
                example_id=example.id,
                provider="openai",
                model="gpt-4o-mini",
                params_json={"temperature": 0.7},
                output_json={
                    "text": run_data["text"],
                    "logprobs": run_data["logprobs"]
                },
                confidence=run_data["confidence"]
            )
            db.add(run)
            teacher_runs.append(run)
        db.commit()
        print(f"   ✅ Created {len(teacher_runs)} teacher runs with logprobs")
        
        # Test extract_logprobs_to_probs
        print("\n5️⃣ Testing extract_logprobs_to_probs...")
        logprobs = runs_data[0]["logprobs"]
        probs = extract_logprobs_to_probs(logprobs)
        assert probs is not None
        assert "moderate" in probs
        assert abs(probs["moderate"] - 0.5) < 0.01
        print(f"   ✅ Extracted probabilities: {probs}")
        
        # Test aggregate_probs_from_runs
        print("\n6️⃣ Testing aggregate_probs_from_runs...")
        runs_dicts = [
            {
                "output_json": {"logprobs": r["logprobs"]},
                "confidence": r["confidence"]
            }
            for r in runs_data
        ]
        aggregated = aggregate_probs_from_runs(runs_dicts, method="weighted_mean")
        assert "moderate" in aggregated
        assert "low" in aggregated
        assert "high" in aggregated
        # Moderate should have highest probability (weighted by confidence)
        assert aggregated["moderate"] > aggregated["low"]
        print(f"   ✅ Aggregated probabilities: {aggregated}")
        
        # Test extract_text_class_probs
        print("\n7️⃣ Testing extract_text_class_probs...")
        class_probs = extract_text_class_probs("moderate", logprobs)
        assert class_probs is not None
        assert "moderate" in class_probs
        print(f"   ✅ Class probabilities: {class_probs}")
        
        # Test create_soft_labels_from_runs
        print("\n8️⃣ Testing create_soft_labels_from_runs...")
        soft_labels = create_soft_labels_from_runs(
            teacher_runs,
            aggregation_method="weighted_mean",
            include_token_probs=True,
            include_class_probs=True
        )
        assert "token_probs" in soft_labels
        assert "class_probs" in soft_labels
        assert soft_labels["num_runs"] == 3
        assert soft_labels["aggregation_method"] == "weighted_mean"
        print(f"   ✅ Soft labels created: {soft_labels}")
        
        # Test create_target_with_soft_labels
        print("\n9️⃣ Testing create_target_with_soft_labels...")
        target = create_target_with_soft_labels(example, teacher_runs)
        assert target.y_text == "low"  # Latest run
        assert target.y_probs_json is not None
        assert "token_probs" in target.y_probs_json
        assert "class_probs" in target.y_probs_json
        print(f"   ✅ Target created with soft labels")
        print(f"      y_probs_json keys: {list(target.y_probs_json.keys())}")
        
        # Save target to database
        db.add(target)
        db.commit()
        
        # Verify retrieval
        retrieved = db.query(Targets).filter_by(id=target.id).first()
        assert retrieved.y_probs_json == target.y_probs_json
        assert retrieved.y_probs_json["num_runs"] == 3
        print("   ✅ Soft labels stored and retrieved correctly")
        
        # Test different aggregation methods
        print("\n🔟 Testing different aggregation methods...")
        mean_probs = aggregate_probs_from_runs(runs_dicts, method="mean")
        max_probs = aggregate_probs_from_runs(runs_dicts, method="max")
        assert mean_probs is not None
        assert max_probs is not None
        print(f"   ✅ Mean aggregation: {mean_probs}")
        print(f"   ✅ Max aggregation: {max_probs}")
        
        # Test with no logprobs
        print("\n1️⃣1️⃣ Testing with no logprobs...")
        run_no_logprobs = TeacherRun(
            id="tr-no-logprobs",
            example_id=example.id,
            provider="openai",
            model="gpt-4o-mini",
            params_json={},
            output_json={"text": "answer"}
        )
        db.add(run_no_logprobs)
        db.commit()
        
        soft_labels_empty = create_soft_labels_from_runs([run_no_logprobs])
        # Should still create structure but with empty probs
        assert soft_labels_empty["num_runs"] == 1
        print("   ✅ Handles missing logprobs correctly")
        
        print("\n" + "=" * 60)
        print("✅ All Soft Labels tests passed!")
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
    success = test_soft_labels()
    sys.exit(0 if success else 1)

